#!/bin/bash

echo "======================================"
echo "  tkinter 설치 스크립트"
echo "======================================"
echo ""
echo "Python3-tk 패키지를 설치합니다..."
echo "시스템 비밀번호를 입력해주세요:"
echo ""

# apt 업데이트 및 tkinter 설치
sudo apt update
sudo apt install -y python3-tk

# 설치 확인
echo ""
echo "설치 확인 중..."
python3 -c "import tkinter; print('✅ tkinter가 성공적으로 설치되었습니다!')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "  설치 완료!"
    echo "======================================"
    echo ""
    echo "이제 GUI 모드를 실행할 수 있습니다."
else
    echo ""
    echo "❌ 설치 실패. 다시 시도해주세요."
    echo "수동으로 설치하려면:"
    echo "sudo apt install python3-tk"
fi

echo ""
echo "Enter 키를 눌러서 종료하세요..."
read