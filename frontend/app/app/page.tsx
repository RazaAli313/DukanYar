import { getUserProfile, signOut } from '../actions/auth'
import { redirect } from 'next/navigation'
import { ChatScreen } from '@/components/chat/ChatScreen'

export default async function DashboardPage() {
  const profile = await getUserProfile()

  if (!profile) {
    redirect('/login')
  }

  return (
    <ChatScreen
      shopName={profile.shops?.name || 'My Dukan'}
      userEmail={profile.email}
      onSignOut={signOut}
    />
  )
}