@echo off
TITLE SECurox — Next-Gen Smart City Cyber Operations Center (SOC)

echo.
echo   ==================================================================
echo     SECurox: Smart City Cyber Risk Detection ^& Operations Center
echo     SH-FIN-05 Target Implementation
echo   ==================================================================
echo.

REM Verify Python environment
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python not found on PATH. Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo [*] Python verified:
python --version

REM Set PYTHONPATH to resolve backend modules
set PYTHONPATH=%CD%\finance\backend;%CD%\finance;%PYTHONPATH%

echo [*] Setting up environment and verifying dependencies...
python -c "import fastapi, uvicorn, sklearn, pydantic; print('[*] Core dependencies verified.')" >nul 2>&1
IF ERRORLEVEL 1 (
    echo [*] Installing required Python packages...
    pip install -r finance\backend\requirements.txt
)

echo.
echo ==================================================================
echo   SECurox Smart City Operations Center Launching
echo ==================================================================
echo.
echo   Dashboard SOC:      http://localhost:8000
echo   API Documentation:  http://localhost:8000/docs
echo.
echo   Modes Available:
echo     - [ LIVE SOC ]
echo     - [ ATTACK SIMULATION LAB ] (Scenarios 01 to 06 + Custom Builder)
echo     - [ EXECUTIVE VIEW ] (CISO ^& Municipal Decision Cockpit)
echo     - [ ANALYST VIEW ] (Forensic Evidence ^& Incident Reports)
echo     - [ DATA ^& MODEL LAB ] (CIC-IDS-2017, UNSW-NB15, Replay Engine)
echo.
echo   Default Credentials: admin / admin123
echo.
echo   Press Ctrl+C to terminate the SOC gateway.
echo ==================================================================
echo.

REM Launch default browser after 3 seconds in background
start "" /b cmd /c "timeout /t 3 >nul && start http://localhost:8000"

REM Run Uvicorn server from finance/backend
cd finance\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
