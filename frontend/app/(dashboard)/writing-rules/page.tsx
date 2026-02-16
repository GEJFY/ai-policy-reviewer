'use client'

import { useState, useEffect } from 'react'
import { Header } from '@/components/layout/header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { writingRulesAPI, WritingRule, WritingRuleCreate } from '@/lib/api'

const RULE_TYPES = [
  { value: 'STYLE', label: '文体ルール' },
  { value: 'FORMAT', label: 'フォーマットルール' },
  { value: 'TERMINOLOGY', label: '用語ルール' },
]

export default function WritingRulesPage() {
  const [rules, setRules] = useState<WritingRule[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedType, setSelectedType] = useState<string>('')
  const [showForm, setShowForm] = useState(false)
  const [editingRule, setEditingRule] = useState<WritingRule | null>(null)

  useEffect(() => {
    loadRules()
  }, [selectedType])

  async function loadRules() {
    try {
      setLoading(true)
      const data = await writingRulesAPI.list(
        selectedType ? { rule_type: selectedType } : undefined
      )
      setRules(data)
    } catch (error) {
      console.error('Failed to load writing rules:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('この記載ルールを削除しますか？')) return
    try {
      await writingRulesAPI.delete(id)
      loadRules()
    } catch (error) {
      console.error('Failed to delete writing rule:', error)
    }
  }

  async function handleToggleActive(rule: WritingRule) {
    try {
      await writingRulesAPI.update(rule.id, { is_active: !rule.is_active })
      loadRules()
    } catch (error) {
      console.error('Failed to update writing rule:', error)
    }
  }

  function getTypeLabel(value: string): string {
    return RULE_TYPES.find((t) => t.value === value)?.label || value
  }

  return (
    <>
      <Header title="記載ルール" />
      <div className="p-6">
        {/* Actions */}
        <div className="mb-6 flex items-center justify-between">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="rounded-md border border-gray-200 px-3 py-2 text-sm"
            aria-label="タイプでフィルタ"
          >
            <option value="">すべてのタイプ</option>
            {RULE_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <Button onClick={() => { setEditingRule(null); setShowForm(true); }}>
            <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
            新規登録
          </Button>
        </div>

        {/* Rules Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-center text-gray-500" role="status" aria-live="polite">読み込み中...</div>
            ) : rules.length === 0 ? (
              <div className="p-8 text-center text-gray-500" role="status">
                記載ルールが登録されていません
              </div>
            ) : (
              <table className="w-full" aria-label="記載ルール一覧">
                <thead className="border-b bg-gray-50">
                  <tr>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      ルール名
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      タイプ
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      状態
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      正しい形式
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {rules.map((rule) => (
                    <tr key={rule.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{rule.name}</td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">
                          {getTypeLabel(rule.rule_type)}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => handleToggleActive(rule)}
                          aria-pressed={rule.is_active}
                          className={`rounded-full px-2 py-1 text-xs ${
                            rule.is_active
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {rule.is_active ? '有効' : '無効'}
                        </button>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 max-w-md truncate">
                        {rule.correct_form}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => { setEditingRule(rule); setShowForm(true); }}
                            aria-label={`${rule.name}を編集`}
                          >
                            <Pencil className="h-4 w-4" aria-hidden="true" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(rule.id)}
                            aria-label={`${rule.name}を削除`}
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

        {/* Form Modal */}
        {showForm && (
          <WritingRuleFormModal
            rule={editingRule}
            onClose={() => { setShowForm(false); setEditingRule(null); }}
            onSaved={() => { setShowForm(false); setEditingRule(null); loadRules(); }}
          />
        )}
      </div>
    </>
  )
}

function WritingRuleFormModal({
  rule,
  onClose,
  onSaved,
}: {
  rule: WritingRule | null
  onClose: () => void
  onSaved: () => void
}) {
  const [formData, setFormData] = useState<WritingRuleCreate>({
    name: rule?.name || '',
    rule_type: rule?.rule_type || 'STYLE',
    pattern: rule?.pattern || '',
    correct_form: rule?.correct_form || '',
    example_bad: rule?.example_bad || '',
    example_good: rule?.example_good || '',
    is_active: rule?.is_active ?? true,
  })
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      if (rule) {
        await writingRulesAPI.update(rule.id, formData)
      } else {
        await writingRulesAPI.create(formData)
      }
      onSaved()
    } catch (error) {
      console.error('Failed to save writing rule:', error)
      alert('保存に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl max-h-[90vh] overflow-y-auto" role="dialog" aria-modal="true" aria-labelledby="writing-rule-form-title">
        <h3 id="writing-rule-form-title" className="mb-4 text-lg font-semibold">
          {rule ? '記載ルールを編集' : '記載ルールを登録'}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              ルール名 <span className="text-red-500">*</span>
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              タイプ <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.rule_type}
              onChange={(e) =>
                setFormData({ ...formData, rule_type: e.target.value })
              }
              className="w-full rounded-md border border-gray-200 px-3 py-2"
            >
              {RULE_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              検出パターン
            </label>
            <Input
              value={formData.pattern || ''}
              onChange={(e) =>
                setFormData({ ...formData, pattern: e.target.value })
              }
              placeholder="正規表現または説明"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              正しい形式 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.correct_form}
              onChange={(e) =>
                setFormData({ ...formData, correct_form: e.target.value })
              }
              required
              rows={2}
              className="w-full rounded-md border border-gray-200 px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              NG例
            </label>
            <Input
              value={formData.example_bad || ''}
              onChange={(e) =>
                setFormData({ ...formData, example_bad: e.target.value })
              }
              placeholder="悪い例"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              OK例
            </label>
            <Input
              value={formData.example_good || ''}
              onChange={(e) =>
                setFormData({ ...formData, example_good: e.target.value })
              }
              placeholder="良い例"
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
