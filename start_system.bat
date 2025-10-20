@echo off
echo ========================================
echo Finance ERP - Complete System Startup
echo ========================================
echo.
echo Starting both Backend and Frontend...
echo.
echo Backend will run on: http://localhost:8007
echo Frontend will run on: http://localhost:3000
echo.
echo Press Ctrl+C in either window to stop
echo ========================================
echo.

rem Start Django backend in a new window
start "Finance ERP - Django Backend" cmd /k "cd /d %~dp0 && .\venv\Scripts\python.exe manage.py runserver 8007"

rem Wait a moment for backend to start
timeout /t 3 /nobreak > nul

rem Start Next.js frontend in a new window
start "Finance ERP - Next.js Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Both servers are starting...
echo.
echo Django Backend: http://localhost:8007
echo Next.js Frontend: http://localhost:3000
echo.
echo Your browser should open automatically to: http://localhost:3000
echo.
timeout /t 5 /nobreak > nul

rem Open browser
start http://localhost:3000

echo.
echo System is running! Close the terminal windows to stop the servers.
echo.
pause
