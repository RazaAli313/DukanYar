-- =====================================================================
-- CATLG-2: process_stock_adjustment RPC
--
-- Supports three adjustment types:
--   restock_add  — stock += value  (positive stock_movement)
--   restock_set  — stock = value   (delta stock_movement)
--   price_update — sale_price = value
-- =====================================================================

CREATE OR REPLACE FUNCTION public.process_stock_adjustment(
  p_shop_id         uuid,
  p_product_id      uuid,
  p_adjustment_type text,     -- 'restock_add', 'restock_set', 'price_update'
  p_value           numeric,
  p_created_by      uuid DEFAULT NULL
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_product    record;
  v_delta      int;
  v_old_stock  int;
  v_old_price  numeric;
BEGIN
  -- Lock the product row
  SELECT id, name, stock, sale_price
    INTO v_product
    FROM public.products
    WHERE id = p_product_id AND shop_id = p_shop_id
    FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Product % not found in shop %', p_product_id, p_shop_id;
  END IF;

  v_old_stock := v_product.stock;
  v_old_price := v_product.sale_price;

  CASE p_adjustment_type
  WHEN 'restock_add' THEN
    v_delta := p_value::int;
    INSERT INTO public.stock_movements (shop_id, product_id, quantity_change)
    VALUES (p_shop_id, p_product_id, v_delta);
    UPDATE public.products
      SET stock = stock + v_delta, updated_at = now()
      WHERE id = p_product_id;

  WHEN 'restock_set' THEN
    v_delta := p_value::int - v_old_stock;
    INSERT INTO public.stock_movements (shop_id, product_id, quantity_change)
    VALUES (p_shop_id, p_product_id, v_delta);
    UPDATE public.products
      SET stock = p_value::int, updated_at = now()
      WHERE id = p_product_id;

  WHEN 'price_update' THEN
    UPDATE public.products
      SET sale_price = p_value, updated_at = now()
      WHERE id = p_product_id;

  ELSE
    RAISE EXCEPTION 'Unknown adjustment_type: %', p_adjustment_type;
  END CASE;

  RETURN jsonb_build_object(
    'product_id',      p_product_id,
    'name',            v_product.name,
    'adjustment_type', p_adjustment_type,
    'old_stock',       v_old_stock,
    'new_stock',       CASE
                         WHEN p_adjustment_type = 'restock_add' THEN v_old_stock + p_value::int
                         WHEN p_adjustment_type = 'restock_set' THEN p_value::int
                         ELSE v_old_stock
                       END,
    'old_price',       v_old_price,
    'new_price',       CASE
                         WHEN p_adjustment_type = 'price_update' THEN p_value
                         ELSE v_old_price
                       END
  );
END;
$$;

COMMENT ON FUNCTION public.process_stock_adjustment
  IS 'CATLG-2: Atomic stock adjustment (restock_add, restock_set, or price_update) for an existing product.';
