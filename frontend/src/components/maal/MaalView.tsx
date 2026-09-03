"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, type Product } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function MaalView() {
  const params = useSearchParams();
  const [lowOnly, setLowOnly] = useState(params.get("low") === "1");
  const [products, setProducts] = useState<Product[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .products()
      .then((r) => setProducts(r.products))
      .catch((e) => setError(e.message));
  }, []);

  const shown = (products ?? []).filter((p) => !lowOnly || p.stock <= 5);

  return (
    <div className="space-y-4 px-4 py-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-serif text-2xl font-semibold tracking-tight">Maal</h1>
          <p className="text-sm text-muted-foreground">Dukaan ka stock aur rate</p>
        </div>
        <button
          onClick={() => setLowOnly((v) => !v)}
          className={cn(
            "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
            lowOnly
              ? "border-caution-foreground/30 bg-caution/50 text-caution-foreground"
              : "border-border text-muted-foreground",
          )}
        >
          Kam stock
        </button>
      </div>

      {error && (
        <Card className="border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error}
        </Card>
      )}

      {!products && (
        <Card className="space-y-3 p-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </Card>
      )}

      {products && shown.length === 0 && (
        <Card className="p-8 text-center text-sm text-muted-foreground">
          {lowOnly ? "Koi cheez kam nahi." : "Abhi koi product nahi."}
        </Card>
      )}

      {shown.length > 0 && (
        <Card className="gap-0 divide-y divide-border p-0">
          {shown.map((p) => {
            const low = p.stock <= 5;
            return (
              <div key={p.id} className="flex items-center gap-3 px-4 py-3">
                <p className="min-w-0 flex-1 truncate text-sm font-medium">{p.name}</p>
                <span
                  className={cn(
                    "amount rounded-md px-2.5 py-1 text-xs font-semibold",
                    low
                      ? "bg-caution/60 text-caution-foreground"
                      : "bg-secondary text-secondary-foreground",
                  )}
                >
                  {p.stock} {low ? "bache" : "stock"}
                </span>
              </div>
            );
          })}
        </Card>
      )}

      <p className="px-1 text-xs text-muted-foreground">
        Naya maal aaya? Poocho screen se bol kar batayein — restock jald aa raha hai.
      </p>
    </div>
  );
}
