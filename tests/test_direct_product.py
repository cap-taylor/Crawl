#!/usr/bin/env python3
"""
상품 직접 접속 - 모든 정보 수집
"""
import asyncio
import sys
import re
import json
from datetime import datetime
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright

async def collect_direct():
    # 13번째 상품 URL (이전 테스트에서 확인됨)
    url = "https://smartstore.naver.com/main/products/10981638556"

    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=300
        )

        context = await browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            extra_http_headers={
                'Accept-Language': 'ko-KR,ko;q=0.9'
            }
        )

        page = await context.new_page()

        print(f"상품 페이지 직접 접속")
        print(f"URL: {url}\n")

        await page.goto(url)
        await page.wait_for_load_state('networkidle')

        print("="*80)
        print("전체 정보 수집 시작")
        print("="*80 + "\n")

        data = {}

        # 1. product_id
        match = re.search(r'/products/(\d+)', url)
        data['product_id'] = match.group(1) if match else None
        print(f"✅ 1. product_id: {data['product_id']}")

        # 2. category_name
        data['category_name'] = "여성의류"
        print(f"✅ 2. category_name: {data['category_name']}")

        # 3. product_name (h3.DCVBehA8ZB)
        try:
            elem = await page.query_selector('h3.DCVBehA8ZB')
            if elem:
                data['product_name'] = await elem.inner_text()
            else:
                data['product_name'] = None
        except:
            data['product_name'] = None
        print(f"✅ 3. product_name: {data['product_name']}")

        # 4. brand_name (h1 - 스토어명)
        try:
            elem = await page.query_selector('h1')
            if elem:
                data['brand_name'] = await elem.inner_text()
            else:
                data['brand_name'] = None
        except:
            data['brand_name'] = None
        print(f"✅ 4. brand_name: {data['brand_name']}")

        # 5. price (strong.Izp3Con8h8)
        try:
            elem = await page.query_selector('strong.Izp3Con8h8')
            if elem:
                price_text = await elem.inner_text()
                price_clean = re.sub(r'[^\d]', '', price_text)
                data['price'] = int(price_clean) if price_clean else None
            else:
                data['price'] = None
        except:
            data['price'] = None
        print(f"✅ 5. price: {data['price']}원")

        # 6. discount_rate (JavaScript로 찾기)
        data['discount_rate'] = None
        try:
            discount_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    // "40%" 같은 패턴, 짧은 텍스트
                    if (text.includes('%') && text.length < 20) {
                        const match = text.match(/(\\d+)%/);
                        if (match && elem.children.length <= 1) {
                            // "할인" 단어와 함께 있는지 확인
                            const parent = elem.parentElement;
                            if (parent && parent.textContent.includes('할인')) {
                                return match[1];
                            }
                        }
                    }
                }
                return null;
            }''')
            if discount_result:
                data['discount_rate'] = int(discount_result)
        except:
            pass
        print(f"✅ 6. discount_rate: {data['discount_rate']}%")

        # 7. review_count ("리뷰 10")
        data['review_count'] = None
        try:
            review_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    // "리뷰 10" 패턴
                    if (text.includes('리뷰') && text.length < 20) {
                        const match = text.match(/리뷰\\s*(\\d+)/);
                        if (match) {
                            return match[1];
                        }
                    }
                }
                return null;
            }''')
            if review_result:
                data['review_count'] = int(review_result)
        except:
            pass
        print(f"✅ 7. review_count: {data['review_count']}개")

        # 8. rating (평점)
        data['rating'] = None
        try:
            rating_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    // "평점 4.5" 또는 "별점 4.5"
                    if ((text.includes('평점') || text.includes('별점')) && text.length < 30) {
                        const match = text.match(/(\\d+\\.\\d+)/);
                        if (match) {
                            return parseFloat(match[1]);
                        }
                    }
                }
                return null;
            }''')
            if rating_result:
                data['rating'] = rating_result
        except:
            pass
        print(f"✅ 8. rating: {data['rating']}")

        # 9. search_tags (전체 스크롤)
        print("\n✅ 9. search_tags 수집 중... (페이지 끝까지 스크롤)")
        data['search_tags'] = []
        all_tags_found = set()

        # 10%부터 100%까지 전체 스크롤
        for scroll_pos in range(10, 101, 10):
            await page.evaluate(f'window.scrollTo(0, document.body.scrollHeight * {scroll_pos/100})')
            await asyncio.sleep(1.5)

            all_links = await page.query_selector_all('a')

            for link in all_links:
                try:
                    text = await link.inner_text()
                    if text and text.strip().startswith('#'):
                        clean_tag = text.strip().replace('#', '').strip()
                        if 1 < len(clean_tag) < 30:
                            all_tags_found.add(clean_tag)
                except:
                    pass

            if all_tags_found and len(all_tags_found) > 0:
                print(f"   {scroll_pos}% 위치: 총 {len(all_tags_found)}개 태그 누적")

        data['search_tags'] = list(all_tags_found)
        print(f"\n   최종 수집: {len(data['search_tags'])}개")
        if data['search_tags']:
            print(f"   → {data['search_tags'][:15]}")
        else:
            print(f"   ❌ 태그 없음")

        # 10. product_url
        data['product_url'] = url
        print(f"\n✅ 10. product_url: {url}")

        # 11. thumbnail_url
        try:
            elem = await page.query_selector('img[class*="image"]')
            if elem:
                data['thumbnail_url'] = await elem.get_attribute('src')
            else:
                data['thumbnail_url'] = None
        except:
            data['thumbnail_url'] = None
        print(f"✅ 11. thumbnail_url: {data['thumbnail_url'][:80] if data['thumbnail_url'] else 'N/A'}...")

        # 12. is_sold_out
        data['is_sold_out'] = False
        try:
            soldout_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('button, span');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    // "품절" 단어만 있는 짧은 텍스트 (버튼이나 상태)
                    if (text.trim() === '품절' || (text.includes('품절') && text.length < 10)) {
                        return true;
                    }
                }
                return false;
            }''')
            data['is_sold_out'] = soldout_result
        except:
            pass
        print(f"✅ 12. is_sold_out: {data['is_sold_out']}")

        # 13, 14. 타임스탬프
        data['crawled_at'] = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        print(f"✅ 13. crawled_at: {data['crawled_at']}")
        print(f"✅ 14. updated_at: {data['updated_at']}")

        # === 추가 정보 수집 시도 ===
        print("\n" + "="*80)
        print("추가 정보 탐색")
        print("="*80 + "\n")

        # 원가 (할인 전 가격)
        try:
            original_price_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    // "115,000원" 같은 패턴 (취소선 또는 작은 글씨)
                    if (text.includes('원') && text.length < 30) {
                        const match = text.match(/([\\d,]+)원/);
                        if (match) {
                            const price = match[1].replace(/,/g, '');
                            // 현재 가격보다 크면 원가일 가능성
                            if (parseInt(price) > 67900) {
                                return parseInt(price);
                            }
                        }
                    }
                }
                return null;
            }''')
            if original_price_result:
                print(f"💡 원가 (할인 전): {original_price_result:,}원")
        except:
            pass

        # 배송비
        try:
            delivery_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    if (text.includes('배송') && text.includes('원') && text.length < 50) {
                        return text.trim();
                    }
                }
                return null;
            }''')
            if delivery_result:
                print(f"💡 배송 정보: {delivery_result}")
        except:
            pass

        # 제조사/브랜드 (상품정보 테이블에서)
        try:
            manufacturer_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    if (text.includes('제조사') && text.length < 100) {
                        return text.trim();
                    }
                }
                return null;
            }''')
            if manufacturer_result:
                print(f"💡 제조사 정보: {manufacturer_result}")
        except:
            pass

        # === 최종 결과 ===
        print("\n" + "="*80)
        print("수집 완료 - JSON 형식")
        print("="*80 + "\n")

        print(json.dumps(data, ensure_ascii=False, indent=2))

        print("\n" + "="*80)
        print("수집 통계")
        print("="*80)

        filled_fields = []
        empty_fields = []

        for k, v in data.items():
            if v not in [None, [], 0, '']:
                filled_fields.append(k)
            else:
                empty_fields.append(k)

        print(f"✅ 수집 성공: {len(filled_fields)}/14 필드 ({len(filled_fields)/14*100:.1f}%)")
        print(f"   → {filled_fields}")
        print(f"\n❌ 수집 실패: {len(empty_fields)}/14 필드")
        print(f"   → {empty_fields}")

        print("\n\n브라우저 60초 유지 (직접 확인)")
        await asyncio.sleep(60)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(collect_direct())
