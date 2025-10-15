# Naver Shopping Crawler Launcher
# 콘솔창은 디버깅용으로만 사용 (GUI 비정상 종료 시 오류 확인)

# 에러가 발생해도 스크립트 계속 실행
$ErrorActionPreference = "Continue"

# 버전 파일 읽기
$versionFile = "$PSScriptRoot\VERSION"
if (Test-Path $versionFile) {
    $version = Get-Content $versionFile -Raw | ForEach-Object { $_.Trim() }
} else {
    $version = "1.0.0"
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Naver Shopping Crawler v$version" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[DEBUG] Error messages will appear here if GUI crashes." -ForegroundColor Yellow
Write-Host ""

# Move to project directory
$projectPath = "D:\MyProjects\Crawl"
if ($PWD.Path -ne $projectPath) {
    Set-Location $projectPath
}

Write-Host "Starting GUI..." -ForegroundColor Green
Write-Host ""

# GUI 실행 (오류 캡처)
try {
    wsl bash -c "cd /home/dino/MyProjects/Crawl && export DISPLAY=:0 && export PYTHONIOENCODING=utf-8 && export LANG=ko_KR.UTF-8 && python3 product_collector_gui.py 2>&1"

    # Normal exit
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "GUI closed normally." -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Cyan
}
catch {
    # Error exit
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Red
    Write-Host "ERROR: GUI crashed!" -ForegroundColor Red
    Write-Host "================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error details:" -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
}
finally {
    # Always show this and wait
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "DEBUG CONSOLE - Check error messages above" -ForegroundColor Yellow
    Write-Host "This window will stay open for debugging." -ForegroundColor Yellow
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press any key to close this window..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}