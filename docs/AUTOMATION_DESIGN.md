# 네이버 쇼핑 장기 수집 자동화 시스템 설계

> 작성일: 2025-10-15
> 목적: 1주일 단위 카테고리별 전체 상품 수집 시스템

## 📋 요구사항

### 핵심 요구사항
1. **지속적 실행**: 남는 컴퓨터에서 24시간 실행
2. **카테고리별 수집**: 1주일 = 1개 대분류 카테고리 전체 수집
3. **자동 전환**: 1주일 후 자동으로 다음 카테고리로 이동
4. **중단 재개**: 중단되어도 이어서 수집 가능
5. **DB 저장**: 모든 데이터를 PostgreSQL에 저장

### 제약사항
- **캡차**: 수동 해결 필요 (20초 대기)
- **봇 탐지**: 과도한 속도로 수집 시 차단 위험
- **네트워크**: 간헐적 타임아웃 발생 가능

## 🏗️ 시스템 구조

### 1. 컴포넌트

```
automation_system/
├── scheduler.py              # 메인 스케줄러 (24시간 실행)
├── category_manager.py       # 카테고리 관리 (현재 카테고리, 진행률)
├── crawler_worker.py         # 실제 크롤링 작업자
├── progress_tracker.py       # 진행 상황 추적 (DB 기반)
├── error_handler.py          # 오류 처리 및 재시도
└── config/
    ├── categories.json       # 대분류 카테고리 목록
    └── crawl_settings.json   # 수집 설정 (속도, 대기시간 등)
```

### 2. 데이터 흐름

```
[Scheduler]
    ↓
[Category Manager] → 현재 카테고리 확인 (예: 여성의류)
    ↓
[Crawler Worker] → 상품 수집 (30번째부터)
    ↓
[DB Connector] → PostgreSQL 저장
    ↓
[Progress Tracker] → 진행 상황 기록 (2735313334번 수집 완료)
    ↓
[Error Handler] → 오류 발생 시 재시도 (최대 3회)
    ↓
다음 상품으로 이동 (31번째 → 32번째 → ...)
```

## 📊 DB 스키마 확장

기존 테이블 외에 진행 상황 추적을 위한 테이블 추가:

```sql
-- 수집 진행 상황 테이블
CREATE TABLE crawl_progress (
    progress_id SERIAL PRIMARY KEY,
    category_id INT NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    current_position INT DEFAULT 0,  -- 현재 수집 중인 상품 인덱스
    total_collected INT DEFAULT 0,   -- 현재까지 수집한 상품 수
    status VARCHAR(20) DEFAULT 'active',  -- active, paused, completed
    last_product_id VARCHAR(255),    -- 마지막으로 수집한 상품 ID
    error_count INT DEFAULT 0,
    notes TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 오류 로그 테이블
CREATE TABLE error_logs (
    error_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100),
    product_id VARCHAR(255),
    error_type VARCHAR(50),
    error_message TEXT,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    retry_count INT DEFAULT 0,
    resolved BOOLEAN DEFAULT FALSE
);
```

## ⚙️ 설정 파일

### categories.json
```json
{
  "categories": [
    {
      "id": 1,
      "name": "여성의류",
      "priority": 1,
      "url": "네이버 쇼핑 여성의류 URL",
      "estimated_products": 100000,
      "status": "active"
    },
    {
      "id": 2,
      "name": "남성의류",
      "priority": 2,
      "url": "네이버 쇼핑 남성의류 URL",
      "estimated_products": 80000,
      "status": "pending"
    },
    {
      "id": 3,
      "name": "디지털/가전",
      "priority": 3,
      "url": "네이버 쇼핑 디지털/가전 URL",
      "estimated_products": 120000,
      "status": "pending"
    }
  ]
}
```

### crawl_settings.json
```json
{
  "crawling": {
    "start_index": 29,
    "batch_size": 10,
    "delay_between_products": 3,
    "captcha_wait_time": 20,
    "max_retries": 3,
    "retry_delay": 30
  },
  "schedule": {
    "category_duration_days": 7,
    "daily_start_hour": 0,
    "daily_end_hour": 23,
    "pause_on_error_threshold": 10
  },
  "monitoring": {
    "log_interval_minutes": 30,
    "checkpoint_interval_products": 100,
    "enable_email_alerts": false
  }
}
```

## 🔄 실행 흐름

### 1. 초기 시작
```bash
python3 automation_system/scheduler.py --mode start
```

**동작:**
1. `categories.json` 읽기
2. `crawl_progress` 테이블에서 현재 진행 중인 카테고리 확인
3. 없으면 첫 번째 카테고리(여성의류)로 시작
4. 있으면 중단된 지점부터 재개

### 2. 정상 실행 중
```
[12:00:00] 여성의류 카테고리 수집 중 (진행률: 35.2%)
[12:00:00] 현재 위치: 3520번째 상품
[12:00:00] 총 수집: 1540개 (검색태그 있는 상품)
[12:00:03] 3521번째 상품 수집 시작...
[12:00:05] ✓ 검색태그 8개 발견
[12:00:06] ✓ DB 저장 완료
[12:00:09] 3522번째 상품 수집 시작...
```

### 3. 캡차 발생
```
[12:05:00] ⚠️ 캡차 감지!
[12:05:00] ⏰ 20초 대기 중...
[사용자가 수동으로 캡차 해결]
[12:05:20] ✅ 캡차 해결 완료
[12:05:22] 크롤링 재개...
```

### 4. 오류 발생
```
[12:10:00] ❌ 오류 발생: 네트워크 타임아웃
[12:10:00] 재시도 1/3...
[12:10:30] ❌ 재시도 실패
[12:10:30] 재시도 2/3...
[12:11:00] ✅ 재시도 성공
[12:11:00] 크롤링 재개...
```

### 5. 카테고리 완료
```
[10월 22일 23:59:59] 여성의류 카테고리 수집 완료!
[10월 22일 23:59:59] 총 수집: 8,542개 상품
[10월 22일 23:59:59] 검색태그 있는 상품: 3,214개
[10월 22일 23:59:59] 다음 카테고리: 남성의류
[10월 23일 00:00:00] 남성의류 카테고리 수집 시작...
```

## 🛠️ 구현 우선순위

### Phase 1: 기본 자동화 (필수)
- [ ] `scheduler.py`: 메인 실행 루프
- [ ] `category_manager.py`: 카테고리 전환 로직
- [ ] `progress_tracker.py`: 진행 상황 추적
- [ ] DB 테이블 추가 (crawl_progress, error_logs)

### Phase 2: 안정성 강화 (중요)
- [ ] `error_handler.py`: 자동 재시도
- [ ] 로깅 시스템 (파일 + DB)
- [ ] 체크포인트 저장 (100개마다)

### Phase 3: 모니터링 (선택)
- [ ] 웹 대시보드 (Flask)
- [ ] 실시간 진행률 표시
- [ ] 이메일 알림

## 🚀 실행 방법

### 1. 최초 실행
```bash
# 1. DB 테이블 생성
psql -h localhost -U postgres -d naver -f database/add_progress_tables.sql

# 2. 카테고리 설정
vi automation_system/config/categories.json

# 3. 스케줄러 실행
python3 automation_system/scheduler.py --mode start
```

### 2. 중단 후 재개
```bash
python3 automation_system/scheduler.py --mode resume
```

### 3. 진행 상황 확인
```bash
python3 automation_system/scheduler.py --mode status
```

### 4. 카테고리 변경 (강제)
```bash
python3 automation_system/scheduler.py --change-category "남성의류"
```

## 📈 예상 성능

### 수집 속도
- **상품당 평균**: 8-12초 (스크롤 + 수집 + DB 저장)
- **시간당 수집**: 약 300-450개 상품
- **일일 수집**: 약 7,200-10,800개 상품 (24시간 기준)
- **주간 수집**: 약 50,000-75,000개 상품

### 검색태그 발견율
- **예상 발견율**: 30-40%
- **주간 검색태그 상품**: 약 15,000-30,000개

## ⚠️ 주의사항

1. **컴퓨터는 항상 켜져 있어야 함**
2. **캡차 발생 시 20초 이내에 해결 필요**
3. **네트워크 안정성 확보 (유선 권장)**
4. **디스크 공간 충분히 확보 (최소 50GB)**
5. **PostgreSQL 자동 시작 설정**

## 🔍 모니터링 포인트

### 정상 동작 확인
- 시간당 300개 이상 수집
- 오류율 5% 미만
- 캡차 발생 빈도 (시간당 1-2회 정상)

### 이상 징후
- 시간당 100개 미만 수집 → 네트워크 문제
- 오류율 20% 이상 → 봇 탐지 가능성
- 캡차 발생 빈도 증가 → 속도 조절 필요

## 📝 다음 단계

1. ✅ DB 저장 기능 완료
2. ⏳ `automation_system/` 폴더 생성 및 기본 스크립트 작성
3. ⏳ 진행 상황 추적 테이블 생성
4. ⏳ 메인 스케줄러 구현
5. ⏳ 카테고리 관리자 구현
6. ⏳ 테스트 실행 (1시간)
7. ⏳ 24시간 테스트 실행

---
*이 문서는 장기 수집 자동화 시스템의 설계 가이드입니다.*
