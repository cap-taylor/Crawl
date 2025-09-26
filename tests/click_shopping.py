#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
현재 열려있는 브라우저에서 쇼핑 클릭
"""

import asyncio
from playwright.async_api import async_playwright

async def click_shopping():
    """쇼핑 링크 클릭"""
    print("="*60)
    print("쇼핑 링크 클릭 테스트")
    print("="*60)

    async with async_playwright() as p:
        # 브라우저 실행
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )

        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        # 네이버 메인 접속
        print("1. 네이버 메인 접속...")
        await page.goto("https://www.naver.com")
        await page.wait_for_load_state('networkidle')
        print("✅ 네이버 메인 접속 완료")

        # 3초 대기
        await asyncio.sleep(3)

        # 쇼핑 링크 클릭 (제공받은 selector 사용)
        print("\n2. 쇼핑 링크 찾기...")
        selector = "#shortcutArea > ul > li:nth-child(4) > a > span.service_icon.type_shopping"

        try:
            # 해당 요소 찾기
            shopping_element = await page.query_selector(selector)

            if shopping_element:
                print(f"✅ 쇼핑 아이콘 찾음: {selector}")

                # 부모 a 태그 찾기 (span의 부모가 a 태그)
                parent_link = await page.query_selector("#shortcutArea > ul > li:nth-child(4) > a")

                if parent_link:
                    print("3. 쇼핑 링크 클릭...")
                    await parent_link.click()

                    # 새 탭이 열릴 수 있으므로 대기
                    await asyncio.sleep(3)

                    # 모든 페이지 확인
                    pages = context.pages
                    print(f"열린 페이지 수: {len(pages)}")

                    # 새 탭이 열렸다면 그 탭으로 전환
                    if len(pages) > 1:
                        new_page = pages[-1]  # 마지막 페이지가 새로 열린 탭
                        await new_page.wait_for_load_state('networkidle')
                        title = await new_page.title()
                        url = new_page.url
                        print(f"✅ 새 탭 열림!")
                        print(f"   제목: {title}")
                        print(f"   URL: {url}")

                        # 쇼핑 페이지인지 확인
                        if "shopping" in url:
                            print("🎉 쇼핑 페이지 접속 성공!")
                        else:
                            print("⚠️ 쇼핑 페이지가 아님")
                    else:
                        # 같은 탭에서 이동했을 수도 있음
                        await page.wait_for_load_state('networkidle')
                        title = await page.title()
                        url = page.url
                        print(f"현재 페이지: {title}")
                        print(f"URL: {url}")
            else:
                print(f"❌ 선택자를 찾을 수 없음: {selector}")

                # 대체 방법 시도
                print("\n대체 방법 시도...")
                alt_selector = 'a[data-clk="svc.shopping"]'
                alt_link = await page.query_selector(alt_selector)

                if alt_link:
                    print(f"✅ 대체 선택자로 찾음: {alt_selector}")
                    await alt_link.click()
                    await asyncio.sleep(3)
                    print("쇼핑 페이지로 이동 시도")
                else:
                    print("❌ 대체 선택자도 실패")

        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")

        # 브라우저 유지
        print("\n" + "="*60)
        print("브라우저를 계속 열어둡니다... (Ctrl+C로 종료)")
        print("="*60)

        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            print("\n종료합니다...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(click_shopping())