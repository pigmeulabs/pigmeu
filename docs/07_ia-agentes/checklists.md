# Checklists

## Checklist de implementação

- [ ] Requisito está documentado em `01_requisitos/`.
- [ ] Código alterado na camada correta (API/repositório/worker/UI).
- [ ] Contrato de API atualizado em `03_api/contratos-api.md`.
- [ ] Erros/códigos atualizados em `03_api/erros-e-codigos.md`.
- [ ] Modelo de dados/índices atualizados em `04_dados/` quando necessário.
- [ ] Testes executados com sucesso (`pytest -q`).

## Checklist de correção de bug

- [ ] Cenário reproduzido.
- [ ] Causa raiz identificada.
- [ ] Correção com menor impacto possível.
- [ ] Regressão coberta por teste novo ou ajuste de teste existente.
- [ ] Documentação ajustada se comportamento mudou.

## Checklist de release interno

- [ ] Migrações executadas sem erro.
- [ ] API e worker sobem no Docker Compose.
- [ ] Health checks OK.
- [ ] Fluxo básico: submit -> contexto -> artigo -> publicação validado.
- [ ] Nenhum segredo exposto em logs/respostas.
