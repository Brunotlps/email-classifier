const PROCESSED_ATTR = 'data-classifier-seen';

function extractEmailText(container) {
    const emailBody = container.querySelector('div.a3s');
    return emailBody ? emailBody.innerText.trim() : '';
}

function setButtonLoading(button, loading) {
    button.disabled = loading;
    button.textContent = loading ? 'Classificando...' : 'Classificar Email';
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
        console.log('[Email Classifier] Texto extraído:', emailText.slice(0, 100) + '...');

        try {
            const response = await chrome.runtime.sendMessage({
                type: 'CLASSIFY_EMAIL',
                emailText,
            });

            if (!response.ok) throw new Error(response.error);

            console.log('[Email Classifier] Resultado:', response.data);
            // Etapa 6: renderizar o painel de resultado
        } catch (err) {
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
