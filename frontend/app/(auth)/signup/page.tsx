"use client";

import { useState } from "react";
import Link from "next/link";
import { signUp } from "../../actions/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function SignupPage() {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(formData: FormData) {
    setLoading(true);
    setError(null);
    const res = await signUp(formData);
    if (res?.error) {
      setError(res.error);
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <Link href="/" className="font-serif text-2xl font-semibold text-primary">
            DukanYar
          </Link>
          <p className="mt-1 text-sm text-muted-foreground">Aapki awaaz, aapka khata</p>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <h1 className="font-serif text-xl font-semibold">Dukaan shuru karein</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Bas teen cheezein, aur aap tayyar hain.
          </p>

          {error && (
            <div className="mt-4 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <form action={handleSubmit} className="mt-5 space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="shopName">Dukaan ka naam</Label>
              <Input
                id="shopName"
                name="shopName"
                type="text"
                required
                placeholder="Bismillah Kiryana Store"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" name="email" type="email" required placeholder="dukaan@misaal.com" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input id="password" name="password" type="password" required placeholder="••••••••" />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Ban rahi hai…" : "Dukaan banayein"}
            </Button>
          </form>
        </div>

        <p className="text-center text-sm text-muted-foreground">
          Pehle se account hai?{" "}
          <Link href="/login" className="font-medium text-primary">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
