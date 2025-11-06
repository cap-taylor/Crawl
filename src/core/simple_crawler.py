#!/usr/bin/env python3
"""
간단하고 깔끔한 네이버 쇼핑 크롤러 (v1.1.0)
13개 필드 완벽 수집 + DB 직접 저장
"""

import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright
from typing import Optional, List, Dict
import sys
from pathlib import Path
import time

# DB Connector import
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.database.db_connector import DatabaseConnector


class SimpleCrawler:
    """
    네이버 쇼핑 상품 수집 크롤러
    13개 필드: product_id, category_name, product_name, search_tags,
              price, rating, product_url, thumbnail_url, brand_name,
              discount_rate, review_count, crawled_at, updated_at
    """

    def __init__(self,
                 category_name: str = "여성의류",
                 category_id: str = "10000107",
                 product_count: Optional[int] = None,  # None = 무한
                 headless: bool = False,
                 save_to_db: bool = True):
        self.category_name = category_name
        self.category_id = category_id
        self.product_count = product_count  # None이면 무한 수집
        self.headless = headless
        self.save_to_db = save_to_db
        self.should_stop = False
        self.products_data = []

        # DB 연결 (save_to_db가 True일 때만) - 세션 유지 방식
        self.db = DatabaseConnector() if save_to_db else None
        self.db_connected = False

        # 통계 추적
        self.start_time = None
        self.saved_count = 0  # DB 저장 성공
        self.skipped_count = 0  # 중복 스킵

        # Sliding Window 설정 (오버레이 메모리 최적화)
        self.OVERLAY_WINDOW = 10  # 현재 상품 ±10개만 오버레이 유지

    async def crawl(self) -> List[Dict]:
        """크롤링 실행"""
        async with async_playwright() as p:
            browser = await p.firefox.launch(
                headless=self.headless,
                slow_mo=300,
                args=['--start-maximized']  # 브라우저 최대화로 시작
            )

            # 📌 viewport 설정 설명:
            # - viewport는 무한 스크롤을 위해 반드시 필요! (no_viewport=True 사용 금지)
            # - 네이버는 "화면에 보이는 영역"을 감지해서 새 상품을 로드함
            # - no_viewport=True → 무한 높이 → "이미 다 보임" → 추가 로드 안 함
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},  # 고정 크기 (Intersection Observer 작동용)
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                locale='ko-KR',
                timezone_id='Asia/Seoul'
            )

            page = await context.new_page()

            try:
                # DB 연결 (세션 유지)
                if self.save_to_db and self.db:
                    try:
                        self.db.connect()
                        self.db_connected = True
                        print("[DB] 연결 성공")
                    except Exception as e:
                        print(f"[DB] 연결 실패: {str(e)}")
                        self.db_connected = False

                # 1. 네이버 메인 → 쇼핑 진입
                print("[1/4] 네이버 메인 페이지 접속...")
                await page.goto('https://www.naver.com')
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(2)

                # 쇼핑 클릭 (광고가 가려도 강제 클릭)
                print("[2/4] 쇼핑 버튼 클릭...")
                shopping_selector = '#shortcutArea > ul > li:nth-child(4) > a'
                await page.locator(shopping_selector).click(timeout=10000, force=True)
                await asyncio.sleep(2)

                # 새 탭 전환
                all_pages = context.pages
                if len(all_pages) > 1:
                    page = all_pages[-1]
                    await page.wait_for_load_state('networkidle')

                # 2. 카테고리 진입 (CRAWLING_LESSONS_LEARNED.md 검증된 방법)
                print(f"[3/4] '{self.category_name}' 카테고리 진입...")
                category_btn = await page.wait_for_selector('button:has-text("카테고리")', timeout=10000)
                await category_btn.click()

                # 카테고리 메뉴가 나타날 때까지 대기 (최대 5초)
                await asyncio.sleep(1)

                # 우선순위별 셀렉터 fallback (문서 1293-1296줄)
                category_elem = None

                # 1순위: ID 기반 (⭐⭐⭐⭐⭐) - 명시적 대기
                if self.category_id:
                    try:
                        category_elem = await page.wait_for_selector(f'#cat_layer_item_{self.category_id}', timeout=5000)
                    except:
                        pass

                # 2순위: data-id 속성 (⭐⭐⭐⭐)
                if not category_elem and self.category_id:
                    try:
                        category_elem = await page.wait_for_selector(f'[data-id="{self.category_id}"]', timeout=3000)
                    except:
                        pass

                # 3순위: data-name 속성 (⭐⭐⭐)
                if not category_elem:
                    try:
                        category_elem = await page.wait_for_selector(f'a[data-name="{self.category_name}"]', timeout=3000)
                    except:
                        pass

                if not category_elem:
                    raise Exception(f"카테고리 '{self.category_name}' (ID: {self.category_id})를 찾을 수 없습니다")

                await category_elem.click()
                await asyncio.sleep(3)

                # 캡차 체크 및 자동 포커스
                print("\n" + "="*60)
                print("[!] 캡차 확인 중...")
                print("="*60)

                # 캡차 입력 필드 찾기 (네이버 캡차 input 셀렉터)
                captcha_input = None
                try:
                    # 캡차 입력 필드가 있는지 확인 (1초 대기)
                    # 실제 테스트로 확인된 셀렉터: input#rcpt_answer, input[name='captcha']
                    captcha_input = await page.wait_for_selector(
                        'input#rcpt_answer, input[name="captcha"], input.input_text',
                        timeout=1000,
                        state='visible'
                    )
                except:
                    # 캡차가 없으면 넘어감
                    pass

                if captcha_input:
                    # 캡차가 있으면 입력 필드에 포커스
                    print("🔔 캡차 감지! 입력 필드에 포커스를 맞췄습니다.")
                    print("브라우저에서 캡차를 입력하고 Enter를 누르세요")
                    print("="*60)

                    # 입력 필드에 포커스 및 하이라이트
                    await captcha_input.focus()
                    await captcha_input.click()

                    # 입력 필드를 노란색으로 하이라이트 (시각적 피드백)
                    await page.evaluate("""
                        (element) => {
                            element.style.border = '3px solid #FFD700';
                            element.style.boxShadow = '0 0 10px #FFD700';
                            element.style.animation = 'pulse 1s infinite';

                            // 애니메이션 추가
                            if (!document.getElementById('captcha-pulse-style')) {
                                const style = document.createElement('style');
                                style.id = 'captcha-pulse-style';
                                style.innerHTML = `
                                    @keyframes pulse {
                                        0% { box-shadow: 0 0 10px #FFD700; }
                                        50% { box-shadow: 0 0 20px #FFD700; }
                                        100% { box-shadow: 0 0 10px #FFD700; }
                                    }
                                `;
                                document.head.appendChild(style);
                            }
                        }
                    """, captcha_input)

                    # 캡차 해결 대기 (최대 30초)
                    for i in range(30, 0, -5):
                        print(f"[대기] 캡차 입력 대기 중... {i}초 남음")

                        # 캡차 입력 필드가 사라졌는지 확인 (실제 셀렉터 사용!)
                        try:
                            await page.wait_for_selector(
                                'input#rcpt_answer, input[name="captcha"], input.input_text',
                                timeout=1000,
                                state='hidden'
                            )
                            print("[✓] 캡차 해결 완료!")
                            break
                        except:
                            pass

                        await asyncio.sleep(5)
                else:
                    # 캡차가 없는 경우 짧게 대기
                    print("캡차 없음 - 페이지 로딩 대기 (5초)")
                    await asyncio.sleep(5)

                print("[OK] 대기 완료! 크롤링 시작...\n")
                print("="*60)
                await asyncio.sleep(2)

                # 3. 무한 스크롤 수집 시작
                if self.product_count:
                    print(f"[4/4] 상품 {self.product_count}개 수집 시작...\n")
                else:
                    print(f"[4/4] 무한 수집 시작 (중지 버튼으로 멈출 수 있습니다)...\n")

                # 시작 시간 기록
                self.start_time = time.time()

                # 상품 영역 시작점 찾기 (광고/헤더 제외)
                try:
                    # 방법 1: #content > div:nth-child(9) 이후 상품들
                    product_container = await page.query_selector('#content > div:nth-child(9)')
                    if product_container:
                        print("[INFO] 상품 영역 시작점 발견: #content > div:nth-child(9)")
                    else:
                        # 방법 2: 정렬 버튼 다음 영역
                        sort_button = await page.query_selector('#product-sort-address-container > div > div > div > button')
                        if sort_button:
                            print("[INFO] 정렬 버튼 기준점 발견")
                except:
                    print("[INFO] 기본 셀렉터 사용")

                # 초기 배치 크기 결정 (실제 상품만)
                # 상품 목록을 더 정확하게 선택
                initial_links = await page.query_selector_all('a[class*="ProductCard_link"]')

                # 광고나 추천 상품 필터링 (상위 6개 이후부터 시작)
                if len(initial_links) > 6:
                    # 처음 6개는 잘 작동하니까 유지, 7번째부터 재검증
                    print(f"[DEBUG] 전체 링크 수: {len(initial_links)}개")

                batch_size = len(initial_links)
                print(f"\n초기 상품 수: {len(initial_links)}개 → 배치 크기: {batch_size}개")

                collected_count = 0
                processed_indices = set()  # 이미 처리한 상품 인덱스 추적
                scroll_count = 0
                batch_num = 0
                max_scroll_attempts = 100  # 최대 스크롤 횟수
                consecutive_failures = 0  # 연속 스크롤 실패 횟수 (리로드 복구용)

                while scroll_count < max_scroll_attempts:
                    if self.should_stop:
                        break

                    batch_num += 1

                    # 현재 페이지의 모든 상품 링크 가져오기
                    # 광고/추천 제외: 정렬 옵션(#product-sort-address-container) 아래 상품만 수집

                    # [OK] 첫 번째 배치에서만 필터링 (이후 스크롤은 추가만)
                    if batch_num == 1:
                        try:
                            print("\n[페이지 상태 확인] 필터링 전 페이지 안정화 대기 중...", flush=True)

                            # 페이지 상태 확인 (최대 10초 대기)
                            page_ready = False
                            for check_attempt in range(10):
                                page_status = await page.evaluate('''() => {
                                    const sortContainer = document.querySelector('#product-sort-address-container');
                                    const productLinks = document.querySelectorAll('a[class*="ProductCard_link"]');

                                    return {
                                        hasSortContainer: !!sortContainer,
                                        productCount: productLinks.length,
                                        pageTitle: document.title,
                                        url: window.location.href
                                    };
                                }''')

                                print(f"  시도 {check_attempt + 1}/10:", flush=True)
                                print(f"    정렬 컨테이너: {'✓' if page_status['hasSortContainer'] else '✗'}", flush=True)
                                print(f"    상품 링크: {page_status['productCount']}개", flush=True)
                                print(f"    페이지: {page_status['pageTitle'][:50]}", flush=True)

                                if page_status['hasSortContainer'] and page_status['productCount'] > 0:
                                    print(f"  [OK] 페이지 준비 완료!", flush=True)
                                    page_ready = True
                                    break

                                await asyncio.sleep(1)

                            if not page_ready:
                                print(f"\n[!!] 경고: 페이지가 완전히 로드되지 않았습니다!", flush=True)
                                print(f"  URL: {page_status['url']}", flush=True)
                                print(f"  계속 진행하되, 문제 발생 가능성 있음", flush=True)

                            # [+] 페이지 리로드 방지 + 감지 시스템 설치
                            print("\n[리로드 방지] 페이지 새로고침 차단 시스템 설치 중...", flush=True)
                            await page.evaluate('''() => {
                                // beforeunload 이벤트로 리로드 방지 시도
                                window.addEventListener('beforeunload', (e) => {
                                    console.error('[[!!] 페이지 리로드 시도 감지!] beforeunload 이벤트 발생');
                                    console.trace('[Stack Trace] 리로드 시도 경로');

                                    // 리로드 방지 (브라우저가 확인 메시지 표시)
                                    e.preventDefault();
                                    e.returnValue = '';

                                    return '크롤링 진행 중입니다. 페이지를 나가시겠습니까?';
                                });

                                // URL 변경 감지 (history API)
                                const originalPushState = history.pushState;
                                const originalReplaceState = history.replaceState;

                                history.pushState = function(...args) {
                                    console.warn('[[!!] URL 변경 감지!] pushState:', args[2]);
                                    return originalPushState.apply(this, arguments);
                                };

                                history.replaceState = function(...args) {
                                    console.warn('[[!!] URL 변경 감지!] replaceState:', args[2]);
                                    return originalReplaceState.apply(this, arguments);
                                };

                                // 초기 URL 저장
                                window.__initialURL = window.location.href;
                                console.log('[리로드 방지] 초기 URL:', window.__initialURL);

                                // 주기적으로 URL 변경 체크
                                setInterval(() => {
                                    if (window.location.href !== window.__initialURL) {
                                        console.error('[[!!] 페이지 리로드 발생!] URL이 변경됨');
                                        console.error('  이전:', window.__initialURL);
                                        console.error('  현재:', window.location.href);
                                        window.__initialURL = window.location.href;
                                    }
                                }, 2000);
                            }''')
                            print("  [OK] 리로드 방지 시스템 활성화", flush=True)

                            print("\n[필터링] 정렬 옵션 아래 상품만 선택 중...", flush=True)

                            # JavaScript로 필터링 (브라우저 크래시 방지)
                            print(f"[필터링] 첫 번째 배치 필터링 시작...", flush=True)

                            try:
                                filtered_count = await page.evaluate('''() => {
                                    // 1. 정렬 옵션 찾기
                                    const sort = document.querySelector('#product-sort-address-container');
                                    if (!sort) return {total: 0, filtered: 0, aboveSort: 0, recommendations: 0, labelPatterns: []};

                                    const sortY = sort.getBoundingClientRect().bottom;

                                    // 2. 모든 상품 링크 찾기
                                    const allLinks = Array.from(document.querySelectorAll('a[class*="ProductCard_link"]'));

                                    // 3. 정렬 옵션 아래 상품만 필터링하고 표시
                                    // [OK] v1.5.9+ "FOR YOU 연관 추천" 섹션 제외 (aria-labelledby 체크)
                                    let filteredCount = 0;
                                    let aboveSortCount = 0;
                                    let recommendationCount = 0;
                                    const labelPatterns = new Set();

                                    allLinks.forEach(link => {
                                        const rect = link.getBoundingClientRect();
                                        const labelId = link.getAttribute('aria-labelledby') || '';

                                        // aria-labelledby 패턴 수집 (처음 5개만)
                                        if (labelId && labelPatterns.size < 5) {
                                            labelPatterns.add(labelId);
                                        }

                                        // "FOR YOU 연관 추천" 섹션 상품 확인
                                        const isRecommendation = labelId.includes('related_recommend_product_information');

                                        if (rect.top <= sortY) {
                                            // 정렬 옵션 위 (제외)
                                            aboveSortCount++;
                                            link.setAttribute('data-filtered', 'false');
                                        } else if (isRecommendation) {
                                            // FOR YOU 추천 (제외)
                                            recommendationCount++;
                                            link.setAttribute('data-filtered', 'false');
                                        } else {
                                            // 정상 상품 (선택)
                                            link.setAttribute('data-filtered', 'true');
                                            filteredCount++;
                                        }
                                    });

                                    return {
                                        total: allLinks.length,
                                        filtered: filteredCount,
                                        aboveSort: aboveSortCount,
                                        recommendations: recommendationCount,
                                        labelPatterns: Array.from(labelPatterns)
                                    };
                                }''')
                                print(f"[DEBUG] evaluate() 성공, 결과 타입: {type(filtered_count)}", flush=True)
                            except Exception as eval_err:
                                print(f"[!!] JavaScript evaluate() 실패!", flush=True)
                                print(f"  에러 타입: {type(eval_err).__name__}", flush=True)
                                print(f"  에러 메시지: {str(eval_err)[:200]}", flush=True)
                                # Fallback: 빈 결과 반환
                                filtered_count = {
                                    'total': 0,
                                    'filtered': 0,
                                    'aboveSort': 0,
                                    'recommendations': 0,
                                    'labelPatterns': []
                                }

                            print(f"[필터링 결과]", flush=True)
                            print(f"  전체 링크: {filtered_count['total']}개", flush=True)
                            print(f"  - 정렬 옵션 위: {filtered_count['aboveSort']}개 (제외)", flush=True)
                            print(f"  - FOR YOU 추천: {filtered_count['recommendations']}개 (제외)", flush=True)
                            print(f"  - 정상 상품: {filtered_count['filtered']}개 (선택)", flush=True)
                            if filtered_count['labelPatterns']:
                                print(f"[셀렉터 패턴] aria-labelledby 예시 (처음 5개):", flush=True)
                                for pattern in filtered_count['labelPatterns']:
                                    print(f"  - {pattern}", flush=True)

                            # 필터링된 상품만 가져오기
                            product_links = await page.query_selector_all('a[data-filtered="true"]')

                            # v1.7.6 디버그: 필터링된 상품 URL 샘플 출력
                            if len(product_links) > 0:
                                sample_urls = await page.evaluate('''() => {
                                    const links = document.querySelectorAll('a[data-filtered="true"]');
                                    const samples = [];
                                    const indices = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90];  // 샘플 인덱스
                                    indices.forEach(i => {
                                        if (i < links.length) {
                                            const url = links[i].href || '';
                                            const productId = url.match(/nvMid=(\d+)/);
                                            samples.push({
                                                index: i,
                                                productId: productId ? productId[1] : 'N/A'
                                            });
                                        }
                                    });
                                    return samples;
                                }''')
                                print(f"[필터링 샘플] 10개씩 확인:", flush=True)
                                for sample in sample_urls:
                                    print(f"  [{sample['index']}번] product_id: {sample['productId']}", flush=True)

                            if len(product_links) == 0:
                                # 필터링 실패 시 전체 사용
                                print(f"\n[!!] [필터링 실패] 필터링된 상품이 0개입니다!", flush=True)
                                print(f"  원인 분석 중...", flush=True)

                                # 페이지 상태 재확인
                                fallback_status = await page.evaluate('''() => {
                                    return {
                                        sortContainer: !!document.querySelector('#product-sort-address-container'),
                                        allLinks: document.querySelectorAll('a[class*="ProductCard_link"]').length,
                                        filteredLinks: document.querySelectorAll('a[data-filtered="true"]').length,
                                        url: window.location.href,
                                        title: document.title
                                    };
                                }''')

                                print(f"  정렬 컨테이너: {'있음' if fallback_status['sortContainer'] else '없음'}", flush=True)
                                print(f"  전체 상품 링크: {fallback_status['allLinks']}개", flush=True)
                                print(f"  필터링된 링크: {fallback_status['filteredLinks']}개", flush=True)
                                print(f"  현재 URL: {fallback_status['url']}", flush=True)

                                # 스크린샷 저장
                                screenshot_path = f"/home/dino/MyProjects/Crawl/temp/filtering_failed_{batch_num}.png"
                                await page.screenshot(path=screenshot_path)
                                print(f"  스크린샷 저장: {screenshot_path}", flush=True)

                                # Fallback: 전체 상품 사용
                                print(f"\n  → Fallback: 전체 상품 사용 시도...", flush=True)
                                product_links = await page.query_selector_all('a[class*="ProductCard_link"]')
                                print(f"  → Fallback 결과: {len(product_links)}개 발견", flush=True)

                        except Exception as e:
                            # 에러 시 기본 셀렉터 사용
                            print(f"\n[**] [필터링 에러] 예외 발생!", flush=True)
                            print(f"  에러 타입: {type(e).__name__}", flush=True)
                            print(f"  에러 메시지: {str(e)[:200]}", flush=True)

                            # 페이지 상태 확인
                            try:
                                error_status = await page.evaluate('window.location.href')
                                print(f"  현재 URL: {error_status}", flush=True)
                            except:
                                print(f"  (URL 확인 불가 - 페이지 크래시 가능성)", flush=True)

                            # 스크린샷 저장
                            try:
                                screenshot_path = f"/home/dino/MyProjects/Crawl/temp/filtering_error_{batch_num}.png"
                                await page.screenshot(path=screenshot_path)
                                print(f"  스크린샷 저장: {screenshot_path}", flush=True)
                            except:
                                print(f"  (스크린샷 저장 실패)", flush=True)

                            # Fallback
                            print(f"\n  → Fallback: 기본 셀렉터 사용...", flush=True)
                            product_links = await page.query_selector_all('a[class*="ProductCard_link"]')
                            print(f"  → Fallback 결과: {len(product_links)}개 발견", flush=True)
                    else:
                        # [OK] v1.5.7+ 두 번째 배치부터도 필터링된 상품만 사용
                        # [OK] v1.5.9+ "FOR YOU 연관 추천" 섹션 제외 (aria-labelledby 체크)
                        print(f"\n[필터링] 배치 {batch_num} - 새로운 상품 필터링 중...", flush=True)

                        # 스크롤 후 새로운 상품 필터링
                        new_filtered = await page.evaluate('''() => {
                            const sort = document.querySelector('#product-sort-address-container');
                            if (!sort) return {newFiltered: 0, newRecommendations: 0};

                            const sortY = sort.getBoundingClientRect().bottom;
                            const allLinks = Array.from(document.querySelectorAll('a[class*="ProductCard_link"]'));

                            let newFilteredCount = 0;
                            let newRecommendationCount = 0;

                            allLinks.forEach(link => {
                                const rect = link.getBoundingClientRect();
                                const labelId = link.getAttribute('aria-labelledby') || '';
                                const isRecommendation = labelId.includes('related_recommend_product_information');

                                // 아직 필터링 안 된 상품만 처리
                                if (!link.hasAttribute('data-filtered')) {
                                    if (rect.top > sortY && !isRecommendation) {
                                        link.setAttribute('data-filtered', 'true');
                                        newFilteredCount++;
                                    } else if (isRecommendation) {
                                        newRecommendationCount++;
                                    }
                                }
                            });

                            return {newFiltered: newFilteredCount, newRecommendations: newRecommendationCount};
                        }''')

                        print(f"[필터링 결과] 새로 추가:", flush=True)
                        print(f"  - 정상 상품: {new_filtered['newFiltered']}개", flush=True)
                        print(f"  - FOR YOU 추천: {new_filtered['newRecommendations']}개 (제외)", flush=True)

                        product_links = await page.query_selector_all('a[data-filtered="true"]')
                        print(f"  총 필터링된 상품: {len(product_links)}개", flush=True)

                    current_total = len(product_links)

                    # v1.7.3 필터링 0개 에러 처리
                    if current_total == 0:
                        print(f"\n[!!] [치명적 에러] 필터링된 상품이 0개입니다!", flush=True)
                        print(f"  배치 번호: {batch_num}", flush=True)
                        print(f"  원인: 페이지 리로드 또는 필터링 실패", flush=True)
                        print(f"\n  크롤링을 종료합니다.", flush=True)
                        break

                    # 이번 라운드 범위: 아직 처리하지 않은 모든 상품 처리
                    # [FIX] v1.8.5: len() 대신 max()+1 사용 (중복 skip으로 인한 건너뛰기 방지)
                    batch_start = max(processed_indices) + 1 if processed_indices else 0
                    batch_end = current_total  # 현재 로드된 모든 상품 처리

                    # [>>] v1.8.5+ 디버그 로그 강화
                    print(f"\n[v1.8.5+] [배치 {batch_num}] 상태", flush=True)
                    print(f"  처리된 인덱스 개수: {len(processed_indices)}개", flush=True)
                    print(f"  마지막 처리 인덱스: {max(processed_indices) if processed_indices else -1}번", flush=True)
                    print(f"  다음 배치 시작: {batch_start}번 (0-based)", flush=True)
                    print(f"  다음 배치 끝: {batch_end-1}번 (0-based)", flush=True)
                    print(f"  처리할 상품: {batch_start+1}~{batch_end}번 ({batch_end - batch_start}개)", flush=True)

                    # 이번 배치 통계 추적
                    collected_in_batch = 0  # 실제 수집
                    duplicates_in_batch = 0  # 중복 skip
                    errors_in_batch = 0  # 오류 skip

                    # 현재 로드된 모든 상품 처리 (필터링으로 광고 이미 제외됨)
                    for idx in range(batch_start, batch_end):
                        # 목표 개수 도달 체크
                        if self.product_count and collected_count >= self.product_count:
                            print(f"\n목표 개수 도달! {collected_count}개 수집 완료")
                            break

                        if self.should_stop:
                            break

                        # [XX] v1.5.7+ 하드코딩된 "첫 14개 건너뛰기" 제거
                        # JavaScript 필터링으로 이미 추천순 아래만 선택됨

                        # 이미 처리한 상품은 건너뛰기
                        if idx in processed_indices:
                            continue

                        try:
                            # [OK] v1.5.7+ 필터링된 상품만 가져오기
                            fresh_links = await page.query_selector_all('a[data-filtered="true"]')
                            if idx >= len(fresh_links):
                                print(f"[{idx+1}번] 상품 인덱스 초과 - SKIP")
                                processed_indices.add(idx)
                                continue

                            product = fresh_links[idx]

                            # 🚀 최적화: 클릭 전 중복 체크
                            if self.save_to_db and self.db and self.db_connected:
                                try:
                                    # URL에서 product_id 추출
                                    product_url = await product.get_attribute('href')
                                    if product_url:
                                        product_id = self.db.extract_product_id(product_url)
                                        print(f"[{idx+1}번] 중복 체크 중... (ID: {product_id[:30]}...)", flush=True)

                                        # DB 중복 체크
                                        if self.db.is_duplicate_product(product_id, {}):
                                            self.skipped_count += 1
                                            duplicates_in_batch += 1  # 배치 중복 카운트
                                            print(f"  └─> ✓ DB에 이미 존재 - SKIP", flush=True)

                                            # 🧹 Sliding Window: 오래된 오버레이 제거
                                            if idx > self.OVERLAY_WINDOW:
                                                old_idx = idx - self.OVERLAY_WINDOW - 1
                                                await page.evaluate(f'''() => {{
                                                    const oldOverlay = document.getElementById('product-overlay-{old_idx}');
                                                    if (oldOverlay) {{
                                                        oldOverlay.remove();
                                                    }}
                                                }}''')

                                            # 회색 테두리 (중복 Skip)
                                            await page.evaluate(f'''(index) => {{
                                                const links = document.querySelectorAll('a[data-filtered="true"]');
                                                const link = links[index];
                                                if (link) {{
                                                    link.style.border = '5px solid #888888';
                                                    link.style.boxShadow = '0 0 20px #888888';

                                                    const overlay = document.createElement('div');
                                                    overlay.id = 'product-overlay-' + index;
                                                    overlay.style.cssText = `
                                                        position: absolute;
                                                        top: 0;
                                                        left: 0;
                                                        background: rgba(136, 136, 136, 0.9);
                                                        color: white;
                                                        padding: 10px;
                                                        font-size: 20px;
                                                        font-weight: bold;
                                                        z-index: 10000;
                                                        pointer-events: none;
                                                    `;
                                                    overlay.textContent = '[{idx+1}번] SKIP - 중복';
                                                    link.appendChild(overlay);

                                                    link.scrollIntoView({{ block: 'center', behavior: 'smooth' }});
                                                }}
                                            }}''', idx)
                                            await asyncio.sleep(0.3)

                                            processed_indices.add(idx)
                                            continue
                                        else:
                                            print(f"  └─> ✓ 신규 상품 - 수집 진행", flush=True)
                                except Exception as e:
                                    print(f"[{idx+1}번] 중복 체크 오류: {str(e)[:50]} - 수집 진행", flush=True)

                            # 여기까지 왔다는 것은 실제로 처리할 상품
                            processed_indices.add(idx)

                            # 🧹 Sliding Window: 오래된 오버레이 제거 (메모리 최적화)
                            if idx > self.OVERLAY_WINDOW:
                                old_idx = idx - self.OVERLAY_WINDOW - 1
                                await page.evaluate(f'''() => {{
                                    const oldOverlay = document.getElementById('product-overlay-{old_idx}');
                                    if (oldOverlay) {{
                                        oldOverlay.remove();
                                        console.log('[Overlay] #{old_idx+1}번 오버레이 제거 (Sliding Window)');
                                    }}
                                }}''')

                            # 🎨 시각적 피드백: 노란 테두리 (클릭 준비)
                            print(f"[{idx+1}번] 클릭 준비 중...", flush=True)
                            await page.evaluate(f'''(index) => {{
                                const links = document.querySelectorAll('a[data-filtered="true"]');
                                const link = links[index];
                                if (link) {{
                                    // 노란 테두리 + 오버레이 텍스트
                                    link.style.border = '5px solid #FFD700';
                                    link.style.boxShadow = '0 0 20px #FFD700';
                                    link.style.position = 'relative';

                                    // 상품 번호 오버레이
                                    const overlay = document.createElement('div');
                                    overlay.id = 'product-overlay-' + index;
                                    overlay.style.cssText = `
                                        position: absolute;
                                        top: 0;
                                        left: 0;
                                        background: rgba(255, 215, 0, 0.9);
                                        color: black;
                                        padding: 10px;
                                        font-size: 20px;
                                        font-weight: bold;
                                        z-index: 10000;
                                        pointer-events: none;
                                    `;
                                    overlay.textContent = '[{idx+1}번] 클릭 준비 중...';
                                    link.appendChild(overlay);

                                    link.scrollIntoView({{ block: 'center', behavior: 'smooth' }});
                                }}
                            }}''', idx)
                            await asyncio.sleep(0.5)

                            # 🎨 빨간 테두리 (클릭 진행)
                            print(f"[{idx+1}번] 클릭 진행 중...", flush=True)
                            await page.evaluate(f'''(index) => {{
                                const links = document.querySelectorAll('a[data-filtered="true"]');
                                const link = links[index];
                                if (link) {{
                                    link.style.border = '5px solid #FF0000';
                                    link.style.boxShadow = '0 0 20px #FF0000';

                                    const overlay = document.getElementById('product-overlay-' + index);
                                    if (overlay) {{
                                        overlay.style.background = 'rgba(255, 0, 0, 0.9)';
                                        overlay.style.color = 'white';
                                        overlay.textContent = '[{idx+1}번] 클릭 중...';
                                    }}
                                }}
                            }}''', idx)

                            await product.click(timeout=10000)
                            await asyncio.sleep(3)

                            # 새 탭 찾기
                            all_pages = context.pages
                            if len(all_pages) <= 1:
                                errors_in_batch += 1  # 오류 카운트
                                print(f"[{idx+1}번] 탭 열림 실패 - SKIP", flush=True)
                                # 회색 테두리 (Skip)
                                await page.evaluate(f'''(index) => {{
                                    const links = document.querySelectorAll('a[data-filtered="true"]');
                                    const link = links[index];
                                    if (link) {{
                                        link.style.border = '5px solid #888888';
                                        link.style.boxShadow = '0 0 20px #888888';

                                        const overlay = document.getElementById('product-overlay-' + index);
                                        if (overlay) {{
                                            overlay.style.background = 'rgba(136, 136, 136, 0.9)';
                                            overlay.style.color = 'white';
                                            overlay.textContent = '[{idx+1}번] SKIP - 탭 열림 실패';
                                        }}
                                    }}
                                }}''', idx)
                                await asyncio.sleep(0.5)
                                continue

                            detail_page = all_pages[-1]
                            await detail_page.wait_for_load_state('domcontentloaded')
                            await asyncio.sleep(2)  # 1초 → 2초 (페이지 로드 대기)

                            # 상품 정보 수집
                            product_data = await self._collect_product_info(detail_page)

                            if product_data and product_data.get('product_name'):
                                self.products_data.append(product_data)
                                collected_count += 1
                                collected_in_batch += 1  # 이번 배치에서 수집한 개수

                                # 🎨 초록 테두리 (수집 완료)
                                print(f"[{idx+1}번] 수집 완료 - {product_data.get('product_name', '')[:30]}...", flush=True)
                                await page.evaluate(f'''(index) => {{
                                    const links = document.querySelectorAll('a[data-filtered="true"]');
                                    const link = links[index];
                                    if (link) {{
                                        link.style.border = '5px solid #00FF00';
                                        link.style.boxShadow = '0 0 20px #00FF00';

                                        const overlay = document.getElementById('product-overlay-' + index);
                                        if (overlay) {{
                                            overlay.style.background = 'rgba(0, 255, 0, 0.9)';
                                            overlay.style.color = 'black';
                                            overlay.textContent = '[{idx+1}번] ✓ 수집 완료';
                                        }}
                                    }}
                                }}''', idx)
                                await asyncio.sleep(0.3)

                                # 메모리 최적화: 1000개 초과 시 오래된 데이터 정리 (마지막 500개만 유지)
                                if len(self.products_data) > 1000:
                                    self.products_data = self.products_data[-500:]

                                # 즉시 DB 저장 (세션 유지)
                                if self.save_to_db and self.db and self.db_connected:
                                    try:
                                        result = self.db.save_product(self.category_name, product_data)
                                        if result == 'saved':
                                            self.saved_count += 1
                                            product_data['_db_status'] = 'saved'
                                        elif result == 'skipped':
                                            self.skipped_count += 1
                                            product_data['_db_status'] = 'skipped'
                                    except Exception as e:
                                        product_data['_db_status'] = 'error'
                                        print(f"[{collected_count}] DB 저장 실패: {str(e)}")
                                else:
                                    product_data['_db_status'] = 'none'

                                # 간략한 진행 메시지만 출력
                                print(f"수집 중... {collected_count}개", end='\r')

                                # 50개마다 상세 테이블 출력
                                if collected_count % 50 == 0:
                                    self._print_products_table(collected_count)
                            else:
                                print(f"[{idx+1}번] 수집 실패 (상품명 없음) - SKIP")

                            # 탭 닫기
                            await detail_page.close()
                            await asyncio.sleep(0.5)

                            # [XX] scrollTo(0, 0) 제거 - 네이버 무한 스크롤 방해
                            # 탭 닫으면 자동으로 원래 페이지로 돌아오고 스크롤 위치 유지됨

                        except Exception as e:
                            errors_in_batch += 1  # 오류 카운트
                            print(f"[{idx+1}번] 오류: {str(e)[:50]} - SKIP", flush=True)
                            continue

                    # 목표 개수 도달 시 종료
                    print(f"[DEBUG] 목표 체크 - product_count={self.product_count}, collected={collected_count}")
                    if self.product_count and collected_count >= self.product_count:
                        print(f"[DEBUG] 목표 도달로 종료")
                        break

                    print(f"[DEBUG] 중지 플래그 체크 - should_stop={self.should_stop}")
                    if self.should_stop:
                        print(f"[DEBUG] 사용자 중지 요청으로 종료")
                        break

                    # 배치 처리 완료 → 스크롤하여 다음 배치 로드
                    # 조건: 모든 상품 처리 완료 (batch_end >= current_total)
                    print(f"\n[DEBUG] batch_end={batch_end}, current_total={current_total}, 조건={batch_end >= current_total}")

                    if batch_end >= current_total:
                        try:
                            # 배치 완료 상태 출력
                            total_processed = batch_end - batch_start
                            print(f"\n{'='*60}", flush=True)
                            print(f"[배치 {batch_num}] 완료 - 처리 통계", flush=True)
                            print(f"{'='*60}", flush=True)
                            print(f"  처리 범위: {batch_start+1}~{batch_end}번 (총 {total_processed}개)", flush=True)
                            print(f"  OK 신규 수집: {collected_in_batch}개", flush=True)
                            print(f"  -- 중복 Skip: {duplicates_in_batch}개", flush=True)
                            print(f"  XX 오류 Skip: {errors_in_batch}개", flush=True)
                            print(f"  >> 누적 수집: {collected_count}개", flush=True)
                            print(f"{'='*60}", flush=True)
                            print(f"\n{'='*60}", flush=True)
                            print(f"[무한 스크롤] 추가 상품 로딩 시작", flush=True)
                            print(f"{'='*60}", flush=True)
                            before_scroll = current_total

                            # 현재 페이지 스크롤 위치 확인
                            scroll_pos = await page.evaluate('window.pageYOffset')
                            doc_height = await page.evaluate('document.body.scrollHeight')
                            print(f"[스크롤 전 상태]", flush=True)
                            print(f"  현재 필터링된 상품: {current_total}개", flush=True)
                            print(f"  스크롤 위치: {scroll_pos}px", flush=True)
                            print(f"  문서 높이: {doc_height}px", flush=True)

                            # [OK] 페이지 안정화 대기 (DOM 변경 완료)
                            await asyncio.sleep(2)

                            # [OK] v1.5.7+ 조금씩만 스크롤 (페이지 재정렬 방지)
                            print(f"\n[스크롤 실행] 800px씩 조금씩 스크롤 (페이지 재정렬 방지)", flush=True)

                            # 현재 스크롤 위치에서 800px만 더 스크롤 (조금씩!)
                            scroll_result = await page.evaluate('''() => {
                                const currentScroll = window.pageYOffset;
                                const newScroll = currentScroll + 800;  // 조금씩만 스크롤
                                window.scrollTo(0, newScroll);
                                return {
                                    before: currentScroll,
                                    after: newScroll,
                                    scrollHeight: document.body.scrollHeight
                                };
                            }''')

                            print(f"  스크롤: {scroll_result['before']}px → {scroll_result['after']}px (+800px)", flush=True)
                            print(f"  대기 중... (1.5초)", flush=True)
                            await asyncio.sleep(1.5)

                            # 스크롤 후 위치 확인
                            await asyncio.sleep(1)
                            scroll_pos_after = await page.evaluate('window.pageYOffset')
                            doc_height_after = await page.evaluate('document.body.scrollHeight')
                            print(f"[스크롤 후 상태]", flush=True)
                            print(f"  스크롤 위치: {scroll_pos_after}px", flush=True)
                            if doc_height_after > doc_height:
                                print(f"  문서 높이: {doc_height_after}px (↑ {doc_height_after - doc_height}px 증가)", flush=True)
                            else:
                                print(f"  문서 높이: {doc_height_after}px (변화 없음)", flush=True)

                            # 재시도 로직: 최대 3번까지 확인 (각 5초 대기)
                            print(f"\n[새 상품 대기] 최대 3회 확인 (각 5초 대기)", flush=True)
                            loaded = False
                            for attempt in range(3):
                                print(f"\n  [시도 {attempt+1}/3] 5초 대기 후 상품 확인...", flush=True)
                                await asyncio.sleep(5)  # 5초 대기

                                # [OK] v1.5.9+ 스크롤 후 새로운 상품 필터링 (추천 제외)
                                filter_result = await page.evaluate('''() => {
                                    const sort = document.querySelector('#product-sort-address-container');
                                    if (!sort) return {newFiltered: 0, newRecommendations: 0, totalLinks: 0};

                                    const sortY = sort.getBoundingClientRect().bottom;
                                    const allLinks = Array.from(document.querySelectorAll('a[class*="ProductCard_link"]'));

                                    let newFilteredCount = 0;
                                    let newRecommendationCount = 0;

                                    allLinks.forEach(link => {
                                        const rect = link.getBoundingClientRect();
                                        const labelId = link.getAttribute('aria-labelledby') || '';
                                        const isRecommendation = labelId.includes('related_recommend_product_information');

                                        // 아직 필터링 안 된 상품만 처리
                                        if (!link.hasAttribute('data-filtered')) {
                                            if (rect.top > sortY && !isRecommendation) {
                                                link.setAttribute('data-filtered', 'true');
                                                newFilteredCount++;
                                            } else if (isRecommendation) {
                                                newRecommendationCount++;
                                            }
                                        }
                                    });

                                    return {
                                        newFiltered: newFilteredCount,
                                        newRecommendations: newRecommendationCount,
                                        totalLinks: allLinks.length
                                    };
                                }''')

                                # [OK] 필터링된 상품만 카운트
                                product_links_after = await page.query_selector_all('a[data-filtered="true"]')
                                after_scroll = len(product_links_after)

                                print(f"  [필터링 결과]", flush=True)
                                print(f"    전체 링크: {filter_result['totalLinks']}개", flush=True)
                                print(f"    새로 필터링: {filter_result['newFiltered']}개", flush=True)
                                print(f"    새로운 추천: {filter_result['newRecommendations']}개 (제외)", flush=True)
                                print(f"    현재 총 필터링: {after_scroll}개 (이전: {before_scroll}개)", flush=True)

                                if after_scroll > before_scroll:
                                    scroll_count += 1
                                    increase = after_scroll - before_scroll
                                    print(f"\n  [OK] 새 상품 발견! {before_scroll}개 → {after_scroll}개 (새로 로드: {increase}개)", flush=True)
                                    print(f"  [스크롤 #{scroll_count}] 성공 - 다음 배치로 진행", flush=True)

                                    # 스크롤 시마다 누적 통계 출력
                                    print(f"\n  [통계] 누적 현황", flush=True)
                                    print(f"    OK 총 신규 수집: {collected_count}개", flush=True)
                                    print(f"    -- 총 중복 Skip: {self.skipped_count}개", flush=True)
                                    print(f"    DB 저장 완료: {self.saved_count}개", flush=True)

                                    consecutive_failures = 0  # 성공 시 실패 카운트 리셋
                                    loaded = True
                                    break
                                elif attempt < 2:
                                    print(f"  [..] 아직 새 상품 없음 - 다시 대기 ({(attempt+1)*5}초 경과)", flush=True)

                            if not loaded:
                                consecutive_failures += 1  # 실패 카운트 증가

                                # v1.8.1 단순화: 3회 연속 실패 시 종료 (오버엔지니어링 제거)
                                print(f"\n[정지] 새 상품 없음 - 연속 실패: {consecutive_failures}회 / 3회", flush=True)

                                if consecutive_failures >= 3:
                                    print(f"\n[XX] 3회 연속 실패 - 크롤링 종료", flush=True)
                                    print(f"[i] 무한 스크롤 끝 도달 또는 네이버 서버가 추가 상품을 제공하지 않음", flush=True)
                                    break
                                else:
                                    print(f"  계속 시도 ({consecutive_failures}/3회)...", flush=True)
                                    # 다음 배치로 진행 (다시 스크롤 시도)
                        except Exception as e:
                            print(f"\n[배치 {batch_num}] 스크롤 실패: {str(e)[:50]}")
                            print(f"브라우저/페이지가 닫혔거나 네트워크 오류 발생. 수집 종료.")
                            break
                    else:
                        # 아직 처리할 상품이 남음 (스크롤 불필요)
                        print(f"[DEBUG] 스크롤 불필요 - batch_end({batch_end}) < current_total({current_total})")
                        print(f"[배치 {batch_num}] 처리 완료 - 다음 배치로 진행 (아직 {current_total - batch_end}개 남음)")
                        continue

                # 최종 테이블 출력 (50의 배수가 아닌 경우)
                if len(self.products_data) % 50 != 0:
                    self._print_products_table(len(self.products_data), final=True)
                else:
                    print(f"\n\n수집 완료! 총 {len(self.products_data)}개 → DB 저장됨")

            finally:
                # DB 연결 종료
                if self.db_connected and self.db:
                    try:
                        self.db.close()
                        print("[DB] 연결 종료")
                    except:
                        pass
                await browser.close()

            return self.products_data

    def _print_products_table(self, count: int, final: bool = False):
        """50개 단위로 수집된 모든 상품 정보를 테이블로 출력"""
        print("\n")  # 진행 메시지 줄바꿈

        # 헤더
        if final:
            print("=" * 61)
            print(f"{'[완료] 수집 완료 - 전체 상품 목록':^55}")
            print("=" * 61)
        else:
            print("=" * 61)
            print(f"{'[진행중] 수집 현황 (' + str(count) + '개 완료)':^55}")
            print("=" * 61)

        # 통계 정보
        elapsed = time.time() - self.start_time
        elapsed_min = int(elapsed // 60)
        elapsed_sec = int(elapsed % 60)
        speed = count / (elapsed / 60) if elapsed > 0 else 0

        if self.save_to_db:
            print(f"  총 수집      : {count}개")
            print(f"  DB 저장      : {self.saved_count}개 ({self.saved_count/count*100:.1f}%)")
            print(f"  중복 스킵    : {self.skipped_count}개 ({self.skipped_count/count*100:.1f}%)")
        else:
            print(f"  총 수집      : {count}개")

        # 가격 통계
        prices = [p.get('price') for p in self.products_data if p.get('price')]
        if prices:
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            print(f"  평균 가격    : {avg_price:,.0f}원")
            print(f"  가격 범위    : {min_price:,}원 ~ {max_price:,}원")

        # 브랜드/태그 통계
        brands = [p for p in self.products_data if p.get('brand_name')]
        tags = [p.get('search_tags', []) for p in self.products_data]
        avg_tags = sum(len(t) for t in tags) / len(tags) if tags else 0

        print(f"  브랜드 수집  : {len(brands)}개 ({len(brands)/count*100:.1f}%)")
        print(f"  태그 평균    : {avg_tags:.1f}개/상품")
        print(f"  소요 시간    : {elapsed_min}분 {elapsed_sec}초")
        print(f"  수집 속도    : {speed:.1f}개/분")
        print("=" * 61)

        # 상품 테이블
        print("\n  # | 상품명 (35자)                      | 가격      | 브랜드     | 태그 | DB ")
        print("-" * 61)

        # 마지막 50개 (또는 전체) 출력
        start_idx = max(0, len(self.products_data) - 50)
        for i, product in enumerate(self.products_data[start_idx:], start=start_idx + 1):
            name = product.get('product_name', 'N/A')[:35]
            price = product.get('price')
            price_str = f"{price:>6,}원" if price else "   N/A"
            brand = (product.get('brand_name') or '-')[:10]
            tags_count = len(product.get('search_tags', []))
            db_status = product.get('_db_status', 'none')

            # DB 상태 기호 (명확한 표시)
            if db_status == 'saved':
                db_icon = 'OK'
            elif db_status == 'skipped':
                db_icon = 'DUP'
            elif db_status == 'error':
                db_icon = 'ERR'
            else:
                db_icon = 'N/A'

            print(f"{i:3d} | {name:35s} | {price_str} | {brand:10s} | {tags_count:2d}개 | {db_icon:3s}")

        print("=" * 61)
        print()

    async def _collect_product_info(self, page) -> Optional[Dict]:
        """상품 정보 수집 (13개 필드)"""
        data = {}

        try:
            # 1. product_id (URL에서 추출)
            url = page.url
            match = re.search(r'/products/(\d+)', url)
            data['product_id'] = match.group(1) if match else None

            # 2. category_name
            data['category_name'] = self.category_name

            # 3. product_name
            elem = await page.query_selector('h3.DCVBehA8ZB')
            data['product_name'] = await elem.inner_text() if elem else None

            # 4. brand_name (테이블에서) - 스크롤 없이 바로 수집
            brand_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('td, th');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    if (text.trim() === '브랜드') {
                        const nextTd = elem.nextElementSibling;
                        if (nextTd) {
                            const brandValue = nextTd.textContent.trim();
                            if (brandValue && brandValue.length < 50) {
                                return brandValue;
                            }
                        }
                    }
                }
                return null;
            }''')
            data['brand_name'] = brand_result

            # 5. price
            elem = await page.query_selector('strong.Izp3Con8h8')
            if elem:
                price_text = await elem.inner_text()
                price_clean = re.sub(r'[^\d]', '', price_text)
                data['price'] = int(price_clean) if price_clean else None
            else:
                data['price'] = None

            # 6. discount_rate (JavaScript evaluate)
            discount_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    if (text.includes('%') && text.length < 20) {
                        const match = text.match(/(\\d+)%/);
                        if (match && elem.children.length <= 1) {
                            return match[1];
                        }
                    }
                }
                return null;
            }''')
            data['discount_rate'] = int(discount_result) if discount_result else None

            # 7. review_count
            review_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    if (text.includes('리뷰') && text.length < 20) {
                        const match = text.match(/리뷰\\s*(\\d+)/);
                        if (match) {
                            return match[1];
                        }
                    }
                }
                return null;
            }''')
            data['review_count'] = int(review_result) if review_result else 0

            # 8. rating
            rating_result = await page.evaluate('''() => {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent || '';
                    if ((text.includes('평점') || text.includes('별점')) && text.length < 30) {
                        const match = text.match(/(\\d+\\.\\d+)/);
                        if (match) {
                            return parseFloat(match[1]);
                        }
                    }
                }
                return null;
            }''')
            data['rating'] = rating_result

            # 9. search_tags (최적화: 2번만 스크롤)
            # 30% 스크롤 (brand_name 위치)
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.3)')
            await asyncio.sleep(1.5)

            # 50% 스크롤 (search_tags 위치)
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.5)')
            await asyncio.sleep(2.0)

            # 태그 수집
            all_tags_found = set()
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

            data['search_tags'] = list(all_tags_found)

            # 10. product_url
            data['product_url'] = url

            # 11. thumbnail_url
            elem = await page.query_selector('img[class*="image"]')
            data['thumbnail_url'] = await elem.get_attribute('src') if elem else None

            # 12, 13. 타임스탬프
            now = datetime.now()
            data['crawled_at'] = now.isoformat()
            data['updated_at'] = now.isoformat()

            return data

        except Exception as e:
            print(f"   수집 오류: {str(e)[:50]}")
            return None


if __name__ == "__main__":
    async def test():
        crawler = SimpleCrawler(product_count=3, headless=False)
        products = await crawler.crawl()

        print("\n=== 수집 결과 ===")
        for i, p in enumerate(products, 1):
            print(f"{i}. {p.get('product_name', 'N/A')[:50]}")
            print(f"   가격: {p.get('price', 'N/A'):,}원")
            print(f"   브랜드: {p.get('brand_name', 'N/A')}")
            print(f"   태그: {len(p.get('search_tags', []))}개")

    asyncio.run(test())
