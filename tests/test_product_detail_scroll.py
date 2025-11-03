#!/usr/bin/env python3
"""
상품 상세 페이지 스크롤 최적화 테스트

목적: 13개 필드가 어느 스크롤 위치에 나타나는지 확인
"""

import asyncio
from playwright.async_api import async_playwright


async def test_product_detail():
    print("="*70)
    print("상품 상세 페이지 필드 위치 확인 테스트")
    print("="*70)

    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=300
        )

        context = await browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )

        page = await context.new_page()

        try:
            # 봇 차단 방지: 네이버 메인 → 쇼핑 → 카테고리 → 상품 클릭
            print("\n[1단계] 네이버 메인 페이지 접속...")
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(2)

            print("[2단계] 쇼핑 버튼 클릭...")
            shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
            await page.locator(shopping_selector).click(timeout=10000)
            await asyncio.sleep(2)

            # 새 탭 전환
            all_pages = context.pages
            if len(all_pages) > 1:
                page = all_pages[-1]
                await page.wait_for_load_state('networkidle')

            print("[3단계] 여성의류 카테고리 진입...")
            category_btn = await page.wait_for_selector('button:has-text("카테고리")')
            await category_btn.click()
            await asyncio.sleep(1)

            womens = await page.wait_for_selector('a[data-name="여성의류"]')
            await womens.click()
            await asyncio.sleep(3)

            # 캡차 대기 (15초 고정)
            print("\n" + "="*60)
            print("⚠️  캡차 확인 - 15초 대기")
            print("="*60)
            print("브라우저에서 캡차를 수동으로 해결해주세요")
            print("="*60)
            for i in range(15, 0, -5):
                print(f"[대기] 남은 시간: {i}초...")
                await asyncio.sleep(5)
            print("✅ 대기 완료! 크롤링 시작...\n")
            await asyncio.sleep(2)

            # 15번째 상품 클릭 (광고 14개 건너뛰기)
            print("\n[4단계] 15번째 상품 클릭...")
            product_links = await page.query_selector_all('a[class*="ProductCard_link"]')
            print(f"현재 로드된 상품: {len(product_links)}개")

            if len(product_links) >= 15:
                product_15 = product_links[14]  # 0-indexed이므로 14
                await product_15.click()
                await asyncio.sleep(2)

                # 새 탭 찾기
                all_pages = context.pages
                if len(all_pages) > 1:
                    detail_page = all_pages[-1]
                    await detail_page.wait_for_load_state('domcontentloaded')
                    await asyncio.sleep(2)
                    page = detail_page
                    print("✅ 상품 상세 페이지 접속 성공!")
            else:
                print(f"❌ 상품 개수 부족: {len(product_links)}개")
                return

            print("\n[5단계] 스크롤 없이 수집 가능한 필드 확인...")

            # 1. product_name
            elem = await page.query_selector('h3.DCVBehA8ZB')
            product_name = await elem.inner_text() if elem else None
            print(f"✅ product_name: {product_name[:50] if product_name else 'None'}...")

            # 2. price
            elem = await page.query_selector('strong.Izp3Con8h8')
            if elem:
                price_text = await elem.inner_text()
                print(f"✅ price: {price_text}")
            else:
                print("❌ price: Not found")

            # 3. discount_rate
            discount_result = await page.evaluate('''() => {
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
            print(f"{'✅' if discount_result else '❌'} discount_rate: {discount_result}%")

            # 4. review_count
            review_result = await page.evaluate('''() => {
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
            print(f"{'✅' if review_result else '❌'} review_count: {review_result}")

            # 5. rating
            rating_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    if ((text.includes('평점') || text.includes('별점')) && text.length < 30) {
                        const match = text.match(/(\\d+\\.\\d+)/);
                        if (match) {
                            return parseFloat(match[1]);
                        }
                    }
                }
                return null;
            }''')
            print(f"{'✅' if rating_result else '❌'} rating: {rating_result}")

            # 6. thumbnail_url
            elem = await page.query_selector('img[class*="image"]')
            thumbnail = await elem.get_attribute('src') if elem else None
            print(f"{'✅' if thumbnail else '❌'} thumbnail_url: {thumbnail[:50] if thumbnail else 'None'}...")

            print("\n[6단계] 30% 스크롤 후 brand_name 확인...")
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.3)')
            await asyncio.sleep(1)

            brand_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('td, th');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    if (text.trim() === '브랜드') {
                        const nextTd = elem.nextElementSibling;
                        if (nextTd) {
                            const brandValue = nextTd.textContent.trim();
                            if (brandValue && brandValue.length < 50) {
                                return brandValue;
                            }
                        }
                    }
                }
                return null;
            }''')
            print(f"{'✅' if brand_result else '❌'} brand_name: {brand_result}")

            print("\n[7단계] 50% 스크롤 후 search_tags 확인...")
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.5)')
            await asyncio.sleep(1)

            tags_50 = set()
            all_links = await page.query_selector_all('a')
            for link in all_links:
                try:
                    text = await link.inner_text()
                    if text and text.strip().startswith('#'):
                        clean_tag = text.strip().replace('#', '').strip()
                        if 1 < len(clean_tag) < 30:
                            tags_50.add(clean_tag)
                except:
                    pass
            print(f"50% 위치 태그 개수: {len(tags_50)}개")

            print("\n[8단계] 70% 스크롤 후 search_tags 확인...")
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.7)')
            await asyncio.sleep(1)

            tags_70 = set()
            all_links = await page.query_selector_all('a')
            for link in all_links:
                try:
                    text = await link.inner_text()
                    if text and text.strip().startswith('#'):
                        clean_tag = text.strip().replace('#', '').strip()
                        if 1 < len(clean_tag) < 30:
                            tags_70.add(clean_tag)
                except:
                    pass
            print(f"70% 위치 태그 개수: {len(tags_70)}개")

            print("\n[9단계] 100% 스크롤 후 search_tags 확인...")
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1)

            tags_100 = set()
            all_links = await page.query_selector_all('a')
            for link in all_links:
                try:
                    text = await link.inner_text()
                    if text and text.strip().startswith('#'):
                        clean_tag = text.strip().replace('#', '').strip()
                        if 1 < len(clean_tag) < 30:
                            tags_100.add(clean_tag)
                except:
                    pass
            print(f"100% 위치 태그 개수: {len(tags_100)}개")

            print("\n" + "="*70)
            print("결과 요약")
            print("="*70)
            print("스크롤 0% (초기):")
            print(f"  - product_name, price, discount_rate, review_count, rating, thumbnail_url")
            print(f"\n스크롤 30%:")
            print(f"  - brand_name")
            print(f"\n검색 태그 수집:")
            print(f"  - 50%: {len(tags_50)}개")
            print(f"  - 70%: {len(tags_70)}개")
            print(f"  - 100%: {len(tags_100)}개")

            if len(tags_70) > 0 and len(tags_100) == len(tags_70):
                print(f"\n✅ 최적화 가능: 70%까지만 스크롤해도 모든 태그 수집 가능!")
            else:
                print(f"\n⚠️ 100%까지 스크롤 필요")

            print("\n브라우저를 10초간 유지합니다. 직접 확인해보세요.")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_product_detail())
