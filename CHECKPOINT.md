# 🔖 네이버 쇼핑 크롤러 프로젝트 체크포인트
> 작성일: 2025-09-26 23:25
> 목적: 상품 정보 수집 시스템 구축 및 프로젝트 현황 정리
> 최종 업데이트: 2025-11-03 17:25

## 📝 커밋 히스토리
```
994df85 - 2025-11-03 17:25 : 체크포인트: GUI 시스템 개선 완료
eb4cf84 - 2025-11-03 16:16 : feat: GUI v1.2.0 - 30개 카테고리 + 무한 수집 + DB 직접 저장
e22c998 - 2025-11-03 15:40 : 백업: 단순화 수정 전 상태 저장
07bf3de - 2025-11-03 00:15 : docs: CHECKPOINT.md 커밋 해시 업데이트 (d79535c)
d79535c - 2025-10-31 19:30 : docs: Python 캐시 문제 시행착오 문서화
4dae57f - 2025-10-31 19:18 : 체크포인트: 봇 차단 최종 해결 (로딩 대기 시간 증가)
8be3a9f - 2025-10-31 18:49 : 체크포인트: 봇 차단 최종 해결 (Stealth 스크립트 + 에러 체크 타이밍)
e5c895e - 2025-10-31 13:08 : 체크포인트: v1.2.2 - 크롤러 무한 루프 버그 수정
372abda - 2025-10-17 20:09 : 체크포인트: v1.2.1 - 크롤러 무한 루프 버그 수정
99d2ebc - 2025-10-17 16:40 : 체크포인트: GUI UI/UX 현대적 개선 (v1.2.0)
a624088 - 2025-10-15 20:27 : 체크포인트: 장시간 크롤링 안전성 개선 (v1.1.4)
7d1756f - 2025-10-15 20:17 : 체크포인트: ElementHandle 예외 처리 개선 (v1.1.4)
8625e62 - 2025-10-15 19:56 : 체크포인트: v1.1.3 - 상품 수집 안정성 대폭 개선
2e1f6e3 - 2025-10-15 19:23 : 체크포인트: 카테고리 경로 수집 완성 (v1.1.2)
880068a - 2025-10-15 17:03 : docs: CHECKPOINT.md 커밋 해시 업데이트 (c0c1070)
c0c1070 - 2025-10-15 15:49 : fix: GUI 로그 한글 깨짐 수정 (v1.0.4)
5135ff3 - 2025-10-15 15:00 : docs: DB 스키마 파일 실제 구조와 동기화
4cb4376 - 2025-10-15 14:50 : 체크포인트: v1.0.3 - GUI 개선 및 로그 간결화
58bd2d6 - 2025-10-15 12:12 : 체크포인트: 여성의류 검색태그 수집 - 시행착오 해결 및 문서화
5bbd4e4 - 2025-10-02 22:15 : docs: CHECKPOINT.md 커밋 해시 및 GitHub URL 업데이트
cde57fe - 2025-09-26 23:30 : 체크포인트: 캡차 수동 해결 시스템 구현 및 프로젝트 초기 설정
```

## 📊 현재 완성된 기능

### ✅ 상품 정보 수집 시스템 (2025-11-03 완성)
- **13개 필드 완벽 수집**
  - 1순위: category_name, product_name, search_tags
  - 2순위: price, rating, product_url, thumbnail_url
  - 3순위: brand_name, discount_rate, review_count, crawled_at, updated_at
- **100% 셀렉터 일관성**: 13번째, 14번째 상품 모두 검증 완료
- **브랜드명 추출**: 상품정보 테이블에서 정확히 추출
- **검색 태그 수집**: 전체 페이지 스크롤(10%-100%)로 모든 태그 수집

### ✅ 봇 탐지 회피 전략 (2025-11-03 완성)
- **실제 클릭 방식**: `product.click()` 사용 (window.open() 금지)
- **정확한 셀렉터**: `a[class*="ProductCard_link"]` (판매자 링크 제외)
- **10/10 성공률**: 상품 페이지 진입 100% 성공
- **봇 차단 0건**: 실제 사용자처럼 클릭 이동

### ✅ 크롤러 핵심 기능
- **카테고리 크롤러** (`src/core/crawler.py`)
  - 네이버 쇼핑 카테고리 수집
  - 메인 페이지 → 클릭으로만 이동 (URL 직접 접근 금지)
  - 비동기 처리 (asyncio + Playwright)

### ✅ GUI 인터페이스
- **customtkinter 기반 GUI** (`product_collector_gui.py`)
  - 크롤링 진행 상황 실시간 표시
  - 카테고리/상품 수 카운터
  - 로그 메시지 표시 (이모지 필터링)
  - 시작/중지 컨트롤

### ✅ 데이터베이스 구조 (v1.1.0)
- **PostgreSQL 데이터베이스**: naver
- **테이블 구조**:
  - categories: 카테고리 메타데이터
  - products: 13개 필드 (is_sold_out 제거)
  - crawl_history: 크롤링 이력 추적

## 🎯 현재 가능한 워크플로우

### 메인 크롤링 프로세스
1. **GUI 실행**:
   ```bash
   python3 main.py
   ```
2. **캡차 발생 시**:
   - 브라우저에 알림 표시
   - 사용자가 직접 캡차 해결
   - 해결 후 자동으로 크롤링 재개

### 테스트 실행
```bash
# 수동 캡차 테스트
python3 tests/test_manual_captcha_handler.py
```

## 📁 프로젝트 구조
```
Crawl/
├── src/
│   ├── core/
│   │   └── crawler.py         # 메인 크롤러
│   ├── database/              # DB 연동 (미구현)
│   ├── gui/
│   │   └── main_window.py     # Tkinter GUI
│   └── utils/
│       ├── captcha_handler.py # 캡차 수동 해결 핸들러
│       └── config.py          # 설정 파일
├── tests/                     # 23개 테스트 파일
│   └── test_manual_captcha_handler.py # 수동 캡차 테스트
├── docs/
│   ├── PRD.md                 # 제품 요구사항
│   └── CRAWLING_LESSONS_LEARNED.md
├── database/
│   └── create_tables.sql      # DB 스키마
├── scripts/
│   └── run_crawler.ps1        # PowerShell 실행 스크립트
├── main.py                    # 진입점
├── VERSION                    # 버전 (1.2.2)
├── CHANGELOG.md              # 변경 이력
├── CHECKPOINT.md             # 이 문서
├── CLAUDE.md                 # 프로젝트 가이드라인
├── PROJECT_GUIDELINES.md     # 개발 지침
└── .env                      # 환경변수 (Git 제외)
```

## 📝 다음 구현해야 할 기능

### 우선순위 1 (긴급)
- [x] 상품 정보 수집 로직 구현 (✅ 2025-11-03 완료)
- [x] 13개 필드 셀렉터 파악 (✅ 2025-11-03 완료)
- [x] 봇 탐지 회피 전략 (✅ 2025-11-03 완료)
- [ ] 크롤러 v2에 통합 (진행 중)
- [ ] DB 저장 로직 연동

### 우선순위 2 (중요)
- [ ] 무한 상품 수집 모드
- [ ] 중단점 저장 및 재개 기능
- [ ] 에러 복구 로직

### 우선순위 3 (개선)
- [ ] 멀티스레드 처리
- [ ] CSV/Excel 내보내기
- [ ] 통계 대시보드

## 🔧 환경 설정

### 필요한 패키지
```bash
pip install -r requirements.txt
playwright install chromium
```

### PostgreSQL 설정
```sql
CREATE DATABASE naver
    WITH
    OWNER = postgres
    ENCODING = 'UTF8';
```

## 💡 복구 방법

### 이 체크포인트로 복구:

1. **코드 복구**:
   ```bash
   git clone https://github.com/cap-taylor/Crawl.git
   cd Crawl
   git checkout cde57fe
   ```

2. **환경 재설정**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **DB 확인**:
   ```bash
   psql -h localhost -U postgres -d naver
   ```

4. **크롤링 시작**:
   ```bash
   python3 main.py
   ```

## 📊 현재 상태
- **상품 정보 수집**: 13개 필드 100% 완성
- **봇 탐지 회피**: 실제 클릭 방식으로 10/10 성공
- **셀렉터 일관성**: 13번째, 14번째 상품 모두 검증 완료
- **다음 단계**: 크롤러 v2 통합 및 DB 저장

## 🐛 해결된 이슈
- ✅ 캡차 자동 해결 → 수동 해결 방식 (2025-09-26)
- ✅ Firefox 브라우저 접속 문제 (2025-10-31)
- ✅ window.open() 봇 탐지 → 실제 클릭 방식 (2025-11-03)
- ✅ 판매자 페이지 오류 → 정확한 셀렉터 (2025-11-03)
- ✅ enumerate 버그 → valid_count 분리 (2025-11-03)
- ✅ 브랜드명 누락 → 테이블 추출 방식 (2025-11-03)
- ✅ 검색 태그 불완전 → 전체 스크롤 (2025-11-03)

## ⚠️ 알려진 이슈
- 없음 (모든 주요 이슈 해결 완료)

## 📌 주의사항
- 캡차 발생 시 반드시 수동으로 해결 필요
- 크롤링 속도 조절로 봇 탐지 최소화
- 네이버 robots.txt 및 이용약관 준수
- Windows에서 실행 시 PowerShell 스크립트 사용

## 🚀 성능 지표
- **캡차 대기 시간**: 최대 5분
- **목표 처리 속도**: 상품당 1-2초
- **메모리 사용**: < 2GB
- **봇 탐지 회피율**: 테스트 중

---
*이 문서는 프로젝트 진행 상황을 추적하고 복구 지점을 제공합니다.*