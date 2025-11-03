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

#### 2. Products 테이블 (v1.1.0)
상품 상세 정보 및 검색 태그 저장 (13개 필드)
```sql
CREATE TABLE products (
    product_id VARCHAR(255) PRIMARY KEY,              -- 상품 고유 ID
    category_name VARCHAR(100),                       -- [1순위] 카테고리명
    product_name TEXT NOT NULL,                       -- [1순위] 상품명
    search_tags TEXT[],                               -- [1순위] 검색 태그 배열
    price INTEGER,                                    -- [2순위] 가격 (원)
    rating DECIMAL(2,1),                              -- [2순위] 평점 (0.0~5.0)
    product_url TEXT,                                 -- [2순위] 상품 URL
    thumbnail_url TEXT,                               -- [2순위] 썸네일 이미지 URL
    brand_name VARCHAR(100),                          -- [3순위] 브랜드명
    discount_rate INTEGER,                            -- [3순위] 할인율 (%)
    review_count INTEGER DEFAULT 0,                   -- [3순위] 리뷰 수
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- [3순위] 수집 시각
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP    -- [3순위] 업데이트 시각
);

-- 인덱스
CREATE INDEX idx_product_name ON products(product_name);
CREATE INDEX idx_product_price ON products(price);
CREATE INDEX idx_crawled_at ON products(crawled_at);
```

**변경사항 (v1.1.0)**:
- ✅ is_sold_out 필드 제거 (현재 판매 상품만 존재하므로 불필요)
- ✅ category_fullname 필드 제거 (단순화)
- ✅ 필드 순서 우선순위별로 재배치

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
- **✅ DECIMAL 정밀도**: `rating DECIMAL(2,1)` → 0.0~5.0 범위
- **✅ 우선순위 설계**: 1순위(핵심), 2순위(중요), 3순위(부가) 필드 분류

## 🤖 크롤링 전략 (네이버 전용)

### 봇 탐지 회피 필수 규칙 (2025-11-03 검증 완료)
1. **절대 카테고리 URL 직접 접근 금지** - 메인 페이지에서 클릭으로만 이동
2. **실제 클릭 사용**: `await product.click()` (window.open() 금지 - 봇 탐지됨)
3. **정확한 셀렉터**: `a[class*="ProductCard_link"]` (판매자 링크 제외)
4. **랜덤 대기 시간**: 1-3초 사이 (자연스러운 간격)
5. **스크롤 방식**: 10%씩 점진적 스크롤 (10%-100%)

### 셀렉터 정보 (2025-11-03 최종 검증)

**카테고리 페이지**:
- 상품 링크: `a[class*="ProductCard_link"]` (판매자 링크 제외!)
- 잘못된 예: `div[class*="product"] a` (판매자 링크 포함됨)

**상품 상세 페이지** (13개 필드):
- `product_name`: `h3.DCVBehA8ZB`
- `price`: `strong.Izp3Con8h8`
- `brand_name`: JavaScript evaluate (테이블에서 "브랜드" → nextTd)
- `discount_rate`: JavaScript evaluate (`/(\d+)%/` 패턴)
- `review_count`: JavaScript evaluate (`/리뷰\s*(\d+)/` 패턴)
- `rating`: JavaScript evaluate (`/(\d+\.\d+)/` 패턴)
- `search_tags`: `a` 링크 중 `#`으로 시작하는 텍스트 (전체 스크롤 필요)
- `thumbnail_url`: `img[class*="image"]`

**상세**: [docs/CRAWLING_LESSONS_LEARNED.md](docs/CRAWLING_LESSONS_LEARNED.md)

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

- **현재 버전**: 1.1.0
- **버전 규칙**: Semantic Versioning (MAJOR.MINOR.PATCH)
- **업데이트 시**: VERSION 파일과 CHANGELOG.md 동시 수정

**v1.1.0 주요 변경사항 (2025-11-03)**:
- ✅ 13개 필드로 확정 (is_sold_out 제거)
- ✅ 봇 탐지 회피 성공 (실제 클릭 방식)
- ✅ 셀렉터 100% 일관성 검증
- ✅ 브랜드명 추출 개선 (테이블 방식)
- ✅ 검색 태그 전체 수집 (스크롤 최적화)