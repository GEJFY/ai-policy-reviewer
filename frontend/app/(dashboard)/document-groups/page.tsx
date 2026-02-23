'use client'

import { useState, useEffect } from 'react'
import { Header } from '@/components/layout/header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Plus,
  Trash2,
  RefreshCw,
  AlertCircle,
  FolderSync,
  FileText,
  Play,
  X,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import {
  documentGroupsAPI,
  documentsAPI,
  DocumentGroup,
  DocumentGroupDetail,
  Document,
  ConsistencyCheckResult,
  ConsistencyFinding,
} from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { HelpTooltip } from '@/components/ui/tooltip'
import { TIPS } from '@/lib/tooltip-texts'

export default function DocumentGroupsPage() {
  const [groups, setGroups] = useState<DocumentGroup[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [selectedGroup, setSelectedGroup] = useState<DocumentGroupDetail | null>(null)
  const [checkResult, setCheckResult] = useState<ConsistencyCheckResult | null>(null)
  const [checking, setChecking] = useState(false)
  const [checkProgress, setCheckProgress] = useState(0)
  const [checkTotal, setCheckTotal] = useState(0)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [groupsData, docsData] = await Promise.all([
        documentGroupsAPI.list(),
        documentsAPI.list(),
      ])
      setGroups(groupsData)
      setDocuments(docsData.filter((d: Document) => d.ocr_status === 'completed'))
      setError(null)
    } catch (e) {
      console.error('Failed to load data:', e)
      setError('データの読み込みに失敗しました')
    } finally {
      setLoading(false)
    }
  }

  async function handleSelectGroup(groupId: number) {
    try {
      const detail = await documentGroupsAPI.get(groupId)
      setSelectedGroup(detail)
      setCheckResult(null)
    } catch (e) {
      console.error('Failed to load group:', e)
    }
  }

  async function handleDeleteGroup(groupId: number) {
    try {
      await documentGroupsAPI.delete(groupId)
      setGroups((prev) => prev.filter((g) => g.id !== groupId))
      if (selectedGroup?.id === groupId) {
        setSelectedGroup(null)
        setCheckResult(null)
      }
    } catch (e) {
      console.error('Failed to delete group:', e)
    }
  }

  async function handleRunCheck() {
    if (!selectedGroup) return
    setChecking(true)
    setCheckResult(null)
    setCheckProgress(0)
    setCheckTotal(0)
    try {
      const job = await documentGroupsAPI.runConsistencyCheck(selectedGroup.id)
      setCheckTotal(job.total_pairs)

      // Poll for status every 2 seconds
      while (true) {
        await new Promise((r) => setTimeout(r, 2000))
        try {
          const status = await documentGroupsAPI.getConsistencyCheckStatus(
            selectedGroup.id,
            job.job_id
          )
          if ('findings' in status) {
            // Completed - got full ConsistencyCheckResult
            setCheckResult(status as ConsistencyCheckResult)
            return
          }
          const jobStatus = status as {
            status: string
            total_pairs: number
            completed_pairs: number
            error?: string
          }
          setCheckProgress(jobStatus.completed_pairs)
          setCheckTotal(jobStatus.total_pairs)
          if (jobStatus.status === 'failed') {
            setError(jobStatus.error || '整合性チェック処理中にエラーが発生しました')
            return
          }
        } catch {
          setError('ステータスの取得に失敗しました')
          return
        }
      }
    } catch (e: any) {
      console.error('Failed to run consistency check:', e)
      setError(e.message || '整合性チェックの開始に失敗しました。LLM設定を確認してください。')
    } finally {
      setChecking(false)
    }
  }

  async function handleAddMember(documentId: number) {
    if (!selectedGroup) return
    try {
      await documentGroupsAPI.addMember(selectedGroup.id, documentId)
      const detail = await documentGroupsAPI.get(selectedGroup.id)
      setSelectedGroup(detail)
      loadData()
    } catch (e) {
      console.error('Failed to add member:', e)
    }
  }

  async function handleRemoveMember(documentId: number) {
    if (!selectedGroup) return
    try {
      await documentGroupsAPI.removeMember(selectedGroup.id, documentId)
      const detail = await documentGroupsAPI.get(selectedGroup.id)
      setSelectedGroup(detail)
      loadData()
    } catch (e) {
      console.error('Failed to remove member:', e)
    }
  }

  if (loading) {
    return (
      <>
        <Header title="規程グループ" />
        <div className="p-6">
          <div className="text-center text-gray-500">読み込み中...</div>
        </div>
      </>
    )
  }

  return (
    <>
      <Header title="規程グループ" />
      <div className="p-6">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <p className="text-sm text-gray-500">
              関連する規程文書をグループ化し、整合性チェックを実行できます
            </p>
            <HelpTooltip text={TIPS.documentGroups?.description || '複数の規程文書間の矛盾や不整合をAIが検出します'} />
          </div>
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="mr-1 h-4 w-4" aria-hidden="true" />
            新規グループ
          </Button>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">
            <AlertCircle className="mr-1 inline h-4 w-4" />
            {error}
            <button onClick={() => setError(null)} className="ml-2 text-red-500 hover:text-red-700">
              <X className="inline h-3 w-3" />
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Group List */}
          <div className="space-y-3">
            <h2 className="text-sm font-medium text-gray-700">グループ一覧</h2>
            {groups.length === 0 ? (
              <Card>
                <CardContent className="p-6 text-center text-gray-500">
                  <FolderSync className="mx-auto mb-2 h-8 w-8 text-gray-300" />
                  <p>グループがありません</p>
                  <p className="text-xs mt-1">「新規グループ」から作成してください</p>
                </CardContent>
              </Card>
            ) : (
              groups.map((group) => (
                <Card
                  key={group.id}
                  className={`cursor-pointer transition-colors hover:border-blue-300 ${
                    selectedGroup?.id === group.id ? 'border-blue-500 bg-blue-50' : ''
                  }`}
                  onClick={() => handleSelectGroup(group.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{group.name}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {group.member_count} 文書 · {formatDate(group.created_at)}
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteGroup(group.id)
                        }}
                        className="text-gray-400 hover:text-red-500"
                        title="グループ削除"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>

          {/* Group Detail */}
          <div className="lg:col-span-2">
            {selectedGroup ? (
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>{selectedGroup.name}</span>
                      <Button
                        onClick={handleRunCheck}
                        disabled={checking || selectedGroup.members.length < 2}
                      >
                        {checking ? (
                          <>
                            <RefreshCw className="mr-1 h-4 w-4 animate-spin" aria-hidden="true" />
                            チェック中... {checkTotal > 0 ? `${checkProgress}/${checkTotal}` : ''}
                          </>
                        ) : (
                          <>
                            <Play className="mr-1 h-4 w-4" aria-hidden="true" />
                            整合性チェック実行
                          </>
                        )}
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {selectedGroup.description && (
                      <p className="text-sm text-gray-600 mb-4">{selectedGroup.description}</p>
                    )}

                    <h3 className="text-sm font-medium text-gray-700 mb-2">メンバー文書</h3>
                    <div className="space-y-2">
                      {selectedGroup.members.map((m) => (
                        <div
                          key={m.document_id}
                          className="flex items-center justify-between rounded-md border p-3"
                        >
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-gray-400" />
                            <span className="text-sm">{m.document_title}</span>
                          </div>
                          <button
                            onClick={() => handleRemoveMember(m.document_id)}
                            className="text-gray-400 hover:text-red-500"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      ))}
                    </div>

                    {/* Add member */}
                    <div className="mt-3">
                      <select
                        onChange={(e) => {
                          const docId = Number(e.target.value)
                          if (docId) handleAddMember(docId)
                          e.target.value = ''
                        }}
                        className="rounded-md border border-gray-200 px-3 py-2 text-sm w-full"
                        defaultValue=""
                      >
                        <option value="" disabled>文書を追加...</option>
                        {documents
                          .filter((d) => !selectedGroup.members.some((m) => m.document_id === d.id))
                          .map((d) => (
                            <option key={d.id} value={d.id}>{d.title}</option>
                          ))}
                      </select>
                    </div>

                    {selectedGroup.members.length < 2 && (
                      <p className="mt-3 text-xs text-amber-600">
                        整合性チェックには2つ以上の文書が必要です
                      </p>
                    )}
                  </CardContent>
                </Card>

                {/* Consistency Check Progress */}
                {checking && checkTotal > 0 && (
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                        <span>整合性チェック進捗</span>
                        <span>{checkProgress} / {checkTotal} ペア</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${checkTotal > 0 ? (checkProgress / checkTotal) * 100 : 0}%` }}
                        />
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Consistency Check Results */}
                {checkResult && (
                  <ConsistencyResults result={checkResult} />
                )}
              </div>
            ) : (
              <Card>
                <CardContent className="p-12 text-center text-gray-500">
                  <FolderSync className="mx-auto mb-3 h-12 w-12 text-gray-300" />
                  <p>グループを選択してください</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Create Group Modal */}
        {showCreate && (
          <CreateGroupModal
            documents={documents}
            onClose={() => setShowCreate(false)}
            onCreate={async (name, description, docIds) => {
              await documentGroupsAPI.create(name, description, docIds)
              setShowCreate(false)
              loadData()
            }}
          />
        )}
      </div>
    </>
  )
}

function ConsistencyResults({ result }: { result: ConsistencyCheckResult }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ HIGH: true, MEDIUM: true, LOW: false })

  const grouped: Record<string, ConsistencyFinding[]> = { HIGH: [], MEDIUM: [], LOW: [] }
  result.findings.forEach((f) => {
    if (grouped[f.severity]) grouped[f.severity].push(f)
    else grouped[f.severity] = [f]
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>整合性チェック結果</span>
          <div className="flex gap-2">
            <Badge variant="destructive">{result.high_count} HIGH</Badge>
            <Badge variant="warning">{result.medium_count} MED</Badge>
            <Badge variant="secondary">{result.low_count} LOW</Badge>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {result.total_findings === 0 ? (
          <p className="text-center text-gray-500 py-4">不整合は検出されませんでした</p>
        ) : (
          <div className="space-y-4">
            {(['HIGH', 'MEDIUM', 'LOW'] as const).map((severity) => {
              const items = grouped[severity] || []
              if (items.length === 0) return null
              const isExpanded = expanded[severity]
              const colors = {
                HIGH: 'bg-red-50 border-red-200',
                MEDIUM: 'bg-yellow-50 border-yellow-200',
                LOW: 'bg-blue-50 border-blue-200',
              }
              const borderColors = {
                HIGH: 'border-l-red-500',
                MEDIUM: 'border-l-yellow-500',
                LOW: 'border-l-blue-400',
              }

              return (
                <div key={severity}>
                  <button
                    onClick={() => setExpanded((prev) => ({ ...prev, [severity]: !prev[severity] }))}
                    className={`w-full flex items-center justify-between rounded-lg border p-2 mb-2 ${colors[severity]}`}
                  >
                    <div className="flex items-center gap-2">
                      {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      <span className="font-medium text-sm">{severity}</span>
                      <span className="text-xs text-gray-500">{items.length} 件</span>
                    </div>
                  </button>
                  {isExpanded && (
                    <div className="space-y-2 ml-2">
                      {items.map((finding, idx) => (
                        <div key={idx} className={`rounded-lg border border-l-4 p-3 ${borderColors[severity]}`}>
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant="outline">{finding.issue_type}</Badge>
                            <span className="text-xs text-gray-500">
                              {finding.document_a_title} ↔ {finding.document_b_title}
                            </span>
                          </div>
                          <p className="text-sm mb-2">{finding.description}</p>
                          <div className="grid grid-cols-2 gap-2">
                            {finding.text_a && (
                              <div className="rounded bg-red-50 p-2 text-xs">
                                <span className="font-medium text-gray-500">{finding.location_a || '文書A'}:</span>
                                <br />{finding.text_a}
                              </div>
                            )}
                            {finding.text_b && (
                              <div className="rounded bg-blue-50 p-2 text-xs">
                                <span className="font-medium text-gray-500">{finding.location_b || '文書B'}:</span>
                                <br />{finding.text_b}
                              </div>
                            )}
                          </div>
                          {finding.suggestion && (
                            <div className="mt-2 rounded bg-green-50 p-2 text-xs">
                              <span className="font-medium text-gray-500">改善提案:</span> {finding.suggestion}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function CreateGroupModal({
  documents,
  onClose,
  onCreate,
}: {
  documents: Document[]
  onClose: () => void
  onCreate: (name: string, description: string, docIds: number[]) => Promise<void>
}) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [selectedDocs, setSelectedDocs] = useState<number[]>([])
  const [creating, setCreating] = useState(false)

  function toggleDoc(id: number) {
    setSelectedDocs((prev) => (prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]))
  }

  async function handleSubmit() {
    if (!name.trim()) return
    setCreating(true)
    try {
      await onCreate(name, description, selectedDocs)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold">新規グループ作成</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700">グループ名</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例: 人事関連規程"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">説明（任意）</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="グループの説明..."
              rows={2}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">
              文書を選択（{selectedDocs.length} 件選択中）
            </label>
            <div className="mt-1 max-h-48 overflow-y-auto rounded-md border p-2 space-y-1">
              {documents.map((doc) => (
                <label key={doc.id} className="flex items-center gap-2 cursor-pointer p-1 hover:bg-gray-50 rounded">
                  <input
                    type="checkbox"
                    checked={selectedDocs.includes(doc.id)}
                    onChange={() => toggleDoc(doc.id)}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <span className="text-sm">{doc.title}</span>
                </label>
              ))}
              {documents.length === 0 && (
                <p className="text-sm text-gray-400 text-center py-2">OCR完了済みの文書がありません</p>
              )}
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>キャンセル</Button>
          <Button onClick={handleSubmit} disabled={!name.trim() || creating}>
            {creating && <RefreshCw className="mr-1 h-4 w-4 animate-spin" />}
            作成
          </Button>
        </div>
      </div>
    </div>
  )
}
