@echo off
setlocal enabledelayedexpansion
title AI PDF Chatbot - Setup
color 0A

echo.
echo  ============================================================
echo    AI PDF Chatbot - Windows Setup
echo    This will install all dependencies (takes 3-5 minutes)
echo  ============================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found!
    echo  Install Python 3.11+ from https://python.org
    echo  Check "Add Python to PATH" during install!
    pause & exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo  [OK] %%i

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Node.js not found!
    echo  Install Node.js 18+ from https://nodejs.org
    pause & exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do echo  [OK] Node.js %%i

echo.
echo  [1/4] Creating Python virtual environment...
cd backend
python -m venv venv
call venv\Scripts\activate.bat

echo  [2/4] Installing Python packages (2-3 min)...
python -m pip install --upgrade pip -q
pip install -r requirements.txt
if %errorlevel% neq 0 (echo [ERROR] pip install failed & pause & exit /b 1)
echo  [OK] Python packages ready

echo  [3/4] Creating folders...
if not exist uploads mkdir uploads
if not exist chroma_db mkdir chroma_db
echo  [OK] Folders created

echo  [4/4] Installing frontend packages (1-2 min)...
cd ..\frontend
npm install
if %errorlevel% neq 0 (echo [ERROR] npm install failed & pause & exit /b 1)
cd ..

echo.
echo  ============================================================
echo    SETUP COMPLETE!
echo    Next: Edit backend\.env and add your GROQ_API_KEY
echo    Get free key: https://console.groq.com/keys
echo    Then run: start.bat
echo  ============================================================
echo.
pause
