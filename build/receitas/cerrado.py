"""Receita do mapa temático do CERRADO: um mapa só sobre os rios que nascem ou correm pelo Cerrado ("berço das águas") e as bacias hidrográficas
para onde vão (decisão do projeto: sem cidades, UCs nem outras camadas). Lê as bases já descompactadas e devolve o dicionário de data/mapas/cerrado.json.

Pasta de entrada (`raw`):
  resolve_ce/cerrado.json   RESOLVE Ecoregions 2017, ecorregião "Cerrado" (ECO_ID 567; GeoJSON do FeatureServer, maxAllowableOffset=0.02)
  biomas/                   IBGE, Biomas 1:250 000 (2025)           lml_bioma_e250k_v20250911_A.*   (limite oficial)
  bc250/                    IBGE, BC250 versão 2025                 hid_trecho_drenagem_l.{shp,shx,dbf,cpg}  (rios nomeados)
  ne_10m_admin_0_countries/, ne_10m_admin_0_boundary_lines_land/, ne_10m_admin_1_states_provinces/   Natural Earth 1:10m (domínio público)

O Cerrado é quase todo brasileiro: a ecorregião RESOLVE só passa ~2° do limite do IBGE (franjas da Bolívia e do Paraguai).
"""
import json, math, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import shp
from mapas_dados import dp, dp_ring, inside, dist_borda, r3, recorta_anel, corta_linha, Mascara

PUB = "dado público do IBGE (termo de licença não localizado)"
FONTES = {
    "resolve": {"titulo": "RESOLVE Ecoregions 2017 (Dinerstein et al., 2017, BioScience), ecorregião Cerrado: limite do bioma, com as franjas na Bolívia e no Paraguai",
                "url": "https://ecoregions.appspot.com/", "data": "2017", "licenca": "CC BY 4.0"},
    "biomas": {"titulo": "IBGE, Biomas e Sistema Costeiro-Marinho do Brasil 1:250 000 (2025): limite oficial do Cerrado",
               "url": "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/vetores/2025_Biomas-e-Sistema-Costeiro-Marinho-do-Brasil-1-250000_shp.zip", "data": "2025-09", "licenca": PUB},
    "bc250": {"titulo": "IBGE, Base Cartográfica Contínua do Brasil 1:250 000 (BC250), versão 2025: trechos de drenagem nomeados",
              "url": "https://geoftp.ibge.gov.br/cartas_e_mapas/bases_cartograficas_continuas/bc250/versao2025/shapefiles/bc_250_shapefiles_2026_03_03.zip", "data": "2026-03", "licenca": PUB},
    "ne": {"titulo": "Natural Earth 1:10 milhões: países, fronteiras, estados e departamentos",
           "url": "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/", "data": "2022", "licenca": "domínio público"},
}
PAISES = {"BRA", "BOL", "PRY", "ARG"}   # a moldura pega a costa de SP/RJ (oceano) e um canto da Argentina
SEM_ESTADO = set()

# Rios do Cerrado (IBGE BC250), por nome: (nome mostrado, bacia hidrográfica, caixa lon0, lat0, lon1, lat1). O nome sozinho não basta (há "Rio Grande",
# "Rio das Mortes"… em outras bacias): cada rio só vale dentro da caixa que cobre o curso real. A bacia vem do conhecimento geral (região hidrográfica
# de cada rio); as caixas foram conferidas contra a extensão encontrada na base.
BACIAS = ["São Francisco", "Tocantins-Araguaia", "Paraná", "Parnaíba", "Paraguai", "Amazônica"]
RIOS = {
    "Rio São Francisco": ("Rio São Francisco", "São Francisco", (-47.8, -21.0, -39.0, -8.5)), "Rio das Velhas": ("Rio das Velhas", "São Francisco", (-44.6, -20.4, -43.5, -17.2)),
    "Rio Paracatu": ("Rio Paracatu", "São Francisco", (-47.6, -17.8, -45.0, -16.0)), "Rio Urucuia": ("Rio Urucuia", "São Francisco", (-46.8, -17.9, -45.2, -15.6)),
    "Rio Carinhanha": ("Rio Carinhanha", "São Francisco", (-45.4, -15.6, -43.5, -13.4)), "Rio Paraopeba": ("Rio Paraopeba", "São Francisco", (-45.3, -20.9, -44.0, -18.2)),
    "Rio Tocantins": ("Rio Tocantins", "Tocantins-Araguaia", (-50.6, -15.2, -47.0, -5.0)), "Rio Araguaia": ("Rio Araguaia", "Tocantins-Araguaia", (-53.9, -18.3, -48.0, -5.0)),
    "Rio Paranã": ("Rio Paranã", "Tocantins-Araguaia", (-48.0, -15.2, -46.0, -12.4)), "Rio do Sono": ("Rio do Sono", "Tocantins-Araguaia", (-48.2, -11.8, -46.4, -8.4)),
    "Rio das Mortes": ("Rio das Mortes", "Tocantins-Araguaia", (-54.9, -16.5, -50.4, -11.5)), "Rio das Almas": ("Rio das Almas", "Tocantins-Araguaia", (-49.6, -15.6, -48.4, -14.4)),
    "Rio Paranaíba": ("Rio Paranaíba", "Paraná", (-51.0, -20.2, -45.8, -17.5)), "Rio Paraná": ("Rio Paraná", "Paraná", (-54.9, -24.3, -49.9, -19.4)),
    "Rio Corumbá": ("Rio Corumbá", "Paraná", (-49.0, -18.5, -48.0, -16.0)),
    "Rio Parnaíba": ("Rio Parnaíba", "Parnaíba", (-46.0, -11.0, -41.0, -4.0)),
    "Rio Paraguai": ("Rio Paraguai", "Paraguai", (-58.4, -17.2, -56.2, -13.4)), "Rio Cuiabá": ("Rio Cuiabá", "Paraguai", (-56.6, -16.6, -53.9, -14.0)),
    "Rio Xingu": ("Rio Xingu", "Amazônica", (-53.9, -13.2, -51.3, -8.0)), "Rio Teles Pires": ("Rio Teles Pires", "Amazônica", (-56.4, -14.2, -54.9, -9.5)), "Rio Juruena": ("Rio Juruena", "Amazônica", (-59.5, -15.2, -57.7, -10.5)),
}
# "Rio Grande" existe em duas bacias do Cerrado (e em outras regiões): duas caixas, dois nomes mostrados
RIO_GRANDE = [("Rio Grande (BA)", "São Francisco", (-46.6, -13.6, -43.0, -11.6)), ("Rio Grande (MG/SP)", "Paraná", (-51.0, -22.5, -44.0, -19.4))]


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
    # ---- a região: ecorregião RESOLVE "Cerrado" + limite oficial do IBGE por cima
    g = json.load(open(f"{raw}/resolve_ce/cerrado.json", encoding="utf-8"))["features"][0]["geometry"]
    polis = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    res_aneis = [[tuple(p) for p in pol[0]] for pol in polis]
    xs, ys = [p[0] for r in res_aneis for p in r], [p[1] for r in res_aneis for p in r]
    reg = (min(xs), min(ys), max(xs), max(ys))
    ibge = [r for a, g in shp.read(f"{raw}/biomas/lml_bioma_e250k_v20250911_A") if a["NM_BIOMA"] == "Cerrado" for r in g]
    P = .6
    bbox = (reg[0] - P, reg[1] - P, reg[2] + P, reg[3] + P); box = (bbox[0] - .3, bbox[1] - .3, bbox[2] + .3, bbox[3] + .3)
    dx, dy = (bbox[2] - bbox[0]) * .05 + .2, (bbox[3] - bbox[1]) * .05 + .2
    vbox = (bbox[0] - dx, bbox[1] - dy, bbox[2] + dx, bbox[3] + dy)   # a terra é recortada numa caixa maior que a moldura (sem faixas vazias)
    limite = [r3(q) for q in (dp_ring(list(r), .03) for r in res_aneis) if q]
    oficial = [r3(q) for q in (dp_ring(list(r), .04) for r in ibge) if q]
    camadas = []

    # ---- países, fronteiras, estados e departamentos (estados do Brasil em cores diferentes)
    paises, estados = [], []
    for a, gm in shp.read(f"{raw}/ne_10m_admin_0_countries/ne_10m_admin_0_countries", vbox):
        if a["ADM0_A3"] not in PAISES: continue
        rings = [q for q in (recorta_anel(r, vbox) for r in gm) if q]
        rings = [q for q in (dp_ring(r + [r[0]], .03) for r in rings) if q]
        if rings: paises.append({"nome": a["NAME_PT"], "rings": [r3(r) for r in rings], "rotulo": centro(rings, bbox)})
    fronteiras = [r3(dp(l, .03)) for a, gm in shp.read(f"{raw}/ne_10m_admin_0_boundary_lines_land/ne_10m_admin_0_boundary_lines_land", vbox) for ln in gm for l in corta_linha(ln, vbox)]
    camadas.append({"id": "paises", "titulo": "Fronteiras entre países", "tipo": "contexto", "fonte": "ne", "ligada": True,
                    "nota": "Países vizinhos com seu nome e uma cor para cada um; as fronteiras vêm do Natural Earth (escala 1:10 milhões) e podem divergir em detalhe dos limites oficiais.",
                    "itens": paises, "fronteiras": fronteiras})
    for a, gm in shp.read(f"{raw}/ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces", vbox):
        if a["adm0_a3"] not in PAISES or a["name"] in SEM_ESTADO: continue
        if not any(recorta_anel(r, box) for r in gm): continue
        rings = [q for q in (recorta_anel(r, vbox) for r in gm) if q]
        if not rings: continue
        e = {"nome": a["name"], "lns": [l for r in gm for l in corta_linha([tuple(p) for p in r], vbox)], "rotulo": centro(rings, bbox)}
        if a["adm0_a3"] == "BRA":
            e["rings"] = [r3(q) for q in (dp_ring(list(r) + [r[0]], .03) for r in rings) if q]
            e["vert"] = {(round(p[0], 2), round(p[1], 2)) for r in gm for p in r}
        estados.append(e)
    br = [e for e in estados if "vert" in e]
    viz = {i: {j for j, f in enumerate(br) if j != i and len(e["vert"] & f["vert"]) >= 2} for i, e in enumerate(br)}
    cor = {}
    for i in sorted(viz, key=lambda i: -len(viz[i])):   # coloração gulosa: estados vizinhos nunca repetem cor (6 cores)
        usadas = {cor[j] for j in viz[i] if j in cor}; cor[i] = next(c for c in range(6) if c not in usadas)
    for i, e in enumerate(br): e["cor"] = cor[i]
    camadas.append({"id": "estados", "titulo": "Estados e departamentos", "tipo": "contexto", "fonte": "ne", "ligada": True,
                    "nota": "Divisas internas dos países (estados no Brasil, departamentos nos vizinhos), Natural Earth 1:10 milhões. Os estados do Brasil são pintados em cores diferentes; o bioma é sempre de uma cor só.",
                    "itens": [{"nome": e["nome"], "rotulo": e["rotulo"], **({"rings": e["rings"], "cor": e["cor"]} if "rings" in e else {})} for e in estados],
                    "fronteiras": [r3(dp(l, .03)) for e in estados for l in e["lns"]]})

    # ---- rios (drenagem do IBGE, pelo nome, dentro da caixa de cada rio; só o trecho que cai na moldura do mapa)
    candidatos = {nome: [(mostrado, bacia, caixa)] for nome, (mostrado, bacia, caixa) in RIOS.items()}
    candidatos["Rio Grande"] = RIO_GRANDE and [(m, b, c) for m, b, c in RIO_GRANDE]
    achados, bacia_de = {}, {}
    for a, gm in shp.read_por_nome(f"{raw}/bc250/hid_trecho_drenagem_l", "nome", set(candidatos)):
        for mostrado, bacia, b in candidatos[a["nome"]]:
            for l in gm:
                m = l[len(l) // 2]
                if len(l) > 1 and b[0] <= m[0] <= b[2] and b[1] <= m[1] <= b[3]:
                    for parte in corta_linha(l, vbox, 0):   # só o que aparece na moldura
                        achados.setdefault(mostrado, []).append(dp(parte, .02)); bacia_de[mostrado] = bacia
    m_pais = {p["nome"]: Mascara([[tuple(q) for q in r_] for r_ in p["rings"]], vbox, .02) for p in paises}
    m_uf = {e["nome"]: Mascara([[tuple(q) for q in r_] for r_ in e["rings"]], vbox, .02) for e in estados if "rings" in e}
    def onde(ls, mascaras):
        pts = [p for l in ls for p in l[::max(1, len(l) // 40)]]
        return [n for n, m in mascaras.items() if sum(m(*p) for p in pts) >= max(2, .04 * len(pts))]   # ignora toques de uma ponta só
    lista = lambda xs: xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " e " + xs[-1]
    rios = []
    for nome, ls in achados.items():
        paises_rio = sorted(onde(ls, m_pais), key=lambda n: (n != "Brasil", n)); estados_rio = sorted(onde(ls, m_uf)); bacia = bacia_de[nome]
        texto = f"{nome} — bacia {bacia}. Passa por: {lista(paises_rio) if paises_rio else 'não identificado'}." + (f" Estados do Brasil: {lista(estados_rio)}." if estados_rio else "")
        rios.append({"nome": nome, "km": round(km(ls)), "linhas": [r3(l) for l in ls], "texto": texto, "paises": paises_rio, "estados": estados_rio, "attrs": {"bacia": bacia}})
    rios.sort(key=lambda r_: -r_["km"])
    for r_ in rios[:18]:   # rótulos: os 18 maiores, no meio do maior trecho
        ls = max((l for l in [[tuple(p) for p in l] for l in r_["linhas"]]), key=len); m = ls[len(ls) // 2]; r_["rotulo"] = [round(m[0], 3), round(m[1], 3)]
    camadas.append({"id": "rios", "titulo": "Rios do Cerrado", "tipo": "linha", "fonte": "bc250", "ligada": True, "por_rio": True, "lista": True, "lista_titulo": "Rios",
                    "nota": "Os principais rios que nascem ou correm pelo Cerrado (\"berço das águas\"), da drenagem do IBGE, só no trecho que aparece no mapa. O filtro separa os rios pela bacia hidrográfica (grande região hidrográfica) para onde correm; a bacia de cada rio vem do conhecimento geral, e as caixas de coordenadas que isolam cada rio (há homônimos em outras regiões) foram conferidas contra a base. Toque num rio para ver por quais países e estados ele passa (limites do Natural Earth, aproximados).",
                    "itens": rios})
    presentes = [b for b in BACIAS if any(r_["attrs"]["bacia"] == b for r_ in rios)]
    filtros = [{"id": "bacia", "titulo": "Bacia hidrográfica", "camada": "rios", "campo": "bacia", "opcoes": [["", "Todas as bacias"]] + [[b, b] for b in presentes]}]
    return {"id": "cerrado", "oceano": True, "secao_titulo": "Rios e bacias do Cerrado", "titulo": "Rios e bacias do Cerrado, o berço das águas",
            "aviso_escopo": "Este mapa trata só dos principais rios que nascem ou correm pelo Cerrado e das bacias para onde vão. O limite do bioma é a ecorregião RESOLVE com o limite oficial do IBGE por cima; os dois vêm de bases diferentes e não coincidem exatamente.",
            "bbox": [round(v, 3) for v in bbox], "limite": limite, "limite_nome": "Cerrado (ecorregião, RESOLVE 2017)",
            "limite_oficial": oficial, "limite_oficial_nome": "Limite oficial (IBGE 2025)",
            "camadas": camadas, "filtros": filtros,
            "lacunas": ["Cidades, unidades de conservação, desmatamento, fogo e aquíferos: não incluídos por escolha do projeto; este mapa é só sobre os principais rios e as bacias.",
                        "Os rios são uma seleção dos principais (24), não toda a rede de drenagem do bioma; as nascentes não estão marcadas.",
                        "Franjas do Cerrado na Bolívia e no Paraguai: só o limite (as camadas detalhadas são do Brasil)."],
            "fontes": FONTES}
