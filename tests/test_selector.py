"""
셀렉터 테스트 - 어떤 셀렉터가 작동하는지 확인
"""
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()
        
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
        
        print("[대기] 20초...")
        for i in range(20, 0, -5):
            print(f"  {i}초...")
            await asyncio.sleep(5)
        
        print("\n[테스트] 다양한 셀렉터 시도\n")
        
        # 1. 기존 셀렉터
        products1 = await page.query_selector_all('a[href*="/products/"]:has(img)')
        print(f"1. a[href*=\"/products/\"]:has(img) → {len(products1)}개")
        
        # 2. 단순 products 링크
        products2 = await page.query_selector_all('a[href*="/products/"]')
        print(f"2. a[href*=\"/products/\"] → {len(products2)}개")
        
        # 3. img 부모의 a 태그
        products3 = await page.query_selector_all('a:has(img)')
        print(f"3. a:has(img) → {len(products3)}개")
        
        # 4. 이미지
        imgs = await page.query_selector_all('img')
        print(f"4. img → {len(imgs)}개")
        
        # 5. div 안의 a
        products5 = await page.query_selector_all('div a')
        print(f"5. div a → {len(products5)}개")
        
        print("\n20초 후 종료...")
        await asyncio.sleep(20)
        await browser.close()

asyncio.run(test())
