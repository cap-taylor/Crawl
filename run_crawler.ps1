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
Write-Host "[디버깅 콘솔] GUI가 비정상 종료되면 여기에 오류가 표시됩니다." -ForegroundColor Yellow
Write-Host ""

# 프로젝트 디렉토리로 이동
$projectPath = "D:\MyProjects\Crawl"
if ($PWD.Path -ne $projectPath) {
    Set-Location $projectPath
}

Write-Host "GUI를 시작합니다..." -ForegroundColor Green
Write-Host ""

# GUI 실행 (오류도 모두 출력)
wsl bash -c "cd /mnt/d/MyProjects/Crawl && export PYTHONIOENCODING=utf-8 && export LANG=ko_KR.UTF-8 && python3 main.py 2>&1"

# GUI가 종료된 후
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "GUI가 종료되었습니다." -ForegroundColor Yellow
Write-Host "오류가 있었다면 위에 표시됩니다." -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")