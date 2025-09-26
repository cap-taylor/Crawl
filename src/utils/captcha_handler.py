#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 캡차 수동 해결 핸들러
캡차 감지 시 사용자에게 알리고 해결될 때까지 대기
"""

import asyncio
import time
from datetime import datetime

class CaptchaHandler:
    def __init__(self, gui=None):
        """캡차 핸들러 초기화"""
        self.gui = gui
        self.max_wait_time = 300  # 최대 5분 대기

    async def check_captcha(self, page):
        """캡차 존재 여부 확인"""
        try:
            # 캡차 감지 요소들
            captcha_indicators = [
                'text=security verification',
                'text=Please complete the security',
                'text=This receipt',
                'input[placeholder*="Answer"]',
                'text=How many',
                'text=보안 확인',
                'text=보안문자',
                'button:has-text("확인")'
            ]

            # 각 지표 확인
            for selector in captcha_indicators:
                element = await page.query_selector(selector)
                if element:
                    return True

            # URL 체크
            current_url = page.url
            if "captcha" in current_url.lower():
                return True

            return False

        except Exception as e:
            print(f"[캡차] 확인 중 오류: {e}")
            return False

    async def wait_for_manual_solve(self, page):
        """수동으로 캡차를 해결할 때까지 대기"""
        try:
            print("\n" + "="*50)
            print("🔐 캡차가 감지되었습니다!")
            print("👤 브라우저에서 직접 캡차를 해결해주세요.")
            print(f"⏰ 최대 {self.max_wait_time}초 동안 대기합니다.")
            print("="*50 + "\n")

            if self.gui:
                self.gui.add_log("캡차 감지! 수동으로 해결해주세요.", "WARNING")

            start_time = time.time()
            check_interval = 2  # 2초마다 확인

            while True:
                # 대기 시간 체크
                elapsed = time.time() - start_time
                if elapsed > self.max_wait_time:
                    print(f"⏱️ 대기 시간 초과 ({self.max_wait_time}초)")
                    return False

                # 캡차가 해결되었는지 확인
                if not await self.check_captcha(page):
                    # 추가로 카테고리 페이지로 이동했는지 확인
                    current_url = page.url
                    if "/category/" in current_url or "/search/" in current_url:
                        print("✅ 캡차가 해결되었습니다!")
                        if self.gui:
                            self.gui.add_log("캡차 해결 완료!", "SUCCESS")
                        return True

                # 진행 상황 표시
                remaining = int(self.max_wait_time - elapsed)
                print(f"⏳ 대기 중... (남은 시간: {remaining}초)", end='\r')

                await asyncio.sleep(check_interval)

        except Exception as e:
            print(f"[캡차] 대기 중 오류: {e}")
            return False

    async def handle_captcha_if_exists(self, page):
        """캡차가 있으면 처리, 없으면 통과"""
        try:
            # 캡차 확인
            if await self.check_captcha(page):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 캡차 감지됨")

                # 스크린샷 저장 (디버깅용)
                screenshot_path = f'/tmp/captcha_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                await page.screenshot(path=screenshot_path)
                print(f"📸 캡차 스크린샷 저장: {screenshot_path}")

                # 수동 해결 대기
                solved = await self.wait_for_manual_solve(page)

                if solved:
                    # 해결 후 잠시 대기 (페이지 로드)
                    await asyncio.sleep(3)
                    return True
                else:
                    return False

            # 캡차 없음
            return True

        except Exception as e:
            print(f"[캡차] 처리 중 오류: {e}")
            return False

    def set_max_wait_time(self, seconds):
        """최대 대기 시간 설정"""
        self.max_wait_time = seconds
        print(f"[캡차] 최대 대기 시간: {seconds}초로 설정")