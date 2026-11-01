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
- **Cena do carimbo:** ao aceitar ("Sim"), um overlay escuro cobre a tela e o passaporte aparece no centro. Depois de 2 s de suspense o carimbo cai, o passaporte treme e, com vários carimbos, eles entram um após o outro. Por fim, abaixo do passaporte: quantos carimbos foram recebidos e quantos faltam para completar a jornada. "Pular" ou Esc encurtam a cena.
- **Jornada completa:** o carimbo vermelho "Jornada pelos Biomas do Brasil COMPLETA" também é aceito pelo visitante e nunca é carimbado junto dos de bioma. Quando os 7 biomas estão carimbados, a folha pergunta "Você coletou os carimbos de todos os biomas! Deseja carimbar sua jornada como COMPLETA agora?" (Sim / Depois). A cena é a mesma, mas com todos os carimbos entrando em sequência e, após 2 s, o vermelho, com um tremor bem mais forte. Em seguida: "Você carimbou todos os biomas! Você completou sua jornada pelos Biomas do Brasil, parabéns!".
- **Compartilhar passaporte** gera um PNG da folha (Web Share com arquivo quando o navegador permite; senão baixa o arquivo).
- **Aceite do carimbo:** vencer o quiz dá direito ao carimbo, que fica pendente até o visitante aceitar. Com carimbos pendentes, a folha recebe um overlay: "Você recebeu o(s) carimbo(s) dos biomas X, Y… Deseja carimbar seu passaporte agora?" com **Sim** (os carimbos entram na folha com animação) e **Depois** (não pergunta de novo nesta sessão).
- **Armazenamento local:** `biomas:carimbos` = `{ <bioma|completa>: { em: "AAAA-MM-DD", aceito: true|false } }`. Nos biomas, `em` é o dia em que o quiz foi vencido (no `completa`, o dia do último carimbo de bioma), e é essa data que aparece no carimbo, não a do aceite. O progresso de leitura continua em `biomas:prog`; quem já tinha vencido quizzes antes entra como pendente, com a data do quiz.
- Código compartilhado entre o painel do mapa e as páginas: `src/comum.js` e `src/comum.css`.

## Gráfico de chuva

Eixo em mm por mês (comum a todos os biomas), valor em mm sobre cada barra e % da chuva do ano embaixo.

## Ferramentas do mapa

- **Ocultar controles:** botão embaixo à esquerda esconde a coluna de navegação, seleção de biomas, camadas e escala (o título e o painel ficam).
- **Screenshot:** gera um PNG só com o mapa (e os textos dele), o título e a tagline; embaixo à esquerda, a marca da brchad com o endereço do site. Controles, painel e o texto de ajuda não entram. Usa `html-to-image` (carregado sob demanda do cdnjs).
- **Tutorial:** botão no menu de navegação (`/?tutorial` nas outras páginas) abre um overlay que destaca cada recurso, com Anterior e Próximo; mapa e painel ficam inertes enquanto ele está aberto.
- Visualização padrão: rios e siglas dos estados desligados; o texto de ajuda do mapa quebra em linhas.

## Painel do mapa

A linha "Espécies" (3 caixinhas) foi substituída pelo bloco **Mais emblemática** (`emblema` em `data/conteudo/<bioma>.json`), com foto opcional (`emblema.foto = { src, credito }`) e link para as fichas do bioma.

## Lab dos carimbos

`/lab-carimbo/` (só no build de desenvolvimento, `python3 build/build.py`; não vai para o `dist/`) ajusta o timing das animações de carimbo e a intensidade e duração do tremor do passaporte: queda do carimbo, atraso até o tremor, tremor leve e forte, clarão vermelho e as pausas das duas cenas. Testa em uma folha ou roda as cenas reais sem gravar nada. "Aplicar neste navegador" grava em `localStorage` (`biomas:anim`) e as cenas reais passam a usar os valores; "Copiar valores" exporta o JSON para virar o padrão em `ANIM_PADRAO` (`src/comum.js`).

## Mantido como está

- Quiz e passaporte, com o mesmo armazenamento (`localStorage`, chave `biomas:prog`).
- Créditos e fontes na página do Brasil, repetidos no Sobre.

## Sobre: conteúdo

Tecnologias (three.js e shaders, Terrain Tiles, build em Python, dados do IBGE e do Natural Earth, Cloudflare Pages), fontes e créditos, e contato: caiomga@gmail.com, caiomga.com e brchad.com.

## Fica para depois

- Revisão completa do layout mobile (inclui o índice de seções no celular).
- Entradas temáticas que cruzam os biomas (espécies, vídeos).
