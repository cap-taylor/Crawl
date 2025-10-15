"""
여성의류 크롤링 - 수동 캡차 해결 버전
캡차가 나타나면 사용자가 수동으로 해결 후 계속 진행
리팩토링: 구조 기반 셀렉터 + 다중 Fallback 시스템
"""
import asyncio
import json
import sys
from datetime import datetime
from typing import Optional
from playwright.async_api import async_playwright
import re

# DB 모듈 임포트
sys.path.append('/home/dino/MyProjects/Crawl')
from src.database.db_connector import save_to_database
from src.utils.config import SELECTORS
from src.utils.selector_helper import SelectorHelper

class WomensClothingManualCaptcha:
    def __init__(self, headless=False, product_count: Optional[int] = 1, enable_screenshot=False,
                 category_name: str = "여성의류", category_id: str = "10000107", debug_selectors: bool = False,
                 specific_index: Optional[int] = None):  # 특정 인덱스만 수집
        self.headless = headless
        self.product_count = product_count  # 수집할 상품 개수 (None이면 무한)
        self.enable_screenshot = enable_screenshot  # 스크린샷 활성화 여부
        self.category_name = category_name  # 카테고리 이름
        self.category_id = category_id  # 카테고리 ID
        self.products_data = []  # 여러 상품 저장
        self.should_stop = False  # 중지 플래그 (GUI에서 설정)
        self.helper = SelectorHelper(debug=debug_selectors)  # 셀렉터 Helper
        self.specific_index = specific_index  # 특정 인덱스만 수집 (0-based)

    async def wait_for_captcha_solve(self, page):
        """캡차 해결 대기 - 15초 고정"""
        print("\n" + "="*60)
        print("⚠️  캡차가 감지되었습니다!")
        print("="*60)
        print("브라우저에서 캡차를 수동으로 해결해주세요:")
        print("1. 캡차 이미지에 표시된 문자를 입력")
        print("2. '확인' 버튼 클릭")
        print("3. 정상 페이지가 나타날 때까지 대기")
        print("="*60)
        print("⏰ 15초 동안 대기합니다...")

        # 15초 대기 (고정)
        for i in range(15, 0, -5):
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
                    slow_mo=500
                    # Firefox는 --start-maximized 지원 안함
                )

                context = await browser.new_context(
                    no_viewport=True,  # 전체화면
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                    locale='ko-KR',
                    timezone_id='Asia/Seoul'
                )

                page = await context.new_page()

                # 1. 네이버 메인 접속
                print("[접속] 네이버 메인 페이지...")
                await page.goto('https://www.naver.com')
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(3)

                # 2. 쇼핑 클릭 (문서에서 검증된 방법 사용)
                print("[클릭] 쇼핑 아이콘...")

                # 페이지 상단으로 스크롤 (쇼핑 버튼이 항상 상단에 있음)
                await page.evaluate('window.scrollTo(0, 0)')
                await asyncio.sleep(1)

                # 문서에서 검증된 셀렉터 사용
                shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
                try:
                    shopping_link = page.locator(shopping_selector)
                    await shopping_link.click(timeout=10000)
                except Exception as e:
                    print(f"[오류] 쇼핑 버튼 클릭 실패: {str(e)[:100]}")
                    await browser.close()
                    return None

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
                print(f"[클릭] {self.category_name} 카테고리...")
                womens = await page.wait_for_selector(f'a[data-name="{self.category_name}"]')
                await womens.click()

                # 페이지 로드 대기 (충분한 시간)
                print("[대기] 페이지 로딩 중...")
                await asyncio.sleep(5)

                # 캡차 체크
                print("[확인] 캡차 여부 체크 중...")
                captcha_elem = await self.helper.try_selectors(
                    page, SELECTORS['captcha_indicators'], "캡차"
                )
                captcha_detected = captcha_elem is not None

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
                if self.specific_index is not None:
                    print(f"\n[탐색] {self.specific_index + 1}번째 상품만 수집...")
                elif self.product_count is None:
                    print(f"\n[탐색] 무한 모드 - 모든 상품 수집 시작...")
                else:
                    print(f"\n[탐색] 상품 {self.product_count}개 수집 시작...")

                # 상품 링크 찾기 (이미지가 있는 링크만 = 상품 썸네일 링크)
                print("[탐색] 상품 이미지 링크 찾는 중...")
                product_elements = await page.query_selector_all('a[href*="/products/"]:has(img)')

                if not product_elements:
                    # Fallback: 기존 방식
                    print("[Fallback] 기존 셀렉터로 재시도...")
                    product_elements = await self.helper.try_selectors(
                        page, SELECTORS['product_links'], "상품 링크", multiple=True
                    )

                # 중복 제거 (URL 기준)
                all_product_elements = []
                if product_elements:
                    seen_urls = set()
                    for elem in product_elements:
                        href = await elem.get_attribute('href')
                        # 정확한 상품 URL 패턴 확인: /products/숫자
                        if href and '/products/' in href and re.search(r'/products/\d+', href) and href not in seen_urls:
                            all_product_elements.append(elem)
                            seen_urls.add(href)
                    print(f"[발견] 총 {len(all_product_elements)}개 상품 발견")
                else:
                    all_product_elements = []

                if not all_product_elements:
                    print("[경고] 상품을 찾을 수 없습니다.")
                    await page.screenshot(path='data/final_page.png')
                    print("[스크린샷] data/final_page.png 저장됨")
                else:
                    # specific_index가 설정되어 있으면 해당 상품만 수집
                    if self.specific_index is not None:
                        print(f"[시작] {self.specific_index + 1}번째 상품부터 수집 시작...\n")
                        idx = self.specific_index  # 특정 인덱스로 시작
                        found_count = 0
                        max_attempts = 10  # 최대 10개까지 시도

                        # 성공할 때까지 다음 상품 시도 (최대 max_attempts개)
                        while found_count == 0 and idx < len(all_product_elements) and (idx - self.specific_index) < max_attempts:
                            print(f"\n[{idx+1}번째 상품] 수집 시도...")

                            # specific_index 모드: 처음 찾은 element 그대로 사용
                            product_elem = all_product_elements[idx]
                            href = await product_elem.get_attribute('href')

                            if not href:
                                print(f"#{idx+1} [SKIP] URL을 가져올 수 없음 - 다음 상품 시도")
                                idx += 1
                                continue

                            try:
                                    # 상품 클릭 (viewport로 스크롤 후 클릭)
                                    try:
                                        # 1. Element를 화면에 보이도록 스크롤
                                        await product_elem.scroll_into_view_if_needed()
                                        await asyncio.sleep(0.5)

                                        # 2. 클릭 시도 (타임아웃 10초)
                                        await product_elem.click(timeout=10000)
                                    except Exception as click_error:
                                        # 3. 실패 시 강제 클릭 시도
                                        print(f"   [재시도] 강제 클릭 시도...")
                                        await product_elem.click(force=True, timeout=5000)

                                    await asyncio.sleep(3)

                                    # 새 탭 찾기
                                    all_pages = context.pages
                                    if len(all_pages) <= 1:
                                        print(f"#{idx+1} [SKIP] 탭 열림 실패 - 다음 상품 시도")
                                        idx += 1
                                        continue

                                    detail_page = all_pages[-1]
                                    await detail_page.wait_for_load_state('domcontentloaded')
                                    await asyncio.sleep(1)

                                    # URL 검증: 상품 페이지인지 확인
                                    current_url = detail_page.url
                                    if not re.search(r'/products/\d+', current_url):
                                        print(f"#{idx+1} [SKIP] 잘못된 페이지 (스토어 페이지?) - 다음 상품 시도")
                                        print(f"         URL: {current_url[:70]}")
                                        await detail_page.close()
                                        idx += 1
                                        continue

                                    # 정상 상품 페이지 - 수집 진행
                                    try:
                                        await detail_page.wait_for_load_state('networkidle', timeout=10000)
                                    except:
                                        pass
                                    await asyncio.sleep(1)

                                    # 스크롤 (검색태그 위치)
                                    await detail_page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.4)')
                                    await asyncio.sleep(2)

                                    # 상품 정보 수집
                                    self.product_data = {}
                                    self.product_data['product_url'] = href
                                    await self._collect_detail_page_info(detail_page)

                                    # 한 줄 요약 출력
                                    detail_info = self.product_data.get('detail_page_info', {})
                                    product_name = detail_info.get('detail_product_name', 'N/A')

                                    # 상품명 검증 (잘못된 페이지인지 확인)
                                    invalid_keywords = ['본문', '바로가기', '네이버', '로그인', '서비스', '스토어 홈', 'For w', 'NAVER']
                                    is_invalid = (
                                        not product_name or
                                        product_name == 'N/A' or
                                        len(product_name) < 5 or  # 너무 짧음
                                        any(keyword in product_name for keyword in invalid_keywords)  # 메뉴 텍스트
                                    )

                                    if is_invalid:
                                        print(f"#{idx+1} [SKIP] 잘못된 상품명: '{product_name[:30]}' - 다음 상품 시도")
                                        print(f"         현재 URL: {detail_page.url[:70]}")
                                        await detail_page.close()
                                        idx += 1
                                        continue

                                    tags_count = len(detail_info.get('search_tags', []))

                                    # 수집 완료
                                    self.products_data.append(self.product_data.copy())
                                    found_count += 1

                                    print(f"#{idx+1} [{product_name[:30]}] - 태그 {tags_count}개 ✅ 수집 성공!")

                                    # 탭 닫기
                                    await detail_page.close()
                                    await asyncio.sleep(1)

                            except Exception as e:
                                print(f"#{idx+1} [ERROR] {str(e)[:50]} - 다음 상품 시도")
                                try:
                                    if len(context.pages) > 2:
                                        await context.pages[-1].close()
                                except:
                                    pass
                                idx += 1
                                continue

                        if found_count == 0:
                            print(f"\n[경고] {self.specific_index + 1}번째부터 {max_attempts}개 시도했지만 수집 실패")

                        print(f"\n{'='*60}")
                        print(f"[완료] {idx+1}번째 상품 수집 완료!")
                        print(f"{'='*60}")
                    else:
                        # 모든 상품 수집 (광고 포함, 검색태그 없어도 수집)
                        print(f"[시작] 1번째 상품부터 모든 상품 수집...\n")
                        print(f"[정보] 광고 포함, 검색태그 없어도 수집\n")

                        found_count = 0
                        idx = 0  # 1번째 상품부터 시작

                        # 무한 모드(product_count=None)이면 계속 수집, 아니면 개수 제한
                        while (self.product_count is None or found_count < self.product_count) and idx < len(all_product_elements):
                            # 중지 요청 확인
                            if self.should_stop:
                                print(f"[중지] 사용자 요청으로 수집 중지 ({found_count}개 수집 완료)")
                                break

                            print(f"\n[{idx+1}번째 상품] 수집 중...")

                            # 매번 새로 element 찾기 (DOM 변경 대응) - 이미지 있는 링크만
                            current_elements = await page.query_selector_all('a[href*="/products/"]:has(img)')
                            if idx >= len(current_elements):
                                print(f"[경고] 더 이상 상품이 없습니다.")
                                break

                            product_elem = current_elements[idx]
                            href = await product_elem.get_attribute('href')

                            try:
                                # 상품 클릭 (viewport로 스크롤 후 클릭)
                                try:
                                    # 1. Element를 화면에 보이도록 스크롤
                                    await product_elem.scroll_into_view_if_needed()
                                    await asyncio.sleep(0.5)

                                    # 2. 클릭 시도 (타임아웃 10초)
                                    await product_elem.click(timeout=10000)
                                except Exception as click_error:
                                    # 3. 실패 시 강제 클릭 시도
                                    print(f"   [재시도] 강제 클릭 시도...")
                                    await product_elem.click(force=True, timeout=5000)

                                await asyncio.sleep(3)

                                # 새 탭 찾기
                                all_pages = context.pages
                                if len(all_pages) <= 1:
                                    print(f"#{idx+1} [SKIP] 탭 열림 실패")
                                    idx += 1
                                    continue

                                detail_page = all_pages[-1]
                                await detail_page.wait_for_load_state('domcontentloaded')
                                await asyncio.sleep(1)

                                # URL 검증: 상품 페이지인지 확인
                                current_url = detail_page.url
                                if not re.search(r'/products/\d+', current_url):
                                    print(f"#{idx+1} [SKIP] 잘못된 페이지 (스토어 페이지?): {current_url[:50]}")
                                    await detail_page.close()
                                    idx += 1
                                    continue

                                try:
                                    await detail_page.wait_for_load_state('networkidle', timeout=10000)
                                except:
                                    pass
                                await asyncio.sleep(1)

                                # 스크롤 (검색태그 위치)
                                await detail_page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.4)')
                                await asyncio.sleep(2)

                                # 상품 정보 수집
                                self.product_data = {}
                                self.product_data['product_url'] = href
                                await self._collect_detail_page_info(detail_page)

                                # 한 줄 요약 출력
                                detail_info = self.product_data.get('detail_page_info', {})
                                product_name = detail_info.get('detail_product_name', 'N/A')[:30]
                                tags_count = len(detail_info.get('search_tags', []))

                                # 수집 완료
                                self.products_data.append(self.product_data.copy())
                                found_count += 1

                                if self.product_count is None:
                                    print(f"#{idx+1} [{product_name}] - 태그 {tags_count}개 (총 {found_count}개)")
                                else:
                                    print(f"#{idx+1} [{product_name}] - 태그 {tags_count}개 ({found_count}/{self.product_count})")

                                # 탭 닫기
                                await detail_page.close()
                                await asyncio.sleep(1)

                            except Exception as e:
                                print(f"#{idx+1} [ERROR] {str(e)[:50]}")
                                try:
                                    if len(context.pages) > 2:
                                        await context.pages[-1].close()
                                except:
                                    pass

                            idx += 1

                    print(f"\n{'='*60}")
                    print(f"[완료] 총 {found_count}개 상품 수집 완료!")
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
            'category': self.category_name,
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
        """
        상세 페이지에서 DB 스키마에 맞춰 모든 정보 수집
        리팩토링: config 기반 다중 fallback 시스템 사용
        """
        detail_info = {}

        # 1. 상품명 (product_name) - TEXT NOT NULL
        elem = await self.helper.try_selectors(page, SELECTORS['product_name'], "상품명")
        detail_info['detail_product_name'] = await self.helper.extract_text(elem, "상품명")

        # 2. 브랜드명 (brand_name) - VARCHAR(100)
        elem = await self.helper.try_selectors(page, SELECTORS['brand_name'], "브랜드")
        detail_info['brand_name'] = await self.helper.extract_text(elem, "브랜드")

        # 3. 가격 (price) - INTEGER
        elem = await self.helper.try_selectors(page, SELECTORS['price'], "가격")
        price_text = await self.helper.extract_text(elem, "가격")
        detail_info['detail_price'] = self.helper.clean_price(price_text)

        # 4. 할인율 (discount_rate) - INTEGER
        elem = await self.helper.try_selectors(page, SELECTORS['discount_rate'], "할인율")
        discount_text = await self.helper.extract_text(elem, "할인율")
        detail_info['discount_rate'] = self.helper.clean_discount_rate(discount_text)

        # 5. 리뷰 수 (review_count) - INTEGER
        elem = await self.helper.try_selectors(page, SELECTORS['review_count'], "리뷰 수")
        review_text = await self.helper.extract_text(elem, "리뷰 수")
        detail_info['detail_review_count'] = self.helper.clean_review_count(review_text)

        # 6. 평점 (rating) - DECIMAL(2,1)
        elem = await self.helper.try_selectors(page, SELECTORS['rating'], "평점")
        rating_text = await self.helper.extract_text(elem, "평점")
        detail_info['rating'] = self.helper.clean_rating(rating_text)

        # 7. 검색 태그 (search_tags) - TEXT[]
        # 구조 기반: "관련 태그" 찾은 후 다음 ul > a 리스트
        tags = []
        try:
            # 먼저 "관련 태그" 텍스트 찾기
            tag_container = await self.helper.find_by_text_then_next(
                page, "관련 태그", "ul", "검색태그 컨테이너"
            )

            if tag_container:
                # 컨테이너 내부에서 링크 찾기
                tag_links = await self.helper.try_selectors_from_element(
                    tag_container, SELECTORS['search_tags_links'], "검색태그 링크", multiple=True
                )

                if tag_links:
                    for link in tag_links:
                        text = await self.helper.extract_text(link, "태그")
                        if text:
                            # # 제거하고 저장
                            clean_tag = text.replace('#', '').strip()
                            if 1 < len(clean_tag) < 30 and clean_tag not in tags:
                                tags.append(clean_tag)
            else:
                # Fallback: 전체 페이지에서 # 으로 시작하는 링크 찾기
                all_links = await page.query_selector_all('a')
                for link in all_links[:100]:  # 최대 100개만 확인
                    text = await self.helper.extract_text(link)
                    if text and text.strip().startswith('#'):
                        clean_tag = text.strip().replace('#', '').strip()
                        if 1 < len(clean_tag) < 30 and clean_tag not in tags:
                            tags.append(clean_tag)

            if tags:
                detail_info['search_tags'] = tags
                print(f"   [검색태그] {len(tags)}개 수집")
            else:
                detail_info['search_tags'] = []
                print(f"   [검색태그] 없음")

        except Exception as e:
            print(f"   [검색태그 오류] {str(e)[:50]}")
            detail_info['search_tags'] = []

        # 8. 썸네일 (thumbnail_url) - TEXT
        elem = await self.helper.try_selectors(page, SELECTORS['thumbnail'], "썸네일")
        detail_info['thumbnail_url'] = await self.helper.extract_attribute(elem, "src", "썸네일")

        # 9. 품절 여부 (is_sold_out) - BOOLEAN
        elem = await self.helper.try_selectors(page, SELECTORS['is_sold_out'], "품절")
        detail_info['is_sold_out'] = (elem is not None)

        # 10. URL (product_url) - TEXT
        detail_info['detail_page_url'] = page.url

        # 11. 카테고리 전체 경로 (category_fullname) - VARCHAR(500)
        # 예: "언더웨어>여성>브라"
        category_path = []
        try:
            # 1순위: 구조 기반 (가장 안정적)
            breadcrumb_links = await self.helper.find_breadcrumb_from_home(page, "카테고리 경로")

            # 2순위: config 기반 fallback
            if not breadcrumb_links:
                breadcrumb_links = await self.helper.try_selectors(
                    page, SELECTORS['category_breadcrumb'], "카테고리 경로", multiple=True
                )

            if breadcrumb_links:
                for link in breadcrumb_links:
                    text = await self.helper.extract_text(link)
                    if text:
                        # "홈", "전체", "쇼핑홈" 같은 불필요한 단어 제거
                        clean_text = text.strip()
                        if clean_text and clean_text not in ['홈', '전체', '쇼핑홈', '쇼핑', 'HOME']:
                            category_path.append(clean_text)

                if category_path:
                    detail_info['category_fullname'] = '>'.join(category_path)
                    print(f"   [카테고리 경로] {detail_info['category_fullname']}")
                else:
                    detail_info['category_fullname'] = self.category_name  # fallback to main category
                    print(f"   [카테고리 경로] breadcrumb 텍스트 없음, 대분류 사용: {self.category_name}")
            else:
                detail_info['category_fullname'] = self.category_name  # fallback
                print(f"   [카테고리 경로] 찾을 수 없음, 대분류 사용: {self.category_name}")

        except Exception as e:
            print(f"   [카테고리 경로 오류] {str(e)[:50]}")
            detail_info['category_fullname'] = self.category_name  # fallback

        # 데이터 저장
        if self.product_data:
            self.product_data['detail_page_info'] = detail_info
        else:
            self.product_data = {
                'category': self.category_name,
                'crawled_at': datetime.now().isoformat(),
                'detail_page_info': detail_info
            }

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
            'category': self.category_name,
            'total_count': len(self.products_data),
            'crawled_at': timestamp,
            'products': self.products_data
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n[저장] {filename}")
        print(f"[저장] 총 {len(self.products_data)}개 상품 저장됨")
        return filename

    def save_to_db(self, skip_duplicates=True):
        """DB에 저장 (중복 체크 선택 가능)"""
        if not self.products_data:
            print("[경고] DB에 저장할 데이터가 없습니다.")
            return False

        print("\n[DB 저장] PostgreSQL에 저장 시작...")
        print(f"총 {len(self.products_data)}개 상품을 DB에 저장합니다:")
        print(f"중복 체크: {'활성화' if skip_duplicates else '비활성화'}\n")

        try:
            # DB 저장 실행
            results = save_to_database(self.category_name, self.products_data, skip_duplicates=skip_duplicates)

            print(f"\n✅ DB 저장 완료:")
            print(f"   - 신규 저장: {results['saved']}개")
            print(f"   - 중복 스킵: {results['skipped']}개")
            print(f"   - 저장 실패: {results['failed']}개")

            return results['saved'] > 0 or results['skipped'] > 0

        except Exception as e:
            print(f"\n❌ DB 저장 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return False

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
        print("여성의류 상품 크롤링 - 전체 상품 수집 (중복 체크)")
        print("="*60)

        # 20개 상품 수집
        crawler = WomensClothingManualCaptcha(product_count=20, enable_screenshot=False)

        # 크롤링 실행
        data = await crawler.crawl_with_manual_captcha()

        if crawler.products_data:
            # JSON 저장
            crawler.save_to_json()

            # DB 저장 (중복 체크)
            crawler.save_to_db()

            # 요약 출력
            crawler.print_summary()
        else:
            print("\n[실패] 데이터 수집 실패")

    asyncio.run(main())