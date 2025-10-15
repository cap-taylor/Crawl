-- =====================================================
-- 네이버 쇼핑 카테고리 분석 SQL 쿼리
-- =====================================================
-- category_fullname 형식: "대분류>중분류>소분류>세분류"
-- 예: "가구/인테리어>DIY자재/용품>가구부속품>가구다리"

-- =====================================================
-- 1. 전체 카테고리 분포 (대분류별 상품 수)
-- =====================================================
SELECT
    SPLIT_PART(category_fullname, '>', 1) AS main_category,
    COUNT(*) AS product_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM products WHERE category_fullname IS NOT NULL), 2) AS percentage
FROM products
WHERE category_fullname IS NOT NULL
GROUP BY main_category
ORDER BY product_count DESC;

-- =====================================================
-- 2. 카테고리 깊이 분석 (Depth 1/2/3/4 분포)
-- =====================================================
WITH category_depth AS (
    SELECT
        product_id,
        category_fullname,
        ARRAY_LENGTH(STRING_TO_ARRAY(category_fullname, '>'), 1) AS depth
    FROM products
    WHERE category_fullname IS NOT NULL
)
SELECT
    depth AS category_depth,
    COUNT(*) AS product_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM category_depth), 2) AS percentage
FROM category_depth
GROUP BY depth
ORDER BY depth;

-- =====================================================
-- 3. 전체 카테고리 트리 구조 (계층적 분포)
-- =====================================================
-- 3-1. Depth 1 (대분류)
SELECT
    SPLIT_PART(category_fullname, '>', 1) AS level_1,
    COUNT(*) AS product_count
FROM products
WHERE category_fullname IS NOT NULL
GROUP BY level_1
ORDER BY product_count DESC;

-- 3-2. Depth 2 (대분류 > 중분류)
SELECT
    SPLIT_PART(category_fullname, '>', 1) AS level_1,
    SPLIT_PART(category_fullname, '>', 2) AS level_2,
    COUNT(*) AS product_count
FROM products
WHERE category_fullname IS NOT NULL
  AND ARRAY_LENGTH(STRING_TO_ARRAY(category_fullname, '>'), 1) >= 2
GROUP BY level_1, level_2
ORDER BY level_1, product_count DESC;

-- 3-3. Depth 3 (대분류 > 중분류 > 소분류)
SELECT
    SPLIT_PART(category_fullname, '>', 1) AS level_1,
    SPLIT_PART(category_fullname, '>', 2) AS level_2,
    SPLIT_PART(category_fullname, '>', 3) AS level_3,
    COUNT(*) AS product_count
FROM products
WHERE category_fullname IS NOT NULL
  AND ARRAY_LENGTH(STRING_TO_ARRAY(category_fullname, '>'), 1) >= 3
GROUP BY level_1, level_2, level_3
ORDER BY level_1, level_2, product_count DESC;

-- 3-4. Depth 4 (대분류 > 중분류 > 소분류 > 세분류)
SELECT
    SPLIT_PART(category_fullname, '>', 1) AS level_1,
    SPLIT_PART(category_fullname, '>', 2) AS level_2,
    SPLIT_PART(category_fullname, '>', 3) AS level_3,
    SPLIT_PART(category_fullname, '>', 4) AS level_4,
    COUNT(*) AS product_count
FROM products
WHERE category_fullname IS NOT NULL
  AND ARRAY_LENGTH(STRING_TO_ARRAY(category_fullname, '>'), 1) >= 4
GROUP BY level_1, level_2, level_3, level_4
ORDER BY level_1, level_2, level_3, product_count DESC;

-- =====================================================
-- 4. 특정 대분류 내 중분류 TOP 10
-- =====================================================
-- 예시: "패션의류" 대분류 내 중분류 분석
SELECT
    SPLIT_PART(category_fullname, '>', 2) AS sub_category,
    COUNT(*) AS product_count,
    ROUND(COUNT(*) * 100.0 / (
        SELECT COUNT(*)
        FROM products
        WHERE category_fullname LIKE '패션의류>%'
    ), 2) AS percentage
FROM products
WHERE category_fullname LIKE '패션의류>%'
  AND ARRAY_LENGTH(STRING_TO_ARRAY(category_fullname, '>'), 1) >= 2
GROUP BY sub_category
ORDER BY product_count DESC
LIMIT 10;

-- =====================================================
-- 5. 카테고리별 평균 가격 분석 (대분류)
-- =====================================================
SELECT
    SPLIT_PART(category_fullname, '>', 1) AS main_category,
    COUNT(*) AS product_count,
    ROUND(AVG(price)::NUMERIC, 0) AS avg_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)::NUMERIC, 0) AS median_price
FROM products
WHERE category_fullname IS NOT NULL
  AND price IS NOT NULL
GROUP BY main_category
ORDER BY avg_price DESC;

-- =====================================================
-- 6. 카테고리별 리뷰 수 분석 (대분류)
-- =====================================================
SELECT
    SPLIT_PART(category_fullname, '>', 1) AS main_category,
    COUNT(*) AS product_count,
    ROUND(AVG(review_count)::NUMERIC, 0) AS avg_reviews,
    ROUND(AVG(rating)::NUMERIC, 2) AS avg_rating,
    COUNT(*) FILTER (WHERE review_count > 100) AS products_with_100plus_reviews
FROM products
WHERE category_fullname IS NOT NULL
GROUP BY main_category
ORDER BY avg_reviews DESC;

-- =====================================================
-- 7. 카테고리 완전성 체크 (NULL 비율)
-- =====================================================
SELECT
    COUNT(*) AS total_products,
    COUNT(*) FILTER (WHERE category_fullname IS NOT NULL) AS with_fullname,
    COUNT(*) FILTER (WHERE category_fullname IS NULL) AS without_fullname,
    ROUND(COUNT(*) FILTER (WHERE category_fullname IS NOT NULL) * 100.0 / COUNT(*), 2) AS completion_rate
FROM products;

-- =====================================================
-- 8. 가장 깊은 카테고리 경로 TOP 10
-- =====================================================
SELECT
    category_fullname,
    ARRAY_LENGTH(STRING_TO_ARRAY(category_fullname, '>'), 1) AS depth,
    COUNT(*) AS product_count
FROM products
WHERE category_fullname IS NOT NULL
GROUP BY category_fullname, depth
ORDER BY depth DESC, product_count DESC
LIMIT 10;

-- =====================================================
-- 9. 카테고리별 브랜드 다양성 (대분류)
-- =====================================================
SELECT
    SPLIT_PART(category_fullname, '>', 1) AS main_category,
    COUNT(DISTINCT brand_name) AS unique_brands,
    COUNT(*) AS product_count,
    ROUND(COUNT(DISTINCT brand_name) * 100.0 / COUNT(*), 2) AS brand_diversity_ratio
FROM products
WHERE category_fullname IS NOT NULL
  AND brand_name IS NOT NULL
GROUP BY main_category
ORDER BY unique_brands DESC;

-- =====================================================
-- 10. 검색태그가 많은 카테고리 TOP 10 (대분류)
-- =====================================================
SELECT
    SPLIT_PART(category_fullname, '>', 1) AS main_category,
    COUNT(*) AS product_count,
    ROUND(AVG(ARRAY_LENGTH(search_tags, 1))::NUMERIC, 2) AS avg_tags_per_product,
    SUM(ARRAY_LENGTH(search_tags, 1)) AS total_tags
FROM products
WHERE category_fullname IS NOT NULL
  AND search_tags IS NOT NULL
GROUP BY main_category
ORDER BY avg_tags_per_product DESC
LIMIT 10;

-- =====================================================
-- 사용 예시 (psql 명령어)
-- =====================================================
-- psql -U postgres -d naver -f database/category_analysis.sql
--
-- 또는 특정 쿼리만 실행:
-- psql -U postgres -d naver -c "SELECT ..."
