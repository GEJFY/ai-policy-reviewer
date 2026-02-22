'use client'

import { useState, useEffect, useCallback } from 'react'
import { Header } from '@/components/layout/header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { HelpTooltip } from '@/components/ui/tooltip'
import {
  Plus,
  Trash2,
  ChevronRight,
  FileText,
  Download,
  Loader2,
  ArrowLeft,
  Check,
  X,
  AlertTriangle,
  Minus,
  Shuffle,
} from 'lucide-react'
import {
  comparisonsAPI,
  documentsAPI,
  ComparisonProject,
  ComparisonProjectDetail,
  ComparisonResult,
  Document,
} from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { useToast } from '@/components/ui/toast'
import { useConfirm } from '@/components/ui/confirm-dialog'
import { TIPS } from '@/lib/tooltip-texts'

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  COMPLIANT: { label: '適合', color: 'bg-green-100 text-green-800', icon: Check },
  STRICTER: { label: 'より厳格', color: 'bg-blue-100 text-blue-800', icon: ChevronRight },
  LOOSER: { label: '緩い', color: 'bg-orange-100 text-orange-800', icon: Minus },
  MISSING: { label: '欠落', color: 'bg-red-100 text-red-800', icon: X },
  DIFFERENT: { label: '異なる', color: 'bg-yellow-100 text-yellow-800', icon: Shuffle },
}

export default function ComparisonsPage() {
  const [projects, setProjects] = useState<ComparisonProject[]>([])
  const [selectedProject, setSelectedProject] = useState<ComparisonProjectDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const { showToast } = useToast()
  const { confirm } = useConfirm()

  const loadProjects = useCallback(async () => {
    try {
      const data = await comparisonsAPI.list()
      setProjects(data)
    } catch (error) {
      console.error('Failed to load projects:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadProjects()
  }, [loadProjects])

  async function handleSelectProject(id: number) {
    try {
      const detail = await comparisonsAPI.get(id)
      setSelectedProject(detail)
    } catch (error) {
      console.error('Failed to load project:', error)
      showToast('プロジェクトの読み込みに失敗しました', 'error')
    }
  }

  async function handleDelete(id: number) {
    const ok = await confirm({ message: 'この比較プロジェクトを削除しますか？' })
    if (!ok) return
    try {
      await comparisonsAPI.delete(id)
      showToast('プロジェクトを削除しました', 'success')
      if (selectedProject?.id === id) setSelectedProject(null)
      loadProjects()
    } catch (error) {
      console.error('Failed to delete project:', error)
      showToast('削除に失敗しました', 'error')
    }
  }

  function getStatusBadge(status: string) {
    const labels: Record<string, { text: string; variant: 'default' | 'secondary' | 'success' | 'warning' | 'destructive' }> = {
      created: { text: '作成済み', variant: 'secondary' },
      checklist_ready: { text: 'チェックリスト準備完了', variant: 'warning' },
      comparing: { text: '比較中', variant: 'warning' },
      completed: { text: '完了', variant: 'success' },
    }
    const info = labels[status] || { text: status, variant: 'secondary' as const }
    return <Badge variant={info.variant}>{info.text}</Badge>
  }

  return (
    <>
      <Header title="親子会社規程比較" />
      <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
        {/* Left: Project List */}
        <div className="w-96 border-r bg-white overflow-y-auto">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold">比較プロジェクト</h2>
                <HelpTooltip text={TIPS.comparisons?.description || '親会社と子会社の規程を比較し、差異を分析します。'} />
              </div>
              <Button size="sm" onClick={() => setShowCreate(true)}>
                <Plus className="mr-1 h-4 w-4" />
                新規
              </Button>
            </div>
          </div>

          {loading ? (
            <div className="p-8 text-center text-gray-500">読み込み中...</div>
          ) : projects.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              プロジェクトがありません
            </div>
          ) : (
            <div className="divide-y">
              {projects.map((p) => (
                <button
                  key={p.id}
                  onClick={() => handleSelectProject(p.id)}
                  className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${
                    selectedProject?.id === p.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-sm">{p.name}</span>
                    {getStatusBadge(p.status)}
                  </div>
                  <div className="mt-1 text-xs text-gray-500">
                    親: {p.parent_document_title}
                  </div>
                  {p.subsidiary_document_title && (
                    <div className="text-xs text-gray-500">
                      子: {p.subsidiary_document_title}
                    </div>
                  )}
                  <div className="mt-1 text-xs text-gray-400">
                    {formatDate(p.created_at)}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Project Detail / Wizard */}
        <div className="flex-1 overflow-y-auto bg-gray-50 p-6">
          {selectedProject ? (
            <ProjectDetail
              project={selectedProject}
              onUpdate={() => {
                handleSelectProject(selectedProject.id)
                loadProjects()
              }}
              onDelete={() => handleDelete(selectedProject.id)}
            />
          ) : (
            <div className="flex h-full items-center justify-center text-gray-400">
              左のリストからプロジェクトを選択してください
            </div>
          )}
        </div>
      </div>

      {showCreate && (
        <CreateProjectModal
          onClose={() => setShowCreate(false)}
          onCreate={(id) => {
            setShowCreate(false)
            loadProjects()
            handleSelectProject(id)
          }}
        />
      )}
    </>
  )
}

function ProjectDetail({
  project,
  onUpdate,
  onDelete,
}: {
  project: ComparisonProjectDetail
  onUpdate: () => void
  onDelete: () => void
}) {
  const { showToast } = useToast()
  const [generating, setGenerating] = useState(false)
  const [comparing, setComparing] = useState(false)
  const [showSubsidiaryModal, setShowSubsidiaryModal] = useState(false)
  const [editingChecklist, setEditingChecklist] = useState(false)
  const [editItems, setEditItems] = useState<{ item_text: string; category: string | null }[]>([])

  async function handleGenerateChecklist() {
    setGenerating(true)
    try {
      const result = await comparisonsAPI.generateChecklist(project.id)
      showToast(`${result.count}件のチェック項目を生成しました`, 'success')
      onUpdate()
    } catch (error: any) {
      showToast(error.message || 'チェックリスト生成に失敗しました', 'error')
    } finally {
      setGenerating(false)
    }
  }

  async function handleCompare() {
    setComparing(true)
    try {
      const result = await comparisonsAPI.compare(project.id)
      showToast(`${result.total}件の比較が完了しました`, 'success')
      onUpdate()
    } catch (error: any) {
      showToast(error.message || '比較に失敗しました', 'error')
    } finally {
      setComparing(false)
    }
  }

  async function handleExport() {
    try {
      await comparisonsAPI.exportExcel(project.id)
      showToast('Excelファイルをダウンロードしました', 'success')
    } catch (error: any) {
      showToast(error.message || 'エクスポートに失敗しました', 'error')
    }
  }

  function startEditChecklist() {
    setEditItems(project.check_items.map((ci) => ({
      item_text: ci.item_text,
      category: ci.category,
    })))
    setEditingChecklist(true)
  }

  async function saveChecklist() {
    try {
      await comparisonsAPI.updateChecklist(
        project.id,
        editItems.map((item) => ({
          item_text: item.item_text,
          category: item.category || undefined,
        }))
      )
      showToast('チェックリストを更新しました', 'success')
      setEditingChecklist(false)
      onUpdate()
    } catch (error: any) {
      showToast(error.message || '更新に失敗しました', 'error')
    }
  }

  // Determine current step
  let currentStep = 1
  if (project.status === 'checklist_ready' || project.check_items.length > 0) currentStep = 2
  if (project.subsidiary_document_id && project.check_items.length > 0) currentStep = 3
  if (project.status === 'completed' && project.results.length > 0) currentStep = 4

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">{project.name}</h2>
          {project.description && (
            <p className="text-sm text-gray-500 mt-1">{project.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          {project.results.length > 0 && (
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="mr-1 h-4 w-4" />
              Excel出力
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={onDelete}>
            <Trash2 className="h-4 w-4 text-red-500" />
          </Button>
        </div>
      </div>

      {/* Step Progress */}
      <div className="flex items-center gap-2">
        {[
          { num: 1, label: '親会社規程' },
          { num: 2, label: 'チェックリスト' },
          { num: 3, label: '子会社規程' },
          { num: 4, label: '比較結果' },
        ].map((step, i) => (
          <div key={step.num} className="flex items-center">
            {i > 0 && <div className={`w-8 h-0.5 ${currentStep > i ? 'bg-blue-500' : 'bg-gray-300'}`} />}
            <div
              className={`flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ${
                currentStep >= step.num
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-current/20 text-xs">
                {currentStep > step.num ? (
                  <Check className="h-3 w-3" />
                ) : (
                  step.num
                )}
              </span>
              {step.label}
            </div>
          </div>
        ))}
      </div>

      {/* Step 1: Parent Document */}
      <Card>
        <CardContent className="p-4">
          <h3 className="font-semibold mb-2">Step 1: 親会社規程</h3>
          <div className="flex items-center gap-2 text-sm">
            <FileText className="h-4 w-4 text-gray-400" />
            <span>{project.parent_document_title}</span>
            <Badge variant="success">選択済み</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Step 2: Checklist */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">Step 2: チェックリスト</h3>
            <div className="flex gap-2">
              {project.check_items.length > 0 && !editingChecklist && (
                <Button variant="outline" size="sm" onClick={startEditChecklist}>
                  編集
                </Button>
              )}
              <Button
                size="sm"
                onClick={handleGenerateChecklist}
                disabled={generating}
              >
                {generating ? (
                  <>
                    <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                    生成中...
                  </>
                ) : project.check_items.length > 0 ? (
                  '再生成'
                ) : (
                  'チェックリスト生成'
                )}
              </Button>
            </div>
          </div>

          {editingChecklist ? (
            <div className="space-y-2">
              {editItems.map((item, idx) => (
                <div key={idx} className="flex gap-2 items-start">
                  <span className="text-xs text-gray-400 mt-2 w-6">{idx + 1}</span>
                  <input
                    type="text"
                    value={item.category || ''}
                    onChange={(e) => {
                      const next = [...editItems]
                      next[idx] = { ...next[idx], category: e.target.value || null }
                      setEditItems(next)
                    }}
                    className="w-24 rounded border px-2 py-1 text-xs"
                    placeholder="カテゴリ"
                  />
                  <input
                    type="text"
                    value={item.item_text}
                    onChange={(e) => {
                      const next = [...editItems]
                      next[idx] = { ...next[idx], item_text: e.target.value }
                      setEditItems(next)
                    }}
                    className="flex-1 rounded border px-2 py-1 text-sm"
                  />
                  <button
                    onClick={() => setEditItems(editItems.filter((_, i) => i !== idx))}
                    className="text-red-400 hover:text-red-600 mt-1"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
              <div className="flex gap-2 mt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setEditItems([...editItems, { item_text: '', category: null }])}
                >
                  <Plus className="mr-1 h-3 w-3" />
                  項目追加
                </Button>
                <Button size="sm" onClick={saveChecklist}>
                  保存
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setEditingChecklist(false)}>
                  キャンセル
                </Button>
              </div>
            </div>
          ) : project.check_items.length > 0 ? (
            <div className="max-h-64 overflow-y-auto border rounded-md divide-y">
              {project.check_items.map((ci, idx) => (
                <div key={ci.id} className="flex items-start gap-2 p-2 text-sm">
                  <span className="text-xs text-gray-400 mt-0.5 w-6">{idx + 1}</span>
                  {ci.category && (
                    <Badge variant="secondary" className="text-xs shrink-0">
                      {ci.category}
                    </Badge>
                  )}
                  <span>{ci.item_text}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              チェックリストを生成してください。親会社規程からAIが自動的にチェック項目を抽出します。
            </p>
          )}
        </CardContent>
      </Card>

      {/* Step 3: Subsidiary Document */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">Step 3: 子会社規程</h3>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSubsidiaryModal(true)}
              disabled={project.check_items.length === 0}
            >
              {project.subsidiary_document_id ? '変更' : '文書を選択'}
            </Button>
          </div>
          {project.subsidiary_document_title ? (
            <div className="flex items-center gap-2 text-sm">
              <FileText className="h-4 w-4 text-gray-400" />
              <span>{project.subsidiary_document_title}</span>
              <Badge variant="success">選択済み</Badge>
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              比較対象の子会社規程を選択してください。
            </p>
          )}
        </CardContent>
      </Card>

      {/* Step 4: Compare & Results */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">Step 4: 比較実行・結果</h3>
            {project.subsidiary_document_id && project.check_items.length > 0 && (
              <Button
                size="sm"
                onClick={handleCompare}
                disabled={comparing}
              >
                {comparing ? (
                  <>
                    <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                    比較中...
                  </>
                ) : project.results.length > 0 ? (
                  '再比較'
                ) : (
                  '比較実行'
                )}
              </Button>
            )}
          </div>

          {project.results.length > 0 ? (
            <ComparisonResults results={project.results} />
          ) : (
            <p className="text-sm text-gray-500">
              {!project.subsidiary_document_id
                ? '子会社規程を選択してから比較を実行してください。'
                : project.check_items.length === 0
                ? 'チェックリストを生成してから比較を実行してください。'
                : '比較を実行すると、各チェック項目について親子間の差異が表示されます。'}
            </p>
          )}
        </CardContent>
      </Card>

      {showSubsidiaryModal && (
        <SelectDocumentModal
          title="子会社規程を選択"
          excludeDocId={project.parent_document_id}
          onClose={() => setShowSubsidiaryModal(false)}
          onSelect={async (docId) => {
            try {
              await comparisonsAPI.setSubsidiary(project.id, docId)
              showToast('子会社規程を設定しました', 'success')
              setShowSubsidiaryModal(false)
              onUpdate()
            } catch (error: any) {
              showToast(error.message || '設定に失敗しました', 'error')
            }
          }}
        />
      )}
    </div>
  )
}

function ComparisonResults({ results }: { results: ComparisonResult[] }) {
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const statusCounts: Record<string, number> = {}
  for (const r of results) {
    statusCounts[r.status] = (statusCounts[r.status] || 0) + 1
  }

  return (
    <div className="space-y-4">
      {/* Summary badges */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
          <div
            key={key}
            className={`flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ${cfg.color}`}
          >
            <cfg.icon className="h-3 w-3" />
            {cfg.label}: {statusCounts[key] || 0}
          </div>
        ))}
      </div>

      {/* Results list */}
      <div className="border rounded-md divide-y max-h-96 overflow-y-auto">
        {results.map((r) => {
          const cfg = STATUS_CONFIG[r.status] || STATUS_CONFIG.DIFFERENT
          const isExpanded = expandedId === r.id
          return (
            <div key={r.id}>
              <button
                onClick={() => setExpandedId(isExpanded ? null : r.id)}
                className="w-full flex items-center gap-2 p-3 text-left hover:bg-gray-50"
              >
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${cfg.color}`}>
                  {cfg.label}
                </span>
                <span className="flex-1 text-sm">{r.check_item_text}</span>
                <ChevronRight
                  className={`h-4 w-4 text-gray-400 transition-transform ${
                    isExpanded ? 'rotate-90' : ''
                  }`}
                />
              </button>
              {isExpanded && (
                <div className="px-3 pb-3 space-y-2 bg-gray-50">
                  {r.parent_text && (
                    <div>
                      <span className="text-xs font-medium text-gray-500">親会社規程:</span>
                      <p className="text-sm text-gray-700 bg-white rounded p-2 mt-1">
                        {r.parent_text}
                      </p>
                    </div>
                  )}
                  {r.subsidiary_text && (
                    <div>
                      <span className="text-xs font-medium text-gray-500">子会社規程:</span>
                      <p className="text-sm text-gray-700 bg-white rounded p-2 mt-1">
                        {r.subsidiary_text}
                      </p>
                    </div>
                  )}
                  {r.explanation && (
                    <div>
                      <span className="text-xs font-medium text-gray-500">説明:</span>
                      <p className="text-sm text-gray-600 mt-1">{r.explanation}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function CreateProjectModal({
  onClose,
  onCreate,
}: {
  onClose: () => void
  onCreate: (id: number) => void
}) {
  const { showToast } = useToast()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedParent, setSelectedParent] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const docs = await documentsAPI.list({ ocr_status: 'completed' })
        setDocuments(docs)
      } catch (error) {
        console.error('Failed to load documents:', error)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  async function handleCreate() {
    if (!name.trim() || !selectedParent) return
    setCreating(true)
    try {
      const project = await comparisonsAPI.create({
        name: name.trim(),
        description: description.trim() || undefined,
        parent_document_id: selectedParent,
      })
      showToast('プロジェクトを作成しました', 'success')
      onCreate(project.id)
    } catch (error: any) {
      showToast(error.message || '作成に失敗しました', 'error')
      setCreating(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl max-h-[80vh] overflow-y-auto">
        <h3 className="mb-4 text-lg font-semibold">比較プロジェクト作成</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              プロジェクト名 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border px-3 py-2 text-sm"
              placeholder="例: 情報セキュリティポリシー比較"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              説明
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full rounded-md border px-3 py-2 text-sm"
              placeholder="比較の目的や背景など"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              親会社規程を選択 <span className="text-red-500">*</span>
            </label>
            {loading ? (
              <div className="py-4 text-center text-gray-500">読み込み中...</div>
            ) : documents.length === 0 ? (
              <div className="py-4 text-center text-gray-500">
                OCR完了済みの文書がありません
              </div>
            ) : (
              <div className="max-h-48 overflow-y-auto border rounded-md divide-y">
                {documents.map((doc) => (
                  <label
                    key={doc.id}
                    className="flex items-center gap-3 p-3 hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type="radio"
                      name="parent_doc"
                      checked={selectedParent === doc.id}
                      onChange={() => setSelectedParent(doc.id)}
                      className="h-4 w-4"
                    />
                    <FileText className="h-4 w-4 text-gray-400" />
                    <span className="text-sm">{doc.title}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <Button variant="outline" onClick={onClose} disabled={creating}>
            キャンセル
          </Button>
          <Button
            onClick={handleCreate}
            disabled={creating || !name.trim() || !selectedParent}
          >
            {creating ? (
              <>
                <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                作成中...
              </>
            ) : (
              '作成'
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}

function SelectDocumentModal({
  title,
  excludeDocId,
  onClose,
  onSelect,
}: {
  title: string
  excludeDocId?: number
  onClose: () => void
  onSelect: (docId: number) => void
}) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<number | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const docs = await documentsAPI.list({ ocr_status: 'completed' })
        setDocuments(docs.filter((d) => d.id !== excludeDocId))
      } catch (error) {
        console.error('Failed to load documents:', error)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [excludeDocId])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl max-h-[70vh] overflow-y-auto">
        <h3 className="mb-4 text-lg font-semibold">{title}</h3>

        {loading ? (
          <div className="py-4 text-center text-gray-500">読み込み中...</div>
        ) : documents.length === 0 ? (
          <div className="py-4 text-center text-gray-500">
            選択可能な文書がありません
          </div>
        ) : (
          <div className="max-h-64 overflow-y-auto border rounded-md divide-y">
            {documents.map((doc) => (
              <label
                key={doc.id}
                className="flex items-center gap-3 p-3 hover:bg-gray-50 cursor-pointer"
              >
                <input
                  type="radio"
                  name="select_doc"
                  checked={selected === doc.id}
                  onChange={() => setSelected(doc.id)}
                  className="h-4 w-4"
                />
                <FileText className="h-4 w-4 text-gray-400" />
                <span className="text-sm">{doc.title}</span>
              </label>
            ))}
          </div>
        )}

        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" onClick={onClose}>
            キャンセル
          </Button>
          <Button
            onClick={() => selected && onSelect(selected)}
            disabled={!selected}
          >
            選択
          </Button>
        </div>
      </div>
    </div>
  )
}
