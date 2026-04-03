@echo off
setlocal enabledelayedexpansion
title AI PDF Chatbot - Running
color 0B

echo.
echo  ============================================================
echo    AI PDF Chatbot - Startup Script v1.0
echo  ============================================================
echo.

REM Get the script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check venv folder exists (more reliable than checking .bat file)
if not exist "backend\venv" (
    echo  [ERROR] Virtual environment not found in backend\venv!
    echo  Please run setup.bat or setup-init.bat first.
    echo.
    pause & exit /b 1
)

REM Check node_modules exists
if not exist "frontend\node_modules" (
    echo  [ERROR] Frontend dependencies not found!
    echo  Please run:
    echo    cd frontend
    echo    npm install
    echo.
    pause & exit /b 1
)

REM Check .env exists
if not exist "backend\.env" (
    echo  [ERROR] backend\.env not found!
    echo  Please create backend\.env with your GROQ_API_KEY
    echo.
    pause & exit /b 1
)

REM Check if GROQ_API_KEY is set properly
for /f "tokens=2 delims==" %%A in ('findstr "GROQ_API_KEY=" backend\.env') do set GROQ_KEY=%%A
if "!GROQ_KEY!"=="" (
    echo  [WARNING] GROQ_API_KEY is empty in backend\.env
    echo  Get a free key at: https://console.groq.com/keys
    echo  Then edit backend\.env and set GROQ_API_KEY=gsk_xxxxx
    echo.
    echo  Continuing anyway... (will fail when chat is used)
    echo.
    timeout /t 2 /nobreak >nul
)


echo.
echo  [1/3] Starting Backend Server (Port 8000)
echo  ============================================================
echo  Backend: FastAPI with LangChain RAG
echo  Model:   llama-3.3-70b-versatile (Groq)
echo  Vector:  ChromaDB (local)
echo.
start "PDF Chatbot - Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload --port 8000"

echo  [2/3] Waiting for backend to initialize (3 seconds)...
timeout /t 3 /nobreak >nul

echo.
echo  [3/3] Starting Frontend Server (Port 5173)
echo  ============================================================
echo  Frontend: React/Vite with Tailwind CSS
echo  Auto-reload: Enabled
echo.
start "PDF Chatbot - Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 4 /nobreak >nul

echo.
echo  ============================================================
echo    ✓ Both servers are running!
echo  ============================================================
echo.
echo  🌐 App URL:        http://localhost:5173
echo  📚 API Docs:      http://localhost:8000/docs
echo  💚 Health Check:   http://localhost:8000/health
echo.
echo  ⚙️  Settings:
echo    - Max file size: 100MB per PDF
echo    - LLM model:    llama-3.3-70b-versatile
echo    - Vector DB:    ChromaDB (local, no setup required)
echo.
echo  🚀 Quick Start:
echo    1. Go to http://localhost:5173 in your browser
echo    2. Upload a PDF file (drag & drop)
echo    3. Wait for "Ready!" notification (1st upload takes time)
echo    4. Ask a question about the document
echo    5. Get AI-powered answers with page citations
echo.
echo  🛑 To Stop:
echo    Close both terminal windows OR press Ctrl+C in each
echo.
echo  ============================================================
echo.

REM Try to open browser automatically (with timeout to let servers start)
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo  Opening browser at http://localhost:5173...
echo.

pause
