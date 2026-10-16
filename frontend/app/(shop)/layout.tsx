import { redirect } from "next/navigation";
import Link from "next/link";
import { getUserProfile, signOut } from "../actions/auth";
import { BottomNav } from "@/components/shell/BottomNav";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";

export default async function ShopLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const profile = await getUserProfile();
  if (!profile) redirect("/login");

  const shopName = profile.shops?.name ?? "Meri Dukan";

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <header className="sticky top-0 z-20 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3">
          <Link href="/app" className="flex items-baseline gap-2">
            <span className="font-serif text-lg font-semibold tracking-tight text-primary">
              DukanYar
            </span>
            <span className="text-xs text-muted-foreground">{shopName}</span>
          </Link>
          <form action={signOut}>
            <Button
              type="submit"
              variant="ghost"
              size="icon-sm"
              aria-label="Sign out"
              className="text-muted-foreground"
            >
              <LogOut className="size-4" />
            </Button>
          </form>
        </div>
      </header>

      <main className="mx-auto w-full max-w-2xl flex-1">{children}</main>

      <BottomNav />
    </div>
  );
}
