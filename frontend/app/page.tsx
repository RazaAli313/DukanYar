import Link from 'next/link'
import { redirect } from 'next/navigation'
import { getUserProfile } from './actions/auth'

export default async function HomePage() {
  const profile = await getUserProfile()
  if (profile) {
    redirect('/app')
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 text-center bg-slate-950 text-slate-100">
      <div className="max-w-md w-full space-y-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl backdrop-blur-sm">
        <div className="flex justify-center">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
            <span className="relative flex h-2 w-2">
              <span className="absolute inset-0 animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            Voice-First Shop Management
          </span>
        </div>

        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100">
            DukanYar
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Awaaz se dukan ka hisaab kitaab, sale aur udhaar sambhalein.
          </p>
        </div>

        <div className="flex flex-col gap-3 pt-2">
          <Link
            href="/login"
            className="w-full rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-emerald-400 transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/signup"
            className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-sm font-medium text-slate-200 hover:bg-slate-800 transition-colors"
          >
            Register Your Shop
          </Link>
        </div>
      </div>
    </main>
  )
}