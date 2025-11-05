#!/usr/bin/env python3
"""
실제 DOM 구조를 확인하는 디버그 스크립트
첫 번째 상품의 전체 HTML을 출력하여 정확한 셀렉터 파악
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_dom():
    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            args=['--start-maximized']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )
        page = await context.new_page()

        # 1. 네이버 메인 → 쇼핑 진입 (봇 차단 회피)
        print("[1/4] 네이버 메인 페이지 접속...")
        await page.goto('https://www.naver.com')
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(2)

        # 쇼핑 클릭
        print("[2/4] 쇼핑 버튼 클릭...")
        shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
        await page.locator(shopping_selector).click(timeout=10000)
        await asyncio.sleep(2)

        # 새 탭 전환
        all_pages = context.pages
        if len(all_pages) > 1:
            page = all_pages[-1]
            await page.wait_for_load_state('networkidle')

        # 2. 카테고리 진입
        print("[3/4] '신선식품' 카테고리 진입...")
        category_btn = await page.wait_for_selector('button:has-text("카테고리")', timeout=10000)
        await category_btn.click()
        await asyncio.sleep(1)

        # 신선식품 카테고리 (ID: 10006530)
        category_id = "10006530"
        category_name = "신선식품"
        category_elem = None

        # 1순위: ID 기반
        try:
            category_elem = await page.wait_for_selector(f'#cat_layer_item_{category_id}', timeout=5000)
        except:
            pass

        # 2순위: data-id 속성
        if not category_elem:
            try:
                category_elem = await page.wait_for_selector(f'[data-id="{category_id}"]', timeout=3000)
            except:
                pass

        # 3순위: data-name 속성
        if not category_elem:
            try:
                category_elem = await page.wait_for_selector(f'a[data-name="{category_name}"]', timeout=3000)
            except:
                pass

        if not category_elem:
            raise Exception(f"카테고리 '{category_name}' (ID: {category_id})를 찾을 수 없습니다")

        await category_elem.click()
        await asyncio.sleep(3)

        # 캡차 확인 및 대기
        print("\n[캡차 확인]")
        captcha_found = False
        try:
            page_text = await page.evaluate('document.body.innerText')
            if '영수증' in page_text:
                print("🧾 영수증 캡차 감지! 브라우저에서 해결하세요 (최대 120초 대기)")
                captcha_found = True
        except:
            pass

        if captcha_found:
            for i in range(12):
                await asyncio.sleep(10)
                try:
                    page_text = await page.evaluate('document.body.innerText')
                    if '영수증' not in page_text:
                        print("[✓] 캡차 해결 완료!")
                        break
                except:
                    pass
                if i == 11:
                    print("[!] 캡차 미해결 - 계속 진행")

        await asyncio.sleep(5)

        print("[4/4] 첫 번째 상품 HTML 구조 출력...\n")

        # 상품 스크롤하여 lazy loading 트리거
        print("[스크롤] 상품 lazy loading 트리거 중...")
        await page.evaluate('window.scrollTo(0, 800)')
        await asyncio.sleep(2)
        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(1)

        # 첫 번째 상품 링크의 전체 HTML
        first_product_html = await page.evaluate('''() => {
            const sortContainer = document.querySelector('#product-sort-address-container');
            if (!sortContainer) return {error: "정렬 컨테이너 없음"};

            const sortY = sortContainer.getBoundingClientRect().bottom;
            const allLinks = Array.from(document.querySelectorAll('a[class*="ProductCard_link"]'));

            // 정렬 옵션 아래 첫 번째 상품
            const firstProduct = allLinks.find(link => {
                const rect = link.getBoundingClientRect();
                return rect.top > sortY;
            });

            if (!firstProduct) return {error: "상품 없음"};

            // aria-labelledby로 참조되는 실제 정보 찾기
            const labelId = firstProduct.getAttribute('aria-labelledby');
            const labelElem = labelId ? document.getElementById(labelId) : null;

            return {
                linkHTML: firstProduct.outerHTML.substring(0, 500),
                linkInnerHTML: firstProduct.innerHTML,
                linkClasses: Array.from(firstProduct.classList),
                linkChildren: Array.from(firstProduct.children).map(child => ({
                    tagName: child.tagName,
                    classList: Array.from(child.classList),
                    textContent: child.textContent.substring(0, 100)
                })),
                labelId: labelId,
                labelHTML: labelElem ? labelElem.outerHTML.substring(0, 1000) : "라벨 요소 없음",
                labelChildren: labelElem ? Array.from(labelElem.children).map(child => ({
                    tagName: child.tagName,
                    classList: Array.from(child.classList),
                    textContent: child.textContent.substring(0, 100)
                })) : []
            };
        }''')

        if 'error' in first_product_html:
            print(f"오류: {first_product_html['error']}")
        else:
            print("="*80)
            print("링크 (<a>) 클래스:")
            print("="*80)
            for cls in first_product_html['linkClasses']:
                print(f"  - {cls}")

            print("\n" + "="*80)
            print("링크 자식 요소:")
            print("="*80)
            if first_product_html['linkChildren']:
                for i, child in enumerate(first_product_html['linkChildren'], 1):
                    print(f"\n[{i}] {child['tagName']}")
                    print(f"  클래스: {', '.join(child['classList'])}")
                    print(f"  내용: {child['textContent'][:80]}...")
            else:
                print("  (비어있음 - lazy loading 또는 다른 구조)")

            print("\n" + "="*80)
            print(f"aria-labelledby ID: {first_product_html['labelId']}")
            print("="*80)

            print("\n" + "="*80)
            print("라벨 요소 자식 구조:")
            print("="*80)
            if first_product_html['labelChildren']:
                for i, child in enumerate(first_product_html['labelChildren'], 1):
                    print(f"\n[{i}] {child['tagName']}")
                    print(f"  클래스: {', '.join(child['classList'])}")
                    print(f"  내용: {child['textContent'][:80]}...")
            else:
                print("  (라벨 요소 없음)")

            print("\n" + "="*80)
            print("라벨 요소 HTML (처음 1000자):")
            print("="*80)
            print(first_product_html['labelHTML'][:1000])

        print("\n브라우저를 30초 후에 닫습니다...")
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_dom())
