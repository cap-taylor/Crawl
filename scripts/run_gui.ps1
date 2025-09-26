# 네이버 쇼핑 크롤러 실행 스크립트
# PowerShell 7에서 WSL을 통해 Python 실행

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   네이버 쇼핑 크롤러 v1.0 " -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# WSL 경로 설정
$wslPath = "/mnt/d/MyProjects/Crawl"

# WSL에서 Python 크롤러 실행
Write-Host "크롤러를 시작합니다..." -ForegroundColor Yellow
Write-Host ""

# Display를 설정하여 WSL에서 GUI 실행 가능하도록 함
$env:DISPLAY = "localhost:0"

# WSL 명령 실행
wsl bash -c "cd $wslPath && export DISPLAY=:0 && python3 main.py"

# 종료 시 대기
Write-Host ""
Write-Host "프로그램이 종료되었습니다." -ForegroundColor Yellow
Write-Host "이 창을 닫으려면 아무 키나 누르세요..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")