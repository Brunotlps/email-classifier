const PROCESSED_ATTR = 'data-classifier-seen';

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

    // Ancora a toolbar imediatamente antes do corpo do email (div.a3s)
    // Isso evita conflitos com o layout interno do Gmail no container externo
    const emailBody = container.querySelector('div.a3s');
    if (emailBody) {
        emailBody.parentElement.insertBefore(toolbar, emailBody);
    } else {
        container.prepend(toolbar);
    }

    button.addEventListener('click', () => {
        console.log('[Email Classifier] Botão clicado!');
        // Etapa 5: aqui chamaremos a API
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
