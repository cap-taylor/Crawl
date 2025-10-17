#!/usr/bin/env python3
"""
남성의류 에러 페이지 처리 테스트
- 서비스 접속 불가 페이지 빠른 감지
- 타임아웃 최적화
"""

import sys
import asyncio
sys.path.append('/home/dino/MyProjects/Crawl')

from src.core.product_crawler import WomensClothingManualCaptcha

async def main():
    print("\n" + "="*60)
    print("남성의류 에러 페이지 처리 테스트")
    print("- 서비스 접속 불가 페이지 빠르게 건너뛰기")
    print("- 타임아웃 5초로 감소")
    print("="*60)

    # 남성의류 카테고리로 20개 수집 테스트
    crawler = WomensClothingManualCaptcha(
        product_count=20,  # 20개만 테스트
        category_name="남성의류",
        category_id="10000108",
        enable_screenshot=False,
        debug_selectors=False
    )

    print(f"\n카테고리: {crawler.category_name}")
    print(f"수집 개수: 20개")
    print(f"중복 체크: 활성화\n")

    # 크롤링 실행
    data = await crawler.crawl_with_manual_captcha()

    if crawler.products_data:
        print(f"\n✅ 성공적으로 {len(crawler.products_data)}개 수집 완료!")

        # 에러 감지 확인
        print("\n[수집 결과 요약]")
        for idx, product in enumerate(crawler.products_data[:5], 1):
            detail = product.get('detail_page_info', {})
            product_name = detail.get('detail_product_name', 'N/A')
            print(f"{idx}. {product_name[:50]}")

        # DB 저장
        print("\n[DB 저장]")
        crawler.save_to_db(skip_duplicates=True)

        print("\n✅ 테스트 성공!")
        print("에러 페이지가 빠르게 감지되고 건너뛰어집니다.")
    else:
        print("\n❌ 데이터 수집 실패")

if __name__ == "__main__":
    asyncio.run(main())