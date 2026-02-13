# Decisões Técnicas

## DT-01 FastAPI + Celery + MongoDB
- Motivo: separação clara entre API síncrona e processamento assíncrono.
- Impacto: API responde rápido enquanto workers executam tarefas pesadas.

## DT-02 Repositórios para acesso a dados
- Motivo: centralizar regras de persistência e reduzir duplicação.
- Impacto: manutenção mais simples de contratos de dados.

## DT-03 LLM com roteamento por provedor
- Motivo: evitar lock-in e permitir fallback entre OpenAI/Groq/Mistral.
- Impacto: resiliência maior quando um provedor não está configurado.

## DT-04 Scraping best-effort
- Motivo: Goodreads/Amazon podem falhar intermitentemente.
- Impacto: pipeline segue com fallback de dados mínimos.

## DT-05 Validação estrutural de artigo
- Motivo: padronizar qualidade mínima do output.
- Regras-chave: H1 único, 8 H2, seção com H3, faixa de palavras e validação de parágrafos.

## DT-06 UI sem framework SPA pesado
- Motivo: simplicidade operacional e menor overhead.
- Impacto: manutenção manual de JS/CSS, porém stack mais enxuta.

## DT-07 Sem autenticação no estágio atual
- Motivo: foco inicial em fluxo operacional interno.
- Risco: API exposta sem controle de acesso em ambientes públicos.

## DT-08 Agendamento persistido sem executor temporal
- Motivo: priorização de MVP funcional.
- Impacto: `schedule_execution` ainda depende de implementação de scheduler.
