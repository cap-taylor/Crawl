"""
DB에 저장된 상품 데이터 확인 스크립트
실제로 어떤 값이 저장됐는지 확인
"""
import sys
sys.path.append('/home/dino/MyProjects/Crawl')
from src.database.db_connector import DatabaseConnector

db = DatabaseConnector()
db.connect()

cursor = db.conn.cursor()

# 최근 수집된 상품 10개 조회
cursor.execute("""
    SELECT
        product_id,
        product_name,
        brand_name,
        price,
        discount_rate,
        review_count,
        rating,
        is_sold_out,
        array_length(search_tags, 1) as tag_count,
        product_url,
        crawled_at
    FROM products
    ORDER BY crawled_at DESC
    LIMIT 10
""")

rows = cursor.fetchall()

print("\n" + "="*120)
print("최근 수집된 상품 10개")
print("="*120)
print(f"{'상품ID':<15} {'상품명':<40} {'브랜드':<15} {'가격':<10} {'할인':<5} {'리뷰':<6} {'평점':<5} {'태그':<5}")
print("-"*120)

for row in rows:
    product_id, name, brand, price, discount, review, rating, sold_out, tag_count, url, crawled = row

    name_short = name[:38] + ".." if len(name) > 40 else name
    brand_short = (brand[:13] + ".." if brand and len(brand) > 15 else brand) or "N/A"
    price_display = f"{price:,}원" if price else "N/A"
    discount_display = f"{discount}%" if discount else "-"
    review_display = f"{review:,}" if review else "0"
    rating_display = f"{rating:.1f}" if rating else "-"
    tag_display = str(tag_count) if tag_count else "0"

    print(f"{product_id:<15} {name_short:<40} {brand_short:<15} {price_display:<10} {discount_display:<5} {review_display:<6} {rating_display:<5} {tag_display:<5}")

print("="*120)

# 문제 있는 데이터 찾기
print("\n🚨 문제 데이터 검사:")
print("-"*120)

cursor.execute("""
    SELECT
        product_id,
        product_name,
        brand_name,
        price,
        discount_rate,
        review_count,
        rating
    FROM products
    WHERE
        price IS NULL
        OR price < 100
        OR brand_name IS NULL
        OR brand_name = ''
    ORDER BY crawled_at DESC
    LIMIT 20
""")

problem_rows = cursor.fetchall()

if problem_rows:
    print(f"\n⚠️ {len(problem_rows)}개의 문제 데이터 발견:")
    for row in problem_rows:
        pid, name, brand, price, discount, review, rating = row
        print(f"\n  상품ID: {pid}")
        print(f"  상품명: {name[:60]}")
        print(f"  브랜드: {brand or 'NULL'}")
        print(f"  가격: {price or 'NULL'}원")
        print(f"  할인율: {discount or 'NULL'}%")
        print(f"  리뷰: {review or 0}개")
        print(f"  평점: {rating or 'NULL'}")
else:
    print("✅ 문제 데이터 없음!")

db.close()
print("\n")
