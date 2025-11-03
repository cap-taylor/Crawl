#!/usr/bin/env python3
"""
스크롤 후 상품 수집 테스트

테스트 시나리오:
1. 카테고리 진입 후 총 상품 개수 확인
2. 첫 번째 페이지의 마지막 상품 수집
3. 전체 상품이 노출될 때까지 스크롤
4. 스크롤 후 마지막 상품 수집
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright
import re


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

    # 15초 대기 (고정)
    for i in range(15, 0, -5):
        print(f"[대기] 남은 시간: {i}초...")
        await asyncio.sleep(5)

    print("✅ 대기 완료! 크롤링을 계속합니다...")
    await asyncio.sleep(2)


async def test_scroll_and_collect():
    print("=" * 70)
    print("스크롤 후 상품 수집 테스트")
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
                # 캡차 해결 후 페이지 재로드 확인
                await page.wait_for_load_state('networkidle')

            # 3. 총 상품 개수 확인
            print("\n[4단계] 총 상품 개수 확인...")

            # 페이지 전체 상품 개수 텍스트 찾기 (예: "12,345개")
            total_text = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    // "12,345개", "총 12,345개", "상품 12,345개" 등 다양한 형식 찾기
                    const match = text.match(/([\\d,]+)개/);
                    if (match && text.length < 50) {
                        const num = parseInt(match[1].replace(/,/g, ''));
                        // 100개 이상인 경우만 총 상품 개수로 판단
                        if (num >= 100) {
                            return match[1] + '개';
                        }
                    }
                }
                return null;
            }''')

            if total_text:
                total_count = int(total_text.replace(',', '').replace('개', ''))
                print(f"✅ 총 상품 개수: {total_count:,}개")
            else:
                print("⚠️ 총 상품 개수를 찾을 수 없습니다.")
                total_count = None

            # 4. 현재 로드된 상품 개수
            product_links = await page.query_selector_all('a[class*="ProductCard_link"]')
            initial_count = len(product_links)
            print(f"현재 로드된 상품: {initial_count}개")

            # 5. 첫 번째 페이지의 마지막 상품 수집
            print(f"\n[5단계] 첫 번째 페이지 마지막 상품(#{initial_count}) 수집...")

            if initial_count > 0:
                last_product = product_links[-1]

                # 상품 클릭
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
                        product_name = await elem.inner_text()
                        print(f"✅ 상품명: {product_name[:50]}...")
                    else:
                        print("❌ 상품명을 찾을 수 없습니다.")

                    # 탭 닫기
                    await detail_page.close()
                    await asyncio.sleep(1)

            # 6. 총 상품 개수만큼 스크롤하여 모두 로드
            print(f"\n[6단계] 총 상품 개수({total_count}개)만큼 스크롤...")

            # 변수 초기화 (스크롤 여부와 관계없이)
            scroll_count = 0

            if not total_count:
                print("⚠️ 총 상품 개수를 알 수 없어 스크롤을 건너뜁니다.")
            else:
                max_scrolls = 50  # 최대 스크롤 횟수

                while scroll_count < max_scrolls:
                    # 스크롤 전 상품 개수
                    before_scroll = len(await page.query_selector_all('a[class*="ProductCard_link"]'))

                    # 페이지 끝까지 스크롤
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(2)

                    # 스크롤 후 상품 개수
                    after_scroll = len(await page.query_selector_all('a[class*="ProductCard_link"]'))

                    scroll_count += 1
                    print(f"  스크롤 #{scroll_count}: {before_scroll}개 → {after_scroll}개 (목표: {total_count}개)")

                    # 목표 개수에 도달하거나 초과하면 중단
                    if after_scroll >= total_count:
                        print(f"✅ 목표 개수 도달! {after_scroll:,}개 로드 완료")
                        break

                    # 더 이상 상품이 로드되지 않으면 중단
                    if after_scroll == before_scroll:
                        print(f"⚠️ 더 이상 로드되지 않음. (총 {after_scroll}개/{total_count}개)")
                        break

            # 7. 스크롤 후 마지막 상품 수집
            print(f"\n[7단계] 스크롤 후 마지막 상품 수집...")

            final_products = await page.query_selector_all('a[class*="ProductCard_link"]')
            final_count = len(final_products)

            if final_count > 0:
                last_product = final_products[-1]

                # 마지막 상품이 보이도록 스크롤
                await last_product.scroll_into_view_if_needed()
                await asyncio.sleep(1)

                # 상품 클릭
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
                        product_name = await elem.inner_text()
                        print(f"✅ 마지막 상품(#{final_count}): {product_name[:50]}...")
                    else:
                        print("❌ 상품명을 찾을 수 없습니다.")

                    # 탭 닫기
                    await detail_page.close()

            # 8. 결과 요약
            print("\n" + "=" * 70)
            print("테스트 결과 요약")
            print("=" * 70)
            if total_count:
                print(f"총 상품 개수: {total_count:,}개")
            print(f"초기 로드: {initial_count}개")
            print(f"스크롤 횟수: {scroll_count}회")
            print(f"최종 로드: {final_count}개")

            if total_count and final_count >= total_count:
                print("✅ 모든 상품 로드 완료!")
            else:
                print(f"⚠️ 일부 상품만 로드됨")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_scroll_and_collect())
