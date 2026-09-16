/**
 * Shared type contracts for tool definitions (TOOL-1).
 *
 * These interfaces are consumed by SALE and CATLG tool files to type their
 * exports. The ToolRegistry class, singleton instance, and orchestration
 * loop are owned by the TOOL epic team — do not re-add them here.
 */

export type RiskTier = 'commit_undo' | 'approval_required';

export interface ToolContext {
  /** Authenticated user's Supabase client */
  supabase: import('@supabase/supabase-js').SupabaseClient;
  /** Shop the current user belongs to */
  shopId: string;
  /** User ID from auth */
  userId: string;
  /** Conversation this call belongs to (for tool_calls logging) */
  conversationId: string;
  /** Message that triggered this tool call */
  messageId: string;
}

export interface ToolResult {
  success: boolean;
  /** Human-readable summary appended to the chat reply */
  summary: string;
  /** Structured payload the orchestrator may feed back to the model */
  data?: Record<string, unknown>;
}

export interface ToolDefinition {
  /** Unique name — the model uses this to invoke the tool */
  name: string;
  /** Natural-language description for the model's system prompt */
  description: string;
  /** JSON Schema the model fills when calling the tool */
  parameters: object;
  /** How the framework handles confirmation (TOOL-3 risk tiers) */
  riskTier: RiskTier;
  /** Async handler — receives parsed params and the request context */
  handler: (params: Record<string, unknown>, ctx: ToolContext) => Promise<ToolResult>;
}
