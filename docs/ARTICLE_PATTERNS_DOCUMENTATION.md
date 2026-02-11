# PADRÕES DE ARTIGOS DESCOBERTOS - Análise detalhada de analisederequisitos.com.br

## Sumário Executivo

Foram analisados 7 artigos de resenhas de livros/guias do blog [analisederequisitos.com.br](https://analisederequisitos.com.br) para extrair padrões consistentes de estrutura, tom, estilo e estratégia de conteúdo. Esta análise fornece a base para configuração parametrizada de geração automática de artigos que se alinhem com a voz e estilo editorial do blog.

### Artigos Analisados:
1. Livro "The Design Sprint: O método usado pelo Google" (PDF)
2. Guia Ágil: Agile Practice Guide (PMI)
3. Livro: Scrum, Kanban e Scrumban
4. Guia PMBOK 5ª edição
5. Livro Agile Software Requirements
6. Livro "Gatilhos Mentais" de Gustavo Ferreira
7. Gestão de Produtos de Software

---

## 1. ESTRUTURA DE ARTIGOS

### 1.1 Hierarquia de Títulos

#### **H1 (Título Principal)**
- **Count**: Exatamente 1 por artigo
- **Position**: Topo do artigo
- **Format Pattern**: 
  ```
  Livro "[TÍTULO COMPLETO EM PORTUGUÊS]" (PDF)
  ou
  Guia [NOME DO GUIA]: [SUBTÍTULO] ([SIGLA/EDIÇÃO])
  ```
- **Exemplos Reais**:
  - "Livro \"The Design Sprint: O método usado pelo Google\" (PDF)"
  - "Guia Ágil: Agile Practice Guide (Guia de Prática Ágil)"
  - "Livro: Scrum, Kanban e Scrumban"
  - "Guia PMBOK 5ª edição em português (download pdf)"

**Padrão**: String descritivo em português com indicação de formato (PDF) quando aplicável.

---

#### **H2 (Seções Principais)**
- **Count**: 2-4 por artigo (média: 3.2)
- **Position**: Dividem o artigo em seções temáticas
- **Exemplos Consistentes**:
  - "Conteúdo do livro [NOME]" - descreve estrutura interna
  - "O que é o Guia [NOME]" - define conceito
  - "Sobre os autores" - bios dos autores
  - "Detalhes do livro [NOME]" - metadados estruturados
  - "[Conceito]" - seções temáticas (ex: "Estrutura do Sprint")

**Padrão**: Títulos descritivos em português, bem diferenciados, que segmentam o conteúdo.

---

#### **H3 (Subsções e Tópicos)**
- **Count**: 3-8 por artigo (média: 5.6)
- **Position**: Subdividem as seções H2
- **Exemplos Consistentes**:
  - Sub-tópicos do conteúdo: "Compreensão do método Sprint", "Estrutura do Sprint", "Tomada de decisão"
  - Autores: "Jake Knapp", "John Zeratsky", "Braden Kowitz"
  - Conceitos: "Reciprocidade: A Dinâmica da Troca", "Prova Social: O Poder da Influência Coletiva"
  - Estrutura: "Os 5 grupos de processo", "As 10 áreas do conhecimento"

**Padrão**: Tópicos específicos, frequentemente com subtítulos explicativos após dois-pontos.

---

### 1.2 Seções Obrigatórias (Ordem Padrão)

1. **Introdução/Apresentação** (Sem H2 dedicado, parte do H1 context)
   - Apresenta livro, autor, contexto
   - Começa com "hook" ou problema/benefício
   
2. **"Você vai ler nesse artigo:" (Sumário Interno)**
   - Sempre presente como subtítulo/tópico
   - Lista os H2/H3 que virão
   - Oferece visão geral e permite scanning rápido

3. **Conteúdo Principal** (múltiplas H2/H3)
   - Explicação detalhada do livro/guia
   - Seções temáticas progressivas
   - Podem ser capítulos do livro ou conceitos relacionados

4. **Sobre os Autores** (H2)
   - Bio individual de cada autor principal
   - Experiência profissional, expertise
   - Links sociais (quando disponíveis)

5. **Detalhes do Livro/Guia** (H2)
   - Formato estruturado (bullets)
   - Metadados: Título, Autor, Editora, Ano, Páginas, ISBN, Links
   
6. **Download/CTA Principal** (H2)
   - "Onde comprar", "Download", "[ação]"
   - Links para Amazon, Livraria Cultura, Goodreads
   - CTA para fazer login/seguir

7. **Seção "URGENTE"** (H2)
   - Donation appeal
   - "SEM SUA DOAÇÃO, SAIREMOS DO AR"
   - Chaves PIX
   - **Nota**: Mantido por consistência com site, mas marca editorial forte

8. **Login/Cadastro** (H2)
   - "FAÇA LOGIN OU CADASTRE-SE GRATUITAMENTE"
   - Botões Google/LinkedIn

9. **Saiba mais / Artigos Relacionados** (H2)
   - Links para conteúdo relacionado
   - "Explore o mundo de..." pattern
   - 3-5 artigos relacionados

---

### 1.3 Contagem de Palavras por Seção

| Seção | Alvo de Palavras | Flexibilidade |
|-------|------------------|------|
| Introdução | 150-250 | ±20% |
| Tabela de Conteúdos | 20-50 | ±10% |
| Conteúdo Principal (por H2) | 300-600 | ±15% |
| Subsseção (H3) | 100-250 | ±20% |
| Sobre Autores | 150-300 | ±15% |
| Detalhes do Livro | 100-150 | ±10% |
| Download/CTA | 50-100 | ±15% |
| **TOTAL DO ARTIGO** | **2000-3500** | **±10%** |

---

## 2. TOM E VOZ (Voice & Tone)

### 2.1 Registro Geral

**Classificação**: Professional Educational + Persuasive Consulting

**Características Dominantes**:
- ✅ Profissional mas tão acessível (não elitista)
- ✅ Educativo sem ser condescendente
- ✅ Bem informado (especialista credível)
- ✅ Prático e acionável (orientado a resultados)
- ✅ Persuasivo mas ético (não é clickbait)
- ✅ Amigável com apelo emocional (human touch)

### 2.2 Frases & Linguagem Característica

#### **Abertura/Hook (Motivacao)**:
```
"Descubra como [livro] pode revolucionar..."
"Aprenda com os autores que desenvolveram [método] no [org]..."
"Transforme sua abordagem de [tema]..."
"Este [livro/guia] oferece um entendimento profundo de..."
```

#### **Posicionamento de Autoridade**:
```
"especialista em [área] com vasta experiência..."
"desenvolvido no [org prestigiosa]..."
"reconhecido por..."
"conhecimento prático de quase duas décadas..."
```

#### **Urgência Branda** (sem alarmismo):
```
"essencial para profissionais que..."
"crucial para quem deseja..."
"fundamental para..."
```

#### **Benefícios/CTA**:
```
"aumentar as chances de sucesso..."
"impulsionar seus resultados..."
"alcançar seus objetivos..."
"transformar sua forma de..."
```

### 2.3 Estrutura de Parágrafos

**Padrão Observado**:
- **Comprimento**: 3-5 linhas (15-20 palavras por frase)
- **Abertura**: Sentença temática (topic sentence)
- **Desenvolvimento**: Explicação + contexto
- **Fechamento**: Exemplo, benefício ou transição
- **Variedade**: Alguns parágrafos com 1-2 linhas para ênfase

**Exemplo Padrão**:
```
[TOPIC] é [DEFINITION]. [EXPANSION]. [EXAMPLE/WHY MATTERS].

A [CONCEPT] explora [DETAIL], demonstrando que [CLAIM]. 
[SUPPORTING EVIDENCE]. Isso permite que [OUTCOME].
```

### 2.4 Tom por Tipo de Livro

| Tipo de Livro | Tom | Exemplos | Características |
|----------------|-----|----------|-----------------|
| **Referência Técnica** (PMBOK, ASR) | Formal-Técnico | Governança, Processos | Estruturado, terminológico |
| **Metodologia Prática** (Scrum, Design Sprint) | Profissional-Prático | Passo-a-passo, aplicação | Equilibrado, exemplos reais |
| **Psicologia/Influência** (Gatilhos) | Persuasivo-Engajador | Comportamento, estratégia | Emocional, conversacional |

---

## 3. ESTRATÉGIA DE LINKS (Internal & External)

### 3.1 Links Internos

**Volume**: 8-15 links internos por artigo

**Tipos e Exemplos**:
- Tags temáticas: `[método-sprint](tag_url)`
- Artigos relacionados: `[Scrum](article_url)`
- Glossário: `[análise de requisitos](homepage_url)`
- Citações: Links dentro de parágrafos via markdown

**Formato de Âncora (Anchor Text)**:
```markdown
[texto descritivo com keywords](url)
```

**Distribuição**:
- Esparsa ao longo do artigo (não concentrada)
- Principalmente em parágrafos principais e introdução
- 1-2 por seção H2

**Exemplos Reais Observados**:
```markdown
[método Sprint](https://analisederequisitos.com.br/tag/metodo-sprint/)
[Scrum Board](https://analisederequisitos.com.br/scrum-board-modelo-exemplo/)
[análise de requisitos](https://analisederequisitos.com.br/)
[Kanban board](https://analisederequisitos.com.br/diferencas-kanban-e-scrum-task-board/)
```

### 3.2 Links Externos

**Volume**: 3-8 links externos

**Tipos**:
1. **Amazon** (compra do livro)
   ```
   https://www.amazon.com.br/[search-slug]
   ```

2. **Livraria Cultura** (alternativa)
   ```
   https://www.livrariacultura.com.br/[product-id]
   ```

3. **Goodreads** (rating + reviews)
   ```
   https://www.goodreads.com/book/show/[book_id]
   ```

4. **PMI/Publisher** (official links quando aplicável)

**Placement**:
- Seção "Onde comprar o livro"
- Seção "Detalhes do livro" (em bullets)
- CTA em "Download" section

### 3.3 Footer/Related Content Links

**Padrão**:
- "Saiba mais sobre [tema relacionado]"
- 3-5 artigos relacionados
- Links para tags temáticas
- Links para categorias

---

## 4. REGRAS DE FORMATAÇÃO

### 4.1 Ênfase (Bold/Italic)

#### **Bold (**texto**)**
- **Uso**: Conceitos-chave, keywords, benefícios
- **Frequência**: 2-4 por seção H2
- **Exemplos**: `**Método Sprint**`, `**análise prática**`, `**5 etapas**`
- **Padrão**: Primeira menção ao conceito importante

#### **Italic (*texto*)**
- **Uso**: Títulos de livros, termos em outro idioma, ênfase
- **Frequência**: 1-2 por seção
- **Exemplos**: `*Design Thinking*`, `*inovação*`
- **Padrão**: Nomes de conceitos originais em inglês

### 4.2 Listas (Bullets e Números)

#### **Bullet Points** (não numerados)
- **Uso**: Características, benefícios, itens relacionados
- **Frequência**: 2-4 listas por artigo
- **Formato**: `• Item um\n• Item dois\n• Item três`
- **Máx itens**: 5-7 por lista
- **Exemplos**:
  ```
  • Gerenciamento da integração
  • Gerenciamento do escopo
  • Gerenciamento do tempo
  • Gerenciamento dos custos
  ```

#### **Numbered Lists**
- **Uso**: Etapas sequenciais, processos, fases
- **Frequência**: 1-3 por artigo
- **Formato**: `1. Etapa um\n2. Etapa dois\n3. Etapa três`
- **Exemplo** (Design Sprint):
  ```
  1. Definir um desafio claro
  2. Gerar uma ampla variedade de soluções
  3. Tomar decisões de forma rápida
  4. Prototipar para aprender
  5. Testar, coletar feedback e iterar
  ```

### 4.3 Imagens

**Volume**: 2-4 imagens por artigo

**Tipos**:
1. **Capa do livro** (principal) - após introdução ou em topo
2. **Screenshot/Excerpt** - do livro quando disponível
3. **Autor** - foto do autor (quando disponível)
4. **Diagrama/Gráfico** - se aplicável

**Dimensões Recomendadas**:
- Featured image: 780x470px
- Inline images: 400-600px width

**Captions** (legendas):
- Em português
- Descritivas, não apenas "Imagem 1"
- Exemplo: "Capa do livro 'Sprint': O método usado no Google para testar e aplicar novas ideias em apenas cinco dias"

### 4.4 Blockquotes

**Uso**: Citações diretas, insights do autor, key takeaways

**Frequência**: 0-1 por artigo

**Formato Markdown**:
```markdown
> "Cotação ou insight importante do livro"
```

---

## 5. METADATA SEO

### 5.1 Title Tag

**Format Pattern**:
```
Livro "[TÍTULO]" ([SUBTÍTULO]) (PDF) - [BENEFÍCIO]
ou
Guia [NOME]: [SUBTÍTULO] em português (download pdf)
```

**Length**: 50-60 caracteres

**Exemplos Reais**:
- "Livro \"The Design Sprint: O método usado pelo Google\" (PDF)"
- "Guia PMBOK 5ª edição em português (download pdf)"
- "Livro: Scrum, Kanban e Scrumban"

### 5.2 Meta Description

**Length**: 155-160 caracteres

**Format Pattern**:
```
Discover [livro/guia] by [author] covering [main topic]. 
Learn [key benefit]. Download PDF free and master 
[skill]. [Secondary benefit or CTA].
```

**Exemplo Gerado**:
```
Discover "Sprint" by Jake Knapp - Google's framework 
for testing ideas in 5 days. Download PDF free and 
learn rapid prototyping & innovation strategies.
```

### 5.3 Keywords

| Tipo | Quantidade | Exemplos |
|------|-----------|----------|
| Primary | 1 | "[livro/guia] [título]" |
| Secondary | 5-8 | "PDF", "download", "agile", "[método]", "management" |
| Long-tail | 3-5 | "[livro] análise prática", "[conceito] em português" |

### 5.4 Categories & Tags

**Category**: "LIVROS E DOWNLOADS" (consistente)

**Tags** (5-10):
- Sempre: "livros", "downloads", "PDF", "agile" (se app.)
- Específicas: "[metodologia]", "[área]", "[conceito]"
- Exemplos:
  ```
  #livros #agile #design-thinking #inovação
  #metodologia-agil #gerenciamento-de-projetos
  #desenvolvimento-de-software #scrum
  ```

---

## 6. PADRÕES DE CONTEÚDO (Content Patterns)

### 6.1 Introduction Pattern

1. **Hook/Problema** (1-2 sent.)
   - Por que este livro importa?
   - Qual problema resolve?
   
2. **Apresentação do Livro** (2-3 sent.)
   - Título, autor, publicação
   - Contexto histórico se relevante
   
3. **O Que Cobre** (2-3 sent.)
   - Visão geral do conteúdo
   - Principais tópicos
   
4. **Quem Deve Ler** (1-2 sent.)
   - Target audience
   - Pré-requisitos
   
5. **Value Proposition** (1-2 sent.)
   - O que o leitor aprenderá
   - Beneficios práticos

**Comprimento Total**: 150-250 palavras

### 6.2 Main Content Pattern (por seção H2)

1. **Contexto/Introdução**
2. **Definição ou Conceito Principal**
3. **Desdobramento (2-3 sub-tópicos com H3)**
4. **Exemplos Práticos**
5. **Aplicação/Benefício**

**Estrutura H3**:
- Cada H3 = 1 conceito específico
- 100-250 palavras por H3
- Começa com definição ou pergunta
- Termina com aplicação prática

### 6.3 Author Bio Pattern

1. **Nome e Título**
2. **Expertise Principal** (1-2 áreas)
3. **Experiência Profissional** (timeline)
4. **Organizações Notáveis**
5. **Método/Abordagem Única**
6. **Links Sociais** (se disponíveis)

**Comprimento**: 150-300 palavras

### 6.4 Book Details Pattern

**Formato Structured Bullets**:
```
• Título: [título original + português if different]
• Autor: [nome(s)]
• Editora: [editora]
• Data Publicação: [ano]
• Edição: [numero]
• Páginas: [numero]
• ISBN-10: [isbn10]
• ISBN-13: [isbn13]
• Goodreads: [link](url)
• Links de Compra: [Amazon](url), [Livraria](url)
```

**Comprimento**: 100-150 palavras (estruturado)

### 6.5 CTA Pattern

1. **Reforço de Valor** (50 palavras)
   - Por que este livro?
   - Que benefício o leitor terá?

2. **Declaração de Ação**
   - "Baixe o PDF"
   - "Clique para acessar"

3. **Download Link** (com autenticação)

4. **Links Alternativos**
   - Comprar na Amazon
   - Comprar em outra livraria
   - Ver no Goodreads

---

## 7. CHAMADAS PARA AÇÃO (CTA)

### 7.1 Primary CTA (Download)

**Posição**: Seção dedicada antes do "URGENTE"

**Text Pattern**:
```
Ao fazer o download do livro em formato PDF no link abaixo, 
você terá acesso a [key content]. Clique no link para 
acessar o PDF e aproveite este recurso valioso.
```

**Styling**: Botão destacado ou link claro

### 7.2 Secondary CTAs (Purchase)

**Locations**:
- "Onde comprar o livro"
- "Detalhes" section

**Links**:
- Amazon (primary)
- Livraria Cultura (alternative)
- Goodreads (social proof)

### 7.3 Donation CTA

**Position**: 
- Sidebar (fixed)
- End of article

**Text**:
```
AJUDE COM UM PIX - Seu apoio é fundamental!
Desde 2011, você tem acesso a conteúdos valiosos e 
gratuitos aqui. Mas a realidade é dura: sem sua ajuda 
imediata, não conseguiremos manter o site no ar.
```

**Tone**: Emotional appeal, not aggressive

---

## 8. ELEMENTOS NÃO ESTRUTURAIS MAS RECORRENTES

### 8.1 Author Byline

**Format**:
```
[Foto] Francilvio Roberto Alff (@chicoalff)
Data Publicação • Última Atualização SMEI
Bio e social links...
```

**Frequência**: Todo artigo tem

**Posição**: Após intro (mini card) e fim (full card)

### 8.2 Related Articles Section

**Format**:
```
### Artigos relacionados
- [Artigo 1](url)
- [Artigo 2](url)
- [Artigo 3](url)
```

**Posição**: Antes de footer

**Quantidade**: 3-5 artigos

### 8.3 Tags/Categories Display

**Position**: End of article

**Format**:
```
[#tag1](url) [#tag2](url) [#tag3](url) ...
```

**Quantity**: 5-10 tags

---

## 9. PADRÕES DE LINGUAGEM POR TIPO DE LIVRO

### Technical/Reference (PMBOK, ASR)
- Usar terminologia específica
- Estrutura linear e progressiva
- Listas extensas são aceitáveis
- Tons mais formais

**Exemplo Language**:
```
"O PMBOK aborda os cinco grupos de processos e as 10 áreas 
do conhecimento envolvidos em um projeto, além de outros 
conceitos e ferramentas."
```

### Methodology/Practical (Design Sprint, Scrum)
- Misturar conceito + aplicação prática
- Usar exemplos do "mundo real"
- Passo-a-passo é bem-vindo
- Tom mais acessível

**Exemplo Language**:
```
"O Sprint fragmenta o trabalho em iterações de tempo fixo, 
normalmente com duração de duas semanas. Durante o sprint, 
a colaboração é fundamental..."
```

### Psychology/Influencing (Gatilhos)
- Mais narrativa, menos listagão
- Apelo emocional + prático
- "Como aplicar" é crítico
- Exemplos de consumidor

**Exemplo Language**:
```
"A reciprocidade, enquanto constructo social arraigado em 
nossa psique, impulsiona a cooperação. Oferecer valor de 
forma genuína ativa o gatilho da reciprocidade..."
```

---

## 10. DESVIOS E VARIAÇÕES DESCOBERTAS

### 10.1 Variações Aceitas

1. **Comprimento de seção**: ±20% é aceitável
2. **Número de H3**: 3-8 é flexível dependendo do livro
3. **Tom**: Varia por tipo de livro (tabela na seção 2.4)
4. **Imagens**: Algumas páginas têm 2, outras 4
5. **Link count**: Mínimo 6, máximo 18 é aceitável

### 10.2 Constantes Não-Negociáveis

1. ✅ **1 H1 exatamente** - nunca duplo
2. ✅ **Seção "Você vai ler"** - sempre presente
3. ✅ **Sobre os autores** - exceto se livro anônimo
4. ✅ **Detalhes estruturados** - sempre presente
5. ✅ **Download CTA** - sempre presente
6. ✅ **Português Brasileiro** - sem exceções
7. ✅ **2-4 imagens mínimo** - visualização importante

---

## 11. APLICAÇÃO PRÁTICA PARA CÓDIGO

### 11.1 Validation Checklist (para validador de artigos)

```python
class ArticleValidator:
    def validate_structure(article):
        ✓ H1 count == 1
        ✓ H2 count between 2-4
        ✓ H3 count between 3-8
        ✓ Required sections: all present
        ✓ Heading hierarchy: no jumps (H1 -> H2 ok, H1 -> H3 NOT ok)
        ✓ Word count: total 2000-3500 ±10%
        ✓ Images: at least 2, at most 4
        ✓ Links internal: 8-15
        ✓ Links external: 3-8
        ✓ Language: Portuguese Brazilian only
        ✓ No broken links
        ✓ All metadata fields: filled
        ✓ Author byline: present
        ✓ Tags: 5-10 tags assigned
```

### 11.2 Template for Prompt Generation

```yaml
PROMPT_TEMPLATE_BOOK_REVIEW:
  system: |
    Você é um especialista em redação de resenhas de livros 
    para um blog de tecnologia. Seus artigos devem seguir 
    padrões específicos de estrutura, tom e formatação.
    [INSERT article-generation-config.yaml CONTENT]
  
  user: |
    Generate article review for:
    - Title: {title}
    - Author: {author}
    - Main Topics: {topics}
    - Target Length: {target_words}
    - Article Type: {type: technical|practical|psychology}
  
  validation: |
    After generation:
    1. Run ArticleValidator
    2. Check all constraints from article-generation-config.yaml
    3. Report any violations
    4. Auto-fix formatting issues
    5. Flag content gaps for human review
```

---

## 12. OBSERVAÇÕES FINAIS

### O que funciona bem neste blog:
1. **Estrutura consistente** - predizível, fácil scanear
2. **Tom equilibrado** - profissional mas acessível
3. **Ações claras** - múltiplos CTAs, sem confusão
4. **SEO considerado** - keywords, meta descriptions, links internos
5. **Autenticidade** - autor do blog aparece em cada artigo (Chico Alff)
6. **Valor agregado** - PDF downloads, links de compra, conteúdo relacionado

### Recomendações para Artigos Gerados:
1. ✅ Manter exatamente esta estrutura
2. ✅ Usar tons variados por tipo de livro
3. ✅ Incluir exemplos práticos, não apenas teoria
4. ✅ Links internos = mais SEO, melhor UX
5. ✅ Sempre incluir meta do autor (Chico Alff) ou criar novo se necessário
6. ✅ Ao menos 2-3 imagens por artigo para visual appeal
7. ✅ CTA claro: download OU compra

---

## 13. PRÓXIMAS ETAPAS (Para Implementação)

1. ✅ **Config File Created**: `/workspaces/pigmeu/config/article-generation-config.yaml`
2. 🔳 **Update Prompt Templates**: scripts/seed_prompts.py com estas diretrizes
3. 🔳 **Create Article Validator**: API endpoint `/validate-article` 
4. 🔳 **Link Finder Implementation**: Extract links from article content
5. 🔳 **Word Count Monitor**: Warn if sections out of range
6. 🔳 **Generate Sample Article**: Test with 1 book, validate, iterate

---

**Document Version**: 1.0  
**Created**: 2024-11-20  
**Analysis Scope**: 7 blog articles  
**Target Audience**: PIGMEU Copilot Developers + LLM Prompt Engineers
