@echo off
chcp 65001 >nul
echo ========================================
echo   規程レビューツール - フロントエンド起動
echo ========================================
echo.

cd /d "%~dp0frontend"

REM node_modulesが存在しない場合はインストール
if not exist "node_modules" (
    echo 依存関係をインストール中...
    call npm install
)

echo.
echo フロントエンドサーバーを起動中...
echo URL: http://localhost:3030
echo.
echo 終了するには Ctrl+C を押してください
echo ========================================
echo.

npm run dev

pause
