"""동적 대기시간 조정 테스트"""
import asyncio
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

from src.core.product_crawler_v2 import ProgressiveCrawler

async def test():
    print('=' * 60)
    print('동적 대기시간 조정 테스트')
    print('=' * 60)
    print('초기 대기시간: 6초')
    print('실패 시 1초씩 증가하여 재시도')
    print('성공 시 해당 시간을 최적 대기시간으로 저장')
    print('=' * 60)

    # 10개 건너뛰고 5개 수집 (11~15번째)
    crawler = ProgressiveCrawler(
        headless=False,
        product_count=5,
        category_name='여성의류',
        category_id='10000107',
        skip_count=10  # 첫 10개 건너뛰기
    )

    try:
        await crawler.crawl()

        if crawler.products_data:
            print(f'\n{"=" * 60}')
            print(f'✅ 수집 성공: {len(crawler.products_data)}개')
            print(f'최종 최적 대기시간: {crawler.optimal_wait_time}초')
            print(f'{"=" * 60}')

            for i, product in enumerate(crawler.products_data, 1):
                name = product.get("product_name", "이름 없음")
                display_name = name[:50] if name else "이름 없음"
                brand = product.get("brand_name", "N/A")
                price = product.get("price", 0)
                review_count = product.get("review_count", 0)

                print(f'\n{i}. {display_name}')
                print(f'   브랜드: {brand}')
                print(f'   가격: {price:,}원')
                print(f'   리뷰: {review_count}개')

            print(f'\n{"=" * 60}')
            print('💡 동적 대기시간 조정 테스트 완료!')
            print(f'   최적 대기시간: {crawler.optimal_wait_time}초')
            print(f'{"=" * 60}')
        else:
            print('❌ 수집 실패')

    except Exception as e:
        print(f'\n❌ 에러: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())