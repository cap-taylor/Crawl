#!/usr/bin/env python3
"""
개선된 번호 시스템 테스트
실제 수집 개수 반영 확인
"""

# 수정 전: 1~10 고정
def old_numbering(total_collected, recent_products):
    """기존 방식 - 1~10 고정"""
    results = []
    for i, product in enumerate(reversed(recent_products)):
        row_num = i + 1
        results.append((row_num, product['name']))
    return results

# 수정 후: 실제 수집 개수 반영
def new_numbering(total_collected, recent_products):
    """새 방식 - 실제 수집 개수 반영"""
    results = []
    for i, product in enumerate(reversed(recent_products)):
        row_num = total_collected - i
        results.append((row_num, product['name']))
    return results

print("=== 번호 시스템 개선 테스트 ===\n")

# 시나리오 1: 28개 수집 (최근 10개 표시)
print("1. 28개 수집 후 (최근 10개)")
recent_products = [{'name': f'상품{i}'} for i in range(19, 29)]
total = 28

print("\n[수정 전 - 1~10 고정]")
old_result = old_numbering(total, recent_products)
for num, name in old_result:
    print(f"  ({num}) {name}")

print("\n[수정 후 - 실제 개수 반영]")
new_result = new_numbering(total, recent_products)
for num, name in new_result:
    print(f"  ({num}) {name}")

# 시나리오 2: 100개 수집
print("\n\n2. 100개 수집 후 (최근 10개)")
recent_products = [{'name': f'상품{i}'} for i in range(91, 101)]
total = 100

print("\n[수정 전 - 1~10 고정]")
old_result = old_numbering(total, recent_products)
for num, name in old_result[:3]:
    print(f"  ({num}) {name}")
print("  ...")
for num, name in old_result[-2:]:
    print(f"  ({num}) {name}")

print("\n[수정 후 - 실제 개수 반영]")
new_result = new_numbering(total, recent_products)
for num, name in new_result[:3]:
    print(f"  ({num}) {name}")
print("  ...")
for num, name in new_result[-2:]:
    print(f"  ({num}) {name}")

# 시나리오 3: 상품 5개만 수집
print("\n\n3. 5개만 수집 후 (5개 표시)")
recent_products = [{'name': f'상품{i}'} for i in range(1, 6)]
total = 5

print("\n[수정 전 - 1~5]")
old_result = old_numbering(total, recent_products)
for num, name in old_result:
    print(f"  ({num}) {name}")

print("\n[수정 후 - 1~5 (동일, 하지만 의미 명확)]")
new_result = new_numbering(total, recent_products)
for num, name in new_result:
    print(f"  ({num}) {name}")

print("\n\n=== 결과 비교 ===")
print("✅ 수정 후 장점:")
print("  1. 최신 상품 번호 = 전체 수집 개수 (즉시 파악)")
print("  2. 각 상품이 몇 번째인지 명확 (28번째, 27번째...)")
print("  3. 진행 상황 직관적 (100개 수집 → 최상단이 (100))")
print("\n❌ 수정 전 문제:")
print("  1. 항상 (10), (9), (8)... → 전체 개수 알 수 없음")
print("  2. 어떤 상품인지 위치 파악 어려움")
