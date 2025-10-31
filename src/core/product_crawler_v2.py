"""
상품 크롤러 V2 - 점진적 수집 최적화 버전
개선사항:
1. 스크롤 → 수집 → 반복 (메모리 효율)
2. DB 사전 중복 체크 (불필요한 클릭 방지)
3. 스마트 재개 (이미 수집한 상품 스킵)
"""
import asyncio
import json
import sys
import re
from datetime import datetime
from typing import Optional, Set
from playwright.async_api import async_playwright

sys.path.append('/home/dino/MyProjects/Crawl')
from src.database.db_connector import save_to_database, DatabaseConnector
from src.utils.config import SELECTORS
from src.utils.selector_helper import SelectorHelper

class ProgressiveCrawler:
    def __init__(self, headless=False, product_count: Optional[int] = None,
                 category_name: str = "여성의류", category_id: str = "10000107"):
        self.headless = headless
        self.product_count = product_count  # None이면 무한 모드
        self.category_name = category_name
        self.category_id = category_id
        self.products_data = []
        self.should_stop = False
        self.helper = SelectorHelper(debug=False)
        self.history_id = None
        self.db_connector = None

        # 중복 방지용 Set
        self.seen_product_ids: Set[str] = set()
        self.db_existing_ids: Set[str] = set()

        # 체크포인트 (마지막 수집 상품 ID)
        self.last_collected_id: Optional[str] = None

        # URL 세트 비교 (동일한 상품 반복 감지)
        self.previous_url_set: Set[str] = set()

    async def _load_existing_products(self):
        """DB에서 이미 수집한 상품 ID 조회"""
        db = DatabaseConnector()
        db.connect()
        try:
            cursor = db.conn.cursor()
            cursor.execute(
                "SELECT product_id FROM products WHERE category_name = %s",
                (self.category_name,)
            )
            rows = cursor.fetchall()
            self.db_existing_ids = {row[0] for row in rows}
            print(f"[DB] 기존 수집 상품: {len(self.db_existing_ids)}개")
        finally:
            db.close()

    def _extract_product_id(self, url: str) -> Optional[str]:
        """URL에서 product_id 추출"""
        match = re.search(r'/products/(\d+)', url)
        return match.group(1) if match else None

    async def _is_duplicate(self, product_id: str) -> bool:
        """중복 체크 (DB + 현재 세션)"""
        if product_id in self.db_existing_ids:
            return True
        if product_id in self.seen_product_ids:
            return True
        return False

    async def wait_for_captcha_solve(self, page):
        """캡차 해결 대기 - 15초 고정"""
        print("\n" + "="*60)
        print("캡차가 감지되었습니다!")
        print("="*60)
        print("브라우저에서 캡차를 수동으로 해결해주세요:")
        print("1. 캡차 이미지에 표시된 문자를 입력")
        print("2. '확인' 버튼 클릭")
        print("3. 정상 페이지가 나타날 때까지 대기")
        print("="*60)
        print("15초 동안 대기합니다...")

        for i in range(15, 0, -5):
            print(f"[대기] 남은 시간: {i}초...")
            await asyncio.sleep(5)

        print("대기 완료! 크롤링을 계속합니다...")
        await asyncio.sleep(2)

    async def _collect_visible_products(self, page) -> list:
        """현재 화면에 보이는 상품 URL 수집 (viewport 내부만)"""
        # JavaScript로 viewport에 보이는 상품만 필터링
        urls = await page.evaluate("""
            () => {
                const products = Array.from(document.querySelectorAll('a[href*="/products/"]'));
                const viewportHeight = window.innerHeight;
                const scrollTop = window.scrollY || window.pageYOffset;

                const visibleProducts = products.filter(elem => {
                    const rect = elem.getBoundingClientRect();
                    const absoluteTop = rect.top + scrollTop;
                    const absoluteBottom = rect.bottom + scrollTop;

                    // viewport 내부 또는 viewport 바로 아래 (다음 스크롤 영역)
                    return absoluteTop < scrollTop + viewportHeight * 2 &&
                           absoluteBottom > scrollTop - viewportHeight;
                });

                // URL 추출 (최대 30개)
                return visibleProducts
                    .slice(0, 30)
                    .map(elem => elem.href)
                    .filter(href => href && href.includes('/products/'));
            }
        """)

        if not urls:
            # 폴백: 기존 방식
            product_elements = await page.query_selector_all('a[href*="/products/"]:has(img)')
            if not product_elements:
                product_elements = await self.helper.try_selectors(
                    page, SELECTORS['product_links'], "상품 링크", multiple=True
                )

            if not product_elements:
                return []

            # viewport 근처만 (스크롤 위치 기준)
            product_elements = product_elements[:30]

            urls = []
            for elem in product_elements:
                try:
                    href = await elem.get_attribute('href')
                    if href and '/products/' in href and re.search(r'/products/\d+', href):
                        if href.startswith('/'):
                            href = f"https://shopping.naver.com{href}"
                        elif not href.startswith('http'):
                            href = f"https://shopping.naver.com/{href}"
                        urls.append(href)
                except:
                    continue

        return urls

    async def _crawl_product_detail(self, page, context, url: str, is_duplicate_ref: list = None) -> Optional[dict]:
        """상품 상세 정보 수집"""
        import random

        # product_id 추출
        product_id = self._extract_product_id(url)
        if not product_id:
            return None

        # 중복 체크
        if await self._is_duplicate(product_id):
            print(f" [SKIP-중복] ID:{product_id}")
            if is_duplicate_ref is not None:
                is_duplicate_ref[0] = True  # 중복 플래그 설정

            # 중복 체크에도 짧은 대기 (봇 차단 방지 - 자연스러운 스캔 패턴)
            await asyncio.sleep(random.uniform(0.3, 0.6))
            return None

        try:
            # 새 상품 발견 시 추가 대기 (중복 체크 직후 바로 클릭하면 의심스러움)
            await asyncio.sleep(random.uniform(1.5, 2.5))

            # 랜덤 대기 (2-5초로 단축 - 위에서 이미 대기했으므로)
            await asyncio.sleep(random.uniform(2.0, 5.0))

            # 같은 브라우저의 새 탭으로 열기 (Ctrl+클릭 방식)
            # 1. 링크 요소 찾기
            link_elem = await page.query_selector(f'a[href*="{product_id}"]')
            if not link_elem:
                # selector가 복잡할 수 있으니 모든 상품 링크 찾아서 URL 매칭
                all_links = await page.query_selector_all('a[href*="/products/"]')
                for link in all_links:
                    href = await link.get_attribute('href')
                    if product_id in href:
                        link_elem = link
                        break

            if not link_elem:
                print(f"\n[오류] 링크 요소를 찾을 수 없음 (ID:{product_id})")
                return None

            # 2. 현재 탭 개수 확인
            pages_before = len(context.pages)

            # 3. 단순 클릭 (JavaScript 조작 없음 - 봇 감지 회피)
            # 마우스를 요소 위로 이동
            await link_elem.hover()
            await asyncio.sleep(random.uniform(0.8, 1.5))

            # ✅ 아무 조작 없이 단순 클릭 (문서 Line 932-948 방식)
            await link_elem.click()
            await asyncio.sleep(random.uniform(4.0, 6.0))  # 새 탭 열림 충분히 대기

            # 4. 새 탭 확인
            pages_after = len(context.pages)

            # 같은 탭에서 열렸으면 스킵 (네이버 링크에 target="_blank" 없음)
            if pages_after <= pages_before:
                print(f"\n[스킵] 같은 탭에서 열림 (ID:{product_id})")
                # 원래 페이지로 돌아가기
                await page.go_back()
                await asyncio.sleep(random.uniform(2.0, 3.0))
                return None

            # 5. 새로 열린 탭 가져오기
            detail_page = context.pages[-1]

            # 페이지 로드 대기 (포커스는 자동으로 이동됨)
            try:
                await detail_page.wait_for_load_state('domcontentloaded', timeout=15000)
                await asyncio.sleep(random.uniform(2.0, 3.0))
            except Exception as nav_error:
                print(f"\n[오류] 페이지 로드 실패 (ID:{product_id}): {str(nav_error)[:60]}")
                await detail_page.close()
                await page.bring_to_front()
                return None

            # URL 검증 (빠른 체크는 괜찮음)
            current_url = detail_page.url
            if not re.search(r'/products/\d+', current_url):
                await detail_page.close()
                await page.bring_to_front()
                return None

            # 페이지 로드 완전 대기 (JavaScript 렌더링 완료까지)
            try:
                await detail_page.wait_for_load_state('networkidle', timeout=8000)
            except:
                await asyncio.sleep(2.0)

            # ✅ 인간처럼 행동: 페이지 읽기 시간 (3-5초 체류)
            await asyncio.sleep(random.uniform(3.0, 5.0))

            # ✅ 마우스 움직임 시뮬레이션 (자연스러운 탐색)
            await detail_page.mouse.move(
                random.randint(200, 800),
                random.randint(100, 400)
            )
            await asyncio.sleep(random.uniform(0.5, 1.0))

            # ✅ 부드러운 다단계 스크롤 (인간은 조금씩 스크롤)
            # 1단계: 조금 스크롤 (상품 정보 보기)
            await detail_page.evaluate('window.scrollBy(0, 300)')
            await asyncio.sleep(random.uniform(1.5, 2.5))

            # 2단계: 중간 위치 (이미지/설명 보기)
            await detail_page.evaluate('window.scrollBy(0, 400)')
            await asyncio.sleep(random.uniform(1.5, 2.5))

            # 3단계: 검색태그 위치 (40% 근처)
            # 정확한 계산 대신 대략적인 스크롤
            await detail_page.evaluate('window.scrollBy(0, 500)')
            await asyncio.sleep(random.uniform(1.0, 2.0))

            # ✅ 에러 페이지 체크 (모든 인간 행동 시뮬레이션 후 체크 - 봇 감지 회피)
            error_selectors = [
                'text="상품이 존재하지 않습니다"',
                'text="현재 서비스 접속이 불가합니다"',
                'text="일시적인 오류"',
                'text="서비스 접근이 제한"',
                'text="잠시 후 다시 시도"'
            ]

            for selector in error_selectors:
                if await detail_page.query_selector(selector):
                    print(f"\n[경고] 봇 차단 감지: {selector}")
                    await detail_page.close()
                    await page.bring_to_front()
                    return None

            # 상품 정보 수집
            detail_info = await self._collect_detail_info(detail_page)

            # 상품명 검증
            product_name = detail_info.get('detail_product_name')
            invalid_keywords = ['본문', '바로가기', '네이버', '로그인', '서비스', '스토어 홈']
            if (not product_name or len(product_name) < 5 or
                any(kw in product_name for kw in invalid_keywords)):
                await detail_page.close()
                await page.bring_to_front()
                return None

            # 탭 닫기
            await detail_page.close()

            # 원래 페이지로 돌아가기 (명시적 focus)
            await page.bring_to_front()
            await asyncio.sleep(random.uniform(0.5, 1.0))

            # 성공 - ID 저장 + 체크포인트
            self.seen_product_ids.add(product_id)
            self.last_collected_id = product_id

            return {
                'category': self.category_name,
                'crawled_at': datetime.now().isoformat(),
                'product_url': url,
                'detail_page_info': detail_info
            }

        except Exception as e:
            # 에러 발생 시 열린 탭 정리
            try:
                if len(context.pages) > 1:
                    await context.pages[-1].close()
                # 원래 페이지로 돌아가기
                await page.bring_to_front()
            except:
                pass
            return None

    async def _collect_detail_info(self, page):
        """상세 페이지 정보 수집"""
        detail_info = {}

        # 상품명
        elem = await self.helper.try_selectors(page, SELECTORS['product_name'], "상품명")
        detail_info['detail_product_name'] = await self.helper.extract_text(elem, "상품명")

        # 브랜드
        elem = await self.helper.try_selectors(page, SELECTORS['brand_name'], "브랜드")
        detail_info['brand_name'] = await self.helper.extract_text(elem, "브랜드")

        # 가격
        elem = await self.helper.try_selectors(page, SELECTORS['price'], "가격")
        price_text = await self.helper.extract_text(elem, "가격")
        detail_info['detail_price'] = self.helper.clean_price(price_text)

        # 할인율
        elem = await self.helper.try_selectors(page, SELECTORS['discount_rate'], "할인율")
        discount_text = await self.helper.extract_text(elem, "할인율")
        detail_info['discount_rate'] = self.helper.clean_discount_rate(discount_text)

        # 리뷰 수
        elem = await self.helper.try_selectors(page, SELECTORS['review_count'], "리뷰 수")
        review_text = await self.helper.extract_text(elem, "리뷰 수")
        detail_info['detail_review_count'] = self.helper.clean_review_count(review_text)

        # 평점
        elem = await self.helper.try_selectors(page, SELECTORS['rating'], "평점")
        rating_text = await self.helper.extract_text(elem, "평점")
        detail_info['rating'] = self.helper.clean_rating(rating_text)

        # 검색태그
        tags = []
        try:
            tag_container = await self.helper.find_by_text_then_next(page, "관련 태그", "ul", "검색태그")
            if tag_container:
                tag_links = await self.helper.try_selectors_from_element(
                    tag_container, SELECTORS['search_tags_links'], "태그 링크", multiple=True
                )
                if tag_links:
                    for link in tag_links:
                        text = await self.helper.extract_text(link, "태그")
                        if text:
                            clean_tag = text.replace('#', '').strip()
                            if 1 < len(clean_tag) < 30 and clean_tag not in tags:
                                tags.append(clean_tag)
        except:
            pass
        detail_info['search_tags'] = tags

        # 썸네일
        elem = await self.helper.try_selectors(page, SELECTORS['thumbnail'], "썸네일")
        detail_info['thumbnail_url'] = await self.helper.extract_attribute(elem, "src", "썸네일")

        # 품절
        elem = await self.helper.try_selectors(page, SELECTORS['is_sold_out'], "품절")
        detail_info['is_sold_out'] = (elem is not None)

        # URL
        detail_info['detail_page_url'] = page.url

        # 카테고리 경로
        category_path = []
        try:
            breadcrumb_links = await self.helper.find_breadcrumb_from_home(page, "카테고리")
            if not breadcrumb_links:
                breadcrumb_links = await self.helper.try_selectors(
                    page, SELECTORS['category_breadcrumb'], "카테고리", multiple=True
                )

            if breadcrumb_links:
                for link in breadcrumb_links:
                    text = await self.helper.extract_text(link)
                    if text:
                        clean_text = text.strip()
                        clean_text = re.sub(r'\(총\s*\d+개\)', '', clean_text).strip()
                        clean_text = re.sub(r'[\U00010000-\U0010ffff]', '', clean_text).strip()
                        clean_text = ' '.join(clean_text.split())

                        if clean_text and clean_text not in ['홈', '전체', '쇼핑홈', '쇼핑', 'HOME']:
                            category_path.append(clean_text)

            detail_info['category_fullname'] = '>'.join(category_path) if category_path else self.category_name
        except:
            detail_info['category_fullname'] = self.category_name

        return detail_info

    async def crawl(self):
        """점진적 수집 실행"""
        # DB 기존 상품 조회
        await self._load_existing_products()

        # DB 세션 시작
        db = DatabaseConnector()
        db.connect()
        self.history_id = db.start_crawl_session(self.category_name, resume=False)
        db.close()

        async with async_playwright() as p:
            browser = None
            # 변수 초기화 (exception handler에서 사용)
            collected_count = 0
            scroll_count = 0
            try:
                print("[시작] Firefox 브라우저 실행...")
                browser = await p.firefox.launch(headless=self.headless, slow_mo=500)
                context = await browser.new_context(
                    no_viewport=True,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
                    locale='ko-KR',
                    timezone_id='Asia/Seoul',
                    # 추가 헤더로 더 자연스럽게
                    extra_http_headers={
                        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                )

                # Stealth 스크립트: navigator.webdriver 제거 (봇 감지 회피)
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });

                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3]
                    });

                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['ko-KR', 'ko', 'en-US', 'en']
                    });
                """)

                page = await context.new_page()

                # 1. 네이버 메인
                print("[접속] 네이버 메인...")
                await page.goto('https://www.naver.com')
                await page.wait_for_load_state('domcontentloaded')  # networkidle 절대 사용 금지!
                await asyncio.sleep(3)

                # 2. 쇼핑 버튼 클릭
                print("[클릭] 쇼핑...")
                await page.evaluate('window.scrollTo(0, 0)')  # 상단으로 스크롤 필수!
                await asyncio.sleep(1)

                shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
                shopping_link = page.locator(shopping_selector)  # Locator API 사용
                await shopping_link.click(timeout=10000)
                await asyncio.sleep(3)
                print("[성공] 쇼핑 클릭 완료")

                # 새 탭 전환
                all_pages = context.pages
                if len(all_pages) > 1:
                    page = all_pages[-1]
                    print(f"[전환] 새 탭으로 전환 (총 {len(all_pages)}개 탭)")
                    await page.wait_for_load_state('networkidle', timeout=15000)

                    # URL 검증
                    current_url = page.url
                    print(f"[확인] 현재 URL: {current_url[:60]}...")
                    if 'shopping.naver.com' not in current_url:
                        print(f"[경고] 쇼핑 페이지가 아닙니다: {current_url}")
                        print("[안내] 브라우저에서 수동으로 네이버 쇼핑으로 이동해주세요")
                        await asyncio.sleep(10)
                else:
                    print(f"[경고] 새 탭이 열리지 않았습니다 (현재 {len(all_pages)}개 탭)")
                    print("[안내] 브라우저에서 수동으로 네이버 쇼핑으로 이동해주세요")
                    await asyncio.sleep(10)

                # 캡차 체크
                await asyncio.sleep(2)
                if await page.query_selector('text="보안 확인을 완료해 주세요"'):
                    await self.wait_for_captcha_solve(page)

                # 3. 카테고리 클릭
                print("[클릭] 카테고리 메뉴...")
                try:
                    category_btn = await page.wait_for_selector('button:has-text("카테고리")', timeout=15000, state='visible')
                    if not category_btn:
                        raise Exception("카테고리 버튼을 찾을 수 없습니다")

                    await category_btn.click()
                    print("[성공] 카테고리 메뉴 열림")
                    await asyncio.sleep(2)  # 메뉴 애니메이션 대기
                except Exception as e:
                    print(f"[오류] 카테고리 메뉴 클릭 실패: {str(e)}")
                    print("[안내] 브라우저에서 수동으로 카테고리 메뉴를 클릭해주세요")
                    await asyncio.sleep(10)

                # 4. 카테고리 선택
                print(f"[클릭] {self.category_name}...")
                try:
                    # 메뉴 항목이 보일 때까지 대기
                    category_link = await page.wait_for_selector(
                        f'a[data-name="{self.category_name}"]',
                        timeout=15000,
                        state='visible'
                    )
                    if not category_link:
                        raise Exception(f"{self.category_name} 카테고리를 찾을 수 없습니다")

                    await category_link.click()
                    print(f"[성공] {self.category_name} 선택 완료")
                    await asyncio.sleep(5)
                except Exception as e:
                    print(f"[오류] {self.category_name} 선택 실패: {str(e)}")
                    print(f"[안내] 브라우저에서 수동으로 '{self.category_name}' 카테고리를 클릭해주세요")
                    await asyncio.sleep(15)

                # 캡차 체크
                captcha_elem = await self.helper.try_selectors(page, SELECTORS['captcha_indicators'], "캡차")
                if captcha_elem:
                    await self.wait_for_captcha_solve(page)

                # 페이지 로드 대기
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    pass
                await asyncio.sleep(2)

                # 5. 점진적 수집 시작
                print(f"\n[점진적 수집] 시작 (DB 중복: {len(self.db_existing_ids)}개 스킵)")
                print(f"[정보] 화면 보이는 상품 → 수집 → 스크롤 → 반복\n")

                if self.product_count is None:
                    print("[정보] 무한 모드 - 10개마다 자동 DB 저장 (데이터 손실 방지)\n")

                collected_count = 0
                scroll_count = 0
                no_new_products_count = 0
                consecutive_duplicates = 0  # 연속 중복 카운터 (전역)
                iteration_count = 0

                import random

                while True:
                    # 무한 루프 방지 (제한 모드에서만 - 버그 방지용)
                    iteration_count += 1
                    if self.product_count is not None and iteration_count > 5000:
                        # 제한 모드(예: 3개 수집)에서만 5000회 제한
                        print(f"\n[안전 종료] 최대 반복 횟수(5000) 도달 (버그 방지)")
                        print(f"[정보] 수집: {collected_count}개, 스크롤: {scroll_count}회")
                        break
                    # 무한 모드(product_count=None)에서는 제한 없음!

                    # 디버깅: 50번 반복마다 상태 출력
                    if iteration_count % 50 == 0:
                        print(f"\n[디버깅] 반복: {iteration_count}회, 수집: {collected_count}개, 연속중복: {consecutive_duplicates}개, no_new: {no_new_products_count}회")

                    # 중지 요청 확인
                    if self.should_stop:
                        print(f"\n[중지] 사용자 요청 ({collected_count}개 수집)")
                        break

                    # 목표 개수 도달
                    if self.product_count and collected_count >= self.product_count:
                        print(f"\n[완료] 목표 개수 도달 ({collected_count}개)")
                        break

                    # 현재 화면 상품 수집
                    visible_urls = await self._collect_visible_products(page)

                    # URL 세트 비교 (동일한 상품 반복 감지)
                    if visible_urls:
                        current_url_set = set(visible_urls)
                        if self.previous_url_set and current_url_set == self.previous_url_set:
                            no_new_products_count += 1
                            print(f"\n[경고] 동일한 상품 세트 반복 ({no_new_products_count}회) - 큰 스크롤로 넘어갑니다...")

                            # 10회 이상 반복되면 페이지 끝일 가능성
                            if no_new_products_count >= 10:
                                print(f"\n[종료] 동일 상품 세트 10회 반복 - 페이지 끝에 도달한 것으로 판단")
                                break

                            # 동일한 상품 세트가 반복되면 대폭 스크롤 (2500px + 1500px)
                            await page.evaluate('window.scrollBy(0, 2500)')
                            await asyncio.sleep(random.uniform(3.5, 5.0))

                            await page.evaluate('window.scrollBy(0, 1500)')
                            await asyncio.sleep(random.uniform(2.5, 3.5))

                            scroll_count += 2
                            continue  # 다시 상품 수집 시도
                        else:
                            # URL 세트가 변경되었으면 카운터 리셋
                            if self.previous_url_set and current_url_set != self.previous_url_set:
                                no_new_products_count = 0

                        # 현재 URL 세트 저장
                        self.previous_url_set = current_url_set

                    if not visible_urls:
                        no_new_products_count += 1

                        # 첫 번째 시도에서 상품 못 찾으면 캡차 문제일 가능성 높음
                        if collected_count == 0 and no_new_products_count == 1:
                            print("\n" + "="*60)
                            print("[오류] 상품을 찾을 수 없습니다")
                            print("="*60)
                            print("원인:")
                            print("  1. 캡차 문제가 해결되지 않았습니다")
                            print("  2. 페이지 로딩이 완료되지 않았습니다")
                            print("  3. 네이버 페이지 구조가 변경되었습니다")
                            print("\n해결 방법:")
                            print("  - 브라우저에서 캡차를 수동으로 해결하세요")
                            print("  - 상품 목록이 정상적으로 보이는지 확인하세요")
                            print("  - 잠시 후 다시 시도하세요")
                            print("="*60 + "\n")
                            break

                        # 무한 크롤링: 상품이 안 보여도 계속 스크롤 시도
                        print(f"\n[스크롤] 상품 없음 ({no_new_products_count}회) - 계속 스크롤...")
                        await page.evaluate('window.scrollBy(0, 500)')
                        await asyncio.sleep(random.uniform(1.5, 2.5))
                        scroll_count += 1
                        continue

                    # 보이는 상품 수집 (한 번에 최대 20개까지만)
                    new_products_this_batch = 0
                    need_immediate_scroll = False  # 즉시 스크롤 플래그

                    # 메모리 보호: 한 번에 최대 20개까지만 처리
                    visible_urls = visible_urls[:20]

                    # 연속 중복 10개 이상이면 즉시 스크롤 (for 루프 진입 전 체크)
                    if consecutive_duplicates >= 10:
                        print(f"\n[스크롤 필요] 연속 중복 {consecutive_duplicates}개 감지, 새 상품 로드 중...")

                        # 큰 스크롤 (2500px) + 충분한 대기 시간
                        await page.evaluate('window.scrollBy(0, 2500)')
                        await asyncio.sleep(random.uniform(3.5, 5.0))  # 새 상품 로드 대기

                        # 추가 스크롤 (네이버 무한 스크롤 트리거)
                        await page.evaluate('window.scrollBy(0, 1500)')
                        await asyncio.sleep(random.uniform(3.0, 4.5))

                        scroll_count += 2
                        consecutive_duplicates = 0  # 리셋
                        print(f"[스크롤 완료] 새 상품 확인 중...")
                        continue  # while 루프 처음으로 돌아가서 새 상품 수집

                    for idx, url in enumerate(visible_urls):
                        if self.should_stop:
                            break
                        if self.product_count and collected_count >= self.product_count:
                            break

                        print(f"[{collected_count + 1}번째] 수집 시도...", end="", flush=True)

                        is_dup_flag = [False]  # 중복 플래그 (리스트로 참조 전달)
                        product_data = await self._crawl_product_detail(page, context, url, is_dup_flag)

                        # 5개 연속 중복마다 더 긴 대기 (인간적인 스캔 패턴)
                        if is_dup_flag[0] and consecutive_duplicates > 0 and consecutive_duplicates % 5 == 0:
                            await asyncio.sleep(random.uniform(1.5, 2.5))

                        if product_data:
                            self.products_data.append(product_data)
                            collected_count += 1
                            new_products_this_batch += 1
                            consecutive_duplicates = 0  # 새 상품 발견 시 리셋

                            product_name = product_data['detail_page_info'].get('detail_product_name', 'N/A')
                            tags_count = len(product_data['detail_page_info'].get('search_tags', []))
                            price = product_data['detail_page_info'].get('detail_price', 0)
                            brand = product_data['detail_page_info'].get('brand_name', 'N/A')
                            category = product_data['detail_page_info'].get('category_fullname', 'N/A')

                            print(f" [{product_name[:40]}] 태그 {tags_count}개 (총 {collected_count}개)")

                            # 10개마다 DB 상태 요약 출력
                            if collected_count % 10 == 0:
                                print(f"\n{'='*60}")
                                print(f"[DB 수집 현황] {collected_count}개 수집 완료")
                                print(f"{'='*60}")
                                print(f"최근 상품: {product_name[:50]}")
                                brand_display = brand[:30] if brand else 'N/A'
                                print(f"  - 브랜드: {brand_display}")
                                print(f"  - 가격: {price:,}원")
                                print(f"  - 카테고리: {category[:50]}")
                                print(f"  - 검색태그: {tags_count}개")
                                print(f"  - DB 기존 중복: {len(self.db_existing_ids)}개")
                                print(f"  - 현재 세션 수집: {len(self.seen_product_ids)}개")

                                # 100개마다 메모리 상태 출력
                                if collected_count % 100 == 0:
                                    print(f"  - 열린 브라우저 탭: {len(context.pages)}개")
                                    print(f"  - 스크롤 횟수: {scroll_count}회")

                                print(f"{'='*60}\n")

                            # 10개마다 자동 저장 (무한 모드 - 데이터 손실 방지)
                            if self.product_count is None and collected_count % 10 == 0:
                                print(f"\n{'='*60}")
                                print(f"[자동 저장] {collected_count}개 수집 완료, DB 저장...")
                                results = save_to_database(self.category_name, self.products_data, skip_duplicates=True)
                                print(f"[완료] 신규: {results['saved']}개, 중복: {results['skipped']}개")
                                if self.last_collected_id:
                                    print(f"[체크포인트] 마지막 상품 ID: {self.last_collected_id}")
                                self.products_data.clear()

                                # 메모리 관리: 1000개마다 seen_product_ids 정리
                                if len(self.seen_product_ids) > 1000:
                                    old_count = len(self.seen_product_ids)
                                    self.seen_product_ids.clear()
                                    print(f"[메모리 관리] 세션 ID 캐시 정리: {old_count}개 → 0개")

                                print(f"{'='*60}\n")
                        elif is_dup_flag[0]:
                            # 중복이었으면 카운터 증가
                            consecutive_duplicates += 1
                            print("")  # 줄바꿈만
                        else:
                            # 기타 오류 (상품명 없음 등)
                            print("")  # 줄바꿈만

                    # 새 상품이 있었으면 카운터 리셋
                    if new_products_this_batch > 0:
                        no_new_products_count = 0
                        consecutive_duplicates = 0  # 새 상품 발견 시 중복 카운터도 리셋
                    else:
                        no_new_products_count += 1

                    # 무한 크롤링 모드: 자동 종료 없음, 스크롤 계속
                    # 중복이 많아도 절대 멈추지 않음 (사용자가 "중지" 버튼 누를 때까지)

                    # 스크롤 전략: 새 상품 로드를 위한 충분한 스크롤
                    if consecutive_duplicates >= 30:
                        # 중복이 매우 많으면 대폭 스크롤 (3000px + 추가 1500px)
                        print(f"\n[스크롤] 연속 중복 {consecutive_duplicates}개, 큰 폭으로 스크롤...")
                        await page.evaluate('window.scrollBy(0, 3000)')
                        await asyncio.sleep(random.uniform(3.5, 5.0))  # 긴 대기

                        # 추가 스크롤로 무한 스크롤 트리거
                        await page.evaluate('window.scrollBy(0, 1500)')
                        await asyncio.sleep(random.uniform(2.5, 3.5))
                        scroll_count += 2
                    else:
                        # 기본: 중간 스크롤 (1200px)
                        await page.evaluate('window.scrollBy(0, 1200)')
                        await asyncio.sleep(random.uniform(2.0, 3.0))
                        scroll_count += 1

                print(f"\n{'='*60}")
                print(f"[완료] 총 {collected_count}개 상품 수집")
                print(f"[스크롤] {scroll_count}회")
                print(f"{'='*60}")

                return self.products_data

            except Exception as e:
                print(f"\n{'='*80}")
                print(f"[치명적 오류 발생]")
                print(f"{'='*80}")
                print(f"오류 메시지: {str(e)}")
                print(f"수집 상태: {collected_count}개 수집 완료")
                print(f"스크롤: {scroll_count}회")
                print(f"마지막 상품 ID: {self.last_collected_id}")
                print(f"\n상세 스택 트레이스:")
                import traceback
                traceback.print_exc()
                print(f"\n복구 방법:")
                print(f"  1. DB에 {collected_count}개 저장됨 (중복 체크로 재시작 가능)")
                print(f"  2. 브라우저를 수동으로 닫으세요")
                print(f"  3. 프로그램을 다시 시작하세요")
                print(f"{'='*80}\n")

                return None

            finally:
                # 브라우저 정리 (항상 실행)
                try:
                    if browser:
                        print("\n[정리] 브라우저 종료 중...")
                        await browser.close()
                        print("[정리] 브라우저 종료 완료")
                except Exception as cleanup_error:
                    print(f"[경고] 브라우저 종료 실패: {cleanup_error}")

                # DB 세션 종료 (항상 실행)
                try:
                    db = DatabaseConnector()
                    db.connect()
                    if self.should_stop:
                        db.end_crawl_session(self.history_id, status='paused')
                        print(f"[DB] 세션 일시중지 기록")
                    elif collected_count > 0:
                        db.end_crawl_session(self.history_id, status='completed')
                        print(f"[DB] 세션 완료 기록")
                    else:
                        db.end_crawl_session(self.history_id, status='failed', error_message='No data collected')
                        print(f"[DB] 세션 실패 기록")
                    db.close()
                except Exception as db_error:
                    print(f"[경고] DB 세션 종료 실패: {db_error}")

                print("[정리] 모든 리소스 정리 완료\n")

    def save_to_db(self, skip_duplicates=True):
        """DB 저장"""
        if not self.products_data:
            print("[경고] 저장할 데이터 없음")
            return False

        print(f"\n[DB 저장] {len(self.products_data)}개 상품 저장 중...")
        results = save_to_database(self.category_name, self.products_data, skip_duplicates=skip_duplicates)

        print(f"[완료] 신규: {results['saved']}개, 중복: {results['skipped']}개, 실패: {results['failed']}개")
        return results['saved'] > 0 or results['skipped'] > 0


if __name__ == "__main__":
    async def main():
        print("\n점진적 상품 수집 크롤러 V2")
        print("="*60)

        crawler = ProgressiveCrawler(product_count=20)
        data = await crawler.crawl()

        if data:
            crawler.save_to_db()
            print("\n수집 완료!")
        else:
            print("\n수집 실패")

    asyncio.run(main())
