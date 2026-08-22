let currentLang = localStorage.getItem('nas_lang') || 'ko';

const i18n = {
    ko: {
        dashTitle: "🛸 내 미니 PC 개인 홈 서버", dashSubtitle: "보안 게이트웨이가 인증한 안전한 가상 공간입니다.",
        c1Title: "개인 클라우드", c1Desc: "웹 파일 탐색기입니다. 자유롭게 파일을 관리하세요.",
        c2Title: "플렉스 미디어", c2Desc: "영화 및 미디어를 집안 어디서든 스트리밍합니다.",
        c3Title: "로컬 AI 챗봇", c3Desc: "외부 유출 없는 강력한 내 개인 전용 AI와 대화합니다.",
        c4Title: "사진 클라우드", c4Desc: "모바일 백그라운드 사진 자동 백업 구글 포토입니다.",
        mCpu: "CPU 사용량", mRam: "RAM 사용량", mUsed: "사용 중",
        btnShutdown: "🔴 미니 PC 본체 전원 차단", confirmShutdown: "⚠️ 미니 PC 본체 하드웨어 전원을 완전히 차단하시겠습니까?"
    },
    en: {
        dashTitle: "🛸 My Mini PC Home Server", dashSubtitle: "Secure virtual space authenticated by Face ID Gateway.",
        c1Title: "Private Cloud", c1Desc: "Web file explorer. Manage your files freely anytime.",
        c2Title: "Plex Media", c2Desc: "Stream movies and media anywhere inside your home.",
        c3Title: "Local AI Chatbot", c3Desc: "Chat with private AI models with zero data leaks.",
        c4Title: "Photo Cloud", c4Desc: "Google Photos alternative with mobile auto background sync.",
        mCpu: "CPU Usage", mRam: "RAM Usage", mUsed: "In Use",
        btnShutdown: "🔴 Shutdown Mini PC Power", confirmShutdown: "⚠️ Are you sure you want to completely shutdown the Mini PC hardware?"
    }
};

const toggleLang = document.getElementById('toggleLang');
const dashTitle = document.getElementById('dashTitle');
const dashSubtitle = document.getElementById('dashSubtitle');
const c1Title = document.getElementById('c1Title'); const c1Desc = document.getElementById('c1Desc');
const c2Title = document.getElementById('c2Title'); const c2Desc = document.getElementById('c2Desc');
const c3Title = document.getElementById('c3Title'); const c3Desc = document.getElementById('c3Desc');
const c4Title = document.getElementById('c4Title'); const c4Desc = document.getElementById('c4Desc');
const mCpu = document.getElementById('mCpu'); const mRam = document.getElementById('mRam');
const shutdownBtn = document.getElementById('shutdownBtn'); const secretTrigger = document.getElementById('secretTrigger');
const modal = document.getElementById('monitorModal'); const monitorBtn = document.getElementById('monitorBtn'); const closeModal = document.getElementById('closeModal');
const cpuText = document.getElementById('cpuText'); const cpuBar = document.getElementById('cpuBar');
const ramText = document.getElementById('ramText'); const ramBar = document.getElementById('ramBar'); const ramDetails = document.getElementById('ramDetails');

function renderLang() {
    const t = i18n[currentLang];
    toggleLang.innerText = currentLang === 'ko' ? 'EN' : 'KO';
    dashTitle.innerText = t.dashTitle; dashSubtitle.innerText = t.dashSubtitle;
    c1Title.innerText = t.c1Title; c1Desc.innerText = t.c1Desc;
    c2Title.innerText = t.c2Title; c2Desc.innerText = t.c2Desc;
    c3Title.innerText = t.c3Title; c3Desc.innerText = t.c3Desc;
    c4Title.innerText = t.c4Title; c4Desc.innerText = t.c4Desc;
    mCpu.innerText = t.mCpu; mRam.innerText = t.mRam;
    shutdownBtn.innerText = t.btnShutdown;
}

toggleLang.onclick = () => {
    currentLang = currentLang === 'ko' ? 'en' : 'ko';
    localStorage.setItem('nas_lang', currentLang);
    renderLang();
};

let clickCount = 0;
secretTrigger.onclick = () => {
    clickCount++;
    if (clickCount === 3) { clickCount = 0; window.open("http://localhost:3005", "_blank"); }
    setTimeout(() => { clickCount = 0; }, 3000);
};

let updateInterval = null;

async function updateStats() {
    try {
        const res = await fetch('/system-status');
        const data = await res.json();
        if (data.success) {
            const t = i18n[currentLang];
            cpuText.innerText = data.cpu + "%"; cpuBar.style.width = data.cpu + "%";
            ramText.innerText = data.ram + "%"; ramBar.style.width = data.ram + "%";
            ramDetails.innerText = `${data.ram_used_gb} GB / ${data.ram_total_gb} GB ${t.mUsed}`;
        }
    } catch (e) { console.error(e); }
}

monitorBtn.onclick = () => { modal.style.display = 'flex'; updateStats(); updateInterval = setInterval(updateStats, 1000); };
closeModal.onclick = () => { modal.style.display = 'none'; clearInterval(updateInterval); };
window.onclick = (e) => { if (e.target == modal) { modal.style.display = 'none'; clearInterval(updateInterval); } };

renderLang();

shutdownBtn.onclick = async () => {
    const t = i18n[currentLang];
    if (!confirm(t.confirmShutdown)) return;
    try {
        await fetch('/shutdown-server', { method: 'POST' });
        document.body.innerHTML = "<h2>🔒 System Shutdown Complete</h2>";
    } catch { document.body.innerHTML = "<h2>🔒 System Shutdown Complete</h2>"; }
};
