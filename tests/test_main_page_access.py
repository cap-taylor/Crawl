#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 쇼핑 메인페이지 접속 테스트
다양한 방법으로 시도하고 성공/실패 기록
"""

import asyncio
from playwright.async_api import async_playwright
import time
from datetime import datetime

class MainPageTester:
    def __init__(self):
        self.test_results = []
        self.success_count = 0
        self.fail_count = 0

    async def test_method_1_basic(self):
        """테스트 1: 기본 접속 (아무 설정 없이)"""
        print("\n" + "="*60)
        print("테스트 1: 기본 접속")
        print("="*60)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            try:
                print("접속 시도: https://shopping.naver.com/ns/home")
                response = await page.goto("https://shopping.naver.com/ns/home")
                await page.wait_for_timeout(3000)

                # 페이지 확인
                title = await page.title()
                url = page.url

                print(f"페이지 타이틀: {title}")
                print(f"현재 URL: {url}")

                # 봇 감지 체크
                content = await page.content()
                if "security" in content.lower() or "verification" in content.lower():
                    print("❌ 실패: 보안 검증 페이지 감지")
                    self.fail_count += 1
                    self.test_results.append(("기본 접속", "실패", "보안 검증 페이지"))
                else:
                    print("✅ 성공: 정상 접속")
                    self.success_count += 1
                    self.test_results.append(("기본 접속", "성공", ""))

            except Exception as e:
                print(f"❌ 오류: {str(e)}")
                self.fail_count += 1
                self.test_results.append(("기본 접속", "실패", str(e)))

            finally:
                await browser.close()

    async def test_method_2_user_agent(self):
        """테스트 2: User-Agent 설정"""
        print("\n" + "="*60)
        print("테스트 2: User-Agent 설정")
        print("="*60)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                print("User-Agent 설정 후 접속 시도")
                response = await page.goto("https://shopping.naver.com/ns/home")
                await page.wait_for_timeout(3000)

                title = await page.title()
                content = await page.content()

                if "security" in content.lower() or "verification" in content.lower():
                    print("❌ 실패: 여전히 보안 검증 페이지")
                    self.fail_count += 1
                    self.test_results.append(("User-Agent 설정", "실패", "보안 검증"))
                else:
                    print("✅ 성공: 정상 접속")
                    self.success_count += 1
                    self.test_results.append(("User-Agent 설정", "성공", ""))

            except Exception as e:
                print(f"❌ 오류: {str(e)}")
                self.fail_count += 1
                self.test_results.append(("User-Agent 설정", "실패", str(e)))

            finally:
                await browser.close()

    async def test_method_3_stealth(self):
        """테스트 3: Stealth 모드 (봇 감지 회피)"""
        print("\n" + "="*60)
        print("테스트 3: Stealth 모드")
        print("="*60)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox'
                ]
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # Stealth 설정
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ko-KR', 'ko', 'en-US', 'en']
                });
                window.chrome = {
                    runtime: {}
                };
            """)

            page = await context.new_page()

            try:
                print("Stealth 모드로 접속 시도")
                response = await page.goto("https://shopping.naver.com/ns/home")
                await page.wait_for_timeout(3000)

                title = await page.title()
                content = await page.content()

                if "security" in content.lower() or "verification" in content.lower():
                    print("❌ 실패: Stealth 모드에도 감지됨")
                    self.fail_count += 1
                    self.test_results.append(("Stealth 모드", "실패", "보안 검증"))
                else:
                    print("✅ 성공: 정상 접속!")
                    self.success_count += 1
                    self.test_results.append(("Stealth 모드", "성공", ""))

                    # 스크린샷 저장
                    await page.screenshot(path="tests/main_page_success.png")
                    print("스크린샷 저장: tests/main_page_success.png")

            except Exception as e:
                print(f"❌ 오류: {str(e)}")
                self.fail_count += 1
                self.test_results.append(("Stealth 모드", "실패", str(e)))

            finally:
                await browser.close()

    async def test_method_4_slow_typing(self):
        """테스트 4: 천천히 사람처럼 접근"""
        print("\n" + "="*60)
        print("테스트 4: 사람처럼 천천히 접근")
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

            # Stealth 설정
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            page = await context.new_page()

            try:
                # 네이버 메인 먼저 접속
                print("1단계: 네이버 메인 접속")
                await page.goto("https://www.naver.com")
                await page.wait_for_timeout(2000)

                # 쇼핑 링크 찾아서 클릭
                print("2단계: 쇼핑 링크 찾기")
                shopping_link = await page.query_selector('a[href*="shopping"]')

                if shopping_link:
                    print("3단계: 쇼핑 링크 클릭")
                    await shopping_link.click()
                    await page.wait_for_timeout(3000)

                    title = await page.title()
                    content = await page.content()

                    if "security" in content.lower() or "verification" in content.lower():
                        print("❌ 실패: 단계적 접근도 감지됨")
                        self.fail_count += 1
                        self.test_results.append(("단계적 접근", "실패", "보안 검증"))
                    else:
                        print("✅ 성공: 정상 접속!")
                        self.success_count += 1
                        self.test_results.append(("단계적 접근", "성공", ""))
                else:
                    print("❌ 쇼핑 링크를 찾을 수 없음")
                    self.fail_count += 1
                    self.test_results.append(("단계적 접근", "실패", "링크 없음"))

            except Exception as e:
                print(f"❌ 오류: {str(e)}")
                self.fail_count += 1
                self.test_results.append(("단계적 접근", "실패", str(e)))

            finally:
                await browser.close()

    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n" + "🔬"*30)
        print("네이버 쇼핑 메인페이지 접속 테스트 시작")
        print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔬"*30)

        # 각 테스트 실행
        await self.test_method_1_basic()
        await asyncio.sleep(2)

        await self.test_method_2_user_agent()
        await asyncio.sleep(2)

        await self.test_method_3_stealth()
        await asyncio.sleep(2)

        await self.test_method_4_slow_typing()

        # 결과 요약
        self.print_summary()

    def print_summary(self):
        """테스트 결과 요약"""
        print("\n" + "📊"*30)
        print("테스트 결과 요약")
        print("📊"*30)

        print(f"\n총 테스트: {len(self.test_results)}개")
        print(f"✅ 성공: {self.success_count}개")
        print(f"❌ 실패: {self.fail_count}개")
        print(f"성공률: {(self.success_count/len(self.test_results)*100):.1f}%")

        print("\n상세 결과:")
        print("-"*60)
        for method, result, detail in self.test_results:
            symbol = "✅" if result == "성공" else "❌"
            print(f"{symbol} {method}: {result} {f'({detail})' if detail else ''}")

        print("\n💡 분석:")
        if self.success_count > 0:
            print("- 일부 방법으로 접속 성공!")
            successful_methods = [m for m, r, _ in self.test_results if r == "성공"]
            print(f"- 성공한 방법: {', '.join(successful_methods)}")
        else:
            print("- 모든 방법이 차단됨")
            print("- 추가적인 우회 방법 필요")

async def main():
    tester = MainPageTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())