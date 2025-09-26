# Changelog

All notable changes to Naver Shopping Crawler will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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