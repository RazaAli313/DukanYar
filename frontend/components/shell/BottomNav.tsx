"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, BookText, Package, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { href: "/app", label: "Ghar", icon: Home },
  { href: "/khata", label: "Khata", icon: BookText },
  { href: "/maal", label: "Maal", icon: Package },
  { href: "/hisaab", label: "Hisaab", icon: BarChart3 },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="sticky bottom-0 z-20 border-t border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
      <div className="mx-auto flex max-w-2xl items-stretch justify-around">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex flex-1 flex-col items-center gap-1 py-2.5 text-[0.7rem] font-medium transition-colors",
                active ? "text-primary" : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Icon className="size-5" strokeWidth={active ? 2.4 : 1.8} />
              {label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
