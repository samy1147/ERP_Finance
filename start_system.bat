@echo off
REM Finance ERP System Startup Script
REM Starts both Django backend and Next.js frontend

echo ========================================
echo Finance ERP - System Startup
echo ========================================
echo.

set PYTHON_EXE=C:/Users/samys/AppData/Local/Programs/Python/Python311/python.exe

echo [INFO] Starting Django Backend Server...
echo        Backend will be available at: http://localhost:8007
echo.

REM Start Django in a new window
start "Django Backend" cmd /k "cd /d %CD% && %PYTHON_EXE% manage.py runserver 8007"

timeout /t 2 /nobreak >nul

echo [INFO] Starting Next.js Frontend Server...
echo        Frontend will be available at: http://localhost:3000 or http://localhost:3001
echo.

REM Start Next.js in a new window
start "Next.js Frontend" cmd /k "cd /d %CD%\frontend && npm run dev"

echo.
echo [SUCCESS] System startup initiated!
echo.
echo Two new windows have been opened:
echo   1. Django Backend  - http://localhost:8007
echo   2. Next.js Frontend - http://localhost:3000
echo.
echo You can close this window now.
echo.
pause
