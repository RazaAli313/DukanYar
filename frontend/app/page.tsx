import Link from 'next/link'

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 text-center">
      <h1 className="text-4xl font-bold tracking-tight text-gray-900">
        Welcome to DukanYar
      </h1>
      <p className="mt-4 text-lg text-gray-600">
        Voice-first, multimodal shop management application.
      </p>
      <div className="mt-6 flex gap-4">
        <Link
          href="/login"
          className="rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-500"
        >
          Go to Login
        </Link>
      </div>
    </main>
  )
}