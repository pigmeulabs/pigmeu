


# PIGPEU.labs — UI/UX Design System Specification

**Versão:** 1.0
**Objetivo:** Padronização visual e estrutural das interfaces.
**Público-alvo:** Desenvolvedores frontend, designers e agentes de IA responsáveis por geração ou validação de UI.

---

# 1. Objetivo do Documento

Definir:

* Paleta de cores oficial
* Sistema tipográfico
* Sistema de espaçamento
* Padrões de componentes
* Estados visuais
* Regras de consistência

Este documento deve ser tratado como **fonte única de verdade (Single Source of Truth)** para implementação de UI.

---

# 2. Design Tokens

## 2.1 Color Tokens

### Primary

```yaml
color.primary: "#2F6FED"
color.primary.hover: "#1E4FD8"
color.primary.light: "#E8F0FF"
```

### Neutral

```yaml
color.background: "#F5F7FA"
color.surface: "#FFFFFF"
color.border: "#E4E7EC"
color.text.primary: "#101828"
color.text.secondary: "#667085"
color.text.muted: "#98A2B3"
```

### Status

```yaml
color.success: "#12B76A"
color.success.light: "#ECFDF3"

color.warning: "#F79009"

color.danger: "#F04438"
color.danger.light: "#FEF3F2"

color.info: "#0BA5EC"
```

---

# 3. Tipografia

## 3.1 Fonte

```yaml
font.family.primary: "Inter, sans-serif"
```

## 3.2 Escala Tipográfica

| Token        | Size | Weight |
| ------------ | ---- | ------ |
| text.h1      | 28px | 600    |
| text.h2      | 22px | 600    |
| text.h3      | 18px | 600    |
| text.body.lg | 16px | 400    |
| text.body    | 14px | 400    |
| text.small   | 12px | 400    |
| text.label   | 13px | 500    |
| text.badge   | 12px | 600    |

## 3.3 Regras

* Nunca usar preto absoluto (#000)
* Títulos sempre weight 600
* Labels acima dos campos
* Texto secundário deve usar `color.text.secondary`

---

# 4. Sistema de Espaçamento

## 4.1 Escala

```yaml
space.1: 4px
space.2: 8px
space.3: 12px
space.4: 16px
space.5: 24px
space.6: 32px
space.7: 48px
```

## 4.2 Regras

* Padding interno de cards: 24px
* Espaço entre campos: 16px
* Espaço entre seções: 32px
* Border radius padrão: 8px
* Border radius card: 12px

---

# 5. Componentes

---

# 5.1 Botões

## Botão Primário

```yaml
background: color.primary
text: #FFFFFF
border: none
radius: 8px
padding: 10px 16px
font-weight: 500
```

Hover:

```yaml
background: color.primary.hover
```

---

## Botão Secundário

```yaml
background: #FFFFFF
border: 1px solid #D0D5DD
text: #344054
```

Hover:

```yaml
background: #F2F4F7
```

---

## Botão Danger

```yaml
background: color.danger
text: #FFFFFF
```

Hover:

```yaml
background: "#D92D20"
```

---

## Botão Ghost

```yaml
background: transparent
border: none
text: color.primary
```

Hover:

```yaml
background: color.primary.light
```

---

# 5.2 Badges de Status

Formato:

```yaml
border-radius: 999px
padding: 4px 10px
font-size: 12px
font-weight: 600
```

### Variantes

Processed:

```yaml
background: color.success.light
text: "#027A48"
```

Failed:

```yaml
background: color.danger.light
text: "#B42318"
```

To Do:

```yaml
background: "#F2F4F7"
text: "#344054"
```

---

# 5.3 Cards

```yaml
background: color.surface
border: 1px solid color.border
border-radius: 12px
box-shadow: "0 1px 2px rgba(16,24,40,0.05)"
padding: 24px
```

Hover opcional:

```yaml
box-shadow: "0 4px 6px rgba(16,24,40,0.08)"
```

---

# 5.4 Inputs

## Input padrão

```yaml
height: 40px
border: 1px solid #D0D5DD
border-radius: 8px
padding: 0 12px
background: #FFFFFF
```

Focus:

```yaml
border: 1px solid color.primary
box-shadow: 0 0 0 3px rgba(47,111,237,0.1)
```

Erro:

```yaml
border: 1px solid color.danger
```

Texto erro:

```yaml
font-size: 12px
color: color.danger
```

---

# 6. Layout

## 6.1 Grid

```yaml
max-width: 1200px
grid-columns: 12
gutter: 24px
sidebar-width: 240px
```

## 6.2 Estrutura padrão

```
Sidebar fixa
|
Container principal centralizado
|
Cards organizados verticalmente
```

---

# 7. Pipeline Visual

## Estados

| Estado    | Cor           |
| --------- | ------------- |
| Completed | Verde         |
| Current   | Azul          |
| Future    | Cinza outline |

Regras:

* Etapa atual: preenchimento azul
* Concluída: verde sólido
* Próxima: cinza claro
* Linha base: #E4E7EC

---

# 8. Consistência de Linguagem

Regras:

* Não misturar idiomas na mesma tela
* Usar Title Case para títulos
* Padronizar termos:

| Errado       | Correto      |
| ------------ | ------------ |
| ATIVO        | Active       |
| Desativar    | Deactivate   |
| Task details | Task Details |

---

# 9. Estados de Interação

## Hover

Sempre:

* Mudança leve de background
* Cursor pointer
* Nunca alterar layout

## Disabled

```yaml
opacity: 0.5
cursor: not-allowed
```

---

# 10. Regras para Agentes de IA

Ao gerar UI:

1. Sempre usar tokens definidos neste documento.
2. Nunca usar cores fora da paleta.
3. Nunca criar tamanhos arbitrários.
4. Sempre respeitar escala de espaçamento.
5. Usar componente existente antes de criar novo.
6. Não misturar estilos antigos.
