"""
여성의류 카테고리 첫 번째 상품 크롤링 테스트
어떤 정보들을 수집할 수 있는지 확인
"""
import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
import re

class WomensClothingCrawler:
    def __init__(self, headless=False):
        self.headless = headless
        self.product_data = {}

    async def crawl_first_product(self):
        """여성의류 카테고리의 첫 번째 상품 크롤링"""
        async with async_playwright() as p:
            try:
                # 브라우저 시작
                print("[시작] Firefox 브라우저 실행...")
                browser = await p.firefox.launch(
                    headless=self.headless,
                    slow_mo=500  # 천천히 동작
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
                await asyncio.sleep(3)

                # 2. 쇼핑 아이콘 클릭 (새 탭으로 열림)
                print("[클릭] 쇼핑 아이콘 클릭...")
                shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
                shopping_link = await page.wait_for_selector(shopping_selector, timeout=10000)
                await shopping_link.click()
                await asyncio.sleep(3)

                # 3. 새 탭으로 전환
                all_pages = context.pages
                if len(all_pages) > 1:
                    page = all_pages[-1]  # 쇼핑 탭
                    await page.wait_for_load_state('networkidle')
                    print("[전환] 쇼핑 탭으로 전환 완료")

                # 4. 카테고리 버튼 클릭
                print("[클릭] 카테고리 메뉴 열기...")
                category_button_selector = 'button:has-text("카테고리")'
                category_button = await page.wait_for_selector(category_button_selector, timeout=10000)
                await category_button.click()
                await asyncio.sleep(2)

                # 5. 여성의류 카테고리 클릭
                print("[클릭] 여성의류 카테고리 선택...")
                womens_clothing_selector = 'a[data-name="여성의류"]'
                womens_clothing = await page.wait_for_selector(womens_clothing_selector, timeout=10000)
                await womens_clothing.click()
                await asyncio.sleep(3)

                # 2. 첫 번째 상품 찾기
                print("[탐색] 첫 번째 상품을 찾는 중...")

                # 상품 리스트 셀렉터들
                product_selectors = [
                    'div[class*="basicList"] a[class*="thumbnail"]',  # 썸네일 링크
                    'div[class*="product"] a[class*="link"]',  # 상품 링크
                    'li[class*="product"] a',  # 리스트 아이템
                    'div[class*="item"] a[href*="/products/"]'  # 상품 URL 포함
                ]

                first_product = None
                for selector in product_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            first_product = elements[0]  # 첫 번째 상품 선택
                            print(f"[선택] 첫 번째 상품 발견! (셀렉터: {selector})")
                            break
                    except:
                        continue

                if not first_product:
                    # 대안: 모든 링크에서 상품 찾기
                    all_links = await page.query_selector_all('a[href*="/products/"]')
                    if all_links:
                        first_product = all_links[0]
                        print("[선택] 대안 방법으로 첫 번째 상품 발견!")

                if first_product:
                    # 3. 상품 기본 정보 수집 (리스트 페이지에서)
                    print("[수집] 리스트 페이지에서 기본 정보 수집 중...")

                    # 상품 컨테이너 찾기
                    product_container = await first_product.evaluate_handle(
                        'el => el.closest("li, div[class*=\'product\'], div[class*=\'item\']")'
                    )

                    # 상품 ID 추출
                    product_url = await first_product.get_attribute('href')
                    product_id_match = re.search(r'/products/(\d+)', product_url or '')
                    product_id = product_id_match.group(1) if product_id_match else None

                    # 리스트 페이지에서 수집 가능한 정보
                    list_page_data = await self._extract_list_page_info(page, product_container)

                    # 4. 상품 상세 페이지 접속
                    print("[접속] 상품 상세 페이지로 이동 중...")
                    await first_product.click()

                    # 새 탭으로 전환
                    await asyncio.sleep(2)
                    all_pages = context.pages
                    if len(all_pages) > 1:
                        detail_page = all_pages[-1]
                        await detail_page.wait_for_load_state('networkidle')
                    else:
                        detail_page = page

                    await asyncio.sleep(3)

                    # 5. 상세 페이지에서 추가 정보 수집
                    print("[수집] 상세 페이지에서 전체 정보 수집 중...")
                    detail_page_data = await self._extract_detail_page_info(detail_page)

                    # 6. 모든 정보 통합
                    self.product_data = {
                        'product_id': product_id,
                        'crawled_at': datetime.now().isoformat(),
                        'category': '여성의류',
                        'list_page_info': list_page_data,
                        'detail_page_info': detail_page_data,
                        'url': detail_page.url
                    }

                    # 스크린샷 저장
                    await detail_page.screenshot(path='data/first_product_detail.png')
                    print("[저장] 상세 페이지 스크린샷 저장: data/first_product_detail.png")

                else:
                    print("[오류] 상품을 찾을 수 없습니다!")

                await browser.close()
                return self.product_data

            except Exception as e:
                print(f"[오류] 크롤링 중 오류 발생: {str(e)}")
                import traceback
                traceback.print_exc()
                raise

    async def _extract_list_page_info(self, page, container):
        """리스트 페이지에서 정보 추출"""
        info = {}

        try:
            # 상품명
            try:
                title_elem = await container.query_selector('[class*="title"], [class*="name"]')
                if title_elem:
                    info['product_name'] = await title_elem.inner_text()
            except:
                pass

            # 가격
            try:
                price_elem = await container.query_selector('[class*="price"] strong, [class*="price_num"]')
                if price_elem:
                    price_text = await price_elem.inner_text()
                    info['price'] = price_text.replace(',', '').replace('원', '')
            except:
                pass

            # 할인율
            try:
                discount_elem = await container.query_selector('[class*="discount"]')
                if discount_elem:
                    info['discount_rate'] = await discount_elem.inner_text()
            except:
                pass

            # 리뷰 수
            try:
                review_elem = await container.query_selector('[class*="review"] em, [class*="review_num"]')
                if review_elem:
                    review_text = await review_elem.inner_text()
                    info['review_count'] = review_text.replace(',', '')
            except:
                pass

            # 평점
            try:
                rating_elem = await container.query_selector('[class*="rating"], [class*="star"]')
                if rating_elem:
                    info['rating'] = await rating_elem.inner_text()
            except:
                pass

            # 브랜드/몰 이름
            try:
                mall_elem = await container.query_selector('[class*="mall"], [class*="brand"]')
                if mall_elem:
                    info['brand_name'] = await mall_elem.inner_text()
            except:
                pass

            # 썸네일 이미지
            try:
                img_elem = await container.query_selector('img')
                if img_elem:
                    info['thumbnail_url'] = await img_elem.get_attribute('src')
            except:
                pass

            # 배송 정보
            try:
                delivery_elem = await container.query_selector('[class*="delivery"]')
                if delivery_elem:
                    info['delivery_info'] = await delivery_elem.inner_text()
            except:
                pass

        except Exception as e:
            print(f"[경고] 리스트 페이지 정보 추출 중 오류: {str(e)}")

        return info

    async def _extract_detail_page_info(self, page):
        """상세 페이지에서 정보 추출"""
        info = {}

        try:
            # 상품명 (상세)
            try:
                title_selectors = [
                    'h3[class*="title"]',
                    'h2[class*="title"]',
                    'div[class*="top"] h3',
                    '[class*="product_title"]'
                ]
                for selector in title_selectors:
                    elem = await page.query_selector(selector)
                    if elem:
                        info['product_name'] = await elem.inner_text()
                        break
            except:
                pass

            # 가격 (상세)
            try:
                price_selectors = [
                    'span[class*="price"] em',
                    'strong[class*="price"]',
                    '[class*="total_price"]'
                ]
                for selector in price_selectors:
                    elem = await page.query_selector(selector)
                    if elem:
                        price_text = await elem.inner_text()
                        info['price'] = price_text.replace(',', '').replace('원', '')
                        break
            except:
                pass

            # 옵션 정보
            try:
                option_selectors = await page.query_selector_all('[class*="option"] select, [class*="option"] button')
                options = []
                for opt in option_selectors[:5]:  # 최대 5개 옵션
                    opt_text = await opt.inner_text()
                    if opt_text:
                        options.append(opt_text)
                if options:
                    info['options'] = options
            except:
                pass

            # 상품 상세 정보
            try:
                detail_selectors = [
                    '[class*="detail_info"]',
                    '[class*="product_info"]',
                    'table[class*="spec"]'
                ]
                for selector in detail_selectors:
                    elem = await page.query_selector(selector)
                    if elem:
                        detail_text = await elem.inner_text()
                        info['detail_info'] = detail_text[:500]  # 처음 500자만
                        break
            except:
                pass

            # 판매자 정보
            try:
                seller_elem = await page.query_selector('[class*="seller"], [class*="store"]')
                if seller_elem:
                    info['seller_info'] = await seller_elem.inner_text()
            except:
                pass

            # 배송 정보 (상세)
            try:
                delivery_selectors = [
                    '[class*="delivery_info"]',
                    '[class*="shipping"]',
                    'div:has-text("배송")'
                ]
                for selector in delivery_selectors:
                    try:
                        elem = await page.query_selector(selector)
                        if elem:
                            info['delivery_detail'] = await elem.inner_text()
                            break
                    except:
                        continue
            except:
                pass

            # 카테고리 경로
            try:
                breadcrumb = await page.query_selector('[class*="breadcrumb"], [class*="location"]')
                if breadcrumb:
                    info['category_path'] = await breadcrumb.inner_text()
            except:
                pass

            # 상품 코드/모델명
            try:
                code_elem = await page.query_selector('text=/상품코드|모델명/')
                if code_elem:
                    parent = await code_elem.evaluate_handle('el => el.parentElement')
                    info['product_code'] = await parent.inner_text()
            except:
                pass

            # 태그/키워드
            try:
                tag_elems = await page.query_selector_all('[class*="tag"], [class*="keyword"]')
                tags = []
                for tag in tag_elems[:10]:  # 최대 10개 태그
                    tag_text = await tag.inner_text()
                    if tag_text:
                        tags.append(tag_text)
                if tags:
                    info['tags'] = tags
            except:
                pass

            # 이미지 URL들
            try:
                image_elems = await page.query_selector_all('[class*="thumb"] img, [class*="product_img"] img')
                images = []
                for img in image_elems[:5]:  # 최대 5개 이미지
                    src = await img.get_attribute('src')
                    if src:
                        images.append(src)
                if images:
                    info['image_urls'] = images
            except:
                pass

        except Exception as e:
            print(f"[경고] 상세 페이지 정보 추출 중 오류: {str(e)}")

        return info

    def save_results(self, filename=None):
        """결과를 JSON 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/womens_clothing_first_product_{timestamp}.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.product_data, f, ensure_ascii=False, indent=2)

        print(f"[저장] 크롤링 결과 저장: {filename}")
        return filename

    def print_summary(self):
        """수집된 정보 요약 출력"""
        print("\n" + "=" * 60)
        print("수집 가능한 상품 정보 목록")
        print("=" * 60)

        if self.product_data:
            print(f"\n[기본 정보]")
            print(f"- 상품 ID: {self.product_data.get('product_id', 'N/A')}")
            print(f"- 카테고리: {self.product_data.get('category', 'N/A')}")
            print(f"- URL: {self.product_data.get('url', 'N/A')}")

            print(f"\n[리스트 페이지에서 수집 가능한 정보]")
            if 'list_page_info' in self.product_data:
                for key, value in self.product_data['list_page_info'].items():
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"- {key}: {value}")

            print(f"\n[상세 페이지에서 추가 수집 가능한 정보]")
            if 'detail_page_info' in self.product_data:
                for key, value in self.product_data['detail_page_info'].items():
                    if isinstance(value, list):
                        print(f"- {key}: {len(value)}개 항목")
                    elif isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                        print(f"- {key}: {value}")
                    else:
                        print(f"- {key}: {value}")

        print("\n" + "=" * 60)


# 실행
if __name__ == "__main__":
    async def main():
        crawler = WomensClothingCrawler(headless=False)

        # 크롤링 실행
        data = await crawler.crawl_first_product()

        # 결과 저장
        if data:
            crawler.save_results()

            # 요약 출력
            crawler.print_summary()

            print("\n[완료] 첫 번째 상품 크롤링 및 분석 완료!")
        else:
            print("\n[실패] 상품 정보를 수집하지 못했습니다.")

    asyncio.run(main())