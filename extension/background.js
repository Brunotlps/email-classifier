const API_BASE = 'https://email-classifier-api.fly.dev/api/v1';

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message.type !== 'ANALYZE_EMAIL') return false;

    fetch(`${API_BASE}/analyze`, {
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

    return true;
});

console.log('[Email Classifier] Background service worker iniciado.');
