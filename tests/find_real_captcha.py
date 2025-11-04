#!/usr/bin/env python3
"""
정확한 캡차 셀렉터 찾기 - 실제 크롤러와 동일한 흐름
네이버 메인 → 쇼핑 → 카테고리 → 캡차
"""
import asyncio
from playwright.async_api import async_playwright

async def find_real_captcha_selector():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        print("="*60)
        print("1단계: 네이버 메인 접속...")
        print("="*60)
        await page.goto('https://www.naver.com')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

        print("\n" + "="*60)
        print("2단계: 쇼핑 탭 클릭...")
        print("="*60)
        shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a')
        await shopping_link.click()
        await asyncio.sleep(3)

        print("\n" + "="*60)
        print("3단계: 새 탭으로 전환...")
        print("="*60)
        all_pages = context.pages
        if len(all_pages) > 1:
            page = all_pages[-1]
            await page.wait_for_load_state('networkidle')
        print(f"현재 페이지: {page.url}")

        print("\n" + "="*60)
        print("4단계: 카테고리 버튼 클릭...")
        print("="*60)
        try:
            category_btn = await page.wait_for_selector('button:has-text("카테고리")', timeout=10000)
            await category_btn.click()
            await asyncio.sleep(2)
            print("✅ 카테고리 버튼 클릭 완료")
        except Exception as e:
            print(f"❌ 카테고리 버튼 클릭 실패: {e}")
            print("페이지 구조 확인 중...")
            buttons = await page.query_selector_all('button')
            for btn in buttons[:10]:
                text = await btn.inner_text()
                print(f"  버튼: {text}")

        print("\n" + "="*60)
        print("5단계: 여성의류 카테고리 클릭...")
        print("="*60)
        try:
            category_elem = await page.wait_for_selector('#cat_layer_item_10000107', timeout=5000)
            await category_elem.click()
            await asyncio.sleep(3)
            print("✅ 여성의류 카테고리 클릭 완료")
        except Exception as e:
            print(f"❌ 카테고리 클릭 실패: {e}")
            print("대체 셀렉터 시도: a[data-name='여성의류']")
            try:
                alt_category = await page.wait_for_selector('a[data-name="여성의류"]', timeout=5000)
                await alt_category.click()
                await asyncio.sleep(3)
                print("✅ 대체 셀렉터로 클릭 완료")
            except Exception as e2:
                print(f"❌ 대체 셀렉터도 실패: {e2}")

        print("\n" + "="*60)
        print("6단계: 캡차 페이지 분석 중...")
        print("="*60)
        print(f"현재 URL: {page.url}")
        print(f"페이지 타이틀: {await page.title()}")

        # 캡차 관련 텍스트 확인
        page_content = await page.content()
        captcha_keywords = ['캡차', 'captcha', '보안', '자동입력', '인증']
        for keyword in captcha_keywords:
            if keyword in page_content.lower():
                print(f"  ✓ '{keyword}' 텍스트 발견")

        print("\n" + "-"*60)
        print("모든 보이는 INPUT 필드 분석:")
        print("-"*60)

        # 모든 input 필드 찾기
        all_inputs = await page.query_selector_all('input')
        text_input_found = False

        for i, input_elem in enumerate(all_inputs):
            is_visible = await input_elem.is_visible()
            if not is_visible:
                continue

            input_type = await input_elem.get_attribute('type') or 'text'
            if input_type == 'hidden':
                continue

            input_id = await input_elem.get_attribute('id') or ''
            input_name = await input_elem.get_attribute('name') or ''
            input_class = await input_elem.get_attribute('class') or ''
            input_placeholder = await input_elem.get_attribute('placeholder') or ''

            print(f"\n[입력 필드 #{i+1}]")
            print(f"  type: {input_type}")
            print(f"  id: {input_id}")
            print(f"  name: {input_name}")
            print(f"  class: {input_class}")
            print(f"  placeholder: {input_placeholder}")

            # 텍스트 입력 필드인 경우
            if input_type in ['text', '']:
                text_input_found = True
                print(f"\n  🎯 텍스트 입력 필드 발견!")
                print(f"  📋 추천 셀렉터:")

                if input_id:
                    print(f"     - input#{input_id}")
                if input_name:
                    print(f"     - input[name='{input_name}']")
                if input_class:
                    class_parts = input_class.split()
                    if class_parts:
                        print(f"     - input.{class_parts[0]}")
                if input_placeholder:
                    print(f"     - input[placeholder*='{input_placeholder[:20]}']")

                # 이 필드에 포커스 및 하이라이트
                print(f"\n  ✨ 포커스 및 하이라이트 적용 중...")
                await input_elem.focus()
                await input_elem.click()

                # 노란색 강조
                await page.evaluate("""
                    (element) => {
                        element.style.border = '5px solid #FFD700';
                        element.style.backgroundColor = '#FFFACD';
                        element.style.boxShadow = '0 0 20px #FFD700';
                        element.style.animation = 'pulse 1s infinite';

                        const style = document.createElement('style');
                        style.innerHTML = `
                            @keyframes pulse {
                                0% { box-shadow: 0 0 10px #FFD700; }
                                50% { box-shadow: 0 0 30px #FFD700; }
                                100% { box-shadow: 0 0 10px #FFD700; }
                            }
                        `;
                        document.head.appendChild(style);
                    }
                """, input_elem)

                # 테스트 입력
                await input_elem.type("TEST", delay=500)
                print(f"  ✅ 'TEST' 입력 완료")

        if not text_input_found:
            print("\n⚠️ 텍스트 입력 필드를 찾지 못했습니다.")
            print("캡차가 나타나지 않았을 수 있습니다.")

        print("\n" + "="*60)
        print("분석 완료!")
        print("노란색으로 강조된 필드가 캡차 입력 필드입니다.")
        print("위 셀렉터 중 하나를 simple_crawler.py에 적용하세요.")
        print("="*60)
        print("\n30초 후 브라우저를 닫습니다...")
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_real_captcha_selector())
