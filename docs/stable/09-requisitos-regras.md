#gras de Negócio Requisitos e Re

**Versão:** 0.1.0  
**Última Atualização:** 2026-02-14

---

## 1. Requisitos Funcionais

### 1.1 Submissão de Livros

| ID | Requisito | Prioridade | Descrição |
|----|-----------|------------|-----------|
| RF-01 | Submissão via API | Alta | Usuário pode submeter livro via POST /submit |
| RF-02 | Submissão via Interface | Alta | Usuário pode submeter livro via formulário web |
| RF-03 | Validação de Entrada | Alta | Sistema valida dados obrigatórios (título, autor, URL Amazon) |
| RF-04 | Verificação de Duplicados | Alta | Sistema impede submissão duplicada pelo mesmo URL Amazon |
| RF-05 | Pipeline Configurável | Média | Usuário pode selecionar pipeline de processamento |
| RF-06 | Agendamento | Baixa | Usuário pode agendar processamento para depois |

### 1.2 Extração de Dados

| ID | Requisito | Prioridade | Descrição |
|----|-----------|------------|-----------|
| RF-10 | Scraping Amazon | Alta | Extrai metadados automaticamente da Amazon |
| RF-11 | Scraping Goodreads | Média | Extrai dados do Goodreads se URL fornecida |
| RF-12 | Processamento de Links Adicionais | Média | Processa site do autor e outros links |
| RF-13 | Extração via IA | Média | Usa LLM para extrair dados de páginas web |
| RF-14 | Rate Limiting | Alta | Respeita limites de requisições das fontes |

### 1.3 Geração de Contexto

| ID | Requisito | Prioridade | Descrição |
|----|-----------|------------|-----------|
| RF-20 | Resumo de Links | Alta | Gera resumos dos links processados |
| RF-21 | Consolidação de Dados | Alta | Unifica dados de múltiplas fontes |
| RF-22 | Pesquisa Web | Média | Realiza pesquisa sobre livro/autor |
| RF-23 | Geração de Contexto | Alta | Cria base de conhecimento consolidada |

### 1.4 Geração de Artigos

| ID | Requisito | Prioridade | Descrição |
|----|-----------|------------|-----------|
| RF-30 | Geração Automática | Alta | Gera artigo estruturado via IA |
| RF-31 | Estrutura SEO | Alta | Artigo com estrutura otimizada para SEO |
| RF-32 | Validação de Extensão | Alta | Valida contagem de palavras (800-1333) |
| RF-33 | Formato Markdown | Alta | Artigo gerado em formato Markdown |
| RF-34 | Revisão Manual | Alta | Usuário pode revisar antes de publicar |

### 1.5 Publicação

| ID | Requisito | Prioridade | Descrição |
|----|-----------|------------|-----------|
| RF-40 | Publicação WordPress | Alta | Publica artigo no WordPress |
| RF-41 | Upload de Imagem | Média | Envia imagem de capa automaticamente |
| RF-42 | Gerenciamento de Tags | Média | Gerencia categorias e tags |
| RF-43 | Aprovação Prévia | Alta | Suporta fluxo de aprovação antes de publicar |
| RF-45 | Link de Retorno | Alta | Retorna URL do post publicado |

### 1.6 Gestão de Configurações

| ID | Requisito | Prioridade | Descrição |
|----|-----------|------------|-----------|
| RF-50 | CRUD Credenciais | Alta | Gerencia credenciais de API |
| RF-51 | CRUD Prompts | Alta | Gerencia templates de prompts |
| RF-52 | CRUD Content Schemas | Média | Gerencia schemas de estrutura |
| RF-53 | CRUD Pipelines | Média | Gerencia configurações de pipelines |

### 1.7 Monitoramento

| ID | Requisito | Prioridade | Descrição |
|----|-----------|------------|-----------|
| RF-60 | Listagem de Tarefas | Alta | Lista todas as submissões |
| RF-61 | Detalhes de Tarefas | Alta | Mostra detalhes completos de uma tarefa |
| RF-62 | Estatísticas | Alta | Mostra métricas de tarefas |
| RF-63 | Filtros e Busca | Alta | Filtra tarefas por status |
| RF-64 | Retry | Alta | Possibilita retry de tarefas falhadas |

---

## 2. Requisitos Não Funcionais

### 2.1 Performance

| Métrica | Meta | Descrição |
|---------|------|-----------|
| Tempo de Resposta API | < 200ms | Para endpoints simples |
| Tempo de Scraping | < 60s | Por página |
| Tempo de Geração de Artigo | < 120s | Via LLM |
| Throughput de Tarefas | 10/min | Processamento paralelo |

### 2.2 Escalabilidade

| Aspecto | Requisito |
|---------|-----------|
| Múltiplos Workers | Suporta scale-out de workers |
| Múltiplas Instâncias API | API stateless para load balancing |
| Banco de Dados | Suporta sharding se necessário |

### 2.3 Disponibilidade

| Aspecto | Requisito |
|---------|-----------|
| Uptime | 99.5% em produção |
| Health Checks | Endpoints de saúde funcionais |
| Recuperação | Retry automático de tasks falhadas |

### 2.4 Segurança

| Aspecto | Requisito |
|---------|-----------|
| Credenciais | Armazenadas de forma segura |
| API | Validação de entrada |
| HTTPS | Recomendado em produção |
| Rate Limiting | Em scraping externo |

### 2.5 Manutenibilidade

| Aspecto | Requisito |
|---------|-----------|
| Logging | Logs estruturados |
| Monitoramento | Métricas disponíveis |
| Documentação | Documentação atualizada |

---

## 3. Regras de Negócio

### 3.1 Submissão de Livros

**RN-001:** Todo livro deve ter pelo menos título, autor e URL da Amazon válidos.

**RN-002:** Uma URL Amazon não pode ser submetida mais de uma vez.

**RN-003:** O sistema deve criar uma submissão mesmo se o scraping falhar (status: "failed").

**RN-004:** Opcionalmente, a submissão pode requerer aprovação humana antes da publicação.

### 3.2 Pipeline de Processamento

**RN-010:** O pipeline padrão ("book_review_v2") executa 7 steps em sequência.

**RN-011:** Cada step pode ser executado de forma independente via retry.

**RN-012:** Se um step falhar, o sistema registra o erro e permite retry.

**RN-013:** O pipeline pode ser pausado/reiniciado a qualquer momento.

### 3.3 Scraping

**RN-020:** Rate limiting deve ser aplicado: máximo 0.5 req/s para Amazon.

**RN-021:** Timeout de scraping: 60 segundos por página.

**RN-022:** Qualquer página que retornar HTTP 4xx/5xx deve ser logada.

**RN-023:** Se o scraping principal falhar, o pipeline marca como "scraping_failed".

### 3.4 Geração de Artigos

**RN-030:** Artigos devem ter entre 800 e 1333 palavras (configurável via content schema).

**RN-031:** Títulos de artigos devem ter no máximo 60 caracteres para SEO.

**RN-032:** Cada artigo deve conter:
- Introdução
- 3 seções temáticas
- Seção "Para quem é este livro"
- Seção "Prós e Contras"
- Seção "Sobre o Autor"
- Conclusão
- Seção "Onde Comprar"

**RN-033:** O sistema pode gerar artigos em Markdown ou HTML.

### 3.5 Publicação

**RN-040:** Publicação requer artigo com status "approved" ou "draft".

**RN-041:** Se "user_approval_required" for true, publicação só é permitida após aprovação.

**RN-042:** Após publicação bem-sucedida, o sistema atualiza:
- Artigo: status → "published", adiciona wordpress_post_id e wordpress_url
- Submissão: status → "published"

**RN-043:** Se a publicação falhar, o sistema registra o erro e permite retry.

### 3.6 Validações

| Campo | Regra |
|-------|-------|
| title (submission) | Obrigatório, mín. 1 caractere |
| author_name | Obrigatório, mín. 1 caractere |
| amazon_url | Obrigatório, deve ser URL válida da Amazon |
| goodreads_url | Opcional, se fornecida deve ser URL válida |
| pipeline_id | Deve existir na coleção pipeline_configs |
| content_schema_id | Se fornecido, deve existir na coleção content_schemas |

### 3.7 Limites do Sistema

| Recurso | Limite |
|---------|--------|
| Tarefas por página | 100 (API) |
| Tamanho de contexto LLM | 32K tokens (Groq) |
| Tempo máximo de task | 30 minutos |
| Tamanho máximo de upload | 10MB |
| Concurrent workers | Configurável |

---

## 4. Estados e Transições

### 4.1 Máquina de Estados de Submissão

```
                    ┌─────────────────┐
                    │ pending_scrape  │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌───────────────┐ ┌──────────────┐ ┌──────────────┐
    │scraping_amazon│ │scraping_     │ │ scraping_     │
    │               │ │goodreads     │ │failed        │
    └───────┬───────┘ └──────┬───────┘ └──────────────┘
            │                │                │
            │                │                │
            ▼                ▼                ▼
    ┌───────────────┐ ┌──────────────┐ ┌──────────────┐
    │    scraped    │ │   scraped    │ │ scraping_    │
    │               │ │              │ │failed        │
    └───────┬───────┘ └──────┬───────┘ └──────────────┘
            │                │
            ▼                ▼
    ┌───────────────────────┐
    │   pending_context     │
    └───────────┬───────────┘
                │
    ┌───────────┼───────────┐
    │           │           │
    ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐
│context │ │context │ │ failed │
│_gen    │ │_gen'd  │ │        │
└───┬────┘ └───┬────┘ └───┬────┘
    │          │          │
    ▼          ▼          ▼
┌──────────┐ ┌─────────────────┐
│pending_  │ │  pending_article│
│article   │ └────────┬────────┘
└────┬─────┘          │
     │         ┌───────┴───────┐
     │         │               │
     ▼         ▼               ▼
┌──────────┐ ┌─────────────┐ ┌───────────┐
│article   │ │ready_for_   │ │  failed    │
│_generated│ │review       │ └───────────┘
└────┬─────┘ └──────┬──────┘
     │              │
     │      ┌───────┴───────┐
     │      │               │
     ▼      ▼               ▼
  ┌─────────────┐ ┌─────────┐ ┌──────────┐
  │  approved   │ │published │ │  failed   │
  └──────┬──────┘ └─────────┘ └──────────┘
         │
         │ (se approval required=false)
         ▼
    ┌──────────┐
    │published │
    └──────────┘
```

### 4.2 Estados de Artigo

```
┌────────┐    approve    ┌─────────┐    publish    ┌──────────┐
│ draft  │ ───────────►  │ in_     │ ───────────► │ published│
└────────┘               │ review  │              └──────────┘
                         └─────────┘
                              │
                              │ reject
                              ▼
                         ┌──────────┐
                         │ archived │
                         └──────────┘
```

---

## 5. Casos de Uso

### 5.1 UC-001: Submeter Livro para Revisão

**Ator:** Usuário do sistema  
**Pré-condições:** Usuário autenticado (se aplicável), credenciais configuradas  
**Fluxo Principal:**

1. Usuário acessa interface de submissão
2. Preenche dados do livro (título, autor, URL Amazon)
3. (Opcional) Fornece URLs adicionais
4. Clica em "Submit"
5. Sistema valida dados
6. Sistema verifica duplicados
7. Sistema cria submissão no banco
8. Sistema dispara pipeline assíncrono
9. Sistema retorna confirmation

**Pós-condições:** Submissão criada, pipeline em execução

### 5.2 UC-002: Revisar e Aprovar Artigo

**Ator:** Editor/Usuário  
**Pré-condições:** Artigo com status "ready_for_review"  
**Fluxo Principal:**

1. Editor acessa lista de tarefas
2. Filtra por status "ready_for_review"
3. Seleciona tarefa
4. Visualiza artigo gerado
5. Revisa conteúdo
6. Clica em "Approve" ou edita rascunho

**Pós-condições:** Artigo aprovado para publicação

### 5.3 UC-003: Publicar Artigo

**Ator:** Sistema ou Editor  
**Pré-condições:** Artigo com status "approved" (ou "ready_for_review" se approval not required)  
**Fluxo Principal:**

1. Sistema/Editor dispara publicação
2. Worker carrega artigo e credenciais WordPress
3. Worker faz upload de imagem de capa
4. Worker cria post no WordPress
5. Worker atualiza artigo com URL do post
6. Worker atualiza status da submissão

**Pós-condições:** Artigo publicado no WordPress, status atualizado

### 5.4 UC-004: Recuperar de Falha

**Ator:** Usuário  
**Pré-condições:** Submissão com status "failed"  
**Fluxo Principal:**

1. Usuário visualiza tarefa falhada
2. Identifica ponto de falha
3. Clica em "Retry Step" (ou retry completo)
4. Sistema limpa dados do step citado
5. Sistema reinicia do step especificado
6. Sistema processa até conclusão

**Pós-condições:** Submissão processada com sucesso ou falha documentada

---

## 6. Restrições Técnicas

### 6.1 APIs Externas

| API | Limite | Penalidade |
|-----|--------|-----------|
| Amazon | 0.5 req/s | 403/429 |
| Goodreads | 0.3 req/s | 429 |
| OpenAI | Según plano | Rate limit |
| Groq | 30 req/min | Rate limit |
| Mistral | Según plano | Rate limit |

### 6.2 Timeout de Operações

| Operação | Timeout |
|----------|---------|
| Scraping (página) | 60 segundos |
| LLM (geração) | 120 segundos |
| WordPress (post) | 30 segundos |
| Task Celery | 30 minutos |

---

## 7. Glossário

| Termo | Definição |
|-------|-----------|
| Scraping | Extração automatizada de dados de páginas web |
| Pipeline | Sequência de steps de processamento |
| Task | Unidade de trabalho assíncrono (Celery) |
| LLM | Large Language Model (Inteligência Artificial) |
| Credential | Chave de API ou senha de serviço |
| Prompt | Template de instrução para LLM |
| Schema | Estrutura de conteúdo definida |
| Submission | Pedido de processamento de um livro |

---

## 8. Referências

- [Arquitetura Técnica](./02-arquitetura.md)
- [Modelo de Dados](./03-modelo-de-dados.md)
- [API REST](./04-api-rest.md)
- [Workers e Pipelines](./05-workers-pipelines.md)
