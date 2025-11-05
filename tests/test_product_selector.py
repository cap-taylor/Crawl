#!/usr/bin/env python3
"""
정렬 옵션 이후 첫 번째 상품부터 정확히 선택하는 테스트
네이버 메인 → 쇼핑 → 카테고리 진입 (실제 크롤러와 동일)
"""
import asyncio
from playwright.async_api import async_playwright

async def test_product_selector():
    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,  # 화면 표시
            args=['--start-maximized']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )
        page = await context.new_page()

        # 1. 네이버 메인 → 쇼핑 진입 (실전 크롤러와 동일)
        print("[1/4] 네이버 메인 페이지 접속...")
        await page.goto('https://www.naver.com')
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(2)

        # 쇼핑 클릭
        print("[2/4] 쇼핑 버튼 클릭...")
        shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
        await page.locator(shopping_selector).click(timeout=10000, force=True)
        await asyncio.sleep(2)

        # 새 탭 전환
        all_pages = context.pages
        if len(all_pages) > 1:
            page = all_pages[-1]
            await page.wait_for_load_state('networkidle')

        # 2. 카테고리 진입 (실전 크롤러와 동일)
        print("[3/4] '신선식품' 카테고리 진입...")
        category_btn = await page.wait_for_selector('button:has-text("카테고리")', timeout=10000)
        await category_btn.click()

        # 카테고리 메뉴가 나타날 때까지 대기
        await asyncio.sleep(1)

        # 신선식품 카테고리 (ID: 10006530)
        category_id = "10006530"
        category_name = "신선식품"
        category_elem = None

        # 1순위: ID 기반
        try:
            category_elem = await page.wait_for_selector(f'#cat_layer_item_{category_id}', timeout=5000)
        except:
            pass

        # 2순위: data-id 속성
        if not category_elem:
            try:
                category_elem = await page.wait_for_selector(f'[data-id="{category_id}"]', timeout=3000)
            except:
                pass

        # 3순위: data-name 속성
        if not category_elem:
            try:
                category_elem = await page.wait_for_selector(f'a[data-name="{category_name}"]', timeout=3000)
            except:
                pass

        if not category_elem:
            raise Exception(f"카테고리 '{category_name}' (ID: {category_id})를 찾을 수 없습니다")

        await category_elem.click()
        await asyncio.sleep(3)

        # 캡차 체크 및 자동 포커스 (실전 크롤러와 동일)
        print("\n" + "="*60)
        print("[!] 캡차 확인 중...")
        print("="*60)

        # 캡차 해결 루프 (최대 3회 - 텍스트 캡차 + 영수증 캡차 반복 가능)
        for captcha_round in range(1, 4):
            print(f"\n[라운드 {captcha_round}] 캡차 확인 중...")

            # 1. 영수증 캡차 먼저 확인 (더 구체적인 패턴)
            receipt_captcha = None
            try:
                # 페이지 내용에서 "영수증" 키워드 확인
                page_text = await page.evaluate('document.body.innerText')
                if '영수증' in page_text and ('확인' in page_text or '새로고침' in page_text):
                    receipt_captcha = await page.wait_for_selector(
                        'input[type="text"], button:has-text("확인")',
                        timeout=1000,
                        state='visible'
                    )
            except:
                pass

            if receipt_captcha:
                print("🧾 영수증 캡차 감지! 답을 입력하세요.")
                print("브라우저에서 영수증을 보고 답을 입력한 후 확인 버튼을 클릭하세요")
                print("="*60)

                # 영수증 캡차 입력 필드 하이라이트
                try:
                    input_field = await page.wait_for_selector('input[type="text"]', timeout=2000)
                    await input_field.focus()
                    await input_field.click()

                    await page.evaluate("""
                        (element) => {
                            element.style.border = '3px solid #FF6B6B';
                            element.style.boxShadow = '0 0 15px #FF6B6B';
                            element.style.animation = 'pulse-red 1s infinite';

                            if (!document.getElementById('captcha-pulse-red-style')) {
                                const style = document.createElement('style');
                                style.id = 'captcha-pulse-red-style';
                                style.innerHTML = `
                                    @keyframes pulse-red {
                                        0% { box-shadow: 0 0 10px #FF6B6B; }
                                        50% { box-shadow: 0 0 20px #FF6B6B; }
                                        100% { box-shadow: 0 0 10px #FF6B6B; }
                                    }
                                `;
                                document.head.appendChild(style);
                            }
                        }
                    """, input_field)
                except:
                    pass

                # 영수증 캡차 해결 대기 (최대 120초)
                for i in range(120, 0, -10):
                    print(f"[대기] 영수증 캡차 대기 중... {i}초 남음")

                    # 확인 버튼이 사라졌는지 체크
                    try:
                        page_text = await page.evaluate('document.body.innerText')
                        if '영수증' not in page_text:
                            print("[✓] 영수증 캡차 해결 완료!")
                            await asyncio.sleep(3)
                            break
                    except:
                        pass

                    await asyncio.sleep(10)

                # 해결 후 다음 캡차 확인을 위해 계속
                continue

            # 2. 텍스트 입력 캡차 확인
            captcha_input = None
            try:
                captcha_input = await page.wait_for_selector(
                    'input#rcpt_answer',
                    timeout=1000,
                    state='visible'
                )
            except:
                pass

            if captcha_input:
                print("🔔 텍스트 캡차 감지! 입력 필드에 포커스를 맞췄습니다.")
                print("브라우저에서 캡차를 입력하고 Enter를 누르세요")
                print("="*60)

                await captcha_input.focus()
                await captcha_input.click()

                # 입력 필드를 노란색으로 하이라이트
                await page.evaluate("""
                    (element) => {
                        element.style.border = '3px solid #FFD700';
                        element.style.boxShadow = '0 0 10px #FFD700';
                        element.style.animation = 'pulse 1s infinite';

                        if (!document.getElementById('captcha-pulse-style')) {
                            const style = document.createElement('style');
                            style.id = 'captcha-pulse-style';
                            style.innerHTML = `
                                @keyframes pulse {
                                    0% { box-shadow: 0 0 10px #FFD700; }
                                    50% { box-shadow: 0 0 20px #FFD700; }
                                    100% { box-shadow: 0 0 10px #FFD700; }
                                }
                            `;
                            document.head.appendChild(style);
                        }
                    }
                """, captcha_input)

                # 캡차 해결 대기 (최대 60초)
                for i in range(60, 0, -5):
                    print(f"[대기] 텍스트 캡차 입력 대기 중... {i}초 남음")

                    try:
                        await page.wait_for_selector(
                            'input#rcpt_answer',
                            timeout=1000,
                            state='hidden'
                        )
                        print("[✓] 텍스트 캡차 해결 완료!")
                        await asyncio.sleep(2)
                        break
                    except:
                        pass

                    await asyncio.sleep(5)

                # 해결 후 다음 캡차 확인을 위해 계속
                continue

            # 캡차가 없으면 루프 종료
            print(f"[라운드 {captcha_round}] 캡차 없음")
            break

        print("\n[완료] 모든 캡차 확인 완료 - 페이지 로딩 대기 (5초)")
        await asyncio.sleep(5)

        print("[OK] 대기 완료! 상품 분석 시작...\n")
        print("="*60)
        await asyncio.sleep(2)

        # 상품 로딩 대기 (최대 10초)
        print("[대기] 상품 로딩 확인 중...")
        for i in range(10):
            product_count = await page.evaluate('''() => {
                return document.querySelectorAll('a[class*="ProductCard_link"]').length;
            }''')
            print(f"  시도 {i+1}: 상품 {product_count}개 발견")
            if product_count > 0:
                break
            await asyncio.sleep(1)

        if product_count == 0:
            print("[!] 경고: 상품이 로드되지 않았습니다. URL 확인:")
            current_url = page.url
            print(f"  현재 URL: {current_url}")

            # 페이지 상태 확인
            page_info = await page.evaluate('''() => {
                return {
                    title: document.title,
                    bodyText: document.body.innerText.substring(0, 500),
                    errorMessages: Array.from(document.querySelectorAll('[class*="error"], [class*="Error"], .notice')).map(e => e.innerText).join(' | '),
                    hasProducts: document.querySelectorAll('a[class*="ProductCard"]').length,
                    hasSortContainer: !!document.querySelector('#product-sort-address-container'),
                    allProductSelectors: document.querySelectorAll('a[href*="product"]').length
                };
            }''')

            print(f"  페이지 제목: {page_info['title']}")
            print(f"  정렬 컨테이너 존재: {page_info['hasSortContainer']}")
            print(f"  ProductCard 링크: {page_info['hasProducts']}개")
            print(f"  상품 링크 (전체): {page_info['allProductSelectors']}개")
            if page_info['errorMessages']:
                print(f"  에러 메시지: {page_info['errorMessages']}")
            print(f"  페이지 내용 (처음 200자):\n{page_info['bodyText'][:200]}")

            # 스크린샷 저장
            await page.screenshot(path='/home/dino/MyProjects/Crawl/temp/debug_no_products.png')
            print(f"  스크린샷 저장: /home/dino/MyProjects/Crawl/temp/debug_no_products.png")

            print("[!] 스크롤 시도 후 10초 더 대기...")
            await page.evaluate('window.scrollTo(0, 1000)')
            await asyncio.sleep(3)
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(7)

        print("\n" + "="*80)
        print("JavaScript 필터링 (실제 크롤러와 동일)")
        print("="*80)

        # JavaScript로 필터링 (실제 크롤러와 동일)
        filtered_count = await page.evaluate('''() => {
            // 1. 정렬 옵션 찾기
            const sort = document.querySelector('#product-sort-address-container');
            if (!sort) return {total: 0, filtered: 0};

            const sortY = sort.getBoundingClientRect().bottom;

            // 2. 모든 상품 링크 찾기
            const allLinks = Array.from(document.querySelectorAll('a[class*="ProductCard_link"]'));

            // 3. 정렬 옵션 아래 상품만 필터링하고 표시
            let filteredCount = 0;
            allLinks.forEach(link => {
                const rect = link.getBoundingClientRect();
                if (rect.top > sortY) {
                    link.setAttribute('data-filtered', 'true');
                    filteredCount++;
                } else {
                    link.setAttribute('data-filtered', 'false');
                }
            });

            return {total: allLinks.length, filtered: filteredCount};
        }''')

        print(f"전체 {filtered_count['total']}개 → 정렬 옵션 아래 {filtered_count['filtered']}개 선택\n")

        # 필터링된 상품만 가져오기
        filtered_links = await page.query_selector_all('a[data-filtered="true"]')
        print(f"필터링된 상품 링크 수: {len(filtered_links)}개")

        print("\n" + "="*80)
        print("필터링된 상품 200개 하나씩 분석 (빨간 테두리 - 3배 빠른 속도)")
        print("="*80)

        # 필터링된 상품을 하나씩 분석 (무한 스크롤 트리거하며)
        displayed_count = 0
        max_display = 200

        while displayed_count < max_display:
            # 현재 필터링된 상품 개수 확인
            current_links = await page.query_selector_all('a[data-filtered="true"]')
            current_count = len(current_links)

            print(f"\n[진행] {displayed_count}/{max_display} 표시 완료, 현재 로드된 상품: {current_count}개")

            # 더 이상 표시할 상품이 없으면 스크롤하여 추가 로드
            if displayed_count >= current_count:
                print(f"[스크롤] 추가 상품 로딩 중...")

                # 현재 스크롤 위치에서 800px만 더 스크롤 (조금씩만!)
                scroll_result = await page.evaluate('''() => {
                    const currentScroll = window.pageYOffset;
                    const newScroll = currentScroll + 800;  // 조금씩만 스크롤
                    window.scrollTo(0, newScroll);
                    return {
                        before: currentScroll,
                        after: newScroll
                    };
                }''')

                print(f"  스크롤: {scroll_result['before']}px → {scroll_result['after']}px (+800px)")
                await asyncio.sleep(2)

                # 스크롤 후 새로운 상품 필터링
                await page.evaluate('''() => {
                    const sort = document.querySelector('#product-sort-address-container');
                    if (!sort) return;
                    const sortY = sort.getBoundingClientRect().bottom;
                    const allLinks = Array.from(document.querySelectorAll('a[class*="ProductCard_link"]'));
                    allLinks.forEach(link => {
                        const rect = link.getBoundingClientRect();
                        if (rect.top > sortY && !link.hasAttribute('data-filtered')) {
                            link.setAttribute('data-filtered', 'true');
                        }
                    });
                }''')

                # 새로운 상품 개수 확인
                new_links = await page.query_selector_all('a[data-filtered="true"]')
                new_count = len(new_links)

                if new_count == current_count:
                    print(f"[완료] 더 이상 상품이 없습니다. 총 {current_count}개")
                    break

                print(f"[추가] {new_count - current_count}개 상품 로드됨")
                continue

            # 다음 10개 상품 표시
            batch_size = min(10, max_display - displayed_count, current_count - displayed_count)

            for i in range(displayed_count, displayed_count + batch_size):
                try:
                    # 상품 정보 수집 (개선된 셀렉터)
                    info = await page.evaluate(f'''(index) => {{
                        const links = document.querySelectorAll('a[data-filtered="true"]');
                        const link = links[index];
                        if (!link) return null;

                        // 이전 하이라이트 제거
                        links.forEach(l => {{
                            l.style.border = '';
                            l.style.outline = '';
                            l.style.boxShadow = '';
                        }});

                        // 현재 링크 하이라이트
                        link.style.border = '5px solid red';
                        link.style.outline = '3px solid yellow';
                        link.style.boxShadow = '0 0 20px red';
                        link.scrollIntoView({{ block: 'center', behavior: 'auto' }});

                        // 상품 정보 추출 (aria-labelledby 방식)
                        const rect = link.getBoundingClientRect();
                        const url = link.href || "";
                        const classes = link.className || "";

                        // aria-labelledby로 실제 정보 요소 찾기
                        const labelId = link.getAttribute('aria-labelledby');
                        const infoElem = labelId ? document.getElementById(labelId) : null;

                        let productName = "상품명 없음";
                        let price = "가격 없음";
                        let reviewCount = "리뷰 없음";

                        if (infoElem) {{
                            // 상품명 찾기
                            const titleElem = infoElem.querySelector('strong[class*="productCardTitle"]');
                            if (titleElem) {{
                                productName = titleElem.textContent.trim();
                            }}

                            // 가격 찾기
                            const priceElem = infoElem.querySelector('div[class*="productCardPrice"]');
                            if (priceElem) {{
                                // 할인 가격만 추출 (마지막 숫자)
                                const priceText = priceElem.textContent.trim();
                                const priceMatch = priceText.match(/(\d{{1,3}}(?:,\d{{3}})*원)(?!.*\d)/);
                                if (priceMatch) {{
                                    price = priceMatch[1];
                                }} else {{
                                    price = priceText.replace(/\s+/g, ' ').substring(0, 50);
                                }}
                            }}

                            // 리뷰 수 찾기
                            const reviewElem = infoElem.querySelector('div[class*="productCardReview"]');
                            if (reviewElem) {{
                                const reviewText = reviewElem.textContent.trim();
                                const reviewMatch = reviewText.match(/리뷰\s*([\d,]+)/);
                                if (reviewMatch) {{
                                    reviewCount = reviewMatch[1];
                                }} else {{
                                    reviewCount = reviewText.substring(0, 30);
                                }}
                            }}
                        }}

                        return {{
                            y: Math.round(rect.top),
                            url: url,
                            classes: classes,
                            productName: productName,
                            price: price,
                            reviewCount: reviewCount
                        }};
                    }}''', i)

                    if info is None:
                        print(f"\n[{i+1}번] 상품 없음 (인덱스 초과)")
                        break

                    await asyncio.sleep(0.33)  # 0.33초 대기 (3배 빠름)

                    print(f"\n[{i+1}번] Y위치: {info['y']}px")
                    print(f"  상품명: {info['productName']}")
                    print(f"  가격: {info['price']}")
                    print(f"  리뷰: {info['reviewCount']}")
                    print(f"  URL: {info['url'][:80]}...")

                except Exception as e:
                    print(f"\n[{i+1}번] 오류: {str(e)}")

            displayed_count += batch_size

        print("\n" + "="*80)
        print("분석 완료! 60초 후 브라우저를 닫습니다...")
        print("="*80)
        await asyncio.sleep(60)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_product_selector())
