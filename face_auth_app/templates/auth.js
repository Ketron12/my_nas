const isRegistered = window.IS_REGISTERED;
let currentLang = localStorage.getItem('nas_lang') || 'ko';

const i18n = {
    ko: {
        titleLogin: "📸 AI Face ID 게이트웨이", titleSetup: "🛠️ 관리자 보안 안면 셋업",
        btnVerify: "👤 Face ID 인증하기", btnRegister: "👤 비밀번호 검증 및 내 얼굴 등록",
        setupAlert: "🔒 <b>서버 초기 셋업 모드</b><br>auto_start.sh 에서 설정한 마스터 비밀번호를 입력해야 내 얼굴을 주인으로 등록할 수 있습니다.",
        statusCamInit: "카메라 조율 중...", statusCamReadyLogin: "정면을 바라본 채 버튼을 누르세요",
        statusCamReadySetup: "위 칸에 암호를 적고 카메라를 정면 응시하세요", statusCamError: "❌ 카메라 장치를 로드할 수 없습니다. (HTTPS 필수)",
        statusAnalyzing: "🤖 AI 안면 특징점 분석 중...", statusSettingUp: "⚙️ 암호 대조 및 안면 지문 빌드 중...",
        passPlaceholder: "2차 비밀번호 입력", setupPassPlaceholder: "초기 셋업 비밀번호 입력",
        btnPass: "확인 및 로그인", alertNoPass: "초기 셋업 비밀번호를 입력해 주세요.",
        msgRegisterSuccess: "마스터 얼굴 등록이 완벽히 완료되었습니다! 이제 Face ID 로그인을 시도하세요.",
        msgMatchSuccess: "✅ Face ID 성공! 시스템 대시보드를 개방합니다.", msgMatchFail: "❌ 일치하지 않는 사용자입니다.",
        msgPassFail: "비밀번호 오류", statusPassNeed: "백업 암호를 입력해 주세요.", statusRegFail: "다시 시도하세요"
    },
    en: {
        titleLogin: "📸 AI Face ID Gateway", titleSetup: "🛠️ Admin Security Face Setup",
        btnVerify: "👤 Authenticate with Face ID", btnRegister: "👤 Verify Password & Register Face",
        setupAlert: "🔒 <b>Initial Server Setup Mode</b><br>Enter the master password set in auto_start.sh to register your face as the owner.",
        statusCamInit: "Initializing camera...", statusCamReadyLogin: "Look straight at the camera and click the button",
        statusCamReadySetup: "Enter password above and look straight at the camera", statusCamError: "❌ Cannot load camera device. (HTTPS required)",
        statusAnalyzing: "🤖 AI analyzing facial features...", statusSettingUp: "⚙️ Verifying password & building face embedding...",
        passPlaceholder: "Enter backup password", setupPassPlaceholder: "Enter setup password",
        btnPass: "Verify & Login", alertNoPass: "Please enter the setup password.",
        msgRegisterSuccess: "Master face registration completed! Now try logging in with Face ID.",
        msgMatchSuccess: "✅ Face ID Match Success! Opening system dashboard.", msgMatchFail: "❌ Authentication failed. Unauthorized user.",
        msgPassFail: "Incorrect password.", statusPassNeed: "Please enter your backup password.", statusRegFail: "Registration failed. Try again."
    }
};

const video = document.getElementById('webcam');
const canvas = document.getElementById('canvas');
const actionBtn = document.getElementById('actionBtn');
const statusDiv = document.getElementById('status');
const resultDiv = document.getElementById('result');
const passwordArea = document.getElementById('passwordArea');
const passBtn = document.getElementById('passBtn');
const mainTitle = document.getElementById('mainTitle');
const setupAlert = document.getElementById('setupAlert');
const toggleLang = document.getElementById('toggleLang');
const setupPassword = document.getElementById('setupPassword');
const backupPassword = document.getElementById('backupPassword');

function renderLang() {
    const t = i18n[currentLang];
    toggleLang.innerText = currentLang === 'ko' ? 'EN' : 'KO';
    backupPassword.placeholder = t.passPlaceholder;
    setupPassword.placeholder = t.setupPassPlaceholder;
    passBtn.innerText = t.btnPass;

    if (isRegistered) {
        mainTitle.innerText = t.titleLogin;
        actionBtn.innerText = t.btnVerify;
        actionBtn.className = "btn-verify";
        setupAlert.style.display = "none";
    } else {
        mainTitle.innerText = t.titleSetup;
        actionBtn.innerText = t.btnRegister;
        actionBtn.className = "btn-register";
        document.getElementById('setupAlertText').innerHTML = t.setupAlert;
        setupAlert.style.display = "block";
    }
}

toggleLang.onclick = () => {
    currentLang = currentLang === 'ko' ? 'en' : 'ko';
    localStorage.setItem('nas_lang', currentLang);
    renderLang();
    initCamera();
};

async function initCamera() {
    const t = i18n[currentLang];
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
        video.srcObject = stream; 
        statusDiv.innerText = isRegistered ? t.statusCamReadyLogin : t.statusCamReadySetup;
    } catch { statusDiv.innerText = t.statusCamError; actionBtn.disabled = true; }
}

renderLang();
initCamera();

actionBtn.onclick = async () => {
    const t = i18n[currentLang];
    resultDiv.style.display = 'none';
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    context.translate(canvas.width, 0); context.scale(-1, 1);
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob(async (blob) => {
        const formData = new FormData();

        if (!isRegistered) {
            const setupPasswordInput = setupPassword.value;
            if (!setupPasswordInput) { alert(t.alertNoPass); return; }
            
            statusDiv.innerText = t.statusSettingUp;
            formData.append('image', blob, 'master.jpg');
            formData.append('password', setupPasswordInput);

            try {
                const response = await fetch('/register-master', { method: 'POST', body: formData });
                const data = await response.json();
                if (data.success) {
                    alert(data.message); window.location.reload();
                } else { alert("❌: " + data.message); statusDiv.innerText = t.statusRegFail; }
            } catch { alert("Server error"); }
            return;
        }

        statusDiv.innerText = t.statusAnalyzing;
        formData.append('image', blob, 'auth_attempt.jpg');
        try {
            const response = await fetch('/verify', { method: 'POST', body: formData });
            const data = await response.json(); resultDiv.style.display = 'block';
            if (data.success && data.is_match) {
                resultDiv.className = "match"; resultDiv.innerHTML = t.msgMatchSuccess;
                setTimeout(() => { window.location.href = "/dashboard"; }, 1500);
            } else {
                resultDiv.className = "fail"; resultDiv.innerHTML = t.msgMatchFail;
                passwordArea.style.display = 'block'; statusDiv.innerText = t.statusPassNeed;
            }
        } catch { alert("Server error"); }
    }, 'image/jpeg');
};

passBtn.onclick = async () => {
    const t = i18n[currentLang];
    const passwordInput = backupPassword.value;
    try {
        const response = await fetch('/verify-password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password: passwordInput }) });
        if (response.ok) { resultDiv.className = "match"; resultDiv.innerHTML = "Success!"; setTimeout(() => { window.location.href = "/dashboard"; }, 1500); }
        else { alert(t.msgPassFail); }
    } catch { alert("Server error"); }
};
