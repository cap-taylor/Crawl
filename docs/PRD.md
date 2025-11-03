# 제품 요구사항 문서 (PRD)
## 네이버 쇼핑 상품 수집기 v2.1

### 문서 이력
| 버전 | 작성일 | 주요 변경사항 |
|------|--------|--------------|
| v1.0 | 2025-09-25 | 초기 요구사항 정의 (백업: docs/archive/PRD_v1.0_initial.md) |
| v2.0 | 2025-10-15 | 실제 구현 기반 전면 개정 - MVP 완성 |
| v2.1 | 2025-11-03 | SimpleCrawler 반영, v1.2.3 아키텍처 업데이트 |

### 1. 개요
**프로젝트명**: 네이버 쇼핑 상품 수집기 (Product Collector)
**버전**: 2.1 (코드 v1.2.3)
**작성일**: 2025-11-03
**상태**: 안정화 완료 (봇 차단 해결, 무한 루프 방지)

### 2. 목표
**간단한 GUI로 네이버 쇼핑 전체 카테고리 상품 정보를 수집하고 DB에 저장**하는 사용하기 쉬운 도구 제공

**v2.1 대비 주요 변경**:
- SimpleCrawler 아키텍처 (DB 직접 저장, 세션 지속성)
- 봇 차단 완전 해결 (적응형 대기 시간 전략)
- 무한 루프 방지 (URL 세트 비교, 중복 감지)
- 크롤링 안정성 대폭 개선 (100% 성공률)

### 3. 핵심 요구사항

#### 3.1 기능 요구사항

**구현 완료 (MVP)**:
- ✅ **전체 카테고리 상품 수집**: 네이버 쇼핑 30개 전체 카테고리 상품 정보 크롤링 (GUI에서 선택 가능)
- ✅ **검색 태그 수집**: 상품 상세 페이지의 관련 태그 섹션 해시태그 추출
- ✅ **수동 캡차 해결**: 캡차 감지 시 30초 대기, 사용자 수동 해결
- ✅ **중복 체크 시스템**: DB 기반 중복 검사로 이미 수집된 상품 자동 스킵
- ✅ **무한 수집 모드**: 테스트 모드(개수 지정) + 무한 모드(중단/재개 가능)
- ✅ **데이터 저장**: PostgreSQL 필수 저장, JSON 파일은 디버그 옵션
- ✅ **GUI 인터페이스**: customtkinter 기반 모던 UI, 실시간 로그 출력
- ✅ **배포 스크립트**: Windows 배치 파일로 쉬운 설치 및 실행

**상품 정보 수집 항목**:
- 상품명
- 가격
- 브랜드/몰 이름
- 리뷰 개수
- 평점
- 할인율
- 상품 URL
- 썸네일 이미지
- **검색 태그** (관련 태그 섹션의 해시태그)

#### 3.2 기술 요구사항
- **언어**: Python 3.10+
- **브라우저 자동화**: Playwright with **Firefox** (캡차 대응)
- **데이터베이스**: PostgreSQL 13+ (데이터베이스명: 'naver')
- **GUI 프레임워크**: **customtkinter 5.2.0** (모던 다크 테마)
- **환경 관리**: python-dotenv (비밀번호 보안)
- **환경**: Windows WSL2 / Linux / Windows 네이티브

### 4. 데이터베이스 스키마

#### 4.1 데이터베이스 정보
- **DB명**: `naver`
- **DBMS**: PostgreSQL 13+
- **문자셋**: UTF-8
- **포트**: 5432
- **환경 변수**: `.env` 파일로 비밀번호 관리

#### 4.2 테이블 구조 (실제 구현)

##### Categories 테이블 (단순화된 카테고리 정보)
```sql
CREATE TABLE categories (
    category_name VARCHAR(100) PRIMARY KEY,  -- 카테고리명 (단순 PK)
    category_id VARCHAR(20),                 -- 네이버 카테고리 ID (참조용)
    is_active BOOLEAN DEFAULT FALSE,         -- 수집 대상 여부
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 데이터 예시 (총 30개 대분류 카테고리)
INSERT INTO categories (category_name, category_id, is_active) VALUES
('여성의류', '10000107', TRUE),
('남성의류', '10000108', TRUE),
('패션잡화', '10000109', TRUE),
('신발', '10000110', TRUE),
('화장품/미용', '10000111', TRUE),
-- ... 총 30개 카테고리 (data/naver_categories_hierarchy.json 참조)
```

**설계 철학**:
- 전체 30개 카테고리 지원 (GUI에서 드롭다운으로 선택)
- 복잡한 계층 구조 제거 (최상위 카테고리만)
- `is_active` 플래그로 향후 확장 준비
- 외래키 없이 독립적 운영 (유연성 우선)

##### Products 테이블 (상품 정보) - 핵심 테이블
```sql
CREATE TABLE products (
    product_id VARCHAR(255) PRIMARY KEY,              -- 상품 URL에서 추출한 ID (최대 255자)
    category_name VARCHAR(100),                       -- 카테고리명 (FK 없음)
    product_name TEXT NOT NULL,                       -- 상품명 (필수)
    brand_name VARCHAR(100),                          -- 브랜드명
    price INTEGER,                                    -- 가격 (원)
    discount_rate INTEGER,                            -- 할인율 (%)
    review_count INTEGER DEFAULT 0,                   -- 리뷰 수
    rating NUMERIC(2,1),                              -- 평점 (0.0 ~ 5.0)
    search_tags TEXT[],                               -- 검색 태그 배열 ⭐ 핵심 필드
    product_url TEXT,                                 -- 상품 상세 페이지 URL
    thumbnail_url TEXT,                               -- 썸네일 이미지 URL
    is_sold_out BOOLEAN DEFAULT FALSE,                -- 품절 여부
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- 크롤링 시간
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- 업데이트 시간
    category_fullname VARCHAR(500)                    -- 카테고리 전체 경로 (예: "남성>상의>티셔츠")
);

-- 인덱스
CREATE INDEX idx_product_name ON products(product_name);
CREATE INDEX idx_product_price ON products(price);
CREATE INDEX idx_crawled_at ON products(crawled_at);
CREATE INDEX idx_category_fullname ON products(category_fullname);
```

**중복 체크 로직**:
- `product_id` 기준으로 UPSERT (ON CONFLICT UPDATE)
- 모든 필드 비교하여 변경 사항 있을 때만 업데이트
- `is_duplicate_product()` 함수로 사전 필터링

##### Crawl_History 테이블 (크롤링 이력)
```sql
CREATE TABLE crawl_history (
    history_id SERIAL PRIMARY KEY,                    -- 이력 ID (자동 증가)
    crawl_type VARCHAR(50) NOT NULL,                  -- 크롤링 유형 (예: "여성의류", "남성의류")
    start_time TIMESTAMP NOT NULL,                    -- 시작 시간
    end_time TIMESTAMP,                               -- 종료 시간
    total_categories INTEGER DEFAULT 0,               -- 크롤링한 카테고리 수
    total_products INTEGER DEFAULT 0,                 -- 수집한 상품 수
    status VARCHAR(20) DEFAULT 'running',             -- 상태 (running, completed, failed)
    error_message TEXT,                               -- 오류 메시지 (있을 경우)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP    -- 생성 시간
);
```

**설계 목적**:
- 크롤링 세션 추적 및 모니터링
- 성능 분석 및 오류 디버깅
- 향후 스케줄링 및 자동화 지원

#### 4.3 환경 변수 설정 (.env)
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=naver
DB_USER=postgres
DB_PASSWORD=your_password_here  # 반드시 설정 필요!
```

**보안**:
- `.env` 파일은 `.gitignore`에 등록 (Git 커밋 금지)
- `.env.example` 템플릿 제공
- 비밀번호 없으면 실행 시 `ValueError` 발생

### 5. 프로젝트 구조 (실제 구현)

```
Crawl/
├── product_collector_gui.py      # GUI 메인 파일 ⭐ (SimpleCrawler 기반)
├── product_collector_multi_gui.py # 멀티 카테고리 GUI (백업)
├── run_crawler.ps1                # PowerShell 실행 스크립트 ⭐
├── requirements.txt               # Python 패키지 목록
├── VERSION                        # 버전 정보 (1.2.3)
├── .env                           # 환경 변수 (Git 제외)
├── .env.example                   # 환경 변수 템플릿
├── README.md                      # 프로젝트 개요
├── CLAUDE.md                      # 개발 가이드라인
│
├── src/
│   ├── core/
│   │   ├── simple_crawler.py      # SimpleCrawler (v1.2.3) ⭐⭐⭐
│   │   ├── product_crawler.py     # 이전 크롤러 (백업)
│   │   └── product_crawler_v2.py  # 이전 크롤러 v2 (백업)
│   ├── database/
│   │   └── db_connector.py        # PostgreSQL 연결 및 저장 ⭐
│   └── utils/
│       └── config.py              # 프로젝트 설정
│
├── tests/
│   └── test_simplified.py         # 간단한 테스트 (수정 전)
│
├── data/                          # 수집된 JSON 파일 저장 폴더
│
├── logs/
│   └── gui_debug.log              # GUI 디버깅 로그
│
└── docs/
    ├── PRD.md                     # 제품 요구사항 문서 (이 파일)
    ├── CRAWLING_LESSONS_LEARNED.md # 개발 과정 및 시행착오 ⭐⭐
    └── archive/
        └── PRD_v1.0_initial.md    # 초기 PRD 백업
```

**핵심 파일 설명 (v1.2.3)**:
- `product_collector_gui.py`: customtkinter GUI, SimpleCrawler 실행, 로그 출력
- `simple_crawler.py`: 13개 필드 수집, DB 직접 저장, 세션 지속성 (핵심!)
- `db_connector.py`: DB 저장, 중복 체크, UPSERT 로직
- `run_crawler.ps1`: PowerShell 실행 스크립트 (버전 정보 자동 로드)
- `CRAWLING_LESSONS_LEARNED.md`: 모든 크롤링 문제 해결 방법 문서화

### 6. 크롤링 전략 (SimpleCrawler v1.2.3)

#### 6.1 네비게이션 흐름
1. **메인 페이지 접속**: https://www.naver.com (봇 탐지 회피)
2. **쇼핑 클릭**: 메인에서 쇼핑 아이콘 클릭 (새 탭 열림)
3. **카테고리 버튼 클릭**: "카테고리" 메뉴 버튼
4. **카테고리 선택**: GUI에서 선택한 카테고리로 진입 (30개 중 선택)
5. **상품 리스트 파싱**: `a[class*="ProductCard_link"]` (판매자 링크 제외!)
6. **상세 페이지 접속**: Ctrl+클릭으로 새 탭 열기 (봇 감지 회피)
7. **적응형 대기**: 첫 상품 8-12초, 이후 5-7초 (봇 차단 방지!)
8. **정보 수집**: networkidle 대기 + 13개 필드 수집
9. **중복 체크**: DB에 동일 상품 있으면 스킵
10. **탭 닫기**: 수집 완료 후 상세 페이지 닫기
11. **무한 루프 방지**: URL 세트 비교 + 연속 중복 감지
12. **반복**: 테스트 모드는 지정 개수까지, 무한 모드는 자동 종료 조건까지

#### 6.2 캡차 해결 전략

**시도했으나 실패한 방법**:
- ❌ Anti-Captcha API (정확도 낮음)
- ❌ OCR (pytesseract) - 네이버 캡차 인식 불가
- ❌ AI 기반 해결 (복잡도 높음)

**최종 채택 방법**:
- ✅ **수동 해결 (30초 대기)**
  - 캡차 감지 시 로그 출력
  - 30초 카운트다운 (5초 간격)
  - 사용자가 브라우저에서 직접 입력
  - 안정적이고 지속 가능

#### 6.3 봇 탐지 회피 방법 (v1.2.3 - 100% 성공!)
- ✅ 메인 페이지에서 클릭으로 이동 (URL 직접 접근 금지)
- ✅ Firefox User-Agent 사용
- ✅ 한국 로케일 및 타임존 설정
- ✅ **적응형 대기 시간**: 첫 상품 8-12초, 이후 5-7초 (핵심!)
- ✅ **Ctrl+클릭**: 새 탭 열기 (window.open 금지)
- ✅ **networkidle 우선**: 페이지 완전 로딩 보장
- ✅ 전체화면 브라우저 실행 (no_viewport=True)
- ✅ 오류 체크 제거 (봇 감지 트리거 방지)

### 7. 데이터 수집 범위 (MVP)

#### 구현 완료 (1단계)
- ✅ 전체 30개 카테고리 상품 정보 (여성의류, 남성의류, 패션잡화, 신발, 화장품/미용, 가구, 가전, 등)
- ✅ 상품명, 가격, 할인율
- ✅ 브랜드/몰 이름
- ✅ 리뷰 수, 평점
- ✅ **검색 태그** (관련 태그 섹션의 해시태그)
- ✅ 상품 URL, 썸네일 이미지

#### 향후 확장 (2단계)
- ✅ ~~다른 카테고리 지원~~ (완료: 30개 카테고리 모두 지원)
- ⏳ 옵션 정보 상세 수집
- ⏳ 판매자 정보 수집
- ⏳ 상세 이미지 다운로드

### 8. 성능 요구사항 (실제 측정)
- **크롤링 속도**: 상품당 약 10-15초 (상세 페이지 접속 포함)
- **메모리 사용량**: < 1GB RAM (Firefox + Python)
- **동시 처리**: 1개 (순차 처리, 안정성 우선)
- **브라우저**: Firefox (Playwright), headless=False
- **오류 처리**: 탭 닫기 실패 시 자동 복구

### 9. 사용자 인터페이스 (customtkinter)

#### 9.1 구현된 기능
- ✅ **다크 모드 테마**: 현대적인 UI
- ✅ **수집 모드 선택**:
  - 🔘 테스트 수집 (개수 지정) - 기본 20개
  - 🔘 전체 수집 (무한, 중단/재개 가능)
- ✅ **저장 옵션**:
  - ☑ DB에 저장 (필수, 비활성화됨)
  - ☑ 중복 상품 건너뛰기 (기본 ON)
  - ☑ JSON 파일로 저장 (디버그용, 기본 OFF)
- ✅ **시작/중지 버튼**: 크롤링 제어
- ✅ **실시간 로그**: 스크롤 가능한 로그 창, 타임스탬프 포함
- ✅ **상태 표시**: "대기 중", "수집 중", "수집 완료" 등
- ✅ **이모지 자동 제거**: customtkinter 렌더링 이슈 해결

#### 9.2 UI 레이아웃
```
┌───────────────────────────────────────────────┐
│   네이버 쇼핑 상품 수집기 v1.2.3              │  ← 제목
├───────────────────────────────────────────────┤
│ [카테고리 선택]                               │
│  카테고리: [여성의류 ▼]                       │  ← 30개 중 선택
│                                               │
├───────────────────────────────────────────────┤
│   네이버 쇼핑 상품 수집기                     │  ← 기존 제목
├───────────────────────────────────────────────┤
│ [수집 모드]                                   │
│  ○ 테스트 수집 (개수 지정)  [20] 개          │  ← 라디오 버튼
│  ○ 전체 수집 (무한, 중단/재개 가능)          │
│                                               │
│ [저장 옵션]                                   │
│  ☑ DB에 저장 (필수)                           │  ← 체크박스
│  ☑ 중복 상품 건너뛰기                         │
│  ☐ JSON 파일로 저장 (디버그용, 대량 수집 시 비권장) │
│                                               │
│ [수집 시작]  [수집 중지]                      │  ← 버튼
│ 상태: 대기 중...                              │  ← 상태 라벨
├───────────────────────────────────────────────┤
│ [실시간 로그]                                 │
│ [14:30:15] 전체 상품 수집 시작 (무한 모드)    │  ← 로그 영역
│ [14:30:18] Firefox 브라우저 실행              │  (스크롤 가능)
│ ...                                           │
└───────────────────────────────────────────────┘
```

### 10. 성공 기준 (MVP)
- ✅ 전체 30개 카테고리 상품을 안정적으로 크롤링 (GUI 드롭다운으로 선택 가능)
- ✅ PostgreSQL에 중복 없이 데이터 저장 (UPSERT)
- ✅ 봇 탐지 회피로 장시간 안정적 수집
- ✅ GUI를 통한 명확한 진행 상황 피드백
- ✅ 수동 캡차 해결로 지속 가능한 수집
- ✅ 테스트/무한 모드로 유연한 수집 제어
- ✅ 중단 후 재개 시 중복 없이 이어서 수집

### 11. 제약사항
- 네이버의 robots.txt 및 이용약관 준수
- 과도한 요청 속도 방지
- 자격 증명 수집이나 악의적인 사용 금지
- 교육 및 연구 목적으로만 사용

### 12. 향후 개선사항
- 멀티스레드 크롤링
- 예약된 자동 실행
- CSV/Excel로 데이터 내보내기
- 시간 경과에 따른 가격 추적
- 데이터 접근을 위한 API 엔드포인트