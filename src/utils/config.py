"""네이버 쇼핑 크롤러 설정 파일"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 데이터베이스 설정
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'naver'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD')  # 비밀번호는 반드시 .env에서 설정
}

# DB 비밀번호 검증
if not DB_CONFIG['password']:
    raise ValueError(
        "DB_PASSWORD 환경변수가 설정되지 않았습니다!\n"
        ".env 파일을 만들고 DB_PASSWORD를 설정하세요.\n"
        "참고: .env.example 파일 참조"
    )

# 크롤링 설정
CRAWL_CONFIG = {
    'base_url': 'https://shopping.naver.com/ns/home',
    'wait_time': {
        'min': 2,
        'max': 5
    },
    'scroll_pause_time': 1.5,
    'batch_size': 100,
    'headless': False,  # False로 하면 브라우저 창이 보임
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# =====================================================
# 셀렉터 정의 (다중 Fallback 시스템)
# =====================================================
# 우선순위: 구조 기반 > 속성 기반 > 패턴 기반
# 네이버의 난독화된 클래스명 대응을 위해 여러 셀렉터 시도

SELECTORS = {
    # ==================== 네비게이션 ====================
    'shopping_button': [
        'a:has-text("쇼핑")',                      # 텍스트 기반 (1순위)
        'a[href*="shopping.naver.com"]',         # 속성 기반 (2순위)
        '#shortcutArea > ul > li:nth-child(4) > a',  # 구조 기반 (3순위)
    ],

    'category_button': [
        'button:has-text("카테고리")',             # 텍스트 기반 (1순위)
        'button[class*="category"]',             # 패턴 기반 (2순위)
        '#gnb-gnb button',                       # ID 기반 (3순위)
    ],

    'category_menu_item': [
        'a[data-name="{category_name}"]',        # 속성 기반 (1순위) - {category_name} 대체 필요
        'a:has-text("{category_name}")',         # 텍스트 기반 (2순위)
    ],

    # ==================== 상품 리스트 ====================
    'product_links': [
        'a[href*="/products/"]',                 # 속성 기반 (1순위)
        'div[class*="product"] a',               # 패턴 기반 (2순위)
        'li[class*="product"] a',                # 패턴 기반 (3순위)
    ],

    # ==================== 상품 상세 정보 ====================
    'product_name': [
        'h3',                                    # 단순 태그 (1순위 - 보통 첫 h3가 상품명)
        'h3[class*="title"]',                    # 패턴 기반 (2순위)
        'h2[class*="title"]',                    # fallback (3순위)
        'div[class*="productTitle"]',            # 패턴 기반 (4순위)
        '[class*="product_title"]',              # 패턴 기반 (5순위)
    ],

    'price': [
        'strong[class*="price"] em',             # 네이버 스토어 (1순위)
        'div[class*="_price"] em',               # 상품 가격 영역 (2순위)
        'span[class*="lowestPrice"]',            # 최저가 (3순위)
        'strong em:has-text("원")',              # 강조 + 원 (4순위)
        'em[class*="salePrice"]',                # 할인가 (5순위)
        'span.price em',                         # 기본 (6순위)
    ],

    'discount_rate': [
        'span[class*="discount"]:has-text("%")', # 할인율 + % (1순위)
        'strong:has-text("%")',                  # 강조 + % (2순위)
        'em[class*="discount"]:has-text("%")',   # em + 할인 (3순위)
    ],

    'review_count': [
        'em[class*="count"]',                    # 리뷰 카운트 (1순위)
        'span[class*="_count"]',                 # 카운트 (2순위)
        'a:has-text("리뷰") em',                 # 리뷰 링크 내 숫자 (3순위)
    ],

    'rating': [
        'span[class*="_rating"]',                # 평점 (1순위)
        'em[class*="rating"]',                   # 평점 em (2순위)
        'strong[class*="star"]',                 # 별점 (3순위)
        'span:has-text("평점")',                 # 평점 텍스트 (4순위)
    ],

    'brand_name': [
        'a[class*="seller"]',                    # 판매자 링크 (1순위)
        'span[class*="seller"]',                 # 판매자 (2순위)
        'a[class*="brand"]',                     # 브랜드 링크 (3순위)
        'div[class*="shopName"]',                # 상점명 (4순위)
        'span[class*="store"]',                  # 스토어 (5순위)
    ],

    'thumbnail': [
        'img[class*="thumb"]',                   # 패턴 기반 (1순위)
        'img[class*="product"]',                 # 패턴 기반 (2순위)
        'img',                                   # 단순 태그 (3순위 - 첫 이미지)
    ],

    'is_sold_out': [
        'span:has-text("품절")',                 # 텍스트 기반 (1순위)
        'div:has-text("일시품절")',              # 텍스트 기반 (2순위)
        '[class*="soldOut"]',                    # 패턴 기반 (3순위)
    ],

    # ==================== 카테고리 경로 (Breadcrumb) ====================
    # 네이버 스토어 구조: ul.ySOklWNBjf > li > a > span.sAla67hq4a
    'category_breadcrumb': [
        'ul.ySOklWNBjf li a',                    # 네이버 스토어 breadcrumb (1순위)
        'ul[class*="ySOkl"] li a',               # 클래스명 일부 매칭 (2순위)
        'li[class*="R_6Kg"] a',                  # li 클래스 패턴 (3순위)
        'nav[aria-label*="breadcrumb"] a',       # 표준 breadcrumb (4순위)
        'div[class*="breadcrumb"] a',            # 패턴 기반 (5순위)
    ],

    # ==================== 검색 태그 ====================
    # 구조 기반: "관련 태그" 텍스트 찾은 후 다음 ul > a 리스트
    # NOTE: selector_helper.find_by_text_then_next() 사용 권장
    'search_tags_container': [
        'text="관련 태그"',                      # 텍스트 앵커 (구조 기반에서 사용)
    ],

    'search_tags_links': [
        'a[href*="search"]',                     # 속성 기반 (1순위)
        'a:has-text("#")',                       # 텍스트 기반 (2순위)
        'a[href*="%23"]',                        # URL 인코딩된 # (3순위)
    ],

    # ==================== 캡차 감지 ====================
    'captcha_indicators': [
        'text="보안 확인을 완료해 주세요"',
        'text="자동입력 방지"',
        'input[name="captchaAnswer"]',
        'img[alt*="보안"]',
        '[class*="captcha"]',
    ],
}