'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Header } from '@/components/layout/header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { HelpTooltip } from '@/components/ui/tooltip'
import { Upload, FileText, Trash2, Play, Eye, RefreshCw, Loader2, CheckSquare } from 'lucide-react'
import { documentsAPI, Document, CheckItem, checkItemsAPI, reviewsAPI, fetchAPI } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { useToast } from '@/components/ui/toast'
import { useConfirm } from '@/components/ui/confirm-dialog'
import { TIPS } from '@/lib/tooltip-texts'

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 })
  const [showReviewModal, setShowReviewModal] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [selectedDocIds, setSelectedDocIds] = useState<number[]>([])
  const [showBatchReviewModal, setShowBatchReviewModal] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { showToast } = useToast()
  const { confirm } = useConfirm()

  const loadDocuments = useCallback(async () => {
    try {
      const data = await documentsAPI.list()
      setDocuments(data)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    setLoading(true)
    loadDocuments()
  }, [loadDocuments])

  // Polling: 処理中のドキュメントがあれば3秒ごとにリフレッシュ
  useEffect(() => {
    const hasProcessing = documents.some(
      (d) => d.ocr_status === 'processing' || d.ocr_status === 'pending'
    )
    if (!hasProcessing) return

    const interval = setInterval(() => {
      loadDocuments()
    }, 3000)

    return () => clearInterval(interval)
  }, [documents, loadDocuments])

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files
    if (!files || files.length === 0) return

    const MAX_SIZE_MB = 50
    const validFiles: File[] = []
    for (const file of Array.from(files)) {
      const ext = file.name.toLowerCase()
      if (!ext.endsWith('.pdf') && !ext.endsWith('.xlsx') && !ext.endsWith('.xls')) {
        showToast(`${file.name}: PDF/Excelファイルのみアップロード可能です`, 'error')
        continue
      }
      if (file.size > MAX_SIZE_MB * 1024 * 1024) {
        showToast(`${file.name}: ファイルサイズが${MAX_SIZE_MB}MBを超えています`, 'error')
        continue
      }
      validFiles.push(file)
    }

    if (validFiles.length === 0) return

    setUploading(true)
    setUploadProgress({ current: 0, total: validFiles.length })

    let successCount = 0
    let failCount = 0
    for (let i = 0; i < validFiles.length; i++) {
      setUploadProgress({ current: i + 1, total: validFiles.length })
      try {
        await documentsAPI.upload(validFiles[i])
        successCount++
      } catch (error) {
        console.error(`Upload failed: ${validFiles[i].name}`, error)
        failCount++
      }
    }

    if (successCount > 0) {
      showToast(`${successCount}件のアップロードが完了しました`, 'success')
    }
    if (failCount > 0) {
      showToast(`${failCount}件のアップロードに失敗しました`, 'error')
    }

    loadDocuments()
    setUploading(false)
    setUploadProgress({ current: 0, total: 0 })
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  async function handleDelete(id: number) {
    const ok = await confirm({ message: 'この文書を削除しますか？' })
    if (!ok) return
    try {
      await documentsAPI.delete(id)
      showToast('文書を削除しました', 'success')
      loadDocuments()
    } catch (error) {
      console.error('Failed to delete document:', error)
      showToast('文書の削除に失敗しました', 'error')
    }
  }

  function getStatusBadge(doc: Document) {
    switch (doc.ocr_status) {
      case 'completed':
        return <Badge variant="success">OCR完了</Badge>
      case 'processing':
        return (
          <div className="flex items-center gap-2">
            <Badge variant="warning" className="flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              処理中
            </Badge>
            {doc.ocr_progress && (
              <span className="text-xs text-gray-500">{doc.ocr_progress}</span>
            )}
          </div>
        )
      case 'failed':
        return <Badge variant="destructive">失敗</Badge>
      default:
        return (
          <Badge variant="secondary" className="flex items-center gap-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            待機中
          </Badge>
        )
    }
  }

  const completedDocs = documents.filter((d) => d.ocr_status === 'completed')

  function toggleDocSelection(id: number) {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  function toggleAllCompleted() {
    if (selectedDocIds.length === completedDocs.length) {
      setSelectedDocIds([])
    } else {
      setSelectedDocIds(completedDocs.map((d) => d.id))
    }
  }

  return (
    <>
      <Header title="文書管理" />
      <div className="p-6">
        {/* Upload Area */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold">文書をアップロード</h3>
                  <HelpTooltip text={TIPS.documents.upload} />
                </div>
                <p className="text-sm text-gray-500">
                  PDF/Excel形式のファイルをアップロードしてください（複数選択可）
                </p>
              </div>
              <div>
                <input
                  ref={fileInputRef}
                  id="file-upload"
                  type="file"
                  accept=".pdf,.xlsx,.xls"
                  multiple
                  onChange={handleUpload}
                  className="hidden"
                  aria-label="PDFファイルを選択"
                />
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  aria-label={uploading ? 'アップロード中' : 'PDFファイルを選択してアップロード'}
                >
                  <Upload className="mr-2 h-4 w-4" aria-hidden="true" />
                  {uploading
                    ? uploadProgress.total > 1
                      ? `アップロード中 (${uploadProgress.current}/${uploadProgress.total})...`
                      : 'アップロード中...'
                    : 'ファイルを選択'}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Batch Selection Bar */}
        {selectedDocIds.length > 0 && (
          <div className="mb-4 flex items-center gap-4 rounded-lg bg-blue-50 p-4">
            <span className="text-sm font-medium">{selectedDocIds.length} 件選択中</span>
            <Button
              size="sm"
              onClick={() => setShowBatchReviewModal(true)}
            >
              <CheckSquare className="mr-1 h-4 w-4" aria-hidden="true" />
              一括チェック
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setSelectedDocIds([])}
            >
              選択解除
            </Button>
          </div>
        )}

        {/* Documents Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-center text-gray-500" role="status" aria-live="polite">読み込み中...</div>
            ) : documents.length === 0 ? (
              <div className="p-8 text-center text-gray-500" role="status">
                文書が登録されていません
              </div>
            ) : (
              <table className="w-full" aria-label="文書一覧">
                <thead className="border-b bg-gray-50">
                  <tr>
                    <th scope="col" className="w-10 px-4 py-3">
                      {completedDocs.length > 0 && (
                        <input
                          type="checkbox"
                          checked={selectedDocIds.length === completedDocs.length && completedDocs.length > 0}
                          onChange={toggleAllCompleted}
                          className="h-4 w-4 rounded border-gray-300"
                          aria-label="すべてのOCR完了文書を選択"
                        />
                      )}
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      タイトル
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      <span className="flex items-center gap-1">
                        OCR状態
                        <HelpTooltip text={TIPS.documents.ocrStatus} />
                      </span>
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      登録日時
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        {doc.ocr_status === 'completed' ? (
                          <input
                            type="checkbox"
                            checked={selectedDocIds.includes(doc.id)}
                            onChange={() => toggleDocSelection(doc.id)}
                            className="h-4 w-4 rounded border-gray-300"
                            aria-label={`${doc.title}を選択`}
                          />
                        ) : (
                          <span className="inline-block w-4" />
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <FileText className="h-5 w-5 text-gray-400" aria-hidden="true" />
                          <span className="font-medium">{doc.title}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">{getStatusBadge(doc)}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {formatDate(doc.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          {doc.ocr_status === 'completed' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setSelectedDocument(doc)
                                setShowReviewModal(true)
                              }}
                            >
                              <Play className="mr-1 h-4 w-4" />
                              レビュー
                            </Button>
                          )}
                          {doc.ocr_status === 'failed' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={async () => {
                                try {
                                  await fetchAPI(`/api/v1/documents/${doc.id}/ocr`, {
                                    method: 'POST',
                                  })
                                  showToast('OCR再処理を開始しました', 'info')
                                  loadDocuments()
                                } catch (error) {
                                  console.error('OCR retry failed:', error)
                                  showToast('OCR再処理の開始に失敗しました', 'error')
                                }
                              }}
                            >
                              <RefreshCw className="mr-1 h-4 w-4" />
                              再試行
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(doc.id)}
                            aria-label={`${doc.title}を削除`}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" aria-hidden="true" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>

        {/* Review Modal */}
        {showReviewModal && selectedDocument && (
          <ReviewStartModal
            document={selectedDocument}
            onClose={() => {
              setShowReviewModal(false)
              setSelectedDocument(null)
            }}
          />
        )}

        {/* Batch Review Modal */}
        {showBatchReviewModal && selectedDocIds.length > 0 && (
          <BatchReviewModal
            documentIds={selectedDocIds}
            documentTitles={documents
              .filter((d) => selectedDocIds.includes(d.id))
              .map((d) => d.title)}
            onClose={() => setShowBatchReviewModal(false)}
            onStarted={() => {
              setShowBatchReviewModal(false)
              setSelectedDocIds([])
            }}
          />
        )}
      </div>
    </>
  )
}

function ReviewStartModal({
  document,
  onClose,
}: {
  document: Document
  onClose: () => void
}) {
  const router = useRouter()
  const [checkItems, setCheckItems] = useState<CheckItem[]>([])
  const [selectedItems, setSelectedItems] = useState<number[]>([])
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadCheckItems()
  }, [])

  async function loadCheckItems() {
    try {
      const items = await checkItemsAPI.list({ is_active: true })
      setCheckItems(items)
      setSelectedItems(items.map((i) => i.id))
    } catch (error) {
      console.error('Failed to load check items:', error)
      setError('チェック項目の読み込みに失敗しました。バックエンドが起動しているか確認してください。')
    } finally {
      setLoading(false)
    }
  }

  async function handleStartReview() {
    if (selectedItems.length === 0) {
      setError('チェック項目を選択してください')
      return
    }

    setStarting(true)
    setError(null)
    try {
      const review = await reviewsAPI.create(document.id, selectedItems)
      router.push(`/reviews/${review.id}`)
    } catch (error) {
      console.error('Failed to start review:', error)
      setError('レビューの開始に失敗しました。バックエンドが起動しているか確認してください。')
      setStarting(false)
    }
  }

  function toggleItem(id: number) {
    setSelectedItems((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  function toggleAll() {
    if (selectedItems.length === checkItems.length) {
      setSelectedItems([])
    } else {
      setSelectedItems(checkItems.map((i) => i.id))
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="presentation">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl max-h-[80vh] overflow-y-auto" role="dialog" aria-modal="true" aria-labelledby="review-modal-title">
        <h3 id="review-modal-title" className="mb-4 text-lg font-semibold">レビューを開始</h3>
        <p className="mb-4 text-sm text-gray-600">
          文書: <span className="font-medium">{document.title}</span>
        </p>

        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700 flex items-center gap-1">
              チェック項目を選択
              <HelpTooltip text="レビュー時にAIがチェックする観点を選択します。すべて選択すると網羅的にチェックできます。" />
            </label>
            <button
              type="button"
              onClick={toggleAll}
              className="text-sm text-blue-600 hover:underline"
            >
              {selectedItems.length === checkItems.length
                ? 'すべて解除'
                : 'すべて選択'}
            </button>
          </div>

          {loading ? (
            <div className="py-4 text-center text-gray-500">読み込み中...</div>
          ) : (
            <div className="max-h-64 overflow-y-auto border rounded-md">
              {checkItems.map((item) => (
                <label
                  key={item.id}
                  className="flex items-center gap-3 p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                >
                  <input
                    type="checkbox"
                    checked={selectedItems.includes(item.id)}
                    onChange={() => toggleItem(item.id)}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <div>
                    <p className="font-medium">{item.name}</p>
                    <p className="text-xs text-gray-500">{item.description}</p>
                  </div>
                  <Badge variant="secondary" className="ml-auto">
                    {item.severity}
                  </Badge>
                </label>
              ))}
            </div>
          )}
        </div>

        {error && (
          <div role="alert" className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={starting}>
            キャンセル
          </Button>
          <Button onClick={handleStartReview} disabled={starting || loading}>
            {starting ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                レビュー開始中...
              </>
            ) : (
              'レビューを開始'
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}

function BatchReviewModal({
  documentIds,
  documentTitles,
  onClose,
  onStarted,
}: {
  documentIds: number[]
  documentTitles: string[]
  onClose: () => void
  onStarted: () => void
}) {
  const router = useRouter()
  const { showToast } = useToast()
  const [checkItems, setCheckItems] = useState<CheckItem[]>([])
  const [selectedItems, setSelectedItems] = useState<number[]>([])
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadCheckItems()
  }, [])

  async function loadCheckItems() {
    try {
      const items = await checkItemsAPI.list({ is_active: true })
      setCheckItems(items)
      setSelectedItems(items.map((i) => i.id))
    } catch (error) {
      console.error('Failed to load check items:', error)
      setError('チェック項目の読み込みに失敗しました')
    } finally {
      setLoading(false)
    }
  }

  async function handleStartBatchReview() {
    if (selectedItems.length === 0) {
      setError('チェック項目を選択してください')
      return
    }

    setStarting(true)
    setError(null)
    try {
      const result = await reviewsAPI.createBatch(documentIds, selectedItems)
      const successCount = result.created_reviews.length
      const failCount = result.failed_document_ids.length
      if (successCount > 0) {
        showToast(`${successCount}件のレビューを開始しました`, 'success')
      }
      if (failCount > 0) {
        showToast(`${failCount}件の文書でレビュー開始に失敗しました`, 'error')
      }
      onStarted()
      if (successCount === 1) {
        router.push(`/reviews/${result.created_reviews[0].id}`)
      } else {
        router.push('/reviews')
      }
    } catch (error) {
      console.error('Failed to start batch review:', error)
      setError('一括レビューの開始に失敗しました')
      setStarting(false)
    }
  }

  function toggleItem(id: number) {
    setSelectedItems((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  function toggleAll() {
    if (selectedItems.length === checkItems.length) {
      setSelectedItems([])
    } else {
      setSelectedItems(checkItems.map((i) => i.id))
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl max-h-[80vh] overflow-y-auto" role="dialog" aria-modal="true" aria-labelledby="batch-review-title">
        <h3 id="batch-review-title" className="mb-4 text-lg font-semibold">
          一括レビューを開始
        </h3>

        <div className="mb-4">
          <p className="text-sm text-gray-500 mb-2">対象文書（{documentIds.length}件）:</p>
          <div className="max-h-24 overflow-y-auto rounded-md border bg-gray-50 p-2">
            {documentTitles.map((title, idx) => (
              <p key={idx} className="text-sm truncate">{title}</p>
            ))}
          </div>
        </div>

        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">
              チェック項目を選択
            </label>
            <button
              type="button"
              onClick={toggleAll}
              className="text-sm text-blue-600 hover:underline"
            >
              {selectedItems.length === checkItems.length ? 'すべて解除' : 'すべて選択'}
            </button>
          </div>
          {loading ? (
            <div className="py-4 text-center text-gray-500">読み込み中...</div>
          ) : (
            <div className="max-h-48 overflow-y-auto border rounded-md">
              {checkItems.map((item) => (
                <label
                  key={item.id}
                  className="flex items-center gap-3 p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                >
                  <input
                    type="checkbox"
                    checked={selectedItems.includes(item.id)}
                    onChange={() => toggleItem(item.id)}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <div>
                    <p className="font-medium">{item.name}</p>
                    <p className="text-xs text-gray-500">{item.description}</p>
                  </div>
                  <Badge variant="secondary" className="ml-auto">
                    {item.severity}
                  </Badge>
                </label>
              ))}
            </div>
          )}
        </div>

        {error && (
          <div role="alert" className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={starting}>
            キャンセル
          </Button>
          <Button onClick={handleStartBatchReview} disabled={starting || loading}>
            {starting ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                レビュー開始中...
              </>
            ) : (
              `${documentIds.length}件の一括レビューを開始`
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
