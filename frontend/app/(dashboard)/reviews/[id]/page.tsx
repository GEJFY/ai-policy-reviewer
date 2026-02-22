'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { Header } from '@/components/layout/header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Check,
  X,
  Pause,
  RefreshCw,
  Download,
} from 'lucide-react'
import { reviewsAPI, findingsAPI, Review, Finding } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { HelpTooltip } from '@/components/ui/tooltip'
import { TIPS } from '@/lib/tooltip-texts'

export default function ReviewDetailPage() {
  const params = useParams()
  const reviewId = Number(params.id)

  const [review, setReview] = useState<Review | null>(null)
  const [findings, setFindings] = useState<Finding[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<number | null>(null)
  const [pollCount, setPollCount] = useState(0)
  const [selectedFindings, setSelectedFindings] = useState<number[]>([])
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    loadReview()
  }, [reviewId])

  useEffect(() => {
    // Poll for status updates if pending or processing (with backoff)
    if (review?.status === 'pending' || review?.status === 'processing') {
      // 最初は3秒、徐々に遅くして最大10秒
      const delay = Math.min(3000 + pollCount * 1000, 10000)
      const timeout = setTimeout(() => {
        loadReview()
        setPollCount((prev) => prev + 1)
      }, delay)
      return () => clearTimeout(timeout)
    } else {
      setPollCount(0)
    }
  }, [review?.status, pollCount])

  async function loadReview() {
    try {
      const [reviewData, findingsData] = await Promise.all([
        reviewsAPI.get(reviewId),
        findingsAPI.list(reviewId),
      ])
      setReview(reviewData)
      setFindings(findingsData)
      setError(null)
    } catch (error) {
      console.error('Failed to load review:', error)
      setError('レビューの読み込みに失敗しました。バックエンドが起動しているか確認してください。')
    } finally {
      setLoading(false)
    }
  }

  async function handleApprove(findingId: number) {
    setActionError(null)
    setActionLoading(findingId)
    try {
      await findingsAPI.approve(findingId)
      loadReview()
    } catch (error) {
      console.error('Failed to approve finding:', error)
      setActionError('指摘の承認に失敗しました')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleReject(findingId: number) {
    setActionError(null)
    setActionLoading(findingId)
    try {
      await findingsAPI.reject(findingId)
      loadReview()
    } catch (error) {
      console.error('Failed to reject finding:', error)
      setActionError('指摘の却下に失敗しました')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleDefer(findingId: number) {
    setActionError(null)
    setActionLoading(findingId)
    try {
      await findingsAPI.defer(findingId)
      loadReview()
    } catch (error) {
      console.error('Failed to defer finding:', error)
      setActionError('指摘の保留に失敗しました')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleBulkApprove() {
    if (selectedFindings.length === 0) return
    setActionError(null)
    try {
      await findingsAPI.bulkApprove(reviewId, selectedFindings, 'APPROVED')
      setSelectedFindings([])
      loadReview()
    } catch (error) {
      console.error('Failed to bulk approve:', error)
      setActionError('一括承認に失敗しました')
    }
  }

  async function handleExport() {
    setExporting(true)
    try {
      await reviewsAPI.exportExcel(reviewId)
    } catch (error) {
      console.error('Failed to export:', error)
      setActionError('Excelエクスポートに失敗しました')
    } finally {
      setExporting(false)
    }
  }

  function toggleFinding(id: number) {
    setSelectedFindings((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  function toggleAllFindings() {
    const pending = filteredFindings.filter((f) => f.status === 'PENDING')
    if (selectedFindings.length === pending.length) {
      setSelectedFindings([])
    } else {
      setSelectedFindings(pending.map((f) => f.id))
    }
  }

  const filteredFindings = findings.filter((f) => {
    if (severityFilter && f.severity !== severityFilter) return false
    if (statusFilter && f.status !== statusFilter) return false
    return true
  })

  function getSeverityColor(severity: string): 'destructive' | 'warning' | 'secondary' {
    switch (severity) {
      case 'HIGH':
        return 'destructive'
      case 'MEDIUM':
        return 'warning'
      default:
        return 'secondary'
    }
  }

  function getStatusBadge(status: string) {
    switch (status) {
      case 'APPROVED':
        return <Badge variant="success">承認</Badge>
      case 'REJECTED':
        return <Badge variant="destructive">却下</Badge>
      case 'DEFERRED':
        return <Badge variant="secondary">保留</Badge>
      default:
        return <Badge variant="outline">未対応</Badge>
    }
  }

  if (loading) {
    return (
      <>
        <Header title="レビュー詳細" />
        <div className="p-6">
          <div className="text-center text-gray-500" role="status" aria-live="polite">読み込み中...</div>
        </div>
      </>
    )
  }

  if (error || !review) {
    return (
      <>
        <Header title="レビュー詳細" />
        <div className="p-6">
          <Link
            href="/reviews"
            className="mb-4 inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft className="mr-1 h-4 w-4" aria-hidden="true" />
            レビュー一覧に戻る
          </Link>
          <Card className="mt-4">
            <CardContent className="p-8 text-center">
              <AlertCircle className="mx-auto mb-3 h-10 w-10 text-red-400" aria-hidden="true" />
              <p className="text-gray-600 mb-4">
                {error || 'レビューが見つかりません'}
              </p>
              <Button onClick={() => { setLoading(true); setError(null); loadReview() }}>
                <RefreshCw className="mr-2 h-4 w-4" aria-hidden="true" />
                再読み込み
              </Button>
            </CardContent>
          </Card>
        </div>
      </>
    )
  }

  return (
    <>
      <Header title="レビュー詳細" />
      <div className="p-6">
        {/* Back Link */}
        <Link
          href="/reviews"
          className="mb-4 inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft className="mr-1 h-4 w-4" aria-hidden="true" />
          レビュー一覧に戻る
        </Link>

        {/* Review Info */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{review.document_title || `文書 #${review.document_id}`}</span>
              <div className="flex items-center gap-2">
                {(review.status === 'pending' || review.status === 'processing') && (
                  <div className="flex items-center gap-2 text-yellow-600">
                    <RefreshCw className="h-5 w-5 animate-spin" aria-hidden="true" />
                    <span className="text-sm" role="status" aria-live="polite">
                      {review.status === 'pending' ? 'レビュー準備中...' : 'AIがレビュー中...'}
                    </span>
                  </div>
                )}
                {review.status === 'completed' && (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleExport}
                      disabled={exporting}
                    >
                      {exporting ? (
                        <RefreshCw className="mr-1 h-4 w-4 animate-spin" aria-hidden="true" />
                      ) : (
                        <Download className="mr-1 h-4 w-4" aria-hidden="true" />
                      )}
                      Excel出力
                    </Button>
                    <HelpTooltip text={TIPS.reviews.export} />
                  </>
                )}
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-500">ステータス</p>
                <div className="flex items-center gap-2 mt-1">
                  {review.status === 'completed' && (
                    <CheckCircle className="h-5 w-5 text-green-500" aria-hidden="true" />
                  )}
                  {(review.status === 'pending' || review.status === 'processing') && (
                    <Clock className="h-5 w-5 text-yellow-500" aria-hidden="true" />
                  )}
                  {review.status === 'failed' && (
                    <XCircle className="h-5 w-5 text-red-500" aria-hidden="true" />
                  )}
                  <span className="font-medium">
                    {review.status === 'completed'
                      ? '完了'
                      : review.status === 'pending'
                        ? '準備中'
                        : review.status === 'processing'
                          ? 'AIレビュー中'
                          : review.status === 'failed'
                            ? '失敗'
                            : '不明'}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500">総指摘数</p>
                <p className="mt-1 text-2xl font-bold">{review.finding_count || 0}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">重要度別</p>
                <div className="mt-1 flex gap-2">
                  <Badge variant="destructive">{review.high_count || 0} HIGH</Badge>
                  <Badge variant="warning">{review.medium_count || 0} MED</Badge>
                  <Badge variant="secondary">{review.low_count || 0} LOW</Badge>
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500">実行日時</p>
                <p className="mt-1 font-medium">{formatDate(review.created_at)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Bulk Actions */}
        {selectedFindings.length > 0 && (
          <div className="mb-4 flex items-center gap-4 rounded-lg bg-blue-50 p-4" aria-live="polite" aria-atomic="true">
            <span className="text-sm font-medium">
              {selectedFindings.length} 件選択中
            </span>
            <Button size="sm" onClick={handleBulkApprove}>
              <Check className="mr-1 h-4 w-4" aria-hidden="true" />
              一括承認
            </Button>
            <HelpTooltip text={TIPS.reviews.bulkApprove} />
            <Button
              size="sm"
              variant="outline"
              onClick={() => setSelectedFindings([])}
            >
              選択解除
            </Button>
          </div>
        )}

        {/* Action Error */}
        {actionError && (
          <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">
            {actionError}
          </div>
        )}

        {/* Filters */}
        <div className="mb-4 flex items-center gap-4">
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="rounded-md border border-gray-200 px-3 py-2 text-sm"
            aria-label="重要度でフィルタ"
          >
            <option value="">すべての重要度</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-md border border-gray-200 px-3 py-2 text-sm"
            aria-label="ステータスでフィルタ"
          >
            <option value="">すべてのステータス</option>
            <option value="PENDING">未対応</option>
            <option value="APPROVED">承認</option>
            <option value="REJECTED">却下</option>
            <option value="DEFERRED">保留</option>
          </select>
          <button
            onClick={toggleAllFindings}
            className="text-sm text-blue-600 hover:underline"
          >
            未対応をすべて選択
          </button>
          <HelpTooltip text={TIPS.reviews.selectAll} />
        </div>

        {/* Findings List */}
        <div className="space-y-4">
          {filteredFindings.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center text-gray-500">
                指摘事項がありません
              </CardContent>
            </Card>
          ) : (
            filteredFindings.map((finding) => (
              <Card key={finding.id} className="overflow-hidden">
                <div className="flex">
                  {/* Checkbox for pending items */}
                  {finding.status === 'PENDING' && (
                    <div className="flex items-center border-r bg-gray-50 px-4">
                      <input
                        type="checkbox"
                        checked={selectedFindings.includes(finding.id)}
                        onChange={() => toggleFinding(finding.id)}
                        className="h-4 w-4 rounded border-gray-300"
                      />
                    </div>
                  )}

                  <div className="flex-1 p-4">
                    {/* Header */}
                    <div className="mb-3 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant={getSeverityColor(finding.severity)}>
                          {finding.severity}
                        </Badge>
                        <Badge variant="outline">{finding.issue_type}</Badge>
                        {finding.location && (
                          <span className="text-sm text-gray-500">
                            {finding.location}
                          </span>
                        )}
                      </div>
                      {getStatusBadge(finding.status)}
                    </div>

                    {/* Original Text */}
                    {finding.original_text && (
                      <div className="mb-3">
                        <p className="text-xs font-medium text-gray-500 mb-1">
                          問題箇所
                        </p>
                        <p className="rounded bg-red-50 p-2 text-sm">
                          {finding.original_text}
                        </p>
                      </div>
                    )}

                    {/* Description */}
                    <div className="mb-3">
                      <p className="text-xs font-medium text-gray-500 mb-1">
                        問題内容
                      </p>
                      <p className="text-sm">{finding.description}</p>
                    </div>

                    {/* Suggestion */}
                    {finding.suggestion && (
                      <div className="mb-3">
                        <p className="text-xs font-medium text-gray-500 mb-1">
                          改善提案
                        </p>
                        <p className="rounded bg-green-50 p-2 text-sm">
                          {finding.suggestion}
                        </p>
                      </div>
                    )}

                    {/* Actions */}
                    {finding.status === 'PENDING' && (
                      <div className="mt-4 flex gap-2 border-t pt-4">
                        <Button
                          size="sm"
                          onClick={() => handleApprove(finding.id)}
                          disabled={actionLoading === finding.id}
                        >
                          {actionLoading === finding.id ? (
                            <RefreshCw className="mr-1 h-4 w-4 animate-spin" aria-hidden="true" />
                          ) : (
                            <Check className="mr-1 h-4 w-4" aria-hidden="true" />
                          )}
                          承認
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDefer(finding.id)}
                          disabled={actionLoading === finding.id}
                        >
                          <Pause className="mr-1 h-4 w-4" aria-hidden="true" />
                          保留
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleReject(finding.id)}
                          disabled={actionLoading === finding.id}
                        >
                          <X className="mr-1 h-4 w-4" aria-hidden="true" />
                          却下
                        </Button>
                      </div>
                    )}

                    {/* Review Comment */}
                    {finding.comment && (
                      <div className="mt-3 text-sm text-gray-500">
                        <span className="font-medium">コメント:</span> {finding.comment}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>
    </>
  )
}
