#!/bin/bash

echo "======================================"
echo "  한글 폰트 설치 스크립트"
echo "======================================"
echo ""
echo "WSL에 한글 폰트를 설치합니다..."
echo "시스템 비밀번호를 입력해주세요:"
echo ""

# 한글 폰트 설치
sudo apt update
sudo apt install -y fonts-nanum fonts-noto-cjk fonts-noto-cjk-extra

# 폰트 캐시 업데이트
sudo fc-cache -f -v

# 설치 확인
echo ""
echo "설치된 한글 폰트 목록:"
fc-list :lang=ko | head -5

echo ""
echo "======================================"
echo "  폰트 설치 완료!"
echo "======================================"
echo ""
echo "GUI를 다시 실행해보세요."
echo ""
echo "Enter 키를 눌러서 종료하세요..."
read