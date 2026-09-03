"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShoppingCart,
  Users,
  ReceiptText,
  Sparkles,
  TriangleAlert,
  ArrowRight,
} from "lucide-react";
import { api, type DashboardToday } from "@/lib/api";
import { pkr } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const actions = [
  { href: "/record/sale", label: "Sale", sub: "Naya sale add karein", icon: ShoppingCart, primary: true },
  { href: "/record/udhaar", label: "Udhaar", sub: "Udhaar entry karein", icon: Users },
  { href: "/record/kharcha", label: "Kharcha", sub: "Dukaan ka kharcha", icon: ReceiptText },
  { href: "/record/ask", label: "Poocho", sub: "Kisi bhi sawal ka jawab", icon: Sparkles },
];

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Assalam u Alaikum";
  if (h < 17) return "Assalam u Alaikum";
  return "Assalam u Alaikum";
}

export function DashboardView({ shopName }: { shopName: string }) {
  const [data, setData] = useState<DashboardToday | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.dashboardToday().then(setData).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-6 px-4 py-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold tracking-tight">
          {greeting()}
        </h1>
        <p className="text-sm text-muted-foreground">
          {new Date().toLocaleDateString("en-PK", {
            weekday: "long",
            day: "numeric",
            month: "long",
          })}{" "}
          · {shopName}
        </p>
      </div>

      {error && (
        <Card className="border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error}
        </Card>
      )}

      {/* ── Aaj ── */}
      <Card className="gap-0 overflow-hidden p-0">
        <div className="p-5">
          <div className="flex items-baseline justify-between">
            <span className="text-sm font-medium text-muted-foreground">
              Aaj ka Munafa
            </span>
          </div>
          {data ? (
            <p className="amount mt-1 font-serif text-4xl font-semibold text-primary">
              {pkr(data.totals.profit)}
            </p>
          ) : (
            <Skeleton className="mt-2 h-10 w-40" />
          )}
        </div>
        <div className="grid grid-cols-3 divide-x divide-border border-t border-border text-center">
          <Stat label="Total Sale" value={data && pkr(data.totals.sale)} />
          <Stat label="Udhaar diya" value={data && pkr(data.totals.udhaar_today)} />
          <Stat label="Kul Kharcha" value={data && pkr(data.totals.kharcha)} />
        </div>
      </Card>

      {/* ── Low stock ── */}
      {data && data.low_stock.length > 0 && (
        <Link href="/maal?low=1">
          <Card className="flex-row items-center gap-3 border-caution/50 bg-caution/40 p-4 text-caution-foreground">
            <TriangleAlert className="size-5 shrink-0" />
            <div className="flex-1 text-sm">
              <p className="font-medium">
                {data.low_stock.length} cheezein kam ho rahi hain
              </p>
              <p className="text-caution-foreground/80">
                {data.low_stock.slice(0, 3).map((p) => `${p.name} (${p.stock})`).join(" · ")}
              </p>
            </div>
            <ArrowRight className="size-4 shrink-0" />
          </Card>
        </Link>
      )}

      {/* ── Actions ── */}
      <div className="grid grid-cols-2 gap-3">
        {actions.map(({ href, label, sub, icon: Icon, primary }) => (
          <Link key={href} href={href}>
            <Card
              className={
                "h-full gap-2 p-4 transition-colors " +
                (primary
                  ? "border-primary bg-primary text-primary-foreground hover:bg-primary/95"
                  : "hover:bg-accent/50")
              }
            >
              <Icon className="size-6" strokeWidth={1.8} />
              <div>
                <p className="font-semibold">{label}</p>
                <p
                  className={
                    "text-xs " +
                    (primary ? "text-primary-foreground/80" : "text-muted-foreground")
                  }
                >
                  {sub}
                </p>
              </div>
            </Card>
          </Link>
        ))}
      </div>

      {/* ── Recent ── */}
      <div>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-semibold">Recent Entries</h2>
          <Link href="/khata" className="text-xs font-medium text-primary">
            Sab dekhein
          </Link>
        </div>
        <Card className="gap-0 divide-y divide-border p-0">
          {!data && (
            <div className="space-y-3 p-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          )}
          {data && data.recent.length === 0 && (
            <p className="p-5 text-center text-sm text-muted-foreground">
              Aaj abhi tak koi entry nahi.
            </p>
          )}
          {data?.recent.map((r, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-3">
              <span className="flex-1 truncate text-sm">{r.label}</span>
              <span
                className={
                  "amount text-sm font-medium " +
                  (r.kind === "expense" ? "text-debit" : "text-foreground")
                }
              >
                {pkr(r.amount)}
              </span>
              <span className="w-16 text-right text-xs text-muted-foreground">
                {r.tag}
              </span>
              <span className="w-14 text-right text-xs text-muted-foreground">
                {new Date(r.at).toLocaleTimeString("en-PK", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="px-2 py-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      {value ? (
        <p className="amount mt-0.5 text-sm font-semibold">{value}</p>
      ) : (
        <Skeleton className="mx-auto mt-1 h-4 w-16" />
      )}
    </div>
  );
}
