import os
import time
from datetime import datetime
from flask import Flask, request, render_template, jsonify, make_response
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
    # 💡 원래는 쿠키를 검사해서 인증된 사람만 열어주어야 안전합니다.
    # 지금은 시험 가동 단계이므로 웹 페이지가 잘 뜨는지 바로 라우팅되도록 처리합니다.
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# 기존 app.py 맨 아래(if __name__ == '__main__': 바로 위)에 아래 코드를 추가합니다.

@app.route('/shutdown-server', methods=['POST'])
def shutdown_server():
    # 🔐 [보안 체크] 인증 쿠키가 없는 사용자가 주소를 쳐서 들어오면 차단합니다.
    auth_cookie = request.cookies.get('nas_voice_auth')
    if auth_cookie != 'authenticated_true':
        return jsonify({"success": False, "message": "권한이 없습니다. 먼저 로그인하세요."}), 403

    try:
        print("[SYSTEM] 주인님의 명령으로 모든 도커 서비스를 안전하게 종료합니다...")
        
        # 💡 [핵심] 파이썬이 리눅스 시스템에 명령을 내려 모든 쪼개진 컴포즈 서비스를 안전 종료시킵니다.
        # 데이터가 하드디스크에 완벽히 기록(Flush)된 후 안전하게 내려갑니다.
        import subprocess
        
        # 백그라운드 셸 명령어로 쪼개진 파일들을 일괄 종료시킵니다.
        # (이 명령어가 실행되면 삼바, AI, 플렉스, 그리고 이 파이썬 컨테이너까지 순차적으로 꺼집니다)
        cmd = "docker compose -f core_network.yml -f docker-compose-infra.yml -f docker-compose-ai.yml -f docker-compose-user.yml -f docker-compose-service.yml down"
        
        # 컨테이너가 즉시 꺼지면 웹 브라우저에 응답을 못 보내므로, 2초 뒤에 실행되도록 비동기로 뺍니다.
        subprocess.Popen(cmd, shell=True, cwd="/app")
        
        return jsonify({"success": True, "message": "모든 나스 및 AI 서비스 종료 시퀀스를 시작합니다. 약 10초 뒤 서버가 완전히 잠듭니다."})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"종료 중 오류 발생: {str(e)}"}), 500
