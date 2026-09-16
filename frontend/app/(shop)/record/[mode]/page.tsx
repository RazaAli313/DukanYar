import { notFound } from "next/navigation";
import { ConversationScreen } from "@/components/conversation/ConversationScreen";
import { isMode } from "@/components/conversation/modes";

export default async function RecordPage({
  params,
}: {
  params: Promise<{ mode: string }>;
}) {
  const { mode } = await params;
  if (!isMode(mode)) notFound();
  return <ConversationScreen mode={mode} />;
}
