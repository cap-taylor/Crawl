"""
캡차 감지 및 스크린샷 캡처 테스트
캡차가 나타났는지 확인하고 스크린샷을 저장
"""
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

class CaptchaDetector:
    def __init__(self, headless=False):
        self.headless = headless
        self.captcha_detected = False

    async def check_for_captcha(self, page):
        """캡차 페이지 감지"""
        print("\n[검사] 캡차 확인 중...")

        # 캡차 페이지 식별 요소들
        captcha_indicators = [
            'text="보안 확인을 완료해 주세요"',
            'text="자동입력 방지문자"',
            'text="보안 확인"',
            'input[placeholder*="문자"]',
            'button:has-text("확인")',
            '#captcha',
            'img[src*="captcha"]'
        ]

        for indicator in captcha_indicators:
            try:
                element = await page.query_selector(indicator)
                if element:
                    self.captcha_detected = True
                    print(f"⚠️ 캡차 감지됨! (셀렉터: {indicator})")

                    # 스크린샷 저장
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    screenshot_path = f'data/captcha_detected_{timestamp}.png'
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f"📸 캡차 스크린샷 저장: {screenshot_path}")

                    # 캡차 이미지 찾기
                    captcha_img = await page.query_selector('div[class*="captcha"] img, #captcha img, img[src*="captcha"]')
                    if captcha_img:
                        # 캡차 이미지만 캡처
                        await captcha_img.screenshot(path=f'data/captcha_image_{timestamp}.png')
                        print(f"📸 캡차 이미지만 저장: data/captcha_image_{timestamp}.png")

                    return True
            except:
                continue

        print("✅ 캡차 없음 - 정상 페이지")
        return False

    async def detect_captcha_flow(self):
        """네이버 쇼핑 접속 과정에서 캡차 감지"""
        async with async_playwright() as p:
            try:
                print("[시작] Firefox 브라우저 실행...")
                browser = await p.firefox.launch(
                    headless=self.headless,
                    slow_mo=500
                )

                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                    locale='ko-KR',
                    timezone_id='Asia/Seoul'
                )

                page = await context.new_page()

                # 1. 네이버 메인
                print("\n[1단계] 네이버 메인 접속...")
                await page.goto('https://www.naver.com')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)

                # 캡차 체크
                if await self.check_for_captcha(page):
                    print("네이버 메인에서 캡차 발생!")
                    return {'stage': 'naver_main', 'captcha': True}

                # 2. 쇼핑 클릭
                print("\n[2단계] 쇼핑 아이콘 클릭...")
                shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a')
                await shopping_link.click()
                await asyncio.sleep(3)

                # 새 탭 전환
                all_pages = context.pages
                if len(all_pages) > 1:
                    page = all_pages[-1]
                    await page.wait_for_load_state('networkidle')
                    print("쇼핑 탭으로 전환 완료")

                # 캡차 체크
                await asyncio.sleep(2)
                if await self.check_for_captcha(page):
                    print("쇼핑 메인에서 캡차 발생!")
                    return {'stage': 'shopping_main', 'captcha': True}

                # 3. 카테고리 버튼
                print("\n[3단계] 카테고리 버튼 클릭...")
                category_btn = await page.wait_for_selector('button:has-text("카테고리")')
                await category_btn.click()
                await asyncio.sleep(2)

                # 캡차 체크
                if await self.check_for_captcha(page):
                    print("카테고리 메뉴에서 캡차 발생!")
                    return {'stage': 'category_menu', 'captcha': True}

                # 4. 여성의류 클릭
                print("\n[4단계] 여성의류 카테고리 클릭...")
                womens = await page.wait_for_selector('a[data-name="여성의류"]')
                await womens.click()
                await asyncio.sleep(3)

                # 최종 캡차 체크
                await page.wait_for_load_state('networkidle')
                if await self.check_for_captcha(page):
                    print("여성의류 카테고리에서 캡차 발생!")

                    # 캡차 페이지 구조 분석
                    print("\n[분석] 캡차 페이지 구조 확인...")

                    # 입력 필드 찾기
                    input_field = await page.query_selector('input[type="text"]')
                    if input_field:
                        placeholder = await input_field.get_attribute('placeholder')
                        print(f"입력 필드 발견: placeholder='{placeholder}'")

                    # 확인 버튼 찾기
                    confirm_btn = await page.query_selector('button:has-text("확인")')
                    if confirm_btn:
                        print("확인 버튼 발견")

                    # 새로고침 버튼 찾기
                    refresh_btn = await page.query_selector('button[class*="refresh"], button[title*="새로"]')
                    if refresh_btn:
                        print("새로고침 버튼 발견")

                    return {'stage': 'womens_clothing', 'captcha': True}

                # 캡차 없이 성공
                print("\n✅ 캡차 없이 여성의류 페이지 도달!")
                await page.screenshot(path='data/womens_success.png')
                print("📸 성공 스크린샷: data/womens_success.png")

                await browser.close()
                return {'stage': 'success', 'captcha': False}

            except Exception as e:
                print(f"[오류] {str(e)}")
                import traceback
                traceback.print_exc()
                return {'stage': 'error', 'captcha': False}


if __name__ == "__main__":
    async def main():
        print("="*60)
        print("캡차 감지 테스트")
        print("="*60)

        detector = CaptchaDetector(headless=False)
        result = await detector.detect_captcha_flow()

        print("\n" + "="*60)
        print("테스트 결과")
        print("="*60)
        print(f"최종 단계: {result['stage']}")
        print(f"캡차 발생: {result['captcha']}")

        if result['captcha']:
            print("\n📌 캡차 해결이 필요합니다!")
            print("스크린샷을 확인하여 캡차 이미지를 분석하세요.")
        else:
            print("\n✅ 캡차 없이 접속 성공!")

    asyncio.run(main())