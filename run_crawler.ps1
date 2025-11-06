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
Write-Host "[DEBUG MODE] Terminal shows only errors" -ForegroundColor Yellow
Write-Host "  - GUI crash errors will appear below" -ForegroundColor Gray
Write-Host "  - All crawler logs are in the GUI window" -ForegroundColor Gray
Write-Host "  - Log file: gui_debug.log" -ForegroundColor Gray
Write-Host ""

# 경로 설정 (WSL 경로 사용)
# PowerShell에서 WSL 경로로 직접 실행되므로 경로 변경 불필요

# Python 캐시 자동 삭제 (최신 코드 실행 보장)
Write-Host "Cleaning Python cache..." -ForegroundColor Yellow
wsl bash -c "cd /home/dino/MyProjects/Crawl && find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true && find . -name '*.pyc' -delete 2>/dev/null || true" 2>$null
Write-Host "  [OK] Cache cleaned" -ForegroundColor Green
Write-Host ""

Write-Host "Starting GUI..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# GUI 실행 (stderr만 캡처, stdout은 숨김)
try {
    wsl bash -c "cd /home/dino/MyProjects/Crawl && export DISPLAY=:0 && export PYTHONIOENCODING=utf-8 && export LANG=ko_KR.UTF-8 && python3 product_collector_gui.py 2>&1 > /dev/null"

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
    Write-Host "You can now select and copy text with your mouse." -ForegroundColor Green
    Write-Host "Press ENTER to close this window..." -ForegroundColor Gray
    Read-Host
}