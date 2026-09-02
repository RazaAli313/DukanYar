import { SupabaseClient } from '@supabase/supabase-js';

export interface SaleItemInput {
  product_id: string;
  quantity: number;
  unit_price: number;
}

export interface RecordSaleParams {
  shop_id: string;
  customer_id?: string | null;
  payment_type: 'cash' | 'udhaar' | 'split';
  total_amount: number; // Stated total primacy (SALE-3)
  created_by?: string;
  items: SaleItemInput[];
}

export interface StockAlert {
  product_id: string;
  product_name: string;
  new_stock: number;
  is_negative: boolean;
}

/**
 * Records sales with non-blocking negative inventory support (SALE-3, SALE-4)
 */
export async function recordSale(
  supabase: SupabaseClient,
  params: RecordSaleParams
) {
  const { shop_id, customer_id, payment_type, total_amount, created_by, items } = params;
  const stockAlerts: StockAlert[] = [];

  // 1. Insert Sales Record
  const { data: sale, error: saleErr } = await supabase
    .from('sales')
    .insert({
      shop_id,
      customer_id: customer_id || null,
      payment_type,
      total_amount,
      created_by: created_by || null,
    })
    .select('id')
    .single();

  if (saleErr || !sale) throw new Error(`Sale creation failed: ${saleErr?.message}`);

  // 2. Insert Line Items & Update Stock Non-Blockingly
  if (items.length > 0) {
    const soldItemsPayload = items.map((item) => ({
      sale_id: sale.id,
      product_id: item.product_id,
      quantity: item.quantity,
      unit_price: item.unit_price,
    }));

    const { error: itemsErr } = await supabase.from('sold_items').insert(soldItemsPayload);
    if (itemsErr) throw new Error(`Failed to record sold items: ${itemsErr.message}`);

    for (const item of items) {
      // Append negative stock movement ledger
      await supabase.from('stock_movements').insert({
        shop_id,
        sale_id: sale.id,
        product_id: item.product_id,
        quantity_change: -item.quantity,
      });

      // Fetch and decrement stock (allows stock < 0)
      const { data: prod } = await supabase
        .from('products')
        .select('name, stock')
        .eq('id', item.product_id)
        .single();

      if (prod) {
        const updatedStock = prod.stock - item.quantity;
        await supabase
          .from('products')
          .update({ stock: updatedStock, updated_at: new Date().toISOString() })
          .eq('id', item.product_id);

        // Flag low or negative stock for chat response
        if (updatedStock < 0) {
          stockAlerts.push({
            product_id: item.product_id,
            product_name: prod.name,
            new_stock: updatedStock,
            is_negative: true,
          });
        }
      }
    }
  }

  // 3. Handle Udhaar / Ledger Entry
  if ((payment_type === 'udhaar' || payment_type === 'split') && customer_id) {
    const { error: ledgerErr } = await supabase.from('ledger_entries').insert({
      shop_id,
      customer_id,
      sale_id: sale.id,
      type: 'udhaar',
      amount: total_amount,
      created_by: created_by || null,
    });

    if (ledgerErr) throw new Error(`Failed to update ledger balance: ${ledgerErr.message}`);
  }

  return { success: true, sale_id: sale.id, stock_alerts: stockAlerts };
}