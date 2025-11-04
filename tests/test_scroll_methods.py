"""
네이버 쇼핑 스크롤 방식 비교 테스트
목적: 3가지 스크롤 방식 중 어떤 게 무한 스크롤을 트리거하는지 확인
"""
import asyncio
from playwright.async_api import async_playwright


async def test_scroll_methods():
    """3가지 스크롤 방식 비교 테스트"""

    async with async_playwright() as p:
        print("=== 네이버 쇼핑 스크롤 방식 비교 테스트 ===\n")

        # SimpleCrawler와 동일한 브라우저 설정
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
            # 여러 셀렉터 시도
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

            # 초기 상품 개수
            initial_products = await page.query_selector_all('a[class*="ProductCard_link"]')
            print(f"\n초기 상품 수: {len(initial_products)}개\n")

            print("=" * 60)
            print("스크롤 방식 비교 테스트 시작")
            print("=" * 60)

            # ==========================================
            # 방식 1: 단계적 스크롤 (여러 번 나눠서)
            # ==========================================
            print("\n\n【방식 1】 단계적 스크롤 (500px씩 5번)")
            print("-" * 60)

            before_count = len(await page.query_selector_all('a[class*="ProductCard_link"]'))
            print(f"스크롤 전: {before_count}개")

            # 500px씩 5번 스크롤 (총 2500px)
            for i in range(5):
                await page.evaluate('window.scrollBy(0, 500)')
                await asyncio.sleep(0.5)
                print(f"  [{i+1}/5] 500px 스크롤...")

            print("3초 대기 중...")
            await asyncio.sleep(3)

            after_count = len(await page.query_selector_all('a[class*="ProductCard_link"]'))
            print(f"스크롤 후: {after_count}개")

            if after_count > before_count:
                print(f"✅ 성공! +{after_count - before_count}개 로드됨")
            else:
                print(f"❌ 실패 (변화 없음)")

            await asyncio.sleep(2)

            # ==========================================
            # 방식 2: scrollIntoView (마지막 상품으로)
            # ==========================================
            print("\n\n【방식 2】 scrollIntoView (마지막 상품)")
            print("-" * 60)

            before_count = len(await page.query_selector_all('a[class*="ProductCard_link"]'))
            print(f"스크롤 전: {before_count}개")

            # 마지막 상품 찾기
            products = await page.query_selector_all('a[class*="ProductCard_link"]')
            if products:
                last_product = products[-1]
                await last_product.scroll_into_view_if_needed()
                print("마지막 상품으로 스크롤 완료")

            print("3초 대기 중...")
            await asyncio.sleep(3)

            after_count = len(await page.query_selector_all('a[class*="ProductCard_link"]'))
            print(f"스크롤 후: {after_count}개")

            if after_count > before_count:
                print(f"✅ 성공! +{after_count - before_count}개 로드됨")
            else:
                print(f"❌ 실패 (변화 없음)")

            await asyncio.sleep(2)

            # ==========================================
            # 방식 3: 페이지 끝까지 반복 스크롤
            # ==========================================
            print("\n\n【방식 3】 반복 스크롤 (현재 높이 → 새 높이)")
            print("-" * 60)

            before_count = len(await page.query_selector_all('a[class*="ProductCard_link"]'))
            print(f"스크롤 전: {before_count}개")

            # 현재 높이 저장
            current_height = await page.evaluate('document.body.scrollHeight')
            print(f"현재 페이지 높이: {current_height}px")

            # 끝까지 스크롤
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1)

            # 새 높이까지 다시 스크롤
            new_height = await page.evaluate('document.body.scrollHeight')
            print(f"새 페이지 높이: {new_height}px")

            if new_height > current_height:
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                print("새 높이까지 재스크롤 완료")

            print("3초 대기 중...")
            await asyncio.sleep(3)

            after_count = len(await page.query_selector_all('a[class*="ProductCard_link"]'))
            print(f"스크롤 후: {after_count}개")

            if after_count > before_count:
                print(f"✅ 성공! +{after_count - before_count}개 로드됨")
            else:
                print(f"❌ 실패 (변화 없음)")

            # ==========================================
            # 최종 결과 요약
            # ==========================================
            print("\n\n" + "=" * 60)
            print("테스트 완료 - 가장 효과적인 방식을 확인하세요")
            print("=" * 60)

            print("\n브라우저를 60초 후 종료합니다 (추가 수동 테스트 가능)...")
            await asyncio.sleep(60)

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_scroll_methods())
