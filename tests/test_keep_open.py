#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
브라우저 유지하면서 테스트
"""

import asyncio
from playwright.async_api import async_playwright

async def test_keep_browser_open():
    """브라우저 유지하면서 접속 테스트"""
    print("="*60)
    print("브라우저 유지 테스트 - 종료하지 않음")
    print("="*60)

    async with async_playwright() as p:
        # 브라우저 실행 (전체화면)
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )

        context = await browser.new_context(
            no_viewport=True  # 전체화면을 위해
        )

        page = await context.new_page()

        # naver.com 접속
        print("1. naver.com 접속 중...")
        await page.goto("https://www.naver.com")
        await page.wait_for_load_state('networkidle')
        print("✅ 네이버 메인 접속 성공")

        # 5초 대기
        await asyncio.sleep(5)

        # 쇼핑 클릭 시도
        print("2. 쇼핑 링크 찾는 중...")
        shopping_link = await page.query_selector('a[href*="shopping"]')
        if shopping_link:
            print("3. 쇼핑 링크 클릭...")
            await shopping_link.click()
            await page.wait_for_load_state('networkidle')
            print("✅ 쇼핑 페이지 이동 성공")

        # 브라우저 유지 (무한 대기)
        print("\n⚠️ 브라우저를 종료하지 않습니다!")
        print("직접 테스트하세요. Ctrl+C로 종료하세요.")
        while True:
            await asyncio.sleep(60)  # 1분마다 대기

if __name__ == "__main__":
    asyncio.run(test_keep_browser_open())