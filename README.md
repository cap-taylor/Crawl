# 네이버 쇼핑 상품 수집기

> **간단한 GUI로 네이버 쇼핑 여성의류 상품 정보를 수집하고 DB에 저장**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40-green.svg)](https://playwright.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-336791.svg)](https://www.postgresql.org/)

---

## 주요 기능

- **GUI 기반 상품 수집**: 클릭 한 번으로 네이버 쇼핑 상품 정보 수집
- **수동 캡차 해결**: 캡차 발생 시 30초 대기 (사용자가 수동으로 해결)
- **중복 체크**: DB에 이미 있는 상품 자동 스킵
- **JSON + DB 저장**: 유연한 데이터 저장 옵션
- **실시간 로그**: 수집 과정 실시간 모니터링

---

## 빠른 시작

### Windows

```bash
# 1. 초기 설정 (최초 1회만)
cd scripts
setup.bat

# 2. .env 파일에서 DB_PASSWORD 설정
# .env 파일을 열고 비밀번호 입력

# 3. GUI 실행
run_gui.bat
```

### Linux/WSL

```bash
# 1. 패키지 설치
pip3 install -r requirements.txt
playwright install firefox

# 2. .env 파일 설정
cp .env.example .env
# .env 파일을 열고 DB_PASSWORD 입력

# 3. GUI 실행
python3 product_collector_gui.py
```

---

## 스크린샷

### GUI 메인 화면
```
┌─────────────────────────────────────────┐
│   네이버 쇼핑 여성의류 상품 수집기      │
├─────────────────────────────────────────┤
│ 수집 상품 개수: [20]                    │
│                                         │
│ ☑ JSON 파일로 저장                      │
│ ☑ DB에 저장                             │
│ ☑ 중복 상품 건너뛰기                    │
│                                         │
│ [수집 시작]  [수집 중지]                │
│                                         │
│ 상태: 수집 중...                        │
├─────────────────────────────────────────┤
│ 실시간 로그:                            │
│ [14:30:15] 수집 시작: 20개              │
│ [14:30:18] Firefox 브라우저 실행        │
│ [14:30:25] 여성의류 카테고리 접속       │
│ [14:30:30] 1번째 상품 수집 중...        │
│ ...                                     │
└─────────────────────────────────────────┘
```

---

## 수집 데이터 (v1.1.0)

### 총 13개 필드 수집

**1순위 필드** (핵심 정보):
- `category_name`: 카테고리명 (예: "여성의류")
- `product_name`: 상품명
- `search_tags`: 검색 태그 배열 (해시태그)

**2순위 필드** (중요 정보):
- `price`: 가격 (원)
- `rating`: 평점 (0.0~5.0)
- `product_url`: 상품 페이지 URL
- `thumbnail_url`: 썸네일 이미지 URL

**3순위 필드** (부가 정보):
- `brand_name`: 브랜드명
- `discount_rate`: 할인율 (%)
- `review_count`: 리뷰 개수
- `crawled_at`: 수집 시각
- `updated_at`: 업데이트 시각

**제거된 필드**:
- ~~`is_sold_out`~~ (현재 판매 상품만 존재하므로 불필요)

---

## 프로젝트 구조

```
Crawl/
├── product_collector_gui.py    # GUI 메인 파일 ⭐ (SimpleCrawler 기반)
├── product_collector_multi_gui.py # 멀티 카테고리 GUI (백업)
├── run_crawler.ps1              # PowerShell 실행 스크립트 ⭐
├── requirements.txt             # Python 패키지 목록
├── VERSION                      # 버전 정보 (1.2.3)
├── .env.example                 # 환경 변수 템플릿
├── README.md                    # 이 파일
│
├── src/
│   ├── core/
│   │   ├── simple_crawler.py    # SimpleCrawler (v1.2.3) ⭐⭐⭐
│   │   ├── product_crawler.py   # 이전 크롤러 (백업)
│   │   └── product_crawler_v2.py # 이전 크롤러 v2 (백업)
│   ├── database/
│   │   └── db_connector.py      # PostgreSQL 연결 및 저장
│   └── utils/
│       └── config.py            # 프로젝트 설정
│
├── tests/
│   └── test_simplified.py       # 간단한 테스트
│
├── data/                        # 수집된 JSON 파일 저장 폴더
│
├── logs/
│   └── gui_debug.log            # GUI 디버깅 로그
│
└── docs/
    ├── PRD.md                   # 제품 요구사항 문서
    └── CRAWLING_LESSONS_LEARNED.md  # 개발 과정 및 시행착오 ⭐⭐
```

---

## 기술 스택

| 분류 | 기술 | 용도 |
|------|------|------|
| **UI** | customtkinter | 모던한 GUI 인터페이스 |
| **크롤링** | Playwright (Firefox) | 브라우저 자동화 |
| **DB** | PostgreSQL + psycopg2 | 데이터 저장 |
| **환경 관리** | python-dotenv | 환경 변수 관리 |

---

## 주요 특징

### 1. 수동 캡차 해결 방식
- 네이버 쇼핑의 캡차는 자동 해결 불가 (OCR/AI 실패)
- 캡차 감지 시 30초 대기 → 사용자가 수동으로 해결
- 안정적이고 지속 가능한 방식

### 2. 중복 체크 시스템
- DB에 이미 있는 상품은 자동으로 스킵
- 모든 필드(가격, 리뷰, 검색태그 등) 비교
- 변경 사항 있으면 업데이트

### 3. SimpleCrawler 아키텍처 (v1.2.3)
```
GUI Layer (product_collector_gui.py)
    ↓
SimpleCrawler (src/core/simple_crawler.py)
    - 13개 필드 수집
    - DB 직접 저장
    - 세션 지속성 (1회 연결/종료)
    - 적응형 대기 시간 (봇 차단 방지)
    ↓
Database Layer (db_connector.py)
    ↓
PostgreSQL
```

---

## 데이터베이스 스키마 (v1.1.0)

### products 테이블 (13개 필드)
```sql
CREATE TABLE products (
    product_id VARCHAR(255) PRIMARY KEY,
    category_name VARCHAR(100),                       -- [1순위]
    product_name TEXT NOT NULL,                       -- [1순위]
    search_tags TEXT[],                               -- [1순위] 검색 태그 배열
    price INTEGER,                                    -- [2순위]
    rating DECIMAL(2,1),                              -- [2순위] 0.0~5.0
    product_url TEXT,                                 -- [2순위]
    thumbnail_url TEXT,                               -- [2순위]
    brand_name VARCHAR(100),                          -- [3순위]
    discount_rate INTEGER,                            -- [3순위]
    review_count INTEGER DEFAULT 0,                   -- [3순위]
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- [3순위]
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP    -- [3순위]
);
```

**변경사항 (v1.1.0)**:
- ✅ is_sold_out 필드 제거 (현재 판매 상품만 존재)
- ✅ 필드 순서 우선순위별로 재배치
- ✅ NOT NULL 제약 조건 추가 (product_name)

---

## 설정 옵션

### .env 파일 (환경 변수)
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=naver
DB_USER=postgres
DB_PASSWORD=your_password_here  # 반드시 설정!
```

### GUI 설정
- **수집 상품 개수**: 1~무제한 (기본 20개)
- **JSON 저장**: data/ 폴더에 타임스탬프 파일 생성
- **DB 저장**: PostgreSQL에 저장
- **중복 체크**: DB 저장 시 중복 상품 스킵

---

## 문서

- **[배포 가이드](docs/DEPLOYMENT_GUIDE.md)** - 새 노트북에서 설치 방법
- **[개발 노트](docs/CRAWLING_LESSONS_LEARNED.md)** - 시행착오 및 해결 과정
- **[코드 가이드](CLAUDE.md)** - 프로젝트 개발 원칙

---

## 라이선스

MIT License

---

## 개발자 노트

이 프로젝트는 네이버 쇼핑의 상품 정보를 수집하는 도구입니다.
**크롤링 윤리**를 준수하고, 과도한 요청으로 서버에 부하를 주지 마세요.

**주요 성과 (v1.2.3 - 2025-10-31)**:
- ✅ 봇 차단 완전 해결 (적응형 대기 시간 전략, 100% 성공률!)
- ✅ SimpleCrawler 구조 (13개 필드, DB 직접 저장)
- ✅ 무한 루프 방지 (URL 세트 비교, 중복 감지)
- ✅ DB 세션 지속성 (1회 연결/종료)
- ✅ 크롤링 안정성 대폭 개선

**개발 마일스톤**:
- 캡차 자동 해결 실패 → 수동 해결 방식 (2025-09-26)
- window.open() 봇 탐지 → 실제 클릭 방식 (2025-11-03)
- 판매자 링크 오류 → 정확한 셀렉터 (2025-11-03)
- 브랜드명 누락 → 테이블 추출 방식 (2025-11-03)
- 봇 차단 문제 → 적응형 대기 시간으로 완전 해결 (2025-10-31)
- 무한 루프 버그 → URL 세트 비교로 해결 (2025-10-31)

**상세 기록**: [docs/CRAWLING_LESSONS_LEARNED.md](docs/CRAWLING_LESSONS_LEARNED.md)

---

**버전**: 1.2.3
**최종 업데이트**: 2025-11-03