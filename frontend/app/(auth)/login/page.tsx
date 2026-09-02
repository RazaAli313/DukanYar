'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Mail, Lock, Mic, ShoppingCart, BarChart3 } from 'lucide-react'
import { signIn } from '../../actions/auth'

export default function LoginPage() {
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(formData: FormData) {
    setLoading(true)
    setError(null)
    const res = await signIn(formData)
    if (res?.error) {
      setError(res.error)
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* ── Left: Brand Panel (hidden on mobile) ── */}
      <div className="relative hidden flex-1 flex-col justify-between overflow-hidden bg-gradient-to-br from-brand-900 via-brand-700 to-brand-800 p-12 lg:flex">
        <div className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-white/5 blur-2xl" />
        <div className="pointer-events-none absolute -bottom-16 -left-16 h-64 w-64 rounded-full bg-emerald-500/10 blur-2xl" />

        <span className="text-2xl font-bold text-white">
          Dukan<span className="text-emerald-400">Yar</span>
        </span>

        <div className="space-y-8">
          <h2 className="text-4xl font-bold leading-tight text-white">
            Run Your Dukan
            <br />
            With Just Your Voice
          </h2>
          <div className="space-y-4">
            {[
              { icon: Mic, text: 'Record sales by speaking in Urdu or English' },
              { icon: ShoppingCart, text: 'Smart product resolution — say it once' },
              { icon: BarChart3, text: 'Real-time inventory and khata tracking' },
            ].map(({ icon: Icon, text }) => (
              <div
                key={text}
                className="flex items-center gap-3 text-indigo-200"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white/10">
                  <Icon className="h-5 w-5" />
                </div>
                <span className="text-sm">{text}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="text-sm text-indigo-300">
          &copy; 2026 DukanYar. Built for Pakistani shopkeepers.
        </p>
      </div>

      {/* ── Right: Auth Form ── */}
      <div className="flex flex-1 items-center justify-center bg-gray-50 p-6 sm:p-10">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <span className="text-lg font-bold text-brand-600 lg:hidden">
              DukanYar
            </span>
            <h1 className="mt-2 text-2xl font-bold tracking-tight text-gray-900">
              Welcome back
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              Sign in to manage your dukan
            </p>
          </div>

          {error && (
            <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form action={handleSubmit} className="space-y-5">
            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="mb-1.5 block text-sm font-medium text-gray-700"
              >
                Email Address
              </label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  autoComplete="email"
                  placeholder="shopkeeper@example.com"
                  className="w-full rounded-lg border border-gray-300 bg-white py-2.5 pl-10 pr-4 text-sm text-gray-900 shadow-sm transition-all placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-sm font-medium text-gray-700"
              >
                Password
              </label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="w-full rounded-lg border border-gray-300 bg-white py-2.5 pl-10 pr-4 text-sm text-gray-900 shadow-sm transition-all placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? (
                <>
                  <svg
                    className="h-4 w-4 animate-spin"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Signing in…
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-gray-500">
            Don&apos;t have a shop account?{' '}
            <Link
              href="/signup"
              className="font-semibold text-brand-600 transition-colors hover:text-brand-700"
            >
              Register your shop
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
