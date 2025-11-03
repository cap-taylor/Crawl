#!/usr/bin/env python3
"""
네이버 쇼핑 상품 수집기 GUI (v1.2.0)
SimpleCrawler 기반 - 13개 필드 수집 + DB 직접 저장 + 무한 모드
"""

import customtkinter as ctk
import tkinter as tk
import asyncio
import threading
import queue
from datetime import datetime
from pathlib import Path
from typing import Optional
import json
import sys
import re
import traceback
import logging

# 터미널 디버깅 로거 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # 터미널 출력
        logging.FileHandler('gui_debug.log', encoding='utf-8')  # 파일 저장
    ]
)
logger = logging.getLogger('GUI')

# SimpleCrawler import
sys.path.append(str(Path(__file__).parent))
from src.core.simple_crawler import SimpleCrawler


def get_version():
    """VERSION 파일에서 버전 읽기"""
    try:
        version_file = Path(__file__).parent / "VERSION"
        with open(version_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        logger.warning(f"VERSION 파일 읽기 실패: {e}, 기본 버전 사용")
        return "1.0.0"


def remove_emojis(text):
    """이모지 제거 (customtkinter 렌더링 문제 회피)"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U0001F900-\U0001F9FF"
        "\U0001FA70-\U0001FAFF"
        "\U00002300-\U000023FF"
        "\U00002600-\U000026FF"
        "\U00002B50"
        "\U0000231A-\U0000231B"
        "\U000023E9-\U000023F3"
        "\U000025AA-\U000025AB"
        "\U000025B6"
        "\U000025C0"
        "\U000025FB-\U000025FE"
        "\U00002614-\U00002615"
        "\U0000263A"
        "\U0000267F"
        "\U00002693"
        "\U000026A1"
        "\U000026AA-\U000026AB"
        "\U000026BD-\U000026BE"
        "\U000026C4-\U000026C5"
        "\U000026CE"
        "\U000026D4"
        "\U000026EA"
        "\U000026F2-\U000026F3"
        "\U000026F5"
        "\U000026FA"
        "\U000026FD"
        "\U00002705"
        "\U0000270A-\U0000270B"
        "\U00002728"
        "\U0000274C"
        "\U0000274E"
        "\U00002753-\U00002755"
        "\U00002757"
        "\U00002795-\U00002797"
        "\U000027A1"
        "\U000027B0"
        "\U000027BF"
        "\U00002B1B-\U00002B1C"
        "\U00002B55"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)


class ProductCollectorGUI:
    """상품 수집 GUI - 모든 카테고리 + 무한 모드 + DB 직접 저장"""

    def __init__(self):
        # 버전 로드
        self.version = get_version()

        logger.info("=" * 70)
        logger.info(f"GUI 초기화 시작 (v{self.version})")
        logger.info("=" * 70)

        try:
            self.root = ctk.CTk()
            # self.root.withdraw()  # 창 숨김 제거
            logger.info("✓ CTk 루트 윈도우 생성 완료")

            self.root.title(f"네이버 쇼핑 상품 수집기 v{self.version}")
            logger.info("✓ 윈도우 타이틀 설정 완료")
        except Exception as e:
            logger.error(f"✗ GUI 초기화 실패: {str(e)}")
            logger.error(traceback.format_exc())
            raise

        window_width = 900
        window_height = 750
        self.root.geometry(f"{window_width}x{window_height}+100+50")
        self.root.minsize(800, 650)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 상태 변수
        self.is_running = False
        self.crawler = None
        self.log_queue = queue.Queue()
        self.stats = {
            'collected': 0,
            'saved': 0,
            'duplicates': 0,
            'errors': 0,
            'start_time': None,
            'last_product': None
        }
        self.recent_products = []  # 최근 10개 상품 저장

        # 카테고리 로드
        self.categories = self._load_categories()

        # UI 구성
        self._create_ui()

        # 타이머
        self.root.after(100, self._update_logs)
        self.root.after(1000, self._update_stats)

        # 창 표시 (강제)
        self.root.update_idletasks()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.lift())
        self.root.after(200, lambda: self.root.focus_force())
        self.root.after(500, lambda: self.root.attributes('-topmost', False))

    def _load_categories(self):
        """카테고리 JSON 파일에서 로드"""
        try:
            json_path = Path(__file__).parent / "data" / "naver_categories_hierarchy.json"
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cat_dict = data.get('카테고리', {})

                # {name: id} 딕셔너리 반환
                return {name: info['id'] for name, info in cat_dict.items()}
        except Exception as e:
            print(f"카테고리 로드 실패: {e}")
            # 기본 카테고리
            return {"여성의류": "10000107"}

    def _create_ui(self):
        """UI 컴포넌트 생성 - 모던 3단 레이아웃 (헤더 | 왼쪽 컨트롤 + 메인 콘텐츠)"""
        # === 색상 팔레트 정의 ===
        self.colors = {
            'bg_dark': '#1a1a1a',
            'bg_card': '#2d2d2d',
            'bg_input': '#252525',
            'accent_blue': '#3b82f6',
            'accent_green': '#10b981',
            'accent_red': '#ef4444',
            'accent_yellow': '#f59e0b',
            'accent_orange': '#fb923c',
            'text_primary': '#ffffff',
            'text_secondary': '#9ca3af',
            'border': '#404040',
            'hover_blue': '#2563eb',
            'hover_green': '#059669',
        }

        # 메인 컨테이너
        main_container = ctk.CTkFrame(self.root, fg_color=self.colors['bg_dark'])
        main_container.pack(fill="both", expand=True)

        # === 1. 헤더 (60px 고정) ===
        self._create_header(main_container)

        # === 2. 콘텐츠 영역 (왼쪽 패널 + 메인 콘텐츠) ===
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # 그리드 설정
        content_frame.grid_columnconfigure(0, weight=0, minsize=280)  # 왼쪽 컨트롤 패널
        content_frame.grid_columnconfigure(1, weight=1)  # 메인 콘텐츠
        content_frame.grid_rowconfigure(0, weight=1)

        # === 왼쪽: 컨트롤 패널 ===
        self._create_control_panel(content_frame)

        # === 오른쪽: 메인 콘텐츠 ===
        self._create_main_content(content_frame)

    def _create_header(self, parent):
        """헤더 생성 (타이틀 + 버전 + 상태)"""
        header = ctk.CTkFrame(parent, fg_color=self.colors['bg_card'], height=60, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        # 왼쪽: 타이틀 + 서브타이틀
        left_frame = ctk.CTkFrame(header, fg_color="transparent")
        left_frame.pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(
            left_frame,
            text="네이버 쇼핑 상품 수집기",
            font=("Arial", 20, "bold"),
            text_color=self.colors['text_primary']
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_frame,
            text=f"v{self.version} - 13개 필드 수집 + PostgreSQL 직접 저장",
            font=("Arial", 10),
            text_color=self.colors['text_secondary']
        ).pack(anchor="w", pady=(2, 0))

        # 오른쪽: 상태 표시
        right_frame = ctk.CTkFrame(header, fg_color="transparent")
        right_frame.pack(side="right", padx=20, pady=10)

        self.header_status = ctk.CTkLabel(
            right_frame,
            text="● 대기 중",
            font=("Arial", 14, "bold"),
            text_color=self.colors['text_secondary']
        )
        self.header_status.pack(anchor="e")

    def _create_control_panel(self, parent):
        """왼쪽 컨트롤 패널 생성"""
        control_panel = ctk.CTkFrame(parent, fg_color=self.colors['bg_card'], corner_radius=8)
        control_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(15, 0))

        control_inner = ctk.CTkFrame(control_panel, fg_color="transparent")
        control_inner.pack(fill="both", expand=True, padx=15, pady=15)

        # 섹션 1: 카테고리 선택
        ctk.CTkLabel(
            control_inner,
            text="수집 카테고리",
            font=("Arial", 13, "bold"),
            text_color=self.colors['text_primary']
        ).pack(anchor="w", pady=(5, 8))  # 위쪽 여백 추가 (0 → 5)

        self.category_var = ctk.StringVar(value="여성의류")
        self.category_dropdown = ctk.CTkOptionMenu(
            control_inner,
            variable=self.category_var,
            values=list(self.categories.keys()),
            width=250,
            height=36,
            font=("Arial", 11),
            fg_color=self.colors['bg_input'],
            button_color=self.colors['accent_blue'],
            button_hover_color=self.colors['hover_blue'],
            dropdown_fg_color=self.colors['bg_card'],
            corner_radius=6
        )
        self.category_dropdown.pack(fill="x", pady=(0, 20))

        # 섹션 2: 수집 모드
        ctk.CTkLabel(
            control_inner,
            text="수집 모드",
            font=("Arial", 13, "bold"),
            text_color=self.colors['text_primary']
        ).pack(anchor="w", pady=(0, 8))

        self.mode_var = ctk.StringVar(value="infinite")

        mode_frame = ctk.CTkFrame(control_inner, fg_color=self.colors['bg_input'], corner_radius=6)
        mode_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkRadioButton(
            mode_frame,
            text="무한 수집 (기본)",
            variable=self.mode_var,
            value="infinite",
            command=self._toggle_count_entry,
            font=("Arial", 11),
            fg_color=self.colors['accent_blue'],
            hover_color=self.colors['hover_blue']
        ).pack(anchor="w", padx=12, pady=(12, 8))

        ctk.CTkRadioButton(
            mode_frame,
            text="개수 지정",
            variable=self.mode_var,
            value="limited",
            command=self._toggle_count_entry,
            font=("Arial", 11),
            fg_color=self.colors['accent_blue'],
            hover_color=self.colors['hover_blue']
        ).pack(anchor="w", padx=12, pady=(0, 8))

        count_input_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        count_input_frame.pack(fill="x", padx=12, pady=(0, 12))

        self.count_entry = ctk.CTkEntry(
            count_input_frame,
            width=80,
            height=32,
            state="disabled",
            font=("Arial", 12),
            fg_color=self.colors['bg_dark'],
            border_color=self.colors['border'],
            corner_radius=4
        )
        self.count_entry.insert(0, "10")
        self.count_entry.pack(side="left")

        ctk.CTkLabel(
            count_input_frame,
            text="개",
            font=("Arial", 11),
            text_color=self.colors['text_secondary']
        ).pack(side="left", padx=8)

        # 섹션 3: 실행 버튼
        self.start_button = ctk.CTkButton(
            control_inner,
            text="▶ 수집 시작",
            command=self._start_collection,
            height=48,
            font=("Arial", 15, "bold"),
            fg_color=self.colors['accent_blue'],
            hover_color=self.colors['hover_blue'],
            corner_radius=8
        )
        self.start_button.pack(fill="x", pady=(0, 10))

        self.stop_button = ctk.CTkButton(
            control_inner,
            text="■ 수집 중지",
            command=self._stop_collection,
            height=48,
            font=("Arial", 15, "bold"),
            fg_color=self.colors['accent_orange'],
            hover_color="#ea580c",
            state="disabled",
            corner_radius=8
        )
        self.stop_button.pack(fill="x")

    def _create_main_content(self, parent):
        """메인 콘텐츠 영역 생성 (통계 대시보드 + 상품 테이블 + 이벤트 로그)"""
        main_content = ctk.CTkFrame(parent, fg_color="transparent")
        main_content.grid(row=0, column=1, sticky="nsew", pady=(15, 0))  # 위쪽 여백 추가

        # 1. 통계 대시보드 (4개 카드)
        self._create_stats_dashboard(main_content)

        # 2. 상품 테이블
        self._create_product_table(main_content)

        # 3. 이벤트 로그 (컴팩트)
        self._create_event_log(main_content)

    def _create_stats_dashboard(self, parent):
        """통계 대시보드 카드 생성"""
        dashboard_frame = ctk.CTkFrame(parent, fg_color="transparent")
        dashboard_frame.pack(fill="x", pady=(15, 15))  # 위쪽 여백 추가 (0 → 15)

        # 4개 카드를 가로로 배치
        cards_container = ctk.CTkFrame(dashboard_frame, fg_color="transparent")
        cards_container.pack(fill="x")

        # 그리드 설정 (4개 균등 분배)
        for i in range(4):
            cards_container.grid_columnconfigure(i, weight=1)

        # 카드 1: 총 수집
        card1 = self._create_stat_card(cards_container, "총 수집", "0개", self.colors['accent_blue'])
        card1.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.stat_collected_label = card1.winfo_children()[1]

        # 카드 2: DB 저장
        card2 = self._create_stat_card(cards_container, "DB 저장", "0개 (0%)", self.colors['accent_green'])
        card2.grid(row=0, column=1, sticky="ew", padx=4)
        self.stat_saved_label = card2.winfo_children()[1]

        # 카드 3: 중복
        card3 = self._create_stat_card(cards_container, "중복", "0개 (0%)", self.colors['accent_yellow'])
        card3.grid(row=0, column=2, sticky="ew", padx=4)
        self.stat_dup_label = card3.winfo_children()[1]

        # 카드 4: 수집 속도
        card4 = self._create_stat_card(cards_container, "수집 속도", "0개/분\n0분 0초", self.colors['accent_blue'])
        card4.grid(row=0, column=3, sticky="ew", padx=(8, 0))
        self.stat_speed_label = card4.winfo_children()[1]

    def _create_stat_card(self, parent, title, value, color):
        """통계 카드 생성 (고정 높이)"""
        card = ctk.CTkFrame(
            parent,
            fg_color=self.colors['bg_card'],
            corner_radius=8,
            border_width=1,
            border_color=self.colors['border'],
            height=90  # 고정 높이
        )
        card.pack_propagate(False)  # 자식 위젯 크기에 맞춰 늘어나지 않음

        # 타이틀
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Arial", 11),
            text_color=self.colors['text_secondary']
        )
        title_label.pack(pady=(10, 2))

        # 값
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("Arial", 16, "bold"),  # 18 → 16 (약간 축소)
            text_color=color,
            justify="center"
        )
        value_label.pack(pady=(0, 10))

        return card

    def _create_product_table(self, parent):
        """상품 테이블 생성 (최근 10개)"""
        table_container = ctk.CTkFrame(parent, fg_color=self.colors['bg_card'], corner_radius=8)
        table_container.pack(fill="both", expand=True, pady=(0, 15))

        # 헤더
        table_header = ctk.CTkFrame(table_container, fg_color="transparent")
        table_header.pack(fill="x", padx=15, pady=(12, 8))

        ctk.CTkLabel(
            table_header,
            text="최근 수집 상품 (최대 10개)",
            font=("Arial", 13, "bold"),
            text_color=self.colors['text_primary']
        ).pack(side="left")

        # 테이블 스크롤 프레임
        table_scroll_frame = ctk.CTkScrollableFrame(
            table_container,
            fg_color=self.colors['bg_dark'],
            corner_radius=6
        )
        table_scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 12))

        # 마우스 휠 바인딩 (상품 테이블)
        self._bind_mousewheel(table_scroll_frame)

        # 테이블 헤더 (고정)
        headers = ["#", "상품명", "가격", "브랜드", "태그", "상태"]
        header_widths = [30, 280, 90, 80, 50, 50]

        header_row = ctk.CTkFrame(table_scroll_frame, fg_color=self.colors['bg_input'], corner_radius=0)
        header_row.pack(fill="x", pady=0)

        for i, (header, width) in enumerate(zip(headers, header_widths)):
            ctk.CTkLabel(
                header_row,
                text=header,
                font=("Arial", 10, "bold"),
                text_color=self.colors['text_secondary'],
                width=width,
                anchor="w" if i > 0 else "center"
            ).pack(side="left", padx=(8 if i == 0 else 4))

        # 테이블 바디 (동적으로 채워질 영역)
        self.table_body = table_scroll_frame

    def _create_event_log(self, parent):
        """이벤트 로그 생성 (에러/경고만)"""
        log_container = ctk.CTkFrame(parent, fg_color=self.colors['bg_card'], corner_radius=8)
        log_container.pack(fill="both", expand=True)

        # 헤더
        log_header = ctk.CTkFrame(log_container, fg_color="transparent")
        log_header.pack(fill="x", padx=15, pady=(12, 8))

        ctk.CTkLabel(
            log_header,
            text="이벤트 로그 (중요 이벤트만)",
            font=("Arial", 13, "bold"),
            text_color=self.colors['text_primary']
        ).pack(side="left")

        # 로그 복사 버튼
        ctk.CTkButton(
            log_header,
            text="복사",
            command=self._copy_logs,
            width=60,
            height=28,
            font=("Arial", 10),
            fg_color=self.colors['bg_input'],
            hover_color=self.colors['border'],
            corner_radius=6
        ).pack(side="right")

        # 로그 텍스트박스
        self.log_text = ctk.CTkTextbox(
            log_container,
            font=("Consolas", 10),
            fg_color=self.colors['bg_dark'],
            corner_radius=6,
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 12))

        # 마우스 휠 바인딩 (이벤트 로그)
        self._bind_mousewheel(self.log_text)

    def _toggle_count_entry(self):
        """개수 입력 필드 활성화/비활성화"""
        if self.mode_var.get() == "limited":
            self.count_entry.configure(state="normal")
        else:
            self.count_entry.configure(state="disabled")

    def _log(self, message: str):
        """로그 메시지 추가 (중요 이벤트만)"""
        clean_msg = remove_emojis(message)
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 중요 이벤트만 로그에 표시
        important_keywords = ["오류", "에러", "실패", "경고", "시작", "완료", "중지", "카테고리", "모드"]
        is_important = any(keyword in clean_msg for keyword in important_keywords) or clean_msg.startswith("=")

        if is_important:
            self.log_queue.put(f"[{timestamp}] {clean_msg}")

    def _add_product_to_table(self, product_data: dict):
        """상품 테이블에 행 추가 (중복 체크 + 깜빡임 방지)"""
        # product_id로 중복 체크
        product_id = product_data.get('product_id')
        if product_id and any(p.get('product_id') == product_id for p in self.recent_products):
            return  # 이미 추가된 상품은 스킵

        # 최근 10개 초과 시 가장 오래된 것 제거
        if len(self.recent_products) >= 10:
            self.recent_products.pop(0)
            # 가장 아래 행 제거 (헤더는 children[0])
            children = self.table_body.winfo_children()[1:]
            if children:
                children[-1].destroy()

        self.recent_products.append(product_data)

        # 새 행만 추가 (맨 위에 삽입, 전체 다시 그리지 않음)
        self._add_single_row_at_top(product_data)

    def _add_single_row_at_top(self, product: dict):
        """테이블 맨 위에 새 행 1개만 추가 (아코디언 방식)"""
        # 상태에 따른 색상
        status = product.get('_db_status', 'unknown')
        if status == 'saved':
            status_text = "OK"
            status_color = self.colors['accent_green']
        elif status == 'skipped':
            status_text = "DUP"
            status_color = self.colors['accent_yellow']
        else:
            status_text = "ERR"
            status_color = self.colors['accent_red']

        # 컨테이너 프레임 (행 + 상세 정보)
        container_frame = ctk.CTkFrame(self.table_body, fg_color="transparent", corner_radius=0)
        container_frame.pack(fill="x", pady=1, after=self.table_body.winfo_children()[0])

        # 행 프레임 (클릭 가능)
        row_frame = ctk.CTkFrame(container_frame, fg_color=self.colors['bg_input'], corner_radius=0)
        row_frame.pack(fill="x")

        # 인덱스 계산
        row_index = len(self.recent_products)

        # 컬럼 데이터
        product_name = (product.get('product_name') or 'N/A')[:30]
        price = f"{product.get('price', 0):,}원" if product.get('price') else "N/A"
        brand = (product.get('brand_name') or 'N/A')[:10]
        tag_count = f"{len(product.get('search_tags', []))}개"

        row_data = [str(row_index), product_name, price, brand, tag_count, status_text]
        row_widths = [30, 280, 90, 80, 50, 50]
        row_colors = [self.colors['text_secondary'], self.colors['text_primary'],
                     self.colors['text_primary'], self.colors['text_secondary'],
                     self.colors['text_secondary'], status_color]

        # 상세 정보 프레임 (초기에는 숨김) - 먼저 생성
        detail_frame = ctk.CTkFrame(container_frame, fg_color=self.colors['bg_dark'], corner_radius=4)
        detail_frame.pack_forget()  # 초기 숨김

        # 토글 상태 저장
        is_expanded = [False]

        # 클릭 이벤트 (아코디언 토글) - for 루프 전에 정의
        def toggle_detail(event=None):
            if is_expanded[0]:
                detail_frame.pack_forget()
                is_expanded[0] = False
            else:
                detail_frame.pack(fill="x", pady=(0, 2))
                is_expanded[0] = True

        # 행 데이터 레이블 생성
        for j, (data, width, color) in enumerate(zip(row_data, row_widths, row_colors)):
            # CTkLabel로 복원 (깔끔한 UI)
            label = ctk.CTkLabel(
                row_frame,
                text=data,
                font=("Arial", 9),
                text_color=color,
                width=width,
                anchor="w" if j > 0 else "center"
            )
            label.pack(side="left", padx=(8 if j == 0 else 4))

            # 우클릭 메뉴 바인딩
            label.bind("<Button-3>", lambda e, d=data: self._show_copy_menu(e, d))
            label.bind("<Button-1>", toggle_detail)  # 이제 정의됨

        # 상세 정보 내용 (CTkLabel + 우클릭 메뉴)
        detail_text = self._create_product_detail_text(product)
        detail_label = ctk.CTkLabel(
            detail_frame,
            text=detail_text,
            font=("Arial", 9),
            text_color=self.colors['text_secondary'],
            justify="left",
            anchor="nw"
        )
        detail_label.pack(fill="both", padx=15, pady=8)

        # 상세 정보 우클릭 메뉴
        detail_label.bind("<Button-3>", lambda e: self._show_copy_menu(e, detail_text, is_multiline=True))

        # 행 프레임 클릭 이벤트
        row_frame.bind("<Button-1>", toggle_detail)
        row_frame.bind("<Button-3>", lambda e: self._show_copy_menu(e, self._create_product_summary(product), is_multiline=True))

    def _create_product_summary(self, product: dict) -> str:
        """상품 요약 정보 생성 (행 전체 복사용)"""
        product_name = product.get('product_name') or 'N/A'
        price = f"{product.get('price', 0):,}원" if product.get('price') else "N/A"
        brand = product.get('brand_name') or 'N/A'
        tag_count = len(product.get('search_tags', []))
        status = product.get('_db_status', 'unknown')

        return f"상품명: {product_name}\n가격: {price}\n브랜드: {brand}\n태그: {tag_count}개\nDB 상태: {status}"

    def _create_product_detail_text(self, product: dict) -> str:
        """상품 상세 정보 텍스트 생성"""
        lines = []

        # 1순위 정보
        lines.append(f"상품명: {product.get('product_name') or 'N/A'}")
        lines.append(f"카테고리: {product.get('category_name') or 'N/A'}")

        # 2순위 정보
        price = product.get('price')
        lines.append(f"가격: {price:,}원" if price else "가격: N/A")
        lines.append(f"평점: {product.get('rating') or 'N/A'} / 5.0")
        lines.append(f"상품 URL: {product.get('product_url') or 'N/A'}")

        # 3순위 정보
        lines.append(f"브랜드: {product.get('brand_name') or 'N/A'}")
        discount = product.get('discount_rate')
        lines.append(f"할인율: {discount}%" if discount else "할인율: 없음")
        lines.append(f"리뷰 수: {product.get('review_count') or 0}개")

        # 검색 태그
        tags = product.get('search_tags', [])
        if tags:
            tags_str = ", ".join(tags[:10])  # 최대 10개
            lines.append(f"검색 태그 ({len(tags)}개): {tags_str}")
        else:
            lines.append("검색 태그: 없음")

        # 수집 시간
        crawled_at = product.get('crawled_at')
        if crawled_at:
            lines.append(f"수집 시간: {crawled_at}")

        return "\n".join(lines)

    def _show_copy_menu(self, event, text: str, is_multiline: bool = False):
        """우클릭 메뉴 표시 (복사 기능)"""
        menu = tk.Menu(self.root, tearoff=0)

        # 복사 함수 (메뉴 자동 닫기 포함)
        def copy_and_close():
            self._copy_to_clipboard(text)
            menu.unpost()  # 메뉴 닫기
            menu.destroy()  # 메뉴 파괴

        if is_multiline:
            menu.add_command(label="전체 복사", command=copy_and_close)
        else:
            menu.add_command(label="복사", command=copy_and_close)

        # 메뉴 표시 (포커스 강탈 없이)
        menu.tk_popup(event.x_root, event.y_root)

        # 메뉴 외부 클릭 시 자동 닫기
        menu.bind("<FocusOut>", lambda e: menu.unpost())

    def _copy_to_clipboard(self, text: str):
        """클립보드에 텍스트 복사"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()  # 클립보드 업데이트
            print(f"[복사] 클립보드에 복사됨 ({len(text)}자)")
        except Exception as e:
            print(f"[복사 오류] {str(e)}")

    def _refresh_product_table(self):
        """상품 테이블 다시 그리기 (전체 재생성)"""
        # 기존 행 제거 (헤더 제외)
        for widget in self.table_body.winfo_children()[1:]:  # 첫 번째는 헤더
            widget.destroy()

        # 최근 상품들을 역순으로 표시 (최신이 위로)
        for i, product in enumerate(reversed(self.recent_products)):
            row_num = i + 1

            # 상태에 따른 색상
            status = product.get('_db_status', 'unknown')
            if status == 'saved':
                status_text = "OK"
                status_color = self.colors['accent_green']
            elif status == 'skipped':
                status_text = "DUP"
                status_color = self.colors['accent_yellow']
            else:
                status_text = "ERR"
                status_color = self.colors['accent_red']

            # 행 프레임
            row_bg = self.colors['bg_input'] if i % 2 == 0 else self.colors['bg_dark']
            row_frame = ctk.CTkFrame(self.table_body, fg_color=row_bg, corner_radius=0)
            row_frame.pack(fill="x", pady=1)

            # 컬럼 데이터
            product_name = product.get('product_name', 'N/A')[:30]
            price = f"{product.get('price', 0):,}원" if product.get('price') else "N/A"
            brand = product.get('brand_name', 'N/A')[:10]
            tag_count = f"{len(product.get('search_tags', []))}개"

            row_data = [str(row_num), product_name, price, brand, tag_count, status_text]
            row_widths = [30, 280, 90, 80, 50, 50]
            row_colors = [self.colors['text_secondary'], self.colors['text_primary'],
                         self.colors['text_primary'], self.colors['text_secondary'],
                         self.colors['text_secondary'], status_color]

            for j, (data, width, color) in enumerate(zip(row_data, row_widths, row_colors)):
                ctk.CTkLabel(
                    row_frame,
                    text=data,
                    font=("Arial", 9),
                    text_color=color,
                    width=width,
                    anchor="w" if j > 0 else "center"
                ).pack(side="left", padx=(8 if j == 0 else 4))

    def _update_logs(self):
        """로그 큐에서 메시지 가져와서 표시"""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_text.insert("end", msg + "\n")
                self.log_text.see("end")
        except queue.Empty:
            pass

        # 로그 크기 제한
        try:
            line_count = int(self.log_text.index('end-1c').split('.')[0])
            if line_count > 1000:
                self.log_text.delete('1.0', '501.0')
        except:
            pass

        self.root.after(100, self._update_logs)

    def _update_stats(self):
        """통계 업데이트 - 대시보드 카드"""
        if self.is_running and self.crawler:
            # 크롤러 데이터 추출
            products = self.crawler.products_data if self.crawler.products_data else []
            collected = len(products)

            # DB 상태별 카운트
            saved = sum(1 for p in products if p.get('_db_status') == 'saved')
            duplicates = sum(1 for p in products if p.get('_db_status') == 'skipped')
            errors = sum(1 for p in products if p.get('_db_status') == 'error')

            # 통계 업데이트
            self.stats['collected'] = collected
            self.stats['saved'] = saved
            self.stats['duplicates'] = duplicates
            self.stats['errors'] = errors

            # 속도 및 시간 계산
            if self.stats['start_time']:
                elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                elapsed_min = elapsed / 60
                speed = collected / elapsed_min if elapsed_min > 0 else 0.0

                # 시간 포맷
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                time_str = f"{minutes}분 {seconds}초"
            else:
                speed = 0.0
                time_str = "0분 0초"

            # 대시보드 카드 업데이트
            self.stat_collected_label.configure(text=f"{collected}개")

            saved_pct = (saved / collected * 100) if collected > 0 else 0
            self.stat_saved_label.configure(text=f"{saved}개 ({saved_pct:.1f}%)")

            dup_pct = (duplicates / collected * 100) if collected > 0 else 0
            self.stat_dup_label.configure(text=f"{duplicates}개 ({dup_pct:.1f}%)")

            self.stat_speed_label.configure(text=f"{speed:.1f}개/분\n{time_str}")

            # 헤더 상태 업데이트
            self.header_status.configure(
                text=f"● 수집 중 ({collected}개)",
                text_color=self.colors['accent_blue']
            )

            # 상품 테이블에 새 상품 추가
            if products and len(products) > len(self.recent_products):
                new_product = products[-1]
                self._add_product_to_table(new_product)

        self.root.after(1000, self._update_stats)

    def _start_collection(self):
        """수집 시작"""
        if self.is_running:
            return

        # 개수 검증 (제한 모드일 때만)
        product_count = None
        if self.mode_var.get() == "limited":
            try:
                product_count = int(self.count_entry.get())
                if product_count <= 0:
                    raise ValueError
            except:
                self._log("오류: 올바른 수집 개수를 입력하세요")
                return

        # 초기화
        self.is_running = True
        self.stats = {
            'collected': 0,
            'saved': 0,
            'duplicates': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'last_product': None
        }
        self.recent_products = []

        # UI 상태
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.header_status.configure(
            text="● 수집 준비 중...",
            text_color=self.colors['accent_yellow']
        )

        # 로그 초기화
        self.log_text.delete("1.0", "end")
        self._log("="*60)
        category_name = self.category_var.get()
        self._log(f"카테고리: {category_name}")
        if product_count:
            self._log(f"수집 모드: 개수 지정 ({product_count}개)")
        else:
            self._log(f"수집 모드: 무한 (중지 버튼으로 멈춤)")
        self._log("="*60)

        # 별도 스레드에서 실행
        thread = threading.Thread(
            target=self._run_crawler,
            args=(category_name, product_count),
            daemon=True
        )
        thread.start()

    def _stop_collection(self):
        """수집 중지"""
        if self.crawler:
            self.crawler.should_stop = True
            self._log("중지 요청... (현재 상품 완료 후 종료)")
            self.header_status.configure(
                text="● 중지 중...",
                text_color=self.colors['accent_orange']
            )

    def _copy_logs(self):
        """로그 내용을 클립보드에 복사"""
        try:
            # 로그 내용 가져오기
            log_content = self.log_text.get("1.0", "end-1c")

            if not log_content.strip():
                self._log("복사할 로그가 없습니다")
                return

            # 클립보드 복사 (다른 GUI와 격리된 안전한 방식)
            # self.root.update() 사용 금지 - 다른 GUI 이벤트 루프 간섭 방지!
            self.root.clipboard_clear()
            self.root.clipboard_append(log_content)
            # update_idletasks()만 사용 - 현재 GUI만 영향
            self.root.update_idletasks()

            logger.info(f"로그 복사 성공: {len(log_content)} 문자")

            # 임시 메시지 표시
            original_text = self.header_status.cget("text")
            original_color = self.header_status.cget("text_color")
            self.header_status.configure(text="● 로그 복사 완료!", text_color=self.colors['accent_green'])
            self.root.after(2000, lambda: self.header_status.configure(text=original_text, text_color=original_color))

        except Exception as e:
            error_msg = f"로그 복사 실패: {str(e)}"
            self._log(error_msg)
            logger.error("=" * 70)
            logger.error("✗ 로그 복사 오류!")
            logger.error(f"오류 타입: {type(e).__name__}")
            logger.error(f"오류 메시지: {str(e)}")
            logger.error(traceback.format_exc())
            logger.error("=" * 70)

    def _run_crawler(self, category_name: str, product_count: Optional[int]):
        """크롤러 실행"""
        logger.info("=" * 70)
        logger.info(f"크롤러 실행 시작: 카테고리={category_name}, 개수={product_count}")
        logger.info("=" * 70)

        try:
            logger.debug("AsyncIO 이벤트 루프 생성 중...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.debug("✓ 이벤트 루프 생성 완료")

            category_id = self.categories.get(category_name, "10000107")
            logger.info(f"카테고리 ID: {category_id}")

            logger.debug("SimpleCrawler 인스턴스 생성 중...")
            self.crawler = SimpleCrawler(
                category_name=category_name,
                category_id=category_id,
                product_count=product_count,  # None = 무한
                headless=False,
                save_to_db=True  # DB 직접 저장
            )
            logger.debug("✓ SimpleCrawler 생성 완료")

            # 로그 리다이렉트 (인스턴스별 격리)
            import io
            import sys as sys_module

            class LogRedirect(io.TextIOBase):
                def __init__(self, logger):
                    self.logger = logger
                def write(self, text):
                    if text.strip():
                        self.logger(text.strip())
                    return len(text)

            # 원본 stdout 백업
            logger.debug("stdout 리다이렉트 설정 중...")
            original_stdout = sys_module.stdout
            sys_module.stdout = LogRedirect(self._log)
            logger.debug("✓ stdout 리다이렉트 완료")

            # 크롤링 실행
            logger.info("크롤링 실행 시작...")
            products = loop.run_until_complete(self.crawler.crawl())
            logger.info(f"크롤링 완료: {len(products) if products else 0}개 수집")

            # 결과
            if products:
                self._log(f"수집 완료! 총 {len(products)}개 상품 → DB 저장됨")
                self.header_status.configure(
                    text=f"● 완료 ({len(products)}개)",
                    text_color=self.colors['accent_green']
                )
                logger.info(f"✓ 수집 성공: {len(products)}개")
            else:
                self._log("수집된 상품이 없습니다")
                self.header_status.configure(
                    text="● 실패",
                    text_color=self.colors['accent_red']
                )
                logger.warning("[!] 수집 실패: 0개")

        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()

            # GUI 로그
            self._log(f"오류 발생: {error_msg}")
            self.header_status.configure(
                text="● 오류 발생",
                text_color=self.colors['accent_red']
            )

            # 터미널 디버깅 로그
            logger.error("=" * 70)
            logger.error("✗ 크롤러 실행 중 오류 발생!")
            logger.error("=" * 70)
            logger.error(f"오류 타입: {type(e).__name__}")
            logger.error(f"오류 메시지: {error_msg}")
            logger.error("\n스택 트레이스:")
            logger.error(error_trace)
            logger.error("=" * 70)

        finally:
            # stdout 복원 (GUI 격리)
            logger.debug("stdout 복원 중...")
            sys_module.stdout = original_stdout
            logger.debug("✓ stdout 복원 완료")

            self.is_running = False
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            logger.info("크롤러 종료 완료")

    def _bind_mousewheel(self, widget):
        """마우스 휠 바인딩 (리눅스/Windows 호환)"""
        def on_mousewheel(event):
            # Linux (event.num)
            if event.num == 4:
                widget._parent_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                widget._parent_canvas.yview_scroll(1, "units")
            # Windows/macOS (event.delta)
            elif hasattr(event, 'delta'):
                widget._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # CTkScrollableFrame의 경우
        if hasattr(widget, '_parent_canvas'):
            widget.bind("<Button-4>", on_mousewheel)  # Linux scroll up
            widget.bind("<Button-5>", on_mousewheel)  # Linux scroll down
            widget.bind("<MouseWheel>", on_mousewheel)  # Windows/macOS
        # CTkTextbox의 경우 (이미 내장 스크롤 지원)
        else:
            # Textbox는 기본 휠 지원됨, 추가 바인딩 불필요
            pass

    def run(self):
        """GUI 실행"""
        logger.info("GUI 메인 루프 시작")
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error("=" * 70)
            logger.error("✗ GUI 메인 루프 오류!")
            logger.error("=" * 70)
            logger.error(f"오류 타입: {type(e).__name__}")
            logger.error(f"오류 메시지: {str(e)}")
            logger.error("\n스택 트레이스:")
            logger.error(traceback.format_exc())
            logger.error("=" * 70)
            raise


def main():
    """메인 함수"""
    logger.info("=" * 70)
    logger.info("프로그램 시작")
    logger.info("=" * 70)

    try:
        logger.info("ProductCollectorGUI 생성 중...")
        app = ProductCollectorGUI()
        logger.info("✓ GUI 생성 완료")

        logger.info("GUI 실행 중...")
        app.run()
        logger.info("✓ GUI 정상 종료")

    except KeyboardInterrupt:
        logger.warning("\n사용자가 프로그램을 중단했습니다 (Ctrl+C)")

    except Exception as e:
        logger.error("=" * 70)
        logger.error("✗ 프로그램 실행 중 치명적 오류!")
        logger.error("=" * 70)
        logger.error(f"오류 타입: {type(e).__name__}")
        logger.error(f"오류 메시지: {str(e)}")
        logger.error("\n스택 트레이스:")
        logger.error(traceback.format_exc())
        logger.error("=" * 70)
        logger.error("\n디버깅 정보:")
        logger.error(f"- 로그 파일: gui_debug.log")
        logger.error(f"- Python 버전: {sys.version}")
        logger.error(f"- customtkinter 버전: {ctk.__version__}")
        logger.error("=" * 70)
        raise

    finally:
        logger.info("프로그램 종료")


if __name__ == "__main__":
    main()
