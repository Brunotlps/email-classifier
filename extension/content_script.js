const PROCESSED_ATTR = 'data-briskmail-seen';

const STRINGS = {
    pt: {
        button: 'Analisar Email',
        buttonLoading: 'Analisando...',
        buttonReload: 'Recarregue a página',
        label: 'BriskMail',
        priorityLabel: { alta: 'Alta prioridade', normal: 'Prioridade normal', baixa: 'Baixa prioridade' },
        actionRequired: 'Requer resposta',
        actionNotRequired: 'Sem ação necessária',
        suggestionsTitle: 'Sugestões de resposta',
        copied: 'Copiado para a área de transferência!',
        categoryMap: {
            'Proposta Comercial': 'Proposta Comercial',
            'Reunião / Agenda': 'Reunião / Agenda',
            'Suporte Técnico': 'Suporte Técnico',
            'Cobrança / Pagamento': 'Cobrança / Pagamento',
            'Newsletter / Marketing': 'Newsletter / Marketing',
            'Feedback / Avaliação': 'Feedback / Avaliação',
            'Pessoal / Casual': 'Pessoal / Casual',
            'Alerta / Notificação': 'Alerta / Notificação',
            'Candidatura / RH': 'Candidatura / RH',
            'Outro': 'Outro',
        },
    },
    en: {
        button: 'Analyze Email',
        buttonLoading: 'Analyzing...',
        buttonReload: 'Reload the page',
        label: 'BriskMail',
        priorityLabel: { alta: 'High priority', normal: 'Normal priority', baixa: 'Low priority' },
        actionRequired: 'Action required',
        actionNotRequired: 'No action needed',
        suggestionsTitle: 'Reply suggestions',
        copied: 'Copied to clipboard!',
        categoryMap: {
            'Proposta Comercial': 'Business Proposal',
            'Reunião / Agenda': 'Meeting / Schedule',
            'Suporte Técnico': 'Technical Support',
            'Cobrança / Pagamento': 'Billing / Payment',
            'Newsletter / Marketing': 'Newsletter / Marketing',
            'Feedback / Avaliação': 'Feedback / Review',
            'Pessoal / Casual': 'Personal / Casual',
            'Alerta / Notificação': 'Alert / Notification',
            'Candidatura / RH': 'Job Application / HR',
            'Outro': 'Other',
        },
    },
};

const PRIORITY_CLASS = { alta: 'ec-priority--high', normal: 'ec-priority--normal', baixa: 'ec-priority--low' };

function extractEmailText(container) {
    const emailBody = container.querySelector('div.a3s');
    return emailBody ? emailBody.innerText.trim() : '';
}

function setButtonLoading(button, loading, s) {
    button.disabled = loading;
    button.textContent = loading ? s.buttonLoading : s.button;
}

function renderResultPanel(toolbar, data, s) {
    const existing = toolbar.parentElement.querySelector('.ec-result-panel');
    if (existing) existing.remove();

    const panel = document.createElement('div');
    panel.className = 'ec-result-panel';

    const hasSuggestions = data.suggestions && data.suggestions.length > 0;
    const priorityClass = PRIORITY_CLASS[data.priority] || 'ec-priority--normal';
    const priorityLabel = s.priorityLabel[data.priority] || data.priority;
    const actionLabel = data.action_required ? s.actionRequired : s.actionNotRequired;
    const categoryLabel = s.categoryMap[data.category] || data.category;

    panel.innerHTML = `
        <div class="ec-result-header">
            <img class="ec-brand-icon" src="${chrome.runtime.getURL('assets/icon48.png')}" alt="BriskMail">
            <span class="ec-category-badge">${categoryLabel}</span>
            <span class="ec-priority ${priorityClass}">${priorityLabel}</span>
            <span class="ec-action-tag ${data.action_required ? 'ec-action-tag--yes' : 'ec-action-tag--no'}">${actionLabel}</span>
        </div>
        <p class="ec-summary">${data.summary}</p>
        ${hasSuggestions ? `
            <div class="ec-suggestions-title">${s.suggestionsTitle}</div>
            ${data.suggestions.map(sg => `
                <button class="ec-suggestion-item" data-text="${encodeURIComponent(sg.content)}">
                    <span class="ec-suggestion-tone">[${sg.tone}]</span>
                    <span class="ec-suggestion-title">${sg.title}</span>
                    <span class="ec-suggestion-preview">${sg.content}</span>
                </button>
            `).join('')}
            <div class="ec-copied-hint">${s.copied}</div>
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

function injectClassifyButton(container, lang) {
    const s = STRINGS[lang] || STRINGS.pt;

    const toolbar = document.createElement('div');
    toolbar.className = 'ec-toolbar';

    const button = document.createElement('button');
    button.className = 'ec-classify-btn';
    button.textContent = s.button;

    toolbar.appendChild(button);

    const emailBody = container.querySelector('div.a3s');
    if (emailBody) {
        emailBody.parentElement.insertBefore(toolbar, emailBody);
    } else {
        container.prepend(toolbar);
    }

    button.addEventListener('click', async () => {
        const emailText = extractEmailText(container);
        if (!emailText) {
            console.warn('[BriskMail] Texto do email não encontrado.');
            return;
        }

        setButtonLoading(button, true, s);

        try {
            const response = await chrome.runtime.sendMessage({
                type: 'ANALYZE_EMAIL',
                emailText,
                language: lang,
            });

            if (!response.ok) throw new Error(response.error);

            renderResultPanel(toolbar, response.data, s);
        } catch (err) {
            if (err.message && err.message.includes('Extension context invalidated')) {
                button.textContent = s.buttonReload;
                return;
            }
            console.error('[BriskMail] Erro na análise:', err);
        } finally {
            setButtonLoading(button, false, s);
        }
    });
}

function checkForEmails(lang) {
    const containers = document.querySelectorAll(`div[data-message-id]:not([${PROCESSED_ATTR}])`);
    containers.forEach(container => {
        container.setAttribute(PROCESSED_ATTR, 'true');
        injectClassifyButton(container, lang);
    });
}

function init() {
    chrome.storage.sync.get({ briskmail_language: 'pt' }, ({ briskmail_language: lang }) => {
        checkForEmails(lang);
        const observer = new MutationObserver(() => checkForEmails(lang));
        observer.observe(document.body, { childList: true, subtree: true });
    });
}

init();

console.log('[BriskMail] Content script carregado no Gmail.');
