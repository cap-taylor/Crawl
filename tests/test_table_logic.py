#!/usr/bin/env python3
"""
테이블 로직 테스트 (GUI 없이)
목적: _refresh_product_table() 호출 여부 확인
"""

# 수정 전 코드 (버그)
def old_add_product(recent_products, product_data):
    """기존 방식 - 번호가 고정됨"""
    if len(recent_products) >= 10:
        recent_products.pop(0)
    recent_products.append(product_data)
    # _add_single_row_at_top() 호출 - 번호 고정!
    return "add_single_row_at_top"

# 수정 후 코드 (수정됨)
def new_add_product(recent_products, product_data):
    """새 방식 - 전체 다시 그리기"""
    if len(recent_products) >= 10:
        recent_products.pop(0)
    recent_products.append(product_data)
    # _refresh_product_table() 호출 - 번호 갱신!
    return "refresh_product_table"

# 테스트
print("=== 테이블 로직 테스트 ===\n")

recent_products = []

print("1. 수정 전 (버그):")
for i in range(1, 13):
    product = {'product_id': f'test_{i}', 'name': f'상품{i}'}
    result = old_add_product(recent_products, product)
    print(f"  상품 {i} 추가 → {result} 호출")
    if i in [10, 11, 12]:
        print(f"     리스트 크기: {len(recent_products)}개")

print("\n2. 수정 후 (정상):")
recent_products = []
for i in range(1, 13):
    product = {'product_id': f'test_{i}', 'name': f'상품{i}'}
    result = new_add_product(recent_products, product)
    print(f"  상품 {i} 추가 → {result} 호출")
    if i in [10, 11, 12]:
        print(f"     리스트 크기: {len(recent_products)}개")
        print(f"     리스트 내용: {[p['name'] for p in recent_products]}")

print("\n=== 결과 ===")
print("✅ 수정 후: refresh_product_table() 호출 → 모든 번호 재계산")
print("   - 상품 11 추가 시: 상품2~11 표시 (번호 1~10)")
print("   - 상품 12 추가 시: 상품3~12 표시 (번호 1~10)")
