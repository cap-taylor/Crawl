#!/usr/bin/env python3
"""
현재 떠있는 캡차 페이지에서 입력 필드 찾기
"""
import asyncio
from playwright.async_api import async_playwright

async def find_captcha_input():
    async with async_playwright() as p:
        # 브라우저 실행
        browser = await p.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        # 캡차 페이지로 직접 이동 (테스트용)
        print("네이버 쇼핑 직접 접속 (캡차 유발)...")
        await page.goto('https://shopping.naver.com')
        await asyncio.sleep(3)

        # 현재 페이지 URL과 타이틀 확인
        current_url = page.url
        current_title = await page.title()

        print("\n" + "="*60)
        print("현재 페이지 정보:")
        print(f"URL: {current_url}")
        print(f"Title: {current_title}")
        print("="*60)

        # 캡차 관련 텍스트가 있는지 확인
        print("\n[캡차 관련 텍스트 검색]")
        captcha_indicators = [
            'robot', 'captcha', 'verify', 'human', 'security',
            '로봇', '캡차', '보안', '인증', '확인'
        ]

        page_content = await page.content()
        for indicator in captcha_indicators:
            if indicator.lower() in page_content.lower():
                print(f"  ✓ '{indicator}' 발견")

        # 모든 보이는 input 필드 찾기
        print("\n[모든 보이는 INPUT 필드]")
        all_inputs = await page.query_selector_all('input')

        text_inputs = []
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

            print(f"\n입력 필드 #{i+1}:")
            print(f"  type: {input_type}")
            print(f"  id: {input_id}")
            print(f"  name: {input_name}")
            print(f"  class: {input_class}")
            print(f"  placeholder: {input_placeholder}")

            if input_type in ['text', 'email', 'password', '']:
                text_inputs.append(input_elem)
                print(f"  🎯 텍스트 입력 가능 필드!")

                # 셀렉터 생성
                selector = None
                if input_id:
                    selector = f"input#{input_id}"
                elif input_name:
                    selector = f"input[name='{input_name}']"
                elif input_class:
                    class_parts = input_class.split()[0]
                    selector = f"input.{class_parts}"
                else:
                    selector = f"input[type='{input_type}']"

                print(f"  추천 셀렉터: {selector}")

        # 첫 번째 텍스트 입력 필드에 포커스
        if text_inputs:
            print(f"\n총 {len(text_inputs)}개의 텍스트 입력 필드 발견!")
            print("첫 번째 필드에 포커스를 맞춥니다...")

            first_input = text_inputs[0]

            # 포커스 및 하이라이트
            await first_input.focus()
            await first_input.click()

            # 노란색 하이라이트
            await page.evaluate("""
                (element) => {
                    element.style.border = '3px solid #FFD700';
                    element.style.backgroundColor = '#FFFACD';
                    element.style.boxShadow = '0 0 10px #FFD700';

                    // 깜빡이는 애니메이션
                    element.style.animation = 'pulse 1s infinite';

                    const style = document.createElement('style');
                    style.innerHTML = `
                        @keyframes pulse {
                            0% { box-shadow: 0 0 10px #FFD700; }
                            50% { box-shadow: 0 0 20px #FFD700; }
                            100% { box-shadow: 0 0 10px #FFD700; }
                        }
                    `;
                    document.head.appendChild(style);
                }
            """, first_input)

            # 테스트로 텍스트 입력
            await first_input.type("TEST", delay=500)

            print("\n✅ 포커스 완료! 노란색으로 하이라이트됨")
            print("'TEST'를 입력해봤습니다.")

        # iframe 확인
        print("\n[IFRAME 확인]")
        iframes = await page.query_selector_all('iframe')
        print(f"iframe 개수: {len(iframes)}")

        for i, iframe in enumerate(iframes):
            frame_src = await iframe.get_attribute('src') or ''
            frame_id = await iframe.get_attribute('id') or ''
            print(f"  iframe #{i+1}: id={frame_id}, src={frame_src[:50]}...")

            # iframe 내부 확인
            if 'captcha' in frame_src.lower() or 'recaptcha' in frame_src.lower():
                print(f"    🎯 캡차 관련 iframe 발견!")

        print("\n" + "="*60)
        print("분석 완료! 30초 후 브라우저를 닫습니다...")
        print("="*60)

        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_captcha_input())