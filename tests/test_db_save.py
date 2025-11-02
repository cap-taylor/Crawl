"""DB 저장 테스트 (3개 수집)"""
import asyncio
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

from src.core.product_crawler_v2 import ProgressiveCrawler

async def test():
    print('=== DB 저장 테스트 (3개 수집) ===')
    print('랜덤 대기 시간 적용')
    print('목표: DB에 정상 저장 확인\n')

    crawler = ProgressiveCrawler(
        headless=False,
        product_count=3,
        category_name='여성의류',
        category_id='10000107'
    )

    try:
        await crawler.crawl()

        if crawler.products_data:
            print(f'\n{"="*60}')
            print(f'수집 완료: {len(crawler.products_data)}개')
            print(f'{"="*60}')

            # DB 저장
            print('\nDB 저장 중...')
            result = crawler.save_to_db(skip_duplicates=True)

            if result:
                print('✅ DB 저장 성공!')
            else:
                print('❌ DB 저장 실패')
        else:
            print('❌ 수집 실패')

    except Exception as e:
        print(f'\n❌ 에러: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
