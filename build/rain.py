"""Chuva por bioma a partir do WorldClim 2.1 (precipitação mensal, resolução de 10 minutos de arco, médias de 1970-2000).

Cada ponto do território brasileiro de um bioma (mapa de ids em data/ids.png) recebe o valor da célula climática que o contém;
a média é ponderada por cos(latitude) para respeitar a área. Só o território brasileiro entra (ids 1 a 6).

Fonte: Fick, S.E. e Hijmans, R.J. (2017), WorldClim 2.1: new 1-km spatial resolution climate surfaces for global land areas.
Uso: python3 -I rain.py data/map.json data/ids.png DIR_COM_wc2.1_10m_prec_01..12.tif data/rain.json
"""
import json, math, os, sys
from array import array
from PIL import Image

meta = json.load(open(sys.argv[1]))
ids = Image.open(sys.argv[2]); IW, IH = ids.size; idp = ids.load()
tif_dir, out = sys.argv[3], sys.argv[4]
K, S, minx, miny = meta["K"], meta["S"], meta["minx"], meta["miny"]
DS = 2.0
SLUG = {1: "amazonia", 2: "cerrado", 3: "mata-atlantica", 4: "caatinga", 5: "pampa", 6: "pantanal"}

months = []
for m in range(1, 13):
    im = Image.open(os.path.join(tif_dir, f"wc2.1_10m_prec_{m:02d}.tif"))
    assert im.mode == "I", im.mode          # int16 com sinal (mm), lido como inteiro de 32 bits; sem dado = -32768
    a = array("i"); a.frombytes(im.tobytes()); months.append(a)
CW, CH = im.size
print("grade climática", CW, CH)

STEP = 3
acc = {n: {"w": 0.0, "m": [0.0] * 12, "ann": []} for n in SLUG}
for j in range(0, IH, STEP):
    y = (j + .5) * DS / S + miny
    lat = -y
    row = int((90 - lat) * 6)
    wt = math.cos(math.radians(lat))
    for i in range(0, IW, STEP):
        n = idp[i, j]
        if n not in SLUG: continue
        x = (i + .5) * DS / S + minx
        lon = x / K
        col = int((lon + 180) * 6)
        idx = row * CW + col
        v = [mm[idx] for mm in months]
        if v[0] < -1000: continue          # sem dado (mar ou fora da grade)
        d = acc[n]; d["w"] += wt
        for k in range(12): d["m"][k] += wt * v[k]
        d["ann"].append((sum(v), wt))

def wpct(pairs, p):
    pairs = sorted(pairs); tot = sum(w for _, w in pairs); c = 0
    for v, w in pairs:
        c += w
        if c >= p * tot: return v
    return pairs[-1][0]

res = {}
for n, d in acc.items():
    mean_m = [x / d["w"] for x in d["m"]]
    ann = sum(mean_m)
    best = max(range(12), key=lambda s: sum(mean_m[(s + k) % 12] for k in range(3)))
    wet = sum(mean_m[(best + k) % 12] for k in range(3))
    res[SLUG[n]] = {
        "mm": [round(x) for x in mean_m],
        "ano": round(ann),
        "p10": round(wpct(d["ann"], .10)), "p90": round(wpct(d["ann"], .90)),
        "seco": sum(1 for x in mean_m if x < 60),                 # meses com menos de 60 mm
        "chuvoso": {"ini": best, "pct": round(wet / ann * 100)},   # 3 meses seguidos mais chuvosos
        "pico": max(range(12), key=lambda k: mean_m[k]),
    }
    print(SLUG[n], res[SLUG[n]])
json.dump(res, open(out, "w"), ensure_ascii=False, separators=(",", ":"))
