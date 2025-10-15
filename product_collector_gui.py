"""
네이버 쇼핑 상품 수집 GUI
간단한 인터페이스로 여성의류 상품 정보를 수집합니다.
"""
import sys
import asyncio
import threading
import queue
import re
from datetime import datetime
import customtkinter as ctk

# 프로젝트 경로 추가
sys.path.append('/home/dino/MyProjects/Crawl')
from tests.test_womens_manual_captcha import WomensClothingManualCaptcha


def remove_emojis(text):
    """
    이모지 제거 함수
    customtkinter는 이모지를 렌더링하지 못해 네모박스로 표시되므로 제거 필요
    """
    # 이모지 유니코드 범위 패턴
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # 얼굴 표정
        "\U0001F300-\U0001F5FF"  # 기호 및 픽토그램
        "\U0001F680-\U0001F6FF"  # 교통 및 지도
        "\U0001F1E0-\U0001F1FF"  # 국기
        "\U00002702-\U000027B0"  # 딩뱃
        "\U000024C2-\U0001F251"  # 기타
        "\U0001F900-\U0001F9FF"  # 추가 기호
        "\U0001FA70-\U0001FAFF"  # 확장 기호
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)


class ProductCollectorGUI:
    """상품 수집 GUI 애플리케이션"""

    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("네이버 쇼핑 상품 수집기")
        self.window.geometry("900x700")

        # 테마 설정
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 크롤러 인스턴스
        self.crawler = None
        self.is_running = False

        # 로그 큐 (스레드 간 통신용)
        self.log_queue = queue.Queue()

        # GUI 구성
        self._create_widgets()

        # 로그 업데이트 타이머
        self.window.after(100, self._update_log_from_queue)

    def _create_widgets(self):
        """GUI 위젯 생성"""

        # 메인 프레임
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 제목
        title_label = ctk.CTkLabel(
            main_frame,
            text="네이버 쇼핑 여성의류 상품 수집기",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=(0, 20))

        # 설정 프레임
        settings_frame = ctk.CTkFrame(main_frame)
        settings_frame.pack(fill="x", pady=(0, 20))

        # 수집 모드 선택
        mode_frame = ctk.CTkFrame(settings_frame)
        mode_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(mode_frame, text="수집 모드:", font=("Arial", 14, "bold")).pack(anchor="w", padx=(0, 10))

        self.collection_mode = ctk.StringVar(value="test")  # "test" or "infinite"

        # 테스트 모드 라디오 버튼
        test_radio_frame = ctk.CTkFrame(mode_frame)
        test_radio_frame.pack(fill="x", pady=5)

        self.test_radio = ctk.CTkRadioButton(
            test_radio_frame,
            text="테스트 수집 (개수 지정)",
            variable=self.collection_mode,
            value="test",
            command=self._toggle_count_entry,
            font=("Arial", 12)
        )
        self.test_radio.pack(side="left")

        self.product_count_entry = ctk.CTkEntry(test_radio_frame, width=80, placeholder_text="20")
        self.product_count_entry.pack(side="left", padx=(10, 0))
        self.product_count_entry.insert(0, "20")

        ctk.CTkLabel(test_radio_frame, text="개", font=("Arial", 12)).pack(side="left", padx=(5, 0))

        # 전체 수집 라디오 버튼
        infinite_radio_frame = ctk.CTkFrame(mode_frame)
        infinite_radio_frame.pack(fill="x", pady=5)

        self.infinite_radio = ctk.CTkRadioButton(
            infinite_radio_frame,
            text="전체 수집 (무한, 중단/재개 가능)",
            variable=self.collection_mode,
            value="infinite",
            command=self._toggle_count_entry,
            font=("Arial", 12)
        )
        self.infinite_radio.pack(side="left")

        # 옵션 프레임
        options_frame = ctk.CTkFrame(settings_frame)
        options_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(options_frame, text="저장 옵션:", font=("Arial", 14, "bold")).pack(anchor="w", padx=(0, 10))

        # DB 저장 (항상 켜짐, 필수)
        self.save_db_var = ctk.BooleanVar(value=True)
        self.save_db_check = ctk.CTkCheckBox(
            options_frame,
            text="DB에 저장 (필수)",
            variable=self.save_db_var,
            font=("Arial", 12),
            state="disabled"  # 항상 켜짐
        )
        self.save_db_check.pack(anchor="w", padx=10, pady=5)

        # 중복 체크 (항상 켜짐)
        self.skip_duplicates_var = ctk.BooleanVar(value=True)
        self.skip_duplicates_check = ctk.CTkCheckBox(
            options_frame,
            text="중복 상품 건너뛰기 (이미 수집된 상품 스킵)",
            variable=self.skip_duplicates_var,
            font=("Arial", 12)
        )
        self.skip_duplicates_check.pack(anchor="w", padx=10, pady=5)

        # JSON 저장 (디버그용, 기본 OFF)
        self.save_json_var = ctk.BooleanVar(value=False)
        self.save_json_check = ctk.CTkCheckBox(
            options_frame,
            text="JSON 파일로 저장 (디버그용, 대량 수집 시 비권장)",
            variable=self.save_json_var,
            font=("Arial", 12)
        )
        self.save_json_check.pack(anchor="w", padx=10, pady=5)

        # 버튼 프레임
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(0, 20))

        # 시작 버튼
        self.start_button = ctk.CTkButton(
            button_frame,
            text="수집 시작",
            command=self._start_crawling,
            font=("Arial", 14, "bold"),
            height=40,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.start_button.pack(side="left", expand=True, fill="x", padx=(10, 5))

        # 중지 버튼 (초기 비활성화)
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="수집 중지",
            command=self._stop_crawling,
            font=("Arial", 14, "bold"),
            height=40,
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_button.pack(side="left", expand=True, fill="x", padx=(5, 10))

        # 상태 표시
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="대기 중...",
            font=("Arial", 14)
        )
        self.status_label.pack(pady=(0, 10))

        # 로그 프레임
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(log_frame, text="실시간 로그:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

        # 로그 텍스트 박스 (스크롤바 포함)
        self.log_text = ctk.CTkTextbox(log_frame, font=("Courier", 11))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _toggle_count_entry(self):
        """수집 모드에 따라 개수 입력 필드 활성화/비활성화"""
        if self.collection_mode.get() == "test":
            self.product_count_entry.configure(state="normal")
        else:
            self.product_count_entry.configure(state="disabled")

    def _log(self, message):
        """로그 메시지 추가 (이모지 제거)"""
        clean_message = remove_emojis(message)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {clean_message}\n"
        self.log_queue.put(log_entry)

    def _update_log_from_queue(self):
        """큐에서 로그 메시지를 가져와 UI 업데이트"""
        try:
            while True:
                log_entry = self.log_queue.get_nowait()
                self.log_text.insert("end", log_entry)
                self.log_text.see("end")
        except queue.Empty:
            pass
        finally:
            # 100ms마다 큐 확인
            self.window.after(100, self._update_log_from_queue)

    def _start_crawling(self):
        """크롤링 시작"""
        if self.is_running:
            self._log("이미 크롤링이 진행 중입니다.")
            return

        # 수집 모드 확인
        is_infinite = self.collection_mode.get() == "infinite"
        product_count = None

        if not is_infinite:
            # 테스트 모드: 상품 개수 검증
            try:
                product_count = int(self.product_count_entry.get())
                if product_count < 1:
                    raise ValueError("1개 이상 입력하세요.")
            except ValueError as e:
                self._log(f"오류: 올바른 상품 개수를 입력하세요. ({e})")
                return

        # UI 상태 변경
        self.is_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text="수집 중...")

        # 로그 초기화
        self.log_text.delete("1.0", "end")
        self._log("="*60)
        if is_infinite:
            self._log("전체 상품 수집 시작 (무한 모드)")
            self._log("중단하려면 '수집 중지' 버튼을 클릭하세요")
        else:
            self._log(f"테스트 수집 시작: {product_count}개")
        self._log("="*60)

        # 옵션 출력
        self._log(f"중복 체크: {'예' if self.skip_duplicates_var.get() else '아니오'}")
        self._log(f"JSON 저장: {'예' if self.save_json_var.get() else '아니오'} (디버그용)")
        self._log("")

        # 별도 스레드에서 크롤링 실행
        thread = threading.Thread(
            target=self._run_crawling_thread,
            args=(product_count, is_infinite),
            daemon=True
        )
        thread.start()

    def _run_crawling_thread(self, product_count, is_infinite):
        """별도 스레드에서 asyncio 이벤트 루프 실행"""
        try:
            # 새 이벤트 루프 생성 (스레드별로 별도 루프 필요)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 크롤러 생성
            # 무한 모드면 product_count=None (무한 수집)
            actual_count = None if is_infinite else product_count

            self.crawler = WomensClothingManualCaptcha(
                product_count=actual_count,
                headless=False,
                enable_screenshot=False
            )

            # 크롤러의 print를 가로채서 로그로 리다이렉트
            self._redirect_crawler_logs()

            # 크롤링 실행
            self._log("크롤링 시작...")
            data = loop.run_until_complete(self.crawler.crawl_with_manual_captcha())

            if not self.is_running:
                self._log("")
                self._log("사용자가 중지했습니다.")
                # 중지해도 수집한 데이터는 저장
                if self.crawler.products_data:
                    self._log(f"중지 전까지 {len(self.crawler.products_data)}개 상품 수집됨")

            # 결과 저장 (중지해도 저장)
            if self.crawler.products_data:
                self._log("")
                self._log(f"총 {len(self.crawler.products_data)}개 상품 수집 완료!")

                # DB 저장 (항상 실행)
                self._log("")
                self._log("DB에 저장 중...")
                skip_dup = self.skip_duplicates_var.get()
                # save_to_db에 skip_duplicates 전달
                success = self.crawler.save_to_db(skip_duplicates=skip_dup)
                if success:
                    self._log("DB 저장 완료!")
                else:
                    self._log("DB 저장 실패!")

                # JSON 저장 (선택사항)
                if self.save_json_var.get():
                    self._log("")
                    self._log("JSON 파일로 저장 중...")
                    filename = self.crawler.save_to_json()
                    if filename:
                        self._log(f"JSON 저장 완료: {filename}")

                # 요약 출력
                self._log("")
                self._log("="*60)
                if self.is_running or not is_infinite:
                    self._log("수집 완료!")
                else:
                    self._log("수집 중지됨 (수집된 데이터는 저장됨)")
                self._log("="*60)
                self.status_label.configure(text="수집 완료!")
            else:
                self._log("상품 수집 실패!")
                self.status_label.configure(text="수집 실패!")

        except Exception as e:
            self._log(f"오류 발생: {str(e)}")
            import traceback
            self._log(traceback.format_exc())
            self.status_label.configure(text="오류 발생!")

        finally:
            # UI 상태 복원
            self.is_running = False
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

    def _redirect_crawler_logs(self):
        """크롤러의 print 출력을 로그로 리다이렉트"""
        import io
        import sys

        class LogRedirector(io.TextIOBase):
            def __init__(self, gui_logger):
                self.gui_logger = gui_logger

            def write(self, text):
                if text.strip():
                    self.gui_logger(text.strip())
                return len(text)

        # stdout을 GUI 로그로 리다이렉트
        sys.stdout = LogRedirector(self._log)
        sys.stderr = LogRedirector(self._log)

    def _stop_crawling(self):
        """크롤링 중지"""
        if not self.is_running:
            return

        self._log("")
        self._log("중지 요청됨... (크롤러가 안전하게 종료될 때까지 대기)")
        self.is_running = False
        self.status_label.configure(text="중지 중...")

    def run(self):
        """GUI 실행"""
        self.window.mainloop()


def main():
    """메인 함수"""
    app = ProductCollectorGUI()
    app.run()


if __name__ == "__main__":
    main()
