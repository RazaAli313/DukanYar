import { getUserProfile } from "../../actions/auth";
import { DashboardView } from "@/components/dashboard/DashboardView";

export default async function DashboardPage() {
  const profile = await getUserProfile();
  return <DashboardView shopName={profile?.shops?.name ?? "Meri Dukan"} />;
}
