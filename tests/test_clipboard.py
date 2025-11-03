#!/usr/bin/env python3
"""
클립보드 복사 테스트 (한글 인코딩 검증)
"""

import customtkinter as ctk
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


def test_clipboard():
    """클립보드 복사 테스트"""
    print("=" * 70)
    print("클립보드 복사 테스트 (한글 인코딩)")
    print("=" * 70)

    # GUI 생성
    root = ctk.CTk()
    root.withdraw()

    # 테스트 로그 (실제 크롤링 로그와 동일한 형식)
    test_log = """[16:51:01] ============================================================
[16:51:01] 카테고리: 여성의류
[16:51:01] 수집 개수: 5개
[16:51:01] ============================================================
[16:51:05] [1/4] 네이버 메인 페이지 접속...
[16:51:10] [2/4] 쇼핑 버튼 클릭...
[16:51:15] [3/4] '여성의류' 카테고리 진입...

============================================================
⚠️  캡차 확인 - 15초 대기
============================================================
브라우저에서 캡차를 수동으로 해결해주세요
============================================================

[16:52:00] [4/4] 상품 5개 수집 시작...

[16:52:05] [1] 폭스클럽 잠옷 빅사이즈 피치기모 수면 가족잠옷 가을 겨울잠옷... | 가격: 14,900원 - DB 저장 ✓
[16:52:10] [2] 패드 일체형 콤비 심리스 브라와 심리스 노라인 팬티... | 가격: 2,700원 - DB 저장 ✓
[16:52:15] [3] 할머니조끼 김장 촌캉스 꽃무늬 엄마 누빔 겨울 경량 패딩... | 가격: 6,800원 - 중복 스킵
[16:52:20] [4] 여성 원피스 가을 겨울 니트 롱 원피스 데일리 캐주얼... | 가격: 19,900원 - DB 저장 ✓
[16:52:25] [5] 빅사이즈 여성 후드 티셔츠 맨투맨 트레이닝복 세트... | 가격: 13,500원 - DB 저장 ✓

목표 개수 도달! 5개 수집 완료

수집 완료! 총 5개

수집 완료! 총 5개 상품 → DB 저장됨"""

    print("\n[1단계] 클립보드에 복사 중...")
    root.clipboard_clear()
    root.clipboard_append(test_log)
    root.update()
    print("✓ 복사 완료")

    print("\n[2단계] 클립보드에서 읽기...")
    copied = root.clipboard_get()
    print("✓ 읽기 완료")

    print("\n[3단계] 검증...")
    print(f"원본 길이: {len(test_log)} 문자")
    print(f"복사본 길이: {len(copied)} 문자")
    print(f"원본 한글: {len([c for c in test_log if ord(c) > 127])}자")
    print(f"복사본 한글: {len([c for c in copied if ord(c) > 127])}자")

    if test_log == copied:
        print("\n✅ 복사 성공! 원본과 100% 일치")
        print("\n[4단계] 메모장 붙여넣기 테스트")
        print("1. 메모장(notepad.exe)을 엽니다")
        print("2. Ctrl+V로 붙여넣기 합니다")
        print("3. 한글이 깨지지 않고 정상 표시되는지 확인합니다")
        print("\n아래 내용이 그대로 보여야 합니다:")
        print("-" * 70)
        print("폭스클럽 잠옷 빅사이즈 피치기모 수면 가족잠옷 가을 겨울잠옷...")
        print("패드 일체형 콤비 심리스 브라와 심리스 노라인 팬티...")
        print("할머니조끼 김장 촌캉스 꽃무늬 엄마 누빔 겨울 경량 패딩...")
        print("-" * 70)

        # 클립보드에 계속 유지 (메모장 테스트용)
        print("\n클립보드에 내용이 저장되어 있습니다.")
        print("지금 메모장을 열어서 Ctrl+V로 붙여넣기 해보세요!")
        print("\n계속하려면 Enter를 누르세요...")
        input()

        return True
    else:
        print("\n❌ 복사 실패! 내용이 일치하지 않습니다")
        print("\n차이점:")
        for i, (c1, c2) in enumerate(zip(test_log, copied)):
            if c1 != c2:
                print(f"위치 {i}: 원본='{c1}' (U+{ord(c1):04X}), 복사본='{c2}' (U+{ord(c2):04X})")
                break
        return False


if __name__ == "__main__":
    try:
        success = test_clipboard()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
