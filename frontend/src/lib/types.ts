export type Sender = "user" | "assistant";
export type MessageStatus = "pending" | "streaming" | "complete" | "error";
/** How a user message entered the conversation (VOICE-2). */
export type Channel = "text" | "voice";

export interface Message {
  id: string;
  sender: Sender;
  text: string;
  status: MessageStatus;
  createdAt: Date;
  /** Set on user messages; defaults to "text" when absent. */
  channel?: Channel;
}
