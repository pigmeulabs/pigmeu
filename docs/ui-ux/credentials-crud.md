# UI-UX: CRUD de Credenciais

Atualizado em: 2026-02-13
Tela: secao `#credentials-section` + modal `#credential-modal`
Wireframes base:

- `docs/ui-ux/wireframes/crud-credenciais.png`
- `docs/ui-ux/wireframes/crud-credenciais-modal.png`

## 1. Objetivo da tela

Permitir administracao operacional de credenciais usadas por providers LLM e WordPress.

## 2. Lista de credenciais (wireframe de listagem)

## 2.1 Conteudo de cada card (wireframe A)

- nome da credencial
- servico
- URL
- segredo mascarado
- criado em / ultimo uso
- status (`Active`/`Inactive`)

## 2.2 Acoes por card (wireframe B)

- editar
- ativar/desativar
- excluir

Comportamentos:

- card inteiro e clicavel para abrir edicao;
- suporte a teclado (`Enter`/`Space`) para abrir modal;
- exclusao exige confirmacao.

## 2.3 Acao de criar (wireframe C)

- botao `Create Credential` abre modal limpo.

## 3. Modal de credencial (wireframe do cadastro)

## 3.1 Campos principais

- `Service`
- `Credential Name`
- `Base URL`
- `API Key *`
- `Username/Email`
- `Encrypt` (checkbox)
- `Active` (checkbox)

## 3.2 Regras de validacao no frontend

- criacao exige `service`, `name` e `key`;
- para `wordpress`, `Base URL` e obrigatoria;
- em edicao, `key` pode ser omitida para manter segredo atual.

## 4. Endpoints usados

- listar: `GET /settings/credentials`
- criar: `POST /settings/credentials`
- editar/toggle: `PATCH /settings/credentials/{id}`
- excluir: `DELETE /settings/credentials/{id}`

## 5. Integracoes indiretas

Alterar credenciais WordPress afeta diretamente:

- carregamento de categorias no formulario Book Review (`main_category`).

Apos salvar/toggle/delete, a UI dispara refresh de:

- lista de credenciais;
- fontes de categoria WordPress no Book Review.

## 6. Mapeamento wireframe -> implementacao

- anotacao de "servicos/tipos" (wireframe modal A): implementado no select de `Service`.
- anotacao de "nome da credencial" (wireframe modal B): implementado em `Credential Name`.
- anotacao de "campos de autenticacao" (wireframe modal C): implementado por `API Key`, `Base URL` e `Username/Email`.
- anotacoes de acoes operacionais na listagem (status/edit/delete): implementadas como botoes icon-only por card.

## 7. Diferencas frente ao wireframe

- layout final usa cards com acessibilidade e icones, sem alterar o fluxo funcional principal do wireframe.
- UI exibe segredo mascarado retornado pela API, sem exibir valor original em listagem.
