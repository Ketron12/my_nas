import os
import time
from datetime import datetime
import psutil
import face_recognition
from flask import Flask, request, render_template, jsonify, make_response, redirect, url_for

app = Flask(__name__)
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

@app.route('/')
def index():
    return render_template('index.html')

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
        return jsonify({"success": False, "message": "master.jpg 가 누락되었습니다."}), 400

    try:
        master_image = face_recognition.load_image_file(master_path)
        attempt_image = face_recognition.load_image_file(auth_path)
        
        master_encodings = face_recognition.face_encodings(master_image)
        attempt_encodings = face_recognition.face_encodings(attempt_image)
        
        if not master_encodings or not attempt_encodings:
            return jsonify({"success": True, "is_match": False, "message": "얼굴 각도나 조명을 조절해 주세요."})

        is_match = face_recognition.compare_faces([master_encodings[0]], attempt_encodings[0], tolerance=0.55)
        
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
        cpu_usage = psutil.cpu_percentage(interval=None)
        ram = psutil.virtual_memory()
        return jsonify({
            "success": True, "cpu": cpu_usage, "ram": ram.percent,
            "ram_used_gb": round(ram.used / (1024**3), 2), "ram_total_gb": round(ram.total / (1024**3), 2)
        })
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route('/shutdown-server', methods=['POST'])
def shutdown_server():
    auth_cookie = request.cookies.get('nas_voice_auth')
    if auth_cookie != 'authenticated_true': return jsonify({"success": False}), 403
    try:
        import subprocess
        cmd = "docker compose -f docker-compose-infra.yml -f docker-compose-ai.yml -f docker-compose-user.yml -f docker-compose-archive.yml -f docker-compose-service.yml down && poweroff"
        subprocess.Popen(cmd, shell=True, cwd="/app")
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)