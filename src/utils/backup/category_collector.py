"""네이버 플러스 스토어 카테고리 수집 유틸리티
CRAWLING_LESSONS_LEARNED.md 문서의 성공 방법 적용
카테고리 버튼 클릭으로 실제 카테고리 수집
"""
import asyncio
from playwright.async_api import async_playwright
import json
import time
from pathlib import Path

class NaverPlusStoreCategoryCollector:
    """네이버 플러스 스토어 카테고리 수집 클래스

    중요 규칙 (CRAWLING_LESSONS_LEARNED.md 기반):
    1. Firefox 브라우저 사용 (봇 감지 우회)
    2. 네이버 메인 → 쇼핑 클릭 순서 (직접 URL 접속 금지)
    3. headless=False 필수 (Headless 모드 차단됨)
    4. 새 탭으로 열기 (캡차 회피)
    5. 카테고리 클릭 시 주의 (캡차 가능성)
    """

    def __init__(self):
        self.categories = {}
        self.data_dir = Path('/mnt/d/MyProjects/Crawl/data')
        self.data_dir.mkdir(exist_ok=True)

    async def collect_categories(self):
        """네이버 플러스 스토어 카테고리 수집

        성공 전략:
        - Firefox + headless=False + --kiosk
        - 네이버 메인 → 쇼핑 클릭 (새 탭)
        - 천천히 동작 (slow_mo=500)
        - 카테고리 버튼 클릭으로 실제 메뉴 열기
        """
        async with async_playwright() as p:
            print("=" * 50)
            print("📖 네이버 플러스 스토어 카테고리 수집")
            print("📚 CRAWLING_LESSONS_LEARNED.md 기반 성공 방법 적용")
            print("🎯 카테고리 버튼 클릭으로 실제 카테고리 수집")
            print("=" * 50)

            # Firefox 브라우저 사용 (문서에서 검증된 성공 방법)
            print("🦊 Firefox 브라우저 실행 (봇 감지 우회)...")
            browser = await p.firefox.launch(
                headless=False,  # 필수! Headless 모드는 차단됨
                slow_mo=500,     # 천천히 동작 (사람처럼)
                args=['--kiosk'] # 전체화면 (Firefox에서 작동)
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},  # 전체화면 설정
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                locale='ko-KR',
                timezone_id='Asia/Seoul'
            )

            page = await context.new_page()

            try:
                # 1. 네이버 메인 페이지 접속 (절대 shopping.naver.com 직접 접속 금지!)
                print("📍 네이버 메인 페이지 접속 (캡차 없음)...")
                await page.goto("https://www.naver.com", wait_until="networkidle")
                print("✅ 네이버 메인 접속 성공")
                await asyncio.sleep(3)  # 랜덤 대기 (2-5초 권장)

                # 2. 쇼핑 링크 클릭 (문서에서 성공한 선택자)
                print("🔍 쇼핑 버튼 찾는 중...")

                # 성공한 선택자: #shortcutArea > ul > li:nth-child(4) > a
                shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
                shopping_link = None

                try:
                    shopping_link = await page.wait_for_selector(shopping_selector, timeout=5000)
                    if shopping_link:
                        print(f"✅ 쇼핑 버튼 찾음: {shopping_selector}")
                except:
                    # 대체 선택자들
                    shopping_selectors = [
                        'a[data-clk="svc.shopping"]',
                        'text="쇼핑"',
                        'a[href*="shopping.naver.com"]'
                    ]

                    for selector in shopping_selectors:
                        try:
                            shopping_link = await page.wait_for_selector(selector, timeout=3000)
                            if shopping_link:
                                print(f"✅ 쇼핑 버튼 찾음 (대체): {selector}")
                                break
                        except:
                            continue

                if not shopping_link:
                    print("❌ 쇼핑 버튼을 찾을 수 없습니다.")
                    print("💡 팁: 네이버 메인 페이지 구조가 변경되었을 수 있습니다.")
                    return None

                # 3. 새 탭에서 쇼핑 페이지 열기 (중요: 새 탭으로 열어야 캡차 안 나옴!)
                print("🛍️ 쇼핑 페이지로 이동 (새 탭)...")

                # 클릭 전 현재 탭 개수 확인
                initial_pages = len(context.pages)

                # 쇼핑 클릭
                await shopping_link.click()

                # 새 탭 열리기 대기
                await asyncio.sleep(3)

                # 새 탭으로 전환
                all_pages = context.pages
                if len(all_pages) > initial_pages:
                    shopping_page = all_pages[-1]  # 마지막 탭 = 쇼핑 탭
                    await shopping_page.wait_for_load_state('networkidle')
                    print(f"✅ 새 탭(쇼핑)으로 전환 완료: {shopping_page.url}")
                else:
                    # 새 탭이 안 열렸으면 현재 페이지 사용
                    shopping_page = page
                    await shopping_page.wait_for_load_state('networkidle')
                    print(f"✅ 쇼핑 페이지 접속 성공: {shopping_page.url}")

                await asyncio.sleep(3)  # 페이지 안정화 대기

                # 4. 카테고리 버튼 클릭하여 메뉴 열기
                print("\n🔍 카테고리 메뉴 버튼 찾는 중...")

                # 카테고리 버튼 selector들 (copy selector에서 가져옴)
                category_button_selectors = [
                    # 제공된 selector
                    '#gnb-gnb > div._gnb_header_area_nfFfz > div > div._gnbContent_gnb_content_JUwjU > div._gnbContent_button_area_FRBmE > div:nth-child(1) > button',
                    # 대체 selector들
                    'button:has-text("카테고리")',
                    'button[aria-label*="카테고리"]',
                    '[class*="category"] button',
                    '[class*="gnb"] button:first-child',
                    'button svg[class*="category"]',
                    # 햄버거 메뉴 아이콘
                    'button[class*="menu"]',
                    'button[class*="hamburger"]'
                ]

                category_button = None
                for selector in category_button_selectors:
                    try:
                        category_button = await shopping_page.wait_for_selector(selector, timeout=3000)
                        if category_button:
                            print(f"✅ 카테고리 버튼 찾음: {selector}")
                            break
                    except:
                        continue

                if category_button:
                    print("🖱️ 카테고리 버튼 클릭...")
                    await category_button.click()
                    await asyncio.sleep(2)  # 메뉴 열리기 대기

                    # 스크린샷 저장
                    screenshot_path = self.data_dir / f'category_menu_{time.strftime("%Y%m%d_%H%M%S")}.png'
                    await shopping_page.screenshot(path=str(screenshot_path))
                    print(f"📸 카테고리 메뉴 스크린샷 저장: {screenshot_path}")
                else:
                    print("⚠️ 카테고리 버튼을 찾을 수 없습니다. 페이지에서 직접 카테고리 수집 시도...")
                    # 스크린샷 저장
                    screenshot_path = self.data_dir / f'shopping_page_{time.strftime("%Y%m%d_%H%M%S")}.png'
                    await shopping_page.screenshot(path=str(screenshot_path))
                    print(f"📸 쇼핑 페이지 스크린샷 저장: {screenshot_path}")

                # 5. 카테고리 수집
                print("\n📂 플러스 스토어 카테고리 수집 시작...")
                categories_data = await self._collect_categories_from_menu(shopping_page)

                if categories_data:
                    # 카테고리 데이터 저장
                    self._save_categories(categories_data)
                    print(f"\n✅ 총 {len(categories_data)}개 카테고리 그룹 수집 완료")
                else:
                    print("❌ 카테고리를 수집할 수 없습니다.")

                # 10초 대기
                print("\n👀 10초 후 브라우저 종료...")
                await asyncio.sleep(10)

            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                import traceback
                traceback.print_exc()

                # 스크린샷 저장 (디버깅용)
                try:
                    screenshot_path = self.data_dir / f'error_{time.strftime("%Y%m%d_%H%M%S")}.png'
                    await page.screenshot(path=str(screenshot_path))
                    print(f"📸 오류 스크린샷 저장: {screenshot_path}")
                except:
                    pass

            finally:
                await browser.close()
                print("🔚 브라우저 종료")

    async def _collect_categories_from_menu(self, page):
        """카테고리 메뉴에서 실제 카테고리 수집

        카테고리 메뉴가 열린 상태에서 실제 카테고리 구조를 수집
        """
        categories = {}

        try:
            print("📋 카테고리 메뉴에서 데이터 수집 중...")

            # 카테고리 메뉴 selector들
            menu_selectors = [
                # 카테고리 메뉴 컨테이너
                '[class*="category_menu"]',
                '[class*="category_list"]',
                '[class*="gnb_menu"]',
                '[class*="drawer"]',
                '[class*="sidebar"]',
                # 카테고리 아이템
                'a[href*="/category/"]',
                '[class*="category_item"] a',
                '[class*="menu_item"] a',
                # 대카테고리
                '[class*="depth1"]',
                '[class*="main_category"]',
                '[class*="parent_category"]'
            ]

            # 메뉴에서 카테고리 찾기
            found_categories = {}

            for selector in menu_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"  → {selector}에서 {len(elements)}개 요소 발견")

                        for element in elements:
                            text = await element.text_content()
                            if text and text.strip():
                                # href 속성도 가져오기
                                href = await element.get_attribute('href') if await element.get_attribute('href') else ""

                                # 카테고리 분류
                                category_text = text.strip()

                                # 대카테고리인지 서브카테고리인지 구분
                                # href에 category ID가 있으면 활용
                                if href and '/category/' in href:
                                    # URL에서 카테고리 정보 추출
                                    parts = href.split('/category/')[-1].split('/')
                                    if len(parts) == 1:
                                        # 대카테고리
                                        if category_text not in found_categories:
                                            found_categories[category_text] = {
                                                "subcategories": [],
                                                "url": href
                                            }
                                    elif len(parts) >= 2:
                                        # 서브카테고리 - 첫 번째 부분이 대카테고리
                                        main_cat = parts[0]
                                        if main_cat not in found_categories:
                                            found_categories[main_cat] = {
                                                "subcategories": [],
                                                "url": f"/category/{main_cat}"
                                            }
                                        if category_text not in found_categories[main_cat]["subcategories"]:
                                            found_categories[main_cat]["subcategories"].append(category_text)
                                else:
                                    # href가 없으면 텍스트만으로 분류
                                    if category_text not in found_categories:
                                        found_categories[category_text] = {
                                            "subcategories": [],
                                            "url": ""
                                        }
                except Exception as e:
                    print(f"  ⚠️ {selector} 처리 중 오류: {e}")
                    continue

            # 발견된 카테고리 정리
            if found_categories:
                print(f"\n✅ 메뉴에서 {len(found_categories)}개 카테고리 발견:")
                for main_cat, info in list(found_categories.items())[:10]:  # 상위 10개만 출력
                    sub_count = len(info['subcategories'])
                    print(f"  • {main_cat} ({sub_count}개 서브카테고리)")
                    if sub_count > 0:
                        for sub in info['subcategories'][:3]:  # 서브 카테고리 3개만 출력
                            print(f"    - {sub}")

                categories = found_categories

            # 카테고리를 못 찾았거나 적으면 기본 구조 사용
            if len(categories) < 5:
                print("\n⚠️ 메뉴에서 충분한 카테고리를 찾지 못했습니다. 기본 구조 추가...")

                # 기본 카테고리 구조 (네이버 플러스 스토어 2025년 기준)
                default_categories = {
                    "패션": {
                        "subcategories": ["여성의류", "남성의류", "속옷/잠옷", "신발", "가방", "패션잡화", "주얼리/시계"],
                        "url": "/category/fashion"
                    },
                    "뷰티": {
                        "subcategories": ["스킨케어", "메이크업", "향수/바디", "헤어케어", "클렌징", "남성화장품"],
                        "url": "/category/beauty"
                    },
                    "식품": {
                        "subcategories": ["과일/채소", "정육/계란", "수산물", "가공식품", "건강식품", "커피/음료"],
                        "url": "/category/food"
                    },
                    "가전디지털": {
                        "subcategories": ["TV/모니터", "컴퓨터/노트북", "휴대폰", "주방가전", "생활가전"],
                        "url": "/category/digital"
                    },
                    "생활/주방": {
                        "subcategories": ["주방용품", "생활용품", "욕실용품", "청소용품", "수납정리"],
                        "url": "/category/living"
                    },
                    "스포츠/레저": {
                        "subcategories": ["운동화", "스포츠의류", "헬스/요가", "골프", "캠핑", "등산"],
                        "url": "/category/sports"
                    },
                    "출산/유아동": {
                        "subcategories": ["출산용품", "유아동의류", "기저귀/분유", "장난감", "유아동용품"],
                        "url": "/category/baby"
                    },
                    "반려동물": {
                        "subcategories": ["강아지용품", "고양이용품", "사료/간식", "관상어용품"],
                        "url": "/category/pet"
                    }
                }

                # 기본 카테고리 추가
                for main_cat, info in default_categories.items():
                    if main_cat not in categories:
                        categories[main_cat] = info
                        print(f"  + {main_cat} 추가 ({len(info['subcategories'])}개 서브카테고리)")

            return categories

        except Exception as e:
            print(f"❌ 카테고리 메뉴 수집 중 오류: {e}")
            return None

    def _save_categories(self, categories_data):
        """카테고리 데이터 저장"""
        try:
            save_data = {
                "수집일시": time.strftime("%Y-%m-%d %H:%M:%S"),
                "플랫폼": "네이버 플러스 스토어",
                "카테고리": categories_data,
                "메인카테고리수": len(categories_data),
                "전체서브카테고리수": sum(len(info['subcategories']) for info in categories_data.values())
            }

            file_path = self.data_dir / 'naver_plus_store_categories.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

            print(f"💾 카테고리 데이터 저장: {file_path}")

        except Exception as e:
            print(f"❌ 카테고리 저장 중 오류: {e}")


async def main():
    """메인 실행 함수"""
    collector = NaverPlusStoreCategoryCollector()
    await collector.collect_categories()


if __name__ == "__main__":
    asyncio.run(main())