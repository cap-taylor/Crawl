"""
재개 기능 테스트 스크립트

1. DB에 진행 상황 저장
2. 재개 지점 로드
3. 진행 상황 업데이트
"""
import sys
sys.path.append('/home/dino/MyProjects/Crawl')

from src.database.db_connector import DatabaseConnector
from datetime import datetime


def test_crawl_session():
    """크롤링 세션 시작/종료 테스트"""
    print("\n" + "="*60)
    print("테스트 1: 크롤링 세션 시작/종료")
    print("="*60)

    db = DatabaseConnector()
    db.connect()

    try:
        # 1. 새 세션 시작
        print("\n[1] 새 세션 시작 (남성의류)")
        history_id = db.start_crawl_session("남성의류", resume=False)
        print(f"   -> history_id: {history_id}")

        # 2. 진행 상황 업데이트 (시뮬레이션)
        print("\n[2] 진행 상황 업데이트 (10개 수집)")
        db.update_crawl_progress(history_id, 9, 10)  # 9번째 상품까지 (0-based), 총 10개
        print(f"   -> 10개 수집 완료, 마지막 인덱스: 9")

        # 3. 세션 일시 중지 (paused)
        print("\n[3] 세션 일시 중지")
        db.end_crawl_session(history_id, status='paused')
        print(f"   -> 상태: paused")

        # 4. 재개 지점 조회
        print("\n[4] 재개 지점 조회")
        last_index = db.get_last_crawl_progress("남성의류")
        if last_index is not None:
            print(f"   -> 재개 지점: {last_index + 1}번째 상품부터 (0-based: {last_index})")
        else:
            print(f"   -> 재개 지점 없음")

        # 5. 세션 재개
        print("\n[5] 세션 재개")
        resumed_id = db.start_crawl_session("남성의류", resume=True)
        print(f"   -> history_id: {resumed_id} (기존 세션과 동일해야 함)")

        # 6. 추가 수집 (20개 더)
        print("\n[6] 추가 수집 (20개 더)")
        db.update_crawl_progress(resumed_id, 29, 30)  # 29번째 상품까지, 총 30개
        print(f"   -> 30개 수집 완료, 마지막 인덱스: 29")

        # 7. 세션 완료
        print("\n[7] 세션 완료")
        db.end_crawl_session(resumed_id, status='completed')
        print(f"   -> 상태: completed")

        print("\n[완료] 테스트 성공!")

    except Exception as e:
        print(f"\n[오류] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_multiple_categories():
    """여러 카테고리 동시 관리 테스트"""
    print("\n" + "="*60)
    print("테스트 2: 여러 카테고리 동시 관리")
    print("="*60)

    db = DatabaseConnector()
    db.connect()

    try:
        # 1. 여성의류 세션 시작
        print("\n[1] 여성의류 세션 시작")
        womens_id = db.start_crawl_session("여성의류", resume=False)
        db.update_crawl_progress(womens_id, 49, 50)
        db.end_crawl_session(womens_id, status='paused')
        print(f"   -> 여성의류: 50개 수집, 일시중지")

        # 2. 남성의류 세션 시작
        print("\n[2] 남성의류 세션 시작")
        mens_id = db.start_crawl_session("남성의류", resume=False)
        db.update_crawl_progress(mens_id, 29, 30)
        db.end_crawl_session(mens_id, status='paused')
        print(f"   -> 남성의류: 30개 수집, 일시중지")

        # 3. 각 카테고리 재개 지점 조회
        print("\n[3] 재개 지점 조회")
        womens_index = db.get_last_crawl_progress("여성의류")
        mens_index = db.get_last_crawl_progress("남성의류")

        print(f"   -> 여성의류: {womens_index + 1}번째부터")
        print(f"   -> 남성의류: {mens_index + 1}번째부터")

        # 4. 여성의류만 재개
        print("\n[4] 여성의류만 재개")
        womens_resumed = db.start_crawl_session("여성의류", resume=True)
        db.update_crawl_progress(womens_resumed, 99, 100)
        db.end_crawl_session(womens_resumed, status='completed')
        print(f"   -> 여성의류: 100개 수집 완료")

        # 5. 남성의류 재개 지점 확인 (영향 없어야 함)
        print("\n[5] 남성의류 재개 지점 확인 (변경 없어야 함)")
        mens_index_after = db.get_last_crawl_progress("남성의류")
        assert mens_index == mens_index_after, "남성의류 재개 지점이 변경되었습니다!"
        print(f"   -> 남성의류: {mens_index_after + 1}번째부터 (변경 없음)")

        print("\n[완료] 테스트 성공!")

    except Exception as e:
        print(f"\n[오류] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_history_table():
    """crawl_history 테이블 조회"""
    print("\n" + "="*60)
    print("테스트 3: crawl_history 테이블 조회")
    print("="*60)

    db = DatabaseConnector()
    db.connect()

    try:
        cursor = db.conn.cursor()

        # 최근 10개 세션 조회
        cursor.execute("""
            SELECT history_id, category_name, total_products,
                   last_product_index, status, start_time
            FROM crawl_history
            WHERE crawl_type = 'product'
            ORDER BY start_time DESC
            LIMIT 10
        """)

        results = cursor.fetchall()

        print(f"\n최근 {len(results)}개 크롤링 세션:")
        print("-" * 80)
        print(f"{'ID':<6} {'카테고리':<12} {'수집':<8} {'마지막 인덱스':<15} {'상태':<12} {'시작 시간'}")
        print("-" * 80)

        for row in results:
            history_id, category, total, last_idx, status, start_time = row
            start_time_str = start_time.strftime("%m-%d %H:%M") if start_time else "N/A"
            print(f"{history_id:<6} {category or 'N/A':<12} {total or 0:<8} {last_idx or 0:<15} {status:<12} {start_time_str}")

        cursor.close()
        print("\n[완료] 조회 성공!")

    except Exception as e:
        print(f"\n[오류] 조회 실패: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("\n재개 기능 테스트 시작...")

    # 테스트 1: 세션 시작/종료/재개
    test_crawl_session()

    # 테스트 2: 여러 카테고리 동시 관리
    test_multiple_categories()

    # 테스트 3: 히스토리 조회
    test_history_table()

    print("\n" + "="*60)
    print("모든 테스트 완료!")
    print("="*60)
