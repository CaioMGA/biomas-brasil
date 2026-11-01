"""Mapa de localização (América do Sul): oceano, continente, Brasil em destaque com os estados contornados e o bioma contornado.

Dois passos, ambos fora do build do site:
  python3 -I build/localizacao.py contexto <pasta com ne_10m_admin_0_countries/ e ne_10m_admin_1_states_provinces/>
      -> data/localizacao/america-do-sul.json  (países, estados do Brasil; Natural Earth 1:10m, domínio público; igual para todos os biomas)
  python3 -I build/localizacao.py bioma <id>
      -> data/localizacao/<id>.json  (contorno do bioma, vindo de data/mapas/<id>.json, e os países que ele toca)
O build lê esses arquivos (`figura()`) e embute um SVG pequeno e estático no começo da página; sem JavaScript.
"""
import html, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapas

E = lambda s: html.escape(str(s), quote=True)
BBOX = (-82.0, -56.5, -34.0, 13.5)   # América do Sul continental (sem as ilhas oceânicas distantes)
SUL = {"ARG", "BOL", "BRA", "CHL", "COL", "ECU", "GUY", "PRY", "PER", "SUR", "URY", "VEN", "FRA"}   # FRA: só a Guiana Francesa
EPS_PAIS = .12   # graus; ~1 px a 400 px de largura


def _pais_nome(a):
    return {"FRA": "Guiana Francesa"}.get(a["ADM0_A3"], a["NAME_PT"])


def contexto(raw, root):
    import shp
    from mapas_dados import dp_ring
    paises, estados = [], []
    for a, g in shp.read(f"{raw}/ne_10m_admin_0_countries/ne_10m_admin_0_countries", BBOX):
        if a["ADM0_A3"] not in SUL: continue
        rings = []
        for r in g:
            xs, ys = [p[0] for p in r], [p[1] for p in r]
            if a["ADM0_A3"] == "FRA" and not (-55 < min(xs) and max(xs) < -51 and 2 < min(ys) and max(ys) < 6.5): continue   # só a Guiana Francesa
            if max(xs) < BBOX[0] or min(xs) > BBOX[2] or max(ys) < BBOX[1] or min(ys) > BBOX[3]: continue
            q = dp_ring(r, EPS_PAIS)
            if q: rings.append([[round(x, 2), round(y, 2)] for x, y in q])
        if rings: paises.append({"nome": _pais_nome(a), "iso": a["ADM0_A3"], "rings": rings})
    for a, g in shp.read(f"{raw}/ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces", BBOX):
        if a["adm0_a3"] != "BRA": continue
        for r in g:
            q = dp_ring(r, EPS_PAIS)
            if q: estados.append([[round(x, 2), round(y, 2)] for x, y in q])
    out = os.path.join(root, "data", "localizacao", "america-do-sul.json"); os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"bbox": BBOX, "fonte": "Natural Earth 1:10 milhões (domínio público)", "paises": paises, "estados": estados}, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(out, os.path.getsize(out) // 1024, "KB;", len(paises), "países,", len(estados), "contornos de estados")


def bioma(id, root):
    from mapas_dados import dp_ring, inside
    ctx = json.load(open(os.path.join(root, "data", "localizacao", "america-do-sul.json"), encoding="utf-8"))
    m = json.load(open(os.path.join(root, "data", "mapas", id + ".json"), encoding="utf-8"))
    aneis = mapas.aneis(m["limite"])
    simp = [q for q in (dp_ring([tuple(p) for p in r], .03) for r in aneis) if q]
    amostra = [p for r in simp for p in r[::max(1, len(r) // 40)]]
    tocados = [p["nome"] for p in ctx["paises"] if any(inside(pt, [tuple(v) for v in r]) for pt in amostra for r in p["rings"])]
    out = os.path.join(root, "data", "localizacao", id + ".json")
    json.dump({"rings": [[[round(x, 2), round(y, 2)] for x, y in r] for r in simp], "paises": sorted(set(tocados))}, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(out, os.path.getsize(out) // 1024, "KB; países:", sorted(set(tocados)))


def figura(root, id, nome):
    """HTML da figura (SVG embutido) ou "" se faltar o contexto ou os dados do bioma."""
    pc, pb = (os.path.join(root, "data", "localizacao", f) for f in ("america-do-sul.json", id + ".json"))
    if not (os.path.exists(pc) and os.path.exists(pb)): return ""
    ctx, b = json.load(open(pc, encoding="utf-8")), json.load(open(pb, encoding="utf-8"))
    P = mapas.Proj(ctx["bbox"], pad=0)
    br = [p for p in ctx["paises"] if p["iso"] == "BRA"]; resto = [p for p in ctx["paises"] if p["iso"] != "BRA"]
    cam = lambda aneis: mapas.caminho(P, aneis, True)
    terra = cam([r for p in resto for r in p["rings"]]); brasil = cam([r for p in br for r in p["rings"]])
    estados = cam(ctx["estados"]); biom = cam(b["rings"])
    paises = b["paises"]; lista = ", ".join(paises[:-1]) + " e " + paises[-1] if len(paises) > 1 else (paises[0] if paises else "")
    desc = f"Mapa da América do Sul: o território brasileiro em destaque, com os estados contornados, e o {nome} contornado e pintado na cor de destaque"
    desc += f", ocupando partes de {lista}." if len(paises) > 1 else "."
    cap = f"Localização do {E(nome)} na América do Sul" + (f": o bioma se estende por {E(lista)}." if len(paises) > 1 else ".")
    return (f'<figure class="loc"><svg viewBox="0 0 {P.w} {P.h}" role="img" aria-label="{E(desc)}" preserveAspectRatio="xMidYMid meet">'
            f'<rect class="loc-mar" width="{P.w}" height="{P.h}"/><path class="loc-terra" d="{terra}"/><path class="loc-br" d="{brasil}"/>'
            f'<path class="loc-uf" d="{estados}"/><path class="loc-br-borda" d="{brasil}"/><path class="loc-bioma" d="{biom}"/></svg>'
            f'<figcaption>{cap}<span class="loc-leg"><i class="loc-sw loc-sw-bioma"></i>{E(nome)}<i class="loc-sw loc-sw-br"></i>Brasil (com os estados)</span></figcaption></figure>')


if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    if sys.argv[1] == "contexto": contexto(sys.argv[2], root)
    elif sys.argv[1] == "bioma": bioma(sys.argv[2], root)
