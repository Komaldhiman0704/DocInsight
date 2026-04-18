@echo off
setlocal enabledelayedexpansion
color 0C
title DocInsight - Shutdown

echo.
echo  ============================================================
echo    DocInsight - Professional Shutdown Script v2.0
echo  ============================================================
echo.
echo  This script will gracefully stop all DocInsight services.
echo.

REM Check if services are running
tasklist | find /I "python.exe" >nul 2>&1
set PYTHON_RUNNING=%errorlevel%

tasklist | find /I "node.exe" >nul 2>&1
set NODE_RUNNING=%errorlevel%

if %PYTHON_RUNNING% neq 0 if %NODE_RUNNING% neq 0 (
    echo  ℹ  No DocInsight services are currently running.
    echo.
    pause
    exit /b 0
)

echo  RUNNING SERVICES:
if %PYTHON_RUNNING% equ 0 echo    ✓ Backend (Python/Uvicorn)
if %NODE_RUNNING% equ 0 echo    ✓ Frontend (Node.js/Vite)
echo.

REM Ask for confirmation
choice /C GQ /M "Gracefully stop services? [G=Graceful, Q=Quit]"
if errorlevel 2 (
    echo.
    echo  Shutdown cancelled.
    echo.
    pause
    exit /b 0
)

echo.
echo  ============================================================
echo    STOPPING SERVICES...
echo  ============================================================
echo.

REM Gracefully stop backend
if %PYTHON_RUNNING% equ 0 (
    echo  [1/2] Stopping backend server...
    REM Try graceful shutdown first
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq DocInsight*" >nul 2>&1
    if errorlevel 1 (
        echo    ✗ Backend stop warning
    ) else (
        echo    ✓ Backend stopped
    )
    timeout /t 2 /nobreak >nul
)

REM Gracefully stop frontend
if %NODE_RUNNING% equ 0 (
    echo  [2/2] Stopping frontend server...
    taskkill /F /IM node.exe >nul 2>&1
    if errorlevel 1 (
        echo    ✗ Frontend stop warning
    ) else (
        echo    ✓ Frontend stopped
    )
)

echo.
echo  ============================================================
echo    ✓ ALL SERVICES STOPPED
echo  ============================================================
echo.
echo  Information:
echo    - To start services: run start.bat
echo    - To view logs: open startup_log.txt
echo.

pause
