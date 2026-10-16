import { redirect } from 'next/navigation'
import { getUserProfile } from '../actions/auth'
import {
  getAdminOverview,
  getAdminShops,
  getVoiceTelemetry,
  getAuditLogs,
  getSystemHealth,
} from '../actions/admin'
import { AdminDashboard } from '@/components/admin/AdminDashboard'

export default async function AdminPage() {
  const profile = await getUserProfile()

  if (!profile) {
    redirect('/login')
  }

  // Guard: strictly enforce admin access (AUTH-2, ADMIN-1)
  if (profile.role_name !== 'admin') {
    redirect('/app')
  }

  // Fetch all administrative telemetry and data in parallel
  const [stats, shops, voiceLogs, auditLogs, health] = await Promise.all([
    getAdminOverview().catch(() => ({
      totalShops: 0,
      activeShops: 0,
      totalUsers: 0,
      totalConversations: 0,
      totalMessages: 0,
      voiceMessages: 0,
      textMessages: 0,
      avgConfidence: 0.95,
    })),
    getAdminShops().catch(() => []),
    getVoiceTelemetry().catch(() => []),
    getAuditLogs().catch(() => []),
    getSystemHealth(),
  ])

  return (
    <AdminDashboard
      initialStats={stats}
      initialShops={shops}
      initialVoiceLogs={voiceLogs}
      initialAuditLogs={auditLogs}
      initialHealth={health}
      adminEmail={profile.email}
    />
  )
}
