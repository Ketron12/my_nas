#!/bin/bash
cd /home/ubuntu/nas_project

# 🔑 [.env 파일이 없거나 필수 값이 비어있다면 초기 비밀 세팅 시퀀스 가동]
if [ ! -f .env ] || ! grep -q "MASTER_PASSWORD" .env || ! grep -q "DUCKDNS_TOKEN" .env; then
    clear
    echo "===================================================="
    echo "🔒 [최초 부팅 세팅] 홈 서버 마스터 보안 셋업"
    echo "===================================================="
    
    # 1. 2차 백업 패스워드 입력받기 (보안을 위해 입력창에는 글자가 표시되지 않습니다)
    read -s -p "🔑 1. Face ID 실패 시 사용할 2차 백업 비밀번호 입력: " PASS_1
    echo ""
    read -s -p "🔄 비밀번호 확인 다시 입력: " PASS_2
    echo ""
    
    if [ "$PASS_1" != "$PASS_2" ]; then
        echo "❌ 비밀번호가 일치하지 않습니다. 스크립트를 다시 가동하세요."
        exit 1
    fi
    
    # 2. DuckDNS 토큰 값 입력받기
    echo "----------------------------------------------------"
    echo "🦆 DuckDNS 홈페이지에서 발급받은 마스터 토큰(Token)을"
    echo "   마우스 우클릭으로 복사·붙여넣기 하세요."
    echo "----------------------------------------------------"
    read -p "🎫 2. DuckDNS 고유 토큰 값 입력: " DELEGATE_TOKEN
    echo ""
    
    if [ -z "$DELEGATE_TOKEN" ]; then
        echo "❌ 토큰 값이 비어있습니다. 세팅을 취소합니다."
        exit 1
    fi
    
    # 🔒 깃허브 업로드에서 제외되는 숨김 .env 파일에 환경변수로 철저히 격리 저장
    echo "MASTER_PASSWORD=$PASS_1" > .env
    echo "DUCKDNS_TOKEN=$DELEGATE_TOKEN" >> .env
    
    echo "===================================================="
    echo "✅ 성공: 마스터 패스워드 및 토큰 동적 주입 완료!"
    echo "===================================================="
    sleep 3
fi

# 📂 필수 물리 저장소 디렉토리 사전 감지 및 자동 빌드
mkdir -p face_data nas_data immich_data nas_data/Archive

# 🌐 공용 가상 네트워크 통로 개설
docker network create nas_core_net 2>/dev/null

# 🚀 5대 서비스 레이어 완전체 백그라운드 동시 기동!
docker compose -f docker-compose-infra.yml -f docker-compose-ai.yml -f docker-compose-user.yml -f docker-compose-archive.yml -f docker-compose-service.yml up -d
