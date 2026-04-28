document.addEventListener('DOMContentLoaded', async () => {
    const dot = document.getElementById('statusDot');
    const label = document.getElementById('statusLabel');

    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        const isGmail = tab?.url?.startsWith('https://mail.google.com');

        if (isGmail) {
            dot.classList.add('status-dot--active');
            label.textContent = 'Ativo no Gmail';
        } else {
            dot.classList.add('status-dot--inactive');
            label.textContent = 'Abra o Gmail para usar';
        }
    } catch {
        dot.classList.add('status-dot--inactive');
        label.textContent = 'Status desconhecido';
    }
});
