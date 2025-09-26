"""
네이버 쇼핑 접속 테스트 - 일반 Playwright 사용
학습한 내용 적용:
1. 네이버 메인 먼저 접속
2. 쇼핑 클릭으로 이동
3. Stealth 모드 적용
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def test_naver_shopping():
    """네이버 쇼핑 접속 테스트"""

    async with async_playwright() as p:
        # Firefox 사용 (문서에서 성공한 방법)
        print("🦊 Firefox 브라우저 실행...")
        browser = await p.firefox.launch(
            headless=False,  # 절대 True 금지!
            slow_mo=500,  # 동작을 천천히 (봇 감지 회피)
            args=['--kiosk']  # 전체화면 모드
        )

        # 화면 크기 설정
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}  # 전체화면
        )

        page = await context.new_page()

        try:
            # 1단계: 네이버 메인 접속
            print("📍 네이버 메인 페이지 접속...")
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('networkidle')
            print("✅ 네이버 메인 접속 성공!")

            # 랜덤 대기 (사람처럼 행동)
            await asyncio.sleep(2)

            # 2단계: 쇼핑 아이콘 클릭
            print("🛍️ 쇼핑 아이콘 찾는 중...")

            # 여러 셀렉터 시도
            selectors = [
                '#shortcutArea > ul > li:nth-child(4) > a',  # 제공된 셀렉터
                'a[data-clk="svc.shopping"]',  # data 속성
                'text=쇼핑',  # 텍스트로 찾기
                'a:has-text("쇼핑")'  # 쇼핑 텍스트 포함 링크
            ]

            clicked = False
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        print(f"  찾음: {selector}")
                        # 그냥 클릭 (새 탭으로 열림 - 캡차 방지)
                        await element.click()
                        clicked = True
                        break
                except:
                    print(f"  시도: {selector} - 실패")
                    continue

            if not clicked:
                print("❌ 쇼핑 아이콘을 찾을 수 없습니다!")
                return False

            # 새 탭이 열릴 때까지 대기
            await asyncio.sleep(3)

            # 새 탭으로 전환
            all_pages = context.pages
            print(f"📑 열린 탭 수: {len(all_pages)}")

            if len(all_pages) > 1:
                page = all_pages[-1]  # 마지막 탭 = 쇼핑 탭
                await page.wait_for_load_state('networkidle')
                print("✅ 새 탭(쇼핑)으로 전환 완료")
            else:
                print("⚠️ 새 탭이 열리지 않았습니다")
                await page.wait_for_load_state('networkidle')

            # 3단계: 결과 확인
            current_url = page.url
            print(f"📍 현재 URL: {current_url}")

            # 스크린샷 저장
            screenshot_path = '/mnt/d/MyProjects/Crawl/tests/naver_shopping_success.png'
            await page.screenshot(path=screenshot_path)
            print(f"📸 스크린샷 저장: {screenshot_path}")

            # 캡차 확인
            if "captcha" in current_url or await page.query_selector('text=security verification'):
                print("⚠️ 캡차 페이지 감지됨!")

                # 캡차 이미지 저장
                await page.screenshot(path='/mnt/d/MyProjects/Crawl/tests/captcha_page.png')
                print("📸 캡차 페이지 스크린샷 저장")

                # 수동 해결 대기
                print("⏳ 캡차를 수동으로 해결해주세요...")
                await asyncio.sleep(30)  # 30초 대기

            elif "shopping.naver.com" in current_url:
                print("✅ 네이버 쇼핑 접속 성공!")

                # 4단계: 카테고리 메뉴 열기
                print("\n📂 카테고리 메뉴 열기...")

                # 잠시 대기 (페이지 완전 로드)
                await asyncio.sleep(2)

                # 카테고리 버튼 찾기 (햄버거 메뉴, 전체 카테고리 등)
                category_menu_selectors = [
                    'text=카테고리',  # 카테고리 텍스트
                    'button:has-text("카테고리")',  # 카테고리 버튼
                    '[class*="category"]',  # category 클래스
                    'text=전체',  # 전체 카테고리
                    '[aria-label*="카테고리"]',  # aria-label
                    '._categoryButton_',  # 클래스명
                ]

                menu_opened = False
                for selector in category_menu_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=2000)
                        if element:
                            print(f"  카테고리 버튼 찾음: {selector}")
                            await element.click()
                            menu_opened = True
                            break
                    except:
                        continue

                if not menu_opened:
                    print("❌ 카테고리 메뉴를 찾을 수 없습니다!")
                    return False

                await asyncio.sleep(2)  # 메뉴 열리기 대기

                # 5단계: 남성의류 카테고리 클릭
                print("👔 남성의류 카테고리 찾는 중...")

                # 남성의류 찾기
                mens_clothing_selectors = [
                    'text=남성의류',  # 텍스트로 찾기
                    'a:has-text("남성의류")',  # 링크 텍스트
                    'span:has-text("남성의류")',  # span 텍스트
                    '[title="남성의류"]',  # title 속성
                    'li:has-text("남성의류")'  # 리스트 아이템
                ]

                category_clicked = False
                for selector in mens_clothing_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=3000)
                        if element:
                            print(f"  남성의류 찾음: {selector}")
                            await element.click()
                            category_clicked = True
                            break
                    except:
                        print(f"  시도: {selector} - 실패")
                        continue

                if category_clicked:
                    await page.wait_for_load_state('networkidle')
                    await asyncio.sleep(3)

                    final_url = page.url
                    print(f"✅ 남성의류 카테고리 접속 성공!")
                    print(f"📍 최종 URL: {final_url}")

                    # 상품 확인
                    products = await page.query_selector_all('[class*="product"]')
                    print(f"👔 남성의류 상품 {len(products)}개 발견")
                else:
                    print("⚠️ 남성의류 카테고리를 찾을 수 없습니다")

                return True
            else:
                print(f"❓ 알 수 없는 페이지: {current_url}")
                return False

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            # 오류 스크린샷
            await page.screenshot(path='/mnt/d/MyProjects/Crawl/tests/error_screenshot.png')
            return False

        finally:
            # 브라우저 유지 (수동 확인용)
            print("\n👀 브라우저를 30초간 유지합니다...")
            await asyncio.sleep(30)
            await browser.close()
            print("🔚 브라우저 종료")

async def test_with_chromium_stealth():
    """Chromium + Stealth 모드 테스트"""

    async with async_playwright() as p:
        print("🌐 Chromium + Stealth 모드 실행...")

        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--lang=ko-KR'
            ]
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        # Stealth 스크립트 적용 (문서에서 성공한 방법)
        await context.add_init_script("""
            // webdriver 제거
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // chrome 객체 추가
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };

            // plugins 추가
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // languages 설정
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ko-KR', 'ko', 'en-US', 'en']
            });

            // platform 설정
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
        """)

        page = await context.new_page()

        try:
            print("📍 네이버 메인 접속 중...")
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('networkidle')
            print("✅ 접속 성공!")

            await asyncio.sleep(30)  # 확인용

        finally:
            await browser.close()

if __name__ == "__main__":
    print("=" * 50)
    print("네이버 쇼핑 접속 테스트 시작")
    print("=" * 50)

    # Firefox 테스트
    print("\n[테스트 1] Firefox 브라우저")
    asyncio.run(test_naver_shopping())

    # Chromium + Stealth 테스트도 원한다면
    # print("\n[테스트 2] Chromium + Stealth")
    # asyncio.run(test_with_chromium_stealth())