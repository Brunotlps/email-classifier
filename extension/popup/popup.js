const STRINGS = {
    pt: {
        subtitle: 'Análise inteligente de emails',
        statusActive: 'Ativo no Gmail',
        statusInactive: 'Abra o Gmail para usar',
        statusUnknown: 'Status desconhecido',
        howToTitle: 'Como usar',
        step1: 'Abra um email no Gmail',
        step2: 'Clique no botão <strong>Analisar Email</strong>',
        step3: 'Veja o resumo, categoria e sugestões de resposta',
        webLink: 'Abrir versão web →',
    },
    en: {
        subtitle: 'Intelligent email analysis',
        statusActive: 'Active on Gmail',
        statusInactive: 'Open Gmail to use',
        statusUnknown: 'Unknown status',
        howToTitle: 'How to use',
        step1: 'Open an email in Gmail',
        step2: 'Click the <strong>Analyze Email</strong> button',
        step3: 'See the summary, category and reply suggestions',
        webLink: 'Open web version →',
    },
};

function applyStrings(lang) {
    const s = STRINGS[lang] || STRINGS.pt;
    document.getElementById('headerSubtitle').textContent = s.subtitle;
    document.getElementById('howToTitle').textContent = s.howToTitle;
    document.getElementById('step1').textContent = s.step1;
    document.getElementById('step2').innerHTML = s.step2;
    document.getElementById('step3').textContent = s.step3;
    document.getElementById('webLink').textContent = s.webLink;

    document.getElementById('langPt').classList.toggle('lang-btn--active', lang === 'pt');
    document.getElementById('langEn').classList.toggle('lang-btn--active', lang === 'en');

    document.documentElement.lang = lang === 'pt' ? 'pt-BR' : 'en';
}

async function updateStatus(lang) {
    const s = STRINGS[lang] || STRINGS.pt;
    const dot = document.getElementById('statusDot');
    const label = document.getElementById('statusLabel');

    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        const isGmail = tab?.url?.startsWith('https://mail.google.com');
        dot.className = 'status-dot ' + (isGmail ? 'status-dot--active' : 'status-dot--inactive');
        label.textContent = isGmail ? s.statusActive : s.statusInactive;
    } catch {
        dot.className = 'status-dot status-dot--inactive';
        label.textContent = s.statusUnknown;
    }
}

function setLanguage(lang) {
    chrome.storage.sync.set({ briskmail_language: lang }, () => {
        applyStrings(lang);
        updateStatus(lang);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    chrome.storage.sync.get({ briskmail_language: 'pt' }, ({ briskmail_language: lang }) => {
        applyStrings(lang);
        updateStatus(lang);
    });

    document.getElementById('langPt').addEventListener('click', () => setLanguage('pt'));
    document.getElementById('langEn').addEventListener('click', () => setLanguage('en'));
});
