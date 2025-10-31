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
        """현재 화면에 보이는 상품 URL 수집 (최대 30개)"""
        product_elements = await page.query_selector_all('a[href*="/products/"]:has(img)')

        if not product_elements:
            product_elements = await self.helper.try_selectors(
                page, SELECTORS['product_links'], "상품 링크", multiple=True
            )

        # None 체크 (캡차 페이지 등에서 상품 못 찾으면 빈 리스트 반환)
        if not product_elements:
            return []

        # 메모리 보호: 최대 30개까지만 수집
        product_elements = product_elements[:30]

        urls = []
        for elem in product_elements:
            try:
                href = await elem.get_attribute('href')
                if href and '/products/' in href and re.search(r'/products/\d+', href):
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
            return None

        try:
            # 랜덤 대기 (5-12초)
            await asyncio.sleep(random.uniform(5.0, 12.0))

            # 새 탭에서 열기
            await page.evaluate(f'window.open("{url}", "_blank")')
            await asyncio.sleep(2)

            # 새 탭 찾기
            all_pages = context.pages
            if len(all_pages) <= 1:
                return None

            detail_page = all_pages[-1]
            await detail_page.wait_for_load_state('domcontentloaded')

            # 에러 페이지 체크
            if await detail_page.query_selector('text="현재 서비스 접속이 불가합니다"'):
                await detail_page.close()
                return None

            # URL 검증
            current_url = detail_page.url
            if not re.search(r'/products/\d+', current_url):
                await detail_page.close()
                return None

            # 페이지 로드 대기
            try:
                await detail_page.wait_for_load_state('networkidle', timeout=3000)
            except:
                pass

            # 스크롤 (검색태그 위치)
            scroll_percent = random.uniform(0.40, 0.50)
            await detail_page.evaluate(f'window.scrollTo(0, document.body.scrollHeight * {scroll_percent})')
            await asyncio.sleep(random.uniform(0.8, 1.5))

            # 상품 정보 수집
            detail_info = await self._collect_detail_info(detail_page)

            # 상품명 검증
            product_name = detail_info.get('detail_product_name')
            invalid_keywords = ['본문', '바로가기', '네이버', '로그인', '서비스', '스토어 홈']
            if (not product_name or len(product_name) < 5 or
                any(kw in product_name for kw in invalid_keywords)):
                await detail_page.close()
                return None

            # 탭 닫기
            await detail_page.close()

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
            try:
                if len(context.pages) > 1:
                    await context.pages[-1].close()
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
            try:
                print("[시작] Firefox 브라우저 실행...")
                browser = await p.firefox.launch(headless=False, slow_mo=1000)
                context = await browser.new_context(
                    no_viewport=True,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                    locale='ko-KR',
                    timezone_id='Asia/Seoul'
                )
                page = await context.new_page()

                # 1. 네이버 메인
                print("[접속] 네이버 메인...")
                await page.goto('https://www.naver.com')
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(3)

                # 2. 쇼핑 클릭
                print("[클릭] 쇼핑...")
                await page.evaluate('window.scrollTo(0, 0)')
                await asyncio.sleep(1)
                shopping_link = page.locator('#shortcutArea > ul > li:nth-child(4) > a')
                await shopping_link.click(timeout=10000)
                await asyncio.sleep(3)

                # 새 탭 전환
                all_pages = context.pages
                if len(all_pages) > 1:
                    page = all_pages[-1]
                    await page.wait_for_load_state('networkidle')

                # 캡차 체크
                await asyncio.sleep(2)
                if await page.query_selector('text="보안 확인을 완료해 주세요"'):
                    await self.wait_for_captcha_solve(page)

                # 3. 카테고리 클릭
                print("[클릭] 카테고리 메뉴...")
                category_btn = await page.wait_for_selector('button:has-text("카테고리")')
                await category_btn.click()

                # 메뉴 열림 대기
                try:
                    await page.wait_for_selector('a[data-name="여성의류"]', timeout=5000, state='visible')
                except:
                    await asyncio.sleep(3)

                # 4. 카테고리 선택
                print(f"[클릭] {self.category_name}...")
                womens = await page.wait_for_selector(f'a[data-name="{self.category_name}"]', timeout=10000)
                await womens.click()
                await asyncio.sleep(5)

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
                max_iterations = 5000  # 무한 루프 방지 (5000번 반복 = 약 2-3시간)
                iteration_count = 0

                import random

                while True:
                    # 무한 루프 방지
                    iteration_count += 1
                    if iteration_count > max_iterations:
                        print(f"\n[안전 종료] 최대 반복 횟수({max_iterations}) 도달")
                        print(f"[정보] 수집: {collected_count}개, 스크롤: {scroll_count}회")
                        break

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
                            print(f"\n[경고] 동일한 상품 세트 반복 감지 ({no_new_products_count}회)")
                            if no_new_products_count >= 3:
                                print(f"[완료] 동일한 상품만 반복, 페이지 끝 도달")
                                break
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

                        if no_new_products_count >= 3:
                            print("\n[완료] 더 이상 새 상품 없음")
                            break

                        # 스크롤 시도 (500px씩 점진적 스크롤, 제한 없음)
                        await page.evaluate('window.scrollBy(0, 500)')
                        await asyncio.sleep(random.uniform(1.5, 2.5))
                        scroll_count += 1
                        continue

                    # 보이는 상품 수집 (한 번에 최대 20개까지만)
                    new_products_this_batch = 0

                    # 메모리 보호: 한 번에 최대 20개까지만 처리
                    visible_urls = visible_urls[:20]

                    for url in visible_urls:
                        if self.should_stop:
                            break
                        if self.product_count and collected_count >= self.product_count:
                            break

                        # 연속 중복 10개 이상이면 즉시 스크롤 (임계값 낮춤)
                        if consecutive_duplicates >= 10:
                            print(f"\n[스크롤 필요] 연속 중복 {consecutive_duplicates}개 감지, 새 상품 로드 중...")
                            # 즉시 스크롤 (1500px - 확실하게 새 상품 영역으로 이동)
                            await page.evaluate('window.scrollBy(0, 1500)')
                            await asyncio.sleep(random.uniform(2.5, 3.5))
                            scroll_count += 1
                            consecutive_duplicates = 0  # 리셋
                            print(f"[스크롤 완료] 새 상품 확인 중...")
                            break

                        print(f"[{collected_count + 1}번째] 수집 시도...", end="", flush=True)

                        is_dup_flag = [False]  # 중복 플래그 (리스트로 참조 전달)
                        product_data = await self._crawl_product_detail(page, context, url, is_dup_flag)

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

                    # 연속 중복 25개 이상 = 더 이상 새 상품 없음 (임계값 조정)
                    if consecutive_duplicates >= 25:
                        print(f"\n[완료] 연속 중복 {consecutive_duplicates}개, 더 이상 새 상품 없음")
                        break

                    # 스크롤 전략: 중복 많으면 큰 스크롤 (임계값 조정)
                    if consecutive_duplicates >= 7:
                        # 중복이 많으면 더 크게 스크롤 (1200px)
                        await page.evaluate('window.scrollBy(0, 1200)')
                        await asyncio.sleep(random.uniform(2.5, 3.5))
                    else:
                        # 기본 스크롤 (600px)
                        await page.evaluate('window.scrollBy(0, 600)')
                        await asyncio.sleep(random.uniform(1.5, 2.5))
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
