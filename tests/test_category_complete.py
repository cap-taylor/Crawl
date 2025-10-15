"""완전한 카테고리 구조 수집 테스트"""
import asyncio
import sys
import os

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.category_collector_complete import CompleteCategoryCollector


async def test_complete_collection():
    """전체 카테고리 구조 완벽 수집 테스트"""
    print("=" * 70)
    print("🎯 네이버 쇼핑 전체 카테고리 구조 완벽 수집 테스트")
    print("=" * 70)
    print("\n이 테스트는 다음을 수행합니다:")
    print("1. 네이버 메인 → 쇼핑 이동 (캡차 회피)")
    print("2. 카테고리 버튼 클릭")
    print("3. 대분류 → 중분류 → 소분류 → 세부분류까지 재귀적 수집")
    print("4. 평면 리스트와 계층 구조로 저장\n")

    try:
        collector = CompleteCategoryCollector(headless=False)

        print("🚀 수집 시작...")
        print("-" * 70)

        categories = await collector.collect_all_categories()

        # 결과 분석
        print("\n" + "=" * 70)
        print("📊 수집 결과 분석")
        print("=" * 70)

        if categories:
            # 통계 계산
            total_main = len(categories)
            total_all = 0
            max_depth = 0

            def analyze_depth(cats, depth=0):
                nonlocal max_depth, total_all
                max_depth = max(max_depth, depth)
                for cat in cats:
                    total_all += 1
                    if isinstance(cat, dict) and 'sub_categories' in cat:
                        analyze_depth(cat['sub_categories'], depth + 1)

            for main_cat, info in categories.items():
                analyze_depth(info.get('sub_categories', []), 1)

            print(f"\n📈 통계:")
            print(f"  • 대분류: {total_main}개")
            print(f"  • 전체 카테고리: {total_all + total_main}개")
            print(f"  • 최대 깊이: {max_depth} 레벨")

            # 샘플 출력
            print(f"\n📋 수집된 카테고리 샘플 (상위 3개):")
            print("-" * 50)

            for i, (main_cat, info) in enumerate(list(categories.items())[:3], 1):
                print(f"\n{i}. {main_cat} (ID: {info.get('id', 'N/A')})")

                # 중분류 출력
                sub_cats = info.get('sub_categories', [])
                for j, sub in enumerate(sub_cats[:3], 1):
                    if isinstance(sub, dict):
                        print(f"   └─ {sub.get('name', 'Unknown')}")

                        # 소분류 출력
                        sub_sub_cats = sub.get('sub_categories', [])
                        for k, sub_sub in enumerate(sub_sub_cats[:2], 1):
                            if isinstance(sub_sub, dict):
                                print(f"      └─ {sub_sub.get('name', 'Unknown')}")

                if len(sub_cats) > 3:
                    print(f"   ... 외 {len(sub_cats) - 3}개")

            print("\n" + "=" * 70)
            print("✅ 전체 카테고리 구조 수집 성공!")
            print("📁 저장된 파일:")
            print("  • categories_complete_[타임스탬프].json - 계층 구조")
            print("  • categories_flat_[타임스탬프].json - 평면 리스트")
            print("  • category_names_[타임스탬프].json - 이름 목록")
            print("=" * 70)

        else:
            print("\n❌ 카테고리 수집 실패")

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n⚠️  주의사항:")
    print("• Firefox가 설치되어 있어야 합니다")
    print("• 브라우저 창이 표시됩니다 (캡차 회피)")
    print("• 전체 수집에 5-10분 소요될 수 있습니다")
    print("• data/ 폴더에 결과가 저장됩니다\n")

    input("Enter를 눌러 전체 카테고리 수집을 시작하세요...")

    asyncio.run(test_complete_collection())