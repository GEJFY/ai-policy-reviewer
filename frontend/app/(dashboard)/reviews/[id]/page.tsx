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
  ChevronDown,
  ChevronRight,
  Search,
  MessageSquare,
  Eye,
  FileText,
  Pencil,
  FileDown,
} from 'lucide-react'
import { reviewsAPI, findingsAPI, termCandidatesAPI, Review, Finding, TermCandidate } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { HelpTooltip } from '@/components/ui/tooltip'
import { TIPS } from '@/lib/tooltip-texts'
import { ContextModal, RevisedTextModal } from '@/components/context-modal'

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
  const [searchQuery, setSearchQuery] = useState('')
  const [exporting, setExporting] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    HIGH: true,
    MEDIUM: false,
    LOW: false,
  })
  const [commentInputs, setCommentInputs] = useState<Record<number, string>>({})
  const [showCommentFor, setShowCommentFor] = useState<number | null>(null)
  const [contextFindingId, setContextFindingId] = useState<number | null>(null)
  const [showRevisedText, setShowRevisedText] = useState(false)
  const [editingSuggestion, setEditingSuggestion] = useState<Record<number, string>>({})
  const [showEditFor, setShowEditFor] = useState<number | null>(null)
  const [termCandidates, setTermCandidates] = useState<TermCandidate[]>([])
  const [candidateActionLoading, setCandidateActionLoading] = useState<number | null>(null)

  useEffect(() => {
    loadReview()
  }, [reviewId])

  useEffect(() => {
    if (review?.status === 'pending' || review?.status === 'processing') {
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

      // Load term candidates (non-blocking) — load if review finished
      if (reviewData.status === 'completed' || reviewData.status === 'failed') {
        termCandidatesAPI.list({ review_id: reviewId })
          .then(setTermCandidates)
          .catch(() => {})
      }
    } catch (error) {
      console.error('Failed to load review:', error)
      setError('レビューの読み込みに失敗しました。バックエンドが起動しているか確認してください。')
    } finally {
      setLoading(false)
    }
  }

  async function handleAction(findingId: number, action: 'approve' | 'reject' | 'defer') {
    setActionError(null)
    setActionLoading(findingId)
    const comment = commentInputs[findingId] || undefined
    try {
      if (action === 'approve') {
        const editedSuggestion = editingSuggestion[findingId]
        await findingsAPI.approve(findingId, comment, editedSuggestion || undefined)
        setEditingSuggestion((prev) => { const next = { ...prev }; delete next[findingId]; return next })
        setShowEditFor(null)
      } else if (action === 'reject') {
        await findingsAPI.reject(findingId, comment)
      } else {
        await findingsAPI.defer(findingId, comment)
      }
      setCommentInputs((prev) => { const next = { ...prev }; delete next[findingId]; return next })
      setShowCommentFor(null)
      loadReview()
    } catch (error) {
      console.error(`Failed to ${action} finding:`, error)
      setActionError(`指摘の${action === 'approve' ? '承認' : action === 'reject' ? '却下' : '保留'}に失敗しました`)
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

  async function handleDownloadRevised() {
    setDownloading(true)
    try {
      await reviewsAPI.downloadRevised(reviewId)
    } catch (error) {
      console.error('Failed to download revised document:', error)
      setActionError('改訂版ダウンロードに失敗しました')
    } finally {
      setDownloading(false)
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

  function toggleSection(severity: string) {
    setExpandedSections((prev) => ({ ...prev, [severity]: !prev[severity] }))
  }

  // Filtering
  const filteredFindings = findings.filter((f) => {
    if (severityFilter && f.severity !== severityFilter) return false
    if (statusFilter && f.status !== statusFilter) return false
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      return (
        f.description.toLowerCase().includes(q) ||
        (f.original_text?.toLowerCase().includes(q) ?? false) ||
        (f.suggestion?.toLowerCase().includes(q) ?? false) ||
        (f.location?.toLowerCase().includes(q) ?? false)
      )
    }
    return true
  })

  // Group by severity
  const groupedFindings: Record<string, Finding[]> = { HIGH: [], MEDIUM: [], LOW: [] }
  filteredFindings.forEach((f) => {
    if (groupedFindings[f.severity]) groupedFindings[f.severity].push(f)
    else groupedFindings[f.severity] = [f]
  })

  // Progress stats
  const totalFindings = findings.length
  const handledFindings = findings.filter((f) => f.status !== 'PENDING').length
  const progressPct = totalFindings > 0 ? Math.round((handledFindings / totalFindings) * 100) : 0

  const hasApproved = findings.some((f) => f.status === 'APPROVED')

  function getSeverityBorderColor(severity: string): string {
    switch (severity) {
      case 'HIGH': return 'border-l-red-500'
      case 'MEDIUM': return 'border-l-yellow-500'
      default: return 'border-l-blue-400'
    }
  }

  function getSeverityColor(severity: string): 'destructive' | 'warning' | 'secondary' {
    switch (severity) {
      case 'HIGH': return 'destructive'
      case 'MEDIUM': return 'warning'
      default: return 'secondary'
    }
  }

  function getStatusBadge(status: string) {
    switch (status) {
      case 'APPROVED': return <Badge variant="success">承認</Badge>
      case 'REJECTED': return <Badge variant="destructive">却下</Badge>
      case 'DEFERRED': return <Badge variant="secondary">保留</Badge>
      default: return <Badge variant="outline">未対応</Badge>
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
                    {hasApproved && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setShowRevisedText(true)}
                      >
                        <FileText className="mr-1 h-4 w-4" aria-hidden="true" />
                        修正文書プレビュー
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleDownloadRevised}
                      disabled={downloading}
                    >
                      {downloading ? (
                        <RefreshCw className="mr-1 h-4 w-4 animate-spin" aria-hidden="true" />
                      ) : (
                        <FileDown className="mr-1 h-4 w-4" aria-hidden="true" />
                      )}
                      改訂版DL
                    </Button>
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
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
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

            {/* Progress Bar */}
            {totalFindings > 0 && (
              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-500">対応進捗</span>
                  <span className="text-sm font-medium">
                    {handledFindings} / {totalFindings} 件対応済み ({progressPct}%)
                  </span>
                </div>
                <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-green-500 transition-all duration-500"
                    style={{ width: `${progressPct}%` }}
                  />
                </div>
              </div>
            )}
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

        {/* Filters - Pill toggle style */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          {/* Severity pills */}
          <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
            {[
              { value: '', label: '全重要度' },
              { value: 'HIGH', label: 'HIGH' },
              { value: 'MEDIUM', label: 'MEDIUM' },
              { value: 'LOW', label: 'LOW' },
            ].map((opt) => (
              <button
                key={opt.value}
                onClick={() => setSeverityFilter(opt.value)}
                className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                  severityFilter === opt.value
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {/* Status pills */}
          <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
            {[
              { value: '', label: '全ステータス' },
              { value: 'PENDING', label: '未対応' },
              { value: 'APPROVED', label: '承認' },
              { value: 'REJECTED', label: '却下' },
              { value: 'DEFERRED', label: '保留' },
            ].map((opt) => (
              <button
                key={opt.value}
                onClick={() => setStatusFilter(opt.value)}
                className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                  statusFilter === opt.value
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {/* Text search */}
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" aria-hidden="true" />
            <input
              type="text"
              placeholder="テキスト検索..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="rounded-md border border-gray-200 pl-8 pr-3 py-1.5 text-sm w-48"
              aria-label="指摘内容を検索"
            />
          </div>

          <button
            onClick={toggleAllFindings}
            className="text-sm text-blue-600 hover:underline"
          >
            未対応をすべて選択
          </button>
          <HelpTooltip text={TIPS.reviews.selectAll} />
        </div>

        {/* Findings - Grouped by Severity */}
        <div className="space-y-4">
          {filteredFindings.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center text-gray-500">
                指摘事項がありません
              </CardContent>
            </Card>
          ) : (
            (['HIGH', 'MEDIUM', 'LOW'] as const).map((severity) => {
              const group = groupedFindings[severity] || []
              if (group.length === 0) return null
              const isExpanded = expandedSections[severity]
              const severityLabel = { HIGH: '重大', MEDIUM: '中程度', LOW: '軽微' }[severity]
              const severityBg = {
                HIGH: 'bg-red-50 border-red-200',
                MEDIUM: 'bg-yellow-50 border-yellow-200',
                LOW: 'bg-blue-50 border-blue-200',
              }[severity]

              return (
                <div key={severity}>
                  {/* Section Header */}
                  <button
                    onClick={() => toggleSection(severity)}
                    className={`w-full flex items-center justify-between rounded-lg border p-3 mb-2 ${severityBg}`}
                  >
                    <div className="flex items-center gap-3">
                      {isExpanded ? (
                        <ChevronDown className="h-5 w-5" />
                      ) : (
                        <ChevronRight className="h-5 w-5" />
                      )}
                      <Badge variant={getSeverityColor(severity)}>{severity}</Badge>
                      <span className="font-medium">{severityLabel}</span>
                      <span className="text-sm text-gray-500">{group.length} 件</span>
                    </div>
                    <span className="text-sm text-gray-500">
                      {group.filter((f) => f.status !== 'PENDING').length}/{group.length} 対応済み
                    </span>
                  </button>

                  {/* Findings in this group */}
                  {isExpanded && (
                    <div className="space-y-3 ml-2">
                      {group.map((finding) => (
                        <FindingCard
                          key={finding.id}
                          finding={finding}
                          severityBorderColor={getSeverityBorderColor(finding.severity)}
                          isSelected={selectedFindings.includes(finding.id)}
                          onToggleSelect={() => toggleFinding(finding.id)}
                          actionLoading={actionLoading}
                          onAction={(action) => handleAction(finding.id, action)}
                          getStatusBadge={getStatusBadge}
                          commentInput={commentInputs[finding.id] || ''}
                          onCommentChange={(val) =>
                            setCommentInputs((prev) => ({ ...prev, [finding.id]: val }))
                          }
                          showComment={showCommentFor === finding.id}
                          onToggleComment={() =>
                            setShowCommentFor((prev) => (prev === finding.id ? null : finding.id))
                          }
                          onShowContext={() => setContextFindingId(finding.id)}
                          editingSuggestion={editingSuggestion[finding.id]}
                          showEdit={showEditFor === finding.id}
                          onToggleEdit={() => {
                            if (showEditFor === finding.id) {
                              setShowEditFor(null)
                            } else {
                              setShowEditFor(finding.id)
                              if (!editingSuggestion[finding.id]) {
                                setEditingSuggestion((prev) => ({
                                  ...prev,
                                  [finding.id]: finding.suggestion || '',
                                }))
                              }
                            }
                          }}
                          onEditSuggestionChange={(val) =>
                            setEditingSuggestion((prev) => ({ ...prev, [finding.id]: val }))
                          }
                        />
                      ))}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* Term Candidates */}
      {termCandidates.length > 0 && (
        <div className="mt-8 p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            用語候補
            <Badge variant="secondary">{termCandidates.filter(c => c.status === 'pending').length} 件未対応</Badge>
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {termCandidates.map((candidate) => (
              <Card key={candidate.id} className={candidate.status !== 'pending' ? 'opacity-60' : ''}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <span className="font-medium text-sm">{candidate.term}</span>
                    <div className="flex items-center gap-1">
                      {candidate.confidence != null && (
                        <span className="text-xs text-gray-400">
                          {Math.round(candidate.confidence * 100)}%
                        </span>
                      )}
                      {candidate.status === 'accepted' && <Badge variant="success">登録済</Badge>}
                      {candidate.status === 'rejected' && <Badge variant="destructive">却下</Badge>}
                    </div>
                  </div>
                  {candidate.category && (
                    <Badge variant="outline" className="mb-2 text-xs">{candidate.category}</Badge>
                  )}
                  {candidate.definition && (
                    <p className="text-xs text-gray-600 mb-2 line-clamp-2">{candidate.definition}</p>
                  )}
                  {candidate.context && (
                    <p className="text-xs text-gray-400 italic mb-3 line-clamp-1">
                      &ldquo;{candidate.context}&rdquo;
                    </p>
                  )}
                  {candidate.status === 'pending' && (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={candidateActionLoading === candidate.id}
                        onClick={async () => {
                          setCandidateActionLoading(candidate.id)
                          try {
                            await termCandidatesAPI.accept(candidate.id)
                            setTermCandidates(prev => prev.map(c =>
                              c.id === candidate.id ? { ...c, status: 'accepted' } : c
                            ))
                          } catch { setActionError('用語の登録に失敗しました') }
                          finally { setCandidateActionLoading(null) }
                        }}
                      >
                        <Check className="mr-1 h-3 w-3" />
                        登録
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        disabled={candidateActionLoading === candidate.id}
                        onClick={async () => {
                          setCandidateActionLoading(candidate.id)
                          try {
                            await termCandidatesAPI.reject(candidate.id)
                            setTermCandidates(prev => prev.map(c =>
                              c.id === candidate.id ? { ...c, status: 'rejected' } : c
                            ))
                          } catch { setActionError('却下に失敗しました') }
                          finally { setCandidateActionLoading(null) }
                        }}
                      >
                        <X className="mr-1 h-3 w-3" />
                        却下
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Context Modal */}
      {contextFindingId !== null && (
        <ContextModal
          findingId={contextFindingId}
          onClose={() => setContextFindingId(null)}
        />
      )}

      {/* Revised Text Modal */}
      {showRevisedText && (
        <RevisedTextModal
          reviewId={reviewId}
          onClose={() => setShowRevisedText(false)}
        />
      )}
    </>
  )
}

function FindingCard({
  finding,
  severityBorderColor,
  isSelected,
  onToggleSelect,
  actionLoading,
  onAction,
  getStatusBadge,
  commentInput,
  onCommentChange,
  showComment,
  onToggleComment,
  onShowContext,
  editingSuggestion,
  showEdit,
  onToggleEdit,
  onEditSuggestionChange,
}: {
  finding: Finding
  severityBorderColor: string
  isSelected: boolean
  onToggleSelect: () => void
  actionLoading: number | null
  onAction: (action: 'approve' | 'reject' | 'defer') => void
  getStatusBadge: (status: string) => React.ReactNode
  commentInput: string
  onCommentChange: (val: string) => void
  showComment: boolean
  onToggleComment: () => void
  onShowContext: () => void
  editingSuggestion: string | undefined
  showEdit: boolean
  onToggleEdit: () => void
  onEditSuggestionChange: (val: string) => void
}) {
  return (
    <Card className={`overflow-hidden border-l-4 ${severityBorderColor}`}>
      <div className="flex">
        {/* Checkbox for pending items */}
        {finding.status === 'PENDING' && (
          <div className="flex items-start border-r bg-gray-50 px-3 pt-4">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={onToggleSelect}
              className="h-4 w-4 rounded border-gray-300"
            />
          </div>
        )}

        <div className="flex-1 p-4">
          {/* Header */}
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="outline">{finding.issue_type}</Badge>
              {finding.location && (
                <span className="text-sm text-gray-500">{finding.location}</span>
              )}
              {finding.confidence != null && (
                <span className="text-xs text-gray-400" title="AI信頼度">
                  信頼度: {Math.round(finding.confidence * 100)}%
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {finding.original_text && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={onShowContext}
                  title="前後のコンテキストを表示"
                >
                  <Eye className="mr-1 h-4 w-4" aria-hidden="true" />
                  コンテキスト
                </Button>
              )}
              {getStatusBadge(finding.status)}
            </div>
          </div>

          {/* Original Text */}
          {finding.original_text && (
            <div className="mb-3">
              <p className="text-xs font-medium text-gray-500 mb-1">問題箇所</p>
              <p className="rounded bg-red-50 p-2 text-sm border border-red-100">
                {finding.original_text}
              </p>
            </div>
          )}

          {/* Description */}
          <div className="mb-3">
            <p className="text-xs font-medium text-gray-500 mb-1">問題内容</p>
            <p className="text-sm">{finding.description}</p>
          </div>

          {/* Suggestion with edit capability */}
          {finding.suggestion && (
            <div className="mb-3">
              <p className="text-xs font-medium text-gray-500 mb-1">
                改善提案
                {finding.status === 'PENDING' && (
                  <button
                    onClick={onToggleEdit}
                    className="ml-2 inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
                    title="提案を編集して承認"
                  >
                    <Pencil className="h-3 w-3" />
                    編集
                  </button>
                )}
              </p>
              {showEdit ? (
                <div>
                  <textarea
                    value={editingSuggestion ?? finding.suggestion}
                    onChange={(e) => onEditSuggestionChange(e.target.value)}
                    rows={3}
                    className="w-full rounded-md border border-blue-300 bg-blue-50 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  />
                  <p className="mt-1 text-xs text-gray-400">
                    提案を編集してから承認すると、編集後のテキストが改訂版に反映されます
                  </p>
                </div>
              ) : (
                <p className="rounded bg-green-50 p-2 text-sm border border-green-100">
                  {finding.edited_suggestion || finding.suggestion}
                </p>
              )}
            </div>
          )}

          {/* Edited suggestion indicator for already approved */}
          {finding.edited_suggestion && finding.status === 'APPROVED' && (
            <div className="mb-3">
              <p className="text-xs font-medium text-blue-600 mb-1">
                編集済み提案（承認時に適用）
              </p>
              <p className="rounded bg-blue-50 p-2 text-sm border border-blue-100">
                {finding.edited_suggestion}
              </p>
            </div>
          )}

          {/* Rationale */}
          {finding.rationale && (
            <div className="mb-3">
              <p className="text-xs font-medium text-gray-500 mb-1">
                指摘根拠 <HelpTooltip text={TIPS.reviews.rationale} />
              </p>
              <p className="rounded bg-gray-50 p-2 text-sm text-gray-700 border border-gray-100">
                {finding.rationale}
              </p>
            </div>
          )}

          {/* Actions */}
          {finding.status === 'PENDING' && (
            <div className="mt-4 border-t pt-4">
              {/* Comment toggle */}
              <div className="mb-3">
                <button
                  onClick={onToggleComment}
                  className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
                >
                  <MessageSquare className="h-3.5 w-3.5" />
                  {showComment ? 'コメントを閉じる' : 'コメントを追加'}
                </button>
                {showComment && (
                  <textarea
                    value={commentInput}
                    onChange={(e) => onCommentChange(e.target.value)}
                    placeholder="コメントを入力（任意）..."
                    rows={2}
                    className="mt-2 w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
                  />
                )}
              </div>

              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => onAction('approve')}
                  disabled={actionLoading === finding.id}
                >
                  {actionLoading === finding.id ? (
                    <RefreshCw className="mr-1 h-4 w-4 animate-spin" aria-hidden="true" />
                  ) : (
                    <Check className="mr-1 h-4 w-4" aria-hidden="true" />
                  )}
                  {editingSuggestion !== undefined &&
                   editingSuggestion !== finding.suggestion
                    ? '編集して承認'
                    : '承認'}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onAction('defer')}
                  disabled={actionLoading === finding.id}
                >
                  <Pause className="mr-1 h-4 w-4" aria-hidden="true" />
                  保留
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => onAction('reject')}
                  disabled={actionLoading === finding.id}
                >
                  <X className="mr-1 h-4 w-4" aria-hidden="true" />
                  却下
                </Button>
              </div>
            </div>
          )}

          {/* Review Comment */}
          {finding.comment && (
            <div className="mt-3 rounded bg-gray-50 p-2 text-sm text-gray-600 border border-gray-100">
              <span className="font-medium text-gray-700">コメント:</span> {finding.comment}
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}
