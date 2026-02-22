'use client'

import * as React from 'react'
import { HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TooltipProps {
  content: string | React.ReactNode
  children: React.ReactElement
  position?: 'top' | 'bottom' | 'left' | 'right'
  delay?: number
  maxWidth?: string
}

export function Tooltip({
  content,
  children,
  position = 'top',
  delay = 300,
  maxWidth = 'max-w-xs',
}: TooltipProps) {
  const [visible, setVisible] = React.useState(false)
  const timeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null)

  const show = () => {
    timeoutRef.current = setTimeout(() => setVisible(true), delay)
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
            positionClasses[position]
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
  position = 'top',
}: {
  text: string
  position?: 'top' | 'bottom' | 'left' | 'right'
}) {
  return (
    <Tooltip content={text} position={position}>
      <span>
        <HelpCircle className="h-3.5 w-3.5 text-gray-400 cursor-help" aria-hidden="true" />
      </span>
    </Tooltip>
  )
}
