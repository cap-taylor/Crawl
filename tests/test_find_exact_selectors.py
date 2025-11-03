#!/usr/bin/env python3
"""
정확한 셀렉터 찾기 - evaluate로 DOM 직접 탐색
"""
import asyncio
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright

async def find_exact_selectors():
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

        print(f"상품 페이지 접속\n")
        await page.goto(url)
        await page.wait_for_load_state('networkidle')

        print("="*80)
        print("JavaScript로 가격 요소 찾기")
        print("="*80 + "\n")

        # JavaScript로 "67,900원" 텍스트를 포함한 요소 찾기
        result = await page.evaluate('''() => {
            const results = [];
            const targetPrices = ['67,900', '67900', '679'];

            // 모든 요소 순회
            const allElements = document.querySelectorAll('*');

            for (let elem of allElements) {
                const text = elem.textContent || '';

                // 가격 패턴 확인
                for (let price of targetPrices) {
                    if (text.includes(price) && text.includes('원')) {
                        // 자식 요소가 없거나 적은 경우만 (리프 노드)
                        if (elem.children.length <= 1) {
                            results.push({
                                tag: elem.tagName,
                                class: elem.className,
                                id: elem.id,
                                text: elem.textContent.trim().substring(0, 100),
                                html: elem.outerHTML.substring(0, 500)
                            });
                            break;
                        }
                    }
                }
            }

            return results;
        }''')

        print(f"가격 요소 {len(result)}개 발견:\n")
        for i, elem in enumerate(result[:10], 1):
            print(f"[{i}] {elem['tag']}")
            print(f"    class: {elem['class']}")
            print(f"    id: {elem['id']}")
            print(f"    text: {elem['text']}")
            print(f"    HTML: {elem['html'][:200]}...")
            print()

        # 40% 할인율 찾기
        print("\n" + "="*80)
        print("JavaScript로 할인율 요소 찾기")
        print("="*80 + "\n")

        discount_result = await page.evaluate('''() => {
            const results = [];
            const allElements = document.querySelectorAll('*');

            for (let elem of allElements) {
                const text = elem.textContent || '';

                if (text.includes('40%') && text.length < 50) {
                    if (elem.children.length <= 1) {
                        results.push({
                            tag: elem.tagName,
                            class: elem.className,
                            id: elem.id,
                            text: elem.textContent.trim(),
                            html: elem.outerHTML.substring(0, 500)
                        });
                    }
                }
            }

            return results;
        }''')

        print(f"할인율 요소 {len(discount_result)}개 발견:\n")
        for i, elem in enumerate(discount_result[:10], 1):
            print(f"[{i}] {elem['tag']}")
            print(f"    class: {elem['class']}")
            print(f"    text: {elem['text']}")
            print(f"    HTML: {elem['html'][:200]}...")
            print()

        # 리뷰, 평점 찾기
        print("\n" + "="*80)
        print("JavaScript로 리뷰/평점 요소 찾기")
        print("="*80 + "\n")

        review_result = await page.evaluate('''() => {
            const results = [];
            const allElements = document.querySelectorAll('*');

            for (let elem of allElements) {
                const text = elem.textContent || '';

                // 리뷰, 평점 관련 키워드
                if ((text.includes('리뷰') || text.includes('평점') || text.includes('별점'))
                    && text.length < 100) {
                    if (elem.children.length <= 2) {
                        results.push({
                            tag: elem.tagName,
                            class: elem.className,
                            text: elem.textContent.trim(),
                            html: elem.outerHTML.substring(0, 300)
                        });
                    }
                }
            }

            return results;
        }''')

        print(f"리뷰/평점 요소 {len(review_result)}개 발견:\n")
        for i, elem in enumerate(review_result[:10], 1):
            print(f"[{i}] {elem['tag']}")
            print(f"    class: {elem['class']}")
            print(f"    text: {elem['text'][:80]}")
            print()

        print("\n브라우저 60초 유지")
        await asyncio.sleep(60)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_exact_selectors())
