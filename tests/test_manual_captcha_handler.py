#!/usr/bin/env python3
"""
캡차 수동 해결 테스트
캡차가 나타나면 사용자가 직접 해결하고, 해결되면 자동으로 진행
"""

import asyncio
from playwright.async_api import async_playwright
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.captcha_handler import CaptchaHandler

async def test_manual_captcha():
    print("=" * 50)
    print("캡차 수동 해결 테스트")
    print("=" * 50)

    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=500
        )
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        # 캡차 핸들러 초기화
        captcha_handler = CaptchaHandler()
        captcha_handler.set_max_wait_time(120)  # 2분 대기

        try:
            # 1. 네이버 메인
            print("1️⃣ 네이버 메인 접속...")
            await page.goto('https://www.naver.com', timeout=60000)
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(2)

            # 2. 쇼핑 클릭
            print("2️⃣ 쇼핑 탭으로 이동...")
            shopping = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a', timeout=5000)
            if shopping:
                await shopping.click()
                await asyncio.sleep(2)

            # 새 탭 처리
            if len(context.pages) > 1:
                page = context.pages[-1]
                await page.wait_for_load_state('networkidle')
                print("✅ 쇼핑 탭 전환 완료")

            await asyncio.sleep(2)

            # 3. 카테고리 메뉴
            print("3️⃣ 카테고리 메뉴 열기...")
            category_btn = await page.wait_for_selector('text=카테고리', timeout=5000)
            if category_btn:
                await category_btn.click()
                await asyncio.sleep(2)
                print("✅ 카테고리 메뉴 열림")

            # 4. 남성의류 클릭
            print("4️⃣ 남성의류 카테고리 선택...")
            mens = await page.wait_for_selector('text=남성의류', timeout=5000)
            if mens:
                await mens.click()
                await asyncio.sleep(3)

            # 5. 캡차 처리
            print("5️⃣ 캡차 확인 중...")

            # 캡차가 있으면 수동 해결 대기
            if await captcha_handler.handle_captcha_if_exists(page):
                print("✅ 캡차 처리 완료 (없거나 해결됨)")

                # 현재 페이지 확인
                current_url = page.url
                print(f"📍 현재 URL: {current_url}")

                if "/category/" in current_url:
                    print("🎉 남성의류 카테고리 접속 성공!")

                    # 상품 개수 확인
                    products = await page.query_selector_all('[class*="product"]')
                    if products:
                        print(f"👔 상품 {len(products)}개 발견")
                    else:
                        print("📦 상품 목록 로딩 중...")

                        # 스크롤해서 상품 로드
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(2)

                        products = await page.query_selector_all('[class*="product"]')
                        if products:
                            print(f"👔 스크롤 후 상품 {len(products)}개 로드")
                else:
                    print("⚠️ 카테고리 페이지 접속 실패")
            else:
                print("❌ 캡차 처리 실패 (시간 초과)")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

        finally:
            print("\n테스트 종료. 브라우저 10초 후 종료...")
            await asyncio.sleep(10)
            await browser.close()
            print("🔚 브라우저 종료")

if __name__ == "__main__":
    asyncio.run(test_manual_captcha())