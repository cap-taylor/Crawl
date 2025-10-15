"""네이버 쇼핑 실제 카테고리 수집 - 시행착오 문서 기반"""
import asyncio
from playwright.async_api import async_playwright
import json
import time

async def collect_real_categories():
    """CRAWLING_LESSONS_LEARNED.md 문서 기반 정확한 방법"""
    async with async_playwright() as p:
        print("=" * 50)
        print("📖 시행착오 문서 기반 카테고리 수집")
        print("=" * 50)

        # Firefox 사용 (문서에서 성공 확인)
        print("🦊 Firefox 브라우저 실행...")
        browser = await p.firefox.launch(
            headless=False,  # 반드시 False (문서: Headless 모드 차단됨)
            args=['--kiosk']  # Firefox 전체화면 (문서: --kiosk 성공)
        )

        context = await browser.new_context(
            viewport=None,
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )

        page = await context.new_page()

        try:
            # 1. 네이버 메인 접속 (문서: 메인→쇼핑 클릭이 성공 방법)
            print("📍 네이버 메인 접속 (캡차 없음)...")
            await page.goto("https://www.naver.com", wait_until="networkidle")
            print("✅ 네이버 메인 접속 성공")
            await asyncio.sleep(3)  # 랜덤 대기 (문서: 2-5초 권장)

            # 2. 쇼핑 버튼 찾기 - 더 정확한 선택자
            print("🔍 쇼핑 버튼 찾는 중...")

            # 스크린샷 저장 (디버깅용)
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            screenshot_path = os.path.join(project_root, "data", "naver_main.png")
            await page.screenshot(path=screenshot_path)
            print(f"📸 메인 페이지 스크린샷 저장: {screenshot_path}")

            # 쇼핑 링크 찾기 - 여러 방법 시도
            shopping_link = None

            # 방법 1: 텍스트로 찾기
            try:
                shopping_link = await page.query_selector('text="쇼핑"')
                if shopping_link:
                    print("✅ 쇼핑 버튼 찾음 (텍스트)")
            except:
                pass

            # 방법 2: 쇼핑 서비스 링크
            if not shopping_link:
                try:
                    links = await page.query_selector_all('#shortcutArea a')
                    for link in links:
                        text = await link.text_content()
                        if text and "쇼핑" in text:
                            shopping_link = link
                            print("✅ 쇼핑 버튼 찾음 (shortcutArea)")
                            break
                except:
                    pass

            if shopping_link:
                # 새 탭 처리
                print("🛍️ 쇼핑 클릭 (새 탭에서 열림)...")

                # 새 탭 이벤트 리스너
                async with context.expect_page() as new_page_info:
                    await shopping_link.click()

                shopping_page = await new_page_info.value
                await shopping_page.wait_for_load_state("networkidle")

                print(f"✅ 쇼핑 페이지 접속 성공: {shopping_page.url}")
                await asyncio.sleep(3)

                # 3. 카테고리 수집
                print("\n📂 카테고리 수집 시작...")

                # 카테고리 영역 찾기
                categories = {}

                # 스크린샷의 카테고리들
                category_names = [
                    # 패션
                    "FashionTown", "미스터", "LUXURY",
                    "스포츠/레저", "반려동물용품", "여성의류", "남성의류",
                    "신발", "가방", "패션잡화",

                    # 뷰티
                    "화장품/미용", "향수", "스킨케어", "메이크업",

                    # 식품
                    "신선식품", "가공식품", "건강식품", "음료/간식",

                    # 가전/디지털
                    "PC/주변기기", "가전", "모바일", "카메라",

                    # 생활
                    "가구", "조명/인테리어", "주방용품", "생활용품",
                    "패브릭/홈데코", "수납/정리",

                    # 기타
                    "출산/유아동", "자동차/오토바이", "키덜트/취미",
                    "건강/의료용품", "도서", "문구"
                ]

                # 각 카테고리 찾기
                for cat_name in category_names:
                    try:
                        elements = await shopping_page.query_selector_all(f'text="{cat_name}"')
                        if elements:
                            categories[cat_name] = True
                            print(f"  ✓ {cat_name}")
                    except:
                        continue

                # 카테고리 저장
                category_data = {
                    "수집일시": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "카테고리": list(categories.keys()),
                    "총개수": len(categories)
                }

                save_path = os.path.join(project_root, "data", "naver_categories.json")
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(category_data, f, ensure_ascii=False, indent=2)

                print(f"\n✅ 총 {len(categories)}개 카테고리 확인")
                print(f"💾 저장: {save_path}")

            else:
                print("❌ 쇼핑 버튼을 찾을 수 없음")
                print("💡 직접 URL 접속은 캡차 발생하므로 사용 안함")

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
    asyncio.run(collect_real_categories())