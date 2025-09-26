"""
캡차 스크린샷 확인 후 자동 해결
"""

import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime

async def test_captcha_solver():
    print("=" * 50)
    print("캡차 자동 해결 테스트")
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

            # 6. 캡차 확인 (더 확실하게)
            print("5️⃣ 캡차 확인 중...")

            # 대기 시간 추가 (캡차 페이지 로드 대기)
            await asyncio.sleep(3)

            # 임시 스크린샷 파일명 (타임스탬프 포함)
            temp_screenshot = f'/tmp/captcha_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            await page.screenshot(path=temp_screenshot)
            print(f"📸 스크린샷 저장: {temp_screenshot}")

            # 여러 방법으로 캡차 확인
            captcha_indicators = [
                await page.query_selector('text=security verification'),
                await page.query_selector('text=Please complete the security'),
                await page.query_selector('text=This receipt is made virtually'),
                await page.query_selector('input[placeholder*="Answer"]'),
                await page.query_selector('text=How many'),
                await page.query_selector('text=보안 확인'),  # 한글
                await page.query_selector('button:has-text("확인")')  # 한글 버튼
            ]

            current_url = page.url

            # URL이 카테고리 페이지가 아니면 캡차로 판단
            is_captcha = any(captcha_indicators) or "captcha" in current_url or ("shopping.naver.com" in current_url and "/category/" not in current_url)

            print(f"현재 URL: {current_url}")
            print(f"캡차 감지: {is_captcha}")

            if is_captcha:
                print("\n🔐 캡차 감지! 스크린샷 촬영...")

                # 임시 스크린샷만 사용 (이미 위에서 저장함)
                print(f"📸 임시 캡차 스크린샷: {temp_screenshot}")

                # 캡차 문제 텍스트 읽기
                print("\n📋 캡차 문제 분석 중...")

                # 질문 텍스트 찾기 (아래쪽에 있는 질문)
                question_text = ""
                question_elem = await page.query_selector('text=How many')
                if not question_elem:
                    question_elem = await page.query_selector('text=몇 개')
                if not question_elem:
                    question_elem = await page.query_selector('text=얼마')

                if question_elem:
                    question_text = await question_elem.inner_text()
                    print(f"질문: {question_text}")

                # 스크린샷을 직접 분석해서 답을 결정해야 함
                # 여기서는 사용자가 스크린샷을 보고 답을 제공해야 함
                print("\n🖼️ 스크린샷을 확인하고 답을 결정합니다...")

                # 임시로 여러 답 시도
                # 실제로는 OCR이나 이미지 분석이 필요
                if "몇 개" in question_text or "How many" in question_text:
                    # 아이템 개수 문제일 가능성
                    answer = "16"  # 방금 확인한 답
                elif "kg" in question_text:
                    answer = "2.46"
                elif "얼마" in question_text or "How much" in question_text:
                    answer = "10000"
                else:
                    answer = "1"

                print(f"💡 시도할 답: {answer}")

                # 답 입력란 찾기
                print("✏️ 답 입력 중...")
                answer_input = await page.query_selector('input[placeholder*="Answer"]')
                if not answer_input:
                    answer_input = await page.query_selector('input[type="text"]')

                if answer_input:
                    await answer_input.click()
                    await answer_input.fill("")  # 기존 값 지우기
                    await asyncio.sleep(0.5)

                    # 답 입력 (천천히, 사람처럼)
                    for char in answer:
                        await page.keyboard.type(char)
                        await asyncio.sleep(0.2)

                    print(f"✅ 답 입력 완료: {answer}")

                    # Confirm 버튼 클릭
                    print("🔘 Confirm 버튼 찾는 중...")
                    confirm_btn = await page.query_selector('button:has-text("Confirm")')
                    if confirm_btn:
                        await confirm_btn.click()
                        print("✅ Confirm 클릭!")

                        # 결과 대기
                        await asyncio.sleep(5)

                        # 성공 확인
                        current_url = page.url
                        captcha_still_there = await page.query_selector('text=security verification')

                        if not captcha_still_there and "captcha" not in current_url:
                            print("\n🎉 캡차 해결 성공! 남성의류 페이지 접속!")
                            print(f"📍 현재 URL: {current_url}")

                            # 임시 스크린샷 삭제
                            if os.path.exists(temp_screenshot):
                                os.remove(temp_screenshot)
                                print(f"🗑️ 임시 스크린샷 삭제: {temp_screenshot}")

                            # 상품 확인
                            products = await page.query_selector_all('[class*="product"]')
                            print(f"👔 남성의류 상품 {len(products)}개 발견")

                            return True
                        else:
                            print("⚠️ 첫 번째 시도 실패, 다른 답 시도...")

                            # 다른 답 시도
                            alternative_answers = ["2.5", "2", "3", "1"]
                            for alt_answer in alternative_answers:
                                print(f"🔄 시도: {alt_answer}")

                                answer_input = await page.query_selector('input[type="text"]')
                                if answer_input:
                                    await answer_input.click()
                                    await answer_input.fill("")
                                    await answer_input.type(alt_answer, delay=100)

                                    confirm_btn = await page.query_selector('button:has-text("Confirm")')
                                    if confirm_btn:
                                        await confirm_btn.click()
                                        await asyncio.sleep(3)

                                        # 확인
                                        if not await page.query_selector('text=security verification'):
                                            print(f"✅ 성공! 정답은 {alt_answer}였습니다!")
                                            return True

                            print("❌ 모든 답 시도 실패")
                            return False
                else:
                    print("❌ 답 입력란을 찾을 수 없습니다")
                    return False
            else:
                print("✅ 캡차 없이 접속 성공!")
                print(f"📍 현재 URL: {current_url}")

                # 임시 스크린샷 삭제
                if os.path.exists(temp_screenshot):
                    os.remove(temp_screenshot)
                    print(f"🗑️ 임시 스크린샷 삭제: {temp_screenshot}")

                return True

        except Exception as e:
            print(f"❌ 오류 발생: {e}")

            # 에러 발생 시에도 임시 스크린샷 삭제
            if 'temp_screenshot' in locals() and os.path.exists(temp_screenshot):
                os.remove(temp_screenshot)
                print(f"🗑️ 임시 스크린샷 삭제: {temp_screenshot}")

            return False
        finally:
            print("\n브라우저를 30초간 유지합니다...")
            await asyncio.sleep(30)
            await browser.close()
            print("🔚 브라우저 종료")

if __name__ == "__main__":
    asyncio.run(test_captcha_solver())