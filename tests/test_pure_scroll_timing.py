"""
순수 스크롤 타이밍 측정 (상품 클릭 없이)
목적: 스크롤만 계속 내리면서 새 상품 로딩 시간 정확히 측정
"""
import asyncio
import time
from playwright.async_api import async_playwright


async def pure_scroll_test():
    """상품 클릭 없이 순수 스크롤만 반복"""

    async with async_playwright() as p:
        print("=== 순수 스크롤 타이밍 측정 (상품 클릭 없음) ===\n")

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
            # 네비게이션
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
                print("❌ 여성의류 링크 못 찾음")
                return

            await category_link.click()
            await asyncio.sleep(3)
            await page.wait_for_load_state('networkidle')
            print("✓ 카테고리 페이지 로딩 완료")

            print("\n페이지 안정화 10초 대기...")
            await asyncio.sleep(10)

            print("\n=== 순수 스크롤 테스트 (20회 반복) ===\n")

            # 20회 스크롤 테스트
            for test_num in range(1, 21):
                print(f"\n{'='*60}")
                print(f"스크롤 #{test_num}")
                print(f"{'='*60}")

                # 스크롤 전 개수
                before_products = await page.query_selector_all('a[class*="ProductCard_link"]')
                before_count = len(before_products)
                print(f"현재 상품: {before_count}개")

                # scrollIntoView 방식 (마지막 상품으로)
                print("⬇️  마지막 상품으로 스크롤...")
                if before_products:
                    last_product = before_products[-1]
                    scroll_start = time.time()
                    await last_product.scroll_into_view_if_needed()
                else:
                    scroll_start = time.time()
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')

                # 0.5초 간격으로 체크 (최대 15초)
                loaded = False
                for i in range(30):  # 30 * 0.5초 = 15초
                    await asyncio.sleep(0.5)

                    current_products = await page.query_selector_all('a[class*="ProductCard_link"]')
                    current_count = len(current_products)

                    if current_count > before_count:
                        elapsed = time.time() - scroll_start
                        increase = current_count - before_count
                        print(f"✅ 로딩 완료! {before_count}개 → {current_count}개 (+{increase}개)")
                        print(f"⏱️  소요 시간: {elapsed:.2f}초")
                        loaded = True
                        break
                    elif i > 0 and i % 4 == 0:  # 2초마다 출력
                        print(f"   [{i//2}초] 대기 중... (아직 {before_count}개)")

                if not loaded:
                    print(f"❌ 15초 내 로딩 안 됨 - 더 이상 상품 없을 가능성")

                    # 추가 확인: 5초 더 대기
                    print("   5초 더 대기 후 재확인...")
                    await asyncio.sleep(5)
                    final_products = await page.query_selector_all('a[class*="ProductCard_link"]')
                    final_count = len(final_products)

                    if final_count > before_count:
                        elapsed = time.time() - scroll_start
                        increase = final_count - before_count
                        print(f"   ✅ 늦게 로딩됨! {before_count}개 → {final_count}개 (+{increase}개)")
                        print(f"   ⏱️  총 소요 시간: {elapsed:.2f}초")
                    else:
                        print(f"   ❌ 확인: 더 이상 상품 없음 (최종 {final_count}개)")
                        break

                # 다음 스크롤 전 1초 대기
                await asyncio.sleep(1)

            print("\n\n=== 측정 완료 ===")
            print("브라우저를 60초 후 종료합니다...")
            await asyncio.sleep(60)

        except Exception as e:
            print(f"\n❌ 오류: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(pure_scroll_test())
