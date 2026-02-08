@echo off
chcp 65001 >nul
echo ========================================
echo   規程レビューツール - 全サービス起動
echo ========================================
echo.
echo バックエンドとフロントエンドを起動します...
echo.

REM バックエンドを新しいウィンドウで起動
start "Policy Reviewer - Backend" cmd /c "%~dp0start_backend.bat"

REM 少し待機（バックエンドの起動を待つ）
echo バックエンドの起動を待機中...
timeout /t 5 /nobreak >nul

REM フロントエンドを新しいウィンドウで起動
start "Policy Reviewer - Frontend" cmd /c "%~dp0start_frontend.bat"

echo.
echo ========================================
echo サービスが起動しました
echo.
echo   フロントエンド: http://localhost:3030
echo   バックエンドAPI: http://localhost:8080
echo   APIドキュメント: http://localhost:8080/docs
echo.
echo 各ウィンドウを閉じるとサービスが停止します
echo ========================================
echo.

REM ブラウザを自動で開く（5秒後）
timeout /t 5 /nobreak >nul
start http://localhost:3030

pause
