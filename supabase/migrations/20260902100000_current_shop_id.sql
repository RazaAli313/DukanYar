-- =====================================================================
-- Fix: Define current_shop_id() helper function
-- The Phase-3 migration (20260902070905) references this in 15 RLS
-- policies but it was never created. Without it, any query against
-- products, customers, sales, stock_movements, ledger_entries, or
-- expenses fails with "function public.current_shop_id() does not exist".
-- =====================================================================

CREATE OR REPLACE FUNCTION public.current_shop_id()
RETURNS uuid
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT shop_id FROM public.profiles WHERE id = auth.uid() LIMIT 1;
$$;

COMMENT ON FUNCTION public.current_shop_id()
  IS 'Returns the shop_id for the currently authenticated user. Used by RLS policies across SALE, KHATA, EXP, and RPT tables.';
