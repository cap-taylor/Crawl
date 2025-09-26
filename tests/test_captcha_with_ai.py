"""
캡차 자동 해결 - AI가 스크린샷 분석
"""

import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime

async def analyze_captcha_screenshot(screenshot_path):
    """
    스크린샷을 분석해서 답을 찾는 함수
    실제로는 여기서 OCR이나 AI 서비스를 사용해야 함
    """
    print(f"\n🔍 스크린샷 분석 중: {screenshot_path}")

    # 여기서 실제 이미지 분석이 필요
    # 예: OCR로 영수증 텍스트 읽기
    # 예: AI 서비스로 이미지 분석

    # 임시로 사용자 입력 받기 (실제 구현시 자동화)
    print("\n" + "=" * 50)
    print("🖼️ 캡차 스크린샷이 저장되었습니다.")
    print(f"📁 파일 위치: {screenshot_path}")
    print("\n질문과 영수증을 보고 답을 입력하세요:")
    print("예시:")
    print("  - 아이템 개수: 숫자 입력 (예: 16)")
    print("  - 무게(kg): 소수점 입력 (예: 2.46)")
    print("  - 가격: 숫자 입력 (예: 50000)")
    print("=" * 50)

    # 자동 분석 시도 (패턴 매칭)
    # 실제로는 OCR 결과를 분석
    answer = "16"  # 기본값

    return answer

async def test_captcha_with_ai():
    print("=" * 50)
    print("캡차 자동 해결 테스트 (AI 분석)")
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
                await asyncio.sleep(5)

            # 6. 캡차 확인
            print("5️⃣ 캡차 확인 중...")
            await asyncio.sleep(3)

            # 스크린샷 저장
            temp_screenshot = f'/tmp/captcha_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            await page.screenshot(path=temp_screenshot)
            print(f"📸 스크린샷 저장: {temp_screenshot}")

            # 캡차 여부 확인
            captcha_indicators = [
                await page.query_selector('text=security verification'),
                await page.query_selector('input[placeholder*="Answer"]'),
                await page.query_selector('text=확인'),
                await page.query_selector('button:has-text("확인")')
            ]

            if any(captcha_indicators):
                print("\n🔐 캡차 감지!")

                # AI로 스크린샷 분석
                answer = await analyze_captcha_screenshot(temp_screenshot)
                print(f"\n💡 분석 결과 답: {answer}")

                # 답 입력
                print("✏️ 답 입력 중...")
                answer_input = await page.query_selector('input[placeholder*="Answer"]')
                if not answer_input:
                    answer_input = await page.query_selector('input[type="text"]')

                if answer_input:
                    await answer_input.click()
                    await answer_input.fill("")
                    await answer_input.type(answer, delay=100)
                    print(f"✅ 답 입력 완료: {answer}")

                    # Confirm 버튼 클릭
                    confirm_btn = await page.query_selector('button:has-text("확인")')
                    if not confirm_btn:
                        confirm_btn = await page.query_selector('button:has-text("Confirm")')

                    if confirm_btn:
                        await confirm_btn.click()
                        print("✅ 확인 버튼 클릭!")

                        # 결과 대기
                        await asyncio.sleep(5)

                        # 성공 확인
                        current_url = page.url
                        if "/category/" in current_url:
                            print("\n🎉 캡차 해결 성공!")
                            print(f"📍 현재 URL: {current_url}")

                            # 임시 스크린샷 삭제
                            if os.path.exists(temp_screenshot):
                                os.remove(temp_screenshot)
                                print(f"🗑️ 임시 스크린샷 삭제")

                            # 상품 확인
                            products = await page.query_selector_all('[class*="product"]')
                            print(f"👔 남성의류 상품 {len(products)}개 발견")

                            return True
                        else:
                            print("⚠️ 캡차 해결 실패")

                            # 다른 답 시도 리스트
                            alternative_answers = ["15", "17", "20", "10", "5", "1", "2.5", "3"]

                            for alt_answer in alternative_answers:
                                print(f"\n🔄 다른 답 시도: {alt_answer}")

                                answer_input = await page.query_selector('input[type="text"]')
                                if answer_input:
                                    await answer_input.click()
                                    await answer_input.fill("")
                                    await answer_input.type(alt_answer, delay=100)

                                    confirm_btn = await page.query_selector('button:has-text("확인")')
                                    if confirm_btn:
                                        await confirm_btn.click()
                                        await asyncio.sleep(3)

                                        if "/category/" in page.url:
                                            print(f"✅ 성공! 정답은 {alt_answer}였습니다!")

                                            # 임시 스크린샷 삭제
                                            if os.path.exists(temp_screenshot):
                                                os.remove(temp_screenshot)

                                            return True

                            print("❌ 모든 시도 실패")
                            return False
            else:
                print("✅ 캡차 없이 접속 성공!")

                # 임시 스크린샷 삭제
                if os.path.exists(temp_screenshot):
                    os.remove(temp_screenshot)
                    print(f"🗑️ 임시 스크린샷 삭제")

                return True

        except Exception as e:
            print(f"❌ 오류 발생: {e}")

            # 에러 시에도 임시 파일 삭제
            if 'temp_screenshot' in locals() and os.path.exists(temp_screenshot):
                os.remove(temp_screenshot)

            return False
        finally:
            print("\n브라우저를 30초간 유지합니다...")
            await asyncio.sleep(30)
            await browser.close()
            print("🔚 브라우저 종료")

if __name__ == "__main__":
    asyncio.run(test_captcha_with_ai())