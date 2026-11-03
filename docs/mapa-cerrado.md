# Mapa temático do Cerrado: os rios e as bacias ("berço das águas")

Branch `mapa-cerrado` (sobre `mapa-tematico-base`). O HERO MAP da home não é tocado. **Decisão do projeto:** o mapa é **só sobre os rios** e as bacias para onde correm, sem cidades, unidades de conservação, desmatamento ou fogo.

## O que o mapa mostra

- **23 rios** que nascem ou correm pelo Cerrado, da drenagem do IBGE (BC250), só no trecho que aparece na moldura: bacia do **São Francisco** (São Francisco, das Velhas, Paracatu, Urucuia, Grande (BA), Carinhanha, Paraopeba), **Tocantins-Araguaia** (Tocantins, Araguaia, Paranã, do Sono, das Mortes, das Almas), **Paraná** (Paranaíba, Grande (MG/SP), Paraná, Corumbá), **Parnaíba**, **Paraguai** (Paraguai, Cuiabá) e **Amazônica** (Xingu, Teles Pires, Juruena, que nascem na transição com a Amazônia).
- **Filtro por bacia hidrográfica** (todas ou uma), e toque num rio para ver a bacia e por onde ele passa.
- **Lista dos rios** abaixo do mapa, antes de "Sobre os dados deste mapa", aberta e acompanhando o filtro, com a bacia, os países e os estados do Brasil.
- **Contexto:** bioma de uma cor só (ecorregião RESOLVE "Cerrado" + limite oficial do IBGE por cima), oceano azul no canto da costa, países e estados do Brasil em cores diferentes, grade (desligada), escala e norte.

## Como foi feito

- **Rios:** `shp.read_por_nome` (índice `.shx`) e uma caixa de coordenadas por rio, porque o nome sozinho não basta (há "Rio Grande", "Rio das Mortes"… em outras regiões). O "Rio Grande" aparece duas vezes, em duas bacias (BA e MG/SP). As caixas foram conferidas contra a extensão encontrada na base (todos os 23 rios foram achados).
- **Bacia de cada rio:** conhecimento geral (região hidrográfica de cada rio), não calculada a partir de dados.
- **Países e estados de cada rio:** máscaras raster dos polígonos do Natural Earth (limites aproximados).

## Como regenerar

1. Bases fora do repositório (docstring de `build/receitas/cerrado.py`); a ecorregião vem de uma consulta GeoJSON à Esri (`ECO_NAME='Cerrado'`, `maxAllowableOffset=0.02`).
2. `python3 -I build/mapas_dados.py <pasta> cerrado` (~6 s) → `data/mapas/cerrado.json`.
3. `python3 -I build/localizacao.py bioma cerrado` → `data/localizacao/cerrado.json`.
4. `python3 -I build/build.py` e `--publish`. O JSON do navegador sai em `assets/mapas/cerrado.json` (~145 KB, ~54 KB com gzip).

## Fontes e licenças

RESOLVE Ecoregions 2017 (CC BY 4.0; Dinerstein et al., 2017, BioScience); IBGE (Biomas 2025 e BC250 2025; termo de licença não localizado); Natural Earth 1:10m (domínio público).

## Lacunas e escolhas

- **Fora por escolha do projeto:** cidades, unidades de conservação (~580 no bioma), desmatamento, fogo e aquíferos.
- **Seleção de rios:** 23 dos principais, não toda a rede de drenagem; as nascentes não estão marcadas.
- **Franjas na Bolívia e no Paraguai:** só o limite (a ecorregião RESOLVE passa ~2° do limite do IBGE); as camadas detalhadas são do Brasil.
