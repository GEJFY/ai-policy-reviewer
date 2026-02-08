@echo off
chcp 65001 >nul
echo ========================================
echo   規程レビューツール - テスト実行
echo ========================================
echo.

cd /d "%~dp0backend"

REM 仮想環境をアクティベート
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo [1/2] テストを実行中...
python -m pytest tests/ -v --tb=short

echo.
echo [2/2] カバレッジ付きでテストを実行...
python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

echo.
echo ========================================
echo   テスト完了
echo ========================================
echo.
echo カバレッジレポート: backend\htmlcov\index.html
echo.
pause
