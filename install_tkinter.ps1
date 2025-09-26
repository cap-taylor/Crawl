# PowerShell 스크립트 - tkinter 설치
Write-Host "======================================"
Write-Host "  tkinter 자동 설치 스크립트"
Write-Host "======================================"
Write-Host ""

# WSL 실행 확인
$wslStatus = wsl --list --running
if ($wslStatus -notmatch "Ubuntu") {
    Write-Host "WSL을 시작합니다..." -ForegroundColor Yellow
    wsl -d Ubuntu -e echo "WSL Started"
}

# tkinter 설치 실행
Write-Host "tkinter(python3-tk)를 설치합니다..." -ForegroundColor Green
Write-Host "시스템 비밀번호를 입력해주세요:" -ForegroundColor Yellow
Write-Host ""

# WSL에서 설치 스크립트 실행
wsl -d Ubuntu bash /mnt/d/MyProjects/Crawl/scripts/install_tkinter.sh

Write-Host ""
Write-Host "설치가 완료되었습니다!" -ForegroundColor Green
Write-Host "이제 크롤러를 다시 실행할 수 있습니다." -ForegroundColor Cyan
Write-Host ""
Write-Host "Enter 키를 눌러서 종료하세요..."
Read-Host