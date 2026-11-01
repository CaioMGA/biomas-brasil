"""Receita do mapa temático da CAATINGA: "os rios que secam". Os principais rios do bioma, classificados pela fração do curso em que a vazão natural
é nula (Q95 = 0, isto é, o rio fica sem vazão em 5% do tempo ou mais), segundo a Disponibilidade Hídrica Superficial da ANA. Sem cidades, UCs nem outras camadas.

Pasta de entrada (`raw`):
  biomas/                   IBGE, Biomas 1:250 000 (2025)           lml_bioma_e250k_v20250911_A.*   (limite oficial; a Caatinga é só brasileira)
  anadisp/                  ANA, Disponibilidade Hídrica Superficial (BHO 2017 5K), DispH_v27nov20_Snirh.{shp,shx,dbf}  (extraída do zip por HTTP Range)
  ne_10m_admin_0_countries/, ne_10m_admin_0_boundary_lines_land/, ne_10m_admin_1_states_provinces/   Natural Earth 1:10m (domínio público)

Nota sobre a base da ANA: os nomes dos rios (campo noriocomp) vêm com acentos corrompidos de forma irregular (ex.: "Rio Sro Francisco", "Rio Parna0ba"),
por isso os rios são achados por expressão regular + caixa de coordenadas e mostrados com o nome correto escrito aqui.
"""
import json, math, mmap, os, re, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import shp
from mapas_dados import dp, dp_ring, inside, dist_borda, r3, recorta_anel, corta_linha, Mascara

PUB = "dado público do IBGE (termo de licença não localizado)"
FONTES = {
    "biomas": {"titulo": "IBGE, Biomas e Sistema Costeiro-Marinho do Brasil 1:250 000 (2025): limite oficial da Caatinga",
               "url": "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/vetores/2025_Biomas-e-Sistema-Costeiro-Marinho-do-Brasil-1-250000_shp.zip", "data": "2025-09", "licenca": PUB},
    "ana": {"titulo": "ANA, Disponibilidade Hídrica Superficial por trecho da Base Hidrográfica Ottocodificada (BHO 2017 5K), versão 27/11/2020: geometria dos rios e vazão natural com 95% de permanência (Q95NAT)",
            "url": "https://metadados.snirh.gov.br/files/7ac42372-3605-44a4-bae4-4dee7af1a2f8/DispH_5kv27nov20_Snirh_shp.zip", "data": "2020-11",
            "licenca": "reprodução permitida com citação da fonte (metadados do SNIRH/ANA)"},
    "ne": {"titulo": "Natural Earth 1:10 milhões: países, fronteiras, estados e departamentos",
           "url": "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/", "data": "2022", "licenca": "domínio público"},
}
PAISES = {"BRA"}
SEM_ESTADO = set()

# Rios: (nome mostrado, expressão regular do nome na base da ANA, caixa lon0, lat0, lon1, lat1). A caixa contém o ponto médio de cada trecho do rio
# certo (há homônimos em outras regiões). Os nomes na base têm acentos corrompidos, por isso as expressões usam ".{0,3}" onde há acento.
RIOS = [
    ("Rio São Francisco", r"Rio S.{0,3}o Francisco", (-46.0, -17.5, -35.0, -8.0)),
    ("Rio Parnaíba", r"Rio Parna(.{0,3}ba)?", (-46.0, -9.5, -41.0, -2.5)),
    ("Rio Gurguéia", r"Rio Gurgu.{0,3}ia", (-46.0, -10.5, -43.0, -6.5)),
    ("Rio Poti", r"Rio Poti", (-43.0, -6.5, -40.0, -4.5)),
    ("Rio Canindé", r"Rio Canind.{0,3}", (-43.0, -8.5, -39.0, -3.5)),
    ("Rio Acaraú", r"Rio Acara.{0,3}", (-41.0, -5.2, -39.9, -2.8)),
    ("Rio Curu", r"Rio Curu", (-40.0, -4.7, -39.0, -3.3)),
    ("Rio Jaguaribe", r"Rio Jaguaribe", (-41.0, -7.0, -37.5, -4.0)),
    ("Rio Banabuiú", r"Rio Banabui.{0,3}", (-40.5, -6.0, -38.0, -5.0)),
    ("Rio Quixeramobim", r"Rio Quixeramobim", (-40.0, -5.7, -38.8, -5.0)),
    ("Rio Salgado (CE)", r"Rio Salgado", (-39.9, -7.6, -38.4, -6.0)),
    ("Rio Apodi", r"Rio Apodi", (-39.0, -6.6, -36.5, -4.6)),
    ("Rio Piranhas-Açu", r"Rio Piranhas( ou A.{0,3}u)?", (-39.0, -7.6, -36.0, -5.0)),
    ("Rio Piancó", r"Rio Pianc.{0,3}", (-39.0, -7.8, -37.5, -6.5)),
    ("Rio Seridó", r"Rio Serid.{0,3}", (-37.5, -7.0, -36.0, -6.0)),
    ("Rio Paraíba", r"Rio Para(.{1,3}ba)?", (-37.7, -8.2, -34.8, -6.8)),
    ("Rio Capibaribe", r"Rio Capibaribe", (-37.0, -8.5, -34.8, -7.7)),
    ("Rio Ipanema", r"Rio Ipanema", (-37.5, -9.9, -36.5, -8.3)),
    ("Rio Moxotó", r"Rio Moxot.{0,3}", (-38.2, -9.3, -37.0, -8.0)),
    ("Rio Pajeú", r"Rio Paje.{0,3}", (-39.0, -8.9, -37.0, -7.3)),
    ("Rio Vaza-Barris", r"Rio Vaza.?Barris", (-39.8, -11.0, -37.3, -9.7)),
    ("Rio Itapicuru (BA)", r"Rio Itapicuru", (-41.0, -12.5, -37.3, -9.5)),
    ("Rio Paraguaçu", r"Rio Paragua.{0,3}u", (-42.0, -13.8, -38.5, -12.2)),
    ("Rio de Contas", r"Rio de Contas", (-42.0, -14.5, -38.9, -13.0)),
]
CLASSES = {"perene": "Sem vazão nula estimada (Q95 > 0)", "parcial": "Vazão nula em parte do curso", "seca": "Vazão nula em quase todo o curso"}


def ler_ana(base, regras, caixa):
    """Lê da base da ANA só os trechos dos rios das `regras` cujo ponto médio cai na caixa do rio. Devolve {nome mostrado: [(linha, q95, fonte)]}."""
    cpl = [(n, re.compile(r"^" + rx + r"$"), b) for n, rx, b in regras]
    with open(base + ".dbf", "rb") as fd, open(base + ".shp", "rb") as fs, open(base + ".shx", "rb") as fx:
        d, s, x = (mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) for f in (fd, fs, fx))
        n, hl, rl = struct.unpack("<IHH", d[4:12])
        campos, o, off = {}, 32, 1
        while d[o] != 0x0D:
            campos[d[o:o + 11].split(b"\0")[0].decode()] = (off, d[o + 16]); off += d[o + 16]; o += 32
        cam = lambda i, k: d[hl + i * rl + campos[k][0]: hl + i * rl + campos[k][0] + campos[k][1]].replace(b"\0", b"").strip()
        fonte = lambda b: (lambda t: t.encode("latin-1").decode("utf-8") if t.isascii() is False and "Ã" in t else t)(b.decode("utf-8", "replace"))
        out = {}
        for i in range(n):
            nome = cam(i, "noriocomp").decode("utf-8", "replace")
            regs = [(m, b) for m, rx, b in cpl if rx.match(nome)]
            if not regs: continue
            of = struct.unpack(">i", x[100 + 8 * i: 104 + 8 * i])[0] * 2
            if struct.unpack("<i", s[of + 8: of + 12])[0] != 3: continue
            np_, npt = struct.unpack("<ii", s[of + 8 + 36: of + 8 + 44])
            p0 = of + 8 + 44
            parts = list(struct.unpack("<%di" % np_, s[p0: p0 + 4 * np_])) + [npt]
            pts = struct.unpack("<%dd" % (2 * npt), s[p0 + 4 * np_: p0 + 4 * np_ + 16 * npt])
            pts = [(pts[2 * j], pts[2 * j + 1]) for j in range(npt)]
            linhas = [pts[parts[j]:parts[j + 1]] for j in range(np_)]
            for m, b in regs:
                md = linhas[0][len(linhas[0]) // 2]
                if b[0] <= md[0] <= b[2] and b[1] <= md[1] <= b[3]:
                    out.setdefault(m, []).append((linhas, float(cam(i, "Q95NAT") or -1), fonte(cam(i, "FONTEQ95"))))
        return out


def centro(rings, bbox, n=24):
    """Rótulo no ponto do trecho visível mais distante das bordas (polo de inacessibilidade, busca em grade)."""
    r = max(rings, key=len); r = list(r) + [r[0]] if r[0] != r[-1] else list(r)
    vx = [p[0] for p in r if bbox[0] < p[0] < bbox[2]] or [p[0] for p in r]; vy = [p[1] for p in r if bbox[1] < p[1] < bbox[3]] or [p[1] for p in r]
    x0, x1, y0, y1 = max(bbox[0], min(vx)), min(bbox[2], max(vx)), max(bbox[1], min(vy)), min(bbox[3], max(vy))
    melhor, pt = -1, ((x0 + x1) / 2, (y0 + y1) / 2)
    for i in range(1, n):
        for j in range(1, n):
            p = (x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * j / n)
            if inside(p, r):
                d = dist_borda(p, r)
                if d > melhor: melhor, pt = d, p
    return [round(pt[0], 3), round(pt[1], 3)]


def km(linhas):
    return sum(math.hypot((q[0] - p[0]) * .95, q[1] - p[1]) * 111 for l in linhas for p, q in zip(l, l[1:]))


def receita(raw):
    ibge = [r for a, g in shp.read(f"{raw}/biomas/lml_bioma_e250k_v20250911_A") if a["NM_BIOMA"] == "Caatinga" for r in g]
    xs, ys = [p[0] for r in ibge for p in r], [p[1] for r in ibge for p in r]
    reg = (min(xs), min(ys), max(xs), max(ys))
    P = .6
    bbox = (reg[0] - P, reg[1] - P, reg[2] + P, reg[3] + P); box = (bbox[0] - .3, bbox[1] - .3, bbox[2] + .3, bbox[3] + .3)
    dx, dy = (bbox[2] - bbox[0]) * .05 + .2, (bbox[3] - bbox[1]) * .05 + .2
    vbox = (bbox[0] - dx, bbox[1] - dy, bbox[2] + dx, bbox[3] + dy)   # a terra é recortada numa caixa maior que a moldura (sem faixas vazias)
    limite = [r3(q) for q in (dp_ring(list(r), .03) for r in ibge) if q]
    camadas = []

    # ---- países, fronteiras, estados (estados do Brasil em cores diferentes)
    paises, estados = [], []
    for a, gm in shp.read(f"{raw}/ne_10m_admin_0_countries/ne_10m_admin_0_countries", vbox):
        if a["ADM0_A3"] not in PAISES: continue
        rings = [q for q in (recorta_anel(r, vbox) for r in gm) if q]
        rings = [q for q in (dp_ring(r + [r[0]], .03) for r in rings) if q]
        if rings: paises.append({"nome": a["NAME_PT"], "rings": [r3(r) for r in rings], "rotulo": centro(rings, bbox)})
    fronteiras = [r3(dp(l, .03)) for a, gm in shp.read(f"{raw}/ne_10m_admin_0_boundary_lines_land/ne_10m_admin_0_boundary_lines_land", vbox) for ln in gm for l in corta_linha(ln, vbox)]
    camadas.append({"id": "paises", "titulo": "Fronteiras entre países", "tipo": "contexto", "fonte": "ne", "ligada": True,
                    "nota": "O território do Brasil com seu nome; as fronteiras vêm do Natural Earth (escala 1:10 milhões) e podem divergir em detalhe dos limites oficiais.",
                    "itens": paises, "fronteiras": fronteiras})
    for a, gm in shp.read(f"{raw}/ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces", vbox):
        if a["adm0_a3"] not in PAISES or a["name"] in SEM_ESTADO: continue
        if not any(recorta_anel(r, box) for r in gm): continue
        rings = [q for q in (recorta_anel(r, vbox) for r in gm) if q]
        if not rings: continue
        e = {"nome": a["name"], "lns": [l for r in gm for l in corta_linha([tuple(p) for p in r], vbox)], "rotulo": centro(rings, bbox)}
        e["rings"] = [r3(q) for q in (dp_ring(list(r) + [r[0]], .03) for r in rings) if q]
        e["vert"] = {(round(p[0], 2), round(p[1], 2)) for r in gm for p in r}
        estados.append(e)
    viz = {i: {j for j, f in enumerate(estados) if j != i and len(e["vert"] & f["vert"]) >= 2} for i, e in enumerate(estados)}
    cor = {}
    for i in sorted(viz, key=lambda i: -len(viz[i])):   # coloração gulosa: estados vizinhos nunca repetem cor (6 cores)
        usadas = {cor[j] for j in viz[i] if j in cor}; cor[i] = next(c for c in range(6) if c not in usadas)
    for i, e in enumerate(estados): e["cor"] = cor[i]
    camadas.append({"id": "estados", "titulo": "Estados", "tipo": "contexto", "fonte": "ne", "ligada": True,
                    "nota": "Estados do Brasil em cores diferentes (Natural Earth 1:10 milhões); o bioma é sempre de uma cor só.",
                    "itens": [{"nome": e["nome"], "rotulo": e["rotulo"], "rings": e["rings"], "cor": e["cor"]} for e in estados],
                    "fronteiras": [r3(dp(l, .03)) for e in estados for l in e["lns"]]})

    # ---- rios (ANA): trechos por rio, classificados pela fração do curso com Q95 natural nula
    achados = ler_ana(f"{raw}/anadisp/DispH_v27nov20_Snirh", RIOS, vbox)
    m_uf = {e["nome"]: Mascara([[tuple(q) for q in r_] for r_ in e["rings"]], vbox, .02) for e in estados}
    def onde(ls, mascaras):
        pts = [p for l in ls for p in l[::max(1, len(l) // 40)]]
        return [n for n, m in mascaras.items() if sum(m(*p) for p in pts) >= max(2, .04 * len(pts))]   # ignora toques de uma ponta só
    lista = lambda xs: xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " e " + xs[-1]
    rios = []
    for nome, trechos in achados.items():
        ls, secos, total, fontes = [], 0.0, 0.0, {}
        for linhas, q95, fonte in trechos:
            kmt = km(linhas); total += kmt
            if q95 == 0: secos += kmt
            fontes[fonte] = fontes.get(fonte, 0) + kmt
            for l in linhas:
                for parte in corta_linha(l, vbox, 0): ls.append(dp(parte, .015))   # só o que aparece na moldura
        if not ls: continue
        pct = round(100 * secos / total) if total else 0
        classe = "perene" if pct < 10 else "parcial" if pct < 90 else "seca"
        estados_rio = sorted(onde(ls, m_uf)); fonte_q = max(fontes, key=fontes.get)
        texto = (f"{nome} — {CLASSES[classe][0].lower() + CLASSES[classe][1:]}: a vazão natural estimada é nula (Q95 = 0) em {pct}% do curso mostrado (≈{round(total)} km). "
                 f"Estados: {lista(estados_rio) if estados_rio else 'não identificado'}. Fonte do dado de vazão: {fonte_q}.")
        rios.append({"nome": nome, "km": round(total), "linhas": [r3(l) for l in ls], "texto": texto, "paises": ["Brasil"], "estados": estados_rio,
                     "pct_seco": pct, "classe": CLASSES[classe], "fonte_q": fonte_q, "attrs": {"regime": classe}})
    rios.sort(key=lambda r_: -r_["km"])
    for r_ in rios[:20]:   # rótulos: os 20 maiores, no meio do maior trecho
        ls = max((l for l in [[tuple(p) for p in l] for l in r_["linhas"]]), key=len); m = ls[len(ls) // 2]; r_["rotulo"] = [round(m[0], 3), round(m[1], 3)]
    camadas.append({"id": "rios", "titulo": "Rios da Caatinga", "tipo": "linha", "fonte": "ana", "ligada": True, "por_rio": True, "lista": True, "lista_titulo": "Rios",
                    "nota": "Os principais rios do bioma, da Disponibilidade Hídrica Superficial da ANA. Cada rio é classificado pela fração do curso mostrado em que a vazão natural estimada é nula em 5% do tempo ou mais (Q95 = 0): sem vazão nula estimada (menos de 10% do curso), vazão nula em parte do curso (10% a 90%) e vazão nula em quase todo o curso (90% ou mais). É uma estimativa regionalizada de vazão natural, não uma observação: \"sem vazão nula estimada\" não quer dizer que o rio nunca seque (a ausência de zero depende do estudo regional que cobriu o rio), e muitos rios que secam na natureza correm o ano todo hoje porque têm açudes e barragens a montante. Toque num rio para ver os dados dele.",
                    "itens": rios})
    filtros = [{"id": "regime", "titulo": "Regime", "camada": "rios", "campo": "regime", "opcoes": [["", "Todos os rios"]] + [[k, v] for k, v in CLASSES.items() if any(r_["attrs"]["regime"] == k for r_ in rios)]}]
    return {"id": "caatinga", "oceano": True, "titulo": "Os rios que secam na Caatinga",
            "aviso_escopo": "Este mapa trata só dos principais rios do bioma e de quanto do curso de cada um fica sem vazão natural. O limite do bioma é o oficial do IBGE (a Caatinga existe só no Brasil).",
            "bbox": [round(v, 3) for v in bbox], "limite": limite, "limite_nome": "Caatinga (IBGE 2025)",
            "camadas": camadas, "filtros": filtros,
            "lacunas": ["Cidades, unidades de conservação, açudes e caatinga remanescente: não incluídos por escolha do projeto; este mapa é só sobre os rios que secam.",
                        f"Os rios são uma seleção dos principais ({len(rios)}), não toda a rede de drenagem do bioma.",
                        "A classificação vem da vazão natural estimada pela ANA (regionalização, 2020), que combina estudos de várias fontes por região; não é medição direta nem leva em conta açudes e barragens. Não existe base oficial aberta que classifique cada rio como perene ou intermitente; o campo de regime da base do IBGE (BC250) marca 97% dos trechos como permanentes e por isso não foi usado.",
                        "Rios da Bahia (de Contas, Paraguaçu, Itapicuru, Vaza-Barris) saem na classe \"sem vazão nula estimada\" porque o estudo regional que os cobre (PNRH 2012) não traz zeros; isso não prova que correm o ano todo: a foto aérea desta página mostra o Rio de Contas parcialmente seco. Os percentuais são quase sempre 0% ou 100% por rio porque acompanham o estudo de origem de cada região.",
                        "A base da ANA tem acentos corrompidos nos nomes dos rios; os nomes mostrados foram escritos à mão e os trechos foram achados por nome mais caixa de coordenadas."],
            "fontes": FONTES}
