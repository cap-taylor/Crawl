"""
실시간 클릭 방식 크롤러 테스트
- 13번째 상품부터 시작
- 10개 수집
- 모든 DB 스키마 정보 출력
"""
import asyncio
import sys
import json
sys.path.append('/home/dino/MyProjects/Crawl')

from playwright.async_api import async_playwright
from src.utils.config import SELECTORS
from src.utils.selector_helper import SelectorHelper
import random
import re
from datetime import datetime

class RealClickCrawler:
    def __init__(self):
        self.products_data = []
        self.helper = SelectorHelper(debug=False)
        
    async def crawl(self):
        async with async_playwright() as p:
            browser = await p.firefox.launch(
                headless=False,
                slow_mo=1000
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
            
            # 1. 네이버 → 쇼핑 → 여성의류
            print("[1] 네이버 메인")
            await page.goto('https://www.naver.com')
            await asyncio.sleep(3)
            
            print("[2] 쇼핑 클릭")
            shopping = page.locator('#shortcutArea > ul > li:nth-child(4) > a')
            await shopping.click()
            await asyncio.sleep(3)
            
            page = context.pages[-1]
            await page.wait_for_load_state('networkidle')
            
            print("[3] 카테고리 클릭")
            category_btn = await page.wait_for_selector('button:has-text("카테고리")')
            await category_btn.click()
            await asyncio.sleep(2)
            
            print("[4] 여성의류 클릭")
            womens = await page.wait_for_selector('a[data-name="여성의류"]')
            await womens.click()
            
            # 20초 대기 (캡차 해결 시간)
            print("[대기] 20초 대기 중 (캡차 풀어주세요)...")
            for i in range(20, 0, -5):
                print(f"  {i}초...")
                await asyncio.sleep(5)
            print("✅ 대기 완료!\n")

            # 추가 로딩 대기
            print("[로딩] 상품 로딩 대기 중...")
            await asyncio.sleep(5)
            print("✅ 로딩 완료!\n")
            
            print("\n[5] 실시간 클릭 수집 시작\n")
            print("목표: 13번째부터 10개 수집 (1-12번 광고 스킵)\n")
            
            clicked_urls = set()  # 클릭한 URL만 기록
            found_count = 0
            total_checked = 0  # 전체 확인한 상품 수
            skip_count = 12  # 처음 12개 광고 스킵
            target_count = 10
            
            while found_count < target_count:
                # 상품 링크만 선택 (판매자 링크 제외)
                # miniProductCard_link 또는 basicProductCard_link (mall 제외)
                products = await page.query_selector_all('a[class*="ProductCard_link"]')
                
                print(f"[디버그] {len(products)}개 상품 링크 발견")
                
                if not products:
                    print("[경고] 상품을 찾을 수 없음")
                    break
                
                new_products_found = False
                
                # 상품 처리
                for idx, product in enumerate(products):
                    # 목표 달성 체크
                    if found_count >= target_count:
                        break
                    
                    try:
                        href = await product.get_attribute('href')

                        # URL 검증 (smartstore.naver.com/main/products/숫자)
                        if not href or 'products' not in href:
                            continue

                        # 광고 URL 필터링
                        if 'ader.naver.com' in href:
                            continue
                        
                        # 이미 클릭한 상품은 스킵
                        if href in clicked_urls:
                            continue
                        
                        # 새 상품 발견
                        total_checked += 1
                        new_products_found = True
                        
                        # 광고 스킵 (처음 12개)
                        if total_checked <= skip_count:
                            print(f"[{total_checked}번째] 광고 스킵")
                            clicked_urls.add(href)  # 스킵한 것도 기록
                            continue
                        
                        # 클릭할 상품
                        clicked_urls.add(href)
                        
                        # 수집 시작
                        print(f"\n[{total_checked}번째 상품] 클릭...", end="", flush=True)
                        
                        # 랜덤 대기 (사람처럼)
                        await asyncio.sleep(random.uniform(2.0, 4.0))
                        
                        # 진짜 클릭 (새 탭 자동 열림)
                        await product.click()
                        await asyncio.sleep(2)
                        
                        # 새 탭 찾기
                        if len(context.pages) > 1:
                            new_tab = context.pages[-1]
                            # 문서 권장: networkidle 15초
                            try:
                                await new_tab.wait_for_load_state('networkidle', timeout=15000)
                            except:
                                await asyncio.sleep(5)
                            
                            # 데이터 수집
                            data = await self._collect_product_data(new_tab, href)
                            
                            if data:
                                self.products_data.append(data)
                                found_count += 1
                                
                                # 간단 출력
                                name = data.get('product_name', 'N/A')[:40]
                                tags = len(data.get('search_tags', []))
                                print(f" [{name}] - 태그 {tags}개 ✅")
                            else:
                                print(" [SKIP] 수집 실패")
                            
                            # 탭 닫기
                            await new_tab.close()
                            await asyncio.sleep(random.uniform(1.0, 2.0))
                        
                    except Exception as e:
                        print(f" [ERROR] {str(e)[:50]}")
                        # 혹시 열린 탭 닫기
                        if len(context.pages) > 1:
                            await context.pages[-1].close()
                
                # 목표 달성 체크
                if found_count >= target_count:
                    break
                
                # 새 상품이 없으면 스크롤
                if not new_products_found:
                    print("\n[스크롤] 새 상품 로딩...")
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(3)
            
            print(f"\n{'='*60}")
            print(f"[완료] {found_count}개 수집 완료!")
            print(f"{'='*60}")
            
            await asyncio.sleep(3)
            await browser.close()
            
            return self.products_data
    
    async def _collect_product_data(self, page, url):
        """상품 데이터 수집 (DB 스키마 전체)"""
        try:
            # 에러 페이지 체크
            error_elem = await page.query_selector('text="현재 서비스 접속이 불가합니다"')
            if error_elem:
                return None
            
            # 스크롤 (검색태그 위치)
            scroll_percent = random.uniform(0.40, 0.50)
            await page.evaluate(f'window.scrollTo(0, document.body.scrollHeight * {scroll_percent})')
            await asyncio.sleep(1)
            
            data = {}
            
            # 1. product_id (URL에서 추출)
            match = re.search(r'/products/(\d+)', url)
            data['product_id'] = match.group(1) if match else None
            
            # 2. category_name
            data['category_name'] = "여성의류"
            
            # 3. product_name
            elem = await self.helper.try_selectors(page, SELECTORS['product_name'], "상품명")
            data['product_name'] = await self.helper.extract_text(elem, "상품명")
            
            # 4. brand_name
            elem = await self.helper.try_selectors(page, SELECTORS['brand_name'], "브랜드")
            data['brand_name'] = await self.helper.extract_text(elem, "브랜드")
            
            # 5. price
            elem = await self.helper.try_selectors(page, SELECTORS['price'], "가격")
            price_text = await self.helper.extract_text(elem, "가격")
            data['price'] = self.helper.clean_price(price_text)
            
            # 6. discount_rate
            elem = await self.helper.try_selectors(page, SELECTORS['discount_rate'], "할인율")
            discount_text = await self.helper.extract_text(elem, "할인율")
            data['discount_rate'] = self.helper.clean_discount_rate(discount_text)
            
            # 7. review_count
            elem = await self.helper.try_selectors(page, SELECTORS['review_count'], "리뷰 수")
            review_text = await self.helper.extract_text(elem, "리뷰 수")
            data['review_count'] = self.helper.clean_review_count(review_text)
            
            # 8. rating
            elem = await self.helper.try_selectors(page, SELECTORS['rating'], "평점")
            rating_text = await self.helper.extract_text(elem, "평점")
            data['rating'] = self.helper.clean_rating(rating_text)
            
            # 9. search_tags
            tags = []
            try:
                all_links = await page.query_selector_all('a')
                for link in all_links[:100]:
                    text = await self.helper.extract_text(link)
                    if text and text.strip().startswith('#'):
                        clean_tag = text.strip().replace('#', '').strip()
                        if 1 < len(clean_tag) < 30 and clean_tag not in tags:
                            tags.append(clean_tag)
            except:
                pass
            data['search_tags'] = tags
            
            # 10. product_url
            data['product_url'] = url
            
            # 11. thumbnail_url
            elem = await self.helper.try_selectors(page, SELECTORS['thumbnail'], "썸네일")
            data['thumbnail_url'] = await self.helper.extract_attribute(elem, "src", "썸네일")
            
            # 12. is_sold_out
            elem = await self.helper.try_selectors(page, SELECTORS['is_sold_out'], "품절")
            data['is_sold_out'] = (elem is not None)
            
            # 13. crawled_at
            data['crawled_at'] = datetime.now().isoformat()
            
            # 14. updated_at
            data['updated_at'] = datetime.now().isoformat()
            
            # 검증: 상품명 필수
            if not data['product_name'] or len(data['product_name']) < 5:
                return None
            
            return data
            
        except Exception as e:
            print(f"[수집 오류] {str(e)[:50]}")
            return None

async def main():
    crawler = RealClickCrawler()
    products = await crawler.crawl()
    
    if products:
        print(f"\n{'='*80}")
        print("📦 수집된 데이터 (DB 스키마 전체)")
        print(f"{'='*80}\n")
        
        for idx, product in enumerate(products, 1):
            print(f"[상품 {idx}]")
            print(json.dumps(product, ensure_ascii=False, indent=2))
            print("-" * 80)
    
    print(f"\n총 {len(products)}개 수집 완료!")

if __name__ == "__main__":
    asyncio.run(main())
