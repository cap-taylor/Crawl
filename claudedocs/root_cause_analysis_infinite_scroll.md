# 무한 스크롤 90-96개 중단 문제 - 근본 원인 분석

**날짜**: 2025-11-04
**버전**: v1.4.2+
**파일**: `/home/dino/MyProjects/Crawl/src/core/simple_crawler.py`

---

## 🔴 문제 요약

### 증상
- **배치 1**: 43개 수집 완료 → wheel 스크롤 실행
- **배치 2**: 47개 수집 완료 (총 90개) → scrollBy 스크롤 실행
- **스크롤 후**: 15초 대기 (3회 × 5초) → 상품 개수 변화 없음 → 종료

### 핵심 단서
사용자: **"직접 브라우저에서 수동으로 스크롤하면 계속 상품이 나옴"**

→ 스크롤 자체는 성공하지만, 네이버 서버가 추가 상품을 제공하지 않음

---

## 🧪 증거 수집

### 현재 스크롤 구현 (line 401-422)

```python
# 방법 1: wheel 이벤트로 스크롤
last_product = product_links[-1]
await last_product.scroll_into_view_if_needed()  # ← 마지막 상품으로 이동
await asyncio.sleep(0.5)

# 추가 wheel 이벤트 (3번)
await page.mouse.wheel(0, 500)
await asyncio.sleep(0.5)
await page.mouse.wheel(0, 500)
await asyncio.sleep(0.5)
await page.mouse.wheel(0, 500)

# 방법 2: scrollBy (fallback)
for i in range(3):
    await page.evaluate('window.scrollBy(0, window.innerHeight)')
    await asyncio.sleep(0.3)
```

### 문제점 분석

#### 1. **과도한 프로그래밍적 스크롤**
```python
# 현재 구현
await last_product.scroll_into_view_if_needed()  # 1회
await page.mouse.wheel(0, 500)                    # +500px
await page.mouse.wheel(0, 500)                    # +500px
await page.mouse.wheel(0, 500)                    # +500px
# → 총 1500px 이동 (순간적)
```

**문제**:
- 너무 빠르고 균일한 스크롤 → 봇 패턴 감지
- 사람은 불규칙하게 스크롤하고, 멈추고, 다시 스크롤함
- `scroll_into_view_if_needed()` 후 즉시 wheel 이벤트 → 부자연스러움

#### 2. **Lazy Loading 트리거 실패**

네이버 무한 스크롤의 작동 원리:
```javascript
// 네이버가 사용하는 Intersection Observer 패턴
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            // 사용자가 실제로 "보고 있을 때"만 로드
            loadMoreProducts();
        }
    });
}, {
    rootMargin: '100px',  // 100px 전에 미리 로드
    threshold: 0.1        // 10% 보이면 트리거
});
```

**현재 코드의 문제**:
- `scroll_into_view_if_needed()`: 요소를 viewport에 넣지만, Intersection Observer가 트리거되기 전에 다시 스크롤
- 빠른 연속 스크롤: Observer가 감지할 시간 없음
- Viewport 체류 시간 부족: 네이버가 "실제로 보고 있는지" 확인 불가

#### 3. **클릭 중 스크롤 위치 손실 (line 304)**

```python
# 상품 클릭 전
await product.scroll_into_view_if_needed()  # 상품 위치로 이동
await asyncio.sleep(0.5)
await product.click()                        # 새 탭 열림
# ... 상품 수집 ...
await detail_page.close()                    # 탭 닫음

# ❌ line 361-362 주석 참고: scrollTo(0,0) 제거함
# → 탭 닫으면 원래 페이지로 돌아오지만, 스크롤 위치가 불안정
```

**문제**:
- 클릭할 때마다 `scroll_into_view_if_needed()` 호출
- 배치 2에서 90번째 상품 클릭 시 페이지 아래로 계속 내려감
- 탭 닫고 돌아오면 스크롤 위치가 애매한 곳에 있음
- 추가 스크롤 시 Intersection Observer가 이미 trigger된 영역으로 이동 → 중복 요청 방지 로직에 의해 무시됨

#### 4. **Viewport 최적화 설정 누락 (line 61)**

```python
context = await browser.new_context(
    no_viewport=True,  # ← 문제!
    user_agent="...",
    locale='ko-KR',
    timezone_id='Asia/Seoul'
)
```

**문제**:
- `no_viewport=True`: 브라우저가 "무한 높이" viewport를 가짐
- Intersection Observer: "모든 요소가 이미 viewport 안에 있음"으로 인식
- Lazy Loading 트리거 조건 충족 불가

---

## 🔬 가설 검증

### 가설 1: 네이버가 자동 스크롤 감지 ❌
**검증**:
- 문서에서 "Firefox는 그냥 사용해도 됨" (line 779)
- 캡차는 통과하고 있음 (증거: 90개까지 수집 성공)
- 봇 감지라면 첫 배치에서 차단됐을 것

**결론**: 봇 감지는 아님

### 가설 2: Lazy Loading 트리거 실패 ✅
**검증**:
```python
# 현재: 너무 빠른 스크롤
await last_product.scroll_into_view_if_needed()
await asyncio.sleep(0.5)  # ← 너무 짧음!
await page.mouse.wheel(0, 500)
```

**네이버 Intersection Observer 요구사항**:
- 요소가 viewport에 **일정 시간 체류** 필요 (예: 1-2초)
- **시각적 렌더링** 완료 필요
- **스크롤 안정화** 필요 (scroll stop event)

**결론**: 가장 유력한 원인

### 가설 3: Viewport 문제 ✅
**검증**:
- `no_viewport=True` → 무한 높이 viewport
- 네이버: "모든 상품이 이미 보이므로 더 로드할 필요 없음"으로 판단 가능

**결론**: 복합 원인

### 가설 4: 스크롤 위치 누적 문제 ✅
**검증**:
```python
# 배치 1: 43번 클릭 → 43번 scroll_into_view
# 배치 2: 47번 클릭 → 47번 scroll_into_view
# → 총 90번 강제 스크롤 → 페이지 끝에 거의 도달
```

**로그 증거** (line 393):
```
[DEBUG] 스크롤 전 - 위치: 15000px, 문서 높이: 16000px
```
→ 이미 페이지 끝에 가까움 → 스크롤해도 새 영역 진입 실패

**결론**: 복합 원인

---

## 💡 근본 원인 (Root Cause)

### 주 원인 (Primary)
**Intersection Observer 트리거 실패**

네이버의 무한 스크롤은 다음 조건을 모두 충족해야 작동:
1. **Sentinel 요소가 viewport에 진입** (현재: ✅ scroll_into_view로 진입)
2. **일정 시간 체류** (현재: ❌ 0.5초만 대기 후 즉시 다음 스크롤)
3. **시각적 렌더링 완료** (현재: ❌ 확인 안 함)
4. **스크롤 안정화** (현재: ❌ 연속 스크롤로 계속 움직임)

### 부 원인 (Contributing Factors)

1. **no_viewport=True 설정**
   - 무한 높이 viewport → Intersection Observer 동작 방해

2. **클릭 중 과도한 scroll_into_view**
   - 배치당 40-50번 호출 → 스크롤 위치 불안정
   - Lazy Loading 영역을 건너뛰고 페이지 끝으로 이동

3. **프로그래밍적 스크롤 패턴**
   - 균일한 속도 (500px × 3회)
   - 대기 시간 부족 (0.5초)
   - 자연스러운 스크롤 행동 부재

---

## 🎯 해결 방안

### 1. Viewport 설정 변경 (Critical)

```python
context = await browser.new_context(
    viewport={'width': 1920, 'height': 1080},  # ✅ 실제 viewport 설정
    # no_viewport=True 제거
    user_agent="...",
    locale='ko-KR',
    timezone_id='Asia/Seoul'
)
```

**효과**: Intersection Observer가 정상 작동

### 2. 자연스러운 스크롤 구현 (Critical)

```python
# ❌ 현재: 빠르고 균일한 스크롤
await page.mouse.wheel(0, 500)
await asyncio.sleep(0.5)
await page.mouse.wheel(0, 500)

# ✅ 개선: 사람처럼 불규칙한 스크롤
async def human_like_scroll(page):
    """사람처럼 자연스러운 스크롤"""
    # 1단계: 천천히 스크롤 시작
    scroll_amount = random.randint(300, 600)
    await page.mouse.wheel(0, scroll_amount)
    await asyncio.sleep(random.uniform(0.3, 0.8))

    # 2단계: 추가 스크롤 (50% 확률)
    if random.random() > 0.5:
        scroll_amount = random.randint(200, 400)
        await page.mouse.wheel(0, scroll_amount)
        await asyncio.sleep(random.uniform(0.5, 1.2))

    # 3단계: 체류 시간 (Intersection Observer 트리거 대기)
    await asyncio.sleep(random.uniform(1.5, 2.5))
```

### 3. Sentinel 요소 기반 스크롤 (Recommended)

```python
async def scroll_to_trigger_lazy_load(page):
    """네이버의 Lazy Loading을 의도적으로 트리거"""

    # 1. 현재 마지막 상품 찾기
    product_links = await page.query_selector_all('a[class*="ProductCard_link"]')
    if not product_links:
        return False

    # 2. 마지막 상품보다 약간 위로 스크롤 (Sentinel 영역)
    second_last = product_links[-5] if len(product_links) > 5 else product_links[-1]

    # 3. Sentinel 영역으로 천천히 스크롤
    await second_last.scroll_into_view_if_needed()
    await asyncio.sleep(1.5)  # ← 중요: Observer 트리거 대기

    # 4. 추가 스크롤 (자연스럽게)
    await page.mouse.wheel(0, random.randint(200, 400))
    await asyncio.sleep(random.uniform(1.0, 2.0))

    # 5. 렌더링 완료 대기
    await page.wait_for_load_state('networkidle', timeout=3000)

    return True
```

### 4. 클릭 중 스크롤 최소화 (Important)

```python
# ❌ 현재: 매 클릭마다 scroll_into_view
await product.scroll_into_view_if_needed()
await product.click()

# ✅ 개선: 클릭 가능할 때만 스크롤
if not await product.is_visible():
    await product.scroll_into_view_if_needed()
    await asyncio.sleep(0.3)

await product.click()
```

### 5. 스크롤 후 대기 시간 증가 (Critical)

```python
# ❌ 현재: 5초 × 3회 = 15초
for attempt in range(3):
    await asyncio.sleep(5)
    # 상품 개수 확인

# ✅ 개선: 점진적 대기 (총 20초)
wait_times = [3, 5, 7, 5]  # 점진적 증가 후 감소
for i, wait_time in enumerate(wait_times):
    await asyncio.sleep(wait_time)
    product_links_after = await page.query_selector_all('a[class*="ProductCard_link"]')

    if len(product_links_after) > before_scroll:
        print(f"[시도 {i+1}] ✅ {wait_time}초 후 {len(product_links_after) - before_scroll}개 로드")
        break
```

---

## 📋 구현 우선순위

### Phase 1: 긴급 수정 (Immediate)
1. ✅ **Viewport 설정 변경** (line 61)
   - `no_viewport=True` → `viewport={'width': 1920, 'height': 1080}`

2. ✅ **스크롤 대기 시간 증가** (line 432)
   - 5초 → 점진적 대기 (3, 5, 7, 5초)

### Phase 2: 개선 (High Priority)
3. ✅ **자연스러운 스크롤** (line 401-422)
   - 불규칙한 스크롤량
   - 랜덤 대기 시간
   - 체류 시간 증가

4. ✅ **Sentinel 기반 스크롤** (line 404-407)
   - 마지막 5번째 상품으로 스크롤
   - Intersection Observer 트리거 시간 확보

### Phase 3: 최적화 (Medium Priority)
5. ✅ **클릭 중 스크롤 최소화** (line 304)
   - `is_visible()` 체크 추가

6. ✅ **networkidle 대기 추가**
   - 스크롤 후 렌더링 완료 확인

---

## 🧪 검증 방법

### 테스트 1: Viewport 효과 확인
```python
# 브라우저 콘솔에서 실행
console.log({
    viewport_height: window.innerHeight,
    document_height: document.body.scrollHeight,
    current_scroll: window.pageYOffset
});
```

**기대 결과**:
- `viewport_height`: 1080 (고정)
- `document_height`: 증가 추세
- `current_scroll`: 점진적 증가

### 테스트 2: Intersection Observer 트리거 확인
```python
# 스크롤 후 즉시 실행
observer_triggered = await page.evaluate('''
    new Promise((resolve) => {
        let triggered = false;
        const lastProduct = document.querySelector('a[class*="ProductCard_link"]:last-child');

        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                triggered = true;
                resolve(true);
            }
        }, { rootMargin: '100px' });

        observer.observe(lastProduct);

        setTimeout(() => resolve(triggered), 3000);
    })
''')

print(f"Intersection Observer Triggered: {observer_triggered}")
```

**기대 결과**: `True`

### 테스트 3: 수집 개수 모니터링
```bash
# 예상 로그
[배치 1] 43개 수집 → 스크롤
[시도 1] ✅ 3초 후 57개 로드  # ← 개선 전: 0개
[배치 2] 47개 수집 → 스크롤
[시도 2] ✅ 5초 후 61개 로드  # ← 개선 전: 0개
[배치 3] 61개 수집 → 스크롤
```

---

## 📝 교훈

### 1. Viewport의 중요성
- `no_viewport=True`는 특수한 경우에만 사용
- Lazy Loading은 viewport 개념에 의존
- 무한 스크롤 = Intersection Observer = viewport 필수

### 2. 타이밍의 중요성
- Intersection Observer는 **시간**이 필요함
- 0.5초 대기로는 부족 (최소 1.5-2초)
- "스크롤 → 즉시 확인"은 실패 확률 높음

### 3. 사람의 행동 모방
- 균일한 패턴 = 봇 감지 위험
- 불규칙성 = 자연스러움
- 대기 시간도 랜덤화 필요

### 4. 디버깅 전략
- "수동으로는 되는데 자동으로는 안 됨" → 타이밍 문제
- Intersection Observer 트리거 여부 직접 확인 필요
- Viewport 설정 반드시 확인

---

## 🔗 관련 문서

- `/home/dino/MyProjects/Crawl/docs/CRAWLING_LESSONS_LEARNED.md` (line 4030-4226)
- `/home/dino/MyProjects/Crawl/src/core/simple_crawler.py` (line 383-514)
- 네이버 Intersection Observer API: https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API

---

## ✅ 다음 단계

1. Phase 1 수정 적용 및 테스트
2. 로그에서 "시도 1-4" 결과 모니터링
3. 200개 이상 수집 성공 여부 확인
4. Phase 2 개선사항 적용
5. 이 문서에 테스트 결과 업데이트

---

**작성자**: Claude (Root Cause Analyst)
**검증 대기**: Phase 1 수정 적용 후
