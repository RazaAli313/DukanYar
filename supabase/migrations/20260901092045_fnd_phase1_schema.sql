-- =============================================================================
-- DukanYar Phase-1 Migration (FND-2)
-- Strictly Aligned with Project-Wide ERD
-- =============================================================================

-- 1. SHOPS TABLE (Tenant Root)
CREATE TABLE public.shops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    address TEXT,
    location TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. ROLES TABLE
CREATE TABLE public.roles (
    name TEXT PRIMARY KEY
);

INSERT INTO public.roles (name) VALUES ('shopkeeper'), ('admin');

-- 3. PROFILES TABLE (Extends auth.users & references roles + shops)
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    shop_id UUID REFERENCES public.shops(id) ON DELETE SET NULL,
    role_name TEXT REFERENCES public.roles(name) ON DELETE SET NULL DEFAULT 'shopkeeper',
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. CONVERSATIONS TABLE
CREATE TABLE public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id UUID NOT NULL REFERENCES public.shops(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. MESSAGES TABLE
CREATE TABLE public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    sender TEXT NOT NULL,
    channel TEXT NOT NULL,
    message TEXT NOT NULL, -- Matched directly to 'message' in visual ERD
    transcription_confidence FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. ENABLE ROW LEVEL SECURITY
ALTER TABLE public.shops ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- 7. ROW LEVEL SECURITY POLICIES

-- Roles Policy: Read-only for authenticated users
CREATE POLICY "Allow read access to roles" 
    ON public.roles FOR SELECT TO authenticated USING (true);

-- Profiles Policies
CREATE POLICY "Users can view own profile" 
    ON public.profiles FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
    ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- Shops Policies
CREATE POLICY "Users can view assigned shop" 
    ON public.shops FOR SELECT 
    USING (id IN (SELECT shop_id FROM public.profiles WHERE id = auth.uid()));

CREATE POLICY "Users can update assigned shop" 
    ON public.shops FOR UPDATE 
    USING (id IN (SELECT shop_id FROM public.profiles WHERE id = auth.uid()));

-- Conversations Policies
CREATE POLICY "Shopkeepers can access their shop conversations" 
    ON public.conversations FOR ALL 
    USING (shop_id IN (SELECT shop_id FROM public.profiles WHERE id = auth.uid()));

-- Messages Policies
CREATE POLICY "Shopkeepers can access their shop messages" 
    ON public.messages FOR ALL 
    USING (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE shop_id IN (
                SELECT shop_id FROM public.profiles WHERE id = auth.uid()
            )
        )
    );