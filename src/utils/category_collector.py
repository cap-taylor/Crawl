"""네이버 쇼핑 카테고리 수집기"""
import asyncio
import json
import time
from playwright.async_api import async_playwright
from datetime import datetime

class CategoryCollector:
    def __init__(self, gui=None, headless=False):
        self.gui = gui
        self.headless = headless
        self.categories = {}
        self.total_count = 0

    def log(self, message, level='INFO'):
        """로그 메시지 출력"""
        print(f"[{level}] {message}")
        if self.gui:
            self.gui.add_log(message, level)

    async def collect_categories(self):
        """카테고리 수집 메인 메서드"""
        async with async_playwright() as p:
            try:
                # Firefox 브라우저 사용 (봇 감지 회피 쉬움)
                self.log("Firefox 브라우저를 시작합니다...", 'INFO')
                browser = await p.firefox.launch(
                    headless=self.headless,
                    slow_mo=500  # 천천히 동작
                )

                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                    locale='ko-KR',
                    timezone_id='Asia/Seoul'
                )

                page = await context.new_page()

                # 1단계: 네이버 메인 접속 (캡차 회피)
                self.log("네이버 메인 페이지 접속...", 'INFO')
                await page.goto('https://www.naver.com')
                await asyncio.sleep(2)

                # 2단계: 쇼핑 클릭 (새 탭으로 열림)
                self.log("쇼핑 페이지로 이동...", 'INFO')
                shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
                shopping_link = await page.wait_for_selector(shopping_selector, timeout=10000)
                await shopping_link.click()
                await asyncio.sleep(3)

                # 3단계: 새 탭으로 전환
                all_pages = context.pages
                if len(all_pages) > 1:
                    page = all_pages[-1]  # 쇼핑 탭
                    await page.wait_for_load_state('networkidle')
                    self.log("쇼핑 페이지 로드 완료", 'SUCCESS')

                # 4단계: 카테고리 버튼 클릭
                self.log("카테고리 메뉴를 여는 중...", 'INFO')

                # 여러 가능한 셀렉터 시도
                category_selectors = [
                    'button:has-text("카테고리")',
                    '[aria-label*="카테고리"]',
                    'button[class*="category"]',
                    '#gnb-gnb button:has-text("카테고리")',
                    '._gnbContent_button_area_FRBmE button:first-child'
                ]

                category_btn = None
                for selector in category_selectors:
                    try:
                        category_btn = await page.wait_for_selector(selector, timeout=3000)
                        if category_btn:
                            self.log(f"카테고리 버튼 발견: {selector}", 'SUCCESS')
                            break
                    except:
                        continue

                if category_btn:
                    await category_btn.click()
                    await asyncio.sleep(2)

                    # 5단계: 메인 카테고리 수집
                    await self._collect_main_categories(page)
                else:
                    self.log("카테고리 버튼을 찾을 수 없습니다", 'ERROR')

                await browser.close()

                # 결과 저장
                self._save_results()

                self.log(f"카테고리 수집 완료! 총 {self.total_count}개", 'SUCCESS')
                return self.categories

            except Exception as e:
                self.log(f"오류 발생: {str(e)}", 'ERROR')
                raise

    async def _collect_main_categories(self, page):
        """메인 카테고리 수집"""
        try:
            # 메인 카테고리 찾기 (우선순위 셀렉터)
            main_selectors = [
                '[data-leaf="false"]',  # 하위 카테고리 있는 것들
                'a._categoryLayer_link_8hzu',
                'a[class*="categoryLayer_link"]'
            ]

            main_categories = []
            for selector in main_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        main_categories = elements
                        self.log(f"메인 카테고리 {len(elements)}개 발견", 'INFO')
                        break
                except:
                    continue

            if not main_categories:
                self.log("메인 카테고리를 찾을 수 없습니다", 'WARNING')
                return

            # 각 메인 카테고리 처리
            for idx, main_cat in enumerate(main_categories[:10], 1):  # 상위 10개만
                try:
                    # 카테고리 정보 추출
                    cat_name = await main_cat.inner_text()
                    cat_id = await main_cat.get_attribute('data-id')

                    if not cat_name or cat_name == '더보기':
                        continue

                    self.log(f"[{idx}] {cat_name} 처리 중...", 'INFO')

                    # 호버하여 서브카테고리 표시
                    await main_cat.hover()
                    await asyncio.sleep(1.5)  # 서브메뉴 로딩 대기

                    # 서브카테고리 수집
                    sub_categories = await self._collect_sub_categories(page, cat_name)

                    # 데이터 저장
                    self.categories[cat_name] = {
                        'id': cat_id,
                        'name': cat_name,
                        'sub_categories': sub_categories,
                        'count': len(sub_categories)
                    }

                    self.total_count += 1 + len(sub_categories)

                    if self.gui:
                        self.gui.update_status(
                            category_name=cat_name,
                            category_count=self.total_count
                        )

                    # 랜덤 대기
                    await asyncio.sleep(0.5)

                except Exception as e:
                    self.log(f"카테고리 처리 중 오류: {str(e)}", 'WARNING')
                    continue

        except Exception as e:
            self.log(f"메인 카테고리 수집 오류: {str(e)}", 'ERROR')

    async def _collect_sub_categories(self, page, main_cat_name):
        """서브카테고리 수집"""
        sub_categories = []

        try:
            # 호버 후 나타나는 서브패널을 찾기
            await asyncio.sleep(0.5)  # 서브패널이 나타날 시간 추가

            # 서브카테고리 패널 셀렉터 (우선순위)
            sub_panel_selectors = [
                '._categoryLayer_sub_panel_V3Sdo',  # 서브 패널
                '[class*="sub_panel"]',  # 클래스에 sub_panel 포함
                'div[class*="categoryLayer"][class*="sub"]'  # 서브 레이어
            ]

            sub_panel = None
            for selector in sub_panel_selectors:
                try:
                    sub_panel = await page.query_selector(selector)
                    if sub_panel:
                        # 서브패널이 보이는지 확인
                        is_visible = await sub_panel.is_visible()
                        if is_visible:
                            self.log(f"    서브패널 발견: {selector}", 'DEBUG')
                            break
                except:
                    continue

            # 서브패널 내의 링크들 수집
            if sub_panel:
                # 서브패널 내의 모든 링크
                sub_links = await sub_panel.query_selector_all('a')

                for link in sub_links:
                    try:
                        text = await link.inner_text()
                        # 메인 카테고리 이름들 제외 리스트
                        main_categories = ['여성의류', '남성의류', '패션잡화', '신발', '화장품/미용',
                                         '신선식품', '가공식품', '건강식품', '출산/유아동', '반려동물용품',
                                         '가전', '휴대폰/카메라', 'PC/주변기기', '가구', '조명/인테리어',
                                         '패브릭/홈데코', '주방용품', '생활용품', '스포츠/레저', '자동차/오토바이',
                                         '키덜트/취미', '건강/의료용품', '악기/문구', '공구', '렌탈관',
                                         'E쿠폰/티켓/생활편의', '여행', '공식몰단독']

                        # 필터링: 메인 카테고리가 아니고, 더보기가 아니고, 현재 카테고리와 다른 것
                        if text and text.strip() not in main_categories and text != '더보기' and text != main_cat_name:
                            sub_categories.append(text.strip())
                    except:
                        continue
            else:
                # 서브패널을 못 찾은 경우, 기존 방식 시도
                self.log(f"    서브패널 미발견, 대체 방법 시도", 'DEBUG')

                # 현재 보이는 모든 span 중에서 서브카테고리 찾기
                all_spans = await page.query_selector_all('span:visible')

                # 메인 카테고리 목록 (하드코딩)
                main_categories = ['여성의류', '남성의류', '패션잡화', '신발', '화장품/미용',
                                 '신선식품', '가공식품', '건강식품', '출산/유아동', '반려동물용품',
                                 '가전', '휴대폰/카메라', 'PC/주변기기', '가구', '조명/인테리어',
                                 '패브릭/홈데코', '주방용품', '생활용품', '스포츠/레저', '자동차/오토바이',
                                 '키덜트/취미', '건강/의료용품', '악기/문구', '공구', '렌탈관',
                                 'E쿠폰/티켓/생활편의', '여행', '공식몰단독']

                for span in all_spans:
                    try:
                        text = await span.inner_text()
                        # 메인 카테고리가 아닌 것만 수집
                        if text and text.strip() not in main_categories and text != '더보기':
                            sub_categories.append(text.strip())
                    except:
                        continue

            # 중복 제거
            sub_categories = list(dict.fromkeys(sub_categories))[:20]  # 상위 20개

            if sub_categories:
                self.log(f"  → {len(sub_categories)}개 서브카테고리 수집", 'SUCCESS')

        except Exception as e:
            self.log(f"서브카테고리 수집 오류: {str(e)}", 'WARNING')

        return sub_categories

    def _save_results(self):
        """결과를 JSON 파일로 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/categories_{timestamp}.json'

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=2)

            self.log(f"카테고리 데이터 저장: {filename}", 'SUCCESS')

        except Exception as e:
            self.log(f"저장 중 오류: {str(e)}", 'ERROR')


# 테스트용 독립 실행
if __name__ == "__main__":
    async def main():
        collector = CategoryCollector(headless=False)
        categories = await collector.collect_categories()

        # 결과 출력
        for main_cat, info in categories.items():
            print(f"\n{main_cat} (ID: {info.get('id', 'N/A')})")
            for sub in info['sub_categories'][:5]:  # 상위 5개만 표시
                print(f"  - {sub}")

    asyncio.run(main())