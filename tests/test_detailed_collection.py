#!/usr/bin/env python3
"""
상세 정보 수집 테스트 - price, search_tags 포함 모든 필드 검증
"""
import asyncio
import sys
import json
import re
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright
from datetime import datetime

async def collect_detailed_info():
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

        print("[2] 20초 대기 (캡차)")
        for i in range(20, 0, -5):
            print(f"  {i}초...")
            await asyncio.sleep(5)

        print("[3] 5초 추가 로딩")
        await asyncio.sleep(5)

        # 13번째 상품 찾기 (광고 12개 스킵)
        products = await page.query_selector_all('div[class*="product"] a')
        print(f"  {len(products)}개 상품 발견\n")

        clicked_urls = set()
        target_index = 13  # 13번째 상품

        for idx, product in enumerate(products, 1):
            href = await product.get_attribute('href')

            if not href or 'products' not in href or 'ader.naver.com' in href:
                continue

            if href in clicked_urls:
                continue

            clicked_urls.add(href)

            if idx == target_index:
                print(f"[{idx}번째 상품] 클릭...")
                await asyncio.sleep(2)
                await product.click(force=True)
                await asyncio.sleep(3)

                new_tab = context.pages[-1]
                try:
                    await new_tab.wait_for_load_state('networkidle', timeout=15000)
                except:
                    await asyncio.sleep(5)

                print("\n" + "="*70)
                print("상세 정보 수집 시작 (디버그 모드)")
                print("="*70 + "\n")

                # Product ID
                match = re.search(r'/products/(\d+)', href)
                product_id = match.group(1) if match else None
                print(f"✓ product_id: {product_id}")

                # Product Name (여러 셀렉터 시도)
                product_name = None
                name_selectors = [
                    'h3.product_title',
                    'h3[class*="title"]',
                    'h2[class*="product"]',
                    'div[class*="title"] h3',
                    'span[class*="name"]'
                ]
                for selector in name_selectors:
                    try:
                        elem = await new_tab.query_selector(selector)
                        if elem:
                            product_name = await elem.inner_text()
                            if product_name:
                                print(f"✓ product_name: {product_name[:60]} (셀렉터: {selector})")
                                break
                    except:
                        pass

                # Price (여러 셀렉터 시도)
                price_raw = None
                price_selectors = [
                    'span.price > em',
                    'span[class*="price"] em',
                    'strong[class*="price"]',
                    'em[class*="price"]',
                    'span.cost_price > em',
                    'div[class*="price"] span'
                ]
                for selector in price_selectors:
                    try:
                        elem = await new_tab.query_selector(selector)
                        if elem:
                            price_raw = await elem.inner_text()
                            if price_raw:
                                # 숫자만 추출
                                price_clean = re.sub(r'[^\d]', '', price_raw)
                                if price_clean:
                                    print(f"✓ price_raw: {price_raw} → {price_clean}원 (셀렉터: {selector})")
                                    break
                    except:
                        pass

                # Discount Rate
                discount_rate = None
                discount_selectors = [
                    'span.discount_rate',
                    'span[class*="discount"]',
                    'em[class*="discount"]'
                ]
                for selector in discount_selectors:
                    try:
                        elem = await new_tab.query_selector(selector)
                        if elem:
                            discount_text = await elem.inner_text()
                            if discount_text:
                                # 숫자만 추출
                                discount_clean = re.sub(r'[^\d]', '', discount_text)
                                if discount_clean:
                                    print(f"✓ discount_rate: {discount_text} → {discount_clean}% (셀렉터: {selector})")
                                    discount_rate = discount_clean
                                    break
                    except:
                        pass

                # Search Tags (점진적 스크롤로 찾기)
                print("\n--- 검색태그 찾기 (점진적 스크롤) ---")
                tags = []
                for scroll_pos in range(10, 61, 10):  # 10% ~ 60%
                    await new_tab.evaluate(f'window.scrollTo(0, document.body.scrollHeight * {scroll_pos/100})')
                    await asyncio.sleep(2)

                    # 모든 링크 확인 (제한 없음!)
                    all_links = await new_tab.query_selector_all('a')
                    print(f"  {scroll_pos}% 위치: {len(all_links)}개 링크 확인 중...")

                    temp_tags = []
                    for link in all_links:
                        try:
                            text = await link.inner_text()
                            if text and text.strip().startswith('#'):
                                clean_tag = text.strip().replace('#', '').strip()
                                if 1 < len(clean_tag) < 30 and clean_tag not in temp_tags:
                                    temp_tags.append(clean_tag)
                        except:
                            pass

                    if temp_tags:
                        print(f"  → {len(temp_tags)}개 태그 발견!")
                        tags = temp_tags
                        break

                print(f"\n✓ search_tags: {tags}")
                print(f"  총 {len(tags)}개")

                # Brand Name
                brand_name = None
                brand_selectors = [
                    'a.product_mall',
                    'a[class*="mall"]',
                    'span[class*="brand"]',
                    'div[class*="seller"] a'
                ]
                for selector in brand_selectors:
                    try:
                        elem = await new_tab.query_selector(selector)
                        if elem:
                            brand_name = await elem.inner_text()
                            if brand_name:
                                print(f"✓ brand_name: {brand_name} (셀렉터: {selector})")
                                break
                    except:
                        pass

                # Review Count & Rating
                review_count = None
                rating = None
                review_selectors = [
                    'span[class*="review"]',
                    'a[class*="review"]',
                    'em[class*="count"]'
                ]
                for selector in review_selectors:
                    try:
                        elem = await new_tab.query_selector(selector)
                        if elem:
                            review_text = await elem.inner_text()
                            if review_text:
                                # 숫자 추출
                                review_num = re.search(r'(\d+)', review_text)
                                if review_num:
                                    print(f"✓ review_count: {review_text} → {review_num.group(1)} (셀렉터: {selector})")
                                    review_count = review_num.group(1)
                                    break
                    except:
                        pass

                rating_selectors = [
                    'span[class*="rating"]',
                    'span.rating > em',
                    'strong[class*="score"]'
                ]
                for selector in rating_selectors:
                    try:
                        elem = await new_tab.query_selector(selector)
                        if elem:
                            rating_text = await elem.inner_text()
                            if rating_text:
                                print(f"✓ rating: {rating_text} (셀렉터: {selector})")
                                rating = rating_text
                                break
                    except:
                        pass

                # Thumbnail
                thumbnail = None
                img_selectors = [
                    'div.image img',
                    'img[class*="thumb"]',
                    'div[class*="image"] img'
                ]
                for selector in img_selectors:
                    try:
                        elem = await new_tab.query_selector(selector)
                        if elem:
                            thumbnail = await elem.get_attribute('src')
                            if thumbnail:
                                print(f"✓ thumbnail_url: {thumbnail[:80]}... (셀렉터: {selector})")
                                break
                    except:
                        pass

                # Is Sold Out
                is_sold_out = False
                soldout_selectors = [
                    'text="품절"',
                    'span:has-text("품절")',
                    'button:has-text("품절")'
                ]
                for selector in soldout_selectors:
                    try:
                        elem = await new_tab.query_selector(selector)
                        if elem:
                            is_sold_out = True
                            print(f"✓ is_sold_out: {is_sold_out} (발견)")
                            break
                    except:
                        pass

                print("\n" + "="*70)
                print("수집 완료!")
                print("="*70)

                await new_tab.close()
                break

        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(collect_detailed_info())
