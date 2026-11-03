"""Acrescenta ecorregiões à extensão (fora do Brasil) de UM bioma no mapa de ids JÁ estendido (data/ids.png), sem refazer os outros biomas.

`extents.py` só pinta a extensão onde o id é 0 (vazio) e roda uma vez sobre o raster original. Depois dele, os outros países da América do Sul já são
"terra neutra" (id 8), então uma ecorregião que ele não associou (ex.: a "Humid Pampas" argentina, que não toca o Pampa brasileiro e por isso fica
abaixo do LIMIAR) não entra se o script for rodado de novo. Aqui a ecorregião é pintada com o id 10 + n SÓ sobre a terra neutra (id 8): o mar (id 0)
e o Brasil (ids 1-7) ficam como estão.

Também recalcula, só para o bioma n: o foco da câmera em data/focus.json e os perímetros do bioma n em data/foreign.json (os dos outros biomas não mudam).

Uso: python3 -I build/extents_add.py <n> <eco1.json> [eco2.json ...] [--dry]
  n = 1..6 (5 = Pampa). Cada eco*.json é um GeoJSON do FeatureServer da RESOLVE com uma feição (a ecorregião inteira, anel externo).
  Para recompor TODAS as ecorregiões do bioma n nos perímetros, passe também as que já faziam parte dele (ex.: a "Uruguayan savanna" para o Pampa).
  Mas só as ecorregiões em `novas` (as que vierem depois de `--novas`) são pintadas; as demais só entram no cálculo dos perímetros.
  Ex.: python3 -I build/extents_add.py 5 ~/biomas-raw/resolve_pa/eco_574.json --novas ~/biomas-raw/resolve_pa/eco_576.json
"""
import json, os, sys
from PIL import Image, ImageChops, ImageDraw

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--") or a == "--novas"]
dry = "--dry" in sys.argv
n = int(args[0]); i = args.index("--novas"); antigas, novas = args[1:i], args[i + 1:]
meta = json.load(open(os.path.join(root, "data/map.json")))
K, S, minx, miny = meta["K"], meta["S"], meta["minx"], meta["miny"]
DS = 2.0
NAMES = {1: "amazonia", 2: "cerrado", 3: "mata-atlantica", 4: "caatinga", 5: "pampa", 6: "pantanal", 7: "costeiro"}
ids_path = os.path.join(root, "data/ids.png"); focus_path = os.path.join(root, "data/focus.json"); foreign_path = os.path.join(root, "data/foreign.json")
im = Image.open(ids_path); W, H = im.size
base = Image.frombytes("L", im.size, im.tobytes())


def px(lon, lat): return ((lon * K - minx) * S / DS, (-lat - miny) * S / DS)


def geom_of(path): return json.load(open(path))["features"][0]["geometry"]


def mask_of(geom):
    m = Image.new("L", im.size, 0); d = ImageDraw.Draw(m)
    for poly in (geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]):
        d.polygon([px(*c[:2]) for c in poly[0]], fill=255)   # só o anel externo
    return m


before = base.histogram()
land = base.point([255 if i == 8 else 0 for i in range(256)])   # terra neutra (outros países)
final = base.copy()
for p in novas:
    m = mask_of(geom_of(p)); final.paste(10 + n, mask=ImageChops.darker(land, m))
after = final.histogram()
print("pixels com id", 10 + n, "antes:", before[10 + n], "depois:", after[10 + n], "| terra neutra (8):", before[8], "->", after[8])
for i in range(256):
    if i not in (8, 10 + n) and before[i] != after[i]: sys.exit(f"ERRO: o id {i} mudou ({before[i]} -> {after[i]})")
if dry: sys.exit()
out = Image.frombytes("P", im.size, final.tobytes()); out.putpalette([c for i in range(18) for c in (i * 15, 0, 0)]); out.save(ids_path, optimize=True)

# foco da câmera só do bioma n (mesma conta do extents.py)
def focus(ids_set):
    m = final.point([255 if i in ids_set else 0 for i in range(256)]); x0, y0, x1, y1 = m.getbbox()
    cx, cy = (x0 + x1) / 2 * DS, (y0 + y1) / 2 * DS
    z = max((x1 - x0) * DS / meta["w"], (y1 - y0) * DS / meta["h"]) * 1.18
    return [round(cx), round(cy), round(max(.38, min(1.05, z)), 3)]
fo = json.load(open(focus_path)); print("foco antes:", fo[NAMES[n]]); fo[NAMES[n]] = focus({n, n + 10}); print("foco depois:", fo[NAMES[n]])
json.dump(fo, open(focus_path, "w"), separators=(",", ":"))

# perímetros do bioma n (mesma regra do extents.py: vértices na borda com o vazio/terra neutra, longe do Brasil)
fp = final.load()
def window(x, y, r=3):
    i, j = int(x / DS), int(y / DS)
    return {fp[a, b] for a in range(i - r, i + r + 1) for b in range(j - r, j + r + 1) if 0 <= a < W and 0 <= b < H}
pieces = []
for path in antigas + novas:
    g = geom_of(path)
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        pts = [((c[0] * K - minx) * S, (-c[1] - miny) * S) for c in poly[0]]; run = []
        for q in pts + [None]:
            keep = False
            if q is not None:
                w = window(*q); keep = (0 in w or 8 in w) and (n + 10) in w and not any(1 <= v <= 7 for v in w)
            if keep: run.append(q); continue
            if len(run) >= 2: pieces.append({"n": n, "o": n, "p": [round(v) for p in run for v in p]})
            run = []
fr = json.load(open(foreign_path)); outros = [p for p in fr if p["n"] != n]
print("perímetros do bioma", n, "antes:", len(fr) - len(outros), "depois:", len(pieces))
json.dump(outros + pieces, open(foreign_path, "w"), separators=(",", ":"))
