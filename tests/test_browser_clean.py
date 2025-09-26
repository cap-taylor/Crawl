#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
브라우저 종료 시 프로세스도 같이 종료
"""

import asyncio
from playwright.async_api import async_playwright
import signal
import sys

async def main():
    print("="*60)
    print("네이버 쇼핑 접속 테스트 (자동 정리)")
    print("="*60)

    browser = None

    # 종료 시그널 핸들러
    def signal_handler(sig, frame):
        print("\n프로그램 종료 중...")
        if browser:
            asyncio.create_task(browser.close())
        sys.exit(0)

    # Ctrl+C 시그널 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        async with async_playwright() as p:
            # 브라우저 실행
            print("\n1. 브라우저 실행...")
            browser = await p.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )

            context = await browser.new_context(no_viewport=True)
            page = await context.new_page()

            # 네이버 메인 접속
            print("2. 네이버 메인 접속...")
            await page.goto("https://www.naver.com")
            await page.wait_for_load_state('networkidle')
            print("✅ 네이버 메인 접속 완료")

            # 3초 대기
            await asyncio.sleep(3)

            # 쇼핑 클릭
            print("\n3. 쇼핑 아이콘 클릭...")
            shopping_selector = "#shortcutArea > ul > li:nth-child(4) > a"

            shopping_link = await page.query_selector(shopping_selector)
            if shopping_link:
                await shopping_link.click()
                print("✅ 쇼핑 클릭!")

                # 새 탭 대기
                await asyncio.sleep(5)

                # 새 탭 확인
                pages = context.pages
                if len(pages) > 1:
                    shopping_page = pages[-1]
                    await shopping_page.wait_for_load_state('networkidle')

                    url = shopping_page.url
                    title = await shopping_page.title()

                    print(f"\n✅ 쇼핑 페이지 접속 성공!")
                    print(f"   URL: {url}")
                    print(f"   제목: {title}")

            # 브라우저 유지 (page closed 이벤트 감지)
            print("\n" + "="*60)
            print("브라우저 유지 중...")
            print("브라우저를 닫으면 자동 종료됩니다.")
            print("또는 Ctrl+C로 종료하세요.")
            print("="*60)

            # 브라우저가 닫히면 자동 종료
            page.on('close', lambda: sys.exit(0))

            # context가 닫히면 자동 종료
            async def on_context_close():
                print("\n브라우저가 닫혔습니다. 프로그램 종료...")
                sys.exit(0)

            context.on('close', on_context_close)

            # 무한 대기 (브라우저가 닫힐 때까지)
            while True:
                # 브라우저가 살아있는지 확인
                try:
                    if not browser.is_connected():
                        print("\n브라우저 연결이 끊어졌습니다. 종료...")
                        break
                except:
                    break

                await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n사용자가 종료했습니다.")
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
    finally:
        # 브라우저가 열려있으면 닫기
        if browser and browser.is_connected():
            await browser.close()
        print("정리 완료")
        sys.exit(0)

if __name__ == "__main__":
    # 비동기 실행 (예외 처리 포함)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n프로그램 종료")
        sys.exit(0)
    except Exception as e:
        print(f"\n예외 발생: {str(e)}")
        sys.exit(1)