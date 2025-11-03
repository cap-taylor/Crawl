#!/usr/bin/env python3
"""
실제 셀렉터 찾기 - 카테고리 진입 후 상품 링크 분석
"""
import asyncio
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright

async def find_selectors():
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

        print("[1] 네이버 메인")
        await page.goto('https://www.naver.com')
        await asyncio.sleep(3)

        print("[2] 쇼핑 클릭")
        shopping = page.locator('#shortcutArea > ul > li:nth-child(4) > a')
        await shopping.click()
        await asyncio.sleep(3)

        page = context.pages[-1]
        await page.wait_for_load_state('networkidle')

        print("[3] 카테고리 클릭")
        category_btn = await page.wait_for_selector('button:has-text("카테고리")')
        await category_btn.click()
        await asyncio.sleep(2)

        print("[4] 여성의류 클릭")
        womens = await page.wait_for_selector('a[data-name="여성의류"]')
        await womens.click()

        print("[5] 20초 대기 (캡차 풀어주세요)")
        for i in range(20, 0, -5):
            print(f"  {i}초...")
            await asyncio.sleep(5)
        print("✅ 완료!\n")

        print("[6] 추가 5초 대기 (페이지 로딩)")
        await asyncio.sleep(5)

        print("\n" + "="*60)
        print("셀렉터 분석 시작")
        print("="*60 + "\n")

        # 다양한 셀렉터 테스트
        selectors = [
            'a[href*="/products/"]',
            'a[href*="/products/"]:has(img)',
            'a[href^="https://search.shopping.naver.com/catalog/"]',
            'a[href^="/catalog/"]',
            'div.product_item a',
            'div[class*="product"] a',
            'div[class*="Product"] a',
            'div[class*="item"] a',
            'a img[alt]',
            'a:has(img[alt])',
        ]

        results = []
        for selector in selectors:
            try:
                count = await page.locator(selector).count()
                results.append((selector, count))
                print(f"✓ '{selector}': {count}개")
            except Exception as e:
                print(f"✗ '{selector}': 오류 - {str(e)[:30]}")

        # 가장 많이 찾은 셀렉터
        print("\n" + "="*60)
        print("상위 3개 셀렉터")
        print("="*60)
        results.sort(key=lambda x: x[1], reverse=True)
        for selector, count in results[:3]:
            print(f"  {count}개: {selector}")

        if results[0][1] > 0:
            best_selector = results[0][0]
            print(f"\n✅ 최적 셀렉터: {best_selector}")

            # 첫 3개 상품 URL 확인
            print("\n" + "="*60)
            print("첫 5개 상품 URL 확인")
            print("="*60)
            products = await page.query_selector_all(best_selector)
            for i, product in enumerate(products[:5], 1):
                try:
                    href = await product.get_attribute('href')
                    text = await product.text_content()
                    print(f"[{i}] {href}")
                    if text:
                        print(f"    텍스트: {text[:50]}")
                except:
                    print(f"[{i}] 속성 읽기 실패")

        print("\n브라우저 30초간 유지 (확인용)")
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_selectors())
