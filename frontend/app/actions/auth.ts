'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { createClient } from '../../utils/supabase/server'
import { createAdminClient } from '../../utils/supabase/admin'

export async function signUp(formData: FormData) {
  const supabase = await createClient()
  const adminSupabase = createAdminClient()

  const email = (formData.get('email') as string)?.trim().toLowerCase()
  const password = formData.get('password') as string
  const shopName = (formData.get('shopName') as string)?.trim()

  if (!email || !password || !shopName) {
    return { error: 'Email, password, and shop name are required.' }
  }

  // 1. Register User in Supabase Auth
  const { data: authData, error: authError } = await supabase.auth.signUp({
    email,
    password,
  })

  if (authError || !authData.user) {
    return { error: authError?.message || 'Failed to register user.' }
  }

  const userId = authData.user.id

  // 2. Insert new Shop into public.shops using Admin Client (Bypasses RLS)
  const { data: shopData, error: shopError } = await adminSupabase
    .from('shops')
    .insert({ name: shopName })
    .select()
    .single()

  if (shopError) {
    console.error('SERVER ACTION ERROR (SHOPS):', shopError)
    return { error: 'User created, but failed to create shop entry.' }
  }

  // 3. Insert user Metadata into public.profiles using Admin Client
  const { error: profileError } = await adminSupabase.from('profiles').insert([
    {
      id: userId,
      shop_id: shopData.id,
      email: email,
      role_name: 'shopkeeper',
    },
  ])

  if (profileError) {
    console.error('SERVER ACTION ERROR (PROFILES):', profileError)
    await adminSupabase.from('shops').delete().eq('id', shopData.id)
    return { error: 'Account created, but failed to set up user profile.' }
  }

  revalidatePath('/', 'layout')
  redirect('/app')
}

export async function signIn(formData: FormData) {
  const supabase = await createClient()

  const email = (formData.get('email') as string)?.trim().toLowerCase()
  const password = formData.get('password') as string

  if (!email || !password) {
    return { error: 'Email and password are required.' }
  }

  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (error) {
    return { error: error.message }
  }

  revalidatePath('/', 'layout')
  redirect('/app')
}

export async function signOut() {
  const supabase = await createClient()
  await supabase.auth.signOut()
  revalidatePath('/', 'layout')
  redirect('/login')
}

export async function getUserProfile() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) return null

  const { data: profile } = await supabase
    .from('profiles')
    .select('*, shops(*)')
    .eq('id', user.id)
    .single()

  return profile
}