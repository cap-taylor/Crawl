#!/usr/bin/env python3
"""
셀렉터 확인 테스트 - 실제 상품 페이지에서 어떤 셀렉터가 작동하는지 확인
"""

import asyncio
from playwright.async_api import async_playwright

async def test_selector():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 실제 상품 페이지로 직접 이동
        test_url = "https://smartstore.naver.com/generalmall/products/11764564945"
        print(f"[접속] {test_url}")
        await page.goto(test_url, wait_until='networkidle', timeout=30000)

        print("\n[셀렉터 테스트 시작]")

        # 다양한 셀렉터 시도
        selectors = [
            # 현재 config.py에 있는 것들
            'h3',
            'h3[class*="title"]',
            'h2[class*="title"]',
            'div[class*="productTitle"]',
            '[class*="product_title"]',

            # 추가로 시도해볼 것들
            'h1',
            'h2',
            '[class*="name"]',
            '[class*="Name"]',
            'div[class*="heading"]',
            'span[class*="title"]',
            'strong[class*="name"]',
            '[role="heading"]',
            'meta[property="og:title"]',  # 메타 태그
        ]

        for selector in selectors:
            try:
                if selector.startswith('meta'):
                    # 메타 태그는 다르게 처리
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.get_attribute('content')
                        print(f"✅ {selector}: '{text[:50]}...'")
                else:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.text_content()
                        if text and len(text.strip()) > 0:
                            print(f"✅ {selector}: '{text[:50]}...'")
                        else:
                            print(f"❌ {selector}: 빈 텍스트")
                    else:
                        print(f"❌ {selector}: 요소 없음")
            except Exception as e:
                print(f"❌ {selector}: 에러 - {str(e)[:30]}")

        print("\n[JavaScript로 모든 텍스트 요소 확인]")
        # JavaScript로 더 자세히 확인
        result = await page.evaluate("""
            () => {
                const elements = [];
                // 큰 텍스트 요소들 찾기
                document.querySelectorAll('h1, h2, h3, h4, strong').forEach(el => {
                    const text = el.textContent.trim();
                    if (text.length > 10 && text.length < 200) {
                        elements.push({
                            tag: el.tagName.toLowerCase(),
                            className: el.className,
                            text: text.substring(0, 50)
                        });
                    }
                });
                return elements.slice(0, 10);  // 상위 10개만
            }
        """)

        for item in result:
            print(f"  {item['tag']}.{item['className']}: '{item['text']}...'")

        await browser.close()
        print("\n[테스트 완료]")

if __name__ == "__main__":
    asyncio.run(test_selector())