# Finance ERP System Startup Script
# Starts both Django backend and Next.js frontend

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Finance ERP - System Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get Python executable path
$pythonExe = "C:/Users/samys/AppData/Local/Programs/Python/Python311/python.exe"

# Check if Python exists
if (-not (Test-Path $pythonExe)) {
    Write-Host "[ERROR] Python not found at $pythonExe" -ForegroundColor Red
    Write-Host "Please update the path in this script or use 'python' if it's in PATH" -ForegroundColor Yellow
    $pythonExe = "python"
}

Write-Host "[INFO] Starting Django Backend Server..." -ForegroundColor Green
Write-Host "       Backend will be available at: http://localhost:8007" -ForegroundColor Yellow
Write-Host ""

# Start Django in a new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; Write-Host 'Django Backend Server' -ForegroundColor Cyan; & '$pythonExe' manage.py runserver 8007"

Start-Sleep -Seconds 2

Write-Host "[INFO] Starting Next.js Frontend Server..." -ForegroundColor Green
Write-Host "       Frontend will be available at: http://localhost:3000 or http://localhost:3001" -ForegroundColor Yellow
Write-Host ""

# Start Next.js in a new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; Write-Host 'Next.js Frontend Server' -ForegroundColor Cyan; npm run dev"

Write-Host ""
Write-Host "[SUCCESS] System startup initiated!" -ForegroundColor Green
Write-Host ""
Write-Host "Two new windows have been opened:" -ForegroundColor Cyan
Write-Host "  1. Django Backend  - http://localhost:8007" -ForegroundColor White
Write-Host "  2. Next.js Frontend - http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
