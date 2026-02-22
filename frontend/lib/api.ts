/**
 * API Client for Policy Review Tool
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Generic fetch wrapper with timeout
export async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 10000)

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
      signal: controller.signal,
    })

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
  status: string
  reviewed_by: string | null
  reviewed_at: string | null
  comment: string | null
  created_at: string
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
  approve: (id: number, comment?: string) =>
    fetchAPI<Finding>(`/api/v1/findings/${id}/approve`, {
      method: 'PUT',
      body: JSON.stringify({ comment }),
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
}
