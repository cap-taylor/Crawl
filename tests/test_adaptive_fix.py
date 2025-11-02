#!/usr/bin/env python3
"""
봇 차단 해결 최종 테스트 - 적응형 대기 시간
- 첫 상품: 8-12초 대기 (페이지 안정화)
- 이후 상품: 5-7초 일반 대기
- 목표: 100% 수집 성공률
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.append(str(Path(__file__).parent.parent))

from src.core.product_crawler_v2 import ProgressiveCrawler

async def test_adaptive_fix():
    print("="*60)
    print("봇 차단 해결 최종 테스트 (v1.2.3)")
    print("="*60)
    print("수정 내용:")
    print("1. Ctrl+클릭으로 새 탭 열기 (문서 검증)")
    print("2. networkidle 먼저 대기 (페이지 완전 로딩)")
    print("3. 첫 상품 8-12초 적응형 대기")
    print("4. 오류 체크 코드 완전 제거")
    print("="*60 + "\n")

    crawler = ProgressiveCrawler(
        headless=False,  # 브라우저 보이기
        product_count=3,  # 3개 테스트
        category_name='여성의류',
        category_id='10000107'
    )

    try:
        print("[시작] 크롤링 시작...\n")
        products = await crawler.crawl()

        # 성공률 계산
        total = 3
        success = len([p for p in products if p and
                      p.get('detail_page_info', {}).get('detail_product_name')
                      and p.get('detail_page_info', {}).get('detail_product_name') != 'N/A'])

        success_rate = (success / total) * 100

        print("\n" + "="*60)
        if success_rate == 100:
            print(f"✅ 완벽! 100% 성공률 달성!")
            print(f"수집된 상품: {success}/{total}개")
        else:
            print(f"⚠️ 부분 성공: {success_rate:.1f}% 성공률")
            print(f"수집된 상품: {success}/{total}개")
        print("="*60)

        # 상품 상세 정보 출력
        for i, product in enumerate(products, 1):
            if product:
                info = product.get('detail_page_info', {})
                name = info.get('detail_product_name', 'N/A')
                price = info.get('detail_price', 0)
                brand = info.get('brand_name', 'N/A')

                print(f"\n[{i}번 상품]")
                print(f"  이름: {name[:50] if name else 'N/A'}...")
                print(f"  브랜드: {brand}")
                print(f"  가격: {price:,}원")

                # 상품명이 None이 아닌지 확인
                if name and name != 'N/A':
                    print("  ✅ 정상 수집됨 (봇 차단 회피 성공)")
                else:
                    print("  ❌ 상품명 없음 (봇 차단 감지)")

        # 최종 결과
        print("\n" + "="*60)
        if success_rate == 100:
            print("🎉 축하합니다! 봇 차단 문제가 완전히 해결되었습니다!")
            print("모든 상품이 성공적으로 수집되었습니다.")
        else:
            print("⚠️ 추가 개선이 필요합니다.")
            print(f"실패한 상품: {total - success}개")
        print("="*60)

        return success_rate

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 0

async def main():
    print("테스트를 시작합니다...")
    success_rate = await test_adaptive_fix()

    # 결과 요약
    print(f"\n최종 성공률: {success_rate:.1f}%")
    if success_rate == 100:
        print("✅ 테스트 통과!")
    else:
        print("❌ 테스트 실패 - 추가 디버깅 필요")

if __name__ == "__main__":
    asyncio.run(main())