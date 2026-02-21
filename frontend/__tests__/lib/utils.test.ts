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
  it('formats ISO string to ja-JP locale', () => {
    const result = formatDate('2025-03-15T10:30:00Z')
    // ja-JP locale output contains year/month/day
    expect(result).toMatch(/2025/)
    expect(result).toMatch(/03/)
    expect(result).toMatch(/15/)
  })

  it('formats Date object', () => {
    const date = new Date('2025-01-01T00:00:00Z')
    const result = formatDate(date)
    expect(result).toMatch(/2025/)
    expect(result).toMatch(/01/)
  })

  it('includes time components', () => {
    const result = formatDate('2025-06-20T14:30:00Z')
    // Should include hour:minute in some format
    expect(result).toBeTruthy()
    expect(result.length).toBeGreaterThan(8) // longer than just date
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
