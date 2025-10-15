"""
단일 상품 URL로 직접 접속하여 정보 수집 테스트
셀렉터 리팩토링 검증용
"""
import asyncio
import json
import sys
from datetime import datetime
from playwright.async_api import async_playwright

sys.path.append('/home/dino/MyProjects/Crawl')
from src.core.product_crawler import WomensClothingManualCaptcha


async def test_single_product(product_url: str):
    """단일 상품 페이지에서 정보 수집 테스트"""

    print("\n" + "="*70)
    print("단일 상품 정보 수집 테스트")
    print("="*70)
    print(f"\n[상품 URL] {product_url}\n")

    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=500
        )

        context = await browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )

        page = await context.new_page()

        # 상품 페이지로 직접 이동
        print("[접속] 상품 페이지로 이동 중...")
        await page.goto(product_url)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(2)

        # 40% 위치로 스크롤 (검색태그 위치)
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.4)')
        await asyncio.sleep(2)

        print("[수집] 상품 정보 수집 중...\n")

        # 크롤러 인스턴스 생성
        crawler = WomensClothingManualCaptcha(debug_selectors=True)

        # 상세 정보 수집
        detail_info = await crawler._collect_detail_page_info(page)

        # 결과 출력
        print("\n" + "="*70)
        print("수집된 정보")
        print("="*70)

        print(f"\n--- 기본 정보 ---")
        print(f"상품명: {detail_info.get('detail_product_name', 'N/A')[:60]}")
        print(f"브랜드: {detail_info.get('brand_name', 'N/A')}")
        print(f"가격: {detail_info.get('detail_price', 'N/A')}원")
        print(f"할인율: {detail_info.get('discount_rate', 'N/A')}%")
        print(f"리뷰 수: {detail_info.get('detail_review_count', 'N/A')}개")
        print(f"평점: {detail_info.get('rating', 'N/A')}")
        print(f"품절: {detail_info.get('is_sold_out', False)}")

        tags = detail_info.get('search_tags', [])
        print(f"\n--- 검색 태그 ({len(tags)}개) ---")
        if tags:
            for idx, tag in enumerate(tags, 1):
                print(f"  {idx}. #{tag}")
        else:
            print("  (없음)")

        print(f"\n--- URL 정보 ---")
        print(f"URL: {detail_info.get('detail_page_url', 'N/A')[:70]}...")
        print(f"썸네일: {detail_info.get('thumbnail_url', 'N/A')[:70]}...")

        # JSON 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/test_single_product_{timestamp}.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(detail_info, f, ensure_ascii=False, indent=2)

        print(f"\n[저장] {filename}")

        # 셀렉터 통계
        print()
        crawler.helper.print_stats()

        # DB 스키마 체크
        print("\n" + "="*70)
        print("DB 스키마 필드 수집 여부")
        print("="*70)

        fields = [
            ('product_name', detail_info.get('detail_product_name')),
            ('brand_name', detail_info.get('brand_name')),
            ('price', detail_info.get('detail_price')),
            ('discount_rate', detail_info.get('discount_rate')),
            ('review_count', detail_info.get('detail_review_count')),
            ('rating', detail_info.get('rating')),
            ('search_tags', detail_info.get('search_tags')),
            ('product_url', detail_info.get('detail_page_url')),
            ('thumbnail_url', detail_info.get('thumbnail_url')),
            ('is_sold_out', detail_info.get('is_sold_out')),
        ]

        collected = sum(1 for _, v in fields if v is not None and v != "" and v != [])
        for field_name, value in fields:
            status = "✓" if value is not None and value != "" and value != [] else "✗"
            value_str = str(value)[:50] if value else "None"
            print(f"{status} {field_name:20s}: {value_str}")

        print("="*70)
        print(f"\n수집 성공: {collected}/{len(fields)} 필드\n")

        print("[완료] 10초 후 브라우저를 닫습니다...")
        await asyncio.sleep(10)

        await browser.close()


if __name__ == "__main__":
    # 테스트할 상품 URL (25번째 상품 URL로 변경)
    product_url = input("\n상품 URL을 입력하세요: ").strip()

    if not product_url:
        print("URL이 입력되지 않았습니다.")
        sys.exit(1)

    asyncio.run(test_single_product(product_url))
