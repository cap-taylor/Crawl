#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 메인에서 쇼핑 클릭으로 이동
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    """클릭으로 쇼핑 이동"""
    print("="*60)
    print("네이버 메인 → 쇼핑 클릭 이동")
    print("="*60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )

        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        # 1. 네이버 메인 접속
        print("\n1. 네이버 메인 접속...")
        await page.goto("https://www.naver.com")
        await page.wait_for_load_state('networkidle')
        print("✅ 네이버 메인 접속 완료")

        # 2초 대기
        await asyncio.sleep(2)

        # 2. 쇼핑 클릭
        print("\n2. 쇼핑 아이콘 클릭...")
        shopping_selector = "#shortcutArea > ul > li:nth-child(4) > a"

        shopping_link = await page.query_selector(shopping_selector)
        if shopping_link:
            await shopping_link.click()
            print("✅ 쇼핑 클릭 완료")

            # 새 탭 대기
            await asyncio.sleep(3)

            # 새 탭 확인
            pages = context.pages
            if len(pages) > 1:
                shopping_page = pages[-1]
                await shopping_page.wait_for_load_state('networkidle')
                url = shopping_page.url
                title = await shopping_page.title()
                print(f"\n✅ 쇼핑 페이지 열림!")
                print(f"   URL: {url}")
                print(f"   제목: {title}")
            else:
                url = page.url
                print(f"현재 URL: {url}")
        else:
            print("❌ 쇼핑 링크를 찾을 수 없음")

        # 브라우저 유지
        print("\n" + "="*60)
        print("브라우저 유지 중... (Ctrl+C로 종료)")
        print("="*60)

        while True:
            await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n종료")