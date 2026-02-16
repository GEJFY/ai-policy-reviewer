'use client'

import { useState, createContext, useContext, useCallback, useRef } from 'react'
import { Button } from './button'

interface ConfirmOptions {
  title?: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
}

interface ConfirmContextValue {
  confirm: (options: ConfirmOptions) => Promise<boolean>
}

const ConfirmContext = createContext<ConfirmContextValue | null>(null)

export function useConfirm() {
  const context = useContext(ConfirmContext)
  if (!context) {
    throw new Error('useConfirm must be used within a ConfirmProvider')
  }
  return context
}

export function ConfirmProvider({ children }: { children: React.ReactNode }) {
  const [options, setOptions] = useState<ConfirmOptions | null>(null)
  const resolveRef = useRef<((value: boolean) => void) | null>(null)

  const confirm = useCallback((opts: ConfirmOptions): Promise<boolean> => {
    setOptions(opts)
    return new Promise((resolve) => {
      resolveRef.current = resolve
    })
  }, [])

  function handleClose(result: boolean) {
    resolveRef.current?.(result)
    resolveRef.current = null
    setOptions(null)
  }

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
      {options && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50" role="presentation">
          <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl" role="alertdialog" aria-modal="true" aria-labelledby="confirm-dialog-title" aria-describedby="confirm-dialog-message">
            <h3 id="confirm-dialog-title" className="mb-2 text-lg font-semibold">
              {options.title || '確認'}
            </h3>
            <p id="confirm-dialog-message" className="mb-6 text-sm text-gray-600">{options.message}</p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => handleClose(false)}>
                {options.cancelLabel || 'キャンセル'}
              </Button>
              <Button variant="destructive" onClick={() => handleClose(true)}>
                {options.confirmLabel || '削除'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  )
}
