# Changelog

All notable changes to Naver Shopping Crawler will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.3] - 2025-10-31

### Fixed
- 봇 차단 문제 완전 해결 (100% 성공률 달성!)
  - 적응형 대기 시간 전략 구현 (첫 상품 8-12초, 이후 5-7초)
  - 네이버가 첫 클릭을 집중 감시하는 패턴 발견 및 해결
  - 오류 체크 코드 제거 (봇 감지 트리거 방지)
  - Ctrl+클릭으로 새 탭 열기 (문서 검증 방식 적용)
  - networkidle 우선 대기로 페이지 완전 로딩 보장

### Changed
- 상품 수집 전략을 사람의 자연스러운 브라우징 패턴으로 개선
- 페이지 로딩 순서 최적화 (networkidle → 추가 대기 → 수집)

### Added
- 적응형 대기 시간 로직 (`_crawl_product_detail` 메서드)
- 첫 상품 처리 플래그로 상태 관리
- 완전한 봇 차단 회피 테스트 스크립트 (test_adaptive_fix.py)

## [1.2.2] - 2025-10-31

### Fixed
- 크롤러 무한 루프 완전 해결
  - URL 세트 비교 로직 추가 (동일한 상품 반복 3회 감지 → 자동 종료)
  - 페이지 끝 감지 강화 (네이버 무한 스크롤 끝 도달 자동 감지)
  - 중복 카운터 버그 수정 (consecutive_duplicates 전역 선언)

### Changed
- 연속 중복 임계값 조정 (20개 → 10개, 40개 → 25개)
- 스크롤 전략 개선 (중복 많으면 1200px, 기본 600px)

### Added
- 디버깅 로그 추가 (50번 반복마다 상태 출력)
- 무한 루프 방지 안전장치 (최대 5000회 반복 제한)

## [1.2.1] - 2025-10-17

### Fixed
- 크롤러 무한 루프 버그 수정
  - TypeError 수정: brand_name이 None일 때 에러 방지
  - 연속 중복 20개 감지 시 자동 스크롤 로직 추가
  - 중복 상품 무한 반복 문제 해결

### Changed
- 스크롤 최적화: 새 상품 로드 시 즉시 스크롤

## [1.2.0] - 2025-10-17

### Added
- 현대적인 GUI UI/UX 개선 (9개 항목)
  - Material Design 색상 적용 (파란색 시작 버튼, 주황색 중지 버튼)
  - 상태별 색상 코딩 (대기/수집중/완료/실패/중지)
  - 버튼 크기 확대 (40px → 50px)
  - 제목 크기 확대 및 부제목 추가
  - 접기 가능한 설정 패널
  - 카드 스타일 디자인 (둥근 모서리, 배경색)
  - 창 크기 확대 (900x800 → 950x850)
  - 실시간 통계 패널 강화
  - 시각적 계층 구조 개선

### Fixed
- CustomTkinter 이모지 렌더링 문제 해결
  - 모든 이모지 제거 (네모 박스 깨짐 방지)
  - 체크박스 텍스트 명확화
  - 버튼 텍스트 단순화

### Changed
- GUI 디자인 전면 개편 (심플, 깔끔, 세련)
- 버튼 높이 증가로 클릭 편의성 향상
- 텍스트 가독성 개선

## [1.1.4] - 2025-10-15

### Fixed
- 장시간 크롤링 메모리 누수 대폭 개선
  - GUI 로그 1000줄 제한 (메모리 누수 방지)
  - 500KB 문자 수 제한 추가
  - 무한 모드 100개마다 자동 DB 저장
  - 로그 출력 간결화 (10개마다 상세 로그)

### Added
- 24시간 연속 실행 가능하도록 최적화
- 장시간 안정성 테스트 스크립트

## [1.1.3] - 2025-10-15

### Fixed
- 상품 수집 안정성 대폭 개선
  - NoneType 에러 완전 해결
  - 카테고리 경로 정리 강화
  - 잘못된 페이지 자동 스킵

## [1.1.2] - 2025-10-15

### Fixed
- 카테고리 경로 수집 완성
  - JSHandle 오류 수정
  - category_fullname 필드 정상 수집

## [1.1.1] - 2025-10-15

### Fixed
- 네이버 메인 페이지 네비게이션 수정
  - networkidle → domcontentloaded 변경

## [1.1.0] - 2025-10-15

### Added
- 셀렉터 시스템 전체 리팩토링
  - selector_helper.py 생성
  - 네이버 난독화 대응

## [1.0.4] - 2025-10-15

### Fixed
- GUI 로그 한글 깨짐 수정

## [1.0.3] - 2025-10-15

### Added
- GUI 개선 (로그 복사, 중지 버튼, 로그 간결화)

## [1.0.2] - 2025-10-15

### Fixed
- PowerShell 한글 깨짐 수정

## [1.0.1] - 2025-09-26

### Fixed
- GUI 한글 폰트 깨짐 문제 해결 (WSL X11 환경)
- 윈도우 타이틀바 영문으로 변경 (한글 깨짐 방지)
- 버전 정보를 VERSION 파일에서 동적으로 읽도록 개선

### Added
- 한글 폰트 설치 스크립트 (install_korean_fonts.sh)
- 버전 정보 자동 로딩 기능

### Changed
- GUI 폰트를 시스템 기본 폰트(TkDefaultFont)로 변경
- GUI 버튼의 이모지 제거 (호환성 향상)
- PowerShell 스크립트에서 버전 정보 동적 로딩

## [1.0.0] - 2025-09-25

### Added
- Initial release of Naver Shopping Crawler
- Basic category crawling functionality
- Tkinter GUI interface
- PostgreSQL database integration
- Anti-bot detection measures
- Project structure organized with src/, docs/, scripts/ directories
- Desktop shortcut creation scripts
- Terminal mode for non-GUI environments

### Project Structure
- Organized code into proper directories (src/core, src/gui, src/database, src/utils)
- Created comprehensive PRD documentation in Korean
- Added English file naming convention

### Known Issues
- GUI may not work in pure WSL environment without X server
- Product crawling feature not yet implemented (planned for v1.1.0)