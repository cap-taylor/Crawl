# 🎯 Crawl 프로젝트 - Claude 필수 지침
> Last Updated: 2025-11-03 21:12


## 🔴 **절대 금지 (NEVER DO THIS)**

### 🚨 크롤링 문제 해결 (최우선!)
**크롤링 관련 문제 발생 시 무조건 문서부터!**
- ❌ **바로 코드 수정 시도 금지** → 시행착오 반복!
- ✅ **반드시 먼저 확인**: `docs/CRAWLING_LESSONS_LEARNED.md`
- ✅ **Grep 검색**: 키워드로 문서 내 해결책 찾기

**문서에 이미 있는 해결책들**:
- 네이버 메인 → 쇼핑 진입 방법 (셀렉터, Locator API)
- 캡차 회피 전략
- 새 탭 전환 패턴
- networkidle vs domcontentloaded
- 모든 에러 케이스별 해결 방법

**이 규칙을 어기면**: 사용자가 짜증남 → "시행착오 문서를 왜 만들었냐"

---

### 코드 품질
- 오버 엔지니어링 절대 금지(간단한 것을 복잡하게 만들지마)
- 기존 파일로 해결 가능한데 새 파일 생성
- 파일명에 `_new`, `_old`, `_v2` 같은 버전 표시
- `test_*.py`를 루트에 생성 → `tests/` 폴더에만

### 보안/안전
- 비밀번호/API키 하드코딩 → `.env` 사용
- `.env` Git 커밋
- Windows 경로(/mnt/c/) 직접 작업 → 성능 저하



### 프로세스
- 백그라운드 프로세스 방치 → 완료 시 `KillShell`
- 날짜/시간 추측 → 반드시 `<env>` 태그 또는 `date` 명령 확인
- 문서 업데이트 없이 Git 백업

### 한글/이모지
- `.bat`/`.ps1` 파일에 한글/이모지 → 깨짐
- Python 로그 메시지에 이모지 → customtkinter 렌더링 불가




## 🧠 **핵심 마인드셋 (읽고 시작!)**
1. **점진적 개선**: 완벽한 것보다 작동하는 것 먼저 → MVP → 보완 (처음부터 100점 노리지 말 것!)
2. **사용자 이해**: 한국인 개발 초보자 → 중학생 수준으로 자세히 설명
3. **확인 후 실행**: 기능 추가 전 "꼭 필요한가?" / 파일 생성 전 "기존에 없나?"
4. **실수 인정**: 틀리면 빠르게 고치기 (변명 NO, 해결 YES)

---


## 📌 **필수 원칙 (MUST FOLLOW)**

### 🏗️ 레이어 분리 (Separation of Concerns)
**왜 중요한가?** Claude 토큰 절약 + 코드 독립성


**규칙:**
- ✅ `collection/` 작업 시 `optimization/` 읽지 않기
- ✅ 레이어 간 의존성은 `→ core` 방향만 (순환 금지)
- ✅ 새 기능: 관심사 다르면 새 레이어, 같으면 기존 레이어 확장

### 📁 파일 조직
- **테스트**: `tests/test_*.py` (루트 금지!)
- **스크립트**: `scripts/*.bat|sh|ps1`
- **임시**: `temp/` (사용 후 즉시 삭제)
- **루트**: 최소 파일만 (gui_app.py, config.py 등)

### 🔄 작업 패턴
1. **읽기 우선**: Edit/Write 전 반드시 Read
2. **수정 우선**: 새 파일 생성보다 기존 파일 수정
3. **확인 필수**: 클래스명 확인 (예: `db_manager.py` → `DBManager` 클래스)

### 📅 날짜/시간 처리
- **날짜**: `<env>` 태그의 "Today's date" 확인
- **시간**: `date '+%Y-%m-%d %H:%M'` 실행
- **금지**: 추측 금지! (2025-01-09가 아니라 2025-10-02일 수 있음)


---

## 🔄 **Git 백업 규칙 (중요!)**

### ✅ Git 커밋이 허용되는 경우
**명시적 백업 요청이 있을 때만:**
- "백업해줘"
- "체크포인트"
- "깃허브 올려줘"

**자동 실행 순서**:
1. 모든 문서 업데이트 (CLAUDE.md, PROJECT_GUIDELINES.md, docs/*.md)
2. 타임스탬프 갱신 (`date '+%Y-%m-%d %H:%M'`)
3. Git 커밋 (메시지: "체크포인트: [변경사항]")
4. GitHub 푸시
5. CHECKPOINT.md 업데이트 (커밋 해시 추가)

### ❌ Git 커밋 절대 금지
**파일 수정만 요청된 경우:**
- "업데이트해"
- "수정해"
- "고쳐줘"
- "버전 올려줘"

**→ 파일 수정만 하고 Git 커밋/푸시 절대 금지!**

**위반 시:** 사용자가 불만 표시 ("백업해달라고 안했는데 왜 자꾸 커밋 되는거야?")

---

## 🔢 **버전 관리 (VERSION) - 자동 업그레이드**

### 🚨 중요: 버전 자동 업데이트 규칙

**Git 백업 시 항상 PATCH 버전 자동 증가!**
- "백업해줘", "체크포인트", "깃허브 올려줘" 요청 시
- PATCH 버전을 자동으로 +1 증가 (1.2.3 → 1.2.4)
- 백업 전에 VERSION 파일 자동 업데이트
- 사용자가 별도 요청하지 않아도 자동 실행

**예외: 수동 버전 지정**
- 사용자가 명시적으로 버전 지정 시 (예: "2.0.0으로 올려줘")
- MAJOR/MINOR 업그레이드는 수동 지정 필요

### 버전 번호 규칙 (Semantic Versioning)
`MAJOR.MINOR.PATCH` 형식 (예: 1.2.4)

**언제 올리나?**
- **MAJOR (1.x.x)**: 큰 변화, 호환성 깨짐 (예: 전체 구조 변경) - 수동
- **MINOR (x.1.x)**: 새 기능 추가 (예: 카테고리 선택 기능) - 수동
- **PATCH (x.x.1)**: 버그 수정, 작은 개선, 문서 업데이트 - **자동**

### 자동 버전 업데이트 절차 (Git 백업 시)

1. **현재 버전 읽기**
   ```bash
   cat VERSION  # 예: 1.2.3
   ```

2. **PATCH 버전 자동 증가**
   ```bash
   # 1.2.3 → 1.2.4로 자동 변경
   echo "1.2.4" > VERSION
   ```

3. **자동 반영 위치**
   - ✅ `VERSION` 파일 (단일 진실의 원천)
   - ✅ `run_crawler.ps1` → PowerShell 터미널 헤더
   - ✅ `product_collector_gui.py` → GUI 창 타이틀, 서브타이틀
   - ✅ Git 커밋 메시지 (백업 시)

4. **백업 순서** (자동 실행)
   ```
   VERSION 파일 업데이트 (PATCH +1)
   ↓
   모든 문서 타임스탬프 갱신
   ↓
   Git 커밋 (새 버전 포함)
   ↓
   GitHub 푸시
   ↓
   CHECKPOINT.md 업데이트
   ```

**🔧 구현 방식**:
- `run_crawler.ps1`: PowerShell `Get-Content` 읽기
- `product_collector_gui.py`: Python `get_version()` 함수
- Git 백업 시 자동 버전 증가 스크립트 실행

**📋 전체 버전 히스토리**: `CHANGELOG.md` 참조

**💡 예시**:
```bash
# 사용자: "백업해줘"
# Claude 자동 실행:
1. cat VERSION → 1.2.3 읽음
2. echo "1.2.4" > VERSION → PATCH +1
3. git add . && git commit -m "체크포인트: 중복 체크 개선 (v1.2.4)"
4. git push
```

---

## 🟡 **환경 설정**

### WSL Ubuntu
- Python: `python3` (NOT `python`)
- 경로: `/home/dino/MyProjects/Crawl`
- Windows 접근: `\\wsl.localhost\Ubuntu-22.04\home\dino\MyProjects\Crawl`

### 바로가기 (고정 - 절대 변경 금지!)
**Windows 바탕화면 바로가기 경로:**
```
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy Bypass -File "\\wsl.localhost\Ubuntu-22.04\home\dino\MyProjects\Crawl\run_crawler.ps1"
```

**중요:**
- 바로가기 경로는 고정 (변경하지 말 것!)
- GUI 업데이트 시 `run_crawler.ps1` 파일만 수정
- 현재 실행 파일: `product_collector_gui.py` (SimpleCrawler 기반)
- 핵심 크롤러: `src/core/simple_crawler.py` (13개 필드 수집, DB 직접 저장)

### PostgreSQL 데이터베이스
- **데이터베이스명**: naver
- **사용자**: postgres
- **비밀번호**: `.env` 파일에서 `DB_PASSWORD` 설정
- **테이블**: categories, products, crawl_history

### 데이터베이스 스키마 구조 (v1.1.0 - 2025-11-03)
**중요**: SQL 스키마 파일(`database/create_tables.sql`)은 실제 DB 구조와 동기화됨

**categories 테이블**:
- `category_name` VARCHAR(100) PRIMARY KEY (예: "여성의류")
- `category_id` VARCHAR(20) (네이버 ID, 예: "10000107")
- `is_active` BOOLEAN DEFAULT false
- `created_at` TIMESTAMP

**products 테이블 (13개 필드)**:
- `product_id` VARCHAR(255) PRIMARY KEY
- `category_name` VARCHAR(100) [1순위] (**FK 없음** - 단순 참조)
- `product_name` TEXT NOT NULL [1순위]
- `search_tags` TEXT[] [1순위] (PostgreSQL 배열)
- `price` INTEGER [2순위]
- `rating` DECIMAL(2,1) [2순위] (0.0~5.0)
- `product_url` TEXT [2순위]
- `thumbnail_url` TEXT [2순위]
- `brand_name` VARCHAR(100) [3순위]
- `discount_rate` INTEGER [3순위]
- `review_count` INTEGER [3순위]
- `crawled_at` TIMESTAMP [3순위]
- `updated_at` TIMESTAMP [3순위]

**설계 특징 (v1.1.0)**:
- ❌ Foreign Key 제약 조건 없음 (유연성 우선)
- ✅ `category_name`으로 직접 조인
- ✅ `search_tags`는 PostgreSQL 배열 타입
- ✅ **is_sold_out 제거** (현재 판매 상품만 존재하므로 불필요)
- ✅ 우선순위별 필드 분류 (1순위 핵심 → 2순위 중요 → 3순위 부가)

---

## 🐛 **알려진 이슈**

### 이모지 렌더링
- **문제**: customtkinter가 이모지 못 읽음 → 네모박스(□)
- **해결**: `gui_app.py:617-673` `remove_emojis()` 함수
- **사용 규칙**:
  - ✅ Markdown, Git 커밋, 주석
  - ❌ Python 로그, GUI 출력, .bat/.ps1

### CHECKPOINT.md 자동 수정
- IDE가 자동 수정 → Edit 후 ENOENT 에러 무시
- 커밋 후 해시 추가: `84c801a - 2025-10-02 22:15 : 체크포인트: [설명]`

### 인코딩
- .bat/.ps1 파일: 영어만 (한글 → 깨짐)
- 증상: '쒖씠', '┰???ㅽ뻉'
### GUI 창이 작업표시줄에만 나타나는 문제 (2025-10-31)
**증상**:
- 바탕화면 바로가기 실행 시 창이 화면에 안 나타남
- 작업 표시줄에만 아이콘 보임
- Alt+Tab으로도 찾을 수 없음

**원인**:
- customtkinter 5.2.0 + WSLg (Windows 11) 호환성 문제
- WSLg 창 관리 캐시 충돌

**해결 (3단계)**:
1. **customtkinter 다운그레이드**:
   ```bash
   pip3 install customtkinter==5.1.3
   ```

2. **WSL 재시작 (PowerShell)**:
   ```powershell
   wsl --shutdown
   ```

3. **바탕화면 바로가기 다시 실행**

**예방**:
- `requirements.txt` 사용: `pip3 install -r requirements.txt`
- customtkinter 5.1.3 버전 고정 유지

**상세**: `docs/CRAWLING_LESSONS_LEARNED.md` 참조

---

## 📦 **의존성 관리**

### requirements.txt
프로젝트 루트에 `requirements.txt` 파일로 의존성 관리:

```bash
pip3 install -r requirements.txt
```

**중요**:
- `customtkinter==5.1.3` 버전 고정 (WSLg 호환성)
- 버전 업그레이드 시 반드시 테스트 후 적용
