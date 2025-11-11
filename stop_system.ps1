# Finance ERP System Shutdown Script
# Stops Django backend and Next.js frontend processes

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Finance ERP - System Shutdown" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[INFO] Stopping Django Backend Server..." -ForegroundColor Yellow

# Stop Django processes (Python running manage.py)
$djangoProcesses = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*manage.py*runserver*"
}

if ($djangoProcesses) {
    $djangoProcesses | Stop-Process -Force
    Write-Host "[SUCCESS] Stopped $($djangoProcesses.Count) Django process(es)" -ForegroundColor Green
} else {
    Write-Host "[INFO] No Django processes found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[INFO] Stopping Next.js Frontend Server..." -ForegroundColor Yellow

# Stop Next.js processes (Node running next dev)
$nextProcesses = Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*next*dev*"
}

if ($nextProcesses) {
    $nextProcesses | Stop-Process -Force
    Write-Host "[SUCCESS] Stopped $($nextProcesses.Count) Next.js process(es)" -ForegroundColor Green
} else {
    Write-Host "[INFO] No Next.js processes found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[SUCCESS] System shutdown complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
