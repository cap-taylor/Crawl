"""
방법 4: 검색으로 남성의류 접근 (가장 쉬운 방법)
"""

import asyncio
from playwright.async_api import async_playwright

async def test_search():
    print("검색으로 남성의류 접근 테스트")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False, slow_mo=500, args=['--kiosk'])
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # 네이버 메인 → 쇼핑
            print("1. 네이버 메인 접속...")
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            print("2. 쇼핑 클릭...")
            shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a')
            await shopping_link.click()
            await asyncio.sleep(3)

            # 새 탭 전환
            if len(context.pages) > 1:
                page = context.pages[-1]
                await page.wait_for_load_state('networkidle')
                print("3. 쇼핑 탭 전환 완료")

            await asyncio.sleep(3)

            # 검색창에 "남성의류" 입력
            print("4. 검색창에 '남성의류' 입력...")
            search_box = await page.wait_for_selector('input[type="text"]', timeout=5000)
            if search_box:
                await search_box.click()
                await asyncio.sleep(1)
                await search_box.type("남성의류", delay=100)
                await asyncio.sleep(1)
                await page.keyboard.press('Enter')
                print("5. 검색 실행!")
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(5)

                current_url = page.url
                print(f"현재 URL: {current_url}")

                if "captcha" in current_url or await page.query_selector('text=security verification'):
                    print("❌ 캡차 발생!")
                    return False
                else:
                    print("✅ 성공! 검색 결과 표시")
                    # 스크린샷 저장
                    await page.screenshot(path='/mnt/d/MyProjects/Crawl/tests/search_success.png')
                    return True
        except Exception as e:
            print(f"❌ 오류: {e}")
            return False
        finally:
            print("30초 대기 (확인용)...")
            await asyncio.sleep(30)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_search())