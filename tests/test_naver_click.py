#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 접속 후 클릭 테스트
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    print("="*60)
    print("네이버 접속")
    print("="*60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )

        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        # 네이버 접속
        print("네이버 접속 중...")
        await page.goto("https://www.naver.com")
        await page.wait_for_load_state('networkidle')
        print("✅ 네이버 접속 완료")

        # 브라우저 유지
        print("\n브라우저 유지 중... (Ctrl+C로 종료)")
        while True:
            await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n종료")