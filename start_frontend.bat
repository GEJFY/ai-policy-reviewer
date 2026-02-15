@echo off
echo ========================================
echo   AI Policy Reviewer - Frontend Start
echo ========================================
echo.

cd /d C:\dev-pr\frontend

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

echo.
echo Starting frontend server...
echo URL: http://localhost:3033
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

npx next dev --webpack -p 3033

pause
