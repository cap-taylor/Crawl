"""카테고리 계층 구조 올바르게 재수집

CRAWLING_LESSONS_LEARNED.md 문서 기반으로 정확하게 재수집:
- 대분류: data-leaf="false"
- 중분류: data-leaf 혼재
- 소분류: data-leaf="true" (최종 카테고리)

호버 방식으로 서브카테고리 표시하여 수집
"""
import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
import time

async def recollect_categories():
    """CRAWLING_LESSONS_LEARNED.md 기반 올바른 카테고리 수집"""
    print("=" * 60)
    print("네이버 플러스 스토어 카테고리 재수집 (올바른 방법)")
    print("CRAWLING_LESSONS_LEARNED.md 문서 기반")
    print("=" * 60)

    async with async_playwright() as p:
        # Firefox 사용 (문서에서 성공 확인)
        print("\n🦊 Firefox 브라우저 실행...")
        browser = await p.firefox.launch(
            headless=False,  # 반드시 False
            slow_mo=500      # 천천히 (봇 감지 회피)
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )

        page = await context.new_page()

        try:
            # 1. 네이버 메인 접속
            print("\n📍 네이버 메인 접속 (캡차 없음)...")
            await page.goto("https://www.naver.com", wait_until="networkidle")
            print("✅ 네이버 메인 접속 성공")
            await asyncio.sleep(3)

            # 2. 쇼핑 클릭 (새 탭)
            print("\n🔍 쇼핑 버튼 찾는 중...")
            shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
            shopping_link = await page.wait_for_selector(shopping_selector, timeout=10000)

            if shopping_link:
                print("🛍️ 쇼핑 클릭 (새 탭에서 열림)...")
                # 새 탭 이벤트 감지
                async with context.expect_page() as new_page_info:
                    await shopping_link.click()

                shopping_page = await new_page_info.value
                await shopping_page.wait_for_load_state("networkidle")
                print(f"✅ 쇼핑 페이지 접속 성공: {shopping_page.url}")
                await asyncio.sleep(3)

                # 3. 카테고리 버튼 클릭
                print("\n📂 카테고리 버튼 클릭...")
                # 여러 방법 시도
                category_button = None

                # 방법 1: 정확한 셀렉터 (CRAWLING_LESSONS_LEARNED.md)
                try:
                    category_button = await shopping_page.wait_for_selector(
                        '#gnb-gnb > div._gnb_header_area_nfFfz > div > div._gnbContent_gnb_content_JUwjU > div._gnbContent_button_area_FRBmE > div:nth-child(1) > button',
                        timeout=5000
                    )
                    print("  ✓ 정확한 셀렉터로 찾음")
                except:
                    pass

                # 방법 2: 텍스트로 찾기
                if not category_button:
                    try:
                        category_button = await shopping_page.wait_for_selector('button:has-text("카테고리")', timeout=5000)
                        print("  ✓ 텍스트로 찾음")
                    except:
                        pass

                # 방법 3: aria-label로 찾기
                if not category_button:
                    try:
                        category_button = await shopping_page.wait_for_selector('button[aria-label*="카테고리"]', timeout=5000)
                        print("  ✓ aria-label로 찾음")
                    except:
                        pass

                if category_button:
                    await category_button.click()
                    await asyncio.sleep(3)  # 메뉴 열리기 충분히 대기
                    print("✅ 카테고리 메뉴 열림")

                    # 스크린샷 저장 (디버깅용)
                    project_root = Path(__file__).parent.parent.parent
                    data_dir = project_root / 'data'
                    data_dir.mkdir(exist_ok=True)
                    screenshot_path = data_dir / 'category_menu_open.png'
                    await shopping_page.screenshot(path=str(screenshot_path))
                    print(f"  📸 스크린샷 저장: {screenshot_path}")
                else:
                    raise Exception("카테고리 버튼을 찾을 수 없습니다")

                # 4. 대분류 카테고리 수집
                print("\n🔍 대분류 카테고리 수집 중...")

                # 여러 셀렉터 시도
                main_category_links = []

                # 방법 1: 클래스 기반
                main_category_links = await shopping_page.query_selector_all('._categoryLayer_link_8hzu')
                print(f"  방법1 (클래스): {len(main_category_links)}개")

                # 방법 2: data-id 속성 기반
                if not main_category_links:
                    main_category_links = await shopping_page.query_selector_all('a[data-id]')
                    print(f"  방법2 (data-id): {len(main_category_links)}개")

                # 방법 3: 카테고리 레이어 내부 링크
                if not main_category_links:
                    main_category_links = await shopping_page.query_selector_all('.categoryLayer a')
                    print(f"  방법3 (categoryLayer a): {len(main_category_links)}개")

                categories_data = {
                    "수집일시": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "플랫폼": "네이버 플러스 스토어",
                    "계층구조": "대분류 > 중분류 > 소분류 (3단계)",
                    "카테고리": {}
                }

                main_count = 0
                sub_count = 0

                for idx, main_link in enumerate(main_category_links):
                    try:
                        # 대분류 정보 추출
                        main_name = await main_link.text_content()
                        main_name = main_name.strip() if main_name else ""

                        if not main_name:
                            continue

                        main_id = await main_link.get_attribute('data-id')
                        main_leaf = await main_link.get_attribute('data-leaf')
                        main_url = await main_link.get_attribute('href')

                        print(f"\n  [{idx+1}] {main_name} (ID: {main_id}, leaf: {main_leaf})")

                        categories_data["카테고리"][main_name] = {
                            "id": main_id,
                            "url": main_url if main_url else f"https://search.shopping.naver.com/ns/category/{main_id}",
                            "data_leaf": main_leaf,
                            "level": 0,
                            "sub_categories": []
                        }
                        main_count += 1

                        # 하위 카테고리가 있으면 호버하여 수집
                        if main_leaf == "false":
                            print(f"    🔍 {main_name} 하위 카테고리 확인 중...")
                            await main_link.hover()
                            await asyncio.sleep(1.5)  # 서브메뉴 로딩 대기

                            # 서브카테고리 수집 (오른쪽 패널)
                            sub_category_elements = await shopping_page.query_selector_all('span._categoryLayer_text_XOd4h')

                            collected_subs = set()  # 중복 방지
                            for sub_elem in sub_category_elements:
                                sub_name = await sub_elem.text_content()
                                sub_name = sub_name.strip() if sub_name else ""

                                # 필터링: "더보기", 빈 문자열, 대분류와 같은 이름 제외
                                if sub_name and sub_name != main_name and "더보기" not in sub_name:
                                    # 대분류 목록과 중복되는지 확인
                                    if sub_name not in categories_data["카테고리"]:
                                        if sub_name not in collected_subs:
                                            # 상위 링크 찾기
                                            parent_link = await sub_elem.evaluate_handle("el => el.closest('a')")
                                            if parent_link:
                                                sub_id = await parent_link.as_element().get_attribute('data-id')
                                                sub_leaf = await parent_link.as_element().get_attribute('data-leaf')
                                                sub_url = await parent_link.as_element().get_attribute('href')

                                                categories_data["카테고리"][main_name]["sub_categories"].append({
                                                    "name": sub_name,
                                                    "id": sub_id,
                                                    "url": sub_url,
                                                    "data_leaf": sub_leaf,
                                                    "level": 1
                                                })
                                                collected_subs.add(sub_name)
                                                sub_count += 1

                            print(f"    ✅ {len(collected_subs)}개 하위 카테고리 수집")

                        # 과도한 요청 방지
                        await asyncio.sleep(0.5)

                    except Exception as e:
                        print(f"    ❌ {main_name} 수집 중 오류: {e}")
                        continue

                # 5. 데이터 저장
                categories_data["대분류수"] = main_count
                categories_data["전체서브카테고리수"] = sub_count

                project_root = Path(__file__).parent.parent.parent
                data_dir = project_root / 'data'
                data_dir.mkdir(exist_ok=True)

                save_path = data_dir / 'naver_categories_hierarchy.json'
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(categories_data, f, ensure_ascii=False, indent=2)

                print(f"\n{'=' * 60}")
                print(f"✅ 카테고리 수집 완료!")
                print(f"  • 대분류: {main_count}개")
                print(f"  • 전체 서브카테고리: {sub_count}개")
                print(f"  • 저장 위치: {save_path}")
                print(f"{'=' * 60}")

            else:
                print("❌ 쇼핑 버튼을 찾을 수 없음")

            # 10초 대기
            print("\n👀 10초 후 브라우저 종료...")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"❌ 오류: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()
            print("🔚 브라우저 종료")

if __name__ == "__main__":
    asyncio.run(recollect_categories())
