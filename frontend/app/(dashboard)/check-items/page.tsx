'use client'

import { useState, useEffect } from 'react'
import { Header } from '@/components/layout/header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { checkItemsAPI, CheckItem, CheckItemCreate } from '@/lib/api'
import { useToast } from '@/components/ui/toast'
import { useConfirm } from '@/components/ui/confirm-dialog'

const CATEGORIES = [
  { value: 'TERMINOLOGY', label: '用語統一' },
  { value: 'GRAMMAR', label: '文法・表現' },
  { value: 'STRUCTURE', label: '構成・体裁' },
  { value: 'COMPLIANCE', label: '法令・コンプライアンス' },
  { value: 'CONSISTENCY', label: '整合性' },
  { value: 'SECURITY', label: 'セキュリティ' },
  { value: 'OPERATIONAL', label: '実務適合性' },
]

const SEVERITIES = [
  { value: 'HIGH', label: 'HIGH', color: 'destructive' },
  { value: 'MEDIUM', label: 'MEDIUM', color: 'warning' },
  { value: 'LOW', label: 'LOW', color: 'secondary' },
]

export default function CheckItemsPage() {
  const [items, setItems] = useState<CheckItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [showForm, setShowForm] = useState(false)
  const [editingItem, setEditingItem] = useState<CheckItem | null>(null)
  const { showToast } = useToast()
  const { confirm } = useConfirm()

  useEffect(() => {
    loadItems()
  }, [selectedCategory])

  async function loadItems() {
    try {
      setLoading(true)
      const data = await checkItemsAPI.list(
        selectedCategory ? { category: selectedCategory } : undefined
      )
      setItems(data)
    } catch (error) {
      console.error('Failed to load check items:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: number) {
    const ok = await confirm({ message: 'このチェック項目を削除しますか？' })
    if (!ok) return
    try {
      await checkItemsAPI.delete(id)
      showToast('チェック項目を削除しました', 'success')
      loadItems()
    } catch (error) {
      console.error('Failed to delete check item:', error)
      showToast('チェック項目の削除に失敗しました', 'error')
    }
  }

  async function handleToggleActive(item: CheckItem) {
    try {
      await checkItemsAPI.update(item.id, { is_active: !item.is_active })
      loadItems()
    } catch (error) {
      console.error('Failed to update check item:', error)
    }
  }

  function getCategoryLabel(value: string): string {
    return CATEGORIES.find((c) => c.value === value)?.label || value
  }

  function getSeverityVariant(severity: string): 'destructive' | 'warning' | 'secondary' {
    const s = SEVERITIES.find((s) => s.value === severity)
    return (s?.color as any) || 'secondary'
  }

  return (
    <>
      <Header title="チェック項目" />
      <div className="p-6">
        {/* Actions */}
        <div className="mb-6 flex items-center justify-between">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="rounded-md border border-gray-200 px-3 py-2 text-sm"
          >
            <option value="">すべてのカテゴリ</option>
            {CATEGORIES.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
          <Button onClick={() => { setEditingItem(null); setShowForm(true); }}>
            <Plus className="mr-2 h-4 w-4" />
            新規登録
          </Button>
        </div>

        {/* Items Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-center text-gray-500">読み込み中...</div>
            ) : items.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                チェック項目が登録されていません
              </div>
            ) : (
              <table className="w-full">
                <thead className="border-b bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      項目名
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      カテゴリ
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      重要度
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      状態
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      説明
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {items.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{item.name}</td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">
                          {getCategoryLabel(item.category)}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={getSeverityVariant(item.severity)}>
                          {item.severity}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => handleToggleActive(item)}
                          className={`rounded-full px-2 py-1 text-xs ${
                            item.is_active
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-500'
                          }`}
                        >
                          {item.is_active ? '有効' : '無効'}
                        </button>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 max-w-md truncate">
                        {item.description}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => { setEditingItem(item); setShowForm(true); }}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(item.id)}
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

        {/* Form Modal */}
        {showForm && (
          <CheckItemFormModal
            item={editingItem}
            onClose={() => { setShowForm(false); setEditingItem(null); }}
            onSaved={() => { setShowForm(false); setEditingItem(null); loadItems(); }}
          />
        )}
      </div>
    </>
  )
}

function CheckItemFormModal({
  item,
  onClose,
  onSaved,
}: {
  item: CheckItem | null
  onClose: () => void
  onSaved: () => void
}) {
  const [formData, setFormData] = useState<CheckItemCreate>({
    name: item?.name || '',
    category: item?.category || 'TERMINOLOGY',
    description: item?.description || '',
    severity: item?.severity || 'MEDIUM',
    prompt_template: item?.prompt_template || '',
    is_active: item?.is_active ?? true,
  })
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setFormError(null)
    try {
      if (item) {
        await checkItemsAPI.update(item.id, formData)
      } else {
        await checkItemsAPI.create(formData)
      }
      onSaved()
    } catch (error) {
      console.error('Failed to save check item:', error)
      setFormError('保存に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl max-h-[90vh] overflow-y-auto">
        <h3 className="mb-4 text-lg font-semibold">
          {item ? 'チェック項目を編集' : 'チェック項目を登録'}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              項目名 <span className="text-red-500">*</span>
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              カテゴリ <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.category}
              onChange={(e) =>
                setFormData({ ...formData, category: e.target.value })
              }
              className="w-full rounded-md border border-gray-200 px-3 py-2"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              重要度 <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.severity}
              onChange={(e) =>
                setFormData({ ...formData, severity: e.target.value })
              }
              className="w-full rounded-md border border-gray-200 px-3 py-2"
            >
              {SEVERITIES.map((sev) => (
                <option key={sev.value} value={sev.value}>
                  {sev.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              説明 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              required
              rows={3}
              className="w-full rounded-md border border-gray-200 px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              カスタムプロンプト（オプション）
            </label>
            <textarea
              value={formData.prompt_template || ''}
              onChange={(e) =>
                setFormData({ ...formData, prompt_template: e.target.value })
              }
              rows={4}
              className="w-full rounded-md border border-gray-200 px-3 py-2 font-mono text-sm"
              placeholder="カスタムプロンプトテンプレートを入力..."
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) =>
                setFormData({ ...formData, is_active: e.target.checked })
              }
            />
            <label htmlFor="is_active" className="text-sm">
              有効にする
            </label>
          </div>

          {formError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
              {formError}
            </div>
          )}

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              キャンセル
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? '保存中...' : '保存'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
