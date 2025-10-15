"""트리 구조 GUI 실행 스크립트"""
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.gui.category_tree_window import main

if __name__ == "__main__":
    print("=" * 50)
    print("네이버 플러스 스토어 크롤러 (트리 GUI)")
    print("=" * 50)
    print("GUI를 시작합니다...")
    print("- F11: 전체화면 토글")
    print("- ESC: 전체화면 종료")
    print("- 카테고리 새로고침: 실제 네이버에서 카테고리 수집")
    print("=" * 50)
    main()