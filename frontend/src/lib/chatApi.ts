/**
 * Chat API layer — TEXT-1 stub implementation.
 *
 * TEXT-2 swap: replace the body of `sendMessage` with a real
 * POST /conversations/{id}/messages call (streaming or complete).
 * The component layer does NOT need to change.
 */

const CANNED_REPLIES = [
  "Jee bilkul, main samajh gaya. Aur kuch poochna hai?",
  "Theek hai, main note kar raha hoon. Koi aur sawaal?",
  "Haan ji, zaroor. Iske baare mein aur detail chahiye?",
  "Bilkul, ho jayega. Aur bataiye kya madad karoon?",
  "Jee, samajh aa gaya. Kuch aur help chahiye aapko?",
];

/**
 * Send a user message and receive an assistant reply.
 * Currently returns a stub reply after a simulated delay.
 */
export async function sendMessage(userMessage: string): Promise<string> {
  // ── STUB (remove in TEXT-2) ──────────────────────────────
  await new Promise((r) => setTimeout(r, 1200));
  const idx = Math.floor(Math.random() * CANNED_REPLIES.length);
  return CANNED_REPLIES[idx];
  // ── END STUB ─────────────────────────────────────────────
}
