# Biomas do Brasil

Mapa 3D com relevo real dos seis biomas do IBGE, com camadas (relevo, divisas estaduais, rios, capitais, centros urbanos) e um efeito de fundo para cada bioma.

## Testar

    cd ~/projs/biomas-brasil && python3 build/build.py && (sleep 1; xdg-open http://localhost:8000 >/dev/null 2>&1 &) && python3 -m http.server 8000

Abre em http://localhost:8000 (Ctrl+C no terminal para parar). Precisa de internet para o three.js e as fontes.

## Estrutura

- `src/template.html`: página (HTML, CSS, JS e shaders).
- `build/build.py`: gera `index.html` (arquivo único) embutindo os dados.
- `build/conv.py`: biomas do IBGE (geobr, 2019) para caminhos, centroides e mapa de ids.
- `build/dem.py`: relevo a partir dos Terrain Tiles (zoom 6), reamostrado para a grade do mapa.
- `build/layers.py`: divisas (IBGE UF 2022), rios e cidades (Natural Earth 1:10m).
- `data/`: dados gerados (`map.json`, `ids.png`, `dem.png`, `layers.json`) e o GeoPackage de origem.

## Fontes

IBGE (biomas, estados, áreas, vegetação), geobr/Ipea, AWS Terrain Tiles (SRTM, GMTED, ETOPO1), Natural Earth, Flora do Brasil 2020.
