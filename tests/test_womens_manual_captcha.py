"""
여성의류 크롤링 - 수동 캡차 해결 버전
캡차가 나타나면 사용자가 수동으로 해결 후 계속 진행
"""
import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
import re

class WomensClothingManualCaptcha:
    def __init__(self, headless=False, product_count=1, enable_screenshot=False):
        self.headless = headless
        self.product_count = product_count  # 수집할 상품 개수
        self.enable_screenshot = enable_screenshot  # 스크린샷 활성화 여부
        self.products_data = []  # 여러 상품 저장

    async def wait_for_captcha_solve(self, page):
        """캡차 해결 대기"""
        print("\n" + "="*60)
        print("⚠️  캡차가 감지되었습니다!")
        print("="*60)
        print("브라우저에서 캡차를 수동으로 해결해주세요:")
        print("1. 캡차 이미지에 표시된 문자를 입력")
        print("2. '확인' 버튼 클릭")
        print("3. 정상 페이지가 나타날 때까지 대기")
        print("="*60)
        print("⏰ 25초 동안 대기합니다...")

        # 25초 대기 (캡차 해결 시간)
        for i in range(25, 0, -5):
            print(f"[대기] 남은 시간: {i}초...")
            await asyncio.sleep(5)

        print("✅ 대기 완료! 크롤링을 계속합니다...")
        await asyncio.sleep(2)

    async def crawl_with_manual_captcha(self):
        """수동 캡차 해결 방식으로 크롤링"""
        async with async_playwright() as p:
            try:
                print("[시작] Firefox 브라우저 실행 (전체화면)...")
                browser = await p.firefox.launch(
                    headless=False,  # 항상 보이도록
                    slow_mo=500,
                    args=['--start-maximized']  # 전체화면으로 시작
                )

                context = await browser.new_context(
                    no_viewport=True,  # 전체 화면 사용
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                    locale='ko-KR',
                    timezone_id='Asia/Seoul'
                )

                page = await context.new_page()

                # 1. 네이버 메인 접속
                print("[접속] 네이버 메인 페이지...")
                await page.goto('https://www.naver.com')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(3)

                # 2. 쇼핑 클릭
                print("[클릭] 쇼핑 아이콘...")
                shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
                shopping_link = await page.wait_for_selector(shopping_selector)
                await shopping_link.click()
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

                # 3. 카테고리 버튼 클릭
                print("[클릭] 카테고리 메뉴 열기...")
                category_btn = await page.wait_for_selector('button:has-text("카테고리")')
                await category_btn.click()
                await asyncio.sleep(2)

                # 4. 여성의류 클릭
                print("[클릭] 여성의류 카테고리...")
                womens = await page.wait_for_selector('a[data-name="여성의류"]')
                await womens.click()

                # 페이지 로드 대기 (충분한 시간)
                print("[대기] 페이지 로딩 중...")
                await asyncio.sleep(5)

                # 캡차 체크 (여러 방법으로 시도)
                print("[확인] 캡차 여부 체크 중...")
                captcha_detected = False

                # 캡차 감지 셀렉터들
                captcha_selectors = [
                    'text="보안 확인을 완료해 주세요"',
                    'text="자동입력 방지"',
                    'input[name="captchaAnswer"]',
                    'img[alt*="보안"]',
                    '[class*="captcha"]'
                ]

                for selector in captcha_selectors:
                    if await page.query_selector(selector):
                        captcha_detected = True
                        print(f"[감지] 캡차 발견! (셀렉터: {selector})")
                        break

                if captcha_detected:
                    await self.wait_for_captcha_solve(page)
                else:
                    print("[확인] 캡차 없음 - 정상 진행")

                # 최종 페이지 로드 대기
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    pass
                await asyncio.sleep(2)

                # 5. 상품 리스트 수집
                print(f"\n[탐색] 상품 {self.product_count}개 수집 시작...")

                # 상품 찾기
                product_selectors = [
                    'a[href*="/products/"]',
                    'div[class*="product"] a',
                    'li[class*="product"] a'
                ]

                all_product_elements = []
                for selector in product_selectors:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        # 중복 제거 (URL 기준)
                        unique_products = []
                        seen_urls = set()
                        for elem in elements:
                            href = await elem.get_attribute('href')
                            if href and '/products/' in href and href not in seen_urls:
                                unique_products.append(elem)
                                seen_urls.add(href)
                        all_product_elements = unique_products
                        print(f"[발견] 총 {len(all_product_elements)}개 상품 발견")
                        break

                if not all_product_elements:
                    print("[경고] 상품을 찾을 수 없습니다.")
                    await page.screenshot(path='data/final_page.png')
                    print("[스크린샷] data/final_page.png 저장됨")
                else:
                    # 검색태그가 있는 상품 찾기
                    print(f"[시작] 검색태그가 있는 상품 찾기...\n")
                    print(f"[정보] 광고 상품 건너뛰기 - 30번째 상품부터 시작\n")

                    found_count = 0
                    idx = 29  # 30번째 상품부터 시작 (1~15번째는 광고)

                    while found_count < self.product_count and idx < len(all_product_elements):
                        print(f"\n{'='*60}")
                        print(f"[{idx+1}번째 상품] 검색태그 확인 중...")
                        print(f"{'='*60}")

                        # 매번 새로 element 찾기 (DOM 변경 대응)
                        current_elements = await page.query_selector_all('a[href*="/products/"]')
                        if idx >= len(current_elements):
                            print(f"[경고] 더 이상 상품이 없습니다.")
                            break

                        product_elem = current_elements[idx]
                        href = await product_elem.get_attribute('href')
                        print(f"[URL] {href[:80]}...")

                        # 상품 클릭
                        print(f"[클릭] 상품 상세 페이지로 이동...")
                        try:
                            # 요소가 안정적인지 확인 (viewport에 보이고 클릭 가능한지)
                            await product_elem.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)

                            # 상품 클릭
                            await product_elem.click()
                            print(f"[대기] 새 탭이 열리는 중...")
                            await asyncio.sleep(3)  # 새 탭이 열릴 때까지 충분히 대기

                            # 새 탭 찾기
                            all_pages = context.pages
                            if len(all_pages) <= 1:
                                print(f"[경고] 새 탭이 열리지 않았습니다. 다음 상품으로...")
                                idx += 1
                                continue

                            # 가장 최근에 열린 탭 선택
                            detail_page = all_pages[-1]
                            print(f"[확인] 새 탭 열림 (총 {len(all_pages)}개 탭)")

                            # 페이지 완전히 로드될 때까지 대기
                            await detail_page.wait_for_load_state('domcontentloaded')
                            await asyncio.sleep(1)
                            try:
                                await detail_page.wait_for_load_state('networkidle', timeout=10000)
                            except:
                                pass
                            await asyncio.sleep(1)

                            # 점진적으로 스크롤하면서 검색태그 찾기
                            print(f"[스크롤] 천천히 스크롤하면서 검색태그 찾는 중...")
                            has_tags = False

                            # 페이지를 10단계로 나눠서 천천히 스크롤
                            for scroll_step in range(1, 11):
                                scroll_position = scroll_step * 10  # 10%, 20%, 30%... 100%
                                await detail_page.evaluate(f'window.scrollTo(0, document.body.scrollHeight * {scroll_position / 100})')
                                print(f"   → {scroll_position}% 위치 확인 중...")
                                await asyncio.sleep(2)  # 2초 대기 (DOM 로드 시간)

                                # 각 단계에서 태그 확인
                                has_tags = await self._check_search_tags(detail_page)
                                if has_tags:
                                    print(f"   ✓ {scroll_position}% 스크롤 위치에서 검색태그 발견!")
                                    break

                            if not has_tags:
                                print(f"   ✗ 페이지 전체를 확인했지만 검색태그 없음")

                            if has_tags:
                                print(f"✅ 검색태그 발견! 상품 정보 수집 시작...")

                                # 현재 상품 데이터 초기화
                                self.product_data = {}
                                self.product_data['product_url'] = href

                                # 상세 정보 수집
                                await self._collect_detail_page_info(detail_page)

                                # 수집 완료
                                self.products_data.append(self.product_data.copy())
                                found_count += 1
                                print(f"✅ 검색태그 있는 상품 수집 완료! ({found_count}/{self.product_count})")

                                # 탭 닫기
                                await detail_page.close()
                                await asyncio.sleep(1)
                            else:
                                print(f"❌ 검색태그 없음 - 다음 상품으로...")
                                # 탭 닫기
                                await detail_page.close()
                                await asyncio.sleep(1)

                        except Exception as e:
                            print(f"[오류] {idx+1}번째 상품 확인 실패: {str(e)}")
                            # 탭이 열려있으면 닫기
                            try:
                                if len(context.pages) > 2:
                                    await context.pages[-1].close()
                            except:
                                pass

                        idx += 1

                    print(f"\n{'='*60}")
                    print(f"[완료] 검색태그 있는 상품 {found_count}개 수집 완료!")
                    print(f"[총 확인] {idx}개 상품 확인")
                    print(f"{'='*60}")

                # 브라우저 30초 더 열어둠 (확인용)
                print("\n[완료] 데이터 수집 완료!")
                print("⏰ 브라우저를 30초 후 자동으로 닫습니다...")
                await asyncio.sleep(30)

                await browser.close()
                return self.products_data

            except Exception as e:
                print(f"[오류] {str(e)}")
                import traceback
                traceback.print_exc()
                return None

    async def _collect_product_info(self, page, product_elem):
        """상품 정보 수집"""
        print("\n[수집] 상품 정보 수집 시작...")

        info = {}

        # 컨테이너 찾기
        container = await product_elem.evaluate_handle(
            'el => el.closest("li, div[class*=\'product\']")'
        )

        # 상품명
        title_elem = await container.query_selector('[class*="title"], [class*="name"]')
        if title_elem:
            info['product_name'] = await title_elem.inner_text()
            print(f"✓ 상품명: {info['product_name'][:40]}...")

        # 가격
        price_elem = await container.query_selector('[class*="price"] strong')
        if price_elem:
            price_text = await price_elem.inner_text()
            info['price'] = price_text.replace(',', '').replace('원', '')
            print(f"✓ 가격: {info['price']}원")

        # 브랜드
        brand_elem = await container.query_selector('[class*="brand"], [class*="mall"]')
        if brand_elem:
            info['brand'] = await brand_elem.inner_text()
            print(f"✓ 브랜드/몰: {info['brand']}")

        # 리뷰
        review_elem = await container.query_selector('[class*="review"]')
        if review_elem:
            review_text = await review_elem.inner_text()
            # 리뷰 수 추출
            review_match = re.search(r'리뷰\s*([0-9,]+)', review_text)
            if review_match:
                info['review_count'] = review_match.group(1).replace(',', '')
                print(f"✓ 리뷰 수: {info['review_count']}개")

            # 평점 추출
            rating_match = re.search(r'(\d+\.\d+)', review_text)
            if rating_match:
                info['rating'] = rating_match.group(1)
                print(f"✓ 평점: {info['rating']}")

        # 할인율
        discount_elem = await container.query_selector('[class*="discount"]')
        if discount_elem:
            discount_text = await discount_elem.inner_text()
            discount_match = re.search(r'(\d+)%', discount_text)
            if discount_match:
                info['discount_rate'] = discount_match.group(1)
                print(f"✓ 할인율: {info['discount_rate']}%")

        # 배송 정보
        delivery_elem = await container.query_selector('[class*="delivery"]')
        if delivery_elem:
            info['delivery'] = await delivery_elem.inner_text()
            print(f"✓ 배송: {info['delivery']}")

        # URL
        href = await product_elem.get_attribute('href')
        if href:
            info['url'] = href
            # 상품 ID 추출
            id_match = re.search(r'/products/(\d+)', href)
            if id_match:
                info['product_id'] = id_match.group(1)
                print(f"✓ 상품 ID: {info['product_id']}")

        # 썸네일
        img_elem = await container.query_selector('img')
        if img_elem:
            info['thumbnail_url'] = await img_elem.get_attribute('src')
            print(f"✓ 썸네일: 수집 완료")

        self.product_data = {
            'category': '여성의류',
            'crawled_at': datetime.now().isoformat(),
            'product_info': info
        }

        print(f"\n[완료] 총 {len(info)}개 항목 수집")
        return info

    async def _check_search_tags(self, page):
        """검색태그 존재 여부 확인 (관련 태그 섹션의 해시태그)"""
        try:
            print(f"   [디버깅] 검색태그 찾기 시작...")

            # 방법 1: "관련 태그" 텍스트가 있는지 확인
            related_tag_section = await page.query_selector('text="관련 태그"')
            if related_tag_section:
                print(f"   [디버깅] '관련 태그' 섹션 발견!")

            # 방법 2: 페이지 내 모든 링크에서 # 으로 시작하는 텍스트 찾기
            all_links = await page.query_selector_all('a')
            print(f"   [디버깅] 총 {len(all_links)}개 링크 확인 중...")

            found_tags = []
            # 제한 제거: 모든 링크 확인
            for idx, link in enumerate(all_links):
                try:
                    text = await link.inner_text()
                    if text and text.strip().startswith('#'):
                        clean_tag = text.strip()
                        if 2 < len(clean_tag) < 30 and clean_tag not in found_tags:
                            found_tags.append(clean_tag)
                            if len(found_tags) <= 3:  # 처음 3개만 출력
                                print(f"   → 검색태그 발견: {clean_tag}")
                except:
                    continue

            if found_tags:
                print(f"   ✓ 총 {len(found_tags)}개 검색태그 발견!")
                return True

            # 방법 3: URL 패턴으로 찾기
            tag_links = await page.query_selector_all('a[href*="/search"], a[href*="tag"], a[href*="%23"]')
            print(f"   [디버깅] URL 패턴으로 {len(tag_links)}개 링크 발견")

            for link in tag_links[:20]:
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute('href')
                    if text and text.strip().startswith('#'):
                        print(f"   → 검색태그 발견: {text.strip()} (URL: {href[:50]}...)")
                        return True
                except:
                    continue

            print(f"   ✗ 검색태그를 찾을 수 없음")
            return False
        except Exception as e:
            print(f"   [오류] 태그 확인 중 오류: {str(e)}")
            return False

    async def _collect_detail_page_info(self, page):
        """상세 페이지에서 추가 정보 수집"""
        print("\n[수집] 상세 페이지 정보 수집 시작...")

        detail_info = {}

        # 검색태그 수집 (관련 태그 섹션의 해시태그)
        try:
            print(f"[디버깅] 검색태그 수집 시작...")
            tags = []

            # 페이지 내 모든 링크에서 # 으로 시작하는 텍스트 찾기
            all_links = await page.query_selector_all('a')
            print(f"[디버깅] 총 {len(all_links)}개 링크 발견")

            tag_count = 0
            # 제한 제거: 모든 링크 확인
            for idx, link in enumerate(all_links):
                try:
                    text = await link.inner_text()
                    if text and text.strip().startswith('#'):
                        clean_tag = text.strip().replace('#', '').strip()
                        if 1 < len(clean_tag) < 30 and clean_tag not in tags:
                            tags.append(clean_tag)
                            tag_count += 1
                            if tag_count <= 5:  # 처음 5개만 출력
                                print(f"   [발견] 태그 #{idx}: {clean_tag}")
                except:
                    continue

            if tags:
                detail_info['search_tags'] = tags
                print(f"✓ 검색태그: {len(tags)}개 - {', '.join(tags)}...")
            else:
                print(f"[경고] 검색태그를 찾을 수 없습니다!")
        except Exception as e:
            print(f"   [오류] 태그 수집 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            pass

        # 상품명 (상세)
        try:
            title_selectors = [
                'h3[class*="title"]',
                'h2[class*="title"]',
                'div[class*="productTitle"]',
                '[class*="product_title"]'
            ]
            for selector in title_selectors:
                elem = await page.query_selector(selector)
                if elem:
                    detail_info['detail_product_name'] = await elem.inner_text()
                    print(f"✓ 상세 상품명: {detail_info['detail_product_name'][:40]}...")
                    break
        except:
            pass

        # 상세 가격
        try:
            price_selectors = [
                'span[class*="price"] em',
                'strong[class*="price"]',
                '[class*="total_price"]',
                'em[class*="salePrice"]'
            ]
            for selector in price_selectors:
                elem = await page.query_selector(selector)
                if elem:
                    price_text = await elem.inner_text()
                    detail_info['detail_price'] = price_text.replace(',', '').replace('원', '')
                    print(f"✓ 상세 가격: {detail_info['detail_price']}원")
                    break
        except:
            pass

        # 옵션 정보
        try:
            option_elems = await page.query_selector_all('select option, [class*="option"] button')
            options = []
            for opt in option_elems[:10]:
                opt_text = await opt.inner_text()
                if opt_text and opt_text.strip():
                    options.append(opt_text.strip())
            if options:
                detail_info['options'] = options
                print(f"✓ 옵션: {len(options)}개")
        except:
            pass

        # 상세 이미지들
        try:
            img_elems = await page.query_selector_all('img')
            images = []
            for img in img_elems[:10]:
                src = await img.get_attribute('src')
                if src and ('image' in src or 'img' in src):
                    images.append(src)
            if images:
                detail_info['detail_images'] = images
                print(f"✓ 상세 이미지: {len(images)}개")
        except:
            pass

        # 판매자 정보
        try:
            seller_selectors = [
                '[class*="seller"]',
                '[class*="store"]',
                '[class*="brandShop"]'
            ]
            for selector in seller_selectors:
                elem = await page.query_selector(selector)
                if elem:
                    detail_info['seller'] = await elem.inner_text()
                    print(f"✓ 판매자: {detail_info['seller'][:30]}...")
                    break
        except:
            pass

        # 배송 정보
        try:
            delivery_elem = await page.query_selector('[class*="delivery"], [class*="shipping"]')
            if delivery_elem:
                detail_info['delivery_detail'] = await delivery_elem.inner_text()
                print(f"✓ 배송 정보: {detail_info['delivery_detail'][:30]}...")
        except:
            pass

        # 리뷰 및 평점 (상세)
        try:
            review_elem = await page.query_selector('[class*="reviewCount"], [class*="review_count"]')
            if review_elem:
                review_text = await review_elem.inner_text()
                detail_info['detail_review_count'] = review_text
                print(f"✓ 리뷰 수 (상세): {review_text}")
        except:
            pass

        # 현재 URL
        detail_info['detail_page_url'] = page.url
        print(f"✓ 상세 페이지 URL: {page.url[:60]}...")

        # 기존 product_data에 상세 정보 추가
        if self.product_data:
            self.product_data['detail_page_info'] = detail_info
        else:
            self.product_data = {
                'category': '여성의류',
                'crawled_at': datetime.now().isoformat(),
                'detail_page_info': detail_info
            }

        print(f"\n[완료] 상세 페이지 {len(detail_info)}개 항목 수집")
        return detail_info

    def save_to_json(self):
        """JSON 파일로 저장"""
        if not self.products_data:
            print("[경고] 저장할 데이터가 없습니다.")
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/womens_products_{timestamp}.json'

        # 여러 상품 데이터를 배열로 저장
        output = {
            'category': '여성의류',
            'total_count': len(self.products_data),
            'crawled_at': timestamp,
            'products': self.products_data
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n[저장] {filename}")
        print(f"[저장] 총 {len(self.products_data)}개 상품 저장됨")
        return filename

    def save_to_db(self):
        """DB에 저장 (구현 예정)"""
        if not self.products_data:
            print("[경고] DB에 저장할 데이터가 없습니다.")
            return False

        print("\n[DB 저장 시뮬레이션]")
        print(f"총 {len(self.products_data)}개 상품을 DB에 저장합니다:\n")

        for idx, product in enumerate(self.products_data, 1):
            info = product.get('product_info', {})
            print(f"[{idx}] {info.get('product_name', 'N/A')[:40]}... (ID: {info.get('product_id', 'N/A')})")

        # TODO: 실제 DB 연결 및 저장 구현
        return True

    def print_summary(self):
        """수집 결과 요약"""
        print("\n" + "="*60)
        print("📊 수집 결과 요약")
        print("="*60)

        if self.products_data:
            print(f"\n총 수집 상품: {len(self.products_data)}개")
            print("\n[수집된 상품 목록]")

            for idx, product in enumerate(self.products_data, 1):
                info = product.get('product_info', {})
                detail = product.get('detail_page_info', {})

                print(f"\n{idx}. {info.get('product_name', 'N/A')[:50]}")
                print(f"   - ID: {info.get('product_id', 'N/A')}")
                print(f"   - 리뷰: {info.get('review_count', 'N/A')}개")
                print(f"   - 평점: {info.get('rating', 'N/A')}")
                if detail:
                    print(f"   - 상세정보: ✅ 수집완료")
        else:
            print("수집된 데이터가 없습니다.")

        print("="*60)


if __name__ == "__main__":
    async def main():
        print("\n" + "="*60)
        print("여성의류 상품 크롤링 - 검색태그 수집")
        print("="*60)

        # 1개 상품 수집 (스크린샷 비활성화)
        crawler = WomensClothingManualCaptcha(product_count=1, enable_screenshot=False)

        # 크롤링 실행
        data = await crawler.crawl_with_manual_captcha()

        if crawler.products_data:
            # JSON 저장
            crawler.save_to_json()

            # DB 저장 (시뮬레이션)
            crawler.save_to_db()

            # 요약 출력
            crawler.print_summary()
        else:
            print("\n[실패] 데이터 수집 실패")

    asyncio.run(main())