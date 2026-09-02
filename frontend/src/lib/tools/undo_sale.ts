/**
 * undo_sale tool (SALE-4, TOOL-3 commit_undo tier).
 *
 * The model calls this when the shopkeeper says "undo" or "woh wali
 * sale hatado".  The handler invokes the undo_sale RPC which atomically
 * restores stock and offsets any udhaar ledger entry.
 */

import type { ToolDefinition, ToolContext, ToolResult } from './registry';

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const parameters = {
  type: 'object',
  properties: {
    sale_id: {
      type: 'string',
      format: 'uuid',
      description: 'The sale_id to undo (returned by record_sale)',
    },
  },
  required: ['sale_id'],
};

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

async function handler(
  params: Record<string, unknown>,
  ctx: ToolContext,
): Promise<ToolResult> {
  const { supabase, shopId } = ctx;
  const saleId = params.sale_id as string;

  if (!saleId) {
    return { success: false, summary: 'No sale_id provided.' };
  }

  // 1. Call the undo_sale RPC
  const { data: rpcResult, error: rpcError } = await supabase.rpc('undo_sale', {
    p_sale_id: saleId,
    p_shop_id: shopId,
  });

  if (rpcError) {
    return {
      success: false,
      summary: `Undo failed: ${rpcError.message}`,
    };
  }

  // 2. Mark the original tool_calls record as 'undone'
  const { data: originalTc } = await supabase
    .from('tool_calls')
    .select('id')
    .eq('tool_name', 'record_sale')
    .eq('status', 'committed')
    .contains('response', { sale_id: saleId })
    .limit(1)
    .maybeSingle();

  if (originalTc) {
    await supabase
      .from('tool_calls')
      .update({ status: 'undone', resolved_at: new Date().toISOString() })
      .eq('id', originalTc.id);
  }

  // 3. Build summary
  const result = rpcResult as Record<string, unknown>;
  const restored = (result.restored ?? []) as Array<Record<string, unknown>>;

  const restoredLines = restored
    .map((r) => `  ${r.name}: +${r.quantity_restored} (now ${r.stock_after} in stock)`)
    .join('\n');

  const summary = `Sale ${saleId} undone. Stock restored:\n${restoredLines}`;

  return {
    success: true,
    summary,
    data: { sale_id: saleId, undone: true },
  };
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

export const undoSaleDefinition: ToolDefinition = {
  name: 'undo_sale',
  description:
    'Undo a previously recorded sale and restore stock. ' +
    'Use this when the shopkeeper says "undo", "cancel that sale", or "woh wali sale hatado".',
  parameters,
  riskTier: 'commit_undo',
  handler,
};
