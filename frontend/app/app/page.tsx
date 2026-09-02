import { getUserProfile, signOut } from '../actions/auth'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const profile = await getUserProfile()

  if (!profile) {
    redirect('/login')
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="mx-auto max-w-4xl space-y-6 rounded-xl bg-white p-6 shadow">
        <div className="flex items-center justify-between border-b pb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {profile.shops?.name || 'My Dukan'}
            </h1>
            <p className="text-sm text-gray-500">
              Role: <span className="font-semibold text-indigo-600">{profile.role_name}</span>
            </p>
          </div>
          <form action={signOut}>
            <button
              type="submit"
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500"
            >
              Sign Out
            </button>
          </form>
        </div>

        <div className="rounded-lg bg-indigo-50 p-4 border border-indigo-100">
          <h2 className="text-lg font-semibold text-indigo-900">
            Welcome to DukanYar Voice Management
          </h2>
          <p className="mt-1 text-sm text-indigo-700">
            Logged in as: <strong>{profile.email}</strong>
          </p>
        </div>
      </div>
    </div>
  )
}