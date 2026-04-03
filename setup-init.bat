@echo off
title PDF Chatbot Setup
color 0A

echo.
echo  ============================================================
echo    PDF Chatbot - First Time Setup
echo  ============================================================
echo.

setlocal enabledelayedexpansion

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found!
    echo  Download from: https://www.python.org/downloads
    echo  Make sure to check "Add Python to PATH" during install
    echo.
    pause & exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js not found!
    echo  Download from: https://nodejs.org (LTS version)
    echo.
    pause & exit /b 1
)

echo  ✓ Python found: 
for /f "tokens=*" %%A in ('python --version') do echo     %%A
echo.

echo  ✓ Node.js found:
for /f "tokens=*" %%A in ('node --version') do echo     %%A
echo.

echo  ✓ npm found:
for /f "tokens=*" %%A in ('npm --version') do echo     %%A
echo.

REM Setup Backend
echo  ============================================================
echo  Setting up Backend...
echo  ============================================================
echo.

if exist backend\venv (
    echo  Virtual environment already exists. Skipping...
) else (
    echo  Creating Python virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
    echo.
    echo  Upgrading pip...
    python -m pip install --upgrade pip
    echo.
    echo  Installing Python dependencies...
    pip install -r requirements.txt
    cd ..
)

echo.
echo  ============================================================
echo  Setting up Frontend...
echo  ============================================================
echo.

if exist frontend\node_modules (
    echo  Node modules already exist. Skipping...
) else (
    echo  Installing npm packages...
    cd frontend
    npm install
    cd ..
)

echo.
echo  ============================================================
echo  ✓ Setup Complete!
echo  ============================================================
echo.
echo  Next steps:
echo    1. Open backend\.env
echo    2. Get a Groq API key: https://console.groq.com/keys
echo    3. Set GROQ_API_KEY=gsk_your_key_here
echo    4. Run: start.bat
echo.
echo  Or run "start.bat" now if API key is already set
echo.

pause
