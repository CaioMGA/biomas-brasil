# Sobre
<!-- id: sobre -->

## Chamada
Um mapa 3D interativo dos biomas do Brasil e uma biblioteca de textos, espécies, vídeos e quizzes para explorar sem passar por ele.

## Tecnologias

### Mapa 3D
three.js e shaders próprios, com relevo real e um efeito de fundo para cada bioma.

### Relevo
Terrain Tiles da AWS (SRTM, GMTED e ETOPO1), reamostrados para a grade do mapa.

### Dados geográficos
Biomas, estados e áreas do IBGE (via geobr/Ipea); rios e cidades do Natural Earth 1:10m; chuva do WorldClim 2.1.

### Mapas dos biomas
Mapas planos, em SVG e JavaScript puro, com camadas e filtros. Os dados vêm do IBGE (Biomas e Base Cartográfica Contínua, 2025), do CNUC/MMA, da ANA, do RESOLVE Ecoregions 2017 e do Natural Earth, conforme o bioma. As fontes ficam na legenda de cada mapa.

### Fotos
Fotos de licença livre do Wikimedia Commons. Autor, licença e link da fonte aparecem junto de cada foto.

### Passaporte
Cada quiz de bioma vencido rende um carimbo. Os carimbos e o progresso de leitura ficam guardados só no seu navegador.

### Build
Python gera o mapa e estas páginas estáticas a partir de um template e dos dados em JSON.

### Hospedagem
Cloudflare Pages.
