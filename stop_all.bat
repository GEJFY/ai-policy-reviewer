@echo off
chcp 65001 >nul
echo ========================================
echo   規程レビューツール - 全サービス停止
echo ========================================
echo.

echo バックエンドプロセスを停止中...
taskkill /f /im python.exe /fi "WINDOWTITLE eq Policy Reviewer - Backend*" 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING') do (
    taskkill /f /pid %%a 2>nul
)

echo フロントエンドプロセスを停止中...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3030 ^| findstr LISTENING') do (
    taskkill /f /pid %%a 2>nul
)

echo.
echo ========================================
echo   全サービスを停止しました
echo ========================================
echo.
pause
