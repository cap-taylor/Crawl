#!/usr/bin/env python3
"""
캡차 후 상품 수집 테스트 - 이미지 링크만 찾기 수정 확인
- 캡차 수동 해결 후 정상 수집되는지 확인
- v1.2.4: :has(img) 셀렉터로 실제 상품만 찾기
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.append(str(Path(__file__).parent.parent))

from src.core.product_crawler_v2 import ProgressiveCrawler

async def test_captcha_fix():
    print("="*60)
    print("캡차 후 상품 수집 테스트 (v1.2.4)")
    print("="*60)
    print("수정 내용:")
    print("1. :has(img) 셀렉터로 이미지 있는 링크만 찾기")
    print("2. 캡차 후 DOM 변경에도 정확한 상품 링크 찾기")
    print("3. 새 탭 URL 디버깅 출력 추가")
    print("="*60 + "\n")

    crawler = ProgressiveCrawler(
        headless=False,  # 브라우저 보이기
        product_count=3,  # 3개 테스트
        category_name='여성의류',
        category_id='10000107'
    )

    try:
        print("[시작] 크롤링 시작...")
        print("[주의] 캡차가 나오면 수동으로 해결해주세요!\n")

        products = await crawler.crawl()

        # 성공률 계산
        total = 3
        success = len([p for p in products if p and
                      p.get('detail_page_info', {}).get('detail_product_name')
                      and p.get('detail_page_info', {}).get('detail_product_name') != 'N/A'])

        success_rate = (success / total) * 100

        print("\n" + "="*60)
        if success_rate >= 66:  # 2개 이상 성공하면 OK
            print(f"✅ 성공! {success_rate:.1f}% 성공률")
            print(f"수집된 상품: {success}/{total}개")
        else:
            print(f"⚠️ 실패: {success_rate:.1f}% 성공률")
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

                if name and name != 'N/A':
                    print("  ✅ 정상 수집됨 (캡차 후 수집 성공)")
                else:
                    print("  ❌ 상품명 없음 (봇 차단 또는 링크 오류)")

        # 최종 결과
        print("\n" + "="*60)
        if success_rate >= 66:
            print("🎉 캡차 후 상품 수집 문제 해결!")
            print("이미지 링크만 찾는 방식이 효과적입니다.")
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
    success_rate = await test_captcha_fix()

    # 결과 요약
    print(f"\n최종 성공률: {success_rate:.1f}%")
    if success_rate >= 66:
        print("✅ 테스트 통과! (캡차 후에도 정상 작동)")
    else:
        print("❌ 테스트 실패 - 추가 디버깅 필요")

if __name__ == "__main__":
    asyncio.run(main())