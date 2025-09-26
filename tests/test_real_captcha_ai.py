#!/usr/bin/env python3
"""
실제 AI 기반 캡차 해결 테스트
하드코딩 없이 실제 스크린샷 분석
"""

import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime

async def test_real_ai_captcha():
    print("=" * 50)
    print("실제 AI 캡차 해결 테스트 (하드코딩 없음)")
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

        try:
            # 1. 네이버 메인
            print("1️⃣ 네이버 메인 접속...")
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            # 2. 쇼핑 클릭
            print("2️⃣ 쇼핑 클릭...")
            shopping = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a', timeout=5000)
            if shopping:
                await shopping.click()
                await asyncio.sleep(3)

            # 새 탭 처리
            if len(context.pages) > 1:
                page = context.pages[-1]
                await page.wait_for_load_state('networkidle')
                print("✅ 쇼핑 탭 전환")

            # 3. 카테고리 메뉴
            print("3️⃣ 카테고리 메뉴 열기...")
            category_btn = await page.wait_for_selector('text=카테고리', timeout=5000)
            if category_btn:
                await category_btn.click()
                await asyncio.sleep(2)

            # 4. 남성의류 클릭
            print("4️⃣ 남성의류 클릭...")
            mens = await page.wait_for_selector('text=남성의류', timeout=5000)
            if mens:
                await mens.click()
                await asyncio.sleep(5)

            # 5. 캡차 확인
            print("5️⃣ 캡차 확인...")

            # 스크린샷 저장
            screenshot_path = f'/tmp/captcha_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 스크린샷 저장: {screenshot_path}")

            # 캡차 페이지 확인
            captcha_detected = False

            # 캡차 요소 확인
            captcha_indicators = [
                await page.query_selector('text=security verification'),
                await page.query_selector('input[placeholder*="Answer"]'),
                await page.query_selector('text=This receipt'),
                await page.query_selector('text=How many')
            ]

            if any(captcha_indicators):
                captcha_detected = True
                print("🔐 캡차 감지됨!")

                # 질문 텍스트 추출
                question = None
                for selector in ['text=How many', 'text=몇', 'text=What']:
                    elem = await page.query_selector(selector)
                    if elem:
                        question = await elem.inner_text()
                        print(f"❓ 질문: {question}")
                        break

                print("\n" + "=" * 50)
                print("⚠️ 실제 AI 분석 기능 없음!")
                print("네이버 캡차는 영수증 이미지 + 질문 형태")
                print("OCR로는 해결 불가능 (이미지 이해 필요)")
                print("필요한 기능:")
                print("  1. 영수증 이미지 인식")
                print("  2. 아이템 개수/가격/무게 계산")
                print("  3. 질문 이해 및 답변")
                print("=" * 50)

                # 수동 입력 대기
                print("\n⏳ 30초 대기 (수동으로 캡차 해결 필요)")
                await asyncio.sleep(30)

            else:
                print("✅ 캡차 없음 또는 이미 통과")

            # 현재 URL 확인
            current_url = page.url
            print(f"📍 최종 URL: {current_url}")

            if "/category/" in current_url:
                print("✅ 카테고리 페이지 접속 성공")
            else:
                print("❌ 캡차 통과 실패")

        except Exception as e:
            print(f"❌ 오류: {e}")
        finally:
            print("\n브라우저 30초 유지...")
            await asyncio.sleep(30)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_real_ai_captcha())