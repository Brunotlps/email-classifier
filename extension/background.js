const API_BASE = 'https://email-classifier-api.fly.dev/api/v1';
const ANALYZE_MESSAGE_TYPE = 'ANALYZE_EMAIL';

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (!message || message.type !== ANALYZE_MESSAGE_TYPE) return false;

    if (!message.emailText || typeof message.emailText !== 'string') {
        sendResponse({ ok: false, error: 'Conteúdo do email ausente ou inválido.' });
        return false;
    }

    const requestStartedAt = Date.now();
    console.info('[BriskMail] Solicitação de análise recebida.', {
        language: message.language || 'pt',
    });

    fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_content: message.emailText, language: message.language || 'pt' }),
    })
        .then(res => {
            if (!res.ok) throw new Error(`Backend HTTP ${res.status}`);
            return res.json();
        })
        .then(data => {
            console.info('[BriskMail] Análise concluída.', {
                durationMs: Date.now() - requestStartedAt,
            });
            sendResponse({ ok: true, data });
        })
        .catch(err => {
            const errorMessage = err instanceof Error ? err.message : String(err);
            console.error('[BriskMail] Falha ao chamar o backend.', {
                error: errorMessage,
                durationMs: Date.now() - requestStartedAt,
            });
            sendResponse({ ok: false, error: errorMessage });
        });

    return true;
});

console.info('[BriskMail] Background service worker iniciado.');
