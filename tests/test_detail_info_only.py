"""
상세 정보 수집만 테스트
수동으로 상품 페이지를 열어놓고 실행
"""
import asyncio
import json
import sys
from datetime import datetime

sys.path.append('/home/dino/MyProjects/Crawl')
from src.core.product_crawler import WomensClothingManualCaptcha


async def main():
    print("\n" + "="*70)
    print("상세 정보 수집 테스트 (리팩토링 검증)")
    print("="*70)
    print("\n[사용 방법]")
    print("1. Firefox 브라우저를 수동으로 실행")
    print("2. 네이버 메인 → 쇼핑 클릭 → 여성의류 → 25번째 상품 클릭")
    print("3. 상품 상세 페이지가 열리면 이 스크립트 실행")
    print("4. 브라우저 창에서 아무것도 하지 말고 대기")
    print()
    input("준비되었으면 Enter를 누르세요...")

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        # CDP를 사용하여 기존 Firefox 연결 (포트 9222)
        # 또는 새 브라우저 실행 후 URL 입력 대기
        print("\n[시작] 새 브라우저 실행...")
        print("[안내] 상품 상세 페이지로 이동해주세요 (클릭으로만!)")
        print()

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

        # 사용자가 수동으로 이동할 시간 제공
        print("[대기] 수동으로 상품 페이지로 이동 중...")
        print("1. 네이버 메인 접속")
        print("2. 쇼핑 클릭")
        print("3. 카테고리 → 여성의류 클릭")
        print("4. 25번째 상품 클릭")
        print()
        await page.goto('https://www.naver.com')
        await asyncio.sleep(3)

        input("\n상품 상세 페이지가 열렸으면 Enter를 누르세요...")

        # 현재 페이지에서 정보 수집
        print("\n[시작] 상품 정보 수집 중...")

        crawler = WomensClothingManualCaptcha(
            debug_selectors=True  # 디버그 모드
        )

        # 상세 정보 수집
        detail_info = await crawler._collect_detail_page_info(page)

        print("\n" + "="*70)
        print("수집된 정보")
        print("="*70)

        print(f"\n[상품명] {detail_info.get('detail_product_name', 'N/A')}")
        print(f"[브랜드] {detail_info.get('brand_name', 'N/A')}")
        print(f"[가격] {detail_info.get('detail_price', 'N/A')}원")
        print(f"[할인율] {detail_info.get('discount_rate', 'N/A')}%")
        print(f"[리뷰 수] {detail_info.get('detail_review_count', 'N/A')}개")
        print(f"[평점] {detail_info.get('rating', 'N/A')}")
        print(f"[품절] {detail_info.get('is_sold_out', False)}")

        tags = detail_info.get('search_tags', [])
        print(f"\n[검색 태그] ({len(tags)}개)")
        if tags:
            for idx, tag in enumerate(tags, 1):
                print(f"  {idx}. #{tag}")
        else:
            print("  (없음)")

        print(f"\n[URL] {detail_info.get('detail_page_url', 'N/A')}")
        print(f"[썸네일] {detail_info.get('thumbnail_url', 'N/A')[:80]}...")

        # JSON 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/test_detail_info_{timestamp}.json'

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

        for field_name, value in fields:
            status = "✓" if value is not None and value != "" and value != [] else "✗"
            value_str = str(value)[:50] if value else "None"
            print(f"{status} {field_name:20s}: {value_str}")

        print("="*70)

        print("\n[완료] 30초 후 브라우저를 닫습니다...")
        await asyncio.sleep(30)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
