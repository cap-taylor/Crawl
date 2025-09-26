#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 메인 페이지 접속 테스트
"""

import asyncio
from playwright.async_api import async_playwright

async def test_naver_main():
    """네이버 메인 페이지 접속"""
    print("="*60)
    print("네이버 메인 페이지 접속 테스트")
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

        print("2. 페이지 로드 대기...")
        await page.wait_for_load_state('networkidle')

        title = await page.title()
        print(f"3. 페이지 타이틀: {title}")

        # 10초 대기 (확인용)
        print("4. 10초 대기 중...")
        await asyncio.sleep(10)

        await browser.close()
        print("테스트 완료")

if __name__ == "__main__":
    asyncio.run(test_naver_main())