'use client'

import * as React from 'react'
import { HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

type TooltipPosition = 'top' | 'bottom' | 'left' | 'right' | 'auto'

interface TooltipProps {
  content: string | React.ReactNode
  children: React.ReactElement
  position?: TooltipPosition
  delay?: number
  maxWidth?: string
}

function resolvePosition(
  triggerRect: DOMRect,
  position: TooltipPosition
): 'top' | 'bottom' | 'left' | 'right' {
  if (position !== 'auto') return position

  // If the trigger is near the top of the viewport, show below
  if (triggerRect.top < 80) return 'bottom'
  // If near the bottom, show above
  if (window.innerHeight - triggerRect.bottom < 80) return 'top'
  // Default to bottom (safer for most dashboard layouts)
  return 'bottom'
}

export function Tooltip({
  content,
  children,
  position = 'auto',
  delay = 300,
  maxWidth = 'max-w-sm',
}: TooltipProps) {
  const [visible, setVisible] = React.useState(false)
  const [resolved, setResolved] = React.useState<'top' | 'bottom' | 'left' | 'right'>('bottom')
  const timeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null)
  const triggerRef = React.useRef<HTMLSpanElement | null>(null)

  const show = () => {
    timeoutRef.current = setTimeout(() => {
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect()
        setResolved(resolvePosition(rect, position))
      }
      setVisible(true)
    }, delay)
  }

  const hide = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    setVisible(false)
  }

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  }

  return (
    <span
      ref={triggerRef}
      className="relative inline-flex items-center"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      {visible && (
        <span
          role="tooltip"
          className={cn(
            'absolute z-50 rounded-lg bg-gray-900 px-3 py-2 text-xs leading-relaxed text-white shadow-lg pointer-events-none whitespace-normal',
            maxWidth,
            positionClasses[resolved]
          )}
        >
          {content}
        </span>
      )}
    </span>
  )
}

export function HelpTooltip({
  text,
  position = 'auto',
}: {
  text: string
  position?: TooltipPosition
}) {
  return (
    <Tooltip content={text} position={position} maxWidth="max-w-sm">
      <span>
        <HelpCircle className="h-3.5 w-3.5 text-gray-400 cursor-help" aria-hidden="true" />
      </span>
    </Tooltip>
  )
}
