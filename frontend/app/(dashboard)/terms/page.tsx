'use client'

import { useState, useEffect } from 'react'
import { Header } from '@/components/layout/header'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Plus, Search, Pencil, Trash2, Upload, FileSpreadsheet } from 'lucide-react'
import { termsAPI, Term, TermCreate } from '@/lib/api'
import { ImportModal } from '@/components/import-modal'
import { formatDate } from '@/lib/utils'
import { HelpTooltip } from '@/components/ui/tooltip'
import { TIPS } from '@/lib/tooltip-texts'

const CATEGORIES = ['人事', '財務', 'IT', '法務', '一般']

export default function TermsPage() {
  const [terms, setTerms] = useState<Term[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [showForm, setShowForm] = useState(false)
  const [showImport, setShowImport] = useState(false)
  const [editingTerm, setEditingTerm] = useState<Term | null>(null)

  useEffect(() => {
    loadTerms()
  }, [selectedCategory])

  async function loadTerms() {
    try {
      setLoading(true)
      const data = await termsAPI.list(
        selectedCategory ? { category: selectedCategory } : undefined
      )
      setTerms(data)
    } catch (error) {
      console.error('Failed to load terms:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('この用語を削除しますか？')) return
    try {
      await termsAPI.delete(id)
      loadTerms()
    } catch (error) {
      console.error('Failed to delete term:', error)
    }
  }

  async function handleSearch() {
    if (!searchQuery.trim()) {
      loadTerms()
      return
    }
    try {
      setLoading(true)
      const data = await termsAPI.search(searchQuery)
      setTerms(data)
    } catch (error) {
      console.error('Search failed:', error)
      // Fallback to regular list
      loadTerms()
    } finally {
      setLoading(false)
    }
  }

  const filteredTerms = terms.filter(
    (term) =>
      !searchQuery ||
      term.term.includes(searchQuery) ||
      term.definition.includes(searchQuery)
  )

  return (
    <>
      <Header title="用語辞書" />
      <div className="p-6">
        {/* Actions */}
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" aria-hidden="true" />
              <Input
                placeholder="用語を検索..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-9 w-64"
                aria-label="用語を検索"
              />
            </div>
            <Button variant="outline" onClick={handleSearch}>
              検索
            </Button>
          </div>
          <div className="flex gap-2">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="rounded-md border border-gray-200 px-3 py-2 text-sm"
            >
              <option value="">すべてのカテゴリ</option>
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
            <Button variant="outline" onClick={() => setShowImport(true)}>
              <Upload className="mr-2 h-4 w-4" aria-hidden="true" />
              インポート
            </Button>
            <Button onClick={() => { setEditingTerm(null); setShowForm(true); }}>
              <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
              新規登録
            </Button>
          </div>
        </div>

        {/* Terms Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-center text-gray-500" role="status" aria-live="polite">読み込み中...</div>
            ) : filteredTerms.length === 0 ? (
              <div className="p-8 text-center text-gray-500" role="status">
                用語が登録されていません
              </div>
            ) : (
              <table className="w-full" aria-label="用語辞書一覧">
                <thead className="border-b bg-gray-50">
                  <tr>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      用語 <HelpTooltip text={TIPS.terms.term} />
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      別名 <HelpTooltip text={TIPS.terms.aliases} />
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      カテゴリ <HelpTooltip text={TIPS.terms.category} />
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      定義 <HelpTooltip text={TIPS.terms.definition} />
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredTerms.map((term) => (
                    <tr key={term.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{term.term}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {term.aliases?.join(', ') || '-'}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="secondary">{term.category}</Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 max-w-md truncate">
                        {term.definition}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => { setEditingTerm(term); setShowForm(true); }}
                            aria-label={`${term.term}を編集`}
                          >
                            <Pencil className="h-4 w-4" aria-hidden="true" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(term.id)}
                            aria-label={`${term.term}を削除`}
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
          <TermFormModal
            term={editingTerm}
            onClose={() => { setShowForm(false); setEditingTerm(null); }}
            onSaved={() => { setShowForm(false); setEditingTerm(null); loadTerms(); }}
          />
        )}

        {/* Import Modal */}
        {showImport && (
          <ImportModal
            title="用語辞書インポート"
            onClose={() => setShowImport(false)}
            onImport={(file) => termsAPI.importFile(file)}
            onDownloadTemplate={() => termsAPI.downloadTemplate()}
            onSuccess={() => loadTerms()}
          />
        )}
      </div>
    </>
  )
}

function TermFormModal({
  term,
  onClose,
  onSaved,
}: {
  term: Term | null
  onClose: () => void
  onSaved: () => void
}) {
  const [formData, setFormData] = useState<TermCreate>({
    term: term?.term || '',
    aliases: term?.aliases || [],
    definition: term?.definition || '',
    category: term?.category || '一般',
    usage_note: term?.usage_note || '',
  })
  const [aliasInput, setAliasInput] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      if (term) {
        await termsAPI.update(term.id, formData)
      } else {
        await termsAPI.create(formData)
      }
      onSaved()
    } catch (error) {
      console.error('Failed to save term:', error)
      alert('保存に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  function addAlias() {
    if (aliasInput.trim() && !formData.aliases?.includes(aliasInput.trim())) {
      setFormData({
        ...formData,
        aliases: [...(formData.aliases || []), aliasInput.trim()],
      })
      setAliasInput('')
    }
  }

  function removeAlias(alias: string) {
    setFormData({
      ...formData,
      aliases: formData.aliases?.filter((a) => a !== alias) || [],
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl" role="dialog" aria-modal="true" aria-labelledby="term-form-title">
        <h3 id="term-form-title" className="mb-4 text-lg font-semibold">
          {term ? '用語を編集' : '用語を登録'}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              用語 <span className="text-red-500">*</span>
            </label>
            <Input
              value={formData.term}
              onChange={(e) => setFormData({ ...formData, term: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              別名
            </label>
            <div className="flex gap-2">
              <Input
                value={aliasInput}
                onChange={(e) => setAliasInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addAlias()
                  }
                }}
                placeholder="別名を入力してEnter"
              />
              <Button type="button" variant="outline" onClick={addAlias}>
                追加
              </Button>
            </div>
            {formData.aliases && formData.aliases.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {formData.aliases.map((alias) => (
                  <Badge key={alias} variant="secondary">
                    {alias}
                    <button
                      type="button"
                      onClick={() => removeAlias(alias)}
                      className="ml-1 hover:text-red-500"
                      aria-label="エイリアスを削除"
                    >
                      ×
                    </button>
                  </Badge>
                ))}
              </div>
            )}
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
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              定義 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.definition}
              onChange={(e) =>
                setFormData({ ...formData, definition: e.target.value })
              }
              required
              rows={3}
              className="w-full rounded-md border border-gray-200 px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              使用上の注意
            </label>
            <textarea
              value={formData.usage_note || ''}
              onChange={(e) =>
                setFormData({ ...formData, usage_note: e.target.value })
              }
              rows={2}
              className="w-full rounded-md border border-gray-200 px-3 py-2"
            />
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
