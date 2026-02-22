'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { Card, CardContent } from '@/components/ui/card'
import {
  FileText,
  Upload,
  FileSearch,
  CheckSquare,
  BookOpen,
  ListChecks,
  FolderSync,
  GitCompareArrows,
  Settings,
  HelpCircle,
  ChevronRight,
} from 'lucide-react'

interface Section {
  id: string
  title: string
  icon: React.ElementType
  content: React.ReactNode
}

const sections: Section[] = [
  {
    id: 'overview',
    title: '概要',
    icon: HelpCircle,
    content: (
      <div className="space-y-4">
        <p>
          規程レビューツールは、AIを活用して社内規程・ポリシー文書のレビューを自動化するツールです。
          文書のアップロードからレビュー実行、結果の確認・承認、レポート出力まで一連のワークフローをサポートします。
        </p>
        <h4 className="font-semibold">主な機能</h4>
        <ul className="list-disc pl-6 space-y-1">
          <li>PDF/テキスト文書のアップロードとOCR処理</li>
          <li>AIによる自動レビュー（用語統一、文体統一、法的要件チェック等）</li>
          <li>レビュー結果の承認・却下・保留ワークフロー</li>
          <li>修正文書のプレビューとダウンロード</li>
          <li>複数文書の一括レビューと整合性チェック</li>
          <li>親子会社間の規程比較</li>
          <li>用語辞書・チェック項目・記載ルールのカスタマイズ</li>
          <li>CSV/Excelによる一括インポート</li>
          <li>レビュー結果のExcelエクスポート</li>
        </ul>
      </div>
    ),
  },
  {
    id: 'documents',
    title: '文書管理',
    icon: FileText,
    content: (
      <div className="space-y-4">
        <h4 className="font-semibold">文書のアップロード</h4>
        <ol className="list-decimal pl-6 space-y-2">
          <li>サイドメニューから「文書管理」を開きます</li>
          <li>「アップロード」ボタンをクリックします</li>
          <li>PDF、テキスト、Word文書を選択します（最大50MB）</li>
          <li>アップロードが完了すると、OCR処理が自動的に開始されます</li>
          <li>OCR処理が完了すると、テキストが抽出されレビュー可能になります</li>
        </ol>

        <h4 className="font-semibold mt-6">対応ファイル形式</h4>
        <ul className="list-disc pl-6 space-y-1">
          <li><strong>PDF</strong> - テキスト埋め込みPDF、スキャンPDF（OCR処理）</li>
          <li><strong>テキスト</strong> - .txt ファイル</li>
          <li><strong>Word</strong> - .docx ファイル</li>
          <li><strong>Excel</strong> - .xlsx ファイル</li>
        </ul>

        <h4 className="font-semibold mt-6">文書の削除</h4>
        <p>
          文書を削除すると、関連するレビュー結果、比較プロジェクト、グループ参加情報もすべて削除されます。
          この操作は取り消せません。
        </p>
      </div>
    ),
  },
  {
    id: 'reviews',
    title: 'レビュー',
    icon: FileSearch,
    content: (
      <div className="space-y-4">
        <h4 className="font-semibold">レビューの実行</h4>
        <ol className="list-decimal pl-6 space-y-2">
          <li>「文書管理」から対象文書を選択します</li>
          <li>「レビュー実行」ボタンをクリックします</li>
          <li>実行するチェック項目を選択します（デフォルトは全項目）</li>
          <li>AIがバックグラウンドでレビューを実行します</li>
          <li>完了すると「レビュー」一覧に結果が表示されます</li>
        </ol>

        <h4 className="font-semibold mt-6">レビュー結果の確認</h4>
        <p>各指摘事項に対して以下のアクションが可能です：</p>
        <ul className="list-disc pl-6 space-y-1">
          <li><strong>承認</strong> - 指摘を受け入れ、修正文書に反映</li>
          <li><strong>却下</strong> - 指摘を却下（修正不要と判断）</li>
          <li><strong>保留</strong> - 判断を保留</li>
        </ul>
        <p className="mt-2">
          承認時にはAIの提案を編集して、独自の修正内容を指定することもできます。
        </p>

        <h4 className="font-semibold mt-6">修正文書のプレビュー</h4>
        <p>
          承認した指摘に基づく修正文書をプレビューできます。
          差分表示では、変更箇所のみがハイライト表示されます。
        </p>

        <h4 className="font-semibold mt-6">エクスポート</h4>
        <ul className="list-disc pl-6 space-y-1">
          <li><strong>個別ダウンロード</strong> - 各レビューのExcelレポートをダウンロード</li>
          <li><strong>一括ダウンロード</strong> - 複数レビューを選択してまとめてExcelダウンロード</li>
          <li><strong>修正文書</strong> - Word形式で修正後の文書をダウンロード</li>
        </ul>
      </div>
    ),
  },
  {
    id: 'terms',
    title: '用語辞書',
    icon: BookOpen,
    content: (
      <div className="space-y-4">
        <p>
          用語辞書は、文書内で統一すべき用語を定義する機能です。
          レビュー時にAIがこの辞書を参照し、用語の不統一を検出します。
        </p>

        <h4 className="font-semibold">用語の登録</h4>
        <ul className="list-disc pl-6 space-y-1">
          <li><strong>用語</strong> - 正式な表記（例：「従業員」）</li>
          <li><strong>別名</strong> - 同義語・非推奨表記（例：「社員」「スタッフ」）</li>
          <li><strong>カテゴリ</strong> - 分類（人事、財務、IT、法務、一般）</li>
          <li><strong>定義</strong> - 用語の正式な定義</li>
          <li><strong>使用上の注意</strong> - 使い分けのルールなど</li>
        </ul>

        <h4 className="font-semibold mt-6">一括インポート</h4>
        <p>
          CSV/Excelファイルから用語を一括登録できます。
          「テンプレートをダウンロード」から雛形を取得し、データを入力してインポートしてください。
        </p>
      </div>
    ),
  },
  {
    id: 'check-items',
    title: 'チェック項目',
    icon: CheckSquare,
    content: (
      <div className="space-y-4">
        <p>
          チェック項目は、AIがレビュー時に確認する観点を定義する機能です。
          デフォルトで用語統一、文体チェック、法的要件などが用意されています。
        </p>

        <h4 className="font-semibold">チェック項目の設定</h4>
        <ul className="list-disc pl-6 space-y-1">
          <li><strong>項目名</strong> - チェックの名称</li>
          <li><strong>カテゴリ</strong> - 用語統一、文法・表現、構成・体裁、法令・コンプライアンス等</li>
          <li><strong>重要度</strong> - HIGH / MEDIUM / LOW</li>
          <li><strong>説明</strong> - チェック内容の詳細</li>
          <li><strong>カスタムプロンプト</strong> - AIへの指示をカスタマイズ（上級者向け）</li>
        </ul>

        <h4 className="font-semibold mt-6">有効/無効の切り替え</h4>
        <p>
          使わないチェック項目は「無効」にすることで、レビュー実行時の選択肢から除外できます。
        </p>
      </div>
    ),
  },
  {
    id: 'writing-rules',
    title: '記載ルール',
    icon: ListChecks,
    content: (
      <div className="space-y-4">
        <p>
          記載ルールは、文書の表記・文体に関するルールを定義する機能です。
          AIがレビュー時にこれらのルールを参照し、違反箇所を検出します。
        </p>

        <h4 className="font-semibold">ルールの種類</h4>
        <ul className="list-disc pl-6 space-y-1">
          <li><strong>文体ルール</strong> - 「です・ます」調と「である」調の統一など</li>
          <li><strong>フォーマットルール</strong> - 数字の全角・半角統一、日付表記など</li>
          <li><strong>用語ルール</strong> - 特定の表記に関するルール</li>
        </ul>

        <h4 className="font-semibold mt-6">設定項目</h4>
        <ul className="list-disc pl-6 space-y-1">
          <li><strong>検出パターン</strong> - 問題を検出するためのパターン</li>
          <li><strong>正しい形式</strong> - あるべき表記の説明</li>
          <li><strong>NG例 / OK例</strong> - 具体的な例</li>
        </ul>
      </div>
    ),
  },
  {
    id: 'document-groups',
    title: '規程グループ',
    icon: FolderSync,
    content: (
      <div className="space-y-4">
        <p>
          規程グループは、関連する複数の文書をまとめて整合性をチェックする機能です。
          例えば、就業規則と給与規程をグループ化し、用語の統一や参照関係を確認できます。
        </p>

        <h4 className="font-semibold">使い方</h4>
        <ol className="list-decimal pl-6 space-y-2">
          <li>「規程グループ」からグループを作成します</li>
          <li>関連する文書をメンバーとして追加します</li>
          <li>「整合性チェック」を実行します</li>
          <li>文書間の矛盾・不整合が検出されます</li>
        </ol>

        <h4 className="font-semibold mt-6">検出される問題</h4>
        <ul className="list-disc pl-6 space-y-1">
          <li>文書間での用語の不統一</li>
          <li>参照先文書の条項との矛盾</li>
          <li>数値・期間の差異</li>
          <li>定義の不一致</li>
        </ul>
      </div>
    ),
  },
  {
    id: 'comparisons',
    title: '親子会社比較',
    icon: GitCompareArrows,
    content: (
      <div className="space-y-4">
        <p>
          親子会社比較は、親会社と子会社の規程を比較し、差異や不足を検出する機能です。
          グループ会社間での規程の整合性を確保するのに役立ちます。
        </p>

        <h4 className="font-semibold">比較の実行手順</h4>
        <ol className="list-decimal pl-6 space-y-2">
          <li>「親子会社比較」から比較プロジェクトを作成します</li>
          <li>親会社の規程文書を選択します</li>
          <li>「チェックリスト生成」でAIが比較観点を自動生成します</li>
          <li>チェックリストを確認・編集します</li>
          <li>子会社の規程文書を選択します</li>
          <li>「比較実行」で差異を検出します</li>
        </ol>

        <h4 className="font-semibold mt-6">比較結果の見方</h4>
        <ul className="list-disc pl-6 space-y-1">
          <li><strong className="text-green-600">適合</strong> - 親会社の基準を満たしている</li>
          <li><strong className="text-yellow-600">一部差異</strong> - 差異があるが大きな問題ではない</li>
          <li><strong className="text-red-600">不適合</strong> - 重要な差異や欠落がある</li>
          <li><strong className="text-gray-500">該当なし</strong> - 子会社に該当する条項がない</li>
        </ul>

        <h4 className="font-semibold mt-6">結果のエクスポート</h4>
        <p>比較結果はExcel形式でダウンロードできます。</p>
      </div>
    ),
  },
  {
    id: 'settings',
    title: '設定',
    icon: Settings,
    content: (
      <div className="space-y-4">
        <p>設定画面では、システムの構成情報を確認できます。</p>

        <h4 className="font-semibold">確認できる情報</h4>
        <ul className="list-disc pl-6 space-y-1">
          <li><strong>LLMプロバイダー</strong> - 使用中のAIモデル（Azure OpenAI、AWS Bedrock等）</li>
          <li><strong>OCRプロバイダー</strong> - PDF文字認識サービス（Azure Document Intelligence等）</li>
          <li><strong>データベース</strong> - 接続状態</li>
          <li><strong>ヘルスチェック</strong> - 各サービスの稼働状態</li>
        </ul>

        <h4 className="font-semibold mt-6">環境設定</h4>
        <p>
          LLMやOCRの設定は環境変数（.envファイル）で行います。
          詳細はセットアップガイドを参照してください。
        </p>
      </div>
    ),
  },
  {
    id: 'faq',
    title: 'よくある質問',
    icon: HelpCircle,
    content: (
      <div className="space-y-6">
        <div>
          <h4 className="font-semibold">Q: レビューにどのくらい時間がかかりますか？</h4>
          <p className="mt-1 text-gray-600">
            A: 文書の長さとチェック項目数によりますが、一般的な規程（20〜60条程度）で
            全チェック項目を実行した場合、2〜5分程度です。
          </p>
        </div>
        <div>
          <h4 className="font-semibold">Q: 対応している言語は？</h4>
          <p className="mt-1 text-gray-600">
            A: 日本語の規程文書に最適化されています。英語文書にも対応していますが、
            チェック項目や用語辞書は日本語での設定を推奨します。
          </p>
        </div>
        <div>
          <h4 className="font-semibold">Q: AIの判断は信頼できますか？</h4>
          <p className="mt-1 text-gray-600">
            A: AIの判断は参考情報として活用してください。最終的な判断は人間が行うことを推奨します。
            特に法的要件に関する指摘は、専門家（弁護士・社労士等）に確認することをお勧めします。
          </p>
        </div>
        <div>
          <h4 className="font-semibold">Q: データのセキュリティは？</h4>
          <p className="mt-1 text-gray-600">
            A: アップロードされた文書はローカルサーバーに保存され、外部サービスにはLLM/OCR処理時のみ
            テキストデータが送信されます。Azure OpenAIのデータはMicrosoftの規約に基づき管理されます。
          </p>
        </div>
        <div>
          <h4 className="font-semibold">Q: CSV/Excelインポートのエンコーディングは？</h4>
          <p className="mt-1 text-gray-600">
            A: UTF-8（BOM付き/なし）、Shift_JIS、CP932に対応しています。
            Excelで保存したCSVファイルもそのままインポートできます。
          </p>
        </div>
        <div>
          <h4 className="font-semibold">Q: レビュー結果を修正できますか？</h4>
          <p className="mt-1 text-gray-600">
            A: 各指摘事項に対してコメントを追加したり、AIの改善提案を編集して独自の修正内容を
            指定することができます。承認時に「提案を編集」から修正してください。
          </p>
        </div>
      </div>
    ),
  },
]

export default function ManualPage() {
  const [activeSection, setActiveSection] = useState('overview')

  return (
    <>
      <Header title="ユーザーマニュアル" />
      <div className="flex h-[calc(100vh-4rem)]">
        {/* Table of Contents */}
        <nav className="w-64 shrink-0 border-r bg-gray-50 overflow-y-auto" aria-label="目次">
          <div className="p-4">
            <h2 className="mb-3 text-sm font-semibold text-gray-500 uppercase tracking-wider">
              目次
            </h2>
            <ul className="space-y-1">
              {sections.map((section) => {
                const Icon = section.icon
                return (
                  <li key={section.id}>
                    <button
                      onClick={() => setActiveSection(section.id)}
                      className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
                        activeSection === section.id
                          ? 'bg-blue-50 text-blue-700 font-medium'
                          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                      }`}
                    >
                      <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                      <span className="truncate">{section.title}</span>
                      {activeSection === section.id && (
                        <ChevronRight className="ml-auto h-4 w-4 shrink-0" aria-hidden="true" />
                      )}
                    </button>
                  </li>
                )
              })}
            </ul>
          </div>
        </nav>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6">
          {sections.map((section) => (
            <div
              key={section.id}
              className={activeSection === section.id ? '' : 'hidden'}
            >
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <section.icon className="h-6 w-6 text-blue-600" aria-hidden="true" />
                    <h3 className="text-xl font-semibold">{section.title}</h3>
                  </div>
                  <div className="prose prose-sm max-w-none text-gray-700 leading-relaxed">
                    {section.content}
                  </div>
                </CardContent>
              </Card>
            </div>
          ))}
        </main>
      </div>
    </>
  )
}
