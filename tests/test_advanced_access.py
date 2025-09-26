#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 쇼핑 메인페이지 접속 테스트 - 고급 방법
더 정교한 봇 감지 우회 방법 시도
"""

import asyncio
from playwright.async_api import async_playwright
import random
import time
from pathlib import Path

class AdvancedTester:
    def __init__(self):
        self.test_results = []

    async def test_method_1_full_stealth(self):
        """테스트 1: 완전한 Stealth 설정"""
        print("\n" + "="*60)
        print("테스트 1: 완전한 Stealth 설정")
        print("="*60)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu'
                ]
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                screen={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale='ko-KR',
                timezone_id='Asia/Seoul',
                permissions=['geolocation'],
                geolocation={'latitude': 37.5665, 'longitude': 126.9780},  # 서울 위치
                color_scheme='light',
                device_scale_factor=1.0,
                has_touch=False,
                is_mobile=False
            )

            # 완전한 Stealth 스크립트
            await context.add_init_script("""
                // webdriver 속성 제거
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
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                            1: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                            length: 2,
                            name: "Chrome PDF Plugin",
                            filename: "internal-pdf-viewer"
                        },
                        {
                            0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                            length: 1,
                            name: "Native Client",
                            filename: "internal-nacl-plugin"
                        }
                    ]
                });

                // languages 설정
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ko-KR', 'ko', 'en-US', 'en']
                });

                // platform 설정
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32'
                });

                // permissions 수정
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // WebGL Vendor 설정
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter.apply(this, arguments);
                };

                // Canvas Fingerprint 방지
                const originalGetContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type, attributes) {
                    if (type === '2d') {
                        const context = originalGetContext.apply(this, arguments);
                        const originalFillText = context.fillText;
                        context.fillText = function() {
                            arguments[0] = arguments[0] + String.fromCharCode(8203);  // Zero-width space
                            return originalFillText.apply(this, arguments);
                        };
                        return context;
                    }
                    return originalGetContext.apply(this, arguments);
                };
            """)

            page = await context.new_page()

            try:
                print("완전한 Stealth 모드로 접속 시도")

                # 랜덤 딜레이
                await asyncio.sleep(random.uniform(1, 3))

                # 천천히 접속
                await page.goto("https://shopping.naver.com/ns/home", wait_until='networkidle')

                # 랜덤 대기
                await page.wait_for_timeout(random.randint(3000, 5000))

                # 페이지 확인
                title = await page.title()
                url = page.url
                content = await page.content()

                print(f"페이지 타이틀: {title}")
                print(f"현재 URL: {url}")

                if "security" in content.lower() or "verification" in content.lower():
                    print("❌ 실패: 여전히 보안 검증 페이지")
                    self.test_results.append(("완전한 Stealth", "실패", "보안 검증"))
                else:
                    print("✅ 성공: 정상 접속!")
                    self.test_results.append(("완전한 Stealth", "성공", ""))
                    await page.screenshot(path="tests/advanced_success.png")

            except Exception as e:
                print(f"❌ 오류: {str(e)}")
                self.test_results.append(("완전한 Stealth", "실패", str(e)))

            finally:
                await browser.close()

    async def test_method_2_human_behavior(self):
        """테스트 2: 인간처럼 행동하기"""
        print("\n" + "="*60)
        print("테스트 2: 인간처럼 행동하기")
        print("="*60)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # 기본 Stealth
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            page = await context.new_page()

            try:
                # 1. 구글 먼저 방문
                print("1단계: 구글 방문")
                await page.goto("https://www.google.com")
                await asyncio.sleep(random.uniform(2, 4))

                # 2. 네이버 검색
                print("2단계: 네이버 검색")
                await page.type('textarea[name="q"]', "네이버", delay=random.randint(100, 200))
                await page.press('textarea[name="q"]', 'Enter')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(random.uniform(2, 4))

                # 3. 네이버 클릭
                print("3단계: 네이버 클릭")
                naver_link = await page.query_selector('a[href*="naver.com"]')
                if naver_link:
                    await naver_link.click()
                    await page.wait_for_load_state('networkidle')
                    await asyncio.sleep(random.uniform(3, 5))

                    # 4. 쇼핑 탭 찾기
                    print("4단계: 쇼핑 탭 찾기")
                    shopping_link = await page.query_selector('a[href*="shopping"]')
                    if shopping_link:
                        # 마우스 움직임 시뮬레이션
                        await page.mouse.move(
                            random.randint(100, 500),
                            random.randint(100, 500),
                            steps=10
                        )
                        await asyncio.sleep(random.uniform(0.5, 1.5))

                        await shopping_link.hover()
                        await asyncio.sleep(random.uniform(0.5, 1))
                        await shopping_link.click()

                        await page.wait_for_load_state('networkidle')
                        await asyncio.sleep(random.uniform(3, 5))

                        # 결과 확인
                        content = await page.content()
                        if "security" in content.lower() or "verification" in content.lower():
                            print("❌ 실패: 인간 행동 모방도 감지됨")
                            self.test_results.append(("인간 행동 모방", "실패", "보안 검증"))
                        else:
                            print("✅ 성공: 정상 접속!")
                            self.test_results.append(("인간 행동 모방", "성공", ""))
                    else:
                        print("❌ 쇼핑 링크 못 찾음")
                        self.test_results.append(("인간 행동 모방", "실패", "링크 없음"))
                else:
                    print("❌ 네이버 링크 못 찾음")
                    self.test_results.append(("인간 행동 모방", "실패", "검색 실패"))

            except Exception as e:
                print(f"❌ 오류: {str(e)}")
                self.test_results.append(("인간 행동 모방", "실패", str(e)))

            finally:
                await browser.close()

    async def test_method_3_firefox(self):
        """테스트 3: Firefox 브라우저 사용"""
        print("\n" + "="*60)
        print("테스트 3: Firefox 브라우저 사용")
        print("="*60)

        try:
            async with async_playwright() as p:
                browser = await p.firefox.launch(headless=False)

                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                    locale='ko-KR'
                )

                page = await context.new_page()

                print("Firefox로 접속 시도")
                await page.goto("https://shopping.naver.com/ns/home")
                await page.wait_for_timeout(3000)

                content = await page.content()
                if "security" in content.lower() or "verification" in content.lower():
                    print("❌ 실패: Firefox도 차단됨")
                    self.test_results.append(("Firefox 브라우저", "실패", "보안 검증"))
                else:
                    print("✅ 성공: Firefox로 접속 성공!")
                    self.test_results.append(("Firefox 브라우저", "성공", ""))

                await browser.close()

        except Exception as e:
            print(f"❌ Firefox 오류: {str(e)}")
            print("Firefox 브라우저가 설치되지 않았을 수 있습니다.")
            print("설치 명령: playwright install firefox")
            self.test_results.append(("Firefox 브라우저", "실패", str(e)))

    async def test_method_4_webkit(self):
        """테스트 4: WebKit (Safari) 브라우저 사용"""
        print("\n" + "="*60)
        print("테스트 4: WebKit 브라우저 사용")
        print("="*60)

        try:
            async with async_playwright() as p:
                browser = await p.webkit.launch(headless=False)

                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                    locale='ko-KR'
                )

                page = await context.new_page()

                print("WebKit으로 접속 시도")
                await page.goto("https://shopping.naver.com/ns/home")
                await page.wait_for_timeout(3000)

                content = await page.content()
                if "security" in content.lower() or "verification" in content.lower():
                    print("❌ 실패: WebKit도 차단됨")
                    self.test_results.append(("WebKit 브라우저", "실패", "보안 검증"))
                else:
                    print("✅ 성공: WebKit으로 접속 성공!")
                    self.test_results.append(("WebKit 브라우저", "성공", ""))

                await browser.close()

        except Exception as e:
            print(f"❌ WebKit 오류: {str(e)}")
            print("WebKit 브라우저가 설치되지 않았을 수 있습니다.")
            print("설치 명령: playwright install webkit")
            self.test_results.append(("WebKit 브라우저", "실패", str(e)))

    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n" + "🔬"*30)
        print("네이버 쇼핑 고급 접속 테스트")
        print("🔬"*30)

        await self.test_method_1_full_stealth()
        await asyncio.sleep(2)

        await self.test_method_2_human_behavior()
        await asyncio.sleep(2)

        await self.test_method_3_firefox()
        await asyncio.sleep(2)

        await self.test_method_4_webkit()

        # 결과 요약
        self.print_summary()

    def print_summary(self):
        """테스트 결과 요약"""
        print("\n" + "📊"*30)
        print("고급 테스트 결과 요약")
        print("📊"*30)

        success_count = sum(1 for _, result, _ in self.test_results if result == "성공")
        fail_count = sum(1 for _, result, _ in self.test_results if result == "실패")

        print(f"\n총 테스트: {len(self.test_results)}개")
        print(f"✅ 성공: {success_count}개")
        print(f"❌ 실패: {fail_count}개")

        print("\n상세 결과:")
        print("-"*60)
        for method, result, detail in self.test_results:
            symbol = "✅" if result == "성공" else "❌"
            print(f"{symbol} {method}: {result} {f'({detail})' if detail else ''}")

        if success_count > 0:
            print("\n🎉 성공한 방법이 있습니다!")
            successful = [m for m, r, _ in self.test_results if r == "성공"]
            print(f"성공 방법: {', '.join(successful)}")
            print("\n💡 다음 단계:")
            print("1. 성공한 방법을 크롤러에 적용")
            print("2. 안정성 테스트 진행")
            print("3. 실제 데이터 수집 시작")
        else:
            print("\n💭 추가 시도 방법:")
            print("1. 실제 Chrome 프로필 사용 (기존 쿠키 활용)")
            print("2. Selenium Stealth 라이브러리 사용")
            print("3. Undetected-chromedriver 사용")
            print("4. 프록시 서버 경유")

async def main():
    tester = AdvancedTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())