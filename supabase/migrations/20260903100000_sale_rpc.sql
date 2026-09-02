-- =====================================================================
-- SALE-3 / SALE-4: Atomic process_sale RPC
--
-- One transaction: insert sale → insert sold_items → insert negative
-- stock_movements → decrement product stock → insert ledger if udhaar.
-- Returns { sale_id, items, stock_flags } where stock_flags lists any
-- item whose stock went negative (out-of-stock flagging, SALE-4).
-- =====================================================================

-- Trim payment_type to 'cash' | 'udhaar' only (SALE-3 alignment).
-- The original migration included 'split' which is not part of the MVP scope.
ALTER TABLE public.sales DROP CONSTRAINT IF EXISTS sales_payment_type_check;
ALTER TABLE public.sales ADD CONSTRAINT sales_payment_type_check
  CHECK (payment_type IN ('cash', 'udhaar'));

CREATE OR REPLACE FUNCTION public.process_sale(
  p_shop_id       uuid,
  p_items         jsonb DEFAULT '[]'::jsonb,   -- [{product_id, quantity, unit_price}]
  p_total_amount  numeric DEFAULT 0,
  p_payment_type  text DEFAULT 'cash',
  p_customer_id   uuid DEFAULT NULL,
  p_created_by    uuid DEFAULT NULL
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_sale_id       uuid;
  v_item          jsonb;
  v_product       record;
  v_new_stock     int;
  v_stock_flags   jsonb := '[]'::jsonb;
  v_result_items  jsonb := '[]'::jsonb;
BEGIN
  -- 1. Insert the sale header
  INSERT INTO public.sales (shop_id, customer_id, payment_type, total_amount, created_by)
  VALUES (p_shop_id, p_customer_id, p_payment_type, p_total_amount, p_created_by)
  RETURNING id INTO v_sale_id;

  -- 2. Process each line item
  FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
  LOOP
    -- Fetch current product row (lock for update within tx)
    SELECT id, name, stock, sale_price
      INTO v_product
      FROM public.products
      WHERE id = (v_item->>'product_id')::uuid
        AND shop_id = p_shop_id
      FOR UPDATE;

    IF NOT FOUND THEN
      RAISE EXCEPTION 'Product % not found in shop %', v_item->>'product_id', p_shop_id;
    END IF;

    -- Use the caller-provided unit_price (stated-total primacy: we
    -- store per-item price for profit calc, but the sale total is
    -- whatever the shopkeeper said, not a sum of line items).
    INSERT INTO public.sold_items (sale_id, product_id, quantity, unit_price)
    VALUES (
      v_sale_id,
      v_product.id,
      (v_item->>'quantity')::int,
      COALESCE((v_item->>'unit_price')::numeric, v_product.sale_price)
    );

    -- Negative stock movement
    INSERT INTO public.stock_movements (shop_id, sale_id, product_id, quantity_change)
    VALUES (p_shop_id, v_sale_id, v_product.id, -((v_item->>'quantity')::int));

    -- Decrement stock (non-blocking: allows negative)
    v_new_stock := v_product.stock - (v_item->>'quantity')::int;

    UPDATE public.products
      SET stock = v_new_stock, updated_at = now()
      WHERE id = v_product.id;

    -- Build result item
    v_result_items := v_result_items || jsonb_build_object(
      'product_id',  v_product.id,
      'name',        v_product.name,
      'quantity',    (v_item->>'quantity')::int,
      'unit_price',  COALESCE((v_item->>'unit_price')::numeric, v_product.sale_price),
      'stock_after', v_new_stock
    );

    -- Flag if stock went negative
    IF v_new_stock < 0 THEN
      v_stock_flags := v_stock_flags || jsonb_build_object(
        'product_id',   v_product.id,
        'name',         v_product.name,
        'stock_before', v_product.stock,
        'stock_after',  v_new_stock,
        'flag',         'negative_stock'
      );
    END IF;
  END LOOP;

  -- 3. Ledger entry for udhaar
  IF p_payment_type = 'udhaar' AND p_customer_id IS NOT NULL THEN
    INSERT INTO public.ledger_entries (shop_id, customer_id, sale_id, type, amount, created_by)
    VALUES (p_shop_id, p_customer_id, v_sale_id, 'udhaar', p_total_amount, p_created_by);
  END IF;

  -- 4. Return
  RETURN jsonb_build_object(
    'sale_id',      v_sale_id,
    'total_amount', p_total_amount,
    'payment_type', p_payment_type,
    'items',        v_result_items,
    'stock_flags',  v_stock_flags
  );
END;
$$;

COMMENT ON FUNCTION public.process_sale
  IS 'Atomic sale transaction: inserts sale + line items + stock movements + optional ledger entry in one tx. Returns stock_flags for out-of-stock items.';
