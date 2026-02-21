import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Badge } from '@/components/ui/badge'

describe('Badge', () => {
  it('renders with children', () => {
    render(<Badge>HIGH</Badge>)
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  it('applies default variant', () => {
    render(<Badge>Default</Badge>)
    expect(screen.getByText('Default').className).toContain('bg-gray-900')
  })

  it('applies destructive variant', () => {
    render(<Badge variant="destructive">Error</Badge>)
    expect(screen.getByText('Error').className).toContain('bg-red-500')
  })

  it('applies success variant', () => {
    render(<Badge variant="success">OK</Badge>)
    expect(screen.getByText('OK').className).toContain('bg-green-500')
  })

  it('applies warning variant', () => {
    render(<Badge variant="warning">Warn</Badge>)
    expect(screen.getByText('Warn').className).toContain('bg-yellow-600')
  })

  it('applies secondary variant', () => {
    render(<Badge variant="secondary">Low</Badge>)
    expect(screen.getByText('Low').className).toContain('bg-gray-100')
  })

  it('applies outline variant', () => {
    render(<Badge variant="outline">Outlined</Badge>)
    expect(screen.getByText('Outlined').className).toContain('text-gray-950')
  })

  it('applies custom className', () => {
    render(<Badge className="ml-2">Custom</Badge>)
    expect(screen.getByText('Custom')).toHaveClass('ml-2')
  })
})
