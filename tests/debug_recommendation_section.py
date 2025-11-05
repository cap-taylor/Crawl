#!/usr/bin/env python3
"""
FOR YOU 연관 추천 섹션의 정확한 구조 확인
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_recommendation():
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

        # 네이버 메인 → 쇼핑
        print("[1/5] 네이버 메인 페이지 접속...")
        await page.goto('https://www.naver.com')
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(2)

        print("[2/5] 쇼핑 버튼 클릭...")
        shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
        await page.locator(shopping_selector).click(timeout=10000)
        await asyncio.sleep(2)

        # 새 탭 전환
        all_pages = context.pages
        if len(all_pages) > 1:
            page = all_pages[-1]
            await page.wait_for_load_state('networkidle')

        # 조명/인테리어 카테고리
        print("[3/5] '조명/인테리어' 카테고리 진입...")
        category_btn = await page.wait_for_selector('button:has-text("카테고리")', timeout=10000)
        await category_btn.click()
        await asyncio.sleep(1)

        category_id = "10000174"
        category_name = "조명/인테리어"

        try:
            category_elem = await page.wait_for_selector(f'#cat_layer_item_{category_id}', timeout=5000)
        except:
            try:
                category_elem = await page.wait_for_selector(f'[data-id="{category_id}"]', timeout=3000)
            except:
                category_elem = await page.wait_for_selector(f'a[data-name="{category_name}"]', timeout=3000)

        await category_elem.click()
        await asyncio.sleep(3)

        # 캡차 확인
        print("[4/5] 캡차 확인...")
        try:
            page_text = await page.evaluate('document.body.innerText')
            if '영수증' in page_text:
                print("캡차 발견 - 60초 대기")
                await asyncio.sleep(60)
        except:
            pass

        await asyncio.sleep(5)

        print("[5/5] 페이지 구조 분석 중...\n")

        # 상품 리스트 구조 확인
        structure = await page.evaluate('''() => {
            const allLinks = Array.from(document.querySelectorAll('a[class*="ProductCard_link"]'));

            // 각 링크의 부모 구조 분석
            const structures = allLinks.map((link, idx) => {
                // 부모 체인 수집
                let parents = [];
                let current = link.parentElement;
                let depth = 0;

                while (current && depth < 10) {
                    const info = {
                        tag: current.tagName,
                        id: current.id || null,
                        classes: Array.from(current.classList).slice(0, 3),
                        text: current.textContent ? current.textContent.substring(0, 50) : null
                    };
                    parents.push(info);
                    current = current.parentElement;
                    depth++;
                }

                // composite-card-list 체크
                const inComposite = link.closest('#composite-card-list') !== null;

                // FOR YOU 섹션 체크 (여러 방법)
                const hasForYouInParent = (() => {
                    let el = link.parentElement;
                    while (el) {
                        const text = el.textContent || '';
                        if (text.includes('FOR YOU') || text.includes('방금 본 상품')) {
                            return true;
                        }
                        el = el.parentElement;
                    }
                    return false;
                })();

                // fullWidthCompositeCardContainer 체크
                const hasFullWidthContainer = link.closest('.fullWidthCompositeCardContainer_full_width_composite_card_container__zCqj9, [class*="fullWidthCompositeCardContainer"]') !== null;

                return {
                    index: idx,
                    href: link.href ? link.href.substring(0, 80) : null,
                    inComposite: inComposite,
                    hasForYouInParent: hasForYouInParent,
                    hasFullWidthContainer: hasFullWidthContainer,
                    parents: parents
                };
            });

            return {
                total: allLinks.length,
                structures: structures.slice(0, 10)  // 처음 10개만
            };
        }''')

        print("="*80)
        print(f"전체 상품 링크: {structure['total']}개")
        print("="*80)

        for item in structure['structures']:
            print(f"\n[{item['index']}번 상품]")
            print(f"  URL: {item['href']}")
            print(f"  #composite-card-list 내부: {item['inComposite']}")
            print(f"  FOR YOU 부모 있음: {item['hasForYouInParent']}")
            print(f"  fullWidthCompositeCardContainer: {item['hasFullWidthContainer']}")
            print(f"  부모 체인 (처음 3개):")
            for i, parent in enumerate(item['parents'][:3]):
                print(f"    [{i}] {parent['tag']}")
                if parent['id']:
                    print(f"        ID: {parent['id']}")
                if parent['classes']:
                    print(f"        클래스: {', '.join(parent['classes'])}")

        print("\n" + "="*80)
        print("브라우저를 60초 후에 닫습니다...")
        print("="*80)
        await asyncio.sleep(60)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_recommendation())
