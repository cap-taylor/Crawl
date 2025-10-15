"""카테고리 수집기 테스트"""
import asyncio
import sys
import os

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.category_collector import CategoryCollector


async def test_category_collection():
    """카테고리 수집 테스트"""
    print("=" * 60)
    print("네이버 쇼핑 카테고리 수집 테스트")
    print("=" * 60)

    try:
        # 카테고리 수집기 생성 (브라우저 표시)
        collector = CategoryCollector(headless=False)

        print("\n[1] Firefox 브라우저로 네이버 메인 접속...")
        print("[2] 쇼핑 클릭으로 이동...")
        print("[3] 카테고리 메뉴 열기...")
        print("[4] 메인 카테고리 호버하여 서브카테고리 수집...\n")

        # 카테고리 수집 실행
        categories = await collector.collect_categories()

        # 결과 출력
        print("\n" + "=" * 60)
        print("📊 수집 결과")
        print("=" * 60)

        if categories:
            total_main = len(categories)
            total_sub = sum(info['count'] for info in categories.values())

            print(f"\n✅ 메인 카테고리: {total_main}개")
            print(f"✅ 서브 카테고리: {total_sub}개")
            print(f"✅ 전체 카테고리: {total_main + total_sub}개\n")

            # 상위 5개 카테고리 상세 표시
            print("📋 수집된 카테고리 (상위 5개):")
            print("-" * 40)

            for i, (main_cat, info) in enumerate(list(categories.items())[:5], 1):
                cat_id = info.get('id', 'N/A')
                sub_count = info['count']
                print(f"\n{i}. {main_cat} (ID: {cat_id}, 서브: {sub_count}개)")

                # 서브카테고리 상위 5개 표시
                for sub in info['sub_categories'][:5]:
                    print(f"   - {sub}")

                if len(info['sub_categories']) > 5:
                    print(f"   ... 외 {len(info['sub_categories']) - 5}개")

            print("\n" + "=" * 60)
            print("✅ 카테고리 수집 테스트 성공!")
            print("=" * 60)

        else:
            print("\n❌ 카테고리 수집 실패 - 데이터가 없습니다")

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n⚠️  주의사항:")
    print("- Firefox가 설치되어 있어야 합니다")
    print("- 브라우저 창이 표시됩니다 (캡차 회피)")
    print("- 네트워크 연결이 필요합니다\n")

    input("Enter를 눌러 테스트를 시작하세요...")

    asyncio.run(test_category_collection())