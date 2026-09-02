import { SupabaseClient } from '@supabase/supabase-js';

export interface ProductMatch {
  id: string;
  name: string;
  sale_price: number;
  cost_price: number;
  stock: number;
  matched_via: string;
}

/**
 * Resolves product names or Roman Urdu/English aliases (SALE-2)
 */
export async function resolveProduct(
  supabase: SupabaseClient,
  searchTerm: string
): Promise<ProductMatch | null> {
  const term = searchTerm.trim().toLowerCase();

  // 1. Direct product name lookup
  const { data: directMatch } = await supabase
    .from('products')
    .select('id, name, sale_price, cost_price, stock')
    .ilike('name', `%${term}%`)
    .limit(1)
    .maybeSingle();

  if (directMatch) {
    return { ...directMatch, matched_via: 'direct_name' };
  }

  // 2. Alias lookup
  const { data: aliasMatch } = await supabase
    .from('product_aliases')
    .select('product_id, alias, products(id, name, sale_price, cost_price, stock)')
    .ilike('alias', term)
    .limit(1)
    .maybeSingle();

  if (aliasMatch && aliasMatch.products) {
    const prod = aliasMatch.products as unknown as ProductMatch;
    return { ...prod, matched_via: `alias:${aliasMatch.alias}` };
  }

  return null;
}