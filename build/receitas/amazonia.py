"""Receita do mapa temático da AMAZÔNIA: um mapa só sobre o Rio Amazonas e seus afluentes (decisão do projeto: a Amazônia é grande demais para
camadas de UCs, Terras Indígenas ou desmatamento). Lê as bases já descompactadas e devolve o dicionário de data/mapas/amazonia.json.

Pasta de entrada (`raw`):
  resolve_am/amazonia.json   RESOLVE Ecoregions 2017, 24 ecorregiões de floresta úmida e várzea da bacia (GeoJSON do FeatureServer; ver ECO_IDS)
  biomas/                    IBGE, Biomas 1:250 000 (2025)           lml_bioma_e250k_v20250911_A.*   (limite oficial da parte brasileira)
  bc250/                     IBGE, BC250 versão 2025                 hid_trecho_drenagem_l.{shp,shx,dbf,cpg}  (rios nomeados, só o Brasil)
  ne_10m_admin_0_countries/, ne_10m_admin_0_boundary_lines_land/, ne_10m_admin_1_states_provinces/, ne_10m_populated_places/,
  ne_rivers/ne_10m_rivers_lake_centerlines   Natural Earth 1:10m (domínio público)

O limite fora do Brasil vem da união das ecorregiões RESOLVE (uma aproximação do bioma amazônico, não o limite oficial); o limite RAISG tem licença
própria (uso não lucrativo, dados "sem alteração") e não permite redistribuir recortes simplificados.
"""
import json, math, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import shp
from mapas_dados import dp, dp_ring, inside, dist_borda, r3, recorta_anel, corta_linha, Mascara, contorno_externo

PUB = "dado público do IBGE (termo de licença não localizado)"
FONTES = {
    "resolve": {"titulo": "RESOLVE Ecoregions 2017 (Dinerstein et al., 2017, BioScience), 24 ecorregiões de floresta úmida e várzea da bacia amazônica: limite aproximado do bioma inteiro",
                "url": "https://ecoregions.appspot.com/", "data": "2017", "licenca": "CC BY 4.0"},
    "biomas": {"titulo": "IBGE, Biomas e Sistema Costeiro-Marinho do Brasil 1:250 000 (2025): limite oficial da parte brasileira",
               "url": "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/vetores/2025_Biomas-e-Sistema-Costeiro-Marinho-do-Brasil-1-250000_shp.zip", "data": "2025-09", "licenca": PUB},
    "bc250": {"titulo": "IBGE, Base Cartográfica Contínua do Brasil 1:250 000 (BC250), versão 2025: trechos de drenagem nomeados",
              "url": "https://geoftp.ibge.gov.br/cartas_e_mapas/bases_cartograficas_continuas/bc250/versao2025/shapefiles/bc_250_shapefiles_2026_03_03.zip", "data": "2026-03", "licenca": PUB},
    "ne": {"titulo": "Natural Earth 1:10 milhões: países, fronteiras, estados e departamentos e rios fora do Brasil",
           "url": "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/", "data": "2022", "licenca": "domínio público"},
}
PAISES = {"BRA", "PER", "COL", "ECU", "VEN", "GUY", "SUR", "BOL", "FRA"}   # FRA: só a Guiana Francesa (os outros polígonos da França ficam fora da caixa)
ECO_IDS = "446,463,464,465,466,467,469,473,474,476,480,482,483,484,496,497,498,503,505,507,508,511,512,518"
SEM_ESTADO = set()

# Rios do Brasil (IBGE BC250), por nome. O nome sozinho não basta (há "Rio Negro", "Rio Branco", "Rio Madeira"… em outras bacias): cada rio só vale
# dentro de uma caixa (lon0, lat0, lon1, lat1) que cobre o curso real. Os dois primeiros formam o canal principal; a margem dos demais é calculada.
BR_RIOS = {
    "Rio Amazonas": (-60.0, -3.8, -49.8, -0.5), "Rio Solimões": (-70.3, -4.7, -59.7, -2.2), "Canal do Norte": (-52.2, -1.8, -48.8, 1.6),
    "Rio Negro": (-70.2, -3.5, -59.5, 2.3), "Rio Branco": (-64.5, -1.6, -59.0, 4.0), "Rio Japurá": (-69.8, -3.5, -64.4, -1.2), "Rio Içá": (-69.9, -3.4, -67.8, -2.7),
    "Rio Trombetas": (-57.4, -2.1, -55.3, 1.2), "Rio Uatumã": (-60.8, -2.8, -57.4, -0.2), "Rio Nhamundá": (-59.1, -2.4, -56.3, 0.2),
    "Rio Paru": (-56.2, -1.7, -52.4, 2.6), "Rio Jari": (-54.8, -1.4, -51.2, 2.3),
    "Rio Madeira": (-66.0, -9.5, -58.0, -3.2), "Rio Purus": (-70.8, -9.8, -61.2, -3.6), "Rio Juruá": (-73.1, -9.6, -62.0, -2.5), "Rio Javari": (-73.6, -7.6, -69.8, -4.2),
    "Rio Jutaí": (-72.0, -7.5, -66.5, -2.4), "Rio Tefé": (-67.2, -5.6, -64.4, -3.2), "Rio Coari": (-65.6, -5.9, -62.7, -3.8),
    "Rio Tapajós": (-58.7, -7.5, -54.5, -2.3), "Rio Juruena": (-59.4, -15.0, -57.8, -7.1), "Rio Teles Pires": (-56.2, -14.0, -55.0, -7.0),
    "Rio Xingu": (-53.8, -13.0, -51.4, -1.3), "Rio Iriri": (-54.8, -9.6, -52.2, -3.6),
    "Rio Acre": (-70.7, -11.3, -67.2, -8.6), "Rio Guaporé": (-65.6, -16.0, -59.0, -11.3), "Rio Mamoré": (-65.6, -12.1, -64.8, -10.1), "Rio Aripuanã": (-61.0, -11.9, -59.0, -5.0),
}
PRINCIPAL = ("Rio Amazonas", "Rio Solimões", "Canal do Norte (foz do Amazonas)")   # o Canal do Norte é a principal saída do Amazonas para o Atlântico, ao longo de Macapá
RENOMEAR = {"Canal do Norte": "Canal do Norte (foz do Amazonas)"}
# Rios fora do Brasil (Natural Earth): nome na base → nome em português. "principal": o Marañón e o Ucayali formam o Amazonas; a parte peruana do "Amazonas" também.
ESTRANGEIROS = {"Marañón": ("Rio Marañón", True), "Ucayali": ("Rio Ucayali", True), "Amazonas": ("Rio Amazonas (Peru)", True),
                "Napo": ("Rio Napo", False), "Putumayo": ("Rio Putumayo (Içá)", False), "Caquetá": ("Rio Caquetá (Japurá)", False),
                "Madre de Dios": ("Rio Madre de Dios", False), "Beni": ("Rio Beni", False), "Guaporé": ("Rio Guaporé (Itenez)", False),
                "Mamoré": ("Rio Mamoré (Bolívia)", False)}


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
    return sum(math.hypot((q[0] - p[0]) * .97, q[1] - p[1]) * 111 for l in linhas for p, q in zip(l, l[1:]))


def receita(raw):
    # ---- a região: união das ecorregiões RESOLVE (bioma amazônico inteiro) + limite oficial do IBGE na parte brasileira
    feats = json.load(open(f"{raw}/resolve_am/amazonia.json", encoding="utf-8"))["features"]
    res_aneis = []
    for f in feats:
        g = f["geometry"]; polis = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        res_aneis += [[tuple(p) for p in pol[0]] for pol in polis]
    xs, ys = [p[0] for r in res_aneis for p in r], [p[1] for r in res_aneis for p in r]
    reg = (min(xs), min(ys), max(xs), max(ys))
    ibge = [r for a, g in shp.read(f"{raw}/biomas/lml_bioma_e250k_v20250911_A") if a["NM_BIOMA"] == "Amazônia" for r in g]
    ibge = [r for r in ibge if reg[0] - .5 < sum(p[0] for p in r) / len(r) < reg[2] + .5 and reg[1] - .5 < sum(p[1] for p in r) / len(r) < reg[3] + .5]
    P = .6
    bbox = (reg[0] - P, reg[1] - P, reg[2] + P, reg[3] + P); box = (bbox[0] - .3, bbox[1] - .3, bbox[2] + .3, bbox[3] + .3)
    dx, dy = (bbox[2] - bbox[0]) * .05 + .2, (bbox[3] - bbox[1]) * .05 + .2
    vbox = (bbox[0] - dx, bbox[1] - dy, bbox[2] + dx, bbox[3] + dy)   # a terra é recortada numa caixa maior que a moldura (sem faixas de "oceano")
    mask_res = Mascara(res_aneis, reg, .02)
    mask_br = Mascara(ibge, reg, .02)                      # só o Brasil (para decidir quando usar o IBGE e quando o Natural Earth)
    mask = Mascara(res_aneis + ibge, reg, .02)
    limite = [r3(q) for q in (dp_ring(list(r), .06) for r in res_aneis) if q]
    contorno = [r3(l) for l in contorno_externo([[tuple(p) for p in r] for r in limite], mask_res, passo=.1, folga=.06)]
    oficial = [r3(q) for q in (dp_ring(list(r), .04) for r in ibge) if q]
    camadas = []

    # ---- países, fronteiras, estados e departamentos (estados do Brasil em cores diferentes)
    paises, estados = [], []
    for a, gm in shp.read(f"{raw}/ne_10m_admin_0_countries/ne_10m_admin_0_countries", vbox):
        if a["ADM0_A3"] not in PAISES: continue
        rings = [q for q in (recorta_anel(r, vbox) for r in gm) if q]
        rings = [q for q in (dp_ring(r + [r[0]], .03) for r in rings) if q]
        if rings: paises.append({"nome": "Guiana Francesa" if a["ADM0_A3"] == "FRA" else a["NAME_PT"], "rings": [r3(r) for r in rings], "rotulo": centro(rings, bbox)})
    fronteiras = [r3(dp(l, .03)) for a, gm in shp.read(f"{raw}/ne_10m_admin_0_boundary_lines_land/ne_10m_admin_0_boundary_lines_land", vbox) for ln in gm for l in corta_linha(ln, vbox)]
    camadas.append({"id": "paises", "titulo": "Fronteiras entre países", "tipo": "contexto", "fonte": "ne", "ligada": True,
                    "nota": "Países da bacia com seu nome e uma cor para cada um; as fronteiras vêm do Natural Earth (escala 1:10 milhões) e podem divergir em detalhe dos limites oficiais.",
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
                    "nota": "Divisas internas dos países (estados no Brasil, departamentos e regiões nos vizinhos), Natural Earth 1:10 milhões. Os estados do Brasil são pintados em cores diferentes; o bioma é sempre de uma cor só.",
                    "itens": [{"nome": e["nome"], "rotulo": e["rotulo"], **({"rings": e["rings"], "cor": e["cor"]} if "rings" in e else {})} for e in estados],
                    "fronteiras": [r3(dp(l, .03)) for e in estados for l in e["lns"]]})

    # ---- rios: o canal principal e os afluentes. Brasil: IBGE pelo nome, dentro da caixa de cada rio. Fora do Brasil: Natural Earth.
    achados, origem = {}, {}   # origem: "brasileiro" (trecho do IBGE, dentro do Brasil) ou "estrangeiro" (trecho do Natural Earth, fora do Brasil)
    for a, gm in shp.read_por_nome(f"{raw}/bc250/hid_trecho_drenagem_l", "nome", set(BR_RIOS)):
        b = BR_RIOS[a["nome"]]
        for l in gm:
            m = l[len(l) // 2]
            if len(l) > 1 and b[0] <= m[0] <= b[2] and b[1] <= m[1] <= b[3]: (achados.setdefault(RENOMEAR.get(a["nome"], a["nome"]), []).append(dp(l, .02)), origem.__setitem__(RENOMEAR.get(a["nome"], a["nome"]), "brasileiro"))
    for a, gm in shp.read(f"{raw}/ne_rivers/ne_10m_rivers_lake_centerlines", box):
        n = a["name"]
        if n not in ESTRANGEIROS or a["featurecla"] != "River": continue
        for l in gm:   # a linha do Natural Earth pode cruzar a fronteira (ex.: o Amazonas do Peru ao Brasil): fica só o pedaço fora do Brasil e dentro da região
            ponta = []
            for v in l + [None]:
                if v is not None and mask(*v) and not mask_br(*v): ponta.append(v)
                else:
                    if len(ponta) > 1: achados.setdefault(ESTRANGEIROS[n][0], []).append(dp(ponta, .03)); origem[ESTRANGEIROS[n][0]] = "estrangeiro"
                    ponta = []
    # canal principal (referência para a margem): Marañón/Ucayali → Amazonas (Peru) → Solimões → Amazonas
    principais = [l for n in ("Rio Marañón", "Rio Ucayali", "Rio Amazonas (Peru)") + PRINCIPAL for l in achados.get(n, [])]
    # referência da margem: só o trecho que corre para leste (Amazonas do Peru, Solimões e Amazonas); o Marañón e o Ucayali correm para o norte e não servem
    ref_l = [l for n in ("Rio Amazonas (Peru)",) + PRINCIPAL for l in achados.get(n, [])]
    canal = sorted([p for l in ref_l for p in l], key=lambda p: p[0])   # a direção "para jusante" é a de longitude crescente
    amostra_canal = canal[::3]
    def margem(ls):
        """Margem do afluente: de que lado do canal fica a sua foz (o ponto dele mais perto do canal). O rio corre para leste: esquerda = norte.
        A direção do canal é suavizada (média dos vértices a oeste e a leste da foz): o canal tem braços e ilhas, e a direção de dois vértices vizinhos é instável."""
        q, lon0, melhor = None, None, 1e9
        for l in ls:
            for p in l[::4]:
                for v in amostra_canal:
                    d = (p[0] - v[0]) ** 2 + (p[1] - v[1]) ** 2
                    if d < melhor: melhor, q, lon0 = d, p, v[0]
        media = lambda pts: (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        def janela(lo, hi):
            pts = [v for v in canal if lo <= v[0] <= hi]
            return pts
        for larg in (.6, 1.2, 2.5, 5.0):
            oeste, leste, meio = janela(lon0 - larg, lon0 - .2 * larg), janela(lon0 + .2 * larg, lon0 + larg), janela(lon0 - .2 * larg, lon0 + .2 * larg)
            if (oeste or leste) and meio: break
        a_, b_ = media(oeste or meio), media(leste or meio); ref = media(meio)
        cruz = (b_[0] - a_[0]) * (q[1] - ref[1]) - (b_[1] - a_[1]) * (q[0] - ref[0])
        return "esquerda" if cruz > 0 else "direita"
    # por quais países e estados do Brasil cada rio passa (máscaras raster dos polígonos: teste O(1) por ponto)
    m_pais = {p["nome"]: Mascara([[tuple(q) for q in r_] for r_ in p["rings"]], vbox, .02) for p in paises}
    m_uf = {e["nome"]: Mascara([[tuple(q) for q in r_] for r_ in e["rings"]], vbox, .02) for e in estados if "rings" in e}
    def onde(ls, mascaras):
        pts = [p for l in ls for p in l[::max(1, len(l) // 40)]]
        return [n for n, m in mascaras.items() if sum(m(*p) for p in pts) >= max(2, .04 * len(pts))]   # ignora toques de uma ponta só (rios que correm na fronteira)
    lista = lambda xs: xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " e " + xs[-1]
    rios = []
    for nome, ls in achados.items():
        principal = nome in PRINCIPAL or any(nome == v[0] and v[1] for v in ESTRANGEIROS.values())
        grupo = "principal" if principal else margem(ls)
        paises_rio = sorted(onde(ls, m_pais), key=lambda n: (n != "Brasil", n)); estados_rio = sorted(onde(ls, m_uf))
        quem = "canal principal do sistema (Marañón/Ucayali → Solimões → Amazonas)" if principal else f"afluente da margem {grupo} ({'norte' if grupo == 'esquerda' else 'sul'}), ou subafluente de um afluente"
        texto = f"{nome} — {quem}. Passa por: {lista(paises_rio) if paises_rio else 'não identificado'}." + (f" Estados do Brasil: {lista(estados_rio)}." if estados_rio else "")
        rios.append({"nome": nome, "km": round(km(ls)), "linhas": [r3(l) for l in ls], "texto": texto, "paises": paises_rio, "estados": estados_rio,
                     "attrs": {"margem": grupo, "paises": "|".join(paises_rio), "estados": "|".join(estados_rio)}})
    rios.sort(key=lambda r_: -r_["km"])
    principais_l = [r_ for r_ in rios if r_["attrs"]["margem"] == "principal"]; afluentes = [r_ for r_ in rios if r_["attrs"]["margem"] != "principal"]
    for r_ in afluentes: r_["attrs"] = {"margem": r_["attrs"]["margem"], "origem": origem[r_["nome"]]}   # o que entra nos filtros; países e estados ficam só no texto de cada rio
    for r_ in principais_l: r_["attrs"] = {"margem": "principal"}
    for r_ in afluentes[:16] + principais_l:   # rótulos: os 16 maiores afluentes e o canal principal, no meio do maior trecho
        ls = max((l for l in [[tuple(p) for p in l] for l in r_["linhas"]]), key=len); m = ls[len(ls) // 2]; r_["rotulo"] = [round(m[0], 3), round(m[1], 3)]
    camadas.append({"id": "amazonas", "titulo": "Rio Amazonas (canal principal)", "tipo": "linha", "fonte": "bc250", "ligada": True, "fixa": True, "por_rio": True, "fixos": ["principal"],
                    "nota": "Sempre aparece, sem caixa de seleção nem filtro: Marañón e Ucayali (que formam o Amazonas no Peru) → Amazonas do Peru → Solimões → Amazonas → Canal do Norte, a principal saída para o Atlântico, ao longo de Macapá. Toque no rio para ver por onde ele passa.",
                    "itens": principais_l})
    camadas.append({"id": "rios", "titulo": "Afluentes", "tipo": "linha", "fonte": "bc250", "ligada": True, "por_rio": True, "lista": True,
                    "nota": "Afluentes principais e alguns subafluentes (Branco, Acre, Guaporé…). O filtro \"Afluentes\" separa os brasileiros (trechos dentro do Brasil, da drenagem do IBGE) dos estrangeiros (trechos fora do Brasil, do Natural Earth): um rio que cruza a fronteira, como o Japurá/Caquetá, aparece nos dois, cada um com o seu trecho. A margem (esquerda = norte) é calculada pela posição da foz em relação ao canal. Toque num rio para ver por quais países e estados ele passa (a partir dos limites do Natural Earth, aproximados). O Tocantins e o Araguaia não entram: desaguam no estuário do Pará, não no Amazonas.",
                    "itens": afluentes})

    filtros = [{"id": "origem", "titulo": "Afluentes", "camada": "rios", "campo": "origem",
                "opcoes": [["", "Todos os afluentes"], ["brasileiro", "Afluentes brasileiros"], ["estrangeiro", "Afluentes estrangeiros"]]},
               {"id": "margem", "titulo": "Margem do Amazonas", "camada": "rios", "campo": "margem",
                "opcoes": [["", "Todas"], ["esquerda", "Margem esquerda (norte)"], ["direita", "Margem direita (sul)"]]}]
    return {"id": "amazonia", "oceano": True, "secao_titulo": "Afluentes do Rio Amazonas", "titulo": "O Rio Amazonas e seus afluentes (bioma amazônico inteiro, em nove países)",
            "aviso_escopo": "Este mapa trata só do Rio Amazonas e dos afluentes principais. O limite do bioma é uma aproximação (ecorregiões RESOLVE) com o limite oficial do IBGE por cima no Brasil; os dois vêm de bases diferentes e não coincidem exatamente.",
            "bbox": [round(v, 3) for v in bbox], "limite": limite, "limite_contorno": contorno, "limite_nome": "Amazônia (ecorregiões, RESOLVE 2017)",
            "limite_oficial": oficial, "limite_oficial_nome": "Limite oficial no Brasil (IBGE 2025)",
            "camadas": camadas, "filtros": filtros,
            "lacunas": ["Cidades, unidades de conservação, Terras Indígenas e desmatamento: não incluídos por escolha do projeto (a Amazônia é grande demais para essas camadas num mapa só); este mapa é só sobre o Rio Amazonas e seus afluentes.",
                        "Limite oficial da Amazônia fora do Brasil: o limite da RAISG tem licença própria (uso não lucrativo, dados sem alteração) e não permite redistribuir recortes simplificados; o mapa usa a união de 24 ecorregiões RESOLVE como aproximação.",
                        "Rios em detalhe fora do Brasil: só os rios principais do Natural Earth; o Brasil usa a drenagem do IBGE."],
            "fontes": FONTES}
