import os
import time
from datetime import datetime
from flask import Flask, request, render_template, jsonify, make_response
from speechbrain.inference.speaker import SpeakerRecognition

app = Flask(__name__)
UPLOAD_FOLDER = '/app/voice_data'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 🔐실패 시 로그인을 허용할 2차 마스터 패스워드
MASTER_PASSWORD = "my_secure_password_123"

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
