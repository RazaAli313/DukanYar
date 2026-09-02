'use server';

// Use relative paths instead of '@/' path aliases
import { createClient } from '../../utils/supabase/server';
import { createAdminClient } from '../../utils/supabase/admin';

export async function signUpAction(formData: FormData) {
  const supabase = await createClient();
  const adminSupabase = createAdminClient();

  const email = formData.get('email') as string;
  const password = formData.get('password') as string;
  const shopName = formData.get('shopName') as string;

  // 1. Create standard Auth User
  const { data: authData, error: authError } = await supabase.auth.signUp({
    email,
    password,
  });

  if (authError || !authData.user) {
    return { error: authError?.message || 'Failed to register user.' };
  }

  // 2. Insert Shop record using Admin Client (Bypasses RLS)
  const { data: shopData, error: shopError } = await adminSupabase
    .from('shops')
    .insert({ name: shopName })
    .select()
    .single();

  if (shopError) {
    return { error: 'Failed to create shop record.' };
  }

  // 3. Insert Profile record linked to Shop ID and assign 'shopkeeper' role
  const { error: profileError } = await adminSupabase
    .from('profiles')
    .insert({
      id: authData.user.id,
      shop_id: shopData.id,
      role_name: 'shopkeeper',
    });

  if (profileError) {
    return { error: 'Failed to complete user profile creation.' };
  }

  return { success: true };
}