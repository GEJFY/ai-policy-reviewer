@echo off
echo ========================================
echo   AI Policy Reviewer - Stop All
echo ========================================
echo.

echo Stopping backend processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8004 ^| findstr LISTENING') do (
    taskkill /f /pid %%a 2>nul
)

echo Stopping frontend processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3033 ^| findstr LISTENING') do (
    taskkill /f /pid %%a 2>nul
)

echo.
echo ========================================
echo   All services stopped
echo ========================================
echo.
pause
