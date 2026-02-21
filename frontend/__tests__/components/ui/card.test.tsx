import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card'

describe('Card', () => {
  it('renders children', () => {
    render(<Card>カード内容</Card>)
    expect(screen.getByText('カード内容')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(<Card className="custom">内容</Card>)
    expect(container.firstChild).toHaveClass('custom')
  })

  it('forwards ref', () => {
    const ref = vi.fn()
    render(<Card ref={ref}>Ref</Card>)
    expect(ref).toHaveBeenCalledWith(expect.any(HTMLDivElement))
  })
})

describe('CardHeader', () => {
  it('renders children', () => {
    render(<CardHeader>ヘッダー</CardHeader>)
    expect(screen.getByText('ヘッダー')).toBeInTheDocument()
  })
})

describe('CardTitle', () => {
  it('renders as h3', () => {
    render(<CardTitle>タイトル</CardTitle>)
    const el = screen.getByText('タイトル')
    expect(el.tagName).toBe('H3')
  })
})

describe('CardDescription', () => {
  it('renders as p', () => {
    render(<CardDescription>説明</CardDescription>)
    const el = screen.getByText('説明')
    expect(el.tagName).toBe('P')
  })
})

describe('CardContent', () => {
  it('renders children', () => {
    render(<CardContent>コンテンツ</CardContent>)
    expect(screen.getByText('コンテンツ')).toBeInTheDocument()
  })
})

describe('CardFooter', () => {
  it('renders children', () => {
    render(<CardFooter>フッター</CardFooter>)
    expect(screen.getByText('フッター')).toBeInTheDocument()
  })
})
