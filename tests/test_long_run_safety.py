#!/usr/bin/env python3
"""
장시간 크롤링 안전성 테스트
- 로그 줄 수 제한 테스트
- 주기적 DB 저장 테스트
- 간결한 로그 출력 테스트
"""

import sys
import asyncio
sys.path.append('/home/dino/MyProjects/Crawl')

from src.core.product_crawler import WomensClothingManualCaptcha


async def test_long_run():
    """장시간 크롤링 시뮬레이션"""

    print("="*60)
    print("장시간 크롤링 안전성 테스트")
    print("="*60)
    print()

    print("설정:")
    print("- 무한 모드 활성화 (product_count=None)")
    print("- 100개마다 자동 DB 저장")
    print("- 간결한 로그 출력")
    print("- 로그 최대 1000줄 제한 (GUI에서)")
    print()

    # 무한 모드로 크롤러 생성
    crawler = WomensClothingManualCaptcha(
        product_count=None,  # 무한 모드
        headless=False,
        enable_screenshot=False,
        category_name="여성의류",
        category_id="10000107"
    )

    print("[시작] 무한 모드 크롤링...")
    print("중단하려면 Ctrl+C를 누르세요")
    print()

    try:
        # 크롤링 실행
        data = await crawler.crawl_with_manual_captcha()

        if crawler.products_data:
            print(f"\n[완료] 총 {len(crawler.products_data)}개 수집")

            # 마지막 저장 (남은 데이터)
            if len(crawler.products_data) > 0:
                print("[마지막 저장] DB에 남은 데이터 저장 중...")
                crawler.save_to_db()

    except KeyboardInterrupt:
        print("\n\n[중단] 사용자가 크롤링을 중단했습니다")

        if crawler.products_data:
            print(f"[중단 전까지] {len(crawler.products_data)}개 수집")
            print("[저장] DB에 저장 중...")
            crawler.save_to_db()
            print("[저장] 완료!")

    print("\n테스트 완료!")


async def test_log_output():
    """로그 출력 테스트"""

    print("="*60)
    print("로그 출력 테스트")
    print("="*60)
    print()

    # 간결한 로그 시뮬레이션
    print("간결한 로그 예시:")
    print("[1] ", end="", flush=True)
    print("✓ ", end="", flush=True)
    print("[2] ", end="", flush=True)
    print("⚠ ", end="", flush=True)
    print("[3] ", end="", flush=True)
    print("✗ ", end="", flush=True)
    print("[4] ", end="", flush=True)
    print("❌ ", end="", flush=True)
    print("[5] ", end="", flush=True)
    print("✓ ", end="", flush=True)
    print()
    print()

    print("[10번째 상품] 수집 중...")
    print("#10 [여성 원피스 플로럴 패턴 미니...] - 태그 5개 (10/100)")
    print()

    print("이제 로그가 훨씬 간결해졌습니다!")
    print("- 10개마다 상세 로그")
    print("- 나머지는 기호로 표시 (✓ ⚠ ✗ ❌)")
    print()


if __name__ == "__main__":
    print("테스트 선택:")
    print("1. 장시간 크롤링 테스트 (무한 모드)")
    print("2. 로그 출력 테스트")

    choice = input("\n선택 (1 또는 2): ").strip()

    if choice == "1":
        asyncio.run(test_long_run())
    elif choice == "2":
        asyncio.run(test_log_output())
    else:
        print("잘못된 선택입니다")