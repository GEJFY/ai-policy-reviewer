@echo off
chcp 65001 >nul
echo ========================================
echo   規程レビューツール - デモデータ投入
echo ========================================
echo.

cd /d "%~dp0backend"

REM 仮想環境をアクティベート
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo デモデータを投入しています...
echo.
python -m scripts.seed_demo_data

echo.
echo ========================================
echo   デモデータ投入完了
echo ========================================
echo.
echo 次のステップ:
echo   1. サーバー起動: run_backend.bat または uvicorn app.main:app --reload
echo   2. http://localhost:8080/docs でAPI確認
echo   3. http://localhost:3030 でフロントエンド確認
echo.
pause
