BEGIN;

ALTER TABLE public.sold_items
  ADD COLUMN IF NOT EXISTS unit_cost numeric(10,2);

ALTER TABLE public.sold_items
  DROP CONSTRAINT IF EXISTS sold_items_unit_cost_check;
ALTER TABLE public.sold_items
  ADD CONSTRAINT sold_items_unit_cost_check
  CHECK (unit_cost IS NULL OR unit_cost > 0);

COMMENT ON COLUMN public.sold_items.unit_cost IS
  'Product acquisition cost captured when the sale line is recorded.';

CREATE OR REPLACE FUNCTION public.capture_sold_item_unit_cost()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
BEGIN
  SELECT cost_price INTO NEW.unit_cost
  FROM public.products
  WHERE id = NEW.product_id;

  IF NEW.unit_cost IS NULL OR NEW.unit_cost <= 0 THEN
    RAISE EXCEPTION 'Product purchase cost is required before sale';
  END IF;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS capture_sold_item_unit_cost ON public.sold_items;
CREATE TRIGGER capture_sold_item_unit_cost
BEFORE INSERT ON public.sold_items
FOR EACH ROW EXECUTE FUNCTION public.capture_sold_item_unit_cost();

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

    SELECT id, name, sale_price, cost_price
      INTO v_product
      FROM public.products
      WHERE id = (v_item->>'product_id')::uuid
        AND shop_id = p_shop_id
      FOR UPDATE;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'Product not found in this shop';
    END IF;
    IF v_product.cost_price <= 0 THEN
      RAISE EXCEPTION 'Product purchase cost is required before sale';
    END IF;

    v_unit_price := COALESCE(
      (v_item->>'unit_price')::numeric,
      v_product.sale_price
    );
    INSERT INTO public.sold_items (
      sale_id, product_id, quantity, unit_price, unit_cost
    )
    VALUES (
      v_sale_id, v_product.id, v_quantity, v_unit_price, v_product.cost_price
    );

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

REVOKE ALL ON FUNCTION public.record_sale_atomic(
  uuid, jsonb, numeric, text, uuid, uuid
) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.record_sale_atomic(
  uuid, jsonb, numeric, text, uuid, uuid
) TO service_role;

COMMIT;
