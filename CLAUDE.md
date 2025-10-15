# 🎯 Crawl 프로젝트 - Claude 필수 지침
> Last Updated: 2025-10-15 19:56


## 🔴 **절대 금지 (NEVER DO THIS)**

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

## 🔢 **버전 관리 (VERSION)**

### 버전 번호 규칙 (Semantic Versioning)
`MAJOR.MINOR.PATCH` 형식 (예: 1.2.3)

**언제 올리나?**
- **MAJOR (1.x.x)**: 큰 변화, 호환성 깨짐 (예: 전체 구조 변경)
- **MINOR (x.1.x)**: 새 기능 추가 (예: 카테고리 선택 기능)
- **PATCH (x.x.1)**: 버그 수정, 작은 개선 (예: 한글 깨짐 수정)

### 버전 업데이트 절차

1. **VERSION 파일 수정**
   ```bash
   echo "1.0.2" > VERSION
   ```

2. **변경사항 확인**
   - MAJOR: 전체 재작성, DB 스키마 변경, API 변경
   - MINOR: 카테고리 선택, 무한 수집, GUI 업그레이드
   - PATCH: 한글 깨짐, 버그 수정, 문서 업데이트

3. **자동 반영**
   - `run_crawler.ps1`이 VERSION 파일 읽어서 자동 표시
   - Git 커밋 메시지에 버전 포함

### 최근 버전 히스토리
- **1.1.3**: 상품 수집 안정성 대폭 개선 (버그 수정)
  - NoneType 에러 완전 해결 (상품명 검증 로직 추가)
  - 카테고리 경로 정리 강화 (이모지, "(총 X개)" 패턴 제거)
  - 잘못된 페이지 자동 스킵 (상품명 없으면 수집 안 함)
  - DB 커넥터 수정 (detail_info 우선 사용)
  - 절대 에러 없이 정상 상품만 수집
- **1.1.2**: 카테고리 경로 수집 완성 (버그 수정)
  - JSHandle 오류 수정 (Locator API + XPath 사용)
  - 텍스트 정리 강화 (개행 문자 제거)
  - 구조 기반 breadcrumb 수집 (Multi-Fallback 전략)
  - category_fullname 필드 정상 수집 (예: "하의 > 바지 & 슬렉스")
- **1.1.1**: 네이버 메인 페이지 네비게이션 수정 (버그 수정)
  - networkidle → domcontentloaded 변경 (타임아웃 해결)
  - 쇼핑 버튼 클릭 전 상단 스크롤 추가
  - Locator API 사용으로 안정성 향상
  - specific_index 파라미터로 특정 상품만 수집 가능
- **1.1.0**: 셀렉터 시스템 전체 리팩토링 (구조 기반 + 다중 fallback)
  - selector_helper.py 생성 (재사용 가능한 셀렉터 로직)
  - config.py 개선 (모든 셀렉터 리스트화, 우선순위 정의)
  - 네이버 난독화 대응 (클래스명 변경에 강건)
  - DB 스키마 전체 필드 수집 (brand_name, rating, is_sold_out 추가)
- **1.0.4**: GUI 로그 한글 깨짐 수정 (remove_emojis 함수)
- **1.0.3**: GUI 개선 (로그 복사 버튼, 중지 버튼 수정, 로그 간결화)
- **1.0.2**: PowerShell 한글 깨짐 수정, 콘솔 디버깅 강화
- **1.0.1**: 카테고리 선택 기능 추가 (40개 카테고리)
- **1.0.0**: 초기 릴리즈 (여성의류 수집)

---

## 🟡 **환경 설정**

### WSL Ubuntu
- Python: `python3` (NOT `python`)
- 경로: `/home/dino/MyProjects/Crawl`
- Windows 접근: `\\wsl.localhost\Ubuntu-22.04\home\dino\MyProjects\Crawl`

### PostgreSQL 데이터베이스
- **데이터베이스명**: naver
- **사용자**: postgres
- **비밀번호**: `.env` 파일에서 `DB_PASSWORD` 설정
- **테이블**: categories, products, crawl_history

### 데이터베이스 스키마 구조
**중요**: SQL 스키마 파일(`database/create_tables.sql`)은 실제 DB 구조와 동기화됨

**categories 테이블**:
- `category_name` VARCHAR(100) PRIMARY KEY (예: "여성의류")
- `category_id` VARCHAR(20) (네이버 ID, 예: "10000107")
- `is_active` BOOLEAN DEFAULT false
- `created_at` TIMESTAMP

**products 테이블**:
- `product_id` VARCHAR(255) PRIMARY KEY
- `category_name` VARCHAR(100) (**FK 없음** - 단순 참조)
- `product_name`, `brand_name`, `price`, `discount_rate`
- `review_count`, `rating`, `search_tags TEXT[]`
- `product_url`, `thumbnail_url`, `is_sold_out`
- `crawled_at`, `updated_at`

**설계 특징**:
- ❌ Foreign Key 제약 조건 없음 (유연성 우선)
- ✅ `category_name`으로 직접 조인
- ✅ `search_tags`는 PostgreSQL 배열 타입

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