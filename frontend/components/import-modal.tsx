'use client'

import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Upload, FileSpreadsheet, AlertCircle, CheckCircle2 } from 'lucide-react'
import { ImportResult } from '@/lib/api'

interface ImportModalProps {
  title: string
  onClose: () => void
  onImport: (file: File) => Promise<ImportResult>
  onDownloadTemplate: () => Promise<void>
  onSuccess: () => void
  acceptTypes?: string
}

export function ImportModal({
  title,
  onClose,
  onImport,
  onDownloadTemplate,
  onSuccess,
  acceptTypes = '.csv,.xlsx,.xls',
}: ImportModalProps) {
  const [file, setFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0]
    if (selected) {
      setFile(selected)
      setResult(null)
      setError(null)
    }
  }

  async function handleImport() {
    if (!file) return
    setImporting(true)
    setError(null)
    setResult(null)
    try {
      const res = await onImport(file)
      setResult(res)
      if (res.success > 0) {
        onSuccess()
      }
    } catch (err: any) {
      setError(err.message || 'インポートに失敗しました')
    } finally {
      setImporting(false)
    }
  }

  async function handleDownloadTemplate() {
    try {
      await onDownloadTemplate()
    } catch (err: any) {
      setError(err.message || 'テンプレートのダウンロードに失敗しました')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div
        className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="import-modal-title"
      >
        <h3 id="import-modal-title" className="mb-4 text-lg font-semibold">
          {title}
        </h3>

        {/* Template download */}
        <div className="mb-4 rounded-md bg-blue-50 p-3">
          <p className="mb-2 text-sm text-blue-700">
            CSVまたはExcel形式のファイルをインポートできます。
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownloadTemplate}
          >
            <FileSpreadsheet className="mr-2 h-4 w-4" aria-hidden="true" />
            テンプレートをダウンロード
          </Button>
        </div>

        {/* File selection */}
        <div className="mb-4">
          <input
            ref={fileInputRef}
            type="file"
            accept={acceptTypes}
            onChange={handleFileChange}
            className="hidden"
          />
          <div
            onClick={() => fileInputRef.current?.click()}
            className="cursor-pointer rounded-md border-2 border-dashed border-gray-300 p-6 text-center transition-colors hover:border-blue-400 hover:bg-blue-50"
          >
            <Upload className="mx-auto mb-2 h-8 w-8 text-gray-400" aria-hidden="true" />
            {file ? (
              <p className="text-sm font-medium text-gray-700">{file.name}</p>
            ) : (
              <p className="text-sm text-gray-500">
                クリックしてファイルを選択
              </p>
            )}
            <p className="mt-1 text-xs text-gray-400">CSV, XLSX, XLS</p>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 flex items-start gap-2 rounded-md bg-red-50 p-3" role="alert">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" aria-hidden="true" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="mb-4 space-y-2">
            {result.success > 0 && (
              <div className="flex items-center gap-2 rounded-md bg-green-50 p-3">
                <CheckCircle2 className="h-4 w-4 text-green-500" aria-hidden="true" />
                <p className="text-sm text-green-700">
                  {result.success}件のインポートに成功しました
                </p>
              </div>
            )}
            {result.errors.length > 0 && (
              <div className="rounded-md bg-yellow-50 p-3">
                <p className="mb-1 text-sm font-medium text-yellow-700">
                  エラー ({result.errors.length}件):
                </p>
                <ul className="max-h-32 overflow-y-auto text-xs text-yellow-600">
                  {result.errors.map((err, i) => (
                    <li key={i} className="py-0.5">
                      {err}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            {result && result.success > 0 ? '閉じる' : 'キャンセル'}
          </Button>
          {(!result || result.success === 0) && (
            <Button
              onClick={handleImport}
              disabled={!file || importing}
            >
              {importing ? 'インポート中...' : 'インポート実行'}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
