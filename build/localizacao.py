"""Mapa de localização (América do Sul): oceano, continente (uma cor só), Brasil e estados contornados e o bioma contornado.

Dois passos, ambos fora do build do site:
  python3 -I build/localizacao.py contexto <pasta com ne_10m_admin_0_countries/ e ne_10m_admin_1_states_provinces/>
      -> data/localizacao/america-do-sul.json  (países, estados do Brasil; Natural Earth 1:10m, domínio público; igual para todos os biomas)
  python3 -I build/localizacao.py bioma <id>
      -> data/localizacao/<id>.json  (contorno do bioma, vindo de data/mapas/<id>.json, e os países que ele toca)
O build lê esses arquivos (`figura()`) e embute um SVG pequeno e estático no começo da página; sem JavaScript.
"""
import html, json, math, os, sys

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
    from mapas_dados import dp, dp_ring, inside
    ctx = json.load(open(os.path.join(root, "data", "localizacao", "america-do-sul.json"), encoding="utf-8"))
    m = json.load(open(os.path.join(root, "data", "mapas", id + ".json"), encoding="utf-8"))
    aneis = mapas.aneis(m["limite"])
    xs = [p[0] for r in aneis for p in r]; ys = [p[1] for r in aneis for p in r]
    eps = max(.03, math.hypot(max(xs) - min(xs), max(ys) - min(ys)) * .002)   # a figura é pequena: biomas grandes podem ser mais simplificados
    simp = [q for q in (dp_ring([tuple(p) for p in r], eps) for r in aneis) if q]
    contorno = [[[round(x, 2), round(y, 2)] for x, y in l] for l in (dp([tuple(p) for p in l], eps) for l in m.get("limite_contorno", [])) if len(l) > 1]   # contorno externo, quando o limite vem de várias peças
    amostra = [p for r in simp for p in r[::max(1, len(r) // 40)]]
    tocados = [p["nome"] for p in ctx["paises"] if any(inside(pt, [tuple(v) for v in r]) for pt in amostra for r in p["rings"])]
    out = os.path.join(root, "data", "localizacao", id + ".json")
    fontes = m.get("fontes", {}); f = fontes.get(m.get("limite_fonte", "resolve")) or next(iter(fontes.values()), {})   # fonte do limite do bioma
    fonte = {"nome": f.get("titulo", "").split(" (")[0].split(", ")[0], "url": f.get("url", ""), "licenca": f.get("licenca", "")}
    json.dump({"rings": [[[round(x, 2), round(y, 2)] for x, y in r] for r in simp], "contorno": contorno, "paises": sorted(set(tocados)), "fonte": fonte}, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
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
    borda = mapas.caminho(P, b["contorno"], False) if b.get("contorno") else biom   # só o contorno externo, sem as divisas internas entre peças do bioma
    paises = b["paises"]; lista = ", ".join(paises[:-1]) + " e " + paises[-1] if len(paises) > 1 else (paises[0] if paises else "")
    desc = f"Mapa da América do Sul: o Brasil e seus estados contornados, e o {nome} contornado e pintado na cor de destaque"
    desc += f", ocupando partes de {lista}." if len(paises) > 1 else "."
    cap = f"Localização do {E(nome)} na América do Sul" + (f": o bioma se estende por {E(lista)}." if len(paises) > 1 else ".")
    fb = b.get("fonte") or {}
    lic = f' ({E(fb["licenca"])})' if fb.get("licenca") else ""
    bio = (f'contorno do bioma: <a href="{E(fb["url"])}" target="_blank" rel="noopener">{E(fb["nome"])}</a>{lic}' if fb.get("url") else "")
    fonte = ('<span class="loc-fonte">Fontes: países e estados do Brasil: <a href="https://www.naturalearthdata.com/" target="_blank" rel="noopener">Natural Earth</a> (domínio público)' + ("; " + bio if bio else "") + ".</span>")
    S = max(P.w, P.h); vx, vy = -(S - P.w) // 2, -(S - P.h) // 2   # moldura quadrada: o continente fica centralizado, com oceano nas sobras
    return (f'<figure class="loc"><div class="loc-mapa"><svg viewBox="{vx} {vy} {S} {S}" role="img" aria-label="{E(desc)}" preserveAspectRatio="xMidYMid meet">'
            f'<rect class="loc-mar" x="{vx}" y="{vy}" width="{S}" height="{S}"/><path class="loc-terra" d="{terra}"/><path class="loc-br" d="{brasil}"/><path class="loc-bioma" d="{biom}"/>'
            f'<path class="loc-front" d="{terra}"/><path class="loc-uf" d="{estados}"/><path class="loc-br-borda" d="{brasil}"/><path class="loc-bioma-borda" d="{borda}"/></svg>'
            f'<p class="loc-mini">{E(nome)} em destaque na América do Sul</p></div>'
            f'<figcaption>{cap}{fonte}<span class="loc-leg"><i class="loc-sw loc-sw-bioma"></i>{E(nome)}</span></figcaption></figure>')


if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    if sys.argv[1] == "contexto": contexto(sys.argv[2], root)
    elif sys.argv[1] == "bioma": bioma(sys.argv[2], root)
