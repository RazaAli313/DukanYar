import Link from "next/link";
import { redirect } from "next/navigation";
import { Mic, BrainCircuit, BookText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getUserProfile } from "./actions/auth";

export default async function LandingPage() {
  const profile = await getUserProfile();
  if (profile) {
    redirect("/app");
  }

  return (
    <div className="min-h-dvh bg-background text-foreground">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
        <span className="font-serif text-xl font-semibold text-primary">DukanYar</span>
        <Button asChild variant="outline" size="sm">
          <Link href="/login">Login</Link>
        </Button>
      </header>

      <main className="mx-auto max-w-5xl px-6">
        <section className="grid items-center gap-10 py-12 md:grid-cols-2 md:py-20">
          <div>
            <h1 className="font-serif text-4xl font-semibold leading-[1.1] tracking-tight md:text-5xl">
              Aap dukan sambhalein,
              <br />
              <span className="text-primary">hisaab hum.</span>
            </h1>
            <p className="mt-5 max-w-md text-[0.95rem] leading-relaxed text-muted-foreground">
              Zyada tar kiryana dukaandaar hisaab nahi rakhte — likhna dheema hai
              aur software seekhna mushkil. Aap bas bolein, DukanYar sunta hai aur
              khata rakh deta hai.
            </p>
            <div className="mt-7 flex gap-3">
              <Button asChild size="lg">
                <Link href="/signup">Dukaan shuru karein</Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/login">Wapas aayein</Link>
              </Button>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Kaise kaam karta hai
            </p>
            <ol className="mt-4 space-y-4">
              <Step icon={Mic} title="Bolo" body='"Bhai 2 coke aur 1 lays becha abhi"' />
              <Step
                icon={BrainCircuit}
                title="Munshi samajhta hai"
                body="AI aapki baat se items, ginti aur amount nikaalta hai."
              />
              <Step
                icon={BookText}
                title="Khata update ho gaya"
                body="Sab kuch aapke khate mein automatically save ho jaata hai."
              />
            </ol>
          </div>
        </section>
      </main>

      <footer className="mx-auto max-w-5xl px-6 py-10 text-xs text-muted-foreground">
        DukanYar — voice-first hisaab-kitaab for Pakistani kiryana shopkeepers.
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
