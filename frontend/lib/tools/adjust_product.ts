/**
 * adjust_product tool (CATLG-2).
 *
 * Restock, correct stock count, or update price for an existing product.
 * Resolves product_name via the catalog service — never creates a new
 * product (that's CATLG-1, cut from MVP).
 */

import { resolveProduct } from '../sales/catalogService';
import type { ToolDefinition, ToolContext, ToolResult } from './registry';

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const parameters = {
  type: 'object',
  properties: {
    product_name: {
      type: 'string',
      description: 'Name or alias of the existing product to adjust',
    },
    adjustment_type: {
      type: 'string',
      enum: ['restock_add', 'restock_set', 'price_update'],
      description:
        'restock_add = add N units to current stock ("24 aur aa gayi"), ' +
        'restock_set = set stock to exact count ("ab 50 bache hain"), ' +
        'price_update = change the sale price ("ab 60 ka ho gaya")',
    },
    value: {
      type: 'number',
      description: 'The numeric value for the adjustment',
      minimum: 0,
    },
  },
  required: ['product_name', 'adjustment_type', 'value'],
};

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

async function handler(
  params: Record<string, unknown>,
  ctx: ToolContext,
): Promise<ToolResult> {
  const { supabase, shopId, userId } = ctx;
  const productName = params.product_name as string;
  const adjustmentType = params.adjustment_type as string;
  const value = Number(params.value);

  // 1. Resolve to existing product (never create new)
  const result = await resolveProduct(supabase, productName);
  if (!result.match) {
    if (result.candidates.length > 0) {
      const names = result.candidates.map((c) => c.name).join(', ');
      return {
        success: false,
        summary: `Did you mean one of these? ${names}. Please specify which product to adjust.`,
      };
    }
    return {
      success: false,
      summary: `Product "${productName}" not found in your catalog. Cannot adjust a product that doesn't exist yet.`,
    };
  }

  // 2. Call the process_stock_adjustment RPC
  const { data: rpcResult, error: rpcError } = await supabase.rpc(
    'process_stock_adjustment',
    {
      p_shop_id: shopId,
      p_product_id: result.match.id,
      p_adjustment_type: adjustmentType,
      p_value: value,
      p_created_by: userId,
    },
  );

  if (rpcError) {
    return {
      success: false,
      summary: `Adjustment failed: ${rpcError.message}`,
    };
  }

  // 3. Build before/after summary (chat text, no card)
  const r = rpcResult as Record<string, unknown>;

  let summary: string;
  switch (adjustmentType) {
    case 'restock_add':
      summary = `Restocked ${r.name}: +${value} units (${r.old_stock} → ${r.new_stock} in stock).`;
      break;
    case 'restock_set':
      summary = `Stock corrected for ${r.name}: set to ${r.new_stock} (was ${r.old_stock}).`;
      break;
    case 'price_update':
      summary = `Price updated for ${r.name}: Rs ${r.old_price} → Rs ${r.new_price}.`;
      break;
    default:
      summary = `Adjustment applied to ${r.name}.`;
  }

  return {
    success: true,
    summary,
    data: rpcResult as Record<string, unknown>,
  };
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

export const adjustProductDefinition: ToolDefinition = {
  name: 'adjust_product',
  description:
    'Restock, correct stock count, or update price for an existing product. ' +
    'Use this when the shopkeeper says things like "Coke ki 24 bottle aur aa gayi" ' +
    '(restock), "Coke ab 60 ka" (price update), or "Coke ke 50 bache hain" (stock correction). ' +
    'Never creates a new product — only adjusts existing ones.',
  parameters,
  riskTier: 'commit_undo',
  handler,
};
