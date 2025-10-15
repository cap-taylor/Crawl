"""
셀렉터 Helper 함수
네이버의 난독화된 클래스명 대응을 위한 다중 fallback 시스템
"""
from typing import List, Optional, Union
from playwright.async_api import Page, ElementHandle
import re


class SelectorHelper:
    """셀렉터 시도 및 디버깅을 위한 Helper 클래스"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.selector_stats = {}  # 셀렉터 성공/실패 통계

    async def try_selectors(
        self,
        page: Page,
        selectors: List[str],
        field_name: str = "unknown",
        multiple: bool = False
    ) -> Optional[Union[ElementHandle, List[ElementHandle]]]:
        """
        여러 셀렉터를 순차적으로 시도하여 첫 번째 성공한 결과 반환

        Args:
            page: Playwright Page 객체
            selectors: 시도할 셀렉터 리스트 (우선순위 순)
            field_name: 디버깅용 필드명
            multiple: True면 query_selector_all, False면 query_selector

        Returns:
            찾은 Element(s) 또는 None
        """
        for idx, selector in enumerate(selectors, 1):
            try:
                if multiple:
                    result = await page.query_selector_all(selector)
                    if result:
                        self._log_success(field_name, selector, idx, len(result))
                        return result
                else:
                    result = await page.query_selector(selector)
                    if result:
                        self._log_success(field_name, selector, idx)
                        return result

                if self.debug:
                    self._log_fail(field_name, selector, idx)

            except Exception as e:
                if self.debug:
                    print(f"   [셀렉터 오류] {field_name} - {selector}: {str(e)[:50]}")

        # 모든 셀렉터 실패
        self._log_all_fail(field_name)
        return None

    async def try_selectors_from_element(
        self,
        element: ElementHandle,
        selectors: List[str],
        field_name: str = "unknown",
        multiple: bool = False
    ) -> Optional[Union[ElementHandle, List[ElementHandle]]]:
        """
        특정 Element 내부에서 셀렉터 시도

        Args:
            element: 부모 Element
            selectors: 시도할 셀렉터 리스트
            field_name: 디버깅용 필드명
            multiple: True면 모든 결과, False면 첫 번째만

        Returns:
            찾은 Element(s) 또는 None
        """
        for idx, selector in enumerate(selectors, 1):
            try:
                if multiple:
                    result = await element.query_selector_all(selector)
                    if result:
                        self._log_success(field_name, selector, idx, len(result))
                        return result
                else:
                    result = await element.query_selector(selector)
                    if result:
                        self._log_success(field_name, selector, idx)
                        return result

                if self.debug:
                    self._log_fail(field_name, selector, idx)

            except Exception as e:
                if self.debug:
                    print(f"   [셀렉터 오류] {field_name} - {selector}: {str(e)[:50]}")

        self._log_all_fail(field_name)
        return None

    async def find_by_text_then_next(
        self,
        page: Page,
        text: str,
        next_selector: str,
        field_name: str = "unknown"
    ) -> Optional[ElementHandle]:
        """
        텍스트를 찾은 후 다음 요소를 찾는 구조 기반 셀렉터

        예: "관련 태그" 텍스트 찾기 → 다음 ul 요소 찾기

        Args:
            page: Playwright Page 객체
            text: 찾을 텍스트
            next_selector: 다음에 찾을 셀렉터 (예: "ul", "div")
            field_name: 디버깅용 필드명

        Returns:
            찾은 Element 또는 None
        """
        try:
            # 텍스트가 포함된 요소 찾기
            text_elem = await page.query_selector(f'text="{text}"')
            if not text_elem:
                if self.debug:
                    print(f"   [구조 셀렉터] {field_name} - 텍스트 '{text}' 못 찾음")
                return None

            # 부모 요소 찾기
            parent = await text_elem.evaluate_handle('el => el.parentElement')

            # 다음 요소 찾기
            next_elem = await parent.query_selector(next_selector)
            if next_elem:
                if self.debug:
                    print(f"   [구조 셀렉터] {field_name} - 성공 ('{text}' → {next_selector})")
                return next_elem
            else:
                if self.debug:
                    print(f"   [구조 셀렉터] {field_name} - '{text}' 찾았지만 {next_selector} 없음")
                return None

        except Exception as e:
            if self.debug:
                print(f"   [구조 셀렉터 오류] {field_name}: {str(e)[:50]}")
            return None

    async def find_breadcrumb_from_home(
        self,
        page: Page,
        field_name: str = "카테고리 경로"
    ) -> Optional[List[ElementHandle]]:
        """
        구조 기반 breadcrumb 수집: '홈' 텍스트로 ul 찾기 → 모든 li > a 수집

        네이버의 난독화 클래스명에 영향받지 않는 가장 안정적인 방법

        Args:
            page: Playwright Page 객체
            field_name: 디버깅용 필드명

        Returns:
            breadcrumb 링크 리스트 또는 None
        """
        try:
            # Locator API 사용 (JSHandle 오류 해결)
            home_link = page.locator('a:has-text("홈")').first

            # 부모 ul 찾기 (XPath 사용)
            ul_locator = home_link.locator('xpath=ancestor::ul[1]')

            # ul 내의 모든 li a 찾기
            breadcrumb_locator = ul_locator.locator('li a')

            # ElementHandle로 변환
            count = await breadcrumb_locator.count()
            if count == 0:
                if self.debug:
                    print(f"   [구조 기반] {field_name} - breadcrumb 링크 없음")
                return None

            breadcrumb_links = []
            for i in range(count):
                elem = await breadcrumb_locator.nth(i).element_handle()
                if elem:
                    breadcrumb_links.append(elem)

            if breadcrumb_links:
                if self.debug:
                    print(f"   [구조 기반 성공] {field_name} - {len(breadcrumb_links)}개 링크 발견")
                return breadcrumb_links
            else:
                if self.debug:
                    print(f"   [구조 기반] {field_name} - ElementHandle 변환 실패")
                return None

        except Exception as e:
            if self.debug:
                print(f"   [구조 기반 오류] {field_name}: {str(e)[:50]}")
            return None

    async def extract_text(
        self,
        element: Optional[ElementHandle],
        field_name: str = "unknown",
        clean: bool = True
    ) -> Optional[str]:
        """
        Element에서 텍스트 추출

        Args:
            element: Element 또는 None
            field_name: 디버깅용 필드명
            clean: True면 공백 제거, 개행 제거, 연속 공백 정리

        Returns:
            추출된 텍스트 또는 None
        """
        if not element:
            return None

        try:
            text = await element.inner_text()
            if clean:
                text = text.strip()
                text = text.replace('\n', ' ')  # 개행 문자 → 공백
                text = ' '.join(text.split())  # 연속 공백 제거

            if self.debug and text:
                print(f"   [텍스트 추출] {field_name}: {text[:50]}")

            return text if text else None

        except Exception as e:
            if self.debug:
                print(f"   [텍스트 추출 오류] {field_name}: {str(e)[:30]}")
            return None

    async def extract_attribute(
        self,
        element: Optional[ElementHandle],
        attribute: str,
        field_name: str = "unknown"
    ) -> Optional[str]:
        """
        Element에서 속성 값 추출

        Args:
            element: Element 또는 None
            attribute: 속성명 (예: "href", "src")
            field_name: 디버깅용 필드명

        Returns:
            추출된 속성 값 또는 None
        """
        if not element:
            return None

        try:
            value = await element.get_attribute(attribute)

            if self.debug and value:
                print(f"   [속성 추출] {field_name} ({attribute}): {value[:50]}")

            return value

        except Exception as e:
            if self.debug:
                print(f"   [속성 추출 오류] {field_name}: {str(e)[:30]}")
            return None

    def clean_price(self, price_text: Optional[str]) -> Optional[int]:
        """
        가격 텍스트 정리 (쉼표, '원' 제거 → 정수 변환)

        Args:
            price_text: "69,000원" 같은 텍스트

        Returns:
            정수 가격 또는 None
        """
        if not price_text:
            return None

        try:
            # 숫자만 추출
            numbers = re.findall(r'\d+', price_text.replace(',', ''))
            if numbers:
                return int(numbers[0])
            return None
        except:
            return None

    def clean_discount_rate(self, discount_text: Optional[str]) -> Optional[int]:
        """
        할인율 텍스트 정리 ("5%" → 5)

        Args:
            discount_text: "5%" 같은 텍스트

        Returns:
            정수 할인율 또는 None
        """
        if not discount_text:
            return None

        try:
            match = re.search(r'(\d+)%', discount_text)
            if match:
                return int(match.group(1))
            return None
        except:
            return None

    def clean_review_count(self, review_text: Optional[str]) -> Optional[int]:
        """
        리뷰 수 텍스트 정리 ("리뷰 1,444" → 1444)

        Args:
            review_text: "리뷰 1,444" 같은 텍스트

        Returns:
            정수 리뷰 수 또는 None
        """
        if not review_text:
            return None

        try:
            numbers = re.findall(r'\d+', review_text.replace(',', ''))
            if numbers:
                return int(numbers[0])
            return None
        except:
            return None

    def clean_rating(self, rating_text: Optional[str]) -> Optional[float]:
        """
        평점 텍스트 정리 ("4.5" → 4.5)

        Args:
            rating_text: "4.5" 같은 텍스트

        Returns:
            실수 평점 또는 None
        """
        if not rating_text:
            return None

        try:
            match = re.search(r'(\d+\.\d+|\d+)', rating_text)
            if match:
                return float(match.group(1))
            return None
        except:
            return None

    # 로그 함수들 (내부용)
    def _log_success(self, field_name: str, selector: str, attempt: int, count: int = 1):
        """성공 로그"""
        # 통계 업데이트
        if field_name not in self.selector_stats:
            self.selector_stats[field_name] = {'success': 0, 'fail': 0, 'last_selector': None}
        self.selector_stats[field_name]['success'] += 1
        self.selector_stats[field_name]['last_selector'] = selector

        if self.debug:
            if count > 1:
                print(f"   [셀렉터 {attempt}번째 성공] {field_name}: {selector} ({count}개)")
            else:
                print(f"   [셀렉터 {attempt}번째 성공] {field_name}: {selector}")

    def _log_fail(self, field_name: str, selector: str, attempt: int):
        """실패 로그"""
        print(f"   [셀렉터 {attempt}번째 실패] {field_name}: {selector}")

    def _log_all_fail(self, field_name: str):
        """전체 실패 로그"""
        # 통계 업데이트
        if field_name not in self.selector_stats:
            self.selector_stats[field_name] = {'success': 0, 'fail': 0, 'last_selector': None}
        self.selector_stats[field_name]['fail'] += 1

        if self.debug:
            print(f"   [모든 셀렉터 실패] {field_name}")

    def print_stats(self):
        """셀렉터 성공/실패 통계 출력"""
        if not self.selector_stats:
            print("\n[통계] 셀렉터 사용 기록 없음")
            return

        print("\n" + "="*60)
        print("[통계] 셀렉터 성공/실패 통계")
        print("="*60)

        for field_name, stats in sorted(self.selector_stats.items()):
            success = stats['success']
            fail = stats['fail']
            total = success + fail
            rate = (success / total * 100) if total > 0 else 0

            print(f"{field_name:20s} | 성공: {success:3d} | 실패: {fail:3d} | 성공률: {rate:5.1f}%")
            if stats['last_selector']:
                print(f"  └─ 최근 사용: {stats['last_selector'][:50]}")

        print("="*60)
