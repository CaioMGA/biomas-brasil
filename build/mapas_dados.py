"""Ferramentas para preparar data/mapas/<bioma>.json (camadas temáticas recortadas ao bioma, simplificadas, com fonte/data/licença).

Roda só quando as bases mudam (não faz parte do build do site). As bases brutas NÃO ficam no repositório: cada receita
(build/receitas/<bioma>.py) lista em `FONTES` as URLs a baixar e o que descompactar; a pasta é passada como argumento.

Uso: python3 -I build/mapas_dados.py <pasta com as bases descompactadas> <bioma> [saída.json]
"""
import importlib, json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def dp(pts, eps):
    """Douglas-Peucker iterativo (eps em graus)."""
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True; st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop(); ax, ay = pts[a]; bx, by = pts[b]
        dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy) or 1e-12; md, mi = 0, -1
        for i in range(a + 1, b):
            d = abs(dy * (pts[i][0] - ax) - dx * (pts[i][1] - ay)) / L
            if d > md: md, mi = d, i
        if md > eps: keep[mi] = True; st += [(a, mi), (mi, b)]
    return [p for p, k in zip(pts, keep) if k]


def dp_ring(r, eps):
    """Simplifica um anel e o devolve aberto; None se sobrar menos de 3 pontos."""
    s = dp(r[:-1] if r[0] == r[-1] else r, eps)
    return s if len(s) >= 4 else None


def inside(pt, ring):
    """Ponto dentro do anel (par/ímpar)."""
    x, y = pt; c = False; j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]; xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi: c = not c
        j = i
    return c


def dist_borda(pt, ring):
    """Distância (graus) do ponto à borda do anel."""
    x, y = pt; best = 1e9
    for i in range(len(ring) - 1):
        ax, ay = ring[i]; bx, by = ring[i + 1]; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy or 1e-12
        t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L2))
        best = min(best, math.hypot(x - ax - t * dx, y - ay - t * dy))
    return best


def toca(geom, ring):
    """True se algum vértice (amostrando até ~200 por anel) de `geom` cai dentro do anel."""
    for r in geom:
        for p in r[::max(1, len(r) // 200)]:
            if inside(p, ring): return True
    return False


def r3(pts):
    return [[round(x, 3), round(y, 3)] for x, y in pts]


def recorta_anel(ring, box):
    """Sutherland-Hodgman contra um retângulo (x0, y0, x1, y1): serve para preenchimentos (a aresta criada na borda é invisível)."""
    x0, y0, x1, y1 = box
    def corta(pts, dentro, cruza):
        out = []
        for i, b in enumerate(pts):
            a = pts[i - 1]
            if dentro(b):
                if not dentro(a): out.append(cruza(a, b))
                out.append(b)
            elif dentro(a): out.append(cruza(a, b))
        return out
    def em_x(x):
        return lambda a, b: (x, a[1] + (b[1] - a[1]) * (x - a[0]) / ((b[0] - a[0]) or 1e-12))
    def em_y(y):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y - a[1]) / ((b[1] - a[1]) or 1e-12), y)
    pts = ring[:-1] if ring and ring[0] == ring[-1] else list(ring)
    for dentro, cruza in ((lambda p: p[0] >= x0, em_x(x0)), (lambda p: p[0] <= x1, em_x(x1)), (lambda p: p[1] >= y0, em_y(y0)), (lambda p: p[1] <= y1, em_y(y1))):
        if not pts: return None
        pts = corta(pts, dentro, cruza)
    return pts if len(pts) >= 3 else None


def corta_linha(line, box, folga=0.02):
    """Divide a polilinha nos trechos que ficam dentro da caixa (com uma folga); não cria arestas falsas na borda."""
    x0, y0, x1, y1 = box[0] - folga, box[1] - folga, box[2] + folga, box[3] + folga
    runs, atual = [], []
    for i, p in enumerate(line):
        if x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
            if not atual and i > 0: atual.append(line[i - 1])   # um ponto fora, para a linha chegar até a borda
            atual.append(p)
        else:
            if atual: atual.append(p); runs.append(atual); atual = []
    if atual: runs.append(atual)
    return [r for r in runs if len(r) > 1]


def toca_caixa(geom, box):
    xs = [p[0] for r in geom for p in r]; ys = [p[1] for r in geom for p in r]
    return not (max(xs) < box[0] or min(xs) > box[2] or max(ys) < box[1] or min(ys) > box[3])


if __name__ == "__main__":
    raw, id_ = sys.argv[1], sys.argv[2]
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(root, "data", "mapas", id_ + ".json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    d = importlib.import_module("receitas." + id_.replace("-", "_")).receita(raw)
    json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(out, os.path.getsize(out) // 1024, "KB;", {c["id"]: len(c["itens"]) for c in d["camadas"]})
