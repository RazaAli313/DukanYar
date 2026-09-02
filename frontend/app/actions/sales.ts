'use server'

import { createClient } from '../../utils/supabase/server';
import { resolveProduct, ResolveResult } from '../../src/lib/sales/catalogService';
import { recordSale, RecordSaleParams, StockAlert } from '../../src/lib/sales/salesService';

/**
 * Server Action: Resolve product by name or alias (SALE-2).
 * Returns { match } when unambiguous, { candidates } when ambiguous,
 * or both empty when no product found.
 */
export async function resolveProductAction(searchTerm: string): Promise<{
  success: boolean;
  data?: ResolveResult;
  error?: string;
}> {
  try {
    const supabase = await createClient();
    const result = await resolveProduct(supabase, searchTerm);
    return { success: true, data: result };
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'An error occurred';
    return { success: false, error: errorMessage };
  }
}

/**
 * Server Action: Process a completed sale transaction (SALE-3, SALE-4)
 */
export async function processSaleAction(params: Omit<RecordSaleParams, 'shop_id'>): Promise<{
  success: boolean;
  sale_id?: string;
  stock_alerts?: StockAlert[];
  warning_message?: string;
  error?: string;
}> {
  try {
    const supabase = await createClient();

    // 1. Resolve current user profile & shop context
    const { data: { user }, error: authErr } = await supabase.auth.getUser();
    if (authErr || !user) throw new Error('Unauthorized');

    const { data: profile, error: profileErr } = await supabase
      .from('profiles')
      .select('shop_id')
      .eq('id', user.id)
      .single();

    if (profileErr || !profile?.shop_id) {
      throw new Error('Active shop not found for user');
    }

    // 2. Execute sale transaction with shop_id scoping
    const result = await recordSale(supabase, {
      ...params,
      shop_id: profile.shop_id,
      created_by: user.id,
    });

    let warningMessage: string | undefined;
    if (result.stock_alerts && result.stock_alerts.length > 0) {
      const itemsStr = result.stock_alerts
        .map((a) => `${a.product_name} (${a.new_stock})`)
        .join(', ');
      warningMessage = `Sale recorded, but inventory went negative for: ${itemsStr}`;
    }

    return {
      success: true,
      sale_id: result.sale_id,
      stock_alerts: result.stock_alerts,
      warning_message: warningMessage,
    };
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'An error occurred';
    return { success: false, error: errorMessage };
  }
}