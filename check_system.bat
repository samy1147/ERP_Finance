@echo off
echo ========================================
echo Finance ERP - System Check
echo ========================================
echo.

echo Checking prerequisites...
echo.

rem Check Python
echo [1/4] Checking Python...
python --version 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    echo.
) else (
    echo [OK] Python is installed
    echo.
)

rem Check pip
echo [2/4] Checking pip...
pip --version 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] pip is not installed
    echo.
) else (
    echo [OK] pip is installed
    echo.
)

rem Check Node.js
echo [3/4] Checking Node.js...
node --version 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    echo.
) else (
    echo [OK] Node.js is installed
    echo.
)

rem Check npm
echo [4/4] Checking npm...
npm --version 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed
    echo.
) else (
    echo [OK] npm is installed
    echo.
)

echo ========================================
echo Checking project structure...
echo ========================================
echo.

rem Check if key files exist
if exist "manage.py" (
    echo [OK] Django project found
) else (
    echo [ERROR] manage.py not found - are you in the project root?
)

if exist "frontend\package.json" (
    echo [OK] Frontend project found
) else (
    echo [ERROR] frontend/package.json not found
)

if exist "db.sqlite3" (
    echo [OK] Database file exists
) else (
    echo [WARNING] Database not found - run: python manage.py migrate
)

if exist "frontend\node_modules" (
    echo [OK] Frontend dependencies installed
) else (
    echo [WARNING] Frontend dependencies not installed - run: cd frontend && npm install
)

echo.
echo ========================================
echo Checking ports...
echo ========================================
echo.

rem Check if ports are available
netstat -ano | findstr :8000 >nul
if %errorlevel% equ 0 (
    echo [WARNING] Port 8000 is in use - Django backend may not start
) else (
    echo [OK] Port 8000 is available
)

netstat -ano | findstr :3000 >nul
if %errorlevel% equ 0 (
    echo [WARNING] Port 3000 is in use - Next.js frontend may not start
) else (
    echo [OK] Port 3000 is available
)

echo.
echo ========================================
echo Summary
echo ========================================
echo.
echo If all checks passed, you can start the system with:
echo   start_system.bat
echo.
echo If there were errors:
echo   1. Install missing prerequisites (Python, Node.js)
echo   2. Run: pip install -r requirements.txt
echo   3. Run: python manage.py migrate
echo   4. Run: cd frontend && npm install
echo   5. Try again!
echo.
echo For detailed setup instructions, see: SETUP_GUIDE.md
echo For quick start, see: QUICK_START.md
echo.
pause
