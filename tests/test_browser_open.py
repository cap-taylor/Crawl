#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
브라우저 열어두고 대기
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    """브라우저 열어두기"""
    print("브라우저 시작...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )

        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        print("네이버 접속...")
        await page.goto("https://www.naver.com")
        print("접속 완료!")

        print("\n브라우저 열어두는 중... (절대 종료하지 않음)")
        print("Ctrl+C로 수동 종료하세요")

        # 무한 대기
        while True:
            await asyncio.sleep(100)

if __name__ == "__main__":
    asyncio.run(main())