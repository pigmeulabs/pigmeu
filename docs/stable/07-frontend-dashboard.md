# Frontend Dashboard

**Versão:** 0.1.0  
**Última Atualização:** 2026-02-14

---

## 1. Visão Geral

O Pigmeu Copilot possui uma interface web (SPA - Single Page Application) para gestão de tarefas, visualização de artigos e configurações do sistema.

### 1.1 URLs de Acesso

| Serviço | URL |
|---------|-----|
| Dashboard | http://localhost:8000/ui |
| Recursos Estáticos | http://localhost:8000/ui/static/ |

### 1.2 Estrutura de Arquivos

```
src/static/
├── index.html      # HTML principal
├── app.js          # Lógica JavaScript
├── styles.css      # Estilos CSS
└── logo-pigmeu-labs-2.png  # Logo
```

---

## 2. Estrutura da Interface

### 2.1 Layout Principal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PIGMEU COPILOT                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  📖 Pigmeu Labs                              [☰]                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
├──────────────┬──────────────────────────────────────────────────────────────┤
│              │                                                               │
│  SIDEBAR    │  HEADER                                                       │
│              │  ┌─────────────────────────────────────────────────────────┐ │
│  📊 Analytics│  │  My Tasks                           [System Online ●] │ │
│  📋 Tasks    │  └─────────────────────────────────────────────────────────┘ │
│              │                                                               │
│  📝 Content  │  CONTENT                                                      │
│    ├ Articles│  ┌─────────────────────────────────────────────────────────┐ │
│    ├ Book Review│ │  [Filters] [Search...] [Status ▼] [Refresh]           │ │
│    └ Social Media│ │                                                         │ │
│              │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                   │ │
│  🔧 SEO Tools│  │  │ Task 1  │ │ Task 2  │ │ Task 3  │                   │ │
│              │  │  │ Status  │ │ Status  │ │ Status  │                   │ │
│  ⚙️ Settings │  │  │ ● Ready │ │ ● Done  │ │ ● Fail │                   │ │
│    ├ Credentials │ └─────────┘ └─────────┘ └─────────┘                   │ │
│    ├ Content Schemas│                                                     │ │
│    ├ Prompts    │  ┌─────────────────────────────────────────────────────┐│ │
│    └ Pipelines  │  │  Pagination: [← Previous] Page 1 of 5 [Next →]   ││ │
│              │  └─────────────────────────────────────────────────────────┘│ │
│  🚪 Logout   │                                                               │
│              │                                                               │
├──────────────┴──────────────────────────────────────────────────────────────┤
│  System Online ●                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Navegação

A sidebar contém os seguintes itens de navegação:

| Seção | Items |
|-------|-------|
| Analytics | Overview |
| Tasks | My Tasks |
| Content Copilot | Articles, Book Review, Social Media |
| SEO Tools | - |
| Settings | Credentials, Content Schemas, Prompts, Pipelines |

---

## 3. Páginas e Funcionalidades

### 3.1 Dashboard de Tarefas (Tasks)

**Rota:** `#tasks`

#### 3.1.1 Barra de Filtros

```html
<input type="text" id="search-tasks" placeholder="Search by title/author...">
<select id="filter-status">
  <option value="">All statuses</option>
  <option value="pending_scrape">Pending Scrape</option>
  <option value="context_generation">Generating Context</option>
  <option value="ready_for_review">Ready for Review</option>
  <option value="published">Published</option>
  <option value="failed">Failed</option>
</select>
<button id="refresh-tasks" class="btn">Refresh</button>
```

#### 3.1.2 Grid de Tarefas

Cada card de tarefa exibe:

- Título do livro
- Autor
- Status atual
- Data de criação
- Pipeline utilizado

#### 3.1.3 Paginação

```html
<button id="prev-page">← Previous</button>
<span id="tasks-pagination">Page 1</span>
<button id="next-page">Next →</button>
```

#### 3.1.4 Estatísticas

Barra de estatísticas mostrando:

- Total de tarefas
- Porcentagem de sucesso
- Tarefas por status

---

### 3.2 Detalhes da Tarefa

**Rota:** `#task-details/{submission_id}`

Exibe informações completas:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TASK DETAILS                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Title: Designing Data-Intensive Applications                               │
│  Author: Martin Kleppmann                                                    │
│  Status: ready_for_review ✓                                                 │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PROGRESS                                                            │   │
│  │                                                                     │   │
│  │  ● Pending Scrape ─● Context ─● Article ─● Ready                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  BOOK DATA                                                           │   │
│  │                                                                     │   │
│  │  Title: Designing Data-Intensive Applications                       │   │
│  │  ASIN: 1449373321                                                   │   │
│  │  ISBN-13: 9781449373327                                             │   │
│  │  Rating: 4.8                                                         │   │
│  │  Pages: 616                                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ARTICLE                                                             │   │
│  │                                                                     │   │
│  │  Title: Designing Data-Intensive Applications: Uma Análise Completa│   │
│  │  Word Count: 1100                                                   │   │
│  │  Status: draft                                                      │   │
│  │                                                                     │   │
│  │  [Edit Draft] [Approve] [Publish to WordPress] [Retry]             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  [← Back to Tasks]                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.3 Formulário de Submissão (Book Review)

**Rota:** `#submit` (Book Review)

Formulário para submeter novos livros:

```html
<form id="submit-form" class="book-review-form">
  <!-- Dados do Livro -->
  <div class="form-group">
    <label for="title">Book Title *</label>
    <input type="text" id="title" name="title" required>
  </div>

  <div class="form-group">
    <label for="author_name">Author Name *</label>
    <input type="text" id="author_name" name="author_name" required>
  </div>

  <!-- URLs -->
  <div class="form-group">
    <label for="amazon_url">Amazon Link *</label>
    <input type="url" id="amazon_url" name="amazon_url" required>
  </div>

  <div class="form-group">
    <label for="goodreads_url">Goodreads Link</label>
    <input type="url" id="goodreads_url" name="goodreads_url">
  </div>

  <div class="form-group">
    <label for="author_site">Author's Website</label>
    <input type="url" id="author_site" name="author_site">
  </div>

  <div class="form-group">
    <label for="other_links">Other Links</label>
    <textarea id="other_links" name="other_links"></textarea>
  </div>

  <!-- Informações Adicionais -->
  <div class="form-group">
    <label for="textual_information">Additional Text Information</label>
    <textarea id="textual_information" name="textual_information"></textarea>
  </div>

  <!-- Configurações -->
  <div class="form-group">
    <label>
      <input type="checkbox" name="run_immediately" checked>
      Process immediately
    </label>
  </div>

  <div class="form-group">
    <label>
      <input type="checkbox" name="user_approval_required">
      Require approval before publishing
    </label>
  </div>

  <!-- Pipeline e Schema -->
  <div class="form-group">
    <label for="pipeline_id">Pipeline</label>
    <select id="pipeline_id" name="pipeline_id">
      <option value="book_review_v2" selected>Book Review v2</option>
    </select>
  </div>

  <div class="form-group">
    <label for="content_schema_id">Content Schema</label>
    <select id="content_schema_id" name="content_schema_id">
      <option value="">Default</option>
    </select>
  </div>

  <button type="submit" class="btn btn-primary">Submit Book</button>
</form>
```

---

### 3.4 CRUD de Credenciais

**Rota:** `#credentials`

Interface para gerenciar credenciais de serviços:

```html
<!-- Lista de Credenciais -->
<div class="credentials-list">
  <div class="credential-item">
    <span class="service-badge">OPENAI</span>
    <span class="name">OpenAI Principal</span>
    <span class="status active">● Active</span>
    <button class="btn-edit">Edit</button>
    <button class="btn-delete">Delete</button>
  </div>
</div>

<!-- Modal de Criação/Edição -->
<dialog id="credential-modal">
  <form>
    <label>Service *</label>
    <select name="service" required>
      <option value="openai">OpenAI</option>
      <option value="groq">Groq</option>
      <option value="mistral">Mistral</option>
      <option value="claude">Claude</option>
      <option value="wordpress">WordPress</option>
    </select>

    <label>Name *</label>
    <input type="text" name="name" required>

    <label>API Key *</label>
    <input type="password" name="key" required>

    <label>URL (for WordPress)</label>
    <input type="url" name="url">

    <label>Username/Email (for WordPress)</label>
    <input type="text" name="username_email">

    <label>
      <input type="checkbox" name="active" checked>
      Active
    </label>

    <button type="submit">Save</button>
    <button type="button" class="btn-cancel">Cancel</button>
  </form>
</dialog>
```

---

### 3.5 CRUD de Prompts

**Rota:** `#prompts`

Interface para gerenciar templates de prompts:

```html
<!-- Lista de Prompts -->
<div class="prompts-list">
  <div class="prompt-item">
    <span class="name">SEO-Optimized Article Writer</span>
    <span class="purpose">article</span>
    <span class="provider">openai</span>
    <button class="btn-edit">Edit</button>
    <button class="btn-delete">Delete</button>
  </div>
</div>

<!-- Campos do Prompt -->
<form>
  <label>Name *</label>
  <input type="text" name="name" required>

  <label>Purpose *</label>
  <input type="text" name="purpose" required>

  <label>Category</label>
  <select name="category">
    <option value="Book Review">Book Review</option>
    <option value="Social Media">Social Media</option>
    <option value="SEO Tools">SEO Tools</option>
  </select>

  <label>Provider</label>
  <select name="provider">
    <option value="openai">OpenAI</option>
    <option value="groq">Groq</option>
    <option value="mistral">Mistral</option>
  </select>

  <label>Model ID</label>
  <input type="text" name="model_id">

  <label>Temperature</label>
  <input type="number" name="temperature" min="0" max="2" step="0.1" value="0.7">

  <label>Max Tokens</label>
  <input type="number" name="max_tokens" min="1" value="2000">

  <label>System Prompt</label>
  <textarea name="system_prompt"></textarea>

  <label>User Prompt</label>
  <textarea name="user_prompt"></textarea>

  <button type="submit">Save</button>
</form>
```

---

### 3.6 CRUD de Content Schemas

**Rota:** `#content-schemas`

Interface para gerenciar schemas de conteúdo:

```html
<form>
  <label>Name *</label>
  <input type="text" name="name" required>

  <label>Target Type</label>
  <input type="text" name="target_type" value="book_review">

  <label>Description</label>
  <textarea name="description"></textarea>

  <label>Min Total Words</label>
  <input type="number" name="min_total_words">

  <label>Max Total Words</label>
  <input type="number" name="max_total_words">

  <label>TOC Template (JSON)</label>
  <textarea name="toc_template"></textarea>

  <label>Internal Links Count</label>
  <input type="number" name="internal_links_count" value="0">

  <label>External Links Count</label>
  <input type="number" name="external_links_count" value="0">

  <label>
    <input type="checkbox" name="active" checked>
    Active
  </label>

  <button type="submit">Save</button>
</form>
```

---

## 4. Implementação JavaScript

### 4.1 Estrutura do App

**Arquivo:** [`src/static/app.js`](../../src/static/app.js)

```javascript
// Estado global
const AppState = {
  currentSection: 'tasks',
  currentTask: null,
  tasks: [],
  page: 1,
  totalPages: 1,
  filters: {
    search: '',
    status: ''
  }
};

// Navegação
function navigate(section) {
  // Esconde todas as seções
  // Mostra a seção selecionada
  // Atualiza estado
}

// Carregamento de dados
async function loadTasks() {
  const params = new URLSearchParams({
    skip: (AppState.page - 1) * 20,
    limit: 20,
    ...AppState.filters
  });
  
  const response = await fetch(`/tasks?${params}`);
  const data = await response.json();
  
  AppState.tasks = data.tasks;
  AppState.totalPages = Math.ceil(data.total / data.count);
  
  renderTasks();
}

// Renderização
function renderTasks() {
  // Renderiza cards de tarefas
}

function renderTaskDetails(taskId) {
  // Renderiza detalhes da tarefa
}
```

### 4.2 Chamadas à API

```javascript
// Listar tarefas
fetch('/tasks?status=ready_for_review&limit=20')

// Obter detalhes
fetch('/tasks/{submission_id}')

// Submeter livro
fetch('/submit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(formData)
})

// Publicar artigo
fetch('/tasks/{submission_id}/publish_article', {
  method: 'POST'
})

// Salvar rascunho
fetch('/tasks/{submission_id}/draft_article', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ content: '...' })
})
```

---

## 5. Estilos CSS

### 5.1 Estrutura de Estilos

**Arquivo:** [`src/static/styles.css`](../../src/static/styles.css)

Principais áreas de estilo:

| Seção | Descrição |
|-------|-----------|
| Layout | Grid e flexbox |
| Sidebar | Navegação lateral |
| Header | Barra superior |
| Forms | Inputs, botões, validação |
| Cards | Tarefas, artigos |
| Tables | Listas de dados |
| Modals | Diálogos |
| Buttons | Estilos de botões |
| Status | Indicadores de status |

### 5.2 Cores do Sistema

```css
:root {
  /* Cores principais */
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  
  /* Cores de status */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;
  
  /* Cores neutras */
  --color-bg: #f9fafb;
  --color-surface: #ffffff;
  --color-border: #e5e7eb;
  --color-text: #111827;
  --color-text-muted: #6b7280;
}
```

---

## 6. Fluxos de Usuário

### 6.1 Fluxo: Submissão de Livro

```
1. Usuário acessa dashboard
2. Clica em "Book Review" no menu
3. Preenche formulário:
   - Título (obrigatório)
   - Autor (obrigatório)
   - Amazon URL (obrigatório)
   - URLs opcionais
4. Clica em "Submit Book"
5. Sistema:
   - Valida dados
   - Cria submissão no banco
   - Dispara pipeline async
6. Redirect para página de tarefas
7. Usuário vê tarefa com status "pending_scrape"
```

### 6.2 Fluxo: Revisão e Publicação

```
1. Usuário vê tarefa com status "ready_for_review"
2. Clica na tarefa para ver detalhes
3. Visualiza artigo gerado
4. Opcional: Edita rascunho
5. Clica em "Approve" ou "Publish to WordPress"
6. Se aprovado:
   - Status → "approved"
7. Se publicado:
   - Worker posta no WordPress
   - Recebe URL do post
   - Status → "published"
```

---

## 7. Recursos e Funcionalidades

### 7.1 Hotkeys

| Atalho | Ação |
|--------|------|
| `Ctrl+R` | Refresh tarefas |
| `Escape` | Fechar modal |

### 7.2 Feedback Visual

- **Loading**: Spinner durante carregamento
- **Success**: Toast de confirmação
- **Error**: Alerta de erro com mensagem

### 7.3 Responsividade

O layout é responsivo:
- Desktop: Sidebar expandida
- Tablet: Sidebar colapsável
- Mobile: Menu hamburger

---

## 8. Testes

### 8.1 Testes E2E

O frontend pode ser testado com:

- Playwright
- Cypress
- Selenium

### 8.2 Testes Unitários

- Jest para lógica JavaScript
- Testes de componentes

---

## Próximos Passos

- [Infraestrutura e Deploy](./08-infraestrutura-deploy.md)
- [Requisitos e Regras de Negócio](./09-requisitos-regras.md)
