'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
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
} from 'lucide-react'

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
        {/* Background decoration */}
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
              レビュー工数を<span className="font-semibold text-gray-900">最大80%</span>削減します。
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

          {/* Hero Image / Stats */}
          <div className="mt-20 grid grid-cols-2 gap-4 md:grid-cols-4">
            {[
              { value: '80%', label: 'レビュー工数削減', icon: Clock },
              { value: '300+', label: 'チェック観点', icon: CheckCircle2 },
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
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
              こんな課題、ありませんか？
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              規程文書のレビューは、多くの企業にとって大きな負担です
            </p>
          </div>

          <div className="mt-16 grid gap-6 md:grid-cols-3">
            {[
              {
                icon: AlertTriangle,
                color: 'red',
                title: '用語の不統一',
                description:
                  '「社員」「従業員」「職員」——同じ意味の用語が文書内で混在。改訂を重ねるたびに統一が崩れ、法的リスクや誤解を招きます。',
              },
              {
                icon: Clock,
                color: 'yellow',
                title: 'レビュー工数の増大',
                description:
                  '数百ページの規程を人の目でチェック。法務・総務部門の担当者が数日〜数週間を費やし、本来の業務が圧迫されます。',
              },
              {
                icon: Users,
                color: 'blue',
                title: '属人化するチェック品質',
                description:
                  'ベテラン社員しか気づけない問題、チェック観点のばらつき。担当者の異動・退職で品質が一気に低下するリスク。',
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
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
              PolicyReview AI の機能
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              AIの力で、規程文書のレビューを根本から変えます
            </p>
          </div>

          <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: FileSearch,
                title: 'AIレビューエンジン',
                description:
                  'Azure OpenAI / AWS Bedrock / GCP Vertex AI など主要LLMに対応。用語統一、文法、法令準拠など多角的に自動チェック。',
              },
              {
                icon: BookOpen,
                title: '用語辞書管理',
                description:
                  '正式用語とエイリアスを辞書登録。「社員→従業員」のような表記ゆれをAIが自動検出し、統一候補を提案します。',
              },
              {
                icon: CheckCircle2,
                title: 'カスタムチェック項目',
                description:
                  '企業独自のチェック観点を自由に定義。プロンプトテンプレートで検出精度を細かく調整できます。',
              },
              {
                icon: Shield,
                title: '指摘事項ワークフロー',
                description:
                  'AIの指摘に対して承認・却下・保留のワークフロー。一括承認やフィルタリングで大量の指摘も効率的に処理。',
              },
              {
                icon: Download,
                title: 'Excelレポート出力',
                description:
                  'レビュー結果をExcelファイルとしてエクスポート。概要シートと指摘事項一覧シートで報告資料をそのまま作成。',
              },
              {
                icon: BarChart3,
                title: 'ダッシュボード・統計',
                description:
                  'レビュー件数、指摘の重要度分布、対応状況をリアルタイムで可視化。品質改善の傾向を一目で把握。',
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="group rounded-2xl border border-gray-100 bg-white p-8 shadow-sm transition-all hover:border-blue-200 hover:shadow-md"
              >
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-blue-600 transition-colors group-hover:bg-blue-100">
                  <feature.icon className="h-6 w-6" />
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
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
              3ステップで完了
            </h2>
            <p className="mt-4 text-lg text-gray-400">
              PDFをアップロードするだけ。あとはAIにお任せ。
            </p>
          </div>

          <div className="mt-16 grid gap-8 md:grid-cols-3">
            {[
              {
                step: '01',
                icon: FileText,
                title: '文書をアップロード',
                description:
                  'PDF形式の規程文書をドラッグ＆ドロップ。OCRで自動テキスト抽出され、50MBまでの大型文書にも対応。',
              },
              {
                step: '02',
                icon: Sparkles,
                title: 'AIがレビュー実行',
                description:
                  '登録済みのチェック項目と用語辞書をもとに、AIが文書全体を網羅的にレビュー。進捗はリアルタイムで確認可能。',
              },
              {
                step: '03',
                icon: CheckCircle2,
                title: '指摘を確認・対応',
                description:
                  '検出された指摘事項を確認し、承認・却下・保留を選択。Excelレポートで関係者への共有もワンクリック。',
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

      {/* Supported Regulations */}
      <section className="py-20 md:py-28">
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
                className="rounded-full border border-gray-200 bg-gray-50 px-4 py-2 text-sm font-medium text-gray-700"
              >
                {doc}
              </span>
            ))}
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
          <div className="mt-10">
            <Link
              href="/"
              className="group inline-flex items-center gap-2 rounded-xl bg-white px-10 py-4 text-lg font-bold text-blue-600 shadow-xl transition-all hover:bg-gray-50 hover:shadow-2xl"
            >
              ダッシュボードを開く
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
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
