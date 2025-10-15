"""네이버 쇼핑 크롤러 GUI - 트리 구조 카테고리 버전"""
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from datetime import datetime
import queue
import sys
import json
from pathlib import Path

# 인코딩 설정
if sys.platform.startswith('win'):
    import ctypes
    ctypes.windll.kernel32.SetConsoleCP(65001)
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)

# 기본 폰트 설정
DEFAULT_FONT = 'TkDefaultFont'  # 시스템 기본 폰트 사용

class NaverCrawlerTreeGUI:
    """트리 구조로 카테고리를 표시하는 GUI"""

    def __init__(self, root):
        self.root = root
        # 버전 파일에서 읽기
        try:
            with open('VERSION', 'r') as f:
                version = f.read().strip()
        except:
            version = "1.0.0"

        # 영문 타이틀 사용 (한글 깨짐 방지)
        self.root.title(f"Naver Plus Store Crawler v{version}")

        # 플랫폼별 전체화면 설정
        import platform
        system = platform.system()

        if system == 'Windows':
            # Windows에서 최대화
            self.root.state('zoomed')
        else:
            # Linux/Mac에서 최대화
            self.root.attributes('-zoomed', True)
            width = self.root.winfo_screenwidth()
            height = self.root.winfo_screenheight()
            self.root.geometry(f"{width}x{height}+0+0")

        # 전체화면 토글 키 바인딩 (F11)
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.exit_fullscreen)

        # 큐 (스레드 간 통신)
        self.log_queue = queue.Queue()

        # 스타일 설정
        self.setup_styles()

        # GUI 구성
        self.setup_gui()

        # 크롤러 스레드 변수
        self.crawler_thread = None
        self.is_crawling = False

        # 선택된 카테고리 저장
        self.selected_categories = {}  # {main: [sub1, sub2], ...}

        # 카테고리 데이터 로드
        self.load_categories()

        # 로그 업데이트 시작
        self.update_logs()

    def setup_styles(self):
        """GUI 스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')

        # 색상 정의
        self.colors = {
            'bg': '#f0f0f0',
            'primary': '#03C75A',  # 네이버 그린
            'secondary': '#1EC800',
            'danger': '#ff4444',
            'text': '#333333'
        }

        self.root.configure(bg=self.colors['bg'])

    def setup_gui(self):
        """GUI 레이아웃 구성"""
        # 메인 컨테이너
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 타이틀
        try:
            with open('VERSION', 'r') as f:
                version = f.read().strip()
        except:
            version = "1.0.0"

        title_label = tk.Label(
            main_frame,
            text=f"네이버 플러스 스토어 크롤러 v{version}",
            font=(DEFAULT_FONT, 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        )
        title_label.pack(pady=(0, 20))

        # 메인 컨테이너를 좌우로 분할
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 왼쪽: 카테고리 트리
        self.setup_category_tree(content_frame)

        # 오른쪽: 컨트롤 패널 + 로그
        right_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # 상단: 컨트롤 패널
        self.setup_control_panel(right_frame)

        # 중간: 진행 상태
        self.setup_progress_panel(right_frame)

        # 하단: 로그
        self.setup_log_panel(right_frame)

    def setup_category_tree(self, parent):
        """카테고리 트리 설정"""
        tree_frame = tk.LabelFrame(
            parent,
            text="📂 카테고리 선택 (체크박스 클릭)",
            font=(DEFAULT_FONT, 11, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))

        # 트리뷰 생성
        self.tree = ttk.Treeview(tree_frame, selectmode='extended')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 스크롤바
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 열 설정
        self.tree['columns'] = ('selected',)
        self.tree.column('#0', width=250, stretch=True)
        self.tree.column('selected', width=50, stretch=False)
        self.tree.heading('#0', text='카테고리명')
        self.tree.heading('selected', text='선택')

        # 체크박스 이미지 (텍스트로 대체)
        self.tree.tag_configure('selected', foreground=self.colors['primary'], font=(DEFAULT_FONT, 10, 'bold'))
        self.tree.tag_configure('unselected', foreground=self.colors['text'])

        # 클릭 이벤트 바인딩
        self.tree.bind('<ButtonRelease-1>', self.on_tree_click)

        # 버튼 프레임
        button_frame = tk.Frame(tree_frame, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(
            button_frame,
            text="전체 선택",
            command=self.select_all,
            font=(DEFAULT_FONT, 9),
            bg='#666666',
            fg='white',
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_frame,
            text="전체 해제",
            command=self.deselect_all,
            font=(DEFAULT_FONT, 9),
            bg='#666666',
            fg='white',
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_frame,
            text="카테고리 새로고침",
            command=self.refresh_categories,
            font=(DEFAULT_FONT, 9),
            bg=self.colors['secondary'],
            fg='white',
            cursor='hand2'
        ).pack(side=tk.RIGHT, padx=2)

    def load_categories(self):
        """저장된 카테고리 데이터 로드"""
        try:
            # 카테고리 파일 경로 (프로젝트 루트 기준)
            import os
            project_root = Path(__file__).parent.parent.parent
            category_file = project_root / 'data' / 'naver_plus_store_categories.json'

            if category_file.exists():
                with open(category_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.categories_data = data.get('카테고리', {})
                    self.populate_tree()
                    self.add_log(f"✅ 카테고리 데이터 로드 완료 ({len(self.categories_data)}개 메인 카테고리)", 'SUCCESS')
            else:
                # 기본 카테고리 구조
                self.categories_data = {
                    "패션": {
                        "subcategories": ["여성의류", "남성의류", "속옷/잠옷", "신발", "가방", "패션잡화"],
                    },
                    "뷰티": {
                        "subcategories": ["스킨케어", "메이크업", "향수/바디", "헤어케어"],
                    },
                    "식품": {
                        "subcategories": ["과일/채소", "정육/계란", "수산물", "가공식품", "건강식품"],
                    },
                    "가전디지털": {
                        "subcategories": ["TV/모니터", "컴퓨터/노트북", "휴대폰", "주방가전"],
                    },
                    "생활용품": {
                        "subcategories": ["세제/청소용품", "욕실용품", "생활잡화"],
                    }
                }
                self.populate_tree()
                self.add_log("⚠️ 저장된 카테고리 없음. 기본 카테고리 사용", 'WARNING')

        except Exception as e:
            self.add_log(f"❌ 카테고리 로드 오류: {e}", 'ERROR')
            # 오류 시 기본 카테고리 사용
            self.categories_data = {"테스트": {"subcategories": ["서브1", "서브2"]}}
            self.populate_tree()

    def populate_tree(self):
        """트리에 카테고리 데이터 추가"""
        # 기존 항목 제거
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 카테고리 추가
        for main_cat, info in self.categories_data.items():
            # 메인 카테고리 추가
            main_item = self.tree.insert('', 'end', text=f"📁 {main_cat}", values=('□',), tags=('unselected',))

            # 서브 카테고리 추가
            subcategories = info.get('subcategories', [])
            for sub_cat in subcategories:
                self.tree.insert(main_item, 'end', text=f"  • {sub_cat}", values=('□',), tags=('unselected',))

            # 메인 카테고리 펼치기
            self.tree.item(main_item, open=True)

    def on_tree_click(self, event):
        """트리 클릭 이벤트 처리"""
        # 클릭된 위치의 아이템 찾기
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return

        # 선택 상태 토글
        current_value = self.tree.item(item, 'values')[0]
        if current_value == '□':
            # 선택
            self.tree.item(item, values=('☑',), tags=('selected',))
            self.add_selected_category(item)
        else:
            # 해제
            self.tree.item(item, values=('□',), tags=('unselected',))
            self.remove_selected_category(item)

        # 선택된 카테고리 수 업데이트
        self.update_selected_count()

    def add_selected_category(self, item):
        """선택된 카테고리 추가"""
        text = self.tree.item(item, 'text')
        parent = self.tree.parent(item)

        if parent:
            # 서브 카테고리
            parent_text = self.tree.item(parent, 'text')
            main_cat = parent_text.replace('📁 ', '')
            sub_cat = text.replace('  • ', '')

            if main_cat not in self.selected_categories:
                self.selected_categories[main_cat] = []
            if sub_cat not in self.selected_categories[main_cat]:
                self.selected_categories[main_cat].append(sub_cat)
        else:
            # 메인 카테고리 - 모든 서브 카테고리 선택
            main_cat = text.replace('📁 ', '')
            children = self.tree.get_children(item)

            if main_cat not in self.selected_categories:
                self.selected_categories[main_cat] = []

            for child in children:
                child_text = self.tree.item(child, 'text')
                sub_cat = child_text.replace('  • ', '')
                if sub_cat not in self.selected_categories[main_cat]:
                    self.selected_categories[main_cat].append(sub_cat)
                # 서브 카테고리도 선택 표시
                self.tree.item(child, values=('☑',), tags=('selected',))

    def remove_selected_category(self, item):
        """선택 해제된 카테고리 제거"""
        text = self.tree.item(item, 'text')
        parent = self.tree.parent(item)

        if parent:
            # 서브 카테고리
            parent_text = self.tree.item(parent, 'text')
            main_cat = parent_text.replace('📁 ', '')
            sub_cat = text.replace('  • ', '')

            if main_cat in self.selected_categories:
                if sub_cat in self.selected_categories[main_cat]:
                    self.selected_categories[main_cat].remove(sub_cat)
                if not self.selected_categories[main_cat]:
                    del self.selected_categories[main_cat]
        else:
            # 메인 카테고리 - 모든 서브 카테고리 해제
            main_cat = text.replace('📁 ', '')
            if main_cat in self.selected_categories:
                del self.selected_categories[main_cat]

            # 서브 카테고리도 해제 표시
            children = self.tree.get_children(item)
            for child in children:
                self.tree.item(child, values=('□',), tags=('unselected',))

    def select_all(self):
        """전체 선택"""
        for item in self.tree.get_children():
            self.tree.item(item, values=('☑',), tags=('selected',))
            self.add_selected_category(item)
            # 서브 카테고리도 선택
            for child in self.tree.get_children(item):
                self.tree.item(child, values=('☑',), tags=('selected',))
        self.update_selected_count()

    def deselect_all(self):
        """전체 해제"""
        self.selected_categories = {}
        for item in self.tree.get_children():
            self.tree.item(item, values=('□',), tags=('unselected',))
            # 서브 카테고리도 해제
            for child in self.tree.get_children(item):
                self.tree.item(child, values=('□',), tags=('unselected',))
        self.update_selected_count()

    def update_selected_count(self):
        """선택된 카테고리 수 업데이트"""
        total_selected = sum(len(subs) for subs in self.selected_categories.values())

        if total_selected > 0:
            categories_text = []
            for main, subs in self.selected_categories.items():
                if subs:
                    categories_text.append(f"{main}({len(subs)})")

            self.selected_label.config(
                text=f"✅ 선택: {', '.join(categories_text[:3])}{'...' if len(categories_text) > 3 else ''} (총 {total_selected}개)",
                fg=self.colors['primary']
            )
        else:
            self.selected_label.config(
                text="선택된 카테고리: 없음",
                fg=self.colors['danger']
            )

    def refresh_categories(self):
        """카테고리 새로고침 (재수집)"""
        self.add_log("🔄 카테고리 새로고침 시작...", 'INFO')

        # 카테고리 수집 스레드 시작
        thread = threading.Thread(target=self.collect_categories_thread, daemon=True)
        thread.start()

    def collect_categories_thread(self):
        """카테고리 수집 스레드"""
        try:
            import asyncio
            from src.utils.category_collector import NaverPlusStoreCategoryCollector

            collector = NaverPlusStoreCategoryCollector()
            asyncio.run(collector.collect_categories())

            # 수집 완료 후 리로드
            self.root.after(0, self.load_categories)
            self.add_log("✅ 카테고리 새로고침 완료!", 'SUCCESS')

        except Exception as e:
            self.add_log(f"❌ 카테고리 수집 오류: {e}", 'ERROR')

    def setup_control_panel(self, parent):
        """컨트롤 패널 설정"""
        control_frame = tk.LabelFrame(
            parent,
            text="크롤링 설정",
            font=(DEFAULT_FONT, 11, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # 선택된 카테고리 표시
        self.selected_label = tk.Label(
            control_frame,
            text="선택된 카테고리: 없음",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg'],
            fg=self.colors['danger']
        )
        self.selected_label.pack(pady=10)

        # 크롤링 옵션
        option_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        option_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(
            option_frame,
            text="크롤링 타입:",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg']
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.crawl_type = tk.StringVar(value="products")

        tk.Radiobutton(
            option_frame,
            text="상품 정보 수집",
            variable=self.crawl_type,
            value="products",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg']
        ).pack(side=tk.LEFT, padx=5)

        tk.Radiobutton(
            option_frame,
            text="카테고리 구조만",
            variable=self.crawl_type,
            value="categories",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg']
        ).pack(side=tk.LEFT, padx=5)

        # 버튼
        button_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        self.start_btn = tk.Button(
            button_frame,
            text="🚀 크롤링 시작",
            command=self.start_crawling,
            font=(DEFAULT_FONT, 11, 'bold'),
            bg=self.colors['primary'],
            fg='white',
            width=20,
            height=2,
            cursor='hand2'
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(
            button_frame,
            text="⏹ 중지",
            command=self.stop_crawling,
            font=(DEFAULT_FONT, 11, 'bold'),
            bg=self.colors['danger'],
            fg='white',
            width=20,
            height=2,
            state=tk.DISABLED,
            cursor='hand2'
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

    def setup_progress_panel(self, parent):
        """진행 상태 패널 설정"""
        progress_frame = tk.LabelFrame(
            parent,
            text="진행 상태",
            font=(DEFAULT_FONT, 11, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        # 상태 정보
        info_frame = tk.Frame(progress_frame, bg=self.colors['bg'])
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        self.status_label = tk.Label(
            info_frame,
            text="상태: 대기 중",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        self.status_label.pack(anchor=tk.W)

        self.current_category_label = tk.Label(
            info_frame,
            text="현재 카테고리: -",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        self.current_category_label.pack(anchor=tk.W)

        self.product_count_label = tk.Label(
            info_frame,
            text="수집된 상품: 0개",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        self.product_count_label.pack(anchor=tk.W)

        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, padx=10, pady=(0, 10))

    def setup_log_panel(self, parent):
        """로그 패널 설정"""
        log_frame = tk.LabelFrame(
            parent,
            text="실행 로그",
            font=(DEFAULT_FONT, 11, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        log_frame.pack(fill=tk.BOTH, expand=True)

        # 로그 컨트롤
        log_control = tk.Frame(log_frame, bg=self.colors['bg'])
        log_control.pack(fill=tk.X, padx=10, pady=(5, 0))

        tk.Button(
            log_control,
            text="로그 지우기",
            command=self.clear_logs,
            font=(DEFAULT_FONT, 9),
            bg='#666666',
            fg='white',
            cursor='hand2'
        ).pack(side=tk.RIGHT)

        # 스크롤 가능한 텍스트 영역
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=60,
            height=12,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#00ff00'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 로그 레벨별 태그 설정
        self.log_text.tag_config('INFO', foreground='#00ff00')
        self.log_text.tag_config('WARNING', foreground='#ffff00')
        self.log_text.tag_config('ERROR', foreground='#ff4444')
        self.log_text.tag_config('SUCCESS', foreground='#00ffff')

    def add_log(self, message, level='INFO'):
        """로그 추가"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        self.log_queue.put((log_entry, level))

    def update_logs(self):
        """로그 업데이트 (메인 스레드)"""
        try:
            while True:
                log_entry, level = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, log_entry, level)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.update_logs)

    def clear_logs(self):
        """로그 지우기"""
        self.log_text.delete(1.0, tk.END)
        self.add_log("로그가 초기화되었습니다.", 'INFO')

    def start_crawling(self):
        """크롤링 시작"""
        if self.is_crawling:
            messagebox.showwarning("경고", "이미 크롤링이 진행 중입니다.")
            return

        # 카테고리가 선택되었는지 확인
        if not self.selected_categories:
            messagebox.showwarning("경고", "최소 1개 이상의 카테고리를 선택해주세요.")
            return

        self.is_crawling = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        # 크롤링 스레드 시작
        crawl_type = self.crawl_type.get()

        self.add_log(f"🚀 크롤링을 시작합니다. (타입: {crawl_type})", 'SUCCESS')

        # 선택된 카테고리 로그
        for main, subs in self.selected_categories.items():
            self.add_log(f"  • {main}: {', '.join(subs)}", 'INFO')

        self.status_label.config(text="상태: 크롤링 중...")

        self.crawler_thread = threading.Thread(
            target=self.run_crawler,
            args=(crawl_type, self.selected_categories),
            daemon=True
        )
        self.crawler_thread.start()

    def stop_crawling(self):
        """크롤링 중지"""
        self.is_crawling = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

        self.add_log("⏹ 크롤링을 중지합니다...", 'WARNING')
        self.status_label.config(text="상태: 중지됨")

    def run_crawler(self, crawl_type, selected_categories):
        """크롤러 실행"""
        try:
            # 크롤러 임포트
            from src.core.crawler import CategoryCrawler

            # 선택된 카테고리를 평면 리스트로 변환
            categories_list = []
            for main, subs in selected_categories.items():
                for sub in subs:
                    categories_list.append(f"{main}/{sub}")

            crawler = CategoryCrawler(
                gui=self,
                headless=False,
                selected_categories=categories_list
            )

            if crawl_type == "categories":
                crawler.crawl_categories_only()
            else:
                crawler.crawl_all()

        except ImportError as e:
            self.add_log(f"❌ 모듈 임포트 오류: {str(e)}", 'ERROR')

        except Exception as e:
            self.add_log(f"❌ 크롤링 중 오류 발생: {str(e)}", 'ERROR')

        finally:
            self.is_crawling = False
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.status_label.config(text="상태: 완료"))

    def update_status(self, category_name=None, product_count=0):
        """상태 업데이트"""
        if category_name:
            self.current_category_label.config(text=f"현재 카테고리: {category_name}")
        self.product_count_label.config(text=f"수집된 상품: {product_count}개")

    def update_progress(self, value):
        """진행률 업데이트"""
        self.progress_var.set(value)

    def toggle_fullscreen(self, event=None):
        """F11 키로 전체화면 토글"""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)
        return "break"

    def exit_fullscreen(self, event=None):
        """ESC 키로 전체화면 종료"""
        self.root.attributes('-fullscreen', False)

        # 플랫폼별 최대화 상태로 돌아가기
        import platform
        if platform.system() == 'Windows':
            self.root.state('zoomed')
        else:
            width = self.root.winfo_screenwidth()
            height = self.root.winfo_screenheight()
            self.root.geometry(f"{width}x{height}+0+0")

        return "break"


def main():
    root = tk.Tk()
    app = NaverCrawlerTreeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()