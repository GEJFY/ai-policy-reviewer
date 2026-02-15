@echo off
echo ====================================
echo   AI Policy Reviewer - Start
echo ====================================
echo.
echo [1/2] Starting Backend (port 8004)...
set DISABLE_SQLALCHEMY_CEXT_RUNTIME=1
start "Backend-8004" cmd /k "cd /d C:\dev-pr\backend && C:\Users\goyos\.venvs\ai-policy-reviewer3\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8004"
timeout /t 5 /nobreak >nul
echo [2/2] Starting Frontend (port 3033)...
start "Frontend-3033" cmd /k "cd /d C:\dev-pr\frontend && npx next dev --webpack -p 3033"
timeout /t 20 /nobreak >nul
echo.
echo   Backend:  http://localhost:8004
echo   Frontend: http://localhost:3033
echo ====================================
start http://localhost:3033
