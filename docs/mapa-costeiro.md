# Mapa do Costeiro-marinho: manguezais, recifes e ilhas

Branch `ajustes-site`. Título da seção: "Manguezais, recifes e ilhas do litoral brasileiro" (escolha do usuário em 2026-11-03: "mangues, recifes e ilhas").

## Camadas e fontes

| Camada | Fonte | Licença | Como entra |
|---|---|---|---|
| Limite do sistema (só contorno, para o azul continuar sendo só da água) | IBGE, Biomas 2019, via geobr (`data/biomes_2019_simplified.gpkg`, já no repo) | dado público do IBGE (termo de licença não localizado) | contorno verde |
| Manguezais | Global Mangrove Watch v3.0, extensão 2020 (Bunting et al., 2022; Zenodo 6894273) | CC BY 4.0 | só dentro do Brasil (máscara Natural Earth); manchas com menor lado < ~900 m descartadas (cerca de 9.789 km² somados, 9.001 km² desenhados) |
| Recifes | IBGE, BC250 2025, `hid_recife_a` | dado público do IBGE | 68 polígonos (coral, rochoso, tipo não informado); filtro por tipo |
| Ilhas | IBGE, BC250 2025, `hid_ilha_a`, campo `tipoilha` = Marítima | dado público do IBGE | 97 ilhas e arquipélagos com nome e ≥ 40 km² (peças do mesmo nome somadas) + as oceânicas de qualquer tamanho; filtro oceânicas/costeiras; lista em tabela |
| Países e estados | Natural Earth 1:10m | domínio público | estados do Brasil em cores diferentes |

## Como regenerar

```bash
# bases (fora do repo, em ~/biomas-raw): gmw/gmw_v3_2020_vec.zip (Zenodo, 177 MB, descompactar ao lado), bc250/hid_recife_a.* e hid_ilha_a.*
# (python3 -I build/httpzip.py <zip do BC250> x ~/biomas-raw/bc250 hid_recife_a.shp ... ), ne_10m_*
python3 -I build/mapas_dados.py ~/biomas-raw costeiro      # data/mapas/costeiro.json
python3 -I build/localizacao.py bioma costeiro             # data/localizacao/costeiro.json (mini-mapa do hero)
python3 -I build/build.py
```

## Lacunas e ressalvas (também escritas no mapa)

- O limite 2019 do IBGE não inclui Trindade, Martim Vaz e São Pedro e São Paulo: o mapa estende a moldura para mostrá-las, fora do contorno.
- O IBGE classifica como "marítimas" ilhas do estuário do Amazonas (Marajó e outras); aparecem como "costeiras".
- Manguezais: dado de satélite (GMW), não o Atlas dos Manguezais do ICMBio.
- Recifes: só o que a base do IBGE tem; recifes profundos, bancos e rodolitos ficam de fora.
- Sem unidades de conservação marinhas, batimetria, pesca nem óleo e gás.
- **Teste visual no navegador pendente.** Só conferi o desenho com `rsvg-convert`; o JS (camadas, filtros, legenda, rótulos de ilhas sem colisão) não rodou num navegador. As classes novas (`mt-mangue`, `mt-recife`, `mt-ilha`) estão em `src/mapa-tematico.css`.
