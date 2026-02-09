@echo off
chcp 65001 >nul
echo ================================================================
echo   規程レビューツール - デモ環境一括セットアップ
echo ================================================================
echo.
echo このスクリプトは以下を実行します:
echo   1. デモデータの投入（用語辞書50件、チェック項目20件、記載ルール15件）
echo   2. デモ用サンプルPDFの生成（就業規則、情報セキュリティ、内部統制）
echo   3. バックエンド・フロントエンドの起動
echo.
echo ----------------------------------------------------------------

cd /d "%~dp0"

REM ==================================================================
REM Step 1: 環境確認
REM ==================================================================
echo.
echo [Step 1/4] 環境確認中...

if not exist "backend\venv\Scripts\activate.bat" (
    echo   ※ 仮想環境が見つかりません。先に setup.bat を実行してください。
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        echo   ※ .env ファイルが見つかりません。.env.example からコピーします。
        copy .env.example .env >nul
        echo   → .env を作成しました。LLMプロバイダーの認証情報を設定してください。
    ) else (
        echo   ※ .env ファイルが見つかりません。先にLLMプロバイダーの設定を行ってください。
        echo.
        pause
        exit /b 1
    )
)

echo   ✓ 環境確認完了

REM ==================================================================
REM Step 2: デモデータ投入
REM ==================================================================
echo.
echo [Step 2/4] デモデータを投入中...
echo.

cd /d "%~dp0backend"
call venv\Scripts\activate.bat

python -m scripts.seed_demo_data
if errorlevel 1 (
    echo   ✗ デモデータ投入に失敗しました
    pause
    exit /b 1
)

REM ==================================================================
REM Step 3: デモ用PDF生成
REM ==================================================================
echo.
echo [Step 3/4] デモ用PDFを生成中...
echo.

python -m scripts.generate_demo_pdfs
if errorlevel 1 (
    echo   ⚠ PDF生成に失敗しました（ReportLabが必要です）
    echo   手動で実行する場合: cd backend ^& python -m scripts.generate_demo_pdfs
)

cd /d "%~dp0"

REM ==================================================================
REM Step 4: サービス起動
REM ==================================================================
echo.
echo [Step 4/4] サービスを起動中...
echo.

if exist "start_all.bat" (
    echo   start_all.bat を実行してサービスを起動します...
    call start_all.bat
) else (
    echo   ⚠ start_all.bat が見つかりません。手動で起動してください:
    echo     バックエンド: cd backend ^& uvicorn app.main:app --reload --port 8080
    echo     フロントエンド: cd frontend ^& npm run dev
)

echo.
echo ================================================================
echo   デモ環境セットアップ完了
echo ================================================================
echo.
echo デモを開始するには:
echo   1. ブラウザで http://localhost:3030 を開く
echo   2. サイドメニューの「文書管理」から samples/ フォルダのPDFをアップロード
echo   3. AIレビューを実行
echo.
echo 利用可能なサンプルPDF:
echo   - samples\就業規則_改定案_v2.pdf     （意図的な問題を多数含む）
echo   - samples\情報セキュリティポリシー.pdf （正式な形式のサンプル）
echo   - samples\内部統制規程.pdf            （法的要件チェック用）
echo.
echo 詳細は docs\DEMO_GUIDE.md を参照してください。
echo.
pause
