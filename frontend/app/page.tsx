<<<<<<< HEAD
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
=======
import Link from 'next/link'
import {
  Mic,
  ShoppingCart,
  BarChart3,
  BookOpen,
  ArrowRight,
  Zap,
  Shield,
  Globe,
} from 'lucide-react'

const features = [
  {
    icon: Mic,
    title: 'Voice-First Sales',
    description:
      'Record sales, manage inventory, and track khata — all by speaking in Urdu or English. No typing needed.',
  },
  {
    icon: ShoppingCart,
    title: 'Fast Checkout',
    description:
      'Process sales in seconds with smart product resolution. Say it once, DukanYar handles the rest.',
  },
  {
    icon: BarChart3,
    title: 'Real-Time Inventory',
    description:
      'Stock levels update instantly with every sale. Get warned when items run low — before they run out.',
  },
  {
    icon: BookOpen,
    title: 'Khata Tracker',
    description:
      'Track udhaar (credit) sales per customer. Know exactly who owes what, always up to date.',
  },
]

const steps = [
  {
    number: '01',
    title: 'Register Your Shop',
    description: 'Create an account and set up your dukan in under a minute.',
  },
  {
    number: '02',
    title: 'Speak to Manage',
    description:
      'Say "2 Coca-Cola, cash" or "Ali ka khata 500" — DukanYar understands Roman Urdu.',
  },
  {
    number: '03',
    title: 'Track Everything',
    description:
      'Sales, stock, and customer balances update in real time. Review anytime.',
  },
]
>>>>>>> origin/feat/sale-catlg-mvp

  return (
<<<<<<< HEAD
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
=======
    <div className="min-h-screen bg-white">
      {/* ── Navbar ── */}
      <nav className="sticky top-0 z-50 border-b border-gray-100 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <span className="text-xl font-bold text-gray-900">
            Dukan<span className="text-brand-600">Yar</span>
          </span>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative overflow-hidden px-6 pb-20 pt-24 sm:pt-32">
        <div className="pointer-events-none absolute inset-0 -z-10 bg-gradient-to-b from-brand-50/60 via-white to-white" />
        <div className="mx-auto max-w-4xl text-center">
          <span className="inline-block rounded-full bg-brand-50 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-brand-700">
            Voice-First POS for Pakistani Shops
          </span>
          <h1 className="mt-8 text-5xl font-extrabold leading-tight tracking-tight text-gray-900 sm:text-6xl">
            Run Your Dukan
            <br />
            <span className="bg-gradient-to-r from-brand-600 to-emerald-500 bg-clip-text text-transparent">
              With Just Your Voice
            </span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-gray-600">
            DukanYar is a voice-first shop management platform. Record sales,
            track inventory, and manage customer khata — all hands-free, in
            Urdu or English.
          </p>
          <div className="mt-10 flex flex-col justify-center gap-4 sm:flex-row">
            <Link
              href="/signup"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-8 py-3.5 text-base font-semibold text-white shadow-md shadow-brand-600/25 transition-all hover:bg-brand-700 hover:shadow-lg"
            >
              Register Your Shop
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-xl border border-gray-300 bg-white px-8 py-3.5 text-base font-semibold text-gray-700 transition-colors hover:bg-gray-50"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="bg-gray-50/70 px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Everything Your Dukan Needs
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-gray-600">
              Built for the way Pakistani shopkeepers actually work — fast,
              conversational, and always on the move.
            </p>
          </div>
          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((f) => (
              <div
                key={f.title}
                className="group rounded-2xl border border-gray-100 bg-white p-6 shadow-sm transition-all hover:shadow-md"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand-600 transition-colors group-hover:bg-brand-600 group-hover:text-white">
                  <f.icon className="h-6 w-6" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-gray-900">
                  {f.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">
                  {f.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-center text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            How DukanYar Works
          </h2>
          <div className="mt-16 grid gap-12 md:grid-cols-3">
            {steps.map((step, i) => (
              <div key={step.number} className="text-center">
                <span className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-brand-600 to-brand-700 text-lg font-bold text-white shadow-md">
                  {step.number}
                </span>
                <h3 className="mt-6 text-lg font-semibold text-gray-900">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">
                  {step.description}
                </p>
                {i < steps.length - 1 && (
                  <div className="mx-auto mt-4 hidden h-px w-16 bg-gray-200 md:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-4xl rounded-3xl bg-gradient-to-br from-brand-600 to-brand-800 px-8 py-16 text-center shadow-xl sm:px-16">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Ready to Modernise Your Dukan?
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-lg text-indigo-200">
            Join the voice-first revolution in shop management. Set up in
            under a minute — no hardware needed.
          </p>
          <div className="mt-8 flex flex-col justify-center gap-4 sm:flex-row">
            <Link
              href="/signup"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-8 py-3.5 text-base font-semibold text-brand-700 shadow-sm transition-colors hover:bg-indigo-50"
            >
              Get Started Free
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-xl border border-white/30 px-8 py-3.5 text-base font-semibold text-white transition-colors hover:bg-white/10"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-gray-100 px-6 py-12">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 sm:flex-row">
          <div>
            <span className="text-lg font-bold text-gray-900">
              Dukan<span className="text-brand-600">Yar</span>
            </span>
            <p className="mt-1 text-sm text-gray-500">
              Voice-first shop management for Pakistani retailers.
            </p>
          </div>
          <div className="flex items-center gap-6 text-sm text-gray-500">
            <span className="inline-flex items-center gap-1.5">
              <Zap className="h-4 w-4" />
              Fast
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Shield className="h-4 w-4" />
              Secure
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Globe className="h-4 w-4" />
              Urdu &amp; English
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
>>>>>>> origin/feat/sale-catlg-mvp
}
