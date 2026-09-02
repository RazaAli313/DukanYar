import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { TenantProvider } from '../providers/TenantProvider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'DukanYar - Voice-First Shop Management',
  description: 'Multimodal shop management app for Pakistani shopkeepers',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Day-1 Contract Context payload (defaults to null before auth resolution)
  const initialTenantState = {
    currentUser: null,
    currentShop: null,
  }

  return (
    <html lang="en">
      <body className={inter.className}>
        <TenantProvider value={initialTenantState}>
          {children}
        </TenantProvider>
      </body>
    </html>
  )
}