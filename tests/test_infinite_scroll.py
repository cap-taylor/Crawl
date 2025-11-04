"""
네이버 쇼핑 무한 스크롤 테스트
목적: 실제로 스크롤 시 상품이 계속 로드되는지 확인
기존 SimpleCrawler 검증된 패턴 반영
"""
import asyncio
from playwright.async_api import async_playwright


async def test_scroll():
    """무한 스크롤 동작 테스트 - SimpleCrawler 패턴 사용"""

    async with async_playwright() as p:
        print("=== 네이버 쇼핑 무한 스크롤 테스트 ===\n")

        # ✅ SimpleCrawler와 동일한 브라우저 설정
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=300  # SimpleCrawler 설정
        )

        context = await browser.new_context(
            no_viewport=True,  # SimpleCrawler 설정
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )

        page = await context.new_page()

        try:
            # ✅ SimpleCrawler 네비게이션 흐름 (line 81-130)
            print("[1/4] 네이버 메인 페이지 접속...")
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(2)

            # ✅ 쇼핑 클릭 (SimpleCrawler line 87-96)
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

            # ✅ 카테고리 진입 (SimpleCrawler line 99-130)
            print("[3/4] 카테고리 버튼 클릭...")
            category_btn = await page.wait_for_selector('button:has-text("카테고리")')
            await category_btn.click()
            await asyncio.sleep(1)

            # 카테고리 메뉴에서 여성의류 클릭
            print("[4/4] 여성의류 카테고리 진입...")
            category_link = await page.wait_for_selector(f'a[href*="10000107"]')
            await category_link.click()
            await asyncio.sleep(3)

            # networkidle 대기
            await page.wait_for_load_state('networkidle')
            print("✓ 카테고리 페이지 로딩 완료")

            # ✅ 10초 대기 (SimpleCrawler line 132-135)
            print("\n페이지 안정화를 위해 10초 대기...")
            await asyncio.sleep(10)

            print("\n=== 무한 스크롤 테스트 시작 ===\n")

            # ✅ 초기 상품 개수 (SimpleCrawler line 147-149)
            initial_products = await page.query_selector_all('a[class*="ProductCard_link"]')
            batch_size = len(initial_products)
            print(f"초기 상품 수: {batch_size}개 → 배치 크기로 사용\n")

            # 스크롤 테스트 (최대 5회)
            for scroll_num in range(1, 6):
                print(f"========== 스크롤 테스트 #{scroll_num} ==========")

                # 현재 개수
                before_scroll = await page.query_selector_all('a[class*="ProductCard_link"]')
                before_count = len(before_scroll)
                print(f"📊 스크롤 전: {before_count}개")

                # ✅ 스크롤 실행 (SimpleCrawler line 258)
                print("⬇️  스크롤 실행 중...")
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')

                # 대기 시간 테스트: 3초, 5초, 7초, 10초
                wait_times = [3, 5, 7, 10]
                loaded_at = None

                for wait_time in wait_times:
                    print(f"   ⏳ {wait_time}초 대기 중...", end=" ")
                    await asyncio.sleep(wait_time - (wait_times[wait_times.index(wait_time) - 1] if wait_time != 3 else 0))

                    after_scroll = await page.query_selector_all('a[class*="ProductCard_link"]')
                    after_count = len(after_scroll)

                    if after_count > before_count:
                        increase = after_count - before_count
                        print(f"✅ {after_count}개 (증가: +{increase}개)")
                        loaded_at = wait_time
                        break
                    else:
                        print(f"❌ {after_count}개 (변화 없음)")

                # 최종 확인
                final_products = await page.query_selector_all('a[class*="ProductCard_link"]')
                final_count = len(final_products)

                print(f"\n📈 결과:")
                if final_count > before_count:
                    print(f"   스크롤 성공! {before_count}개 → {final_count}개")
                    print(f"   새로 로드: +{final_count - before_count}개")
                    print(f"   최적 대기 시간: {loaded_at}초\n")
                else:
                    print(f"   ❌ 스크롤 실패: {final_count}개 (변화 없음)")
                    print(f"   → 더 이상 새 상품이 로드되지 않습니다.\n")
                    break

                # 다음 스크롤 전 2초 대기
                await asyncio.sleep(2)

            print("\n=== 테스트 완료 ===")
            print("✅ 스크롤 동작 패턴 파악 완료")
            print("\n브라우저를 60초 후 종료합니다 (수동 스크롤 테스트 가능)...")
            await asyncio.sleep(60)

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_scroll())
