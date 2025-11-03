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

        # DB 연결 (save_to_db가 True일 때만)
        self.db = DatabaseConnector() if save_to_db else None

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

                # 2. 카테고리 진입
                print(f"[3/4] '{self.category_name}' 카테고리 진입...")
                category_btn = await page.wait_for_selector('button:has-text("카테고리")')
                await category_btn.click()
                await asyncio.sleep(1)

                womens = await page.wait_for_selector(f'a[data-name="{self.category_name}"]')
                await womens.click()
                await asyncio.sleep(3)

                # 3. 상품 링크 수집
                if self.product_count:
                    print(f"[4/4] 상품 {self.product_count}개 수집 시작...\n")
                else:
                    print(f"[4/4] 무한 수집 시작 (중지 버튼으로 멈출 수 있습니다)...\n")

                product_links = await page.query_selector_all('a[class*="ProductCard_link"]')

                collected_count = 0
                for idx, product in enumerate(product_links, 1):
                    # 무한 모드가 아니면 개수 체크
                    if self.product_count and collected_count >= self.product_count:
                        break
                    if self.should_stop:
                        break

                    try:
                        # 상품 클릭 (실제 클릭 방식)
                        await product.click()
                        await asyncio.sleep(2)

                        # 새 탭 찾기
                        all_pages = context.pages
                        if len(all_pages) <= 1:
                            print(f"[{idx}번] 탭 열림 실패 - SKIP")
                            continue

                        detail_page = all_pages[-1]
                        await detail_page.wait_for_load_state('domcontentloaded')
                        await asyncio.sleep(1)

                        # 상품 정보 수집
                        product_data = await self._collect_product_info(detail_page)

                        if product_data and product_data.get('product_name'):
                            self.products_data.append(product_data)
                            collected_count += 1

                            # 즉시 DB 저장
                            if self.save_to_db and self.db:
                                try:
                                    self.db.connect()
                                    self.db.save_product(product_data)
                                    self.db.close()
                                    print(f"[{collected_count}] {product_data['product_name'][:40]} - DB 저장 ✓")
                                except Exception as e:
                                    print(f"[{collected_count}] DB 저장 실패: {str(e)[:30]}")
                            else:
                                if self.product_count:
                                    print(f"[{collected_count}/{self.product_count}] {product_data['product_name'][:40]} ✓")
                                else:
                                    print(f"[{collected_count}] {product_data['product_name'][:40]} ✓")
                        else:
                            print(f"[{idx}번] 수집 실패 - SKIP")

                        # 탭 닫기
                        await detail_page.close()
                        await asyncio.sleep(1)

                    except Exception as e:
                        print(f"[{idx}번] 오류: {str(e)[:50]} - SKIP")
                        continue

                print(f"\n수집 완료! 총 {len(self.products_data)}개")

            finally:
                await browser.close()

            return self.products_data

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

            # 4. brand_name (테이블에서)
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.3)')
            await asyncio.sleep(0.5)

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

            # 9. search_tags (전체 스크롤)
            all_tags_found = set()
            for scroll_pos in range(10, 101, 10):
                await page.evaluate(f'window.scrollTo(0, document.body.scrollHeight * {scroll_pos/100})')
                await asyncio.sleep(0.3)

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
