'use client'

import Link from 'next/link'
import { useState, useEffect, useRef } from 'react'
import { useIntersectionObserver } from '@/lib/use-intersection-observer'
import {
  FileSearch,
  Shield,
  Zap,
  BarChart3,
  CheckCircle2,
  FileText,
  BookOpen,
  ArrowRight,
  ChevronDown,
  Sparkles,
  Clock,
  Users,
  Download,
  AlertTriangle,
  GitCompareArrows,
  FileSpreadsheet,
  FolderSync,
  FileDown,
  Layers,
  Eye,
  Pencil,
  Server,
} from 'lucide-react'

function AnimatedSection({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  const [ref, isVisible] = useIntersectionObserver()
  return (
    <div
      ref={ref}
      className={`animate-on-scroll ${isVisible ? 'visible' : ''} ${className}`}
    >
      {children}
    </div>
  )
}

export default function LandingPage() {
  const [scrollY, setScrollY] = useState(0)

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY)
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div className="min-h-screen bg-white text-gray-900">
      {/* Navigation */}
      <nav
        className={`fixed top-0 z-50 w-full transition-all duration-300 ${
          scrollY > 50
            ? 'bg-white/95 shadow-sm backdrop-blur-md'
            : 'bg-transparent'
        }`}
      >
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
              <FileSearch className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-bold">PolicyReview AI</span>
          </div>
          <div className="hidden items-center gap-8 md:flex">
            <a href="#features" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              機能
            </a>
            <a href="#problems" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              課題解決
            </a>
            <a href="#workflow" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              ワークフロー
            </a>
            <a href="#comparison" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              規程比較
            </a>
            <Link
              href="/"
              className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 transition-colors"
            >
              アプリを開く
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden pt-32 pb-20 md:pt-40 md:pb-32">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 h-[600px] w-[600px] rounded-full bg-blue-50 blur-3xl opacity-60" />
          <div className="absolute top-40 right-0 h-[400px] w-[400px] rounded-full bg-indigo-50 blur-3xl opacity-40" />
        </div>

        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-1.5 text-sm text-blue-700">
              <Sparkles className="h-4 w-4" />
              AIが規程文書を自動レビュー
            </div>
            <h1 className="mb-6 text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl md:text-6xl">
              <span className="block">規程・社内文書の</span>
              <span className="block bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                レビュー品質を革新する
              </span>
            </h1>
            <p className="mb-10 text-lg text-gray-600 md:text-xl">
              就業規則、情報セキュリティポリシー、内部統制規程——
              <br className="hidden md:block" />
              AIが用語統一・文法・法令準拠を瞬時にチェック。
              <br className="hidden md:block" />
              親子会社間の規程比較やExcel入出力にも対応。
            </p>
            <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
              <Link
                href="/"
                className="group flex items-center gap-2 rounded-xl bg-blue-600 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700 transition-all hover:shadow-xl hover:shadow-blue-600/30"
              >
                無料で始める
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
              <a
                href="#features"
                className="flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-8 py-3.5 text-base font-semibold text-gray-700 shadow-sm hover:bg-gray-50 transition-colors"
              >
                機能を見る
              </a>
            </div>
          </div>

          {/* Stats */}
          <div className="mt-20 grid grid-cols-2 gap-4 md:grid-cols-4">
            {[
              { value: '80%', label: 'レビュー工数削減', icon: Clock },
              { value: '7+', label: 'チェック観点', icon: CheckCircle2 },
              { value: '99%', label: '用語不統一の検出率', icon: FileSearch },
              { value: '< 3分', label: '100ページの処理時間', icon: Zap },
            ].map((stat) => (
              <div
                key={stat.label}
                className="rounded-2xl border border-gray-100 bg-white p-6 text-center shadow-sm"
              >
                <stat.icon className="mx-auto mb-3 h-6 w-6 text-blue-600" />
                <div className="text-2xl font-extrabold text-gray-900 md:text-3xl">
                  {stat.value}
                </div>
                <div className="mt-1 text-sm text-gray-500">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-16 flex justify-center">
          <a href="#problems" className="animate-bounce text-gray-400">
            <ChevronDown className="h-6 w-6" />
          </a>
        </div>
      </section>

      {/* Problems Section */}
      <section id="problems" className="bg-gray-50 py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-6">
          <AnimatedSection>
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
                こんな課題、ありませんか？
              </h2>
              <p className="mt-4 text-lg text-gray-600">
                規程文書のレビューは、多くの企業にとって大きな負担です
              </p>
            </div>
          </AnimatedSection>

          <div className="mt-16 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {[
              {
                icon: AlertTriangle,
                color: 'red',
                title: '用語の不統一',
                description:
                  '「社員」「従業員」「職員」——同じ意味の用語が文書内で混在。法的リスクや誤解を招きます。',
              },
              {
                icon: Clock,
                color: 'yellow',
                title: 'レビュー工数の増大',
                description:
                  '数百ページの規程を人の目でチェック。法務・総務が数日〜数週間を費やします。',
              },
              {
                icon: Users,
                color: 'blue',
                title: '属人化するチェック',
                description:
                  'ベテランしか気づけない問題。担当者の異動・退職で品質が低下するリスク。',
              },
              {
                icon: GitCompareArrows,
                color: 'purple',
                title: '親子間の規程不整合',
                description:
                  '親会社と子会社の規程の整合性チェックを手作業で実施。漏れや見落としが発生。',
              },
            ].map((problem) => (
              <div
                key={problem.title}
                className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm"
              >
                <div
                  className={`inline-flex h-12 w-12 items-center justify-center rounded-xl ${
                    problem.color === 'red'
                      ? 'bg-red-100 text-red-600'
                      : problem.color === 'yellow'
                        ? 'bg-yellow-100 text-yellow-600'
                        : problem.color === 'purple'
                          ? 'bg-purple-100 text-purple-600'
                          : 'bg-blue-100 text-blue-600'
                  }`}
                >
                  <problem.icon className="h-6 w-6" />
                </div>
                <h3 className="mt-5 text-xl font-bold">{problem.title}</h3>
                <p className="mt-3 text-gray-600 leading-relaxed">{problem.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-6">
          <AnimatedSection>
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
                PolicyReview AI の機能
              </h2>
              <p className="mt-4 text-lg text-gray-600">
                AIの力で、規程文書のレビューを根本から変えます
              </p>
            </div>
          </AnimatedSection>

          <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: FileSearch,
                title: 'AIレビューエンジン',
                isNew: false,
                description:
                  'Azure OpenAI / AWS Bedrock / GCP Vertex AI など主要LLMに対応。用語統一、文法、法令準拠など多角的に自動チェック。',
              },
              {
                icon: Layers,
                title: '一括レビュー',
                isNew: true,
                description:
                  '複数の文書を一度に選択してバッチレビューを実行。大量の規程を効率よく処理できます。',
              },
              {
                icon: GitCompareArrows,
                title: '親子会社規程比較',
                isNew: true,
                description:
                  '親会社規程からAIがチェックリストを自動生成。子会社規程との適合・欠落・相違を5段階で判定。',
              },
              {
                icon: FileSpreadsheet,
                title: 'Excel入出力対応',
                isNew: true,
                description:
                  'Excelファイル(.xlsx/.xls)のアップロードとテキスト抽出に対応。レビュー結果もExcelで出力。',
              },
              {
                icon: Eye,
                title: 'コンテキスト表示・提案編集',
                isNew: true,
                description:
                  '指摘箇所の前後文脈を表示。AIの修正提案をカスタム編集し、改訂版文書プレビューも可能。',
              },
              {
                icon: FileDown,
                title: '改訂版DOCXダウンロード',
                isNew: true,
                description:
                  '承認した指摘事項を反映した改訂版文書をWord形式でダウンロード。変更箇所の追跡も容易。',
              },
              {
                icon: BookOpen,
                title: '用語辞書管理',
                isNew: false,
                description:
                  '正式用語とエイリアスを辞書登録。「社員→従業員」のような表記ゆれをAIが自動検出し統一候補を提案。',
              },
              {
                icon: Shield,
                title: '指摘事項ワークフロー',
                isNew: false,
                description:
                  'AIの指摘に対して承認・却下・保留のワークフロー。一括承認やフィルタリングで大量の指摘も効率的に処理。',
              },
              {
                icon: BarChart3,
                title: 'ダッシュボード・統計',
                isNew: false,
                description:
                  'レビュー件数、指摘の重要度分布、対応状況をリアルタイムで可視化。品質改善の傾向を一目で把握。',
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="group rounded-2xl border border-gray-100 bg-white p-8 shadow-sm transition-all hover:border-blue-200 hover:shadow-md"
              >
                <div className="flex items-center gap-3">
                  <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-blue-600 transition-colors group-hover:bg-blue-100">
                    <feature.icon className="h-6 w-6" />
                  </div>
                  {feature.isNew && (
                    <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-700">
                      NEW
                    </span>
                  )}
                </div>
                <h3 className="mt-5 text-lg font-bold">{feature.title}</h3>
                <p className="mt-3 text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow Section */}
      <section id="workflow" className="bg-gray-900 py-20 md:py-28 text-white">
        <div className="mx-auto max-w-7xl px-6">
          <AnimatedSection>
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
                4ステップで完了
              </h2>
              <p className="mt-4 text-lg text-gray-400">
                PDF/Excelをアップロードするだけ。あとはAIにお任せ。
              </p>
            </div>
          </AnimatedSection>

          <div className="mt-16 grid gap-8 md:grid-cols-4">
            {[
              {
                step: '01',
                icon: FileText,
                title: '文書をアップロード',
                description:
                  'PDF・Excelの規程文書をアップロード。OCRで自動テキスト抽出。50MBまで対応。',
              },
              {
                step: '02',
                icon: Sparkles,
                title: 'AIがレビュー実行',
                description:
                  'チェック項目と用語辞書をもとに、AIが文書全体を網羅的にレビュー。一括レビューも可能。',
              },
              {
                step: '03',
                icon: Pencil,
                title: '指摘を確認・編集',
                description:
                  '指摘事項の文脈を確認し、AI提案をカスタム編集。承認・却下・保留を選択。',
              },
              {
                step: '04',
                icon: Download,
                title: 'レポート・改訂版出力',
                description:
                  'Excel形式のレビューレポートと改訂版Word文書をダウンロード。報告・共有もスムーズ。',
              },
            ].map((item) => (
              <div key={item.step} className="relative">
                <div className="mb-4 text-5xl font-extrabold text-gray-800">
                  {item.step}
                </div>
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600/20 text-blue-400">
                  <item.icon className="h-6 w-6" />
                </div>
                <h3 className="mt-5 text-xl font-bold">{item.title}</h3>
                <p className="mt-3 text-gray-400 leading-relaxed">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Feature Highlight */}
      <section id="comparison" className="py-20 md:py-28 bg-gradient-to-br from-indigo-50 to-blue-50">
        <div className="mx-auto max-w-7xl px-6">
          <AnimatedSection>
          <div className="grid gap-12 md:grid-cols-2 items-center">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-indigo-100 px-4 py-1.5 text-sm font-medium text-indigo-700">
                <GitCompareArrows className="h-4 w-4" />
                NEW: 親子会社規程比較
              </div>
              <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
                親会社・子会社の
                <br />
                規程差異を自動検出
              </h2>
              <p className="mt-4 text-lg text-gray-600 leading-relaxed">
                AIが親会社規程からチェックリストを自動生成し、
                子会社規程との整合性を5段階で判定。
                適合・より厳格・緩い・欠落・異なるの分類で、
                対応が必要な箇所を一目で把握できます。
              </p>
              <div className="mt-8 space-y-3">
                {[
                  'チェックリスト自動生成（AIが親会社規程を分析）',
                  'ステップウィザード形式で簡単操作',
                  '5段階の判定結果（色分け表示）',
                  '比較結果のExcelエクスポート',
                ].map((item) => (
                  <div key={item} className="flex items-center gap-3 text-sm text-gray-700">
                    <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
                    {item}
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-lg">
              <div className="space-y-3">
                {[
                  { status: '適合', color: 'bg-green-100 text-green-800', width: 'w-full' },
                  { status: 'より厳格', color: 'bg-blue-100 text-blue-800', width: 'w-4/5' },
                  { status: '緩い', color: 'bg-orange-100 text-orange-800', width: 'w-3/5' },
                  { status: '欠落', color: 'bg-red-100 text-red-800', width: 'w-2/5' },
                  { status: '異なる', color: 'bg-yellow-100 text-yellow-800', width: 'w-1/5' },
                ].map((item) => (
                  <div key={item.status} className="flex items-center gap-3">
                    <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${item.color}`}>
                      {item.status}
                    </span>
                    <div className="flex-1 h-3 rounded-full bg-gray-100 overflow-hidden">
                      <div className={`h-full rounded-full ${item.color.split(' ')[0]} ${item.width} transition-all`} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-6 grid grid-cols-2 gap-4 text-center">
                <div className="rounded-xl bg-gray-50 p-4">
                  <div className="text-2xl font-bold text-gray-900">25</div>
                  <div className="text-xs text-gray-500">チェック項目</div>
                </div>
                <div className="rounded-xl bg-gray-50 p-4">
                  <div className="text-2xl font-bold text-green-600">72%</div>
                  <div className="text-xs text-gray-500">適合率</div>
                </div>
              </div>
            </div>
          </div>
          </AnimatedSection>
        </div>
      </section>

      {/* Tech Stack / Enterprise */}
      <section className="py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
              エンタープライズ対応
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              セキュリティと運用性を重視した設計
            </p>
          </div>

          <div className="mt-16 grid gap-6 md:grid-cols-3">
            {[
              {
                icon: Server,
                title: 'マルチクラウドLLM',
                items: ['Azure OpenAI', 'AWS Bedrock', 'GCP Vertex AI', 'Ollama（ローカル）'],
              },
              {
                icon: Shield,
                title: 'セキュリティ',
                items: ['JWT認証', 'レート制限', 'セキュリティヘッダー', '監査ログ'],
              },
              {
                icon: BarChart3,
                title: '運用・監視',
                items: ['Prometheusメトリクス', 'サーキットブレーカー', '構造化ログ', 'ヘルスチェック'],
              },
            ].map((section) => (
              <div
                key={section.title}
                className="rounded-2xl border border-gray-100 bg-white p-8 shadow-sm"
              >
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gray-100 text-gray-600">
                  <section.icon className="h-6 w-6" />
                </div>
                <h3 className="mt-5 text-lg font-bold">{section.title}</h3>
                <ul className="mt-4 space-y-2">
                  {section.items.map((item) => (
                    <li key={item} className="flex items-center gap-2 text-sm text-gray-600">
                      <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Supported Regulations */}
      <section className="bg-gray-50 py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
              対応する規程文書
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              あらゆる社内規程のレビューをサポート
            </p>
          </div>

          <div className="mt-12 flex flex-wrap justify-center gap-3">
            {[
              '就業規則',
              '情報セキュリティポリシー',
              '内部統制規程',
              'コンプライアンス規程',
              '個人情報保護規程',
              'リスク管理規程',
              '経理規程',
              '取締役会規則',
              '稟議規程',
              '出張旅費規程',
              'ハラスメント防止規程',
              'テレワーク規程',
              '知的財産管理規程',
              '危機管理マニュアル',
              '反社会的勢力対応規程',
            ].map((doc) => (
              <span
                key={doc}
                className="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700"
              >
                {doc}
              </span>
            ))}
          </div>

          <div className="mt-8 text-center">
            <p className="text-sm text-gray-500">
              PDF / Excel (.xlsx, .xls) 形式に対応
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-br from-blue-600 to-indigo-700 py-20 md:py-28">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white md:text-4xl">
            規程レビューの未来を、今すぐ体験
          </h2>
          <p className="mt-4 text-lg text-blue-100">
            セットアップ不要。ブラウザからすぐに利用開始できます。
          </p>
          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/"
              className="group inline-flex items-center gap-2 rounded-xl bg-white px-10 py-4 text-lg font-bold text-blue-600 shadow-xl transition-all hover:bg-gray-50 hover:shadow-2xl"
            >
              ダッシュボードを開く
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link
              href="/comparisons"
              className="group inline-flex items-center gap-2 rounded-xl border-2 border-white/30 px-8 py-4 text-lg font-bold text-white transition-all hover:bg-white/10"
            >
              規程比較を試す
              <GitCompareArrows className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-white py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600">
                <FileSearch className="h-4 w-4 text-white" />
              </div>
              <span className="font-bold">PolicyReview AI</span>
            </div>
            <p className="text-sm text-gray-500">
              &copy; 2026 PolicyReview AI. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
