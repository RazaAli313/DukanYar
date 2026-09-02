'use server'

import { createClient } from '../../utils/supabase/server';
import { resolveProduct, ProductMatch } from '../../src/lib/sales/catalogService';
import { recordSale, RecordSaleParams, StockAlert } from '../../src/lib/sales/salesService';

/**
 * Server Action: Search or resolve product by name or alias (SALE-2)
 */
export async function resolveProductAction(searchTerm: string): Promise<{
  success: boolean;
  data?: ProductMatch | null;
  error?: string;
}> {
  try {
    const supabase = await createClient();
    const match = await resolveProduct(supabase, searchTerm);
    return { success: true, data: match };
  } catch (err: any) {
    return { success: false, error: err.message || 'Failed to resolve product' };
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
  } catch (err: any) {
    return { success: false, error: err.message || 'Failed to process sale' };
  }
}