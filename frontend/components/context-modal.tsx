'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { X, RefreshCw } from 'lucide-react'
import { findingsAPI, FindingContext } from '@/lib/api'

interface ContextModalProps {
  findingId: number
  onClose: () => void
}

export function ContextModal({ findingId, onClose }: ContextModalProps) {
  const [context, setContext] = useState<FindingContext | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'original' | 'corrected'>('original')

  useEffect(() => {
    loadContext()
  }, [findingId])

  async function loadContext() {
    try {
      setLoading(true)
      setError(null)
      const data = await findingsAPI.getContext(findingId)
      setContext(data)
    } catch (err) {
      console.error('Failed to load context:', err)
      setError('コンテキストの読み込みに失敗しました')
    } finally {
      setLoading(false)
    }
  }

  function renderHighlightedText(
    text: string,
    start: number,
    end: number,
    highlightClass: string
  ) {
    if (start < 0 || !text) return <p className="whitespace-pre-wrap text-sm">{text}</p>

    const before = text.slice(0, start)
    const highlighted = text.slice(start, end)
    const after = text.slice(end)

    return (
      <p className="whitespace-pre-wrap text-sm leading-relaxed">
        {before}
        <mark className={highlightClass}>{highlighted}</mark>
        {after}
      </p>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div
        className="w-full max-w-3xl rounded-lg bg-white shadow-xl max-h-[85vh] flex flex-col"
        role="dialog"
        aria-modal="true"
        aria-labelledby="context-modal-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h3 id="context-modal-title" className="text-lg font-semibold">
            コンテキスト表示
          </h3>
          <button
            onClick={onClose}
            className="rounded-md p-1 hover:bg-gray-100"
            aria-label="閉じる"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b px-6">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab('original')}
              className={`border-b-2 py-3 text-sm font-medium transition-colors ${
                activeTab === 'original'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              原文（問題箇所ハイライト）
            </button>
            <button
              onClick={() => setActiveTab('corrected')}
              className={`border-b-2 py-3 text-sm font-medium transition-colors ${
                activeTab === 'corrected'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              修正プレビュー
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="mr-2 h-5 w-5 animate-spin text-gray-400" />
              <span className="text-gray-500">読み込み中...</span>
            </div>
          ) : error ? (
            <div className="py-8 text-center">
              <p className="text-red-500 mb-3">{error}</p>
              <Button variant="outline" size="sm" onClick={loadContext}>
                再試行
              </Button>
            </div>
          ) : context ? (
            <>
              {activeTab === 'original' ? (
                <div>
                  {context.context_text ? (
                    <div className="rounded-lg border bg-gray-50 p-4">
                      {renderHighlightedText(
                        context.context_text,
                        context.highlight_start,
                        context.highlight_end,
                        'bg-red-200 text-red-900 px-0.5 rounded'
                      )}
                    </div>
                  ) : (
                    <p className="text-center text-gray-500 py-8">
                      コンテキストが見つかりませんでした。原文テキストがドキュメント内に存在しない可能性があります。
                    </p>
                  )}
                  {context.original_text && (
                    <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3">
                      <p className="text-xs font-medium text-red-700 mb-1">問題箇所</p>
                      <p className="text-sm text-red-800">{context.original_text}</p>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  {context.corrected_text ? (
                    <>
                      <div className="rounded-lg border bg-gray-50 p-4">
                        {context.suggestion ? (
                          renderHighlightedText(
                            context.corrected_text,
                            context.highlight_start,
                            context.highlight_start + context.suggestion.length,
                            'bg-green-200 text-green-900 px-0.5 rounded'
                          )
                        ) : (
                          <p className="whitespace-pre-wrap text-sm">{context.corrected_text}</p>
                        )}
                      </div>
                      {context.suggestion && (
                        <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-3">
                          <p className="text-xs font-medium text-green-700 mb-1">修正内容</p>
                          <p className="text-sm text-green-800">{context.suggestion}</p>
                        </div>
                      )}
                    </>
                  ) : (
                    <p className="text-center text-gray-500 py-8">
                      修正プレビューを生成できませんでした。改善提案がないか、原文が見つかりませんでした。
                    </p>
                  )}
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="border-t px-6 py-4 flex justify-end">
          <Button variant="outline" onClick={onClose}>
            閉じる
          </Button>
        </div>
      </div>
    </div>
  )
}

interface RevisedTextModalProps {
  reviewId: number
  onClose: () => void
}

export function RevisedTextModal({ reviewId, onClose }: RevisedTextModalProps) {
  const [data, setData] = useState<{ original_text: string; revised_text: string; changes_applied: number; total_approved: number } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'revised' | 'diff'>('revised')

  useEffect(() => {
    loadRevisedText()
  }, [reviewId])

  async function loadRevisedText() {
    try {
      setLoading(true)
      setError(null)
      const result = await findingsAPI.getRevisedText(reviewId)
      setData(result)
    } catch (err) {
      console.error('Failed to load revised text:', err)
      setError('改訂テキストの生成に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div
        className="w-full max-w-4xl rounded-lg bg-white shadow-xl max-h-[85vh] flex flex-col"
        role="dialog"
        aria-modal="true"
        aria-labelledby="revised-text-modal-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <div>
            <h3 id="revised-text-modal-title" className="text-lg font-semibold">
              修正文書プレビュー
            </h3>
            {data && (
              <p className="text-sm text-gray-500 mt-1">
                {data.changes_applied} / {data.total_approved} 件の承認済み修正を適用
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1 hover:bg-gray-100"
            aria-label="閉じる"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b px-6">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab('revised')}
              className={`border-b-2 py-3 text-sm font-medium transition-colors ${
                activeTab === 'revised'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              修正後テキスト
            </button>
            <button
              onClick={() => setActiveTab('diff')}
              className={`border-b-2 py-3 text-sm font-medium transition-colors ${
                activeTab === 'diff'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              差分表示
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="mr-2 h-5 w-5 animate-spin text-gray-400" />
              <span className="text-gray-500">改訂テキストを生成中...</span>
            </div>
          ) : error ? (
            <div className="py-8 text-center">
              <p className="text-red-500 mb-3">{error}</p>
              <Button variant="outline" size="sm" onClick={loadRevisedText}>
                再試行
              </Button>
            </div>
          ) : data ? (
            activeTab === 'revised' ? (
              <div className="rounded-lg border bg-gray-50 p-4">
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {data.revised_text}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                  <p className="text-xs font-medium text-red-700 mb-2">修正前</p>
                  <p className="whitespace-pre-wrap text-sm text-red-900 leading-relaxed">
                    {data.original_text}
                  </p>
                </div>
                <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                  <p className="text-xs font-medium text-green-700 mb-2">修正後</p>
                  <p className="whitespace-pre-wrap text-sm text-green-900 leading-relaxed">
                    {data.revised_text}
                  </p>
                </div>
              </div>
            )
          ) : null}
        </div>

        {/* Footer */}
        <div className="border-t px-6 py-4 flex justify-end gap-2">
          {data && (
            <Button
              variant="outline"
              onClick={() => {
                navigator.clipboard.writeText(data.revised_text)
              }}
            >
              テキストをコピー
            </Button>
          )}
          <Button variant="outline" onClick={onClose}>
            閉じる
          </Button>
        </div>
      </div>
    </div>
  )
}
