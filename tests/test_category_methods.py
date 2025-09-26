"""
네이버 쇼핑 카테고리 진입 방법 테스트
6가지 방법으로 캡차 회피 시도
"""

import asyncio
from playwright.async_api import async_playwright
import time
import random

async def test_method_1_longer_wait():
    """방법 1: 더 긴 대기 시간"""
    print("\n[방법 1] 더 긴 대기 시간 테스트")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False, slow_mo=500, args=['--kiosk'])
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # 네이버 메인 → 쇼핑
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a')
            await shopping_link.click()
            await asyncio.sleep(3)

            # 새 탭 전환
            if len(context.pages) > 1:
                page = context.pages[-1]
                await page.wait_for_load_state('networkidle')

            # 긴 대기 시간
            print("  10초 대기 중...")
            await asyncio.sleep(10)

            # 카테고리 메뉴 열기
            category_btn = await page.wait_for_selector('text=카테고리', timeout=5000)
            if category_btn:
                await category_btn.click()
                await asyncio.sleep(5)  # 긴 대기

                # 남성의류 클릭
                mens_clothing = await page.wait_for_selector('text=남성의류', timeout=5000)
                if mens_clothing:
                    await mens_clothing.click()
                    await asyncio.sleep(5)

                    current_url = page.url
                    if "captcha" in current_url or await page.query_selector('text=security verification'):
                        print("  ❌ 캡차 발생!")
                        return False
                    else:
                        print("  ✅ 성공!")
                        return True
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return False
        finally:
            await asyncio.sleep(5)
            await browser.close()

async def test_method_2_hover():
    """방법 2: 마우스 호버 후 클릭"""
    print("\n[방법 2] 마우스 호버 후 클릭 테스트")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False, slow_mo=500, args=['--kiosk'])
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # 네이버 메인 → 쇼핑
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a')
            await shopping_link.click()
            await asyncio.sleep(3)

            # 새 탭 전환
            if len(context.pages) > 1:
                page = context.pages[-1]
                await page.wait_for_load_state('networkidle')

            await asyncio.sleep(3)

            # 카테고리 메뉴 호버 후 클릭
            category_btn = await page.wait_for_selector('text=카테고리', timeout=5000)
            if category_btn:
                await category_btn.hover()  # 호버
                await asyncio.sleep(2)
                await category_btn.click()
                await asyncio.sleep(3)

                # 남성의류 호버 후 클릭
                mens_clothing = await page.wait_for_selector('text=남성의류', timeout=5000)
                if mens_clothing:
                    await mens_clothing.hover()  # 호버
                    await asyncio.sleep(2)
                    await mens_clothing.click()
                    await asyncio.sleep(5)

                    current_url = page.url
                    if "captcha" in current_url or await page.query_selector('text=security verification'):
                        print("  ❌ 캡차 발생!")
                        return False
                    else:
                        print("  ✅ 성공!")
                        return True
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return False
        finally:
            await asyncio.sleep(5)
            await browser.close()

async def test_method_3_scroll():
    """방법 3: 스크롤 동작 추가"""
    print("\n[방법 3] 스크롤 동작 추가 테스트")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False, slow_mo=500, args=['--kiosk'])
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # 네이버 메인 → 쇼핑
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a')
            await shopping_link.click()
            await asyncio.sleep(3)

            # 새 탭 전환
            if len(context.pages) > 1:
                page = context.pages[-1]
                await page.wait_for_load_state('networkidle')

            # 스크롤 동작
            print("  스크롤 중...")
            await page.evaluate("window.scrollTo(0, 300)")
            await asyncio.sleep(2)
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(2)

            # 카테고리 메뉴 열기
            category_btn = await page.wait_for_selector('text=카테고리', timeout=5000)
            if category_btn:
                await category_btn.click()
                await asyncio.sleep(3)

                # 카테고리 내에서 스크롤
                await page.evaluate("window.scrollBy(0, 200)")
                await asyncio.sleep(2)

                # 남성의류 클릭
                mens_clothing = await page.wait_for_selector('text=남성의류', timeout=5000)
                if mens_clothing:
                    await mens_clothing.click()
                    await asyncio.sleep(5)

                    current_url = page.url
                    if "captcha" in current_url or await page.query_selector('text=security verification'):
                        print("  ❌ 캡차 발생!")
                        return False
                    else:
                        print("  ✅ 성공!")
                        return True
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return False
        finally:
            await asyncio.sleep(5)
            await browser.close()

async def test_method_4_search():
    """방법 4: 검색으로 남성의류 접근"""
    print("\n[방법 4] 검색으로 접근 테스트")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False, slow_mo=500, args=['--kiosk'])
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # 네이버 메인 → 쇼핑
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a')
            await shopping_link.click()
            await asyncio.sleep(3)

            # 새 탭 전환
            if len(context.pages) > 1:
                page = context.pages[-1]
                await page.wait_for_load_state('networkidle')

            await asyncio.sleep(3)

            # 검색창에 "남성의류" 입력
            print("  검색창에 '남성의류' 입력...")
            search_box = await page.wait_for_selector('input[type="search"], input[placeholder*="검색"]', timeout=5000)
            if search_box:
                await search_box.click()
                await asyncio.sleep(1)
                await search_box.type("남성의류", delay=100)
                await asyncio.sleep(1)
                await page.keyboard.press('Enter')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(5)

                current_url = page.url
                if "captcha" in current_url or await page.query_selector('text=security verification'):
                    print("  ❌ 캡차 발생!")
                    return False
                else:
                    print("  ✅ 성공! 검색 결과 표시")
                    return True
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return False
        finally:
            await asyncio.sleep(5)
            await browser.close()

async def test_method_5_right_click():
    """방법 5: 우클릭 → 새 탭에서 열기"""
    print("\n[방법 5] 우클릭 → 새 탭에서 열기 테스트")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False, slow_mo=500, args=['--kiosk'])
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # 네이버 메인 → 쇼핑
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a')
            await shopping_link.click()
            await asyncio.sleep(3)

            # 새 탭 전환
            if len(context.pages) > 1:
                page = context.pages[-1]
                await page.wait_for_load_state('networkidle')

            await asyncio.sleep(3)

            # 카테고리 메뉴 열기
            category_btn = await page.wait_for_selector('text=카테고리', timeout=5000)
            if category_btn:
                await category_btn.click()
                await asyncio.sleep(3)

                # 남성의류 우클릭
                mens_clothing = await page.wait_for_selector('text=남성의류', timeout=5000)
                if mens_clothing:
                    print("  남성의류 우클릭...")
                    await mens_clothing.click(button='right')  # 우클릭
                    await asyncio.sleep(2)

                    # "새 탭에서 링크 열기" 클릭
                    new_tab_option = await page.wait_for_selector('text=새 탭에서 링크 열기', timeout=3000)
                    if new_tab_option:
                        await new_tab_option.click()
                        await asyncio.sleep(3)

                        # 새 탭으로 전환
                        if len(context.pages) > 2:
                            page = context.pages[-1]
                            await page.wait_for_load_state('networkidle')

                            current_url = page.url
                            if "captcha" in current_url or await page.query_selector('text=security verification'):
                                print("  ❌ 캡차 발생!")
                                return False
                            else:
                                print("  ✅ 성공! 새 탭에서 열림")
                                return True
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return False
        finally:
            await asyncio.sleep(5)
            await browser.close()

async def test_method_6_manual_captcha():
    """방법 6: 캡차 수동 해결"""
    print("\n[방법 6] 캡차 수동 해결 테스트")
    print("  캡차가 나타나면 수동으로 해결해주세요...")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False, slow_mo=500, args=['--kiosk'])
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # 네이버 메인 → 쇼핑
            await page.goto('https://www.naver.com')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            shopping_link = await page.wait_for_selector('#shortcutArea > ul > li:nth-child(4) > a')
            await shopping_link.click()
            await asyncio.sleep(3)

            # 새 탭 전환
            if len(context.pages) > 1:
                page = context.pages[-1]
                await page.wait_for_load_state('networkidle')

            await asyncio.sleep(3)

            # 카테고리 메뉴 열기
            category_btn = await page.wait_for_selector('text=카테고리', timeout=5000)
            if category_btn:
                await category_btn.click()
                await asyncio.sleep(3)

                # 남성의류 클릭
                mens_clothing = await page.wait_for_selector('text=남성의류', timeout=5000)
                if mens_clothing:
                    await mens_clothing.click()
                    await asyncio.sleep(3)

                    # 캡차 확인
                    current_url = page.url
                    if "captcha" in current_url or await page.query_selector('text=security verification'):
                        print("  ⏳ 캡차 감지! 30초 내에 해결해주세요...")
                        await asyncio.sleep(30)  # 수동 해결 대기

                        # 다시 확인
                        current_url = page.url
                        if "shopping.naver.com" in current_url and "captcha" not in current_url:
                            print("  ✅ 캡차 해결 성공!")
                            return True
                        else:
                            print("  ❌ 캡차 해결 실패")
                            return False
                    else:
                        print("  ✅ 캡차 없이 성공!")
                        return True
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return False
        finally:
            await asyncio.sleep(10)
            await browser.close()

async def main():
    """모든 방법 순차 테스트"""
    print("=" * 50)
    print("네이버 쇼핑 카테고리 진입 테스트")
    print("=" * 50)

    results = []

    # 방법 1: 긴 대기 시간
    result = await test_method_1_longer_wait()
    results.append(("긴 대기 시간", result))

    # 방법 2: 호버
    result = await test_method_2_hover()
    results.append(("마우스 호버", result))

    # 방법 3: 스크롤
    result = await test_method_3_scroll()
    results.append(("스크롤 동작", result))

    # 방법 4: 검색
    result = await test_method_4_search()
    results.append(("검색 활용", result))

    # 방법 5: 우클릭
    result = await test_method_5_right_click()
    results.append(("우클릭 새탭", result))

    # 방법 6: 수동 해결
    result = await test_method_6_manual_captcha()
    results.append(("수동 해결", result))

    # 결과 정리
    print("\n" + "=" * 50)
    print("테스트 결과 요약")
    print("=" * 50)
    for method, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{method}: {status}")

if __name__ == "__main__":
    asyncio.run(main())