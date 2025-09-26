# 네이버 쇼핑 크롤링 시행착오 문서

> 이 문서는 네이버 쇼핑 크롤링 개발 과정에서 겪은 모든 시행착오와 해결책을 기록합니다.
> **절대 같은 실수를 반복하지 않기 위한 필수 참고 문서입니다.**

## 📅 최종 업데이트: 2025-09-26

---

## ⛔ 네이버 쇼핑 API 관련 (절대 사용 금지)

### 네이버 쇼핑 API를 사용하면 안 되는 이유 (2025-09-26)
**중요**: 네이버 쇼핑 API는 **절대 사용 금지!**

### API가 제공하는 데이터 (매우 제한적)
네이버 쇼핑 검색 API는 다음 필드만 제공:
- `title`: 상품명 (HTML 태그 포함된 간단한 제목)
- `link`: 네이버 쇼핑 상품 링크
- `image`: 썸네일 이미지 URL (1개)
- `lprice`: 최저가
- `hprice`: 최고가
- `mallName`: 판매 쇼핑몰명
- `productId`: 상품 ID
- `productType`: 상품 타입 번호
- `brand`: 브랜드명
- `maker`: 제조사
- `category1~4`: 카테고리 분류

### 크롤링으로만 얻을 수 있는 중요 정보
API로는 절대 얻을 수 없는 필수 정보들:
- ❌ **리뷰 개수와 평점** (구매 결정 핵심 요소)
- ❌ **실제 할인율** (%)
- ❌ **배송 정보** (무료배송, 로켓배송 등)
- ❌ **쿠폰 및 혜택 정보**
- ❌ **판매자별 가격 비교**
- ❌ **재고 상태** (품절, 한정수량)
- ❌ **인기도/판매량 순위**
- ❌ **상품 옵션** (색상, 사이즈 등)
- ❌ **상세 이미지들** (여러 장)
- ❌ **상품 상세 설명**
- ❌ **찜 개수**
- ❌ **구매 문의 내용**
- ❌ **상세 스펙 정보**
- ❌ **연관/추천 상품**
- ❌ **베스트 상품 순위**
- ❌ **시간별 가격 변동**
- ❌ **프로모션 배지** (베스트, 신상품 등)

### 검증 결과 (2025-09-26)
- 테스트 파일: `/tests/test_naver_api.py`
- API는 단순 검색 결과만 제공
- 실제 쇼핑몰 운영에 필요한 데이터 90% 이상 누락

**결론**:
- ❌ 네이버 쇼핑 API 사용 금지 (데이터 부족)
- ✅ 반드시 웹 크롤링으로 완전한 데이터 수집

---

## 🚫 봇 차단 관련

### 메인 페이지 접속 테스트 결과 (2025-09-26)
**테스트 파일**: `/tests/test_main_page_access.py`

**테스트한 4가지 방법**:
1. **기본 접속** → ❌ 보안 검증 페이지
2. **User-Agent 설정** → ❌ 여전히 보안 검증
3. **Stealth 모드** → ❌ 감지됨
4. **단계적 접근 (네이버 메인 → 쇼핑)** → ❌ 타임아웃

**실패 원인 분석**:
- 네이버의 봇 감지 시스템이 매우 강력함
- 기본적인 Stealth 설정으로는 우회 불가능
- User-Agent 변경만으로는 부족
- 네이버 메인에서 클릭 방식도 차단됨

**다음 시도할 방법들**:
- 실제 Chrome 프로필 사용 (쿠키, 히스토리 포함)
- 더 정교한 Stealth 설정 (플러그인, 언어, 시간대 등)
- 실제 사용자 행동 모방 (마우스 움직임, 랜덤 딜레이)
- Firefox나 WebKit 브라우저 테스트

### 🎉 성공한 접속 방법! (2025-09-26)
**테스트 파일**: `/tests/test_advanced_access.py`

**성공한 2가지 방법**:
1. ✅ **완전한 Stealth 설정 (Chromium)**
   - 모든 봇 감지 속성 제거
   - WebGL, Canvas Fingerprint 방지
   - Chrome 객체, 플러그인 추가
   - 성공 스크린샷: `tests/advanced_success.png`

2. ✅ **Firefox 브라우저**
   - 기본 Firefox로 접속 성공
   - 별도 Stealth 설정 불필요

**핵심 Stealth 스크립트** (반드시 포함):
```javascript
// webdriver 제거
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// chrome 객체 추가
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {}
};

// plugins 추가
Object.defineProperty(navigator, 'plugins', {
    get: () => [/* 플러그인 배열 */]
});

// languages 설정
Object.defineProperty(navigator, 'languages', {
    get: () => ['ko-KR', 'ko', 'en-US', 'en']
});

// platform 설정
Object.defineProperty(navigator, 'platform', {
    get: () => 'Win32'
});
```

**적용 방법**:
- Chromium: 완전한 Stealth 스크립트 필수
- Firefox: 그냥 사용해도 됨!

### 네이버 메인 vs 쇼핑 접속 차이 (2025-09-26)
**중요 발견**:
- ✅ `naver.com` → 정상 접속 (캡차 없음)
- ❌ `shopping.naver.com/ns/home` → 캡차 발생

**원인 분석**:
- 네이버 쇼핑은 직접 접속 시 봇 감지가 더 엄격함
- 네이버 메인에서 시작하면 정상 사용자로 인식

**해결 방법**:
1. 네이버 메인(`naver.com`) 먼저 접속
2. 쇼핑 탭 클릭으로 이동
3. 또는 캡차 자동 해결 기능 구현

### ⚠️ 절대 규칙: 클릭으로만 이동! (2025-09-26)
**중요**:
- ❌ **절대 직접 URL 접속 금지**: `await page.goto("shopping.naver.com")` → 캡차!
- ✅ **반드시 클릭으로 이동**: 네이버 메인 → 쇼핑 클릭
- ⚠️ **브라우저 중복 실행 금지**: 이미 열려있으면 그곳에서 작업

**올바른 접근 순서**:
```python
# 1. 브라우저가 이미 열려있는지 확인
# - 현재 URL이 https://www.naver.com/ 인지 체크
# - 열려있으면 그 브라우저에서 계속 작업

# 2. 없을 때만 새 브라우저 실행
if not browser_exists:
    browser = await p.chromium.launch(headless=False)
    await page.goto("https://www.naver.com")

# 3. 쇼핑 아이콘 클릭 (selector 사용)
shopping_link = await page.query_selector("#shortcutArea > ul > li:nth-child(4) > a")
await shopping_link.click()
```

**절대 하지 말 것**:
```python
# ❌ 이렇게 하면 캡차 발생!
await page.goto("https://shopping.naver.com/ns/home")

# ❌ 브라우저가 이미 열려있는데 또 새로 실행
browser = await p.chromium.launch()  # 중복 실행 금지!
```

---

## 🚫 봇 차단 관련

### 1. Headless 모드 차단 (2025-09-26)
**문제**:
- Headless 모드(브라우저 숨김)로 실행 시 네이버가 즉시 차단
- HTTP 405 에러 또는 "점검 중" 페이지로 리다이렉트

**테스트 결과**:
```python
# headless=True → 405 에러, 차단됨
# headless=False → 405 에러 (자동화 감지)
```

**결론**:
- ❌ **절대 Headless 모드 사용 금지**
- ❌ 백그라운드 실행 옵션 제거됨
- ✅ 항상 브라우저 창이 보이는 상태로만 실행

**증거**:
- 테스트 파일: `/tests/test_headless.py`
- 405 에러 = 네이버가 자동화 브라우저 감지
- "점검 중" 페이지 = 차단된 것

---

### 2. URL 접근 방식 (2025-09-26)
**문제**:
- 잘못된 URL 사용 시 차단
- 직접 카테고리 URL 접근 시 차단

**올바른 접근**:
```python
# ✅ 정확한 URL (반드시 이것만 사용)
base_url = 'https://shopping.naver.com/ns/home'

# ❌ 잘못된 URL들 (차단됨)
# 'https://shopping.naver.com/'  → 302 리다이렉트 → 차단
# 'https://shopping.naver.com/home'  → 405 에러
```

**규칙**:
1. 반드시 메인 페이지(`/ns/home`)에서 시작
2. 카테고리는 클릭으로만 이동
3. 절대 카테고리 URL 직접 접근 금지

---

## 🔤 인코딩 및 폰트 문제

### 1. WSL GUI 한글 깨짐 (2025-09-26)
**문제**:
- WSL + X11 환경에서 tkinter GUI 한글 깨짐
- 윈도우 타이틀바 한글 깨짐

**해결책**:
1. **한글 폰트 설치** (필수):
   ```bash
   sudo apt install fonts-nanum fonts-noto-cjk fonts-noto-cjk-extra
   sudo fc-cache -f -v
   ```

2. **코드 수정**:
   ```python
   # 한글 폰트명 → 영문 폰트명
   # font=('맑은 고딕', 12) → font=('Arial', 12)
   # 또는 시스템 기본 폰트 사용
   font=('TkDefaultFont', 12)
   ```

3. **윈도우 타이틀 영문 사용**:
   ```python
   # 한글 타이틀 깨짐
   root.title("네이버 쇼핑 크롤러")  # ❌ 깨짐
   root.title("Naver Shopping Crawler")  # ✅ 정상
   ```

**설치 스크립트**: `/scripts/install_korean_fonts.sh`

---

## 🛠️ 환경 설정

### 1. tkinter 설치 (2025-09-26)
**문제**: WSL에 tkinter 미설치로 GUI 실행 불가

**해결**:
```bash
sudo apt update
sudo apt install python3-tk
```

**설치 스크립트**: `/scripts/install_tkinter.sh`

---

### 2. Playwright 설정
**필수 설정** (봇 감지 회피):
```python
# Stealth 모드 설정 - 반드시 포함
await context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5]
    });
    Object.defineProperty(navigator, 'languages', {
        get: () => ['ko-KR', 'ko']
    });
""")

# User-Agent 설정
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
```

---

## 📝 개발 규칙

### 1. 버전 관리
- **Semantic Versioning** 사용: `MAJOR.MINOR.PATCH`
- VERSION 파일에서 버전 읽기
- 모든 변경사항은 CHANGELOG.md에 기록

### 2. 파일 구조
- 테스트 파일은 반드시 `tests/` 폴더에
- 스크립트는 `scripts/` 폴더에
- 루트 디렉토리에 임시 파일 생성 금지

---

## ⚠️ 주의사항 체크리스트

크롤링 전 반드시 확인:

- [ ] URL이 `https://shopping.naver.com/ns/home`인가?
- [ ] Headless 모드 비활성화 되어있나?
- [ ] Stealth 모드 스크립트 포함되어 있나?
- [ ] 랜덤 대기 시간(2-5초) 설정되어 있나?
- [ ] User-Agent 설정되어 있나?

---

## 📚 참고 파일

- 설정 파일: `/src/utils/config.py`
- 크롤러 코드: `/src/core/crawler.py`
- GUI 코드: `/src/gui/main_window.py`
- 테스트 코드: `/tests/test_headless.py`

---

## 🔄 업데이트 로그

| 날짜 | 내용 | 결과 |
|------|------|------|
| 2025-09-26 | Headless 모드 테스트 | ❌ 차단됨, 옵션 제거 |
| 2025-09-26 | WSL 한글 폰트 문제 | ✅ 해결 (폰트 설치) |
| 2025-09-26 | URL 접근 방식 테스트 | ✅ `/ns/home` 사용 |
| 2025-09-26 | 터미널 모드 제거 | ✅ GUI만 사용하도록 단순화 |
| 2025-09-26 | PowerShell 오류 처리 | ✅ 오류 시에도 창 유지 |
| 2025-09-26 | 상품 구조 분석 시도 | ❌ 보안 검증 페이지 표시 |
| 2025-09-26 | 메인 페이지 접속 테스트 (4가지 방법) | ❌ 모두 차단됨 |
| 2025-09-26 | 고급 접속 방법 테스트 | ✅ 2가지 방법 성공! |
| 2025-09-26 | 네이버 메인(naver.com) 접속 | ✅ 성공 - 캡차 없음 |
| 2025-09-26 | 쇼핑 직접 URL 접속 | ❌ 캡차 발생! |
| 2025-09-26 | 쇼핑 클릭으로 이동 | ✅ 정상 접속 |
| 2025-09-26 | 브라우저 중복 실행 문제 | ❌ 이미 열려있는데 새로 실행 |
| 2025-09-26 | Playwright MCP 토큰 초과 문제 | ❌ 응답 25,000 토큰 초과 에러 |
| 2025-09-26 | 일반 Playwright + Firefox | ✅ 플러스스토어 접속 성공! |
| 2025-09-26 | Firefox 전체화면 설정 | ✅ --kiosk 옵션으로 성공! |
| 2025-09-26 | 새 탭 전환 + 캡차 회피 | ✅ 클릭→새탭→캡차 없음! |
| 2025-09-26 | 카테고리 → 남성의류 클릭 | ⚠️ 캡차 발생! |

---

## 🔍 Playwright MCP 토큰 초과 문제 (2025-09-26)

### 문제 상황
- **증상**: `browser_snapshot`, `browser_navigate`, `browser_evaluate` 등 사용 시 토큰 초과 에러
- **에러 메시지**: "MCP tool response exceeds maximum allowed tokens (25000)"
- **발생 페이지**: 네이버 메인, 쇼핑 캡차 페이지 등

### 원인 분석
캡차 페이지처럼 **단순해 보이는 페이지도** 실제로는:
1. **숨겨진 JavaScript 코드**: 보안, 추적, 분석 스크립트
2. **복잡한 DOM 구조**: 보이지 않는 div, iframe, 숨겨진 요소들
3. **네이버 보안 시스템**: 캡차 검증을 위한 방대한 코드
4. **CSS와 스타일 정보**: 모든 요소의 스타일 정보
5. **이벤트 리스너**: 각 요소에 걸린 이벤트 핸들러

### 해결 방법
✅ **사용 가능한 도구**:
- `browser_take_screenshot`: 스크린샷만 (토큰 적음)
- `browser_click`: 특정 요소만 클릭
- `browser_type`: 텍스트 입력
- `browser_press_key`: 키 입력

❌ **피해야 할 도구** (복잡한 페이지에서):
- `browser_snapshot`: 전체 DOM 반환 (토큰 과다)
- `browser_evaluate`: 실행 결과 + DOM 반환
- `browser_navigate`: 페이지 로드 후 전체 정보 반환

### 실제 사례
```python
# ❌ 네이버 페이지에서 snapshot 시도 → 50,000+ 토큰
await browser_snapshot()  # 에러!

# ✅ 스크린샷으로 대체
await browser_take_screenshot()  # 성공!

# ✅ 직접 클릭/입력 작업
await browser_type(ref="e24", text="2.46")  # 성공!
```

---

## 🎉 일반 Playwright로 성공! (2025-09-26)

### 성공한 접근 방법
**테스트 파일**: `/tests/test_naver_normal.py`

**성공 조합**:
1. ✅ **Firefox 브라우저** 사용 (봇 감지 우회 쉬움)
2. ✅ **네이버 메인 → 쇼핑 클릭** 순서
3. ✅ **일반 Playwright** (MCP 아님)
4. ✅ **headless=False** (창 보이기)
5. ✅ **slow_mo=500** (천천히 동작)

### 코드 핵심 부분
```python
# Firefox 사용
browser = await p.firefox.launch(
    headless=False,  # 필수!
    slow_mo=500      # 천천히
)

# 1. 네이버 메인 접속
await page.goto('https://www.naver.com')

# 2. 쇼핑 아이콘 클릭
selector = '#shortcutArea > ul > li:nth-child(4) > a'
element = await page.wait_for_selector(selector)
await element.click()

# 3. 성공! 플러스스토어 접속됨
```

### MCP vs 일반 Playwright 결론
| 구분 | MCP Playwright | 일반 Playwright |
|------|---------------|----------------|
| 네이버 페이지 | ❌ 토큰 초과 | ✅ 정상 작동 |
| 제어 수준 | 제한적 | 완전한 제어 |
| 적합한 용도 | 간단한 테스트 | 실제 크롤러 |

**결정**: 네이버는 **일반 Playwright + Firefox** 조합 사용!

---

## 💻 브라우저 전체화면 설정 (2025-09-26)

### 실패한 시도들
1. ❌ `args=['--start-maximized']` → Firefox는 인식 안함
2. ❌ `window.resizeTo()` JavaScript → 부분적 작동
3. ❌ `no_viewport=True` → 화면 우측 치우침, 작업표시줄 가림

### ✅ 성공한 방법: --kiosk 옵션
```python
browser = await p.firefox.launch(
    headless=False,
    slow_mo=500,
    args=['--kiosk']  # ✅ 전체화면 성공!
)

context = await browser.new_context(
    viewport={'width': 1920, 'height': 1030}  # 작업표시줄 고려
)
```

**핵심 포인트**:
- Firefox에서 `--kiosk` 옵션이 전체화면 효과
- viewport 높이는 1080 (완전 전체화면, 작업표시줄 가려도 OK)
- 작업표시줄 가려지지만 크롤링에는 문제없음

---

## 🎯 새 탭 전환 전략 (2025-09-26)

### 중요 발견
**새 탭으로 열어야 캡차 안 나옴!**

### 실패한 방법들
1. ❌ `href` 가져와서 `goto()` → 캡차 발생!
2. ❌ 같은 탭에서 이동 → 캡차 발생!
3. ❌ `Shift+Click` → 여전히 캡차

### ✅ 성공한 방법
```python
# 1. 쇼핑 아이콘 클릭 (새 탭으로 열림)
await element.click()

# 2. 새 탭 전환
await asyncio.sleep(3)  # 탭 열리기 대기
all_pages = context.pages
if len(all_pages) > 1:
    page = all_pages[-1]  # 마지막 탭 = 쇼핑 탭
    await page.wait_for_load_state('networkidle')
    print("✅ 새 탭(쇼핑)으로 전환 완료")
```

**핵심 규칙**:
- ✅ 네이버 메인 → 쇼핑 클릭 → **새 탭으로 열기** → 캡차 없음!
- ❌ 직접 URL 접속 또는 같은 탭 이동 → 캡차 발생!

---

## ⚠️ 카테고리 진입 시 캡차 문제 (2025-09-26)

### 발견된 패턴
**성공 경로**:
- ✅ 네이버 메인 → 쇼핑 클릭(새탭) → 메인 페이지 정상 표시

**실패 경로**:
- ❌ 쇼핑 메인 → 카테고리 클릭 → 남성의류 클릭 → **캡차 발생!**

### 원인 분석
- 네이버 쇼핑 메인까지는 OK
- 세부 카테고리 진입 시 봇 감지 강화
- 카테고리 이동은 더 엄격한 검증

### 가능한 해결 방안
1. 카테고리 클릭 전 더 긴 대기 시간
2. 마우스 호버 후 클릭 (사람처럼)
3. 스크롤 동작 추가
4. 카테고리 직접 URL 대신 검색 활용
5. 수동으로 캡차 해결 후 진행

**현재 상태**: 카테고리 진입 방법 연구 필요

---

**⚠️ 중요**: 이 문서에 기록된 시행착오는 절대 반복하지 말 것!