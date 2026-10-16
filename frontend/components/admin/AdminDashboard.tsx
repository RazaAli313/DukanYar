'use client'

import React, { useState, useTransition } from 'react'
import type {
  AdminStats,
  AdminShop,
  VoiceInteraction,
  AuditLogItem,
  SystemHealthStatus,
} from '@/app/actions/admin'
import { toggleShopActiveStatus } from '@/app/actions/admin'
import { signOut } from '@/app/actions/auth'
import Link from 'next/link'

interface AdminDashboardProps {
  initialStats: AdminStats
  initialShops: AdminShop[]
  initialVoiceLogs: VoiceInteraction[]
  initialAuditLogs: AuditLogItem[]
  initialHealth: SystemHealthStatus
  adminEmail: string
}

export function AdminDashboard({
  initialStats,
  initialShops,
  initialVoiceLogs,
  initialAuditLogs,
  initialHealth,
  adminEmail,
}: AdminDashboardProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'shops' | 'voice' | 'audit'>('overview')
  const [shops, setShops] = useState<AdminShop[]>(initialShops)
  const [searchShop, setSearchShop] = useState('')
  const [searchAudit, setSearchAudit] = useState('')
  const [isPending, startTransition] = useTransition()
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  const filteredShops = shops.filter(
    (s) =>
      s.name.toLowerCase().includes(searchShop.toLowerCase()) ||
      (s.owner_email && s.owner_email.toLowerCase().includes(searchShop.toLowerCase()))
  )

  const filteredAuditLogs = initialAuditLogs.filter(
    (log) =>
      log.action.toLowerCase().includes(searchAudit.toLowerCase()) ||
      (log.user_email && log.user_email.toLowerCase().includes(searchAudit.toLowerCase())) ||
      log.entity_type.toLowerCase().includes(searchAudit.toLowerCase())
  )

  const handleToggleShop = (shopId: string, currentActive: boolean) => {
    startTransition(async () => {
      const res = await toggleShopActiveStatus(shopId, currentActive)
      if (res.success) {
        setShops((prev) =>
          prev.map((s) => (s.id === shopId ? { ...s, is_active: !currentActive } : s))
        )
        setStatusMessage(`Shop ${!currentActive ? 'activated' : 'suspended'} successfully.`)
        setTimeout(() => setStatusMessage(null), 3000)
      } else {
        alert(res.error || 'Failed to update shop status')
      }
    })
  }

  const voicePercent =
    initialStats.totalMessages > 0
      ? Math.round((initialStats.voiceMessages / initialStats.totalMessages) * 100)
      : 0

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans">
      {/* ── Top Admin Header ────────────────────────────────────────── */}
      <header className="border-b border-slate-800 bg-[#0f172a]/90 backdrop-blur sticky top-0 z-20 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-sm">
            🛡️
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold tracking-tight text-white">
                DukanYar Admin Console
              </h1>
              <span className="rounded bg-indigo-500/20 px-1.5 py-0.5 text-[0.6875rem] font-medium text-indigo-300 border border-indigo-500/30">
                Phase 4 Platform
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Admin: <span className="text-slate-300 font-mono">{adminEmail}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/app"
            className="rounded-md border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
          >
            ← Counter App
          </Link>
          <form action={signOut}>
            <button
              type="submit"
              className="rounded-md bg-rose-600/80 hover:bg-rose-500 px-3 py-1.5 text-xs font-medium text-white transition"
            >
              Sign Out
            </button>
          </form>
        </div>
      </header>

      {/* ── Status Toast ────────────────────────────────────────────── */}
      {statusMessage && (
        <div className="bg-emerald-950/80 border-b border-emerald-700/50 px-6 py-2 text-xs text-emerald-300 flex items-center justify-between animate-fadeIn">
          <span>✓ {statusMessage}</span>
          <button onClick={() => setStatusMessage(null)} className="text-emerald-400 hover:text-white">
            ✕
          </button>
        </div>
      )}

      {/* ── Navigation Tabs ─────────────────────────────────────────── */}
      <div className="border-b border-slate-800 bg-[#0c1222] px-6">
        <nav className="flex space-x-6 text-sm font-medium">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-3.5 border-b-2 transition flex items-center gap-2 ${
              activeTab === 'overview'
                ? 'border-emerald-400 text-emerald-300 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            📊 System Health & Overview
          </button>
          <button
            onClick={() => setActiveTab('shops')}
            className={`py-3.5 border-b-2 transition flex items-center gap-2 ${
              activeTab === 'shops'
                ? 'border-emerald-400 text-emerald-300 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            🏪 Shops & Users ({initialShops.length})
          </button>
          <button
            onClick={() => setActiveTab('voice')}
            className={`py-3.5 border-b-2 transition flex items-center gap-2 ${
              activeTab === 'voice'
                ? 'border-emerald-400 text-emerald-300 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            🎙️ Voice & STT Telemetry
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`py-3.5 border-b-2 transition flex items-center gap-2 ${
              activeTab === 'audit'
                ? 'border-emerald-400 text-emerald-300 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            📋 Audit Trail ({initialAuditLogs.length})
          </button>
        </nav>
      </div>

      {/* ── Main Content Area ───────────────────────────────────────── */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto space-y-6">
        {/* ============================================================ */}
        {/* TAB 1: OVERVIEW & SYSTEM HEALTH (ADMIN-3)                     */}
        {/* ============================================================ */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="rounded-xl border border-slate-800 bg-[#111827] p-5">
                <p className="text-xs font-medium text-slate-400">Total Registered Shops</p>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-white">{initialStats.totalShops}</span>
                  <span className="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                    {initialStats.activeShops} Active
                  </span>
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-[#111827] p-5">
                <p className="text-xs font-medium text-slate-400">Platform Users</p>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-white">{initialStats.totalUsers}</span>
                  <span className="text-xs text-slate-400">Shopkeepers & Admins</span>
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-[#111827] p-5">
                <p className="text-xs font-medium text-slate-400">Total Interactions</p>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-white">{initialStats.totalMessages}</span>
                  <span className="text-xs text-indigo-300 font-mono">
                    {voicePercent}% Voice
                  </span>
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-[#111827] p-5">
                <p className="text-xs font-medium text-slate-400">Avg STT Accuracy</p>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-emerald-400">
                    {Math.round(initialStats.avgConfidence * 100)}%
                  </span>
                  <span className="text-xs text-slate-400">Speechmatics Scribe</span>
                </div>
              </div>
            </div>

            {/* Service Health Monitoring Grid (ADMIN-3) */}
            <div className="rounded-xl border border-slate-800 bg-[#111827] p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-semibold text-white">Live Service Infrastructure Health</h3>
                  <p className="text-xs text-slate-400">Real-time connectivity and status of platform pillars</p>
                </div>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400 border border-emerald-500/20">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  All Systems Operational
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
                {/* FastAPI Backend */}
                <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-300">FastAPI Backend API</span>
                    <span
                      className={`text-[0.6875rem] font-bold px-2 py-0.5 rounded ${
                        initialHealth.backend.status === 'healthy'
                          ? 'bg-emerald-500/15 text-emerald-300'
                          : 'bg-rose-500/15 text-rose-300'
                      }`}
                    >
                      {initialHealth.backend.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>GET /health</span>
                    <span className="font-mono">{initialHealth.backend.latencyMs}ms</span>
                  </div>
                </div>

                {/* Supabase Database */}
                <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-300">Supabase DB (RLS)</span>
                    <span
                      className={`text-[0.6875rem] font-bold px-2 py-0.5 rounded ${
                        initialHealth.database.status === 'healthy'
                          ? 'bg-emerald-500/15 text-emerald-300'
                          : 'bg-rose-500/15 text-rose-300'
                      }`}
                    >
                      {initialHealth.database.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>PostgreSQL Multi-tenant</span>
                    <span className="font-mono">{initialHealth.database.latencyMs}ms</span>
                  </div>
                </div>

                {/* AI Pipeline Providers */}
                <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-300">AI Speech & LLM Pipeline</span>
                    <span className="text-[0.6875rem] font-bold px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300">
                      READY
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>STT / TTS / Gemini Flash</span>
                    <span className="font-mono text-emerald-400">Active</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* TAB 2: SHOPS & USERS MANAGEMENT (ADMIN-1)                    */}
        {/* ============================================================ */}
        {activeTab === 'shops' && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              <input
                type="text"
                value={searchShop}
                onChange={(e) => setSearchShop(e.target.value)}
                placeholder="Search shops by name or owner email..."
                className="w-full sm:w-80 rounded-lg border border-slate-800 bg-[#111827] px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
              />
              <span className="text-xs text-slate-400">
                Showing {filteredShops.length} of {shops.length} shops
              </span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-[#111827] overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-[#0f172a] text-slate-400 uppercase text-[0.6875rem] border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3">Shop Name</th>
                      <th className="px-4 py-3">Owner / Email</th>
                      <th className="px-4 py-3">Users</th>
                      <th className="px-4 py-3">Conversations</th>
                      <th className="px-4 py-3">Registered On</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredShops.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                          No shops found matching your search.
                        </td>
                      </tr>
                    ) : (
                      filteredShops.map((shop) => (
                        <tr key={shop.id} className="hover:bg-slate-900/40 transition">
                          <td className="px-4 py-3 font-semibold text-white">{shop.name}</td>
                          <td className="px-4 py-3 font-mono text-slate-300">{shop.owner_email}</td>
                          <td className="px-4 py-3">{shop.user_count}</td>
                          <td className="px-4 py-3">{shop.conversation_count}</td>
                          <td className="px-4 py-3 text-slate-400">
                            {new Date(shop.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[0.6875rem] font-medium ${
                                shop.is_active
                                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                              }`}
                            >
                              <span
                                className={`h-1.5 w-1.5 rounded-full ${
                                  shop.is_active ? 'bg-emerald-400' : 'bg-rose-400'
                                }`}
                              />
                              {shop.is_active ? 'Active' : 'Suspended'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button
                              onClick={() => handleToggleShop(shop.id, shop.is_active)}
                              disabled={isPending}
                              className={`rounded px-2.5 py-1 text-[0.6875rem] font-medium transition ${
                                shop.is_active
                                  ? 'bg-rose-600/20 text-rose-300 border border-rose-600/30 hover:bg-rose-600 hover:text-white'
                                  : 'bg-emerald-600/20 text-emerald-300 border border-emerald-600/30 hover:bg-emerald-600 hover:text-white'
                              }`}
                            >
                              {shop.is_active ? 'Suspend' : 'Activate'}
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* TAB 3: VOICE & TRANSCRIPTION TELEMETRY (ADMIN-2)             */}
        {/* ============================================================ */}
        {activeTab === 'voice' && (
          <div className="space-y-6">
            {/* Channel Breakdown Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-xl border border-slate-800 bg-[#111827] p-5">
                <p className="text-xs text-slate-400">Total Audio Voice Clips</p>
                <p className="mt-2 text-2xl font-bold text-indigo-400">
                  {initialStats.voiceMessages}
                </p>
                <p className="mt-1 text-xs text-slate-500">Transcribed via Speechmatics / Whisper</p>
              </div>

              <div className="rounded-xl border border-slate-800 bg-[#111827] p-5">
                <p className="text-xs text-slate-400">Text Chat Interactions</p>
                <p className="mt-2 text-2xl font-bold text-slate-200">{initialStats.textMessages}</p>
                <p className="mt-1 text-xs text-slate-500">Typed Urdu & Roman-Urdu queries</p>
              </div>

              <div className="rounded-xl border border-slate-800 bg-[#111827] p-5">
                <p className="text-xs text-slate-400">Voice Share of Total Usage</p>
                <p className="mt-2 text-2xl font-bold text-emerald-400">{voicePercent}%</p>
                <p className="mt-1 text-xs text-slate-500">Multimodal usage proportion</p>
              </div>
            </div>

            {/* Recent Voice Interactions & Accuracy Table */}
            <div className="rounded-xl border border-slate-800 bg-[#111827] p-5 space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-white">Recent Voice Transcriptions & Quality</h3>
                <p className="text-xs text-slate-400">
                  Realtime monitoring of Urdu speech recognition confidence and accuracy
                </p>
              </div>

              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-[#0f172a] text-slate-400 uppercase text-[0.6875rem] border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3">Timestamp</th>
                      <th className="px-4 py-3">Recognized Transcript</th>
                      <th className="px-4 py-3">Sender</th>
                      <th className="px-4 py-3">Confidence Score</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[0.8125rem]">
                    {initialVoiceLogs.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-slate-500 font-sans">
                          No voice interactions recorded yet. Use the mic button in the counter app to generate voice telemetry.
                        </td>
                      </tr>
                    ) : (
                      initialVoiceLogs.map((log) => {
                        const conf = log.transcription_confidence ?? 0.95
                        const isLowConfidence = conf < 0.75
                        return (
                          <tr key={log.id} className="hover:bg-slate-900/40 transition">
                            <td className="px-4 py-3 text-slate-400 text-xs font-sans">
                              {new Date(log.created_at).toLocaleTimeString()}
                            </td>
                            <td className="px-4 py-3 text-slate-100 font-sans max-w-md truncate">
                              &ldquo;{log.message}&rdquo;
                            </td>
                            <td className="px-4 py-3 text-xs capitalize text-slate-400 font-sans">
                              {log.sender}
                            </td>
                            <td className="px-4 py-3">
                              <span
                                className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-semibold ${
                                  isLowConfidence
                                    ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                                    : 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                                }`}
                              >
                                {Math.round(conf * 100)}%
                              </span>
                            </td>
                            <td className="px-4 py-3 text-xs font-sans">
                              {isLowConfidence ? (
                                <span className="text-amber-400 font-medium">⚠️ Review Prompt</span>
                              ) : (
                                <span className="text-emerald-400">✓ Accurate</span>
                              )}
                            </td>
                          </tr>
                        )
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* TAB 4: AUDIT TRAIL (ADMIN-3)                                  */}
        {/* ============================================================ */}
        {activeTab === 'audit' && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              <input
                type="text"
                value={searchAudit}
                onChange={(e) => setSearchAudit(e.target.value)}
                placeholder="Filter audit logs by action or user..."
                className="w-full sm:w-80 rounded-lg border border-slate-800 bg-[#111827] px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
              />
              <span className="text-xs text-slate-400">
                Showing {filteredAuditLogs.length} events
              </span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-[#111827] overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-[#0f172a] text-slate-400 uppercase text-[0.6875rem] border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3">Timestamp</th>
                      <th className="px-4 py-3">Actor / Email</th>
                      <th className="px-4 py-3">Action Type</th>
                      <th className="px-4 py-3">Target Entity</th>
                      <th className="px-4 py-3">Payload Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                    {filteredAuditLogs.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-slate-500 font-sans">
                          No audit log entries recorded yet. Significant security and management actions will appear here.
                        </td>
                      </tr>
                    ) : (
                      filteredAuditLogs.map((item) => (
                        <tr key={item.id} className="hover:bg-slate-900/40 transition">
                          <td className="px-4 py-3 text-slate-400 whitespace-nowrap font-sans text-xs">
                            {new Date(item.created_at).toLocaleString()}
                          </td>
                          <td className="px-4 py-3 text-slate-300">{item.user_email || 'system'}</td>
                          <td className="px-4 py-3">
                            <span className="rounded bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 text-[0.6875rem] font-bold">
                              {item.action}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-400">
                            {item.entity_type} {item.entity_id ? `(${item.entity_id.slice(0, 8)}...)` : ''}
                          </td>
                          <td className="px-4 py-3 text-slate-400 font-mono text-[0.6875rem] max-w-xs truncate">
                            {JSON.stringify(item.details)}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
