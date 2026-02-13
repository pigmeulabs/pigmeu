# Requisitos do Sistema

Atualizado em: 2026-02-13
Escopo: estado funcional atualmente implementado no codigo.

## 1. Requisitos funcionais

## RF-01 Ingestao de submissao

O sistema deve:

- aceitar criacao de submissao com `title`, `author_name` e `amazon_url` obrigatorios;
- aceitar campos opcionais de contexto/editorial (`other_links`, `textual_information`, `main_category`, `content_schema_id`, `article_status`, `user_approval_required`);
- permitir selecao de `pipeline_id` valido;
- rejeitar submissao duplicada pelo mesmo `amazon_url`;
- enfileirar pipeline automaticamente quando `run_immediately=true`.

## RF-02 Gestao de tasks

O sistema deve:

- listar tasks com pagina/filtro/busca;
- retornar detalhe completo da task (submissao, livro, resumos, KB, artigo, draft, pipeline e progresso);
- permitir atualizar dados de submissao e livro;
- permitir exclusao completa da task e artefatos associados.

## RF-03 Controle de pipeline

O sistema deve:

- permitir retry completo da task;
- permitir retry por etapa especifica;
- limpar artefatos posteriores ao ponto de retry para manter consistencia;
- permitir disparo manual de geracao de contexto;
- permitir disparo manual de geracao de artigo.

## RF-04 Geracao de contexto

O sistema deve:

- coletar dados Amazon e links adicionais;
- consolidar dados bibliograficos;
- executar pesquisa web complementar;
- gerar base de conhecimento em markdown (KB) para suportar geracao de artigo.

## RF-05 Geracao e validacao de artigo

O sistema deve:

- gerar artigo em markdown com apoio de prompts e configuracao de pipeline;
- aplicar content schema quando configurado;
- validar estrutura do artigo e salvar relatorio de validacao;
- persistir artigo com status inicial coerente (`draft`/`in_review`).

## RF-06 Publicacao WordPress

O sistema deve:

- enfileirar publicacao do artigo via worker dedicado;
- converter markdown para HTML;
- resolver/criar categorias e tags no WordPress;
- criar post e salvar `wordpress_post_id` + `wordpress_url`;
- atualizar status da submissao para `published` ao final.

## RF-07 CRUD de credenciais

O sistema deve:

- criar/listar/editar/excluir credenciais de servicos;
- permitir ativar/desativar credenciais;
- mascarar segredo em respostas de API.

## RF-08 CRUD de prompts

O sistema deve:

- criar/listar/editar/excluir prompts;
- permitir filtros por categoria/provedor/nome;
- permitir ativar/desativar prompt;
- expor categorias de prompt combinando dados de prompts e content schemas.

## RF-09 CRUD de content schemas

O sistema deve:

- criar/listar/editar/excluir content schemas;
- permitir ativar/desativar schema;
- aceitar TOC configuravel com regras por secao (nivel, limites, source fields, prompt por item);
- validar coerencia de limites globais e por secao.

## RF-10 Configuracao de pipelines

O sistema deve:

- listar pipelines disponiveis;
- exibir detalhe de etapas e opcoes de AI;
- permitir editar `delay_seconds`, `credential_id` e `prompt_id` por etapa;
- validar atualizacao de etapas de AI e nao-AI.

## RF-11 UI operacional unica

O sistema deve oferecer SPA que permita:

- dashboard de tasks com metricas;
- detalhe da task com timeline por etapa;
- retry por etapa e visualizacao do conteudo gerado por etapa;
- formularios CRUD para Book Review, Credentials, Prompts, Content Schemas e Pipelines.

## 2. Requisitos nao funcionais

## RNF-01 Assincronia e isolamento

- processamento longo deve ocorrer em workers Celery, nao no request HTTP.
- API deve responder rapido para comandos de enqueue (`202`).

## RNF-02 Persistencia e integridade

- banco deve manter unicidade de `amazon_url`.
- dados devem ser atualizados com timestamps de auditoria.
- retry por etapa deve manter consistencia de cadeia (sem artefatos fora de ordem).

## RNF-03 Configurabilidade operacional

- prompts/credentials/pipeline steps devem ser alteraveis sem deploy.
- delays por etapa devem ser configuraveis em segundos.

## RNF-04 Robustez de integracao externa

- scraping deve tolerar falhas com retry/backoff.
- geracao de texto deve prever fallback quando LLM indisponivel.
- leitura de categorias WordPress deve suportar tentativas com e sem auth.

## RNF-05 Observabilidade minima

- API deve expor health endpoint.
- modulo de tasks deve expor estatisticas agregadas.
- logs devem registrar falhas em API e workers.

## RNF-06 Usabilidade operacional

- interface deve indicar estado de processamento por task/etapa.
- operacoes manuais devem ter feedback de sucesso/erro.
- interface deve suportar uso responsivo com breakpoints CSS.

## RNF-07 Testabilidade

- o codigo deve ter suite de testes automatizados (pytest) para API, scrapers e estruturacao de artigo.
- o ambiente de teste depende de MongoDB acessivel via `MONGODB_URI`.

## 3. Regras de negocio

- `run_immediately=false` exige `schedule_execution` na entrada.
- submissao duplicada por `amazon_url` e bloqueada.
- publicacao pode ser bloqueada quando `user_approval_required=true` e status da submissao nao estiver em `approved` ou `ready_for_review`.
- retry por etapa remove resultados de etapas posteriores antes de reenfileirar.
- para etapas sem AI, nao e permitido salvar `prompt_id`/`credential_id` na configuracao de pipeline.
- `delay_seconds` de etapa deve ser inteiro entre `0` e `86400`.

## 4. Wireframes e aderencia

Wireframes historicos em `docs/ui-ux/wireframes/` descrevem:

- Book Review CRUD
- Task details com progresso por etapa
- Credentials list/modal
- Prompts list/modal

A implementacao atual preserva os fluxos centrais desses wireframes e adiciona:

- CRUD de content schemas;
- configuracao detalhada de pipelines;
- cards e acoes com icones e atalhos operacionais.

## 5. Limites e fora de escopo no estado atual

- nao ha autenticao/autorizacao de usuario.
- nao ha scheduler nativo para executar automaticamente `schedule_execution` em horario futuro.
- modulos `Analytics`, `Articles`, `Social Media`, `SEO Tools`, `Settings` e `Logout` estao como placeholders na UI.
- pipeline `links_content_v1` existe como configuracao, mas o encadeamento automatico principal ainda segue o fluxo `book_review_v2`.

## 6. Riscos tecnicos atuais

- credenciais default bootstrapadas em codigo exigem endurecimento para uso produtivo.
- ausencia de auth implica risco de operacao irrestrita em ambientes expostos.
- alta dependencia de scraping externo (Amazon/web) pode gerar instabilidade por bloqueios e mudancas de DOM.
