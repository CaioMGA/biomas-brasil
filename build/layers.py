"""Gera data/layers.json: divisas estaduais (IBGE), fronteiras, rios e cidades (Natural Earth) na grade do mapa.
Rode depois de extents.py: rios e cidades fora do Brasil só entram dentro da extensão dos biomas.

Fontes:
  - IBGE, malha de UFs 2022 (BR_UF_2022.shp/.dbf)
  - Natural Earth 1:10m: rivers_lake_centerlines, populated_places_simple e admin_0_boundary_lines_land
Uso: python3 -I layers.py data/map.json data/ids.png BR_UF_2022(sem extensao) rivers.geojson places.geojson borders.geojson data/layers.json
"""
import json, math, struct, sys
from PIL import Image

meta = json.load(open(sys.argv[1]))
ids = Image.open(sys.argv[2]); IW, IH = ids.size; idp = ids.load()
shp_base, rivers_f, places_f, borders_f, out = sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7]
K, S, minx, miny = meta["K"], meta["S"], meta["minx"], meta["miny"]
DS = 2.0  # a imagem de ids tem 1 pixel = DS unidades do mapa

def proj(lon, lat):
    return (lon * K - minx) * S, (-lat - miny) * S

def inside(x, y):
    i, j = int(x / DS), int(y / DS)
    return 0 <= i < IW and 0 <= j < IH and idp[i, j] > 0

def dp(pts, eps):
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop()
        ax, ay = pts[a]; bx, by = pts[b]
        dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy) or 1e-12
        md, mi = 0, -1
        for i in range(a + 1, b):
            d = abs(dy * (pts[i][0] - ax) - dx * (pts[i][1] - ay)) / L
            if d > md: md, mi = d, i
        if md > eps: keep[mi] = True; st += [(a, mi), (mi, b)]
    return [p for p, k in zip(pts, keep) if k]

def dp_ring(pts, eps):
    far = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
    return dp(pts[:far + 1], eps)[:-1] + dp(pts[far:], eps)

from collections import Counter
def owner_at(x, y, r=2):
    """0 = Brasil (sempre visível); n = extensão do bioma n fora do Brasil (visível com o bioma selecionado); None = fora de tudo."""
    i, j = int(x / DS), int(y / DS)
    vals = [idp[a, b] for a in range(i - r, i + r + 1) for b in range(j - r, j + r + 1) if 0 <= a < IW and 0 <= b < IH]
    if any(1 <= v <= 7 for v in vals): return 0
    f = [v - 10 for v in vals if v > 10]
    return Counter(f).most_common(1)[0][0] if f else None

def by_owner(run):
    """Divide uma linha em trechos de mesmo dono."""
    out, cur, co = [], [], None
    for p in run:
        o = owner_at(*p)
        if o is None or o != co:
            if len(cur) >= 2 and co is not None: out.append((co, cur))
            cur = [p] if o is not None else []; co = o
        else: cur.append(p)
    if len(cur) >= 2 and co is not None: out.append((co, cur))
    return out

def flat(pts): return [round(v) for p in pts for v in p]

# --- Shapefile (tipo Polygon) e DBF, sem dependências ---
def read_shp(path):
    b = open(path + ".shp", "rb").read(); o = 100; shapes = []
    while o < len(b):
        clen = struct.unpack(">i", b[o + 4:o + 8])[0] * 2; o += 8
        st = struct.unpack("<i", b[o:o + 4])[0]
        if st == 5:
            np_, npt = struct.unpack("<ii", b[o + 36:o + 44])
            parts = list(struct.unpack("<%di" % np_, b[o + 44:o + 44 + 4 * np_])) + [npt]
            pp = o + 44 + 4 * np_
            pts = struct.unpack("<%dd" % (2 * npt), b[pp:pp + 16 * npt])
            pts = [(pts[2 * i], pts[2 * i + 1]) for i in range(npt)]
            shapes.append([pts[parts[i]:parts[i + 1]] for i in range(np_)])
        else:
            shapes.append([])
        o += clen
    return shapes

def read_dbf(path):
    b = open(path + ".dbf", "rb").read()
    n, hl, rl = struct.unpack("<IHH", b[4:12])
    fields, o = [], 32
    while b[o] != 0x0D:
        fields.append((b[o:o + 11].split(b"\0")[0].decode(), b[o + 16])); o += 32
    rows = []
    for i in range(n):
        r = b[hl + i * rl + 1: hl + (i + 1) * rl]; d = {}; p = 0
        for name, ln in fields: d[name] = r[p:p + ln].decode("latin-1").strip(); p += ln
        rows.append(d)
    return rows

res = {"states": [], "borders": [], "rivers": [], "capitals": [], "cities": []}
for rec, rings in zip(read_dbf(shp_base), read_shp(shp_base)):
    out_rings = []
    for ring in rings:
        pts = dp_ring([proj(x, y) for x, y in ring], 1.1)
        if len(pts) >= 4: out_rings.append(flat(pts))
    res["states"].append({"uf": rec["SIGLA_UF"], "name": rec["NM_UF"], "rings": out_rings})
print("estados", len(res["states"]))

FW, FH = meta["w"], meta["h"]
for f in json.load(open(borders_f))["features"]:
    g = f["geometry"]; lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    for ln in lines:
        run = []
        for c in [proj(c[0], c[1]) for c in ln] + [None]:
            if c is not None and -50 <= c[0] <= FW + 50 and -50 <= c[1] <= FH + 50: run.append(c); continue
            if len(run) >= 2:
                for o, seg in by_owner(dp(run, .9)):
                    if len(seg) >= 2: res["borders"].append({"o": o, "p": flat(seg)})
            run = []
print("fronteiras", len(res["borders"]))

RIVER_FIX = {"Uruguay": "Rio Uruguai", "Paraiba": "Rio Paraíba", "Corumba": "Rio Corumbá", "Braco Menor": "Braço Menor", "Bois": "Rio dos Bois"}
def river_label(n):
    n = " ".join(n.split())
    if n in RIVER_FIX: return RIVER_FIX[n]
    return n if n.startswith("Rio ") else "Rio " + n

def along(run):
    """Ponto médio (por comprimento) do trecho e um ponto adiante, para orientar o rótulo."""
    d = [0.0]
    for p0, p1 in zip(run, run[1:]): d.append(d[-1] + math.hypot(p1[0] - p0[0], p1[1] - p0[1]))
    h = d[-1] / 2
    i = next(k for k in range(1, len(d)) if d[k] >= h)
    t = (h - d[i - 1]) / ((d[i] - d[i - 1]) or 1)
    x = run[i - 1][0] + (run[i][0] - run[i - 1][0]) * t; y = run[i - 1][1] + (run[i][1] - run[i - 1][1]) * t
    q0, q1 = run[max(0, i - 3)], run[min(len(run) - 1, i + 3)]
    dx, dy = q1[0] - q0[0], q1[1] - q0[1]; n = math.hypot(dx, dy) or 1
    return d[-1], (x, y, x + dx / n * 30, y + dy / n * 30)

best, rank, skipped = {}, {}, 0
for f in json.load(open(rivers_f))["features"]:
    name = (f["properties"]["name"] or "").strip()
    g = f["geometry"]; lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    pts_runs = []
    for ln in lines:
        run = []
        for p in [proj(c[0], c[1]) for c in ln] + [None]:
            if p is not None and inside(*p): run.append(p); continue
            if len(run) >= 2: pts_runs.append(dp(run, .9))
            run = []
    if not name:
        skipped += len(pts_runs); continue          # todo rio exibido tem nome
    label = river_label(name); r = f["properties"]["scalerank"]
    rank[label] = min(rank.get(label, 99), r)
    for run in pts_runs:
        for o, seg in by_owner(run):
            res["rivers"].append({"n": label, "r": r, "o": o, "p": flat(seg)})
        L, pos = along(run)
        if label not in best or L > best[label][0]: best[label] = (L, pos)
res["rl"] = [{"n": n, "x": round(v[1][0]), "y": round(v[1][1]), "x2": round(v[1][2]), "y2": round(v[1][3]), "r": rank[n]} for n, v in best.items()]
print("rios sem nome descartados:", skipped, "| rótulos:", len(res["rl"]))
print("rios", len(res["rivers"]))

CAPS = {"Rio Branco", "Maceió", "Macapá", "Manaus", "Salvador", "Fortaleza", "Brasília", "Vitória", "Goiânia", "São Luís", "Cuiabá",
        "Campo Grande", "Belo Horizonte", "Belém", "João Pessoa", "Curitiba", "Recife", "Teresina", "Rio de Janeiro", "Natal",
        "Porto Alegre", "Porto Velho", "Boa Vista", "Florianópolis", "São Paulo", "Aracaju", "Palmas"}
CAP_UF = {"Rio Branco": "AC", "Maceió": "AL", "Macapá": "AP", "Manaus": "AM", "Salvador": "BA", "Fortaleza": "CE", "Brasília": "DF", "Vitória": "ES",
          "Goiânia": "GO", "São Luís": "MA", "Cuiabá": "MT", "Campo Grande": "MS", "Belo Horizonte": "MG", "Belém": "PA", "João Pessoa": "PB",
          "Curitiba": "PR", "Recife": "PE", "Teresina": "PI", "Rio de Janeiro": "RJ", "Natal": "RN", "Porto Alegre": "RS", "Porto Velho": "RO",
          "Boa Vista": "RR", "Florianópolis": "SC", "São Paulo": "SP", "Aracaju": "SE", "Palmas": "TO"}
seen = set()
for f in json.load(open(places_f))["features"]:
    p = f["properties"]
    if p["name"] in seen: continue
    x, y = proj(p["longitude"], p["latitude"])
    if p["adm0_a3"] != "BRA":
        # fora do Brasil: só dentro da extensão de algum bioma (id 11 a 16)
        i, j = int(x / DS), int(y / DS)
        if 0 <= i < IW and 0 <= j < IH and idp[i, j] > 10:
            if p["featurecla"] == "Admin-0 capital":
                seen.add(p["name"]); res["capitals"].append({"n": p["name"], "uf": p["adm0name"], "x": round(x), "y": round(y), "f": 1})
            elif p["pop_max"] >= 250000:
                seen.add(p["name"]); res["cities"].append({"n": p["name"], "x": round(x), "y": round(y), "f": 1})
        continue
    if p["name"] in CAPS and p["featurecla"] not in ("Admin-1 capital", "Admin-0 capital"): continue   # homônimo que não é capital (ex.: Natal, AM)
    if p["name"] in CAPS:
        seen.add(p["name"]); res["capitals"].append({"n": p["name"], "uf": p["adm1name"], "sg": CAP_UF[p["name"]], "x": round(x), "y": round(y)})
    elif p["pop_max"] >= 450000 and p["name"] != "Jaboatao":
        seen.add(p["name"]); res["cities"].append({"n": p["name"], "x": round(x), "y": round(y)})
print("capitais", len(res["capitals"]), "(inclui", sum(1 for c in res["capitals"] if c.get("f")), "fora do Brasil) cidades", len(res["cities"]))
assert sum(1 for c in res["capitals"] if not c.get("f")) == 27, "faltam capitais"
import os
d0 = os.path.dirname(out)
res["outlines"] = [pc for f in ("outlines.json", "foreign.json") if os.path.exists(os.path.join(d0, f)) for pc in json.load(open(os.path.join(d0, f)))]
print("contornos", len(res["outlines"]))
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
import os; print("layers.json", os.path.getsize(out) // 1024, "KB")
