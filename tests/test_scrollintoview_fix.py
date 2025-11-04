"""
scrollIntoView 방식 적용 후 무한 스크롤 검증 테스트
목적: simple_crawler.py 수정 후 실제로 무한 스크롤이 작동하는지 확인
"""
import asyncio
from playwright.async_api import async_playwright


async def test_scrollintoview_infinite():
    """scrollIntoView 방식으로 무한 스크롤 검증"""

    async with async_playwright() as p:
        print("=== scrollIntoView 방식 무한 스크롤 검증 ===\n")

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
            # SimpleCrawler 네비게이션 흐름
            print("[1/4] 네이버 메인 페이지 접속...")
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(2)

            print("[2/4] 쇼핑 버튼 클릭...")
            shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
            await page.locator(shopping_selector).click(timeout=10000)
            await asyncio.sleep(2)

            # 새 탭 전환
            all_pages = context.pages
            if len(all_pages) > 1:
                page = all_pages[-1]
                await page.wait_for_load_state('networkidle')
                print("✓ 쇼핑 탭 전환 완료")

            print("[3/4] 카테고리 버튼 클릭...")
            category_btn = await page.wait_for_selector('button:has-text("카테고리")')
            await category_btn.click()
            await asyncio.sleep(1)

            print("[4/4] 여성의류 카테고리 진입...")
            category_link = None
            selectors = [
                'a[href*="10000107"]',
                'text=여성의류',
                'a:has-text("여성의류")'
            ]

            for selector in selectors:
                try:
                    category_link = await page.wait_for_selector(selector, timeout=5000)
                    if category_link:
                        print(f"✓ 카테고리 링크 발견: {selector}")
                        break
                except:
                    continue

            if not category_link:
                print("❌ 여성의류 링크 못 찾음 - 테스트 중단")
                return

            await category_link.click()
            await asyncio.sleep(3)

            await page.wait_for_load_state('networkidle')
            print("✓ 카테고리 페이지 로딩 완료")

            print("\n페이지 안정화를 위해 10초 대기...")
            await asyncio.sleep(10)

            print("\n=== scrollIntoView 방식 무한 스크롤 테스트 ===\n")

            # 초기 상품 개수
            initial_products = await page.query_selector_all('a[class*="ProductCard_link"]')
            print(f"초기 상품 수: {len(initial_products)}개\n")

            # 5회 스크롤 테스트
            for scroll_num in range(1, 6):
                print(f"========== 스크롤 #{scroll_num} ==========")

                # 현재 개수
                before_products = await page.query_selector_all('a[class*="ProductCard_link"]')
                before_count = len(before_products)
                print(f"📊 스크롤 전: {before_count}개")

                # ✅ scrollIntoView 방식 (simple_crawler.py 적용 방식)
                print("⬇️  scrollIntoView 실행 중...")
                product_links = await page.query_selector_all('a[class*="ProductCard_link"]')
                if product_links:
                    last_product = product_links[-1]
                    await last_product.scroll_into_view_if_needed()
                    print("   ✓ 마지막 상품으로 스크롤 완료")
                else:
                    print("   ⚠️  상품 없음 - fallback 방식")
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')

                print("   ⏳ 3초 대기 중...")
                await asyncio.sleep(3)

                # 스크롤 후 개수 확인
                after_products = await page.query_selector_all('a[class*="ProductCard_link"]')
                after_count = len(after_products)

                print(f"\n📈 결과:")
                if after_count > before_count:
                    increase = after_count - before_count
                    print(f"   ✅ 성공! {before_count}개 → {after_count}개")
                    print(f"   새로 로드: +{increase}개\n")
                else:
                    print(f"   ❌ 실패: {after_count}개 (변화 없음)")
                    print(f"   → 더 이상 새 상품이 로드되지 않습니다.\n")
                    break

                await asyncio.sleep(2)

            print("\n=== 테스트 완료 ===")
            print("✅ scrollIntoView 방식 검증 완료")
            print("\n브라우저를 60초 후 종료합니다 (추가 수동 테스트 가능)...")
            await asyncio.sleep(60)

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_scrollintoview_infinite())
