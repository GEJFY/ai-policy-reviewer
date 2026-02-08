@echo off
chcp 65001 >nul
echo ========================================
echo   規程レビューツール - 初期セットアップ
echo ========================================
echo.

cd /d "%~dp0"

REM データディレクトリの作成
echo [1/6] データディレクトリを作成中...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
echo       完了

REM バックエンドのセットアップ
echo.
echo [2/6] バックエンド仮想環境を作成中...
cd backend
if not exist "venv" (
    python -m venv venv
    echo       仮想環境を作成しました
) else (
    echo       仮想環境は既に存在します
)

echo.
echo [3/6] バックエンド依存関係をインストール中...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
echo       完了

echo.
echo [4/6] データベースを初期化中...
python -c "from app.db.init_db import create_tables; create_tables()"
echo       完了

echo.
echo [5/6] 初期データを投入中...
python -m app.db.seed_data
echo       完了

cd ..

REM フロントエンドのセットアップ
echo.
echo [6/6] フロントエンド依存関係をインストール中...
cd frontend
call npm install --silent
echo       完了

cd ..

echo.
echo ========================================
echo   セットアップが完了しました
echo ========================================
echo.
echo 次のステップ:
echo   1. .env ファイルにAzure認証情報を設定
echo   2. start_all.bat をダブルクリックして起動
echo.
echo 起動用バッチファイル:
echo   start_all.bat      - 全サービス起動（推奨）
echo   start_backend.bat  - バックエンドのみ
echo   start_frontend.bat - フロントエンドのみ
echo.
pause
