import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { fetchAPI, termsAPI, reviewsAPI, findingsAPI, documentsAPI } from '@/lib/api'

// Mock global fetch
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

beforeEach(() => {
  mockFetch.mockReset()
})

afterEach(() => {
  vi.restoreAllMocks()
})

function jsonResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    headers: new Headers(),
  })
}

function errorResponse(detail: string, status = 400) {
  return Promise.resolve({
    ok: false,
    status,
    json: () => Promise.resolve({ detail }),
    headers: new Headers(),
  })
}

describe('fetchAPI', () => {
  it('fetches data successfully', async () => {
    mockFetch.mockReturnValue(jsonResponse({ message: 'ok' }))
    const result = await fetchAPI<{ message: string }>('/api/v1/test')
    expect(result).toEqual({ message: 'ok' })
    expect(mockFetch).toHaveBeenCalledOnce()
  })

  it('includes Content-Type header by default', async () => {
    mockFetch.mockReturnValue(jsonResponse({}))
    await fetchAPI('/api/v1/test')
    const [, options] = mockFetch.mock.calls[0]
    expect(options.headers['Content-Type']).toBe('application/json')
  })

  it('throws on non-ok response with detail', async () => {
    mockFetch.mockReturnValue(errorResponse('Not found', 404))
    await expect(fetchAPI('/api/v1/test')).rejects.toThrow('Not found')
  })

  it('throws generic error when response has no detail', async () => {
    mockFetch.mockReturnValue(
      Promise.resolve({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error('parse error')),
        headers: new Headers(),
      })
    )
    await expect(fetchAPI('/api/v1/test')).rejects.toThrow('API Error: 500')
  })

  it('returns null for 204 No Content', async () => {
    mockFetch.mockReturnValue(
      Promise.resolve({
        ok: true,
        status: 204,
        json: () => Promise.resolve(null),
        headers: new Headers(),
      })
    )
    const result = await fetchAPI('/api/v1/test')
    expect(result).toBeNull()
  })

  it('throws timeout error on abort', async () => {
    mockFetch.mockImplementation(() => {
      const err = new Error('Aborted')
      err.name = 'AbortError'
      return Promise.reject(err)
    })
    await expect(fetchAPI('/api/v1/test')).rejects.toThrow(
      'サーバーに接続できません'
    )
  })
})

describe('termsAPI', () => {
  it('list calls correct endpoint', async () => {
    mockFetch.mockReturnValue(jsonResponse([]))
    await termsAPI.list()
    expect(mockFetch.mock.calls[0][0]).toContain('/api/v1/terms')
  })

  it('list with category filter', async () => {
    mockFetch.mockReturnValue(jsonResponse([]))
    await termsAPI.list({ category: '人事' })
    expect(mockFetch.mock.calls[0][0]).toContain('category=人事')
  })

  it('create sends POST with body', async () => {
    mockFetch.mockReturnValue(jsonResponse({ id: 1, term: 'テスト' }))
    await termsAPI.create({ term: 'テスト', definition: '定義', category: '一般' })
    const [, options] = mockFetch.mock.calls[0]
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toMatchObject({ term: 'テスト' })
  })

  it('delete sends DELETE', async () => {
    mockFetch.mockReturnValue(
      Promise.resolve({ ok: true, status: 204, json: () => Promise.resolve(null), headers: new Headers() })
    )
    await termsAPI.delete(1)
    const [url, options] = mockFetch.mock.calls[0]
    expect(url).toContain('/api/v1/terms/1')
    expect(options.method).toBe('DELETE')
  })
})

describe('reviewsAPI', () => {
  it('list with status filter', async () => {
    mockFetch.mockReturnValue(jsonResponse([]))
    await reviewsAPI.list({ status: 'completed' })
    expect(mockFetch.mock.calls[0][0]).toContain('status=completed')
  })

  it('create sends POST', async () => {
    mockFetch.mockReturnValue(jsonResponse({ id: 1 }))
    await reviewsAPI.create(1, [1, 2])
    const [, options] = mockFetch.mock.calls[0]
    expect(options.method).toBe('POST')
    const body = JSON.parse(options.body)
    expect(body.document_id).toBe(1)
    expect(body.check_item_ids).toEqual([1, 2])
  })

  it('getStatus returns progress data', async () => {
    const mockStatus = { status: 'processing', total_checks: 5, completed_checks: 2, progress_percent: 40 }
    mockFetch.mockReturnValue(jsonResponse(mockStatus))
    const result = await reviewsAPI.getStatus(1)
    expect(result.progress_percent).toBe(40)
  })
})

describe('findingsAPI', () => {
  it('list with severity filter', async () => {
    mockFetch.mockReturnValue(jsonResponse([]))
    await findingsAPI.list(1, { severity: 'HIGH' })
    expect(mockFetch.mock.calls[0][0]).toContain('severity=HIGH')
  })

  it('approve sends PUT', async () => {
    mockFetch.mockReturnValue(jsonResponse({ id: 1, status: 'APPROVED' }))
    await findingsAPI.approve(1, 'ok')
    const [url, options] = mockFetch.mock.calls[0]
    expect(url).toContain('/api/v1/findings/1/approve')
    expect(options.method).toBe('PUT')
  })

  it('bulkApprove sends POST with action', async () => {
    mockFetch.mockReturnValue(jsonResponse([]))
    await findingsAPI.bulkApprove(1, [1, 2], 'APPROVED', 'テスト')
    const [url, options] = mockFetch.mock.calls[0]
    expect(url).toContain('/findings/bulk-approve')
    const body = JSON.parse(options.body)
    expect(body.action).toBe('APPROVED')
    expect(body.finding_ids).toEqual([1, 2])
  })
})

describe('documentsAPI', () => {
  it('upload sends FormData', async () => {
    mockFetch.mockReturnValue(
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: 1 }),
        headers: new Headers(),
      })
    )
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    await documentsAPI.upload(file)
    const [url, options] = mockFetch.mock.calls[0]
    expect(url).toContain('/api/v1/documents/upload')
    expect(options.method).toBe('POST')
    expect(options.body).toBeInstanceOf(FormData)
  })

  it('upload does not set Content-Type header (browser sets it with boundary)', async () => {
    mockFetch.mockReturnValue(
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: 1 }),
        headers: new Headers(),
      })
    )
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    await documentsAPI.upload(file)
    const [, options] = mockFetch.mock.calls[0]
    // FormData upload should NOT have explicit Content-Type
    expect(options.headers).toBeUndefined()
  })
})
