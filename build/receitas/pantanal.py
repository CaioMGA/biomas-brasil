"""Receita do mapa temático do Pantanal INTEIRO (Brasil, Bolívia e Paraguai): lê as bases já descompactadas e devolve o dicionário de data/mapas/pantanal.json.

Pasta de entrada (`raw`), com estas subpastas/arquivos:
  biomas/    IBGE, Biomas 1:250 000 (2025)            lml_bioma_e250k_v20250911_A.*      (limite oficial da parte brasileira)
  cnuc/      MMA, CNUC edição 2025-08                 cnuc_2025_08.*
  locais/    IBGE, Localidades do Brasil 2022         BR_localidades_2022.*
  bc250/     IBGE, BC250 versão 2025 (hidrografia)    hid_trecho_drenagem_l.*, hid_massa_dagua_a.*
  resolve.json   RESOLVE Ecoregions 2017, ECO_NAME='Pantanal' (GeoJSON do FeatureServer; ver FONTES["resolve"])
  ne_10m_admin_0_countries/, ne_10m_admin_0_boundary_lines_land/, ne_10m_admin_1_states_provinces/, ne_10m_populated_places/,
  ne_rivers/ne_10m_rivers_lake_centerlines   Natural Earth 1:10m (domínio público)
O zip da BC250 tem ~800 MB; dá para extrair só os arquivos hid_* lendo o zip por HTTP Range (build/httpzip.py).

Fora do Brasil não há UCs nem hidrografia detalhada: WDPA (Protected Planet) não permite redistribuir e o HydroRIVERS tem licença
própria com restrição de redistribuição; por isso fora do Brasil o mapa traz o limite, países, estados, sedes (Natural Earth) e rios
principais (Natural Earth, sem nomes: a base chama o Rio Paraguai de "Paraná").
"""
import json, math, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import shp
from mapas_dados import dp, dp_ring, inside, dist_borda, toca, r3, recorta_anel, corta_linha

PUB = "dado público do IBGE (termo de licença não localizado)"
FONTES = {
    "resolve": {"titulo": "RESOLVE Ecoregions 2017 (Dinerstein et al., 2017, BioScience), ecorregião Pantanal: limite do bioma inteiro, com Bolívia e Paraguai",
                "url": "https://ecoregions.appspot.com/", "data": "2017", "licenca": "CC BY 4.0"},
    "biomas": {"titulo": "IBGE, Biomas e Sistema Costeiro-Marinho do Brasil 1:250 000 (2025): limite oficial da parte brasileira",
               "url": "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/vetores/2025_Biomas-e-Sistema-Costeiro-Marinho-do-Brasil-1-250000_shp.zip", "data": "2025-09", "licenca": PUB},
    "bc250": {"titulo": "IBGE, Base Cartográfica Contínua do Brasil 1:250 000 (BC250), versão 2025: trechos de drenagem e massas d'água",
              "url": "https://geoftp.ibge.gov.br/cartas_e_mapas/bases_cartograficas_continuas/bc250/versao2025/shapefiles/bc_250_shapefiles_2026_03_03.zip", "data": "2026-03", "licenca": PUB},
    "cnuc": {"titulo": "MMA, Cadastro Nacional de Unidades de Conservação (CNUC), edição de agosto de 2025",
             "url": "https://dados.mma.gov.br/dataset/unidadesdeconservacao", "data": "2025-08", "licenca": "CC-BY"},
    "locais": {"titulo": "IBGE, Localidades do Brasil 2022: sedes municipais e localidades indígenas e quilombolas",
               "url": "https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/localidades/Localidades_do_Brasil/2022/Localidades_Brasil_shp.zip", "data": "2022", "licenca": PUB},
    "ne": {"titulo": "Natural Earth 1:10 milhões: países, fronteiras, estados e departamentos, lugares povoados e rios principais",
           "url": "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/", "data": "2022", "licenca": "domínio público"},
}

MINUSC = {"de", "do", "da", "dos", "das", "e", "ao", "no", "na", "em"}
SIGLAS = {"sesc": "Sesc", "rppn": "RPPN", "apa": "APA"}
ROMANOS = {"i", "ii", "iii", "iv", "v", "vi"}
PAISES = {"BRA", "BOL", "PRY", "ARG"}


def titulo(nome):
    """MAIÚSCULAS do CNUC → nome legível; RPPN e APA viram sigla (rótulos mais curtos)."""
    t = " ".join(nome.lower().split())
    for longo, sigla in (("reserva particular do patrimônio natural", "rppn"), ("reserva particular do patrimonio natural", "rppn"),
                         ("reserva particular dopatrimonio natural", "rppn"), ("área de proteção ambiental", "apa")):
        if t.startswith(longo): t = sigla + t[len(longo):]; break
    out = []
    for i, w in enumerate(t.split(" ")):
        out.append(SIGLAS.get(w) or (w.upper() if w in ROMANOS and i else w if (w in MINUSC and i) else w.capitalize()))
    return " ".join(out)


def centro(rings, bbox, n=36):
    """Rótulo no ponto do trecho visível mais distante das bordas ("polo de inacessibilidade", busca em grade).
    O centro da caixa não serve: o Brasil envolve o mapa pelo norte e pelo leste e o centro cairia sobre a Bolívia."""
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


def receita(raw):
    # ---- a região: ecorregião inteira (RESOLVE) + limite oficial do IBGE na parte brasileira
    g = json.load(open(f"{raw}/resolve.json", encoding="utf-8"))["features"][0]["geometry"]
    polis = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    res_aneis = [[tuple(p) for p in pol[0]] for pol in polis]
    ibge = [g for a, g in shp.read(f"{raw}/biomas/lml_bioma_e250k_v20250911_A") if a["NM_BIOMA"] == "Pantanal"] and \
           max([g for a, g in shp.read(f"{raw}/biomas/lml_bioma_e250k_v20250911_A") if a["NM_BIOMA"] == "Pantanal"][0], key=len)
    todos = res_aneis + [ibge]
    xs, ys = [p[0] for r in todos for p in r], [p[1] for r in todos for p in r]
    reg = (min(xs), min(ys), max(xs), max(ys))
    P = .6   # folga em graus: o mapa mostra os arredores (países e estados vizinhos), não só o bioma
    bbox = (reg[0] - P, reg[1] - P, reg[2] + P, reg[3] + P); box = (bbox[0] - .3, bbox[1] - .3, bbox[2] + .3, bbox[3] + .3)
    dentro = lambda p: any(inside(p, r) for r in todos)
    limite = [r3(q) for q in (dp_ring(list(r), .004) for r in res_aneis) if q]
    oficial = [r3(dp_ring(ibge, .004))]
    camadas = []

    # ---- países (preenchimento, nome) e fronteiras entre eles; estados e departamentos
    paises, estados = [], []
    for a, gm in shp.read(f"{raw}/ne_10m_admin_0_countries/ne_10m_admin_0_countries", box):
        if a["ADM0_A3"] not in PAISES: continue
        rings = [q for q in (recorta_anel(r, box) for r in gm) if q]
        rings = [q for q in (dp_ring(r + [r[0]], .01) for r in rings) if q]
        if rings: paises.append({"nome": a["NAME_PT"], "rings": [r3(r) for r in rings], "rotulo": centro(rings, bbox)})
    fronteiras = [r3(dp(l, .01)) for a, gm in shp.read(f"{raw}/ne_10m_admin_0_boundary_lines_land/ne_10m_admin_0_boundary_lines_land", box) for ln in gm for l in corta_linha(ln, box)]
    camadas.append({"id": "paises", "titulo": "Fronteiras entre países", "tipo": "contexto", "fonte": "ne", "ligada": True,
                    "nota": "Países vizinhos com seu nome e uma cor para cada um; as fronteiras vêm do Natural Earth (escala 1:10 milhões) e podem divergir em detalhe dos limites oficiais.",
                    "itens": paises, "fronteiras": fronteiras})
    for a, gm in shp.read(f"{raw}/ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces", box):
        if a["adm0_a3"] not in PAISES: continue
        rings = [q for q in (recorta_anel(r, box) for r in gm) if q]
        if not rings: continue
        e = {"nome": a["name"], "lns": [l for r in gm for l in corta_linha([tuple(p) for p in r], box)], "rotulo": centro(rings, bbox)}
        if a["adm0_a3"] == "BRA":   # só os estados brasileiros são pintados; vértices (arredondados) servem para achar os vizinhos
            e["rings"] = [r3(q) for q in (dp_ring(list(r) + [r[0]], .01) for r in rings) if q]
            e["vert"] = {(round(p[0], 2), round(p[1], 2)) for r in gm for p in r}
        estados.append(e)
    br = [e for e in estados if "vert" in e]
    viz = {i: {j for j, f in enumerate(br) if j != i and len(e["vert"] & f["vert"]) >= 2} for i, e in enumerate(br)}
    cor = {}
    for i in sorted(viz, key=lambda i: -len(viz[i])):   # coloração gulosa: vizinhos nunca repetem cor (6 cores)
        usadas = {cor[j] for j in viz[i] if j in cor}; cor[i] = next(c for c in range(6) if c not in usadas)
    for i, e in enumerate(br): e["cor"] = cor[i]
    camadas.append({"id": "estados", "titulo": "Estados e departamentos", "tipo": "contexto", "fonte": "ne", "ligada": True,
                    "nota": "Divisas internas dos países (estados no Brasil, departamentos na Bolívia e no Paraguai, províncias na Argentina), Natural Earth 1:10 milhões. Os estados do Brasil são pintados em cores diferentes; o bioma é sempre de uma cor só.",
                    "itens": [{"nome": e["nome"], "rotulo": e["rotulo"], **({"rings": e["rings"], "cor": e["cor"]} if "rings" in e else {})} for e in estados],
                    "fronteiras": [r3(dp(l, .01)) for e in estados for l in e["lns"]]})

    # ---- baías, lagoas, meandros e rios largos (massas d'água; só Brasil): nomeadas ou com área relevante
    TIPO = {"Rio": "rio", "Lago/Lagoa": "lagoa", "Baía": "baia", "Meandro abandonado": "meandro"}
    massas = []
    for a, gm in shp.read(f"{raw}/bc250/hid_massa_dagua_a", box):
        if not dentro(gm[0][len(gm[0]) // 2]): continue
        xs_, ys_ = [p[0] for p in gm[0]], [p[1] for p in gm[0]]
        if not a["nome"] and (max(xs_) - min(xs_)) * (max(ys_) - min(ys_)) < 6e-5: continue   # lagoas minúsculas sem nome ficam de fora
        rings = [q for q in (dp_ring(r, .0015) for r in gm) if q]
        if rings: massas.append({"nome": a["nome"], "tipo": TIPO.get(a["tipomassad"], "outro"), "rings": [r3(q) for q in rings]})
    camadas.append({"id": "massas", "titulo": "Baías, lagoas e rios largos", "tipo": "poligono", "fonte": "bc250", "ligada": True,
                    "nota": "Só no Brasil. Água permanente mapeada na escala 1:250 000; lagoas sem nome só aparecem se maiores que ~0,5 km². Não mostra a área alagada na cheia.", "itens": massas})

    # ---- rios e córregos nomeados (trechos de drenagem; Brasil), com o flag de navegabilidade POR TRECHO
    por_nome = {}
    for a, gm in shp.read(f"{raw}/bc250/hid_trecho_drenagem_l", box):
        if not a["nome"]: continue
        for r in gm:
            if len(r) > 1 and dentro(r[len(r) // 2]):
                d = por_nome.setdefault(a["nome"], {"sim": [], "nao": []})
                d["sim" if a["navegavel"] == "Sim" else "nao"].append(dp(r, .003))
    rios = []
    for n, v in por_nome.items():
        todas = v["sim"] + v["nao"]
        km = sum(math.hypot((q[0] - p[0]) * .95, q[1] - p[1]) * 111 for l in todas for p, q in zip(l, l[1:]))
        if km < 60: continue   # só nomes com extensão relevante dentro do bioma (a rede completa deixava o mapa ilegível)
        rios.append({"nome": n, "km": round(km), "nav": [r3(l) for l in v["sim"]], "nao": [r3(l) for l in v["nao"]], "_todas": todas})
    rios.sort(key=lambda r: -r["km"])
    for r in [r for r in rios if r["nome"].startswith("Rio ")][:8]:   # rótulos só nos 8 maiores "Rio …", no meio do maior trecho
        l = max(r["_todas"], key=len); m = l[len(l) // 2]; r["rotulo"] = [round(m[0], 3), round(m[1], 3)]
    for r in rios: del r["_todas"]
    # fora do Brasil: rios principais do Natural Earth (linhas com ponto médio dentro da ecorregião e fora do limite do IBGE), SEM nome
    ext = []
    for a, gm in shp.read(f"{raw}/ne_rivers/ne_10m_rivers_lake_centerlines", box):
        for r in gm:
            if len(r) > 1 and any(inside(p, rr) for p in r[::3] for rr in res_aneis) and not inside(r[len(r) // 2], ibge): ext.append(r3(dp(r, .004)))
    rios.append({"nome": "Rios principais fora do Brasil (sem nome)", "km": 0, "nav": [], "nao": [], "ext": ext})
    camadas.append({"id": "rios", "titulo": "Rios e córregos", "tipo": "linha", "fonte": "bc250", "ligada": True,
                    "nota": "No Brasil: trechos nomeados com mais de 60 km dentro do bioma (nomes iguais são somados; a navegabilidade vale para cada trecho). Fora do Brasil: só os rios principais do Natural Earth, sem nome e sem informação de navegabilidade.",
                    "itens": rios})

    # ---- unidades de conservação (CNUC; só Brasil): polígonos que tocam o bioma
    ucs = []
    for a, gm in shp.read(f"{raw}/cnuc/cnuc_2025_08", box):
        if not (toca(gm, ibge) or any(toca(gm, r) for r in res_aneis)): continue
        rings = [q for q in (dp_ring(r, .004) for r in gm) if q]
        if not rings: continue
        ucs.append({"nome": titulo(a["nome_uc"]), "categoria": a["categoria"], "grupo": "PI" if a["grupo"].startswith("Prote") else "US",
                    "esfera": a["esfera"], "uf": a["uf"], "ha": round(float(a["ha_total"] or 0)), "ano": a["cria_ano"][-4:] if a["cria_ano"] else "",
                    "rings": [r3(q) for q in rings]})
    ucs.sort(key=lambda u: -u["ha"])
    camadas.append({"id": "ucs", "titulo": "Unidades de conservação", "tipo": "poligono", "fonte": "cnuc", "ligada": True,
                    "nota": "Só no Brasil: federais, estaduais, municipais e RPPNs que tocam o bioma. Bolívia e Paraguai ficam de fora porque a base mundial (WDPA) não permite redistribuição.", "itens": ucs})

    # ---- sedes municipais (IBGE, Brasil) + cidades da Bolívia, Paraguai e Argentina (Natural Earth); localidades indígenas e quilombolas (IBGE, Brasil)
    cid, pov = [], []
    for a, gm in shp.read(f"{raw}/locais/BR_localidades_2022", box):
        p = gm[0]; d = a["CT_LOCALID"]
        perto = dentro(p) or any(dist_borda(p, r) < .12 for r in todos)
        if d == "Cidade" and a["SCT_LOCALI"] == "Sede Municipal" and perto:
            cid.append({"nome": a["NM_LOCALID"], "uf": a["SIGLA_UF"], "pt": [round(p[0], 3), round(p[1], 3)]})
        elif d in ("Localidade Indígena", "Localidade Quilombola") and dentro(p):
            pov.append({"nome": a["NM_LOCALID"], "uf": a["SIGLA_UF"], "tipo": "indigena" if "Ind" in d else "quilombola", "pt": [round(p[0], 3), round(p[1], 3)]})
    for a, gm in shp.read(f"{raw}/ne_10m_populated_places/ne_10m_populated_places", box):
        p = gm[0]
        if a["ADM0_A3"] in ("BOL", "PRY", "ARG") and (dentro(p) or any(dist_borda(p, r) < .12 for r in todos)):
            cid.append({"nome": a["NAME"], "uf": a["ADM1NAME"], "pt": [round(p[0], 3), round(p[1], 3)]})
    camadas.append({"id": "cidades", "titulo": "Sedes municipais e cidades", "tipo": "ponto", "fonte": "locais", "ligada": True,
                    "nota": "No Brasil, sedes municipais (IBGE); na Bolívia, no Paraguai e na Argentina, as cidades do Natural Earth. Dentro do bioma ou a até ~13 km do limite.", "itens": cid})
    camadas.append({"id": "povos", "titulo": "Localidades indígenas e quilombolas", "tipo": "ponto", "fonte": "locais", "ligada": False,
                    "nota": "Só no Brasil. Pontos de localidades do Censo 2022 (IBGE). Não são os limites das Terras Indígenas nem dos territórios quilombolas.", "itens": pov})

    filtros = [
        {"id": "tipoagua", "titulo": "Corpo d'água", "camada": "massas", "campo": "tipo",
         "opcoes": [["", "Todos"], ["rio", "Rios largos"], ["lagoa", "Lagoas"], ["baia", "Baías"], ["meandro", "Meandros abandonados"]]},
        {"id": "navegavel", "titulo": "Rios e córregos", "camada": "rios", "campo": "navegavel",
         "opcoes": [["", "Todos"], ["sim", "Navegáveis"], ["nao", "Não navegáveis"]]},
        {"id": "grupo", "titulo": "Proteção", "camada": "ucs", "campo": "grupo",
         "opcoes": [["", "Todas"], ["PI", "Proteção integral"], ["US", "Uso sustentável"]]},
        {"id": "esfera", "titulo": "Esfera", "camada": "ucs", "campo": "esfera",
         "opcoes": [["", "Todas"], ["Federal", "Federal"], ["Estadual", "Estadual"], ["Municipal", "Municipal"]]},
        {"id": "tipo", "titulo": "Povos", "camada": "povos", "campo": "tipo",
         "opcoes": [["", "Todos"], ["indigena", "Indígenas"], ["quilombola", "Quilombolas"]]},
    ]
    return {"id": "pantanal", "secao_titulo": "Água, áreas protegidas e povos do Pantanal", "titulo": "Mapa do Pantanal inteiro (Brasil, Bolívia e Paraguai): água, áreas protegidas e povos",
            "aviso_escopo": "O limite cobre o Pantanal inteiro; as camadas detalhadas (rios com nome, lagoas, unidades de conservação, localidades) existem só para o lado brasileiro. Os dois limites (ecorregião RESOLVE e oficial do IBGE) vêm de bases diferentes e não coincidem exatamente.",
            "bbox": [round(v, 3) for v in bbox], "limite": limite, "limite_nome": "Pantanal (ecorregião, RESOLVE 2017)",
            "limite_oficial": oficial, "limite_oficial_nome": "Limite oficial no Brasil (IBGE 2025)",
            "camadas": camadas, "filtros": filtros,
            "lacunas": ["Unidades de conservação e hidrografia detalhada na Bolívia e no Paraguai: as bases livres encontradas não permitem redistribuição (WDPA) ou não têm nomes (HydroRIVERS); fontes nacionais (SERNAP, Bolívia; MADES, Paraguai) não foram pesquisadas.",
                        "Limites das Terras Indígenas: ainda não incluídos neste mapa; os pontos de localidades indígenas e quilombolas não substituem os limites oficiais.",
                        "Área alagada na cheia e diferença entre cheia e seca: o mapa mostra só a água permanente mapeada. A planície alagável sazonal ainda não está representada."],
            "fontes": FONTES}
