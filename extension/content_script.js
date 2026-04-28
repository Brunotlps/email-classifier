const PROCESSED_ATTR = 'data-classifier-seen';

function onEmailDetected(emailContainer) {
    const messageId = emailContainer.getAttribute('data-message-id');
    console.log('[Email Classifier] Email detectado! data-message-id:', messageId);
}

function checkForEmails() {
    // Seleciona apenas containers que ainda não foram processados
    const containers = document.querySelectorAll(`div[data-message-id]:not([${PROCESSED_ATTR}])`);

    containers.forEach(container => {
        // Marca como processado antes de qualquer outra coisa
        container.setAttribute(PROCESSED_ATTR, 'true');
        onEmailDetected(container);
    });
}

// Verifica se já há um email aberto quando o script carrega
checkForEmails();

// Observa mudanças no DOM para detectar emails abertos depois
const observer = new MutationObserver(checkForEmails);
observer.observe(document.body, { childList: true, subtree: true });

console.log('[Email Classifier] Content script carregado no Gmail.');
