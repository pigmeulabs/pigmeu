# Documentação do Sistema PIGMEU

Atualizado em: 2026-02-12

Este diretório contém a documentação oficial do estado atual do sistema, organizada por domínio funcional e técnico.

## Estrutura

```text
docs/
├── README.md
├── 00_contexto/
│   ├── visao-e-escopo.md
│   └── glossario.md
├── 01_requisitos/
│   ├── requisitos-sistema.md
│   ├── estados-e-transicoes-pipeline.md
│   ├── ui-web.md
│   └── criterios-de-aceite.md
├── 02_arquitetura/
│   ├── arquitetura-tecnica.md
│   └── decisoes-tecnicas.md
├── 03_api/
│   ├── contratos-api.md
│   └── erros-e-codigos.md
├── 04_dados/
│   ├── modelo-de-dados.md
│   └── indices-e-migracoes.md
├── 05_modulos/
│   ├── tasks.md
│   ├── credentials.md
│   ├── prompts.md
│   └── article-generation.md
├── 06_operacao/
│   ├── setup.md
│   ├── ambiente-e-envvars.md
│   ├── docker.md
│   └── testes.md
├── 07_ia-agentes/
│   ├── contexto-para-agentes.md
│   └── checklists.md
└── _arquivo_historico/
    ├── sessoes/
    ├── rascunhos/
    └── legado/
```

## Como usar esta documentação

- Contexto e objetivos: `00_contexto/`
- Requisitos e comportamento esperado: `01_requisitos/`
- Arquitetura e decisões técnicas: `02_arquitetura/`
- Contratos de API e erros: `03_api/`
- Modelo de dados e índices: `04_dados/`
- Documentação por módulo: `05_modulos/`
- Operação local e execução: `06_operacao/`
- Guias para agentes/IA: `07_ia-agentes/`

## Histórico

Nenhuma documentação anterior foi excluída. Todo o conteúdo legado foi movido para `docs/_arquivo_historico/`.
