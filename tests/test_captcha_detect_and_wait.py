"""
캡차 감지 및 수동 해결 대기
캡차가 나타나면 알림을 주고 사용자가 해결할 때까지 대기
"""
import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
import re

class CaptchaDetectorAndWait:
    def __init__(self, headless=False):
        self.headless = headless
        self.product_data = {}

    async def collect_product_info(self, detail_page, product_id):
        """상세 페이지에서 상품 정보 수집"""
        product_info = {'product_id': product_id}

        try:
            # 페이지 하단으로 스크롤 (해시태그는 하단에 있음)
            await detail_page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)

            # 상품명 (스크린샷에서 확인: h3 태그)
            # 디버깅: 모든 h3 찾기
            all_h3 = await detail_page.query_selector_all('h3')
            print(f"   [디버그] 찾은 h3 태그 개수: {len(all_h3)}")
            for idx, h3 in enumerate(all_h3[:5]):
                text = await h3.inner_text()
                print(f"   [디버그] h3[{idx}]: {text[:50] if text else '(빈 문자열)'}...")

            name_elem = await detail_page.query_selector('h3')
            if not name_elem:
                name_elem = await detail_page.query_selector('h2')
            if not name_elem:
                name_elem = await detail_page.query_selector('h1')
            if name_elem:
                name_text = (await name_elem.inner_text()).strip()
                if name_text:
                    product_info['product_name'] = name_text
                    print(f"   [디버그] 상품명 수집 성공: {name_text[:30]}...")

            # 가격 (여러 셀렉터 시도)
            price_selectors = [
                'strong.zPdReA',  # 스마트스토어 가격
                'span[class*="price"]',
                'strong[class*="price"]',
                'div[class*="price"] strong',
                'em[class*="price"]'
            ]
            for price_sel in price_selectors:
                price_elem = await detail_page.query_selector(price_sel)
                if price_elem:
                    price_text = await price_elem.inner_text()
                    price_nums = re.findall(r'[\d,]+', price_text)
                    if price_nums:
                        product_info['price'] = price_nums[0].replace(',', '')
                        break

            # 해시태그 찾기 (스크린샷에서 확인: a._1JswZdbu)
            hashtags = []
            # 여러 패턴 시도 (하드코딩 없이)
            tag_selectors = [
                'a[class*="_1JswZdbu"]',  # 스마트스토어 스타일
                'a[href*="/search"][class*="linkAnchor"]',  # 검색 링크
                'a.oe34bePu',  # 다른 스타일
                'ul[class*="related"] a',  # 연관 태그
                'div[class*="tag"] a',  # 태그 영역
                'a[href*="/search/"]'  # 일반 검색 링크
            ]

            for tag_sel in tag_selectors:
                tag_elements = await detail_page.query_selector_all(tag_sel)
                if tag_elements:
                    print(f"   [디버그] 검색태그 발견: {tag_sel} ({len(tag_elements)}개)")
                    break

            for tag_elem in tag_elements[:30]:
                tag_text = await tag_elem.inner_text()
                if tag_text and tag_text.strip():
                    hashtags.append(tag_text.strip())

            if hashtags:
                product_info['search_tags'] = ', '.join(hashtags)
                print(f"   [디버그] 검색태그 수집: {len(hashtags)}개")

            # 리뷰
            review_elem = await detail_page.query_selector('[class*="review"]')
            if review_elem:
                review_text = await review_elem.inner_text()
                numbers = re.findall(r'[\d,]+', review_text)
                if numbers:
                    product_info['review_count'] = numbers[0].replace(',', '')

            # 평점
            rating_elem = await detail_page.query_selector('[class*="star"], [class*="rating"]')
            if rating_elem:
                rating_text = await rating_elem.inner_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    product_info['rating'] = rating_match.group(1)

            # URL
            product_info['url'] = detail_page.url

            return product_info

        except Exception as e:
            print(f"   정보 수집 오류: {str(e)[:50]}")
            return None

    async def crawl_with_manual_captcha(self):
        """캡차 감지 및 수동 해결 대기 크롤링"""
        async with async_playwright() as p:
            try:
                print("[시작] Firefox 브라우저 실행...")
                browser = await p.firefox.launch(
                    headless=False,  # 항상 보이도록
                    slow_mo=500  # CRAWLING_LESSONS_LEARNED.md에 따라 천천히
                )

                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                    locale='ko-KR',
                    timezone_id='Asia/Seoul'
                )

                page = await context.new_page()

                # 1. 네이버 메인 접속
                print("\n[1단계] 네이버 메인 접속...")
                await page.goto('https://www.naver.com', timeout=60000)
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(1)  # 더 짧게

                # 네이버 메인에서는 캡차 체크 생략 (캡차 없음)

                # 2. 쇼핑 클릭
                print("\n[2단계] 쇼핑 페이지로 이동...")
                shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a')
                await shopping_link.click()
                await asyncio.sleep(1.5)  # 더 빠르게

                # 새 탭 전환 (CRAWLING_LESSONS_LEARNED.md: 새 탭으로 열어야 캡차 안 나옴!)
                await asyncio.sleep(3)  # 탭 열리기 대기
                all_pages = context.pages
                if len(all_pages) > 1:
                    page = all_pages[-1]  # 마지막 탭 = 쇼핑 탭
                    await page.wait_for_load_state('networkidle')
                    print("✅ 새 탭(쇼핑)으로 전환 완료")

                # 쇼핑 메인에서도 캡차 체크 생략

                # 3. 카테고리 버튼 클릭
                print("\n[3단계] 카테고리 메뉴 열기...")
                category_btn = await page.wait_for_selector('button:has-text("카테고리")')
                await category_btn.click()
                await asyncio.sleep(1)  # 더 빠르게

                # 4. 여성의류 클릭 (data-name 속성 사용이 더 안정적)
                print("\n[4단계] 여성의류 카테고리 선택...")
                # 먼저 호버하고 클릭 (사람처럼)
                womens = await page.wait_for_selector('a[data-name="여성의류"]')
                await womens.hover()  # 호버 추가
                await asyncio.sleep(1)  # 호버 후 대기
                await womens.click()

                print("\n⏳ 캡차가 뜰 수 있습니다. 30초 대기 중...")
                print("캡차가 나타나면 직접 해결해주세요!")
                print("한글 입력 안되면: 메모장에 답 적고 복사-붙여넣기 하세요!")
                await asyncio.sleep(30)  # 30초 대기 - 캡차 해결 시간

                await page.wait_for_load_state('networkidle')
                print("✅ 계속 진행합니다...")

                # 5. 일반 상품 첫 번째 클릭해서 정보 수집
                print("\n[5단계] 일반 상품 첫 번째 클릭...")

                # 페이지 로딩 확인을 위한 추가 대기
                await asyncio.sleep(3)

                # 일반 상품 영역까지 스크롤
                print("일반 상품 영역까지 스크롤 중...")
                for i in range(3):  # 초기 스크롤
                    await page.evaluate(f'window.scrollBy(0, 1000)')
                    await asyncio.sleep(1)

                # 일반 상품 첫 번째 찾기 (docs/selectors/일반 상품.txt 참고)
                first_product = await page.wait_for_selector('#composite-card-list > div > ul:nth-child(1) > li:nth-child(1) > div > a')

                if first_product:
                    print("✅ 일반 상품 첫 번째 찾음!")

                    # 상품 ID 추출
                    href = await first_product.get_attribute('href')
                    id_match = re.search(r'/products/(\d+)', href)
                    product_id = id_match.group(1) if id_match else 'unknown'
                    print(f"상품 ID: {product_id}")

                    # 상품 클릭
                    await first_product.click()
                    await asyncio.sleep(3)

                    # 새 탭으로 전환
                    all_pages = context.pages
                    if len(all_pages) > 2:
                        detail_page = all_pages[-1]
                        await detail_page.wait_for_load_state('networkidle')
                        print("✅ 상세 페이지 열림")

                        # 디버깅: 스크린샷 저장
                        await detail_page.screenshot(path='data/product_detail_debug.png')

                        # 상품 정보 수집
                        product_info = await self.collect_product_info(detail_page, product_id)

                        if product_info:
                            print(f"\n{'='*60}")
                            print("📦 수집된 상품 정보:")
                            print(f"{'='*60}")
                            print(f"🆔 상품 ID: {product_info.get('product_id', 'N/A')}")
                            print(f"📦 상품명: {product_info.get('product_name', 'N/A')}")
                            print(f"💰 가격: {product_info.get('price', 'N/A')}원")
                            print(f"⭐ 평점: {product_info.get('rating', 'N/A')}")
                            print(f"💬 리뷰 수: {product_info.get('review_count', 'N/A')}")
                            print(f"🔗 URL: {product_info.get('url', 'N/A')}")
                            print(f"\n🏷️ 검색태그 (해시태그):")
                            if product_info.get('search_tags'):
                                print(f"{product_info['search_tags']}")
                            else:
                                print("   (검색태그 없음)")
                            print(f"{'='*60}")

                            # JSON 저장
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            json_file = f'data/product_{timestamp}.json'
                            with open(json_file, 'w', encoding='utf-8') as f:
                                json.dump({
                                    'category': '여성의류',
                                    'category_id': 10000107,
                                    'crawled_at': datetime.now().isoformat(),
                                    'product': product_info
                                }, f, ensure_ascii=False, indent=2)
                            print(f"\n💾 JSON 저장: {json_file}")

                            # DB 저장 (현재는 JSON만)
                            print("\n📝 DB 저장용 데이터 (PostgreSQL 준비 후 저장 가능):")
                            self.product_data = product_info

                        await detail_page.close()
                else:
                    print("❌ 일반 상품을 찾을 수 없습니다")
                    await page.screenshot(path='data/no_products.png')

                await browser.close()
                return self.product_data

            except Exception as e:
                print(f"\n[오류] {str(e)}")
                import traceback
                traceback.print_exc()
                return None


if __name__ == "__main__":
    async def main():
        print("="*60)
        print("네이버 쇼핑 크롤러 - 캡차 감지 및 수동 해결")
        print("="*60)
        print("캡차가 나타나면 브라우저에서 직접 해결해주세요.")
        print("="*60)

        detector = CaptchaDetectorAndWait(headless=False)
        data = await detector.crawl_with_manual_captcha()

        if data:
            print("\n🎉 크롤링 성공!")
            print(f"수집된 상품: {data.get('product_name', 'N/A')}")
        else:
            print("\n❌ 크롤링 실패")

    asyncio.run(main())