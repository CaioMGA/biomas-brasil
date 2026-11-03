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
- Cada bioma completado (quiz com 60% ou mais) vira um carimbo de viagem na folha, na cor do bioma no mapa, com data. Os carimbos têm formas diferentes, ficam levemente tortos e deslocados, e as tintas se mesclam onde se sobrepõem (multiplicação de cor). O quiz do Brasil rende um carimbo azul à parte, em losango alongado como o da bandeira.
- A folha é um papel levemente amassado (filtro SVG) que projeta sombra; o contorno do Brasil e o dos 6 biomas continentais são desenhados em traço fino e falho. Embaixo à direita, o nome do site em fonte do site, como papel timbrado, com a barra de gradiente do painel do Brasil logo abaixo, com a mesma textura de tinta dos carimbos.
- No fim das páginas de conteúdo, os outros biomas aparecem em dois grupos: "Ainda sem carimbo" e "Já carimbados".
- **São 8 carimbos:** os 7 biomas e o **Quiz final** (Brasil), que pode ser vencido em qualquer ordem. Com os 8, vem o carimbo vermelho "Jornada pelos Biomas do Brasil COMPLETA".
- **Sem aceite:** vencer um quiz coloca o carimbo direto na folha, e a folha sempre mostra todos os carimbos que o visitante tem.
- **Cena do carimbo:** ao vencer o quiz (ou, na carga seguinte de qualquer página, se ainda não viu a cena), um overlay escuro cobre a tela com o passaporte já com os carimbos anteriores. Depois de 2 s de suspense o carimbo novo cai, o passaporte treme e, abaixo, aparecem quantos carimbos foram recebidos e quantos faltam. "Pular" ou Esc encurtam a cena.
- **Jornada completa:** quando os 8 carimbos existem e falta o vermelho, a cena da jornada completa abre em **qualquer página** (inclusive o mapa): os carimbos entram em sequência, com o último vencido como penúltimo, e o vermelho por último, com o tremor bem mais forte. O vermelho é gravado quando a cena começa, então "Pular" não o perde, e a cena só acontece uma vez.
- **Capa (só em `/biomas/jornada/`):** o passaporte **sempre começa fechado**, com capa de couro verde e emblema dourado, e só abre girando na lombada quando o visitante clica na capa (ou usa Enter); clicar no passaporte aberto fecha a capa de novo. Os cards abaixo do passaporte carregam o estado de cada carimbo: o carimbado mostra o mini-carimbo e "Carimbado em <data>"; o sem carimbo mostra "Faça o quiz para carimbar →" (no Brasil, "Quiz final").
- **Hierarquia da página do passaporte:** o passaporte (livreto) é o herói e vem primeiro; logo abaixo ficam o painel de progresso ("N de 8 carimbos") ou, com a jornada completa, o painel verde "Você completou a jornada!", e depois os botões.
- **Entrada:** na primeira vez que o passaporte aparece na sessão, os carimbos que o visitante já tem caem em sequência (curto; desligado com `prefers-reduced-motion`).
- **Compartilhar passaporte** gera um JPEG da folha, com no máximo 500 KB, no formato escolhido num popup que abre ao clicar em **Compartilhar**: quadrado (1080 × 1080), stories (1080 × 1920) ou horizontal (Web Share com arquivo quando o navegador permite; senão baixa o arquivo).
- **Armazenamento local:** `biomas:carimbos` = `{ <bioma|brasil|completa>: { em: "AAAA-MM-DD", ts, visto: true|false } }`. `em` é o dia em que o quiz foi vencido (no `completa`, o do último carimbo), e é essa data que aparece no carimbo. `visto` diz se a cena do overlay já foi mostrada. O formato antigo (`aceito`) é migrado sozinho: tudo vira visto, e uma `completa` nunca aceita some (ela passa a exigir os 8). O progresso de leitura continua em `biomas:prog`.
- **Fluxo das páginas:** o último bioma (Costeiro) aponta para o Brasil ("Quiz final"). O fim da página do Brasil mostra o primeiro bioma ainda sem carimbo (Amazônia no HTML estático) e, com os 7 carimbados (com ou sem o do Brasil), leva a `/biomas/`. O card do Brasil é o último nas grades.
- Código compartilhado entre o painel do mapa e as páginas: `src/comum.js` e `src/comum.css`.

## Gráfico de chuva

Eixo em mm por mês (comum a todos os biomas), valor em mm sobre cada barra e % da chuva do ano embaixo.

## Ferramentas do mapa

- **Ocultar controles:** botão no alto da coluna de controles, antes do conteúdo que ele esconde (bússola, biomas, camadas e escala; o título, o painel e os botões de ferramenta ficam). No celular os controles começam escondidos e o botão é um texto: "Mostrar filtros" / "Ocultar filtros".
- **Screenshot:** gera um JPEG (no máximo 500 KB) só com o mapa (e os textos dele), o título e a tagline; embaixo à esquerda, a marca da brchad com o endereço do site. Controles, painel e o texto de ajuda não entram. Usa `html-to-image` (carregado sob demanda do cdnjs).
- **Tutorial:** botão no menu de navegação (`/?tutorial` nas outras páginas) abre um overlay que destaca cada recurso, com Anterior e Próximo; mapa e painel ficam inertes enquanto ele está aberto.
- **Celular:** o mapa começa em 2D; a coluna de filtros é um painel de vidro (fundo translúcido com blur), sem a lista de biomas (o bioma se escolhe tocando no mapa). Dois dedos: a pinça dá zoom, a torção gira o mapa e mover os dois juntos arrasta; um dedo arrasta. No toque, os nomes dos biomas no mapa não capturam o dedo.
- Visualização padrão: rios e siglas dos estados desligados; o texto de ajuda do mapa quebra em linhas.

## Painel do mapa

A linha "Espécies" (3 caixinhas) foi substituída pelo bloco **Mais emblemática** (`emblema` em `data/conteudo/<bioma>.json`), com foto opcional (`emblema.foto = { src, credito }`) e link para as fichas do bioma.

## Lab dos carimbos

`/lab-carimbo/` (só no build de desenvolvimento, `python3 build/build.py`; não vai para o `dist/`) ajusta o timing das animações de carimbo e a intensidade e duração do tremor do passaporte: queda do carimbo, atraso até o tremor, tremor leve e forte, clarão vermelho e as pausas das duas cenas. Testa em uma folha ou roda as cenas reais sem gravar nada. "Aplicar neste navegador" grava em `localStorage` (`biomas:anim`) e as cenas reais passam a usar os valores; "Copiar valores" exporta o JSON para virar o padrão em `ANIM_PADRAO` (`src/comum.js`).

## Textos em Markdown

Todos os textos de conteúdo (sem textos de interface) estão em `textos/*.md`, um arquivo por página. Os JSONs de `data/conteudo/` e `data/sobre.json` continuam sendo a fonte do site: `python3 build/conteudo_md.py exportar` gera os md e `importar` devolve os textos editados aos JSONs, validando o formato (`--simular` só confere). Detalhes de como editar em `textos/LEIA-ME.md`.

## Mantido como está

- Quiz e passaporte, com o mesmo armazenamento (`localStorage`, chave `biomas:prog`).
- **Créditos e fontes são a última seção de todas as páginas** (os 7 biomas e o Brasil, no índice lateral; no hub e no Sobre, no fim). Nos biomas a lista de vídeos mostra só os da própria página, e a frase de fontes de cada bioma fica dentro dos créditos.

## Sobre: conteúdo

Tecnologias (three.js e shaders, Terrain Tiles, build em Python, dados do IBGE e do Natural Earth, Cloudflare Pages), fontes e créditos, e contato: caiomga@gmail.com, caiomga.com e brchad.com.

## Fica para depois

- Revisão completa do layout mobile (inclui o índice de seções no celular).
- Entradas temáticas que cruzam os biomas (espécies, vídeos).
