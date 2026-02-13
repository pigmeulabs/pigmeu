# UI Web — Especificação de Interfaces (Wireframes)

**Projeto:** PIGMEU  
**Versão:** 1.0  
**Data:** 2026-02-12  
**Documento base:** `docs/_arquivo_historico/legado/requirements/UI_WEB_SPEC.md`

---

## 1. Objetivo

Definir as especificações funcionais e de interface da UI Web com base nos wireframes em `docs/01_requisitos/00_wireframes`, cobrindo:

- criação de task de Book Review;
- CRUD de credenciais;
- CRUD de prompts;
- comportamento de modais, ações e estados de interface.

---

## 2. Referências Visuais

- `docs/01_requisitos/00_wireframes/crud-task-book-review.png`
- `docs/01_requisitos/00_wireframes/crud-credenciais.png`
- `docs/01_requisitos/00_wireframes/crud-credenciais-modal.png`
- `docs/01_requisitos/00_wireframes/crud-prompts.png`
- `docs/01_requisitos/00_wireframes/crud-prompts-modal.png`

---

## 3. Padrões Globais da Interface

### 3.1 Layout base

- Sidebar fixa à esquerda com logo e navegação principal.
- Área de conteúdo à direita com título do módulo e ação primária.
- Listagens em cards verticais.
- Criação/edição realizada em modal sobreposto para módulos de Configuração.

### 3.2 Navegação lateral esperada

- Analytics
- Tasks
- Content Copilot
- Book Review
- Articles
- Social media
- SEO Tools
- Settings
- Credentials
- Content Schemas
- Prompts
- Logout

### 3.3 Padrões de interação

- Ação primária com botão destacado no topo direito (`Create ...`).
- Ações secundárias por item (status, edit, delete, expand/collapse).
- Feedback visual de sucesso/erro após envio.
- Operações destrutivas com confirmação explícita.

### 3.4 Requisitos globais

- `RUI-GERAL-01`: toda tela deve ter título de contexto.
- `RUI-GERAL-02`: ações primárias devem ficar visíveis sem rolagem horizontal.
- `RUI-GERAL-03`: formulários devem indicar campos obrigatórios.
- `RUI-GERAL-04`: erros de validação devem ser exibidos próximos ao campo.
- `RUI-GERAL-05`: interface deve operar em desktop e mobile sem perda de funcionalidade.

---

## 4. Interface: Nova Task — Book Review

**Wireframe:** `crud-task-book-review.png`

### 4.1 Estrutura da tela

- Bloco A: formulário principal da task.
- Bloco B: painel de opções de execução.
- Botão `Create Task` no canto inferior direito do painel de opções.

### 4.2 Campos do formulário principal (A)

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| Book Title | input text | Sim | Não aceitar vazio |
| Author name | input text | Sim | Não aceitar vazio |
| Amazon Link | input URL | Sim | URL válida |
| Additional Content Link | input URL dinâmico | Não | Permitir múltiplos via botão `+` |
| Textual information | textarea | Não | Texto livre complementar |

### 4.3 Campos do painel de opções (B)

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| Run immediately | checkbox | Não | Se marcado, desabilita agendamento |
| Schedule execution | datetime | Condicional | Obrigatório quando `Run immediately` estiver desmarcado |
| Main Category | select | Não | Categoria editorial principal |
| Article Status | select | Não | Estado inicial editorial |
| User approval required | checkbox | Não | Exige aprovação para publicação |

### 4.4 Comportamentos

- `RUI-TASK-01`: impedir envio sem `Book Title`, `Author name` e `Amazon Link`.
- `RUI-TASK-02`: validar formato de URL nos campos de link.
- `RUI-TASK-03`: exigir `Schedule execution` quando `Run immediately = false`.
- `RUI-TASK-04`: permitir inserir/remover links adicionais sem recarregar a tela.
- `RUI-TASK-05`: mostrar confirmação com identificador da task após criação.
- `RUI-TASK-06`: informar erro de duplicidade para `Amazon Link` já cadastrada.

---

## 5. Interface: Listagem de Credenciais

**Wireframe:** `crud-credenciais.png`

### 5.1 Estrutura da tela

- Título `Credentials`.
- Botão primário `Create Credential`.
- Lista em cards, um card por credencial.

### 5.2 Conteúdo de cada card

- Nome da credencial.
- Tipo/serviço da conta.
- Data/hora de criação.
- Data/hora de último uso.
- Grupo de ações rápidas no canto direito.

### 5.3 Ações por credencial

- Status (`Active`/`Inactive`) com alternância.
- `Edit` para abrir modal em modo edição.
- `Delete` para remoção com confirmação.

### 5.4 Requisitos

- `RUI-CRED-01`: listar credenciais com metadados operacionais (criação/último uso).
- `RUI-CRED-02`: permitir ativar/inativar credencial diretamente na listagem.
- `RUI-CRED-03`: ação `Edit` deve abrir modal pré-preenchido.
- `RUI-CRED-04`: ação `Delete` deve exigir confirmação antes da remoção.
- `RUI-CRED-05`: botão `Create Credential` deve abrir modal em modo criação.

---

## 6. Interface: Modal de Credencial

**Wireframe:** `crud-credenciais-modal.png`

### 6.1 Campos

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| Service | select | Sim | Seleciona serviço/tipo de credencial |
| Credential Name | input text | Sim | Identificador visual da credencial |
| API Key | input password/text | Sim | Valor secreto da credencial |
| Username/email | input text | Condicional | Exigido conforme serviço |

### 6.2 Serviços/tipos previstos no wireframe

- WordPress API Account
- Mistral API
- Groq API

### 6.3 Requisitos

- `RUI-CRED-MODAL-01`: o formulário deve adaptar campos conforme `Service`.
- `RUI-CRED-MODAL-02`: não exibir segredo completo após salvar.
- `RUI-CRED-MODAL-03`: não permitir salvar sem `Service`, `Credential Name` e segredo.
- `RUI-CRED-MODAL-04`: botão `Save` deve fechar modal somente em sucesso.

---

## 7. Interface: Listagem de Prompts

**Wireframe:** `crud-prompts.png`

### 7.1 Estrutura da tela

- Título `Prompts`.
- Botão primário `Create Prompt`.
- Lista em cards com estado recolhido/expandido.

### 7.2 Conteúdo do card (resumido)

- Nome do prompt.
- Short description.
- Grupo de ações: `Active`, `Edit`, `Delete`, `Expand/Collapse`.

### 7.3 Conteúdo do card expandido

- `System prompt` completo.
- `User prompt` completo.

### 7.4 Requisitos

- `RUI-PROMPT-01`: cards devem suportar alternância expandido/recolhido por item.
- `RUI-PROMPT-02`: ação `Active` deve refletir status atual do prompt.
- `RUI-PROMPT-03`: ação `Edit` deve abrir modal com dados carregados.
- `RUI-PROMPT-04`: ação `Delete` deve solicitar confirmação.
- `RUI-PROMPT-05`: botão `Create Prompt` abre modal em modo criação.

---

## 8. Interface: Modal de Prompt

**Wireframe:** `crud-prompts-modal.png`

### 8.1 Seção A — Identificação do prompt

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| Prompt name | input text | Sim | Nome único do prompt |
| Short description | input text | Sim | Resumo funcional curto |

### 8.2 Seção B — Configuração técnica do modelo

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| Provider | select | Sim | Define provedor de IA |
| Credential | select | Sim | Deve filtrar por provider |
| Model | select | Sim | Modelos do provider selecionado |
| Temperature | input numérico | Sim | Faixa configurável |
| Max Tokens | input numérico | Sim | Limite de resposta |

### 8.3 Seção C — Conteúdo do prompt

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| System Prompt | textarea | Sim | Instruções base do agente |
| User Prompt | textarea | Sim | Template de execução |

### 8.4 Requisitos

- `RUI-PROMPT-MODAL-01`: validar obrigatoriedade de todos os campos críticos.
- `RUI-PROMPT-MODAL-02`: `Prompt name` deve ser único.
- `RUI-PROMPT-MODAL-03`: `Credential` deve depender do `Provider` selecionado.
- `RUI-PROMPT-MODAL-04`: `Model` deve depender do `Provider` selecionado.
- `RUI-PROMPT-MODAL-05`: `Save` deve persistir e refletir atualização imediata na listagem.

---

## 9. Estados de Interface

- `RUI-ESTADO-01`: loading para listagens e submit de formulários.
- `RUI-ESTADO-02`: empty state quando não houver registros.
- `RUI-ESTADO-03`: error state com mensagem objetiva de falha de API.
- `RUI-ESTADO-04`: desabilitar botão de ação durante requisição.
- `RUI-ESTADO-05`: mensagens de sucesso após create/update/delete.

---

## 10. Segurança e Acessibilidade

- `RUI-SEG-01`: segredos de credenciais não devem ser logados no frontend.
- `RUI-SEG-02`: segredos devem ser mascarados em listagem/detalhe.
- `RUI-A11Y-01`: todos os campos com label visível.
- `RUI-A11Y-02`: foco de teclado em ordem lógica no modal e na tela.
- `RUI-A11Y-03`: contraste mínimo adequado em botões, textos e status.

---

## 11. Mapeamento UI -> API (alto nível)

- Criar task: `POST /submit`
- Listar tasks: `GET /tasks`
- Detalhar task: `GET /tasks/{submission_id}`
- Atualizar task: `PATCH /tasks/{submission_id}`
- Gerar contexto: `POST /tasks/{submission_id}/generate_context`
- Gerar artigo: `POST /tasks/{submission_id}/generate_article`
- Salvar draft: `POST /tasks/{submission_id}/draft_article`
- Publicar artigo: `POST /tasks/{submission_id}/publish_article`
- Retry task: `POST /tasks/{submission_id}/retry`
- Estatísticas: `GET /tasks/stats`
- CRUD credenciais: `GET/POST/PATCH/DELETE /settings/credentials`
- CRUD prompts: `GET/POST/PATCH/DELETE /settings/prompts`

