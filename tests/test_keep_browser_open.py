#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
브라우저를 종료하지 않고 계속 테스트
"""

import asyncio
from playwright.async_api import async_playwright

async def test_keep_open():
    """브라우저 열어두고 테스트"""
    print("="*60)
    print("브라우저 계속 열어두기 테스트")
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

        # 1. naver.com 접속
        print("\n1단계: naver.com 접속...")
        await page.goto("https://www.naver.com")
        await page.wait_for_load_state('networkidle')
        print("✅ 네이버 메인 접속 성공")

        print("\n⏸️ 10초 대기 (원하시는 테스트를 진행하세요)...")
        await asyncio.sleep(10)

        # 2. 쇼핑 탭 클릭 시도
        print("\n2단계: 쇼핑 탭 찾기...")
        shopping_link = await page.query_selector('a[data-clk="svc.shopping"]')
        if shopping_link:
            print("쇼핑 링크 발견! 클릭합니다...")
            await shopping_link.click()
            await page.wait_for_load_state('networkidle')
            print("✅ 쇼핑 페이지 이동")
        else:
            print("❌ 쇼핑 링크를 찾을 수 없음")

        print("\n⏸️ 30초 대기 (추가 테스트 진행하세요)...")
        await asyncio.sleep(30)

        # 3. 카테고리 확인
        print("\n3단계: 카테고리 확인...")
        categories = await page.query_selector_all('.category-list a')
        print(f"카테고리 개수: {len(categories)}개")

        # 브라우저 계속 열어두기
        print("\n" + "="*60)
        print("🔴 브라우저를 종료하지 않습니다!")
        print("💡 원하시는 테스트를 계속 진행하세요")
        print("종료하려면 Ctrl+C를 누르세요")
        print("="*60)

        # 무한 대기 (수동 종료할 때까지)
        try:
            while True:
                await asyncio.sleep(60)
                print("⏰ 브라우저 유지 중... (Ctrl+C로 종료)")
        except KeyboardInterrupt:
            print("\n수동 종료 감지")
            await browser.close()
            print("브라우저 종료됨")

if __name__ == "__main__":
    try:
        asyncio.run(test_keep_open())
    except KeyboardInterrupt:
        print("\n프로그램 종료")