'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Header } from '@/components/layout/header'
import { useAuth } from '@/lib/auth-context'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Server,
  Brain,
  Cloud,
  Eye,
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Activity,
  Database,
} from 'lucide-react'
import { settingsAPI, SystemSettings, HealthDetailed } from '@/lib/api'
import { HelpTooltip } from '@/components/ui/tooltip'
import { TIPS } from '@/lib/tooltip-texts'

// プロバイダー表示名
const PROVIDER_LABELS: Record<string, string> = {
  azure: 'Azure OpenAI / Foundry',
  aws_bedrock: 'AWS Bedrock',
  gcp_vertex: 'GCP Vertex AI',
  local: 'Ollama (ローカル)',
  azure_openai: 'Azure OpenAI',
  azure_doc_intel: 'Azure Document Intelligence',
  tesseract: 'Tesseract (ローカル)',
  aws_tesseract: 'AWS Tesseract',
}

function providerLabel(key: string): string {
  return PROVIDER_LABELS[key] || key
}

export default function SettingsPage() {
  const { user } = useAuth()
  const router = useRouter()
  const [settings, setSettings] = useState<SystemSettings | null>(null)
  const [health, setHealth] = useState<HealthDetailed | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Admin-only access guard
  useEffect(() => {
    if (user && !user.roles?.includes('admin')) {
      router.push('/dashboard')
    }
  }, [user, router])

  if (!user?.roles?.includes('admin')) {
    return (
      <>
        <Header title="設定" />
        <div className="p-6 text-center text-gray-500">
          管理者のみアクセスできます。
        </div>
      </>
    )
  }

  useEffect(() => {
    async function loadData() {
      try {
        const results = await Promise.allSettled([
          settingsAPI.get(),
          settingsAPI.getHealth(),
        ])

        if (results[0].status === 'fulfilled') {
          setSettings(results[0].value)
        }
        if (results[1].status === 'fulfilled') {
          setHealth(results[1].value)
        }
        if (results[0].status === 'rejected' && results[1].status === 'rejected') {
          setError('設定情報の取得に失敗しました。バックエンドが起動しているか確認してください。')
        }
      } catch (err) {
        setError('設定情報の取得に失敗しました。')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  if (loading) {
    return (
      <>
        <Header title="設定" />
        <div className="p-6">
          <div className="text-center text-gray-500 py-12">読み込み中...</div>
        </div>
      </>
    )
  }

  if (error && !settings && !health) {
    return (
      <>
        <Header title="設定" />
        <div className="p-6">
          <Card>
            <CardContent className="py-12 text-center">
              <AlertTriangle className="mx-auto h-8 w-8 text-yellow-500 mb-3" />
              <p className="text-gray-600">{error}</p>
            </CardContent>
          </Card>
        </div>
      </>
    )
  }

  return (
    <>
      <Header title="設定" />
      <div className="p-6 space-y-6">
        {/* 設定バリデーション警告 */}
        {settings?.validation && !settings.validation.is_valid && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="py-4">
              <div className="flex items-start gap-3">
                <XCircle className="h-5 w-5 text-red-500 mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-red-800">設定エラー</p>
                  <ul className="mt-1 text-sm text-red-700 list-disc list-inside">
                    {settings.validation.missing.map((m) => (
                      <li key={m}>{m} が未設定です</li>
                    ))}
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {settings?.validation?.warnings && settings.validation.warnings.length > 0 && (
          <Card className="border-yellow-200 bg-yellow-50">
            <CardContent className="py-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-yellow-800">警告</p>
                  <ul className="mt-1 text-sm text-yellow-700 list-disc list-inside">
                    {settings.validation.warnings.map((w) => (
                      <li key={w}>{w}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* システム情報 & ヘルスステータス */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SystemInfoCard settings={settings} />
          <HealthStatusCard health={health} />
        </div>

        {/* LLMプロバイダー設定 */}
        <LLMProviderCard settings={settings} health={health} />

        {/* Embedding & OCR */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <EmbeddingCard settings={settings} />
          <OCRCard settings={settings} />
        </div>

        {/* アプリケーション設定 */}
        <AppSettingsCard settings={settings} />
      </div>
    </>
  )
}

function SystemInfoCard({ settings }: { settings: SystemSettings | null }) {
  if (!settings) return null

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 pb-3">
        <Server className="h-5 w-5 text-gray-500" />
        <CardTitle className="text-base">システム情報</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="space-y-3 text-sm">
          <InfoRow label="バージョン" value={settings.system.version} />
          <InfoRow
            label="環境"
            value={
              <Badge variant={settings.system.debug ? 'warning' : 'success'}>
                {settings.system.debug ? 'Development' : 'Production'}
              </Badge>
            }
          />
          <InfoRow label="データベース" value={settings.system.database_url} mono />
        </dl>
      </CardContent>
    </Card>
  )
}

function HealthStatusCard({ health }: { health: HealthDetailed | null }) {
  if (!health) return null

  const statusColor = {
    healthy: 'text-green-600',
    degraded: 'text-yellow-600',
    unhealthy: 'text-red-600',
  }[health.status] || 'text-gray-600'

  const statusBadge = {
    healthy: 'success' as const,
    degraded: 'warning' as const,
    unhealthy: 'destructive' as const,
  }[health.status] || 'secondary' as const

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 pb-3">
        <Activity className="h-5 w-5 text-gray-500" />
        <CardTitle className="text-base">ヘルスステータス</CardTitle>
        <Badge variant={statusBadge} className="ml-auto">
          {health.status.toUpperCase()}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {Object.entries(health.checks).map(([name, check]) => (
            <div key={name} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                {check.healthy ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-500" />
                )}
                <span className="text-gray-700">{serviceLabel(name)}</span>
              </div>
              <span className={check.healthy ? 'text-green-600' : 'text-red-600'}>
                {check.healthy ? '正常' : 'エラー'}
              </span>
            </div>
          ))}

          {/* サーキットブレーカー */}
          {Object.keys(health.circuit_breakers).length > 0 && (
            <div className="mt-3 pt-3 border-t">
              <p className="text-xs font-medium text-gray-500 mb-2">サーキットブレーカー</p>
              {Object.entries(health.circuit_breakers).map(([name, cb]) => (
                <div key={name} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700">{name}</span>
                  <Badge
                    variant={
                      cb.state === 'closed' ? 'success' :
                      cb.state === 'half_open' ? 'warning' : 'destructive'
                    }
                  >
                    {cb.state}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function LLMProviderCard({
  settings,
  health,
}: {
  settings: SystemSettings | null
  health: HealthDetailed | null
}) {
  if (!settings) return null

  const providers = [
    { key: 'azure', config: settings.providers.azure },
    { key: 'aws_bedrock', config: settings.providers.aws_bedrock },
    { key: 'gcp_vertex', config: settings.providers.gcp_vertex },
    { key: 'ollama', config: settings.providers.ollama },
  ]

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 pb-3">
        <Brain className="h-5 w-5 text-gray-500" />
        <CardTitle className="text-base">LLMプロバイダー <HelpTooltip text={TIPS.settings.llmProvider} /></CardTitle>
        <Badge variant="outline" className="ml-auto">
          {providerLabel(settings.llm.provider)}
        </Badge>
      </CardHeader>
      <CardContent>
        <dl className="space-y-2 text-sm mb-4">
          <InfoRow label="使用モデル" value={settings.llm.model} mono />
          {settings.llm.tier && (
            <InfoRow label="ティア" value={settings.llm.tier} />
          )}
        </dl>

        <div className="space-y-3">
          {providers.map(({ key, config }) => {
            const isActive = settings.llm.provider === key
            return (
              <div
                key={key}
                className={`rounded-lg border p-3 ${
                  isActive ? 'border-blue-200 bg-blue-50' : 'border-gray-100'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Cloud className="h-4 w-4 text-gray-400" />
                    <span className="font-medium text-sm">{providerLabel(key)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {isActive && <Badge variant="default">Active</Badge>}
                    <Badge variant={config.configured ? 'success' : 'secondary'}>
                      {config.configured ? '設定済み' : '未設定'}
                    </Badge>
                  </div>
                </div>
                {config.configured && (
                  <ProviderDetails providerKey={key} config={config} />
                )}
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

function ProviderDetails({ providerKey, config }: { providerKey: string; config: any }) {
  switch (providerKey) {
    case 'azure':
      return (
        <dl className="text-xs text-gray-600 space-y-1 ml-6">
          <InfoRow label="エンドポイント" value={config.endpoint || '(設定済み)'} mono small />
          <InfoRow label="デプロイメント" value={config.deployment} mono small />
          <InfoRow label="Embedding" value={config.embedding_deployment} mono small />
          <InfoRow label="APIバージョン" value={config.api_version} mono small />
        </dl>
      )
    case 'aws_bedrock':
      return (
        <dl className="text-xs text-gray-600 space-y-1 ml-6">
          <InfoRow label="リージョン" value={config.region} mono small />
          <InfoRow label="モデルID" value={config.model_id} mono small />
          <InfoRow label="Embedding" value={config.embedding_model} mono small />
        </dl>
      )
    case 'gcp_vertex':
      return (
        <dl className="text-xs text-gray-600 space-y-1 ml-6">
          <InfoRow label="プロジェクトID" value={config.project_id} mono small />
          <InfoRow label="ロケーション" value={config.location} mono small />
          <InfoRow label="モデル" value={config.model} mono small />
          <InfoRow label="Embedding" value={config.embedding_model} mono small />
        </dl>
      )
    case 'ollama':
      return (
        <dl className="text-xs text-gray-600 space-y-1 ml-6">
          <InfoRow label="ベースURL" value={config.base_url} mono small />
          <InfoRow label="モデル" value={config.model} mono small />
          <InfoRow label="Embedding" value={config.embedding_model} mono small />
        </dl>
      )
    default:
      return null
  }
}

function EmbeddingCard({ settings }: { settings: SystemSettings | null }) {
  if (!settings) return null

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 pb-3">
        <Database className="h-5 w-5 text-gray-500" />
        <CardTitle className="text-base">Embedding <HelpTooltip text={TIPS.settings.embeddingProvider} /></CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="space-y-3 text-sm">
          <InfoRow
            label="プロバイダー"
            value={providerLabel(settings.embedding.provider)}
          />
        </dl>
      </CardContent>
    </Card>
  )
}

function OCRCard({ settings }: { settings: SystemSettings | null }) {
  if (!settings) return null

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 pb-3">
        <Eye className="h-5 w-5 text-gray-500" />
        <CardTitle className="text-base">OCR <HelpTooltip text={TIPS.settings.ocrProvider} /></CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="space-y-3 text-sm">
          <InfoRow
            label="プロバイダー"
            value={providerLabel(settings.ocr.provider)}
          />
          <InfoRow
            label="Azure Doc Intel"
            value={
              <Badge variant={settings.ocr.azure_doc_intel.configured ? 'success' : 'secondary'}>
                {settings.ocr.azure_doc_intel.configured ? '設定済み' : '未設定'}
              </Badge>
            }
          />
          <InfoRow
            label="Tesseract"
            value={
              <Badge variant={settings.ocr.tesseract.configured ? 'success' : 'secondary'}>
                {settings.ocr.tesseract.configured ? '設定済み' : '未設定'}
              </Badge>
            }
          />
          {settings.ocr.tesseract.configured && (
            <InfoRow label="言語" value={settings.ocr.tesseract.lang} mono />
          )}
        </dl>
      </CardContent>
    </Card>
  )
}

function AppSettingsCard({ settings }: { settings: SystemSettings | null }) {
  if (!settings) return null

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 pb-3">
        <Shield className="h-5 w-5 text-gray-500" />
        <CardTitle className="text-base">アプリケーション設定</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="space-y-3 text-sm">
          <InfoRow label="アップロードディレクトリ" value={settings.app.upload_dir} mono />
          <InfoRow label="最大ファイルサイズ" value={`${settings.app.max_file_size_mb} MB`} />
          <InfoRow
            label="CORS オリジン"
            value={settings.app.cors_origins.join(', ')}
            mono
          />
        </dl>
      </CardContent>
    </Card>
  )
}

// ユーティリティ
function InfoRow({
  label,
  value,
  mono,
  small,
}: {
  label: string
  value: React.ReactNode
  mono?: boolean
  small?: boolean
}) {
  return (
    <div className={`flex items-start justify-between gap-4 ${small ? 'text-xs' : ''}`}>
      <dt className="text-gray-500 shrink-0">{label}</dt>
      <dd className={`text-right ${mono ? 'font-mono text-gray-800' : 'text-gray-900'}`}>
        {value}
      </dd>
    </div>
  )
}

function serviceLabel(key: string): string {
  const labels: Record<string, string> = {
    database: 'データベース',
    llm_service: 'LLMサービス',
    ocr_service: 'OCRサービス',
  }
  return labels[key] || key
}
