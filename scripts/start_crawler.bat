@echo off
REM 네이버 쇼핑 크롤러 실행 스크립트
REM 더블클릭으로 실행하세요

echo ============================================
echo 네이버 쇼핑 상품 수집기 시작
echo ============================================
echo.

REM 현재 디렉토리를 스크립트 위치로 변경
cd /d "%~dp0\.."

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되지 않았습니다.
    echo Python 3.10 이상을 설치하세요: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [확인] Python 설치됨
echo.

REM GUI 실행 (멀티 태스크 버전 - 최신)
echo [실행] GUI 시작 중...
python product_collector_multi_gui.py

REM 오류 발생 시 창 유지
if errorlevel 1 (
    echo.
    echo [오류] 프로그램 실행 중 오류 발생
    pause
)
