"""21번째 상품부터 수집 테스트"""
import asyncio
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

from src.core.product_crawler_v2 import ProgressiveCrawler

async def test():
    print('=== 17번째 상품부터 수집 테스트 ===')
    print('첫 16개 건너뛰기')
    print('목표: 17~21번째 상품 5개 수집\n')

    crawler = ProgressiveCrawler(
        headless=False,
        product_count=5,
        category_name='여성의류',
        category_id='10000107',
        skip_count=16  # 첫 16개 건너뛰기
    )

    try:
        await crawler.crawl()

        if crawler.products_data:
            print(f'\n{"="*60}')
            print(f'수집 완료: {len(crawler.products_data)}개')
            print(f'{"="*60}')

            for i, product in enumerate(crawler.products_data, 1):
                print(f'\n{i}. {product["product_name"][:50]}')
                print(f'   브랜드: {product["brand_name"]}')
                print(f'   가격: {product["price"]:,}원')
                print(f'   리뷰: {product["review_count"]}개')
                print(f'   검색태그: {len(product["search_tags"])}개')

            print(f'\n{"="*60}')
            print('✅ 21번째부터 수집 성공!')
            print(f'{"="*60}')
        else:
            print('❌ 수집 실패')

    except Exception as e:
        print(f'\n❌ 에러: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
