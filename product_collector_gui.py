"""
네이버 쇼핑 상품 수집 GUI
간단한 인터페이스로 다양한 카테고리의 상품 정보를 수집합니다.
"""
import sys
import asyncio
import threading
import queue
import re
import json
from datetime import datetime
import customtkinter as ctk

# 프로젝트 경로 추가
sys.path.append('/home/dino/MyProjects/Crawl')
from src.core.product_crawler_v2 import ProgressiveCrawler


def remove_emojis(text):
    """
    이모지 제거 함수
    customtkinter는 이모지를 렌더링하지 못해 네모박스로 표시되므로 제거 필요

    중요: 한글(U+AC00~U+D7AF)은 제거하지 않음!
    """
    # 이모지 유니코드 범위 패턴 (한글 제외)
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
        "\U0000231A-\U0000231B"  # 시계 이모지
        "\U000023E9-\U000023F3"  # 미디어 이모지
        "\U000025AA-\U000025AB"  # 사각형 이모지
        "\U000025B6"             # 재생 버튼
        "\U000025C0"             # 되감기 버튼
        "\U000025FB-\U000025FE"  # 사각형
        "\U00002614-\U00002615"  # 우산, 커피
        "\U0000263A"             # 웃는 얼굴
        "\U0000267F"             # 휠체어
        "\U00002693"             # 닻
        "\U000026A1"             # 번개
        "\U000026AA-\U000026AB"  # 원
        "\U000026BD-\U000026BE"  # 축구공, 야구공
        "\U000026C4-\U000026C5"  # 눈사람, 구름
        "\U000026CE"             # 양자리
        "\U000026D4"             # 진입금지
        "\U000026EA"             # 교회
        "\U000026F2-\U000026F3"  # 분수, 골프
        "\U000026F5"             # 요트
        "\U000026FA"             # 텐트
        "\U000026FD"             # 주유소
        "\U00002705"             # 체크마크
        "\U0000270A-\U0000270B"  # 주먹
        "\U00002728"             # 반짝임
        "\U0000274C"             # X표
        "\U0000274E"             # X표
        "\U00002753-\U00002755"  # 물음표, 느낌표
        "\U00002757"             # 느낌표
        "\U00002795-\U00002797"  # +, -, /
        "\U000027A1"             # 화살표
        "\U000027B0"             # 고리
        "\U000027BF"             # 이중 고리
        "\U00002B1B-\U00002B1C"  # 사각형
        "\U00002B55"             # 원
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)


class ProductCollectorGUI:
    """상품 수집 GUI 애플리케이션"""

    def __init__(self):
        self.window = ctk.CTk()

        # 창을 일단 숨김 (초기화 중 깜빡임 방지)
        self.window.withdraw()

        self.window.title("네이버 쇼핑 상품 수집기")

        # 창 크기 및 위치 설정 (고정 좌표 사용)
        window_width = 950
        window_height = 850
        x_position = 100
        y_position = 50

        self.window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.window.minsize(800, 700)

        # 테마 설정
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 크롤러 인스턴스
        self.crawler = None
        self.is_running = False

        # 로그 큐 (스레드 간 통신용)
        self.log_queue = queue.Queue()

        # 카테고리 데이터 로드
        self.categories = self._load_categories()

        # 통계 정보 (실시간 업데이트용)
        self.stats = {
            'collected': 0,    # 수집된 상품 수
            'skipped': 0,      # 중복 스킵
            'failed': 0,       # 실패
            'speed': 0.0,      # 평균 속도 (개/분)
            'start_time': None,
            'last_product': None  # 최근 수집 상품명
        }

        # 로그 레벨 (간결/상세)
        self.log_level = "normal"  # "normal" or "verbose"

        # 설정 접기 상태 (기본: 접힌 상태)
        self.settings_collapsed = True

        # GUI 구성
        self._create_widgets()

        # 로그 업데이트 타이머
        self.window.after(100, self._update_log_from_queue)

        # 통계 업데이트 타이머 (1초마다)
        self.window.after(1000, self._update_stats_display)

        # 키보드 단축키 바인딩
        self.window.bind('<Return>', self._on_enter_key)
        self.window.bind('<Escape>', self._on_escape_key)

        # 모든 위젯 초기화 완료 후 창 표시 (중요!)
        self.window.update_idletasks()  # 레이아웃 계산 완료
        self.window.deiconify()  # 창 표시
        self.window.lift()  # 최상단으로
        self.window.attributes('-topmost', True)  # 잠시 최상단 고정
        self.window.after(300, lambda: self.window.attributes('-topmost', False))  # 0.3초 후 해제

    def _load_categories(self):
        """카테고리 JSON 파일에서 카테고리 목록 로드"""
        try:
            with open('data/naver_categories_hierarchy.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                categories_data = data.get('카테고리', {})

                # 카테고리 목록 생성 (이름: ID)
                categories = {}
                for cat_name, cat_info in categories_data.items():
                    cat_id = cat_info.get('id')
                    if cat_id:
                        categories[cat_name] = cat_id

                return categories
        except Exception as e:
            print(f"[경고] 카테고리 파일 로드 실패: {e}")
            # 기본 카테고리만 제공
            return {
                "여성의류": "10000107",
                "남성의류": "10000108",
                "패션잡화": "10000109",
                "신발": "10000110"
            }

    def _create_widgets(self):
        """GUI 위젯 생성"""

        # 메인 프레임
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 제목 (더 크고 세련되게)
        title_label = ctk.CTkLabel(
            main_frame,
            text="네이버 쇼핑 상품 수집기",
            font=("Arial", 28, "bold")
        )
        title_label.pack(pady=(0, 10))

        # 부제목
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="간편하게 상품 데이터를 수집하세요",
            font=("Arial", 12),
            text_color="gray60"
        )
        subtitle_label.pack(pady=(0, 20))

        # 설정 프레임 (접기 가능)
        settings_container = ctk.CTkFrame(main_frame)
        settings_container.pack(fill="x", pady=(0, 10))

        # 설정 헤더 (접기 버튼)
        settings_header = ctk.CTkFrame(settings_container)
        settings_header.pack(fill="x", padx=10, pady=5)

        self.settings_toggle_button = ctk.CTkButton(
            settings_header,
            text="설정 (펼치기)",
            command=self._toggle_settings,
            font=("Arial", 13, "bold"),
            height=35,
            fg_color="gray30",
            hover_color="gray40",
            anchor="w",
            width=150
        )
        self.settings_toggle_button.pack(side="left")

        ctk.CTkLabel(
            settings_header,
            text="수집 옵션을 설정하세요",
            font=("Arial", 11),
            text_color="gray60"
        ).pack(side="left", padx=10)

        # 설정 프레임 (접을 수 있음, 기본: 접힌 상태)
        self.settings_frame = ctk.CTkFrame(settings_container)
        # 초기에는 pack하지 않음 (접힌 상태)

        # 카테고리 선택 프레임
        category_frame = ctk.CTkFrame(self.settings_frame)
        category_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(category_frame, text="카테고리 선택:", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 5))

        # 카테고리 드롭다운
        category_dropdown_frame = ctk.CTkFrame(category_frame)
        category_dropdown_frame.pack(fill="x", pady=5)

        category_names = list(self.categories.keys())
        self.selected_category = ctk.StringVar(value="여성의류")  # 기본값

        self.category_dropdown = ctk.CTkOptionMenu(
            category_dropdown_frame,
            variable=self.selected_category,
            values=category_names,
            font=("Arial", 12),
            width=300
        )
        self.category_dropdown.pack(side="left")

        # 카테고리 변경 이벤트 핸들러
        self.selected_category.trace_add('write', self._on_category_change)

        # 수집 모드 선택
        mode_frame = ctk.CTkFrame(self.settings_frame)
        mode_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(mode_frame, text="수집 모드:", font=("Arial", 14, "bold")).pack(anchor="w", padx=(0, 10))

        self.collection_mode = ctk.StringVar(value="infinite")  # "test" or "infinite" - 기본: 무한 모드

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

        self.product_count_entry = ctk.CTkEntry(test_radio_frame, width=80, placeholder_text="예: 20", state="disabled")
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
        options_frame = ctk.CTkFrame(self.settings_frame)
        options_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(options_frame, text="저장 옵션:", font=("Arial", 14, "bold")).pack(anchor="w", padx=(0, 10))

        # DB 저장 (항상 켜짐, 필수)
        self.save_db_var = ctk.BooleanVar(value=True)
        self.save_db_check = ctk.CTkCheckBox(
            options_frame,
            text="DB 저장 (필수)",
            variable=self.save_db_var,
            font=("Arial", 12),
            state="disabled"  # 항상 켜짐
        )
        self.save_db_check.pack(anchor="w", padx=10, pady=5)

        # 중복 체크
        self.skip_duplicates_var = ctk.BooleanVar(value=True)
        self.skip_duplicates_check = ctk.CTkCheckBox(
            options_frame,
            text="중복 상품 건너뛰기",
            variable=self.skip_duplicates_var,
            font=("Arial", 12)
        )
        self.skip_duplicates_check.pack(anchor="w", padx=10, pady=5)

        # JSON 저장 (디버그용, 기본 OFF)
        self.save_json_var = ctk.BooleanVar(value=False)
        self.save_json_check = ctk.CTkCheckBox(
            options_frame,
            text="JSON 파일 저장 (디버그용)",
            variable=self.save_json_var,
            font=("Arial", 12)
        )
        self.save_json_check.pack(anchor="w", padx=10, pady=5)

        # 재개 옵션
        self.resume_var = ctk.BooleanVar(value=False)
        self.resume_check = ctk.CTkCheckBox(
            options_frame,
            text="이어서 수집 (중단 지점부터 재개)",
            variable=self.resume_var,
            font=("Arial", 12),
            command=self._on_resume_check
        )
        self.resume_check.pack(anchor="w", padx=10, pady=5)

        # 재개 정보 표시
        self.resume_info_label = ctk.CTkLabel(
            options_frame,
            text="",
            font=("Arial", 10),
            text_color="gray60"
        )
        self.resume_info_label.pack(anchor="w", padx=30, pady=(0, 5))

        # 메모리 관리 안내
        memory_info = ctk.CTkLabel(
            options_frame,
            text="※ 장시간 실행 시 브라우저 메모리 증가 가능 (정상 현상)",
            font=("Arial", 9),
            text_color="gray50"
        )
        memory_info.pack(anchor="w", padx=10, pady=(0, 5))

        # 버튼 프레임
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(0, 20))

        # 시작 버튼 (현대적인 파란색)
        self.start_button = ctk.CTkButton(
            button_frame,
            text="수집 시작",
            command=self._start_crawling,
            font=("Arial", 15, "bold"),
            height=50,
            fg_color="#2196F3",
            hover_color="#1976D2",
            corner_radius=8
        )
        self.start_button.pack(side="left", expand=True, fill="x", padx=(10, 5))

        # 중지 버튼 (주황색, 초기 비활성화)
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="수집 중지",
            command=self._stop_crawling,
            font=("Arial", 15, "bold"),
            height=50,
            fg_color="#FF9800",
            hover_color="#F57C00",
            corner_radius=8,
            state="disabled"
        )
        self.stop_button.pack(side="left", expand=True, fill="x", padx=(5, 10))

        # 상태 프레임 (진행률 + 통계) - 카드 스타일
        status_frame = ctk.CTkFrame(main_frame, fg_color="gray25", corner_radius=10)
        status_frame.pack(fill="x", pady=(0, 15))

        # 왼쪽: 상태 + 진행률
        left_status_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        left_status_frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)

        self.status_label = ctk.CTkLabel(
            left_status_frame,
            text="● 대기 중",  # ● 기호 추가
            font=("Arial", 16, "bold")
        )
        self.status_label.pack(pady=(0, 8))

        # 진행률 표시
        self.progress_label = ctk.CTkLabel(
            left_status_frame,
            text="수집: 0개",
            font=("Arial", 13)
        )
        self.progress_label.pack(pady=(0, 8))

        # 프로그레스 바
        self.progress_bar = ctk.CTkProgressBar(
            left_status_frame,
            width=200,
            height=10
        )
        self.progress_bar.pack()
        self.progress_bar.set(0)  # 초기값 0%

        # 오른쪽: 통계 패널 - 카드 스타일 (2x2 그리드)
        stats_frame = ctk.CTkFrame(status_frame, fg_color="gray20", corner_radius=8)
        stats_frame.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(stats_frame, text="실시간 통계", font=("Arial", 13, "bold")).pack(pady=(8, 8))

        # 2x2 그리드 컨테이너
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(padx=10, pady=(0, 8))

        # 첫 번째 행
        row1 = ctk.CTkFrame(stats_grid, fg_color="transparent")
        row1.pack(fill="x", pady=2)

        self.stats_collected_label = ctk.CTkLabel(row1, text="수집: 0개", font=("Arial", 12), width=110)
        self.stats_collected_label.pack(side="left", padx=5)

        self.stats_skipped_label = ctk.CTkLabel(row1, text="중복: 0개", font=("Arial", 12), width=110)
        self.stats_skipped_label.pack(side="left", padx=5)

        # 두 번째 행
        row2 = ctk.CTkFrame(stats_grid, fg_color="transparent")
        row2.pack(fill="x", pady=2)

        self.stats_speed_label = ctk.CTkLabel(row2, text="속도: 0.0개/분", font=("Arial", 12), width=110)
        self.stats_speed_label.pack(side="left", padx=5)

        # 상품 미리보기는 별도 행
        self.stats_preview_label = ctk.CTkLabel(
            stats_frame,
            text="최근: -",
            font=("Arial", 10),
            text_color="gray50",
            wraplength=220
        )
        self.stats_preview_label.pack(pady=(6, 8))

        # 로그 프레임
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True)

        # 로그 헤더 (제목 + 버튼들)
        log_header_frame = ctk.CTkFrame(log_frame)
        log_header_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(log_header_frame, text="실시간 로그:", font=("Arial", 12, "bold")).pack(side="left")

        # 오른쪽 버튼들 (간격 8px로 증가)
        # 최근 기록 보기 버튼
        self.history_button = ctk.CTkButton(
            log_header_frame,
            text="최근 기록",
            command=self._show_history,
            font=("Arial", 11),
            width=90,
            height=28,
            fg_color="gray30",
            hover_color="gray40"
        )
        self.history_button.pack(side="right", padx=(8, 0))

        # 로그 레벨 토글 버튼
        self.log_level_button = ctk.CTkButton(
            log_header_frame,
            text="간결 모드",
            command=self._toggle_log_level,
            font=("Arial", 11),
            width=90,
            height=28,
            fg_color="gray30",
            hover_color="gray40"
        )
        self.log_level_button.pack(side="right", padx=(8, 0))

        # 테마 토글 버튼
        self.theme_button = ctk.CTkButton(
            log_header_frame,
            text="라이트 모드",
            command=self._toggle_theme,
            font=("Arial", 11),
            width=100,
            height=28,
            fg_color="gray30",
            hover_color="gray40"
        )
        self.theme_button.pack(side="right", padx=(8, 0))

        # 로그 복사 버튼
        self.copy_log_button = ctk.CTkButton(
            log_header_frame,
            text="로그 복사",
            command=self._copy_log,
            font=("Arial", 11),
            width=90,
            height=28,
            fg_color="gray30",
            hover_color="gray40"
        )
        self.copy_log_button.pack(side="right", padx=(8, 0))

        # 로그 텍스트 박스 (스크롤바 포함)
        self.log_text = ctk.CTkTextbox(log_frame, font=("Courier", 11))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _on_enter_key(self, event):
        """Enter 키: 수집 시작"""
        if not self.is_running:
            self._start_crawling()

    def _on_escape_key(self, event):
        """Escape 키: 수집 중지"""
        if self.is_running:
            self._stop_crawling()

    def _toggle_settings(self):
        """설정 영역 접기/펼치기"""
        self.settings_collapsed = not self.settings_collapsed

        if self.settings_collapsed:
            # 접기
            self.settings_frame.pack_forget()
            self.settings_toggle_button.configure(text="설정 (펼치기)")
        else:
            # 펼치기
            self.settings_frame.pack(fill="x", padx=10, pady=(5, 10), after=self.settings_toggle_button.master)
            self.settings_toggle_button.configure(text="설정 (접기)")

    def _on_category_change(self, *args):
        """카테고리 선택 변경 시 호출"""
        # 카테고리 변경 시 재개 정보 업데이트
        if self.resume_var.get():
            self._update_resume_info()

    def _on_resume_check(self):
        """재개 체크박스 변경 시 정보 업데이트"""
        self._update_resume_info()

    def _update_resume_info(self):
        """재개 모드 정보 조회 및 표시"""
        if not self.resume_var.get():
            self.resume_info_label.configure(text="")
            return

        try:
            from src.database.db_connector import DatabaseConnector
            category_name = self.selected_category.get()

            db = DatabaseConnector()
            db.connect()
            last_index = db.get_last_crawl_progress(category_name)
            db.close()

            if last_index is not None:
                self.resume_info_label.configure(
                    text=f"마지막 수집: {last_index + 1}번째 상품까지 완료 ({last_index + 2}번째부터 재개)"
                )
            else:
                self.resume_info_label.configure(text="재개 가능한 세션이 없습니다 (처음부터 시작)")
        except Exception as e:
            self.resume_info_label.configure(text=f"재개 정보 조회 실패: {str(e)[:30]}")

    def _toggle_theme(self):
        """다크/라이트 테마 토글"""
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            ctk.set_appearance_mode("light")
            self.theme_button.configure(text="다크 모드")
        else:
            ctk.set_appearance_mode("dark")
            self.theme_button.configure(text="라이트 모드")

    def _toggle_log_level(self):
        """로그 레벨 토글 (간결/상세)"""
        if self.log_level == "normal":
            self.log_level = "verbose"
            self.log_level_button.configure(text="상세 모드")
            self._log("로그 모드: 상세 (모든 로그 표시)")
        else:
            self.log_level = "normal"
            self.log_level_button.configure(text="간결 모드")
            self._log("로그 모드: 간결 (중요 로그만 표시)")

    def _show_history(self):
        """최근 수집 기록 보기 (로그에 출력)"""
        try:
            from src.database.db_connector import DatabaseConnector

            db = DatabaseConnector()
            db.connect()

            cursor = db.conn.cursor()
            cursor.execute(
                """
                SELECT category_name, start_time, end_time, status, total_products
                FROM crawl_history
                WHERE crawl_type = 'product'
                ORDER BY start_time DESC
                LIMIT 10
                """,
            )
            results = cursor.fetchall()
            cursor.close()
            db.close()

            # 로그에 출력 (팝업 대신)
            self._log("")
            self._log("="*60)
            self._log("최근 10회 수집 기록")
            self._log("="*60)

            if results:
                for idx, row in enumerate(results, 1):
                    category, start, end, status, total = row
                    start_str = start.strftime("%Y-%m-%d %H:%M") if start else "N/A"
                    end_str = end.strftime("%Y-%m-%d %H:%M") if end else "진행중"
                    total_str = str(total) if total else "0"

                    self._log(f"{idx}. {category} | {start_str} ~ {end_str} | {status} | {total_str}개")
            else:
                self._log("수집 기록이 없습니다.")

            self._log("="*60)
            self._log("")

        except Exception as e:
            self._log(f"기록 조회 실패: {str(e)[:80]}")

    def _update_stats_display(self):
        """통계 정보 업데이트 (1초마다 호출)"""
        if self.is_running and self.crawler:
            # 크롤러에서 실시간 정보 가져오기
            collected = len(self.crawler.products_data) if self.crawler.products_data else 0
            self.stats['collected'] = collected

            # 평균 속도 계산
            if self.stats['start_time']:
                elapsed_minutes = (datetime.now() - self.stats['start_time']).total_seconds() / 60
                if elapsed_minutes > 0:
                    self.stats['speed'] = collected / elapsed_minutes

            # 진행률 업데이트
            if self.collection_mode.get() == "infinite":
                self.progress_label.configure(text=f"수집: {collected}개 (무한 모드)")
                self.progress_bar.set(0)  # 무한 모드에서는 프로그레스 바 비활성화
            else:
                target = int(self.product_count_entry.get()) if self.product_count_entry.get().isdigit() else 0
                if target > 0:
                    progress_percent = min(100, int(collected / target * 100))
                    progress_value = min(1.0, collected / target)
                    self.progress_label.configure(text=f"수집: {collected}/{target}개 ({progress_percent}%)")
                    self.progress_bar.set(progress_value)  # 0.0 ~ 1.0
                else:
                    self.progress_label.configure(text=f"수집: {collected}개")
                    self.progress_bar.set(0)

            # 통계 패널 업데이트 (숫자 강조)
            self.stats_collected_label.configure(text=f"수집: {collected}개")
            self.stats_skipped_label.configure(text=f"중복: {self.stats['skipped']}개")
            self.stats_speed_label.configure(text=f"속도: {self.stats['speed']:.1f}개/분")

            # 상품 미리보기 업데이트
            if self.stats['last_product']:
                preview_text = self.stats['last_product'][:35] + "..." if len(self.stats['last_product']) > 35 else self.stats['last_product']
                self.stats_preview_label.configure(text=f"최근: {preview_text}")
            else:
                self.stats_preview_label.configure(text="최근: -")

        # 1초마다 재호출
        self.window.after(1000, self._update_stats_display)

    def _toggle_count_entry(self):
        """수집 모드에 따라 개수 입력 필드 활성화/비활성화"""
        if self.collection_mode.get() == "test":
            self.product_count_entry.configure(state="normal")
        else:
            self.product_count_entry.configure(state="disabled")

    def _log(self, message, level="normal"):
        """
        로그 메시지 추가 (이모지 제거, 레벨 필터링)

        Args:
            message: 로그 메시지
            level: "normal" (중요), "verbose" (상세) - normal은 항상 표시됨
        """
        # 로그 레벨 필터링
        if self.log_level == "normal" and level == "verbose":
            return  # 간결 모드에서 상세 로그는 스킵

        clean_message = remove_emojis(message)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {clean_message}\n"
        self.log_queue.put(log_entry)

        # 상품 수집 로그에서 상품명 추출 (미리보기용)
        if "[" in clean_message and "]" in clean_message and "수집" in clean_message:
            try:
                # "[상품명] - 태그 X개" 패턴에서 상품명 추출
                start = clean_message.find("[") + 1
                end = clean_message.find("]")
                if start < end:
                    product_name = clean_message[start:end]
                    if len(product_name) > 5 and product_name not in ["로그 모드", "완료", "시작"]:
                        self.stats['last_product'] = product_name
            except:
                pass

    def _update_log_from_queue(self):
        """큐에서 로그 메시지를 가져와 UI 업데이트 (메모리 누수 방지)"""
        try:
            while True:
                log_entry = self.log_queue.get_nowait()
                self.log_text.insert("end", log_entry)
                self.log_text.see("end")
        except queue.Empty:
            pass
        finally:
            # 메모리 누수 방지: 줄 수 + 문자 수 제한
            try:
                line_count = int(self.log_text.index('end-1c').split('.')[0])

                # 1. 줄 수 제한 (1000줄 초과 시 오래된 500줄 삭제)
                if line_count > 1000:
                    self.log_text.delete('1.0', '501.0')
                    line_count = int(self.log_text.index('end-1c').split('.')[0])

                # 2. 문자 수 제한 (500KB 초과 시 절반 삭제)
                content = self.log_text.get('1.0', 'end-1c')
                content_size = len(content.encode('utf-8'))
                if content_size > 500 * 1024:  # 500KB
                    half_line = max(1, line_count // 2)
                    self.log_text.delete('1.0', f'{half_line}.0')
            except:
                pass

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
        # 무한 모드는 팝업 없이 바로 시작 (사용자 편의성)

        # 통계 초기화
        self.stats = {
            'collected': 0,
            'skipped': 0,
            'failed': 0,
            'speed': 0.0,
            'start_time': datetime.now(),
            'last_product': None
        }

        # UI 상태 변경 (색상 적용)
        self.is_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text="▶ 수집 중", text_color="#2196F3")  # 파란색, ▶ 기호
        self.progress_label.configure(text="수집: 0개")
        self.progress_bar.set(0)  # 프로그레스 바 초기화

        # 로그 초기화
        self.log_text.delete("1.0", "end")
        self._log("="*60)
        category_name = self.selected_category.get()
        self._log(f"카테고리: {category_name}")
        if is_infinite:
            self._log("전체 상품 수집 시작 (무한 모드)")
            self._log("중단하려면 '수집 중지' 버튼을 클릭하세요")
        else:
            self._log(f"테스트 수집 시작: {product_count}개")
        self._log("="*60)

        # 옵션 출력
        self._log(f"중복 체크: {'예' if self.skip_duplicates_var.get() else '아니오'}")
        self._log(f"JSON 저장: {'예' if self.save_json_var.get() else '아니오'} (디버그용)")
        self._log(f"재개 모드: {'예' if self.resume_var.get() else '아니오 (처음부터 시작)'}")
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

            # 선택된 카테고리 정보 가져오기
            category_name = self.selected_category.get()
            category_id = self.categories.get(category_name, "10000107")

            # 크롤러 생성
            # 무한 모드면 product_count=None (무한 수집)
            actual_count = None if is_infinite else product_count

            # V2 크롤러 사용 (점진적 수집 최적화)
            self.crawler = ProgressiveCrawler(
                product_count=actual_count,
                headless=False,  # 항상 브라우저 보이기 (캡차 해결용)
                category_name=category_name,
                category_id=category_id,
                skip_count=10  # 첫 10개 건너뛰고 11번째부터 수집
            )

            # 크롤러의 print를 가로채서 로그로 리다이렉트
            self._redirect_crawler_logs()

            # 크롤링 실행
            self._log("크롤링 시작...")
            data = loop.run_until_complete(self.crawler.crawl())

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
                self.status_label.configure(text="✓ 수집 완료", text_color="#4CAF50")  # 녹색, ✓ 기호
            else:
                self._log("상품 수집 실패!")
                self.status_label.configure(text="✗ 수집 실패", text_color="#F44336")  # 빨간색, ✗ 기호

        except Exception as e:
            self._log(f"오류 발생: {str(e)}")
            import traceback
            self._log(traceback.format_exc())
            self.status_label.configure(text="오류 발생!")

        finally:
            # UI 상태 복원 (대기 상태로)
            self.is_running = False
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            if not self.crawler or not self.crawler.products_data:
                self.status_label.configure(text="● 대기 중", text_color="white")  # ● 기호

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

    def _copy_log(self):
        """로그 내용을 클립보드에 복사 (WSL 환경 대응)"""
        import subprocess
        import platform

        log_content = self.log_text.get("1.0", "end-1c")

        try:
            # WSL 환경에서는 clip.exe를 사용해 Windows 클립보드에 직접 복사
            if platform.system() == 'Linux' and 'microsoft' in platform.uname().release.lower():
                # WSL 환경 감지
                # clip.exe는 UTF-16LE BOM이 필요함
                process = subprocess.run(
                    ['clip.exe'],
                    input=log_content.encode('utf-16le'),
                    check=True,
                    capture_output=True
                )
                self._log("로그가 클립보드에 복사되었습니다. (Windows 클립보드)")
            else:
                # 일반 Linux/Mac/Windows 환경
                self.window.clipboard_clear()
                self.window.clipboard_append(log_content)
                self._log("로그가 클립보드에 복사되었습니다.")
        except Exception as e:
            self._log(f"클립보드 복사 실패: {str(e)}")

    def _stop_crawling(self):
        """크롤링 중지"""
        if not self.is_running:
            return

        self._log("")
        self._log("중지 요청됨... (현재 상품 수집 완료 후 종료)")
        self.is_running = False

        # 크롤러에도 중지 신호 전달
        if self.crawler:
            self.crawler.should_stop = True

        self.status_label.configure(text="■ 중지 중", text_color="#FF9800")  # 주황색, ■ 기호

    def run(self):
        """GUI 실행"""
        # 메인 루프 시작 (창은 이미 __init__에서 표시됨)
        self.window.mainloop()


def main():
    """메인 함수"""
    app = ProductCollectorGUI()
    app.run()


if __name__ == "__main__":
    main()
