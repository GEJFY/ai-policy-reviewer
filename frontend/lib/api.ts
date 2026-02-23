/**
 * API Client for Policy Review Tool
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Helper: get auth headers from localStorage
function getAuthHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {}
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Helper: attempt token refresh on 401
async function tryRefreshToken(): Promise<string | null> {
  if (typeof window === 'undefined') return null
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) return null

  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!res.ok) return null
    const data = await res.json()
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    return data.access_token
  } catch {
    return null
  }
}

// Generic fetch wrapper with timeout and auth
export async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 120000)

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...options?.headers,
      },
      ...options,
      signal: controller.signal,
    })

  // Handle 401: try refresh token
  if (response.status === 401) {
    const newToken = await tryRefreshToken()
    if (newToken) {
      const retryResponse = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${newToken}`,
          ...options?.headers,
        },
        ...options,
        signal: controller.signal,
      })
      if (retryResponse.ok) {
        if (retryResponse.status === 204) return null as T
        return retryResponse.json()
      }
    }
    // Refresh failed: clear tokens and redirect to login
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    throw new Error('認証が切れました。再度ログインしてください。')
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `API Error: ${response.status}`)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T
  }

  return response.json()
  } catch (err: any) {
    if (err.name === 'AbortError') {
      throw new Error('サーバーに接続できません。バックエンドが起動しているか確認してください。')
    }
    throw err
  } finally {
    clearTimeout(timeout)
  }
}

// Types
export interface Term {
  id: number
  term: string
  aliases: string[] | null
  definition: string
  category: string
  usage_note: string | null
  created_at: string
  updated_at: string
}

export interface TermCreate {
  term: string
  aliases?: string[]
  definition: string
  category: string
  usage_note?: string
}

export interface CheckItem {
  id: number
  name: string
  category: string
  description: string
  severity: string
  prompt_template: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CheckItemCreate {
  name: string
  category: string
  description: string
  severity: string
  prompt_template?: string
  is_active?: boolean
}

export interface WritingRule {
  id: number
  name: string
  rule_type: string
  pattern: string | null
  correct_form: string
  example_bad: string | null
  example_good: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface WritingRuleCreate {
  name: string
  rule_type: string
  pattern?: string
  correct_form: string
  example_bad?: string
  example_good?: string
  is_active?: boolean
}

export interface Document {
  id: number
  title: string
  file_path: string
  file_type: string | null
  extracted_text: string | null
  ocr_status: string
  ocr_progress: string | null
  created_at: string
  updated_at: string
}

export interface Review {
  id: number
  document_id: number
  status: string
  created_at: string
  completed_at: string | null
  document_title?: string
  finding_count?: number
  high_count?: number
  medium_count?: number
  low_count?: number
}

export interface Finding {
  id: number
  review_id: number
  check_item_id: number | null
  location: string | null
  original_text: string | null
  issue_type: string
  severity: string
  description: string
  suggestion: string | null
  rationale: string | null
  confidence: number | null
  status: string
  reviewed_by: string | null
  reviewed_at: string | null
  comment: string | null
  edited_suggestion: string | null
  created_at: string
}

export interface FindingContext {
  finding_id: number
  context_text: string
  highlight_start: number
  highlight_end: number
  original_text: string | null
  suggestion: string | null
  corrected_text: string
}

export interface RevisedText {
  review_id: number
  original_text: string
  revised_text: string
  changes_applied: number
  total_approved: number
}

// Settings types
export interface SystemSettings {
  system: {
    version: string
    debug: boolean
    database_url: string
  }
  llm: {
    provider: string
    model: string
    tier: string | null
    available_providers: string[]
  }
  providers: {
    azure: {
      configured: boolean
      endpoint: string
      api_key: string
      deployment: string
      embedding_deployment: string
      api_version: string
      use_v1_api: boolean
    }
    aws_bedrock: {
      configured: boolean
      region: string
      access_key_id: string
      model_id: string
      embedding_model: string
    }
    gcp_vertex: {
      configured: boolean
      project_id: string
      location: string
      model: string
      embedding_model: string
      credentials_path: boolean
    }
    ollama: {
      configured: boolean
      base_url: string
      model: string
      embedding_model: string
    }
  }
  embedding: {
    provider: string
  }
  ocr: {
    provider: string
    azure_doc_intel: {
      configured: boolean
      endpoint: string
    }
    tesseract: {
      configured: boolean
      lang: string
    }
  }
  app: {
    upload_dir: string
    max_file_size_mb: number
    cors_origins: string[]
  }
  validation: {
    is_valid: boolean
    missing: string[]
    warnings: string[]
  }
}

export interface HealthDetailed {
  status: string
  version: string
  environment: string
  checks: {
    database: { healthy: boolean; latency_ms?: number; error?: string }
    llm_service: {
      healthy: boolean
      active_provider: string | null
      available_providers: string[]
      error?: string
    }
    ocr_service: {
      healthy: boolean
      active_provider: string
      available_providers: string[]
      configured: boolean
      note: string | null
      error?: string
    }
  }
  circuit_breakers: Record<string, {
    state: string
    failure_count: number
    time_until_retry: number | null
    stats: { total_calls: number; failed_calls: number; rejected_calls: number }
  }>
  timestamp: string
}

// Dashboard types
export interface DashboardStats {
  document_count: number
  review_count: number
  term_count: number
  check_item_count: number
  writing_rule_count: number
  finding_total: number
  finding_by_severity: { high: number; medium: number; low: number }
  finding_by_status: { pending: number; approved: number; rejected: number; deferred: number }
  review_by_status: { pending: number; processing: number; completed: number; failed: number }
}

// Import result type
export interface ImportResult {
  success: number
  errors: string[]
}

// Helper: download file from URL
async function downloadFile(url: string, fallbackFilename: string) {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error('ダウンロードに失敗しました')
  }
  const blob = await response.blob()
  const blobUrl = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = blobUrl
  a.download = fallbackFilename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(blobUrl)
}

// Helper: upload file for import
async function uploadImportFile(url: string, file: File): Promise<ImportResult> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'インポートに失敗しました')
  }
  return response.json()
}

// API Functions

// Dashboard
export const dashboardAPI = {
  getStats: () => fetchAPI<DashboardStats>('/api/v1/dashboard/stats'),
}

// Settings
export const settingsAPI = {
  get: () => fetchAPI<SystemSettings>('/api/v1/settings/'),
  getModels: () => fetchAPI<{ models: Record<string, { tier: string; model: string }[]> }>('/api/v1/settings/models'),
  getHealth: () => fetchAPI<HealthDetailed>('/health/detailed'),
}

// Terms
export const termsAPI = {
  list: (params?: { category?: string }) => {
    const query = params?.category ? `?category=${params.category}` : ''
    return fetchAPI<Term[]>(`/api/v1/terms${query}`)
  },
  get: (id: number) => fetchAPI<Term>(`/api/v1/terms/${id}`),
  create: (data: TermCreate) =>
    fetchAPI<Term>('/api/v1/terms', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Partial<TermCreate>) =>
    fetchAPI<Term>(`/api/v1/terms/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  delete: (id: number) =>
    fetchAPI<void>(`/api/v1/terms/${id}`, { method: 'DELETE' }),
  search: (query: string, top_k?: number) =>
    fetchAPI<Term[]>('/api/v1/terms/search', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: top_k || 10 }),
    }),
  downloadTemplate: () => downloadFile(`${API_BASE}/api/v1/terms/template`, 'terms_template.csv'),
  importFile: (file: File) => uploadImportFile(`${API_BASE}/api/v1/terms/import`, file),
}

// Check Items
export const checkItemsAPI = {
  list: (params?: { category?: string; is_active?: boolean }) => {
    const searchParams = new URLSearchParams()
    if (params?.category) searchParams.set('category', params.category)
    if (params?.is_active !== undefined)
      searchParams.set('is_active', String(params.is_active))
    const query = searchParams.toString() ? `?${searchParams}` : ''
    return fetchAPI<CheckItem[]>(`/api/v1/check-items${query}`)
  },
  get: (id: number) => fetchAPI<CheckItem>(`/api/v1/check-items/${id}`),
  create: (data: CheckItemCreate) =>
    fetchAPI<CheckItem>('/api/v1/check-items', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Partial<CheckItemCreate>) =>
    fetchAPI<CheckItem>(`/api/v1/check-items/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  delete: (id: number) =>
    fetchAPI<void>(`/api/v1/check-items/${id}`, { method: 'DELETE' }),
  getCategories: () =>
    fetchAPI<{ value: string; label: string }[]>('/api/v1/check-items/categories'),
  downloadTemplate: () => downloadFile(`${API_BASE}/api/v1/check-items/template`, 'check_items_template.csv'),
  importFile: (file: File) => uploadImportFile(`${API_BASE}/api/v1/check-items/import`, file),
}

// Writing Rules
export const writingRulesAPI = {
  list: (params?: { rule_type?: string; is_active?: boolean }) => {
    const searchParams = new URLSearchParams()
    if (params?.rule_type) searchParams.set('rule_type', params.rule_type)
    if (params?.is_active !== undefined)
      searchParams.set('is_active', String(params.is_active))
    const query = searchParams.toString() ? `?${searchParams}` : ''
    return fetchAPI<WritingRule[]>(`/api/v1/writing-rules${query}`)
  },
  get: (id: number) => fetchAPI<WritingRule>(`/api/v1/writing-rules/${id}`),
  create: (data: WritingRuleCreate) =>
    fetchAPI<WritingRule>('/api/v1/writing-rules', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Partial<WritingRuleCreate>) =>
    fetchAPI<WritingRule>(`/api/v1/writing-rules/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  delete: (id: number) =>
    fetchAPI<void>(`/api/v1/writing-rules/${id}`, { method: 'DELETE' }),
  downloadTemplate: () => downloadFile(`${API_BASE}/api/v1/writing-rules/template`, 'writing_rules_template.csv'),
  importFile: (file: File) => uploadImportFile(`${API_BASE}/api/v1/writing-rules/import`, file),
}

// Documents
export const documentsAPI = {
  list: (params?: { ocr_status?: string }) => {
    const query = params?.ocr_status ? `?ocr_status=${params.ocr_status}` : ''
    return fetchAPI<Document[]>(`/api/v1/documents${query}`)
  },
  get: (id: number) => fetchAPI<Document>(`/api/v1/documents/${id}`),
  upload: async (file: File) => {
    const controller = new AbortController()
    // アップロードは大きいファイルに対応するため120秒タイムアウト
    const timeout = setTimeout(() => controller.abort(), 120000)

    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await fetch(`${API_BASE}/api/v1/documents/upload`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      })
      if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        throw new Error(error.detail || 'Upload failed')
      }
      return response.json()
    } catch (err: any) {
      if (err.name === 'AbortError') {
        throw new Error('アップロードがタイムアウトしました。ファイルサイズを確認してください。')
      }
      throw err
    } finally {
      clearTimeout(timeout)
    }
  },
  delete: (id: number) =>
    fetchAPI<void>(`/api/v1/documents/${id}`, { method: 'DELETE' }),
  getText: (id: number) =>
    fetchAPI<{ text: string }>(`/api/v1/documents/${id}/text`),
}

// Reviews
export const reviewsAPI = {
  list: (params?: { document_id?: number; status?: string }) => {
    const searchParams = new URLSearchParams()
    if (params?.document_id)
      searchParams.set('document_id', String(params.document_id))
    if (params?.status) searchParams.set('status', params.status)
    const query = searchParams.toString() ? `?${searchParams}` : ''
    return fetchAPI<Review[]>(`/api/v1/reviews${query}`)
  },
  get: (id: number) => fetchAPI<Review>(`/api/v1/reviews/${id}`),
  create: (document_id: number, check_item_ids: number[]) =>
    fetchAPI<Review>('/api/v1/reviews', {
      method: 'POST',
      body: JSON.stringify({ document_id, check_item_ids }),
    }),
  getStatus: (id: number) =>
    fetchAPI<{
      status: string
      total_checks: number
      completed_checks: number
      progress_percent: number
    }>(`/api/v1/reviews/${id}/status`),
  delete: (id: number) =>
    fetchAPI<void>(`/api/v1/reviews/${id}`, { method: 'DELETE' }),
  exportExcel: async (id: number) => {
    const response = await fetch(`${API_BASE}/api/v1/reviews/${id}/export`)
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || 'Export failed')
    }
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    // Content-Dispositionからファイル名を取得
    const disposition = response.headers.get('content-disposition')
    let filename = `review_${id}.xlsx`
    if (disposition) {
      const match = disposition.match(/filename\*=UTF-8''(.+)/)
      if (match) {
        filename = decodeURIComponent(match[1])
      }
    }
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  },
  createBatch: (document_ids: number[], check_item_ids: number[]) =>
    fetchAPI<{ created_reviews: Review[]; failed_document_ids: number[] }>(
      '/api/v1/reviews/batch',
      {
        method: 'POST',
        body: JSON.stringify({ document_ids, check_item_ids }),
      }
    ),
  downloadRevised: async (id: number) => {
    const response = await fetch(
      `${API_BASE}/api/v1/reviews/${id}/revised-document`
    )
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || 'Download failed')
    }
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const disposition = response.headers.get('content-disposition')
    let filename = `review_${id}_revised.docx`
    if (disposition) {
      const match = disposition.match(/filename\*=UTF-8''(.+)/)
      if (match) {
        filename = decodeURIComponent(match[1])
      }
    }
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  },
  bulkExport: async (reviewIds: number[]) => {
    const response = await fetch(`${API_BASE}/api/v1/reviews/bulk-export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ review_ids: reviewIds }),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || 'Bulk export failed')
    }
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const disposition = response.headers.get('content-disposition')
    let filename = 'レビュー結果_一括.xlsx'
    if (disposition) {
      const match = disposition.match(/filename\*=UTF-8''(.+)/)
      if (match) {
        filename = decodeURIComponent(match[1])
      }
    }
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  },
}

// Comparisons
export interface ComparisonProject {
  id: number
  name: string
  description: string | null
  parent_document_id: number
  parent_document_title: string
  subsidiary_document_id: number | null
  subsidiary_document_title: string | null
  status: string
  check_item_count: number
  result_count: number
  created_at: string
  updated_at: string
}

export interface ComparisonCheckItem {
  id: number
  item_text: string
  category: string | null
  order_index: number
}

export interface ComparisonResult {
  id: number
  check_item_id: number
  check_item_text: string
  status: string
  parent_text: string | null
  subsidiary_text: string | null
  explanation: string | null
}

export interface ComparisonProjectDetail extends ComparisonProject {
  check_items: ComparisonCheckItem[]
  results: ComparisonResult[]
}

export const comparisonsAPI = {
  list: () => fetchAPI<ComparisonProject[]>('/api/v1/comparisons'),
  get: (id: number) => fetchAPI<ComparisonProjectDetail>(`/api/v1/comparisons/${id}`),
  create: (data: { name: string; description?: string; parent_document_id: number }) =>
    fetchAPI<ComparisonProjectDetail>('/api/v1/comparisons', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  delete: (id: number) =>
    fetchAPI<void>(`/api/v1/comparisons/${id}`, { method: 'DELETE' }),
  generateChecklist: (id: number) =>
    fetchAPI<{ message: string; count: number }>(`/api/v1/comparisons/${id}/generate-checklist`, {
      method: 'POST',
    }),
  updateChecklist: (id: number, items: { item_text: string; category?: string }[]) =>
    fetchAPI<{ message: string }>(`/api/v1/comparisons/${id}/checklist`, {
      method: 'PUT',
      body: JSON.stringify({ items }),
    }),
  setSubsidiary: (id: number, subsidiary_document_id: number) =>
    fetchAPI<{ message: string }>(`/api/v1/comparisons/${id}/subsidiary`, {
      method: 'PUT',
      body: JSON.stringify({ subsidiary_document_id }),
    }),
  compare: (id: number) =>
    fetchAPI<{ message: string; project_id: number; status: string; total_items: number }>(
      `/api/v1/comparisons/${id}/compare`,
      { method: 'POST' }
    ),
  getStatus: (id: number) =>
    fetchAPI<{
      status: string
      total_items: number
      completed_items: number
      progress_percent: number
    }>(`/api/v1/comparisons/${id}/status`),
  exportExcel: async (id: number) => {
    const response = await fetch(`${API_BASE}/api/v1/comparisons/${id}/export`)
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || 'Export failed')
    }
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const disposition = response.headers.get('content-disposition')
    let filename = `comparison_${id}.xlsx`
    if (disposition) {
      const match = disposition.match(/filename\*=UTF-8''(.+)/)
      if (match) filename = decodeURIComponent(match[1])
    }
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  },
}

// Findings
export const findingsAPI = {
  list: (reviewId: number, params?: { severity?: string; status?: string }) => {
    const searchParams = new URLSearchParams()
    if (params?.severity) searchParams.set('severity', params.severity)
    if (params?.status) searchParams.set('status', params.status)
    const query = searchParams.toString() ? `?${searchParams}` : ''
    return fetchAPI<Finding[]>(`/api/v1/reviews/${reviewId}/findings${query}`)
  },
  get: (id: number) => fetchAPI<Finding>(`/api/v1/findings/${id}`),
  approve: (id: number, comment?: string, edited_suggestion?: string) =>
    fetchAPI<Finding>(`/api/v1/findings/${id}/approve`, {
      method: 'PUT',
      body: JSON.stringify({ comment, edited_suggestion }),
    }),
  reject: (id: number, comment?: string) =>
    fetchAPI<Finding>(`/api/v1/findings/${id}/reject`, {
      method: 'PUT',
      body: JSON.stringify({ comment }),
    }),
  defer: (id: number, comment?: string) =>
    fetchAPI<Finding>(`/api/v1/findings/${id}/defer`, {
      method: 'PUT',
      body: JSON.stringify({ comment }),
    }),
  bulkApprove: (
    reviewId: number,
    findingIds: number[],
    action: 'APPROVED' | 'REJECTED' | 'DEFERRED',
    comment?: string
  ) =>
    fetchAPI<Finding[]>(`/api/v1/reviews/${reviewId}/findings/bulk-approve`, {
      method: 'POST',
      body: JSON.stringify({ finding_ids: findingIds, action, comment }),
    }),
  getContext: (id: number) =>
    fetchAPI<FindingContext>(`/api/v1/findings/${id}/context`),
  getRevisedText: (reviewId: number) =>
    fetchAPI<RevisedText>(`/api/v1/reviews/${reviewId}/revised-text`),
}

// Document Groups
export interface DocumentGroup {
  id: number
  name: string
  description: string | null
  member_count: number
  created_at: string
  updated_at: string | null
}

export interface DocumentGroupMember {
  document_id: number
  document_title: string
  added_at: string
}

export interface DocumentGroupDetail extends DocumentGroup {
  members: DocumentGroupMember[]
}

export interface ConsistencyFinding {
  document_a_title: string
  document_b_title: string
  location_a: string | null
  location_b: string | null
  text_a: string | null
  text_b: string | null
  issue_type: string
  severity: string
  description: string
  suggestion: string | null
}

export interface ConsistencyCheckResult {
  group_id: number
  group_name: string
  total_findings: number
  high_count: number
  medium_count: number
  low_count: number
  findings: ConsistencyFinding[]
}

export const documentGroupsAPI = {
  list: () => fetchAPI<DocumentGroup[]>('/api/v1/document-groups'),
  create: (name: string, description?: string, document_ids?: number[]) =>
    fetchAPI<DocumentGroupDetail>('/api/v1/document-groups', {
      method: 'POST',
      body: JSON.stringify({ name, description, document_ids: document_ids || [] }),
    }),
  get: (id: number) => fetchAPI<DocumentGroupDetail>(`/api/v1/document-groups/${id}`),
  update: (id: number, data: { name?: string; description?: string }) =>
    fetchAPI<DocumentGroup>(`/api/v1/document-groups/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  delete: (id: number) =>
    fetchAPI<void>(`/api/v1/document-groups/${id}`, { method: 'DELETE' }),
  addMember: (groupId: number, documentId: number) =>
    fetchAPI<{ message: string }>(
      `/api/v1/document-groups/${groupId}/members?document_id=${documentId}`,
      { method: 'POST' }
    ),
  removeMember: (groupId: number, documentId: number) =>
    fetchAPI<void>(`/api/v1/document-groups/${groupId}/members/${documentId}`, {
      method: 'DELETE',
    }),
  runConsistencyCheck: (groupId: number) =>
    fetchAPI<{
      job_id: number
      group_id: number
      status: string
      total_pairs: number
      completed_pairs: number
      progress_percent: number
    }>(
      `/api/v1/document-groups/${groupId}/consistency-check`,
      { method: 'POST' }
    ),
  getConsistencyCheckStatus: (groupId: number, jobId: number) =>
    fetchAPI<
      ConsistencyCheckResult | {
        job_id: number
        group_id: number
        status: string
        total_pairs: number
        completed_pairs: number
        progress_percent: number
        error?: string
      }
    >(`/api/v1/document-groups/${groupId}/consistency-check/${jobId}`),
}
