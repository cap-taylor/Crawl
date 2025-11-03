"""
단순화된 크롤링 테스트: Ctrl+클릭 → 새 탭 → 수집 → 탭 닫기
"""
import asyncio
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright
import random

async def test_simple_crawl():
    """3개만 수집 테스트"""
    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=1000
        )

        context = await browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            locale='ko-KR'
        )

        page = await context.new_page()

        # 네이버 → 쇼핑 → 여성의류
        print("[1] 네이버 메인")
        await page.goto('https://www.naver.com')
        await asyncio.sleep(3)

        print("[2] 쇼핑 클릭")
        shopping = page.locator('#shortcutArea > ul > li:nth-child(4) > a')
        await shopping.click()
        await asyncio.sleep(3)

        # 새 탭 전환
        page = context.pages[-1]
        await page.wait_for_load_state('networkidle')

        print("[3] 카테고리 클릭")
        category_btn = await page.wait_for_selector('button:has-text("카테고리")')
        await category_btn.click()
        await asyncio.sleep(2)

        print("[4] 여성의류 클릭")
        womens = await page.wait_for_selector('a[data-name="여성의류"]')
        await womens.click()
        await asyncio.sleep(5)

        print("\n[5] 상품 수집 시작 (Ctrl+클릭 방식)\n")

        collected_urls = set()
        found_count = 0
        target_count = 3

        while found_count < target_count:
            # 현재 화면의 상품 링크 찾기
            products = await page.query_selector_all('a[href*="/products/"]:has(img)')

            # 새 상품만 클릭
            for product in products:
                if found_count >= target_count:
                    break

                href = await product.get_attribute('href')
                if not href or href in collected_urls:
                    continue

                if not '/products/' in href:
                    continue

                collected_urls.add(href)

                print(f"[상품 {found_count + 1}] 클릭...")

                # 랜덤 대기 (사람처럼)
                await asyncio.sleep(random.uniform(2.0, 4.0))

                # Ctrl+클릭으로 새 탭 열기
                await product.click(modifiers=['Control'])
                await asyncio.sleep(2)

                # 새 탭 찾기
                if len(context.pages) > 1:
                    new_tab = context.pages[-1]
                    await new_tab.wait_for_load_state('domcontentloaded')

                    # 상품명 수집
                    try:
                        title_elem = await new_tab.wait_for_selector('h2, h3', timeout=3000)
                        title = await title_elem.inner_text()
                        print(f"   → [{title[:40]}] ✅")
                        found_count += 1
                    except:
                        print(f"   → 수집 실패")

                    # 탭 닫기
                    await new_tab.close()
                    await asyncio.sleep(random.uniform(1.0, 2.0))

            # 목표 달성하면 종료
            if found_count >= target_count:
                break

            # 스크롤 (새 상품 로딩)
            print("\n[스크롤] 새 상품 로딩...\n")
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(3)

        print(f"\n{'='*60}")
        print(f"[완료] {found_count}개 수집 완료!")
        print(f"{'='*60}")

        await asyncio.sleep(3)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_simple_crawl())
