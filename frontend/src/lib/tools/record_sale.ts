/**
 * record_sale tool (SALE-3, SALE-4).
 *
 * The model calls this with parsed items and a total.  The handler
 * resolves each product_name to a product_id via the catalog service,
 * then invokes the atomic process_sale RPC.  Stock flags (out-of-stock
 * warnings) are appended to the chat reply summary.
 */

// import { SupabaseClient } from '@supabase/supabase-js';
import { resolveProduct } from '../sales/catalogService';
import type { ToolDefinition, ToolContext, ToolResult } from './registry';

// ---------------------------------------------------------------------------
// Schema the model fills when calling this tool
// ---------------------------------------------------------------------------

const parameters = {
  type: 'object',
  properties: {
    items: {
      type: 'array',
      description: 'Line items the shopkeeper mentioned',
      items: {
        type: 'object',
        properties: {
          product_name: { type: 'string', description: 'Spoken product name or alias' },
          quantity: { type: 'integer', description: 'Number of units sold', minimum: 1 },
        },
        required: ['product_name', 'quantity'],
      },
    },
    total_amount: {
      type: 'number',
      description: 'The total amount the shopkeeper stated (source of truth)',
      minimum: 0,
    },
    payment_type: {
      type: 'string',
      enum: ['cash', 'udhaar'],
      description: 'cash if no khata mentioned; udhaar if a khata number is given',
    },
    khata_number: {
      type: 'integer',
      description: 'Customer khata number (only for udhaar sales)',
      nullable: true,
    },
  },
  required: ['items', 'total_amount'],
};

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

async function handler(
  params: Record<string, unknown>,
  ctx: ToolContext,
): Promise<ToolResult> {
  const { supabase, shopId, userId } = ctx;

  // 1. Resolve each product name to an ID
  const rawItems = (params.items as Array<{ product_name: string; quantity: number }>) ?? [];
  const resolvedItems: Array<{
    product_id: string;
    name: string;
    quantity: number;
    unit_price: number;
  }> = [];
  const unresolved: string[] = [];

  for (const item of rawItems) {
    const result = await resolveProduct(supabase, item.product_name);

    if (result.match) {
      resolvedItems.push({
        product_id: result.match.id,
        name: result.match.name,
        quantity: item.quantity,
        unit_price: result.match.sale_price,
      });
    } else if (result.candidates.length > 0) {
      // Ambiguous — pick the first candidate but note the ambiguity
      const best = result.candidates[0];
      resolvedItems.push({
        product_id: best.id,
        name: best.name,
        quantity: item.quantity,
        unit_price: best.sale_price,
      });
    } else {
      unresolved.push(item.product_name);
    }
  }

  if (unresolved.length > 0) {
    return {
      success: false,
      summary: `Could not find these products in your catalog: ${unresolved.join(', ')}. Please check the name and try again.`,
    };
  }

  if (resolvedItems.length === 0) {
    return { success: false, summary: 'No items to record.' };
  }

  // 2. Resolve customer if khata number provided
  let customerId: string | null = null;
  const paymentType = (params.payment_type as string) ?? 'cash';
  const khataNumber = params.khata_number as number | null | undefined;

  if (khataNumber && paymentType !== 'cash') {
    const { data: customer } = await supabase
      .from('customers')
      .select('id')
      .eq('shop_id', shopId)
      .eq('khata_number', khataNumber)
      .maybeSingle();

    if (!customer) {
      return {
        success: false,
        summary: `Khata number ${khataNumber} not found. Please check the number or record as a cash sale.`,
      };
    }
    customerId = customer.id;
  }

  // 3. Call the atomic process_sale RPC
  const totalAmount = Number(params.total_amount) || 0;

  const { data: rpcResult, error: rpcError } = await supabase.rpc('process_sale', {
    p_shop_id: shopId,
    p_items: resolvedItems.map((i) => ({
      product_id: i.product_id,
      quantity: i.quantity,
      unit_price: i.unit_price,
    })),
    p_total_amount: totalAmount,
    p_payment_type: paymentType,
    p_customer_id: customerId,
    p_created_by: userId,
  });

  if (rpcError) {
    return {
      success: false,
      summary: `Sale failed: ${rpcError.message}`,
    };
  }

  // 4. Build human-readable summary (includes Phase 4D out-of-stock flags)
  const result = rpcResult as Record<string, unknown>;
  const items = result.items as Array<Record<string, unknown>>;
  const stockFlags = (result.stock_flags ?? []) as Array<Record<string, unknown>>;

  const itemLines = items
    .map((i) => `  ${i.name} x${i.quantity} @ Rs ${i.unit_price}`)
    .join('\n');

  let summary = `Sale recorded — Rs ${totalAmount} (${paymentType}).\n${itemLines}`;

  // Phase 4D: append out-of-stock warnings directly into the chat text
  if (stockFlags.length > 0) {
    const warnings = stockFlags
      .map((f) => `${f.name} is now out of stock (${f.stock_after})`)
      .join(', ');
    summary += `\nWarning: ${warnings}`;
  }

  // Append sale_id for undo reference
  summary += `\n(sale_id: ${result.sale_id})`;

  return {
    success: true,
    summary,
    data: { sale_id: result.sale_id, stock_flags: stockFlags },
  };
}

// ---------------------------------------------------------------------------
// Exported definition for the registry
// ---------------------------------------------------------------------------

export const recordSaleDefinition: ToolDefinition = {
  name: 'record_sale',
  description:
    'Record a sale with items, total amount, and optional khata number. ' +
    'Use this when the shopkeeper mentions selling items. ' +
    'The stated total amount is always the source of truth — do not compute it from prices.',
  parameters,
  riskTier: 'commit_undo',
  handler,
};
