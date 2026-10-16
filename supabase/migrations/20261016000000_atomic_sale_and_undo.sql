-- Atomic SALE-3/SALE-4 write and reversal used by the backend tool layer.
-- The existing sold_items trigger owns stock decrement + negative movement.

BEGIN;

CREATE OR REPLACE FUNCTION public.record_sale_atomic(
  p_shop_id uuid,
  p_items jsonb,
  p_total_amount numeric,
  p_payment_type text,
  p_customer_id uuid DEFAULT NULL,
  p_created_by uuid DEFAULT NULL
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_sale_id uuid;
  v_item jsonb;
  v_product record;
  v_quantity integer;
  v_unit_price numeric;
  v_stock_after integer;
  v_stock_alerts jsonb := '[]'::jsonb;
BEGIN
  IF p_payment_type NOT IN ('cash', 'udhaar') THEN
    RAISE EXCEPTION 'Invalid payment type';
  END IF;
  IF p_total_amount < 0 THEN
    RAISE EXCEPTION 'Total cannot be negative';
  END IF;
  IF jsonb_array_length(COALESCE(p_items, '[]'::jsonb)) = 0 THEN
    RAISE EXCEPTION 'At least one item is required';
  END IF;
  IF p_payment_type = 'udhaar' AND p_customer_id IS NULL THEN
    RAISE EXCEPTION 'Udhaar sale requires a customer';
  END IF;
  IF p_customer_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM public.customers
    WHERE id = p_customer_id AND shop_id = p_shop_id
  ) THEN
    RAISE EXCEPTION 'Customer does not belong to this shop';
  END IF;

  INSERT INTO public.sales (
    shop_id, customer_id, payment_type, total_amount, created_by
  )
  VALUES (
    p_shop_id, p_customer_id, p_payment_type, p_total_amount, p_created_by
  )
  RETURNING id INTO v_sale_id;

  FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
  LOOP
    v_quantity := (v_item->>'quantity')::integer;
    IF v_quantity <= 0 THEN
      RAISE EXCEPTION 'Item quantity must be positive';
    END IF;

    SELECT id, name, sale_price
      INTO v_product
      FROM public.products
      WHERE id = (v_item->>'product_id')::uuid
        AND shop_id = p_shop_id
      FOR UPDATE;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'Product not found in this shop';
    END IF;

    v_unit_price := COALESCE(
      (v_item->>'unit_price')::numeric,
      v_product.sale_price
    );
    INSERT INTO public.sold_items (sale_id, product_id, quantity, unit_price)
    VALUES (v_sale_id, v_product.id, v_quantity, v_unit_price);

    SELECT stock INTO v_stock_after
    FROM public.products WHERE id = v_product.id;
    IF v_stock_after <= 0 THEN
      v_stock_alerts := v_stock_alerts || jsonb_build_object(
        'product_id', v_product.id,
        'name', v_product.name,
        'stock', v_stock_after
      );
    END IF;
  END LOOP;

  IF p_payment_type = 'udhaar' THEN
    INSERT INTO public.ledger_entries (
      shop_id, customer_id, sale_id, type, amount, created_by
    )
    VALUES (
      p_shop_id, p_customer_id, v_sale_id, 'udhaar', p_total_amount, p_created_by
    );
  END IF;

  RETURN jsonb_build_object(
    'sale_id', v_sale_id,
    'total_amount', p_total_amount,
    'payment_type', p_payment_type,
    'stock_alerts', v_stock_alerts
  );
END;
$$;

CREATE OR REPLACE FUNCTION public.reverse_sale_atomic(
  p_shop_id uuid,
  p_sale_id uuid
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_line record;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.sales
    WHERE id = p_sale_id AND shop_id = p_shop_id
    FOR UPDATE
  ) THEN
    RETURN false;
  END IF;

  FOR v_line IN
    SELECT si.product_id, si.quantity
    FROM public.sold_items si
    JOIN public.products p ON p.id = si.product_id
    WHERE si.sale_id = p_sale_id
    FOR UPDATE OF p
  LOOP
    UPDATE public.products
    SET stock = stock + v_line.quantity, updated_at = now()
    WHERE id = v_line.product_id AND shop_id = p_shop_id;

    INSERT INTO public.stock_movements (
      shop_id, sale_id, product_id, quantity_change
    )
    VALUES (p_shop_id, p_sale_id, v_line.product_id, v_line.quantity);
  END LOOP;

  -- Delete the debt created by an udhaar sale before deleting the sale.
  DELETE FROM public.ledger_entries
  WHERE shop_id = p_shop_id AND sale_id = p_sale_id;

  DELETE FROM public.sales
  WHERE id = p_sale_id AND shop_id = p_shop_id;
  RETURN true;
END;
$$;

REVOKE ALL ON FUNCTION public.record_sale_atomic(
  uuid, jsonb, numeric, text, uuid, uuid
) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.reverse_sale_atomic(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.record_sale_atomic(
  uuid, jsonb, numeric, text, uuid, uuid
) TO service_role;
GRANT EXECUTE ON FUNCTION public.reverse_sale_atomic(uuid, uuid) TO service_role;

COMMIT;
