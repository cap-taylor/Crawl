#!/usr/bin/env python3
"""
네이버 쇼핑 카테고리 최종 수집 스크립트
올바른 계층 구조로 수집 (대분류 > 중분류 > 소분류)
"""
import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
import time
from datetime import datetime

async def collect_categories_correctly():
    """카테고리를 올바른 계층 구조로 수집"""
    print("=" * 60)
    print("네이버 쇼핑 카테고리 정확한 수집")
    print("목표: 올바른 계층 구조 (대분류>중분류>소분류)")
    print("=" * 60)

    async with async_playwright() as p:
        print("\n🔧 브라우저 시작 (Firefox)...")
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=500  # 천천히 동작
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
        )

        page = await context.new_page()

        try:
            # 1. 네이버 메인 접속
            print("\n1️⃣ 네이버 메인 접속...")
            await page.goto("https://www.naver.com", wait_until="networkidle")
            await asyncio.sleep(2)

            # 2. 쇼핑 클릭
            print("2️⃣ 쇼핑 탭 클릭...")
            shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a', timeout=10000)

            # 새 탭 열기 감지
            async with context.expect_page() as new_page_info:
                await shopping_link.click()

            shopping_page = await new_page_info.value
            await shopping_page.wait_for_load_state("networkidle")
            print(f"   ✅ 쇼핑 페이지 열림: {shopping_page.url}")
            await asyncio.sleep(3)

            # 3. 카테고리 버튼 찾기
            print("\n3️⃣ 카테고리 메뉴 열기...")

            # 카테고리 버튼 찾기 (여러 방법)
            category_btn = None

            # 텍스트로 찾기
            try:
                category_btn = await shopping_page.wait_for_selector('button:has-text("카테고리")', timeout=5000)
                print("   ✓ 카테고리 버튼 찾음 (텍스트)")
            except:
                pass

            # 정확한 셀렉터로 찾기
            if not category_btn:
                try:
                    category_btn = await shopping_page.query_selector('button._gnbCategory_button_h6LW7')
                    if category_btn:
                        print("   ✓ 카테고리 버튼 찾음 (클래스)")
                except:
                    pass

            if not category_btn:
                print("   ❌ 카테고리 버튼 못 찾음. 스크린샷 저장...")
                await shopping_page.screenshot(path="data/debug_no_category_btn.png")
                raise Exception("카테고리 버튼을 찾을 수 없음")

            # 카테고리 메뉴 열기
            await category_btn.click()
            await asyncio.sleep(3)
            print("   ✅ 카테고리 메뉴 열림")

            # 4. 대분류 카테고리 수집 (메뉴가 열린 상태에서)
            print("\n4️⃣ 카테고리 데이터 수집 시작...")

            # 카테고리 구조 초기화
            categories = {}

            # 대분류 링크들 찾기 (왼쪽 패널의 메인 카테고리)
            main_links = await shopping_page.query_selector_all('a[data-id]')
            print(f"   발견된 링크 수: {len(main_links)}개")

            # 대분류만 필터링 (10000으로 시작하는 ID)
            main_categories = []

            for link in main_links:
                try:
                    cat_id = await link.get_attribute('data-id')
                    cat_text = await link.text_content()
                    cat_leaf = await link.get_attribute('data-leaf')

                    if cat_id and cat_text:
                        cat_text = cat_text.strip()

                        # 대분류 판단: ID가 10000으로 시작하고 7-8자리
                        if cat_id.startswith('10000') and len(cat_id) <= 8:
                            # 왼쪽 메뉴에 있는 대분류인지 확인
                            parent_elem = await link.evaluate_handle('el => el.parentElement.parentElement')
                            parent_class = await parent_elem.as_element().get_attribute('class')

                            # 메인 카테고리 리스트에 있는지 확인
                            if '_categoryLayer_list_' in str(parent_class):
                                main_categories.append({
                                    'name': cat_text,
                                    'id': cat_id,
                                    'leaf': cat_leaf,
                                    'element': link
                                })
                                print(f"   ✓ 대분류: {cat_text} (ID: {cat_id})")
                except Exception as e:
                    continue

            print(f"\n   대분류 총 {len(main_categories)}개 발견")

            # 5. 각 대분류의 중분류 수집
            for main_cat in main_categories[:5]:  # 테스트로 5개만
                try:
                    print(f"\n   📂 {main_cat['name']} 처리 중...")

                    # 대분류 데이터 저장
                    categories[main_cat['name']] = {
                        'id': main_cat['id'],
                        'level': '대분류',
                        'sub_categories': {}
                    }

                    # leaf가 false면 하위 카테고리가 있음
                    if main_cat['leaf'] == 'false':
                        # 호버하여 서브메뉴 표시
                        await main_cat['element'].hover()
                        await asyncio.sleep(1.5)

                        # 오른쪽 패널의 중분류 수집
                        # 현재 표시된 서브카테고리 찾기
                        sub_links = await shopping_page.query_selector_all('._categoryLayer_sub_panel_V3Sdo a[data-id]')

                        for sub_link in sub_links:
                            try:
                                sub_id = await sub_link.get_attribute('data-id')
                                sub_text = await sub_link.text_content()
                                sub_leaf = await sub_link.get_attribute('data-leaf')

                                if sub_id and sub_text:
                                    sub_text = sub_text.strip()

                                    # 대분류와 중복 제거
                                    is_main = False
                                    for mc in main_categories:
                                        if mc['name'] == sub_text:
                                            is_main = True
                                            break

                                    if not is_main and sub_text != main_cat['name']:
                                        categories[main_cat['name']]['sub_categories'][sub_text] = {
                                            'id': sub_id,
                                            'level': '중분류',
                                            'leaf': sub_leaf
                                        }
                                        print(f"      └─ {sub_text}")
                            except:
                                continue

                    await asyncio.sleep(0.5)  # 과도한 요청 방지

                except Exception as e:
                    print(f"   ❌ {main_cat['name']} 처리 중 오류: {e}")
                    continue

            # 6. 데이터 저장
            result = {
                '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '플랫폼': '네이버 쇼핑',
                '카테고리_수': len(categories),
                '카테고리': categories
            }

            # 저장
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / 'data'
            data_dir.mkdir(exist_ok=True)

            output_file = data_dir / f'categories_correct_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"\n{'=' * 60}")
            print(f"✅ 수집 완료!")
            print(f"   • 대분류: {len(categories)}개")
            print(f"   • 파일: {output_file}")
            print(f"{'=' * 60}")

            # 10초 대기
            print("\n⏳ 10초 후 종료...")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()
            print("\n🔚 브라우저 종료")

if __name__ == "__main__":
    asyncio.run(collect_categories_correctly())