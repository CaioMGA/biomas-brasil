# Plano de navegação: outros pontos de entrada e páginas de conteúdo

Decisões da conversa de design. O infográfico (mapa 3D) continua sendo a joia do site, mas deixa de ser passagem obrigatória para ler os conteúdos dos biomas e do Brasil.

## Estrutura

Páginas estáticas geradas por `build/build.py` (leves, sem three.js, boas no celular e para buscadores):

| URL | O que é |
|---|---|
| `/` | O mapa 3D, como hoje. |
| `/biomas/` | Hub: passaporte no topo e um cartão por região (silhueta na cor do bioma, nome, introdução, tempo de leitura, "lido"/selo). Inclui o Brasil. |
| `/biomas/<id>/` | Conteúdo de cada um dos 7 biomas (`amazonia`, `cerrado`, `mata-atlantica`, `caatinga`, `pampa`, `pantanal`, `costeiro`). |
| `/brasil/` | Abertura do Brasil: comparador, glossário, linha do tempo, quiz final, créditos e fontes. |
| `/sobre/` | Como foi feito: tecnologias, dados e fontes, créditos (repetidos do Brasil) e contato. |

## Navegação

- Barra fixa em todas as páginas: **Mapa · Biomas · Sobre**. No mapa ela só aparece depois do loading e da abertura.
- No mapa, **Mergulhar** navega para `/biomas/<id>/`. Lá, **Voltar ao mapa** leva a `/?skipintro#<id>`, com o bioma enquadrado e sem repetir a abertura.
- Páginas de conteúdo: layout do modo leitura atual no desktop (índice lateral, barra de progresso, minutos por seção, seções lidas marcadas).
- Rodapé de cada página de conteúdo: passaporte e sugestões dos outros biomas, **primeiro os não lidos**, com tempo de leitura e selo, e por último os já lidos.
- Passaporte também no topo do hub.

## Mantido como está

- Quiz, selos (acerto mínimo de 60%) e passaporte, com o mesmo armazenamento (`localStorage`, chave `biomas:prog`).
- Créditos e fontes na página do Brasil, repetidos no Sobre.

## Sobre: conteúdo

Tecnologias (three.js e shaders, Terrain Tiles, build em Python, dados do IBGE e do Natural Earth, Cloudflare Pages), fontes e créditos, e contato: caiomga@gmail.com, caiomga.com e brchad.com.

## Fica para depois

- Revisão completa do layout mobile (inclui o índice de seções no celular).
- Entradas temáticas que cruzam os biomas (espécies, vídeos).
