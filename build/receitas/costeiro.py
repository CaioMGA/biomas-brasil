"""Receita do mapa temático do SISTEMA COSTEIRO-MARINHO: manguezais, recifes e ilhas (decisão do projeto, 2026-11-03: "mangues, recifes e ilhas").
Lê as bases já descompactadas e devolve o dicionário de data/mapas/costeiro.json.

Pasta de entrada (`raw`):
  gmw/gmw_v3_2020_vec.*     Global Mangrove Watch v3.0, extensão de manguezais em 2020 (Bunting et al., 2022; Zenodo 6894273; CC BY 4.0; shapefile global de ~900 MB)
  bc250/                    IBGE, BC250 versão 2025: hid_recife_a.* (recifes) e hid_ilha_a.* (ilhas; campo `tipoilha`)
  ne_10m_admin_0_countries/, ne_10m_admin_1_states_provinces/   Natural Earth 1:10m (domínio público)
Além disso, o limite do sistema vem de data/biomes_2019_simplified.gpkg (IBGE, Biomas 2019, via geobr/Ipea), que já está no repositório.

Escolhas e limites (também escritos em `lacunas`):
- Manguezais: só os que caem dentro do Brasil (máscara do Natural Earth); polígonos menores que ~1 km de lado são descartados para o arquivo não crescer (a área somada antes e depois do corte
  está na nota da camada).
- Ilhas: só as de `tipoilha` = "Marítima" no BC250 (a classificação do IBGE inclui ilhas do estuário do Amazonas, como Marajó), com nome e ao menos 40 km² (somando as peças do mesmo nome),
  mais as ilhas e arquipélagos oceânicos de qualquer tamanho.
"""
import json, math, os, re, sqlite3, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import shp
from mapas_dados import dp, dp_ring, r3, recorta_anel, corta_linha, Mascara
from receitas.pampa import centro   # rótulo no ponto mais interno do trecho visível

PUB = "dado público do IBGE (termo de licença não localizado)"
FONTES = {
    "geobr": {"titulo": "IBGE, Biomas e Sistema Costeiro-Marinho do Brasil, edição 2019 (via pacote geobr/Ipea): limite do Sistema Costeiro-Marinho",
              "url": "https://github.com/ipeaGIT/geobr", "data": "2019", "licenca": PUB},
    "gmw": {"titulo": "Global Mangrove Watch, versão 3.0 (Bunting et al., 2022, Remote Sensing 14(15):3657): extensão dos manguezais em 2020",
            "url": "https://zenodo.org/records/6894273", "data": "2020", "licenca": "CC BY 4.0"},
    "bc250": {"titulo": "IBGE, Base Cartográfica Contínua do Brasil 1:250 000 (BC250), versão 2025: recifes e ilhas",
              "url": "https://geoftp.ibge.gov.br/cartas_e_mapas/bases_cartograficas_continuas/bc250/versao2025/shapefiles/bc_250_shapefiles_2026_03_03.zip", "data": "2026-03", "licenca": PUB},
    "ne": {"titulo": "Natural Earth 1:10 milhões: países, fronteiras e estados",
           "url": "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/", "data": "2022", "licenca": "domínio público"},
}
PAISES = {"BRA", "URY", "ARG", "PRY", "BOL", "PER", "COL", "VEN", "GUY", "SUR"}
OCEANICAS = re.compile(r"fernando de noronha|atol das rocas|trindade|martin vaz|martim vaz|ilha do norte|são pedro e são paulo", re.I)   # ilhas e arquipélagos oceânicos
MIN_ILHA_KM2 = 40
MIN_MANGUE = .008   # graus (~900 m): menor lado do envelope abaixo disso é descartado
EPS_MANGUE = .004


def limite_costeiro(root):
    """Polígono do Sistema Costeiro-Marinho (anéis externos) do GeoPackage do repositório."""
    c = sqlite3.connect(os.path.join(root, "data", "biomes_2019_simplified.gpkg"))
    b = c.execute("select geom from biomes_2019_simplified where name_biome = 'Sistema Costeiro'").fetchone()[0]
    env = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(b[3] >> 1) & 7]; w = b[8 + env:]

    def wkb(o):
        bo = "<" if w[o] == 1 else ">"; t = struct.unpack_from(bo + "I", w, o + 1)[0] & 0xFFFF; o += 5; polys = []
        if t == 3:
            n = struct.unpack_from(bo + "I", w, o)[0]; o += 4; rings = []
            for _ in range(n):
                m = struct.unpack_from(bo + "I", w, o)[0]; o += 4
                pts = struct.unpack_from(bo + "%dd" % (2 * m), w, o); o += 16 * m
                rings.append([(pts[i], pts[i + 1]) for i in range(0, 2 * m, 2)])
            return [rings], o
        n = struct.unpack_from(bo + "I", w, o)[0]; o += 4
        for _ in range(n):
            p, o = wkb(o); polys += p
        return polys, o
    polys, _ = wkb(0)
    return [p[0] for p in polys]   # só o anel externo de cada parte


milhar = lambda n: f"{round(n):,}".replace(",", ".")


def area_km2(rings):
    """Área líquida aproximada (shoelace com sinal: anel externo horário menos buracos anti-horários; graus → km², com cos da latitude média)."""
    lat = sum(p[1] for r in rings for p in r) / sum(len(r) for r in rings); k = 111.32; s = 0
    for r in rings: s += sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r)))
    return abs(s) / 2 * k * k * math.cos(math.radians(lat))


def receita(raw):
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    aneis = limite_costeiro(root)
    xs, ys = [p[0] for r in aneis for p in r], [p[1] for r in aneis for p in r]
    # as ilhas oceânicas (Trindade, Martim Vaz, São Pedro e São Paulo) ficam fora do limite do IBGE: a moldura cresce para incluí-las
    oce_pts = [g[0][0] for a, g in shp.read(f"{raw}/bc250/hid_ilha_a", (-34.5, -25, -20, 5)) if a["tipoilha"] == "Marítima" and OCEANICAS.search(a["nome"])]
    xs += [p[0] for p in oce_pts]; ys += [p[1] for p in oce_pts]
    reg = (min(xs), min(ys), max(xs), max(ys)); P = .6
    bbox = (reg[0] - P, reg[1] - P, reg[2] + P, reg[3] + P); box = (bbox[0] - .3, bbox[1] - .3, bbox[2] + .3, bbox[3] + .3)
    dx, dy = (bbox[2] - bbox[0]) * .05 + .2, (bbox[3] - bbox[1]) * .05 + .2
    vbox = (bbox[0] - dx, bbox[1] - dy, bbox[2] + dx, bbox[3] + dy)
    limite = [r3(q) for q in (dp_ring(list(r), .03) for r in aneis) if q]
    camadas = []

    # ---- países, fronteiras e estados (os do Brasil, em cores diferentes)
    paises, estados = [], []
    for a, gm in shp.read(f"{raw}/ne_10m_admin_0_countries/ne_10m_admin_0_countries", vbox):
        if a["ADM0_A3"] not in PAISES: continue
        rings = [q for q in (recorta_anel(r, vbox) for r in gm) if q]
        rings = [q for q in (dp_ring(r + [r[0]], .02) for r in rings) if q]
        if rings: paises.append({"nome": a["NAME_PT"], "rings": [r3(r) for r in rings], "rotulo": centro(rings, bbox)})
    fronteiras = [r3(dp(l, .02)) for a, gm in shp.read(f"{raw}/ne_10m_admin_0_boundary_lines_land/ne_10m_admin_0_boundary_lines_land", vbox) for ln in gm for l in corta_linha(ln, vbox)]
    camadas.append({"id": "paises", "titulo": "Fronteiras entre países", "tipo": "contexto", "fonte": "ne", "ligada": True,
                    "nota": "Países vizinhos, cada um com uma cor; as fronteiras vêm do Natural Earth (escala 1:10 milhões) e podem divergir em detalhe dos limites oficiais.",
                    "itens": paises, "fronteiras": fronteiras})
    for a, gm in shp.read(f"{raw}/ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces", vbox):
        if a["adm0_a3"] != "BRA": continue
        rings = [q for q in (recorta_anel(r, vbox) for r in gm) if q]
        if not rings: continue
        estados.append({"nome": a["name"], "lns": [l for r in gm for l in corta_linha([tuple(p) for p in r], vbox)], "rotulo": centro(rings, bbox),
                        "rings": [r3(q) for q in (dp_ring(list(r) + [r[0]], .02) for r in rings) if q], "vert": {(round(p[0], 2), round(p[1], 2)) for r in gm for p in r}})
    viz = {i: {j for j, f in enumerate(estados) if j != i and len(e["vert"] & f["vert"]) >= 2} for i, e in enumerate(estados)}
    cor = {}
    for i in sorted(viz, key=lambda i: -len(viz[i])):   # coloração gulosa: estados vizinhos nunca repetem cor (6 cores)
        usadas = {cor[j] for j in viz[i] if j in cor}; cor[i] = next(c for c in range(6) if c not in usadas)
    for i, e in enumerate(estados): e["cor"] = cor[i]
    camadas.append({"id": "estados", "titulo": "Estados do Brasil", "tipo": "contexto", "fonte": "ne", "ligada": True,
                    "nota": "Divisas dos estados (Natural Earth 1:10 milhões), em cores diferentes. O sistema costeiro-marinho é sempre de uma cor só.",
                    "itens": [{"nome": e["nome"], "rotulo": e["rotulo"], "rings": e["rings"], "cor": e["cor"]} for e in estados],
                    "fronteiras": [r3(dp(l, .02)) for e in estados for l in e["lns"]]})
    brasil = [[tuple(q) for q in r] for p in paises if p["nome"] == "Brasil" for r in p["rings"]]
    m_br = Mascara(brasil, vbox, .02)

    # ---- manguezais (GMW 2020): só dentro do Brasil, sem as manchas menores que ~1 km
    gm_all = shp.read(f"{raw}/gmw/gmw_v3_2020_vec", (box[0], box[1], box[2], box[3]))
    total = mantido = 0.0; rings_m = []
    for a, gm in gm_all:
        r = gm[0]; px = [p[0] for p in r]; py = [p[1] for p in r]
        if not m_br((min(px) + max(px)) / 2, (min(py) + max(py)) / 2): continue
        ar = area_km2(gm); total += ar
        if min(max(px) - min(px), max(py) - min(py)) < MIN_MANGUE: continue
        q = dp_ring(list(r), EPS_MANGUE)
        if q: rings_m.append(r3(q)); mantido += ar
    camadas.append({"id": "manguezais", "titulo": "Manguezais", "tipo": "cobertura", "fonte": "gmw", "ligada": True,
                    "nota": f"Extensão dos manguezais em 2020 (Global Mangrove Watch v3.0, mapeados por satélite com pixels de 25 m), só dentro do Brasil. Somados, os polígonos têm cerca de {milhar(total)} km²; "
                            f"o desenho mostra {milhar(len(rings_m))} manchas maiores que ~1 km de lado (cerca de {milhar(mantido)} km² dessa área), simplificadas; as menores foram descartadas para o mapa carregar rápido.",
                    "itens": [{"rings": [r]} for r in rings_m]})

    # ---- recifes (BC250): coral, rochoso e tipo desconhecido
    TIPO = {"Coral": "Coral", "Rochoso": "Rochoso"}
    recifes = []
    for a, gm in shp.read(f"{raw}/bc250/hid_recife_a", box):
        rings = [q for q in (dp_ring(r, .001) or (r[:-1] if r[0] == r[-1] else r) for r in gm) if q and len(q) >= 3]
        if rings: recifes.append({"nome": a["nome"], "tipo": TIPO.get(a["tiporecife"], "Tipo não informado"), "rings": [r3(q) for q in rings]})
    camadas.append({"id": "recifes", "titulo": "Recifes", "tipo": "poligono", "fonte": "bc250", "ligada": True,
                    "nota": f"{len(recifes)} polígonos de recifes da Base Cartográfica Contínua do IBGE (1:250 000): coral, rochoso ou de tipo não informado. É o que a base mapeia, não um inventário completo dos recifes brasileiros; os polígonos são pequenos e aparecem com contorno realçado.",
                    "itens": recifes})

    # ---- ilhas marítimas (BC250): nomeadas e com ao menos 40 km², mais as oceânicas
    por_nome = {}
    for a, gm in shp.read(f"{raw}/bc250/hid_ilha_a", box):
        if a["tipoilha"] != "Marítima" or not a["nome"]: continue
        oce = bool(OCEANICAS.search(a["nome"])) and gm[0][0][0] > -34.5   # "Ilha da Trindade" também é nome de ilha costeira do Maranhão: só vale a que está a leste de -34,5°
        por_nome.setdefault((a["nome"], oce), []).append(gm)
    ilhas = []
    for (nome, oce), grupos in por_nome.items():
        rings = [r for gm in grupos for r in gm]; ar = area_km2(rings)
        if ar < MIN_ILHA_KM2 and not oce: continue
        maior = max(rings, key=len)
        q = [dp_ring(r, .002) or (r[:-1] if r[0] == r[-1] else r) for r in rings]
        xs_, ys_ = [p[0] for r in rings for p in r], [p[1] for r in rings for p in r]
        ilhas.append({"nome": nome, "posicao": "oceanica" if oce else "costeira", "km2": round(ar, 2), "rings": [r3(x) for x in q if x and len(x) >= 3],
                      "rotulo": [round((min(xs_) + max(xs_)) / 2, 3), round((min(ys_) + max(ys_)) / 2, 3)]})
    ilhas.sort(key=lambda i: -i["km2"])
    camadas.append({"id": "ilhas", "titulo": "Ilhas", "tipo": "poligono", "fonte": "bc250", "ligada": True, "lista": True,
                    "nota": f"{len(ilhas)} ilhas e arquipélagos que o IBGE classifica como marítimos (BC250), com nome e ao menos {MIN_ILHA_KM2} km² (as peças de um mesmo arquipélago são somadas), mais as ilhas oceânicas de qualquer tamanho: Fernando de Noronha, Atol das Rocas, "
                            "São Pedro e São Paulo, Trindade e Martim Vaz. A classificação do IBGE inclui ilhas do estuário do Amazonas, como Marajó. As áreas são aproximadas (calculadas sobre os polígonos simplificados).",
                    "itens": ilhas})

    filtros = [
        {"id": "posicao", "titulo": "Ilhas", "camada": "ilhas", "campo": "posicao", "opcoes": [["", "Todas"], ["oceanica", "Oceânicas"], ["costeira", "Costeiras"]]},
        {"id": "tiporecife", "titulo": "Recifes", "camada": "recifes", "campo": "tipo",
         "opcoes": [["", "Todos"]] + [[t, t] for t in ("Coral", "Rochoso", "Tipo não informado") if any(r["tipo"] == t for r in recifes)]},
    ]
    return {"id": "costeiro", "oceano": True, "secao_titulo": "Manguezais, recifes e ilhas do litoral brasileiro", "titulo": "Mapa do Sistema Costeiro-Marinho: manguezais, recifes e ilhas",
            "nome_exibido": "Sistema Costeiro-Marinho", "limite_so_contorno": True, "dica": "Toque ou passe o mouse sobre um recife ou uma ilha para ver os detalhes.",
            "aviso_escopo": "O sistema costeiro-marinho é, em sua maior parte, mar (o limite do IBGE inclui a zona econômica exclusiva); o mapa mostra o que está nele e na costa, sem a profundidade.",
            "bbox": [round(v, 3) for v in bbox], "limite": limite, "limite_nome": "Sistema Costeiro-Marinho (IBGE, 2019)",
            "camadas": camadas, "filtros": filtros,
            "lacunas": ["Limite do sistema: edição 2019 do IBGE (via geobr), a mesma do mapa 3D da página inicial; a edição 2025 do IBGE usa outro arquivo, que não foi usado aqui. Nesse limite ficam de fora Trindade, Martim Vaz e o Arquipélago de São Pedro e São Paulo, que por isso aparecem fora do contorno no mapa.",
                        "Manguezais: dado de satélite (GMW), não o levantamento oficial brasileiro (ICMBio, Atlas dos Manguezais); manchas menores que ~1 km de lado foram omitidas.",
                        "Recifes: só os 68 polígonos da base do IBGE; recifes de profundidade, bancos e áreas de algas calcárias (rodolitos) não estão incluídos. Não há camada com licença aberta confirmada para eles.",
                        "Ilhas: classificação do IBGE (inclui ilhas do estuário do Amazonas); ilhas menores que 40 km², exceto as oceânicas, não aparecem. As áreas são aproximadas.",
                        "Unidades de conservação marinhas, rotas de migração, pesca, óleo e gás e profundidade (batimetria): não incluídos."],
            "fontes": FONTES}
