"""
상세 페이지 셀렉터 테스트 스크립트
실제 상품 1개를 열어서 HTML 구조 확인
"""
import asyncio
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright

async def test_detail_page():
    # 스크린샷에서 보이는 상품 URL (예시)
    test_urls = [
        "https://smartstore.naver.com/outofit/products/11601678842",  # 로그에서 첫 번째 상품
    ]

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        for url in test_urls:
            print(f"\n{'='*80}")
            print(f"테스트 URL: {url}")
            print(f"{'='*80}\n")

            # 페이지 열기
            await page.goto(url)
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(3)

            # ==================== 상품명 ====================
            print("\n[1] 상품명:")
            selectors = ['h3', 'h2', 'h1', 'div[class*="title"]', 'span[class*="title"]']
            for sel in selectors:
                try:
                    elem = await page.query_selector(sel)
                    if elem:
                        text = await elem.text_content()
                        text = text.strip() if text else ''
                        if text and len(text) > 5:
                            print(f"  ✓ {sel}: {text[:60]}")
                            break
                except:
                    pass

            # ==================== 가격 ====================
            print("\n[2] 가격:")
            price_selectors = [
                'span.price em',
                'strong[class*="price"]',
                'em[class*="salePrice"]',
                'span[class*="price"]',
                'div[class*="price"]'
            ]
            for sel in price_selectors:
                try:
                    elems = await page.query_selector_all(sel)
                    for elem in elems:
                        text = await elem.text_content()
                        text = text.strip() if text else ''
                        if text and ('원' in text or text.isdigit()):
                            print(f"  ✓ {sel}: {text}")
                except:
                    pass

            # ==================== 브랜드 ====================
            print("\n[3] 브랜드:")
            brand_selectors = [
                'span[class*="brand"]',
                'a[class*="brand"]',
                'div[class*="seller"]',
                'span[class*="store"]',
                'div[class*="shop"]'
            ]
            for sel in brand_selectors:
                try:
                    elem = await page.query_selector(sel)
                    if elem:
                        text = await elem.text_content()
                        text = text.strip() if text else ''
                        if text and len(text) > 1 and len(text) < 50:
                            print(f"  ✓ {sel}: {text}")
                except:
                    pass

            # ==================== 할인율 ====================
            print("\n[4] 할인율:")
            discount_selectors = [
                'span[class*="discount"]',
                'em[class*="discount"]',
                'strong[class*="discount"]',
                'div:has-text("%")'
            ]
            for sel in discount_selectors:
                try:
                    elems = await page.query_selector_all(sel)
                    for elem in elems:
                        text = await elem.text_content()
                        text = text.strip() if text else ''
                        if text and '%' in text:
                            print(f"  ✓ {sel}: {text}")
                except:
                    pass

            # ==================== 리뷰 수 ====================
            print("\n[5] 리뷰 수:")
            review_selectors = [
                'span[class*="reviewCount"]',
                'em[class*="review"]',
                'span:has-text("리뷰")',
                'a:has-text("리뷰")'
            ]
            for sel in review_selectors:
                try:
                    elems = await page.query_selector_all(sel)
                    for elem in elems:
                        text = await elem.text_content()
                        text = text.strip() if text else ''
                        if text and ('리뷰' in text or text.replace(',', '').isdigit()):
                            print(f"  ✓ {sel}: {text}")
                except:
                    pass

            # ==================== 평점 ====================
            print("\n[6] 평점:")
            rating_selectors = [
                'span[class*="rating"]',
                'em[class*="star"]',
                'span[class*="star"]',
                'div[class*="rate"]'
            ]
            for sel in rating_selectors:
                try:
                    elems = await page.query_selector_all(sel)
                    for elem in elems:
                        text = await elem.text_content()
                        text = text.strip() if text else ''
                        if text and (text.replace('.', '').isdigit() or '점' in text):
                            print(f"  ✓ {sel}: {text}")
                except:
                    pass

            # ==================== HTML 스크린샷 ====================
            print("\n\n[전체 HTML 출력 - 가격 영역 근처]")
            print("페이지에서 '원' 텍스트가 포함된 모든 요소:")

            price_elements = await page.query_selector_all('*:has-text("원")')
            for i, elem in enumerate(price_elements[:10]):  # 처음 10개만
                try:
                    html = await elem.inner_html()
                    if len(html) < 200:  # 너무 긴 건 스킵
                        print(f"  [{i+1}] {html[:150]}")
                except:
                    pass

            print(f"\n{'='*80}")
            print("브라우저를 열어두었습니다. 60초 후 자동 종료...")
            print("개발자 도구 (F12)로 직접 확인하세요!")
            print("가격, 브랜드, 할인율 등의 실제 HTML 구조를 확인하세요!")
            print(f"{'='*80}\n")

            await asyncio.sleep(60)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_detail_page())
