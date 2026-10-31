"""Estende o mapa de ids com a parte dos biomas que fica fora do Brasil.

Cada ecorregião do WWF (RESOLVE Ecoregions 2017) é associada ao bioma brasileiro com que mais se sobrepõe,
se essa sobreposição for pelo menos LIMIAR da área da ecorregião (ou se ela estiver na lista MANUAL).
A parte fora do Brasil dessas ecorregiões recebe o id 10 + n (n = bioma 1..6) em data/ids.png.
Também gera data/focus.json: centro e zoom da câmera para cada bioma (Brasil + extensão) e para o Brasil.

Uso: python3 -I extents.py data/map.json data/ids.png ecoregions.geojson data/focus.json [countries.geojson] [--dry]
"""
import json, sys
from PIL import Image, ImageChops, ImageDraw

LIMIAR = 0.20
# Ajustes manuais. Amazônia (n=1): bacia amazônica e Escudo das Guianas fora do Brasil, que o critério de área não captura.
MANUAL = {"Napo moist forests": 1, "Ucayali moist forests": 1, "Caqueta moist forests": 1, "Beni savanna": 1,
          "Guianan Highlands moist forests": 1, "Guianan lowland moist forests": 1, "Pantepui forests & shrublands": 1}
# Transição ou costeiras que o critério associaria ao bioma errado.
EXCLUDE = {"Chiquitano dry forests", "Amazon-Orinoco-Southern Caribbean mangroves"}
meta = json.load(open(sys.argv[1]))
ids_path, eco_path, focus_path = sys.argv[2], sys.argv[3], sys.argv[4]
countries_path = sys.argv[5] if len(sys.argv) > 5 and not sys.argv[5].startswith("--") else None
dry = "--dry" in sys.argv
K, S, minx, miny = meta["K"], meta["S"], meta["minx"], meta["miny"]
DS = 2.0
NAMES = {1: "amazonia", 2: "cerrado", 3: "mata-atlantica", 4: "caatinga", 5: "pampa", 6: "pantanal", 7: "costeiro"}

im = Image.open(ids_path); W, H = im.size
base = Image.frombytes("L", im.size, im.tobytes())
binary = {n: base.point([255 if i == n else 0 for i in range(256)]) for n in range(1, 8)}

def px(lon, lat): return ((lon * K - minx) * S / DS, (-lat - miny) * S / DS)

def mask_of(geom):
    m = Image.new("L", im.size, 0); d = ImageDraw.Draw(m)
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        d.polygon([px(*c[:2]) for c in poly[0]], fill=255)   # só o anel externo
    return m

def count(m): return m.histogram()[255]

feats = json.load(open(eco_path))["features"]
assigned = {}   # nome -> (n, mask)
for f in feats:
    name = f["properties"]["ECO_NAME"]
    m = mask_of(f["geometry"]); area = count(m)
    if not area: continue
    ov = {n: count(ImageChops.darker(m, binary[n])) for n in range(1, 7)}
    n, o = max(ov.items(), key=lambda kv: kv[1])
    ratio = o / area
    pick = None if name in EXCLUDE else (MANUAL.get(name) or (n if ratio >= LIMIAR else None))
    if o or name in MANUAL: print(f"{name:42s} melhor={NAMES[n]:15s} {ratio:5.0%} da ecorregião {'-> ' + NAMES[pick] if pick else ''}")
    if pick: assigned[name] = (pick, m, f["geometry"])

print("\nassociadas:", {k: NAMES[v[0]] for k, v in assigned.items()})
if dry: sys.exit()

# Desenha a extensão fora do Brasil (só onde o id é 0)
ext = Image.new("L", im.size, 0)
for n, m, _ in assigned.values():
    ext.paste(10 + n, mask=m)
outside = base.point([255 if i == 0 else 0 for i in range(256)])
final = base.copy()
# Terra neutra (id 8): os outros países da América do Sul, para o Brasil não flutuar no vazio. A extensão dos biomas vai por cima.
if countries_path:
    land = Image.new("L", im.size, 0)
    for f in json.load(open(countries_path))["features"]:
        pr = f["properties"]; nm = pr.get("NAME") or pr.get("name"); ct = pr.get("CONTINENT") or pr.get("continent")
        if ct != "South America" or nm in ("Brazil", "Falkland Is."): continue
        land.paste(255, mask=mask_of(f["geometry"]))
    final.paste(8, mask=ImageChops.darker(outside, land))
final.paste(ext, mask=ImageChops.darker(outside, ext.point([255 if i else 0 for i in range(256)])))
out = Image.frombytes("P", im.size, final.tobytes())
out.putpalette([c for i in range(18) for c in (i * 15, 0, 0)])
out.save(ids_path, optimize=True)

# Foco da câmera
def focus(ids_set):
    m = final.point([255 if i in ids_set else 0 for i in range(256)])
    x0, y0, x1, y1 = m.getbbox()
    cx, cy = (x0 + x1) / 2 * DS, (y0 + y1) / 2 * DS
    z = max((x1 - x0) * DS / meta["w"], (y1 - y0) * DS / meta["h"]) * 1.18
    return [round(cx), round(cy), round(max(.38, min(1.05, z)), 3)]
res = {NAMES[n]: focus({n, n + 10}) for n in range(1, 8)}
res["brasil"] = focus(set(range(1, 8)))
json.dump(res, open(focus_path, "w"), separators=(",", ":"))
print("foco", res)

# Perímetro vetorial da extensão: vértices das ecorregiões que ficam na borda com o vazio (id 0), longe do Brasil
fp = final.load()
def window(x, y, r=3):
    i, j = int(x / DS), int(y / DS)
    return {fp[a, b] for a in range(i - r, i + r + 1) for b in range(j - r, j + r + 1) if 0 <= a < W and 0 <= b < H}
pieces = []
for name, (n, m, geom) in assigned.items():
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        pts = [((c[0] * K - minx) * S, (-c[1] - miny) * S) for c in poly[0]]
        run = []
        for q in pts + [None]:
            keep = False
            if q is not None:
                w = window(*q); keep = (0 in w or 8 in w) and (n + 10) in w and not any(1 <= v <= 7 for v in w)
            if keep: run.append(q); continue
            if len(run) >= 2: pieces.append({"n": n, "o": n, "p": [round(v) for p in run for v in p]})
            run = []
json.dump(pieces, open(focus_path.replace("focus.json", "foreign.json"), "w"), separators=(",", ":"))
print("perímetros fora do Brasil:", len(pieces))
