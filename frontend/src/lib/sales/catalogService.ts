import { SupabaseClient } from '@supabase/supabase-js';

export interface ProductMatch {
  id: string;
  name: string;
  sale_price: number;
  cost_price: number;
  stock: number;
  matched_via: string;
}

export interface ResolveResult {
  match: ProductMatch | null;
  candidates: ProductMatch[];
}

/**
 * Resolves product names or Roman Urdu/English aliases (SALE-2).
 * Returns a single match when unambiguous, or a list of candidates
 * when multiple products match similarly.  No matches → both null/empty.
 */
export async function resolveProduct(
  supabase: SupabaseClient,
  searchTerm: string
): Promise<ResolveResult> {
  const term = searchTerm.trim().toLowerCase();
  const seen = new Set<string>();
  const candidates: ProductMatch[] = [];

  // 1. Direct product name lookup — fetch all ilike hits, not just one
  const { data: directMatches } = await supabase
    .from('products')
    .select('id, name, sale_price, cost_price, stock')
    .ilike('name', `%${term}%`);

  for (const row of directMatches ?? []) {
    if (!seen.has(row.id)) {
      seen.add(row.id);
      candidates.push({ ...row, matched_via: 'direct_name' });
    }
  }

  // 2. Alias lookup — fetch all alias hits
  const { data: aliasMatches } = await supabase
    .from('product_aliases')
    .select('product_id, alias, products(id, name, sale_price, cost_price, stock)')
    .ilike('alias', `%${term}%`);

  for (const row of aliasMatches ?? []) {
    if (row.products && !seen.has(row.product_id)) {
      const prod = row.products as unknown as ProductMatch;
      seen.add(row.product_id);
      candidates.push({ ...prod, matched_via: `alias:${row.alias}` });
    }
  }

  // 3. Decision logic
  if (candidates.length === 1) {
    return { match: candidates[0], candidates: [] };
  }
  if (candidates.length > 1) {
    // Ambiguous — caller should ask the shopkeeper to clarify
    return { match: null, candidates };
  }
  return { match: null, candidates: [] };
}

/**
 * Lists all products for a shop, sorted by name (SALE-1).
 * Used by the chat assistant to answer "what's in stock?" queries.
 */
export async function listProducts(
  supabase: SupabaseClient,
  shopId: string
): Promise<ProductMatch[]> {
  const { data } = await supabase
    .from('products')
    .select('id, name, sale_price, cost_price, stock')
    .eq('shop_id', shopId)
    .order('name');

  return (data ?? []).map((row) => ({ ...row, matched_via: 'catalog' }));
}