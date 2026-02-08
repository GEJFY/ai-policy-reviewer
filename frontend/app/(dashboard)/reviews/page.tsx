'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Header } from '@/components/layout/header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Eye, Trash2, CheckCircle, Clock, AlertCircle, XCircle } from 'lucide-react'
import { reviewsAPI, Review } from '@/lib/api'
import { formatDate } from '@/lib/utils'

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('')

  useEffect(() => {
    loadReviews()
  }, [statusFilter])

  async function loadReviews() {
    try {
      setLoading(true)
      const data = await reviewsAPI.list(
        statusFilter ? { status: statusFilter } : undefined
      )
      setReviews(data)
    } catch (error) {
      console.error('Failed to load reviews:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('このレビューを削除しますか？')) return
    try {
      await reviewsAPI.delete(id)
      loadReviews()
    } catch (error) {
      console.error('Failed to delete review:', error)
    }
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'processing':
        return <Clock className="h-5 w-5 text-yellow-500" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }

  function getStatusLabel(status: string) {
    switch (status) {
      case 'completed':
        return '完了'
      case 'processing':
        return '処理中'
      case 'failed':
        return '失敗'
      default:
        return '待機中'
    }
  }

  return (
    <>
      <Header title="レビュー一覧" />
      <div className="p-6">
        {/* Filter */}
        <div className="mb-6 flex items-center gap-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-md border border-gray-200 px-3 py-2 text-sm"
          >
            <option value="">すべてのステータス</option>
            <option value="pending">待機中</option>
            <option value="processing">処理中</option>
            <option value="completed">完了</option>
            <option value="failed">失敗</option>
          </select>
          <Button variant="outline" onClick={loadReviews}>
            更新
          </Button>
        </div>

        {/* Reviews Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-center text-gray-500">読み込み中...</div>
            ) : reviews.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                レビューがありません
              </div>
            ) : (
              <table className="w-full">
                <thead className="border-b bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      文書
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      ステータス
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      指摘数
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      実行日時
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {reviews.map((review) => (
                    <tr key={review.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <span className="font-medium">
                          {review.document_title || `文書 #${review.document_id}`}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(review.status)}
                          <span className="text-sm">
                            {getStatusLabel(review.status)}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {review.high_count! > 0 && (
                            <Badge variant="destructive">
                              {review.high_count} HIGH
                            </Badge>
                          )}
                          {review.medium_count! > 0 && (
                            <Badge variant="warning">
                              {review.medium_count} MEDIUM
                            </Badge>
                          )}
                          {review.low_count! > 0 && (
                            <Badge variant="secondary">
                              {review.low_count} LOW
                            </Badge>
                          )}
                          {(review.finding_count || 0) === 0 && (
                            <span className="text-sm text-gray-500">-</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {formatDate(review.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <Link href={`/reviews/${review.id}`}>
                            <Button variant="outline" size="sm">
                              <Eye className="mr-1 h-4 w-4" />
                              詳細
                            </Button>
                          </Link>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(review.id)}
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
      </div>
    </>
  )
}
