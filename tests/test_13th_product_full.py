#!/usr/bin/env python3
"""
13번째 상품 전체 정보 추출 + 셀렉터 구조 분석
"""
import asyncio
import sys
import re
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright

async def analyze_13th_product():
    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=300
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

        await asyncio.sleep(5)

        # 13번째 상품 찾기
        products = await page.query_selector_all('a[class*="ProductCard_link"]')
        print(f"[3] {len(products)}개 상품 발견\n")

        clicked_urls = set()
        target_index = 13
        valid_count = 0  # 유효한 상품 카운터

        for idx, product in enumerate(products, 1):
            href = await product.get_attribute('href')

            if not href or 'products' not in href or 'ader.naver.com' in href:
                continue

            if href in clicked_urls:
                continue

            clicked_urls.add(href)
            valid_count += 1  # 유효한 상품 증가

            if valid_count == target_index:
                print(f"[{idx}번째 상품] 클릭...\n")
                await asyncio.sleep(2)
                await product.click(force=True)
                await asyncio.sleep(3)

                new_tab = context.pages[-1]
                try:
                    await new_tab.wait_for_load_state('networkidle', timeout=15000)
                except:
                    await asyncio.sleep(5)

                print("="*80)
                print("13번째 상품 전체 정보 추출 + 셀렉터 구조 분석")
                print("="*80 + "\n")

                # Product ID
                match = re.search(r'/products/(\d+)', href)
                product_id = match.group(1) if match else None
                print(f"✅ product_id: {product_id}")
                print(f"   URL: {href[:80]}\n")

                # === 1. 상품명 ===
                print("-" * 80)
                print("📦 상품명 (product_name)")
                print("-" * 80)
                name_selectors = [
                    'h3.product_title',
                    'h3[class*="title"]',
                    'h2[class*="product"]',
                    'div[class*="title"] h3',
                    'span[class*="name"]',
                    'h1',
                    'h2',
                    'h3',
                ]

                product_name = None
                for selector in name_selectors:
                    try:
                        elements = await new_tab.query_selector_all(selector)
                        if elements:
                            for elem in elements[:3]:
                                text = await elem.inner_text()
                                html = await elem.evaluate('el => el.outerHTML')
                                if text and len(text) > 5:
                                    print(f"\n✅ 발견: '{selector}'")
                                    print(f"   텍스트: {text[:80]}")
                                    print(f"   HTML: {html[:200]}...")
                                    if not product_name:
                                        product_name = text
                                    break
                    except:
                        pass

                # === 2. 브랜드명 ===
                print("\n" + "-" * 80)
                print("🏪 브랜드명 (brand_name)")
                print("-" * 80)
                brand_selectors = [
                    'a.product_mall',
                    'a[class*="mall"]',
                    'span[class*="brand"]',
                    'div[class*="seller"] a',
                    'a[class*="shop"]',
                ]

                brand_name = None
                for selector in brand_selectors:
                    try:
                        elements = await new_tab.query_selector_all(selector)
                        if elements:
                            for elem in elements[:3]:
                                text = await elem.inner_text()
                                html = await elem.evaluate('el => el.outerHTML')
                                if text:
                                    print(f"\n✅ 발견: '{selector}'")
                                    print(f"   텍스트: {text[:80]}")
                                    print(f"   HTML: {html[:200]}...")
                                    if not brand_name:
                                        brand_name = text
                                    break
                    except:
                        pass

                # === 3. 가격 ===
                print("\n" + "-" * 80)
                print("💰 가격 (price)")
                print("-" * 80)
                price_selectors = [
                    'span.price',
                    'span.price em',
                    'span[class*="price"] em',
                    'strong[class*="price"]',
                    'em[class*="price"]',
                    'div[class*="price"]',
                ]

                price = None
                for selector in price_selectors:
                    try:
                        elements = await new_tab.query_selector_all(selector)
                        if elements:
                            for elem in elements[:3]:
                                text = await elem.inner_text()
                                html = await elem.evaluate('el => el.outerHTML')
                                # 숫자 포함 여부 확인
                                if text and re.search(r'\d', text):
                                    print(f"\n✅ 발견: '{selector}'")
                                    print(f"   텍스트: {text}")
                                    print(f"   HTML: {html[:200]}...")
                                    # 숫자만 추출
                                    price_clean = re.sub(r'[^\d]', '', text)
                                    if price_clean and not price:
                                        price = price_clean
                                        print(f"   정제: {price_clean}원")
                    except:
                        pass

                # === 4. 할인율 ===
                print("\n" + "-" * 80)
                print("🏷️ 할인율 (discount_rate)")
                print("-" * 80)
                discount_selectors = [
                    'span.discount_rate',
                    'span[class*="discount"]',
                    'em[class*="discount"]',
                    'strong[class*="discount"]',
                ]

                discount_rate = None
                for selector in discount_selectors:
                    try:
                        elements = await new_tab.query_selector_all(selector)
                        if elements:
                            for elem in elements[:3]:
                                text = await elem.inner_text()
                                html = await elem.evaluate('el => el.outerHTML')
                                if text and '%' in text:
                                    print(f"\n✅ 발견: '{selector}'")
                                    print(f"   텍스트: {text}")
                                    print(f"   HTML: {html[:200]}...")
                                    discount_clean = re.sub(r'[^\d]', '', text)
                                    if discount_clean and not discount_rate:
                                        discount_rate = discount_clean
                                        print(f"   정제: {discount_clean}%")
                    except:
                        pass

                # === 5. 리뷰 수 ===
                print("\n" + "-" * 80)
                print("⭐ 리뷰 수 (review_count)")
                print("-" * 80)
                review_selectors = [
                    'span[class*="review"]',
                    'a[class*="review"]',
                    'em[class*="count"]',
                    'strong[class*="count"]',
                ]

                review_count = None
                for selector in review_selectors:
                    try:
                        elements = await new_tab.query_selector_all(selector)
                        if elements:
                            for elem in elements[:3]:
                                text = await elem.inner_text()
                                html = await elem.evaluate('el => el.outerHTML')
                                if text and re.search(r'\d', text):
                                    print(f"\n✅ 발견: '{selector}'")
                                    print(f"   텍스트: {text}")
                                    print(f"   HTML: {html[:200]}...")
                                    review_num = re.search(r'(\d+)', text)
                                    if review_num and not review_count:
                                        review_count = review_num.group(1)
                                        print(f"   정제: {review_count}개")
                    except:
                        pass

                # === 6. 평점 ===
                print("\n" + "-" * 80)
                print("⭐ 평점 (rating)")
                print("-" * 80)
                rating_selectors = [
                    'span[class*="rating"]',
                    'span.rating em',
                    'strong[class*="score"]',
                    'em[class*="rating"]',
                ]

                rating = None
                for selector in rating_selectors:
                    try:
                        elements = await new_tab.query_selector_all(selector)
                        if elements:
                            for elem in elements[:3]:
                                text = await elem.inner_text()
                                html = await elem.evaluate('el => el.outerHTML')
                                if text and re.search(r'\d', text):
                                    print(f"\n✅ 발견: '{selector}'")
                                    print(f"   텍스트: {text}")
                                    print(f"   HTML: {html[:200]}...")
                                    if not rating:
                                        rating = text
                    except:
                        pass

                # === 7. 검색태그 ===
                print("\n" + "-" * 80)
                print("🏷️ 검색태그 (search_tags)")
                print("-" * 80)
                print("점진적 스크롤 (10% ~ 70%):\n")

                tags = []
                for scroll_pos in range(10, 71, 10):
                    await new_tab.evaluate(f'window.scrollTo(0, document.body.scrollHeight * {scroll_pos/100})')
                    await asyncio.sleep(2)

                    all_links = await new_tab.query_selector_all('a')
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

                    print(f"  {scroll_pos}%: {len(all_links)}개 링크 → {len(temp_tags)}개 태그")

                    if temp_tags and not tags:
                        tags = temp_tags
                        # 첫 5개 태그의 HTML 구조 확인
                        print(f"\n  ✅ {len(tags)}개 태그 발견!")
                        print(f"  처음 5개: {tags[:5]}")

                        # 태그 HTML 구조 확인
                        print("\n  태그 HTML 구조 분석:")
                        tag_count = 0
                        for link in all_links:
                            try:
                                text = await link.inner_text()
                                if text and text.strip().startswith('#') and tag_count < 3:
                                    html = await link.evaluate('el => el.outerHTML')
                                    print(f"\n  태그 {tag_count + 1}: {text}")
                                    print(f"  HTML: {html[:300]}...")
                                    tag_count += 1
                            except:
                                pass
                        break

                if not tags:
                    print("\n  ❌ 태그를 찾지 못함")

                # === 8. 썸네일 ===
                print("\n" + "-" * 80)
                print("🖼️ 썸네일 (thumbnail_url)")
                print("-" * 80)

                img_selectors = [
                    'img[class*="image"]',
                    'div.image img',
                    'img[class*="thumb"]',
                    'img[alt]',
                ]

                thumbnail = None
                for selector in img_selectors:
                    try:
                        elements = await new_tab.query_selector_all(selector)
                        if elements:
                            elem = elements[0]
                            src = await elem.get_attribute('src')
                            html = await elem.evaluate('el => el.outerHTML')
                            if src:
                                print(f"\n✅ 발견: '{selector}'")
                                print(f"   src: {src[:100]}")
                                print(f"   HTML: {html[:300]}...")
                                if not thumbnail:
                                    thumbnail = src
                                break
                    except:
                        pass

                # === 9. 품절 여부 ===
                print("\n" + "-" * 80)
                print("❌ 품절 여부 (is_sold_out)")
                print("-" * 80)

                soldout_selectors = [
                    'text="품절"',
                    'span:has-text("품절")',
                    'button:has-text("품절")',
                    'div:has-text("품절")',
                ]

                is_sold_out = False
                for selector in soldout_selectors:
                    try:
                        elem = await new_tab.query_selector(selector)
                        if elem:
                            html = await elem.evaluate('el => el.outerHTML')
                            print(f"\n✅ 발견: '{selector}'")
                            print(f"   HTML: {html[:200]}...")
                            is_sold_out = True
                            break
                    except:
                        pass

                if not is_sold_out:
                    print("\n  상품 구매 가능 (품절 아님)")

                # === 최종 요약 ===
                print("\n" + "="*80)
                print("최종 수집 요약")
                print("="*80)
                print(f"product_id: {product_id}")
                print(f"product_name: {product_name[:60] if product_name else 'N/A'}...")
                print(f"brand_name: {brand_name if brand_name else 'N/A'}")
                print(f"price: {price if price else 'N/A'}원")
                print(f"discount_rate: {discount_rate if discount_rate else 'N/A'}%")
                print(f"review_count: {review_count if review_count else 'N/A'}개")
                print(f"rating: {rating if rating else 'N/A'}")
                print(f"search_tags: {len(tags)}개")
                if tags:
                    print(f"  → {tags[:10]}")
                print(f"thumbnail_url: {thumbnail[:60] if thumbnail else 'N/A'}...")
                print(f"is_sold_out: {is_sold_out}")

                await new_tab.close()
                break

        print("\n\n브라우저 30초 유지")
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_13th_product())
