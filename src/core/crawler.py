"""네이버 쇼핑 카테고리 크롤러"""
import asyncio
import time
import random
from playwright.async_api import async_playwright
from src.utils.config import CRAWL_CONFIG, SELECTORS
from src.utils.captcha_handler import CaptchaHandler
import json

class CategoryCrawler:
    def __init__(self, gui=None, headless=False):
        self.gui = gui
        self.headless = headless
        self.categories = []
        self.category_count = 0
        self.is_running = True
        self.captcha_handler = CaptchaHandler(gui)

    def log(self, message, level='INFO'):
        """로그 메시지 출력"""
        print(f"[{level}] {message}")
        if self.gui:
            self.gui.add_log(message, level)

    def update_status(self, category_name=None):
        """GUI 상태 업데이트"""
        if self.gui:
            self.gui.update_status(
                category_name=category_name,
                category_count=self.category_count,
                product_count=0
            )

    def crawl_categories_only(self):
        """카테고리만 수집"""
        asyncio.run(self._crawl_categories())

    def crawl_all(self):
        """카테고리 + 상품 수집"""
        # TODO: 상품 수집 로직 추가
        asyncio.run(self._crawl_categories())

    async def _crawl_categories(self):
        """비동기 카테고리 크롤링"""
        async with async_playwright() as p:
            try:
                # 브라우저 시작
                self.log("브라우저를 시작합니다...", 'INFO')
                self.log(f"Headless 모드: {self.headless} (False = 브라우저 표시)", 'INFO')

                # Firefox를 우선 시도, 실패하면 Chromium + Stealth
                try:
                    # Firefox 시도 (별도 Stealth 불필요)
                    self.log("Firefox 브라우저로 시도합니다...", 'INFO')
                    browser = await p.firefox.launch(
                        headless=self.headless,
                        args=['--start-maximized', '--start-fullscreen']
                    )
                    using_firefox = True
                except:
                    # Firefox 실패 시 Chromium + 완전한 Stealth
                    self.log("Firefox 실패, Chromium + Stealth로 시도합니다...", 'INFO')
                    browser = await p.chromium.launch(
                        headless=self.headless,
                        args=[
                            '--start-maximized',  # 최대화로 시작
                            '--start-fullscreen', # 전체화면으로 시작
                            '--disable-blink-features=AutomationControlled',
                            '--disable-web-security',
                            '--disable-features=IsolateOrigins,site-per-process',
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-accelerated-2d-canvas',
                            '--no-first-run',
                            '--no-zygote',
                            '--single-process',
                            '--disable-gpu'
                        ]
                    )
                    using_firefox = False

                # Firefox와 Chromium에 맞는 User-Agent 설정 (전체화면)
                if 'using_firefox' in locals() and using_firefox:
                    context = await browser.new_context(
                        viewport=None,  # 전체화면을 위해 viewport 제거
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                        locale='ko-KR',
                        timezone_id='Asia/Seoul',
                        no_viewport=True  # 전체화면 모드
                    )
                else:
                    context = await browser.new_context(
                        viewport=None,  # 전체화면을 위해 viewport 제거
                        no_viewport=True,  # 전체화면 모드
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        locale='ko-KR',
                        timezone_id='Asia/Seoul',
                        permissions=['geolocation'],
                        geolocation={'latitude': 37.5665, 'longitude': 126.9780},  # 서울
                        color_scheme='light',
                        device_scale_factor=1.0,
                        has_touch=False,
                        is_mobile=False
                    )

                # Chromium일 때만 완전한 Stealth 스크립트 적용
                if 'using_firefox' not in locals() or not using_firefox:
                    await context.add_init_script("""
                        // webdriver 속성 제거
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });

                        // chrome 객체 추가
                        window.chrome = {
                            runtime: {},
                            loadTimes: function() {},
                            csi: function() {},
                            app: {}
                        };

                        // plugins 추가
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [
                                {
                                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                                    1: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                                    length: 2,
                                    name: "Chrome PDF Plugin",
                                    filename: "internal-pdf-viewer"
                                },
                                {
                                    0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                                    length: 1,
                                    name: "Native Client",
                                    filename: "internal-nacl-plugin"
                                }
                            ]
                        });

                        // languages 설정
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['ko-KR', 'ko', 'en-US', 'en']
                        });

                        // platform 설정
                        Object.defineProperty(navigator, 'platform', {
                            get: () => 'Win32'
                        });

                        // permissions 수정
                        const originalQuery = window.navigator.permissions.query;
                        window.navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );

                        // WebGL Vendor 설정
                        const getParameter = WebGLRenderingContext.prototype.getParameter;
                        WebGLRenderingContext.prototype.getParameter = function(parameter) {
                            if (parameter === 37445) {
                                return 'Intel Inc.';
                            }
                            if (parameter === 37446) {
                                return 'Intel Iris OpenGL Engine';
                            }
                            return getParameter.apply(this, arguments);
                        };

                        // Canvas Fingerprint 방지
                        const originalGetContext = HTMLCanvasElement.prototype.getContext;
                        HTMLCanvasElement.prototype.getContext = function(type, attributes) {
                            if (type === '2d') {
                                const context = originalGetContext.apply(this, arguments);
                                const originalFillText = context.fillText;
                                context.fillText = function() {
                                    arguments[0] = arguments[0] + String.fromCharCode(8203);  // Zero-width space
                                    return originalFillText.apply(this, arguments);
                                };
                                return context;
                            }
                            return originalGetContext.apply(this, arguments);
                        };
                    """)

                page = await context.new_page()

                # 브라우저 최대화 (전체화면 대신)
                self.log("브라우저를 최대화합니다...", 'INFO')
                # 화면 크기 가져오기
                await page.evaluate("""
                    () => {
                        window.moveTo(0, 0);
                        window.resizeTo(screen.width, screen.height);
                    }
                """)
                await asyncio.sleep(0.5)

                # 네이버 쇼핑 메인 페이지 접속 (랜덤 딜레이 추가)
                self.log(f"네이버 쇼핑 페이지 접속: {CRAWL_CONFIG['base_url']}", 'INFO')
                await asyncio.sleep(random.uniform(1, 3))  # 접속 전 랜덤 대기
                await page.goto(CRAWL_CONFIG['base_url'], wait_until='networkidle')
                await self.random_wait()

                # 캡차 페이지 처리
                is_captcha = await self.captcha_solver.handle_captcha_page(page)
                if is_captcha:
                    self.log("캡차 해결 시도 중...", 'INFO')
                    # 캡차 해결 후 다시 로드 대기
                    await page.wait_for_load_state('networkidle')

                # 페이지 로드 대기
                await page.wait_for_load_state('networkidle')
                self.log("페이지 로드 완료", 'SUCCESS')

                # 카테고리 수집 시작
                await self.collect_categories(page)

                await browser.close()
                self.log(f"크롤링 완료! 총 {self.category_count}개의 카테고리를 수집했습니다.", 'SUCCESS')

            except Exception as e:
                self.log(f"크롤링 중 오류 발생: {str(e)}", 'ERROR')

                # 오류 타입별 안내
                error_str = str(e).lower()
                if "405" in error_str or "차단" in error_str or "blocked" in error_str:
                    self.log("⚠️ 네이버가 봇을 감지했습니다!", 'ERROR')
                    self.log("해결 방법:", 'WARNING')
                    self.log("1. 잠시 후 다시 시도하세요 (5-10분)", 'WARNING')
                    self.log("2. 브라우저가 표시되는지 확인하세요 (Headless=False)", 'WARNING')
                    self.log("3. docs/CRAWLING_LESSONS_LEARNED.md 참고", 'WARNING')
                elif "timeout" in error_str:
                    self.log("⏱️ 시간 초과 오류", 'ERROR')
                    self.log("네트워크 연결을 확인하거나 잠시 후 다시 시도하세요", 'WARNING')
                elif "connection" in error_str or "network" in error_str:
                    self.log("🌐 네트워크 오류", 'ERROR')
                    self.log("인터넷 연결을 확인하세요", 'WARNING')

                raise

    async def collect_categories(self, page):
        """카테고리 정보 수집"""
        try:
            # 카테고리 버튼 찾기 및 클릭
            self.log("카테고리 메뉴를 찾고 있습니다...", 'INFO')

            # 여러 가능한 셀렉터 시도
            category_selectors = [
                'button:has-text("카테고리")',
                '[aria-label*="카테고리"]',
                'button[class*="category"]',
                '#gnb-gnb button',
                '._gnbCategory_button',
            ]

            category_btn = None
            for selector in category_selectors:
                try:
                    category_btn = await page.wait_for_selector(selector, timeout=3000)
                    if category_btn:
                        self.log(f"카테고리 버튼 발견: {selector}", 'SUCCESS')
                        break
                except:
                    continue

            if not category_btn:
                # 페이지 구조 분석
                self.log("카테고리 버튼을 찾을 수 없습니다. 페이지 구조를 분석합니다...", 'WARNING')

                # 대안: 직접 카테고리 페이지로 이동
                all_links = await page.query_selector_all('a')
                category_links = []

                for link in all_links:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()

                    # 카테고리 관련 링크 수집
                    if href and ('category' in href.lower() or 'catalog' in href.lower()):
                        category_links.append({
                            'name': text.strip(),
                            'url': href
                        })

                # 중복 제거
                seen = set()
                unique_categories = []
                for cat in category_links:
                    if cat['name'] and cat['name'] not in seen:
                        seen.add(cat['name'])
                        unique_categories.append(cat)

                self.categories = unique_categories[:50]  # 상위 50개만
                self.category_count = len(self.categories)

                self.log(f"대체 방법으로 {self.category_count}개의 카테고리를 발견했습니다.", 'INFO')

                # 카테고리 정보 저장
                await self.save_categories()
                return

            # 카테고리 버튼 클릭
            await category_btn.click()
            await self.random_wait()

            # 카테고리 메뉴가 열릴 때까지 대기
            self.log("카테고리 메뉴가 열리기를 기다리는 중...", 'INFO')
            await page.wait_for_selector('[class*="category"]', timeout=5000)

            # 모든 카테고리 수집
            category_elements = await page.query_selector_all('a[href*="/catalog/"], a[href*="/category/"]')

            self.log(f"{len(category_elements)}개의 카테고리 요소를 발견했습니다.", 'INFO')

            for element in category_elements:
                if not self.is_running:
                    break

                try:
                    name = await element.inner_text()
                    href = await element.get_attribute('href')

                    if name and href:
                        category_info = {
                            'name': name.strip(),
                            'url': href if href.startswith('http') else f'https://shopping.naver.com{href}',
                            'level': 1  # 대카테고리로 가정
                        }

                        self.categories.append(category_info)
                        self.category_count += 1

                        self.update_status(category_name=name.strip())
                        self.log(f"카테고리 수집: {name.strip()}", 'INFO')

                        # 진행률 업데이트
                        if self.gui:
                            progress = (self.category_count / len(category_elements)) * 100
                            self.gui.update_progress(progress)

                except Exception as e:
                    self.log(f"카테고리 수집 중 오류: {str(e)}", 'WARNING')
                    continue

            # 수집된 카테고리 저장
            await self.save_categories()

        except Exception as e:
            self.log(f"카테고리 수집 중 오류: {str(e)}", 'ERROR')

    async def save_categories(self):
        """수집된 카테고리 저장"""
        try:
            # JSON 파일로 저장 (임시)
            with open('categories.json', 'w', encoding='utf-8') as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=2)

            self.log(f"카테고리 정보가 categories.json 파일에 저장되었습니다.", 'SUCCESS')

            # TODO: DB에 저장하는 로직 추가

        except Exception as e:
            self.log(f"카테고리 저장 중 오류: {str(e)}", 'ERROR')

    async def random_wait(self):
        """랜덤 대기 시간"""
        wait_time = random.uniform(
            CRAWL_CONFIG['wait_time']['min'],
            CRAWL_CONFIG['wait_time']['max']
        )
        await asyncio.sleep(wait_time)

    def stop(self):
        """크롤링 중지"""
        self.is_running = False
        self.log("크롤링이 중지되었습니다.", 'WARNING')