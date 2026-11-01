# Mapa temático do Pantanal: dados, decisões e lacunas

Branch `mapa-pantanal` (sobre `mapa-tematico-base`). O HERO MAP da home não é tocado: o mapa temático é plano (2D), em SVG, com camadas e filtros, só nas páginas de bioma.

## Como regenerar

1. Baixe e descompacte as bases em uma pasta (fora do repositório), com as subpastas `biomas/`, `cnuc/`, `locais/` e `bc250/` (ver o docstring de `build/receitas/pantanal.py`). O zip da BC250 tem ~800 MB; `build/httpzip.py` extrai só os arquivos `hid_*` lendo o zip por HTTP Range.
2. `python3 -I build/mapas_dados.py <pasta> pantanal` gera `data/mapas/pantanal.json` (~650 KB).
3. `python3 -I build/build.py` e `python3 -I build/build.py --publish` geram as páginas; o JSON do navegador sai em `assets/mapas/pantanal.json` (~200 KB, ~70 KB com gzip), carregado só quando a seção chega perto da tela.

## Fontes (todas oficiais; termo de licença do IBGE não localizado, CNUC é CC-BY)

- IBGE, Biomas 1:250 000 (2025): limite do Pantanal.
- IBGE, BC250 versão 2025: trechos de drenagem (rios e córregos nomeados com mais de 60 km no bioma) e massas d'água (lagoas, baías, meandros, rios largos; sem nome só acima de ~0,5 km²).
- MMA, CNUC edição 2025-08: unidades de conservação (federais, estaduais, municipais, RPPNs), filtradas espacialmente (a coluna `pantanal` do CNUC está vazia para várias UCs do bioma, por isso não foi usada).
- IBGE, Localidades 2022: sedes municipais e localidades indígenas e quilombolas (pontos).

## Lacunas (por validar)

- **Terras Indígenas (FUNAI):** os links oficiais (`geoserver.funai.gov.br`, camada `tis_poligonais`) falham aqui por cadeia de certificados incompleta no servidor; a verificação TLS não foi contornada. Baixar o shapefile manualmente e acrescentar à receita.
- **Planície alagável e cheia × seca:** a camada `hid_terreno_sujeito_inundacao_a` da BC250 tem 232 feições, todas no Nordeste, nenhuma no Pantanal; e 4.363 das 4.373 massas d'água do bioma estão como "Permanente". Opção mapeada: MapBiomas Água (mensal, 30 m), via Google Earth Engine (exige conta; licença e ano ou média a decidir).
- **Natural Earth descartado:** nomeia o Rio Paraguai como "Paraná" nesta região.
- **Hidrografia ANA (BHO/ottobacias):** não houve URL de download direto verificada.
- **Sítios Ramsar e UNESCO:** não incluídos (Ramsar do MMA é de 2022; UNESCO sem polígono oficial fácil).

## Pendências de validação

O JS/CSS do mapa só foi validado por sintaxe e pela geometria renderizada em PNG. Falta o teste no Chrome (desktop e celular): console, camadas, filtros, painel de detalhes, tabelas, colisão de rótulos. Screenshots em `~/biomas-capturas/`.
