const API_URL = 'https://email-classifier-api.fly.dev/api/v1/classify';

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message.type !== 'CLASSIFY_EMAIL') return false;

    fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_content: message.emailText }),
    })
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(data => sendResponse({ ok: true, data }))
        .catch(err => sendResponse({ ok: false, error: err.message }));

    // Retornar true mantém o canal aberto para a resposta assíncrona
    return true;
});

console.log('[Email Classifier] Background service worker iniciado.');
