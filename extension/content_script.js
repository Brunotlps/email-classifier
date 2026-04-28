const PROCESSED_ATTR = 'data-classifier-seen';

const PRIORITY_LABEL = { alta: 'Alta prioridade', normal: 'Prioridade normal', baixa: 'Baixa prioridade' };
const PRIORITY_CLASS = { alta: 'ec-priority--high', normal: 'ec-priority--normal', baixa: 'ec-priority--low' };

function extractEmailText(container) {
    const emailBody = container.querySelector('div.a3s');
    return emailBody ? emailBody.innerText.trim() : '';
}

function setButtonLoading(button, loading) {
    button.disabled = loading;
    button.textContent = loading ? 'Analisando...' : 'Analisar Email';
}

function renderResultPanel(toolbar, data) {
    const existing = toolbar.parentElement.querySelector('.ec-result-panel');
    if (existing) existing.remove();

    const panel = document.createElement('div');
    panel.className = 'ec-result-panel';

    const hasSuggestions = data.suggestions && data.suggestions.length > 0;
    const actionLabel = data.action_required ? 'Requer resposta' : 'Sem ação necessária';
    const priorityClass = PRIORITY_CLASS[data.priority] || 'ec-priority--normal';
    const priorityLabel = PRIORITY_LABEL[data.priority] || data.priority;

    panel.innerHTML = `
        <div class="ec-result-header">
            <span class="ec-category-badge">${data.category}</span>
            <span class="ec-priority ${priorityClass}">${priorityLabel}</span>
            <span class="ec-action-tag ${data.action_required ? 'ec-action-tag--yes' : 'ec-action-tag--no'}">${actionLabel}</span>
        </div>
        <p class="ec-summary">${data.summary}</p>
        ${hasSuggestions ? `
            <div class="ec-suggestions-title">Sugestões de resposta</div>
            ${data.suggestions.map(s => `
                <button class="ec-suggestion-item" data-text="${encodeURIComponent(s.content)}">
                    <span class="ec-suggestion-tone">[${s.tone}]</span>
                    <span class="ec-suggestion-title">${s.title}</span>
                    <span class="ec-suggestion-preview">${s.content}</span>
                </button>
            `).join('')}
            <div class="ec-copied-hint">Copiado para a área de transferência!</div>
        ` : ''}
    `;

    toolbar.insertAdjacentElement('afterend', panel);

    panel.querySelectorAll('.ec-suggestion-item').forEach(btn => {
        btn.addEventListener('click', () => {
            navigator.clipboard.writeText(decodeURIComponent(btn.dataset.text)).then(() => {
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
    button.textContent = 'Analisar Email';

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
                type: 'ANALYZE_EMAIL',
                emailText,
            });

            if (!response.ok) throw new Error(response.error);

            renderResultPanel(toolbar, response.data);
        } catch (err) {
            if (err.message.includes('Extension context invalidated')) {
                button.textContent = 'Recarregue a página';
                return;
            }
            console.error('[Email Classifier] Erro na análise:', err);
        } finally {
            setButtonLoading(button, false);
        }
    });
}

function onEmailDetected(container) {
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
