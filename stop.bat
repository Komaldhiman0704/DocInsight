@echo off
title Stop PDF Chatbot Services
color 0C

echo.
echo  ============================================================
echo    Stopping PDF Chatbot Services
echo  ============================================================
echo.

echo  This will close the backend and frontend servers.
echo.
echo  Option 1: Manual Stop (Recommended)
echo    - Go to each terminal window
echo    - Press Ctrl+C
echo    - Press 'Y' to confirm
echo.
echo  Option 2: Force Close
echo    - Running taskkill now to force close servers...
echo.

REM Ask user if they want to continue
choice /C YN /M "Force close all servers? (Y/N)"
if errorlevel 2 goto end
if errorlevel 1 goto force_close

:force_close
echo.
echo  Killing Python (uvicorn) processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq PDF Chatbot*" >nul 2>&1

echo  Killing Node (npm) processes...
taskkill /F /IM node.exe >nul 2>&1

echo.
echo  ============================================================
echo    Services stopped!
echo  ============================================================
echo.
echo  To restart: run start.bat
echo.

pause
goto end

:end
