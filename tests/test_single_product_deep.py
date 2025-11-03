#!/usr/bin/env python3
"""
한 상품 집중 분석 - price와 search_tags 정확히 찾기
"""
import asyncio
import sys
import re
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright

async def analyze_single_product():
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

        # 직접 상품 페이지 접속
        test_url = "https://smartstore.naver.com/main/products/8748744637"

        print(f"[1] 상품 페이지 직접 접속")
        print(f"    {test_url}\n")

        await page.goto(test_url)
        await page.wait_for_load_state('networkidle')

        print("="*70)
        print("PRICE 찾기")
        print("="*70 + "\n")

        # 페이지에서 숫자 포함된 모든 텍스트 찾기
        price_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*원',
            r'(\d+)\s*원',
        ]

        page_text = await page.inner_text('body')

        for pattern in price_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                print(f"패턴 '{pattern}' 매치:")
                for m in matches[:10]:
                    print(f"  - {m}원")
                print()

        # 가격 관련 요소 찾기
        print("\n가격 관련 셀렉터 테스트:")
        price_selectors = [
            ('span.price', 'span.price'),
            ('em (price 포함)', 'em[class*="price"]'),
            ('strong (price 포함)', 'strong[class*="price"]'),
            ('div (price 포함)', 'div[class*="price"]'),
            ('span (cost 포함)', 'span[class*="cost"]'),
        ]

        for desc, selector in price_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"\n[{desc}] {len(elements)}개 발견:")
                    for i, elem in enumerate(elements[:5], 1):
                        text = await elem.inner_text()
                        if text:
                            print(f"  {i}. {text}")
            except Exception as e:
                print(f"[{desc}] 오류: {str(e)[:30]}")

        print("\n" + "="*70)
        print("SEARCH_TAGS 찾기")
        print("="*70 + "\n")

        # 점진적 스크롤
        print("점진적 스크롤 (10% ~ 70%):")
        for scroll_pos in range(10, 71, 10):
            await page.evaluate(f'window.scrollTo(0, document.body.scrollHeight * {scroll_pos/100})')
            await asyncio.sleep(2)

            # # 포함된 링크 찾기
            all_links = await page.query_selector_all('a')
            tags_found = []

            for link in all_links:
                try:
                    text = await link.inner_text()
                    if text and text.strip().startswith('#'):
                        clean_tag = text.strip().replace('#', '').strip()
                        if 1 < len(clean_tag) < 30 and clean_tag not in tags_found:
                            tags_found.append(clean_tag)
                except:
                    pass

            print(f"  {scroll_pos}%: {len(all_links)}개 링크 → {len(tags_found)}개 태그")

            if tags_found:
                print(f"       발견된 태그: {tags_found[:10]}")
                break

        # 전체 링크에서 # 포함된 텍스트 검색
        print("\n\n전체 페이지에서 '#' 텍스트 검색:")
        if '#' in page_text:
            hash_positions = [i for i, c in enumerate(page_text) if c == '#']
            print(f"  '#' 문자 {len(hash_positions)}개 발견")

            # 처음 10개 # 주변 텍스트
            print("\n  처음 10개 # 주변 텍스트:")
            for i, pos in enumerate(hash_positions[:10], 1):
                start = max(0, pos - 5)
                end = min(len(page_text), pos + 30)
                context = page_text[start:end]
                print(f"    {i}. ...{context}...")
        else:
            print("  '#' 문자 없음")

        print("\n\n브라우저 60초 유지 (직접 확인)")
        print("스크롤해서 가격과 검색태그 위치를 확인하세요!")
        await asyncio.sleep(60)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_single_product())
