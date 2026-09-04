"use client";

import { Check, TriangleAlert, Loader2 } from "lucide-react";
import type { ActionCard } from "@/lib/chatApi";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface Props {
  card: ActionCard;
  busy?: boolean;
  onConfirm?: () => void;
  onCancel?: () => void;
}

export function ConfirmationCard({ card, busy, onConfirm, onCancel }: Props) {
  const recorded = card.status === "recorded";
  const failed = card.status === "failed";

  return (
    <Card
      className={
        "gap-0 overflow-hidden p-0 " +
        (recorded ? "border-primary/40" : failed ? "border-destructive/40" : "border-border")
      }
    >
      <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
        <span className="text-sm font-semibold">{card.title}</span>
        {recorded && (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-primary">
            <Check className="size-3.5" /> Record ho gaya
          </span>
        )}
      </div>

      <div className="divide-y divide-border">
        {card.lines.map((ln, i) => (
          <div key={i} className="flex items-center justify-between px-4 py-2.5 text-sm">
            <span className="flex items-center gap-1.5">
              {ln.flag && <TriangleAlert className="size-3.5 text-destructive" />}
              {ln.label}
            </span>
            {ln.value && (
              <span
                className={
                  "amount " + (ln.flag ? "text-destructive" : "text-muted-foreground")
                }
              >
                {ln.value}
              </span>
            )}
          </div>
        ))}
      </div>

      {card.total && (
        <div className="flex items-center justify-between border-t border-border bg-secondary/40 px-4 py-3">
          <span className="text-sm font-semibold">Total</span>
          <span className="amount font-serif text-lg font-semibold">{card.total}</span>
        </div>
      )}

      {card.note && (
        <p className="border-t border-border bg-caution/40 px-4 py-2.5 text-xs text-caution-foreground">
          {card.note}
        </p>
      )}

      {!recorded && !failed && (
        <div className="flex gap-2 border-t border-border p-3">
          <Button variant="outline" className="flex-1" onClick={onCancel} disabled={busy}>
            Theek karein
          </Button>
          <Button className="flex-1" onClick={onConfirm} disabled={busy}>
            {busy ? <Loader2 className="size-4 animate-spin" /> : "Haan, save karein"}
          </Button>
        </div>
      )}
    </Card>
  );
}
