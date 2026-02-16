'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Header } from '@/components/layout/header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Upload, FileText, Trash2, Play, Eye, RefreshCw } from 'lucide-react'
import { documentsAPI, Document, CheckItem, checkItemsAPI, reviewsAPI, fetchAPI } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { useToast } from '@/components/ui/toast'
import { useConfirm } from '@/components/ui/confirm-dialog'

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [showReviewModal, setShowReviewModal] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { showToast } = useToast()
  const { confirm } = useConfirm()

  useEffect(() => {
    loadDocuments()
  }, [])

  async function loadDocuments() {
    try {
      setLoading(true)
      const data = await documentsAPI.list()
      setDocuments(data)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showToast('PDFファイルのみアップロード可能です', 'error')
      return
    }

    // フロントエンドでのサイズ事前チェック（50MB上限）
    const MAX_SIZE_MB = 50
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      showToast(`ファイルサイズが${MAX_SIZE_MB}MBを超えています`, 'error')
      return
    }

    setUploading(true)
    try {
      await documentsAPI.upload(file)
      showToast('アップロードが完了しました', 'success')
      loadDocuments()
    } catch (error) {
      console.error('Upload failed:', error)
      showToast('アップロードに失敗しました', 'error')
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
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

  function getStatusBadge(status: string) {
    switch (status) {
      case 'completed':
        return <Badge variant="success">OCR完了</Badge>
      case 'processing':
        return <Badge variant="warning">処理中</Badge>
      case 'failed':
        return <Badge variant="destructive">失敗</Badge>
      default:
        return <Badge variant="secondary">待機中</Badge>
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
                <h3 className="text-lg font-semibold">文書をアップロード</h3>
                <p className="text-sm text-gray-500">
                  PDF形式のファイルをアップロードしてください
                </p>
              </div>
              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleUpload}
                  className="hidden"
                />
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                >
                  <Upload className="mr-2 h-4 w-4" />
                  {uploading ? 'アップロード中...' : 'ファイルを選択'}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Documents Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-center text-gray-500">読み込み中...</div>
            ) : documents.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                文書が登録されていません
              </div>
            ) : (
              <table className="w-full">
                <thead className="border-b bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      タイトル
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      OCR状態
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      登録日時
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <FileText className="h-5 w-5 text-gray-400" />
                          <span className="font-medium">{doc.title}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">{getStatusBadge(doc.ocr_status)}</td>
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
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl max-h-[80vh] overflow-y-auto">
        <h3 className="mb-4 text-lg font-semibold">レビューを開始</h3>
        <p className="mb-4 text-sm text-gray-600">
          文書: <span className="font-medium">{document.title}</span>
        </p>

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
          <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
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
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
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
