@echo off
echo ========================================
echo   AI Policy Reviewer - Initial Setup
echo ========================================
echo.

cd /d "%~dp0"

REM Create data directories
echo [1/6] Creating data directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
echo       Done

REM Backend setup
echo.
echo [2/6] Creating backend virtual environment...
cd backend
if not exist "venv" (
    python -m venv venv
    echo       Created virtual environment
) else (
    echo       Virtual environment already exists
)

echo.
echo [3/6] Installing backend dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
echo       Done

echo.
echo [4/6] Initializing database...
python -c "from app.db.init_db import create_tables; create_tables()"
echo       Done

echo.
echo [5/6] Seeding initial data...
python -m app.db.seed_data
echo       Done

cd ..

REM Frontend setup
echo.
echo [6/6] Installing frontend dependencies...
cd frontend
call npm install --silent
echo       Done

cd ..

echo.
echo ========================================
echo   Setup Complete
echo ========================================
echo.
echo Next steps:
echo   1. Set Azure credentials in .env
echo   2. Run start.bat to launch services
echo.
echo Startup scripts:
echo   start.bat          - Start all services (recommended)
echo   start_backend.bat  - Backend only
echo   start_frontend.bat - Frontend only
echo.
pause
