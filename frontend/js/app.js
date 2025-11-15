// Configuração da API
const API_BASE_URL = 'http://localhost:8001';

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

let currentFile = null;

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