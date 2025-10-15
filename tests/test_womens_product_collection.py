"""
여성의류 첫 번째 상품 정보 수집
실제로 상품 정보를 추출하여 DB에 저장
"""
import asyncio
import json
import psycopg2
from datetime import datetime
from playwright.async_api import async_playwright
import re
from typing import Dict, Optional

class WomensProductCollector:
    def __init__(self, headless=False):
        self.headless = headless
        self.product_data = {}
        self.db_conn = None

    def connect_db(self):
        """PostgreSQL 데이터베이스 연결"""
        try:
            self.db_conn = psycopg2.connect(
                host="localhost",
                database="naver",
                user="postgres",
                password="postgres"  # 실제 비밀번호로 변경 필요
            )
            print("[DB] 데이터베이스 연결 성공")
            return True
        except Exception as e:
            print(f"[DB] 데이터베이스 연결 실패: {str(e)}")
            return False

    async def collect_first_product(self):
        """여성의류 첫 번째 상품 수집"""
        async with async_playwright() as p:
            try:
                print("[시작] Firefox 브라우저 실행...")
                browser = await p.firefox.launch(
                    headless=self.headless,
                    slow_mo=300
                )

                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                    locale='ko-KR',
                    timezone_id='Asia/Seoul'
                )

                page = await context.new_page()

                # 1. 네이버 메인 → 쇼핑 → 카테고리 → 여성의류
                print("[접속] 네이버 메인...")
                await page.goto('https://www.naver.com')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)

                print("[클릭] 쇼핑...")
                shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a')
                await shopping_link.click()
                await asyncio.sleep(3)

                # 새 탭 전환
                all_pages = context.pages
                if len(all_pages) > 1:
                    page = all_pages[-1]
                    await page.wait_for_load_state('networkidle')

                print("[클릭] 카테고리 버튼...")
                category_btn = await page.wait_for_selector('button:has-text("카테고리")')
                await category_btn.click()
                await asyncio.sleep(2)

                print("[클릭] 여성의류...")
                womens = await page.wait_for_selector('a[data-name="여성의류"]')
                await womens.click()
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(3)

                # 2. 첫 번째 상품 찾기
                print("\n[수집] 첫 번째 상품 정보 추출 중...")

                # 상품 리스트 컨테이너 찾기
                product_selectors = [
                    'li.productList_item__',  # 실제 클래스명 일부
                    'div[class*="basicList_item"]',
                    'li[class*="product_item"]',
                    'div[class*="product_list"] > div'
                ]

                first_product = None
                for selector in product_selectors:
                    products = await page.query_selector_all(selector)
                    if products and len(products) > 0:
                        first_product = products[0]
                        print(f"✅ 첫 번째 상품 발견! (셀렉터: {selector})")
                        break

                if not first_product:
                    # 대안: 첫 번째 상품 링크 찾기
                    product_links = await page.query_selector_all('a[href*="/products/"]')
                    if product_links:
                        # 첫 번째 상품 링크의 부모 컨테이너 찾기
                        first_product = await product_links[0].evaluate_handle(
                            'el => el.closest("li, div[class*=\'product\']")'
                        )
                        print("✅ 대안 방법으로 첫 번째 상품 발견!")

                if first_product:
                    # 상품 정보 추출
                    product_info = await self._extract_product_info(first_product)

                    # 상품 URL로부터 ID 추출
                    product_link = await first_product.query_selector('a[href*="/products/"]')
                    if product_link:
                        href = await product_link.get_attribute('href')
                        id_match = re.search(r'/products/(\d+)', href)
                        if id_match:
                            product_info['product_id'] = id_match.group(1)
                            product_info['url'] = f"https://search.shopping.naver.com{href}" if href.startswith('/') else href

                    self.product_data = {
                        'category': '여성의류',
                        'category_id': 10000107,
                        'crawled_at': datetime.now().isoformat(),
                        'product': product_info
                    }

                    # 스크린샷 저장
                    await page.screenshot(path='data/womens_clothing_success.png')
                    print("📸 스크린샷 저장: data/womens_clothing_success.png")

                    await browser.close()
                    return self.product_data

                else:
                    print("[오류] 상품을 찾을 수 없습니다!")
                    await page.screenshot(path='data/no_products_found.png')

                await browser.close()
                return None

            except Exception as e:
                print(f"[오류] {str(e)}")
                import traceback
                traceback.print_exc()
                return None

    async def _extract_product_info(self, element) -> Dict:
        """상품 요소에서 정보 추출"""
        info = {}

        try:
            # 상품명
            name_selectors = [
                'a[class*="title"]',
                'a[class*="name"]',
                'div[class*="name"]',
                '[class*="basicList_title"]'
            ]
            for selector in name_selectors:
                name_elem = await element.query_selector(selector)
                if name_elem:
                    info['product_name'] = await name_elem.inner_text()
                    print(f"  ✓ 상품명: {info['product_name'][:40]}...")
                    break

            # 가격
            price_selectors = [
                'span[class*="price"] > em',
                'span[class*="price_num"]',
                'strong[class*="price"]',
                '[class*="basicList_price"] em'
            ]
            for selector in price_selectors:
                price_elem = await element.query_selector(selector)
                if price_elem:
                    price_text = await price_elem.inner_text()
                    info['price'] = int(price_text.replace(',', '').replace('원', ''))
                    print(f"  ✓ 가격: {info['price']:,}원")
                    break

            # 브랜드/판매몰
            brand_selectors = [
                'a[class*="mall"]',
                'span[class*="mall"]',
                '[class*="basicList_mall"]'
            ]
            for selector in brand_selectors:
                brand_elem = await element.query_selector(selector)
                if brand_elem:
                    info['brand_name'] = await brand_elem.inner_text()
                    print(f"  ✓ 브랜드: {info['brand_name']}")
                    break

            # 리뷰 수
            review_selectors = [
                'em[class*="review"]',
                '[class*="basicList_etc"] em',
                'a[class*="review"] em'
            ]
            for selector in review_selectors:
                review_elem = await element.query_selector(selector)
                if review_elem:
                    review_text = await review_elem.inner_text()
                    # "리뷰 1,234" 형태에서 숫자만 추출
                    numbers = re.findall(r'[\d,]+', review_text)
                    if numbers:
                        info['review_count'] = int(numbers[0].replace(',', ''))
                        print(f"  ✓ 리뷰: {info['review_count']:,}개")
                    break

            # 평점
            rating_elem = await element.query_selector('[class*="star"], [class*="rating"]')
            if rating_elem:
                rating_text = await rating_elem.inner_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    info['rating'] = float(rating_match.group(1))
                    print(f"  ✓ 평점: {info['rating']}")

            # 할인율
            discount_elem = await element.query_selector('[class*="discount"]')
            if discount_elem:
                discount_text = await discount_elem.inner_text()
                discount_match = re.search(r'(\d+)%', discount_text)
                if discount_match:
                    info['discount_rate'] = int(discount_match.group(1))
                    print(f"  ✓ 할인율: {info['discount_rate']}%")

            # 썸네일 이미지
            img_elem = await element.query_selector('img')
            if img_elem:
                info['thumbnail_url'] = await img_elem.get_attribute('src')
                print(f"  ✓ 썸네일: 수집 완료")

            # 배송 정보
            delivery_elem = await element.query_selector('[class*="delivery"]')
            if delivery_elem:
                delivery_text = await delivery_elem.inner_text()
                info['delivery_info'] = delivery_text
                print(f"  ✓ 배송: {delivery_text}")

            # 품절 여부
            soldout_elem = await element.query_selector('[class*="soldout"], text="품절"')
            info['is_sold_out'] = soldout_elem is not None

        except Exception as e:
            print(f"[경고] 정보 추출 중 오류: {str(e)}")

        return info

    def save_to_db(self):
        """PostgreSQL DB에 저장"""
        if not self.product_data or 'product' not in self.product_data:
            print("[DB] 저장할 데이터가 없습니다.")
            return False

        if not self.db_conn:
            if not self.connect_db():
                return False

        try:
            cursor = self.db_conn.cursor()
            product = self.product_data['product']

            # 카테고리 확인/삽입
            cursor.execute("""
                INSERT INTO categories (category_id, category_name, category_level, category_url, category_path)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (category_id) DO NOTHING
            """, (
                10000107,
                '여성의류',
                1,
                'https://search.shopping.naver.com/category/category/10000107',
                '여성의류'
            ))

            # 상품 삽입/업데이트
            cursor.execute("""
                INSERT INTO products (
                    product_id, category_id, category_name, product_name,
                    brand_name, price, discount_rate, review_count, rating,
                    product_url, thumbnail_url, is_sold_out
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_id) DO UPDATE SET
                    price = EXCLUDED.price,
                    discount_rate = EXCLUDED.discount_rate,
                    review_count = EXCLUDED.review_count,
                    rating = EXCLUDED.rating,
                    is_sold_out = EXCLUDED.is_sold_out,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                product.get('product_id'),
                10000107,
                '여성의류',
                product.get('product_name'),
                product.get('brand_name'),
                product.get('price'),
                product.get('discount_rate'),
                product.get('review_count', 0),
                product.get('rating'),
                product.get('url'),
                product.get('thumbnail_url'),
                product.get('is_sold_out', False)
            ))

            self.db_conn.commit()
            print("\n✅ DB 저장 완료!")
            print(f"  - 상품 ID: {product.get('product_id')}")
            print(f"  - 상품명: {product.get('product_name', 'N/A')[:50]}...")

            cursor.close()
            return True

        except Exception as e:
            print(f"[DB] 저장 실패: {str(e)}")
            if self.db_conn:
                self.db_conn.rollback()
            return False

    def save_to_json(self):
        """JSON 파일로도 저장 (백업)"""
        if not self.product_data:
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/womens_product_{timestamp}.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.product_data, f, ensure_ascii=False, indent=2)

        print(f"[JSON] 백업 저장: {filename}")
        return filename

    def print_summary(self):
        """수집 결과 요약"""
        print("\n" + "="*60)
        print("📊 네이버 쇼핑 여성의류 - 수집 가능한 정보")
        print("="*60)

        print("\n✅ 수집 가능한 정보 (리스트 페이지):")
        print("1. product_id - 상품 고유 ID")
        print("2. product_name - 상품명")
        print("3. price - 가격")
        print("4. brand_name - 브랜드/판매몰")
        print("5. review_count - 리뷰 수")
        print("6. rating - 평점 (0.0~5.0)")
        print("7. discount_rate - 할인율 (%)")
        print("8. delivery_info - 배송 정보")
        print("9. thumbnail_url - 썸네일 이미지")
        print("10. is_sold_out - 품절 여부")
        print("11. product_url - 상품 상세 페이지 URL")

        if self.product_data and 'product' in self.product_data:
            product = self.product_data['product']
            print("\n📦 실제 수집된 첫 번째 상품:")
            for key, value in product.items():
                if isinstance(value, str) and len(value) > 80:
                    value = value[:80] + "..."
                print(f"  - {key}: {value}")

        print("="*60)


if __name__ == "__main__":
    async def main():
        print("="*60)
        print("여성의류 첫 번째 상품 정보 수집 및 DB 저장")
        print("="*60)

        collector = WomensProductCollector(headless=False)

        # 상품 정보 수집
        data = await collector.collect_first_product()

        if data:
            # JSON 백업
            collector.save_to_json()

            # DB 저장 시도
            collector.save_to_db()

            # 요약 출력
            collector.print_summary()

            print("\n✅ 작업 완료!")
        else:
            print("\n❌ 상품 정보 수집 실패")

    asyncio.run(main())