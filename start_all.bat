@echo off
echo ========================================
echo   AI Policy Reviewer - Start All
echo ========================================
echo.
echo Starting backend and frontend...
echo.

REM Start backend in new window
set DISABLE_SQLALCHEMY_CEXT_RUNTIME=1
start "Backend-8004" cmd /k "cd /d C:\dev-pr\backend && C:\Users\goyos\.venvs\ai-policy-reviewer3\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8004"

REM Wait for backend to start
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Start frontend in new window
start "Frontend-3033" cmd /k "cd /d C:\dev-pr\frontend && npx next dev --webpack -p 3033"

echo.
echo ========================================
echo   Services started
echo.
echo   Frontend: http://localhost:3033
echo   Backend:  http://localhost:8004
echo   API Docs: http://localhost:8004/docs
echo.
echo   Close each window to stop its service
echo ========================================
echo.

REM Open browser after frontend is ready
timeout /t 20 /nobreak >nul
start http://localhost:3033

pause
