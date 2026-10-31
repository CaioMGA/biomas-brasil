# Correção: nomes de rios e capitais

Revisão dos rótulos de rios e capitais em `data/layers.json`, que é gerado por `build/layers.py` a partir do Natural Earth 1:10m.
Todas as correções são em `build/layers.py`; o template não precisa mudar.
Depois de editar, gere o `layers.json` de novo e rode o build (comandos no fim).

## Resumo

- **Capitais:** as 27 estão certas, com nome e acentos corretos. Cada ponto cai dentro do próprio estado no teste ponto-no-polígono com a malha IBGE 2022, e o erro de posição fica entre 1 e 8 km. Só falta traduzir a capital estrangeira "Montevideo" para "Montevidéu".
- **Rios:** há 3 erros visíveis já na vista inicial, mais 2 problemas de posição de rótulo e 7 nomes a ajustar.

## Problemas encontrados

### Visíveis na vista inicial (rank ≤ 4, dentro do Brasil)

1. **"Rio Paraná" está no rio errado.** No Natural Earth, a feição `Paraná` com `scalerank == 2` junta três rios numa linha só:
   - **Rio Cuiabá**: da nascente (−55,08; −14,32), passando pela cidade de Cuiabá, até o encontro com o Paraguai em **(−57,47; −17,94)**;
   - **Rio Paraguai**: de (−57,47; −17,94) até a foz no Paraná, perto de (−58,6; −27,3);
   - **Rio Paraná**: daí para o sul, já na Argentina.

   O rótulo atual fica em (−56,6; −17,2), que é o Rio Cuiabá no Pantanal. Com isso, o Paraguai fica sem nome, e o Paraná brasileiro (as feições `Paraná` com `scalerank == 4`, na divisa SP/MS e no PR) também fica sem rótulo.
   Observação: o alto Paraguai (de Cáceres até −17,94) não existe no Natural Earth 10m. A feição sem nome que chega a esse ponto vem das lagoas da fronteira com a Bolívia; não use essa feição como Paraguai.
2. **"Rio Indaiá" é o alto São Francisco.** A feição `Indaiá` (rank 4) vai de (−46,50; −20,32), na Serra da Canastra, até (−45,09; −19,05), exatamente onde começa a feição `São  Francisco`. É um erro de nome no Natural Earth.
3. **"Braço Menor"** aparece sem "Rio" e sem contexto. É o **Rio Javaés**, o braço leste do Araguaia em volta da Ilha do Bananal.

### Posição do rótulo

4. **"Rio Amazonas"** está a −63,8 de longitude, a oeste de Manaus. No Brasil, o trecho entre Tabatinga (−69,95) e o Encontro das Águas (−59,9) se chama **Rio Solimões**.
5. **"Rio Grande" (MG/SP) fica sem nome.** O script cria um rótulo por nome e o coloca no trecho mais longo, que aqui é o Río Grande da Bolívia (rank 3). Esse ponto cai em terra neutra (id 8 em `ids.png`), onde o template nunca mostra rótulo. O Rio Grande da divisa MG/SP (rank 5) não ganha rótulo. O mesmo acontece com outros nomes repetidos (Negro, Verde, Pardo…).

### Nomes a ajustar

| Natural Earth (`name`) | Aparece hoje | Correto |
|---|---|---|
| `Purús` | Rio Purús | Rio Purus |
| `Velhas` | Rio Velhas | Rio das Velhas |
| `Contas` | Rio Contas | Rio de Contas |
| `Jiparaná` | Rio Jiparaná | Rio Ji-Paraná |
| `Paraiba` | Rio Paraíba | Rio Paraíba do Sul (o traçado é o do RJ/SP) |
| `Ribeira` | Rio Ribeira | Rio Ribeira de Iguape |
| `Corantijn` e `Courantyne` | dois rótulos | o mesmo rio: use "Rio Corantijn" nos dois |
| `Indaiá` | Rio Indaiá | Rio São Francisco (item 2) |
| `Braco Menor` | Braço Menor | Rio Javaés (item 3) |

Capital estrangeira: `Montevideo` → **Montevidéu**.

## Patch proposto para `build/layers.py`

> Este patch não foi executado. Rode e confira com a checagem do fim do arquivo.

### 1. Nomes e trechos (substitui `RIVER_FIX` e `river_label`)

```python
RIVER_FIX = {"Uruguay": "Rio Uruguai", "Paraiba": "Rio Paraíba do Sul", "Corumba": "Rio Corumbá", "Braco Menor": "Rio Javaés",
             "Bois": "Rio dos Bois", "Indaiá": "Rio São Francisco", "Purús": "Rio Purus", "Velhas": "Rio das Velhas",
             "Contas": "Rio de Contas", "Jiparaná": "Rio Ji-Paraná", "Ribeira": "Rio Ribeira de Iguape",
             "Courantyne": "Rio Corantijn"}
def river_label(n, r=None, lon=None, lat=None):
    n = " ".join(n.split())
    if n == "Paraná" and r == 2 and lat > -27.3:          # o traçado junta Cuiabá + Paraguai + Paraná
        return "Rio Cuiabá" if lat > -17.94 else "Rio Paraguai"
    if n == "Amazonas" and -69.95 < lon < -59.9:          # trecho brasileiro a montante do Encontro das Águas
        return "Rio Solimões"
    if n in RIVER_FIX: return RIVER_FIX[n]
    return n if n.startswith("Rio ") else "Rio " + n

def pieces(name, r, ln):
    """Divide a linha onde o nome muda, repetindo o ponto de junção nos dois trechos."""
    out, cur, cl = [], [], None
    for c in ln:
        lab = river_label(name, r, c[0], c[1])
        if cl is not None and lab != cl:
            out.append((cl, cur + [c])); cur = []
        cur.append(c); cl = lab
    if len(cur) >= 2: out.append((cl, cur))
    return out
```

### 2. Laço dos rios (substitui o bloco de `best, rank, skipped = ...` até o `print("rios", ...)`)

O rótulo vai para o trecho brasileiro mais longo. Só fica fora do Brasil se o rio não passa pelo país. O rank do rótulo passa a ser o do trecho escolhido, não o menor rank entre rios homônimos.

```python
best, skipped = {}, 0
def add(label, r, run):
    for o, seg in by_owner(run):
        res["rivers"].append({"n": label, "r": r, "o": o, "p": flat(seg)})
        L, pos = along(seg)
        key = (o == 0, L)
        if label not in best or key > best[label][0]: best[label] = (key, pos, r)

for f in json.load(open(rivers_f))["features"]:
    name = (f["properties"]["name"] or "").strip(); r = f["properties"]["scalerank"]
    g = f["geometry"]; lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    for ln in lines:
        for label, piece in (pieces(name, r, ln) if name else [(None, ln)]):
            run = []
            for p in [proj(c[0], c[1]) for c in piece] + [None]:
                if p is not None and inside(*p): run.append(p); continue
                if len(run) >= 2:
                    if label is None: skipped += 1          # todo rio exibido tem nome
                    else: add(label, r, dp(run, .9))
                run = []
res["rl"] = [{"n": n, "x": round(v[1][0]), "y": round(v[1][1]), "x2": round(v[1][2]), "y2": round(v[1][3]), "r": v[2]} for n, v in best.items()]
print("rios sem nome descartados:", skipped, "| rótulos:", len(res["rl"]))
print("rios", len(res["rivers"]))
```

Atenção: algumas feições do arquivo têm `geometry` nula (já vi uma). Se o laço quebrar com `TypeError`, pule essas feições com `if not g: continue`.

### 3. Capital estrangeira

No laço das cidades, no ramo `featurecla == "Admin-0 capital"` fora do Brasil, troque `"n": p["name"]` por:

```python
"n": {"Montevideo": "Montevidéu"}.get(p["name"], p["name"])
```

## Gerar de novo e conferir

As entradas do Natural Earth e do IBGE estão em `~/.claude/jobs/9bb470c5/tmp/` (`dl_ne/` e `dl_uf/`):

```sh
cd ~/projs/biomas-brasil
D=~/.claude/jobs/9bb470c5/tmp
python3 -I build/layers.py data/map.json data/ids.png $D/dl_uf/BR_UF_2022 \
  $D/dl_ne/rivers.geojson $D/dl_ne/places.geojson $D/dl_ne/borders.geojson data/layers.json
python3 build/build.py
```

O que conferir depois:

- `rl` tem "Rio Cuiabá", "Rio Paraguai" e "Rio Solimões". O rótulo "Rio Paraná" fica no Brasil (por volta de −51 a −54 de longitude), e "Rio Grande" fica entre MG e SP.
- `rl` não tem mais "Rio Indaiá", "Braço Menor", "Rio Purús" nem "Rio Courantyne".
- O `assert` das 27 capitais continua passando.
- Nenhum `id` `rio:...` em `data/labels.json` ficou órfão. Hoje não há nenhum, só `bio:`, `cont:` e `geo:`.
- No navegador, na vista inicial: "Rio Paraguai" aparece no Pantanal, e o "Rio Amazonas" fica a leste de Manaus.

## Correções adicionais (Mamoré e foz do Amazonas)

- **Rio Mamoré:** no Natural Earth, o trecho de baixo (da foz do Guaporé, −65,02°/−11,89°, até o início do Madeira, −65,40°/−10,39°) vem com o nome `Guaporé` e `scalerank == 3`. Isso deixava o Mamoré truncado em −12° (com o nome num toco de 2 pontos) e um Guaporé falso na fronteira. `river_label` agora renomeia `Guaporé` com rank 3 para "Rio Mamoré".
- **Foz do Amazonas:** a feição `Amazonas` do Natural Earth 10m termina em −52,71°/−1,58°, a ~170 km do mar. O trecho final foi traçado à mão (`EXTRA_RIVERS` em `build/layers.py`, canal norte por Gurupá e Macapá até −49,8°/0,3°); é uma aproximação, não dado oficial.
- **Refazer só os rios:** `python3 -I build/layers.py data/map.json data/ids.png - rivers.geojson - - data/layers.json --rivers-only` (reaproveita o `layers.json` atual; `rivers.geojson` é o `ne_10m_rivers_lake_centerlines` do Natural Earth).

## Países vizinhos e capitais estrangeiras

- **Contornos e nomes dos vizinhos:** `layers.json` ganhou `countries` (contorno de Uruguai, Argentina, Paraguai, Bolívia, Peru, Colômbia, Venezuela, Guiana, Suriname e Guiana Francesa, dentro do quadro do mapa) e `cl` (um nome por país). Aparecem com a camada "Divisas e fronteiras"; os nomes são editáveis no lab de textos (ids `pais:Argentina`…). Fonte: Natural Earth `ne_10m_admin_0_countries`.
- **Capitais estrangeiras:** omitidas (`layers.py` não gera mais as capitais com `f: 1`).
- **Refazer:** `python3 -I build/layers.py data/map.json data/ids.png - rivers.geojson - - data/layers.json --rivers-only --countries=countries.geojson`.
