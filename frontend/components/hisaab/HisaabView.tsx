"use client";

import { useEffect, useState } from "react";
import { api, type DashboardToday, type LedgerTxn } from "@/lib/api";
import { pkr, cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function HisaabView() {
  const [today, setToday] = useState<DashboardToday | null>(null);
  const [txns, setTxns] = useState<LedgerTxn[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.dashboardToday(), api.ledger("all")])
      .then(([d, l]) => {
        setToday(d);
        setTxns(l.transactions);
      })
      .catch((e) => setError(e.message));
  }, []);

  const week = summarise(txns ?? [], 7);
  const month = summarise(txns ?? [], 30);

  return (
    <div className="space-y-5 px-4 py-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold tracking-tight">Hisaab</h1>
        <p className="text-sm text-muted-foreground">Sale, munafa aur udhaar ka khulasa</p>
      </div>

      {error && (
        <Card className="border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error}
        </Card>
      )}

      <Card className="gap-0 overflow-hidden p-0">
        <div className="p-5">
          <p className="text-sm font-medium text-muted-foreground">Aaj ka munafa</p>
          {today ? (
            <p className="amount mt-1 font-serif text-3xl font-semibold text-primary">
              {pkr(today.totals.profit)}
            </p>
          ) : (
            <Skeleton className="mt-2 h-9 w-32" />
          )}
        </div>
        <div className="grid grid-cols-2 divide-x divide-border border-t border-border">
          <Metric label="Aaj ki sale" value={today && pkr(today.totals.sale)} />
          <Metric
            label="Kul udhaar baqaya"
            value={today && pkr(today.totals.outstanding_udhaar)}
            tone={today && today.totals.outstanding_udhaar > 0 ? "debit" : undefined}
          />
        </div>
      </Card>

      <Period title="Is hafte" data={week} loading={!txns} />
      <Period title="Is mahine" data={month} loading={!txns} />
    </div>
  );
}

function Period({
  title,
  data,
  loading,
}: {
  title: string;
  data: { sale: number; kharcha: number; udhaar: number; wasooli: number };
  loading: boolean;
}) {
  return (
    <div>
      <p className="mb-1.5 px-1 text-sm font-semibold">{title}</p>
      <Card className="grid grid-cols-2 gap-0 divide-x divide-y divide-border p-0">
        <Metric label="Sale" value={loading ? null : pkr(data.sale)} />
        <Metric label="Kharcha" value={loading ? null : pkr(data.kharcha)} tone="debit" />
        <Metric label="Udhaar diya" value={loading ? null : pkr(data.udhaar)} />
        <Metric label="Wasooli" value={loading ? null : pkr(data.wasooli)} tone="credit" />
      </Card>
    </div>
  );
}

function Metric({
  label,
  value,
  tone,
}: {
  label: string;
  value: string | null | undefined;
  tone?: "credit" | "debit";
}) {
  return (
    <div className="p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      {value ? (
        <p
          className={cn(
            "amount mt-0.5 text-sm font-semibold",
            tone === "credit" && "text-credit",
            tone === "debit" && "text-debit",
          )}
        >
          {value}
        </p>
      ) : (
        <Skeleton className="mt-1 h-4 w-16" />
      )}
    </div>
  );
}

function summarise(rows: LedgerTxn[], days: number) {
  const since = Date.now() - days * 864e5;
  const acc = { sale: 0, kharcha: 0, udhaar: 0, wasooli: 0 };
  for (const r of rows) {
    if (new Date(r.at).getTime() < since) continue;
    if (r.kind === "sale") acc.sale += r.amount;
    else if (r.kind === "expense") acc.kharcha += r.amount;
    else if (r.kind === "udhaar") acc.udhaar += r.amount;
    else if (r.kind === "payment") acc.wasooli += r.amount;
  }
  return acc;
}
