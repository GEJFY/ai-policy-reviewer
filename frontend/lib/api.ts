/**
 * API Client for Policy Review Tool
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Generic fetch wrapper
export async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
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

// API Functions

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
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch(`${API_BASE}/api/v1/documents/upload`, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || 'Upload failed')
    }
    return response.json()
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
