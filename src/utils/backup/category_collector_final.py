"""네이버 플러스 스토어 카테고리 수집 유틸리티 - 최종 버전
CRAWLING_LESSONS_LEARNED.md 문서 기반 정확한 서브카테고리 수집
"""
import asyncio
from playwright.async_api import async_playwright
import json
import time
from pathlib import Path

class NaverCategoryCollectorFinal:
    """네이버 플러스 스토어 카테고리 수집 - 문서 기반 최종 버전"""

    def __init__(self):
        self.categories = {}
        self.data_dir = Path('/mnt/d/MyProjects/Crawl/data')
        self.data_dir.mkdir(exist_ok=True)

    async def collect_categories(self):
        """카테고리 수집 메인 함수"""
        async with async_playwright() as p:
            print("=" * 60)
            print("📖 네이버 플러스 스토어 카테고리 수집 - 최종 버전")
            print("📚 CRAWLING_LESSONS_LEARNED.md 문서 기반")
            print("🎯 정확한 서브카테고리 수집")
            print("=" * 60)

            # Firefox 브라우저 사용 (문서에서 검증된 방법)
            print("\n🦊 Firefox 브라우저 실행...")
            browser = await p.firefox.launch(
                headless=False,  # 필수!
                slow_mo=500,     # 천천히 동작
                args=['--kiosk'] # 전체화면
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                locale='ko-KR',
                timezone_id='Asia/Seoul'
            )

            page = await context.new_page()

            try:
                # 1. 네이버 메인 접속 (직접 URL 금지!)
                print("📍 네이버 메인 페이지 접속...")
                await page.goto("https://www.naver.com", wait_until="networkidle")
                print("✅ 네이버 메인 접속 성공")
                await asyncio.sleep(3)

                # 2. 쇼핑 클릭
                print("\n🔍 쇼핑 버튼 찾는 중...")
                shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'

                try:
                    shopping_link = await page.wait_for_selector(shopping_selector, timeout=5000)
                    print(f"✅ 쇼핑 버튼 찾음")
                except:
                    print("❌ 쇼핑 버튼을 찾을 수 없습니다")
                    return None

                # 새 탭에서 쇼핑 페이지 열기
                print("🛍️ 쇼핑 페이지로 이동 (새 탭)...")
                initial_pages = len(context.pages)
                await shopping_link.click()
                await asyncio.sleep(3)

                # 새 탭으로 전환
                all_pages = context.pages
                if len(all_pages) > initial_pages:
                    shopping_page = all_pages[-1]
                    await shopping_page.wait_for_load_state('networkidle')
                    print(f"✅ 쇼핑 페이지 접속: {shopping_page.url}")
                else:
                    shopping_page = page

                await asyncio.sleep(3)

                # 3. 카테고리 버튼 클릭 (문서에서 확인된 정확한 selector)
                print("\n🔍 카테고리 메뉴 버튼 찾는 중...")
                category_button_selector = '#gnb-gnb > div._gnb_header_area_nfFfz > div > div._gnbContent_gnb_content_JUwjU > div._gnbContent_button_area_FRBmE > div:nth-child(1) > button'

                try:
                    category_button = await shopping_page.wait_for_selector(category_button_selector, timeout=5000)
                    print("✅ 카테고리 버튼 찾음")
                    print("🖱️ 카테고리 버튼 클릭...")
                    await category_button.click()
                    await asyncio.sleep(2)  # 메뉴 열리기 대기

                    # 스크린샷 저장
                    screenshot_path = self.data_dir / f'category_menu_opened_{time.strftime("%Y%m%d_%H%M%S")}.png'
                    await shopping_page.screenshot(path=str(screenshot_path))
                    print(f"📸 카테고리 메뉴 스크린샷: {screenshot_path}")

                except Exception as e:
                    print(f"❌ 카테고리 버튼 클릭 실패: {e}")
                    # 대체 selector 시도
                    try:
                        category_button = await shopping_page.query_selector('button:has-text("카테고리")')
                        if category_button:
                            await category_button.click()
                            await asyncio.sleep(2)
                            print("✅ 대체 selector로 카테고리 버튼 클릭 성공")
                    except:
                        print("❌ 카테고리 메뉴를 열 수 없습니다")
                        return None

                # 4. 카테고리 수집 (문서 기반 정확한 방법)
                print("\n📂 카테고리 데이터 수집 시작...")
                categories_data = await self._collect_categories_correctly(shopping_page)

                if categories_data:
                    self._save_categories(categories_data)

                    # 통계 출력
                    total_main = len(categories_data)
                    total_sub = sum(len(info['subcategories']) for info in categories_data.values())

                    print("\n✅ 수집 완료!")
                    print(f"  • 메인 카테고리: {total_main}개")
                    print(f"  • 서브 카테고리: {total_sub}개")
                    print(f"  • 전체: {total_main + total_sub}개")

                    # 샘플 데이터 출력
                    print("\n📋 수집된 카테고리 샘플:")
                    for i, (main, info) in enumerate(list(categories_data.items())[:3]):
                        print(f"\n  [{i+1}] {main}")
                        for j, sub in enumerate(info['subcategories'][:5]):
                            if isinstance(sub, dict):
                                print(f"      - {sub.get('name', sub)}")
                            else:
                                print(f"      - {sub}")
                        if len(info['subcategories']) > 5:
                            print(f"      ... 외 {len(info['subcategories'])-5}개")
                else:
                    print("❌ 카테고리를 수집할 수 없습니다")

                # 10초 대기
                print("\n👀 10초 후 브라우저 종료...")
                await asyncio.sleep(10)

            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                import traceback
                traceback.print_exc()

            finally:
                await browser.close()
                print("🔚 브라우저 종료")

    async def _collect_categories_correctly(self, page):
        """문서 기반 정확한 카테고리 수집"""
        categories = {}

        try:
            # 1. 메인 카테고리 수집 (문서에서 확인된 selector)
            print("\n📋 메인 카테고리 수집 중...")

            # 메인 카테고리 링크 selector (문서 기반)
            main_selector = 'a._categoryLayer_link_8hzu'

            # selector가 안 맞으면 대체 시도
            main_elements = await page.query_selector_all(main_selector)
            if not main_elements:
                print("  → 기본 selector 실패, 대체 selector 시도...")
                alternative_selectors = [
                    'div._categoryLayer_category_layer_1JUQ0 a',
                    '[class*="categoryLayer"] a[href*="/category/"]',
                    'div[class*="category_content"] a',
                    'ul[class*="category_list"] > li > a'
                ]

                for alt_selector in alternative_selectors:
                    main_elements = await page.query_selector_all(alt_selector)
                    if main_elements:
                        print(f"  → 대체 selector 성공: {alt_selector}")
                        break

            print(f"  → {len(main_elements)}개 메인 카테고리 발견")

            # 2. 각 메인 카테고리별 서브카테고리 수집
            for idx, main_elem in enumerate(main_elements):
                try:
                    # 메인 카테고리 정보 추출
                    main_text = await main_elem.text_content()
                    if not main_text:
                        continue

                    main_text = main_text.strip()

                    # 특별 카테고리 제외
                    if main_text in ['베스트', 'N배송', '패션타운', 'LUXURY', 'FashionTown',
                                     '미스터', '편집샵', '럭셔리', '더보기', '']:
                        continue

                    main_href = await main_elem.get_attribute('href')

                    # 카테고리 ID 추출
                    category_id = None
                    if main_href and '/category/' in main_href:
                        parts = main_href.split('/category/')[-1].split('/')
                        if parts[0].isdigit():
                            category_id = parts[0]

                    print(f"\n  [{idx+1}] {main_text} (ID: {category_id})")

                    # 메인 카테고리 저장
                    categories[main_text] = {
                        'id': category_id,
                        'url': main_href or '',
                        'subcategories': []
                    }

                    # 3. 호버하여 서브카테고리 표시 (문서 기반)
                    print(f"    → 호버하여 서브카테고리 표시...")
                    await main_elem.hover()
                    await asyncio.sleep(1.5)  # 서브메뉴 로딩 대기 (충분히!)

                    # 서브카테고리 수집 (문서에서 확인된 selector)
                    sub_selector = 'span._categoryLayer_text_XOd4h'
                    sub_elements = await page.query_selector_all(sub_selector)

                    if not sub_elements:
                        # 대체 selector 시도
                        print("    → 기본 서브 selector 실패, 대체 시도...")
                        alt_sub_selectors = [
                            f'[class*="categoryLayer"][class*="sub"] a',
                            f'div[class*="layer"] a[href*="{category_id}"]' if category_id else '',
                            f'[class*="subcategory"] a',
                            f'[class*="depth2"] a'
                        ]

                        for alt_sub in alt_sub_selectors:
                            if alt_sub:
                                sub_elements = await page.query_selector_all(alt_sub)
                                if sub_elements:
                                    break

                    # 서브카테고리 정보 수집
                    sub_count = 0
                    for sub_elem in sub_elements:
                        try:
                            # 텍스트 추출
                            if sub_elem.name == 'span':
                                sub_text = await sub_elem.text_content()
                                # 부모 a 태그에서 href 가져오기
                                parent = await sub_elem.evaluate_handle('el => el.parentElement')
                                sub_href = await parent.get_property('href')
                                sub_href = str(await sub_href.json_value()) if sub_href else ''
                            else:
                                sub_text = await sub_elem.text_content()
                                sub_href = await sub_elem.get_attribute('href') or ''

                            if not sub_text:
                                continue

                            sub_text = sub_text.strip()

                            # 필터링: 메인 카테고리 중복, 더보기, 빈 값 제외
                            if (sub_text == main_text or
                                sub_text in ['더보기', '더보기 >', ''] or
                                sub_text in categories.keys() or
                                len(sub_text) > 30):  # 너무 긴 텍스트 제외
                                continue

                            # 서브카테고리 저장
                            sub_info = {
                                'name': sub_text,
                                'url': sub_href
                            }

                            if sub_info not in categories[main_text]['subcategories']:
                                categories[main_text]['subcategories'].append(sub_info)
                                sub_count += 1

                                # 처음 5개만 출력
                                if sub_count <= 5:
                                    print(f"      • {sub_text}")

                        except Exception as e:
                            continue

                    if sub_count > 5:
                        print(f"      ... 외 {sub_count-5}개")
                    elif sub_count == 0:
                        print("      → 서브카테고리 없음")

                except Exception as e:
                    print(f"  ⚠️ {main_text} 처리 중 오류: {e}")
                    continue

            # 4. 데이터 검증
            print("\n📊 수집 데이터 검증...")

            # 빈 서브카테고리 처리
            for main_cat, info in categories.items():
                if len(info['subcategories']) == 0:
                    print(f"  → {main_cat}: 서브카테고리 없음")

            return categories

        except Exception as e:
            print(f"❌ 카테고리 수집 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _save_categories(self, categories_data):
        """카테고리 데이터 저장"""
        try:
            # 통계 계산
            total_main = len(categories_data)
            total_sub = sum(len(info['subcategories']) for info in categories_data.values())

            # 전체 데이터 저장
            save_data = {
                "수집일시": time.strftime("%Y-%m-%d %H:%M:%S"),
                "플랫폼": "네이버 플러스 스토어",
                "버전": "최종 (CRAWLING_LESSONS_LEARNED.md 기반)",
                "통계": {
                    "메인카테고리수": total_main,
                    "전체서브카테고리수": total_sub,
                    "총카테고리수": total_main + total_sub
                },
                "카테고리": categories_data
            }

            file_path = self.data_dir / 'naver_categories_final.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

            print(f"\n💾 전체 데이터 저장: {file_path}")

            # GUI용 간단한 버전 저장
            simple_categories = {}
            for main, info in categories_data.items():
                simple_categories[main] = {
                    'subcategories': [
                        sub['name'] if isinstance(sub, dict) else sub
                        for sub in info['subcategories']
                    ],
                    'url': info.get('url', ''),
                    'id': info.get('id', '')
                }

            simple_data = {
                "수집일시": time.strftime("%Y-%m-%d %H:%M:%S"),
                "플랫폼": "네이버 플러스 스토어",
                "카테고리": simple_categories,
                "메인카테고리수": total_main,
                "전체서브카테고리수": total_sub
            }

            # 기존 GUI 파일 덮어쓰기
            gui_path = self.data_dir / 'naver_plus_store_categories.json'
            with open(gui_path, 'w', encoding='utf-8') as f:
                json.dump(simple_data, f, ensure_ascii=False, indent=2)

            print(f"💾 GUI용 데이터 저장: {gui_path}")

        except Exception as e:
            print(f"❌ 데이터 저장 중 오류: {e}")


async def main():
    """메인 실행 함수"""
    collector = NaverCategoryCollectorFinal()
    await collector.collect_categories()


if __name__ == "__main__":
    asyncio.run(main())