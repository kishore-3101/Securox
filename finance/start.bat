@echo off
TITLE Securox — Cyber Risk Intelligence Platform

echo.
echo   ███████╗███████╗██████╗ ██╗   ██╗██████╗ ██████╗ ██╗  ██╗
echo   ██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██╔═══██╗╚██╗██╔╝
echo   ███████╗█████╗  ██║     ██║   ██║██████╔╝██║   ██║ ╚███╔╝
echo   ╚════██║██╔══╝  ██║     ██║   ██║██╔══██╗██║   ██║ ██╔██╗
echo   ███████║███████╗╚██████╗╚██████╔╝██║  ██║╚██████╔╝██╔╝ ██╗
echo   ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
echo.
echo   Autonomous Cyber Risk Intelligence Platform for Smart Cities
echo   ---------------------------------------------------------------
echo.

REM Check Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: Python not found. Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

REM Create venv if needed
IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install --quiet --upgrade pip
pip install --quiet -r backend\requirements.txt

echo.
echo ============================================================
echo   Securox Starting...
echo ============================================================
echo.
echo   Dashboard:  http://localhost:8000
echo   API Docs:   http://localhost:8000/docs
echo.
echo   Demo login: admin / admin123
echo.
echo   Press Ctrl+C to stop.
echo.

cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info

pause
