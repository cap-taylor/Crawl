# 제품 요구사항 문서 (PRD)
## 네이버 쇼핑 크롤러 v1.0

### 1. 개요
**프로젝트명**: 네이버 쇼핑 크롤러
**버전**: 1.0
**작성일**: 2025-09-25
**작성자**: 개발팀

### 2. 목표
네이버 쇼핑에서 카테고리, 상품명, 검색 태그 등의 상품 정보를 자동으로 수집하는 웹 크롤러 개발

### 3. 핵심 요구사항

#### 3.1 기능 요구사항
- **카테고리 수집**: 모든 카테고리 계층 구조 크롤링 (대/중/소 카테고리)
- **상품 정보**: 상품명 및 관련 검색 태그 추출
- **봇 차단 회피**: 메인 페이지에서 클릭으로 이동하여 봇 탐지 방지
- **데이터 저장**: 수집된 데이터를 PostgreSQL 데이터베이스에 저장
- **GUI 인터페이스**: 진행 상황 모니터링을 위한 Tkinter 기반 사용자 인터페이스

#### 3.2 기술 요구사항
- **언어**: Python 3.8+
- **브라우저 자동화**: Playwright with Chromium
- **데이터베이스**: PostgreSQL (데이터베이스명: 'naver')
- **GUI 프레임워크**: Tkinter
- **환경**: Windows WSL2 / Linux

### 4. 데이터베이스 스키마

#### 4.1 데이터베이스 정보
- **DB명**: `naver`
- **DBMS**: PostgreSQL 13+
- **문자셋**: UTF-8
- **포트**: 5432

#### 4.2 테이블 구조

##### Categories 테이블 (카테고리 정보)
```sql
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,                   -- 카테고리 고유 ID
    category_name VARCHAR(100) NOT NULL,              -- 카테고리명
    category_level INT NOT NULL,                      -- 계층 레벨 (1: 대, 2: 중, 3: 소)
    parent_category_id INT,                           -- 부모 카테고리 ID
    category_url TEXT NOT NULL,                       -- 네이버 쇼핑 카테고리 URL
    category_path TEXT,                                -- 전체 카테고리 경로 (예: "패션/여성의류/원피스")
    is_active BOOLEAN DEFAULT true,                   -- 활성 상태
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- 크롤링 시간
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- 업데이트 시간

    CONSTRAINT fk_parent_category
        FOREIGN KEY (parent_category_id)
        REFERENCES categories(category_id) ON DELETE CASCADE
);

-- 인덱스
CREATE INDEX idx_category_level ON categories(category_level);
CREATE INDEX idx_parent_category ON categories(parent_category_id);
CREATE INDEX idx_category_name ON categories(category_name);
```

##### Products 테이블 (상품 정보)
```sql
CREATE TABLE products (
    product_id VARCHAR(255) PRIMARY KEY,              -- 네이버 상품 ID
    category_id INT NOT NULL,                         -- 카테고리 ID (FK)
    category_name VARCHAR(100),                       -- 카테고리명 (캐시용)
    product_name TEXT NOT NULL,                       -- 상품명
    brand_name VARCHAR(100),                          -- 브랜드명
    price INTEGER,                                     -- 가격 (원)
    discount_rate INTEGER,                             -- 할인율 (%)
    review_count INTEGER DEFAULT 0,                   -- 리뷰 수
    rating DECIMAL(2,1),                               -- 평점 (0.0 ~ 5.0)
    search_tags TEXT[],                                -- 검색 태그 배열
    product_url TEXT,                                  -- 상품 상세 페이지 URL
    thumbnail_url TEXT,                                -- 썸네일 이미지 URL
    is_sold_out BOOLEAN DEFAULT false,                -- 품절 여부
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- 크롤링 시간
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- 업데이트 시간

    CONSTRAINT fk_category
        FOREIGN KEY (category_id)
        REFERENCES categories(category_id) ON DELETE CASCADE
);

-- 인덱스
CREATE INDEX idx_product_category ON products(category_id);
CREATE INDEX idx_product_name ON products(product_name);
CREATE INDEX idx_product_price ON products(price);
CREATE INDEX idx_crawled_at ON products(crawled_at);
```

##### Crawl_History 테이블 (크롤링 이력)
```sql
CREATE TABLE crawl_history (
    history_id SERIAL PRIMARY KEY,                    -- 이력 ID
    crawl_type VARCHAR(50) NOT NULL,                  -- 크롤링 타입 (category, product)
    start_time TIMESTAMP NOT NULL,                    -- 시작 시간
    end_time TIMESTAMP,                               -- 종료 시간
    total_categories INTEGER DEFAULT 0,               -- 수집된 카테고리 수
    total_products INTEGER DEFAULT 0,                 -- 수집된 상품 수
    status VARCHAR(20) DEFAULT 'running',             -- 상태 (running, completed, failed)
    error_message TEXT,                               -- 오류 메시지
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP    -- 생성 시간
);
```

#### 4.3 데이터베이스 설정 SQL
```sql
-- 데이터베이스 생성
CREATE DATABASE naver
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;

-- 확장 모듈 활성화 (배열 함수 지원)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 5. 프로젝트 구조
```
naver-shopping-crawler/
├── docs/                    # 문서
│   ├── PRD.md
│   └── selectors/          # CSS 셀렉터 샘플
├── src/                    # 소스 코드
│   ├── core/              # 핵심 크롤러 로직
│   │   ├── crawler.py
│   │   └── browser.py
│   ├── database/          # 데이터베이스 작업
│   │   ├── models.py
│   │   └── connection.py
│   ├── gui/               # GUI 컴포넌트
│   │   └── main_window.py
│   └── utils/             # 유틸리티
│       └── config.py
├── scripts/               # 실행 스크립트
│   ├── run.ps1
│   └── run.sh
├── tests/                 # 테스트 파일
├── .env.example          # 환경 변수 템플릿
├── requirements.txt      # 의존성 패키지
└── main.py              # 진입점
```

### 6. 크롤링 전략

#### 6.1 네비게이션 흐름
1. 메인 페이지 접속: https://shopping.naver.com/ns/home
2. 카테고리 메뉴 버튼 클릭
3. 각 카테고리 순회
4. 무한 스크롤로 상품 로드
5. 상품 정보 추출

#### 6.2 봇 탐지 회피 방법
- 랜덤 대기 시간 (2-5초)
- 사람처럼 보이는 마우스 움직임
- 현실적인 스크롤 속도
- User-Agent 로테이션
- 절대 카테고리 URL로 직접 접근하지 않음

### 7. 데이터 수집 범위

#### 1단계 (현재)
- 모든 카테고리명과 계층 구조
- 카테고리별 기본 상품 정보

#### 2단계 (향후)
- 상품 가격
- 판매자 정보
- 리뷰 수와 평점
- 상품 이미지

### 8. 성능 요구사항
- **크롤링 속도**: 상품당 1-2초
- **메모리 사용량**: < 2GB RAM
- **데이터베이스 배치 크기**: 100개 항목당 삽입
- **오류 복구**: 지수 백오프를 통한 자동 재시도

### 9. 사용자 인터페이스 요구사항
- **시작/중지 컨트롤**: 쉬운 크롤러 관리
- **진행 상황 추적**: 실시간 상태 업데이트
- **로그 표시**: 스크롤 가능한 로그 창
- **통계**: 카테고리 및 상품 카운터
- **모드 선택**: 카테고리만 또는 전체 크롤

### 10. 성공 기준
- 모든 네이버 쇼핑 카테고리를 성공적으로 크롤링
- PostgreSQL에 중복 없이 데이터 저장
- 지속적인 작업을 위한 봇 탐지 회피
- GUI를 통한 명확한 진행 상황 피드백 제공
- 로깅과 함께 오류를 우아하게 처리

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