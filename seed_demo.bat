@echo off
echo ========================================
echo   AI Policy Reviewer - Seed Demo Data
echo ========================================
echo.

cd /d C:\dev-pr\backend

echo Seeding demo data...
echo.
C:\Users\goyos\.venvs\ai-policy-reviewer3\Scripts\python.exe -m scripts.seed_demo_data

echo.
echo ========================================
echo   Demo data seeding complete
echo ========================================
echo.
echo Next steps:
echo   1. Start services: start.bat
echo   2. API docs: http://localhost:8004/docs
echo   3. Frontend:  http://localhost:3033
echo.
pause
