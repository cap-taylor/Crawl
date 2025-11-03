#!/usr/bin/env python3
"""
모든 정보 수집 테스트 - 발견한 셀렉터 적용
13번째 상품으로 전체 필드 검증
"""
import asyncio
import sys
import re
from datetime import datetime
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright

async def collect_all_info():
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

        await asyncio.sleep(5)

        # 13번째 상품 찾기
        products = await page.query_selector_all('a[class*="ProductCard_link"]')
        print(f"[3] {len(products)}개 상품 발견\n")

        clicked_urls = set()
        target_index = 13
        valid_count = 0

        for idx, product in enumerate(products, 1):
            href = await product.get_attribute('href')

            if not href or 'products' not in href or 'ader.naver.com' in href:
                continue

            if href in clicked_urls:
                continue

            clicked_urls.add(href)
            valid_count += 1

            if valid_count == target_index:
                print(f"[{valid_count}번째 상품] 클릭...\n")
                await asyncio.sleep(2)
                await product.click(force=True)
                await asyncio.sleep(3)

                new_tab = context.pages[-1]
                try:
                    await new_tab.wait_for_load_state('networkidle', timeout=15000)
                except:
                    await asyncio.sleep(5)

                print("="*80)
                print("전체 정보 수집 (발견한 셀렉터 적용)")
                print("="*80 + "\n")

                data = {}

                # 1. product_id
                match = re.search(r'/products/(\d+)', href)
                data['product_id'] = match.group(1) if match else None
                print(f"1. product_id: {data['product_id']}")

                # 2. category_name
                data['category_name'] = "여성의류"
                print(f"2. category_name: {data['category_name']}")

                # 3. product_name (h3.DCVBehA8ZB)
                try:
                    elem = await new_tab.query_selector('h3.DCVBehA8ZB')
                    if elem:
                        data['product_name'] = await elem.inner_text()
                    else:
                        data['product_name'] = None
                except:
                    data['product_name'] = None
                print(f"3. product_name: {data['product_name']}")

                # 4. brand_name (h1.ic78vHV230 - 스토어명)
                try:
                    elem = await new_tab.query_selector('h1.ic78vHV230')
                    if elem:
                        data['brand_name'] = await elem.inner_text()
                    else:
                        data['brand_name'] = None
                except:
                    data['brand_name'] = None
                print(f"4. brand_name: {data['brand_name']}")

                # 5. price (strong.Izp3Con8h8)
                try:
                    elem = await new_tab.query_selector('strong.Izp3Con8h8')
                    if elem:
                        price_text = await elem.inner_text()
                        # 숫자만 추출
                        price_clean = re.sub(r'[^\d]', '', price_text)
                        data['price'] = int(price_clean) if price_clean else None
                    else:
                        data['price'] = None
                except:
                    data['price'] = None
                print(f"5. price: {data['price']}원")

                # 6. discount_rate (여러 방법 시도)
                data['discount_rate'] = None
                try:
                    # 방법 1: JavaScript로 "40%" 텍스트 찾기
                    discount_result = await new_tab.evaluate('''() => {
                        const allElements = document.querySelectorAll('*');
                        for (let elem of allElements) {
                            const text = elem.textContent || '';
                            if (text.includes('%') && text.length < 20) {
                                const match = text.match(/(\\d+)%/);
                                if (match && elem.children.length <= 1) {
                                    return match[1];
                                }
                            }
                        }
                        return null;
                    }''')
                    if discount_result:
                        data['discount_rate'] = int(discount_result)
                except:
                    pass
                print(f"6. discount_rate: {data['discount_rate']}%")

                # 7. review_count ("리뷰 10" 탭에서)
                data['review_count'] = None
                try:
                    # "리뷰" 텍스트 포함된 요소 찾기
                    review_result = await new_tab.evaluate('''() => {
                        const allElements = document.querySelectorAll('*');
                        for (let elem of allElements) {
                            const text = elem.textContent || '';
                            if (text.includes('리뷰') && text.length < 20) {
                                const match = text.match(/리뷰\\s*(\\d+)/);
                                if (match) {
                                    return match[1];
                                }
                            }
                        }
                        return null;
                    }''')
                    if review_result:
                        data['review_count'] = int(review_result)
                except:
                    pass
                print(f"7. review_count: {data['review_count']}개")

                # 8. rating (평점)
                data['rating'] = None
                try:
                    # "평점", "별점", 숫자.숫자 패턴 찾기
                    rating_result = await new_tab.evaluate('''() => {
                        const allElements = document.querySelectorAll('*');
                        for (let elem of allElements) {
                            const text = elem.textContent || '';
                            // "4.5", "평점 4.5" 같은 패턴
                            if ((text.includes('평점') || text.includes('별점')) && text.length < 30) {
                                const match = text.match(/(\\d+\\.\\d+|\\d+)/);
                                if (match) {
                                    return match[1];
                                }
                            }
                        }
                        return null;
                    }''')
                    if rating_result:
                        data['rating'] = float(rating_result)
                except:
                    pass
                print(f"8. rating: {data['rating']}")

                # 9. search_tags (점진적 스크롤 - a.og34GRpFBf)
                print("\n9. search_tags 수집 중...")
                data['search_tags'] = []

                for scroll_pos in range(10, 71, 10):
                    await new_tab.evaluate(f'window.scrollTo(0, document.body.scrollHeight * {scroll_pos/100})')
                    await asyncio.sleep(2)

                    # 모든 링크에서 # 시작하는 텍스트 찾기
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

                    if temp_tags:
                        data['search_tags'] = temp_tags
                        print(f"   {scroll_pos}% 위치에서 {len(temp_tags)}개 발견!")
                        break

                print(f"   최종: {len(data['search_tags'])}개")
                if data['search_tags']:
                    print(f"   → {data['search_tags'][:10]}")

                # 10. product_url
                data['product_url'] = href
                print(f"\n10. product_url: {href[:80]}...")

                # 11. thumbnail_url (img[class*="image"])
                try:
                    elem = await new_tab.query_selector('img[class*="image"]')
                    if elem:
                        data['thumbnail_url'] = await elem.get_attribute('src')
                    else:
                        data['thumbnail_url'] = None
                except:
                    data['thumbnail_url'] = None
                print(f"11. thumbnail_url: {data['thumbnail_url'][:80] if data['thumbnail_url'] else 'N/A'}...")

                # 12. is_sold_out
                data['is_sold_out'] = False
                try:
                    # "품절" 텍스트 찾기 (단, Q&A 내용 제외)
                    soldout_result = await new_tab.evaluate('''() => {
                        const allElements = document.querySelectorAll('*');
                        for (let elem of allElements) {
                            const text = elem.textContent || '';
                            // "품절" 단어가 있고, 짧은 텍스트 (버튼이나 상태 표시)
                            if (text.includes('품절') && text.length < 50 && !text.includes('Q.')) {
                                // 부모 요소가 버튼이거나 상태 표시 요소인 경우
                                if (elem.tagName === 'BUTTON' || elem.tagName === 'SPAN') {
                                    return true;
                                }
                            }
                        }
                        return false;
                    }''')
                    data['is_sold_out'] = soldout_result
                except:
                    pass
                print(f"12. is_sold_out: {data['is_sold_out']}")

                # 13, 14. 타임스탬프
                data['crawled_at'] = datetime.now().isoformat()
                data['updated_at'] = datetime.now().isoformat()
                print(f"13. crawled_at: {data['crawled_at']}")
                print(f"14. updated_at: {data['updated_at']}")

                # 최종 요약
                print("\n" + "="*80)
                print("수집 완료 - DB 스키마 전체 (14개 필드)")
                print("="*80)

                import json
                print(json.dumps(data, ensure_ascii=False, indent=2))

                print("\n" + "="*80)
                print("수집 통계")
                print("="*80)
                filled = sum(1 for k, v in data.items() if v not in [None, [], 0])
                total = len(data)
                print(f"필드 채움률: {filled}/{total} ({filled/total*100:.1f}%)")
                print(f"누락 필드: {[k for k, v in data.items() if v in [None, [], 0]]}")

                await new_tab.close()
                break

        print("\n브라우저 30초 유지")
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(collect_all_info())
