# 네이버 쇼핑 크롤러 실행 스크립트 (터미널 버전)
# PowerShell 7에서 WSL을 통해 Python 실행

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   네이버 쇼핑 크롤러 v1.0 (터미널 모드)" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# WSL 경로 설정
$wslPath = "/mnt/d/MyProjects/Crawl"

# 프로젝트 디렉토리로 이동
Set-Location "D:\MyProjects\Crawl"

Write-Host "크롤러를 시작합니다..." -ForegroundColor Yellow
Write-Host "GUI가 실행되지 않으면 터미널 버전이 실행됩니다." -ForegroundColor Yellow
Write-Host ""

# WSL에서 Python 크롤러 실행
wsl bash -c "cd $wslPath && python3 main.py 2>/dev/null || python3 terminal_crawler.py"

# 종료 시 대기
Write-Host ""
Write-Host "프로그램이 종료되었습니다." -ForegroundColor Yellow
Write-Host "이 창을 닫으려면 아무 키나 누르세요..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")