#!/usr/bin/env python3
"""
캡차 입력 필드 셀렉터 찾기 테스트
"""
import asyncio
from playwright.async_api import async_playwright

async def find_captcha_selector():
    async with async_playwright() as p:
        # 브라우저 실행 (화면 보이게)
        browser = await p.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        print("네이버 쇼핑 접속 중...")

        # 1. 네이버 메인 접속
        await page.goto('https://www.naver.com')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

        # 2. 쇼핑 클릭
        shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a')
        await shopping_link.click()
        await asyncio.sleep(3)

        # 3. 새 탭으로 전환
        all_pages = context.pages
        if len(all_pages) > 1:
            page = all_pages[-1]
            await page.wait_for_load_state('networkidle')

        # 4. 카테고리 버튼 클릭
        print("카테고리 버튼 클릭...")
        category_btn = await page.wait_for_selector('button:has-text("카테고리")')
        await category_btn.click()
        await asyncio.sleep(2)

        # 5. 여성의류 카테고리 클릭 (캡차 유발)
        print("여성의류 카테고리 클릭 중...")
        womens_category = await page.wait_for_selector('a[data-name="여성의류"]')
        await womens_category.click()
        await asyncio.sleep(3)

        print("\n" + "="*60)
        print("캡차 페이지 분석 중...")
        print("="*60)

        # 6. 모든 input 필드 찾기
        print("\n[모든 input 필드 검색]")
        all_inputs = await page.query_selector_all('input')
        for i, input_elem in enumerate(all_inputs):
            input_type = await input_elem.get_attribute('type')
            input_id = await input_elem.get_attribute('id')
            input_name = await input_elem.get_attribute('name')
            input_placeholder = await input_elem.get_attribute('placeholder')
            input_class = await input_elem.get_attribute('class')
            is_visible = await input_elem.is_visible()

            if is_visible and input_type != 'hidden':
                print(f"\n입력 필드 #{i+1}:")
                print(f"  - type: {input_type}")
                print(f"  - id: {input_id}")
                print(f"  - name: {input_name}")
                print(f"  - placeholder: {input_placeholder}")
                print(f"  - class: {input_class}")
                print(f"  - visible: {is_visible}")

                # 이 필드에 포커스 시도
                if input_type == 'text':
                    print(f"  🎯 텍스트 입력 필드 발견! 포커스 시도...")
                    await input_elem.focus()
                    await input_elem.click()

                    # 하이라이트
                    await page.evaluate("""
                        (element) => {
                            element.style.border = '3px solid red';
                            element.style.backgroundColor = 'yellow';
                        }
                    """, input_elem)

        # 7. 캡차 관련 텍스트 찾기
        print("\n[캡차 관련 요소 검색]")
        captcha_texts = [
            '보안 문자', '자동입력 방지', '문자를 입력', '숫자를 입력',
            '캡차', 'captcha', '보안', '인증'
        ]

        for text in captcha_texts:
            elements = await page.query_selector_all(f'text="{text}"')
            if elements:
                print(f"  - '{text}' 텍스트 발견: {len(elements)}개")

        print("\n" + "="*60)
        print("캡차 입력 필드를 찾았습니다!")
        print("빨간 테두리와 노란 배경으로 표시됨")
        print("30초 후 브라우저가 닫힙니다...")
        print("="*60)

        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_captcha_selector())