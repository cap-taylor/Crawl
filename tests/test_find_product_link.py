#!/usr/bin/env python3
"""
상품 링크 vs 판매자 링크 구분하기
"""
import asyncio
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright

async def find_product_links():
    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=500
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
        print("모든 링크 분석")
        print("="*70 + "\n")

        # 이전에 110개 찾았던 셀렉터
        all_links = await page.query_selector_all('div[class*="product"] a')
        print(f"총 {len(all_links)}개 링크 발견\n")

        product_links = []
        seller_links = []
        ad_links = []
        other_links = []

        for i, link in enumerate(all_links[:30], 1):  # 처음 30개만
            href = await link.get_attribute('href')
            class_name = await link.get_attribute('class')

            if not href:
                other_links.append(i)
                continue

            # 분류
            if 'ader.naver.com' in href:
                ad_links.append((i, href, class_name))
            elif '/products/' in href and 'smartstore.naver.com' in href:
                product_links.append((i, href, class_name))
            elif 'smartstore.naver.com' in href and '/products/' not in href:
                seller_links.append((i, href, class_name))
            else:
                other_links.append((i, href, class_name))

        print(f"📦 상품 링크: {len(product_links)}개")
        for idx, href, cls in product_links[:5]:
            print(f"  [{idx}] class='{cls}'")
            print(f"       {href[:80]}")

        print(f"\n🏪 판매자 링크: {len(seller_links)}개")
        for idx, href, cls in seller_links[:5]:
            print(f"  [{idx}] class='{cls}'")
            print(f"       {href[:80]}")

        print(f"\n📢 광고 링크: {len(ad_links)}개")
        print(f"⚠️  기타 링크: {len(other_links)}개")

        # 판매자 링크의 class 패턴 분석
        if seller_links:
            print("\n" + "="*70)
            print("판매자 링크 class 패턴")
            print("="*70)
            seller_classes = set()
            for _, _, cls in seller_links:
                if cls:
                    seller_classes.add(cls)

            for cls in list(seller_classes)[:10]:
                print(f"  - {cls}")

            # 제외할 class 패턴 찾기
            print("\n제외할 패턴:")
            if 'mall' in str(seller_classes).lower():
                print("  ✅ 'mall' 포함된 링크 제외")
            if 'shop' in str(seller_classes).lower():
                print("  ✅ 'shop' 포함된 링크 제외")
            if 'store' in str(seller_classes).lower():
                print("  ✅ 'store' 포함된 링크 제외")

        # 상품 링크의 class 패턴 분석
        if product_links:
            print("\n" + "="*70)
            print("상품 링크 class 패턴")
            print("="*70)
            product_classes = set()
            for _, _, cls in product_links:
                if cls:
                    product_classes.add(cls)

            for cls in list(product_classes)[:10]:
                print(f"  - {cls}")

            # 추천 셀렉터
            print("\n✅ 추천 셀렉터:")
            common_class = None
            for cls in product_classes:
                if cls:
                    common_class = cls.split()[0]  # 첫 번째 class
                    break

            if common_class:
                print(f"   a.{common_class}")
                print(f"   또는")
                print(f"   a[class*='{common_class}']")

        print("\n브라우저 30초 유지")
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_product_links())
