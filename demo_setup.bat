@echo off
echo ================================================================
echo   AI Policy Reviewer - Demo Environment Setup
echo ================================================================
echo.
echo This script will:
echo   1. Seed demo data (terms, check items, writing rules)
echo   2. Generate demo sample PDFs
echo   3. Start backend and frontend services
echo.
echo ----------------------------------------------------------------

cd /d "%~dp0"

REM ==================================================================
REM Step 1: Check environment
REM ==================================================================
echo.
echo [Step 1/4] Checking environment...

if not exist ".env" (
    if exist ".env.example" (
        echo   * .env not found. Copying from .env.example...
        copy .env.example .env >nul
        echo   -> Created .env. Please set your LLM provider credentials.
    ) else (
        echo   * .env not found. Please configure LLM provider settings first.
        echo.
        pause
        exit /b 1
    )
)

echo   OK - Environment check passed

REM ==================================================================
REM Step 2: Seed demo data
REM ==================================================================
echo.
echo [Step 2/4] Seeding demo data...
echo.

cd /d C:\dev-pr\backend
C:\Users\goyos\.venvs\ai-policy-reviewer3\Scripts\python.exe -m scripts.seed_demo_data
if errorlevel 1 (
    echo   FAILED - Demo data seeding failed
    pause
    exit /b 1
)

REM ==================================================================
REM Step 3: Generate demo PDFs
REM ==================================================================
echo.
echo [Step 3/4] Generating demo PDFs...
echo.

C:\Users\goyos\.venvs\ai-policy-reviewer3\Scripts\python.exe -m scripts.generate_demo_pdfs
if errorlevel 1 (
    echo   WARNING - PDF generation failed (ReportLab required)
    echo   Manual: cd backend ^& python -m scripts.generate_demo_pdfs
)

cd /d "%~dp0"

REM ==================================================================
REM Step 4: Start services
REM ==================================================================
echo.
echo [Step 4/4] Starting services...
echo.

if exist "start.bat" (
    echo   Running start.bat...
    call start.bat
) else (
    echo   WARNING - start.bat not found. Start manually:
    echo     Backend:  cd backend ^& uvicorn app.main:app --port 8004
    echo     Frontend: cd frontend ^& npm run dev
)

echo.
echo ================================================================
echo   Demo Environment Setup Complete
echo ================================================================
echo.
echo To begin the demo:
echo   1. Open http://localhost:3033 in your browser
echo   2. Go to Document Management and upload PDFs from samples/
echo   3. Run AI Review
echo.
echo Available sample PDFs:
echo   - samples\test.pdf
echo   - samples\test2.pdf
echo   - samples\test_full.pdf
echo.
pause
