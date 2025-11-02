#!/bin/bash
# 멀티 태스크 GUI 실행 스크립트 (터미널 독립)
# 사용법: bash scripts/run_multi_gui.sh

echo "=========================================="
echo "Multi-Task GUI Starting (Independent Mode)"
echo "=========================================="
echo ""
echo "터미널을 닫아도 GUI가 계속 실행됩니다."
echo ""

# nohup으로 백그라운드 실행 (터미널 독립)
nohup python3 product_collector_multi_gui.py > logs/multi_gui.log 2>&1 &

PID=$!

echo "✅ GUI 실행 완료!"
echo "PID: $PID"
echo ""
echo "로그 확인: tail -f logs/multi_gui.log"
echo "종료 방법: kill $PID"
echo ""
echo "이제 터미널을 닫아도 GUI가 계속 실행됩니다."
echo "=========================================="
