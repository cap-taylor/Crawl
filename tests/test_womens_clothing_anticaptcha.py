"""
여성의류 카테고리 첫 번째 상품 크롤링 - 캡차 회피 버전
사람처럼 행동하여 캡차를 회피
"""
import asyncio
import json
import random
from datetime import datetime
from playwright.async_api import async_playwright
import re

class WomensClothingCrawlerAntiCaptcha:
    def __init__(self, headless=False):
        self.headless = headless
        self.product_data = {}

    async def random_delay(self, min_sec=2, max_sec=5):
        """랜덤 대기 시간"""
        delay = random.uniform(min_sec, max_sec)
        print(f"[대기] {delay:.1f}초 대기 중...")
        await asyncio.sleep(delay)

    async def human_like_scroll(self, page):
        """사람처럼 스크롤"""
        print("[스크롤] 페이지 스크롤 중...")
        # 천천히 여러 번 나눠서 스크롤
        for _ in range(3):
            scroll_amount = random.randint(300, 600)
            await page.evaluate(f'window.scrollBy(0, {scroll_amount})')
            await asyncio.sleep(random.uniform(0.5, 1.5))

        # 맨 위로 돌아가기
        await asyncio.sleep(1)
        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(1)

    async def crawl_first_product(self):
        """여성의류 카테고리의 첫 번째 상품 크롤링"""
        async with async_playwright() as p:
            try:
                # 브라우저 시작
                print("[시작] Firefox 브라우저 실행...")
                browser = await p.firefox.launch(
                    headless=self.headless,
                    slow_mo=1000  # 더 천천히 동작
                )

                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                    locale='ko-KR',
                    timezone_id='Asia/Seoul'
                )

                page = await context.new_page()

                # 1. 네이버 메인 접속
                print("[접속] 네이버 메인 페이지 로드 중...")
                await page.goto('https://www.naver.com')
                await page.wait_for_load_state('networkidle')
                await self.random_delay(3, 5)

                # 페이지 스크롤 (사람처럼)
                await self.human_like_scroll(page)

                # 2. 쇼핑 아이콘 찾고 호버 후 클릭
                print("[탐색] 쇼핑 아이콘 찾는 중...")
                shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
                shopping_link = await page.wait_for_selector(shopping_selector, timeout=10000)

                # 호버 후 클릭
                print("[호버] 쇼핑 아이콘에 마우스 올리기...")
                await shopping_link.hover()
                await asyncio.sleep(random.uniform(0.5, 1.5))

                print("[클릭] 쇼핑 아이콘 클릭...")
                await shopping_link.click()
                await self.random_delay(3, 5)

                # 3. 새 탭으로 전환
                all_pages = context.pages
                if len(all_pages) > 1:
                    page = all_pages[-1]  # 쇼핑 탭
                    await page.wait_for_load_state('networkidle')
                    print("[전환] 쇼핑 탭으로 전환 완료")
                    await self.random_delay(2, 4)

                # 쇼핑 페이지에서도 스크롤
                await self.human_like_scroll(page)

                # 4. 카테고리 버튼 찾기 - 다양한 셀렉터 시도
                print("[탐색] 카테고리 버튼 찾는 중...")
                category_button = None

                # 여러 셀렉터 시도
                category_selectors = [
                    'button:has-text("카테고리")',
                    'button[aria-label*="카테고리"]',
                    '[class*="category"][class*="button"]',
                    'button span:has-text("카테고리")'
                ]

                for selector in category_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for elem in elements:
                            text = await elem.inner_text()
                            if "카테고리" in text:
                                category_button = elem
                                print(f"[발견] 카테고리 버튼 찾음: {selector}")
                                break
                        if category_button:
                            break
                    except:
                        continue

                if category_button:
                    # 호버 후 클릭
                    print("[호버] 카테고리 버튼에 마우스 올리기...")
                    await category_button.hover()
                    await asyncio.sleep(random.uniform(1, 2))

                    print("[클릭] 카테고리 메뉴 열기...")
                    await category_button.click()
                    await self.random_delay(2, 3)

                    # 5. 여성의류 카테고리 찾기
                    print("[탐색] 여성의류 카테고리 찾는 중...")

                    womens_selectors = [
                        'a[data-name="여성의류"]',
                        'a[data-id="10000107"]',
                        'a:has-text("여성의류")'
                    ]

                    womens_clothing = None
                    for selector in womens_selectors:
                        try:
                            womens_clothing = await page.query_selector(selector)
                            if womens_clothing:
                                print(f"[발견] 여성의류 카테고리 찾음: {selector}")
                                break
                        except:
                            continue

                    if womens_clothing:
                        # 호버 후 클릭
                        print("[호버] 여성의류 카테고리에 마우스 올리기...")
                        await womens_clothing.hover()
                        await asyncio.sleep(random.uniform(1, 2))

                        print("[클릭] 여성의류 카테고리 선택...")
                        await womens_clothing.click()
                        await self.random_delay(3, 5)

                        # 페이지 로드 완료 대기
                        await page.wait_for_load_state('networkidle')

                        # 스크롤하여 상품 로드
                        await self.human_like_scroll(page)

                        # 6. 첫 번째 상품 찾기
                        print("[탐색] 첫 번째 상품을 찾는 중...")

                        # 더 구체적인 상품 셀렉터
                        product_selectors = [
                            'li[class*="product"] a[class*="thumbnail"]',
                            'div[class*="product_item"] a',
                            'div[class*="basicList"] a[class*="thumbnail"]',
                            'a[href*="/products/"]'
                        ]

                        first_product = None
                        for selector in product_selectors:
                            try:
                                await page.wait_for_selector(selector, timeout=5000)
                                elements = await page.query_selector_all(selector)
                                if elements:
                                    first_product = elements[0]
                                    print(f"[선택] 첫 번째 상품 발견! (셀렉터: {selector})")

                                    # 상품 URL 확인
                                    href = await first_product.get_attribute('href')
                                    if href and '/products/' in href:
                                        print(f"[확인] 상품 URL: {href[:50]}...")
                                        break
                            except:
                                continue

                        if first_product:
                            # 상품 정보 수집
                            await self._collect_product_info(page, first_product)

                            # 스크린샷 저장
                            await page.screenshot(path='data/womens_clothing_page.png')
                            print("[저장] 페이지 스크린샷 저장: data/womens_clothing_page.png")
                        else:
                            print("[오류] 상품을 찾을 수 없습니다!")
                            # 디버깅용 스크린샷
                            await page.screenshot(path='data/debug_no_products.png')
                            print("[디버그] 현재 페이지 스크린샷: data/debug_no_products.png")
                    else:
                        print("[오류] 여성의류 카테고리를 찾을 수 없습니다!")
                else:
                    print("[오류] 카테고리 버튼을 찾을 수 없습니다!")
                    # 디버깅용 스크린샷
                    await page.screenshot(path='data/debug_no_category.png')
                    print("[디버그] 현재 페이지 스크린샷: data/debug_no_category.png")

                await browser.close()
                return self.product_data

            except Exception as e:
                print(f"[오류] 크롤링 중 오류 발생: {str(e)}")
                import traceback
                traceback.print_exc()
                raise

    async def _collect_product_info(self, page, product_element):
        """상품 정보 수집"""
        print("[수집] 상품 정보 수집 중...")

        try:
            # 상품 컨테이너 찾기
            container = await product_element.evaluate_handle(
                'el => el.closest("li, div[class*=\'product\']")'
            )

            info = {}

            # 상품명
            try:
                title_elem = await container.query_selector('[class*="title"], [class*="name"]')
                if title_elem:
                    info['product_name'] = await title_elem.inner_text()
                    print(f"  - 상품명: {info['product_name'][:30]}...")
            except:
                pass

            # 가격
            try:
                price_elem = await container.query_selector('[class*="price"] strong, [class*="price_num"]')
                if price_elem:
                    price_text = await price_elem.inner_text()
                    info['price'] = price_text.replace(',', '').replace('원', '')
                    print(f"  - 가격: {info['price']}원")
            except:
                pass

            # 브랜드
            try:
                brand_elem = await container.query_selector('[class*="brand"], [class*="mall"]')
                if brand_elem:
                    info['brand'] = await brand_elem.inner_text()
                    print(f"  - 브랜드: {info['brand']}")
            except:
                pass

            # 리뷰
            try:
                review_elem = await container.query_selector('[class*="review"]')
                if review_elem:
                    review_text = await review_elem.inner_text()
                    info['review'] = review_text
                    print(f"  - 리뷰: {info['review']}")
            except:
                pass

            # URL
            try:
                href = await product_element.get_attribute('href')
                if href:
                    info['url'] = href
                    # 상품 ID 추출
                    id_match = re.search(r'/products/(\d+)', href)
                    if id_match:
                        info['product_id'] = id_match.group(1)
                        print(f"  - 상품 ID: {info['product_id']}")
            except:
                pass

            self.product_data = {
                'category': '여성의류',
                'crawled_at': datetime.now().isoformat(),
                'product_info': info
            }

            print(f"[완료] {len(info)}개 항목 수집 완료")

        except Exception as e:
            print(f"[경고] 정보 수집 중 오류: {str(e)}")

    def save_results(self, filename=None):
        """결과를 JSON 파일로 저장"""
        if not self.product_data:
            print("[경고] 저장할 데이터가 없습니다.")
            return None

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/womens_first_product_{timestamp}.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.product_data, f, ensure_ascii=False, indent=2)

        print(f"[저장] 크롤링 결과 저장: {filename}")
        return filename

    def print_summary(self):
        """수집된 정보 요약 출력"""
        print("\n" + "=" * 60)
        print("수집된 상품 정보")
        print("=" * 60)

        if self.product_data and 'product_info' in self.product_data:
            info = self.product_data['product_info']
            print(f"카테고리: {self.product_data.get('category', 'N/A')}")
            print(f"수집 시간: {self.product_data.get('crawled_at', 'N/A')}")
            print(f"\n수집 가능한 정보 목록:")
            for key, value in info.items():
                if len(str(value)) > 50:
                    value = str(value)[:50] + "..."
                print(f"  - {key}: {value}")
        else:
            print("수집된 정보가 없습니다.")

        print("=" * 60)


# 실행
if __name__ == "__main__":
    async def main():
        crawler = WomensClothingCrawlerAntiCaptcha(headless=False)

        print("\n" + "=" * 60)
        print("여성의류 첫 번째 상품 크롤링 (캡차 회피)")
        print("=" * 60)
        print("사람처럼 행동하여 캡차를 회피합니다...")
        print("- 랜덤 대기 시간")
        print("- 마우스 호버")
        print("- 페이지 스크롤")
        print("=" * 60 + "\n")

        # 크롤링 실행
        data = await crawler.crawl_first_product()

        # 결과 저장 및 출력
        if data:
            crawler.save_results()
            crawler.print_summary()
            print("\n[성공] 크롤링 완료!")
        else:
            print("\n[실패] 상품 정보를 수집하지 못했습니다.")

    asyncio.run(main())