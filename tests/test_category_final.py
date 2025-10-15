"""최종 카테고리 수집 테스트"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.category_collector_final import NaverCategoryCollectorFinal


async def test_final_collection():
    """최종 카테고리 수집 테스트"""
    print("=" * 60)
    print("네이버 플러스 스토어 카테고리 수집 - 최종 테스트")
    print("CRAWLING_LESSONS_LEARNED.md 문서 기반")
    print("=" * 60)

    collector = NaverCategoryCollectorFinal()
    await collector.collect_categories()

    print("\n테스트 완료!")

    # 수집된 데이터 확인
    import json
    project_root = Path(__file__).parent.parent
    data_file = project_root / 'data' / 'naver_plus_store_categories.json'
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"\n✅ GUI용 데이터 파일 생성 확인")
            print(f"  • 메인 카테고리: {data.get('메인카테고리수', 0)}개")
            print(f"  • 서브 카테고리: {data.get('전체서브카테고리수', 0)}개")


if __name__ == "__main__":
    asyncio.run(test_final_collection())