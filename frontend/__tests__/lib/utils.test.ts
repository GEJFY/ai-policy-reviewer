import { describe, it, expect } from 'vitest'
import { cn, formatDate, truncate } from '@/lib/utils'

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('handles conditional classes', () => {
    expect(cn('base', false && 'hidden', 'visible')).toBe('base visible')
  })

  it('resolves tailwind conflicts (last wins)', () => {
    const result = cn('px-4', 'px-6')
    expect(result).toBe('px-6')
  })

  it('handles empty input', () => {
    expect(cn()).toBe('')
  })

  it('handles undefined and null', () => {
    expect(cn('base', undefined, null, 'extra')).toBe('base extra')
  })
})

describe('formatDate', () => {
  it('formats ISO string in Asia/Tokyo timezone', () => {
    // 2025-03-15T10:30:00Z = 2025-03-15T19:30:00 JST
    const result = formatDate('2025-03-15T10:30:00Z')
    expect(result).toMatch(/2025/)
    expect(result).toMatch(/03/)
    expect(result).toMatch(/15/)
    expect(result).toMatch(/19/) // 10:30 UTC = 19:30 JST
    expect(result).toMatch(/30/)
  })

  it('formats Date object in Asia/Tokyo timezone', () => {
    // 2025-01-01T00:00:00Z = 2025-01-01T09:00:00 JST
    const date = new Date('2025-01-01T00:00:00Z')
    const result = formatDate(date)
    expect(result).toMatch(/2025/)
    expect(result).toMatch(/01/)
    expect(result).toMatch(/09/) // 00:00 UTC = 09:00 JST
  })

  it('handles date crossing midnight in JST', () => {
    // 2025-06-20T16:00:00Z = 2025-06-21T01:00:00 JST (next day)
    const result = formatDate('2025-06-20T16:00:00Z')
    expect(result).toMatch(/2025/)
    expect(result).toMatch(/06/)
    expect(result).toMatch(/21/) // crosses to next day in JST
    expect(result).toMatch(/01/) // 01:00 JST
  })
})

describe('truncate', () => {
  it('returns original string if within limit', () => {
    expect(truncate('hello', 10)).toBe('hello')
  })

  it('returns original string if exactly at limit', () => {
    expect(truncate('hello', 5)).toBe('hello')
  })

  it('truncates and adds ellipsis', () => {
    expect(truncate('hello world', 5)).toBe('hello...')
  })

  it('handles empty string', () => {
    expect(truncate('', 5)).toBe('')
  })

  it('handles zero length', () => {
    expect(truncate('hello', 0)).toBe('...')
  })
})
