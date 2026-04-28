const PROCESSED_ATTR = 'data-classifier-seen';

function extractEmailText(container) {
    const emailBody = container.querySelector('div.a3s');
    return emailBody ? emailBody.innerText.trim() : '';
}

function setButtonLoading(button, loading) {
    button.disabled = loading;
    button.textContent = loading ? 'Classificando...' : 'Classificar Email';
}

function renderResultPanel(toolbar, data) {
    const existing = toolbar.parentElement.querySelector('.ec-result-panel');
    if (existing) existing.remove();

    const isProductive = data.classification === 'produtivo';
    const modifier = isProductive ? 'productive' : 'unproductive';
    const badgeLabel = isProductive ? 'Produtivo' : 'Improdutivo';
    const confidencePct = Math.round((data.confidence ?? 0) * 100);

    const panel = document.createElement('div');
    panel.className = 'ec-result-panel';

    panel.innerHTML = `
        <div class="ec-result-header">
            <span class="ec-badge ec-badge--${modifier}">${badgeLabel}</span>
            <span class="ec-confidence">Confiança: ${confidencePct}%</span>
        </div>
        <div class="ec-progress-bar-wrap">
            <div class="ec-progress-bar-fill ec-progress-bar-fill--${modifier}"
                 style="width: ${confidencePct}%"></div>
        </div>
        ${data.suggestions && data.suggestions.length > 0 ? `
            <div class="ec-suggestions-title">Sugestões de resposta</div>
            ${data.suggestions.map(s => `
                <button class="ec-suggestion-item" data-text="${encodeURIComponent(s.content)}">
                    <span class="ec-suggestion-tone">[${s.tone}]</span>${s.content}
                </button>
            `).join('')}
            <div class="ec-copied-hint">Copiado para a área de transferência!</div>
        ` : ''}
    `;

    toolbar.insertAdjacentElement('afterend', panel);

    panel.querySelectorAll('.ec-suggestion-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const text = decodeURIComponent(btn.dataset.text);
            navigator.clipboard.writeText(text).then(() => {
                const hint = panel.querySelector('.ec-copied-hint');
                hint.classList.add('ec-copied-hint--visible');
                setTimeout(() => hint.classList.remove('ec-copied-hint--visible'), 2000);
            });
        });
    });
}

function injectClassifyButton(container) {
    const toolbar = document.createElement('div');
    toolbar.className = 'ec-toolbar';

    const button = document.createElement('button');
    button.className = 'ec-classify-btn';
    button.textContent = 'Classificar Email';

    const label = document.createElement('span');
    label.className = 'ec-toolbar-label';
    label.textContent = 'Email Classifier';

    toolbar.appendChild(button);
    toolbar.appendChild(label);

    const emailBody = container.querySelector('div.a3s');
    if (emailBody) {
        emailBody.parentElement.insertBefore(toolbar, emailBody);
    } else {
        container.prepend(toolbar);
    }

    button.addEventListener('click', async () => {
        const emailText = extractEmailText(container);
        if (!emailText) {
            console.warn('[Email Classifier] Texto do email não encontrado.');
            return;
        }

        setButtonLoading(button, true);

        try {
            const response = await chrome.runtime.sendMessage({
                type: 'CLASSIFY_EMAIL',
                emailText,
            });

            if (!response.ok) throw new Error(response.error);

            renderResultPanel(toolbar, response.data);
        } catch (err) {
            if (err.message.includes('Extension context invalidated')) {
                button.textContent = 'Recarregue a página';
                return;
            }
            console.error('[Email Classifier] Erro na classificação:', err);
        } finally {
            setButtonLoading(button, false);
        }
    });
}

function onEmailDetected(container) {
    const messageId = container.getAttribute('data-message-id');
    console.log('[Email Classifier] Email detectado! data-message-id:', messageId);
    injectClassifyButton(container);
}

function checkForEmails() {
    const containers = document.querySelectorAll(`div[data-message-id]:not([${PROCESSED_ATTR}])`);
    containers.forEach(container => {
        container.setAttribute(PROCESSED_ATTR, 'true');
        onEmailDetected(container);
    });
}

checkForEmails();

const observer = new MutationObserver(checkForEmails);
observer.observe(document.body, { childList: true, subtree: true });

console.log('[Email Classifier] Content script carregado no Gmail.');
