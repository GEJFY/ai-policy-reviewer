@echo off
echo ========================================
echo   AI Policy Reviewer - Backend Start
echo ========================================
echo.

cd /d C:\dev-pr\backend

set DISABLE_SQLALCHEMY_CEXT_RUNTIME=1

echo.
echo Starting backend server...
echo URL: http://localhost:8004
echo API Docs: http://localhost:8004/docs
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

C:\Users\goyos\.venvs\ai-policy-reviewer3\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8004

pause
