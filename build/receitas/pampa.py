"""Receita do mapa temático do PAMPA: lagoas e rios largos, principais rios (por bacia) e unidades de conservação (decisão do projeto: sem cidades).
Lê as bases já descompactadas e devolve o dicionário de data/mapas/pampa.json.

Pasta de entrada (`raw`):
  resolve_pa/eco_574.json   RESOLVE Ecoregions 2017, ecorregião "Uruguayan savanna" (ECO_ID 574; GeoJSON do FeatureServer, maxAllowableOffset=0.003): Brasil e Uruguai
  resolve_pa/eco_576.json   RESOLVE Ecoregions 2017, ecorregião "Humid Pampas" (ECO_ID 576, mesmos parâmetros): a parte argentina do Pampa (Buenos Aires, Córdoba, Santa Fe, Entre Ríos, La Pampa)
  biomas/                   IBGE, Biomas 1:250 000 (2025)           lml_bioma_e250k_v20250911_A.*   (limite oficial)
  bc250/                    IBGE, BC250 versão 2025                 hid_trecho_drenagem_l.{shp,shx,dbf,cpg} (rios nomeados) e hid_massa_dagua_a.{shp,dbf,cpg} (lagoas)
  cnuc/                     MMA, CNUC edição 2025-08                cnuc_2025_08.*
  ne_10m_admin_0_countries/, ne_10m_admin_0_boundary_lines_land/, ne_10m_admin_1_states_provinces/   Natural Earth 1:10m (domínio público)

Por que só uma ecorregião: medido por amostragem (3.000 pontos, semente fixa) dentro do polígono do Pampa do IBGE, contra 10 ecorregiões RESOLVE da região:
~87% cai na "Uruguayan savanna", ~5% nas florestas do Alto Paraná, ~1% nas restingas da costa atlântica, ~0,6% nas florestas de araucária e da Serra do Mar,
e ~6% em nenhuma (167 dos 175 pontos desses 6% estão dentro do polígono da Lagoa dos Patos no BC250). Por isso o limite é a ecorregião dominante inteira, com o
limite do IBGE por cima (que cobre as bordas com a Mata Atlântica), como no Cerrado, e não há camada de ecorregiões. A extensão completa do Pampa inclui a parte argentina: o limite é a "Uruguayan savanna" mais a "Humid Pampas"
(~35 + ~40 Mha por área aproximada dos polígonos, contra 83,8 Mha de Pampa trinacional no MapBiomas, que usa a Província Fitogeográfica Pampeana na Argentina, 46,7 Mha). Por amostragem (4.000 pontos), a "Uruguayan
savanna" tem ~47% da área no Brasil, ~53% no Uruguai e 0% na Argentina.

UCs: entram as unidades que o CNUC marca com área no Pampa (campo `pampa` do cadastro, numérico: a área da unidade dentro do bioma; vazio = sem área no Pampa).
"""
import json, math, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import shp
from mapas_dados import dp, dp_ring, inside, dist_borda, r3, recorta_anel, corta_linha, Mascara

PUB = "dado público do IBGE (termo de licença não localizado)"
FONTES = {
    "resolve": {"titulo": "RESOLVE Ecoregions 2017 (Dinerstein et al., 2017, BioScience), ecorregiões Uruguayan savanna (Brasil e Uruguai) e Humid Pampas (Argentina): extensão completa do Pampa",
                "url": "https://ecoregions.appspot.com/", "data": "2017", "licenca": "CC BY 4.0"},
    "biomas": {"titulo": "IBGE, Biomas e Sistema Costeiro-Marinho do Brasil 1:250 000 (2025): limite oficial do Pampa",
               "url": "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/vetores/2025_Biomas-e-Sistema-Costeiro-Marinho-do-Brasil-1-250000_shp.zip", "data": "2025-09", "licenca": PUB},
    "bc250": {"titulo": "IBGE, Base Cartográfica Contínua do Brasil 1:250 000 (BC250), versão 2025: massas d'água (lagoas) e trechos de drenagem nomeados",
              "url": "https://geoftp.ibge.gov.br/cartas_e_mapas/bases_cartograficas_continuas/bc250/versao2025/shapefiles/bc_250_shapefiles_2026_03_03.zip", "data": "2026-03", "licenca": PUB},
    "cnuc": {"titulo": "MMA, Cadastro Nacional de Unidades de Conservação (CNUC), edição de agosto de 2025",
             "url": "https://dados.mma.gov.br/dataset/unidadesdeconservacao", "data": "2025-08", "licenca": "CC-BY"},
    "ne": {"titulo": "Natural Earth 1:10 milhões: países, fronteiras, estados e departamentos",
           "url": "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/", "data": "2022", "licenca": "domínio público"},
}
PAISES = {"BRA", "URY", "ARG", "PRY"}
# províncias e departamentos que só aparecem como fatias nos cantos do mapa, sem relação com o bioma: ficam de fora (as divisas dos vizinhos continuam desenhadas por eles).
# Todo o Paraguai (só pintura de país, sem departamentos) e seis províncias argentinas dos cantos.
SEM_ESTADO = {"Formosa", "Chaco", "Catamarca", "La Rioja", "Tucumán", "Santiago del Estero"}
SEM_ESTADO_ARG_APENAS = {"Río Negro"}   # a província argentina; o departamento uruguaio de mesmo nome fica
SEM_ESTADO_PAIS = {"PRY"}
ESFERAS = {"Federal": "federais", "Estadual": "estaduais", "Municipal": "municipais"}

# Rios do Pampa (IBGE BC250), por nome: (nome mostrado, bacia, caixa lon0, lat0, lon1, lat1). O nome sozinho não basta ("Rio Santa Maria", "Rio Jacuí",
# "Rio Vacacaí"… existem em outras regiões): cada rio só vale dentro da caixa que cobre o curso real, conferida contra a extensão encontrada na base.
# A bacia vem do conhecimento geral (bacias hidrográficas do Rio Grande do Sul), não de uma base de dados: está declarada na nota da camada e nas lacunas.
BACIAS = ["Uruguai", "Guaíba", "Camaquã", "Mirim–São Gonçalo"]
RIOS = {
    "Rio Uruguai": ("Rio Uruguai", "Uruguai", (-57.7, -30.4, -51.8, -27.0)), "Rio Ibicuí": ("Rio Ibicuí", "Uruguai", (-56.9, -30.0, -53.0, -28.9)),
    "Rio Ibicuí-Mirim": ("Rio Ibicuí-Mirim", "Uruguai", (-54.6, -29.8, -53.6, -29.3)), "Rio Ibirapuitã": ("Rio Ibirapuitã", "Uruguai", (-56.1, -31.0, -55.5, -29.3)),
    "Rio Quaraí": ("Rio Quaraí", "Uruguai", (-57.7, -31.0, -55.3, -30.0)), "Rio Santa Maria": ("Rio Santa Maria", "Uruguai", (-55.9, -31.4, -54.2, -29.8)),
    "Rio Cacequi": ("Rio Cacequi", "Uruguai", (-55.0, -30.5, -54.4, -29.8)), "Rio Toropi": ("Rio Toropi", "Uruguai", (-54.7, -29.9, -53.6, -29.1)),
    "Rio Icamaquã": ("Rio Icamaquã", "Uruguai", (-56.1, -29.1, -54.6, -28.4)), "Rio Butuí": ("Rio Butuí", "Uruguai", (-56.4, -29.2, -55.4, -28.7)),
    "Rio Jacuí": ("Rio Jacuí", "Guaíba", (-53.5, -30.3, -51.2, -28.0)), "Rio Vacacaí": ("Rio Vacacaí", "Guaíba", (-54.0, -30.1, -53.0, -29.8)),
    "Rio Vacacaí-Mirim": ("Rio Vacacaí-Mirim", "Guaíba", (-53.9, -29.95, -53.0, -29.6)),
    "Rio Camaquã": ("Rio Camaquã", "Camaquã", (-53.8, -31.6, -51.6, -30.7)),
    "Rio Jaguarão": ("Rio Jaguarão", "Mirim–São Gonçalo", (-54.1, -33.8, -53.0, -31.2)), "Rio Piratini": ("Rio Piratini", "Mirim–São Gonçalo", (-53.4, -32.1, -52.3, -31.4)),
}
MAIOR_LAGOA = 2e-4    # massas d'água nomeadas só entram se a caixa do polígono tiver mais que isso (graus², ~2,5 km²); sem nome, 20× mais
TIPO_ROTULO = {"lagoa": "Lagoas", "banhado": "Banhados", "rio": "Rios largos", "represa": "Represas"}


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


MINUSC = {"de", "do", "da", "dos", "das", "e", "ao", "no", "na", "em"}
SIGLAS = {"rppn": "RPPN", "apa": "APA", "arie": "ARIE", "resex": "RESEX", "rebio": "REBIO"}
ROMANOS = {"i", "ii", "iii", "iv", "v", "vi"}
milhar = lambda n: f"{round(n):,}".replace(",", ".")


def titulo(nome):
    """MAIÚSCULAS do CNUC → nome legível; RPPN e APA viram sigla."""
    t = " ".join(nome.lower().split())
    for longo, sigla in (("reserva particular do patrimônio natural", "rppn"), ("reserva particular do patrimonio natural", "rppn"), ("área de proteção ambiental", "apa")):
        if t.startswith(longo): t = sigla + t[len(longo):]; break
    return " ".join(SIGLAS.get(w) or (w.upper() if w in ROMANOS and i else w if (w in MINUSC and i) else w.capitalize()) for i, w in enumerate(t.split(" ")))


def tipo_massa(a):
    n = a["nome"].lower()
    if n.startswith("banhado"): return "banhado"
    if n.startswith(("lagoa", "lago ")) or a["tipomassad"] in ("Laguna", "Lago/Lagoa"): return "lagoa"
    if n.startswith(("represa", "barragem", "açude")) or a["tipomassad"] == "Represa/açude": return "represa"
    return "rio"   # rios largos (Uruguai, Jacuí, Guaíba…) e canais


def receita(raw):
    # ---- a região: ecorregiões RESOLVE "Uruguayan savanna" (Brasil e Uruguai) e "Humid Pampas" (Argentina) + limite oficial do IBGE por cima
    res_aneis = []
    for eco in ("eco_574", "eco_576"):
        g = json.load(open(f"{raw}/resolve_pa/{eco}.json", encoding="utf-8"))["features"][0]["geometry"]
        polis = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        res_aneis += [[tuple(p) for p in pol[0]] for pol in polis]
    ibge = [r for a, gm in shp.read(f"{raw}/biomas/lml_bioma_e250k_v20250911_A") if a["NM_BIOMA"] == "Pampa" for r in gm]
    xs, ys = [p[0] for r in res_aneis + ibge for p in r], [p[1] for r in res_aneis + ibge for p in r]
    reg = (min(xs), min(ys), max(xs), max(ys))
    P = .6
    bbox = (reg[0] - P, reg[1] - P, reg[2] + P, reg[3] + P); box = (bbox[0] - .3, bbox[1] - .3, bbox[2] + .3, bbox[3] + .3)
    dx, dy = (bbox[2] - bbox[0]) * .05 + .2, (bbox[3] - bbox[1]) * .05 + .2
    vbox = (bbox[0] - dx, bbox[1] - dy, bbox[2] + dx, bbox[3] + dy)   # a terra é recortada numa caixa maior que a moldura (sem faixas vazias)
    limite = [r3(q) for q in (dp_ring(list(r), .02) for r in res_aneis) if q]
    oficial = [r3(q) for q in (dp_ring(list(r), .01) for r in ibge) if q]
    camadas = []

    # ---- países, fronteiras, estados e departamentos (estados do Brasil em cores diferentes)
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
        if a["adm0_a3"] not in PAISES or a["adm0_a3"] in SEM_ESTADO_PAIS or a["name"] in SEM_ESTADO or (a["adm0_a3"] == "ARG" and a["name"] in SEM_ESTADO_ARG_APENAS): continue
        if not any(recorta_anel(r, box) for r in gm): continue
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
                    "nota": "Divisas internas dos países (estados no Brasil, departamentos no Uruguai, províncias na Argentina), Natural Earth 1:10 milhões. Os estados do Brasil são pintados em cores diferentes; o bioma é sempre de uma cor só.",
                    "itens": [{"nome": e["nome"], "rotulo": e["rotulo"], **({"rings": e["rings"], "cor": e["cor"]} if "rings" in e else {})} for e in estados],
                    "fronteiras": [r3(dp(l, .02)) for e in estados for l in e["lns"]]})

    # ---- lagoas e rios largos (massas d'água do BC250; só Brasil): nomeadas e com área relevante
    massas = []
    for a, gm in shp.read(f"{raw}/bc250/hid_massa_dagua_a", box):
        if "oceano" in a["nome"].lower(): continue   # o oceano já é o fundo do mapa
        xs_, ys_ = [p[0] for p in gm[0]], [p[1] for p in gm[0]]
        area = (max(xs_) - min(xs_)) * (max(ys_) - min(ys_))
        if area < (MAIOR_LAGOA if a["nome"] else MAIOR_LAGOA * 20): continue
        rings = [q for q in (dp_ring(r, .003) for r in gm) if q]
        if rings: massas.append({"nome": a["nome"], "tipo": tipo_massa(a), "rings": [r3(q) for q in rings]})
    camadas.append({"id": "massas", "titulo": "Lagoas e rios largos", "tipo": "poligono", "fonte": "bc250", "ligada": True,
                    "nota": "Só no Brasil. Água permanente mapeada na escala 1:250 000: lagoas, banhados e represas com nome e mais de ~2,5 km², e rios largos (Uruguai, Jacuí, Guaíba). A Lagoa Mirim aparece só no lado brasileiro.",
                    "itens": massas})

    # ---- rios (drenagem do IBGE, pelo nome, dentro da caixa de cada rio; só o trecho que cai na moldura do mapa)
    candidatos = {nome: [(mostrado, bacia, caixa)] for nome, (mostrado, bacia, caixa) in RIOS.items()}
    achados, bacia_de = {}, {}
    for a, gm in shp.read_por_nome(f"{raw}/bc250/hid_trecho_drenagem_l", "nome", set(candidatos)):
        for mostrado, bacia, b in candidatos[a["nome"]]:
            for l in gm:
                m = l[len(l) // 2]
                if len(l) > 1 and b[0] <= m[0] <= b[2] and b[1] <= m[1] <= b[3]:
                    for parte in corta_linha(l, vbox, 0):
                        achados.setdefault(mostrado, []).append(dp(parte, .01)); bacia_de[mostrado] = bacia
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
    for r_ in rios[:7]:   # rótulos: só os 7 maiores (o bioma é pequeno e os textos não podem se sobrepor)
        ls = max((l for l in [[tuple(p) for p in l] for l in r_["linhas"]]), key=len); m = ls[len(ls) // 2]; r_["rotulo"] = [round(m[0], 3), round(m[1], 3)]
    camadas.append({"id": "rios", "titulo": "Rios dos Pampas (Brasil)", "tipo": "linha", "fonte": "bc250", "ligada": True, "por_rio": True, "lista": True, "lista_titulo": "Rios",
                    "nota": f"Os {len(rios)} principais rios que correm pelo Pampa gaúcho, da drenagem do IBGE, só no trecho que aparece no mapa. O filtro separa os rios pela bacia hidrográfica do Rio Grande do Sul; a bacia de cada rio vem do conhecimento geral (não de uma base de dados), e as caixas de coordenadas que isolam cada rio (há homônimos em outras regiões) foram conferidas contra a base. Toque num rio para ver por quais países e estados ele passa (limites do Natural Earth, aproximados).",
                    "itens": rios})

    # ---- unidades de conservação (CNUC; só Brasil): as que o próprio CNUC marca com área no Pampa (campo `pampa`, em ha). RPPNs de poucos hectares ficam
    # como manchas minúsculas (simplificação fraca; se mesmo assim o anel colapsar, vale o anel original)
    ucs = []
    for a, gm in shp.read(f"{raw}/cnuc/cnuc_2025_08", box):
        if not a["pampa"]: continue
        ha_ = float(a["ha_total"] or 0); eps = .004 if ha_ > 2000 else .001 if ha_ > 100 else .0003
        rings = [q for q in (dp_ring(r, eps) or (r[:-1] if r[0] == r[-1] else r) for r in gm) if q and len(q) >= 3]
        if not rings: continue
        ucs.append({"nome": titulo(a["nome_uc"]), "categoria": a["categoria"], "grupo": "PI" if a["grupo"].startswith("Prote") else "US",
                    "esfera": a["esfera"], "uf": a["uf"], "ha": round(float(a["ha_total"] or 0)), "ano": a["cria_ano"][-4:] if a["cria_ano"] else "",
                    "rings": [r3(q) for q in rings]})
    ucs.sort(key=lambda u: -u["ha"])
    camadas.append({"id": "ucs", "titulo": "Unidades de conservação", "tipo": "poligono", "fonte": "cnuc", "ligada": True,
                    "nota": "Só no Brasil: federais, estaduais, municipais e RPPNs que o CNUC marca com área no Pampa (campo \"pampa\" do cadastro; as RPPNs de poucos hectares são manchas minúsculas, quase invisíveis). A área é a total da unidade (a parte fora do Pampa também conta). Uruguai e Argentina ficam de fora porque a base mundial (WDPA) não permite redistribuição.",
                    "itens": ucs})

    presentes = [b for b in BACIAS if any(r_["attrs"]["bacia"] == b for r_ in rios)]
    tipos = [t for t in TIPO_ROTULO if any(m["tipo"] == t for m in massas)]
    filtros = [
        {"id": "bacia", "titulo": "Bacia hidrográfica", "camada": "rios", "campo": "bacia", "opcoes": [["", "Todas as bacias"]] + [[b, b] for b in presentes]},
        {"id": "tipoagua", "titulo": "Corpo d'água", "camada": "massas", "campo": "tipo", "opcoes": [["", "Todos"]] + [[t, TIPO_ROTULO[t]] for t in tipos]},
        {"id": "grupo", "titulo": "Proteção", "camada": "ucs", "campo": "grupo", "opcoes": [["", "Todas"], ["PI", "Proteção integral"], ["US", "Uso sustentável"]]},
        {"id": "esfera", "titulo": "Esfera", "camada": "ucs", "campo": "esfera", "opcoes": [["", "Todas"], ["Federal", "Federal"], ["Estadual", "Estadual"], ["Municipal", "Municipal"]]},
    ]
    return {"id": "pampa", "oceano": True, "titulo": "Mapa dos Pampas: lagoas, rios e unidades de conservação",
            "nome_exibido": "Pampas", "plural": True,
            "aviso_escopo": "O limite do bioma mostra a extensão completa do Pampa: a ecorregião RESOLVE \"Uruguayan savanna\" (Rio Grande do Sul e Uruguai) mais a \"Humid Pampas\" (Argentina), com o limite oficial do IBGE por cima na parte brasileira; os dois vêm de bases diferentes e não coincidem exatamente. As camadas detalhadas (lagoas, rios, unidades de conservação) existem só para o lado brasileiro.",
            "bbox": [round(v, 3) for v in bbox], "limite": limite, "limite_nome": "Pampas (ecorregiões, RESOLVE 2017)",
            "limite_oficial": oficial, "limite_oficial_nome": "Pampa no Brasil (limite oficial, IBGE 2025)",
            "camadas": camadas, "filtros": filtros,
            "lacunas": ["Cidades: não incluídas por escolha do projeto.",
                        "Parte argentina: desenhada com a ecorregião RESOLVE \"Humid Pampas\" (~40 Mha por área aproximada). O MapBiomas usa outro limite para o Pampa na Argentina (Província Fitogeográfica Pampeana, 46,7 Mha), maior que esse; a extensão argentina muda conforme a fonte. Nenhuma camada detalhada (rios, lagoas, unidades de conservação) cobre a Argentina nem o Uruguai.",
                        "Ecorregiões: a RESOLVE tem uma ecorregião dominante sobre o Pampa brasileiro (Uruguayan savanna, ~87% da área do IBGE em amostragem); o resto é Alto Paraná (~5%), restingas (~1%), araucária e Serra do Mar (<1%) e Lagoa dos Patos (~6%, sem ecorregião). Por isso não há camada de ecorregiões; as bordas com a Mata Atlântica ficam cobertas só pelo limite oficial do IBGE.",
                        "Unidades de conservação no Uruguai e na Argentina: a base mundial (WDPA) não permite redistribuição.",
                        f"Os rios são uma seleção dos principais ({len(rios)}), não toda a rede de drenagem; a bacia de cada um vem do conhecimento geral (bacias do Rio Grande do Sul), não de uma base de dados. A Lagoa Mirim aparece só no lado brasileiro (o BC250 cobre só o Brasil).",
                        "Banhados e zonas úmidas (como os do Taim), cobertura de campo nativo remanescente e conversão para lavoura e silvicultura: não incluídos; não há camada com licença aberta confirmada para este mapa (o MapBiomas só sai pelo Google Earth Engine).",
                        "Terras Indígenas e territórios quilombolas: não incluídos (limites oficiais da FUNAI indisponíveis)."],
            "fontes": FONTES}
