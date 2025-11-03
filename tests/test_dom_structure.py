#!/usr/bin/env python3
"""
DOM 구조 분석 - 실제 HTML 구조 확인
"""
import asyncio
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright

async def analyze_dom():
    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=1000
        )

        context = await browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            extra_http_headers={
                'Accept-Language': 'ko-KR,ko;q=0.9'
            }
        )

        page = await context.new_page()

        print("[1] 네이버 → 쇼핑 → 여성의류")
        await page.goto('https://www.naver.com')
        await asyncio.sleep(2)

        shopping = page.locator('#shortcutArea > ul > li:nth-child(4) > a')
        await shopping.click()
        await asyncio.sleep(2)

        page = context.pages[-1]
        await page.wait_for_load_state('networkidle')

        category_btn = await page.wait_for_selector('button:has-text("카테고리")')
        await category_btn.click()
        await asyncio.sleep(1)

        womens = await page.wait_for_selector('a[data-name="여성의류"]')
        await womens.click()

        print("[2] 20초 대기")
        for i in range(20, 0, -5):
            print(f"  {i}초...")
            await asyncio.sleep(5)

        await asyncio.sleep(5)

        print("\n" + "="*70)
        print("첫 번째 상품 카드 HTML 구조 분석")
        print("="*70 + "\n")

        # 상품 카드 찾기
        product_cards = await page.query_selector_all('div[class*="basicProductCard"]')

        if product_cards:
            print(f"총 {len(product_cards)}개 상품 카드 발견\n")

            # 첫 번째 카드 HTML 출력
            first_card = product_cards[0]
            html = await first_card.inner_html()

            print("=== 첫 번째 상품 카드 HTML (앞 2000자) ===")
            print(html[:2000])
            print("\n...")

            # 카드 내 모든 링크 찾기
            links = await first_card.query_selector_all('a')
            print(f"\n=== 카드 내 링크 분석 ({len(links)}개) ===")

            for i, link in enumerate(links, 1):
                href = await link.get_attribute('href')
                class_name = await link.get_attribute('class')
                text = await link.inner_text()

                # 링크 타입 판별
                link_type = "기타"
                if href:
                    if '/products/' in href:
                        link_type = "✅ 상품"
                    elif 'smartstore.naver.com' in href and '/products/' not in href:
                        link_type = "❌ 판매자"

                print(f"\n링크 {i}:")
                print(f"  타입: {link_type}")
                print(f"  class: {class_name}")
                print(f"  text: {text[:50] if text else '(없음)'}")
                print(f"  href: {href[:80] if href else '(없음)'}")

        print("\n브라우저 60초 유지 (확인용)")
        await asyncio.sleep(60)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_dom())
