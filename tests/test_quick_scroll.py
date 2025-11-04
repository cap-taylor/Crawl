#!/usr/bin/env python3
"""
빠른 무한 스크롤 검증 테스트 (상품 클릭 없이)
목적: 스크롤만 5회 반복해서 새 상품 로딩 확인 - 1분 완료
"""
import asyncio
from playwright.async_api import async_playwright


async def quick_scroll_test():
    """상품 클릭 없이 스크롤만 5회 테스트"""

    async with async_playwright() as p:
        print("=== 빠른 무한 스크롤 검증 (1분 완료) ===\n")

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
            # 네비게이션 (SimpleCrawler와 동일)
            print("[1/4] 네이버 메인 → 쇼핑...")
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(2)

            shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
            await page.locator(shopping_selector).click(timeout=10000)
            await asyncio.sleep(2)

            # 새 탭 전환
            all_pages = context.pages
            if len(all_pages) > 1:
                page = all_pages[-1]
                await page.wait_for_load_state('networkidle')

            print("[2/4] 카테고리 버튼...")
            category_btn = await page.wait_for_selector('button:has-text("카테고리")')
            await category_btn.click()
            await asyncio.sleep(1)

            print("[3/4] 여성의류...")
            category_link = await page.wait_for_selector('a[href*="10000107"]')
            await category_link.click()
            await asyncio.sleep(3)

            await page.wait_for_load_state('networkidle')
            print("[4/4] 10초 대기...\n")
            await asyncio.sleep(10)

            print("=== 스크롤 테스트 시작 ===\n")

            # 5회 스크롤
            for scroll_num in range(1, 6):
                before_products = await page.query_selector_all('a[class*="ProductCard_link"]')
                before_count = len(before_products)

                print(f"[스크롤 #{scroll_num}] 전: {before_count}개", end=" → ")

                # ✅ 부드러운 스크롤 (네이버 무한 스크롤 트리거)
                await asyncio.sleep(2)  # 페이지 안정화
                await page.evaluate('''
                    window.scrollTo({
                        top: document.body.scrollHeight,
                        behavior: 'smooth'
                    });
                ''')
                await asyncio.sleep(7)  # smooth 스크롤 + 서버 응답 대기

                after_products = await page.query_selector_all('a[class*="ProductCard_link"]')
                after_count = len(after_products)

                if after_count > before_count:
                    print(f"후: {after_count}개 ✅ (+{after_count - before_count}개)")
                else:
                    print(f"후: {after_count}개 ❌ (변화 없음)")
                    print("\n⚠️  무한 스크롤 실패!")
                    break

            print("\n=== 테스트 완료 ===")
            print("60초 후 종료...")
            await asyncio.sleep(60)

        except Exception as e:
            print(f"\n❌ 오류: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(quick_scroll_test())
