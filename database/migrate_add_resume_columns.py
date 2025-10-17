"""
crawl_history 테이블에 재개 기능용 컬럼 추가
- category_name VARCHAR(100)
- last_product_index INTEGER DEFAULT 0
"""
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

from src.database.db_connector import DatabaseConnector

def migrate():
    """DB 마이그레이션 실행"""
    db = DatabaseConnector()

    try:
        db.connect()
        cursor = db.conn.cursor()

        print("[마이그레이션] crawl_history 테이블 업데이트 시작...")

        # 1. category_name 컬럼 추가
        try:
            cursor.execute("""
                ALTER TABLE crawl_history
                ADD COLUMN IF NOT EXISTS category_name VARCHAR(100)
            """)
            print("  ✓ category_name 컬럼 추가 완료")
        except Exception as e:
            print(f"  [경고] category_name 추가 실패: {e}")

        # 2. last_product_index 컬럼 추가
        try:
            cursor.execute("""
                ALTER TABLE crawl_history
                ADD COLUMN IF NOT EXISTS last_product_index INTEGER DEFAULT 0
            """)
            print("  ✓ last_product_index 컬럼 추가 완료")
        except Exception as e:
            print(f"  [경고] last_product_index 추가 실패: {e}")

        # 3. 커밋
        db.conn.commit()
        print("\n[마이그레이션] 완료!")

        # 4. 테이블 구조 확인
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'crawl_history'
            ORDER BY ordinal_position
        """)

        print("\n[테이블 구조] crawl_history:")
        print(f"{'컬럼명':<25} {'타입':<20} {'NULL':<10} {'기본값':<15}")
        print("-" * 70)

        for row in cursor.fetchall():
            col_name, data_type, is_null, default_val = row
            print(f"{col_name:<25} {data_type:<20} {is_null:<10} {str(default_val):<15}")

        cursor.close()

    except Exception as e:
        print(f"[오류] 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
