'use server';

import { redirect } from 'next/navigation';
import { createClient } from '../../utils/supabase/server';
import { createAdminClient } from '../../utils/supabase/admin';

// ---------------------------------------------------------------------------
// Sign In (login)
// ---------------------------------------------------------------------------

export async function signIn(formData: FormData) {
  const supabase = await createClient();

  const email = formData.get('email') as string;
  const password = formData.get('password') as string;

  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    return { error: error.message };
  }

  redirect('/app');
}

// ---------------------------------------------------------------------------
// Sign Up (register)
// ---------------------------------------------------------------------------

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

  redirect('/login');
}

/** Alias so pages can import either `signUpAction` or `signUp`. */
export { signUpAction as signUp };

// ---------------------------------------------------------------------------
// Get User Profile (dashboard)
// ---------------------------------------------------------------------------

export async function getUserProfile() {
  const supabase = await createClient();

  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return null;

  const { data: profile, error } = await supabase
    .from('profiles')
    .select('*, shops(id, name, address)')
    .eq('id', user.id)
    .single();

  if (error || !profile) return null;

  return { ...profile, email: user.email ?? profile.email };
}

// ---------------------------------------------------------------------------
// Sign Out
// ---------------------------------------------------------------------------

export async function signOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect('/login');
}