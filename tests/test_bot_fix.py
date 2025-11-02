#!/usr/bin/env python3
"""
봇 차단 수정 테스트
- networkidle을 먼저 기다려서 페이지 완전 로딩 보장
- 2개 상품 수집 테스트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.append(str(Path(__file__).parent.parent))

from src.core.product_crawler_v2 import ProgressiveCrawler

async def test_bot_fix():
    print("="*60)
    print("봇 차단 해결 테스트")
    print("="*60)
    print("수정 내용:")
    print("1. networkidle을 가장 먼저 대기 (페이지 완전 로딩)")
    print("2. 로딩 후 1-2초만 대기 (10초 대기 제거)")
    print("3. 동적 대기시간 로직 제거")
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
            print("✅ 성공! 봇 차단 우회 성공")
            print(f"수집된 상품: {len(products)}개")
            print("="*60)

            for i, product in enumerate(products, 1):
                info = product.get('detail_page_info', {})
                name = info.get('detail_product_name', 'N/A')
                price = info.get('detail_price', 0)
                print(f"\n[{i}번 상품]")
                print(f"  이름: {name[:50] if name else 'N/A'}")
                print(f"  가격: {price:,}원")

                # 상품명이 None이 아닌지 확인 (봇 차단 검증)
                if name and name != 'N/A':
                    print("  ✅ 정상 수집됨")
                else:
                    print("  ❌ 봇 차단 (상품명 없음)")
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
    asyncio.run(test_bot_fix())