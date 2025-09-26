# Create desktop shortcut script

$desktopPath = [Environment]::GetFolderPath("Desktop")

# Create batch file for easier execution
$batchContent = @"
@echo off
title Naver Shopping Crawler
color 0A
echo ================================================
echo    Naver Shopping Crawler v1.0
echo ================================================
echo.
cd /d D:\MyProjects\Crawl
echo Starting crawler...
echo.
wsl bash -c "cd /mnt/d/MyProjects/Crawl && python3 main.py 2>/dev/null || python3 src/core/terminal_crawler.py"
echo.
echo Press any key to exit...
pause > nul
"@

$batchPath = Join-Path $desktopPath "Naver_Shopping_Crawler.bat"
Set-Content -Path $batchPath -Value $batchContent -Encoding ASCII

Write-Host "Desktop shortcut created successfully!" -ForegroundColor Green
Write-Host "Location: $batchPath" -ForegroundColor Yellow

# Also create PowerShell 7 version
$ps7Content = @"
# Naver Shopping Crawler Launcher
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Naver Shopping Crawler v1.0" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "D:\MyProjects\Crawl"
wsl bash -c "cd /mnt/d/MyProjects/Crawl && python3 main.py 2>/dev/null || python3 src/core/terminal_crawler.py"

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
`$null = `$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
"@

$ps7Path = Join-Path $desktopPath "Naver_Crawler_PS7.ps1"
Set-Content -Path $ps7Path -Value $ps7Content -Encoding UTF8

Write-Host "PowerShell 7 version also created: $ps7Path" -ForegroundColor Yellow