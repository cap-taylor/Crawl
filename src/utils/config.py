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
    'password': os.getenv('DB_PASSWORD', '')
}

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

# 셀렉터 정의
SELECTORS = {
    'category_button': '#gnb-gnb button',  # 카테고리 메뉴 버튼
    'category_menu': '._gnbCategory_menu_container',  # 카테고리 메뉴 컨테이너
    'category_items': 'a[class*="category"]',  # 카테고리 항목들
    'product_card': '#composite-card-list li',  # 상품 카드
    'product_name': '.product-title',  # 상품명
    'search_tags': '#INTRODUCE .f_JzwGZdbu a',  # 검색 태그
}