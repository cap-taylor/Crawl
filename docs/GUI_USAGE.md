# Multi-Task GUI 사용 가이드

## 실행 방법

### 방법 1: 직접 실행 (터미널 종료 시 GUI도 종료)
```bash
python3 product_collector_multi_gui.py
```

### 방법 2: 독립 실행 (터미널 닫아도 GUI 유지) ✅ 권장
```bash
bash scripts/run_multi_gui.sh
```

또는 nohup 직접 사용:
```bash
nohup python3 product_collector_multi_gui.py > logs/multi_gui.log 2>&1 &
```

---

## 터미널 독립성

### ✅ 개선 사항
- **SIGHUP 무시**: 터미널 닫아도 GUI 프로세스 유지
- **프로세스 그룹 독립**: 자식 프로세스(크롤러)도 독립 실행
- **로그 파일 저장**: `logs/multi_gui.log`에 모든 출력 기록

### 작동 원리
```
터미널 실행
  └─ GUI 프로세스 (독립)
       └─ 크롤러 프로세스 1 (독립)
       └─ 크롤러 프로세스 2 (독립)
       └─ 크롤러 프로세스 3 (독립)

터미널 닫기 → GUI 계속 실행 ✅
```

---

## 프로세스 확인

### GUI 실행 확인
```bash
ps aux | grep product_collector_multi_gui
```

### 실행 중인 크롤러 확인
```bash
ps aux | grep python3 | grep crawl
```

### 로그 실시간 확인
```bash
tail -f logs/multi_gui.log
```

---

## 종료 방법

### 정상 종료 (권장)
1. GUI 창의 [X] 버튼 클릭
2. 모든 작업이 자동으로 정리됨

### 강제 종료 (비상시)
```bash
# PID 확인
ps aux | grep product_collector_multi_gui

# 종료
kill <PID>

# 강제 종료 (응답 없을 때만)
kill -9 <PID>
```

### Firefox 좀비 프로세스 정리
```bash
pkill -f firefox
```

---

## 트러블슈팅

### 1. 터미널 닫으면 GUI도 닫힘
**원인**: 직접 실행 방식 사용
**해결**: `bash scripts/run_multi_gui.sh` 사용

### 2. 로그를 볼 수 없음
**원인**: 백그라운드 실행으로 stdout/stderr 리다이렉트됨
**해결**: `tail -f logs/multi_gui.log` 실행

### 3. GUI가 응답 없음
**원인**: 메모리 과부하 또는 크롤러 크래시
**해결**:
1. `ps aux | grep python3` → PID 확인
2. `kill <PID>` → 프로세스 종료
3. `pkill -f firefox` → 브라우저 정리
4. 재시작

### 4. 여러 GUI가 실행 중
**원인**: 중복 실행
**해결**:
```bash
ps aux | grep product_collector_multi_gui
kill <PID1> <PID2> ...
```

---

## 권장 사용 패턴

### 장시간 크롤링 (무한 모드)
1. `bash scripts/run_multi_gui.sh` 실행
2. 카테고리 추가 (무한 모드 선택)
3. 시작 버튼 클릭
4. 터미널 닫기 ✅
5. 나중에 GUI 창으로 확인

### 단기 테스트
1. `python3 product_collector_multi_gui.py` 직접 실행
2. 카테고리 추가 (20-50개 지정)
3. 시작 버튼 클릭
4. 터미널에서 실시간 로그 확인

---

## 디버깅 정보

### 오류 발생 시 확인 사항
```
[치명적 오류 발생]
================================================================================
오류 메시지: <에러 메시지>
수집 상태: X개 수집 완료
스크롤: Y회
마지막 상품 ID: ZZZZ

상세 스택 트레이스:
<파이썬 traceback>

복구 방법:
  1. DB에 X개 저장됨 (중복 체크로 재시작 가능)
  2. 브라우저를 수동으로 닫으세요
  3. 프로그램을 다시 시작하세요
================================================================================
```

### 리소스 정리 확인
```
[정리] 브라우저 종료 중...
[정리] 브라우저 종료 완료
[DB] 세션 완료 기록
[정리] 모든 리소스 정리 완료
```

---

## 파일 구조

```
Crawl/
├── product_collector_multi_gui.py  # 멀티 태스크 GUI
├── scripts/
│   └── run_multi_gui.sh            # 독립 실행 스크립트
├── logs/
│   └── multi_gui.log               # GUI 로그 (자동 생성)
└── docs/
    └── GUI_USAGE.md                # 이 파일
```

---

## 주의 사항

1. **메모리 관리**: 무한 모드는 10개마다 자동 저장 (메모리 누수 방지)
2. **봇 차단**: 네이버 캡차 나오면 수동 해결 (15초 대기)
3. **중복 수집**: DB 중복 체크로 이미 수집한 상품은 자동 스킵
4. **프로세스 정리**: 종료 시 Firefox 프로세스 수동 확인 권장

---

**Last Updated**: 2025-10-30
