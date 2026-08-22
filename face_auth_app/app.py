import os
import time
from datetime import datetime
import psutil
import face_recognition
from flask import Flask, request, render_template, jsonify, make_response, redirect, url_for

app = Flask(__name__, static_folder='templates', static_url_path='/templates')
UPLOAD_FOLDER = '/app/face_data'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

MASTER_PASSWORD = os.environ.get("MASTER_PASSWORD", "default_fallback_pass_123")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def delete_old_files():
    now = time.time()
    seconds_in_60_days = 60 * 24 * 60 * 60
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename == "master.jpg": continue
        if filename.startswith("auth_") and filename.endswith(".jpg"):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if (now - os.path.getmtime(file_path)) > seconds_in_60_days:
                try: os.remove(file_path)
                except: pass

# 🚪 대문 페이지: master.jpg 유무에 따라 로그인 또는 등록 화면 동적 스위칭
@app.route('/')
def index():
    master_path = os.path.join(app.config['UPLOAD_FOLDER'], "master.jpg")
    # 💡 주인 사진이 아직 없다면 초기 등록 상태 신호를 프론트엔드로 전달
    is_registered = os.path.exists(master_path)
    return render_template('index.html', is_registered=is_registered)

# app.py 내부의 register_master 함수 부분을 아래 코드로 교체해 줍니다.

@app.route('/register-master', methods=['POST'])
def register_master():
    master_path = os.path.join(app.config['UPLOAD_FOLDER'], "master.jpg")
    
    # 🛡️ 1차 방어: 이미 주인이 등록되어 있다면 초기화 차단
    if os.path.exists(master_path):
        return jsonify({"success": False, "message": "이미 관리자가 등록되어 있습니다."}), 400
        
    # 🛡️ 2차 방어: 요청 데이터에서 이미지와 비밀번호를 긁어옵니다.
    if 'image' not in request.files or 'password' not in request.form:
        return jsonify({"success": False, "message": "인증 데이터 또는 사진이 누락되었습니다."}), 400
        
    user_password = request.form.get('password', '')
    
    # 💡 [핵심] auto_start.sh로 세팅한 마스터 암호와 일치하는지 철저히 대조
    if user_password != MASTER_PASSWORD:
        return jsonify({"success": False, "message": "초기 세팅 비밀번호가 일치하지 않아 관리자 등록이 거부되었습니다."}), 401
        
    file = request.files['image']
    file.save(master_path)
    
    # 등록된 사진에 진짜 사람 얼굴이 있는지 검증
    try:
        img = face_recognition.load_image_file(master_path)
        encodings = face_recognition.face_encodings(img)
        if not encodings:
            os.remove(master_path) # 얼굴 인식 실패 시 파일 즉각 삭제
            return jsonify({"success": False, "message": "사진에서 얼굴 특징점을 찾지 못했습니다. 정면을 똑바로 바라보고 다시 촬영해 주세요."})
            
        print("[SECURITY-SUCCESS] 🌌 주인의 비밀번호 인증 통과 및 최초 Face ID 지문 빌드가 완료되었습니다.")
        return jsonify({"success": True, "message": "마스터 얼굴 등록이 완벽히 완료되었습니다! 이제 Face ID 로그인을 시도하세요."})
    except Exception as e:
        if os.path.exists(master_path): os.remove(master_path)
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/dashboard')
def dashboard():
    auth_cookie = request.cookies.get('nas_voice_auth')
    if not auth_cookie or auth_cookie != 'authenticated_true':
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/verify', methods=['POST'])
def verify_face():
    delete_old_files()
    if 'image' not in request.files:
        return jsonify({"success": False, "message": "사진 데이터 오류"}), 400
    
    file = request.files['image']
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    auth_filename = f"auth_{timestamp}.jpg"
    auth_path = os.path.join(app.config['UPLOAD_FOLDER'], auth_filename)
    file.save(auth_path)
    
    master_path = os.path.join(app.config['UPLOAD_FOLDER'], "master.jpg")
    if not os.path.exists(master_path):
        return jsonify({"success": False, "message": "서버 초기 등록이 완료되지 않았습니다."}), 400

    try:
        master_image = face_recognition.load_image_file(master_path)
        attempt_image = face_recognition.load_image_file(auth_path)
        
        master_encodings = face_recognition.face_encodings(master_image)
        attempt_encodings = face_recognition.face_encodings(attempt_image)
        
        if not master_encodings or not attempt_encodings:
            return jsonify({"success": True, "is_match": False, "message": "얼굴 각도를 조절해 주세요."})

        is_match = face_recognition.compare_faces([master_encodings], attempt_encodings, tolerance=0.55)
        
        if is_match:
            response = make_response(jsonify({"success": True, "is_match": True}))
            response.set_cookie('nas_voice_auth', 'authenticated_true', max_age=86400, httponly=True)
            return response
        else:
            return jsonify({"success": True, "is_match": False})
            
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

@app.route('/system-status', methods=['GET'])
def system_status():
    auth_cookie = request.cookies.get('nas_voice_auth')
    if not auth_cookie or auth_cookie != 'authenticated_true': return jsonify({"success": False}), 403
    try:
        return jsonify({"success": True, "cpu": psutil.cpu_percentage(), "ram": psutil.virtual_memory().percent, "ram_used_gb": round(psutil.virtual_memory().used / (1024**3), 2), "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2)})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route('/shutdown-server', methods=['POST'])
def shutdown_server():
    auth_cookie = request.cookies.get('nas_voice_auth')
    if auth_cookie != 'authenticated_true': return jsonify({"success": False}), 403
    import subprocess
    cmd = "docker compose -f docker-compose-infra.yml -f docker-compose-ai.yml -f docker-compose-user.yml -f docker-compose-archive.yml -f docker-compose-service.yml down && poweroff"
    subprocess.Popen(cmd, shell=True, cwd="/app")
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
