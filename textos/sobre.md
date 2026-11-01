# Sobre
<!-- id: sobre -->

## Chamada
Um mapa 3D dos biomas do Brasil e uma biblioteca de textos para ler sem passar por ele.

## Tecnologias

### Mapa 3D
three.js e shaders próprios, com relevo real e um efeito de fundo para cada bioma.

### Relevo
Terrain Tiles da AWS (SRTM, GMTED e ETOPO1), reamostrados para a grade do mapa.

### Dados geográficos
Biomas, estados e áreas do IBGE (via geobr/Ipea); rios e cidades do Natural Earth 1:10m; chuva do WorldClim 2.1.

### Build
Python gera o mapa e estas páginas estáticas a partir de um template e dos dados em JSON.

### Hospedagem
Cloudflare Pages.
