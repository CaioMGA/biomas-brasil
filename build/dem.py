"""Gera data/dem.png (relevo do Brasil) na mesma grade equiretangular do mapa de biomas.

Fonte: tiles Terrarium (AWS Open Data, "Terrain Tiles": SRTM, GMTED e ETOPO1), zoom 6.
Codificação de saída: (elevação em metros + 6000) * 6, 16 bits em R (byte alto) e G (byte baixo); abaixo de 0 é batimetria.
Uso: python3 -I dem.py data/map.json CACHE_DIR data/dem.png
"""
import io, json, math, os, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

meta = json.load(open(sys.argv[1]))
cache, out = sys.argv[2], sys.argv[3]
Z = 6
OW = 1400
OH = round(OW * meta["h"] / meta["w"])
K, minx, maxx, miny, maxy = meta["K"], meta["minx"], meta["maxx"], meta["miny"], meta["maxy"]
lon0, lon1 = minx / K, maxx / K
lat1, lat0 = -miny, -maxy  # y = -lat

def merc(lon, lat):
    n = 2 ** Z * 256
    x = (lon + 180) / 360 * n
    r = math.radians(lat)
    y = (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n
    return x, y

x0, y0 = merc(lon0, lat1)
x1, y1 = merc(lon1, lat0)
tx0, tx1 = int(x0 // 256) - 1, int(x1 // 256) + 1
ty0, ty1 = int(y0 // 256) - 1, int(y1 // 256) + 1
tiles = [(x, y) for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]
print("tiles", len(tiles), "saida", OW, OH)

def get(t):
    x, y = t
    f = os.path.join(cache, f"{Z}_{x}_{y}.png")
    if not os.path.exists(f):
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{Z}/{x}/{y}.png"
        for _ in range(3):
            try:
                data = urllib.request.urlopen(url, timeout=30).read()
                open(f, "wb").write(data)
                break
            except Exception as e:
                err = e
        else:
            raise err
    return t, Image.open(f).convert("RGB")

os.makedirs(cache, exist_ok=True)
with ThreadPoolExecutor(8) as ex:
    got = dict(ex.map(get, tiles))

BW, BH = (tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256
big = Image.new("RGB", (BW, BH))
for (x, y), im in got.items():
    big.paste(im, ((x - tx0) * 256, (y - ty0) * 256))
px = big.load()
ox, oy = tx0 * 256, ty0 * 256

def elev(ix, iy):
    r, g, b = px[ix, iy]
    return r * 256 + g + b / 256 - 32768

res = Image.new("RGB", (OW, OH))
op = res.load()
for j in range(OH):
    lat = lat1 - (j + .5) / OH * (lat1 - lat0)
    for i in range(OW):
        lon = lon0 + (i + .5) / OW * (lon1 - lon0)
        mx, my = merc(lon, lat)
        fx, fy = mx - ox - .5, my - oy - .5
        ix, iy = int(fx), int(fy)
        ax, ay = fx - ix, fy - iy
        e = (elev(ix, iy) * (1 - ax) * (1 - ay) + elev(ix + 1, iy) * ax * (1 - ay)
             + elev(ix, iy + 1) * (1 - ax) * ay + elev(ix + 1, iy + 1) * ax * ay)
        v = int((max(-6000.0, min(4900.0, e)) + 6000) * 6)
        op[i, j] = (v >> 8, v & 255, 0)
res.save(out, optimize=True)
print("ok", os.path.getsize(out) // 1024, "KB")
