'use client'

import { Sidebar } from '@/components/layout/sidebar'
import { ToastProvider } from '@/components/ui/toast'
import { ConfirmProvider } from '@/components/ui/confirm-dialog'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ToastProvider>
      <ConfirmProvider>
        <div className="flex h-screen">
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:z-[200] focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-medium"
          >
            メインコンテンツへスキップ
          </a>
          <Sidebar />
          <main id="main-content" className="flex-1 overflow-auto bg-gray-50">
            {children}
          </main>
        </div>
      </ConfirmProvider>
    </ToastProvider>
  )
}
