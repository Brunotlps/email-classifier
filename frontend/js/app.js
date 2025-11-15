// Configuração da API
// Em produção, use a URL do Railway. Em desenvolvimento, localhost.
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8001'
    : 'https:///email-classifier-production-947c.up.railway.app'; // ⚠️ SUBSTITUIR pela URL real do Railway após deploy

// Elementos DOM
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');
const emailText = document.getElementById('emailText');
const charCount = document.getElementById('charCount');
const classifyTextBtn = document.getElementById('classifyTextBtn');
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const selectedFile = document.getElementById('selectedFile');
const classifyFileBtn = document.getElementById('classifyFileBtn');
const loading = document.getElementById('loading');
const resultSection = document.getElementById('resultSection');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const historyList = document.getElementById('historyList');

let currentFile = null;

// ====================
// HISTÓRICO - LOCALSTORAGE
// ====================
const HISTORY_KEY = 'email_classifications_history';
const MAX_HISTORY_ITEMS = 50;

function saveToHistory(emailPreview, result) {
    try {
        const history = getHistory();
        const newItem = {
            id: Date.now(),
            date: new Date().toISOString(),
            emailPreview: emailPreview.substring(0, 200), // Limita preview
            classification: result.classification,
            confidence: result.confidence,
            reasoning: result.reasoning
        };
        
        history.unshift(newItem); // Adiciona no início
        
        // Limita a 50 itens
        if (history.length > MAX_HISTORY_ITEMS) {
            history.pop();
        }
        
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
        updateHistoryDisplay();
    } catch (error) {
        console.error('Erro ao salvar no histórico:', error);
    }
}

function getHistory() {
    try {
        const history = localStorage.getItem(HISTORY_KEY);
        return history ? JSON.parse(history) : [];
    } catch (error) {
        console.error('Erro ao carregar histórico:', error);
        return [];
    }
}

function clearHistory() {
    if (confirm('Tem certeza que deseja limpar todo o histórico?')) {
        localStorage.removeItem(HISTORY_KEY);
        updateHistoryDisplay();
    }
}

function updateHistoryDisplay() {
    const history = getHistory();
    
    if (history.length === 0) {
        historyList.innerHTML = `
            <div class="empty-history">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                    <path d="M32 56C45.2548 56 56 45.2548 56 32C56 18.7452 45.2548 8 32 8C18.7452 8 8 18.7452 8 32C8 45.2548 18.7452 56 32 56Z" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                    <path d="M30 20V34L40 42" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                </svg>
                <p>Nenhuma classificação ainda</p>
                <p class="empty-hint">Classifique emails para ver o histórico aqui</p>
            </div>
        `;
        return;
    }
    
    historyList.innerHTML = history.map(item => {
        const date = new Date(item.date);
        const formattedDate = date.toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        return `
            <div class="history-item">
                <div class="history-item-header">
                    <span class="history-item-date">${formattedDate}</span>
                    <span class="badge ${item.classification}">${item.classification}</span>
                </div>
                <div class="history-item-preview">${item.emailPreview}</div>
                <div class="history-item-footer">
                    <span class="history-confidence">Confiança: ${(item.confidence * 100).toFixed(0)}%</span>
                </div>
            </div>
        `;
    }).join('');
}

// Event listener para limpar histórico
clearHistoryBtn.addEventListener('click', clearHistory);

// Carrega histórico ao iniciar
document.addEventListener('DOMContentLoaded', updateHistoryDisplay);

// ====================
// TABS
// ====================
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        
        // Atualiza tabs
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Atualiza conteúdo
        tabContents.forEach(content => {
            content.classList.remove('active');
            if (content.id === `${tabName}-tab`) {
                content.classList.add('active');
            }
        });
        
        // Reset resultado
        hideResult();
    });
});

// ====================
// CONTADOR DE CARACTERES
// ====================
emailText.addEventListener('input', () => {
    const length = emailText.value.length;
    charCount.textContent = length;
    
    // Valida mínimo de caracteres
    classifyTextBtn.disabled = length < 10;
});

// ====================
// UPLOAD DE ARQUIVO
// ====================
uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--primary)';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = 'var(--gray-300)';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--gray-300)';
    
    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
});

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    handleFileSelect(file);
});

function handleFileSelect(file) {
    if (!file) return;
    
    // Valida extensão
    const validExtensions = ['.txt', '.eml', '.pdf'];
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(extension)) {
        alert(`Formato não suportado. Use: ${validExtensions.join(', ')}`);
        return;
    }
    
    // Valida tamanho (5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert('Arquivo muito grande. Máximo: 5MB');
        return;
    }
    
    currentFile = file;
    
    // Mostra arquivo selecionado
    selectedFile.innerHTML = `
        <strong>Arquivo selecionado:</strong> ${file.name} 
        <span style="color: var(--gray-500)">(${formatFileSize(file.size)})</span>
    `;
    selectedFile.classList.add('show');
    classifyFileBtn.disabled = false;
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ====================
// CLASSIFICAÇÃO - TEXTO
// ====================
classifyTextBtn.addEventListener('click', async () => {
    const content = emailText.value.trim();
    
    if (content.length < 10) {
        alert('Email muito curto. Mínimo: 10 caracteres.');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/classify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email_content: content
            })
        });
        
        if (!response.ok) {
            throw new Error('Erro ao classificar email');
        }
        
        const data = await response.json();
        displayResult(data);
        
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao classificar email. Verifique se a API está rodando.');
    } finally {
        hideLoading();
    }
});

// ====================
// CLASSIFICAÇÃO - ARQUIVO
// ====================
classifyFileBtn.addEventListener('click', async () => {
    if (!currentFile) return;
    
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('file', currentFile);
        
        const response = await fetch(`${API_BASE_URL}/api/v1/classify-file`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao classificar arquivo');
        }
        
        const data = await response.json();
        displayResult(data);
        
    } catch (error) {
        console.error('Erro:', error);
        alert(error.message || 'Erro ao classificar arquivo. Verifique se a API está rodando.');
    } finally {
        hideLoading();
    }
});

// ====================
// EXIBIR RESULTADO
// ====================
function displayResult(data) {
    const { classification, confidence, reasoning, suggestions } = data;
    
    // Badge de classificação
    const badge = document.getElementById('classificationBadge');
    badge.textContent = classification;
    badge.className = `badge ${classification}`;
    
    // Barra de confiança
    const confidenceValue = document.getElementById('confidenceValue');
    const progressFill = document.getElementById('progressFill');
    
    confidenceValue.textContent = `${(confidence * 100).toFixed(0)}%`;
    progressFill.style.width = `${confidence * 100}%`;
    
    // Reasoning
    const reasoningText = document.getElementById('reasoningText');
    reasoningText.textContent = reasoning;
    
    // Sugestões (se houver)
    const suggestionsContainer = document.getElementById('suggestionsContainer');
    
    if (suggestions && suggestions.length > 0) {
        suggestionsContainer.innerHTML = `
            <h3>Sugestões de Resposta</h3>
            ${suggestions.map(s => `
                <div class="suggestion-card">
                    <div class="suggestion-header">
                        <span class="suggestion-title">${s.title}</span>
                        <span class="suggestion-tone">${s.tone}</span>
                    </div>
                    <div class="suggestion-content">${s.content}</div>
                </div>
            `).join('')}
        `;
        suggestionsContainer.style.display = 'block';
    } else {
        suggestionsContainer.style.display = 'none';
    }
    
    // Salva no histórico
    const emailPreview = emailText.value || 'Arquivo enviado';
    saveToHistory(emailPreview, data);
    
    // Mostra resultado
    showResult();
}

// ====================
// HELPERS
// ====================
function showLoading() {
    loading.classList.add('show');
    resultSection.classList.remove('show');
}

function hideLoading() {
    loading.classList.remove('show');
}

function showResult() {
    resultSection.classList.add('show');
    
    // Scroll suave até resultado
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function hideResult() {
    resultSection.classList.remove('show');
}