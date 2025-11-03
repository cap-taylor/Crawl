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

            # 새 데이터 정리 (detail_info 우선, 없으면 product_info)
            detail_info = product_data.get('detail_page_info', {})
            product_info = product_data.get('product_info', {})

            new_data = {
                'product_name': detail_info.get('detail_product_name') or product_info.get('product_name', f"상품_{product_id}"),
                'brand_name': detail_info.get('brand_name') or product_info.get('brand', None),
                'price': detail_info.get('detail_price') or (int(product_info.get('price', 0)) if product_info.get('price') else None),
                'discount_rate': detail_info.get('discount_rate') or (int(product_info.get('discount_rate', 0)) if product_info.get('discount_rate') else None),
                'review_count': detail_info.get('detail_review_count') or (int(product_info.get('review_count', 0)) if product_info.get('review_count') else 0),
                'rating': detail_info.get('rating') or (float(product_info.get('rating', 0)) if product_info.get('rating') else None),
                'search_tags': detail_info.get('search_tags', []),
                'product_url': product_data.get('product_url', ''),
                'thumbnail_url': detail_info.get('thumbnail_url') or product_info.get('thumbnail_url', None),
                'is_sold_out': detail_info.get('is_sold_out', False)
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
            # product_id 추출
            product_id = product_data.get('product_id')
            if not product_id:
                product_url = product_data.get('product_url', '')
                product_id = self.extract_product_id(product_url)

            # 중복 체크
            if skip_duplicates and self.is_duplicate_product(product_id, product_data):
                return 'skipped'

            # SimpleCrawler 형식 지원 (단순 딕셔너리)
            if 'product_name' in product_data:
                # SimpleCrawler 형식
                product_name = product_data.get('product_name')
                brand_name = product_data.get('brand_name')
                price = product_data.get('price')
                discount_rate = product_data.get('discount_rate')
                review_count = product_data.get('review_count', 0)
                rating = product_data.get('rating')
                search_tags = product_data.get('search_tags', [])
                thumbnail_url = product_data.get('thumbnail_url')
                product_url = product_data.get('product_url', '')
            else:
                # 기존 형식 (detail_page_info/product_info)
                detail_info = product_data.get('detail_page_info', {})
                product_info = product_data.get('product_info', {})

                product_name = detail_info.get('detail_product_name') or product_info.get('product_name', f"상품_{product_id}")
                brand_name = detail_info.get('brand_name') or product_info.get('brand', None)
                price = detail_info.get('detail_price') or (int(product_info.get('price', 0)) if product_info.get('price') else None)
                discount_rate = detail_info.get('discount_rate') or (int(product_info.get('discount_rate', 0)) if product_info.get('discount_rate') else None)
                review_count = detail_info.get('detail_review_count') or (int(product_info.get('review_count', 0)) if product_info.get('review_count') else 0)
                rating = detail_info.get('rating') or (float(product_info.get('rating', 0)) if product_info.get('rating') else None)
                search_tags = detail_info.get('search_tags', [])
                thumbnail_url = detail_info.get('thumbnail_url') or product_info.get('thumbnail_url', None)
                product_url = product_data.get('product_url', '')

            # 상품 데이터 저장 (UPSERT) - 13개 필드
            cursor.execute(
                """
                INSERT INTO products (
                    product_id, category_name, product_name,
                    brand_name, price, discount_rate, review_count, rating,
                    search_tags, product_url, thumbnail_url,
                    crawled_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
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
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    product_id, category_name, product_name,
                    brand_name, price, discount_rate, review_count, rating,
                    search_tags, product_url, thumbnail_url
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

    def get_last_crawl_progress(self, category_name: str) -> Optional[int]:
        """
        특정 카테고리의 마지막 크롤링 진행 상황 조회

        Args:
            category_name: 카테고리 이름 (예: "남성의류")

        Returns:
            int: 마지막 수집 상품 인덱스 (0-based), 없으면 None
        """
        cursor = self.conn.cursor()

        try:
            # 해당 카테고리의 가장 최근 진행 중(paused) 또는 완료(completed) 크롤링 조회
            cursor.execute(
                """
                SELECT last_product_index, status, total_products
                FROM crawl_history
                WHERE category_name = %s
                  AND crawl_type = 'product'
                  AND status IN ('paused', 'running')
                ORDER BY start_time DESC
                LIMIT 1
                """,
                (category_name,)
            )
            result = cursor.fetchone()

            if result:
                last_index, status, total_products = result
                print(f"[DB] 재개 지점 발견: {category_name} - {last_index + 1}번째 상품부터 (상태: {status}, 수집: {total_products}개)")
                return last_index
            else:
                print(f"[DB] 재개 지점 없음: {category_name} - 처음부터 시작")
                return None

        except Exception as e:
            print(f"[DB] 진행 상황 조회 실패: {e}")
            return None
        finally:
            cursor.close()

    def start_crawl_session(self, category_name: str, resume: bool = False) -> Optional[int]:
        """
        크롤링 세션 시작 및 history_id 반환

        Args:
            category_name: 카테고리 이름
            resume: True면 재개, False면 새로 시작

        Returns:
            int: history_id (진행 상황 업데이트용), 실패 시 None
        """
        cursor = self.conn.cursor()

        try:
            if resume:
                # 기존 세션 찾기
                cursor.execute(
                    """
                    SELECT history_id, last_product_index
                    FROM crawl_history
                    WHERE category_name = %s
                      AND crawl_type = 'product'
                      AND status IN ('paused', 'running')
                    ORDER BY start_time DESC
                    LIMIT 1
                    """,
                    (category_name,)
                )
                result = cursor.fetchone()

                if result:
                    history_id, last_index = result
                    # 세션 재개 (status를 running으로)
                    cursor.execute(
                        """
                        UPDATE crawl_history
                        SET status = 'running'
                        WHERE history_id = %s
                        """,
                        (history_id,)
                    )
                    self.conn.commit()
                    print(f"[DB] 세션 재개: history_id={history_id}, {last_index + 1}번째 상품부터")
                    return history_id
                else:
                    print(f"[DB] 재개할 세션 없음 - 새 세션 시작")
                    resume = False

            # 새 세션 시작
            cursor.execute(
                """
                INSERT INTO crawl_history (
                    crawl_type, category_name, start_time, status
                )
                VALUES (%s, %s, %s, %s)
                RETURNING history_id
                """,
                ('product', category_name, datetime.now(), 'running')
            )
            history_id = cursor.fetchone()[0]
            self.conn.commit()
            print(f"[DB] 새 세션 시작: history_id={history_id}, 카테고리={category_name}")
            return history_id

        except Exception as e:
            print(f"[DB] 세션 시작 실패: {e}")
            self.conn.rollback()
            return None
        finally:
            cursor.close()

    def update_crawl_progress(self, history_id: int, current_index: int, total_products: int):
        """
        크롤링 진행 상황 업데이트

        Args:
            history_id: 세션 ID
            current_index: 현재 수집 중인 상품 인덱스 (0-based)
            total_products: 총 수집된 상품 수
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE crawl_history
                SET last_product_index = %s,
                    total_products = %s
                WHERE history_id = %s
                """,
                (current_index, total_products, history_id)
            )
            self.conn.commit()

        except Exception as e:
            print(f"[DB] 진행 상황 업데이트 실패: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def end_crawl_session(self, history_id: int, status: str = 'completed', error_message: Optional[str] = None):
        """
        크롤링 세션 종료

        Args:
            history_id: 세션 ID
            status: 'completed', 'failed', 'paused'
            error_message: 오류 메시지 (선택)
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE crawl_history
                SET end_time = %s,
                    status = %s,
                    error_message = %s
                WHERE history_id = %s
                """,
                (datetime.now(), status, error_message, history_id)
            )
            self.conn.commit()
            print(f"[DB] 세션 종료: history_id={history_id}, 상태={status}")

        except Exception as e:
            print(f"[DB] 세션 종료 실패: {e}")
            self.conn.rollback()
        finally:
            cursor.close()


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
