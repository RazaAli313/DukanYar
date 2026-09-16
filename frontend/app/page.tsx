import Link from "next/link";
import { redirect } from "next/navigation";
import {
  Mic,
  BrainCircuit,
  BookText,
  ShoppingCart,
  BarChart3,
  BookOpen,
  ArrowRight,
  Shield,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { getUserProfile } from "./actions/auth";

export default async function LandingPage() {
  const profile = await getUserProfile();
  if (profile) {
    redirect("/app");
  }

  return (
    <div className="min-h-dvh bg-background text-foreground">
      {/* ── Header ── */}
      <header className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5 border-b border-border/50">
        <span className="font-serif text-2xl font-bold text-primary">DukanYar</span>
        <div className="flex items-center gap-3">
          <Button asChild variant="outline" size="sm">
            <Link href="/login">Login</Link>
          </Button>
          <Button asChild size="sm">
            <Link href="/signup">Dukaan Shuru Karein</Link>
          </Button>
        </div>
      </header>

      {/* ── Hero Section ── */}
      <main className="mx-auto max-w-5xl px-6">
        <section className="grid items-center gap-10 py-12 md:grid-cols-2 md:py-20">
          <div>
            <div className="inline-flex items-center gap-1.5 rounded-full bg-accent px-3 py-1 text-xs font-semibold text-accent-foreground border border-primary/20 mb-4">
              <span className="relative flex h-2 w-2">
                <span className="absolute inset-0 animate-ping rounded-full bg-primary opacity-75" />
                <span className="relative h-2 w-2 rounded-full bg-primary" />
              </span>
              Voice-First Shop Management
            </div>

            <h1 className="font-serif text-4xl font-semibold leading-[1.15] tracking-tight md:text-5xl">
              Aap dukan sambhalein,
              <br />
              <span className="text-primary">hisaab hum.</span>
            </h1>
            <p className="mt-5 max-w-md text-[0.95rem] leading-relaxed text-muted-foreground">
              Zyada tar kiryana dukaandaar hisaab nahi rakhte — likhna dheema hai
              aur software seekhna mushkil. Aap bas bolein, DukanYar sunta hai aur
              khata rakh deta hai.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link href="/signup">
                  Dukaan shuru karein
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/login">Wapas aayein</Link>
              </Button>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Kaise kaam karta hai (3 Asaan Steps)
            </p>
            <ol className="mt-4 space-y-4">
              <Step
                icon={Mic}
                title="1. Bolo"
                body='"Bhai 2 coke aur 1 lays becha abhi 480 rupay"'
              />
              <Step
                icon={BrainCircuit}
                title="2. Munshi samajhta hai"
                body="AI aapki baat se items, ginti aur amount foran nikaalta hai."
              />
              <Step
                icon={BookText}
                title="3. Khata update ho gaya"
                body="Stock aur hisaab aapke khate mein automatically save ho jaata hai."
              />
            </ol>
          </div>
        </section>

        {/* ── Feature Highlights ── */}
        <section className="py-12 border-t border-border/50">
          <div className="text-center mb-10">
            <h2 className="font-serif text-2xl font-bold tracking-tight md:text-3xl">
              Dukan Ka Mukammal Nizam
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Aapki zubaan mein, aapki dukan ke liye
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <FeatureCard
              icon={Mic}
              title="Awaaz Se Sale"
              description="Urdu ya English mein bolein, baghair typing ke sale likhein."
            />
            <FeatureCard
              icon={ShoppingCart}
              title="Smart Inventory"
              description="Sale ke sath stock foran kam hota hai aur kam hone par alert milta hai."
            />
            <FeatureCard
              icon={BookOpen}
              title="Customer Khata"
              description="Kis customer ke kitne udhaar hain, ek awaaz par pata lagayein."
            />
            <FeatureCard
              icon={BarChart3}
              title="Rozana Munafa"
              description="Din ke aakhir mein kul sale aur munafay ka seedha hisaab."
            />
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-border/50 mt-12 py-8">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 px-6 sm:flex-row text-xs text-muted-foreground">
          <p>© 2026 DukanYar — Voice-first hisaab-kitaab for Pakistani shopkeepers.</p>
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1">
              <Zap className="h-3.5 w-3.5 text-primary" /> Fast
            </span>
            <span className="inline-flex items-center gap-1">
              <Shield className="h-3.5 w-3.5 text-primary" /> Secure
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

function Step({
  icon: Icon,
  title,
  body,
}: {
  icon: typeof Mic;
  title: string;
  body: string;
}) {
  return (
    <li className="flex gap-3">
      <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
        <Icon className="size-4" />
      </span>
      <div>
        <p className="text-sm font-semibold">{title}</p>
        <p className="text-sm text-muted-foreground">{body}</p>
      </div>
    </li>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof Mic;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-sm transition-all hover:border-primary/40">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground mb-3">
        <Icon className="h-5 w-5" />
      </div>
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
        {description}
      </p>
    </div>
  );
}
