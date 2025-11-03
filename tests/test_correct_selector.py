#!/usr/bin/env python3
"""
올바른 셀렉터 찾기 - 상품 이미지/상품명만 클릭
"""
import asyncio
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright

async def find_correct_selector():
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

        print("\n" + "="*60)
        print("셀렉터 테스트")
        print("="*60 + "\n")

        # 상품 이미지/상품명 관련 셀렉터 테스트
        selectors = [
            ('상품 이미지 링크', 'a:has(img[alt])'),
            ('상품 썸네일', 'a img[class*="thumb"]'),
            ('상품 카드 이미지', 'div[class*="product"] a:has(img)'),
            ('상품 링크 (img 포함)', 'a[href*="products"]:has(img)'),
            ('상품명 링크', 'a[class*="title"]'),
            ('상품명 링크2', 'a[class*="name"]'),
            ('이미지만', 'img[class*="image"]'),
            ('상품 카드 전체', 'div[class*="basicProductCard"]'),
        ]

        for desc, selector in selectors:
            try:
                count = await page.locator(selector).count()
                print(f"  [{desc:20s}] '{selector}': {count}개")

                # 처음 3개 URL 확인
                if count > 0 and 'a' in selector:
                    elements = await page.query_selector_all(selector)
                    print(f"    처음 3개 URL 확인:")
                    for i, elem in enumerate(elements[:3], 1):
                        try:
                            href = await elem.get_attribute('href')
                            if href:
                                # 판매자 스토어인지 상품 상세인지 구분
                                if '/products/' in href:
                                    print(f"      {i}. ✅ 상품: {href[:80]}")
                                elif 'smartstore.naver.com' in href:
                                    print(f"      {i}. ❌ 판매자: {href[:80]}")
                                else:
                                    print(f"      {i}. ⚠️  기타: {href[:80]}")
                        except:
                            pass
                    print()
            except Exception as e:
                print(f"  [{desc:20s}] 오류: {str(e)[:30]}")

        # 최적 셀렉터 추천
        print("\n" + "="*60)
        print("추천 셀렉터 분석")
        print("="*60)

        # 이미지 링크만
        img_links = await page.query_selector_all('a:has(img[alt])')
        product_count = 0
        seller_count = 0

        for link in img_links[:20]:
            href = await link.get_attribute('href')
            if href:
                if '/products/' in href:
                    product_count += 1
                elif 'smartstore.naver.com' in href and '/products/' not in href:
                    seller_count += 1

        print(f"\n'a:has(img[alt])' 분석 (처음 20개):")
        print(f"  - 상품 링크: {product_count}개 ✅")
        print(f"  - 판매자 링크: {seller_count}개 ❌")

        if product_count > seller_count:
            print(f"\n✅ 추천 셀렉터: 'a:has(img[alt])'")
        else:
            print(f"\n⚠️  추가 필터링 필요")

        print("\n브라우저 30초 유지 (확인용)")
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_correct_selector())
