import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Header } from '@/components/layout/header'

// Mock useAuth to avoid needing AuthProvider + Next.js router
vi.mock('@/lib/auth-context', () => ({
  useAuth: () => ({
    user: { user_id: '1', username: 'testuser', display_name: 'Test User', roles: ['user'] },
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  }),
}))

describe('Header', () => {
  it('renders title', () => {
    render(<Header title="ダッシュボード" />)
    expect(screen.getByText('ダッシュボード')).toBeInTheDocument()
  })

  it('renders notification button with accessible label', () => {
    render(<Header title="テスト" />)
    expect(screen.getByRole('button', { name: '通知' })).toBeInTheDocument()
  })

  it('renders as header element', () => {
    render(<Header title="テスト" />)
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })

  it('renders without title', () => {
    render(<Header />)
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })

  it('displays user name', () => {
    render(<Header title="テスト" />)
    expect(screen.getByText('Test User')).toBeInTheDocument()
  })
})
