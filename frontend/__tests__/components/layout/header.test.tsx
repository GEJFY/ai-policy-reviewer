import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Header } from '@/components/layout/header'

describe('Header', () => {
  it('renders title', () => {
    render(<Header title="ダッシュボード" />)
    expect(screen.getByText('ダッシュボード')).toBeInTheDocument()
  })

  it('renders notification button with accessible label', () => {
    render(<Header title="テスト" />)
    expect(screen.getByRole('button', { name: '通知' })).toBeInTheDocument()
  })

  it('renders user button with accessible label', () => {
    render(<Header title="テスト" />)
    expect(screen.getByRole('button', { name: 'ユーザー' })).toBeInTheDocument()
  })

  it('renders as header element', () => {
    render(<Header title="テスト" />)
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })

  it('renders without title', () => {
    render(<Header />)
    // Should still render the header element
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })
})
