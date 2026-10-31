import sqlite3, struct, math, json, sys
src, out = sys.argv[1], sys.argv[2]
c = sqlite3.connect(src)
rows = c.execute("select name_biome, geom from biomes_2019_simplified").fetchall()

def parse(b):
    flags = b[3]
    env = {0:0,1:32,2:48,3:48,4:64}[(flags>>1)&7]
    w = b[8+env:]
    return wkb(w)[0]

def wkb(w, o=0):
    bo = '<' if w[o]==1 else '>'
    t = struct.unpack_from(bo+'I', w, o+1)[0] & 0xFFFF
    o += 5
    if t == 3:
        n = struct.unpack_from(bo+'I', w, o)[0]; o += 4
        rings = []
        for _ in range(n):
            m = struct.unpack_from(bo+'I', w, o)[0]; o += 4
            pts = struct.unpack_from(bo+'%dd'%(2*m), w, o); o += 16*m
            rings.append([(pts[i], pts[i+1]) for i in range(0, 2*m, 2)])
        return [rings], o
    if t == 6:
        n = struct.unpack_from(bo+'I', w, o)[0]; o += 4
        polys = []
        for _ in range(n):
            p, o = wkb(w, o); polys += p
        return polys, o
    raise ValueError(t)

def dp(pts, eps):
    if len(pts) < 3: return pts
    keep = [False]*len(pts); keep[0]=keep[-1]=True
    st = [(0, len(pts)-1)]
    while st:
        a, b = st.pop()
        ax, ay = pts[a]; bx, by = pts[b]
        dx, dy = bx-ax, by-ay; L = math.hypot(dx, dy) or 1e-12
        md, mi = 0, -1
        for i in range(a+1, b):
            d = abs(dy*(pts[i][0]-ax) - dx*(pts[i][1]-ay))/L
            if d > md: md, mi = d, i
        if md > eps:
            keep[mi] = True; st += [(a, mi), (mi, b)]
    return [p for p, k in zip(pts, keep) if k]

K = math.cos(math.radians(14))
def proj(x, y): return (x*K, -y)
def area(r): return abs(sum(r[i][0]*r[i+1][1]-r[i+1][0]*r[i][1] for i in range(len(r)-1)))/2

data = {}
allp = []
for name, g in rows:
    polys = parse(g)
    # Ilhas oceânicas (Fernando de Noronha, Atol das Rocas, Trindade e Martim Vaz, São Pedro e São Paulo) entram no IBGE como polígonos
    # soltos da Mata Atlântica, a leste de todo o continente (ponta mais a leste: -34,79). Ficam fora do mapa.
    if name != "Sistema Costeiro":
        polys = [p for p in polys if min(x for x, _ in p[0]) <= -34.6]
    data[name] = [[[proj(x, y) for x, y in r] for r in p] for p in polys]
    for p in data[name]:
        allp += p[0]
minx = min(p[0] for p in allp); maxx = max(p[0] for p in allp)
miny = min(p[1] for p in allp); maxy = max(p[1] for p in allp)
minx = -81.8 * K; miny = -12.8; maxy = 56.2   # quadro da América do Sul inteira (da Venezuela à Terra do Fogo)
S = 100.0
W, H = (maxx-minx)*S, (maxy-miny)*S
res = {"minx": minx, "maxx": maxx, "miny": miny, "maxy": maxy, "K": K, "S": S, "w": round(W), "h": round(H), "paths": {}, "centroid": {}, "deg2": {}}
for name, polys in data.items():
    d = []; tot = 0; cx = cy = 0
    for p in polys:
        if area(p[0]) < 0.02: continue   # drop slivers/islets
        for ri, r in enumerate(p):
            if ri > 0 and area(r) < 0.02: continue
            r = [((x-minx)*S, (y-miny)*S) for x, y in r]
            far = max(range(len(r)), key=lambda i: (r[i][0]-r[0][0])**2+(r[i][1]-r[0][1])**2)
            r = dp(r[:far+1], 2.6)[:-1] + dp(r[far:], 2.6)
            if len(r) < 4: continue
            d.append("M" + "L".join("%.0f,%.0f" % q for q in r[:-1]) + "Z")
        a = area(p[0]); tot += a
        mx = sum(q[0] for q in p[0])/len(p[0]); my = sum(q[1] for q in p[0])/len(p[0])
        cx += mx*a; cy += my*a
    res["paths"][name] = "".join(d)
    res["deg2"][name] = tot
    res["centroid"][name] = [round((cx/tot-minx)*S), round((cy/tot-miny)*S)]
six = [n for n in res["deg2"] if n != "Sistema Costeiro"]
tot6 = sum(res["deg2"][n] for n in six)
for n in six: print(n, "%.1f%%" % (100*res["deg2"][n]/tot6), len(res["paths"][n]))
print(res["w"], res["h"], res["centroid"])
json.dump(res, open(out, "w"), ensure_ascii=False)

from PIL import Image, ImageDraw
order = ["Sistema Costeiro","Amazônia","Cerrado","Mata Atlântica","Caatinga","Pampa","Pantanal"]
IDS = {"Sistema Costeiro": 7, "Amazônia": 1, "Cerrado": 2, "Mata Atlântica": 3, "Caatinga": 4, "Pampa": 5, "Pantanal": 6}
DS = 2.0  # px da imagem = unidades/DS
im = Image.new("P", (round(W/DS), round(H/DS)), 0)
dr = ImageDraw.Draw(im)
for n in order:
    for p in data[n]:
        dr.polygon([((x-minx)*S/DS, (y-miny)*S/DS) for x, y in p[0]], fill=IDS[n])
im.putpalette([c for i in range(18) for c in (i * 15, 0, 0)])  # índice i -> cor (15*i, 0, 0); 1-7 Brasil e mar, 11-16 extensão fora do Brasil
im.save(out.replace("map.json", "ids.png"), optimize=True)
print("ids", im.size)

# --- contornos vetoriais dos biomas (anéis simplificados, em unidades do mapa) ---
def dp_ring(pts, eps):
    far = max(range(len(pts)), key=lambda i: (pts[i][0]-pts[0][0])**2 + (pts[i][1]-pts[0][1])**2)
    return dp(pts[:far+1], eps)[:-1] + dp(pts[far:], eps)

idp = im.load(); IWd, IHd = im.size
def near_sea(x, y, r=3):   # o contorno do Sistema Costeiro só vale onde há mar visível (a faixa continental fica sob os biomas)
    i, j = int(x / DS), int(y / DS)
    return any(0 <= a < IWd and 0 <= b < IHd and idp[a, b] == 7 for a in range(i-r, i+r+1) for b in range(j-r, j+r+1))

outlines = []
for n in order:
    idx = IDS[n]
    for poly in data[n]:
        for ri, ring in enumerate(poly):
            pts = dp_ring([((x-minx)*S, (y-miny)*S) for x, y in ring], .8)
            if len(pts) < 4: continue
            runs = [pts]
            if idx == 7:
                runs, cur = [], []
                for q in pts:
                    if near_sea(*q): cur.append(q)
                    else:
                        if len(cur) >= 2: runs.append(cur)
                        cur = []
                if len(cur) >= 2: runs.append(cur)
            for r in runs:
                outlines.append({"n": idx, "o": 0, "h": 1 if ri else 0, "p": [round(v) for q in r for v in q]})   # h: anel interno (furo)
json.dump(outlines, open(out.replace("map.json", "outlines.json"), "w"), separators=(",", ":"))
print("contornos", len(outlines))
