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
  AlertTriangle,
  CheckCircle,
  Clock,
  PenLine,
} from 'lucide-react'
import { dashboardAPI, reviewsAPI, DashboardStats, Review } from '@/lib/api'
import { HelpTooltip } from '@/components/ui/tooltip'
import { TIPS } from '@/lib/tooltip-texts'

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentReviews, setRecentReviews] = useState<Review[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const results = await Promise.allSettled([
          dashboardAPI.getStats(),
          reviewsAPI.list(),
        ])

        if (results[0].status === 'fulfilled') {
          setStats(results[0].value)
        }
        if (results[1].status === 'fulfilled') {
          setRecentReviews(results[1].value.slice(0, 5))
        }
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
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-5">
          <StatsCard
            title="登録文書"
            value={stats?.document_count ?? 0}
            icon={FileText}
            href="/documents"
            tooltip={TIPS.dashboard.documentCount}
          />
          <StatsCard
            title="レビュー"
            value={stats?.review_count ?? 0}
            icon={FileSearch}
            href="/reviews"
            tooltip={TIPS.dashboard.reviewCount}
          />
          <StatsCard
            title="用語辞書"
            value={stats?.term_count ?? 0}
            icon={BookOpen}
            href="/terms"
            tooltip={TIPS.dashboard.termCount}
          />
          <StatsCard
            title="チェック項目"
            value={stats?.check_item_count ?? 0}
            icon={CheckSquare}
            href="/check-items"
            tooltip={TIPS.dashboard.checkItemCount}
          />
          <StatsCard
            title="記載ルール"
            value={stats?.writing_rule_count ?? 0}
            icon={PenLine}
            href="/writing-rules"
            tooltip={TIPS.dashboard.writingRuleCount}
          />
        </div>

        {/* Finding & Review Summary */}
        {stats && stats.finding_total > 0 && (
          <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* Finding Severity */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-gray-500">
                  指摘事項（重要度別）
                  <HelpTooltip text={TIPS.dashboard.findingSummary} />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-end gap-4">
                  <div className="text-3xl font-bold">{stats.finding_total}</div>
                  <div className="mb-1 text-sm text-gray-500">件</div>
                </div>
                <div className="mt-4 flex gap-3">
                  {stats.finding_by_severity.high > 0 && (
                    <Badge variant="destructive">
                      <AlertCircle className="mr-1 h-3 w-3" aria-hidden="true" />
                      HIGH {stats.finding_by_severity.high}
                    </Badge>
                  )}
                  {stats.finding_by_severity.medium > 0 && (
                    <Badge variant="warning">
                      <AlertTriangle className="mr-1 h-3 w-3" aria-hidden="true" />
                      MEDIUM {stats.finding_by_severity.medium}
                    </Badge>
                  )}
                  {stats.finding_by_severity.low > 0 && (
                    <Badge variant="secondary">
                      LOW {stats.finding_by_severity.low}
                    </Badge>
                  )}
                </div>
                {/* Progress bar */}
                <div className="mt-4 flex h-2 overflow-hidden rounded-full bg-gray-100">
                  {stats.finding_by_severity.high > 0 && (
                    <div
                      className="bg-red-500"
                      style={{ width: `${(stats.finding_by_severity.high / stats.finding_total) * 100}%` }}
                    />
                  )}
                  {stats.finding_by_severity.medium > 0 && (
                    <div
                      className="bg-yellow-500"
                      style={{ width: `${(stats.finding_by_severity.medium / stats.finding_total) * 100}%` }}
                    />
                  )}
                  {stats.finding_by_severity.low > 0 && (
                    <div
                      className="bg-gray-400"
                      style={{ width: `${(stats.finding_by_severity.low / stats.finding_total) * 100}%` }}
                    />
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Finding Status */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-gray-500">
                  レビュー対応状況
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-500">未対応</div>
                    <div className="text-2xl font-bold text-orange-600">
                      {stats.finding_by_status.pending}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">承認済み</div>
                    <div className="text-2xl font-bold text-green-600">
                      {stats.finding_by_status.approved}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">却下</div>
                    <div className="text-2xl font-bold text-red-600">
                      {stats.finding_by_status.rejected}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">保留</div>
                    <div className="text-2xl font-bold text-gray-600">
                      {stats.finding_by_status.deferred}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Recent Reviews */}
        <div className="mt-8">
          <h3 className="mb-4 text-lg font-semibold">
            最近のレビュー
            <HelpTooltip text={TIPS.dashboard.recentReviews} />
          </h3>
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="p-8 text-center text-gray-500" role="status" aria-live="polite">読み込み中...</div>
              ) : recentReviews.length === 0 ? (
                <div className="p-8 text-center text-gray-500" role="status">
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
                        {(review.high_count ?? 0) > 0 && (
                          <Badge variant="destructive">{review.high_count} HIGH</Badge>
                        )}
                        {(review.medium_count ?? 0) > 0 && (
                          <Badge variant="warning">{review.medium_count} MEDIUM</Badge>
                        )}
                        {(review.low_count ?? 0) > 0 && (
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
  tooltip,
}: {
  title: string
  value: number
  icon: React.ElementType
  href: string
  tooltip?: string
}) {
  return (
    <Link href={href}>
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-gray-500">
            {title}
            {tooltip && <HelpTooltip text={tooltip} />}
          </CardTitle>
          <Icon className="h-5 w-5 text-gray-400" aria-hidden="true" />
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
      return <CheckCircle className="h-5 w-5 text-green-500" aria-hidden="true" role="img" />
    case 'processing':
      return <Clock className="h-5 w-5 text-yellow-500" aria-hidden="true" role="img" />
    case 'failed':
      return <AlertCircle className="h-5 w-5 text-red-500" aria-hidden="true" role="img" />
    default:
      return <Clock className="h-5 w-5 text-gray-400" aria-hidden="true" role="img" />
  }
}
