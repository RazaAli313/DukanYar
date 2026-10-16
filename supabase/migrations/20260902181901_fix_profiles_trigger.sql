-- Fix handle_new_user trigger to handle profile & shop creation cleanly
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  v_shop_id uuid;
BEGIN
  -- 1. Insert into public.profiles with guaranteed email fallback
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (
    new.id,
    COALESCE(new.email, new.raw_user_meta_data->>'email', ''),
    COALESCE(new.raw_user_meta_data->>'full_name', '')
  )
  ON CONFLICT (id) DO UPDATE 
  SET email = EXCLUDED.email;

  -- 2. Insert into public.shops if shop_name metadata is present
  IF new.raw_user_meta_data->>'shop_name' IS NOT NULL THEN
    INSERT INTO public.shops (owner_id, name)
    VALUES (new.id, new.raw_user_meta_data->>'shop_name')
    RETURNING id INTO v_shop_id;

    -- Update profile with the newly created shop_id if column exists
    UPDATE public.profiles 
    SET shop_id = v_shop_id 
    WHERE id = new.id;
  END IF;

  RETURN new;
END;
$$;

-- Ensure the trigger fires whenever a user is created in auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();