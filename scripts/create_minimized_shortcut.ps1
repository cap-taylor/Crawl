# PowerShell 바로가기 생성 스크립트 (최소화 실행)

$shortcutPath = "$env:USERPROFILE\Desktop\네이버 쇼핑 크롤러 (최소화).lnk"
$targetPath = "pwsh.exe"
$arguments = "-WindowStyle Minimized -ExecutionPolicy Bypass -File `"D:\MyProjects\Crawl\run_crawler.ps1`""

# WScript.Shell COM 객체 생성
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)

# 바로가기 속성 설정
$shortcut.TargetPath = $targetPath
$shortcut.Arguments = $arguments
$shortcut.WorkingDirectory = "D:\MyProjects\Crawl"
$shortcut.WindowStyle = 7  # 7 = 최소화 실행
$shortcut.IconLocation = "powershell.exe,0"
$shortcut.Description = "네이버 쇼핑 크롤러 (자동 최소화)"

# 바로가기 저장
$shortcut.Save()

Write-Host "✅ 바로가기가 생성되었습니다: $shortcutPath" -ForegroundColor Green
Write-Host ""
Write-Host "이 바로가기를 실행하면:" -ForegroundColor Yellow
Write-Host "1. PowerShell이 최소화 상태로 시작됩니다" -ForegroundColor White
Write-Host "2. GUI가 자동으로 실행됩니다" -ForegroundColor White
Write-Host "3. 오류가 발생해도 창이 닫히지 않습니다" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")