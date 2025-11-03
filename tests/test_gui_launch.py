#!/usr/bin/env python3
"""
GUI 실행 테스트 - 기존 바로가기 호환 확인
"""

import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.append(str(Path(__file__).parent.parent))

def test_gui_import():
    """GUI 클래스 import 테스트"""
    print("="*60)
    print("GUI Import 테스트")
    print("="*60)

    try:
        from product_collector_gui import ProductCollectorGUI, main
        print("✅ ProductCollectorGUI 클래스 import 성공")
        print("✅ main() 함수 import 성공")
        return True
    except Exception as e:
        print(f"❌ Import 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_crawler_import():
    """SimpleCrawler import 테스트"""
    print("\n" + "="*60)
    print("SimpleCrawler Import 테스트")
    print("="*60)

    try:
        from src.core.simple_crawler import SimpleCrawler
        print("✅ SimpleCrawler 클래스 import 성공")

        # 클래스 인스턴스 생성 테스트
        crawler = SimpleCrawler(product_count=1, headless=True)
        print(f"✅ SimpleCrawler 인스턴스 생성 성공")
        print(f"   - category_name: {crawler.category_name}")
        print(f"   - category_id: {crawler.category_id}")
        print(f"   - product_count: {crawler.product_count}")

        return True
    except Exception as e:
        print(f"❌ Import 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """의존성 패키지 확인"""
    print("\n" + "="*60)
    print("의존성 패키지 확인")
    print("="*60)

    packages = {
        'customtkinter': 'customtkinter',
        'playwright': 'playwright.async_api'
    }

    all_ok = True
    for name, import_path in packages.items():
        try:
            __import__(import_path)
            print(f"✅ {name} 설치됨")
        except ImportError:
            print(f"❌ {name} 미설치")
            all_ok = False

    return all_ok

def main_test():
    """전체 테스트 실행"""
    print("\n" + "="*60)
    print("GUI + SimpleCrawler 통합 테스트")
    print("="*60)
    print()

    results = []

    # 1. 의존성 확인
    results.append(("의존성", test_dependencies()))

    # 2. SimpleCrawler import
    results.append(("SimpleCrawler", test_simple_crawler_import()))

    # 3. GUI import
    results.append(("GUI", test_gui_import()))

    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)

    all_passed = all(result for _, result in results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print("="*60)

    if all_passed:
        print("✅ 모든 테스트 통과!")
        print("\n바로가기 실행 가능합니다:")
        print("   python3 /home/dino/MyProjects/Crawl/product_collector_gui.py")
        print("   또는 Windows 바탕화면 바로가기 사용")
    else:
        print("❌ 일부 테스트 실패")
        print("   문제를 해결한 후 다시 시도하세요")

    print("="*60)

    return all_passed

if __name__ == "__main__":
    success = main_test()
    sys.exit(0 if success else 1)
