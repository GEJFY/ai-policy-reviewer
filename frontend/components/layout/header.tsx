'use client'

import { useState, useRef, useEffect } from 'react'
import { Bell, HelpCircle, User, LogOut, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/lib/auth-context'
import Link from 'next/link'

interface HeaderProps {
  title?: string
}

export function Header({ title }: HeaderProps) {
  const { user, logout } = useAuth()
  const [showMenu, setShowMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
      <div className="flex items-center gap-4">
        <Link href="/manual">
          <Button variant="ghost" size="icon" aria-label="ヘルプ・マニュアル">
            <HelpCircle className="h-5 w-5" aria-hidden="true" />
          </Button>
        </Link>
        <Button variant="ghost" size="icon" aria-label="通知">
          <Bell className="h-5 w-5" aria-hidden="true" />
        </Button>
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-gray-100 transition-colors"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-600">
              <User className="h-4 w-4" />
            </div>
            {user && (
              <span className="text-sm font-medium text-gray-700 hidden sm:block">
                {user.display_name}
              </span>
            )}
          </button>

          {showMenu && (
            <div className="absolute right-0 top-12 w-48 rounded-lg border bg-white shadow-lg py-1 z-50">
              {user && (
                <div className="px-4 py-2 border-b">
                  <p className="text-sm font-medium">{user.display_name}</p>
                  <p className="text-xs text-gray-500">{user.username}</p>
                </div>
              )}
              {user?.roles?.includes('admin') && (
                <Link
                  href="/settings"
                  onClick={() => setShowMenu(false)}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <Settings className="h-4 w-4" />
                  設定
                </Link>
              )}
              <button
                onClick={() => { setShowMenu(false); logout() }}
                className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                <LogOut className="h-4 w-4" />
                ログアウト
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
