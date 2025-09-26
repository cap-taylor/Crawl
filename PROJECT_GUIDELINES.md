# 프로젝트 개발 지침 - 네이버 쇼핑 크롤러

## 🔒 고정 설정 (절대 수정 금지)

### 실행 파일 경로
- **PowerShell 스크립트**: `run_crawler.ps1`
  - 위치: 프로젝트 루트 (절대 이동 금지)
  - 경로: `D:\#MyProjects#Crawl\#run_crawler.ps1`
  - Windows 바로가기에서 직접 참조 중

### 실행 방법
1. **바탕화면 바로가기**: 더블클릭 → PowerShell 7 자동 실행
2. **PowerShell 직접 실행**: `pwsh -ExecutionPolicy Bypass -File D:\MyProjects\Crawl\run_crawler.ps1`
3. **WSL 터미널**: `python3 main.py`

## 📁 프로젝트 구조 (고정)

```
Crawl/
├── src/                    # 소스 코드
│   ├── core/              # 크롤러 핵심 로직
│   │   ├── crawler.py     # 메인 크롤러
│   │   └── terminal_crawler.py  # 터미널 모드
│   ├── database/          # DB 연동
│   ├── gui/               # GUI 컴포넌트
│   │   └── main_window.py # Tkinter GUI
│   └── utils/             # 유틸리티
│       └── config.py      # 설정 파일
├── docs/                  # 문서
│   ├── PRD.md            # 제품 요구사항 (한글)
│   └── selectors/        # 네이버 셀렉터 정보
├── scripts/              # 실행 스크립트
├── database/             # DB 스키마
│   └── create_tables.sql
├── run_crawler.ps1       # ⚠️ 실행 스크립트 (절대 이동 금지)
├── main.py              # 진입점
├── VERSION              # 버전 파일
├── CHANGELOG.md         # 변경 이력
└── .env                 # 환경 변수
```

## 🗄️ 데이터베이스 설정

### PostgreSQL 정보
- **DB 이름**: `naver` (고정)
- **기본 포트**: 5432
- **테이블**:
  - `categories`: 카테고리 정보
  - `products`: 상품 정보 및 검색 태그

### 환경 변수 (.env)
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=naver
DB_USER=postgres
DB_PASSWORD=postgres
```

## 🤖 크롤링 전략 (네이버 전용)

### 봇 탐지 회피 필수 규칙
1. **절대 카테고리 URL 직접 접근 금지** - 메인 페이지에서 클릭으로만 이동
2. **랜덤 대기 시간**: 2-5초 사이
3. **스크롤 속도**: 사람처럼 점진적으로
4. **User-Agent**: 실제 브라우저 설정 사용
5. **클릭 시뮬레이션**: 실제 마우스 움직임 재현

### 셀렉터 정보 (docs/selectors/)
- 카테고리 버튼: `#gnb-gnb button`
- 상품 카드: `#composite-card-list li`
- 검색 태그: `#INTRODUCE .f_JzwGZdbu a`

## 🔧 개발 시 주의사항

### 필수 준수 사항
1. **모든 경로는 영어로**: 파일명, 폴더명 모두 영어 사용
2. **문서는 한글로**: PRD, 사용자 문서는 한글 작성
3. **import 경로**: `src.` 접두사 사용 (예: `from src.core.crawler import ...`)
4. **테스트 파일**: `tests/` 폴더에만 생성

### 금지 사항
1. ❌ `run_crawler.ps1` 파일 이동 또는 수정
2. ❌ 프로젝트 구조 임의 변경
3. ❌ 루트 디렉토리에 임시 파일 생성
4. ❌ 네이버 카테고리 URL 직접 접근

## 📊 성능 기준

- **크롤링 속도**: 상품당 1-2초
- **메모리 사용**: 최대 2GB
- **DB 배치 크기**: 100개씩 저장
- **재시도**: 실패 시 지수 백오프 (2, 4, 8초...)

## 🚀 배포 및 실행

### 개발 환경
- Python 3.8+
- WSL2 (Windows)
- PostgreSQL 13+
- Playwright (Chromium)

### 의존성 설치
```bash
pip install -r requirements.txt
playwright install chromium
```

### 첫 실행 전 확인
1. PostgreSQL 서비스 실행 중
2. `naver` 데이터베이스 생성됨
3. `.env` 파일에 DB 정보 입력됨
4. Chromium 브라우저 설치됨

## 📝 버전 관리

- **현재 버전**: 1.0.0
- **버전 규칙**: Semantic Versioning (MAJOR.MINOR.PATCH)
- **업데이트 시**: VERSION 파일과 CHANGELOG.md 동시 수정