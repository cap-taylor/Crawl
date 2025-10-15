"""
40번째 상품 수집 테스트
리팩토링된 셀렉터 시스템 검증
"""
import asyncio
import json
import sys
from datetime import datetime

sys.path.append('/home/dino/MyProjects/Crawl')
from src.core.product_crawler import WomensClothingManualCaptcha


async def main():
    print("\n" + "="*70)
    print("리팩토링 검증: 여성의류 40번째 상품 수집 테스트")
    print("="*70)
    print("\n[목표]")
    print("- 여성의류 카테고리 40번째 상품 정확히 수집")
    print("- 구조 기반 셀렉터 동작 확인")
    print("- DB 스키마 필드 모두 수집 검증")
    print("- 검색태그 수집 정확도 확인")
    print()

    # 크롤러 생성 (debug 모드 활성화) - 40번째만 수집
    crawler = WomensClothingManualCaptcha(
        product_count=None,        # 개수는 상관없음
        headless=False,            # 브라우저 보이기
        enable_screenshot=False,
        category_name="여성의류",
        category_id="10000107",
        debug_selectors=True,      # 셀렉터 디버깅 활성화
        specific_index=39          # 40번째 상품 (0-based index)
    )

    # 크롤링 실행
    print("[시작] 크롤링 시작...")
    data = await crawler.crawl_with_manual_captcha()

    if crawler.products_data and len(crawler.products_data) >= 1:
        print("\n" + "="*70)
        print("40번째 상품 상세 정보")
        print("="*70)

        # 40번째 상품 (index 0, 우리가 1개만 수집했으므로)
        product_40 = crawler.products_data[0]
        detail = product_40.get('detail_page_info', {})

        # 출력
        print(f"\n[카테고리] {product_40.get('category', 'N/A')}")
        print(f"[수집 시간] {product_40.get('crawled_at', 'N/A')}")
        print(f"\n--- 기본 정보 ---")
        print(f"상품명: {detail.get('detail_product_name', 'N/A')}")
        print(f"브랜드: {detail.get('brand_name', 'N/A')}")
        print(f"가격: {detail.get('detail_price', 'N/A')}원")
        print(f"할인율: {detail.get('discount_rate', 'N/A')}%")
        print(f"리뷰 수: {detail.get('detail_review_count', 'N/A')}개")
        print(f"평점: {detail.get('rating', 'N/A')}")
        print(f"품절: {detail.get('is_sold_out', False)}")

        print(f"\n--- 검색 태그 ({len(detail.get('search_tags', []))}개) ---")
        tags = detail.get('search_tags', [])
        if tags:
            for idx, tag in enumerate(tags, 1):
                print(f"  {idx}. #{tag}")
        else:
            print("  (없음)")

        print(f"\n--- URL 정보 ---")
        print(f"상품 URL: {detail.get('detail_page_url', 'N/A')}")
        print(f"썸네일: {detail.get('thumbnail_url', 'N/A')[:80]}...")

        # JSON 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/test_product_40th_{timestamp}.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(product_40, f, ensure_ascii=False, indent=2)

        print(f"\n[저장] {filename}")
        print("="*70)

        # 셀렉터 통계 출력
        print("\n")
        crawler.helper.print_stats()

        # DB 스키마 필드 체크
        print("\n" + "="*70)
        print("DB 스키마 필드 수집 여부 체크")
        print("="*70)

        required_fields = [
            ('product_name', detail.get('detail_product_name')),
            ('price', detail.get('detail_price')),
            ('discount_rate', detail.get('discount_rate')),
            ('review_count', detail.get('detail_review_count')),
            ('rating', detail.get('rating')),
            ('search_tags', detail.get('search_tags')),
            ('product_url', detail.get('detail_page_url')),
            ('thumbnail_url', detail.get('thumbnail_url')),
            ('is_sold_out', detail.get('is_sold_out')),
            ('brand_name', detail.get('brand_name')),
        ]

        for field_name, value in required_fields:
            status = "✓" if value is not None and value != "" and value != [] else "✗"
            print(f"{status} {field_name:20s}: {str(value)[:50]}")

        print("="*70)

    else:
        print("\n[실패] 40번째 상품 수집 실패")
        print(f"총 {len(crawler.products_data) if crawler.products_data else 0}개 수집됨")


if __name__ == "__main__":
    asyncio.run(main())
