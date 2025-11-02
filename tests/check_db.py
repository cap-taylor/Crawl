"""DB 확인 스크립트"""
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

from src.database.db_connector import DatabaseConnector

db = DatabaseConnector()
db.connect()

try:
    cursor = db.conn.cursor()

    # 여성의류 카테고리 상품 조회
    cursor.execute("""
        SELECT product_id, product_name, brand_name, price, review_count, is_sold_out, crawled_at
        FROM products
        WHERE category_name='여성의류'
        ORDER BY crawled_at DESC
        LIMIT 5
    """)

    rows = cursor.fetchall()

    print("=" * 80)
    print(f"DB 저장 확인: 최근 {len(rows)}개 상품")
    print("=" * 80)

    for i, row in enumerate(rows, 1):
        product_id, name, brand, price, review_count, is_sold_out, crawled_at = row
        print(f"\n{i}. {name[:50]}")
        print(f"   ID: {product_id}")
        print(f"   브랜드: {brand}")
        print(f"   가격: {price:,}원" if price is not None else "   가격: N/A")
        print(f"   리뷰: {review_count}개")
        print(f"   품절: {is_sold_out}")
        print(f"   수집시간: {crawled_at}")

    print("\n" + "=" * 80)
    print(f"✅ DB에 정상 저장됨!")
    print("=" * 80)

finally:
    db.close()
