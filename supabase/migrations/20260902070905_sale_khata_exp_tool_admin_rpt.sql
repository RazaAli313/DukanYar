-- =====================================================================
-- DukanYar — Phase 3+ Migration: SALE, KHATA, EXP, TOOL, ADMIN, RPT
-- ERD-aligned schema (Matches DukanYar_Project-Wide_ERD.pdf)
-- Depends on: 001_foundation.sql (shops, profiles, messages, current_shop_id(), is_admin())
-- =====================================================================

BEGIN;

-- =====================================================================
-- 1. SALE & CATALOG (Products, Aliases, Sales, Sold Items, Movements)
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  shop_id UUID NOT NULL REFERENCES public.shops(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  sale_price NUMERIC(10,2) NOT NULL CHECK (sale_price >= 0),
  cost_price NUMERIC(10,2) NOT NULL CHECK (cost_price >= 0),
  stock INTEGER NOT NULL DEFAULT 0, -- Can dip negative per SALE-4 (non-blocking)
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Supports fuzzy matching & voice resolution (SALE-1, SALE-2)
CREATE TABLE IF NOT EXISTS public.product_aliases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID NOT NULL REFERENCES public.products(id) ON DELETE CASCADE,
  alias TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_product_alias UNIQUE (product_id, alias)
);

-- =====================================================================
-- 2. KHATA (Customers & Ledger Entries)
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  shop_id UUID NOT NULL REFERENCES public.shops(id) ON DELETE CASCADE,
  khata_number INTEGER NOT NULL,
  name TEXT NOT NULL,
  cnic TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_customer_khata_per_shop UNIQUE (shop_id, khata_number),
  CONSTRAINT uq_customer_cnic_per_shop UNIQUE (shop_id, cnic)
);

-- Auto-increments khata_number sequentially per shop
CREATE OR REPLACE FUNCTION public.assign_khata_number()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.khata_number IS NULL THEN
    SELECT COALESCE(MAX(khata_number), 0) + 1 INTO NEW.khata_number
    FROM public.customers WHERE shop_id = NEW.shop_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_assign_khata_number ON public.customers;
CREATE TRIGGER trg_assign_khata_number
BEFORE INSERT ON public.customers
FOR EACH ROW EXECUTE FUNCTION public.assign_khata_number();

-- =====================================================================
-- 3. SALES TRANSACTIONS & STOCK MOVEMENTS
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.sales (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  shop_id UUID NOT NULL REFERENCES public.shops(id) ON DELETE CASCADE,
  customer_id UUID REFERENCES public.customers(id) ON DELETE SET NULL, -- NULL = cash transaction
  payment_type TEXT NOT NULL CHECK (payment_type IN ('cash', 'udhaar', 'split')),
  total_amount NUMERIC(10,2) NOT NULL CHECK (total_amount >= 0), -- Stated total primacy (SALE-3)
  created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.sold_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sale_id UUID NOT NULL REFERENCES public.sales(id) ON DELETE CASCADE,
  product_id UUID NOT NULL REFERENCES public.products(id) ON DELETE RESTRICT,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0), -- Historical snapshot for profit calculation
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.stock_movements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  shop_id UUID NOT NULL REFERENCES public.shops(id) ON DELETE CASCADE, -- Denormalized for RLS speed
  sale_id UUID REFERENCES public.sales(id) ON DELETE SET NULL,
  product_id UUID NOT NULL REFERENCES public.products(id) ON DELETE CASCADE,
  quantity_change INTEGER NOT NULL, -- Negative = sale decrement, positive = restocking
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.ledger_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  shop_id UUID NOT NULL REFERENCES public.shops(id) ON DELETE CASCADE, -- Denormalized for RLS speed
  customer_id UUID NOT NULL REFERENCES public.customers(id) ON DELETE CASCADE,
  sale_id UUID REFERENCES public.sales(id) ON DELETE SET NULL,
  type TEXT NOT NULL CHECK (type IN ('udhaar', 'payment')),
  amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
  created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- 4. EXPENSE TRACKING
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.expense_categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO public.expense_categories (name) 
VALUES ('Uncategorized')
ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS public.expenses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  shop_id UUID NOT NULL REFERENCES public.shops(id) ON DELETE CASCADE,
  category_id UUID REFERENCES public.expense_categories(id) ON DELETE SET NULL,
  amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
  note TEXT,
  expense_date DATE NOT NULL DEFAULT CURRENT_DATE,
  created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- 5. TOOL CALLS & ACTION STATE MANAGEMENT
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.tool_calls (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id UUID NOT NULL REFERENCES public.messages(id) ON DELETE CASCADE,
  tool_name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (
    status IN (
      'pending',          -- Intercepted, evaluating execution path
      'pending_approval', -- Money-in requiring shopkeeper tap approval (KHATA-3, TOOL-3)
      'committed',        -- Executed and written to DB
      'rejected',         -- Declined on approval card
      'undone',           -- Committed transaction rolled back via inverse delta (TOOL-3)
      'failed'            -- Code or validation exception
    )
  ),
  params JSONB NOT NULL DEFAULT '{}'::jsonb,
  response JSONB, -- Stores execution result, error detail, or UI card metadata (TOOL-4)
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ
);

-- =====================================================================
-- 6. ADMIN AUDIT TRAIL
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  shop_id UUID REFERENCES public.shops(id) ON DELETE SET NULL, -- NULL = platform system action
  action_type TEXT NOT NULL,
  details JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- 7. ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================================

ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sold_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stock_movements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.expense_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tool_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;

-- Products
CREATE POLICY "shop read products" ON public.products FOR SELECT USING (public.is_admin() OR shop_id = public.current_shop_id());
CREATE POLICY "shop insert products" ON public.products FOR INSERT WITH CHECK (shop_id = public.current_shop_id());
CREATE POLICY "shop update products" ON public.products FOR UPDATE USING (shop_id = public.current_shop_id());

-- Customers
CREATE POLICY "shop read customers" ON public.customers FOR SELECT USING (public.is_admin() OR shop_id = public.current_shop_id());
CREATE POLICY "shop insert customers" ON public.customers FOR INSERT WITH CHECK (shop_id = public.current_shop_id());

-- Sales & Ledger
CREATE POLICY "shop read sales" ON public.sales FOR SELECT USING (public.is_admin() OR shop_id = public.current_shop_id());
CREATE POLICY "shop insert sales" ON public.sales FOR INSERT WITH CHECK (shop_id = public.current_shop_id());

CREATE POLICY "shop read stock movements" ON public.stock_movements FOR SELECT USING (public.is_admin() OR shop_id = public.current_shop_id());
CREATE POLICY "shop insert stock movements" ON public.stock_movements FOR INSERT WITH CHECK (shop_id = public.current_shop_id());

CREATE POLICY "shop read ledger entries" ON public.ledger_entries FOR SELECT USING (public.is_admin() OR shop_id = public.current_shop_id());
CREATE POLICY "shop insert ledger entries" ON public.ledger_entries FOR INSERT WITH CHECK (shop_id = public.current_shop_id());

-- Expenses
CREATE POLICY "shop read expenses" ON public.expenses FOR SELECT USING (public.is_admin() OR shop_id = public.current_shop_id());
CREATE POLICY "shop insert expenses" ON public.expenses FOR INSERT WITH CHECK (shop_id = public.current_shop_id());
CREATE POLICY "shop delete expenses" ON public.expenses FOR DELETE USING (shop_id = public.current_shop_id());

-- Relational/Parent-scoped policies
CREATE POLICY "shop read product aliases" ON public.product_aliases
  FOR SELECT USING (public.is_admin() OR product_id IN (SELECT id FROM public.products WHERE shop_id = public.current_shop_id()));
CREATE POLICY "shop insert product aliases" ON public.product_aliases
  FOR INSERT WITH CHECK (product_id IN (SELECT id FROM public.products WHERE shop_id = public.current_shop_id()));

CREATE POLICY "shop read sold items" ON public.sold_items
  FOR SELECT USING (public.is_admin() OR sale_id IN (SELECT id FROM public.sales WHERE shop_id = public.current_shop_id()));
CREATE POLICY "shop insert sold items" ON public.sold_items
  FOR INSERT WITH CHECK (sale_id IN (SELECT id FROM public.sales WHERE shop_id = public.current_shop_id()));

CREATE POLICY "shop read tool calls" ON public.tool_calls
  FOR SELECT USING (
    public.is_admin() OR
    message_id IN (SELECT m.id FROM public.messages m JOIN public.conversations c ON c.id = m.conversation_id WHERE c.shop_id = public.current_shop_id())
  );
CREATE POLICY "shop insert tool calls" ON public.tool_calls
  FOR INSERT WITH CHECK (
    message_id IN (SELECT m.id FROM public.messages m JOIN public.conversations c ON c.id = m.conversation_id WHERE c.shop_id = public.current_shop_id())
  );
CREATE POLICY "shop update tool calls" ON public.tool_calls
  FOR UPDATE USING (
    public.is_admin() OR
    message_id IN (SELECT m.id FROM public.messages m JOIN public.conversations c ON c.id = m.conversation_id WHERE c.shop_id = public.current_shop_id())
  );

-- Global & Admin
CREATE POLICY "authenticated read expense categories" ON public.expense_categories
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "admin read audit log" ON public.audit_log 
  FOR SELECT USING (public.is_admin());

-- =====================================================================
-- 8. REPORTING VIEWS (RPT-1 to RPT-4)
-- =====================================================================

-- Daily Sales & Profit (RPT-1, RPT-2)
CREATE OR REPLACE VIEW public.daily_sales_profit_view AS
SELECT
  s.shop_id,
  DATE(s.created_at) AS report_date,
  SUM(s.total_amount) AS total_sales,
  SUM(s.total_amount) - COALESCE(SUM(si.quantity * p.cost_price), 0) AS total_profit
FROM public.sales s
LEFT JOIN public.sold_items si ON si.sale_id = s.id
LEFT JOIN public.products p ON p.id = si.product_id
GROUP BY s.shop_id, DATE(s.created_at);

-- Outstanding Customer Udhaar Balances (RPT-3)
CREATE OR REPLACE VIEW public.outstanding_udhaar_view AS
SELECT
  c.shop_id,
  c.id AS customer_id,
  c.khata_number,
  c.name AS customer_name,
  COALESCE(SUM(CASE WHEN le.type = 'udhaar' THEN le.amount ELSE 0 END), 0)
    - COALESCE(SUM(CASE WHEN le.type = 'payment' THEN le.amount ELSE 0 END), 0) AS balance
FROM public.customers c
LEFT JOIN public.ledger_entries le ON le.customer_id = c.id
GROUP BY c.shop_id, c.id, c.khata_number, c.name;

-- Low Stock Inventory Threshold (RPT-4)
CREATE OR REPLACE VIEW public.low_stock_view AS
SELECT
  p.shop_id,
  p.id AS product_id,
  p.name,
  p.stock
FROM public.products p
WHERE p.stock <= 5;

COMMIT;