#!/usr/bin/env python3
"""
서브카테고리 호버 문제 디버깅 스크립트
카테고리 메뉴의 정확한 구조를 파악하기 위한 스크립트
"""
import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
from datetime import datetime

async def debug_category_hover():
    """카테고리 호버 동작 디버깅"""
    print("=" * 60)
    print("카테고리 호버 디버깅")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=1000  # 더 천천히 동작하여 관찰
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
        )

        page = await context.new_page()

        try:
            # 1. 네이버 메인 접속
            print("\n1️⃣ 네이버 메인 접속...")
            await page.goto("https://www.naver.com")
            await asyncio.sleep(2)

            # 2. 쇼핑 클릭 (새 탭으로 열림)
            print("2️⃣ 쇼핑 페이지로 이동...")
            shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
            shopping_link = await page.wait_for_selector(shopping_selector, timeout=10000)
            await shopping_link.click()
            await asyncio.sleep(3)

            # 3. 새 탭으로 전환 (CategoryCollector와 동일한 방식)
            all_pages = context.pages
            if len(all_pages) > 1:
                page = all_pages[-1]  # 쇼핑 탭
                await page.wait_for_load_state('networkidle')
                print("✅ 쇼핑 페이지 로드 완료")

            # 4. 카테고리 메뉴 열기
            print("\n3️⃣ 카테고리 메뉴 열기...")
            category_btn = await page.wait_for_selector('button:has-text("카테고리")', timeout=5000)
            await category_btn.click()
            await asyncio.sleep(2)

            # 5. 메인 카테고리 요소들 찾기
            print("\n4️⃣ 카테고리 구조 분석...")

            # 여러 셀렉터로 시도
            selectors = {
                'data-id 속성': 'a[data-id]',
                'data-leaf false': 'a[data-leaf="false"]',
                '카테고리 링크 클래스': 'a._categoryLayer_link_Bhzgu',
                '카테고리 레이어 내 링크': '._categoryLayer_category_layer_1JUQ0 a',
                '왼쪽 패널 링크': '._categoryLayer_list_3Qw7B a'
            }

            for name, selector in selectors.items():
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"\n✓ {name}: {len(elements)}개 발견")

                    if elements and len(elements) > 0:
                        # 첫 번째 요소의 정보 출력
                        first_elem = elements[0]
                        text = await first_elem.text_content()
                        data_id = await first_elem.get_attribute('data-id')
                        data_leaf = await first_elem.get_attribute('data-leaf')
                        print(f"  첫 번째: {text} (ID: {data_id}, leaf: {data_leaf})")
                except Exception as e:
                    print(f"✗ {name}: 오류 - {e}")

            # 6. 호버 테스트
            print("\n5️⃣ 호버 테스트...")

            # 패션잡화 찾아서 호버
            test_categories = ['패션잡화', '여성의류', '남성의류']

            for cat_name in test_categories:
                print(f"\n📂 '{cat_name}' 테스트:")

                # 카테고리 찾기
                cat_element = None
                try:
                    # 텍스트로 찾기
                    cat_element = await page.query_selector(f'a:has-text("{cat_name}")')

                    if not cat_element:
                        # data-name으로 찾기
                        cat_element = await page.query_selector(f'a[data-name="{cat_name}"]')

                    if cat_element:
                        print(f"  ✓ {cat_name} 요소 발견")

                        # 호버 전 스크린샷
                        await page.screenshot(path=f"data/before_hover_{cat_name}.png")

                        # 호버
                        await cat_element.hover()
                        print(f"  🖱️ 호버 실행")
                        await asyncio.sleep(2)  # 서브메뉴 로딩 대기

                        # 호버 후 스크린샷
                        await page.screenshot(path=f"data/after_hover_{cat_name}.png")

                        # 서브카테고리 패널 찾기
                        print(f"  📋 서브카테고리 찾기:")

                        # 여러 방법으로 서브카테고리 찾기
                        sub_selectors = {
                            '서브 패널': '._categoryLayer_sub_panel_V3Sdo',
                            '서브 카테고리 텍스트': '._categoryLayer_text_XOd4h',
                            '서브 리스트': '._categoryLayer_sub_list_37MFS',
                            '호버된 카테고리의 서브': '[aria-expanded="true"] + div',
                            '표시된 서브메뉴': '.서브메뉴:visible'
                        }

                        for sub_name, sub_selector in sub_selectors.items():
                            try:
                                sub_elements = await page.query_selector_all(sub_selector)
                                if sub_elements:
                                    print(f"    ✓ {sub_name}: {len(sub_elements)}개")

                                    # 처음 3개만 텍스트 출력
                                    for i, elem in enumerate(sub_elements[:3]):
                                        try:
                                            text = await elem.text_content()
                                            if text and text.strip():
                                                print(f"      - {text.strip()}")
                                        except:
                                            pass
                            except Exception as e:
                                print(f"    ✗ {sub_name}: 오류")

                        # 현재 보이는 모든 링크 확인
                        print(f"\n  📊 현재 보이는 모든 카테고리 링크:")
                        visible_links = await page.query_selector_all('a[data-id]:visible')
                        print(f"    총 {len(visible_links)}개의 링크가 보임")

                        # aria-expanded 상태 확인
                        expanded = await cat_element.get_attribute('aria-expanded')
                        print(f"    aria-expanded: {expanded}")

                    else:
                        print(f"  ✗ {cat_name} 요소를 찾을 수 없음")

                except Exception as e:
                    print(f"  ❌ 오류: {e}")

                await asyncio.sleep(1)

            # 7. DOM 구조 저장
            print("\n6️⃣ DOM 구조 저장...")

            # 카테고리 레이어의 HTML 저장
            try:
                category_layer = await page.query_selector('._categoryLayer_category_layer_1JUQ0')
                if category_layer:
                    html_content = await category_layer.inner_html()

                    # HTML 파일로 저장
                    with open('data/category_layer.html', 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    print("  ✓ category_layer.html 저장 완료")

                    # 구조 분석
                    print("\n  📊 카테고리 레이어 구조:")
                    print(f"    HTML 길이: {len(html_content)} 문자")

                    # 클래스 이름 수집
                    import re
                    classes = set(re.findall(r'class="([^"]+)"', html_content))
                    print(f"    발견된 클래스: {len(classes)}개")
                    for cls in list(classes)[:10]:
                        print(f"      - {cls}")

            except Exception as e:
                print(f"  ❌ DOM 저장 실패: {e}")

            print("\n" + "=" * 60)
            print("디버깅 완료! 스크린샷과 HTML 파일을 확인하세요.")
            print("=" * 60)

            # 10초 대기
            await asyncio.sleep(10)

        except Exception as e:
            print(f"\n❌ 전체 오류: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_category_hover())