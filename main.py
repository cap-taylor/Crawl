#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Naver Shopping Crawler - Main Entry Point"""

import sys
import os
import traceback

# 인코딩 설정
if sys.platform == 'win32':
    import locale
    locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def main_with_error_handling():
    """GUI 실행 with 오류 처리"""
    try:
        # 버전 읽기
        try:
            with open('VERSION', 'r') as f:
                version = f.read().strip()
        except:
            version = "1.0.0"

        print("=" * 50)
        print(f"Naver Shopping Crawler v{version}")
        print("=" * 50)
        print("GUI Starting...")
        print()

        from src.gui.main_window import main
        main()

    except ImportError as e:
        print("\n[오류] 필요한 모듈을 찾을 수 없습니다:")
        print(f"  → {str(e)}")
        print("\n해결 방법:")
        print("  1. tkinter 설치: sudo apt install python3-tk")
        print("  2. 한글 폰트 설치: bash scripts/install_korean_fonts.sh")
        traceback.print_exc()

    except Exception as e:
        print("\n[오류] GUI 실행 중 예상치 못한 오류가 발생했습니다:")
        print(f"  → {str(e)}")
        print("\n상세 오류 내용:")
        traceback.print_exc()

    finally:
        print("\n[디버깅] GUI 종료됨")

if __name__ == "__main__":
    main_with_error_handling()