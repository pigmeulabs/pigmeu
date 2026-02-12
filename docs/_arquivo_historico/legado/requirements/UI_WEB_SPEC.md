# UI Web — Especificação Funcional

**Projeto:** PIGMEU  
**Versão:** 1.0  
**Data:** 2026-02-12

---

## 1. Objetivo

Definir a especificação da interface web do PIGMEU para operação do pipeline editorial: criação e gestão de tasks, gestão de credenciais e gestão de prompts.

---

## 2. Estrutura Global da UI

### 2.1 Layout Base
- Sidebar fixa à esquerda.
- Área de conteúdo principal à direita.
- Cabeçalho da página com título do módulo e ações principais.

### 2.2 Navegação Lateral
Itens esperados:
1. Analytics
2. Tasks
3. Content Copilot
4. Book Review
5. Articles
6. Social media
7. SEO Tools
8. Settings
9. Credentials
10. Content Schemas
11. Prompts
12. Logout

---

## 3. Módulo UI: Nova Task de Book Review

### 3.1 Tela
Título: `New Task: Book Review Article`

### 3.2 Campos de formulário
Obrigatórios:
- `Book Title`
- `Author name`
- `Amazon Link`

Opcionais:
- `Additional Content Link` (múltiplos links)
- `Textual information`

### 3.3 Painel de opções
- `Run immediately` (checkbox)
- `Schedule execution` (datetime)
- `Main Category` (select)
- `Article Status` (select)
- `User approval required` (checkbox)

### 3.4 Ações
- Botão primário: `Create Task`

### 3.5 Validações
- Campos obrigatórios preenchidos.
- URLs válidas para campos de link.
- Se `Run immediately = false`, `Schedule execution` obrigatório.
- Regra de duplicidade por `Amazon Link`.

### 3.6 Feedbacks
- Sucesso: confirmação da criação e exibição de `submission_id`.
- Erro: mensagem clara por campo e erro geral de submissão.

---

## 4. Módulo UI: Tasks

### 4.1 Listagem
- Lista paginada de tasks.
- Filtro por status.
- Busca textual (ex.: título/autor).

### 4.2 Detalhe da task
- Dados da submissão.
- Status atual e progresso por etapa.
- Erros e tentativas.
- Links para artefatos associados.

### 4.3 Ações operacionais
- Gerar contexto.
- Gerar artigo.
- Retry de etapas com falha.
- Publicar artigo (quando habilitado).
- Salvar/editar draft de artigo (quando habilitado).

---

## 5. Módulo UI: Credenciais

### 5.1 Tela de listagem
Cada card/linha deve exibir:
- Nome da credencial.
- Tipo/serviço.
- Status (`Active` / `Inactive`).
- Data de criação.
- Último uso.

### 5.2 Ações por credencial
- `Edit`
- `Delete`

### 5.3 Ação global
- Botão `Create Credential`

### 5.4 Modal Add/Edit Credential
Campos:
- `Service`
- `Credential Name`
- `API Key` (obrigatório)
- `Username/email` (opcional)

Ações:
- `Save`

### 5.5 Regras de segurança na UI
- Nunca exibir segredo completo após salvar.
- Não logar segredo no frontend.

---

## 6. Módulo UI: Prompts

### 6.1 Tela de listagem
Cada card/linha deve exibir:
- `Prompt Name`
- `Prompt short description`
- Status (`Active` / `Inactive`)
- Preview/expansão de `System prompt` e `User Prompt`

### 6.2 Ações por prompt
- `Edit`
- `Delete`
- Ativar/Inativar
- Expandir/colapsar detalhes

### 6.3 Ação global
- Botão `Create Prompt`

### 6.4 Modal Add/Edit Prompt
Campos:
- `Prompt name`
- `Short description`
- `System Prompt`
- `User Prompt`

Ações:
- `Save`

### 6.5 Validações
- `Prompt name` obrigatório.
- `System Prompt` obrigatório.
- `User Prompt` obrigatório.

---

## 7. Estados de Interface

### 7.1 Estados de dados
- Loading (listagens e submits)
- Empty state (sem registros)
- Error state (falha de API)

### 7.2 Estados de ação
- Botão desabilitado durante envio.
- Mensagens de sucesso/erro após ações de CRUD.

---

## 8. Requisitos de UX e Acessibilidade

1. Labels visíveis para todos os campos.
2. Feedback de erro próximo ao campo inválido.
3. Ordem de tabulação coerente.
4. Contraste adequado em botões e status.
5. Componentes funcionais em desktop e mobile.

---

## 9. Mapeamento UI -> API (alto nível)

- Criar task: `POST /submit`
- Listar tasks: `GET /tasks`
- Detalhar task: `GET /tasks/{id}`
- Atualizar task: `PATCH /tasks/{id}`
- Retry task: `POST /tasks/{id}/retry`
- Gerar contexto: `POST /tasks/{id}/generate_context`
- Gerar artigo: `POST /tasks/{id}/generate_article`
- Publicar artigo: `POST /tasks/{id}/publish_article`
- Draft artigo: `POST /tasks/{id}/draft_article`
- CRUD credenciais: endpoints de `credentials`
- CRUD prompts: endpoints de `prompts`

