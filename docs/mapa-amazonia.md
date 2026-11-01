# Mapa temático da Amazônia: o Rio Amazonas e seus afluentes

Branch `mapa-amazonia` (sobre `mapa-tematico-base`). O HERO MAP da home não é tocado. **Decisão do projeto:** a Amazônia é grande demais para camadas de unidades de conservação, Terras Indígenas ou desmatamento; este mapa é **só sobre o Rio Amazonas e seus afluentes**, sem cidades.

## O que o mapa mostra

- **O Rio Amazonas (canal principal), sempre visível:** é uma camada fixa, sem caixa de seleção nem filtro: Marañón e Ucayali (que formam o Amazonas no Peru) → Amazonas do Peru → Solimões → Amazonas → Canal do Norte (a principal saída para o Atlântico, ao longo de Macapá).
- **Afluentes (31 rios):** diretos e principais subafluentes (Branco, Acre, Guaporé, Mamoré, Beni, Madre de Dios, Iriri, Juruena, Teles Pires…). O Tocantins e o Araguaia ficam de fora: desaguam no estuário do Pará, não no Amazonas. Podem ser desligados na caixa "Afluentes".
- **Filtros (só dos afluentes):** **Afluentes** (todos / brasileiros / estrangeiros) e **margem** (esquerda = norte, direita = sul). "Brasileiro" = trecho dentro do Brasil (drenagem do IBGE); "estrangeiro" = trecho fora do Brasil (Natural Earth). Um rio que cruza a fronteira aparece nos dois, cada um com o seu trecho (Içá / Putumayo, Japurá / Caquetá, Guaporé / Guaporé-Itenez, Mamoré / Mamoré-Bolívia). Tocar num rio mostra por quais países e estados ele passa. Não há filtros de país nem de estado (foram retirados a pedido).
- **Contexto:** bioma de uma cor só (24 ecorregiões RESOLVE) com o limite oficial do IBGE por cima no Brasil, oceano azul, países com cores e nomes, fronteiras, estados do Brasil em cores diferentes, grade (desligada), escala e norte.

## Como foi feito

- **Brasil:** drenagem do IBGE (BC250) pelos **nomes** dos rios (`shp.read_por_nome`, que usa o índice `.shx` e lê só os trechos pedidos: o arquivo tem 2,5 milhões de trechos). Há **homônimos** (Rio Negro, Rio Branco, Rio Madeira… existem em outras bacias), então cada rio só vale dentro de uma caixa de coordenadas que cobre o curso real (`BR_RIOS` na receita).
- **Fora do Brasil:** Natural Earth (Marañón, Ucayali, Amazonas do Peru, Napo, Putumayo/Içá, Caquetá/Japurá, Madre de Dios, Beni, Mamoré, Guaporé). As linhas do Natural Earth que cruzam a fronteira são cortadas, e só o pedaço de fora do Brasil é usado (o do Brasil vem do IBGE).
- **Margem:** calculada pela posição da foz do afluente em relação ao canal (a direção do canal é suavizada, porque o canal tem braços e ilhas). Conferi o resultado contra a geografia conhecida: 0 divergências em 31 afluentes.
- **Países e estados de cada rio:** máscaras raster dos polígonos do Natural Earth; só conta o país ou estado com pelo menos 4% dos pontos do rio (ignora toques de ponta). Os limites do Natural Earth são aproximados, então um rio que corre na fronteira pode aparecer nos dois lados.

## Como regenerar

1. Bases fora do repositório, nas subpastas do docstring de `build/receitas/amazonia.py` (as 24 ecorregiões saem de uma consulta GeoJSON ao serviço público da Esri: `ECO_ID IN (446,463,464,465,466,467,469,473,474,476,480,482,483,484,496,497,498,503,505,507,508,511,512,518)`, `maxAllowableOffset=0.02`). A drenagem do IBGE exige `hid_trecho_drenagem_l.{shp,shx,dbf,cpg}` (o `.shx` é extraído do zip pela mesma leitura por HTTP Range, `build/httpzip.py`).
2. `python3 -I build/mapas_dados.py <pasta> amazonia` (~15 s) → `data/mapas/amazonia.json`.
3. `python3 -I build/localizacao.py bioma amazonia` → `data/localizacao/amazonia.json`.
4. `python3 -I build/build.py` e `--publish`. O JSON do navegador sai em `assets/mapas/amazonia.json` (~265 KB, ~93 KB com gzip).

## Fontes e licenças

RESOLVE Ecoregions 2017 (CC BY 4.0; Dinerstein et al., 2017, BioScience); IBGE (Biomas 2025 e BC250 2025; termo de licença não localizado); Natural Earth 1:10m (domínio público).

## Lacunas e escolhas

- **Cidades, UCs, Terras Indígenas e desmatamento:** fora por escolha do projeto. O portal TerraBrasilis (INPE) tem as Terras Indígenas e o PRODES (CC BY-SA 4.0 no rodapé do portal; a licença específica de cada camada não foi confirmada), mas o PRODES tem ~800 mil polígonos e as Terras Indígenas, 23 MB.
- **Limite oficial fora do Brasil:** o limite da RAISG (que cobre os 9 países) tem licença própria (uso não lucrativo, dados "sem alteração") e não permite redistribuir recortes simplificados. Usei a união das ecorregiões RESOLVE, uma aproximação; os dois limites (RESOLVE e IBGE) não coincidem exatamente.
- **Terras Indígenas da FUNAI:** o servidor oficial continua com a cadeia de certificados inválida; a verificação TLS não foi contornada.
- **Natural Earth:** os nomes "Natal" e "Vila Velha" têm a população de cidades de outro estado, em posições erradas; irrelevante agora (sem cidades), mas fica o aviso.
- **Foz:** o Canal do Norte é a saída principal; o estuário com suas ilhas e os canais ao sul de Marajó (Rio Pará) não estão desenhados.
