#!/bin/bash

CORE="core_network.yml"
INFRA="docker-compose-infra.yml"
AI="docker-compose-ai.yml"
USER_SVC="docker-compose-user.yml"
AI_SVC="docker-compose-service.yml"

ALL_FILES="-f $INFRA -f $AI -f $USER_SVC -f $AI_SVC"

# 🔑 [.env 파일 체크 및 비밀번호 동적 생성]
if [ ! -f .env ] || ! grep -q "MASTER_PASSWORD" .env; then
    clear
    echo "===================================================="
    echo "🔒 [초기 세팅] AI 보안 나스 관리자 비밀번호 설정"
    echo "===================================================="
    echo "목소리 인증 실패 시 사용할 2차 백업 비밀번호를 설정하세요."
    read -s -p "🔑 비밀번호 입력: " PASS_1
    echo ""
    read -s -p "🔄 비밀번호 확인: " PASS_2
    echo ""
    
    if [ "$PASS_1" != "$PASS_2" ]; then
        echo "❌ 비밀번호가 일치하지 않습니다. 스크립트를 다시 실행하세요."
        exit 1
    fi
    
    # 깃허브에 노출되지 않는 로컬 .env 파일에 환경변수로 저장
    echo "MASTER_PASSWORD=$PASS_1" > .env
    echo "✅ 비밀번호가 안전하게 로컬 환경 변수로 등록되었습니다!"
    sleep 2
fi

clear
echo "===================================================="
echo "      🛸 미니 PC NAS & AI 서비스 마스터 컨트롤러     "
echo "===================================================="
echo " 1) [START] 모든 그룹 전체 가동"
echo " 2) [STOP] 모든 그룹 전체 종료 (데이터 보존)"
echo " 3) [STATUS] 현재 컨테이너 구동 현황 모니터링"
echo " 4) [RESTART-AI] 로컬 AI 및 목소리 서비스만 재부팅"
echo " 5) [RESET-PASS] 2차 백업 비밀번호 재설정"
echo " 6) [EXIT] 종료"
echo "===================================================="
read -p "원하는 작업 번호를 입력하세요: " CHOICE

case $CHOICE in
    1)
        echo "🌐 공용 가상 네트워크를 개설합니다..."
        docker compose -f $CORE up -d
        echo "🚀 모든 서비스 그룹 전체를 순차 가동합니다..."
        docker compose $ALL_FILES up -d
        echo "✅ 모든 서비스가 백그라운드에서 정상 가동되었습니다."
        ;;
    2)
        echo "🛑 안전하게 모든 컨테이너 서비스를 종료합니다..."
        docker compose $ALL_FILES down
        echo "✅ 모든 서비스가 안전하게 중지되었습니다."
        ;;
    3)
        echo "📊 현재 가동 중인 나스 인프라 현황입니다:"
        docker compose $ALL_FILES ps
        ;;
    4)
        echo "🔄 AI 관련 서비스(Ollama, WebUI, Voice)만 골라서 재시작합니다..."
        docker compose -f $AI -f $AI_SVC restart
        echo "✅ AI 레이어 재부팅 완료."
        ;;
    5)
        rm -f .env
        echo "🔄 기존 비밀번호 설정이 삭제되었습니다. 다음 시작 시 재설정 창이 뜹니다."
        ;;
    6)
        echo "컨트롤러를 닫습니다."
        exit 0
        ;;
    *)
        echo "❌ 잘못된 번호입니다."
        ;;
esac
