# Mapa temático do Pantanal inteiro: dados, decisões e lacunas

Branch `mapa-pantanal` (sobre `mapa-tematico-base`). O HERO MAP da home não é tocado: o mapa temático é plano (2D), em SVG, com camadas e filtros, só nas páginas de bioma. Cores de atlas (terra clara, água azul, áreas protegidas verdes), sem a cor de destaque do bioma. Camadas e filtros ficam num painel recolhível que sempre começa fechado.

## O que o mapa mostra

- **Pantanal inteiro** (Brasil, Bolívia e Paraguai): ecorregião RESOLVE 2017 (CC BY 4.0), com o limite oficial da parte brasileira (IBGE 2025) por cima. As duas bases não coincidem exatamente (a do IBGE é mais detalhada e chega mais ao sul).
- **Contexto:** países vizinhos com fronteiras e nomes (camada "Fronteiras entre países", ligada por padrão), divisas de estados e departamentos, grade de coordenadas (desligada), escala e norte.
- **Só no Brasil:** rios e córregos nomeados, baías/lagoas/rios largos, unidades de conservação, sedes municipais e localidades indígenas e quilombolas.
- **Fora do Brasil:** cidades (Natural Earth) e os rios principais do Natural Earth, sem nome e sem informação de navegabilidade.

## Como regenerar

1. Baixe e descompacte as bases numa pasta fora do repositório (lista e caminhos no docstring de `build/receitas/pantanal.py`). O zip da BC250 tem ~800 MB; `build/httpzip.py` extrai só os arquivos `hid_*` lendo o zip por HTTP Range. O limite RESOLVE vem de uma consulta GeoJSON ao serviço público da Esri (`ECO_NAME='Pantanal'`), guardada como `resolve.json`.
2. `python3 -I build/mapas_dados.py <pasta> pantanal` gera `data/mapas/pantanal.json` (~730 KB, ~2 min).
3. `python3 -I build/build.py` e `--publish` geram as páginas; o JSON do navegador sai em `assets/mapas/pantanal.json` (~220 KB, ~72 KB com gzip), carregado só quando a seção chega perto da tela.

## Fontes e licenças

RESOLVE Ecoregions 2017 (CC BY 4.0; citar Dinerstein et al., 2017, BioScience); IBGE (Biomas 2025, BC250 2025, Localidades 2022; termo de licença não localizado); MMA CNUC 2025-08 (CC-BY); Natural Earth 1:10m (domínio público).

## Lacunas (por validar)

- **UCs e hidrografia detalhada na Bolívia e no Paraguai:** a WDPA (Protected Planet) não permite redistribuir geometrias e o HydroRIVERS tem licença própria com restrição de redistribuição (não tem nomes). Fontes nacionais (SERNAP, Bolívia; MADES, Paraguai) não foram pesquisadas.
- **Terras Indígenas (FUNAI):** os links oficiais (`geoserver.funai.gov.br`, camada `tis_poligonais`) falham por cadeia de certificados incompleta no servidor; a verificação TLS não foi contornada. Baixar o shapefile manualmente.
- **Planície alagável e cheia × seca:** a camada `hid_terreno_sujeito_inundacao_a` da BC250 não tem feições no Pantanal, e 4.363 das 4.373 massas d'água do bioma estão como "Permanente". Opção mapeada: MapBiomas Água (via Google Earth Engine; exige conta; licença e ano ou média a decidir).
- **Natural Earth descartado para rios nomeados:** nomeia o Rio Paraguai como "Paraná".
- **Relevo sombreado:** não incluído (o Natural Earth tem raster de 91 MB, grosseiro para este recorte; SRTM/Copernicus DEM não foram pesquisados).

## Pendências de validação

O JS/CSS só foi validado por sintaxe e pela geometria renderizada em PNG. Falta o teste no Chrome (desktop e celular): console, camadas, filtros, painel recolhível, painel de detalhes, listas, colisão de rótulos e escala.

## Mapa de localização (América do Sul)

Figura estática no começo da página (SVG embutido, sem JavaScript): oceano azul, continente amarelo, Brasil em amarelo mais forte com os estados contornados e o bioma (inteiro, com as partes na Bolívia e no Paraguai) contornado e pintado na cor de destaque. Países de apoio, estados do Brasil: Natural Earth 1:10 milhões (domínio público); contorno do bioma: o mesmo limite RESOLVE do mapa temático.

- Contexto da América do Sul (igual para todos os biomas, uma vez só): `python3 -I build/localizacao.py contexto <pasta com ne_10m_admin_0_countries/ e ne_10m_admin_1_states_provinces/>` → `data/localizacao/america-do-sul.json`.
- Contorno do bioma e países que ele toca: `python3 -I build/localizacao.py bioma pantanal` → `data/localizacao/pantanal.json` (lê `data/mapas/pantanal.json`).
