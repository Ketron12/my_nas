import os
from flask import Flask, request, render_template, jsonify
from speechbrain.inference.speaker import SpeakerRecognition

app = Flask(__name__)
UPLOAD_FOLDER = '/app/voice_data'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 🤖 내장된 오픈소스 화자 인식 AI 모델 로드 (최초 실행 시 자동 다운로드)
verification = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="pretrained_models")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify', methods=['POST'])
def verify_voice():
    if 'audio' not in request.files:
        return jsonify({"success": False, "message": "음성 파일이 없습니다."}), 400
    
    file = request.files['audio']
    auth_path = os.path.join(app.config['UPLOAD_FOLDER'], "auth_attempt.wav")
    file.save(auth_path)
    
    # 💡 기준이 되는 주인의 목소리 파일 (사전에 voice_data/master.wav로 저장해 두어야 합니다)
    master_path = os.path.join(app.config['UPLOAD_FOLDER'], "master.wav")
    
    if not os.path.exists(master_path):
        return jsonify({"success": False, "message": "기준 주인 목소리(master.wav)가 등록되지 않았습니다."}), 400

    try:
        # AI 모델로 두 음성 파일의 유사도(Score) 측정 및 판별
        score, prediction = verification.verify_files(master_path, auth_path)
        
        # prediction은 Boolean 결과값 (True: 동일인, False: 타인)
        is_match = bool(prediction[0])
        confidence = float(score[0])
        
        return jsonify({
            "success": True,
            "is_match": is_match,
            "confidence_score": confidence,
            "message": "본인 확인 완료" if is_match else "목소리가 일치하지 않습니다."
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)