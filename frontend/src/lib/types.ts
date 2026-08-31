export type Sender = "user" | "assistant";
export type MessageStatus = "pending" | "complete" | "error";

export interface Message {
  id: string;
  sender: Sender;
  text: string;
  status: MessageStatus;
  createdAt: Date;
}
