'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Header } from '@/components/layout/header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  FileText,
  FileSearch,
  BookOpen,
  CheckSquare,
  AlertCircle,
  CheckCircle,
  Clock,
} from 'lucide-react'
import { reviewsAPI, documentsAPI, termsAPI, checkItemsAPI } from '@/lib/api'

interface Stats {
  documents: number
  reviews: number
  terms: number
  checkItems: number
  pendingFindings: number
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({
    documents: 0,
    reviews: 0,
    terms: 0,
    checkItems: 0,
    pendingFindings: 0,
  })
  const [recentReviews, setRecentReviews] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const [documents, reviews, terms, checkItems] = await Promise.all([
          documentsAPI.list(),
          reviewsAPI.list(),
          termsAPI.list(),
          checkItemsAPI.list(),
        ])

        setStats({
          documents: documents.length,
          reviews: reviews.length,
          terms: terms.length,
          checkItems: checkItems.length,
          pendingFindings: reviews.reduce((sum, r) => sum + (r.finding_count || 0), 0),
        })

        setRecentReviews(reviews.slice(0, 5))
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  return (
    <>
      <Header title="ダッシュボード" />
      <div className="p-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            title="登録文書"
            value={stats.documents}
            icon={FileText}
            href="/documents"
          />
          <StatsCard
            title="レビュー"
            value={stats.reviews}
            icon={FileSearch}
            href="/reviews"
          />
          <StatsCard
            title="用語辞書"
            value={stats.terms}
            icon={BookOpen}
            href="/terms"
          />
          <StatsCard
            title="チェック項目"
            value={stats.checkItems}
            icon={CheckSquare}
            href="/check-items"
          />
        </div>

        {/* Recent Reviews */}
        <div className="mt-8">
          <h3 className="mb-4 text-lg font-semibold">最近のレビュー</h3>
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="p-8 text-center text-gray-500">読み込み中...</div>
              ) : recentReviews.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  レビューがありません
                </div>
              ) : (
                <div className="divide-y">
                  {recentReviews.map((review) => (
                    <Link
                      key={review.id}
                      href={`/reviews/${review.id}`}
                      className="flex items-center justify-between p-4 hover:bg-gray-50"
                    >
                      <div className="flex items-center gap-4">
                        <StatusIcon status={review.status} />
                        <div>
                          <p className="font-medium">
                            {review.document_title || `文書 #${review.document_id}`}
                          </p>
                          <p className="text-sm text-gray-500">
                            {new Date(review.created_at).toLocaleString('ja-JP')}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {review.high_count > 0 && (
                          <Badge variant="destructive">{review.high_count} HIGH</Badge>
                        )}
                        {review.medium_count > 0 && (
                          <Badge variant="warning">{review.medium_count} MEDIUM</Badge>
                        )}
                        {review.low_count > 0 && (
                          <Badge variant="secondary">{review.low_count} LOW</Badge>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  )
}

function StatsCard({
  title,
  value,
  icon: Icon,
  href,
}: {
  title: string
  value: number
  icon: any
  href: string
}) {
  return (
    <Link href={href}>
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-gray-500">
            {title}
          </CardTitle>
          <Icon className="h-5 w-5 text-gray-400" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{value}</div>
        </CardContent>
      </Card>
    </Link>
  )
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="h-5 w-5 text-green-500" />
    case 'processing':
      return <Clock className="h-5 w-5 text-yellow-500" />
    case 'failed':
      return <AlertCircle className="h-5 w-5 text-red-500" />
    default:
      return <Clock className="h-5 w-5 text-gray-400" />
  }
}
