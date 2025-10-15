"""
여성의류 1번째 상품 수집 테스트 (실패 시 자동으로 다음 상품)
- specific_index=0 (0-based) 사용
- 카테고리 전체 경로(category_fullname) 포함
- DB 저장 및 확인
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.product_crawler import WomensClothingManualCaptcha
from src.database.db_connector import DatabaseConnector


async def test_1st_product():
    """여성의류 1번째 상품부터 수집 (실패 시 자동으로 다음 상품)"""

    print("=" * 60)
    print("여성의류 1번째 상품 수집 테스트 (카테고리 경로 확인)")
    print("=" * 60)

    # 크롤러 생성 (1번째 상품부터, 실패 시 자동으로 다음 상품)
    crawler = WomensClothingManualCaptcha(
        product_count=None,
        headless=False,
        enable_screenshot=False,
        category_name="여성의류",
        category_id="10000107",
        debug_selectors=True,
        specific_index=0  # 1번째 상품부터 시작 (0-based index)
    )

    db = DatabaseConnector()

    try:
        # DB 연결
        db.connect()
        print("\n[DB] 연결 성공")

        # 크롤링 실행
        print("\n[크롤링] 여성의류 1번째 상품부터 수집 시작...")
        print("(1번째가 실패하면 자동으로 2, 3... 순서로 시도)")
        await crawler.crawl_with_manual_captcha()

        if not crawler.products_data or len(crawler.products_data) == 0:
            print("\n[실패] 상품을 수집하지 못했습니다.")
            return

        print(f"\n[성공] {len(crawler.products_data)}개 상품 수집 완료")

        # 수집된 데이터 출력
        product = crawler.products_data[0]
        detail = product.get('detail_page_info', {})

        print("\n" + "=" * 60)
        print("수집된 상품 정보")
        print("=" * 60)

        # 기본 정보
        print(f"\n[기본 정보]")
        print(f"  - 상품명: {detail.get('detail_product_name', 'N/A')}")
        print(f"  - 브랜드: {detail.get('brand_name', 'N/A')}")
        print(f"  - 가격: {detail.get('detail_price', 'N/A')}원")
        print(f"  - 할인율: {detail.get('discount_rate', 'N/A')}%")
        print(f"  - 리뷰 수: {detail.get('detail_review_count', 'N/A')}")
        print(f"  - 평점: {detail.get('rating', 'N/A')}")
        print(f"  - 품절: {detail.get('is_sold_out', False)}")
        print(f"  - URL: {detail.get('detail_page_url', 'N/A')}")

        # 카테고리 정보 (★ 새로 추가된 부분)
        category_fullname = detail.get('category_fullname', 'N/A')
        print(f"\n[카테고리 정보] ★ 새로운 필드")
        print(f"  - 대분류: 여성의류")
        print(f"  - 전체 경로: {category_fullname}")

        # 검색 태그
        search_tags = detail.get('search_tags', [])
        print(f"\n[검색 태그] ({len(search_tags)}개)")
        if search_tags:
            for i, tag in enumerate(search_tags[:10], 1):
                print(f"  {i}. #{tag}")
            if len(search_tags) > 10:
                print(f"  ... 외 {len(search_tags) - 10}개")
        else:
            print("  (없음)")

        # DB 저장을 위한 데이터 변환
        # db_connector는 다른 형식을 기대하므로 변환 필요
        db_product_data = {
            'product_url': detail.get('detail_page_url', ''),
            'detail_page_info': {
                'category_fullname': detail.get('category_fullname', '여성의류'),
                'search_tags': detail.get('search_tags', [])
            },
            'product_info': {
                'product_name': detail.get('detail_product_name', ''),
                'brand': detail.get('brand_name', None),
                'price': detail.get('detail_price', 0),
                'discount_rate': detail.get('discount_rate', 0),
                'review_count': detail.get('detail_review_count', 0),
                'rating': detail.get('rating', 0),
                'thumbnail_url': detail.get('thumbnail_url', None)
            }
        }

        # DB 저장
        print("\n" + "=" * 60)
        print("DB 저장 중...")
        print("=" * 60)

        result = db.save_product("여성의류", db_product_data, skip_duplicates=False)

        if result == 'saved':
            print("\n[성공] DB 저장 완료!")
        else:
            print(f"\n[경고] DB 저장 결과: {result}")

        # DB에서 확인
        print("\n" + "=" * 60)
        print("DB 저장 확인")
        print("=" * 60)

        product_url = detail.get('detail_page_url', '')
        product_id = db.extract_product_id(product_url)
        cursor = db.conn.cursor()

        cursor.execute(
            """
            SELECT product_id, product_name, category_name, category_fullname,
                   price, brand_name, review_count, rating,
                   ARRAY_LENGTH(search_tags, 1) as tag_count
            FROM products
            WHERE product_id = %s
            """,
            (product_id,)
        )

        row = cursor.fetchone()

        if row:
            print(f"\n[DB 조회 성공]")
            print(f"  - product_id: {row[0]}")
            print(f"  - product_name: {row[1]}")
            print(f"  - category_name: {row[2]}")
            print(f"  - category_fullname: {row[3]} ★ 새 필드!")
            print(f"  - price: {row[4]}")
            print(f"  - brand_name: {row[5]}")
            print(f"  - review_count: {row[6]}")
            print(f"  - rating: {row[7]}")
            print(f"  - tag_count: {row[8]}")
        else:
            print("\n[실패] DB에서 상품을 찾을 수 없습니다.")

        cursor.close()

    except Exception as e:
        print(f"\n[오류] {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_1st_product())
