#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Headless 모드 봇 차단 테스트
네이버 쇼핑이 headless 브라우저를 감지하는지 확인
"""

import asyncio
from playwright.async_api import async_playwright
import sys
import os

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.config import CRAWL_CONFIG

async def test_headless_mode(headless=True):
    """Headless 모드로 네이버 쇼핑 접속 테스트"""
    print(f"\n{'='*50}")
    print(f"테스트 모드: {'Headless (브라우저 숨김)' if headless else 'Headful (브라우저 표시)'}")
    print(f"{'='*50}\n")

    async with async_playwright() as p:
        try:
            # 브라우저 시작
            print(f"[1/5] 브라우저 시작중... (headless={headless})")
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    f'--user-agent={CRAWL_CONFIG["user_agent"]}'
                ]
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=CRAWL_CONFIG['user_agent']
            )

            # Stealth 모드 설정
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ko-KR', 'ko']
                });
                window.chrome = {
                    runtime: {}
                };
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({state: 'granted'})
                    })
                });
            """)

            page = await context.new_page()

            # 네이버 쇼핑 접속
            print(f"[2/5] 네이버 쇼핑 접속중...")
            response = await page.goto(CRAWL_CONFIG['base_url'], wait_until='networkidle')

            # 응답 상태 확인
            print(f"[3/5] 응답 상태 코드: {response.status}")

            if response.status != 200:
                print(f"❌ 비정상 응답: {response.status}")
                return False

            # 페이지 타이틀 확인
            title = await page.title()
            print(f"[4/5] 페이지 타이틀: {title}")

            # 봇 감지 체크
            print(f"[5/5] 봇 감지 체크중...")

            # 1. 차단 페이지 감지
            blocked_texts = [
                "정상적이지 않은 방법",
                "차단",
                "blocked",
                "captcha",
                "보안문자",
                "로봇이 아닙니다"
            ]

            page_content = await page.content()
            is_blocked = False

            for blocked_text in blocked_texts:
                if blocked_text.lower() in page_content.lower():
                    print(f"❌ 봇 차단 감지: '{blocked_text}' 발견")
                    is_blocked = True
                    break

            if not is_blocked:
                # 2. 카테고리 버튼 찾기 시도
                try:
                    category_btn = await page.wait_for_selector(
                        'button:has-text("카테고리")',
                        timeout=5000
                    )
                    if category_btn:
                        print(f"✅ 카테고리 버튼 발견 - 정상 접속!")

                        # 스크린샷 저장
                        screenshot_name = f"headless_{headless}.png"
                        await page.screenshot(path=f"tests/{screenshot_name}")
                        print(f"📸 스크린샷 저장: tests/{screenshot_name}")

                        return True
                except:
                    print(f"⚠️ 카테고리 버튼을 찾을 수 없음")

                # 3. 메인 콘텐츠 확인
                try:
                    main_content = await page.query_selector('#__next')
                    if main_content:
                        print(f"✅ 메인 콘텐츠 발견 - 정상 접속 가능")
                        return True
                except:
                    pass

            await browser.close()
            return not is_blocked

        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")
            return False

async def main():
    """메인 테스트 함수"""
    print("\n" + "="*70)
    print("네이버 쇼핑 Headless 모드 봇 차단 테스트")
    print("="*70)

    # 1. Headless 모드 테스트
    headless_result = await test_headless_mode(headless=True)

    # 2초 대기
    await asyncio.sleep(2)

    # 2. Headful 모드 테스트 (비교용)
    headful_result = await test_headless_mode(headless=False)

    # 결과 요약
    print("\n" + "="*70)
    print("테스트 결과 요약")
    print("="*70)
    print(f"Headless 모드 (브라우저 숨김): {'✅ 성공' if headless_result else '❌ 차단됨'}")
    print(f"Headful 모드 (브라우저 표시): {'✅ 성공' if headful_result else '❌ 차단됨'}")

    if not headless_result:
        print("\n⚠️ Headless 모드가 차단되므로 백그라운드 실행 옵션을 제거해야 합니다.")
    else:
        print("\n✅ Headless 모드가 정상 작동하므로 백그라운드 실행 옵션을 유지할 수 있습니다.")

    return headless_result

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)