"use client";

import { useEffect, useState } from "react";
import { api, type LedgerTxn } from "@/lib/api";
import { pkr } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const tabs = [
  { key: "all", label: "Sab" },
  { key: "sale", label: "Sale" },
  { key: "udhaar", label: "Udhaar" },
  { key: "kharcha", label: "Kharcha" },
] as const;

type TabKey = (typeof tabs)[number]["key"];

export function KhataView() {
  const [tab, setTab] = useState<TabKey>("all");
  const [rows, setRows] = useState<LedgerTxn[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRows(null);
    api
      .ledger(tab)
      .then((r) => setRows(r.transactions))
      .catch((e) => setError(e.message));
  }, [tab]);

  const grouped = groupByDay(rows ?? []);

  return (
    <div className="space-y-4 px-4 py-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold tracking-tight">Khata</h1>
        <p className="text-sm text-muted-foreground">Aapke tamam len-den ka record</p>
      </div>

      <div className="flex gap-1 rounded-lg bg-secondary p-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "flex-1 rounded-md py-1.5 text-sm font-medium transition-colors",
              tab === t.key
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && (
        <Card className="border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error}
        </Card>
      )}

      {!rows && (
        <Card className="space-y-3 p-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-3/4" />
        </Card>
      )}

      {rows && rows.length === 0 && (
        <Card className="p-8 text-center text-sm text-muted-foreground">
          Is category mein abhi koi entry nahi.
        </Card>
      )}

      {grouped.map(([day, items]) => (
        <div key={day}>
          <p className="mb-1.5 px-1 text-xs font-medium text-muted-foreground">{day}</p>
          <Card className="gap-0 divide-y divide-border p-0">
            {items.map((r, i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm">{r.detail}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(r.at).toLocaleTimeString("en-PK", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                    {" · "}
                    {r.qism}
                  </p>
                </div>
                <span
                  className={cn(
                    "amount text-sm font-semibold",
                    r.direction === "out" ? "text-debit" : "text-credit",
                  )}
                >
                  {r.direction === "out" ? "− " : ""}
                  {pkr(r.amount)}
                </span>
              </div>
            ))}
          </Card>
        </div>
      ))}
    </div>
  );
}

function groupByDay(rows: LedgerTxn[]): [string, LedgerTxn[]][] {
  const map = new Map<string, LedgerTxn[]>();
  for (const r of rows) {
    const d = new Date(r.at);
    const key = isToday(d)
      ? "Aaj"
      : d.toLocaleDateString("en-PK", { day: "numeric", month: "short", year: "numeric" });
    (map.get(key) ?? map.set(key, []).get(key)!).push(r);
  }
  return [...map.entries()];
}

function isToday(d: Date) {
  const n = new Date();
  return (
    d.getDate() === n.getDate() &&
    d.getMonth() === n.getMonth() &&
    d.getFullYear() === n.getFullYear()
  );
}
