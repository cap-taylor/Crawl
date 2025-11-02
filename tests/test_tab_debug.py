#!/usr/bin/env python3
"""
탭 전환 디버깅 테스트 - CAPTCHA 후 새 탭 문제 진단
"""

import asyncio
from playwright.async_api import async_playwright

async def test_tab_switching():
    print("="*60)
    print("탭 전환 디버깅 테스트")
    print("="*60)
    print("목적: CAPTCHA 후 Ctrl+클릭이 제대로 작동하는지 확인")
    print("="*60 + "\n")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 여성의류 카테고리로 이동
        category_url = "https://search.shopping.naver.com/category/category/10000107"
        print(f"[접속] {category_url}")
        await page.goto(category_url, wait_until='networkidle', timeout=30000)

        # CAPTCHA 대기
        print("\n⚠️ CAPTCHA가 나오면 수동으로 해결해주세요!")
        print("30초 대기 중... (CAPTCHA 없으면 그냥 기다리세요)")
        await asyncio.sleep(30)

        print("\n[테스트] CAPTCHA 해결 후 테스트 시작")
        await asyncio.sleep(2)

        # 첫 번째 상품 링크 찾기
        print("\n[1단계] 상품 링크 찾기")

        # 방법 1: 직접 상품 링크 찾기
        product_links = await page.query_selector_all('a[href*="/products/"]')
        print(f"  - 찾은 상품 링크 개수: {len(product_links)}")

        if product_links:
            # 첫 번째 링크 분석
            first_link = product_links[0]
            href = await first_link.get_attribute('href')
            print(f"  - 첫 번째 링크 href: {href[:100]}...")

            # 링크 내부 구조 확인
            inner_html = await first_link.inner_html()
            has_img = '<img' in inner_html
            print(f"  - 이미지 포함 여부: {has_img}")

            # Ctrl+클릭 테스트
            print("\n[2단계] Ctrl+클릭으로 새 탭 열기")
            pages_before = len(context.pages)
            print(f"  - 현재 탭 개수: {pages_before}")

            # Hover 후 Ctrl+클릭
            await first_link.hover()
            await asyncio.sleep(1)

            print("  - Ctrl+클릭 실행...")
            await first_link.click(modifiers=['Control'])

            # 새 탭 확인
            await asyncio.sleep(3)
            pages_after = len(context.pages)
            print(f"  - 클릭 후 탭 개수: {pages_after}")

            if pages_after > pages_before:
                new_page = context.pages[-1]
                print(f"\n[3단계] 새 탭 분석")
                print(f"  - 새 탭 URL: {new_page.url}")

                # URL 패턴 확인
                if '/products/' in new_page.url:
                    print("  ✅ 상품 페이지가 정상적으로 열림!")

                    # 페이지 로딩 대기
                    await new_page.wait_for_load_state('networkidle', timeout=10000)

                    # 상품명 확인
                    h3_elem = await new_page.query_selector('h3')
                    if h3_elem:
                        product_name = await h3_elem.text_content()
                        print(f"  - 상품명: {product_name[:50]}...")
                    else:
                        print("  ❌ 상품명을 찾을 수 없음")

                elif 'category' in new_page.url:
                    print("  ❌ 카테고리 페이지가 열림 (상품 페이지 아님)")
                else:
                    print(f"  ❌ 예상치 못한 URL: {new_page.url}")

                # 새 탭 닫기
                await new_page.close()
            else:
                print("  ❌ 새 탭이 열리지 않음")

                # 대안: 일반 클릭 테스트
                print("\n[대안] 일반 클릭 테스트")
                await first_link.click()
                await asyncio.sleep(3)

                current_url = page.url
                print(f"  - 현재 URL: {current_url}")

                if '/products/' in current_url:
                    print("  - 일반 클릭으로 상품 페이지 이동됨")
                else:
                    print("  - 일반 클릭도 실패")

        # JavaScript로 링크 구조 분석
        print("\n[4단계] JavaScript로 링크 구조 분석")
        link_analysis = await page.evaluate("""
            () => {
                const links = document.querySelectorAll('a[href*="/products/"]');
                const results = [];

                for (let i = 0; i < Math.min(3, links.length); i++) {
                    const link = links[i];
                    results.push({
                        href: link.href,
                        hasOnClick: !!link.onclick,
                        target: link.target,
                        hasImage: link.querySelector('img') !== null,
                        innerHTML: link.innerHTML.substring(0, 100)
                    });
                }

                return results;
            }
        """)

        for i, info in enumerate(link_analysis, 1):
            print(f"\n  링크 {i}:")
            print(f"    - href: {info['href'][:80]}...")
            print(f"    - onclick 있음: {info['hasOnClick']}")
            print(f"    - target: {info['target']}")
            print(f"    - 이미지 있음: {info['hasImage']}")

        await browser.close()
        print("\n[완료] 테스트 종료")

if __name__ == "__main__":
    asyncio.run(test_tab_switching())