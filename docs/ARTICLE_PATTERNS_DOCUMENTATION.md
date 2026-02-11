# Padrões de artigos – analisederequisitos.com.br

Este guia resume os padrões encontrados nos reviews de livros do blog e mostra como eles foram traduzidos para `docs/article_style.yaml`.

## Fontes analisadas
- https://analisederequisitos.com.br/pmbok-5/ citeturn0open0
- https://analisederequisitos.com.br/gestao-de-produtos-de-software/ citeturn3open0

## Características de tom e voz
- 2ª pessoa (“você”), tom didático e entusiasmado, com ganchos motivacionais logo na abertura. citeturn0open0turn3open0
- Vocabulário simples, ocasional uso de metáforas de cotidiano/cultura pop (ex.: “mestre Jedi”). citeturn3open0
- Parágrafos curtos (2–4 frases) e uso frequente de bullets ou listas numeradas para processos. citeturn0open0

## Estrutura recorrente do artigo
1) **Hero**: breadcrumbs, título H1 com subtítulo/benefício, autor, data e última atualização, capa com legenda. citeturn0open0turn3open0  
2) **TOC**: bloco “Você vai ler nesse artigo:” com links âncora para as seções. citeturn0open0  
3) **Conteúdo principal**: definição/visão geral, lista de tópicos do livro, listas numeradas para “grupos de processo” ou “áreas de conhecimento”. citeturn0open0  
4) **Autor do livro**: mini-bio e credenciais do autor da obra. citeturn3open0  
5) **Download**: seção dedicada “Download do livro” com CTA claro (frequentemente exige login). citeturn0open0  
6) **Doação**: bloco em caixa alta “⚠️ URGENTE: SEM SUA DOAÇÃO, SAIREMOS DO AR” + chave PIX. citeturn0open0  
7) **Login/Cadastro**: seção “FAÇA LOGIN OU CADASTRE-SE GRATUITAMENTE” com botões “Continuar com Google/LinkedIn”. citeturn0open0  
8) **Relacionados**: lista “Mais livros e downloads relacionados” com pelo menos 4 itens. citeturn0open0  
9) **Etiquetas (tags)** e **Bio do autor do artigo** no rodapé. citeturn0open0

## Formatação e CTAs
- Headings principais em H2; subtemas em H3; alertas (doação/login) em caixa alta. citeturn0open0  
- Bullets com hífen; listas numeradas para etapas/processos. citeturn0open0  
- CTAs padrão: “Baixe agora”; “⚠️ URGENTE: SEM SUA DOAÇÃO, SAIREMOS DO AR”; “FAÇA LOGIN OU CADASTRE-SE GRATUITAMENTE”; botões “Continuar com Google/LinkedIn”. citeturn0open0  
- Download costuma ter link âncora interno e nota de legalidade/uso. citeturn0open0  
- Imagens com legenda e alt descrevendo capa/autor. citeturn0open0

## Campos mínimos para persistência/geração
- `titulo`, `subtitulo`, `autor`, `edicao`, `publicacao_ano`, `published_at`, `updated_at`, `cover_image_url`, `download_url`, `categoria`, `tags`, `pix_key`, `related_links`. citeturn0open0turn3open0

## Como usar (pipeline)
1. Carregar `docs/article_style.yaml` para obter persona, ordem de seções e CTAs.  
2. Alimentar os prompts `context_builder` e `article_generator` com os dados do livro e knowledge_base.  
3. Após gerar o markdown, aplicar `formatter_rules` para inserir TOC, blocos de download/doação/login, relacionados, tags e bio.  
4. Validar que parágrafos estão curtos, listas estão em bullets/ordem correta e CTAs mantêm texto exato.
