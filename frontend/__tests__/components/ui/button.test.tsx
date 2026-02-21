import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '@/components/ui/button'

describe('Button', () => {
  it('renders with children', () => {
    render(<Button>テスト</Button>)
    expect(screen.getByRole('button', { name: 'テスト' })).toBeInTheDocument()
  })

  it('handles click events', async () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>クリック</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledOnce()
  })

  it('is disabled when disabled prop is set', () => {
    render(<Button disabled>無効</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('applies custom className', () => {
    render(<Button className="custom-class">ボタン</Button>)
    expect(screen.getByRole('button')).toHaveClass('custom-class')
  })

  it('renders with default variant styles', () => {
    render(<Button>デフォルト</Button>)
    const btn = screen.getByRole('button')
    expect(btn.className).toContain('bg-gray-900')
  })

  it('renders with destructive variant', () => {
    render(<Button variant="destructive">削除</Button>)
    const btn = screen.getByRole('button')
    expect(btn.className).toContain('bg-red-500')
  })

  it('renders with outline variant', () => {
    render(<Button variant="outline">アウトライン</Button>)
    const btn = screen.getByRole('button')
    expect(btn.className).toContain('border')
  })

  it('renders with sm size', () => {
    render(<Button size="sm">小</Button>)
    const btn = screen.getByRole('button')
    expect(btn.className).toContain('h-8')
  })

  it('renders with lg size', () => {
    render(<Button size="lg">大</Button>)
    const btn = screen.getByRole('button')
    expect(btn.className).toContain('h-10')
  })

  it('forwards ref', () => {
    const ref = vi.fn()
    render(<Button ref={ref}>Ref</Button>)
    expect(ref).toHaveBeenCalledWith(expect.any(HTMLButtonElement))
  })
})
