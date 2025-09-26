# 네이버 쇼핑 크롤러 v1.0

## 📋 기능
- 네이버 쇼핑 카테고리 정보 수집
- 상품명 및 검색 태그 수집
- Tkinter GUI 인터페이스
- PostgreSQL 데이터베이스 저장

## 🚀 설치 방법

### 1. 필수 요구사항
- Python 3.8 이상
- PostgreSQL 데이터베이스
- Chrome 브라우저

### 2. 패키지 설치
```bash
# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 필요 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 3. 데이터베이스 설정
1. PostgreSQL에 'naver' 데이터베이스 생성
2. `.env` 파일 생성 (`.env.example` 참고)
```bash
cp .env.example .env
# .env 파일에서 DB 정보 수정
```
3. 테이블 생성
```bash
psql -U postgres -d naver -f database/create_tables.sql
```

### 4. 실행
```bash
python main.py
```

## 📁 프로젝트 구조
```
Crawl/
├── main.py              # 메인 실행 파일
├── gui.py               # Tkinter GUI
├── category_crawler.py  # 카테고리 크롤러
├── config.py           # 설정 파일
├── .env                # 환경 변수 (생성 필요)
├── requirements.txt    # 의존성 패키지
└── database/
    └── create_tables.sql  # DB 스키마
```

## 🎮 사용 방법
1. GUI에서 크롤링 타입 선택
   - "카테고리만 수집": 카테고리 정보만 수집
   - "카테고리 + 상품 수집": 상품 정보까지 수집
2. "크롤링 시작" 버튼 클릭
3. 실행 로그에서 진행 상황 확인
4. 수집된 데이터는 PostgreSQL DB에 저장됨

## ⚠️ 주의사항
- 네이버 쇼핑의 봇 정책을 준수해주세요
- 과도한 요청은 IP 차단의 원인이 될 수 있습니다
- 크롤링 속도는 config.py에서 조절 가능합니다

## 🐛 문제 해결
- **브라우저가 실행되지 않음**: `playwright install chromium` 재실행
- **DB 연결 오류**: `.env` 파일의 DB 정보 확인
- **카테고리를 찾을 수 없음**: 네이버 쇼핑 페이지 구조 변경 가능성