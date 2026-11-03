"""Receita do mapa temático da MATA ATLÂNTICA inteira (Brasil, Paraguai e Argentina): lê as bases já descompactadas e devolve o dicionário de data/mapas/mata-atlantica.json.

Pasta de entrada (`raw`), com estas subpastas/arquivos:
  resolve_ma/*.json   RESOLVE Ecoregions 2017, as 8 ecorregiões da Mata Atlântica (GeoJSON do FeatureServer; ver ECOS e FONTES["resolve"])
  biomas/             IBGE, Biomas 1:250 000 (2025)           lml_bioma_e250k_v20250911_A.*   (limite oficial da parte brasileira)
  cnuc/               MMA, CNUC edição 2025-08                cnuc_2025_08.*
  ne_10m_admin_0_countries/, ne_10m_admin_0_boundary_lines_land/, ne_10m_admin_1_states_provinces/, ne_10m_populated_places/,
  ne_rivers/ne_10m_rivers_lake_centerlines   Natural Earth 1:10m (domínio público)

Escala: o bioma tem ~1.800 UCs e mais de 3.000 sedes municipais; por isso as UCs vão fundidas por categoria (só as maiores que LIMITE_HA são
desenhadas; a lista em texto traz as federais e estaduais de proteção integral), as cidades são só capitais e as grandes, e os rios são os principais.
Fora do escopo, por falta de fonte com licença confirmada: cobertura florestal remanescente (ver `lacunas`).
"""
import json, math, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import shp
from mapas_dados import dp, dp_ring, inside, dist_borda, r3, recorta_anel, corta_linha, Mascara, contorno_externo

PUB = "dado público do IBGE (termo de licença não localizado)"
FONTES = {
    "resolve": {"titulo": "RESOLVE Ecoregions 2017 (Dinerstein et al., 2017, BioScience), 8 ecorregiões da Mata Atlântica: limite do bioma inteiro, com Paraguai e Argentina",
                "url": "https://ecoregions.appspot.com/", "data": "2017", "licenca": "CC BY 4.0"},
    "biomas": {"titulo": "IBGE, Biomas e Sistema Costeiro-Marinho do Brasil 1:250 000 (2025): limite oficial da parte brasileira",
               "url": "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/vetores/2025_Biomas-e-Sistema-Costeiro-Marinho-do-Brasil-1-250000_shp.zip", "data": "2025-09", "licenca": PUB},
    "cnuc": {"titulo": "MMA, Cadastro Nacional de Unidades de Conservação (CNUC), edição de agosto de 2025",
             "url": "https://dados.mma.gov.br/dataset/unidadesdeconservacao", "data": "2025-08", "licenca": "CC-BY"},
    "ne": {"titulo": "Natural Earth 1:10 milhões: países, fronteiras, estados e departamentos, cidades e rios principais",
           "url": "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/", "data": "2022", "licenca": "domínio público"},
}
# (arquivo, nome descritivo em português). Os nomes originais da RESOLVE ("Pernambuco ..." e "Bahia ...") são regiões biogeográficas, não estados:
# por isso os nomes abaixo são descrições escritas a partir dos estados que cada polígono realmente cobre (conferido nos dados).
ECOS = [("Alto_Paran_Atlantic_forests.json", "Florestas do Alto Paraná"), ("Araucaria_moist_forests.json", "Florestas de araucária"),
        ("Serra_do_Mar_coastal_forests.json", "Serra do Mar"), ("Atlantic_Coast_restingas.json", "Restingas da costa atlântica"),
        ("Bahia_coastal_forests.json", "Florestas costeiras do Leste (BA a ES)"), ("Bahia_interior_forests.json", "Florestas do interior do Leste (MG, BA e ES)"),
        ("Pernambuco_coastal_forests.json", "Florestas costeiras do Nordeste (PB a AL)"), ("Pernambuco_interior_forests.json", "Florestas do interior do Nordeste (RN a SE)")]
PAISES = {"BRA", "PRY", "ARG", "URY", "BOL"}
LIMITE_HA = 1000   # UCs menores que isso entram nas contagens, mas não no desenho (invisíveis nesta escala)
# nomes dos rios do Natural Earth em português (a base escreve "Paraiba" para o Paraíba do Sul, confirmado pela posição, e "Uruguay")
RIOS_PT = {"Paraiba": "Paraíba do Sul", "Uruguay": "Uruguai"}
# estados e departamentos que só aparecem como "pontas" nos cantos do mapa, sem relação com o bioma: ficam de fora (pintura, nome e divisas própria).
# As divisas compartilhadas com os vizinhos continuam desenhadas pelos vizinhos, e as fronteiras entre países pela camada de países.
SEM_ESTADO = {"Amazonas", "Santa Cruz", "Alto Paraguay", "Entre Ríos", "Salto", "Paysandú"}
ESFERAS = {"Federal": "federais", "Estadual": "estaduais", "Municipal": "municipais"}
milhar = lambda n: f"{round(n):,}".replace(",", ".")   # 1234567 → 1.234.567


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


MINUSC = {"de", "do", "da", "dos", "das", "e", "ao", "no", "na", "em"}
SIGLAS = {"sesc": "Sesc", "rppn": "RPPN", "apa": "APA", "arie": "ARIE", "resex": "RESEX"}
ROMANOS = {"i", "ii", "iii", "iv", "v", "vi"}


def titulo(nome):
    """MAIÚSCULAS do CNUC → nome legível; RPPN e APA viram sigla."""
    t = " ".join(nome.lower().split())
    for longo, sigla in (("reserva particular do patrimônio natural", "rppn"), ("reserva particular do patrimonio natural", "rppn"), ("área de proteção ambiental", "apa")):
        if t.startswith(longo): t = sigla + t[len(longo):]; break
    return " ".join(SIGLAS.get(w) or (w.upper() if w in ROMANOS and i else w if (w in MINUSC and i) else w.capitalize()) for i, w in enumerate(t.split(" ")))


def receita(raw):
    # ---- a região: 8 ecorregiões RESOLVE (bioma inteiro) + limite oficial do IBGE na parte brasileira (sem as ilhas oceânicas)
    ibge_todos = [r for a, g in shp.read(f"{raw}/biomas/lml_bioma_e250k_v20250911_A") if a["NM_BIOMA"] == "Mata Atlântica" for r in g]
    # No Brasil o limite oficial é o do IBGE, que termina a ~30°S: as restingas da RESOLVE seguem pelo litoral sul do RS (e do Uruguai), onde o IBGE
    # classifica o bioma como Pampa. A ecorregião de restingas é cortada ao sul do ponto mais ao sul do limite do IBGE.
    corte_sul = min(p[1] for r in ibge_todos for p in r)
    ecos = []
    for arq, nome in ECOS:
        g = json.load(open(f"{raw}/resolve_ma/{arq}", encoding="utf-8"))["features"][0]["geometry"]
        polis = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        aneis = [[tuple(p) for p in pol[0]] for pol in polis]
        if "restingas" in arq: aneis = [q for q in (recorta_anel(r, (-180, corte_sul, 180, 90)) for r in aneis) if q]
        ecos.append((nome, aneis))
    res_aneis = [r for _, rs in ecos for r in rs]
    xs, ys = [p[0] for r in res_aneis for p in r], [p[1] for r in res_aneis for p in r]
    reg = (min(xs), min(ys), max(xs), max(ys))
    dentro_reg = lambda r: reg[0] - .5 < sum(p[0] for p in r) / len(r) < reg[2] + .5 and reg[1] - .5 < sum(p[1] for p in r) / len(r) < reg[3] + .5
    ibge = [r for r in ibge_todos if dentro_reg(r)]   # fora ficam Fernando de Noronha, São Pedro e São Paulo e outras ilhas oceânicas
    P = .6
    bbox = (reg[0] - P, reg[1] - P, reg[2] + P, reg[3] + P); box = (bbox[0] - .3, bbox[1] - .3, bbox[2] + .3, bbox[3] + .3)
    # a moldura do mapa vai até bbox ± 3% do tamanho (mapas.Proj); a terra (países, estados, fronteiras) é recortada numa caixa MAIOR que isso,
    # para o desenho ir até a borda da imagem (com a caixa menor sobravam faixas de "oceano" nas laterais). Quais estados entram continua decidido por `box`.
    dx, dy = (bbox[2] - bbox[0]) * .05 + .2, (bbox[3] - bbox[1]) * .05 + .2
    vbox = (bbox[0] - dx, bbox[1] - dy, bbox[2] + dx, bbox[3] + dy)
    mask_res = Mascara(res_aneis, reg, .01)                 # só as ecorregiões (para o contorno externo)
    mask = Mascara(res_aneis + ibge, reg, .01)              # ecorregiões + IBGE (para decidir o que está dentro do bioma)
    limite = [r3(q) for q in (dp_ring(list(r), .01) for r in res_aneis) if q]
    limite_simpl = [[tuple(p) for p in r] for r in limite]
    contorno = [r3(l) for l in contorno_externo(limite_simpl, mask_res)]
    oficial = [r3(q) for q in (dp_ring(list(r), .03) for r in ibge) if q]
    camadas = []

    # ---- países, fronteiras, estados/departamentos (estados do Brasil pintados em cores diferentes)
    paises, estados = [], []
    for a, gm in shp.read(f"{raw}/ne_10m_admin_0_countries/ne_10m_admin_0_countries", vbox):
        if a["ADM0_A3"] not in PAISES: continue
        rings = [q for q in (recorta_anel(r, vbox) for r in gm) if q]
        rings = [q for q in (dp_ring(r + [r[0]], .02) for r in rings) if q]
        if rings: paises.append({"nome": a["NAME_PT"], "rings": [r3(r) for r in rings], "rotulo": centro(rings, bbox)})
    fronteiras = [r3(dp(l, .02)) for a, gm in shp.read(f"{raw}/ne_10m_admin_0_boundary_lines_land/ne_10m_admin_0_boundary_lines_land", vbox) for ln in gm for l in corta_linha(ln, vbox)]
    camadas.append({"id": "paises", "titulo": "Fronteiras entre países", "tipo": "contexto", "fonte": "ne", "ligada": True,
                    "nota": "Países vizinhos com seu nome e uma cor para cada um; as fronteiras vêm do Natural Earth (escala 1:10 milhões) e podem divergir em detalhe dos limites oficiais.",
                    "itens": paises, "fronteiras": fronteiras})
    for a, gm in shp.read(f"{raw}/ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces", vbox):
        if a["adm0_a3"] not in PAISES or a["name"] in SEM_ESTADO: continue
        if not any(recorta_anel(r, box) for r in gm): continue   # quais estados entram: só os que tocam a caixa menor (a faixa extra não traz estados novos)
        rings = [q for q in (recorta_anel(r, vbox) for r in gm) if q]
        if not rings: continue
        e = {"nome": a["name"], "lns": [l for r in gm for l in corta_linha([tuple(p) for p in r], vbox)], "rotulo": centro(rings, bbox)}
        if a["adm0_a3"] == "BRA":
            e["rings"] = [r3(q) for q in (dp_ring(list(r) + [r[0]], .02) for r in rings) if q]
            e["vert"] = {(round(p[0], 2), round(p[1], 2)) for r in gm for p in r}
        estados.append(e)
    br = [e for e in estados if "vert" in e]
    viz = {i: {j for j, f in enumerate(br) if j != i and len(e["vert"] & f["vert"]) >= 2} for i, e in enumerate(br)}
    cor = {}
    for i in sorted(viz, key=lambda i: -len(viz[i])):   # coloração gulosa: estados vizinhos nunca repetem cor (6 cores)
        usadas = {cor[j] for j in viz[i] if j in cor}; cor[i] = next(c for c in range(6) if c not in usadas)
    for i, e in enumerate(br): e["cor"] = cor[i]
    camadas.append({"id": "estados", "titulo": "Estados e departamentos", "tipo": "contexto", "fonte": "ne", "ligada": True,
                    "nota": "Divisas internas dos países (estados no Brasil, departamentos no Paraguai, províncias na Argentina), Natural Earth 1:10 milhões. Os estados do Brasil são pintados em cores diferentes; o bioma é sempre de uma cor só.",
                    "itens": [{"nome": e["nome"], "rotulo": e["rotulo"], **({"rings": e["rings"], "cor": e["cor"]} if "rings" in e else {})} for e in estados],
                    "fronteiras": [r3(dp(l, .02)) for e in estados for l in e["lns"]]})

    # ---- contornos das ecorregiões (só linhas: o bioma continua de uma cor só)
    eco_itens, eco_linhas = [], []
    for nome, rs in ecos:
        rr = [q for q in (dp_ring(list(r), .02) for r in rs) if q]
        eco_linhas += [r3(q + [q[0]]) for q in rr]
        eco_itens.append({"nome": nome, "rotulo": centro(rr, bbox)})
    camadas.append({"id": "ecorregioes", "titulo": "Ecorregiões (contornos)", "tipo": "contexto", "fonte": "resolve", "ligada": False,
                    "nota": "As 8 ecorregiões da Mata Atlântica na classificação RESOLVE 2017. São só contornos; o bioma continua de uma cor só. Os nomes são descrições nossas, a partir dos estados que cada área cobre: os nomes originais da RESOLVE (\"Pernambuco coastal forests\", \"Pernambuco interior forests\", \"Bahia coastal forests\", \"Bahia interior forests\") se referem a regiões biogeográficas, não aos estados, e as áreas ultrapassam os limites estaduais.",
                    "itens": eco_itens, "fronteiras": eco_linhas})

    # ---- rios principais (Natural Earth): trechos com ponto médio dentro do bioma, agrupados por nome; todos sem informação de navegabilidade ("ext")
    por_nome = {}
    for a, gm in shp.read(f"{raw}/ne_rivers/ne_10m_rivers_lake_centerlines", box):
        if not a["name"] or a["featurecla"] != "River": continue
        for r in gm:
            if len(r) > 1 and mask(*r[len(r) // 2]):
                por_nome.setdefault(a["name"], []).append(dp(r, .01))
    rios = []
    for n, ls in por_nome.items():
        km = sum(math.hypot((q[0] - p[0]) * .95, q[1] - p[1]) * 111 for l in ls for p, q in zip(l, l[1:]))
        rios.append({"nome": "Rio " + RIOS_PT.get(n, n), "km": round(km), "ext": [r3(l) for l in ls], "_ls": ls})
    rios.sort(key=lambda r: -r["km"])
    for r in rios[:10]:   # rótulo nos 10 maiores, no meio do maior trecho
        l = max(r["_ls"], key=len); m = l[len(l) // 2]; r["rotulo"] = [round(m[0], 3), round(m[1], 3)]
    for r in rios: del r["_ls"]
    camadas.append({"id": "rios", "titulo": "Rios principais", "tipo": "linha", "fonte": "ne", "ligada": True,
                    "nota": "Só os rios principais (Natural Earth 1:10 milhões), sem informação de navegabilidade; o desenho é generalizado.", "itens": rios})

    # ---- unidades de conservação (CNUC; só Brasil): fundidas por categoria; as maiores que LIMITE_HA são desenhadas
    classes, lista = {}, []
    for a, gm in shp.read(f"{raw}/cnuc/cnuc_2025_08", box):
        amostra = [p for r in gm for p in r[::max(1, len(r) // 40)]]
        if not any(mask(*p) for p in amostra): continue
        grupo = "PI" if a["grupo"].startswith("Prote") else "US"; esf = a["esfera"]; ha = float(a["ha_total"] or 0)
        c = classes.setdefault((grupo, esf), {"n": 0, "ha": 0.0, "desenhadas": 0, "rings": []})
        c["n"] += 1; c["ha"] += ha
        if ha >= LIMITE_HA:
            c["desenhadas"] += 1
            c["rings"] += [r3(q) for q in (dp_ring(list(r), .015 if ha > 20000 else .008) for r in gm) if q]
        if grupo == "PI" and esf in ("Federal", "Estadual"):
            lista.append({"nome": titulo(a["nome_uc"]), "categoria": a["categoria"], "grupo": grupo, "esfera": esf, "uf": a["uf"], "ha": round(ha), "ano": a["cria_ano"][-4:] if a["cria_ano"] else ""})
    lista.sort(key=lambda u: -u["ha"])
    itens_uc = []
    for (grupo, esf), c in sorted(classes.items()):
        if not c["rings"]: continue
        prot = "proteção integral" if grupo == "PI" else "uso sustentável"
        itens_uc.append({"grupo": grupo, "esfera": esf, "rings": c["rings"],
                         "texto": f"UCs {ESFERAS.get(esf, esf.lower())} de {prot}: {milhar(c['n'])} unidades no bioma, somando {milhar(c['ha'])} ha de área total (a parte fora do bioma também conta). No mapa aparecem as {milhar(c['desenhadas'])} com mais de {milhar(LIMITE_HA)} ha."})
    camadas.append({"id": "ucs", "titulo": "Unidades de conservação", "tipo": "poligono", "fonte": "cnuc", "ligada": True,
                    "nota": f"Só no Brasil, fundidas por categoria (proteção × esfera). Toque numa mancha para ver quantas unidades ela representa. Não aparecem as menores que {milhar(LIMITE_HA)} ha.",
                    "nota_lista": "A lista traz só as unidades federais e estaduais de proteção integral; as demais (uso sustentável e municipais) estão no CNUC.", "lista": lista, "itens": itens_uc})

    # ---- cidades: capitais estaduais e cidades com mais de 500 mil habitantes (Brasil); cidades com mais de 100 mil no Paraguai e na Argentina
    cid = []
    for a, gm in shp.read(f"{raw}/ne_10m_populated_places/ne_10m_populated_places", box):
        p = gm[0]; pop = float(a["POP_MAX"] or 0); pmin = float(a["POP_MIN"] or 0)   # POP_MAX é da aglomeração (Canoas = 600 mil); POP_MIN é a da cidade
        capital = "capital" in a["FEATURECLA"].lower() and a["NAME"] != "Niterói"   # o Natural Earth marca Niterói como capital por engano (a capital do RJ é o Rio)
        if a["ADM0_A3"] == "BRA" and (capital or pmin >= 400000) and mask.perto(p[0], p[1], .3 if capital else .15):
            cid.append({"nome": a["NAME_PT"] or a["NAME"], "uf": a["ADM1NAME"], "pt": [round(p[0], 3), round(p[1], 3)]})
        elif a["ADM0_A3"] in ("PRY", "ARG") and pop >= 100000 and mask(*p):
            cid.append({"nome": a["NAME"], "uf": a["ADM1NAME"], "pt": [round(p[0], 3), round(p[1], 3)]})
    camadas.append({"id": "cidades", "titulo": "Capitais e grandes cidades", "tipo": "ponto", "fonte": "ne", "ligada": True,
                    "nota": "Capitais estaduais e cidades grandes do Brasil (população estimada acima de ~400 mil no Natural Earth, que usa estimativas defasadas), e cidades com mais de 100 mil no Paraguai e na Argentina; dentro do bioma ou perto do limite (capitais: até ~30 km). A Mata Atlântica abriga a maior parte da população brasileira.", "itens": cid})

    filtros = [
        {"id": "grupo", "titulo": "Proteção", "camada": "ucs", "campo": "grupo", "opcoes": [["", "Todas"], ["PI", "Proteção integral"], ["US", "Uso sustentável"]]},
        {"id": "esfera", "titulo": "Esfera", "camada": "ucs", "campo": "esfera", "opcoes": [["", "Todas"], ["Federal", "Federal"], ["Estadual", "Estadual"], ["Municipal", "Municipal"]]},
    ]
    return {"id": "mata-atlantica", "oceano": True, "titulo": "Mapa da Mata Atlântica inteira (Brasil, Paraguai e Argentina): unidades de conservação, rios e cidades",
            "aviso_escopo": "O limite cobre a Mata Atlântica inteira; as unidades de conservação existem só para o lado brasileiro. Os dois limites (ecorregiões RESOLVE e oficial do IBGE) vêm de bases diferentes e não coincidem exatamente. As ilhas oceânicas (Fernando de Noronha, São Pedro e São Paulo) ficam fora do recorte.",
            "bbox": [round(v, 3) for v in bbox], "limite": limite, "limite_contorno": contorno, "limite_nome": "Mata Atlântica (ecorregiões, RESOLVE 2017)",
            "limite_oficial": oficial, "limite_oficial_nome": "Limite oficial no Brasil (IBGE 2025)",
            "camadas": camadas, "filtros": filtros,
            "lacunas": ["Cobertura florestal remanescente (a floresta que restou): o Atlas da SOS Mata Atlântica/INPE exige cadastro e não tem licença aberta confirmada; o MapBiomas só sai pelo Google Earth Engine; o Hansen Global Forest Change (CC BY 4.0) conta qualquer árvore, inclusive plantios, e tem tiles de até 290 MB. Nada disso foi incluído.",
                        "Unidades de conservação no Paraguai e na Argentina: a base mundial (WDPA) não permite redistribuição.",
                        "Rios com nome e navegabilidade em detalhe: a drenagem do IBGE (BC250) tem milhões de trechos nesta área e não coube; o mapa traz só os rios principais do Natural Earth.",
                        "Costa sul do Rio Grande do Sul e do Uruguai: a ecorregião de restingas da RESOLVE desce até lá, mas o IBGE classifica essa costa como Pampa; o mapa corta as restingas ao sul de 30°S (limite sul do IBGE).",
                        "Terras Indígenas e territórios quilombolas: não incluídos (limites oficiais da FUNAI indisponíveis; as milhares de localidades quilombolas do IBGE ficam para outra escala)."],
            "fontes": FONTES}
