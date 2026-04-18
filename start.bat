@echo off
setlocal enabledelayedexpansion
color 0B
title DocInsight - Startup

REM ==================== CONFIGURATION ====================
set BACKEND_PORT=8000
set FRONTEND_PORT=5173
set LOG_FILE=startup_log.txt

cd /d "%~dp0"

REM Clear old log
if exist "%LOG_FILE%" del "%LOG_FILE%" >nul 2>&1

REM ==================== DISPLAY BANNER ====================
cls
echo.
echo  ============================================================
echo    DocInsight - Professional Startup v2.1
echo  ============================================================
echo.
echo  [%date% %time%] Starting DocInsight services...
echo  [%date% %time%] Starting DocInsight services... >> "%LOG_FILE%"
echo.

REM ==================== PREREQUISITES VALIDATION ====================
echo  [STEP 1/5] Validating prerequisites...
echo  [STEP 1/5] Validating prerequisites... >> "%LOG_FILE%"

where python >nul 2>&1
if errorlevel 1 (
    echo  X ERROR: Python not found
    echo  X ERROR: Python not found >> "%LOG_FILE%"
    echo    Install from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
    echo  X ERROR: Node.js not found
    echo  X ERROR: Node.js not found >> "%LOG_FILE%"
    echo    Install from: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo  ✓ Python found
echo  ✓ Node.js found
echo.

REM ==================== PORT AVAILABILITY CHECK ====================
echo  [STEP 2/5] Checking port availability...

REM Only check for LISTENING state (ignore TIME_WAIT/CLOSE_WAIT)
netstat -ano | find /I "listening" | find ":%BACKEND_PORT% " >nul 2>&1
if not errorlevel 1 (
    echo  X ERROR: Port %BACKEND_PORT% in use
    echo.
    pause
    exit /b 1
)

netstat -ano | find /I "listening" | find ":%FRONTEND_PORT% " >nul 2>&1
if not errorlevel 1 (
    echo  X ERROR: Port %FRONTEND_PORT% in use
    echo.
    pause
    exit /b 1
)

echo  ✓ Port %BACKEND_PORT% available
echo  ✓ Port %FRONTEND_PORT% available
echo.

REM ==================== SETUP: Backend Environment ====================
echo  [STEP 3/5] Preparing backend environment...

if not exist "backend\venv" (
    echo    Creating Python virtual environment...
    cd backend
    python -m venv venv >>"..\%LOG_FILE%" 2>&1
    call venv\Scripts\activate.bat
    echo    Installing Python dependencies...
    pip install --quiet --upgrade pip setuptools wheel >>"..\%LOG_FILE%" 2>&1
    pip install -q -r requirements.txt >>"..\%LOG_FILE%" 2>&1
    cd ..
)

echo  ✓ Backend ready
echo.

REM ==================== SETUP: Frontend Environment ====================
echo  [STEP 4/5] Preparing frontend environment...

if not exist "frontend\node_modules" (
    echo    Installing Node.js dependencies...
    cd frontend
    call npm install --silent >>"..\%LOG_FILE%" 2>&1
    cd ..
)

echo  ✓ Frontend ready
echo.

REM ==================== SETUP: Configuration ====================
echo  [STEP 5/5] Checking configuration...

if not exist "backend\.env" (
    echo    Creating backend\.env file...
    (
        echo # DocInsight Environment Configuration
        echo # Get free GROQ_API_KEY: https://console.groq.com/keys
        echo GROQ_API_KEY=gsk_your_key_here
        echo GROQ_MODEL=llama-3.3-70b-versatile
        echo MAX_UPLOAD_SIZE_MB=100
    ) > backend\.env
    echo  ⚠ Edit backend\.env and add GROQ_API_KEY
)

echo  ✓ Configuration ready
echo.

REM ==================== STARTUP: SERVICES ====================
echo  ============================================================
echo    STARTING SERVICES...
echo  ============================================================
echo.

echo  [1/2] Starting Backend on port %BACKEND_PORT%
start "DocInsight Backend" cmd /k "cd /d backend && venv\Scripts\activate.bat && python -m uvicorn main:app --reload --port %BACKEND_PORT%"
timeout /t 5 /nobreak >nul

echo  [2/2] Starting Frontend on port %FRONTEND_PORT%
start "DocInsight Frontend" cmd /k "cd /d frontend && npm run dev"
timeout /t 8 /nobreak >nul

echo  ✓ Services started
echo.


REM ==================== SUCCESS MESSAGE ====================
echo  ============================================================
echo    ✓ ALL SYSTEMS READY!
echo  ============================================================
echo.
echo  🌐 Application:   http://localhost:%FRONTEND_PORT%
echo  📚 API Docs:      http://localhost:%BACKEND_PORT%/docs
echo  ✓ Health Check:   http://localhost:%BACKEND_PORT%/health
echo.
echo  Stack:
echo    - Backend: FastAPI + LangChain + ChromaDB
echo    - Frontend: React + Vite + Tailwind
echo    - Model: llama-3.3-70b-versatile (Groq)
echo.
echo  Usage:
echo    1. Upload PDF files
echo    2. Ask questions about documents
echo    3. Get AI-powered answers with citations
echo.
echo  Shutdown: Press Ctrl+C in terminal windows or run stop.bat
echo  Logs: %LOG_FILE%
echo.
echo  ============================================================
echo.

timeout /t 3 /nobreak >nul
start http://localhost:%FRONTEND_PORT%

echo  Opening browser...
echo.
pause
