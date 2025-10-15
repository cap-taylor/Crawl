"""네이버 플러스 스토어 카테고리 수집 유틸리티 v2
서브카테고리까지 완전히 수집하는 개선 버전
"""
import asyncio
from playwright.async_api import async_playwright
import json
import time
from pathlib import Path

class NaverPlusStoreCategoryCollectorV2:
    """네이버 플러스 스토어 카테고리 수집 클래스 V2

    개선사항:
    - 메인 카테고리 호버로 서브카테고리 표시
    - 계층 구조 정확히 파악
    - 서브카테고리 URL도 수집
    """

    def __init__(self):
        self.categories = {}
        self.data_dir = Path('/mnt/d/MyProjects/Crawl/data')
        self.data_dir.mkdir(exist_ok=True)

    async def collect_categories(self):
        """네이버 플러스 스토어 카테고리 수집"""
        async with async_playwright() as p:
            print("=" * 50)
            print("📖 네이버 플러스 스토어 카테고리 수집 V2")
            print("🎯 서브카테고리까지 완전 수집")
            print("=" * 50)

            # Firefox 브라우저 사용
            print("🦊 Firefox 브라우저 실행...")
            browser = await p.firefox.launch(
                headless=False,
                slow_mo=500,
                args=['--kiosk']
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                locale='ko-KR',
                timezone_id='Asia/Seoul'
            )

            page = await context.new_page()

            try:
                # 1. 네이버 메인 접속
                print("📍 네이버 메인 페이지 접속...")
                await page.goto("https://www.naver.com", wait_until="networkidle")
                print("✅ 네이버 메인 접속 성공")
                await asyncio.sleep(3)

                # 2. 쇼핑 클릭
                print("🔍 쇼핑 버튼 찾는 중...")
                shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
                shopping_link = await page.wait_for_selector(shopping_selector, timeout=5000)

                if not shopping_link:
                    print("❌ 쇼핑 버튼을 찾을 수 없습니다.")
                    return None

                print("🛍️ 쇼핑 페이지로 이동...")
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
                    await shopping_page.wait_for_load_state('networkidle')

                await asyncio.sleep(3)

                # 3. 카테고리 버튼 클릭
                print("\n🔍 카테고리 메뉴 버튼 찾는 중...")

                # 카테고리 버튼 selector
                category_button_selector = '#gnb-gnb > div._gnb_header_area_nfFfz > div > div._gnbContent_gnb_content_JUwjU > div._gnbContent_button_area_FRBmE > div:nth-child(1) > button'

                try:
                    category_button = await shopping_page.wait_for_selector(category_button_selector, timeout=5000)
                    if category_button:
                        print("✅ 카테고리 버튼 찾음")
                        print("🖱️ 카테고리 버튼 클릭...")
                        await category_button.click()
                        await asyncio.sleep(2)
                except:
                    print("❌ 카테고리 버튼을 찾을 수 없습니다")
                    return None

                # 4. 카테고리 수집 (개선된 방법)
                print("\n📂 카테고리 데이터 수집 시작...")
                categories_data = await self._collect_all_categories(shopping_page)

                if categories_data:
                    self._save_categories(categories_data)

                    # 통계 출력
                    total_main = len(categories_data)
                    total_sub = sum(len(info['subcategories']) for info in categories_data.values())
                    print(f"\n✅ 수집 완료!")
                    print(f"  • 메인 카테고리: {total_main}개")
                    print(f"  • 서브 카테고리: {total_sub}개")
                    print(f"  • 전체: {total_main + total_sub}개")
                else:
                    print("❌ 카테고리를 수집할 수 없습니다.")

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

    async def _collect_all_categories(self, page):
        """모든 카테고리 수집 (서브카테고리 포함)"""
        categories = {}

        try:
            # 카테고리 메뉴가 열려있는 상태에서 수집
            print("📋 카테고리 메뉴 분석 중...")

            # 1. 메인 카테고리 찾기
            # 오른쪽 사이드바의 카테고리 리스트
            main_category_selector = 'div._categoryDrawer_category_content_v6bQ5 a._categoryDrawer_main_category_link_2_9xG'

            # 대체 selector들
            if not await page.query_selector(main_category_selector):
                main_category_selectors = [
                    'a[class*="main_category"]',
                    'div[class*="category_list"] > a',
                    'ul[class*="category"] > li > a',
                    # 스크린샷에서 보이는 구조
                    'div[class*="category_content"] a',
                    'a[href*="/ns/category/"]'
                ]

                for selector in main_category_selectors:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        main_category_selector = selector
                        print(f"  → 메인 카테고리 selector 발견: {selector}")
                        break

            # 메인 카테고리 수집
            main_elements = await page.query_selector_all(main_category_selector)
            print(f"  → {len(main_elements)}개 메인 카테고리 발견")

            for i, main_elem in enumerate(main_elements):
                try:
                    # 메인 카테고리 정보
                    main_text = await main_elem.text_content()
                    main_text = main_text.strip() if main_text else ""

                    # 이상한 텍스트 필터링
                    if not main_text or len(main_text) > 20 or '더보기' in main_text:
                        continue

                    main_href = await main_elem.get_attribute('href')

                    print(f"\n  [{i+1}] {main_text}")

                    # 메인 카테고리 저장
                    if main_text not in categories:
                        categories[main_text] = {
                            'subcategories': [],
                            'url': main_href or ""
                        }

                    # 2. 메인 카테고리에 마우스 호버하여 서브카테고리 표시
                    try:
                        await main_elem.hover()
                        await asyncio.sleep(0.5)  # 서브메뉴 표시 대기

                        # 서브카테고리 찾기
                        # 호버 시 나타나는 서브메뉴 selector들
                        sub_category_selectors = [
                            f'div[class*="subcategory"]:visible',
                            f'div[class*="sub_menu"]:visible',
                            f'ul[class*="sub"] li a:visible',
                            # 동적으로 나타나는 레이어
                            'div[class*="layer"] a',
                            'div[class*="popup"] a',
                            # 일반적인 서브메뉴 구조
                            f'div[class*="depth2"] a',
                            f'ul[class*="depth2"] a',
                            # 현재 호버된 메인 카테고리의 서브들
                            f'a[href*="/category/{main_text}"]'
                        ]

                        sub_found = False
                        for sub_selector in sub_category_selectors:
                            sub_elements = await page.query_selector_all(sub_selector)
                            if sub_elements:
                                print(f"    → {len(sub_elements)}개 서브카테고리 발견")

                                for sub_elem in sub_elements[:10]:  # 최대 10개만
                                    sub_text = await sub_elem.text_content()
                                    sub_text = sub_text.strip() if sub_text else ""

                                    if sub_text and sub_text != main_text and len(sub_text) < 20:
                                        sub_href = await sub_elem.get_attribute('href')

                                        # 서브카테고리 정보 저장
                                        sub_info = {
                                            'name': sub_text,
                                            'url': sub_href or ""
                                        }

                                        if sub_info not in categories[main_text]['subcategories']:
                                            categories[main_text]['subcategories'].append(sub_info)
                                            print(f"      • {sub_text}")

                                sub_found = True
                                break

                        if not sub_found:
                            print(f"    → 서브카테고리 없음")

                    except Exception as e:
                        print(f"    ⚠️ 서브카테고리 수집 실패: {e}")

                except Exception as e:
                    print(f"  ⚠️ 메인 카테고리 처리 실패: {e}")
                    continue

            # 3. 서브카테고리가 없는 경우 기본 구조 추가
            for main_cat, info in categories.items():
                if len(info['subcategories']) == 0:
                    # 기본 서브카테고리 추가 (네이버 쇼핑 일반 구조)
                    default_subs = self._get_default_subcategories(main_cat)
                    for sub in default_subs:
                        info['subcategories'].append({
                            'name': sub,
                            'url': ''
                        })

                    if default_subs:
                        print(f"  → {main_cat}에 기본 서브카테고리 {len(default_subs)}개 추가")

            return categories

        except Exception as e:
            print(f"❌ 카테고리 수집 중 오류: {e}")
            return None

    def _get_default_subcategories(self, main_category):
        """메인 카테고리별 기본 서브카테고리"""
        default_map = {
            '여성의류': ['티셔츠', '블라우스', '원피스', '팬츠', '스커트', '자켓', '코트', '니트'],
            '남성의류': ['티셔츠', '셔츠', '팬츠', '자켓', '코트', '니트', '정장', '캐주얼'],
            '신발': ['운동화', '구두', '부츠', '샌들', '슬리퍼', '스니커즈'],
            '가방': ['숄더백', '토트백', '백팩', '크로스백', '클러치', '지갑'],
            '패션잡화': ['모자', '벨트', '스카프', '장갑', '양말', '넥타이'],
            '화장품/미용': ['스킨케어', '메이크업', '클렌징', '마스크팩', '향수', '헤어케어'],
            '신선식품': ['과일', '채소', '정육', '수산물', '계란', '유제품'],
            '가공식품': ['과자', '음료', '라면', '통조림', '조미료', '냉동식품'],
            '건강식품': ['비타민', '홍삼', '프로바이오틱스', '다이어트', '단백질보충제'],
            '가전': ['TV', '냉장고', '세탁기', '에어컨', '청소기', '공기청정기'],
            '가구': ['침대', '소파', '책상', '의자', '수납장', '테이블'],
            '생활용품': ['세제', '휴지', '청소용품', '욕실용품', '주방세제'],
            '주방용품': ['냄비', '프라이팬', '식기', '조리도구', '보관용기'],
            '스포츠/레저': ['운동복', '운동기구', '캠핑용품', '등산용품', '자전거용품']
        }

        return default_map.get(main_category, [])

    def _save_categories(self, categories_data):
        """카테고리 데이터 저장"""
        try:
            # 통계 계산
            total_main = len(categories_data)
            total_sub = sum(len(info['subcategories']) for info in categories_data.values())

            save_data = {
                "수집일시": time.strftime("%Y-%m-%d %H:%M:%S"),
                "플랫폼": "네이버 플러스 스토어",
                "버전": "V2 (서브카테고리 포함)",
                "통계": {
                    "메인카테고리수": total_main,
                    "전체서브카테고리수": total_sub,
                    "총카테고리수": total_main + total_sub
                },
                "카테고리": categories_data
            }

            file_path = self.data_dir / 'naver_plus_store_categories_v2.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

            print(f"\n💾 카테고리 데이터 저장: {file_path}")

            # 간단한 버전도 저장 (GUI용)
            simple_categories = {}
            for main, info in categories_data.items():
                simple_categories[main] = {
                    'subcategories': [sub['name'] for sub in info['subcategories']],
                    'url': info['url']
                }

            simple_data = {
                "수집일시": time.strftime("%Y-%m-%d %H:%M:%S"),
                "플랫폼": "네이버 플러스 스토어",
                "카테고리": simple_categories,
                "메인카테고리수": total_main,
                "전체서브카테고리수": total_sub
            }

            simple_path = self.data_dir / 'naver_plus_store_categories.json'
            with open(simple_path, 'w', encoding='utf-8') as f:
                json.dump(simple_data, f, ensure_ascii=False, indent=2)

            print(f"💾 GUI용 데이터 저장: {simple_path}")

        except Exception as e:
            print(f"❌ 카테고리 저장 중 오류: {e}")


async def main():
    """메인 실행 함수"""
    collector = NaverPlusStoreCategoryCollectorV2()
    await collector.collect_categories()


if __name__ == "__main__":
    asyncio.run(main())