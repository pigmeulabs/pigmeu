# Análise de Problemas do Sistema Pigmeu Copilot

**Data da Análise:** 2026-02-14  
**Versão do Sistema:** 0.1.0

## 📋 Sumário Executivo

O sistema Pigmeu Copilot é uma aplicação Python/FastAPI para geração automatizada de resenhas de livros técnicos. Após análise completa do código-fonte, configurações e infraestrutura, foram identificados **8 problemas críticos** e **5 problemas de configuração** que impedem o funcionamento adequado do sistema.

---

## 🔴 PROBLEMAS CRÍTICOS (Impedem Funcionamento)

### 1. **Chave OpenAI Inválida no .env**
**Arquivo:** `.env` (linha 13)  
**Severidade:** 🔴 CRÍTICA  
**Status:** Sistema não pode usar IA

**Problema:**
```env
OPENAI_API_KEY=sk-your-key-here
```

A chave da OpenAI está com valor placeholder. Embora o sistema use principalmente Groq e Mistral, algumas funcionalidades podem depender da OpenAI.

**Impacto:**
- Falha em qualquer operação que tente usar OpenAI
- Possível falha em fallbacks de IA

**Solução:**
```env
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXX
```
Obter chave válida em: https://platform.openai.com/api-keys

---

### 2. **Falta de Chaves Groq e Mistral**
**Arquivo:** `.env`  
**Severidade:** 🔴 CRÍTICA  
**Status:** Pipeline de IA completamente quebrado

**Problema:**
O arquivo `.env` não contém as chaves necessárias para os provedores de IA principais:
- `GROQ_API_KEY` - ausente
- `MISTRAL_API_KEY` - ausente

**Evidência no código:**
```python
# src/config.py (linhas 17-19)
openai_api_key: str = ""
groq_api_key: Optional[str] = None
mistral_api_key: Optional[str] = None
```

**Impacto:**
- **100% das operações de IA falharão**
- Pipeline de geração de contexto não funciona
- Pipeline de geração de artigos não funciona
- Sumarização de links não funciona
- Pesquisa na internet não funciona

**Solução:**
Adicionar ao `.env`:
```env
# Groq (usado para contexto e pesquisa)
GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXXX

# Mistral (usado para geração de artigos)
MISTRAL_API_KEY=XXXXXXXXXXXXXXXXXXXXX
```

Obter chaves em:
- Groq: https://console.groq.com/keys
- Mistral: https://console.mistral.ai/api-keys/

---

### 3. **Python Não Instalado no Ambiente**
**Severidade:** 🔴 CRÍTICA  
**Status:** Impossível executar aplicação

**Problema:**
```bash
$ python --version
/bin/sh: 1: python: not found

$ python3 --version
/bin/sh: 1: python3: not found
```

**Impacto:**
- Não é possível executar a aplicação diretamente
- Scripts de migração não podem ser executados
- Testes não podem ser executados
- Sistema depende 100% do Docker

**Solução:**
```bash
# Instalar Python 3.10+
apt-get update
apt-get install -y python3.10 python3-pip

# Ou usar Docker conforme documentado
docker-compose -f infra/docker-compose.yml up --build
```

---

### 4. **Credenciais WordPress Inválidas**
**Arquivo:** `.env` (linhas 15-18)  
**Severidade:** 🟡 ALTA  
**Status:** Publicação não funciona

**Problema:**
```env
WORDPRESS_URL=https://example.wordpress.com
WORDPRESS_USERNAME=admin
WORDPRESS_PASSWORD=password
```

Credenciais são placeholders e não funcionarão para publicação.

**Impacto:**
- Impossível publicar artigos gerados
- Endpoint de publicação falhará
- Última etapa do pipeline não funciona

**Solução:**
```env
WORDPRESS_URL=https://analisederequisitos.com.br
WORDPRESS_USERNAME=seu_usuario_real
WORDPRESS_PASSWORD=sua_senha_aplicacao_wordpress
```

**Nota:** Use senha de aplicação do WordPress, não a senha principal.

---

### 5. **Falta de Dados Seed Obrigatórios**
**Arquivos:** `scripts/seed_prompts.py`, `scripts/seed_content_schema.py`  
**Severidade:** 🔴 CRÍTICA  
**Status:** Sistema não pode processar submissões

**Problema:**
O sistema requer dados iniciais (prompts, schemas, pipelines) no MongoDB para funcionar, mas não há evidência de que foram executados.

**Dados obrigatórios ausentes:**
1. **Prompts de IA** - templates para cada etapa do pipeline
2. **Content Schemas** - estrutura dos artigos
3. **Pipeline Configs** - configuração do fluxo de trabalho
4. **Credentials** - credenciais dos provedores de IA

**Evidência:**
```python
# src/api/settings.py (linha 45-49)
await _ensure_system_defaults(
    pipeline_repo=pipeline_repo,
    credential_repo=credential_repo,
    content_schema_repo=content_schema_repo,
)
```

**Impacto:**
- Submissões falham ao tentar buscar pipeline
- Tarefas de IA falham por falta de prompts
- Geração de artigos falha por falta de schema

**Solução:**
```bash
# Executar scripts de seed (dentro do container ou com Python instalado)
python scripts/seed_prompts.py
python scripts/seed_content_schema.py
python scripts/migrate.py
```

---

### 6. **Configuração de Redis Inconsistente**
**Arquivos:** `.env`, `infra/docker-compose.yml`  
**Severidade:** 🟡 ALTA  
**Status:** Workers Celery não funcionam

**Problema:**
```env
# .env
REDIS_URL=redis://localhost:6379

# docker-compose.yml (linha 14)
REDIS_URL=redis://redis:6379
```

Quando executado via Docker, o `.env` aponta para `localhost` mas deveria apontar para o serviço `redis` do Docker.

**Impacto:**
- Workers Celery não conseguem conectar ao Redis
- Tarefas assíncronas não são processadas
- Pipeline completo não funciona

**Solução:**
Atualizar `.env`:
```env
# Para uso com Docker
REDIS_URL=redis://redis:6379

# Para uso local (desenvolvimento sem Docker)
# REDIS_URL=redis://localhost:6379
```

---

### 7. **Configuração de MongoDB Inconsistente**
**Arquivos:** `.env`, `infra/docker-compose.yml`  
**Severidade:** 🟡 ALTA  
**Status:** Conflito entre MongoDB Atlas e MongoDB local

**Problema:**
```env
# .env - aponta para MongoDB Atlas (cloud)
MONGODB_URI=mongodb+srv://pigmeu-copilot:Y1QrL27uAnrRskPn@pigmeu-copilot.kfd3uq3.mongodb.net/

# docker-compose.yml (linha 12) - sobrescreve para MongoDB local
MONGODB_URI=mongodb://mongo:27017
```

O Docker Compose sobrescreve a URI do Atlas para usar MongoDB local, mas isso pode causar confusão e perda de dados.

**Impacto:**
- Dados podem estar em locais diferentes
- Confusão sobre qual banco está sendo usado
- Possível perda de dados ao alternar entre ambientes

**Solução:**
**Opção 1 - Usar MongoDB Atlas (recomendado para produção):**
```yaml
# docker-compose.yml - remover override
environment:
  # - MONGODB_URI=mongodb://mongo:27017  # REMOVER esta linha
  - MONGO_DB_NAME=pigmeu
```

**Opção 2 - Usar MongoDB local (desenvolvimento):**
```env
# .env
MONGODB_URI=mongodb://localhost:27017
```

---

### 8. **Falta de Validação de Dependências Críticas**
**Arquivo:** `requirements.txt`  
**Severidade:** 🟡 MÉDIA  
**Status:** Possíveis incompatibilidades

**Problema:**
Algumas dependências estão com versões fixas antigas:
```txt
fastapi==0.104.1      # Versão de Nov 2023
uvicorn[standard]==0.24.0
motor==3.3.2
celery==5.3.4
langchain==0.1.0      # Versão muito antiga
```

**Impacto:**
- Possíveis bugs conhecidos não corrigidos
- Vulnerabilidades de segurança
- Incompatibilidades com Python 3.11+

**Solução:**
Atualizar `requirements.txt`:
```txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
motor>=3.4.0
celery>=5.3.6
langchain>=0.1.10
pydantic>=2.6.0
```

---

## 🟡 PROBLEMAS DE CONFIGURAÇÃO

### 9. **Falta de Arquivo .env na Raiz do Projeto**
**Severidade:** 🟡 MÉDIA

Embora exista um `.env`, ele pode não estar sendo carregado corretamente pelo Docker Compose se não estiver no local esperado.

**Solução:**
Verificar que `.env` está na raiz do projeto e é referenciado corretamente no `docker-compose.yml`.

---

### 10. **Logs Não Configurados**
**Severidade:** 🟡 BAIXA

Não há configuração de rotação de logs ou persistência de logs do Docker.

**Solução:**
Adicionar ao `docker-compose.yml`:
```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

### 11. **Falta de Health Checks nos Workers**
**Severidade:** 🟡 BAIXA

O serviço `worker` no Docker não tem health check configurado.

**Solução:**
Adicionar ao `docker-compose.yml`:
```yaml
worker:
  healthcheck:
    test: ["CMD-SHELL", "celery -A src.workers.worker inspect ping"]
    interval: 30s
    timeout: 10s
    retries: 3
```

---

### 12. **Variáveis de Ambiente Expostas**
**Severidade:** 🟡 MÉDIA (Segurança)

O arquivo `.env` contém credenciais reais do MongoDB Atlas e está versionado (ou pode estar).

**Solução:**
1. Adicionar `.env` ao `.gitignore`
2. Usar secrets management em produção
3. Rotacionar credenciais expostas

---

### 13. **Falta de Documentação de Setup**
**Severidade:** 🟡 BAIXA

O README menciona arquivos que não existem:
```markdown
- [Setup Instructions](docs/SETUP.md)  # Não existe
- [API Documentation](docs/API.md)     # Não existe
```

**Solução:**
Criar documentação ou remover referências.

---

## 📊 RESUMO DE PRIORIDADES

### 🔴 CRÍTICO - Resolver Imediatamente
1. ✅ Adicionar `GROQ_API_KEY` ao `.env`
2. ✅ Adicionar `MISTRAL_API_KEY` ao `.env`
3. ✅ Executar scripts de seed (prompts, schemas, pipelines)
4. ✅ Corrigir configuração de Redis para Docker
5. ✅ Decidir entre MongoDB Atlas ou local

### 🟡 IMPORTANTE - Resolver em Seguida
6. ⚠️ Atualizar credenciais WordPress
7. ⚠️ Atualizar chave OpenAI (se necessária)
8. ⚠️ Instalar Python no ambiente (ou usar Docker)
9. ⚠️ Atualizar dependências do requirements.txt

### 🟢 MELHORIAS - Resolver Quando Possível
10. 📝 Configurar logs adequadamente
11. 📝 Adicionar health checks
12. 📝 Melhorar segurança de credenciais
13. 📝 Completar documentação

---

## 🚀 PLANO DE AÇÃO RECOMENDADO

### Passo 1: Configurar Chaves de API (5 minutos)
```bash
# Editar .env
nano .env

# Adicionar:
GROQ_API_KEY=gsk_sua_chave_aqui
MISTRAL_API_KEY=sua_chave_aqui
OPENAI_API_KEY=sk-proj-sua_chave_aqui  # Opcional
```

### Passo 2: Ajustar Configurações Docker (2 minutos)
```bash
# Editar .env
REDIS_URL=redis://redis:6379

# Decidir sobre MongoDB:
# Opção A: Usar Atlas (remover override no docker-compose.yml)
# Opção B: Usar local (manter como está)
```

### Passo 3: Iniciar Serviços (3 minutos)
```bash
cd infra
docker-compose up -d mongo redis
docker-compose up -d api
```

### Passo 4: Executar Migrações e Seeds (5 minutos)
```bash
# Dentro do container da API
docker-compose exec api python scripts/migrate.py
docker-compose exec api python scripts/seed_prompts.py
docker-compose exec api python scripts/seed_content_schema.py
```

### Passo 5: Iniciar Workers (2 minutos)
```bash
docker-compose up -d worker
```

### Passo 6: Verificar Saúde (2 minutos)
```bash
# Testar API
curl http://localhost:8000/health

# Testar UI
curl http://localhost:8000/ui

# Verificar logs
docker-compose logs -f api
docker-compose logs -f worker
```

### Passo 7: Testar Submissão (5 minutos)
```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Clean Code",
    "author_name": "Robert C. Martin",
    "amazon_url": "https://www.amazon.com.br/dp/8576082675",
    "run_immediately": true
  }'
```

---

## 🔍 VERIFICAÇÕES ADICIONAIS NECESSÁRIAS

### Verificar se Playwright está instalado
```bash
docker-compose exec api playwright --version
```

### Verificar conectividade com MongoDB
```bash
docker-compose exec api python -c "from src.db.connection import get_database; import asyncio; asyncio.run(get_database())"
```

### Verificar conectividade com Redis
```bash
docker-compose exec api python -c "import redis; r = redis.from_url('redis://redis:6379'); print(r.ping())"
```

### Verificar Celery Workers
```bash
docker-compose exec worker celery -A src.workers.worker inspect active
```

---

## 📝 NOTAS IMPORTANTES

1. **Segurança:** As credenciais do MongoDB Atlas estão expostas neste documento. Elas devem ser rotacionadas imediatamente.

2. **Ambiente:** O sistema foi projetado para rodar em Docker. Executar localmente requer instalação manual de todas as dependências.

3. **Dados:** Há backups em `backups/` que podem conter dados importantes. Verificar antes de executar seeds.

4. **Testes:** Não há evidência de testes automatizados funcionando. Considerar adicionar testes de integração.

5. **Monitoramento:** Não há sistema de monitoramento configurado. Considerar adicionar Prometheus/Grafana.

---

## 🎯 CONCLUSÃO

O sistema Pigmeu Copilot tem uma arquitetura sólida e bem estruturada, mas está **completamente não-funcional** devido a:

1. **Falta de chaves de API** (Groq, Mistral)
2. **Falta de dados seed** (prompts, schemas, pipelines)
3. **Configurações inconsistentes** (Redis, MongoDB)

Com as correções listadas acima, o sistema deve funcionar corretamente. O tempo estimado para resolver todos os problemas críticos é de **aproximadamente 30 minutos**.

**Status Atual:** 🔴 NÃO FUNCIONAL  
**Status Após Correções:** 🟢 FUNCIONAL

---

**Documento gerado por:** Análise automatizada do código-fonte  
**Última atualização:** 2026-02-14T04:00:00Z
