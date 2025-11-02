"""
네이버 쇼핑 상품 수집 GUI - 멀티 태스크 버전
하나의 GUI에서 여러 카테고리를 독립적으로 실행 가능
"""
import sys
import asyncio
import threading
import queue
import re
import json
import multiprocessing
from datetime import datetime
from typing import Dict, Optional
import customtkinter as ctk

# 프로젝트 경로 추가
sys.path.append('/home/dino/MyProjects/Crawl')
from src.core.product_crawler_v2 import ProgressiveCrawler


def remove_emojis(text):
    """이모지 제거 함수"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # 얼굴 표정
        "\U0001F300-\U0001F5FF"  # 기호 및 픽토그램
        "\U0001F680-\U0001F6FF"  # 교통 및 지도
        "\U0001F1E0-\U0001F1FF"  # 국기
        "\U00002702-\U000027B0"  # 딩뱃
        "\U0001F900-\U0001F9FF"  # 추가 기호
        "\U0001FA70-\U0001FAFF"  # 확장 기호
        "\U00002300-\U000023FF"  # 기타 기술 기호
        "\U00002600-\U000026FF"  # 기타 기호
        "\U00002B50"             # 별 이모지
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)


def run_crawler_process(category_name: str, category_id: str, product_count: Optional[int],
                       skip_duplicates: bool, save_json: bool, resume: bool, headless: bool,
                       log_queue: multiprocessing.Queue, stop_event: multiprocessing.Event):
    """
    별도 프로세스에서 크롤러 실행

    Args:
        category_name: 카테고리 이름
        category_id: 카테고리 ID
        product_count: 수집 개수 (None이면 무한)
        skip_duplicates: 중복 체크 여부
        save_json: JSON 저장 여부
        resume: 재개 여부
        log_queue: 로그 전달용 큐
        stop_event: 중지 이벤트
    """
    # 프로세스 독립성 설정 (터미널 종료 시에도 살아남기)
    import os
    import signal

    # SIGHUP 무시 (터미널 종료 신호 무시)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)

    # 새 프로세스 그룹 생성 (부모로부터 독립)
    try:
        os.setpgid(0, 0)
    except:
        pass  # Windows에서는 실패할 수 있음

    async def crawl():
        try:
            # 로그를 큐로 리다이렉트
            class QueueLogger:
                def __init__(self, log_queue):
                    self.log_queue = log_queue

                def write(self, text):
                    if text.strip():
                        self.log_queue.put(('log', text.strip()))
                    return len(text)

                def flush(self):
                    pass

            sys.stdout = QueueLogger(log_queue)
            sys.stderr = QueueLogger(log_queue)

            # 크롤러 생성
            crawler = ProgressiveCrawler(
                product_count=product_count,
                headless=headless,
                category_name=category_name,
                category_id=category_id
            )

            # 중지 이벤트 연결
            def check_stop():
                if stop_event.is_set():
                    crawler.should_stop = True

            # 주기적으로 중지 체크
            log_queue.put(('status', 'running'))
            log_queue.put(('log', f"{category_name} 크롤링 시작..."))

            # 크롤링 실행
            data = await crawler.crawl()

            if stop_event.is_set():
                log_queue.put(('log', f"{category_name} 사용자가 중지했습니다"))
                log_queue.put(('status', 'stopped'))
            else:
                log_queue.put(('log', f"{category_name} 크롤링 완료!"))
                log_queue.put(('status', 'completed'))

            # DB 저장
            if crawler.products_data:
                log_queue.put(('log', f"{category_name} DB 저장 중..."))
                success = crawler.save_to_db(skip_duplicates=skip_duplicates)
                if success:
                    log_queue.put(('log', f"{category_name} DB 저장 완료!"))
                    log_queue.put(('collected', len(crawler.products_data)))
                else:
                    log_queue.put(('log', f"{category_name} DB 저장 실패!"))

                # JSON 저장 (선택)
                if save_json:
                    log_queue.put(('log', f"{category_name} JSON 저장 중..."))
                    filename = crawler.save_to_json()
                    if filename:
                        log_queue.put(('log', f"{category_name} JSON 저장: {filename}"))

            return data

        except Exception as e:
            log_queue.put(('log', f"{category_name} 오류: {str(e)}"))
            log_queue.put(('status', 'failed'))
            import traceback
            log_queue.put(('log', traceback.format_exc()))
            return None

    # asyncio 실행
    asyncio.run(crawl())


class CategoryTaskCard:
    """개별 카테고리 작업 카드 UI"""

    def __init__(self, parent, category_name: str, category_id: str,
                 product_count: Optional[int], skip_duplicates: bool,
                 save_json: bool, resume: bool, headless: bool, on_remove_callback):
        self.category_name = category_name
        self.category_id = category_id
        self.product_count = product_count
        self.skip_duplicates = skip_duplicates
        self.save_json = save_json
        self.resume = resume
        self.headless = headless
        self.on_remove_callback = on_remove_callback

        # 프로세스 관련
        self.process: Optional[multiprocessing.Process] = None
        self.log_queue: Optional[multiprocessing.Queue] = None
        self.stop_event: Optional[multiprocessing.Event] = None
        self.is_running = False

        # 통계
        self.collected_count = 0
        self.status = "대기 중"

        # UI 프레임 (카드 스타일)
        self.frame = ctk.CTkFrame(parent, fg_color="gray25", corner_radius=10)
        self.frame.pack(fill="x", padx=10, pady=5)

        # 헤더 (카테고리명 + 버튼)
        header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)

        # 카테고리명
        self.title_label = ctk.CTkLabel(
            header_frame,
            text=f"{category_name}",
            font=("Arial", 16, "bold")
        )
        self.title_label.pack(side="left")

        # 제거 버튼
        self.remove_button = ctk.CTkButton(
            header_frame,
            text="X",
            command=self._on_remove,
            width=30,
            height=30,
            fg_color="gray30",
            hover_color="red"
        )
        self.remove_button.pack(side="right", padx=5)

        # 중지 버튼
        self.stop_button = ctk.CTkButton(
            header_frame,
            text="중지",
            command=self._stop_crawling,
            width=80,
            height=30,
            fg_color="#FF9800",
            hover_color="#F57C00",
            state="disabled"
        )
        self.stop_button.pack(side="right", padx=5)

        # 시작 버튼
        self.start_button = ctk.CTkButton(
            header_frame,
            text="시작",
            command=self._start_crawling,
            width=80,
            height=30,
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.start_button.pack(side="right", padx=5)

        # 상태 영역
        status_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        status_frame.pack(fill="x", padx=15, pady=(0, 10))

        # 상태 텍스트
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="대기 중",
            font=("Arial", 12)
        )
        self.status_label.pack(side="left")

        # 수집 카운터
        self.count_label = ctk.CTkLabel(
            status_frame,
            text="수집: 0개",
            font=("Arial", 12)
        )
        self.count_label.pack(side="right")

        # 설정 정보
        info_text = f"모드: {'무한' if product_count is None else f'{product_count}개'} | 중복: {'스킵' if skip_duplicates else '허용'}"
        self.info_label = ctk.CTkLabel(
            status_frame,
            text=info_text,
            font=("Arial", 10),
            text_color="gray60"
        )
        self.info_label.pack(side="left", padx=(20, 0))

        # 로그 텍스트박스 (접을 수 있는 영역)
        self.log_visible = True  # 기본값: 열림
        self.log_frame = ctk.CTkFrame(self.frame, fg_color="gray20")

        # 로그 토글 버튼
        self.log_toggle_btn = ctk.CTkButton(
            self.frame,
            text="▲ 로그 숨기기",  # 열린 상태
            command=self._toggle_log,
            width=100,
            height=25,
            fg_color="gray30",
            hover_color="gray35",
            font=("Arial", 10)
        )
        self.log_toggle_btn.pack(fill="x", padx=15, pady=(5, 0))

        # 로그 텍스트박스
        self.log_textbox = ctk.CTkTextbox(
            self.log_frame,
            height=150,
            font=("Consolas", 10),
            fg_color="gray15"
        )
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=10)

        # 로그 영역 기본으로 표시
        self.log_frame.pack(fill="x", padx=15, pady=(0, 10))

    def _toggle_log(self):
        """로그 영역 토글"""
        if self.log_visible:
            self.log_frame.pack_forget()
            self.log_toggle_btn.configure(text="▼ 로그 보기")
            self.log_visible = False
        else:
            self.log_frame.pack(fill="x", padx=15, pady=(0, 10))
            self.log_toggle_btn.configure(text="▲ 로그 숨기기")
            self.log_visible = True

    def _start_crawling(self):
        """크롤링 시작"""
        if self.is_running:
            return

        self.is_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text="▶ 실행 중", text_color="#2196F3")

        # 멀티프로세싱 큐와 이벤트 생성
        self.log_queue = multiprocessing.Queue()
        self.stop_event = multiprocessing.Event()

        # 별도 프로세스에서 크롤러 실행
        self.process = multiprocessing.Process(
            target=run_crawler_process,
            args=(
                self.category_name,
                self.category_id,
                self.product_count,
                self.skip_duplicates,
                self.save_json,
                self.resume,
                self.headless,
                self.log_queue,
                self.stop_event
            )
        )
        self.process.start()

        # 로그 모니터링 스레드 시작
        threading.Thread(target=self._monitor_logs, daemon=True).start()

    def _stop_crawling(self):
        """크롤링 중지"""
        if not self.is_running or not self.stop_event:
            return

        self.stop_event.set()
        self.status_label.configure(text="■ 중지 중", text_color="#FF9800")

    def _on_remove(self):
        """카드 제거"""
        if self.is_running:
            # 실행 중이면 먼저 중지
            if self.stop_event:
                self.stop_event.set()
            if self.process and self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=3)

        # UI 제거
        self.frame.destroy()

        # 콜백 호출
        if self.on_remove_callback:
            self.on_remove_callback(self)

    def _monitor_logs(self):
        """로그 큐 모니터링"""
        while self.is_running:
            try:
                # 큐에서 메시지 가져오기 (타임아웃 1초)
                msg_type, msg_data = self.log_queue.get(timeout=1)

                if msg_type == 'log':
                    # 로그를 textbox에 추가
                    clean_msg = remove_emojis(msg_data)
                    self.log_textbox.configure(state="normal")
                    self.log_textbox.insert("end", f"{clean_msg}\n")
                    self.log_textbox.see("end")  # 자동 스크롤
                    self.log_textbox.configure(state="disabled")

                    # 디버깅용 print (터미널에도 출력)
                    print(f"[{self.category_name}] {clean_msg}")

                elif msg_type == 'status':
                    if msg_data == 'running':
                        self.status_label.configure(text="▶ 실행 중", text_color="#2196F3")
                    elif msg_data == 'completed':
                        self.status_label.configure(text="✓ 완료", text_color="#4CAF50")
                        self._finish_task()
                    elif msg_data == 'stopped':
                        self.status_label.configure(text="■ 중지됨", text_color="#FF9800")
                        self._finish_task()
                    elif msg_data == 'failed':
                        self.status_label.configure(text="✗ 실패", text_color="#F44336")
                        self._finish_task()

                elif msg_type == 'collected':
                    self.collected_count = msg_data
                    self.count_label.configure(text=f"수집: {self.collected_count}개")

            except queue.Empty:
                # 프로세스가 종료되었는지 확인
                if self.process and not self.process.is_alive():
                    if self.is_running:
                        # 비정상 종료
                        self.status_label.configure(text="✗ 종료됨", text_color="#F44336")
                        self._finish_task()
                    break
            except Exception as e:
                print(f"[{self.category_name}] 로그 모니터링 오류: {e}")
                break

    def _finish_task(self):
        """작업 종료 처리"""
        self.is_running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")


class MultiTaskGUI:
    """멀티 태스크 GUI 메인 클래스"""

    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("네이버 쇼핑 상품 수집기 - 멀티 태스크")
        self.window.geometry("1000x800")
        self.window.minsize(900, 700)

        # 테마 설정
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 카테고리 데이터
        self.categories = self._load_categories()

        # 작업 카드 리스트
        self.task_cards: Dict[str, CategoryTaskCard] = {}

        # GUI 구성
        self._create_widgets()

    def _load_categories(self):
        """카테고리 JSON 파일 로드"""
        try:
            with open('data/naver_categories_hierarchy.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                categories_data = data.get('카테고리', {})

                categories = {}
                for cat_name, cat_info in categories_data.items():
                    cat_id = cat_info.get('id')
                    if cat_id:
                        categories[cat_name] = cat_id

                return categories
        except Exception as e:
            print(f"[경고] 카테고리 파일 로드 실패: {e}")
            return {
                "여성의류": "10000107",
                "남성의류": "10000108",
                "패션잡화": "10000109",
                "신발": "10000110"
            }

    def _create_widgets(self):
        """GUI 위젯 생성"""
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 제목
        title_label = ctk.CTkLabel(
            main_frame,
            text="네이버 쇼핑 상품 수집기 - 멀티 태스크",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=(0, 10))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="여러 카테고리를 독립적으로 실행할 수 있습니다",
            font=("Arial", 11),
            text_color="gray60"
        )
        subtitle_label.pack(pady=(0, 20))

        # 작업 추가 패널
        add_panel = ctk.CTkFrame(main_frame)
        add_panel.pack(fill="x", pady=(0, 15))

        # 카테고리 선택
        ctk.CTkLabel(add_panel, text="카테고리:", font=("Arial", 12)).pack(side="left", padx=10)

        self.category_var = ctk.StringVar(value="여성의류")
        category_dropdown = ctk.CTkOptionMenu(
            add_panel,
            variable=self.category_var,
            values=list(self.categories.keys()),
            width=150
        )
        category_dropdown.pack(side="left", padx=5)

        # 수집 모드
        ctk.CTkLabel(add_panel, text="모드:", font=("Arial", 12)).pack(side="left", padx=(20, 5))

        self.mode_var = ctk.StringVar(value="infinite")
        mode_radio1 = ctk.CTkRadioButton(
            add_panel,
            text="무한",
            variable=self.mode_var,
            value="infinite"
        )
        mode_radio1.pack(side="left", padx=5)

        mode_radio2 = ctk.CTkRadioButton(
            add_panel,
            text="개수 지정",
            variable=self.mode_var,
            value="count"
        )
        mode_radio2.pack(side="left", padx=5)

        self.count_entry = ctk.CTkEntry(add_panel, width=60, placeholder_text="20")
        self.count_entry.pack(side="left", padx=5)

        # 옵션
        self.skip_dup_var = ctk.BooleanVar(value=True)
        skip_dup_check = ctk.CTkCheckBox(
            add_panel,
            text="중복 스킵",
            variable=self.skip_dup_var
        )
        skip_dup_check.pack(side="left", padx=(20, 5))

        self.headless_var = ctk.BooleanVar(value=True)
        headless_check = ctk.CTkCheckBox(
            add_panel,
            text="브라우저 숨기기",
            variable=self.headless_var
        )
        headless_check.pack(side="left", padx=5)

        # 작업 추가 버튼
        add_button = ctk.CTkButton(
            add_panel,
            text="+ 작업 추가",
            command=self._add_task,
            fg_color="#4CAF50",
            hover_color="#45a049",
            width=120
        )
        add_button.pack(side="right", padx=10)

        # 스크롤 가능한 작업 목록 영역
        self.tasks_scroll = ctk.CTkScrollableFrame(
            main_frame,
            label_text="작업 목록"
        )
        self.tasks_scroll.pack(fill="both", expand=True)

        # 하단 정보
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", pady=(15, 0))

        info_label = ctk.CTkLabel(
            info_frame,
            text="팁: 각 카테고리는 독립적으로 실행됩니다. 여러 작업을 추가하고 동시에 실행할 수 있습니다.",
            font=("Arial", 10),
            text_color="gray60"
        )
        info_label.pack(pady=10)

    def _add_task(self):
        """작업 추가"""
        category_name = self.category_var.get()
        category_id = self.categories.get(category_name)

        # 이미 추가된 카테고리 확인
        if category_name in self.task_cards:
            print(f"[경고] {category_name}는 이미 추가되었습니다")
            return

        # 수집 개수
        if self.mode_var.get() == "infinite":
            product_count = None
        else:
            try:
                product_count = int(self.count_entry.get() or "20")
            except:
                product_count = 20

        # 작업 카드 생성
        card = CategoryTaskCard(
            parent=self.tasks_scroll,
            category_name=category_name,
            category_id=category_id,
            product_count=product_count,
            skip_duplicates=self.skip_dup_var.get(),
            save_json=False,
            resume=False,
            headless=self.headless_var.get(),
            on_remove_callback=self._remove_task
        )

        self.task_cards[category_name] = card
        print(f"[추가] {category_name} 작업 추가됨")

    def _remove_task(self, card: CategoryTaskCard):
        """작업 제거"""
        if card.category_name in self.task_cards:
            del self.task_cards[card.category_name]
            print(f"[제거] {card.category_name} 작업 제거됨")

    def run(self):
        """GUI 실행"""
        self.window.mainloop()


def main():
    """메인 함수"""
    # 프로세스 독립성 설정 (터미널 종료 시에도 GUI 유지)
    import os
    import signal

    # SIGHUP 무시 (터미널 종료 신호 무시)
    try:
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
    except:
        pass  # Windows에서는 SIGHUP 없음

    # 멀티프로세싱 설정 (Windows/Linux 호환)
    multiprocessing.set_start_method('spawn', force=True)

    print("="*60)
    print("Multi-Task GUI Started")
    print("="*60)
    print("터미널을 닫아도 GUI가 계속 실행됩니다.")
    print("종료: GUI 창의 [X] 버튼 클릭")
    print("="*60 + "\n")

    app = MultiTaskGUI()
    app.run()


if __name__ == "__main__":
    main()
