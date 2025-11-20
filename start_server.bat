@echo off
REM Django ERP Finance Server Startup Script
REM Starts the Django development server on port 8007

echo Starting Django ERP Finance Server...
echo.

.\venv\Scripts\python.exe manage.py runserver 8007
