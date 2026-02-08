@echo off
chcp 65001 >nul
echo ========================================
echo   規程レビューツール - バックエンド起動
echo ========================================
echo.

cd /d "%~dp0backend"

REM 仮想環境が存在する場合はアクティベート
if exist "venv\Scripts\activate.bat" (
    echo 仮想環境をアクティベート中...
    call venv\Scripts\activate.bat
)

REM データディレクトリの作成
if not exist "..\data" (
    echo データディレクトリを作成中...
    mkdir "..\data"
)

REM ログディレクトリの作成
if not exist "logs" (
    echo ログディレクトリを作成中...
    mkdir "logs"
)

echo.
echo バックエンドサーバーを起動中...
echo URL: http://localhost:8080
echo API Docs: http://localhost:8080/docs
echo.
echo 終了するには Ctrl+C を押してください
echo ========================================
echo.

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8080

pause
