"""Receita do mapa temático do Pantanal: lê as bases oficiais (já descompactadas) e devolve o dicionário de data/mapas/pantanal.json.

Pasta de entrada (`raw`), com estas subpastas descompactadas:
  biomas/   IBGE, Biomas 1:250 000 (2025)            lml_bioma_e250k_v20250911_A.*
  cnuc/     MMA, CNUC edição 2025-08                 cnuc_2025_08.*
  locais/   IBGE, Localidades do Brasil 2022         BR_localidades_2022.*
  bc250/    IBGE, BC250 versão 2025 (hidrografia)    hid_trecho_drenagem_l.*, hid_massa_dagua_a.*
O zip da BC250 tem ~800 MB; dá para extrair só os arquivos hid_* lendo o zip por HTTP Range (o servidor aceita).
"""
import math, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import shp
from mapas_dados import dp, dp_ring, inside, dist_borda, toca, r3

FONTES = {
    "biomas": {"titulo": "IBGE, Biomas e Sistema Costeiro-Marinho do Brasil 1:250 000 (2025)",
               "url": "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/vetores/2025_Biomas-e-Sistema-Costeiro-Marinho-do-Brasil-1-250000_shp.zip",
               "data": "2025-09", "licenca": "dado público do IBGE (termo de licença não localizado)"},
    "cnuc": {"titulo": "MMA, Cadastro Nacional de Unidades de Conservação (CNUC), edição de agosto de 2025",
             "url": "https://dados.mma.gov.br/dataset/unidadesdeconservacao", "data": "2025-08", "licenca": "CC-BY"},
    "locais": {"titulo": "IBGE, Localidades do Brasil 2022",
               "url": "https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/localidades/Localidades_do_Brasil/2022/Localidades_Brasil_shp.zip",
               "data": "2022", "licenca": "dado público do IBGE (termo de licença não localizado)"},
    "bc250": {"titulo": "IBGE, Base Cartográfica Contínua do Brasil 1:250 000 (BC250), versão 2025: trechos de drenagem e massas d'água",
              "url": "https://geoftp.ibge.gov.br/cartas_e_mapas/bases_cartograficas_continuas/bc250/versao2025/shapefiles/bc_250_shapefiles_2026_03_03.zip",
              "data": "2026-03", "licenca": "dado público do IBGE (termo de licença não localizado)"},
}

MINUSC = {"de", "do", "da", "dos", "das", "e", "ao", "no", "na", "em"}
SIGLAS = {"sesc": "Sesc", "rppn": "RPPN", "apa": "APA"}
ROMANOS = {"i", "ii", "iii", "iv", "v", "vi"}


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


def receita(raw):
    b = [g for a, g in shp.read(f"{raw}/biomas/lml_bioma_e250k_v20250911_A") if a["NM_BIOMA"] == "Pantanal"][0]
    anel = max(b, key=len)
    xs, ys = [p[0] for p in anel], [p[1] for p in anel]
    bbox = (min(xs), min(ys), max(xs), max(ys)); box = (bbox[0] - .3, bbox[1] - .3, bbox[2] + .3, bbox[3] + .3)
    limite = dp_ring(anel, .004)
    camadas = []

    # --- Baías, lagoas, meandros e rios largos (massas d'água): nomeadas ou com área relevante
    TIPO = {"Rio": "rio", "Lago/Lagoa": "lagoa", "Baía": "baia", "Meandro abandonado": "meandro"}
    massas = []
    for a, g in shp.read(f"{raw}/bc250/hid_massa_dagua_a", box):
        if not inside(g[0][len(g[0]) // 2], anel): continue
        xs_, ys_ = [p[0] for p in g[0]], [p[1] for p in g[0]]
        if not a["nome"] and (max(xs_) - min(xs_)) * (max(ys_) - min(ys_)) < 6e-5: continue   # lagoas minúsculas sem nome ficam de fora
        rings = [q for q in (dp_ring(r, .0015) for r in g) if q]
        if rings: massas.append({"nome": a["nome"], "tipo": TIPO.get(a["tipomassad"], "outro"), "rings": [r3(q) for q in rings]})
    camadas.append({"id": "massas", "titulo": "Baías, lagoas e rios largos", "tipo": "poligono", "fonte": "bc250", "ligada": True,
                    "nota": "Água permanente mapeada na escala 1:250 000; lagoas sem nome só aparecem se maiores que ~0,5 km². Não mostra a área alagada na cheia.", "itens": massas})

    # --- Rios e córregos nomeados (trechos de drenagem): agrupados por nome, com o flag de navegabilidade POR TRECHO
    por_nome = {}
    for a, g in shp.read(f"{raw}/bc250/hid_trecho_drenagem_l", box):
        if not a["nome"]: continue
        for r in g:
            if len(r) > 1 and inside(r[len(r) // 2], anel):
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
    camadas.append({"id": "rios", "titulo": "Rios e córregos nomeados", "tipo": "linha", "fonte": "bc250", "ligada": True,
                    "nota": "Trechos nomeados com mais de 60 km dentro do bioma. Nomes iguais (ex.: Rio Negro) são somados; a navegabilidade vale para cada trecho.", "itens": rios})

    # --- Unidades de conservação (CNUC): polígonos que tocam o bioma
    ucs = []
    for a, g in shp.read(f"{raw}/cnuc/cnuc_2025_08", box):
        if not toca(g, anel): continue
        rings = [q for q in (dp_ring(r, .004) for r in g) if q]
        if not rings: continue
        ucs.append({"nome": titulo(a["nome_uc"]), "categoria": a["categoria"], "grupo": "PI" if a["grupo"].startswith("Prote") else "US",
                    "esfera": a["esfera"], "uf": a["uf"], "ha": round(float(a["ha_total"] or 0)), "ano": a["cria_ano"][-4:] if a["cria_ano"] else "",
                    "rings": [r3(q) for q in rings]})
    ucs.sort(key=lambda u: -u["ha"])
    camadas.append({"id": "ucs", "titulo": "Unidades de conservação", "tipo": "poligono", "fonte": "cnuc", "ligada": True,
                    "nota": "Inclui federais, estaduais, municipais e RPPNs que tocam o bioma; na exibição são recortadas pelo limite do Pantanal.", "itens": ucs})

    # --- Localidades IBGE
    cid, pov = [], []
    for a, g in shp.read(f"{raw}/locais/BR_localidades_2022", box):
        p = g[0]; d = a["CT_LOCALID"]
        if d == "Cidade" and a["SCT_LOCALI"] == "Sede Municipal" and (inside(p, anel) or dist_borda(p, anel) < .12):
            cid.append({"nome": a["NM_LOCALID"], "uf": a["SIGLA_UF"], "pt": [round(p[0], 3), round(p[1], 3)]})
        elif d in ("Localidade Indígena", "Localidade Quilombola") and inside(p, anel):
            pov.append({"nome": a["NM_LOCALID"], "uf": a["SIGLA_UF"], "tipo": "indigena" if "Ind" in d else "quilombola", "pt": [round(p[0], 3), round(p[1], 3)]})
    camadas.append({"id": "cidades", "titulo": "Sedes municipais", "tipo": "ponto", "fonte": "locais", "ligada": True,
                    "nota": "Sedes municipais dentro do bioma ou a até ~13 km do limite.", "itens": cid})
    camadas.append({"id": "povos", "titulo": "Localidades indígenas e quilombolas", "tipo": "ponto", "fonte": "locais", "ligada": False,
                    "nota": "Pontos de localidades do Censo 2022 (IBGE). Não são os limites das Terras Indígenas nem dos territórios quilombolas.", "itens": pov})

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
    return {"id": "pantanal", "titulo": "Mapa do Pantanal: água, áreas protegidas e povos",
            "bbox": [round(v, 3) for v in bbox], "limite": r3(limite), "camadas": camadas, "filtros": filtros,
            "lacunas": ["Planície alagável e cheia × seca: a camada oficial de terrenos sujeitos a inundação do IBGE (hid_terreno_sujeito_inundacao_a) não tem feições no Pantanal, e 4.363 das 4.373 massas d'água do bioma estão classificadas como permanentes; falta uma base sazonal (opção: MapBiomas Água, via Google Earth Engine, a validar).",
                        "Terras Indígenas (FUNAI): o servidor oficial tem a cadeia de certificados inválida; é preciso baixar o shapefile manualmente (geoserver.funai.gov.br, camada tis_poligonais)."],
            "fontes": FONTES}
