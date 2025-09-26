"""
캡차 수동 해결로 남성의류 접속
"""

import asyncio
from playwright.async_api import async_playwright

async def test_with_manual_captcha():
    print("=" * 50)
    print("캡차 수동 해결 테스트")
    print("=" * 50)

    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=500,
            args=['--kiosk']
        )
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # 1. 네이버 메인
            print("1️⃣ 네이버 메인 접속...")
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            # 2. 쇼핑 클릭
            print("2️⃣ 쇼핑 클릭...")
            shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a')
            await shopping_link.click()
            await asyncio.sleep(3)

            # 3. 새 탭 전환
            if len(context.pages) > 1:
                page = context.pages[-1]
                await page.wait_for_load_state('networkidle')
                print("✅ 쇼핑 탭 전환 완료")

            await asyncio.sleep(3)

            # 4. 카테고리 메뉴 열기
            print("3️⃣ 카테고리 메뉴 열기...")
            category_btn = await page.wait_for_selector('text=카테고리', timeout=5000)
            if category_btn:
                await category_btn.click()
                await asyncio.sleep(3)
                print("✅ 카테고리 메뉴 열림")

            # 5. 남성의류 클릭
            print("4️⃣ 남성의류 클릭...")
            mens_clothing = await page.wait_for_selector('text=남성의류', timeout=5000)
            if mens_clothing:
                await mens_clothing.click()
                await asyncio.sleep(3)

            # 6. 캡차 확인
            current_url = page.url
            if "captcha" in current_url or await page.query_selector('text=security verification'):
                print("\n" + "⚠️" * 20)
                print("🔐 캡차가 나타났습니다!")
                print("👉 브라우저에서 직접 캡차를 풀어주세요")
                print("⏳ 60초 대기 중...")
                print("⚠️" * 20 + "\n")

                # 60초 대기
                for i in range(60, 0, -10):
                    print(f"  {i}초 남음...")
                    await asyncio.sleep(10)

                # 캡차 해결 확인
                current_url = page.url
                if "shopping.naver.com" in current_url and "captcha" not in current_url:
                    print("\n✅ 캡차 해결 완료! 남성의류 카테고리 접속 성공!")
                    print(f"📍 현재 URL: {current_url}")

                    # 스크린샷
                    await page.screenshot(path='/mnt/d/MyProjects/Crawl/tests/mens_category_success.png')
                    print("📸 스크린샷 저장: mens_category_success.png")

                    # 상품 확인
                    products = await page.query_selector_all('[class*="product"]')
                    print(f"👔 남성의류 상품 {len(products)}개 발견")

                    return True
                else:
                    print("❌ 캡차 해결 실패 또는 시간 초과")
                    return False
            else:
                print("✅ 캡차 없이 접속 성공! (이상하네요?)")
                return True

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path='/mnt/d/MyProjects/Crawl/tests/error.png')
            return False
        finally:
            print("\n브라우저를 60초간 유지합니다...")
            await asyncio.sleep(60)
            await browser.close()
            print("🔚 브라우저 종료")

if __name__ == "__main__":
    asyncio.run(test_with_manual_captcha())