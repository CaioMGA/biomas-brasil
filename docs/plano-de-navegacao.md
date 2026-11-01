# Plano de navegação: outros pontos de entrada e páginas de conteúdo

Decisões da conversa de design. O infográfico (mapa 3D) continua sendo a joia do site, mas deixa de ser passagem obrigatória para ler os conteúdos dos biomas e do Brasil.

## Estrutura

Páginas estáticas geradas por `build/build.py` (leves, sem three.js, boas no celular e para buscadores):

| URL | O que é |
|---|---|
| `/` | O mapa 3D, como hoje. |
| `/biomas/` | Hub: passaporte no topo e um cartão por região (silhueta na cor do bioma, nome, introdução, "lido"/"carimbado"). Inclui o Brasil. |
| `/biomas/<id>/` | Conteúdo de cada um dos 7 biomas (`amazonia`, `cerrado`, `mata-atlantica`, `caatinga`, `pampa`, `pantanal`, `costeiro`). |
| `/brasil/` | Abertura do Brasil: comparador, glossário, linha do tempo, quiz final, créditos e fontes. |
| `/sobre/` | Como foi feito: tecnologias, dados e fontes, créditos (repetidos do Brasil) e contato. |

## Navegação

- Barra fixa em todas as páginas: **Mapa · Biomas · Sobre**. No mapa ela só aparece depois do loading e da abertura.
- No mapa, **Mergulhar** navega para `/biomas/<id>/`. Lá, **Ver no mapa** leva a `/#<id>`, com o bioma enquadrado. Vindo de outra página do site (referrer do mesmo domínio), o mapa não mostra o loading com tempo mínimo nem a abertura: isso fica só para quem abre a home direto.
- Páginas de conteúdo: layout do modo leitura atual no desktop (índice lateral, barra de progresso, seções lidas marcadas).
- Rodapé de cada página de conteúdo: passaporte e sugestões dos outros biomas, **primeiro os não lidos**, e por último os já lidos e carimbados.
- Passaporte também no topo do hub.
- Sem tempos de leitura em cartões, índices e seções; o tempo total aparece só abaixo do tagline das páginas de bioma e do Brasil.

## Passaporte e carimbos

- A folha de progresso começa em branco, só com o contorno do Brasil em traço preto, fino e falho.
- Cada bioma completado (quiz com 60% ou mais) vira um carimbo de viagem na folha, na cor do bioma no mapa, com data. Os carimbos têm formas diferentes, ficam levemente tortos e deslocados, e as tintas se mesclam onde se sobrepõem (multiplicação de cor). O quiz do Brasil rende um carimbo azul à parte.
- Mesmo armazenamento de antes (`localStorage`, chave `biomas:prog`); o quiz agora guarda também a data do carimbo (`quiz.em`).
- Código compartilhado entre o painel do mapa e as páginas: `src/comum.js` e `src/comum.css`.

## Gráfico de chuva

Eixo em mm por mês (comum a todos os biomas), valor em mm sobre cada barra e % da chuva do ano embaixo.

## Mantido como está

- Quiz e passaporte, com o mesmo armazenamento (`localStorage`, chave `biomas:prog`).
- Créditos e fontes na página do Brasil, repetidos no Sobre.

## Sobre: conteúdo

Tecnologias (three.js e shaders, Terrain Tiles, build em Python, dados do IBGE e do Natural Earth, Cloudflare Pages), fontes e créditos, e contato: caiomga@gmail.com, caiomga.com e brchad.com.

## Fica para depois

- Revisão completa do layout mobile (inclui o índice de seções no celular).
- Entradas temáticas que cruzam os biomas (espécies, vídeos).
