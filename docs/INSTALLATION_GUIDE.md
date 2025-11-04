# 네이버 쇼핑 크롤러 설치 가이드
> Windows 10 Home 환경 기준 (SSD 500GB, RAM 4GB)
>
> 최종 업데이트: 2025-11-04

---

## 📋 목차
1. [시스템 요구사항](#1-시스템-요구사항)
2. [WSL2 + Ubuntu 설치](#2-wsl2--ubuntu-설치)
3. [VS Code + Claude Code 설치](#3-vs-code--claude-code-설치)
4. [SuperClaude 프레임워크 설치](#4-superclaude-프레임워크-설치)
5. [프로젝트 환경 구성](#5-프로젝트-환경-구성)
6. [PostgreSQL 데이터베이스 설정](#6-postgresql-데이터베이스-설정)
7. [Python 패키지 설치](#7-python-패키지-설치)
8. [GUI 실행 바로가기 생성](#8-gui-실행-바로가기-생성)
9. [설치 검증](#9-설치-검증)
10. [문제 해결](#10-문제-해결)

---

## 1. 시스템 요구사항

### 최소 사양
- **OS**: Windows 10 Home (64-bit, 버전 1903 이상)
- **CPU**: 듀얼 코어 이상
- **RAM**: 4GB (8GB 권장)
- **저장공간**: 20GB 여유 공간
- **인터넷**: 안정적인 연결 필요

### 확인 방법
1. `Windows 키 + R` → `winver` 입력 → 버전 확인
2. Windows 버전이 1903 미만이면 Windows 업데이트 필요

---

## 2. WSL2 + Ubuntu 설치

### 2.1 Windows 기능 활성화

**PowerShell 관리자 권한으로 실행:**
1. `Windows 키` 클릭 → "PowerShell" 검색
2. 우클릭 → "관리자 권한으로 실행"
3. 아래 명령어 실행:

```powershell
# WSL 기능 활성화
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Virtual Machine 기능 활성화
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

4. **컴퓨터 재부팅** (필수!)

### 2.2 WSL2 Linux 커널 업데이트

**재부팅 후 PowerShell 관리자 권한으로 실행:**

1. WSL2 커널 다운로드:
   - **다운로드 URL**: https://aka.ms/wsl2kernel
   - 파일명: `wsl_update_x64.msi`
   - 다운로드 후 설치 진행

2. WSL2를 기본 버전으로 설정:
```powershell
wsl --set-default-version 2
```

### 2.3 Ubuntu 22.04 설치

**Microsoft Store 사용:**

1. **Microsoft Store 실행**
   - `Windows 키` → "Microsoft Store" 검색

2. **Ubuntu 22.04 LTS 검색 및 설치**
   - Store 검색창에 "Ubuntu 22.04" 입력
   - **다운로드 URL**: https://apps.microsoft.com/detail/9pn20msr04dw
   - "설치" 버튼 클릭 (약 500MB, 5-10분 소요)

3. **Ubuntu 초기 설정**
   - 설치 완료 후 "실행" 클릭
   - 사용자 이름 입력 (예: `dino`)
   - 비밀번호 입력 (2번 입력, 화면에 표시 안됨)
   - 완료 메시지: "Installation successful!"

4. **WSL 버전 확인**
```powershell
# PowerShell에서 실행
wsl --list --verbose
```
출력 예시:
```
  NAME            STATE           VERSION
* Ubuntu-22.04    Running         2
```
VERSION이 2여야 정상!

### 2.4 Ubuntu 업데이트

**Ubuntu 터미널에서 실행:**
```bash
sudo apt update
sudo apt upgrade -y
```
비밀번호 입력 후 5-10분 대기

---

## 3. VS Code + Claude Code 설치

### 3.1 VS Code 설치

1. **다운로드 URL**: https://code.visualstudio.com/download
2. "Windows" 버전 다운로드 (약 90MB)
3. 설치 파일 실행:
   - ✅ "Add to PATH" 체크
   - ✅ "Create a desktop icon" 체크
   - 설치 완료 (약 300MB)

### 3.2 WSL 확장 설치

**VS Code 실행 후:**

1. 좌측 Extensions 아이콘 클릭 (또는 `Ctrl+Shift+X`)
2. "WSL" 검색
3. **WSL (Microsoft 제작)** 설치
   - **확장 URL**: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl

### 3.3 Claude Code 설치

**방법 1: Extensions에서 직접 설치**
1. VS Code Extensions에서 "Claude Code" 검색
2. **Claude Code (Anthropic)** 설치
   - **확장 URL**: https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code

**방법 2: 명령어로 설치**
```bash
# PowerShell에서 실행
code --install-extension anthropic.claude-code
```

### 3.4 Claude Code API 키 설정

1. Anthropic API 키 발급:
   - **URL**: https://console.anthropic.com/
   - 회원가입 후 "API Keys" → "Create Key"
   - API 키 복사 (예: `sk-ant-api03-...`)

2. VS Code에서 설정:
   - `Ctrl+Shift+P` → "Claude Code: Set API Key" 입력
   - 복사한 API 키 붙여넣기

---

## 4. SuperClaude 프레임워크 설치

### 4.1 WSL Ubuntu에서 작업

**VS Code에서 WSL 연결:**
1. `Ctrl+Shift+P` → "WSL: Connect to WSL" 선택
2. 새 VS Code 창이 WSL 환경으로 열림

### 4.2 SuperClaude 설치

**Ubuntu 터미널에서 실행:**

```bash
# 홈 디렉토리로 이동
cd ~

# .claude 디렉토리 생성
mkdir -p .claude

# SuperClaude 파일 다운로드 (Git 필요 시 설치)
sudo apt install -y git

# SuperClaude GitHub 저장소 클론
git clone https://github.com/cyanheads/super-claude.git temp-superclaude

# SuperClaude 파일 복사
cp -r temp-superclaude/.claude/* ~/.claude/

# 임시 폴더 삭제
rm -rf temp-superclaude
```

**설치 확인:**
```bash
ls -la ~/.claude/
```
출력 예시:
```
BUSINESS_PANEL_EXAMPLES.md
BUSINESS_SYMBOLS.md
FLAGS.md
PRINCIPLES.md
RULES.md
MODE_Brainstorming.md
MODE_Business_Panel.md
...
```

---

## 5. 프로젝트 환경 구성

### 5.1 프로젝트 디렉토리 생성

```bash
# 프로젝트 폴더 생성
mkdir -p ~/MyProjects/Crawl
cd ~/MyProjects/Crawl
```

### 5.2 필수 시스템 패키지 설치

```bash
# Python 3.10+ 설치
sudo apt install -y python3 python3-pip python3-venv

# PostgreSQL 클라이언트 설치
sudo apt install -y postgresql-client libpq-dev

# Playwright 의존성 설치
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0

# X11 디스플레이 서버 (GUI 필요)
sudo apt install -y x11-apps
```

### 5.3 Python 버전 확인

```bash
python3 --version
```
출력: `Python 3.10.x` 이상이어야 함

---

## 6. PostgreSQL 데이터베이스 설정

### 6.1 PostgreSQL 설치

```bash
# PostgreSQL 서버 설치
sudo apt install -y postgresql postgresql-contrib

# PostgreSQL 서비스 시작
sudo service postgresql start

# 부팅 시 자동 시작 (선택사항)
sudo update-rc.d postgresql enable
```

### 6.2 데이터베이스 및 사용자 생성

```bash
# postgres 사용자로 전환
sudo -u postgres psql

# PostgreSQL 콘솔에서 실행 (아래 명령어들):
```

```sql
-- 데이터베이스 생성
CREATE DATABASE naver;

-- 사용자 비밀번호 설정
ALTER USER postgres WITH PASSWORD 'your_secure_password';

-- 권한 부여
GRANT ALL PRIVILEGES ON DATABASE naver TO postgres;

-- 종료
\q
```

**중요**: `your_secure_password`를 강력한 비밀번호로 변경하세요!

### 6.3 데이터베이스 테이블 생성

**프로젝트 폴더에 스키마 파일 생성:**

```bash
# database 폴더 생성
mkdir -p ~/MyProjects/Crawl/database

# 스키마 파일 생성
cat > ~/MyProjects/Crawl/database/create_tables.sql << 'EOF'
-- 카테고리 테이블
CREATE TABLE IF NOT EXISTS categories (
    category_name VARCHAR(100) PRIMARY KEY,
    category_id VARCHAR(20),
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 상품 테이블 (13개 필드)
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(255) PRIMARY KEY,
    category_name VARCHAR(100),
    product_name TEXT NOT NULL,
    search_tags TEXT[],
    price INTEGER,
    rating DECIMAL(2,1),
    product_url TEXT,
    thumbnail_url TEXT,
    brand_name VARCHAR(100),
    discount_rate INTEGER,
    review_count INTEGER,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 크롤링 히스토리 테이블
CREATE TABLE IF NOT EXISTS crawl_history (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100),
    products_count INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(50)
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_name);
CREATE INDEX IF NOT EXISTS idx_products_crawled_at ON products(crawled_at);
CREATE INDEX IF NOT EXISTS idx_crawl_history_category ON crawl_history(category_name);
EOF
```

**테이블 생성 실행:**
```bash
psql -U postgres -d naver -f ~/MyProjects/Crawl/database/create_tables.sql
```
비밀번호 입력 후 완료!

---

## 7. Python 패키지 설치

### 7.1 requirements.txt 파일 생성

```bash
cd ~/MyProjects/Crawl

cat > requirements.txt << 'EOF'
# GUI Framework
customtkinter==5.1.3
Pillow==10.1.0

# Web Scraping
playwright==1.40.0
beautifulsoup4==4.12.2

# Database
psycopg2-binary==2.9.9

# Utilities
python-dotenv==1.0.0
asyncio==3.4.3

# Data Processing
pandas==2.1.4
openpyxl==3.1.2
EOF
```

### 7.2 패키지 설치

```bash
# pip 업그레이드
python3 -m pip install --upgrade pip

# requirements.txt로 일괄 설치
pip3 install -r requirements.txt

# Playwright 브라우저 설치 (Chromium)
playwright install chromium
playwright install-deps
```

설치 시간: 약 5-10분 소요

---

## 8. GUI 실행 바로가기 생성

### 8.1 프로젝트 파일 구조 생성

```bash
cd ~/MyProjects/Crawl

# 필수 디렉토리 생성
mkdir -p src/core
mkdir -p tests
mkdir -p database
mkdir -p exports
mkdir -p docs
mkdir -p scripts
```

### 8.2 환경 변수 파일 생성

```bash
cat > .env << 'EOF'
# PostgreSQL 데이터베이스 설정
DB_HOST=localhost
DB_PORT=5432
DB_NAME=naver
DB_USER=postgres
DB_PASSWORD=your_secure_password

# 크롤링 설정
HEADLESS=false
TIMEOUT=30000
EOF
```

**중요**: `DB_PASSWORD`를 실제 설정한 비밀번호로 변경!

### 8.3 PowerShell 실행 스크립트 생성

```bash
cat > run_crawler.ps1 << 'EOF'
# Naver Shopping Crawler Launcher

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
    Write-Host "Press any key to close this window..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
EOF
```

### 8.4 VERSION 파일 생성

```bash
echo "1.4.7" > VERSION
```

### 8.5 Windows 바탕화면 바로가기 생성

**수동 생성 방법:**

1. **바탕화면에서 우클릭** → "새로 만들기" → "바로 가기"

2. **항목 위치 입력:**
```
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy Bypass -File "\\wsl.localhost\Ubuntu-22.04\home\dino\MyProjects\Crawl\run_crawler.ps1"
```

3. **바로가기 이름**: "네이버 쇼핑 크롤러"

4. **완료** 클릭

**바로가기 아이콘 변경 (선택사항):**
- 바로가기 우클릭 → "속성"
- "아이콘 변경" → 원하는 아이콘 선택

---

## 9. 설치 검증

### 9.1 WSL 환경 확인

**PowerShell에서 실행:**
```powershell
wsl --list --verbose
```
출력:
```
  NAME            STATE           VERSION
* Ubuntu-22.04    Running         2
```

### 9.2 PostgreSQL 연결 확인

**Ubuntu 터미널에서 실행:**
```bash
# PostgreSQL 서비스 시작 (항상 먼저 실행)
sudo service postgresql start

# 연결 테스트
psql -U postgres -d naver -c "SELECT version();"
```
비밀번호 입력 후 PostgreSQL 버전 정보가 출력되면 성공!

### 9.3 Python 패키지 확인

```bash
# 설치된 패키지 확인
pip3 list | grep -E "customtkinter|playwright|psycopg2"
```
출력 예시:
```
customtkinter        5.1.3
playwright           1.40.0
psycopg2-binary      2.9.9
```

### 9.4 Playwright 브라우저 확인

```bash
playwright --version
```
출력: `Version 1.40.0`

### 9.5 GUI 실행 테스트

**바탕화면 바로가기 더블클릭**

정상 실행 시:
1. PowerShell 디버그 콘솔 창 표시
2. GUI 창이 화면 중앙에 표시
3. 카테고리 선택 가능
4. "수집 시작" 버튼 활성화

---

## 10. 문제 해결

### 10.1 WSL2 설치 오류

**증상**: "WSL 2 requires an update to its kernel component"

**해결**:
1. https://aka.ms/wsl2kernel 에서 커널 업데이트 다운로드
2. `wsl_update_x64.msi` 설치
3. PowerShell 재시작 후 `wsl --set-default-version 2` 실행

### 10.2 GUI 창이 작업표시줄에만 나타남

**증상**: 바로가기 실행 시 작업표시줄 아이콘만 보이고 창이 안 보임

**해결**:
```bash
# customtkinter 버전 다운그레이드
pip3 install customtkinter==5.1.3

# WSL 재시작 (PowerShell에서)
wsl --shutdown
```

### 10.3 PostgreSQL 연결 실패

**증상**: "psql: error: connection to server failed"

**해결**:
```bash
# PostgreSQL 서비스 시작
sudo service postgresql start

# 서비스 상태 확인
sudo service postgresql status
```

**부팅 시 자동 시작 설정:**
```bash
# /etc/wsl.conf 파일 생성
sudo tee /etc/wsl.conf << 'EOF'
[boot]
command="service postgresql start"
EOF

# WSL 재시작 (PowerShell에서)
wsl --shutdown
```

### 10.4 Playwright 브라우저 실행 오류

**증상**: "Browser executable not found"

**해결**:
```bash
# Playwright 브라우저 재설치
playwright install chromium
playwright install-deps

# 의존성 패키지 설치
sudo apt install -y libnss3 libnspr4 libatk1.0-0
```

### 10.5 customtkinter 이모지 렌더링 문제

**증상**: GUI에 이모지가 네모박스(□)로 표시

**원인**: customtkinter가 이모지를 렌더링하지 못함

**해결**: 코드 수정 불필요 - 현재 버전(v1.4.7)에서 이미 `remove_emojis()` 함수로 처리됨

### 10.6 메모리 부족 (4GB RAM)

**증상**: 크롤링 중 시스템이 느려지거나 멈춤

**해결**:
1. **불필요한 프로그램 종료**
   - Chrome, Edge 등 브라우저 탭 최소화
   - 백그라운드 앱 종료

2. **WSL 메모리 제한 설정**
```powershell
# Windows 사용자 폴더에 .wslconfig 파일 생성
# 경로: C:\Users\YourUsername\.wslconfig

notepad $env:USERPROFILE\.wslconfig
```

파일 내용:
```ini
[wsl2]
memory=2GB
processors=2
swap=2GB
```

저장 후 WSL 재시작:
```powershell
wsl --shutdown
```

### 10.7 캡차 자동 포커스 안됨

**증상**: 캡차 페이지에서 입력 필드에 포커스가 안 맞춰짐

**확인**:
1. GUI 로그에서 "캡차 감지!" 메시지 확인
2. 브라우저에서 입력 필드가 노란색으로 하이라이트되는지 확인

**해결**:
- 현재 버전(v1.4.7)에서 수정됨
- 업데이트 확인: `cat VERSION` → `1.4.7` 이상

### 10.8 무한 스크롤이 멈춤

**증상**: 3-4개 상품만 수집하고 멈춤

**원인**: 대부분 중복 상품 스킵

**확인**:
```bash
# PostgreSQL에서 중복 확인
psql -U postgres -d naver -c "SELECT category_name, COUNT(*) FROM products GROUP BY category_name;"
```

**해결**:
1. 다른 카테고리 선택 (예: "휴대폰/카메라", "식품")
2. 또는 DB에서 해당 카테고리 삭제:
```sql
DELETE FROM products WHERE category_name = '여성의류';
```

---

## 📚 추가 자료

### 관련 문서
- `README.md` - 프로젝트 개요 및 사용법
- `docs/CRAWLING_LESSONS_LEARNED.md` - 크롤링 문제 해결 사례
- `CLAUDE.md` - Claude AI 작업 지침
- `PROJECT_GUIDELINES.md` - 프로젝트 구조 및 규칙

### 유용한 명령어

**WSL 관리:**
```powershell
# WSL 종료
wsl --shutdown

# WSL 상태 확인
wsl --list --verbose

# Ubuntu 실행
wsl -d Ubuntu-22.04
```

**PostgreSQL 관리:**
```bash
# 서비스 시작
sudo service postgresql start

# 서비스 중지
sudo service postgresql stop

# 서비스 상태
sudo service postgresql status

# DB 백업
pg_dump -U postgres naver > backup.sql

# DB 복원
psql -U postgres naver < backup.sql
```

**Python 환경:**
```bash
# 가상환경 생성 (선택사항)
python3 -m venv venv
source venv/bin/activate

# 패키지 재설치
pip3 install -r requirements.txt --force-reinstall

# 캐시 삭제
find . -type d -name __pycache__ -exec rm -rf {} +
```

---

## ✅ 설치 완료 체크리스트

- [ ] Windows 10 버전 확인 (1903 이상)
- [ ] WSL2 기능 활성화
- [ ] Ubuntu 22.04 설치 및 초기 설정
- [ ] VS Code 설치
- [ ] WSL 확장 설치
- [ ] Claude Code 설치 및 API 키 설정
- [ ] SuperClaude 프레임워크 설치
- [ ] PostgreSQL 설치 및 데이터베이스 생성
- [ ] Python 패키지 설치 (requirements.txt)
- [ ] Playwright 브라우저 설치
- [ ] .env 파일 생성 및 비밀번호 설정
- [ ] run_crawler.ps1 스크립트 생성
- [ ] 바탕화면 바로가기 생성
- [ ] GUI 실행 테스트 성공

**모든 체크리스트 완료 시 크롤링 시스템 가동 준비 완료!**

---

## 🆘 지원 및 문의

**문제가 해결되지 않을 경우:**
1. `docs/CRAWLING_LESSONS_LEARNED.md` 문서 확인
2. GUI 로그 파일 확인: `gui_debug.log`
3. GitHub Issues에 문제 보고 (해당되는 경우)

**정상 작동 확인:**
- GUI 창이 정상적으로 표시됨
- 카테고리 선택 가능
- "수집 시작" 버튼 클릭 시 브라우저 자동 실행
- 캡차 페이지에서 입력 필드에 자동 포커스 (노란색 하이라이트)
- 상품 수집 진행 로그가 GUI에 표시됨
- PostgreSQL DB에 상품 데이터 저장됨

---

**설치 소요 시간**: 약 30-60분 (인터넷 속도에 따라 차이)
**디스크 사용량**: 약 5-7GB (WSL, PostgreSQL, Python 패키지 포함)
