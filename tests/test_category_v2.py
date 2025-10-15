"""카테고리 수집 V2 테스트 - 서브카테고리 포함"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.category_collector_v2 import NaverPlusStoreCategoryCollectorV2


async def test_category_collection_v2():
    """카테고리 수집 V2 테스트"""
    print("=" * 60)
    print("네이버 플러스 스토어 카테고리 수집 V2 테스트")
    print("서브카테고리까지 완전 수집")
    print("=" * 60)

    collector = NaverPlusStoreCategoryCollectorV2()
    await collector.collect_categories()

    print("\n테스트 완료!")


if __name__ == "__main__":
    asyncio.run(test_category_collection_v2())