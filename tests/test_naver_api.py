#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 쇼핑 검색 API 테스트
실제로 API가 제공하는 데이터 확인
"""

import requests
import json
from datetime import datetime

# 네이버 API 정보 (테스트용)
CLIENT_ID = "YOUR_CLIENT_ID"  # 실제 ID로 교체 필요
CLIENT_SECRET = "YOUR_CLIENT_SECRET"  # 실제 Secret으로 교체 필요

def test_naver_shopping_api():
    """네이버 쇼핑 API 테스트"""

    # API 엔드포인트
    url = "https://openapi.naver.com/v1/search/shop.json"

    # 검색 키워드
    query = "노트북"

    # 요청 파라미터
    params = {
        "query": query,
        "display": 5,  # 검색 결과 출력 개수
        "start": 1,    # 검색 시작 위치
        "sort": "sim"  # 정렬 방법 (sim: 유사도순, date: 날짜순, asc: 가격오름차순, dsc: 가격내림차순)
    }

    # 헤더 설정
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }

    print("=" * 80)
    print("네이버 쇼핑 검색 API 테스트")
    print("=" * 80)
    print(f"검색어: {query}")
    print(f"요청 URL: {url}")
    print(f"요청 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)

    try:
        # API 호출
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()

            # 응답 구조 확인
            print("\n### API 응답 구조 ###")
            print(f"전체 검색 결과 수: {data.get('total', 0):,}")
            print(f"현재 시작 위치: {data.get('start', 0)}")
            print(f"출력 개수: {data.get('display', 0)}")
            print(f"응답 생성 시간: {data.get('lastBuildDate', '')}")

            # 상품 정보 확인
            items = data.get('items', [])
            print(f"\n### 상품 정보 ({len(items)}개) ###")

            if items:
                # 첫 번째 상품 상세 분석
                first_item = items[0]
                print("\n[첫 번째 상품 상세 정보]")
                print("-" * 40)

                # 모든 필드 출력
                for key, value in first_item.items():
                    print(f"  {key}: {value}")

                print("\n[API가 제공하는 필드 목록]")
                print("-" * 40)
                fields = list(first_item.keys())
                for field in fields:
                    print(f"  - {field}")

                # 모든 상품 간단 요약
                print("\n[전체 상품 요약]")
                print("-" * 40)
                for idx, item in enumerate(items, 1):
                    print(f"\n{idx}. {item.get('title', 'N/A')}")
                    print(f"   최저가: {item.get('lprice', 'N/A'):,}원")
                    print(f"   최고가: {item.get('hprice', 'N/A'):,}원")
                    print(f"   쇼핑몰: {item.get('mallName', 'N/A')}")
                    print(f"   브랜드: {item.get('brand', 'N/A')}")

            # 전체 응답 저장
            with open('tests/api_response.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n전체 응답이 'tests/api_response.json'에 저장되었습니다.")

        else:
            print(f"API 호출 실패: {response.status_code}")
            print(f"오류 메시지: {response.text}")

    except Exception as e:
        print(f"오류 발생: {str(e)}")

def compare_api_vs_crawling():
    """API와 크롤링 차이점 비교"""

    print("\n" + "=" * 80)
    print("네이버 쇼핑 API vs 웹 크롤링 비교")
    print("=" * 80)

    api_fields = [
        "title (상품명)",
        "link (상품 링크)",
        "image (이미지 URL)",
        "lprice (최저가)",
        "hprice (최고가)",
        "mallName (쇼핑몰명)",
        "productId (상품ID)",
        "productType (상품 타입)",
        "brand (브랜드)",
        "maker (제조사)",
        "category1~4 (카테고리)"
    ]

    crawling_fields = [
        "상품명 (상세)",
        "실제 판매가격",
        "할인율",
        "리뷰 개수",
        "평점 (별점)",
        "배송 정보",
        "쿠폰/혜택 정보",
        "판매자별 가격 비교",
        "상품 옵션",
        "재고 상태",
        "인기도/판매량",
        "상세 이미지",
        "상품 설명",
        "구매 가능 여부",
        "찜 개수",
        "문의 내용",
        "상세 스펙",
        "연관 상품",
        "베스트 순위",
        "시간별 가격 변동"
    ]

    print("\n### API로 얻을 수 있는 정보 ###")
    for field in api_fields:
        print(f"  ✅ {field}")

    print("\n### 크롤링으로만 얻을 수 있는 정보 ###")
    for field in crawling_fields:
        print(f"  ❌ {field} (API 제공 안함)")

    print("\n### 결론 ###")
    print("- API는 기본적인 상품 정보만 제공")
    print("- 실제 판매/마케팅에 필요한 상세 정보는 크롤링 필요")
    print("- 실시간 재고, 할인, 리뷰 등 중요 정보는 API로 불가능")

if __name__ == "__main__":
    # API 테스트 (CLIENT_ID와 SECRET 필요)
    # test_naver_shopping_api()

    # API vs 크롤링 비교
    compare_api_vs_crawling()