# 프로젝트 개발 지침 - 네이버 쇼핑 크롤러

## 🔒 고정 설정 (절대 수정 금지)

### 실행 파일 경로
- **PowerShell 스크립트**: `run_crawler.ps1`
  - 위치: 프로젝트 루트 (절대 이동 금지)
  - WSL 경로: `/home/dino/MyProjects/Crawl/run_crawler.ps1`
  - Windows 경로: `\\wsl.localhost\Ubuntu-22.04\home\dino\MyProjects\Crawl\run_crawler.ps1`

### 실행 방법
1. **WSL 터미널** (권장): `python3 main.py`
2. **PowerShell**: 프로젝트 루트에서 `pwsh -ExecutionPolicy Bypass -File ./run_crawler.ps1`
3. **직접 실행**: `python3 /home/dino/MyProjects/Crawl/main.py`

## 📁 프로젝트 구조 (절대 준수!)

### ⚠️ 중요: 루트 디렉토리 규칙
**루트(`/home/dino/MyProjects/Crawl/`)에는 아래 파일만 허용됩니다. 절대 다른 파일 생성 금지!**

### 허용된 루트 파일
- `main.py` - 메인 실행 파일 (유일한 Python 파일)
- `run_crawler.ps1` - PowerShell 실행 스크립트 (⚠️ 절대 이동 금지)
- `install_tkinter.ps1` - 설치 스크립트
- `.env`, `.env.example` - 환경 설정
- `.gitignore` - Git 설정
- `README.md` - 프로젝트 소개
- `requirements.txt` - 패키지 목록
- `VERSION` - 버전 정보
- `CHANGELOG.md` - 변경 이력
- `CHECKPOINT.md` - Git 체크포인트
- `CLAUDE.md` - Claude 사용 지침
- `PROJECT_GUIDELINES.md` - 이 문서

### 전체 디렉토리 구조
```
Crawl/
├── src/                    # 소스 코드
│   ├── core/              # 크롤러 핵심 로직
│   │   ├── crawler.py     # 메인 크롤러
│   │   └── terminal_crawler.py  # 터미널 모드
│   ├── database/          # DB 연동
│   ├── gui/               # GUI 컴포넌트
│   │   ├── main_window.py # Tkinter GUI
│   │   └── category_tree_window.py # 카테고리 트리 GUI
│   └── utils/             # 유틸리티
│       ├── config.py      # 설정 파일
│       └── category_*.py  # 카테고리 수집기들
├── tests/                 # 테스트 파일 (test_*.py만!)
├── scripts/               # 스크립트 파일
│   ├── run/              # 실행 스크립트
│   │   ├── collect_categories.py
│   │   └── run_tree_gui.py
│   └── install/          # 설치 스크립트
├── data/                  # 데이터 파일
│   ├── *.json            # JSON 데이터
│   ├── *.csv             # CSV 데이터
│   ├── *.xlsx            # Excel 데이터
│   ├── screenshots/      # 스크린샷
│   └── temp/             # 임시 파일 (사용 후 즉시 삭제)
├── docs/                  # 문서
│   ├── PRD.md            # 제품 요구사항 (한글)
│   ├── CRAWLING_LESSONS_LEARNED.md  # 크롤링 시행착오
│   └── selectors/        # 네이버 셀렉터 정보
├── database/              # DB 스키마
│   └── create_tables.sql
├── logs/                  # 로그 파일
├── run_crawler.ps1       # ⚠️ 실행 스크립트 (절대 이동 금지)
├── main.py              # 진입점 (유일한 루트 Python 파일)
├── VERSION              # 버전 파일
├── CHANGELOG.md         # 변경 이력
└── .env                 # 환경 변수
```

### 📝 파일 생성 규칙
1. **테스트 파일**: 반드시 `tests/test_*.py` 형식으로 `tests/` 폴더에만 생성
2. **실행 스크립트**: `scripts/run/` 폴더에 생성
3. **카테고리 수집기**: `src/utils/category_*.py` 형식으로 생성
4. **데이터 파일**: `data/` 폴더에만 저장
5. **임시 파일**: 절대 생성 금지! 필요시 `data/temp/` 사용 후 즉시 삭제
6. **루트에 Python 파일 생성 절대 금지** (main.py만 예외)

## 🗄️ 데이터베이스 설정

### PostgreSQL 정보
- **DB 이름**: `naver` (고정)
- **기본 포트**: 5432
- **테이블**: `categories`, `products`, `crawl_history`

### 환경 변수 (.env)
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=naver
DB_USER=postgres
DB_PASSWORD=postgres
```

### 데이터베이스 스키마

#### 1. Categories 테이블
카테고리 메타데이터 저장
```sql
CREATE TABLE categories (
    category_name VARCHAR(100) PRIMARY KEY,    -- 카테고리 이름 (예: "여성의류")
    category_id VARCHAR(20),                   -- 네이버 카테고리 ID (예: "10000107")
    is_active BOOLEAN DEFAULT FALSE,           -- 활성화 상태
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. Products 테이블
상품 상세 정보 및 검색 태그 저장
```sql
CREATE TABLE products (
    product_id VARCHAR(255) PRIMARY KEY,       -- 상품 고유 ID
    category_name VARCHAR(100),                -- 카테고리명 (categories 참조, FK 없음)
    product_name TEXT NOT NULL,                -- 상품명
    brand_name VARCHAR(100),                   -- 브랜드명
    price INTEGER,                             -- 가격 (원)
    discount_rate INTEGER,                     -- 할인율 (%)
    review_count INTEGER DEFAULT 0,            -- 리뷰 수
    rating NUMERIC(2,1),                       -- 평점 (0.0~5.0)
    search_tags TEXT[],                        -- 검색 태그 배열
    product_url TEXT,                          -- 상품 URL
    thumbnail_url TEXT,                        -- 썸네일 이미지 URL
    is_sold_out BOOLEAN DEFAULT FALSE,         -- 품절 여부
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category_fullname VARCHAR(500)             -- 카테고리 전체 경로 (예: "하의 > 바지 & 슬렉스")
);

-- 인덱스
CREATE INDEX idx_product_name ON products(product_name);
CREATE INDEX idx_product_price ON products(price);
CREATE INDEX idx_crawled_at ON products(crawled_at);
CREATE INDEX idx_category_fullname ON products(category_fullname);
```

#### 3. Crawl_History 테이블
크롤링 작업 이력 추적
```sql
CREATE TABLE crawl_history (
    history_id SERIAL PRIMARY KEY,             -- 자동 증가 ID
    crawl_type VARCHAR(50) NOT NULL,           -- 크롤링 유형 (카테고리/상품)
    start_time TIMESTAMP NOT NULL,             -- 시작 시각
    end_time TIMESTAMP,                        -- 종료 시각
    total_categories INTEGER DEFAULT 0,        -- 수집한 카테고리 수
    total_products INTEGER DEFAULT 0,          -- 수집한 상품 수
    status VARCHAR(20) DEFAULT 'running',      -- 상태 (running/completed/failed)
    error_message TEXT,                        -- 에러 메시지
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 설계 특징
- **❌ Foreign Key 없음**: `category_name`으로 직접 조인 (유연성 우선)
- **✅ PostgreSQL 배열**: `search_tags TEXT[]` 네이티브 배열 타입 사용
- **✅ 인덱스 최적화**: 자주 검색하는 필드에 인덱스 설정
- **✅ NUMERIC 정밀도**: `rating NUMERIC(2,1)` → 0.0~9.9 범위 (실제 0.0~5.0)
- **✅ 카테고리 경로**: `category_fullname` 필드로 전체 경로 저장

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

## 🎨 GUI 설계 원칙

### 팝업 사용 금지
- **원칙**: 모든 정보는 메인 창 내에서 표시 (팝업 절대 금지)
- **이유**: 팝업 클릭이 번거롭고, 사용자 워크플로우 방해
- **대안**: 로그 영역에 정보 출력 또는 메인 창 영역 활용

### 확인창 금지
- **무한 모드 시작**: 확인창 없이 바로 시작
- **설정 변경**: 즉시 반영 (확인 불필요)
- **최근 기록**: 로그 영역에 출력

### 정보 표시 원칙
- ✅ 메인 창 내 라벨/텍스트로 표시
- ✅ 로그 영역에 상세 정보 출력
- ✅ 상태 바에 간단한 알림
- ❌ 별도 팝업 창 생성 금지
- ❌ 확인/취소 다이얼로그 금지

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