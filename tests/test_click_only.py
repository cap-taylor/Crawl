#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 메인에서 쇼핑 클릭 - 새 탭 말고 클릭만!
"""

import asyncio
from playwright.async_api import async_playwright
import sys

async def main():
    print("="*60)
    print("네이버 → 쇼핑 클릭 테스트")
    print("="*60)

    try:
        async with async_playwright() as p:
            # 브라우저 실행
            print("\n1. 브라우저 실행...")
            browser = await p.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )

            context = await browser.new_context(no_viewport=True)

            # 새 탭 열리는 것 방지 - 같은 탭에서 이동하도록
            await context.route('**/*', lambda route: route.continue_())

            page = await context.new_page()

            # 네이버 메인 접속
            print("2. 네이버 메인 접속...")
            await page.goto("https://www.naver.com")
            await page.wait_for_load_state('networkidle')
            print("✅ 네이버 메인 접속 완료")

            # 3초 대기
            await asyncio.sleep(3)

            # 쇼핑 클릭 - target="_blank" 제거하고 클릭
            print("\n3. 쇼핑 아이콘 클릭 (같은 탭에서)...")

            # target="_blank" 속성 제거
            await page.evaluate("""
                const shoppingLink = document.querySelector('#shortcutArea > ul > li:nth-child(4) > a');
                if (shoppingLink) {
                    shoppingLink.removeAttribute('target');
                    console.log('target 속성 제거됨');
                }
            """)

            # 쇼핑 링크 클릭
            shopping_selector = "#shortcutArea > ul > li:nth-child(4) > a"
            shopping_link = await page.query_selector(shopping_selector)

            if shopping_link:
                print("쇼핑 링크 클릭...")
                await shopping_link.click()
                print("✅ 클릭 완료!")

                # 페이지 이동 대기
                print("페이지 이동 대기...")
                await page.wait_for_load_state('networkidle')

                # 현재 페이지 정보
                url = page.url
                title = await page.title()

                print(f"\n현재 페이지:")
                print(f"   URL: {url}")
                print(f"   제목: {title}")

                if "shopping" in url:
                    print("🎉 쇼핑 페이지 접속 성공!")

                    # 캡차 확인
                    content = await page.content()
                    if "captcha" in content.lower() or "보안" in content:
                        print("⚠️ 캡차 발생")
                    else:
                        print("✅ 캡차 없이 정상 접속!")
                else:
                    print("⚠️ 아직 네이버 메인페이지")
            else:
                print("❌ 쇼핑 링크를 찾을 수 없음")

            # 브라우저 유지
            print("\n" + "="*60)
            print("브라우저 유지 중... (브라우저 닫으면 자동 종료)")
            print("="*60)

            # 브라우저가 닫힐 때까지 대기
            while browser.is_connected():
                await asyncio.sleep(1)

            print("\n브라우저가 닫혔습니다.")

    except KeyboardInterrupt:
        print("\n사용자가 종료했습니다.")
    except Exception as e:
        print(f"\n오류: {str(e)}")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())