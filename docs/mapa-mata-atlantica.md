# Mapa temático da Mata Atlântica inteira: dados, decisões e lacunas

Branch `mapa-mata-atlantica` (sobre `mapa-tematico-base`). O HERO MAP da home não é tocado. O mapa segue o mesmo padrão do Pantanal (plano, SVG, camadas e filtros num painel recolhível que começa fechado, cores de atlas, bioma de uma cor só), com as mudanças que a escala deste bioma exige.

## O que o mapa mostra

- **Bioma inteiro** (Brasil, Paraguai e Argentina): as 8 ecorregiões RESOLVE 2017 da Mata Atlântica (CC BY 4.0), com o contorno externo desenhado sem as divisas entre elas, e o limite oficial do IBGE por cima (sem as ilhas oceânicas: Fernando de Noronha, São Pedro e São Paulo).
- **Contexto:** oceano azul, países com cores e nomes, fronteiras, estados do Brasil em cores diferentes (vizinhos nunca repetem cor), divisas de estados e departamentos, grade (desligada), escala e norte.
- **Ecorregiões (contornos):** camada desligada por padrão, só linhas com os nomes em português (tradução livre dos nomes RESOLVE); o bioma continua de uma cor só.
- **Unidades de conservação (só Brasil):** ~1.800 no bioma. Fundidas em 6 categorias (proteção integral/uso sustentável × federal/estadual/municipal), desenhando só as de mais de 1.000 ha; tocar numa mancha mostra quantas unidades ela representa. A lista em texto traz as 294 federais e estaduais de proteção integral. Filtros: proteção e esfera.
- **Cidades:** capitais estaduais e cidades grandes do Brasil (população estimada acima de ~400 mil no Natural Earth) e cidades com mais de 100 mil no Paraguai e na Argentina.
- **Rios principais:** Natural Earth, sem nome de navegabilidade (a drenagem do IBGE tem milhões de trechos nesta área).
- Não há camada de povos (decisão: milhares de localidades quilombolas e indígenas não cabem nesta escala).

## Como regenerar

1. Bases fora do repositório, nas subpastas listadas no docstring de `build/receitas/mata_atlantica.py` (as 8 ecorregiões saem de consultas GeoJSON ao serviço público da Esri, `ECO_NAME=<nome>`, com `maxAllowableOffset=0.003`).
2. `python3 -I build/mapas_dados.py <pasta> mata-atlantica` (~10 s) → `data/mapas/mata-atlantica.json` (~690 KB).
3. `python3 -I build/localizacao.py bioma mata-atlantica` → `data/localizacao/mata-atlantica.json`.
4. `python3 -I build/build.py` e `--publish`. O JSON do navegador sai em `assets/mapas/mata-atlantica.json` (~215 KB, ~72 KB com gzip), carregado só quando a seção chega perto da tela.

## Fontes e licenças

RESOLVE Ecoregions 2017 (CC BY 4.0; citar Dinerstein et al., 2017, BioScience); IBGE Biomas 2025 (termo de licença não localizado); MMA CNUC 2025-08 (CC-BY); Natural Earth 1:10m (domínio público).

## Lacunas (por validar)

- **Cobertura florestal remanescente** (a floresta que restou, que seria a camada central): não incluída. O Atlas da SOS Mata Atlântica/INPE exige cadastro e não tem licença aberta confirmada; o MapBiomas só sai pelo Google Earth Engine; o Hansen Global Forest Change (CC BY 4.0) conta qualquer árvore, inclusive plantios, e tem tiles de até 290 MB. Dados abertos de remanescentes nativos viabilizariam a camada.
- **UCs no Paraguai e na Argentina:** a base mundial (WDPA) não permite redistribuição.
- **Rios com nome e navegabilidade em detalhe:** só os principais do Natural Earth.
- **Terras Indígenas e territórios quilombolas:** não incluídos.
- **Natural Earth:** as estimativas de população são defasadas (ex.: Joinville aparece com 433 mil), e o Natural Earth marca o Niterói como capital (o corte de população o mantém por mérito próprio).

## Pendências de validação

O JS/CSS só foi validado por sintaxe e pela geometria renderizada em PNG. Falta o teste no Chrome (desktop e celular): painel recolhível, camadas e filtros, as manchas de UCs, legenda dinâmica, colisão dos rótulos (a camada de ecorregiões e os estados do Brasil geram muitos textos) e o carrossel de espécies.
