-- =====================================================================
-- EXP-1 / EXP-2 — seed default expense categories
-- Additive. The base schema (20260902070905_...) seeds only 'Uncategorized';
-- EXP-2's category inference ("bijli ka bill" -> utilities) needs the rest.
-- =====================================================================

INSERT INTO public.expense_categories (name) VALUES
  ('Utilities'),      -- bijli, gas, paani, phone, internet
  ('Rent'),           -- kiraya
  ('Supplies'),       -- shopping bags, packaging, shop consumables
  ('Salaries'),       -- staff tankhwah
  ('Transport'),      -- delivery, fuel, rickshaw, loading
  ('Maintenance'),    -- repairs, marammat
  ('Other')
ON CONFLICT (name) DO NOTHING;
