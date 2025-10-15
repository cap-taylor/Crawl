# 배포 가이드 - 새 노트북에서 상품 수집 GUI 실행하기

> **목적**: 새로운 컴퓨터에서 네이버 쇼핑 상품 수집 GUI를 쉽게 설치하고 실행하기

---

## 📋 사전 요구사항

### 1. Python 3.10 이상 설치
- **다운로드**: https://www.python.org/downloads/
- **설치 시 주의**:
  - ✅ "Add Python to PATH" 체크박스 **반드시 선택**
  - ✅ "Install pip" 옵션 포함
  - 설치 후 확인: 명령 프롬프트에서 `python --version` 실행

### 2. PostgreSQL 데이터베이스 (DB 저장 사용 시)
- **다운로드**: https://www.postgresql.org/download/
- 설치 시 비밀번호 설정 (나중에 `.env` 파일에 입력 필요)

### 3. Git (선택사항)
- 프로젝트를 GitHub에서 클론할 경우 필요
- **다운로드**: https://git-scm.com/downloads/

---

## 🚀 설치 방법

### 방법 1: GitHub에서 클론 (추천)

```bash
# 1. 프로젝트 클론
git clone https://github.com/your-username/Crawl.git
cd Crawl

# 2. 초기 설정 실행
cd scripts
setup.bat
```

### 방법 2: ZIP 파일로 배포

1. 프로젝트 폴더를 USB 또는 클라우드로 복사
2. 압축 해제
3. `scripts` 폴더로 이동
4. `setup.bat` 더블클릭 실행

---

## ⚙️ 초기 설정 (setup.bat)

`scripts/setup.bat`를 실행하면 자동으로:

1. ✅ Python 설치 확인
2. ✅ 필요한 Python 패키지 설치 (customtkinter, playwright 등)
3. ✅ Playwright Firefox 브라우저 설치
4. ✅ `.env` 파일 생성 (`.env.example`에서 복사)

### 설정 완료 후 필수 작업

1. `.env` 파일 열기 (프로젝트 루트 폴더)
2. `DB_PASSWORD` 값 수정:
   ```
   DB_PASSWORD=your_actual_password_here
   ```
3. 저장 후 닫기

---

## 🎮 GUI 실행 방법

### Windows

1. `scripts` 폴더로 이동
2. `run_gui.bat` 더블클릭
3. GUI 창이 열리면 설정 후 "수집 시작" 클릭

### Linux/WSL

```bash
cd /home/dino/MyProjects/Crawl
python3 product_collector_gui.py
```

---

## 🖥️ GUI 사용 방법

### 1. 설정

| 항목 | 설명 | 기본값 |
|------|------|--------|
| **수집 상품 개수** | 수집할 상품 수 (1개 이상) | 20 |
| **JSON 파일로 저장** | `data/` 폴더에 JSON 파일 저장 | ✅ 체크 |
| **DB에 저장** | PostgreSQL DB에 저장 | ✅ 체크 |
| **중복 상품 건너뛰기** | DB에 이미 있는 상품 스킵 (DB 저장 시에만) | ✅ 체크 |

### 2. 수집 시작

1. "수집 시작" 버튼 클릭
2. Firefox 브라우저 자동 실행
3. 실시간 로그에서 진행 상황 확인

### 3. 캡차 해결 (중요!)

- **캡차가 나타나면**:
  1. 로그에 "캡차 감지" 메시지 표시
  2. Firefox 브라우저에서 **수동으로 캡차 입력**
  3. 30초 동안 대기 후 자동 재개

### 4. 수집 완료

- JSON 파일 저장 위치: `data/womens_products_YYYYMMDD_HHMMSS.json`
- DB 저장 결과: 로그에 신규/중복/실패 개수 표시
- 브라우저 자동 닫힘 (30초 후)

---

## 🗂️ 파일 구조

```
Crawl/
├── product_collector_gui.py    # GUI 메인 파일
├── requirements.txt             # Python 패키지 목록
├── .env                         # 환경 변수 (DB 비밀번호)
├── .env.example                 # 환경 변수 템플릿
├── scripts/
│   ├── setup.bat                # 초기 설정 스크립트 (Windows)
│   └── run_gui.bat              # GUI 실행 스크립트 (Windows)
├── src/
│   ├── database/
│   │   └── db_connector.py      # DB 연결 및 저장
│   └── utils/
│       └── config.py            # 설정 파일
├── tests/
│   └── test_womens_manual_captcha.py  # 크롤러 핵심 로직
└── data/                        # 수집된 JSON 파일 저장
```

---

## ❓ 문제 해결 (Troubleshooting)

### 1. "Python is not installed" 오류

**원인**: Python PATH 설정 안 됨

**해결**:
1. Python 재설치 시 "Add Python to PATH" 체크
2. 또는 수동으로 PATH 추가:
   - 시스템 환경 변수 → Path → 편집
   - Python 설치 경로 추가 (예: `C:\Python310\`)

### 2. "DB_PASSWORD 환경변수가 설정되지 않았습니다" 오류

**원인**: `.env` 파일에 DB 비밀번호 미설정

**해결**:
1. `.env` 파일 열기
2. `DB_PASSWORD=your_password_here` 수정
3. 저장 후 재실행

### 3. Playwright 브라우저 오류

**원인**: Firefox 브라우저 미설치

**해결**:
```bash
playwright install firefox
```

### 4. GUI 창이 안 열림 (WSL)

**원인**: WSL에서 GUI 실행 불가

**해결**:
- Windows에서 직접 실행 (`scripts/run_gui.bat`)
- 또는 WSLg 설정 (Windows 11)

### 5. customtkinter 이모지 깨짐

**원인**: customtkinter는 이모지 렌더링 불가

**해결**: 자동 처리됨 (코드에 `remove_emojis()` 함수 포함)

---

## 🔄 업데이트 방법

### Git 사용 시

```bash
cd Crawl
git pull origin main
pip install -r requirements.txt --upgrade
```

### 수동 업데이트

1. 새 버전 파일 다운로드
2. 기존 `.env` 파일 백업
3. 프로젝트 폴더 교체
4. `.env` 파일 복원
5. `scripts/setup.bat` 재실행

---

## 📊 데이터 확인

### JSON 파일

```bash
# 최신 JSON 파일 확인
cd data
dir /O:-D  # Windows
ls -lt     # Linux
```

### DB 확인

```bash
# PostgreSQL 접속
psql -U postgres -d naver

# 상품 개수 확인
SELECT COUNT(*) FROM products;

# 최근 수집 상품 확인
SELECT product_name, crawled_at FROM products ORDER BY crawled_at DESC LIMIT 10;
```

---

## 🛡️ 보안 주의사항

1. **절대 Git에 커밋하지 마세요**:
   - `.env` 파일
   - `data/*.json` 파일 (개인정보 포함 가능)

2. **DB 비밀번호 관리**:
   - 강력한 비밀번호 사용
   - `.env` 파일 권한 제한 (Linux: `chmod 600 .env`)

3. **크롤링 윤리**:
   - 과도한 요청으로 서버 부하 주지 않기
   - 네이버 쇼핑 이용약관 준수

---

## 📞 지원

- **프로젝트 문서**: `docs/` 폴더 참조
- **코드 가이드**: `CLAUDE.md` 참조
- **개발 노트**: `docs/CRAWLING_LESSONS_LEARNED.md` 참조

---

**버전**: 1.0
**최종 업데이트**: 2025-10-15
