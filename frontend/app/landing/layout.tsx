import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'PolicyReview AI — AI規程レビューツール',
  description:
    '就業規則・セキュリティポリシー・内部統制規程をAIが自動レビュー。用語統一・文法・法令準拠チェックで、レビュー工数を最大80%削減。',
}

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>
}
