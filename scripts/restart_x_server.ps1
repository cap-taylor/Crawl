# X Server (VcXsrv) Restart Script
# WSL GUI not showing - Run this to fix

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   X Server Restart Utility" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Kill VcXsrv
Write-Host "[1/3] Stopping VcXsrv..." -ForegroundColor Yellow
taskkill /IM vcxsrv.exe /F 2>$null
if ($?) {
    Write-Host "VcXsrv stopped successfully." -ForegroundColor Green
} else {
    Write-Host "VcXsrv was not running or already stopped." -ForegroundColor Gray
}

Start-Sleep -Seconds 2

# 2. Find and start VcXsrv
Write-Host ""
Write-Host "[2/3] Starting VcXsrv..." -ForegroundColor Yellow

$vcxsrvPaths = @(
    "C:\Program Files\VcXsrv\vcxsrv.exe",
    "C:\Program Files (x86)\VcXsrv\vcxsrv.exe"
)

$found = $false
foreach ($path in $vcxsrvPaths) {
    if (Test-Path $path) {
        Write-Host "Found: $path" -ForegroundColor Green
        Start-Process $path -ArgumentList ":0 -multiwindow -clipboard -wgl -ac" -WindowStyle Hidden
        $found = $true
        break
    }
}

if (-not $found) {
    Write-Host "VcXsrv not found in standard locations." -ForegroundColor Red
    Write-Host "Please start VcXsrv manually from Start Menu." -ForegroundColor Yellow
} else {
    Write-Host "VcXsrv started successfully." -ForegroundColor Green
}

Start-Sleep -Seconds 2

# 3. Verify
Write-Host ""
Write-Host "[3/3] Verifying..." -ForegroundColor Yellow
$process = Get-Process vcxsrv -ErrorAction SilentlyContinue
if ($process) {
    Write-Host "VcXsrv is running (PID: $($process.Id))" -ForegroundColor Green
} else {
    Write-Host "VcXsrv verification failed." -ForegroundColor Red
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Done! You can now run the crawler GUI." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to close..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
