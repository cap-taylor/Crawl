#!/usr/bin/env python3
"""
간소화된 로그 시스템 테스트
50개 단위 테이블 출력 확인
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
from datetime import datetime


def generate_mock_products(count=50):
    """모의 상품 데이터 생성"""
    products = []
    for i in range(1, count + 1):
        product = {
            'product_id': f'123456{i:04d}',
            'category_name': '여성의류',
            'product_name': f'테스트 상품 {i}번 - 여성용 겨울 패딩 점퍼 롱 코트',
            'brand_name': f'브랜드{i % 10}' if i % 3 != 0 else None,
            'price': 10000 + (i * 1000) % 90000,
            'discount_rate': (i % 70) if i % 5 == 0 else None,
            'review_count': i * 10,
            'rating': 4.0 + (i % 10) / 10,
            'search_tags': [f'태그{j}' for j in range(1, (i % 15) + 1)],
            'product_url': f'https://shopping.naver.com/products/{i}',
            'thumbnail_url': f'https://example.com/image{i}.jpg',
            'crawled_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            '_db_status': 'saved' if i % 10 != 0 else 'skipped'
        }
        products.append(product)
    return products


def print_products_table(products, count, start_time, saved_count, skipped_count, final=False):
    """50개 단위로 수집된 모든 상품 정보를 테이블로 출력"""
    print("\n")

    # 헤더
    if final:
        print("=" * 61)
        print(f"{'✅ 수집 완료 - 전체 상품 목록':^55}")
        print("=" * 61)
    else:
        print("=" * 61)
        print(f"{'📦 수집 현황 (' + str(count) + '개 완료)':^55}")
        print("=" * 61)

    # 통계 정보
    elapsed = time.time() - start_time
    elapsed_min = int(elapsed // 60)
    elapsed_sec = int(elapsed % 60)
    speed = count / (elapsed / 60) if elapsed > 0 else 0

    print(f"  총 수집      : {count}개")
    print(f"  DB 저장      : {saved_count}개 ({saved_count/count*100:.1f}%)")
    print(f"  중복 스킵    : {skipped_count}개 ({skipped_count/count*100:.1f}%)")

    # 가격 통계
    prices = [p.get('price') for p in products if p.get('price')]
    if prices:
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        print(f"  평균 가격    : {avg_price:,.0f}원")
        print(f"  가격 범위    : {min_price:,}원 ~ {max_price:,}원")

    # 브랜드/태그 통계
    brands = [p for p in products if p.get('brand_name')]
    tags = [p.get('search_tags', []) for p in products]
    avg_tags = sum(len(t) for t in tags) / len(tags) if tags else 0

    print(f"  브랜드 수집  : {len(brands)}개 ({len(brands)/count*100:.1f}%)")
    print(f"  태그 평균    : {avg_tags:.1f}개/상품")
    print(f"  소요 시간    : {elapsed_min}분 {elapsed_sec}초")
    print(f"  수집 속도    : {speed:.1f}개/분")
    print("=" * 61)

    # 상품 테이블
    print("\n  # | 상품명 (35자) | 가격 | 브랜드 | 태그 | DB")
    print("-" * 61)

    # 마지막 50개 출력
    start_idx = max(0, len(products) - 50)
    for i, product in enumerate(products[start_idx:], start=start_idx + 1):
        name = product.get('product_name', 'N/A')[:35]
        price = product.get('price')
        price_str = f"{price:>6,}원" if price else "   N/A"
        brand = (product.get('brand_name') or '-')[:10]
        tags_count = len(product.get('search_tags', []))
        db_status = product.get('_db_status', 'none')

        # DB 상태 기호
        if db_status == 'saved':
            db_icon = '✓'
        elif db_status == 'skipped':
            db_icon = '○'
        elif db_status == 'error':
            db_icon = '✗'
        else:
            db_icon = '-'

        print(f"{i:3d} | {name:35s} | {price_str} | {brand:10s} | {tags_count:2d}개 | {db_icon}")

    print("=" * 61)
    print()


def test_log_output():
    """로그 출력 테스트"""
    print("=" * 70)
    print("간소화된 로그 시스템 테스트")
    print("=" * 70)

    print("\n[시뮬레이션] 크롤링 시작...\n")

    start_time = time.time()
    all_products = []

    # 50개 수집 시뮬레이션
    print("수집 중... 1개\r", end='')
    time.sleep(0.1)
    print("수집 중... 10개\r", end='')
    time.sleep(0.1)
    print("수집 중... 25개\r", end='')
    time.sleep(0.1)
    print("수집 중... 47개\r", end='')
    time.sleep(0.1)

    # 50개 완료
    products_50 = generate_mock_products(50)
    all_products.extend(products_50)
    saved_50 = sum(1 for p in products_50 if p.get('_db_status') == 'saved')
    skipped_50 = sum(1 for p in products_50 if p.get('_db_status') == 'skipped')

    print_products_table(all_products, 50, start_time, saved_50, skipped_50)

    # 100개 수집 시뮬레이션
    print("수집 중... 52개\r", end='')
    time.sleep(0.1)
    print("수집 중... 75개\r", end='')
    time.sleep(0.1)
    print("수집 중... 98개\r", end='')
    time.sleep(0.1)

    # 100개 완료
    products_100 = generate_mock_products(100)
    all_products = products_100  # 전체 교체
    saved_100 = sum(1 for p in products_100 if p.get('_db_status') == 'saved')
    skipped_100 = sum(1 for p in products_100 if p.get('_db_status') == 'skipped')

    print_products_table(all_products, 100, start_time, saved_100, skipped_100)

    # 167개 (최종) 시뮬레이션
    print("수집 중... 112개\r", end='')
    time.sleep(0.1)
    print("수집 중... 145개\r", end='')
    time.sleep(0.1)
    print("수집 중... 167개\r", end='')
    time.sleep(0.1)

    # 167개 완료 (50의 배수가 아님)
    products_167 = generate_mock_products(167)
    all_products = products_167
    saved_167 = sum(1 for p in products_167 if p.get('_db_status') == 'saved')
    skipped_167 = sum(1 for p in products_167 if p.get('_db_status') == 'skipped')

    print_products_table(all_products, 167, start_time, saved_167, skipped_167, final=True)

    print("수집 완료! 총 167개 → DB 저장됨\n")


if __name__ == "__main__":
    test_log_output()
