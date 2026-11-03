# Biomas do Brasil

Mapa 3D com relevo real dos seis biomas do IBGE, com camadas (relevo, divisas estaduais, rios, capitais, centros urbanos) e um efeito de fundo para cada bioma.

## Estrutura

- `src/template.html`: o mapa 3D (HTML, CSS, JS e shaders).
- `src/pagina.css`, `src/pagina.js` e `build/paginas.py`: páginas estáticas de conteúdo (`/biomas/`, `/biomas/<bioma>/`, `/brasil/`, `/sobre/`), geradas ao lado do `index.html` com os textos de `data/conteudo/`. Plano em `docs/plano-de-navegacao.md`.
- `build/build.py`: gera `index.html` (mapa, arquivo único) embutindo os dados e chama `paginas.py`. Com `--publish`, grava tudo em `dist/`.
- `build/conv.py`: biomas do IBGE (geobr, 2019) para caminhos, centroides e mapa de ids.
- `build/dem.py`: relevo a partir dos Terrain Tiles (zoom 6), reamostrado para a grade do mapa.
- `build/layers.py`: divisas (IBGE UF 2022), rios e cidades (Natural Earth 1:10m).
- `data/`: dados gerados (`map.json`, `ids.png`, `dem.png`, `layers.json`) e o GeoPackage de origem.

## Fontes

IBGE (biomas, estados, áreas, vegetação), geobr/Ipea, AWS Terrain Tiles (SRTM, GMTED, ETOPO1), Natural Earth, Flora do Brasil 2020.
