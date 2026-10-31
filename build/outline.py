"""Contorno do território brasileiro como caminho SVG, para a tela de carregamento (fica embutido no HTML, sem depender de nada externo).

Usa a máscara dos 6 biomas continentais (ids 1 a 6 de data/ids.png): fecha pequenas fendas para as ilhas costeiras se juntarem,
fica com a maior massa conectada e percorre a borda externa (Moore), simplificando e suavizando o traçado.
Uso: python3 -I outline.py data/ids.png data/outline.json
"""
import json, math, sys
from PIL import Image, ImageFilter

F = 3   # redução da imagem antes de traçar
im = Image.open(sys.argv[1]); out = sys.argv[2]
raw = Image.frombytes("L", im.size, im.tobytes())
mask = raw.point([255 if 1 <= i <= 6 else 0 for i in range(256)]).resize((im.width // F, im.height // F), Image.NEAREST)
mask = mask.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7))   # fecha frestas entre ilhas e continente
W, H = mask.size
land = bytearray(1 if v else 0 for v in mask.tobytes())

# maior componente conexa (8 vizinhos)
seen = bytearray(W * H); best = []
for s in range(W * H):
    if not land[s] or seen[s]: continue
    comp, stack = [], [s]; seen[s] = 1
    while stack:
        p = stack.pop(); comp.append(p); x, y = p % W, p // W
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H:
                    q = ny * W + nx
                    if land[q] and not seen[q]: seen[q] = 1; stack.append(q)
    if len(comp) > len(best): best = comp
main = bytearray(W * H)
for p in best: main[p] = 1

D = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]   # sentido horário, começando a leste
def L(x, y): return 0 <= x < W and 0 <= y < H and main[y * W + x]
sy = next(y for y in range(H) if any(main[y * W:(y + 1) * W]))
sx = main[sy * W:(sy + 1) * W].index(1)
b = (sx, sy); d = 4                     # d: direção (a partir de b) do vizinho de fundo de onde se veio (oeste)
pts = [b]; first = None
for _ in range(W * H):
    nxt = None
    for k in range(8):
        dd = (d + 1 + k) % 8
        nx, ny = b[0] + D[dd][0], b[1] + D[dd][1]
        if L(nx, ny): nxt = (nx, ny, dd); break
    if nxt is None: break
    nx, ny, dd = nxt
    cb = (b[0] + D[(dd - 1) % 8][0], b[1] + D[(dd - 1) % 8][1])        # vizinho de fundo examinado logo antes
    d = D.index((cb[0] - nx, cb[1] - ny)) if (cb[0] - nx, cb[1] - ny) in D else (dd + 4) % 8
    b = (nx, ny)
    if first is None: first = b
    elif b == pts[0] and len(pts) > 8: break
    pts.append(b)
print("contorno bruto:", len(pts), "pontos")

def dp(p, eps):
    if len(p) < 3: return p
    keep = [False] * len(p); keep[0] = keep[-1] = True; st = [(0, len(p) - 1)]
    while st:
        a, c = st.pop(); ax, ay = p[a]; cx, cy = p[c]; dx, dy = cx - ax, cy - ay; ln = math.hypot(dx, dy) or 1e-9
        md, mi = 0, -1
        for i in range(a + 1, c):
            v = abs(dy * (p[i][0] - ax) - dx * (p[i][1] - ay)) / ln
            if v > md: md, mi = v, i
        if md > eps: keep[mi] = True; st += [(a, mi), (mi, c)]
    return [q for q, k in zip(p, keep) if k]
far = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
ring = dp(pts[:far + 1], 1.4)[:-1] + dp(pts[far:] + [pts[0]], 1.4)[:-1]
for _ in range(2):   # suaviza (Chaikin)
    nr = []
    for i in range(len(ring)):
        a, c = ring[i], ring[(i + 1) % len(ring)]
        nr += [(.75 * a[0] + .25 * c[0], .75 * a[1] + .25 * c[1]), (.25 * a[0] + .75 * c[0], .25 * a[1] + .75 * c[1])]
    ring = nr
xs = [p[0] for p in ring]; ys = [p[1] for p in ring]; pad = 6
x0, y0 = min(xs) - pad, min(ys) - pad
w, h = round(max(xs) - x0 + pad), round(max(ys) - y0 + pad)
d = "M" + "L".join("%.1f,%.1f" % (p[0] - x0, p[1] - y0) for p in ring) + "Z"
json.dump({"d": d, "w": w, "h": h}, open(out, "w"), separators=(",", ":"))
print("contorno:", len(ring), "pontos |", w, "x", h, "|", len(d), "bytes")
