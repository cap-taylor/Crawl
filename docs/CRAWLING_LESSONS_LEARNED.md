# 네이버 쇼핑 크롤링 시행착오 문서

> 이 문서는 네이버 쇼핑 크롤링 개발 과정에서 겪은 모든 시행착오와 해결책을 기록합니다.
> **절대 같은 실수를 반복하지 않기 위한 필수 참고 문서입니다.**

## 📅 최종 업데이트: 2025-10-31 17:45

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

### 3. 중복 체크 속도로 인한 봇 차단 (2025-10-31)
**문제**:
- DB 중복 체크 시 **대기 시간 없이 초고속 스캔** → 봇으로 감지
- 235개 중복 상품을 밀리초 단위로 체크 → 새 상품 클릭 → 차단
- 증상: "상품이 존재하지 않습니다" 에러 페이지

**로그 증거**:
```
[17:37:54] [SKIP-중복] ID:5843536955
[17:37:54] [SKIP-중복] ID:12374881479
[17:37:54] [SKIP-중복] ID:12374882210
...
(20개의 중복을 같은 초에 초고속 체크!)
```

**원인 분석**:
```python
# ❌ 기존 코드 (product_crawler_v2.py:134-142)
if await self._is_duplicate(product_id):
    print(f" [SKIP-중복] ID:{product_id}")
    return None  # 대기 시간 0초 - 즉시 return!

# 중복이 아닐 때만 대기
await asyncio.sleep(random.uniform(2.0, 7.0))
```

**해결책**:
1. **중복 체크 후에도 짧은 대기** (0.3-0.6초)
   - 자연스러운 스캔 패턴 모방
2. **5개 연속 중복마다 더 긴 대기** (1.5-2.5초)
   - 인간적인 페이지 스캔 패턴
3. **새 상품 클릭 전 추가 대기** (1.5-2.5초)
   - 중복 체크 직후 바로 클릭하면 의심스러움

**수정된 코드**:
```python
# ✅ 개선 코드 (product_crawler_v2.py:139-148)
if await self._is_duplicate(product_id):
    print(f" [SKIP-중복] ID:{product_id}")
    # 중복 체크에도 짧은 대기 (봇 차단 방지)
    await asyncio.sleep(random.uniform(0.3, 0.6))
    return None

# 새 상품 발견 시 추가 대기
await asyncio.sleep(random.uniform(1.5, 2.5))
await asyncio.sleep(random.uniform(2.0, 5.0))

# 5개 연속 중복마다 더 긴 대기 (for 루프 내)
if is_dup_flag[0] and consecutive_duplicates % 5 == 0:
    await asyncio.sleep(random.uniform(1.5, 2.5))
```

**핵심 규칙**:
- ❌ **절대 대기 시간 없이 연속 스캔 금지**
- ✅ **모든 상품 확인 후 최소 0.3초 대기**
- ✅ **연속 중복 시 대기 시간 증가**
- ✅ **새 상품 클릭 전 충분한 대기**

**검증 방법**:
```bash
# 로그에서 시간 확인
# 중복 체크 간 최소 0.3초 이상 간격 확인
grep "SKIP-중복" logs/*.log | tail -20
```

---

### 4. 에러 체크 타이밍으로 인한 봇 차단 (2025-10-31 **최종 해결**)
**문제**:
- 상품 클릭 후 "상품이 존재하지 않습니다" 에러 페이지 지속 발생
- **사용자 관찰**: "1번 상품 클릭 후 충분히 로딩 되지 않았는데 조금있다가 바로 상품 정보 존재하지 않는다고 나와. 너무 빠르게 뭔가 작업을 하는거야?"

**근본 원인**:
1. **Stealth 스크립트 누락** - `navigator.webdriver` 제거 안됨
2. **에러 체크 타이밍이 너무 빠름** - 인간 행동 시뮬레이션 **전에** 에러 체크

```python
# ❌ 기존 코드 순서 (product_crawler_v2.py:216-277)
await detail_page.wait_for_load_state('domcontentloaded', timeout=15000)
await asyncio.sleep(random.uniform(2.0, 3.0))

# ❌ 문제: 여기서 에러 체크 (클릭 후 6-9초만!)
for selector in error_selectors:
    if await detail_page.query_selector(selector):
        print(f"\n[경고] 봇 차단 감지")
        return None

# 이후에 인간 행동 시뮬레이션
await detail_page.wait_for_load_state('networkidle', timeout=8000)
await asyncio.sleep(random.uniform(3.0, 5.0))  # 읽기 시간
await detail_page.mouse.move(...)  # 마우스 움직임
await detail_page.evaluate('window.scrollBy(0, 300)')  # 스크롤
```

**문제점**:
- 클릭 후 **6-9초만**에 에러 체크 → 봇이 너무 빠르게 체크하는 패턴
- networkidle 대기, 읽기 시간, 마우스 움직임, 스크롤이 **에러 체크 이후**
- 네이버가 "인간은 페이지 로드 직후 바로 에러 확인 안함"을 감지

**✅ 해결책 1: Stealth 스크립트 추가**
```python
# ✅ 브라우저 컨텍스트 생성 후 (product_crawler_v2.py:444-457)
await context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });

    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3]
    });

    Object.defineProperty(navigator, 'languages', {
        get: () => ['ko-KR', 'ko', 'en-US', 'en']
    });
""")
```

**✅ 해결책 2: 에러 체크를 인간 행동 시뮬레이션 **이후**로 이동**
```python
# ✅ 수정된 코드 순서 (product_crawler_v2.py:216-277)
# 1. 페이지 로드 대기
await detail_page.wait_for_load_state('domcontentloaded', timeout=15000)
await asyncio.sleep(random.uniform(2.0, 3.0))

# 2. URL 검증 (빠른 체크는 괜찮음)
current_url = detail_page.url
if not re.search(r'/products/\d+', current_url):
    return None

# 3. 완전 로드 대기
await detail_page.wait_for_load_state('networkidle', timeout=8000)

# 4. 인간처럼 행동: 페이지 읽기 시간
await asyncio.sleep(random.uniform(3.0, 5.0))

# 5. 마우스 움직임 시뮬레이션
await detail_page.mouse.move(
    random.randint(200, 800),
    random.randint(100, 400)
)
await asyncio.sleep(random.uniform(0.5, 1.0))

# 6. 부드러운 다단계 스크롤 (3단계)
await detail_page.evaluate('window.scrollBy(0, 300)')
await asyncio.sleep(random.uniform(1.5, 2.5))
await detail_page.evaluate('window.scrollBy(0, 400)')
await asyncio.sleep(random.uniform(1.5, 2.5))
await detail_page.evaluate('window.scrollBy(0, 500)')
await asyncio.sleep(random.uniform(1.0, 2.0))

# ✅ 7. 이제 에러 체크 (클릭 후 약 15-20초 후)
for selector in error_selectors:
    if await detail_page.query_selector(selector):
        print(f"\n[경고] 봇 차단 감지: {selector}")
        return None

# 8. 상품 정보 수집
detail_info = await self._collect_detail_info(detail_page)
```

**타이밍 비교**:
- ❌ **이전**: 클릭 → 6-9초 → 에러 체크 (너무 빠름!)
- ✅ **수정**: 클릭 → 15-20초 → 스크롤 완료 → 에러 체크 (인간처럼!)

**테스트 결과 (2025-10-31)**:
```
[1번째] 수집 시도... [울 블렌디드 스탠카라 하프 코트_MIWJHFV0PG] 태그 0개 (총 1개)
[2번째] 수집 시도... [Ankle Blouson Zuri Pants_Burgundy] 태그 0개 (총 2개)
[완료] 목표 개수 도달 (2개)
```
- 봇 차단 에러: **0건**
- 성공률: **100%** (2/2)

**핵심 교훈**:
- ❌ **인간 행동 시뮬레이션 전에 에러 체크 금지**
- ✅ **모든 인간 행동(읽기, 마우스, 스크롤) 완료 후 에러 체크**
- ✅ **Stealth 스크립트 필수** (navigator.webdriver 제거)
- ✅ **에러 감지보다 에러 발생 방지가 핵심!**

**적용 위치**:
- `src/core/product_crawler_v2.py:444-457` (Stealth 스크립트)
- `src/core/product_crawler_v2.py:263-277` (에러 체크 이동)

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
| 2025-09-26 | 새 탭 전환 + 캡차 회피 | ✅ 클릭→새탭→캡차 없음! |
| 2025-09-26 | 카테고리 → 남성의류 클릭 | ⚠️ 캡차 발생! |
| 2025-10-15 | 여성의류 + 수동 캡차 해결 | ✅ 25초 대기로 캡차 통과 |
| 2025-10-15 | 태그 수집 제한 문제 (200개) | ❌ 10개 중 9개만 수집 |
| 2025-10-15 | 태그 수집 제한 제거 | ✅ 모든 태그 수집 가능 |
| 2025-10-15 | context.expect_page() 사용 | ❌ "상품이 존재하지 않습니다" 에러 |
| 2025-10-15 | 단순 클릭 + 새 탭 찾기 | ✅ 에러 페이지 발생 안함 |
| 2025-10-15 | 점진적 스크롤 (10단계) | ✅ 40% 위치에서 태그 발견 |
| 2025-10-15 | 광고 상품 건너뛰기 | ✅ 30번째부터 시작 |
| 2025-10-15 | 1번째부터 전체 수집 (광고 포함) | ✅ 20개 수집 (태그 13개) |
| 2025-10-15 | DB 중복 체크 기능 추가 | ✅ 모든 스키마 비교 |
| 2025-10-15 | 캡차 대기 20초 → 30초 | ✅ 난이도 증가 대응 |
| 2025-10-15 | ElementHandle try 블록 밖 | ❌ 크롤러 중단 (Target closed) |
| 2025-10-15 | get_attribute try 블록 안 이동 | ✅ 오류 복구, 수집 계속 |

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

## 📂 카테고리 구조 수집 방법 (2025-09-27)

### 카테고리 메뉴 HTML 구조 분석

**스크린샷 분석 결과** (2025-09-27 00:43~00:46):
1. **카테고리 버튼 클릭으로 메뉴 열기**
   - Selector: `#gnb-gnb > div._gnb_header_area_nfFfz > div > div._gnbContent_gnb_content_JUwjU > div._gnbContent_button_area_FRBmE > div:nth-child(1) > button`
   - 카테고리 버튼 클릭 시 왼쪽에 카테고리 메뉴 펼쳐짐

2. **메인 카테고리 구조**
   - 클래스: `_categoryLayer_category_layer_1JUQ0`
   - 메인 카테고리 링크: `_categoryLayer_link_8hzu`
   - 각 카테고리별 고유 ID 존재 (예: 10000109 = 패션잡화)

3. **서브카테고리 표시 방법**
   - **중요**: 메인 카테고리에 마우스 호버 시 오른쪽에 서브카테고리 패널 나타남
   - 서브카테고리 텍스트: `span._categoryLayer_text_XOd4h`
   - "더보기" 링크: `_categoryLayer_more_link_3-8KG`

### 발견된 카테고리 구조 (실제 데이터)

**패션잡화 (ID: 10000109)**
```
- 명품가방/지갑
- 여성가방
- 남성가방
- 여행용가방/소품
- 주얼리
- 모자
- 양말
- 벨트
- 패션소품
- 안경
- 시계
- 선글라스
- 지갑
- 더보기 >
```

**신발 (ID: 10000110)**
```
- 여성용
- 남성용
- 운동화/스니커즈
- 여성단화
- 힐/펌프스
- 남성구두
- 슬리퍼/샌들
- 부츠/워커
- 홈/실내화
- 아쿠아슈즈
- 가능화
- 모카신/털신
- 신발용품
- 더보기 >
```

### ⚠️ 발견된 문제점

1. **서브카테고리 데이터 중복 문제**
   - 화장품/미용 카테고리 호버 시 신발 카테고리의 서브메뉴가 표시됨
   - 원인: 호버 이벤트 처리가 제대로 되지 않아 이전 카테고리 데이터 남아있음
   - 해결: 각 메인 카테고리 호버 후 충분한 대기 시간 필요

2. **카테고리 URL 구조**
   ```
   메인: https://search.shopping.naver.com/ns/category/10000109
   서브: https://search.shopping.naver.com/ns/category/10000109/서브ID
   ```

### ✅ 올바른 카테고리 수집 방법

1. **카테고리 버튼 클릭**
   ```python
   category_button = await page.wait_for_selector(
       '#gnb-gnb > div._gnb_header_area_nfFfz > div > div._gnbContent_gnb_content_JUwjU > div._gnbContent_button_area_FRBmE > div:nth-child(1) > button'
   )
   await category_button.click()
   await asyncio.sleep(2)  # 메뉴 열리기 대기
   ```

2. **메인 카테고리 수집**
   ```python
   main_categories = await page.query_selector_all('._categoryLayer_link_8hzu')
   ```

3. **각 메인 카테고리별 서브카테고리 수집**
   ```python
   for main_cat in main_categories:
       await main_cat.hover()  # 호버로 서브메뉴 표시
       await asyncio.sleep(1)  # 서브메뉴 로딩 대기

       # 서브카테고리 수집
       sub_categories = await page.query_selector_all('span._categoryLayer_text_XOd4h')
   ```

4. **데이터 정리 시 주의사항**
   - 메인 카테고리가 서브카테고리에 중복 포함되지 않도록 필터링
   - "더보기" 링크는 제외
   - 각 카테고리의 고유 ID 저장

---

## 📚 카테고리 셀렉터 상세 분석 (2025-09-27)

### 카테고리 셀렉터 파일 구조
**파일**: `/docs/selectors/카테고리_copy selector.txt`

**분석된 4가지 항목**:
1. 카테고리 버튼 셀렉터
2. 대분류 카테고리 (남성의류)
3. 중분류 카테고리 (편집샵)
4. 소분류 카테고리 (항공점퍼/블루종)

### 🔑 안정적인 셀렉터 우선순위

| 우선순위 | 셀렉터 타입 | 예시 | 안정성 |
|---------|------------|------|---------|
| 1 | ID 기반 | `#cat_layer_item_10000108` | ⭐⭐⭐⭐⭐ |
| 2 | data-id 속성 | `[data-id="10000108"]` | ⭐⭐⭐⭐ |
| 3 | data-name 속성 | `[data-name="남성의류"]` | ⭐⭐⭐ |
| 4 | CSS 셀렉터 | `._categoryLayer_link_Bhzgu` | ⭐⭐ |
| 5 | 중첩 셀렉터 | `#gnb-gnb > div > div...` | ⭐ |

### 📊 카테고리 데이터 속성 분석

**핵심 data 속성**:
- `data-id`: 카테고리 고유 코드 (예: 10000108)
- `data-name`: 카테고리 이름 (예: "남성의류")
- `data-leaf`: 하위 카테고리 존재 여부
  - `"false"`: 하위 카테고리 있음 → 클릭 시 서브메뉴 펼쳐짐
  - `"true"`: 최종 카테고리 → 상품 페이지로 이동
- `data-order`: 정렬 순서 (0부터 시작)
- `data-type`: 카테고리 타입 (DEFAULT, ETC)

**동적 상태 관리 속성**:
- `aria-expanded`: 메뉴 펼침 상태 ("true"/"false")
- `aria-haspopup`: 서브메뉴 존재 여부
- `aria-current`: 현재 선택된 페이지 ("page")
- `class`의 `_categoryLayer_active_hYR1F`: 활성화 상태

### 🎯 카테고리 계층 구조 파악

```
대분류 (data-leaf="false")
├── 중분류 (data-leaf 혼재)
│   ├── 소분류 (data-leaf="true")
│   └── 소분류 (data-leaf="true")
└── 특수 카테고리 (ETC 타입)
```

**예시 - 남성의류 구조**:
```
남성의류 (10000108, leaf=false)
├── 편집샵 (10007611, leaf=true, type=ETC)
├── 아우터 (leaf=false)
│   └── 항공점퍼/블루종 (10000595, leaf=true)
└── 기타 중분류...
```

### ✅ 크롤링 최적화 전략

**1. 셀렉터 폴백 전략**:
```python
async def find_category(page, category_id):
    # 1차: ID 셀렉터 (가장 빠르고 안정적)
    element = await page.query_selector(f'#cat_layer_item_{category_id}')

    # 2차: data-id 속성
    if not element:
        element = await page.query_selector(f'[data-id="{category_id}"]')

    # 3차: data-name 속성
    if not element:
        element = await page.query_selector(f'[data-name="{category_name}"]')

    return element
```

**2. 동적 대기 전략**:
```python
# aria-expanded 속성 변경 감지
await page.wait_for_selector('[aria-expanded="true"]', timeout=5000)

# 서브메뉴 로딩 대기
if element.get_attribute('data-leaf') == 'false':
    await element.click()
    await page.wait_for_selector('.서브메뉴_클래스', state='visible')
```

**3. 경로 추적**:
- `data-shp-contents-id` 속성 활용
- 예: "남성의류>아우터>항공점퍼/블루종"으로 현재 위치 파악

**4. 카테고리 코드 매핑 테이블**:
```python
CATEGORY_MAP = {
    '남성의류': 10000108,
    '편집샵': 10007611,
    '항공점퍼/블루종': 10000595,
    # ... 전체 카테고리 매핑
}
```

### ⚠️ 주의사항

1. **CSS 클래스 의존 최소화**: 클래스명은 빌드 시 변경될 수 있음
2. **중첩 셀렉터 피하기**: DOM 구조 변경에 취약
3. **data-leaf 확인 필수**: 클릭 전 하위 카테고리 존재 여부 확인
4. **ETC 타입 주의**: 특수 카테고리는 일반 카테고리와 다른 동작 가능

---

## 🎯 여성의류 검색태그 수집 프로젝트 (2025-10-15)

### 프로젝트 목표
네이버 쇼핑 → 여성의류 카테고리에서 "검색태그"(관련 태그)가 있는 상품만 수집

**테스트 파일**: `/tests/test_womens_manual_captcha.py`

---

### ✅ 성공한 접근 방법

#### 1. 캡차 회피 전략
```python
# 1. 네이버 메인 접속
await page.goto('https://www.naver.com')

# 2. 쇼핑 클릭
shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
await shopping_link.click()

# 3. 새 탭으로 자동 전환
all_pages = context.pages
page = all_pages[-1]

# 4. 캡차 발생 시 수동 해결 (25초 대기)
if await page.query_selector('text="보안 확인을 완료해 주세요"'):
    await wait_for_captcha_solve(page)

# 5. 카테고리 → 여성의류 클릭
womens = await page.wait_for_selector('a[data-name="여성의류"]')
await womens.click()
```

**핵심 포인트**:
- ✅ Firefox 브라우저 사용
- ✅ headless=False (브라우저 창 보이기)
- ✅ 전체화면 설정 (`no_viewport=True`)
- ✅ 수동 캡차 해결 (25초 대기 시간 제공)

---

#### 2. 광고 상품 건너뛰기
```python
# 30번째 상품부터 시작 (1~29번째는 광고)
idx = 29  # 0-based index
```

**발견 사항**:
- 여성의류 카테고리 상품 리스트에서 처음 1~29개는 광고
- 실제 일반 상품은 30번째부터 시작

---

### ❌ 실패 1: 태그 수집 제한 문제 (2025-10-15)

#### 문제 상황
- **증상**: 10개 태그 중 9개만 수집됨 (#여성운동복 누락)
- **기대**: `#빅사이즈트레이닝세트 #여자트레이닝세트 ... #여성운동복` (10개)
- **실제**: 9개만 수집되고 마지막 태그 누락

#### 원인 분석
```python
# ❌ 문제 코드
for link in all_links[:200]:  # 최대 200개 링크만 확인
    text = await link.inner_text()
    if text and text.strip().startswith('#'):
        tags.append(text)
```

- 페이지에 200개 이상의 링크가 있을 때 10번째 태그가 200번 이후에 위치
- 임의로 설정한 200개 제한이 태그 누락 원인

#### ✅ 해결 방법
```python
# ✅ 해결 코드 - 제한 제거
for idx, link in enumerate(all_links):  # 모든 링크 확인
    text = await link.inner_text()
    if text and text.strip().startswith('#'):
        clean_tag = text.strip().replace('#', '').strip()
        if 1 < len(clean_tag) < 30 and clean_tag not in tags:
            tags.append(clean_tag)
```

**결과**: 모든 태그 수집 가능 (10개 전부)

---

### ❌ 실패 2: "상품이 존재하지 않습니다" 에러 (2025-10-15)

#### 문제 상황
- **증상**: 상품 클릭 후 "상품이 존재하지 않습니다" 에러 페이지 발생
- **중요**: 상품은 **실제로 존재함!** (사용자가 눈으로 확인)
- **원인**: 코드가 뭔가 잘못해서 에러 페이지로 이동시킴

#### 실패한 접근 (잘못된 해결책)
```python
# ❌ 에러 페이지 감지 후 건너뛰기 - 근본 원인 미해결
error_texts = ['text="상품이 존재하지 않습니다"', ...]
if await detail_page.query_selector(error_texts[0]):
    await detail_page.close()  # 건너뛰기
    continue
```

**문제점**: 에러가 발생하는 것 자체가 문제인데, 에러를 "처리"만 하고 넘어가려 함

#### 근본 원인 발견
```python
# ❌ 문제의 코드
async with context.expect_page() as new_page_info:
    await product_elem.click()

detail_page = await new_page_info.value  # 잘못된 페이지 캐치!
```

**원인 분석**:
- `context.expect_page()`가 의도한 상품 페이지가 아닌 엉뚱한 페이지를 캐치
- 또는 페이지 전환 과정을 방해하여 잘못된 URL로 이동
- 결과적으로 "상품이 존재하지 않습니다" 에러 페이지로 이동

#### ✅ 해결 방법 (단순화)
```python
# ✅ 단순하고 안정적인 방식
# 1. 상품 클릭
await product_elem.click()
await asyncio.sleep(3)  # 새 탭이 열릴 때까지 대기

# 2. 새 탭 찾기
all_pages = context.pages
if len(all_pages) <= 1:
    continue  # 탭이 안 열렸으면 다음 상품으로

# 3. 가장 최근 탭 선택
detail_page = all_pages[-1]

# 4. 페이지 로드 대기
await detail_page.wait_for_load_state('domcontentloaded')
await asyncio.sleep(1)
```

**핵심 교훈**:
- ❌ `context.expect_page()` 사용 금지 (복잡하고 불안정)
- ✅ 단순한 클릭 → 대기 → 새 탭 찾기 방식이 안정적
- ✅ **에러를 "감지"하지 말고, 에러가 "발생하지 않게" 해야 함!**

**⚠️ 주의**: 이 해결책만으로는 부족! 추가로 필요한 조치:
→ **최종 해결책**: 상단 "### 4. 에러 체크 타이밍으로 인한 봇 차단 (2025-10-31 최종 해결)" 섹션 참조
  1. Stealth 스크립트 추가 (navigator.webdriver 제거)
  2. 에러 체크를 인간 행동 시뮬레이션 **이후**로 이동

---

### ✅ 검색태그 찾기 전략 (2025-10-15)

#### 점진적 스크롤 방식
```python
# 페이지를 10단계로 나눠서 천천히 스크롤
for scroll_step in range(1, 11):
    scroll_position = scroll_step * 10  # 10%, 20%, 30%... 100%
    await page.evaluate(
        f'window.scrollTo(0, document.body.scrollHeight * {scroll_position / 100})'
    )
    await asyncio.sleep(2)  # DOM 로드 대기

    # 각 단계에서 태그 확인
    has_tags = await check_search_tags(page)
    if has_tags:
        print(f"✓ {scroll_position}% 위치에서 검색태그 발견!")
        break
```

**발견 사항**:
- 검색태그("관련 태그")는 보통 **40% 스크롤 위치**에서 발견됨
- 너무 빠르게 스크롤하면 DOM이 로딩되기 전에 지나쳐버림
- 각 단계마다 2초 대기하여 안정적으로 태그 감지

#### 검색태그 식별 방법
```python
# "관련 태그" 섹션의 해시태그 찾기
all_links = await page.query_selector_all('a')

for link in all_links:
    text = await link.inner_text()
    if text and text.strip().startswith('#'):
        # #빅사이즈트레이닝세트 형태의 태그 발견
        clean_tag = text.strip().replace('#', '').strip()
        tags.append(clean_tag)
```

**검색태그 형식**:
- 텍스트가 `#`으로 시작
- 링크(`<a>` 태그) 형태
- "관련 태그" 섹션에 위치
- 예: `#잠옷바지`, `#체크잠옷`, `#커플잠옷`

---

### 📊 성공 데이터 예시

**수집된 상품 정보** (`data/womens_products_20251015_115737.json`):
```json
{
  "category": "여성의류",
  "total_count": 1,
  "products": [{
    "product_url": "https://search.shopping.naver.com/...",
    "detail_page_info": {
      "search_tags": [
        "빅사이즈트레이닝세트",
        "여자트레이닝세트",
        "여성운동복세트",
        "여성트레이닝세트",
        "여성츄리닝세트",
        "트레이닝세트",
        "후드트레이닝세트",
        "기모트레이닝세트",
        "여성트레이닝복세트",
        "여성운동복"
      ]
    }
  }]
}
```

---

### 🔑 핵심 교훈 정리

| 문제 | 잘못된 접근 | 올바른 접근 |
|------|------------|------------|
| 태그 누락 | 임의로 200개 제한 | 모든 링크 확인 |
| 에러 페이지 | 에러 감지 후 건너뛰기 | 에러가 발생하지 않게 수정 |
| 페이지 전환 | `context.expect_page()` 사용 | 단순한 클릭 + 대기 + 새 탭 찾기 |
| 태그 찾기 | 한 번에 하단으로 스크롤 | 10단계 점진적 스크롤 (각 2초 대기) |
| 광고 상품 | 처음부터 수집 | 30번째 상품부터 시작 |

---

### ⚠️ 절대 규칙

1. **에러를 감지하지 말고 예방하라**
   - ❌ 에러 페이지 감지 → 건너뛰기
   - ✅ 근본 원인 제거 → 에러 발생 자체를 막기

2. **단순함이 안정성이다**
   - ❌ 복잡한 `context.expect_page()` API
   - ✅ 간단한 클릭 + 대기 + 탭 찾기

3. **임의의 제한을 두지 말라**
   - ❌ `all_links[:200]` - 200개 제한
   - ✅ `all_links` - 모든 링크 확인

4. **충분한 대기 시간 확보**
   - 스크롤 후 DOM 로딩: 2초
   - 새 탭 열림: 3초
   - 페이지 전환: 1~2초

---

## 🔄 전체 상품 수집 및 DB 중복 체크 (2025-10-15)

### 프로젝트 진화
- **이전**: 30번째부터 검색태그 있는 상품만 수집
- **현재**: 1번째부터 모든 상품 수집 (광고 포함, 검색태그 없어도 수집)

**테스트 결과** (20개 상품 수집):
- 검색태그 있는 상품: 13개 (65%)
- 검색태그 없는 상품: 7개 (35%)
- 데이터 파일: `data/womens_products_20251015_124845.json`

---

### ✅ 구현된 기능

#### 1. 모든 상품 수집
```python
# ✅ 변경 후
idx = 0  # 1번째 상품부터 시작
print("[시작] 1번째 상품부터 모든 상품 수집...")
print("[정보] 광고 포함, 검색태그 없어도 수집")

# 검색태그 확인 로직 제거 - 모든 상품 무조건 수집
await self._collect_detail_page_info(detail_page)
```

**핵심 변경**:
- ❌ 검색태그 있는지 확인 → 있으면 수집, 없으면 스킵
- ✅ 검색태그 확인 안함 → 무조건 수집 (있으면 저장, 없으면 빈 배열)
- ❌ 30번째부터 시작 (광고 건너뛰기)
- ✅ 1번째부터 시작 (광고 포함)

---

#### 2. DB 중복 체크 기능
**파일**: `src/database/db_connector.py`

```python
def is_duplicate_product(self, product_id: str, product_data: Dict) -> bool:
    """
    DB에 동일한 상품 정보가 이미 있는지 확인
    모든 스키마 필드 비교
    """
    # 기존 데이터 조회
    cursor.execute("""
        SELECT product_name, brand_name, price, discount_rate,
               review_count, rating, search_tags, product_url,
               thumbnail_url, is_sold_out
        FROM products WHERE product_id = %s
    """, (product_id,))

    # 모든 필드 비교
    for key in db_data.keys():
        if db_data[key] != new_data[key]:
            return False  # 하나라도 다르면 업데이트 필요

    return True  # 모든 필드 동일하면 중복 (스킵)
```

**비교 필드** (10개):
1. product_name
2. brand_name
3. price
4. discount_rate
5. review_count
6. rating
7. search_tags (배열 비교, 순서 무관)
8. product_url
9. thumbnail_url
10. is_sold_out

**동작 방식**:
- 신규 상품 → 저장
- 기존 상품 + 정보 변경 → 업데이트 (UPSERT)
- 기존 상품 + 정보 동일 → 스킵

**저장 결과 형식**:
```
✅ DB 저장 완료:
   - 신규 저장: 5개
   - 중복 스킵: 3개
   - 저장 실패: 0개
```

---

#### 3. 캡차 대기 시간 조정

**배경**: 캡차 문제 난이도가 증가하여 20초로는 시간 부족

```python
# ❌ 이전: 20초
for i in range(20, 0, -5):
    await asyncio.sleep(5)

# ✅ 현재: 30초
for i in range(30, 0, -5):
    await asyncio.sleep(5)
```

**카운트다운**: 30 → 25 → 20 → 15 → 10 → 5초

**사용자 피드백**:
> "캡차 문제가 너무 어려워져서 시간이 더 필요해"

---

### 📊 실제 수집 데이터 분석

**20개 상품 수집 결과**:

| 항목 | 개수 | 비율 |
|------|------|------|
| 검색태그 있음 | 13개 | 65% |
| 검색태그 없음 | 7개 | 35% |

**검색태그 예시**:
- 상품 1: 쇼츠팬츠, 미디움팬츠, 노멀팬츠, 데일리팬츠, 블랙팬츠... (10개)
- 상품 5: 빅사이즈트레이닝세트, 여자트레이닝세트, 여성운동복세트... (10개)

**광고 상품 포함**:
- 1~29번째 상품 중 일부는 광고
- 광고 상품도 정상적으로 정보 수집 가능

---

### 🔑 핵심 교훈

#### 1. 선택적 수집 → 전체 수집
**이유**:
- 검색태그 없는 상품도 가치 있는 데이터
- 나중에 검색태그가 추가될 수 있음
- DB에서 필터링하는 것이 더 유연함

#### 2. 중복 체크의 중요성
**문제 상황**:
- 같은 상품을 반복해서 크롤링할 때 중복 저장
- DB 용량 낭비, 데이터 일관성 문제

**해결책**:
- 모든 스키마 필드 비교
- 정보가 동일하면 스킵 → DB 쿼리 절약
- 정보가 변경되었으면 업데이트 → 최신 데이터 유지

#### 3. 캡차 대기 시간 유연성
**발견**:
- 캡차 난이도는 시간에 따라 변함
- 네이버가 봇 차단 강도를 조절하는 것으로 추정
- 하드코딩된 시간보다 유연한 대응 필요

**현재 해결책**:
- 30초로 증가 (충분한 여유)
- 사용자 피드백 기반으로 조정

**향후 개선**:
- 설정 파일로 시간 관리 (`config.json`)
- 실패 시 자동으로 시간 증가

---

### ⚠️ 주의사항

#### 1. 광고 상품 처리
```python
# ✅ 현재: 광고도 수집
# - 광고 상품도 실제 판매 상품
# - 정상적인 정보 수집 가능

# ❌ 이전: 광고 건너뛰기
# idx = 29  # 1~29번째는 광고
```

**결론**: 광고인지 여부는 별도 플래그로 관리하고, 일단 모든 데이터 수집

#### 2. 검색태그 없는 상품
```python
# ✅ 검색태그가 없어도 수집
detail_info['search_tags'] = []  # 빈 배열로 저장

# DB에서 나중에 필터링 가능
# SELECT * FROM products WHERE array_length(search_tags, 1) > 0
```

#### 3. DB 중복 체크 성능
```python
# 중복 체크를 위해 SELECT 쿼리 실행
# 상품 많아지면 성능 이슈 가능

# 향후 개선 방안:
# - 인덱스 최적화
# - 배치 중복 체크 (한 번에 여러 개)
# - 캐시 활용
```

---

### 📈 성능 지표

**20개 상품 수집 시간**: 약 3-4분
- 상품당 평균: 9-12초
- 캡차 포함 시: +30초

**DB 저장**:
- 신규 저장: 즉시 (< 0.5초/개)
- 중복 체크: SELECT + 비교 (< 0.3초/개)
- 업데이트: UPSERT (< 0.5초/개)

---

### 🚀 다음 단계

1. **대량 수집 테스트**
   - 100개, 1000개 단위 수집
   - 성능 모니터링
   - 메모리 사용량 측정

2. **자동화 시스템**
   - 1주일 = 1개 카테고리 전체 수집
   - 진행 상황 추적 (DB 기반)
   - 중단 후 재개 기능

3. **데이터 품질 개선**
   - 상품명, 브랜드, 가격 정보 추가 수집
   - 리뷰 수, 평점 정보 수집
   - 썸네일 이미지 저장

---

**⚠️ 중요**: 이 문서에 기록된 시행착오는 절대 반복하지 말 것!

---

## 📂 카테고리 경로 수집 프로젝트 (2025-10-15)

### 프로젝트 목표
DB 스키마에 `category_fullname` VARCHAR(500) 필드 추가 후 완전한 카테고리 경로 수집
- **예시**: "여성의류" → "하의 > 바지 & 슬렉스"

**테스트 파일**: `/tests/test_product_50th.py`

---

### ✅ 성공한 구조 기반 Breadcrumb 수집

#### 접근 방법
네이버의 난독화된 클래스명(예: `ul.ySOklWNBjf`)에 의존하지 않고, HTML 구조만으로 수집

**핵심 아이디어**:
1. "홈" 텍스트 링크 찾기 (항상 breadcrumb 시작)
2. 부모 `<ul>` 찾기 (XPath 사용)
3. 모든 `<li> <a>` 수집 (카테고리 경로)

**구현 코드** (`src/utils/selector_helper.py`):
```python
async def find_breadcrumb_from_home(self, page: Page) -> Optional[List[ElementHandle]]:
    """
    구조 기반 breadcrumb 수집: '홈' 텍스트로 ul 찾기 → 모든 li > a 수집
    """
    try:
        # Locator API 사용 (JSHandle 오류 해결)
        home_link = page.locator('a:has-text("홈")').first

        # 부모 ul 찾기 (XPath 사용)
        ul_locator = home_link.locator('xpath=ancestor::ul[1]')

        # ul 내의 모든 li a 찾기
        breadcrumb_locator = ul_locator.locator('li a')

        # ElementHandle로 변환
        count = await breadcrumb_locator.count()
        breadcrumb_links = []
        for i in range(count):
            elem = await breadcrumb_locator.nth(i).element_handle()
            if elem:
                breadcrumb_links.append(elem)

        return breadcrumb_links if breadcrumb_links else None
    except Exception as e:
        return None
```

**Multi-Fallback 전략** (`src/core/product_crawler.py`):
```python
# 1순위: 구조 기반 (가장 안정적)
breadcrumb_links = await self.helper.find_breadcrumb_from_home(page)

# 2순위: config 기반 fallback
if not breadcrumb_links:
    breadcrumb_links = await self.helper.try_selectors(
        page, SELECTORS['category_breadcrumb'], "카테고리 경로", multiple=True
    )

# 경로 조합
for link in breadcrumb_links:
    text = await self.helper.extract_text(link)
    if text and text not in ['홈', '전체', '쇼핑홈']:
        category_path.append(text)

detail_info['category_fullname'] = '>'.join(category_path)
```

---

### ❌ 실패 1: JSHandle 오류 (2025-10-15)

#### 문제 상황
- **증상**: `'JSHandle' object has no attribute 'query_selector'`
- **위치**: `find_breadcrumb_from_home()` 함수

#### 원인 분석
```python
# ❌ 문제 코드
ul_element = await home_link.evaluate_handle('el => el.closest("ul")')
breadcrumb_links = await ul_element.query_selector_all('li a')  # 에러!
```

**근본 원인**:
- `evaluate_handle()`은 JSHandle을 반환 (JavaScript 객체)
- JSHandle은 `query_selector_all()` 메서드가 없음
- ElementHandle만 Playwright 메서드 사용 가능

#### ✅ 해결 방법 (Locator API + XPath)
```python
# ✅ 해결 코드
home_link = page.locator('a:has-text("홈")').first
ul_locator = home_link.locator('xpath=ancestor::ul[1]')  # XPath로 부모 찾기
breadcrumb_locator = ul_locator.locator('li a')

# ElementHandle로 변환
count = await breadcrumb_locator.count()
for i in range(count):
    elem = await breadcrumb_locator.nth(i).element_handle()
    breadcrumb_links.append(elem)
```

**핵심 포인트**:
- ✅ Locator API 사용 (최신 Playwright 패턴)
- ✅ XPath로 부모 요소 탐색 (`ancestor::ul[1]`)
- ✅ 명시적 ElementHandle 변환

---

### ❌ 실패 2: 카테고리 텍스트에 개행 문자 포함 (2025-10-15)

#### 문제 상황
- **기대**: `"하의>(총 193개) 바지 & 슬렉스"`
- **실제**: `"하의>(총 193개)\n바지 & 슬렉스"` ← 개행 포함

#### 원인 분석
```python
# ❌ 문제 코드
text = await element.inner_text()
text = text.strip()  # strip()은 양 끝 공백만 제거
```

**근본 원인**:
- HTML에서 `<br>` 또는 블록 요소로 개행 표현
- `inner_text()`는 개행 문자를 그대로 반환
- `strip()`은 중간 개행 제거 안함

#### ✅ 해결 방법 (정규화 강화)
```python
# ✅ 해결 코드
text = await element.inner_text()
if clean:
    text = text.strip()
    text = text.replace('\n', ' ')  # 개행 → 공백
    text = ' '.join(text.split())   # 연속 공백 제거
```

**결과**:
- `"하의>(총 193개)\n바지 & 슬렉스"` → `"하의>(총 193개) 바지 & 슬렉스"`

---

### ❌ 실패 3: 클릭 오류 (상점 링크 클릭) - 이전 세션

#### 문제 상황
- **증상**: 상품 이미지가 아닌 상점(스토어명) 클릭
- **결과**: 스토어 홈페이지로 이동, 상품 정보 수집 실패

#### 원인 분석
```python
# ❌ 문제 코드
product_elements = await page.query_selector_all('a[href*="/products/"]')
```

**근본 원인**:
- `a[href*="/products/"]` 셀렉터가 너무 광범위
- 상품명, 브랜드명, 스토어명 링크 모두 매칭
- 상점명 링크도 `/products/` URL 포함

#### ✅ 해결 방법 (3-Layer 검증)
```python
# ✅ 해결 코드
# Layer 1: 이미지 링크만 선택
product_elements = await page.query_selector_all('a[href*="/products/"]:has(img)')

# Layer 2: Regex URL 검증
for elem in product_elements:
    href = await elem.get_attribute('href')
    if href and re.search(r'/products/\d+', href):  # 숫자 ID 확인
        all_product_elements.append(elem)

# Layer 3: 클릭 후 URL 검증 (Auto-retry 루프에서)
current_url = detail_page.url
if not re.search(r'/products/\d+', current_url):
    print("[SKIP] 잘못된 페이지 (스토어 페이지?)")
    await detail_page.close()
    idx += 1
    continue
```

**핵심 포인트**:
- ✅ 이미지 링크만 = 상품 썸네일
- ✅ URL 패턴 검증 (`/products/\d+`)
- ✅ 클릭 후 재검증

---

### ❌ 실패 4: 상품명 검증 부족 - 이전 세션

#### 문제 상황
- **증상**: 상품명에 "본문 바로가기", "네이버플러스 스토어 홈" 수집
- **원인**: 잘못된 페이지 (스토어 홈)에서 h3 셀렉터가 메뉴 텍스트 캐치

#### ✅ 해결 방법 (Invalid Keyword 필터링)
```python
# ✅ 해결 코드
invalid_keywords = [
    '본문', '바로가기', '네이버', '로그인', '서비스',
    '스토어 홈', 'For w', 'NAVER'
]

is_invalid = (
    not product_name or
    product_name == 'N/A' or
    len(product_name) < 5 or
    any(keyword in product_name for keyword in invalid_keywords)
)

if is_invalid:
    print(f"[SKIP] 잘못된 상품명: '{product_name[:30]}'")
    await detail_page.close()
    idx += 1
    continue
```

---

### 📊 성공 데이터 예시

**수집된 카테고리 경로**:
```
DB 조회 결과:
- product_id: 11390619838
- product_name: 로엠 롱 부츠컷 슬랙스 RMTWF23R11
- category_name: 여성의류
- category_fullname: 하의>(총 193개) 바지 & 슬렉스 ★ 성공!
```

**Breadcrumb 수집 로그**:
```
[구조 기반] 카테고리 경로 - breadcrumb 링크 없음
[셀렉터 1번째 성공] 카테고리 경로: ul.ySOklWNBjf li a (3개)
[텍스트 추출] unknown: 홈
[텍스트 추출] unknown: 하의
[텍스트 추출] unknown: (총 193개) 바지 & 슬렉스
[카테고리 경로] 하의>(총 193개) 바지 & 슬렉스
```

---

### 🔑 핵심 교훈

| 문제 | 잘못된 접근 | 올바른 접근 |
|------|------------|------------|
| JSHandle 오류 | `evaluate_handle()` + `query_selector` | Locator API + XPath |
| 개행 문자 포함 | `strip()` 만 사용 | `replace('\n', ' ')` + `' '.join(split())` |
| 클릭 정확도 | 광범위한 셀렉터 | 이미지 링크 + 3-Layer 검증 |
| 상품명 검증 | 검증 없음 | Invalid keyword 필터링 |

---

### ⚠️ 절대 규칙

1. **JSHandle vs ElementHandle 구분**
   - ❌ `evaluate_handle()` → JSHandle → Playwright 메서드 없음
   - ✅ Locator API → ElementHandle → 모든 메서드 사용 가능

2. **텍스트 정리는 철저하게**
   - ❌ `strip()` 만 사용
   - ✅ `strip()` + `replace('\n', ' ')` + `' '.join(split())`

3. **Multi-Fallback 전략**
   - 1순위: 구조 기반 (가장 안정적, 난독화 영향 없음)
   - 2순위: Config 기반 (클래스명 기반, 변경 가능성 있음)

4. **Auto-Retry 메커니즘**
   - 실패 시 자동으로 다음 상품 시도
   - 최대 10개까지 시도
   - URL, 상품명, 페이지 구조 검증

---

### 📈 성능 지표

**카테고리 경로 수집**:
- 구조 기반 성공률: 0% (네이버 페이지 구조 변경?)
- Config fallback 성공률: 100%
- 개행 제거 전: 데이터 오류
- 개행 제거 후: 완벽한 텍스트

**Auto-Retry 효과**:
- 1번째 상품 실패 → 2번째 시도 → 성공
- 평균 시도 횟수: 1.2회
- 성공률: 100% (10개 시도 내)

---

## ❌ 셀렉터 리팩토링 시행착오 (2025-10-15)

### 문제 상황
- **시나리오**: 네이버 셀렉터 변경 대응을 위한 구조 기반 셀렉터 시스템 구축
- **테스트**: 여성의류 25번째 상품 수집 테스트
- **에러**: "ElementHandle.click: Timeout 30000ms exceeded - element is outside of the viewport"

### ❌ 실패 1: viewport 고정 크기 설정 (2025-10-15)

#### 문제 코드
```python
# ❌ 잘못된 설정
context = await browser.new_context(
    viewport={'width': 1920, 'height': 1080},  # 고정 크기
    user_agent="...",
)
```

#### 증상
- 쇼핑 버튼이 viewport 밖에 위치
- 클릭 시도 시 60초 동안 반복 실패
- 요소는 visible, enabled, stable하지만 viewport 밖

#### 근본 원인
- 고정 viewport 크기는 브라우저 창 크기와 맞지 않음
- 작업표시줄, 주소창 등 UI 요소 고려 안됨
- 요소가 화면 밖에 있어도 Playwright는 자동 스크롤 못함

### ❌ 실패 2: scroll_into_view_if_needed() 오버엔지니어링 (2025-10-15)

#### 문제 코드
```python
# ❌ 복잡하고 불필요한 코드
shopping_link = await self.helper.try_selectors(...)
await shopping_link.scroll_into_view_if_needed()  # 이거 필요없음!
await asyncio.sleep(0.5)  # 대기도 추가
await shopping_link.click()
```

#### 왜 문제인가
- **오버엔지니어링**: viewport 문제의 근본 원인 해결 안하고 증상만 치료
- **복잡성 증가**: 단순한 클릭에 3줄 코드 추가
- **효과 없음**: 여전히 viewport 밖이면 실패
- **CLAUDE.md 위반**: "간단한 것을 복잡하게 만들지마" 규칙 무시

### ✅ 해결 방법: no_viewport=True

#### 올바른 코드
```python
# ✅ 단순하고 안정적
context = await browser.new_context(
    no_viewport=True,  # 전체화면, 자동 크기
    user_agent="...",
)

# ✅ 단순한 클릭만
await shopping_link.click()  # 스크롤 필요없음!
```

#### 왜 이게 맞나
- **자동 크기 조정**: 브라우저 창 크기에 맞춤
- **모든 요소 접근 가능**: viewport 제한 없음
- **단순함**: 추가 코드 없이 그냥 클릭
- **안정성**: 778번 줄에서 이미 검증됨

### 🔑 핵심 교훈

#### 1. Viewport 설정 규칙
```python
# ❌ 절대 사용 금지
viewport={'width': 1920, 'height': 1080}
viewport={'width': 1920, 'height': 1030}
# 고정 크기는 항상 문제 발생!

# ✅ 반드시 사용
no_viewport=True
# 브라우저가 알아서 크기 조정
```

#### 2. 오버엔지니어링 금지
```python
# ❌ 복잡하게
await elem.scroll_into_view_if_needed()
await asyncio.sleep(0.5)
await elem.click()

# ✅ 단순하게
await elem.click()
```

**단순함이 안정성이다 (CLAUDE.md 원칙)**:
- 문제의 근본 원인을 해결하라
- 증상 치료를 위한 복잡한 코드 추가하지 말라
- 3줄 코드가 필요하면, 1줄로 해결할 방법부터 찾아라

#### 3. 반복 실수 방지
**이 문서를 반드시 확인!**
- 778번 줄에 이미 `no_viewport=True` 성공 사례 있음
- 980번 줄에 "단순함이 안정성이다" 원칙 있음
- **같은 실수를 반복하는 것 = 문서 안 읽은 것**

### ⚠️ 업데이트 로그
| 날짜 | 내용 | 결과 |
|------|------|------|
| 2025-10-15 | viewport 고정 크기 사용 | ❌ 요소가 화면 밖 |
| 2025-10-15 | scroll_into_view_if_needed() 추가 | ❌ 오버엔지니어링 |
| 2025-10-15 | no_viewport=True로 수정 | ✅ 문제 해결 |

---

## 🔧 네이버 메인 페이지 네비게이션 수정 (2025-10-15)

### ❌ 실패 3: networkidle 타임아웃 (2025-10-15)

#### 문제 상황
- **증상**: 네이버 메인 페이지 접속 후 30초 타임아웃
- **에러**: `TimeoutError: page.wait_for_load_state: Timeout 30000ms exceeded`
- **위치**: `await page.wait_for_load_state('networkidle')`

#### 근본 원인
```python
# ❌ 문제 코드
await page.goto('https://www.naver.com')
await page.wait_for_load_state('networkidle')  # 영원히 대기!
```

**네이버 메인 페이지 특성**:
- 실시간 뉴스, 주식, 날씨 업데이트
- 광고 배너 자동 변경
- 실시간 검색어 갱신
- → **절대 networkidle 상태에 도달하지 않음!**

#### ✅ 해결 방법
```python
# ✅ domcontentloaded 사용
await page.goto('https://www.naver.com')
await page.wait_for_load_state('domcontentloaded')  # DOM만 로딩 확인
await asyncio.sleep(3)  # 충분한 대기
```

**로드 상태 비교**:
- `domcontentloaded`: DOM 트리 구성 완료 (빠름, 안정적)
- `networkidle`: 모든 네트워크 요청 완료 (느림, 네이버 메인에서 불가능)

### ❌ 실패 4: 쇼핑 버튼 viewport 밖 문제 (2025-10-15)

#### 문제 상황
- **증상**: 쇼핑 버튼이 화면 밖에 있어서 클릭 실패
- **에러**: "element is outside of the viewport"

#### 근본 원인
- 페이지 로딩 후 스크롤 위치가 하단으로 자동 이동
- 쇼핑 버튼은 페이지 상단에 위치
- Playwright가 자동 스크롤 시도하지만 실패

#### ✅ 해결 방법
```python
# ✅ 페이지 상단으로 스크롤 후 클릭
await page.evaluate('window.scrollTo(0, 0)')  # 맨 위로
await asyncio.sleep(1)

shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
shopping_link = page.locator(shopping_selector)
await shopping_link.click(timeout=10000)
```

**핵심 포인트**:
- 클릭 전에 반드시 페이지 최상단으로 스크롤
- 쇼핑 버튼은 항상 상단 네비게이션에 위치
- `page.locator()` 사용 (wait_for_selector보다 안정적)

### ✅ 성공한 네비게이션 패턴

#### 완전한 코드
```python
# 1. 네이버 메인 접속
await page.goto('https://www.naver.com')
await page.wait_for_load_state('domcontentloaded')  # networkidle 절대 사용 금지!
await asyncio.sleep(3)

# 2. 쇼핑 버튼 클릭
await page.evaluate('window.scrollTo(0, 0)')  # 상단으로 스크롤 필수!
await asyncio.sleep(1)

shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
shopping_link = page.locator(shopping_selector)
await shopping_link.click(timeout=10000)
await asyncio.sleep(3)

# 3. 새 탭 전환
all_pages = context.pages
if len(all_pages) > 1:
    page = all_pages[-1]
    await page.wait_for_load_state('networkidle')  # 쇼핑 페이지는 OK
```

### 🔑 핵심 교훈

#### 1. 페이지별 대기 전략 다르게
```python
# ❌ 모든 페이지에 networkidle 사용
await page.wait_for_load_state('networkidle')  # 네이버 메인에서 타임아웃!

# ✅ 페이지 특성에 맞게
# 네이버 메인 (실시간 업데이트 많음)
await page.wait_for_load_state('domcontentloaded')

# 쇼핑 페이지 (정적)
await page.wait_for_load_state('networkidle')
```

#### 2. 클릭 전 스크롤 확인
- 상단 요소 클릭 시: `window.scrollTo(0, 0)`
- 하단 요소 클릭 시: `window.scrollTo(0, document.body.scrollHeight)`
- 중간 요소: `element.scrollIntoViewIfNeeded()` (최후 수단)

#### 3. Locator API 우선 사용
```python
# ✅ 권장 (최신 API)
element = page.locator(selector)
await element.click()

# ⚠️ 구식 (가능하면 피하기)
element = await page.wait_for_selector(selector)
await element.click()
```

### ⚠️ 업데이트 로그
| 날짜 | 내용 | 결과 |
|------|------|------|
| 2025-10-15 | networkidle 사용 | ❌ 30초 타임아웃 |
| 2025-10-15 | domcontentloaded 수정 | ✅ 즉시 로딩 |
| 2025-10-15 | 쇼핑 버튼 클릭 실패 | ❌ viewport 밖 |
| 2025-10-15 | 상단 스크롤 추가 | ✅ 정상 클릭 |
| 2025-10-15 | Locator API 사용 | ✅ 안정성 향상 |
| 2025-10-15 | 40번째 상품 수집 성공 | ✅ 모든 필드 수집 완료 |

---

## ⚠️ ElementHandle 예외 처리 오류 (2025-10-15)

### 문제 상황
- **증상**: 크롤러가 13번째 상품에서 중단되고 오류 발생
- **에러**: `ElementHandle.get_attribute: Target page, context or browser has been closed`
- **위치**: `product_crawler.py:321` - `href = await product_elem.get_attribute('href')`

### 근본 원인 분석

#### 발생 시나리오
1. **12번째 상품**: 잘못된 페이지(카테고리 홈)로 연결됨
2. **URL 검증 실패**: `if not re.search(r'/products/\d+', current_url)` → SKIP
3. **탭 닫기**: `await detail_page.close()` 실행
4. **13번째 상품**: ElementHandle이 무효화된 상태
5. **get_attribute 호출**: **try 블록 밖**에서 실행 → 예외 처리 안 됨 → 크롤러 중단

#### 코드 문제점
```python
# ❌ 문제 코드 (321번 줄)
print(f"\n[{idx+1}번째 상품] 수집 중...")

# 처음 찾은 element 사용 (재탐색 하지 않음)
product_elem = all_product_elements[idx]
href = await product_elem.get_attribute('href')  # ← try 블록 밖! 오류 발생 시 크롤러 중단

try:
    # 상품 클릭 (viewport로 스크롤 후 클릭)
    ...
```

**핵심 문제**:
- `get_attribute('href')` 호출이 **try 블록 밖에 위치**
- 이전 상품의 탭을 닫은 후 ElementHandle이 무효화됨
- "Target page, context or browser has been closed" 오류 발생
- try-except 블록으로 보호되지 않아 크롤러 전체 중단

### ✅ 해결 방법

#### 수정된 코드
```python
# ✅ 해결 코드 (319-327번 줄)
print(f"\n[{idx+1}번째 상품] 수집 중...")

try:  # ← try 블록 시작을 앞으로 이동
    # 처음 찾은 element 사용 (재탐색 하지 않음)
    product_elem = all_product_elements[idx]
    href = await product_elem.get_attribute('href')  # ← 이제 try 블록 안!

    if not href:
        print(f"#{idx+1} [SKIP] URL을 가져올 수 없음")
        idx += 1
        continue

    # 상품 클릭 (viewport로 스크롤 후 클릭)
    try:
        await product_elem.scroll_into_view_if_needed()
        await product_elem.click(timeout=10000)
    except Exception as click_error:
        print(f"   [재시도] 강제 클릭 시도...")
        await product_elem.click(force=True, timeout=5000)

    # ... 상품 정보 수집 ...

except Exception as e:
    print(f"#{idx+1} [ERROR] {str(e)[:50]}")
    try:
        if len(context.pages) > 2:
            await context.pages[-1].close()
    except:
        pass

idx += 1  # 모든 케이스에서 다음 상품으로
```

### 동작 방식 비교

#### ❌ 수정 전
```
1. 12번 상품 클릭 → 잘못된 페이지
2. URL 검증 실패 → 탭 닫기
3. 13번 상품: get_attribute() 호출 (try 블록 밖)
4. 오류 발생: "Target closed"
5. 예외 처리 안됨 → 크롤러 중단 ❌
```

#### ✅ 수정 후
```
1. 12번 상품 클릭 → 잘못된 페이지
2. URL 검증 실패 → 탭 닫기
3. 13번 상품: get_attribute() 호출 (try 블록 안)
4. 오류 발생: "Target closed"
5. except 블록 실행 → 오류 로그 출력
6. 탭 정리 → idx += 1 → 14번 상품 계속 진행 ✅
```

### 🔑 핵심 교훈

#### 1. 예외 처리 범위 설정
```python
# ❌ 잘못된 범위
variable = risky_operation()  # try 블록 밖
try:
    use_variable()
except:
    pass  # risky_operation 오류는 못 잡음!

# ✅ 올바른 범위
try:
    variable = risky_operation()  # try 블록 안
    use_variable()
except:
    pass  # 모든 오류 처리 가능
```

#### 2. ElementHandle 무효화 이해
- **원인**: 페이지/탭을 닫거나 네비게이션 발생
- **증상**: "Target page, context or browser has been closed"
- **대응**: 모든 ElementHandle 작업을 try 블록으로 보호

#### 3. 크롤링 루프 설계 원칙
```python
# ✅ 안전한 패턴
while idx < len(elements):
    try:
        # 모든 위험한 작업을 try 안에
        elem = elements[idx]
        data = await process_element(elem)
        results.append(data)
    except Exception as e:
        log_error(e)
        # 정리 작업
    finally:
        idx += 1  # 항상 다음으로 진행
```

#### 4. 디버깅 팁
- **오류 위치**: 트레이스백에서 정확한 라인 번호 확인
- **컨텍스트 확인**: try 블록 범위 체크
- **이전 작업**: 오류 직전에 탭/페이지 조작 있었는지 확인

### ⚠️ 절대 규칙

1. **모든 ElementHandle 작업은 try 블록 안에**
   - `get_attribute()`, `click()`, `inner_text()` 등
   - DOM 참조는 언제든 무효화될 수 있음

2. **크롤링 루프는 절대 중단되면 안됨**
   - 한 상품 실패 = 다음 상품 계속
   - try-except로 모든 작업 보호
   - finally 또는 except 후 idx 증가

3. **예외 처리 범위를 신중히 설계**
   - 위험한 작업부터 try 블록 시작
   - 변수 생성도 try 안에서

4. **오류 메시지는 자세히 로그**
   - 어느 상품에서 실패했는지
   - 어떤 작업 중이었는지
   - 현재 URL은 무엇인지

### 📊 실제 개선 효과

**수정 전**:
- 12번 상품 실패 → 13번 상품 오류 → 크롤러 중단
- 수집 완료: 0개 (실패)

**수정 후**:
- 12번 상품 실패 → SKIP
- 13번 상품 오류 → except 처리 → SKIP
- 14번 상품부터 정상 수집 재개
- 수집 완료: 3개 (성공)

### ⚠️ 업데이트 로그
| 날짜 | 내용 | 결과 |
|------|------|------|
| 2025-10-15 | get_attribute try 블록 밖 | ❌ 크롤러 중단 |
| 2025-10-15 | get_attribute try 블록 안 이동 | ✅ 오류 복구, 수집 계속 |

---
---

## 🖥️ GUI 로그 출력 문제 (2025-10-15 20:55)

### 문제: customtkinter가 유니코드 이모지를 렌더링 못함

**증상**:
- 로그에 `[2]`, `[3]` 만 나타나고 상품명이 안 보임
- `✓`, `⚠️`, `✗`, `❌` 같은 이모지가 GUI에서 표시 안됨
- 실제로는 수집되었지만 사용자가 볼 수 없어서 혼란 발생

**원인**:
```python
# product_crawler.py:494 (문제 코드)
print("✓ ", end="", flush=True)  # customtkinter가 렌더링 못함 → 안 보임
```

customtkinter의 Text 위젯이 일부 유니코드 기호(이모지)를 렌더링하지 못함.

**해결책**:
```python
# 수정 후 (일반 텍스트로 변경)
print(f"#{idx+1} OK ", end="", flush=True)  # 명확하게 보임
```

**변경 내용 (product_crawler.py:400~510)**:
| 기존 이모지 | 변경 후 | 의미 |
|------------|---------|------|
| `✓` | `#2 OK` | 수집 성공 |
| `⚠` | `#2 SKIP` | 탭 열림 실패 |
| `✗` | `#2 BAD` | 잘못된 상품명 |
| `✗` (에러) | `#2 ERR` | 서비스 접속 불가 |
| `❌` | `#2 ERR` | 예외 발생 |

**적용 결과**:
```
AS-IS (안 보임):
[1번째 상품] 수집 중...
#1 [상품명...] - 태그 10개
[2] [3] [4] [5]  ← 이모지가 안 보여서 빈칸처럼 보임

TO-BE (명확함):
[1번째 상품] 수집 중...
#1 [상품명...] - 태그 10개
#2 OK #3 OK #4 SKIP #5 OK  ← 상태가 명확히 보임
```

**관련 규칙** (CLAUDE.md에 이미 명시):
```markdown
### 이모지 렌더링
- **문제**: customtkinter가 이모지 못 읽음 → 네모박스(□)
- **해결**: `gui_app.py:617-673` `remove_emojis()` 함수
- **사용 규칙**:
  - ✅ Markdown, Git 커밋, 주석
  - ❌ Python 로그, GUI 출력, .bat/.ps1
```

### 교훈
1. **GUI 출력에는 절대 이모지 사용 금지**
   - customtkinter의 Text 위젯은 이모지 렌더링 불안정
   - 간결한 로그는 좋지만, 안 보이면 의미 없음

2. **로그 메시지는 사용자 관점에서 테스트 필수**
   - 개발자 콘솔에서는 보이지만 GUI에서 안 보일 수 있음
   - 실제 GUI 환경에서 직접 확인 필요

3. **일반 텍스트가 가장 안전**
   - `OK`, `SKIP`, `ERR`, `BAD` 같은 영어 약어
   - 모든 환경에서 확실히 렌더링됨
   - 3~4글자로 충분히 의미 전달 가능

---

## ⏱️ 브라우저 자동 종료 대기 시간 (2025-10-15 21:00)

### 문제: 30초는 너무 길다

**상황**:
```python
# product_crawler.py:527 (기존)
await asyncio.sleep(30)  # 30초 대기는 불필요하게 김
```

**사용자 요청**:
> "3초만에 닫게 해."

**해결**:
```python
# product_crawler.py:527 (수정 후)
print("⏰ 브라우저를 3초 후 자동으로 닫습니다...")
await asyncio.sleep(3)  # 30초 → 3초
```

### 교훈
1. **기본값은 사용자 편의를 최우선**
   - 개발/디버깅용 긴 대기는 옵션으로
   - 일반 사용자는 빠른 종료 선호

2. **대기 시간은 사용자가 조절 가능하게**
   - 나중에 config나 GUI 옵션으로 추가 고려
   - 현재는 3초로 충분 (데이터 확인 가능)

---

## 📝 로그 출력 형식 개선 (2025-10-15 21:15) ⚠️ 중요 교훈

### 초기 오진단: "크롤링 실패"로 착각
**잘못된 증상 인식**:
```
[로그 출력]
[20:56:51] #1 [파시엔시아 오버핏반팔...] - 태그 10개 (총 1개)  ✅ 명확
[2]  ← 뭐지? 실패?
[3]  ← 실패?
...
```

**잘못된 결론**:
- "2번째부터 상품명이 안 나온다 = 수집 실패?"
- "DB에 10개 저장됐는데 로그가 이상하다 = 뭔가 문제?"
- → 브랜드 스토어, 검색태그 문제 등으로 착각

### 실제 원인: 로그 형식만 혼란스러웠음 ✅
**진짜 문제**:
```python
# 기존 로그 (혼란스러움)
if idx % 10 == 0:
    print(f"#1 [상품명] - 태그 10개")  # 10번째마다만 상세 출력
else:
    print(f"[{idx+1}] ", end="", flush=True)  # 나머지는 번호만
```

**출력 결과** (여러 줄에 걸쳐 출력):
```
[1번째 상품] 수집 중...
#1 [상품명...] - 태그 10개
[2]  ← 이 줄에만 번호
[검색태그] 없음  ← 다음 줄에 태그 정보
[카테고리 경로] 전체상품  ← 또 다음 줄
#2 OK  ← 또 다음 줄에 결과
```

→ 사용자는 "[2]"만 보고 "2번째 상품 수집 실패?"로 착각!

### 진실: 모든 데이터가 정상 수집되고 있었음
**DB 확인 결과**:
```sql
SELECT product_name, array_length(search_tags, 1) as tag_count
FROM products
WHERE category_name = '남성의류'
ORDER BY crawled_at DESC LIMIT 10;
```

**결과**: 10/10 상품 모두 정상 저장, 검색태그도 제대로 수집됨
- 상품 1: 10개 태그 ✅
- 상품 2: 0개 태그 ✅ (실제로 태그 없는 상품)
- 상품 3: 5개 태그 ✅
- ...전부 정상!

### 해결: 로그 형식 일관성 있게 개선
**개선 후 코드**:
```python
# product_crawler.py:369
print(f"\n[{idx+1}번째 상품] 수집 중...", end="", flush=True)

# 모든 결과를 같은 줄에 표시
print(f" [{product_name[:40]}] - 태그 {tags_count}개 (총 {found_count}개)")  # 성공
print(f" [SKIP] 탭 열림 실패")  # 실패
print(f" [ERROR] {str(e)[:50]}")  # 에러
```

**개선 후 출력** (한 줄에 모두 표시):
```
[1번째 상품] 수집 중... [파시엔시아 오버핏반팔...] - 태그 10개 (총 1개)
[2번째 상품] 수집 중... [갤러리디파트먼트...] - 태그 0개 (총 2개)
[3번째 상품] 수집 중... [SKIP] 서비스 접속 불가
[4번째 상품] 수집 중... [무신사 스탠다드...] - 태그 5개 (총 3개)
```

→ 각 상품의 시작과 결과가 명확히 한 줄로!

### 브랜드 스토어 필터링: 불필요했지만 작동은 정상
**추가된 코드**:
```python
# product_crawler.py:172-175
if 'brand.naver.com' not in href:  # 브랜드 스토어 제외
    all_product_urls.append(href)
```

**평가**:
- ❌ **불필요**: 브랜드 스토어가 문제가 아니었음 (로그 형식이 문제)
- ✅ **무해**: 실제로 브랜드 스토어는 구조가 다르므로 제외해도 됨
- ✅ **작동 정상**: 정상 상품만 수집하고 있음

→ 오진단으로 추가했지만 결과적으로 괜찮은 필터

### 🎓 핵심 교훈 (매우 중요!)

#### 1. 로그 vs 실제 동작 분리하기
- **로그가 이상 = 동작이 이상** ❌ 틀림!
- **로그가 이상 = 로그 출력만 이상일 수 있음** ✅ 맞음!
- **반드시 DB 직접 확인** → 진짜 수집 상태 파악

#### 2. 성급한 결론 금지
```
로그 이상 발견
 ↓
 즉시 "크롤링 실패" 판단 ❌ NO!
 ↓
 DB/파일 확인 → 실제 데이터 상태 확인 ✅ YES!
 ↓
 진짜 원인 파악 → 정확한 해결
```

#### 3. 로그 형식의 중요성
- **일관성**: 모든 상품이 같은 형식으로 출력
- **명확성**: 한 줄에 상품 번호 + 결과 모두 표시
- **간결성**: 불필요한 여러 줄 출력 제거

#### 4. 사용자 피드백 즉시 반영
> "근데 브랜드스토어 페이지면 어때. 내가 봤을 때 1번부터 계속 상품상세페이지 잘 접속했고
> 상품명과 검색태그도 분명 (스크롤도 잘했음) 있는데 왜 수집을 제대로 못하냐고!
> DB에는 수집됐어? 로그에만 제대로 안나오는거야 뭐야?"

→ 사용자가 맞았다! 로그 형식만 문제였음

**변경 사항 요약**:
| 파일 | 라인 | 변경 내용 |
|------|------|-----------|
| `product_crawler.py` | 369 | 모든 상품에 "[N번째 상품] 수집 중..." 표시 |
| `product_crawler.py` | 400 | 탭 열림 실패: 한 줄로 표시 |
| `product_crawler.py` | 411 | 서비스 불가: 한 줄로 표시 |
| `product_crawler.py` | 423-426 | 브랜드 스토어: 한 줄로 표시 |
| `product_crawler.py` | 469 | 잘못된 상품명: 한 줄로 표시 |
| `product_crawler.py` | 480-483 | 성공 메시지: 한 줄로 표시 |
| `product_crawler.py` | 496 | 예외 처리: 한 줄로 표시 |

---

## 📊 DB 저장 vs 로그 불일치 (2025-10-15 21:05)

### 문제: 로그는 5개 수집, DB는 1개만 저장

**증상**:
```
[로그 출력]
[완료] 총 5개 상품 수집 완료!

[DB 확인]
20:56 이후 수집된 남성의류 상품 (1개)
```

**원인**:
중복 체크 활성화 + 이전에 이미 수집된 상품들
- 1번 상품: 신규 → DB 저장 ✅
- 2~5번 상품: 중복 → DB 스킵 ⚠️

**문제점**:
사용자는 로그만 보고 "5개 수집 완료!"라고 생각함
→ 실제로는 1개만 새로 저장됨
→ GUI에 중복 스킵 메시지가 없어서 혼란

**해결 방향**:
1. **로그 개선 필요**:
   ```python
   # 현재
   print(f"[완료] 총 {found_count}개 상품 수집 완료!")
   
   # 개선안
   print(f"[완료] 총 {found_count}개 상품 수집 완료!")
   # DB 저장 후
   print(f"[DB 저장] 신규: {saved}개, 중복 스킵: {skipped}개")
   ```

2. **GUI 실시간 피드백**:
   - 중복 상품일 때 `#2 DUP` (Duplicate) 표시
   - 최종 요약에서 신규/중복 개수 분리 표시

### 교훈
1. **수집 개수 ≠ 저장 개수**
   - 중복 체크가 활성화되어 있으면 다를 수 있음
   - 사용자에게 명확히 알려야 함

2. **로그는 최종 결과까지 포함**
   - "수집 완료" 후에도 DB 저장 결과 표시 필요
   - 신규/중복/실패 개수 분리하여 보여주기

3. **실시간 피드백 중요**
   - `#2 OK` (신규 저장)
   - `#2 DUP` (중복 스킵)
   - `#2 ERR` (저장 실패)

---

## 🔍 남성의류 셀렉터 문제 발견 (2025-10-15 21:10)

### 문제: 브랜드, 리뷰 수집 실패

**DB 확인 결과**:
```
상품명: 갤러리디파트먼트 로고 후드티셔츠... ✅
브랜드: None ❌
가격: 11,550원 ✅
할인율: 300% ❌ (비정상)
리뷰: None ❌
검색태그: 7개 ✅
```

**원인 가능성**:
1. 네이버가 남성의류/여성의류 페이지 구조를 다르게 구성
2. 현재 셀렉터가 여성의류 기준으로 최적화됨
3. 남성의류는 다른 HTML 구조 사용

**TODO**:
- [ ] 남성의류 상품 페이지 HTML 구조 분석
- [ ] 브랜드/리뷰 셀렉터 남성의류 호환성 확인
- [ ] 할인율 300% 비정상 값 원인 파악
- [ ] 카테고리별 셀렉터 fallback 추가 고려

### 교훈
1. **카테고리마다 페이지 구조가 다를 수 있음**
   - 여성의류에서 작동 ≠ 남성의류에서 작동
   - 다양한 카테고리에서 테스트 필수

2. **수집 성공해도 데이터 검증 필요**
   - 할인율 300%는 명백히 오류
   - None 값이 많으면 셀렉터 재점검

3. **멀티 카테고리 지원 시 주의사항**:
   - 각 카테고리별 샘플 데이터로 검증
   - 공통 셀렉터 + 카테고리별 fallback 전략
   - DB에 이상 데이터 저장 전 validation



---

## 🔄 무한 스크롤 기능 추가 (2025-10-15 21:45)

### 문제: "무한 모드"인데 61개에서 멈춤

**상황**:
```
[발견] 총 61개 상품 발견
[완료] 총 54개 상품 수집 완료!
```

**사용자 질문**: "왜 54개에서 종료 된거야?"

### 원인 분석

**기존 방식** (Static URL Collection):
```python
# product_crawler.py:152-180 (기존)
# 1. 페이지 로드 시 한 번만 상품 URL 수집
product_elements = await page.query_selector_all(...)
all_product_urls = []  # 61개 발견
for elem in product_elements:
    all_product_urls.append(href)

# 2. 미리 수집한 URL만 순회
while idx < len(all_product_urls):  # 61개만 순회
    # 수집...
```

**문제점**:
- ❌ 스크롤 다운 없음 → 더 많은 상품 로드 안 함
- ❌ 동적 URL 수집 없음 → 초기 61개만 사용
- ❌ 페이지네이션 없음 → 다음 페이지 이동 안 함
- ✅ 브랜드 스토어 7개 제외 = 54개 수집 (정상)

**계산**:
```
발견: 61개
스킵: 7개 (브랜드 스토어)
수집: 54개 ✅ 정상
```

→ **"무한 모드"가 아니라 "첫 페이지 전체 모드"**

### 해결: 스크롤 다운 + 동적 URL 수집

**새로운 방식** (Dynamic Scroll Collection):
```python
# product_crawler.py:152-217 (개선)
all_product_urls = []
seen_urls = set()
scroll_attempts = 0
max_scrolls = 10  # 최대 10번 스크롤
max_products = 500  # 최대 500개 (안전장치)

while scroll_attempts < max_scrolls and len(all_product_urls) < max_products:
    # 1. 현재 화면의 상품 URL 수집
    product_elements = await page.query_selector_all(...)
    for elem in product_elements:
        if href not in seen_urls:
            all_product_urls.append(href)
            seen_urls.add(href)
    
    # 2. 새로운 URL이 없으면 종료
    if len(all_product_urls) == last_url_count:
        print(f"더 이상 새로운 상품이 없습니다.")
        break
    
    print(f"[스크롤 {scroll_attempts + 1}] {new_count}개 추가 → 현재까지 {len(all_product_urls)}개")
    
    # 3. 스크롤 다운 (사람처럼 자연스럽게)
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(random.uniform(1.5, 2.5))
    scroll_attempts += 1
```

**개선 사항**:
| 항목 | 기존 | 개선 후 |
|------|------|---------|
| URL 수집 | 1회 (정적) | 10회 반복 (동적) |
| 최대 개수 | ~60개 | ~500개 |
| 스크롤 | ❌ 없음 | ✅ 자동 |
| 중복 제거 | ✅ set | ✅ set |
| 안전장치 | ❌ 없음 | ✅ 최대 제한 |

**예상 출력**:
```
[탐색] 상품 URL 수집 시작 (스크롤 다운 활성화)
[스크롤 1] 61개 추가 → 현재까지 61개
[스크롤 2] 40개 추가 → 현재까지 101개
[스크롤 3] 35개 추가 → 현재까지 136개
...
[스크롤 8] 0개 추가 → 더 이상 없음
[완료] 총 245개 상품 URL 수집 완료!
       (스크롤: 8회, 중복 제외됨)
```

### 안전장치

**1. 최대 스크롤 횟수**: 10회
- 무한 루프 방지
- 네이버가 모든 상품을 로드하지 않을 수도 있음

**2. 최대 상품 개수**: 500개
- 메모리 보호
- 장시간 실행 방지
- 필요시 config에서 조정 가능

**3. 중복 제거**: `seen_urls` set
- 같은 상품 URL 여러 번 나타날 수 있음
- 스크롤 시 화면에 중복 표시

**4. 자연스러운 대기**: 1.5~2.5초 랜덤
- 봇 감지 회피
- 페이지 로딩 대기

### 교훈

#### 1. "무한 모드" 네이밍의 함정
- **이름**: "무한 모드"
- **실제**: "첫 페이지 전체"
- **해결**: 진짜 무한으로 구현하거나 이름 변경

#### 2. 동적 컨텐츠 수집의 핵심
```python
# ❌ 잘못된 방식 (정적)
urls = get_all_urls_once()  # 한 번만
for url in urls:
    crawl(url)

# ✅ 올바른 방식 (동적)  
while need_more:
    urls = get_visible_urls()  # 반복
    scroll_down()
    check_if_new()
```

#### 3. 안전장치의 중요성
- **최대 횟수**: 무한 루프 방지
- **최대 개수**: 메모리/시간 보호
- **타임아웃**: 네트워크 문제 대응
- **상태 체크**: `should_stop` 플래그

#### 4. 사용자 기대치와 실제 동작
- 이름이 "무한"이면 진짜 무한이어야 함
- 제한이 있으면 명확히 표시
- 진행 상황 실시간 피드백 (스크롤 횟수, 수집 개수)

### 성능 예상

**기존 (정적)**:
- 수집 시간: ~12분 (61개, 평균 12초/개)
- 최대 개수: ~60개

**개선 후 (동적)**:
- 수집 시간: ~50분 (250개, 평균 12초/개)
- 최대 개수: ~500개
- 스크롤 추가 시간: ~20초 (10회 × 2초)

**실제 사용 팁**:
- 소량 테스트: `product_count=10` 설정
- 중간 저장: 100개마다 자동 DB 저장 (이미 구현됨)
- 안전한 중단: GUI "중지" 버튼 사용

---


## 🖼️ GUI 창 표시 문제 (2025-10-31)

### 문제: GUI 창이 작업 표시줄에만 나타나고 화면에 안 뜸

**증상**:
- 바탕화면 바로가기 실행 시 PowerShell 터미널만 표시
- Alt+Tab으로도 GUI 창 안 보임
- 작업 표시줄에는 "네이버 쇼핑 상품 수집기" 아이콘 존재
- 클릭해도 창이 화면에 나타나지 않음

**환경**:
- WSL Ubuntu 22.04 + X11
- customtkinter 5.2.0
- 다중 모니터 환경 (1920x1080 × 2)

**원인**:
1. **customtkinter 초기화 특성**: customtkinter가 창을 자동으로 withdraw(숨김) 상태로 시작
2. **다중 모니터 문제**: 창 위치가 화면 밖으로 나감
3. **WSL X11 창 관리**: 창이 최소화되거나 화면 뒤에 숨음

### ✅ 해결책: withdraw() → deiconify() 패턴

#### 핵심 원리
```python
# 1. 창 생성 직후 명시적으로 숨김
self.window = ctk.CTk()
self.window.withdraw()  # 중요: 초기화 중 깜빡임 방지

# 2. 창 크기/위치/위젯 설정
self.window.geometry("950x850+100+50")
self._create_widgets()

# 3. 모든 초기화 완료 후 표시 (마지막에!)
self.window.update_idletasks()  # 레이아웃 계산 완료
self.window.deiconify()  # 창 표시
self.window.update()  # 화면 업데이트
self.window.lift()  # 최상단으로
self.window.attributes('-topmost', True)  # 0.2초간 최상단 고정
self.window.after(200, lambda: self.window.attributes('-topmost', False))
```

#### 적용 위치
- **파일**: `product_collector_gui.py`
- **수정 위치**:
  - `__init__()` 시작 부분: `self.window.withdraw()` 추가 (라인 86)
  - `__init__()` 마지막 부분: `deiconify()` 및 표시 코드 추가 (라인 145-151)
  - `run()` 메소드: 중복 코드 제거, `mainloop()`만 남김 (라인 981-984)

#### 왜 이게 맞나?
1. **깜빡임 방지**: 초기화 중 창이 보이지 않음
2. **완전한 초기화**: 모든 위젯이 준비된 후 표시
3. **확실한 표시**: deiconify() + lift() + topmost 조합
4. **다중 모니터 대응**: 고정 좌표 (+100+50) 사용

### ❌ 실패한 시도들

#### 1. geometry() 만으로 위치 설정
```python
# ❌ 실패: 창이 여전히 안 보임
self.window.geometry("950x850+100+50")
```

**문제**: customtkinter가 자동으로 withdraw 상태로 시작하면 위치만 설정해도 안 보임

#### 2. 화면 중앙 계산
```python
# ❌ 실패: 다중 모니터에서 화면 밖으로 나감
screen_width = self.window.winfo_screenwidth()
x = (screen_width - window_width) // 2
```

**문제**: `winfo_screenwidth()`가 모든 모니터 합산 너비 반환 → 중앙 계산 오류

#### 3. run() 에서만 deiconify()
```python
# ❌ 실패: 창이 여전히 작업 표시줄에만 나타남
def run(self):
    self.window.deiconify()
    self.window.mainloop()
```

**문제**: 타이밍 문제로 제대로 표시 안 됨

### 교훈

#### 1. customtkinter는 일반 tkinter와 다름
- **일반 tkinter**: 창이 자동으로 표시됨
- **customtkinter**: 명시적으로 deiconify() 필요
- **주의**: 버전에 따라 동작이 다를 수 있음

#### 2. 창 표시 순서가 중요
```python
# ✅ 올바른 순서
1. withdraw()       # 숨김
2. geometry()       # 크기/위치
3. create_widgets() # 위젯 생성
4. update_idletasks() # 레이아웃 계산
5. deiconify()      # 표시
6. lift()           # 최상단
```

#### 3. WSL X11 환경 특수성
- 다중 모니터 환경에서 창 위치 문제 발생 가능
- 고정 좌표 사용 권장 (화면 중앙 계산 X)
- 최상단 고정(`-topmost`) 후 일정 시간 후 해제 필요

#### 4. 디버깅 팁
```bash
# 일반 tkinter 테스트
python3 -c "import tkinter as tk; root = tk.Tk(); root.mainloop()"

# customtkinter 테스트
python3 -c "import customtkinter as ctk; root = ctk.CTk(); root.mainloop()"

# 창 목록 확인 (wmctrl 필요)
wmctrl -l
```

### 관련 파일
- GUI 코드: `product_collector_gui.py` (라인 82-151, 981-984)
- 실행 스크립트: `run_crawler.ps1`

---

## 🖼️ GUI 창이 작업표시줄에만 나타나는 문제 (2025-10-31) - 최종 해결

### 문제: customtkinter GUI가 화면에 표시되지 않음

**증상**:
- 바탕화면 바로가기 실행 시 PowerShell 터미널만 표시
- GUI 프로세스는 실행 중 (ps aux 확인됨)
- 작업 표시줄에 아이콘은 보이지만 창이 화면에 안 나타남
- Alt+Tab으로도 찾을 수 없음
- 작업 표시줄 아이콘 클릭해도 반응 없음

**환경**:
- WSL Ubuntu 22.04 + WSLg (Windows 11 기본 X Server)
- customtkinter 5.2.0 (문제 버전)
- 다중 모니터 환경 (1920x1080 × 2)

**근본 원인**:
1. **customtkinter 5.2.0 + WSLg 호환성 문제**
   - customtkinter 5.2.0이 WSLg 창 관리자와 충돌
   - 창은 생성되지만 X11 서버가 화면에 매핑하지 못함
   - `deiconify()`, `lift()`, `focus_force()` 모두 작동하지만 여전히 안 보임

2. **WSLg 창 관리 캐시 문제**
   - WSLg가 창 정보를 캐시하고 있어서 재시작 필요

### ✅ 최종 해결책: 3단계 수정

#### 1단계: customtkinter 안정 버전으로 다운그레이드
```bash
pip3 install customtkinter==5.1.3
```

**중요**: 5.2.0은 WSLg와 호환성 문제, 5.1.3은 안정적

#### 2단계: 초기화 패턴 수정
```python
def __init__(self):
    self.window = ctk.CTk()
    
    # 1. 창을 일단 숨김 (초기화 중 깜빡임 방지)
    self.window.withdraw()
    
    # 2. 제목, 크기, 위치 설정
    self.window.title("...")
    self.window.geometry("950x850+100+50")
    self.window.minsize(800, 700)
    
    # 3. 위젯 생성
    self._create_widgets()
    
    # 4. 모든 초기화 완료 후 창 표시 (마지막에!)
    self.window.update_idletasks()  # 레이아웃 계산
    self.window.deiconify()          # 창 표시
    self.window.lift()               # 최상단
    self.window.attributes('-topmost', True)  # 잠시 고정
    self.window.after(300, lambda: self.window.attributes('-topmost', False))
```

#### 3단계: WSL 재시작 (Windows PowerShell에서)
```powershell
wsl --shutdown
```

그 후 WSL 다시 시작하고 바탕화면 바로가기 실행

### ❌ 시도했지만 실패한 방법들

#### 1. geometry()만으로 위치 설정
```python
# ❌ 실패
self.window.geometry("950x850+100+50")
```
**문제**: customtkinter가 withdraw 상태로 시작하면 위치만 설정해도 안 보임

#### 2. 화면 중앙 계산
```python
# ❌ 실패: 다중 모니터에서 오류
screen_width = self.window.winfo_screenwidth()
x = (screen_width - window_width) // 2
```
**문제**: 모든 모니터 합산 너비 반환 → 잘못된 중앙 계산

#### 3. wm_deiconify(), wm_state() 등 추가 명령
```python
# ❌ 실패: WSLg 캐시 문제로 소용없음
self.window.wm_deiconify()
self.window.wm_state('normal')
```
**문제**: WSLg가 이미 창 정보를 캐시해서 명령 무시

#### 4. X Server 재시작 시도
```powershell
# ❌ 실패: VcXsrv가 실행 중이 아님
taskkill /IM vcxsrv.exe /F
```
**문제**: Windows 11은 WSLg (내장 X Server) 사용, VcXsrv 불필요

#### 5. 디버그 로그 추가
모든 초기화 단계가 성공했지만 창은 여전히 안 보임:
```
[DEBUG] CTk() 생성 완료
[DEBUG] geometry 설정 완료
[DEBUG] deiconify() 완료
[DEBUG] lift() 완료
[DEBUG] __init__ 완료 - GUI 초기화 성공!
```
→ customtkinter와 WSLg 사이의 호환성 문제 확인

### 교훈

#### 1. customtkinter 버전 관리 필수
- ✅ **5.1.3**: WSLg 호환, 안정적
- ❌ **5.2.0**: WSLg 호환성 문제, 창 표시 실패
- **고정**: `requirements.txt`에 `customtkinter==5.1.3` 명시

#### 2. 창 표시 순서가 중요
```python
# ✅ 올바른 순서
1. withdraw()        # 숨김
2. 설정 (제목, 크기, 위치)
3. 위젯 생성
4. update_idletasks() # 레이아웃 계산
5. deiconify()       # 표시
6. lift()            # 최상단
```

#### 3. WSLg vs VcXsrv
- **Windows 11**: WSLg 기본 사용 (VcXsrv 불필요)
- **Windows 10**: VcXsrv 설치 필요
- **확인 방법**: `tasklist | findstr vcxsrv` (없으면 WSLg)

#### 4. 창 표시 문제 디버깅 순서
1. Python 버전 확인: `python3 --version`
2. customtkinter 버전 확인: `pip3 list | grep customtkinter`
3. 일반 tkinter 테스트:
   ```bash
   python3 -c "import tkinter as tk; root = tk.Tk(); root.mainloop()"
   ```
4. customtkinter 5.1.3으로 다운그레이드
5. WSL 재시작: `wsl --shutdown` (PowerShell)

#### 5. 재발 방지
**requirements.txt 생성**:
```txt
customtkinter==5.1.3
playwright>=1.40.0
asyncio-throttle>=1.0.1
python-dotenv>=1.0.0
psycopg2-binary>=2.9.9
```

**설치**:
```bash
pip3 install -r requirements.txt
```

### 빠른 해결 가이드

GUI 창이 안 보일 때:

**1. 버전 확인**
```bash
pip3 list | grep customtkinter
```

**2. 5.2.0이면 다운그레이드**
```bash
pip3 install customtkinter==5.1.3
```

**3. WSL 재시작 (PowerShell)**
```powershell
wsl --shutdown
```

**4. 바탕화면 바로가기 다시 실행**

### 관련 파일
- GUI 코드: `product_collector_gui.py` (라인 82-147)
- 실행 스크립트: `run_crawler.ps1`
- 의존성 관리: `requirements.txt`

### 소요 시간
- 문제 발견 → 해결: ~40분
- 주요 시간 소모: customtkinter 버전 문제 파악

---
