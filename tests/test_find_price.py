#!/usr/bin/env python3
"""
가격 정보 찾기 - 전체 페이지 스캔
"""
import asyncio
import sys
import re
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright

async def find_price_info():
    # 직접 상품 페이지 접속
    url = "https://smartstore.naver.com/main/products/10981638556"

    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=500
        )

        context = await browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            extra_http_headers={
                'Accept-Language': 'ko-KR,ko;q=0.9'
            }
        )

        page = await context.new_page()

        print(f"상품 페이지 접속: {url}\n")
        await page.goto(url)
        await page.wait_for_load_state('networkidle')

        print("="*80)
        print("가격 정보 전체 스캔")
        print("="*80 + "\n")

        # 페이지 전체 텍스트
        page_text = await page.inner_text('body')

        # "원" 포함된 모든 패턴 찾기
        price_patterns = [
            (r'(\d{1,3}(?:,\d{3})+)\s*원', '1,000원 형식'),
            (r'(\d+)\s*원', '숫자+원 형식'),
            (r'(\d+)%', '할인율'),
        ]

        for pattern, desc in price_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                unique = list(dict.fromkeys(matches))  # 중복 제거
                print(f"[{desc}]")
                for m in unique[:15]:
                    if '%' in pattern:
                        print(f"  - {m}%")
                    else:
                        print(f"  - {m}원")
                print()

        # 가격 관련 요소의 HTML 구조 확인
        print("\n" + "="*80)
        print("가격 요소 HTML 구조")
        print("="*80 + "\n")

        # 모든 요소 중 "원" 텍스트 포함된 것 찾기
        all_elements = await page.query_selector_all('*')
        price_elements = []

        for elem in all_elements[:500]:  # 처음 500개만
            try:
                text = await elem.inner_text()
                if text and '원' in text and len(text) < 50:
                    # 숫자 포함 여부
                    if re.search(r'\d', text):
                        tag = await elem.evaluate('el => el.tagName')
                        class_name = await elem.get_attribute('class')
                        html = await elem.evaluate('el => el.outerHTML')

                        price_elements.append({
                            'text': text,
                            'tag': tag,
                            'class': class_name,
                            'html': html[:300]
                        })
            except:
                pass

        # 중복 제거 (텍스트 기준)
        seen_texts = set()
        unique_elements = []
        for elem in price_elements:
            if elem['text'] not in seen_texts:
                seen_texts.add(elem['text'])
                unique_elements.append(elem)

        print(f"가격 관련 요소 {len(unique_elements)}개 발견:\n")
        for i, elem in enumerate(unique_elements[:10], 1):
            print(f"[{i}] {elem['tag']}")
            print(f"    텍스트: {elem['text']}")
            print(f"    class: {elem['class']}")
            print(f"    HTML: {elem['html']}...")
            print()

        print("\n브라우저 60초 유지 (직접 확인)")
        print("Ctrl+F로 '원' 검색해서 가격이 어디 있는지 확인하세요!")
        await asyncio.sleep(60)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_price_info())
