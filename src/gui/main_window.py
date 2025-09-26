"""네이버 쇼핑 크롤러 GUI"""
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from datetime import datetime
import queue
import sys
import locale

# 인코딩 설정
if sys.platform.startswith('win'):
    import ctypes
    ctypes.windll.kernel32.SetConsoleCP(65001)
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)

# 기본 폰트 설정
DEFAULT_FONT = 'TkDefaultFont'  # 시스템 기본 폰트 사용

class NaverCrawlerGUI:
    def __init__(self, root):
        self.root = root
        # 버전 파일에서 읽기
        try:
            with open('VERSION', 'r') as f:
                version = f.read().strip()
        except:
            version = "1.0.0"

        # 영문 타이틀 사용 (한글 깨짐 방지)
        self.root.title(f"Naver Shopping Crawler v{version}")
        self.root.geometry("900x700")

        # 큐 (스레드 간 통신)
        self.log_queue = queue.Queue()

        # 스타일 설정
        self.setup_styles()

        # GUI 구성
        self.setup_gui()

        # 크롤러 스레드 변수
        self.crawler_thread = None
        self.is_crawling = False

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
        # 버전 정보 포함
        try:
            with open('VERSION', 'r') as f:
                version = f.read().strip()
        except:
            version = "1.0.0"

        title_label = tk.Label(
            main_frame,
            text=f"네이버 쇼핑 크롤러 v{version}",
            font=(DEFAULT_FONT, 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        )
        title_label.pack(pady=(0, 20))

        # 상단 프레임 - 컨트롤 패널
        self.setup_control_panel(main_frame)

        # 중간 프레임 - 진행 상태
        self.setup_progress_panel(main_frame)

        # 하단 프레임 - 로그
        self.setup_log_panel(main_frame)

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

        # 첫 번째 행 - 크롤링 타입 선택
        type_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        type_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(
            type_frame,
            text="크롤링 타입:",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg']
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.crawl_type = tk.StringVar(value="categories")

        tk.Radiobutton(
            type_frame,
            text="카테고리만 수집",
            variable=self.crawl_type,
            value="categories",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg']
        ).pack(side=tk.LEFT, padx=5)

        tk.Radiobutton(
            type_frame,
            text="카테고리 + 상품 수집",
            variable=self.crawl_type,
            value="all",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg']
        ).pack(side=tk.LEFT, padx=5)

        # 두 번째 행 - 버튼
        button_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.start_btn = tk.Button(
            button_frame,
            text="크롤링 시작",
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
            text="중지",
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

        self.clear_btn = tk.Button(
            button_frame,
            text="로그 지우기",
            command=self.clear_logs,
            font=(DEFAULT_FONT, 10),
            bg='#666666',
            fg='white',
            width=15,
            height=2,
            cursor='hand2'
        )
        self.clear_btn.pack(side=tk.RIGHT, padx=5)

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

        # 왼쪽 - 현재 상태
        left_frame = tk.Frame(info_frame, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_label = tk.Label(
            left_frame,
            text="상태: 대기 중",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        self.status_label.pack(anchor=tk.W)

        self.current_category_label = tk.Label(
            left_frame,
            text="현재 카테고리: -",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        self.current_category_label.pack(anchor=tk.W)

        # 오른쪽 - 통계
        right_frame = tk.Frame(info_frame, bg=self.colors['bg'])
        right_frame.pack(side=tk.RIGHT)

        self.category_count_label = tk.Label(
            right_frame,
            text="수집된 카테고리: 0개",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        self.category_count_label.pack(anchor=tk.E)

        self.product_count_label = tk.Label(
            right_frame,
            text="수집된 상품: 0개",
            font=(DEFAULT_FONT, 10),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        self.product_count_label.pack(anchor=tk.E)

        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=300,
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

        # 스크롤 가능한 텍스트 영역
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=80,
            height=15,
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

        self.is_crawling = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        # 크롤링 스레드 시작
        crawl_type = self.crawl_type.get()

        self.add_log(f"크롤링을 시작합니다. (타입: {crawl_type})", 'SUCCESS')
        self.status_label.config(text="상태: 크롤링 중...")

        self.crawler_thread = threading.Thread(
            target=self.run_crawler,
            args=(crawl_type,),
            daemon=True
        )
        self.crawler_thread.start()

    def stop_crawling(self):
        """크롤링 중지"""
        self.is_crawling = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

        self.add_log("크롤링을 중지합니다...", 'WARNING')
        self.status_label.config(text="상태: 중지됨")

    def run_crawler(self, crawl_type):
        """Run crawler in separate thread"""
        try:
            # Import crawler from proper location
            from src.core.crawler import CategoryCrawler

            crawler = CategoryCrawler(gui=self, headless=False)  # 항상 False (봇 차단 방지)

            if crawl_type == "categories":
                crawler.crawl_categories_only()
            else:
                crawler.crawl_all()

        except ImportError as e:
            error_msg = f"모듈 임포트 오류: {str(e)}"
            self.add_log(error_msg, 'ERROR')
            self.add_log("해결 방법: 필요한 패키지가 설치되었는지 확인하세요", 'WARNING')
            import traceback
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    self.add_log(line, 'ERROR')

        except Exception as e:
            error_msg = f"크롤링 중 오류 발생: {str(e)}"
            self.add_log(error_msg, 'ERROR')

            # 상세 오류 정보 로그에 표시
            import traceback
            self.add_log("=== 상세 오류 정보 ===", 'ERROR')
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    self.add_log(line, 'ERROR')
            self.add_log("======================", 'ERROR')

        finally:
            self.is_crawling = False
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.status_label.config(text="상태: 완료"))

    def update_status(self, category_name=None, category_count=0, product_count=0):
        """상태 업데이트"""
        if category_name:
            self.current_category_label.config(text=f"현재 카테고리: {category_name}")
        self.category_count_label.config(text=f"수집된 카테고리: {category_count}개")
        self.product_count_label.config(text=f"수집된 상품: {product_count}개")

    def update_progress(self, value):
        """진행률 업데이트"""
        self.progress_var.set(value)

def main():
    root = tk.Tk()
    app = NaverCrawlerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()