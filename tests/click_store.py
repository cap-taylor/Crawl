#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
현재 열린 브라우저에서 스토어 클릭
"""

import asyncio
from playwright.async_api import async_playwright

async def click_store():
    print("스토어 클릭 시도...")

    async with async_playwright() as p:
        # 이미 열려있는 브라우저에 연결하는 대신
        # 새 브라우저로 테스트
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
        print("✅ 네이버 접속 완료")

        await asyncio.sleep(2)

        # 스토어/쇼핑 클릭
        print("\n2. 스토어(쇼핑) 클릭 시도...")

        # 제공받은 selector 사용
        shopping_selector = "#shortcutArea > ul > li:nth-child(4) > a"

        shopping_link = await page.query_selector(shopping_selector)

        if shopping_link:
            print(f"✅ 쇼핑 링크 찾음: {shopping_selector}")
            await shopping_link.click()
            print("✅ 클릭 완료!")

            # 새 탭 확인
            await asyncio.sleep(3)

            pages = context.pages
            print(f"\n열린 탭 수: {len(pages)}")

            if len(pages) > 1:
                # 새 탭으로 전환
                new_page = pages[-1]
                await new_page.wait_for_load_state('networkidle')

                url = new_page.url
                title = await new_page.title()

                print("\n🎉 네이버 쇼핑 접속 성공!")
                print(f"URL: {url}")
                print(f"제목: {title}")

                # 캡차 확인
                content = await new_page.content()
                if "captcha" in content.lower() or "보안" in content:
                    print("⚠️ 캡차 발생!")
                else:
                    print("✅ 정상 접속 (캡차 없음)")

        else:
            print("❌ 쇼핑 링크를 찾을 수 없음")

        # 브라우저 유지
        print("\n브라우저 유지 중... (Ctrl+C로 종료)")
        while True:
            await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(click_store())
    except KeyboardInterrupt:
        print("\n종료")