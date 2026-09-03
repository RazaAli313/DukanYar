import { Suspense } from "react";
import { MaalView } from "@/components/maal/MaalView";
export default function MaalPage() {
  return (
    <Suspense fallback={null}>
      <MaalView />
    </Suspense>
  );
}
