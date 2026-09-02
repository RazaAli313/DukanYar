-- =====================================================================
-- SALE-4: Atomic undo_sale RPC
--
-- Reverses a committed sale: restore product stock via positive
-- stock_movements, reverse ledger entries if udhaar.  Does NOT delete
-- the sale row — instead the tool_calls record is marked 'undone' by
-- the application layer.  This preserves the audit trail.
-- =====================================================================

CREATE OR REPLACE FUNCTION public.undo_sale(
  p_sale_id uuid,
  p_shop_id uuid
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_sale       record;
  v_item       record;
  v_restored   jsonb := '[]'::jsonb;
BEGIN
  -- 1. Verify the sale exists and belongs to this shop
  SELECT id, shop_id, customer_id, payment_type, total_amount
    INTO v_sale
    FROM public.sales
    WHERE id = p_sale_id AND shop_id = p_shop_id
    FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Sale % not found in shop %', p_sale_id, p_shop_id;
  END IF;

  -- 2. Reverse each sold item: restore stock + insert positive movement
  FOR v_item IN
    SELECT si.product_id, si.quantity, p.name, p.stock AS current_stock
    FROM public.sold_items si
    JOIN public.products p ON p.id = si.product_id
    WHERE si.sale_id = p_sale_id
    FOR UPDATE OF p
  LOOP
    -- Positive stock movement (restoration)
    INSERT INTO public.stock_movements (shop_id, sale_id, product_id, quantity_change)
    VALUES (p_shop_id, p_sale_id, v_item.product_id, v_item.quantity);

    -- Restore stock
    UPDATE public.products
      SET stock = stock + v_item.quantity, updated_at = now()
      WHERE id = v_item.product_id;

    v_restored := v_restored || jsonb_build_object(
      'product_id',    v_item.product_id,
      'name',          v_item.name,
      'quantity_restored', v_item.quantity,
      'stock_after',   v_item.current_stock + v_item.quantity
    );
  END LOOP;

  -- 3. Reverse ledger entry if this was an udhaar sale
  IF v_sale.payment_type = 'udhaar' AND v_sale.customer_id IS NOT NULL THEN
    INSERT INTO public.ledger_entries (shop_id, customer_id, sale_id, type, amount)
    VALUES (p_shop_id, v_sale.customer_id, p_sale_id, 'payment', v_sale.total_amount);
  END IF;

  RETURN jsonb_build_object(
    'sale_id',   p_sale_id,
    'undone',    true,
    'restored',  v_restored
  );
END;
$$;

COMMENT ON FUNCTION public.undo_sale
  IS 'Reverses a committed sale: restores stock via positive stock_movements and offsets ledger if udhaar. The sale row is kept for audit trail.';
