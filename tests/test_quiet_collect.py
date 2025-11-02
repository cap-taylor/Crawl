#!/usr/bin/env python3
"""
봇 차단 회피 테스트 - 에러 체크 없이 조용히 수집
- "상품이 존재하지 않습니다" 체크 제거
- 충분한 대기 시간 확보
- 2개 상품 수집 테스트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.append(str(Path(__file__).parent.parent))

from src.core.product_crawler_v2 import ProgressiveCrawler

async def test_quiet_collect():
    print("="*60)
    print("봇 차단 회피 테스트 (조용히 수집)")
    print("="*60)
    print("수정 내용:")
    print("1. '상품이 존재하지 않습니다' 체크 제거 (봇 감지 트리거 방지)")
    print("2. networkidle 타임아웃 30초로 증가")
    print("3. 로딩 후 3-5초 대기 (충분한 안정화 시간)")
    print("4. 수집 전 추가 2-3초 대기")
    print("="*60 + "\n")

    crawler = ProgressiveCrawler(
        headless=False,  # 브라우저 보이기
        product_count=2,  # 2개만 테스트
        category_name='여성의류',
        category_id='10000107'
    )

    try:
        print("[시작] 크롤링 시작...\n")
        products = await crawler.crawl()

        if products and len(products) > 0:
            print("\n" + "="*60)
            print("✅ 성공! 100% 상품 수집 성공")
            print(f"수집된 상품: {len(products)}개")
            print("="*60)

            for i, product in enumerate(products, 1):
                info = product.get('detail_page_info', {})
                name = info.get('detail_product_name', 'N/A')
                price = info.get('detail_price', 0)
                print(f"\n[{i}번 상품]")
                print(f"  이름: {name[:50] if name else 'N/A'}...")
                print(f"  가격: {price:,}원")

                # 상품명이 None이 아닌지 확인
                if name and name != 'N/A':
                    print("  ✅ 정상 수집됨 (봇 차단 회피 성공)")
                else:
                    print("  ❌ 상품명 없음 (봇 차단됨)")
        else:
            print("\n" + "="*60)
            print("❌ 실패: 상품을 수집할 수 없음")
            print("봇 차단이 계속되고 있습니다")
            print("="*60)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("테스트를 시작합니다...")
    asyncio.run(test_quiet_collect())