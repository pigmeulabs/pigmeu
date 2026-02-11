# 📋 Análise de Features Pendentes - PIGMEU COPILOT

## Status Geral
**Implementação: ~60%** | Collections: ✅ | Scrapers: ✅ | Context Generator: ✅ | Article Generator: ⚠️ (básico)

---

## 🟢 IMPLEMENTADO

### 1. **Estrutura MongoDB**
- ✅ `submissions` — Tarefas e informações iniciais do livro
- ✅ `books` — Dados extraídos da Amazon (15 campos)
- ✅ `summaries` — Resumos de URLs
- ✅ `knowledge_base` — Contexto markdown gerado
- ✅ `articles` — Artigos finais
- ✅ `articles_drafts` — Rascunhos (preparação para edição)
- ✅ `credentials` — Credenciais de API (OpenAI, WordPress, etc.)
- ✅ `prompts` — Templates de prompts para cada etapa

### 2. **Scrapers e Coleta de Dados**
- ✅ `scrape_amazon_task` — Extrai 15 metadados: título, autores, tema, idioma, edição, ISBN, páginas, preço, rating
- ✅ `scrape_goodreads_task` — Busca dados do Goodreads (ratings, reviews)
- ✅ `scrape_author_website_task` — Coleta biografia e dados do autor
- ✅ Pipeline de scraping com retry automático e rollback

### 3. **Geração de Contexto**
- ✅ `generate_context_task` — Gera markdown de contexto baseado em dados extraídos
- ✅ Integração com OpenAI (com fallback para template local)
- ✅ Persistência em `knowledge_base` collection

### 4. **Geração de Artigo (MVP)**
- ✅ `generate_article_task` — Gera artigo markdown
- ✅ Integração com OpenAI para geração LLM
- ✅ Fallback para artigo template simples
- ✅ Persistência em `articles` collection
- ✅ Atualização de status em `submissions`

### 5. **API REST**
- ✅ `POST /submit` — Criar nova tarefa de review
- ✅ `GET /tasks` — Listar tarefas com paginação
- ✅ `GET /tasks/{id}` — Detalhes completos da tarefa
- ✅ `PATCH /tasks/{id}` — Editar dados da tarefa
- ✅ `POST /tasks/{id}/generate_context` — Enfileirar geração de contexto
- ✅ `POST /tasks/{id}/generate_article` — Enfileirar geração de artigo
- ✅ `GET/POST /settings/credentials` — CRUD de credenciais
- ✅ `GET/POST/DELETE /settings/prompts` — CRUD de prompts

### 6. **Interface Web**
- ✅ Dashboard com sidebar navigation
- ✅ Seção de tarefas (grid de cards, modal de detalhes)
- ✅ Seção de submissão (formulário com validação)
- ✅ Seção de settings (credenciais e prompts)
- ✅ Modal para editar detalhes de tarefas
- ✅ Botões para gerar contexto e artigo
- ✅ Responsividade mobile

---

## 🔴 NÃO IMPLEMENTADO (Priority Crítica)

### 1. **Prompts Iniciais/Seed**
**Requisito:** Sistema deve ter prompts pré-configurados para cada etapa da pipeline  
**Status:** ❌ Faltam  
**Detalhes:** Precisa criar prompts para:
- **Extração de Metadados** — Guiar o scraper de Amazon para campos específicos
- **Geração de Contexto** — Estruturar resumos em markdown
- **Geração de Artigo** — Gerar com hierarquia H1+H2+H3 exata
- **Busca de Links** — Encontrar 3 links relevantes sobre o livro
- **Sumarização de Links** — Resumir conteúdo de cada link

**Impacto:** Sem prompts, o sistema funciona com templates genéricos, perdendo qualidade e SEO

### 2. **Estrutura de Artigo Não Conforme Spec**
**Requisito:** Artigo final deve ter:
- Título (H1, ≤60 caracteres)
- 8 seções H2 (3 temáticas + 5 fixas)
- 1 seção H2 com 2-4 H3 (máximo)
- 800-1333 palavras total
- Parágrafos: 3-6 frases (50-100 palavras)

**Status:** ⚠️ Parcialmente implementado
- ✅ H1 + H2 gerados via LLM
- ❌ Seções não validam min/max palavras
- ❌ Hierarquia H3 não é forçada
- ❌ Estrutura não segue as 8 seções fixas
- ❌ Sem validação de word count

**Impacto:** Artigos gerados podem não ser SEO-otimizados ou estruturalmente inconsistentes

### 3. **Extração de Tópicos Dinâmicos para 3 Seções Temáticas**
**Requisito:** Sistema deve identificar 3 tópicos principais do livro e criar seções temáticas  
**Status:** ❌ Faltam  
**Exemplo:** Para "Designing Data-Intensive Applications":
1. Distributed Systems & Replication
2. Storage Engines & Data Structures
3. Stream Processing & Event Sourcing

**Implementação Necessária:**
- Extrair tópicos do título, ISBN, categoria Amazon, resumos Goodreads
- Usar LLM para identificar 3 tópicos principais
- Estruturar 3 seções H2 temáticas com H3 subtopics

### 4. **Busca e Sumarização de Links Externos**
**Requisito:** Para cada livro, encontrar 3 links externos relevantes, ler e sumarizar  
**Status:** ❌ Não implementado  
**Processo esperado:**
1. Buscar Google/Web por: "Título do Livro"
2. Filtrar primeiros 3 resultados relevantes
3. Fazer scrape de cada página
4. Gerar resumo MD com tópicos extraídos
5. Persistir em `summaries` collection

**Impacto:** Knowledge base fica incompleta, contexto gerado é genérico

### 5. **Validação de Word Count e Estrutura de Seções**
**Requisito:** Validar após geração:
- Artigo: 800-1333 palavras
- Cada seção H2: mínimo 150 palavras (exceto seções fixas pequenas: 50-100)
- Seção com H3: 200+ palavras + 2-4 H3 de 80+ palavras cada

**Status:** ❌ Sem validação  
**Impacto:** Qualidade inconsistente; pode gerar artigos muito curtos ou longos

### 6. **Prompts Dinâmicos por Tipo de Livro**
**Requisito:** Diferentes tipos de livro precisam de prompts diferentes  
**Status:** ❌ Não implementado  
**Exemplo:**
- **Livro Técnico**: Foco em frameworks, ferramentas, código
- **Livro de Negócios**: Foco em estratégia, cases de sucesso
- **Livro de Design**: Foco em princípios, exemplos práticos

**Impacto:** Todos os artigos soam genéricos; perdem análise específica

### 7. **WordPress Publishing Pipeline**
**Requisito:** Endpoint para publicar artigo gerado em WordPress  
**Status:** ❌ Totalmente faltando  
**Necessário:**
- `POST /tasks/{id}/publish_article` — Enfileirar publicação
- `publish_article_task` — Celery task que:
  - Autentica em WordPress API
  - Cria post com artigo (título, conteúdo)
  - Adiciona metadados (categoria, tags)
  - Configura SEO (meta description, keywords)
  - Retorna link do artigo publicado
- UI: Botão "Publish to WordPress" na modal de detalhes
- Settings: Campo para selecionar blog/categoria padrão

**Impacto:** Sistema não tem saída para o trabalho gerado

---

## 🟡 NÃO IMPLEMENTADO (Priority Alta)

### 8. **Filtro de Status e Busca na UI**
**Requisito:** Dashboard deve filtrar tarefas por status e buscar por título/autor  
**Status:** ⚠️ HTML tem campos de filtro, mas JS não wira
**Faltando:**
- Event listener em `#filter-status`
- Event listener em `#search-tasks`
- Reload de tasksGrid com filtros aplicados

### 9. **Metricas e Monitoramento**
**Requisito:** Dashboard deveria mostrar:
- Total de tarefas (por status: pendentes, em progresso, completas, com erro)
- Taxa de sucesso de scraping
- Tempo médio de geração de artigo

**Status:** ❌ Não implementado  
**Impacto:** Usuário não tem visibilidade sobre saúde do sistema

### 10. **Edição de Artigo Antes de Publicar**
**Requisito:** Usuário deve poder revisar e editar artigo antes de publicação  
**Status:** ❌ Faltando  
**Necessário:**
- `POST /tasks/{id}/draft_article` — Salvar em `articles_drafts`
- Modal de editor markdown
- Botão "Save Draft" e "Publish"
- Histórico de versões

### 11. **Retry de Tarefas Falhadas**
**Requisito:** Botão para reprocessar tarefas que falharam  
**Status:** ❌ Não há endpoint  
**Necessário:**
- `POST /tasks/{id}/retry` — Reiniciar scraping/geração
- Resetar status e limpar erros anteriores

---

## 📊 Mapa de Prioridade

| Feature | Impacto | Dificuldade | Tempo | Priority |
|---------|---------|-------------|-------|----------|
| Prompts iniciais | 🔴 Crítico | 🟢 Fácil | 30min | 🔴 NOW |
| Estrutura de artigo conforme spec | 🔴 Crítico | 🟠 Médio | 4h | 🔴 NOW |
| Busca e sumarização de links | 🔴 Crítico | 🔴 Difícil | 6h | 🔴 NOW |
| WordPress publishing | 🔴 Crítico | 🟠 Médio | 3h | 🟡 HIGH |
| Extração de tópicos dinâmicos | 🟡 Alto | 🟠 Médio | 3h | 🟡 HIGH |
| Validação word count/estrutura | 🟡 Alto | 🟢 Fácil | 1.5h | 🟡 HIGH |
| Editor de artigo antes publicação | 🟡 Alto | 🟠 Médio | 3h | 🟡 HIGH |
| Filtro/busca na UI | 🟡 Alto | 🟢 Fácil | 1h | 🟡 MED |
| Métricas e dashboard | 🟡 Alto | 🟠 Médio | 2h | 🟡 MED |
| Retry de tarefas | 🟡 Alto | 🟢 Fácil | 1h | 🟡 MED |

---

## 🎯 Recomendação de Ordem de Implementação

### **Fase 1: Essencial (Today - 2h)**
1. Criar script de seed com 4-5 prompts iniciais padrão
2. Validar e completar estrutura de artigo conforme spec

### **Fase 2: Core (Next - 8h)**
3. Implementar busca e sumarização de links externos
4. Implementar extração de tópicos dinâmicos → 3 seções temáticas
5. Implementar WordPress publishing

### **Fase 3: Polish (Later - 4h)**
6. Editor de rascunho com versioning
7. Filtros e busca na UI
8. Métricas do sistema

---

## 📝 Checklist de Conclusão

- [ ] Prompts seed criados e funcionando
- [ ] Artigos validam estrutura (H1+8H2+1H2com3H3, 800-1333 palavras)
- [ ] Busca automática de 3 links sobre cada livro
- [ ] Sumarização automática de links em markdown
- [ ] Extração automática de 3 tópicos principais → seções temáticas
- [ ] WordPress API integration completa
- [ ] Botão "Publish to WordPress" funcional
- [ ] Editor de artigo antes de publicação
- [ ] Filtros na dashboard funcionais
- [ ] Métricas do sistema visíveis
- [ ] Testes de ponta a ponta (submit → publish)
