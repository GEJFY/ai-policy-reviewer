'use client'

import { Sidebar } from '@/components/layout/sidebar'
import { ToastProvider } from '@/components/ui/toast'
import { ConfirmProvider } from '@/components/ui/confirm-dialog'
import { AuthProvider, useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isLoading, isAuthenticated, router])

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          <p className="mt-3 text-sm text-gray-500">読み込み中...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return <>{children}</>
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <AuthProvider>
      <AuthGuard>
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
      </AuthGuard>
    </AuthProvider>
  )
}
