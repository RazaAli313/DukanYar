-- =====================================================================
-- SALE-1: Seed data for demo catalog
-- ~16 realistic Pakistani retail products with voice-resolution aliases.
-- Idempotent: safe to re-run via INSERT ... ON CONFLICT DO NOTHING.
-- =====================================================================

-- Demo shop (fixed UUID so frontend/backend stubs can reference it)
INSERT INTO public.shops (id, name, address)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'Demo Dukan',
  'Model Town, Lahore'
)
ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- Products
-- =====================================================================
INSERT INTO public.products (id, shop_id, name, sale_price, cost_price, stock) VALUES
  ('a0000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'Coca-Cola 345ml',       80,    60,   48),
  ('a0000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'Pepsi 345ml',            80,    60,   36),
  ('a0000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'Lays Classic (family)', 150,   110,   30),
  ('a0000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001', 'Oreo Biscuit',           60,    42,   24),
  ('a0000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000001', 'Nestle Water 1.5L',     100,    70,   60),
  ('a0000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000001', 'Tapal Danedar 900g',   1400,  1200,   12),
  ('a0000000-0000-0000-0000-000000000007', '00000000-0000-0000-0000-000000000001', 'Olper Milk 1L',         280,   245,   24),
  ('a0000000-0000-0000-0000-000000000008', '00000000-0000-0000-0000-000000000001', 'Shan Biryani Masala',    90,    65,   18),
  ('a0000000-0000-0000-0000-000000000009', '00000000-0000-0000-0000-000000000001', 'National Ketchup 310g', 250,   190,   15),
  ('a0000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000001', 'Dalda Oil 5L',         2800,  2500,    8),
  ('a0000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000001', 'Surf Excel 1kg',        650,   520,   15),
  ('a0000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000001', 'Lifebuoy Soap',          90,    65,   20),
  ('a0000000-0000-0000-0000-000000000013', '00000000-0000-0000-0000-000000000001', 'Jazz SIM',              100,    80,   10),
  ('a0000000-0000-0000-0000-000000000014', '00000000-0000-0000-0000-000000000001', 'Rooh Afza 800ml',      450,   370,   12),
  ('a0000000-0000-0000-0000-000000000015', '00000000-0000-0000-0000-000000000001', 'Parle-G Biscuit',        30,    20,   50),
  ('a0000000-0000-0000-0000-000000000016', '00000000-0000-0000-0000-000000000001', 'Sting Energy Drink',    150,   110,   24)
ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- Product aliases (voice-resolution nicknames)
-- =====================================================================

-- Coca-Cola 345ml
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000001', 'coke'),
  ('a0000000-0000-0000-0000-000000000001', 'thanda'),
  ('a0000000-0000-0000-0000-000000000001', 'cola')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Pepsi 345ml
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000002', 'pepsi')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Lays Classic (family)
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000003', 'lays'),
  ('a0000000-0000-0000-0000-000000000003', 'chips')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Oreo Biscuit
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000004', 'oreo'),
  ('a0000000-0000-0000-0000-000000000004', 'biscuit')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Nestle Water 1.5L
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000005', 'paani'),
  ('a0000000-0000-0000-0000-000000000005', 'pani'),
  ('a0000000-0000-0000-0000-000000000005', 'water')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Tapal Danedar 900g
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000006', 'tapal'),
  ('a0000000-0000-0000-0000-000000000006', 'chai'),
  ('a0000000-0000-0000-0000-000000000006', 'tea')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Olper Milk 1L
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000007', 'doodh'),
  ('a0000000-0000-0000-0000-000000000007', 'milk'),
  ('a0000000-0000-0000-0000-000000000007', 'olpers')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Shan Biryani Masala
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000008', 'biryani masala'),
  ('a0000000-0000-0000-0000-000000000008', 'shan')
ON CONFLICT (product_id, alias) DO NOTHING;

-- National Ketchup 310g
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000009', 'ketchup'),
  ('a0000000-0000-0000-0000-000000000009', 'sauce')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Dalda Oil 5L
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000010', 'dalda'),
  ('a0000000-0000-0000-0000-000000000010', 'oil'),
  ('a0000000-0000-0000-0000-000000000010', 'ghee')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Surf Excel 1kg
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000011', 'surf'),
  ('a0000000-0000-0000-0000-000000000011', 'detergent')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Lifebuoy Soap
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000012', 'lifebuoy'),
  ('a0000000-0000-0000-0000-000000000012', 'sabun'),
  ('a0000000-0000-0000-0000-000000000012', 'soap')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Jazz SIM
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000013', 'jazz'),
  ('a0000000-0000-0000-0000-000000000013', 'sim')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Rooh Afza 800ml
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000014', 'rooh afza'),
  ('a0000000-0000-0000-0000-000000000014', 'sharbat')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Parle-G Biscuit
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000015', 'parle'),
  ('a0000000-0000-0000-0000-000000000015', 'parle-g')
ON CONFLICT (product_id, alias) DO NOTHING;

-- Sting Energy Drink
INSERT INTO public.product_aliases (product_id, alias) VALUES
  ('a0000000-0000-0000-0000-000000000016', 'sting'),
  ('a0000000-0000-0000-0000-000000000016', 'energy')
ON CONFLICT (product_id, alias) DO NOTHING;
