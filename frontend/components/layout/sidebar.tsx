'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  BookOpen,
  CheckSquare,
  FileText,
  GitCompareArrows,
  Home,
  ListChecks,
  Settings,
  FileSearch,
  FolderSync,
  HelpCircle,
} from 'lucide-react'

const navigation = [
  { name: 'ダッシュボード', href: '/', icon: Home },
  { name: '文書管理', href: '/documents', icon: FileText },
  { name: 'レビュー', href: '/reviews', icon: FileSearch },
  { name: '規程グループ', href: '/document-groups', icon: FolderSync },
  { name: '親子会社比較', href: '/comparisons', icon: GitCompareArrows },
  { name: '用語辞書', href: '/terms', icon: BookOpen },
  { name: 'チェック項目', href: '/check-items', icon: CheckSquare },
  { name: '記載ルール', href: '/writing-rules', icon: ListChecks },
  { name: 'マニュアル', href: '/manual', icon: HelpCircle },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="flex h-full w-64 flex-col bg-gray-900" aria-label="メインナビゲーション">
      <div className="flex h-16 items-center px-6">
        <h1 className="text-xl font-bold text-white">規程レビューツール</h1>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4" aria-label="サイドバー">
        {navigation.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href))
          return (
            <Link
              key={item.name}
              href={item.href}
              aria-current={isActive ? 'page' : undefined}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white',
                isActive
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              )}
            >
              <item.icon className="h-5 w-5" aria-hidden="true" />
              {item.name}
            </Link>
          )
        })}
      </nav>
      <div className="border-t border-gray-800 p-4">
        <Link
          href="/settings"
          aria-current={pathname === '/settings' ? 'page' : undefined}
          className={cn(
            'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white',
            pathname === '/settings'
              ? 'bg-gray-800 text-white'
              : 'text-gray-300 hover:bg-gray-800 hover:text-white'
          )}
        >
          <Settings className="h-5 w-5" aria-hidden="true" />
          設定
        </Link>
      </div>
    </aside>
  )
}
