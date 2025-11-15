# 🚀 Guia de Deploy - Railway + Vercel

## 📦 Backend no Railway

### 1. Criar projeto no Railway
1. Acesse [railway.app](https://railway.app)
2. Conecte seu repositório GitHub `Brunotlps/email-classifier`
3. Railway vai detectar automaticamente o `Dockerfile`

### 2. Configurar Variáveis de Ambiente
No dashboard do Railway, adicione estas variáveis:

```env
ENVIRONMENT=production
AI_PROVIDER=openai
OPENAI_API_KEY=sua-chave-openai-aqui
OPENAI_MODEL=gpt-3.5-turbo
MAX_TOKENS=500
TEMPERATURE=0.7
ALLOWED_ORIGINS=https://seu-frontend.vercel.app
```

**⚠️ IMPORTANTE**: 
- Use **OpenAI** em produção (Railway não suporta Ollama)
- Adicione a URL do Vercel em `ALLOWED_ORIGINS` depois do deploy do frontend

### 3. Deploy
- Railway faz deploy automático ao detectar push no GitHub
- Anote a URL gerada (ex: `https://email-classifier-production.up.railway.app`)

### 4. Testar
```bash
curl https://sua-url.railway.app/health
# Deve retornar: {"status":"healthy"}
```

---

## 🌐 Frontend no Vercel

### 1. Preparar URL da API
1. Abra `frontend/js/app.js`
2. Linha 3: Substitua pela URL real do Railway:
   ```javascript
   const API_BASE_URL = window.location.hostname === 'localhost' 
       ? 'http://localhost:8001'
       : 'https://email-classifier-production.up.railway.app'; // URL do Railway
   ```

### 2. Deploy no Vercel
```bash
cd frontend
npx vercel --prod
```

**Ou via Dashboard:**
1. Acesse [vercel.com](https://vercel.com)
2. Importar repositório `Brunotlps/email-classifier`
3. Root Directory: `frontend`
4. Deploy!

### 3. Atualizar CORS no Railway
Após obter a URL do Vercel (ex: `https://email-classifier.vercel.app`):

1. Volte no Railway Dashboard
2. Atualize a variável:
   ```
   ALLOWED_ORIGINS=https://email-classifier.vercel.app
   ```
3. Railway vai redeployar automaticamente

---

## ✅ Checklist Final

- [ ] Backend deployed no Railway com OpenAI configurado
- [ ] Frontend deployed no Vercel
- [ ] URL do Railway atualizada no `frontend/js/app.js`
- [ ] URL do Vercel adicionada no `ALLOWED_ORIGINS` do Railway
- [ ] Testado endpoint `/health` do Railway
- [ ] Testado classificação de email no frontend

---

## 🧪 Testar em Produção

1. Acesse seu frontend no Vercel
2. Digite um email de teste
3. Clique em "Classificar Email"
4. Verifique se a classificação e sugestões aparecem

**Exemplo de email para teste:**
```
Olá equipe,

Preciso urgentemente da atualização do relatório trimestral até amanhã às 14h.
Esta informação é crucial para a reunião com os investidores.

Aguardo retorno.
```

---

## 🐛 Troubleshooting

### Erro CORS
- Verifique se a URL do Vercel está em `ALLOWED_ORIGINS`
- Formato: URLs completas separadas por vírgula (sem espaços)

### Erro 500 na API
- Verifique os logs no Railway Dashboard
- Confirme se `OPENAI_API_KEY` está configurada corretamente

### Frontend não carrega resultados
- Abra DevTools (F12) → Console
- Verifique se a URL da API no `app.js` está correta
- Teste direto: `curl https://sua-url.railway.app/health`
