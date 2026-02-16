'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  BookOpen,
  CheckSquare,
  FileText,
  Home,
  ListChecks,
  Settings,
  FileSearch,
} from 'lucide-react'

const navigation = [
  { name: 'ダッシュボード', href: '/', icon: Home },
  { name: '文書管理', href: '/documents', icon: FileText },
  { name: 'レビュー', href: '/reviews', icon: FileSearch },
  { name: '用語辞書', href: '/terms', icon: BookOpen },
  { name: 'チェック項目', href: '/check-items', icon: CheckSquare },
  { name: '記載ルール', href: '/writing-rules', icon: ListChecks },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex h-full w-64 flex-col bg-gray-900">
      <div className="flex h-16 items-center px-6">
        <h1 className="text-xl font-bold text-white">規程レビューツール</h1>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href))
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>
      <div className="border-t border-gray-800 p-4">
        <Link
          href="/settings"
          className={cn(
            'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
            pathname === '/settings'
              ? 'bg-gray-800 text-white'
              : 'text-gray-300 hover:bg-gray-800 hover:text-white'
          )}
        >
          <Settings className="h-5 w-5" />
          設定
        </Link>
      </div>
    </div>
  )
}
