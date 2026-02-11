# Base de Conhecimento — Sessão PIGMEU Copilot

**Última atualização:** 2026-02-11
**Autor (gerado):** PIGMEU Copilot

---

**Objetivo deste documento**
- Consolidar toda a informação, decisões, artefatos e padrões extraídos durante a sessão atual.
- Servir como base de conhecimento e contexto para outros agentes de IA ou desenvolvedores que automatizem geração de artigos.

**Localização dos artefatos principais**
- Config YAML gerada: [config/article-generation-config.yaml](config/article-generation-config.yaml)
- Documentação de padrões: [docs/ARTICLE_PATTERNS_DOCUMENTATION.md](docs/ARTICLE_PATTERNS_DOCUMENTATION.md)
- Arquivo de base desta sessão: [docs/SESSION_KNOWLEDGE_BASE.md](docs/SESSION_KNOWLEDGE_BASE.md)

---

**Resumo executivo da sessão**
- Escopo: Análise de 7 artigos do blog `analisederequisitos.com.br` para extrair padrões de títulos, estrutura, tom, formatação, links e CTAs.
- Resultado principal: criação de um arquivo de configuração YAML parametrizado (`config/article-generation-config.yaml`) e documentação detalhada (`docs/ARTICLE_PATTERNS_DOCUMENTATION.md`) com regras, exemplos e checklist de validação.
- Objetivo final: permitir que agentes/LLMs gerem artigos com a mesma voz, estrutura e SEO do site analisado.

---

**Artigos analisados (fonte)**
1. https://analisederequisitos.com.br/gestao-de-produtos-de-software/
2. https://analisederequisitos.com.br/pmbok-5/
3. https://analisederequisitos.com.br/livro-design-sprint-metodo-google-pdf/
4. https://analisederequisitos.com.br/livro-scrum-kanban-e-scrumban/
5. https://analisederequisitos.com.br/livro-agile-software-requirements/
6. https://analisederequisitos.com.br/livro-gatilhos-mentais/
7. https://analisederequisitos.com.br/guia-agil-pmi/

---

**Principais observações e padrões (resumo)**
- Hierarquia de títulos:
  - 1x H1 (formato descritivo, frequentemente incluindo "(PDF)")
  - H2: 2-4 seções principais (Conteúdo, Sobre os autores, Detalhes, Download, etc.)
  - H3: 3-8 subseções detalhando conceitos, capítulos ou bios
- Estrutura obrigatória: introdução com "Você vai ler nesse artigo:", conteúdo principal, seção "Sobre os autores", detalhes do livro em bullets, CTA de download, seção de doação (PIX), seção de login/cadastro e artigos relacionados.
- Tamanho: alvo total 2000-3500 palavras; seções e H3 têm metas próprias (configuradas no YAML).
- Tom: `Português Brasileiro`, registro profissional-educacional, acessível e prático; variações por tipo de livro (técnico vs. metodológico vs. persuasivo).
- Links: 8-15 links internos; 3-8 externos (Amazon, Goodreads, editoras).
- Formatação: uso moderado de **bold**, *italic*, listas (bullets e numeradas), imagens (2-4) e ocasional blockquote.

---

**Artefatos gerados nesta sessão**
- `config/article-generation-config.yaml` — configuração parametrizada contendo regras de estrutura, tom, SEO, validação e templates. (ver [config/article-generation-config.yaml](config/article-generation-config.yaml))
- `docs/ARTICLE_PATTERNS_DOCUMENTATION.md` — documentação detalhada da análise com exemplos, checklists, padrões por tipo de livro e instruções para aplicação em prompts. (ver [docs/ARTICLE_PATTERNS_DOCUMENTATION.md](docs/ARTICLE_PATTERNS_DOCUMENTATION.md))
- `docs/SESSION_KNOWLEDGE_BASE.md` — este arquivo de conhecimento consolidado.

---

**Trechos práticos e templates (para agentes)**

- Prompt system template (exemplo resumido):

```
System: Você é um especialista em redação de resenhas para um blog técnico.
Siga as regras em config/article-generation-config.yaml.
Produza artigo em Português Brasileiro com 2000-3500 palavras.

User: Gere uma resenha para o livro: {title}, autor: {author}, tópicos: {topics}.
Validation: rodar ArticleValidator conforme regras do YAML.
```

- ArticleValidator checklist (essencial):
  - H1 count == 1
  - H2 count entre 2-4
  - H3 count entre 3-8
  - Presença das seções obrigatórias
  - Word count total entre 2000-3500
  - Images >= 2
  - Internal links 8-15
  - External links 3-8
  - Meta fields preenchidos (title, description, tags)
  - Language == Portuguese (pt-BR)

---

**Como usar esta base por outro agente**
1. Carregue `config/article-generation-config.yaml` como fonte de verdade sobre formato e restrições.
2. Use o template de prompt acima injetando os campos do livro a ser reseñado.
3. Após geração, aplique `ArticleValidator` (checklist acima). Se houver violações, aplique autofixes simples (corrigir counts de headings, adicionar bullets, inserir links internos a partir de um índice) e re-valide; se persistir, reencaminhar para revisão humana.
4. Pré-publique: preencher metadados SEO usando os formatos em `seo_metadata` no YAML.

---

**Notas de implementação técnica (recomendações)**
- Implementar endpoint `/api/validate-article` que aceite HTML/Markdown e retorne lista de violações (baseado no YAML).
- Implementar rotina de `link_finder` que extrai e classifica links internos/externos e sugere âncoras.
- Atualizar `scripts/seed_prompts.py` para incorporar variáveis e constraints do YAML.
- Criar testes automatizados que gerem um artigo de amostra e rodem `ArticleValidator` como integração contínua.

---

**Decisões e justificativas**
- Mantemos a seção "URGENTE: SEM SUA DOAÇÃO, SAIREMOS DO AR" porque aparece de forma recorrente na amostra; é considerada parte do template editorial do site e deve ser suportada pelo gerador (opcional toggle configurável).
- Preservar o autor byline `Francilvio Roberto Alff` quando apropriado; em gerações automatizadas usar campo `author_byline` do YAML para mapear.

---

**Riscos e observações legais**
- Conteúdos que oferecem PDFs para download podem ter questões de direitos autorais; o agente que publicar deve validar legalidade do link/arquivo antes de disponibilizar.
- Recomendação: adicionar uma verificação legal/manual para downloads externos e exibir disclaimer quando necessário.

---

**Próximos passos sugeridos (prioritização)**
1. Integrar `config/article-generation-config.yaml` nos prompts (alta prioridade).
2. Implementar `ArticleValidator` e endpoint `/api/validate-article` (alta).
3. Implementar `link_finder` e `autofix` simples (média).
4. Gerar 1 artigo de teste, validar e ajustar prompts (média).
5. Automatizar testes no CI para validação de estrutura (baixa).

---

**Histórico da Sessão / Change log**
- 2024-11-20: Criado `config/article-generation-config.yaml` e `docs/ARTICLE_PATTERNS_DOCUMENTATION.md` com base em análise de 7 artigos.
- 2026-02-11: Consolidado e gerado `docs/SESSION_KNOWLEDGE_BASE.md` (este arquivo).

---

**Metadados do repositório/contexto**
- Repositório: `pigmeu` (owner: pigmeulabs)
- Branch atual: `main`
- Workspace raiz: `/workspaces/pigmeu`

---

Se desejar, eu posso:
- 1) Atualizar `scripts/seed_prompts.py` para incluir diretamente o conteúdo do YAML;
- 2) Implementar um protótipo do `ArticleValidator` em Python e rodar testes básicos;
- 3) Gerar um artigo de amostra seguindo as regras e entregar para validação.

Indique qual das opções prefere que eu execute em seguida.
