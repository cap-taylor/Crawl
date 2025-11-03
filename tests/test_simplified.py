#!/usr/bin/env python3
"""
단순화된 무한 스크롤 테스트

테스트 시나리오:
1. 카테고리 진입 후 현재 로드된 상품 개수 확인 (예: 63개)
2. 마지막 상품 수집
3. 스크롤 1회 (새 상품 로드됨)
4. 다시 마지막 상품 수집 (이전과 다른 상품이면 무한 수집 가능)
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright


async def wait_for_manual_captcha():
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

    for i in range(15, 0, -5):
        print(f"[대기] 남은 시간: {i}초...")
        await asyncio.sleep(5)

    print("✅ 대기 완료! 크롤링을 계속합니다...")
    await asyncio.sleep(2)


async def test_infinite_scroll():
    print("=" * 70)
    print("무한 스크롤 테스트 (단순화)")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=300
        )

        context = await browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )

        page = await context.new_page()

        try:
            # 1. 네이버 메인 → 쇼핑 진입
            print("\n[1단계] 네이버 메인 페이지 접속...")
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(2)

            print("[2단계] 쇼핑 버튼 클릭...")
            shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
            await page.locator(shopping_selector).click(timeout=10000)
            await asyncio.sleep(2)

            # 새 탭 전환
            all_pages = context.pages
            if len(all_pages) > 1:
                page = all_pages[-1]
                await page.wait_for_load_state('networkidle')

            # 2. 카테고리 진입
            print("[3단계] 여성의류 카테고리 진입...")
            category_btn = await page.wait_for_selector('button:has-text("카테고리")')
            await category_btn.click()
            await asyncio.sleep(1)

            womens = await page.wait_for_selector('a[data-name="여성의류"]')
            await womens.click()
            await asyncio.sleep(3)

            # 캡차 감지 및 대기
            page_content = await page.content()
            if 'captcha' in page_content.lower() or 'recaptcha' in page_content.lower():
                await wait_for_manual_captcha()
                await page.wait_for_load_state('networkidle')

            # 3. 현재 로드된 상품 개수 확인
            print("\n[4단계] 현재 로드된 상품 개수 확인...")
            product_links = await page.query_selector_all('a[class*="ProductCard_link"]')
            initial_count = len(product_links)
            print(f"✅ 현재 로드된 상품: {initial_count}개")

            # 4. 첫 번째 마지막 상품 수집
            print(f"\n[5단계] 마지막 상품(#{initial_count}) 수집...")
            if initial_count > 0:
                last_product = product_links[-1]
                await last_product.click()
                await asyncio.sleep(2)

                # 새 탭 찾기
                all_pages = context.pages
                if len(all_pages) > 1:
                    detail_page = all_pages[-1]
                    await detail_page.wait_for_load_state('domcontentloaded')
                    await asyncio.sleep(1)

                    # 상품명 추출
                    elem = await detail_page.query_selector('h3.DCVBehA8ZB')
                    if elem:
                        product_name_1 = await elem.inner_text()
                        print(f"✅ 상품명: {product_name_1[:50]}...")
                    else:
                        print("❌ 상품명을 찾을 수 없습니다.")
                        product_name_1 = None

                    # 탭 닫고 원래 페이지로
                    await detail_page.close()
                    await asyncio.sleep(1)

            # 5. 스크롤 1회 (새 상품 로드)
            print(f"\n[6단계] 페이지 끝까지 스크롤...")
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(3)  # 로딩 대기

            # 6. 스크롤 후 상품 개수 확인
            product_links_after = await page.query_selector_all('a[class*="ProductCard_link"]')
            after_count = len(product_links_after)
            print(f"✅ 스크롤 후 상품 개수: {after_count}개 (증가: {after_count - initial_count}개)")

            # 7. 스크롤 후 마지막 상품 수집
            print(f"\n[7단계] 스크롤 후 마지막 상품(#{after_count}) 수집...")
            if after_count > 0:
                last_product_after = product_links_after[-1]

                # 마지막 상품이 보이도록 스크롤
                await last_product_after.scroll_into_view_if_needed()
                await asyncio.sleep(1)

                await last_product_after.click()
                await asyncio.sleep(2)

                # 새 탭 찾기
                all_pages = context.pages
                if len(all_pages) > 1:
                    detail_page = all_pages[-1]
                    await detail_page.wait_for_load_state('domcontentloaded')
                    await asyncio.sleep(1)

                    # 상품명 추출
                    elem = await detail_page.query_selector('h3.DCVBehA8ZB')
                    if elem:
                        product_name_2 = await elem.inner_text()
                        print(f"✅ 상품명: {product_name_2[:50]}...")
                    else:
                        print("❌ 상품명을 찾을 수 없습니다.")
                        product_name_2 = None

                    # 탭 닫기
                    await detail_page.close()

            # 8. 결과 요약
            print("\n" + "=" * 70)
            print("테스트 결과 요약")
            print("=" * 70)
            print(f"초기 상품 개수: {initial_count}개")
            print(f"스크롤 후 개수: {after_count}개")
            print(f"증가량: {after_count - initial_count}개")

            if product_name_1 and product_name_2:
                if product_name_1 != product_name_2:
                    print("\n✅ 무한 스크롤 테스트 성공!")
                    print("   - 스크롤 전후 마지막 상품이 다름")
                    print("   - 계속 새로운 상품이 로드됨 (무한 수집 가능)")
                else:
                    print("\n⚠️ 동일한 상품 감지")
                    print("   - 더 이상 새 상품이 로드되지 않음")
            else:
                print("\n❌ 상품명 수집 실패")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_infinite_scroll())
