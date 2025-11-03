#!/usr/bin/env python3
"""
네이버 쇼핑 상품 수집기 GUI (v1.2.0)
SimpleCrawler 기반 - 13개 필드 수집 + DB 직접 저장 + 무한 모드
"""

import customtkinter as ctk
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
    """상품 수집 GUI (v1.2.0) - 모든 카테고리 + 무한 모드 + DB 직접 저장"""

    def __init__(self):
        logger.info("=" * 70)
        logger.info("GUI 초기화 시작")
        logger.info("=" * 70)

        try:
            self.root = ctk.CTk()
            self.root.withdraw()
            logger.info("✓ CTk 루트 윈도우 생성 완료")

            self.root.title("네이버 쇼핑 상품 수집기 v1.2.0")
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
            'start_time': None,
            'last_product': None
        }

        # 카테고리 로드
        self.categories = self._load_categories()

        # UI 구성
        self._create_ui()

        # 타이머
        self.root.after(100, self._update_logs)
        self.root.after(1000, self._update_stats)

        # 창 표시
        self.root.update_idletasks()
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(300, lambda: self.root.attributes('-topmost', False))

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
        """UI 컴포넌트 생성"""
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 제목
        ctk.CTkLabel(
            main_frame,
            text="네이버 쇼핑 상품 수집기",
            font=("Arial", 24, "bold")
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            main_frame,
            text="13개 필드 완벽 수집 → DB 직접 저장 (v1.2.0)",
            font=("Arial", 12),
            text_color="gray60"
        ).pack(pady=(0, 20))

        # 설정 영역
        settings_frame = ctk.CTkFrame(main_frame, fg_color="gray25")
        settings_frame.pack(fill="x", pady=(0, 20))

        # 카테고리 선택
        cat_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        cat_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            cat_frame,
            text="카테고리:",
            font=("Arial", 13)
        ).pack(side="left", padx=(0, 10))

        self.category_var = ctk.StringVar(value="여성의류")
        self.category_dropdown = ctk.CTkOptionMenu(
            cat_frame,
            variable=self.category_var,
            values=list(self.categories.keys()),
            width=200
        )
        self.category_dropdown.pack(side="left")

        # 수집 모드
        mode_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        mode_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            mode_frame,
            text="수집 모드:",
            font=("Arial", 13)
        ).pack(side="left", padx=(0, 10))

        self.mode_var = ctk.StringVar(value="infinite")

        ctk.CTkRadioButton(
            mode_frame,
            text="무한 수집 (기본)",
            variable=self.mode_var,
            value="infinite",
            command=self._toggle_count_entry
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            mode_frame,
            text="개수 지정:",
            variable=self.mode_var,
            value="limited",
            command=self._toggle_count_entry
        ).pack(side="left", padx=10)

        self.count_entry = ctk.CTkEntry(mode_frame, width=80, state="disabled")
        self.count_entry.insert(0, "10")
        self.count_entry.pack(side="left", padx=5)

        ctk.CTkLabel(mode_frame, text="개").pack(side="left")

        # 버튼 영역
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 20))

        self.start_button = ctk.CTkButton(
            button_frame,
            text="수집 시작",
            command=self._start_collection,
            width=180,
            height=45,
            font=("Arial", 15, "bold"),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.start_button.pack(side="left", expand=True, padx=(0, 10))

        self.stop_button = ctk.CTkButton(
            button_frame,
            text="수집 중지",
            command=self._stop_collection,
            width=180,
            height=45,
            font=("Arial", 15, "bold"),
            fg_color="#FF9800",
            hover_color="#F57C00",
            state="disabled"
        )
        self.stop_button.pack(side="left", expand=True, padx=(10, 0))

        # 상태 표시
        status_frame = ctk.CTkFrame(main_frame, fg_color="gray25")
        status_frame.pack(fill="x", pady=(0, 15))

        status_inner = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_inner.pack(padx=20, pady=15)

        self.status_label = ctk.CTkLabel(
            status_inner,
            text="대기 중",
            font=("Arial", 16, "bold")
        )
        self.status_label.pack(pady=(0, 8))

        self.progress_label = ctk.CTkLabel(
            status_inner,
            text="수집: 0개",
            font=("Arial", 13)
        )
        self.progress_label.pack()

        # 통계
        stats_frame = ctk.CTkFrame(main_frame, fg_color="gray25")
        stats_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            stats_frame,
            text="실시간 통계",
            font=("Arial", 13, "bold")
        ).pack(pady=(10, 5))

        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(padx=20, pady=(0, 10))

        self.stats_collected = ctk.CTkLabel(stats_grid, text="수집: 0개", font=("Arial", 12))
        self.stats_collected.pack(side="left", padx=15)

        self.stats_speed = ctk.CTkLabel(stats_grid, text="속도: 0.0개/분", font=("Arial", 12))
        self.stats_speed.pack(side="left", padx=15)

        self.stats_preview = ctk.CTkLabel(
            stats_frame,
            text="최근: -",
            font=("Arial", 10),
            text_color="gray50"
        )
        self.stats_preview.pack(pady=(0, 10))

        # 로그 영역
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True)

        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            log_header,
            text="실시간 로그:",
            font=("Arial", 12, "bold")
        ).pack(side="left")

        # 로그 복사 버튼
        ctk.CTkButton(
            log_header,
            text="로그 복사",
            command=self._copy_logs,
            width=90,
            height=28,
            font=("Arial", 11),
            fg_color="gray40",
            hover_color="gray30"
        ).pack(side="right", padx=5)

        self.log_text = ctk.CTkTextbox(log_frame, font=("Courier", 11))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _toggle_count_entry(self):
        """개수 입력 필드 활성화/비활성화"""
        if self.mode_var.get() == "limited":
            self.count_entry.configure(state="normal")
        else:
            self.count_entry.configure(state="disabled")

    def _log(self, message: str):
        """로그 메시지 추가"""
        clean_msg = remove_emojis(message)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {clean_msg}")

        # 상품명 추출
        if "DB 저장" in clean_msg or "수집" in clean_msg:
            try:
                if "]" in clean_msg and "[" in clean_msg:
                    parts = clean_msg.split("]")
                    if len(parts) >= 2:
                        name_part = parts[1].split("-")[0].strip()
                        if len(name_part) > 5:
                            self.stats['last_product'] = name_part[:40]
            except:
                pass

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
        """통계 업데이트"""
        if self.is_running and self.crawler:
            collected = len(self.crawler.products_data) if self.crawler.products_data else 0
            self.stats['collected'] = collected

            # 속도 계산
            if self.stats['start_time']:
                elapsed_min = (datetime.now() - self.stats['start_time']).total_seconds() / 60
                speed = collected / elapsed_min if elapsed_min > 0 else 0.0
            else:
                speed = 0.0

            # UI 업데이트
            if self.mode_var.get() == "infinite":
                self.progress_label.configure(text=f"수집: {collected}개 (무한 모드)")
            else:
                try:
                    target = int(self.count_entry.get())
                    self.progress_label.configure(text=f"수집: {collected}/{target}개")
                except:
                    self.progress_label.configure(text=f"수집: {collected}개")

            self.stats_collected.configure(text=f"수집: {collected}개")
            self.stats_speed.configure(text=f"속도: {speed:.1f}개/분")

            if self.stats['last_product']:
                preview = self.stats['last_product'][:35] + "..." if len(self.stats['last_product']) > 35 else self.stats['last_product']
                self.stats_preview.configure(text=f"최근: {preview}")

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
            'start_time': datetime.now(),
            'last_product': None
        }

        # UI 상태
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text="수집 중", text_color="#2196F3")

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
        self._log("")

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
            self._log("")
            self._log("중지 요청... (현재 상품 완료 후 종료)")

    def _copy_logs(self):
        """로그 내용을 클립보드에 복사"""
        try:
            # 로그 내용 가져오기
            log_content = self.log_text.get("1.0", "end-1c")

            if not log_content.strip():
                self._log("복사할 로그가 없습니다")
                return

            # 클립보드 복사 (UTF-8 인코딩 보장)
            self.clipboard_clear()
            self.clipboard_append(log_content)
            self.update()  # 클립보드 업데이트 강제 적용

            # 복사 검증
            try:
                copied = self.clipboard_get()
                if copied != log_content:
                    logger.warning("클립보드 복사 검증 실패: 내용이 일치하지 않음")
                    self._log("로그 복사 경고: 일부 내용이 누락되었을 수 있습니다")
                else:
                    logger.info(f"로그 복사 성공: {len(log_content)} 문자, 한글 {len([c for c in log_content if ord(c) > 127])}자")
            except Exception as verify_error:
                logger.warning(f"복사 검증 실패: {verify_error}")

            # 임시 메시지 표시
            original_text = self.status_label.cget("text")
            self.status_label.configure(text="로그 복사 완료!")
            self.after(2000, lambda: self.status_label.configure(text=original_text if original_text != "로그 복사 완료!" else "대기 중"))

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
            self._log("")
            if products:
                self._log(f"수집 완료! 총 {len(products)}개 상품 → DB 저장됨")
                self.status_label.configure(text="수집 완료", text_color="#4CAF50")
                logger.info(f"✓ 수집 성공: {len(products)}개")
            else:
                self._log("수집된 상품이 없습니다")
                self.status_label.configure(text="수집 실패", text_color="#F44336")
                logger.warning("⚠ 수집 실패: 0개")

        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()

            # GUI 로그
            self._log(f"오류 발생: {error_msg}")
            self.status_label.configure(text="오류 발생", text_color="#F44336")

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
