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

## 수집 데이터

### 상품 정보
- 상품명
- 가격
- 브랜드/몰 이름
- 리뷰 개수
- 평점
- 할인율
- 상품 URL
- 썸네일 이미지

### 상세 정보
- **검색 태그** (관련 태그 섹션의 해시태그)
- 옵션 정보
- 상세 이미지
- 판매자 정보
- 배송 정보

---

## 프로젝트 구조

```
Crawl/
├── product_collector_gui.py    # GUI 메인 파일 ⭐
├── requirements.txt             # Python 패키지 목록
├── .env.example                 # 환경 변수 템플릿
├── README.md                    # 이 파일
│
├── scripts/
│   ├── setup.bat                # Windows 초기 설정 스크립트
│   └── run_gui.bat              # Windows GUI 실행 스크립트
│
├── src/
│   ├── database/
│   │   └── db_connector.py      # PostgreSQL 연결 및 저장
│   └── utils/
│       └── config.py            # 프로젝트 설정
│
├── tests/
│   └── test_womens_manual_captcha.py  # 크롤러 핵심 로직
│
├── data/                        # 수집된 JSON 파일 저장 폴더
│
└── docs/
    ├── DEPLOYMENT_GUIDE.md      # 배포 가이드 (새 노트북 설치 방법)
    ├── CRAWLING_LESSONS_LEARNED.md  # 개발 과정 및 시행착오
    └── AUTOMATION_DESIGN.md     # 자동화 설계 문서
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

### 3. 레이어 분리 아키텍처
```
GUI Layer (product_collector_gui.py)
    ↓
Crawler Layer (test_womens_manual_captcha.py)
    ↓
Database Layer (db_connector.py)
    ↓
PostgreSQL
```

---

## 데이터베이스 스키마

### products 테이블
```sql
CREATE TABLE products (
    product_id VARCHAR(50) PRIMARY KEY,
    category_id INTEGER,
    category_name VARCHAR(100),
    product_name TEXT,
    brand_name VARCHAR(200),
    price INTEGER,
    discount_rate INTEGER,
    review_count INTEGER,
    rating NUMERIC(3,2),
    search_tags TEXT[],              -- 검색 태그 배열
    product_url TEXT,
    thumbnail_url TEXT,
    is_sold_out BOOLEAN DEFAULT FALSE,
    crawled_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

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

**개발 과정**:
- 캡차 자동 해결 실패 (Anti-Captcha, OCR, AI 모두 실패)
- 수동 해결 방식 채택 → 안정적 운영
- 검색 태그 수집 성공 (여성의류 20개 상품 테스트 완료)

---

**버전**: 1.0
**최종 업데이트**: 2025-10-15