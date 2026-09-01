-- Fix Roles Seeding
DELETE FROM public.roles;

INSERT INTO public.roles (name) VALUES
  ('shopkeeper'),
  ('admin')
ON CONFLICT (name) DO NOTHING;

-- Admin Helper Function
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.profiles
    WHERE id = auth.uid() AND role_name = 'admin'
  );
$$;

-- Add user_id to Conversations
ALTER TABLE public.conversations 
ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL;

-- Add ERD Columns to Messages
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'message_channel') THEN
    CREATE TYPE message_channel AS ENUM ('text', 'voice');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'message_status') THEN
    CREATE TYPE message_status AS ENUM ('pending', 'streaming', 'complete', 'failed');
  END IF;
END $$;

ALTER TABLE public.messages
ADD COLUMN IF NOT EXISTS channel message_channel DEFAULT 'text',
ADD COLUMN IF NOT EXISTS status message_status DEFAULT 'complete',
ADD COLUMN IF NOT EXISTS transcription_confidence numeric(4,3) CHECK (transcription_confidence BETWEEN 0 AND 1);

-- Harden RLS Policies with Admin Override
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow profile insertion on signup" ON public.profiles;
DROP POLICY IF EXISTS "Allow individual read access to profiles" ON public.profiles;
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;

CREATE POLICY "Users can insert own profile" ON public.profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "Users or Admins can view profiles" ON public.profiles FOR SELECT USING (auth.uid() = id OR public.is_admin());

ALTER TABLE public.shops ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow public insert for shop registration" ON public.shops;
DROP POLICY IF EXISTS "Allow users to read their shops" ON public.shops;
DROP POLICY IF EXISTS "Allow users to view shops" ON public.shops;

CREATE POLICY "Authenticated users can insert shop" ON public.shops FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Shopkeepers or Admins can view assigned shop" ON public.shops FOR SELECT USING (
  id IN (SELECT shop_id FROM public.profiles WHERE id = auth.uid()) OR public.is_admin()
);

ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Shopkeepers can access their shop conversations" ON public.conversations;

CREATE POLICY "Shopkeepers or Admins can access conversations" ON public.conversations FOR ALL USING (
  shop_id IN (SELECT shop_id FROM public.profiles WHERE id = auth.uid()) OR public.is_admin()
);

ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Shopkeepers can access their shop messages" ON public.messages;

CREATE POLICY "Shopkeepers or Admins can access messages" ON public.messages FOR ALL USING (
  conversation_id IN (
    SELECT id FROM public.conversations 
    WHERE shop_id IN (SELECT shop_id FROM public.profiles WHERE id = auth.uid())
  ) OR public.is_admin()
);