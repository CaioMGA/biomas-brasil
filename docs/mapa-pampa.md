# Mapa temático do Pampa: dados, decisões e lacunas

Branch `mapa-pampa` (sobre `mapa-tematico-base`). O HERO MAP da home não é tocado. O mapa segue o padrão dos outros biomas (plano, SVG, camadas e filtros num painel recolhível que começa fechado, bioma de uma cor só), com o tema que o Pampa pede: **as águas (lagoas, banhados, rios largos), os principais rios por bacia e as unidades de conservação**. Sem cidades (decisão do usuário).

## O que o mapa mostra

- **Limite do bioma:** a ecorregião RESOLVE 2017 "Uruguayan savanna" (CC BY 4.0), que segue pelo Uruguai (por amostragem, ~47% da área da ecorregião está no Brasil, ~53% no Uruguai e 0% na Argentina), com o limite oficial do IBGE (2025) por cima, na parte brasileira.
- **Contexto:** oceano azul, países com cores e nomes, fronteiras, estados do Brasil em cores diferentes (vizinhos nunca repetem cor), divisas de estados e departamentos, grade (desligada), escala e norte. Do Paraguai só a cor do país (sem departamentos), e quatro províncias argentinas que aparecem só como fatias nos cantos ficam sem divisas próprias (Formosa, Chaco, Santa Fe, Ciudad de Buenos Aires).
- **Lagoas, banhados, represas e rios largos (só Brasil):** massas d'água do BC250 com nome e mais de ~2,5 km² (sem nome, só as bem maiores). São 112 polígonos: 48 lagoas (Patos, Mirim, Mangueira, Peixe, Itapeva…), 2 banhados, 30 represas e 32 rios largos (Uruguai, Jacuí, Guaíba…). Filtro: tipo de corpo d'água.
- **Rios (só Brasil):** os 16 principais rios do Pampa gaúcho, da drenagem nomeada do BC250, agrupados em 4 bacias (Uruguai, Guaíba, Camaquã, Mirim–São Gonçalo). Toque num rio para ver por quais países e estados ele passa. Só os 7 maiores levam rótulo (o bioma é pequeno e os textos não podem se sobrepor). Filtro: bacia.
- **Unidades de conservação (só Brasil):** 48, as que o próprio CNUC marca com área no Pampa (campo `pampa` do cadastro, numérico; pelos valores, é a área da unidade dentro do bioma), todas no Rio Grande do Sul, 22 delas com menos de 100 ha (RPPNs, manchas minúsculas) (por exemplo APA do Ibirapuitã, Parque Nacional da Lagoa do Peixe, Estação Ecológica do Taim). Sem rótulo no mapa, só na lista; a área é a total da unidade (a parte fora do Pampa também conta). Filtros: proteção e esfera.
- **Não há:** cidades (por escolha do projeto) e camada de ecorregiões (ver abaixo).

## Por que não há camada de ecorregiões

Medido por amostragem de pontos (3.000, semente fixa) dentro do polígono do Pampa do IBGE, contra 10 ecorregiões RESOLVE da região (consulta por interseção com a caixa −58,−35,−48,−27): ~87% cai na "Uruguayan savanna" (574), ~5% nas florestas do Alto Paraná (439), ~1% nas restingas da costa atlântica (441), ~0,6% nas florestas de araucária (440) e da Serra do Mar (500), e ~6% em nenhuma; 167 dos 175 pontos desses 6% estão dentro do polígono da Lagoa dos Patos (BC250) e 8 em lugar nenhum identificado. Uma ecorregião dominante não justifica uma camada; por isso o limite é a "Uruguayan savanna" inteira com o oficial do IBGE por cima (que cobre as bordas com a Mata Atlântica), como no Cerrado. **Isso difere do plano combinado na conversa** ("ecorregiões, UCs e rios em camadas") e fica registrado aqui. A primeira versão do texto dizia que as outras ecorregiões "não tocam" o Pampa brasileiro: estava errado (o Alto Paraná toca ~5%) e foi corrigido depois de medir as 10.

## Como regenerar

1. Bases fora do repositório (aqui, em `~/biomas-raw/`, que não é apagada com o job): `biomas/`, `bc250/` (`hid_trecho_drenagem_l.*` e `hid_massa_dagua_a.*`), `cnuc/`, `ne_10m_admin_0_countries/`, `ne_10m_admin_0_boundary_lines_land/`, `ne_10m_admin_1_states_provinces/` e `resolve_pa/eco_574.json`. A ecorregião vem de consulta GeoJSON ao serviço público da Esri (`ECO_ID=574`, `maxAllowableOffset=0.003`, `geometryPrecision=3`):
   `https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/Resolve_Ecoregions/FeatureServer/0/query`
2. `python3 -I build/mapas_dados.py <pasta> pampa` (~4 s) → `data/mapas/pampa.json` (~275 KB).
3. `python3 -I build/localizacao.py bioma pampa` → `data/localizacao/pampa.json`.
4. `python3 -I build/build.py` e `--publish` (só escreve `dist/`; não envia nada). O JSON do navegador sai em `assets/mapas/pampa.json` (~99 KB).

## Fontes e licenças

RESOLVE Ecoregions 2017 (CC BY 4.0; citar Dinerstein et al., 2017, BioScience); IBGE Biomas 2025 e BC250 2025 (termo de licença não localizado, declarado no mapa); MMA CNUC 2025-08 (CC-BY); Natural Earth 1:10m (domínio público).

## Lacunas (por validar)

- **A bacia de cada rio vem do conhecimento geral** (bacias hidrográficas do Rio Grande do Sul), não de uma base de dados; a nota da camada diz isso. Falta conferir com o Atlas de Bacias do RS ou a base da ANA. Em particular: Santa Maria, Cacequi, Toropi, Icamaquã e Butuí foram atribuídos à bacia do Uruguai por serem afluentes do Ibicuí ou do Uruguai; Piratini e Jaguarão, à Mirim–São Gonçalo.
- **Caixas de coordenadas dos rios:** o nome sozinho não basta (há "Rio Ibicuí", "Rio Jacuí", "Rio Santa Maria" em outras regiões; achado na validação: um "Rio Ibicuí" em Santa Catarina, a ~51,1°O, 27,4°S, fora da caixa). As caixas foram conferidas contra as extensões da base, não contra a literatura.
- **A camada de água e os rios são recortados pela moldura, não pelo bioma:** represas do Planalto (Passo Real, Passo Fundo, Itaúba) e o curso alto dos rios (Jacuí, Uruguai, Ibicuí) aparecem fora do Pampa, na parte da moldura ocupada por outros biomas.
- **Seleção de rios:** são 16, não toda a rede (por exemplo Taquari, Caí, Sinos e Pardo, que correm na borda com a Mata Atlântica, ficaram de fora).
- **Lagoa Mirim e Rio Uruguai:** o BC250 cobre só o Brasil; o lado uruguaio e argentino não aparece como polígono.
- **Nomes do BC250:** copiados como estão (há grafias duvidosas, como "Canal de São Gonsalo"); só o nome dos rios mostrados no mapa foi tratado.
- **Banhados e zonas úmidas (Taim, Banhado Grande), campo nativo remanescente e conversão para lavoura e silvicultura:** não incluídos; não há camada com licença aberta confirmada para este mapa (o MapBiomas só sai pelo Google Earth Engine).
- **UCs no Uruguai e na Argentina:** a base mundial (WDPA) não permite redistribuição.
- **Terras Indígenas e territórios quilombolas:** não incluídos (limites da FUNAI indisponíveis, TLS quebrado).

## Pendências de validação

**O visual no navegador não foi verificado:** o Chrome bloqueia `file://` e o servidor em segundo plano é vetado. Foi conferido o que dá sem navegador: os dados (contagens, nomes, países e estados por rio, bbox), que as páginas geram, e um PNG feito com PIL direto da geometria de `data/mapas/pampa.json` (enquadramento, limites, lagoas, rios e UCs). Não foram verificados o JS, o CSS, a colisão de rótulos nem os filtros. Falta o teste no Chrome (`! python3 -m http.server 8765` dentro do worktree, abrir `/biomas/pampa/`): painel recolhível, camadas e filtros, a legenda dinâmica, colisão dos rótulos (26 divisas de estados e departamentos e 7 rótulos de rios), nomes de país dentro do território, moldura sem faixas azuis laterais e o carrossel de espécies. Olhar primeiro: (1) o rótulo do Paraguai (lat −26,894) fica a ~0,06° do topo da moldura (−26,836), uma fatia na borda, e a regra "nome de país cabe no território" pode falhar ali; (2) a moldura segue a ecorregião inteira, com o Uruguai ocupando todo o canto inferior esquerdo, e o Brasil só o lado direito; (3) a Argentina aparece só como terra de contexto, sem área do bioma.
