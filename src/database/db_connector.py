"""
PostgreSQL 데이터베이스 연결 및 저장 모듈
"""
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()


class DatabaseConnector:
    """PostgreSQL 데이터베이스 연결 및 작업 클래스"""

    def __init__(self):
        """DB 연결 설정 초기화"""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.dbname = os.getenv('DB_NAME', 'naver')
        self.user = os.getenv('DB_USER', 'postgres')

        # 비밀번호는 반드시 환경변수에서 가져오기
        self.password = os.getenv('DB_PASSWORD')
        if not self.password:
            raise ValueError(
                "DB_PASSWORD 환경변수가 설정되지 않았습니다!\n"
                ".env 파일을 만들고 DB_PASSWORD를 설정하세요.\n"
                "예: .env.example 파일을 복사하여 .env로 이름 변경 후 비밀번호 입력"
            )

        self.conn = None

    def connect(self):
        """데이터베이스 연결"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password
            )
            print(f"[DB] 연결 성공: {self.dbname}@{self.host}")
            return self.conn
        except Exception as e:
            print(f"[DB] 연결 실패: {e}")
            raise

    def close(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
            print("[DB] 연결 종료")

    def validate_category(self, category_name: str) -> bool:
        """
        카테고리가 DB에 존재하는지 확인

        Args:
            category_name: 카테고리 이름 (예: "여성의류")

        Returns:
            bool: 존재하면 True, 없으면 False
        """
        cursor = self.conn.cursor()

        try:
            # 카테고리 존재 여부 확인
            cursor.execute(
                "SELECT category_name FROM categories WHERE category_name = %s",
                (category_name,)
            )
            result = cursor.fetchone()

            if result:
                print(f"[DB] 카테고리 확인: {category_name}")
                return True
            else:
                print(f"[DB] 경고: 카테고리 '{category_name}'가 DB에 없습니다!")
                return False

        except Exception as e:
            print(f"[DB] 카테고리 확인 실패: {e}")
            return False
        finally:
            cursor.close()

    def extract_product_id(self, product_url: str) -> str:
        """
        상품 URL에서 product_id 추출

        Args:
            product_url: 상품 URL (예: "https://smartstore.naver.com/main/products/2735313334")

        Returns:
            product_id: 상품 ID (예: "2735313334")
        """
        match = re.search(r'/products/(\d+)', product_url)
        if match:
            return match.group(1)

        # 패턴 매칭 실패 시 URL 전체를 해시
        return str(abs(hash(product_url)))

    def is_duplicate_product(self, product_id: str, product_data: Dict) -> bool:
        """
        DB에 동일한 상품 정보가 이미 있는지 확인

        Args:
            product_id: 상품 ID
            product_data: 새로 수집한 상품 데이터

        Returns:
            bool: True면 중복(스킵), False면 신규 또는 업데이트 필요
        """
        cursor = self.conn.cursor()

        try:
            # DB에서 기존 상품 조회
            cursor.execute(
                """
                SELECT product_name, brand_name, price, discount_rate,
                       review_count, rating, search_tags, product_url,
                       thumbnail_url, is_sold_out
                FROM products
                WHERE product_id = %s
                """,
                (product_id,)
            )
            result = cursor.fetchone()

            # 기존 데이터 없으면 신규
            if not result:
                return False

            # 기존 데이터와 비교
            db_data = {
                'product_name': result[0],
                'brand_name': result[1],
                'price': result[2],
                'discount_rate': result[3],
                'review_count': result[4],
                'rating': float(result[5]) if result[5] else None,
                'search_tags': result[6] if result[6] else [],
                'product_url': result[7],
                'thumbnail_url': result[8],
                'is_sold_out': result[9]
            }

            # 새 데이터 정리
            detail_info = product_data.get('detail_page_info', {})
            product_info = product_data.get('product_info', {})

            new_data = {
                'product_name': product_info.get('product_name', f"상품_{product_id}"),
                'brand_name': product_info.get('brand', None),
                'price': int(product_info.get('price', 0)) if product_info.get('price') else None,
                'discount_rate': int(product_info.get('discount_rate', 0)) if product_info.get('discount_rate') else None,
                'review_count': int(product_info.get('review_count', 0)) if product_info.get('review_count') else 0,
                'rating': float(product_info.get('rating', 0)) if product_info.get('rating') else None,
                'search_tags': detail_info.get('search_tags', []),
                'product_url': product_data.get('product_url', ''),
                'thumbnail_url': product_info.get('thumbnail_url', None),
                'is_sold_out': False
            }

            # 모든 필드 비교
            for key in db_data.keys():
                db_value = db_data[key]
                new_value = new_data[key]

                # None 처리
                if db_value is None and new_value is None:
                    continue
                if db_value is None or new_value is None:
                    return False

                # search_tags 배열 비교
                if key == 'search_tags':
                    if set(db_value) != set(new_value):
                        return False
                # 일반 필드 비교
                else:
                    if db_value != new_value:
                        return False

            # 모든 필드가 동일하면 중복
            return True

        except Exception as e:
            print(f"[DB] 중복 체크 중 오류: {e}")
            return False
        finally:
            cursor.close()

    def save_product(self, category_name: str, product_data: Dict, skip_duplicates: bool = True) -> str:
        """
        상품 데이터 저장

        Args:
            category_name: 카테고리 이름 (예: "여성의류")
            product_data: 상품 데이터 딕셔너리
            skip_duplicates: True면 중복 데이터 스킵

        Returns:
            str: 'saved', 'skipped', 'failed'
        """
        cursor = self.conn.cursor()

        try:
            # 카테고리 유효성 검사 (선택사항)
            self.validate_category(category_name)

            # product_id 추출
            product_url = product_data.get('product_url', '')
            product_id = self.extract_product_id(product_url)

            # 중복 체크
            if skip_duplicates and self.is_duplicate_product(product_id, product_data):
                print(f"[DB] 상품 스킵 (중복): {product_id}")
                return 'skipped'

            # 데이터 추출
            detail_info = product_data.get('detail_page_info', {})
            product_info = product_data.get('product_info', {})

            # 모든 필드 정리
            product_name = product_info.get('product_name', f"상품_{product_id}")
            brand_name = product_info.get('brand', None)
            price = int(product_info.get('price', 0)) if product_info.get('price') else None
            discount_rate = int(product_info.get('discount_rate', 0)) if product_info.get('discount_rate') else None
            review_count = int(product_info.get('review_count', 0)) if product_info.get('review_count') else 0
            rating = float(product_info.get('rating', 0)) if product_info.get('rating') else None
            search_tags = detail_info.get('search_tags', [])
            thumbnail_url = product_info.get('thumbnail_url', None)
            is_sold_out = False

            # 상품 데이터 저장 (UPSERT) - category_id 제거
            cursor.execute(
                """
                INSERT INTO products (
                    product_id, category_name, product_name,
                    brand_name, price, discount_rate, review_count, rating,
                    search_tags, product_url, thumbnail_url, is_sold_out,
                    crawled_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_id)
                DO UPDATE SET
                    category_name = EXCLUDED.category_name,
                    product_name = EXCLUDED.product_name,
                    brand_name = EXCLUDED.brand_name,
                    price = EXCLUDED.price,
                    discount_rate = EXCLUDED.discount_rate,
                    review_count = EXCLUDED.review_count,
                    rating = EXCLUDED.rating,
                    search_tags = EXCLUDED.search_tags,
                    product_url = EXCLUDED.product_url,
                    thumbnail_url = EXCLUDED.thumbnail_url,
                    is_sold_out = EXCLUDED.is_sold_out,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    product_id, category_name, product_name,
                    brand_name, price, discount_rate, review_count, rating,
                    search_tags, product_url, thumbnail_url, is_sold_out,
                    datetime.now(), datetime.now()
                )
            )

            self.conn.commit()
            print(f"[DB] 상품 저장 성공: {product_id} (카테고리: {category_name}, 검색태그: {len(search_tags)}개)")
            return 'saved'

        except Exception as e:
            self.conn.rollback()
            print(f"[DB] 상품 저장 실패: {e}")
            return 'failed'
        finally:
            cursor.close()

    def save_products_batch(self, category_name: str, products_list: List[Dict], skip_duplicates: bool = True) -> Dict[str, int]:
        """
        여러 상품 일괄 저장

        Args:
            category_name: 카테고리 이름
            products_list: 상품 데이터 리스트
            skip_duplicates: True면 중복 데이터 스킵

        Returns:
            dict: {'saved': n, 'skipped': n, 'failed': n}
        """
        results = {'saved': 0, 'skipped': 0, 'failed': 0}

        for product_data in products_list:
            result = self.save_product(category_name, product_data, skip_duplicates)
            results[result] += 1

        print(f"[DB] 일괄 저장 완료: 저장 {results['saved']}개 | 스킵 {results['skipped']}개 | 실패 {results['failed']}개")
        return results


# 간편 함수들
def save_to_database(category_name: str, products_list: List[Dict], skip_duplicates: bool = True) -> Dict[str, int]:
    """
    간편 DB 저장 함수

    Args:
        category_name: 카테고리 이름 (예: "여성의류")
        products_list: 상품 데이터 리스트
        skip_duplicates: True면 중복 데이터 스킵

    Returns:
        dict: {'saved': n, 'skipped': n, 'failed': n}
    """
    db = DatabaseConnector()
    try:
        db.connect()
        results = db.save_products_batch(category_name, products_list, skip_duplicates)
        return results
    finally:
        db.close()


if __name__ == "__main__":
    # 테스트 코드
    test_data = {
        "product_url": "https://smartstore.naver.com/main/products/2735313334",
        "detail_page_info": {
            "search_tags": ["노와이어브라", "여자속옷", "심리스브라"]
        }
    }

    db = DatabaseConnector()
    try:
        db.connect()
        db.save_product("여성의류", test_data)
    finally:
        db.close()
