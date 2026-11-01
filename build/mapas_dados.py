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


if __name__ == "__main__":
    raw, id_ = sys.argv[1], sys.argv[2]
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(root, "data", "mapas", id_ + ".json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    d = importlib.import_module("receitas." + id_.replace("-", "_")).receita(raw)
    json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(out, os.path.getsize(out) // 1024, "KB;", {c["id"]: len(c["itens"]) for c in d["camadas"]})
