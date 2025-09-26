#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 쇼핑 실제 상품 정보 구조 분석 스크립트
실제 페이지에서 어떤 정보들이 표시되는지 확인
"""

import asyncio
from playwright.async_api import async_playwright
import json
import sys
import os

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.config import CRAWL_CONFIG

async def analyze_product_structure():
    """네이버 쇼핑 상품 정보 구조 분석"""

    async with async_playwright() as p:
        print("브라우저 시작...")
        browser = await p.chromium.launch(
            headless=False,  # 화면 표시
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=CRAWL_CONFIG['user_agent']
        )

        # Stealth 모드
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = await context.new_page()

        try:
            print(f"네이버 쇼핑 접속: {CRAWL_CONFIG['base_url']}")
            await page.goto(CRAWL_CONFIG['base_url'])
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)

            print("페이지 스크롤하여 상품 로드...")
            await page.evaluate("window.scrollTo(0, 2000)")
            await asyncio.sleep(2)

            # 상품 카드 찾기
            print("\n상품 정보 분석 중...")

            # 첫 번째 상품 카드 선택
            product_cards = await page.query_selector_all('[class*="product"]')

            if product_cards and len(product_cards) > 0:
                print(f"상품 카드 {len(product_cards)}개 발견\n")

                # 첫 번째 상품 상세 분석
                first_product = product_cards[0]

                # 가능한 모든 텍스트 추출
                product_html = await first_product.inner_html()
                product_text = await first_product.inner_text()

                print("=== 첫 번째 상품 카드 텍스트 ===")
                print(product_text[:500])  # 처음 500자만
                print("\n")

                # 구조적 분석
                print("=== 상품 정보 요소 분석 ===")

                # 상품명
                title_elem = await first_product.query_selector('[class*="title"], [class*="name"]')
                if title_elem:
                    title = await title_elem.inner_text()
                    print(f"✅ 상품명: {title}")

                # 가격
                price_elem = await first_product.query_selector('[class*="price"]')
                if price_elem:
                    price = await price_elem.inner_text()
                    print(f"✅ 가격: {price}")

                # 브랜드/몰명
                brand_elem = await first_product.query_selector('[class*="brand"], [class*="mall"]')
                if brand_elem:
                    brand = await brand_elem.inner_text()
                    print(f"✅ 브랜드/몰: {brand}")

                # 리뷰
                review_elem = await first_product.query_selector('[class*="review"]')
                if review_elem:
                    review = await review_elem.inner_text()
                    print(f"✅ 리뷰: {review}")

                # 평점
                rating_elem = await first_product.query_selector('[class*="rating"], [class*="star"]')
                if rating_elem:
                    rating = await rating_elem.inner_text()
                    print(f"✅ 평점: {rating}")

                # 배송
                delivery_elem = await first_product.query_selector('[class*="delivery"], [class*="ship"]')
                if delivery_elem:
                    delivery = await delivery_elem.inner_text()
                    print(f"✅ 배송: {delivery}")

                # 태그/혜택
                tags = await first_product.query_selector_all('[class*="tag"], [class*="badge"]')
                if tags:
                    print(f"✅ 태그/혜택: {len(tags)}개")
                    for tag in tags[:3]:  # 처음 3개만
                        tag_text = await tag.inner_text()
                        print(f"   - {tag_text}")

                # 할인
                discount_elem = await first_product.query_selector('[class*="discount"]')
                if discount_elem:
                    discount = await discount_elem.inner_text()
                    print(f"✅ 할인: {discount}")

                print("\n=== HTML 구조 샘플 (처음 1000자) ===")
                print(product_html[:1000])

            else:
                print("상품 카드를 찾을 수 없습니다.")

                # 페이지 전체 구조 확인
                print("\n페이지 구조 분석 중...")
                all_text = await page.inner_text('body')
                print("페이지 텍스트 (처음 1000자):")
                print(all_text[:1000])

            # 스크린샷 저장
            await page.screenshot(path="tests/product_analysis.png")
            print("\n스크린샷 저장: tests/product_analysis.png")

        except Exception as e:
            print(f"오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

        finally:
            print("\n분석 완료. 브라우저를 닫습니다...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_product_structure())