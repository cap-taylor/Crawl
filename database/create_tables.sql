-- =====================================================
-- 네이버 쇼핑 크롤러 데이터베이스 스키마
-- Version: 1.0.2
-- Date: 2025-10-15
-- Database: PostgreSQL 13+
-- Description: 실제 DB 구조와 동기화 (category_id FK 제거)
-- =====================================================

-- 데이터베이스 생성 (이미 생성되어 있다면 스킵)
-- CREATE DATABASE naver
--     WITH
--     OWNER = postgres
--     ENCODING = 'UTF8'
--     CONNECTION LIMIT = -1;

-- 데이터베이스 연결
-- \c naver;

-- 확장 모듈 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 기존 테이블 삭제 (주의: 모든 데이터가 삭제됩니다!)
-- DROP TABLE IF EXISTS products CASCADE;
-- DROP TABLE IF EXISTS categories CASCADE;
-- DROP TABLE IF EXISTS crawl_history CASCADE;

-- =====================================================
-- Categories 테이블 (카테고리 정보)
-- =====================================================
CREATE TABLE IF NOT EXISTS categories (
    category_name VARCHAR(100) PRIMARY KEY,           -- 카테고리명 (예: "여성의류")
    category_id VARCHAR(20),                          -- 네이버 카테고리 ID (예: "10000107")
    is_active BOOLEAN DEFAULT false,                  -- 활성 상태
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP    -- 생성 시간
);

-- Categories 코멘트
COMMENT ON TABLE categories IS '네이버 쇼핑 카테고리 정보';
COMMENT ON COLUMN categories.category_name IS '카테고리명 (Primary Key)';
COMMENT ON COLUMN categories.category_id IS '네이버 카테고리 ID';
COMMENT ON COLUMN categories.is_active IS '활성 상태';
COMMENT ON COLUMN categories.created_at IS '생성 시간';

-- =====================================================
-- Products 테이블 (상품 정보)
-- =====================================================
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(255) PRIMARY KEY,              -- 네이버 상품 ID
    category_name VARCHAR(100),                       -- 카테고리명 (예: "여성의류")
    product_name TEXT NOT NULL,                       -- 상품명
    brand_name VARCHAR(100),                          -- 브랜드명
    price INTEGER,                                     -- 가격 (원)
    discount_rate INTEGER,                             -- 할인율 (%)
    review_count INTEGER DEFAULT 0,                   -- 리뷰 수
    rating DECIMAL(2,1),                               -- 평점 (0.0 ~ 5.0)
    search_tags TEXT[],                                -- 검색 태그 배열
    product_url TEXT,                                  -- 상품 상세 페이지 URL
    thumbnail_url TEXT,                                -- 썸네일 이미지 URL
    is_sold_out BOOLEAN DEFAULT false,                -- 품절 여부
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- 크롤링 시간
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP    -- 업데이트 시간
);

-- Products 인덱스
CREATE INDEX IF NOT EXISTS idx_product_name ON products(product_name);
CREATE INDEX IF NOT EXISTS idx_product_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_crawled_at ON products(crawled_at);

-- Products 코멘트
COMMENT ON TABLE products IS '네이버 쇼핑 상품 정보';
COMMENT ON COLUMN products.product_id IS '네이버 상품 ID (Primary Key)';
COMMENT ON COLUMN products.category_name IS '카테고리명 (Foreign Key 없음)';
COMMENT ON COLUMN products.product_name IS '상품명';
COMMENT ON COLUMN products.brand_name IS '브랜드명';
COMMENT ON COLUMN products.price IS '가격 (원)';
COMMENT ON COLUMN products.discount_rate IS '할인율 (%)';
COMMENT ON COLUMN products.review_count IS '리뷰 수';
COMMENT ON COLUMN products.rating IS '평점 (0.0 ~ 5.0)';
COMMENT ON COLUMN products.search_tags IS '검색 태그 배열';
COMMENT ON COLUMN products.product_url IS '상품 상세 페이지 URL';
COMMENT ON COLUMN products.thumbnail_url IS '썸네일 이미지 URL';
COMMENT ON COLUMN products.is_sold_out IS '품절 여부';
COMMENT ON COLUMN products.crawled_at IS '크롤링 시간';
COMMENT ON COLUMN products.updated_at IS '업데이트 시간';

-- =====================================================
-- Crawl_History 테이블 (크롤링 이력)
-- =====================================================
CREATE TABLE IF NOT EXISTS crawl_history (
    history_id SERIAL PRIMARY KEY,                    -- 이력 ID
    crawl_type VARCHAR(50) NOT NULL,                  -- 크롤링 타입 (category, product)
    start_time TIMESTAMP NOT NULL,                    -- 시작 시간
    end_time TIMESTAMP,                               -- 종료 시간
    total_categories INTEGER DEFAULT 0,               -- 수집된 카테고리 수
    total_products INTEGER DEFAULT 0,                 -- 수집된 상품 수
    status VARCHAR(20) DEFAULT 'running',             -- 상태 (running, completed, failed)
    error_message TEXT,                               -- 오류 메시지
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP    -- 생성 시간
);

-- Crawl_History 코멘트
COMMENT ON TABLE crawl_history IS '크롤링 실행 이력';
COMMENT ON COLUMN crawl_history.history_id IS '이력 ID';
COMMENT ON COLUMN crawl_history.crawl_type IS '크롤링 타입 (category, product)';
COMMENT ON COLUMN crawl_history.start_time IS '시작 시간';
COMMENT ON COLUMN crawl_history.end_time IS '종료 시간';
COMMENT ON COLUMN crawl_history.total_categories IS '수집된 카테고리 수';
COMMENT ON COLUMN crawl_history.total_products IS '수집된 상품 수';
COMMENT ON COLUMN crawl_history.status IS '상태 (running, completed, failed)';
COMMENT ON COLUMN crawl_history.error_message IS '오류 메시지';
COMMENT ON COLUMN crawl_history.created_at IS '생성 시간';

-- =====================================================
-- 테이블 생성 확인
-- =====================================================
SELECT 'Categories 테이블' as table_name, COUNT(*) as record_count FROM categories
UNION ALL
SELECT 'Products 테이블', COUNT(*) FROM products
UNION ALL
SELECT 'Crawl_History 테이블', COUNT(*) FROM crawl_history;

-- =====================================================
-- 유용한 쿼리들
-- =====================================================

-- 1. 카테고리별 상품 수 통계
-- SELECT category_name, COUNT(*) as product_count
-- FROM products
-- GROUP BY category_name
-- ORDER BY product_count DESC;

-- 2. 최근 크롤링 이력
-- SELECT * FROM crawl_history
-- ORDER BY start_time DESC
-- LIMIT 10;

-- 3. 오늘 크롤링된 상품 수
-- SELECT COUNT(*) as today_products
-- FROM products
-- WHERE DATE(crawled_at) = CURRENT_DATE;

-- 4. 검색태그가 많은 상품 TOP 10
-- SELECT product_id, product_name, category_name,
--        array_length(search_tags, 1) as tag_count
-- FROM products
-- WHERE search_tags IS NOT NULL
-- ORDER BY tag_count DESC
-- LIMIT 10;

-- 5. 카테고리 목록 조회
-- SELECT category_name, category_id, created_at
-- FROM categories
-- WHERE is_active = true
-- ORDER BY category_name;