"""
GUI 개선 사항 테스트 스크립트
GUI 창이 정상적으로 열리고 모든 위젯이 표시되는지 확인
"""
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

def test_gui_launch():
    """GUI 실행 테스트 (창 열기만)"""
    print("\n" + "="*60)
    print("GUI 개선 사항 테스트")
    print("="*60)
    print("\n다음 항목을 확인하세요:\n")

    print("1. [진행률 표시] 상태 영역에 '수집: 0개' 표시됨")
    print("2. [통계 패널] 오른쪽에 '실시간 통계' 패널 (수집/중복/속도/최근)")
    print("3. [재개 정보] '이어서 수집' 체크박스 아래 재개 정보 표시")
    print("4. [버튼들] 로그 헤더에 5개 버튼 (로그 복사, 테마, 간결, 최근 기록)")
    print("5. [테마 토글] '라이트 모드' 버튼 클릭 시 테마 변경")
    print("6. [로그 레벨] '간결 모드' 버튼으로 로그 레벨 변경")
    print("7. [최근 기록] '최근 기록' 버튼 클릭 시 팝업 창")
    print("8. [무한 모드] '전체 수집' 선택 후 시작하면 확인창")
    print("\n" + "="*60)
    print("GUI 창을 열어서 위 항목들을 확인하세요.")
    print("확인 후 창을 닫으면 테스트 완료입니다.")
    print("="*60 + "\n")

    try:
        from product_collector_gui import ProductCollectorGUI

        print("[시작] GUI 실행 중...\n")
        app = ProductCollectorGUI()

        # 초기 상태 확인
        print("초기 상태:")
        print(f"  - 창 크기: {app.window.winfo_width()}x{app.window.winfo_height()} (목표: 900x800)")
        print(f"  - 진행률 라벨: {'존재' if hasattr(app, 'progress_label') else '없음'}")
        print(f"  - 통계 라벨: {'존재' if hasattr(app, 'stats_collected_label') else '없음'}")
        print(f"  - 재개 정보 라벨: {'존재' if hasattr(app, 'resume_info_label') else '없음'}")
        print(f"  - 테마 버튼: {'존재' if hasattr(app, 'theme_button') else '없음'}")
        print(f"  - 로그 레벨 버튼: {'존재' if hasattr(app, 'log_level_button') else '없음'}")
        print(f"  - 최근 기록 버튼: {'존재' if hasattr(app, 'history_button') else '없음'}")
        print(f"  - 상품 미리보기: {'존재' if hasattr(app, 'stats_preview_label') else '없음'}")
        print()

        # GUI 실행
        app.run()

        print("\n[완료] GUI 테스트 완료!")
        print("="*60)
        return True

    except Exception as e:
        print(f"\n[오류] GUI 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gui_launch()
    sys.exit(0 if success else 1)
