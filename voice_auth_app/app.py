import os
import time
from datetime import datetime
import psutil  # 💡 추가
from flask import Flask, request, render_template, jsonify, make_response, redirect, url_for
from speechbrain.inference.speaker import SpeakerRecognition


app = Flask(__name__)
UPLOAD_FOLDER = '/app/voice_data'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 🔐 [보안 강화] 소스 코드에서 비밀번호를 지우고, 도커 환경변수에서 동적으로 가져옵니다.
# 만약 환경변수가 비어있다면 에러 방지를 위해 기본 임시 비밀번호를 할당합니다.
MASTER_PASSWORD = os.environ.get("MASTER_PASSWORD", "default_fallback_pass_123")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

verification = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", 
    savedir="pretrained_models"
)

def delete_old_files():
    now = time.time()
    seconds_in_60_days = 60 * 24 * 60 * 60
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename == "master.wav": continue
        if filename.startswith("auth_") and filename.endswith(".wav"):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if (now - os.path.getmtime(file_path)) > seconds_in_60_days:
                try: os.remove(file_path)
                except: pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify', methods=['POST'])
def verify_voice():
    delete_old_files()
    if 'audio' not in request.files:
        return jsonify({"success": False, "message": "데이터 오류"}), 400
    
    file = request.files['audio']
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    auth_filename = f"auth_{timestamp}.wav"
    auth_path = os.path.join(app.config['UPLOAD_FOLDER'], auth_filename)
    file.save(auth_path)
    
    master_path = os.path.join(app.config['UPLOAD_FOLDER'], "master.wav")
    if not os.path.exists(master_path):
        return jsonify({"success": False, "message": "master.wav가 없습니다."}), 400

    try:
        score, prediction = verification.verify_files(master_path, auth_path)
        is_match = bool(prediction)
        confidence = float(score)
        
        if is_match:
            response = make_response(jsonify({"success": True, "is_match": True, "confidence_score": confidence}))
            response.set_cookie('nas_voice_auth', 'authenticated_true', max_age=86400, httponly=True)
            return response
        else:
            return jsonify({"success": True, "is_match": False, "confidence_score": confidence})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/verify-password', methods=['POST'])
def verify_password():
    data = request.get_json()
    if data.get("password") == MASTER_PASSWORD:
        response = make_response(jsonify({"success": True}))
        response.set_cookie('nas_voice_auth', 'authenticated_true', max_age=86400, httponly=True)
        return response
    return jsonify({"success": False, "message": "비밀번호 오류"}), 401

@app.route('/dashboard')
def dashboard():
    # 1. 브라우저에서 'nas_voice_auth' 쿠키 값을 긁어옵니다.
    auth_cookie = request.cookies.get('nas_voice_auth')
    
    # 2. 쿠키가 아예 없거나, 값이 우리가 설정한 'authenticated_true'가 아니라면 위조범입니다.
    if not auth_cookie or auth_cookie != 'authenticated_true':
        print("[보안 경고] 인증되지 않은 사용자가 대시보드 직공격을 시도하여 대문으로 추방합니다.")
        # 🚪 가차 없이 첫 대문 로그인 화면('/')으로 튕겨버립니다.
        return redirect(url_for('index'))
    
    # 3. 쿠키가 완벽하게 일치하는 검증된 주인님만 대시보드 화면을 열어줍니다.
    return render_template('dashboard.html')

@app.route('/system-status', methods=['GET'])
def system_status():
    auth_cookie = request.cookies.get('nas_voice_auth')
    if not auth_cookie or auth_cookie != 'authenticated_true':
        return jsonify({"success": False, "message": "권한이 없습니다. 해킹 시도가 감지되었습니다."}), 403

    try:
        cpu_usage = psutil.cpu_percentage(interval=None)
        ram = psutil.virtual_memory()
        return jsonify({
            "success": True,
            "cpu": cpu_usage,
            "ram": ram.percent,
            "ram_used_gb": round(ram.used / (1024**3), 2),
            "ram_total_gb": round(ram.total / (1024**3), 2)
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# 기존 app.py 맨 아래(if __name__ == '__main__': 바로 위)에 아래 코드를 추가합니다.

# app.py 의 shutdown_server 함수 내부 cmd 변수 부분만 아래 코드로 교체해 줍니다.

@app.route('/shutdown-server', methods=['POST'])
def shutdown_server():
    auth_cookie = request.cookies.get('nas_voice_auth')
    if auth_cookie != 'authenticated_true':
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    try:
        print("[SYSTEM] 주인님의 명령으로 미니 PC 본체 전원 오프 시퀀스를 가동합니다...")
        import subprocess
        
        # 💡 [치트키] 1. 도커 컨테이너들을 3초 이내에 안전하게 싹 정리한 뒤
        #            2. 리눅스 호스트 시스템 자체를 즉시 완전 종료(poweroff) 시켜 본체 전원을 차단합니다.
        cmd = "docker compose -f core_network.yml -f docker-compose-infra.yml -f docker-compose-ai.yml -f docker-compose-user.yml -f docker-compose-service.yml down && poweroff"
        
        # 비동기로 시스템 명령어를 던집니다.
        subprocess.Popen(cmd, shell=True, cwd="/app")
        
        return jsonify({"success": True, "message": "서버 안전 종료 및 미니 PC 본체 전원 오프 시퀀스를 시작합니다. 약 10초 뒤 기기가 완전히 꺼집니다."})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"오류 발생: {str(e)}"}), 500

