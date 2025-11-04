#!/usr/bin/env python3
"""
GUI 로그 테이블 테스트 - 번호 갱신 확인
목적: 새 상품 추가 시 모든 행의 번호가 올바르게 갱신되는지 확인
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import customtkinter as ctk
from product_collector_gui import ProductCollectorGUI
import time


def test_table_numbering():
    """테이블 번호 갱신 테스트"""
    print("=== GUI 로그 테이블 번호 갱신 테스트 ===\n")

    # GUI 생성
    app = ProductCollectorGUI()

    # 테스트 상품 15개 추가 (10개 넘어가면서 갱신 확인)
    for i in range(1, 16):
        product = {
            'product_id': f'test_{i}',
            'product_name': f'테스트 상품 #{i}',
            'price': 10000 + i * 1000,
            'brand_name': f'브랜드{i}',
            'search_tags': ['태그1', '태그2'],
            '_db_status': 'saved' if i % 3 != 0 else 'skipped'
        }

        print(f"[{i}번째 상품 추가] {product['product_name']}")
        app._add_product_to_table(product)
        app.root.update()

        # 현재 테이블 상태 확인
        table_rows = app.table_body.winfo_children()[1:]  # 헤더 제외
        print(f"  → 테이블 행 수: {len(table_rows)}개")

        # 각 행의 번호 확인
        for idx, row in enumerate(table_rows):
            labels = [w for w in row.winfo_children() if isinstance(w, ctk.CTkLabel)]
            if labels:
                row_number = labels[0].cget("text")
                product_name = labels[1].cget("text") if len(labels) > 1 else "N/A"
                print(f"     행 {idx+1}: 번호={row_number}, 상품={product_name}")

        print()
        time.sleep(0.5)

    print("\n=== 테스트 완료 ===")
    print("20초 후 종료...")
    app.root.after(20000, app.root.quit)
    app.root.mainloop()


if __name__ == "__main__":
    test_table_numbering()
