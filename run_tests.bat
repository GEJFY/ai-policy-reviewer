@echo off
echo ========================================
echo   AI Policy Reviewer - Run Tests
echo ========================================
echo.

cd /d C:\dev-pr\backend

echo [1/2] Running tests...
C:\Users\goyos\.venvs\ai-policy-reviewer3\Scripts\python.exe -m pytest tests/ -v --tb=short

echo.
echo [2/2] Running tests with coverage...
C:\Users\goyos\.venvs\ai-policy-reviewer3\Scripts\python.exe -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

echo.
echo ========================================
echo   Tests Complete
echo ========================================
echo.
echo Coverage report: backend\htmlcov\index.html
echo.
pause
