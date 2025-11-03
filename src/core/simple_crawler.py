#!/usr/bin/env python3
"""
간단하고 깔끔한 네이버 쇼핑 크롤러 (v1.1.0)
13개 필드 완벽 수집 + DB 직접 저장
"""

import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright
from typing import Optional, List, Dict
import sys
from pathlib import Path
import time

# DB Connector import
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.database.db_connector import DatabaseConnector


class SimpleCrawler:
    """
    네이버 쇼핑 상품 수집 크롤러
    13개 필드: product_id, category_name, product_name, search_tags,
              price, rating, product_url, thumbnail_url, brand_name,
              discount_rate, review_count, crawled_at, updated_at
    """

    def __init__(self,
                 category_name: str = "여성의류",
                 category_id: str = "10000107",
                 product_count: Optional[int] = None,  # None = 무한
                 headless: bool = False,
                 save_to_db: bool = True):
        self.category_name = category_name
        self.category_id = category_id
        self.product_count = product_count  # None이면 무한 수집
        self.headless = headless
        self.save_to_db = save_to_db
        self.should_stop = False
        self.products_data = []

        # DB 연결 (save_to_db가 True일 때만) - 세션 유지 방식
        self.db = DatabaseConnector() if save_to_db else None
        self.db_connected = False

        # 통계 추적
        self.start_time = None
        self.saved_count = 0  # DB 저장 성공
        self.skipped_count = 0  # 중복 스킵

    async def crawl(self) -> List[Dict]:
        """크롤링 실행"""
        async with async_playwright() as p:
            browser = await p.firefox.launch(
                headless=self.headless,
                slow_mo=300
            )

            context = await browser.new_context(
                no_viewport=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                locale='ko-KR',
                timezone_id='Asia/Seoul'
            )

            page = await context.new_page()

            try:
                # DB 연결 (세션 유지)
                if self.save_to_db and self.db:
                    try:
                        self.db.connect()
                        self.db_connected = True
                        print("[DB] 연결 성공")
                    except Exception as e:
                        print(f"[DB] 연결 실패: {str(e)}")
                        self.db_connected = False

                # 1. 네이버 메인 → 쇼핑 진입
                print("[1/4] 네이버 메인 페이지 접속...")
                await page.goto('https://www.naver.com')
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(2)

                # 쇼핑 클릭
                print("[2/4] 쇼핑 버튼 클릭...")
                shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
                await page.locator(shopping_selector).click(timeout=10000)
                await asyncio.sleep(2)

                # 새 탭 전환
                all_pages = context.pages
                if len(all_pages) > 1:
                    page = all_pages[-1]
                    await page.wait_for_load_state('networkidle')

                # 2. 카테고리 진입 (CRAWLING_LESSONS_LEARNED.md 검증된 방법)
                print(f"[3/4] '{self.category_name}' 카테고리 진입...")
                category_btn = await page.wait_for_selector('button:has-text("카테고리")')
                await category_btn.click()
                await asyncio.sleep(2)  # 메뉴 열리기 대기

                # 우선순위별 셀렉터 fallback (문서 1293-1296줄)
                category_elem = None

                # 1순위: ID 기반 (⭐⭐⭐⭐⭐)
                if self.category_id:
                    category_elem = await page.query_selector(f'#cat_layer_item_{self.category_id}')

                # 2순위: data-id 속성 (⭐⭐⭐⭐)
                if not category_elem and self.category_id:
                    category_elem = await page.query_selector(f'[data-id="{self.category_id}"]')

                # 3순위: data-name 속성 (⭐⭐⭐)
                if not category_elem:
                    category_elem = await page.query_selector(f'a[data-name="{self.category_name}"]')

                if not category_elem:
                    raise Exception(f"카테고리 '{self.category_name}' (ID: {self.category_id})를 찾을 수 없습니다")

                await category_elem.click()
                await asyncio.sleep(3)

                # 캡차 대기 (15초 고정)
                print("\n" + "="*60)
                print("[!] 캡차 확인 - 15초 대기")
                print("="*60)
                print("브라우저에서 캡차를 수동으로 해결해주세요")
                print("="*60)
                for i in range(15, 0, -5):
                    print(f"[대기] 남은 시간: {i}초...")
                    await asyncio.sleep(5)
                print("[OK] 대기 완료! 크롤링 시작...\n")
                await asyncio.sleep(2)

                # 3. 무한 스크롤 수집 시작
                if self.product_count:
                    print(f"[4/4] 상품 {self.product_count}개 수집 시작...\n")
                else:
                    print(f"[4/4] 무한 수집 시작 (중지 버튼으로 멈출 수 있습니다)...\n")

                # 시작 시간 기록
                self.start_time = time.time()

                collected_count = 0
                processed_indices = set()  # 이미 처리한 상품 인덱스 추적
                scroll_count = 0
                max_scroll_attempts = 100  # 최대 스크롤 횟수

                while scroll_count < max_scroll_attempts:
                    if self.should_stop:
                        break

                    # 현재 페이지의 모든 상품 링크 가져오기
                    product_links = await page.query_selector_all('a[class*="ProductCard_link"]')
                    current_total = len(product_links)

                    # 새로운 상품만 수집
                    for idx in range(len(product_links)):
                        # 목표 개수 도달 체크
                        if self.product_count and collected_count >= self.product_count:
                            print(f"\n목표 개수 도달! {collected_count}개 수집 완료")
                            break

                        if self.should_stop:
                            break

                        # 첫 14개 상품 건너뛰기 (광고)
                        if idx < 14:
                            processed_indices.add(idx)
                            continue

                        # 이미 처리한 상품은 건너뛰기
                        if idx in processed_indices:
                            continue

                        processed_indices.add(idx)

                        try:
                            # 상품 클릭 (매번 새로 쿼리 - DOM 변경 대응)
                            fresh_links = await page.query_selector_all('a[class*="ProductCard_link"]')
                            if idx >= len(fresh_links):
                                print(f"[{idx+1}번] 상품 인덱스 초과 - SKIP")
                                continue

                            product = fresh_links[idx]
                            await product.click()
                            await asyncio.sleep(3)  # 2초 → 3초 (탭 열림 대기)

                            # 새 탭 찾기
                            all_pages = context.pages
                            if len(all_pages) <= 1:
                                print(f"[{idx+1}번] 탭 열림 실패 - SKIP")
                                continue

                            detail_page = all_pages[-1]
                            await detail_page.wait_for_load_state('domcontentloaded')
                            await asyncio.sleep(2)  # 1초 → 2초 (페이지 로드 대기)

                            # 상품 정보 수집
                            product_data = await self._collect_product_info(detail_page)

                            if product_data and product_data.get('product_name'):
                                self.products_data.append(product_data)
                                collected_count += 1

                                # 메모리 최적화: 1000개 초과 시 오래된 데이터 정리 (마지막 500개만 유지)
                                if len(self.products_data) > 1000:
                                    self.products_data = self.products_data[-500:]

                                # 즉시 DB 저장 (세션 유지)
                                if self.save_to_db and self.db and self.db_connected:
                                    try:
                                        result = self.db.save_product(self.category_name, product_data)
                                        if result == 'saved':
                                            self.saved_count += 1
                                            product_data['_db_status'] = 'saved'
                                        elif result == 'skipped':
                                            self.skipped_count += 1
                                            product_data['_db_status'] = 'skipped'
                                    except Exception as e:
                                        product_data['_db_status'] = 'error'
                                        print(f"[{collected_count}] DB 저장 실패: {str(e)}")
                                else:
                                    product_data['_db_status'] = 'none'

                                # 간략한 진행 메시지만 출력
                                print(f"수집 중... {collected_count}개", end='\r')

                                # 50개마다 상세 테이블 출력
                                if collected_count % 50 == 0:
                                    self._print_products_table(collected_count)
                            else:
                                print(f"[{idx+1}번] 수집 실패 (상품명 없음) - SKIP")

                            # 탭 닫기
                            await detail_page.close()
                            await asyncio.sleep(1)

                        except Exception as e:
                            print(f"[{idx+1}번] 오류: {str(e)[:50]} - SKIP")
                            continue

                    # 목표 개수 도달 시 종료
                    if self.product_count and collected_count >= self.product_count:
                        break

                    if self.should_stop:
                        break

                    # 스크롤하여 새 상품 로드
                    before_scroll = current_total
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(3)  # 로딩 대기

                    # 스크롤 후 상품 개수 확인
                    product_links_after = await page.query_selector_all('a[class*="ProductCard_link"]')
                    after_scroll = len(product_links_after)

                    scroll_count += 1

                    if after_scroll > before_scroll:
                        print(f"\n[스크롤 #{scroll_count}] {before_scroll}개 → {after_scroll}개 (증가: {after_scroll - before_scroll}개)")
                    else:
                        print(f"\n더 이상 새 상품이 로드되지 않습니다.")
                        break

                # 최종 테이블 출력 (50의 배수가 아닌 경우)
                if len(self.products_data) % 50 != 0:
                    self._print_products_table(len(self.products_data), final=True)
                else:
                    print(f"\n\n수집 완료! 총 {len(self.products_data)}개 → DB 저장됨")

            finally:
                # DB 연결 종료
                if self.db_connected and self.db:
                    try:
                        self.db.close()
                        print("[DB] 연결 종료")
                    except:
                        pass
                await browser.close()

            return self.products_data

    def _print_products_table(self, count: int, final: bool = False):
        """50개 단위로 수집된 모든 상품 정보를 테이블로 출력"""
        print("\n")  # 진행 메시지 줄바꿈

        # 헤더
        if final:
            print("=" * 61)
            print(f"{'[완료] 수집 완료 - 전체 상품 목록':^55}")
            print("=" * 61)
        else:
            print("=" * 61)
            print(f"{'[진행중] 수집 현황 (' + str(count) + '개 완료)':^55}")
            print("=" * 61)

        # 통계 정보
        elapsed = time.time() - self.start_time
        elapsed_min = int(elapsed // 60)
        elapsed_sec = int(elapsed % 60)
        speed = count / (elapsed / 60) if elapsed > 0 else 0

        if self.save_to_db:
            print(f"  총 수집      : {count}개")
            print(f"  DB 저장      : {self.saved_count}개 ({self.saved_count/count*100:.1f}%)")
            print(f"  중복 스킵    : {self.skipped_count}개 ({self.skipped_count/count*100:.1f}%)")
        else:
            print(f"  총 수집      : {count}개")

        # 가격 통계
        prices = [p.get('price') for p in self.products_data if p.get('price')]
        if prices:
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            print(f"  평균 가격    : {avg_price:,.0f}원")
            print(f"  가격 범위    : {min_price:,}원 ~ {max_price:,}원")

        # 브랜드/태그 통계
        brands = [p for p in self.products_data if p.get('brand_name')]
        tags = [p.get('search_tags', []) for p in self.products_data]
        avg_tags = sum(len(t) for t in tags) / len(tags) if tags else 0

        print(f"  브랜드 수집  : {len(brands)}개 ({len(brands)/count*100:.1f}%)")
        print(f"  태그 평균    : {avg_tags:.1f}개/상품")
        print(f"  소요 시간    : {elapsed_min}분 {elapsed_sec}초")
        print(f"  수집 속도    : {speed:.1f}개/분")
        print("=" * 61)

        # 상품 테이블
        print("\n  # | 상품명 (35자)                      | 가격      | 브랜드     | 태그 | DB ")
        print("-" * 61)

        # 마지막 50개 (또는 전체) 출력
        start_idx = max(0, len(self.products_data) - 50)
        for i, product in enumerate(self.products_data[start_idx:], start=start_idx + 1):
            name = product.get('product_name', 'N/A')[:35]
            price = product.get('price')
            price_str = f"{price:>6,}원" if price else "   N/A"
            brand = (product.get('brand_name') or '-')[:10]
            tags_count = len(product.get('search_tags', []))
            db_status = product.get('_db_status', 'none')

            # DB 상태 기호 (명확한 표시)
            if db_status == 'saved':
                db_icon = 'OK'
            elif db_status == 'skipped':
                db_icon = 'DUP'
            elif db_status == 'error':
                db_icon = 'ERR'
            else:
                db_icon = 'N/A'

            print(f"{i:3d} | {name:35s} | {price_str} | {brand:10s} | {tags_count:2d}개 | {db_icon:3s}")

        print("=" * 61)
        print()

    async def _collect_product_info(self, page) -> Optional[Dict]:
        """상품 정보 수집 (13개 필드)"""
        data = {}

        try:
            # 1. product_id (URL에서 추출)
            url = page.url
            match = re.search(r'/products/(\d+)', url)
            data['product_id'] = match.group(1) if match else None

            # 2. category_name
            data['category_name'] = self.category_name

            # 3. product_name
            elem = await page.query_selector('h3.DCVBehA8ZB')
            data['product_name'] = await elem.inner_text() if elem else None

            # 4. brand_name (테이블에서) - 스크롤 없이 바로 수집
            brand_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('td, th');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    if (text.trim() === '브랜드') {
                        const nextTd = elem.nextElementSibling;
                        if (nextTd) {
                            const brandValue = nextTd.textContent.trim();
                            if (brandValue && brandValue.length < 50) {
                                return brandValue;
                            }
                        }
                    }
                }
                return null;
            }''')
            data['brand_name'] = brand_result

            # 5. price
            elem = await page.query_selector('strong.Izp3Con8h8')
            if elem:
                price_text = await elem.inner_text()
                price_clean = re.sub(r'[^\d]', '', price_text)
                data['price'] = int(price_clean) if price_clean else None
            else:
                data['price'] = None

            # 6. discount_rate (JavaScript evaluate)
            discount_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    if (text.includes('%') && text.length < 20) {
                        const match = text.match(/(\\d+)%/);
                        if (match && elem.children.length <= 1) {
                            return match[1];
                        }
                    }
                }
                return null;
            }''')
            data['discount_rate'] = int(discount_result) if discount_result else None

            # 7. review_count
            review_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    if (text.includes('리뷰') && text.length < 20) {
                        const match = text.match(/리뷰\\s*(\\d+)/);
                        if (match) {
                            return match[1];
                        }
                    }
                }
                return null;
            }''')
            data['review_count'] = int(review_result) if review_result else 0

            # 8. rating
            rating_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    if ((text.includes('평점') || text.includes('별점')) && text.length < 30) {
                        const match = text.match(/(\\d+\\.\\d+)/);
                        if (match) {
                            return parseFloat(match[1]);
                        }
                    }
                }
                return null;
            }''')
            data['rating'] = rating_result

            # 9. search_tags (최적화: 2번만 스크롤)
            # 30% 스크롤 (brand_name 위치)
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.3)')
            await asyncio.sleep(1.5)

            # 50% 스크롤 (search_tags 위치)
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.5)')
            await asyncio.sleep(2.0)

            # 태그 수집
            all_tags_found = set()
            all_links = await page.query_selector_all('a')
            for link in all_links:
                try:
                    text = await link.inner_text()
                    if text and text.strip().startswith('#'):
                        clean_tag = text.strip().replace('#', '').strip()
                        if 1 < len(clean_tag) < 30:
                            all_tags_found.add(clean_tag)
                except:
                    pass

            data['search_tags'] = list(all_tags_found)

            # 10. product_url
            data['product_url'] = url

            # 11. thumbnail_url
            elem = await page.query_selector('img[class*="image"]')
            data['thumbnail_url'] = await elem.get_attribute('src') if elem else None

            # 12, 13. 타임스탬프
            now = datetime.now()
            data['crawled_at'] = now.isoformat()
            data['updated_at'] = now.isoformat()

            return data

        except Exception as e:
            print(f"   수집 오류: {str(e)[:50]}")
            return None


if __name__ == "__main__":
    async def test():
        crawler = SimpleCrawler(product_count=3, headless=False)
        products = await crawler.crawl()

        print("\n=== 수집 결과 ===")
        for i, p in enumerate(products, 1):
            print(f"{i}. {p.get('product_name', 'N/A')[:50]}")
            print(f"   가격: {p.get('price', 'N/A'):,}원")
            print(f"   브랜드: {p.get('brand_name', 'N/A')}")
            print(f"   태그: {len(p.get('search_tags', []))}개")

    asyncio.run(test())
