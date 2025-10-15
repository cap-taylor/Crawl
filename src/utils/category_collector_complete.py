"""네이버 쇼핑 전체 카테고리 구조 완벽 수집기"""
import asyncio
import json
import time
from playwright.async_api import async_playwright
from datetime import datetime

class CompleteCategoryCollector:
    def __init__(self, gui=None, headless=False):
        self.gui = gui
        self.headless = headless
        self.categories = {}
        self.total_count = 0
        self.all_categories_flat = []  # 모든 카테고리 평면 리스트

    def log(self, message, level='INFO'):
        """로그 메시지 출력"""
        print(f"[{level}] {message}")
        if self.gui:
            self.gui.add_log(message, level)

    async def collect_all_categories(self):
        """모든 카테고리를 세부까지 완벽하게 수집"""
        async with async_playwright() as p:
            try:
                # Firefox 브라우저 사용
                self.log("Firefox 브라우저를 시작합니다...", 'INFO')
                browser = await p.firefox.launch(
                    headless=self.headless,
                    args=['--kiosk'] if not self.headless else [],
                    slow_mo=300  # 천천히 동작
                )

                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                    locale='ko-KR',
                    timezone_id='Asia/Seoul'
                )

                page = await context.new_page()

                # 1. 네이버 메인 접속
                self.log("네이버 메인 페이지 접속...", 'INFO')
                await page.goto('https://www.naver.com')
                await asyncio.sleep(3)

                # 2. 쇼핑 클릭
                self.log("쇼핑 페이지로 이동...", 'INFO')
                shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
                shopping_link = await page.wait_for_selector(shopping_selector, timeout=10000)
                await shopping_link.click()
                await asyncio.sleep(3)

                # 3. 새 탭으로 전환
                all_pages = context.pages
                if len(all_pages) > 1:
                    page = all_pages[-1]
                    await page.wait_for_load_state('networkidle')
                    self.log("쇼핑 페이지 로드 완료", 'SUCCESS')

                # 4. 카테고리 버튼 찾기 - 다양한 셀렉터 시도
                self.log("카테고리 메뉴를 찾는 중...", 'INFO')

                category_selectors = [
                    'button:has-text("카테고리")',
                    'button[aria-label*="카테고리"]',
                    '[class*="category"][class*="button"]',
                    '#gnb-gnb button:has-text("카테고리")',
                    'button[class*="_gnbCategory"]',
                    'div[class*="button_area"] button:first-child',
                    'button span:has-text("카테고리")',
                ]

                category_btn = None
                for selector in category_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for elem in elements:
                            text = await elem.inner_text()
                            if "카테고리" in text:
                                category_btn = elem
                                self.log(f"카테고리 버튼 발견: {selector}", 'SUCCESS')
                                break
                        if category_btn:
                            break
                    except:
                        continue

                if not category_btn:
                    # 페이지 내 모든 버튼 검사
                    self.log("모든 버튼을 검사 중...", 'WARNING')
                    all_buttons = await page.query_selector_all('button')
                    for btn in all_buttons:
                        try:
                            text = await btn.inner_text()
                            if "카테고리" in text:
                                category_btn = btn
                                self.log("카테고리 버튼을 찾았습니다!", 'SUCCESS')
                                break
                        except:
                            continue

                if category_btn:
                    await category_btn.click()
                    await asyncio.sleep(2)
                    self.log("카테고리 메뉴가 열렸습니다", 'SUCCESS')

                    # 5. 전체 카테고리 구조 수집
                    await self._collect_category_structure(page)
                else:
                    self.log("카테고리 버튼을 찾을 수 없습니다", 'ERROR')

                await browser.close()

                # 결과 저장
                self._save_results()
                self._save_flat_list()

                self.log(f"전체 카테고리 수집 완료! 총 {self.total_count}개", 'SUCCESS')
                return self.categories

            except Exception as e:
                self.log(f"오류 발생: {str(e)}", 'ERROR')
                import traceback
                traceback.print_exc()
                raise

    async def _collect_category_structure(self, page):
        """전체 카테고리 구조 수집 (대분류 > 중분류 > 소분류 > 세부분류)"""
        try:
            # 대분류 카테고리 찾기 - 왼쪽 메인 메뉴에서만
            main_selectors = [
                'div[class*="categoryLayer_category_layer"] > ul > li > a',  # 메인 레이어의 직계 자식
                'div[class*="categoryLayer"] > ul:first-child > li > a',  # 첫 번째 ul의 항목들
                'ul[class*="category_list"] > li > a',  # 카테고리 리스트
                'a[data-leaf="false"]',  # 하위 카테고리가 있는 것들
            ]

            main_categories = []
            for selector in main_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        self.log(f"셀렉터 {selector}로 {len(elements)}개 요소 발견", 'INFO')

                        # 대분류인지 확인 (보통 왼쪽에 있고, 큰 카테고리)
                        for elem in elements:
                            try:
                                # 요소가 보이는지 확인
                                is_visible = await elem.is_visible()
                                if not is_visible:
                                    continue

                                text = await elem.inner_text()
                                # 대분류 카테고리 이름들 (네이버 쇼핑 기준)
                                main_category_names = [
                                    '여성의류', '남성의류', '패션잡화', '신발', '화장품/미용',
                                    '신선식품', '가공식품', '건강식품', '출산/유아동', '반려동물용품',
                                    '가전', '휴대폰/카메라', 'PC/주변기기', '가구', '조명/인테리어',
                                    '패브릭/홈데코', '주방용품', '생활용품', '스포츠/레저', '자동차/오토바이',
                                    '키덜트/취미', '건강/의료용품', '악기/문구', '공구', '렌탈관',
                                    'E쿠폰/티켓/생활편의', '여행'
                                ]

                                if text in main_category_names:
                                    main_categories.append(elem)
                            except:
                                continue

                        if main_categories:
                            self.log(f"대분류 카테고리 {len(main_categories)}개 확정", 'INFO')
                            break
                except:
                    continue

            if not main_categories:
                # 대안: 보이는 모든 카테고리 링크에서 대분류 찾기
                all_links = await page.query_selector_all('a[href*="/category/"]')
                for link in all_links[:50]:
                    try:
                        text = await link.inner_text()
                        if text and len(text) < 15:  # 대분류는 보통 짧음
                            main_categories.append(link)
                            if len(main_categories) >= 30:
                                break
                    except:
                        continue

            # 각 대분류 처리
            for idx, main_cat in enumerate(main_categories, 1):
                try:
                    cat_name = await main_cat.inner_text()
                    cat_id = await main_cat.get_attribute('data-id')

                    if not cat_name or cat_name in ['더보기', '전체보기']:
                        continue

                    self.log(f"\n[{idx}/{len(main_categories)}] 대분류: {cat_name}", 'INFO')

                    # 대분류 호버 또는 클릭
                    await main_cat.hover()
                    await asyncio.sleep(1.5)

                    # 중분류 수집
                    sub_categories = await self._collect_sub_categories(page, cat_name, 1)

                    # 데이터 구조 저장
                    self.categories[cat_name] = {
                        'id': cat_id,
                        'level': 0,  # 대분류
                        'name': cat_name,
                        'sub_categories': sub_categories,
                        'total_count': self._count_all_categories(sub_categories)
                    }

                    self.total_count += 1 + self.categories[cat_name]['total_count']

                    # 평면 리스트에 추가
                    self._add_to_flat_list(cat_name, cat_id, 0, None)

                    if self.gui:
                        self.gui.update_status(
                            category_name=cat_name,
                            category_count=self.total_count
                        )

                except Exception as e:
                    self.log(f"대분류 처리 오류: {str(e)}", 'WARNING')
                    continue

        except Exception as e:
            self.log(f"카테고리 구조 수집 오류: {str(e)}", 'ERROR')

    async def _collect_sub_categories(self, page, parent_name, level):
        """하위 카테고리 재귀적 수집"""
        sub_categories = []

        try:
            # 호버 후 약간 대기하여 서브메뉴가 로드되도록
            await asyncio.sleep(0.5)

            # 현재 보이는 서브카테고리 찾기 - 오른쪽 패널에서
            sub_selectors = [
                'div[class*="categoryLayer_sub_panel"] a',  # 서브 패널 내의 링크
                'div[class*="sub_category"] a',  # 서브 카테고리 영역
                'div[aria-expanded="true"] + div a',  # 확장된 영역의 링크
                'div[class*="panel"]:not([style*="none"]) a',  # 보이는 패널의 링크
            ]

            # 대분류 카테고리 이름들 (제외할 항목)
            main_category_names = [
                '여성의류', '남성의류', '패션잡화', '신발', '화장품/미용',
                '신선식품', '가공식품', '건강식품', '출산/유아동', '반려동물용품',
                '가전', '휴대폰/카메라', 'PC/주변기기', '가구', '조명/인테리어',
                '패브릭/홈데코', '주방용품', '생활용품', '스포츠/레저', '자동차/오토바이',
                '키덜트/취미', '건강/의료용품', '악기/문구', '공구', '렌탈관',
                'E쿠폰/티켓/생활편의', '여행'
            ]

            found_elements = []
            for selector in sub_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        # 보이는 요소만 필터링
                        for elem in elements:
                            try:
                                is_visible = await elem.is_visible()
                                if is_visible:
                                    text = await elem.inner_text()
                                    # 대분류가 아니고, 부모와 다른 이름인 경우만
                                    if (text and
                                        text not in main_category_names and
                                        text != parent_name and
                                        text not in ['더보기', '전체보기', '전체']):
                                        found_elements.append(elem)
                            except:
                                continue

                        if found_elements:
                            break
                except:
                    continue

            # 수집된 요소들 처리
            seen_names = set()
            for elem in found_elements:
                try:
                    text = await elem.inner_text()
                    elem_id = await elem.get_attribute('data-id')

                    # 중복 제거
                    if text not in seen_names:
                        seen_names.add(text)

                        sub_cat_data = {
                            'name': text.strip(),
                            'id': elem_id,
                            'level': level,
                            'sub_categories': []
                        }

                        # 재귀적 수집은 깊이 제한 (3레벨까지)
                        if level < 3:
                            has_sub = await elem.get_attribute('data-leaf')
                            if has_sub == 'false':
                                await elem.hover()
                                await asyncio.sleep(0.5)
                                sub_cat_data['sub_categories'] = await self._collect_sub_categories(
                                    page, text, level + 1
                                )

                        sub_categories.append(sub_cat_data)

                        # 평면 리스트에 추가
                        self._add_to_flat_list(text, elem_id, level, parent_name)

                except:
                    continue

            # 중복 제거
            seen = set()
            unique_subs = []
            for sub in sub_categories:
                if sub['name'] not in seen:
                    seen.add(sub['name'])
                    unique_subs.append(sub)

            if unique_subs:
                self.log(f"  {'  ' * level}→ {len(unique_subs)}개 수집", 'SUCCESS')

            return unique_subs[:30]  # 각 레벨당 최대 30개

        except Exception as e:
            self.log(f"서브카테고리 수집 오류: {str(e)}", 'WARNING')
            return []

    def _count_all_categories(self, categories):
        """전체 카테고리 개수 카운트 (재귀)"""
        count = len(categories)
        for cat in categories:
            if 'sub_categories' in cat and cat['sub_categories']:
                count += self._count_all_categories(cat['sub_categories'])
        return count

    def _add_to_flat_list(self, name, cat_id, level, parent):
        """평면 리스트에 카테고리 추가"""
        self.all_categories_flat.append({
            'name': name,
            'id': cat_id,
            'level': level,
            'parent': parent,
            'full_path': f"{parent} > {name}" if parent else name
        })

    def _save_results(self):
        """계층 구조로 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/categories_complete_{timestamp}.json'

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=2)

            self.log(f"계층 구조 저장: {filename}", 'SUCCESS')

        except Exception as e:
            self.log(f"저장 오류: {str(e)}", 'ERROR')

    def _save_flat_list(self):
        """평면 리스트로 저장 (검색/매칭용)"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/categories_flat_{timestamp}.json'

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_categories_flat, f, ensure_ascii=False, indent=2)

            self.log(f"평면 리스트 저장: {filename}", 'SUCCESS')

            # 카테고리 이름만 추출한 리스트도 저장
            names_only = [cat['name'] for cat in self.all_categories_flat]
            names_file = f'data/category_names_{timestamp}.json'

            with open(names_file, 'w', encoding='utf-8') as f:
                json.dump(names_only, f, ensure_ascii=False, indent=2)

            self.log(f"카테고리 이름 리스트 저장: {names_file}", 'SUCCESS')

        except Exception as e:
            self.log(f"평면 리스트 저장 오류: {str(e)}", 'ERROR')


# 독립 실행
if __name__ == "__main__":
    async def main():
        collector = CompleteCategoryCollector(headless=False)
        categories = await collector.collect_all_categories()

        # 결과 요약 출력
        print("\n" + "=" * 60)
        print("📊 수집 완료 요약")
        print("=" * 60)

        if categories:
            print(f"✅ 대분류: {len(categories)}개")

            total_sub = 0
            for main_cat, info in categories.items():
                sub_count = info.get('total_count', 0)
                total_sub += sub_count
                print(f"  - {main_cat}: {sub_count}개 하위 카테고리")

            print(f"\n✅ 전체 카테고리: {len(categories) + total_sub}개")

    asyncio.run(main())