"""Mapas temáticos das páginas de bioma: planos (2D), com camadas e filtros. Nada a ver com o HERO MAP da home.

Entrada:  data/mapas/<bioma>.json (gerado por build/mapas_dados.py a partir de bases oficiais; ver build/receitas/).
Saída:    - seção HTML (`secao_html`): painel recolhível de camadas e filtros, legenda, listas acessíveis, fontes e lacunas;
          - assets/mapas/<bioma>.json (`dados_cliente`): geometrias já projetadas e fundidas em poucos <path>, carregado
            só quando a seção chega perto da tela (src/mapa-tematico.js).
Sem three.js, sem bibliotecas: SVG + JS puro. A projeção é própria (equiretangular local, x · cos φ), não a grade do HERO MAP.

Camadas especiais (contexto cartográfico): "paises" (preenchimento por país + fronteiras + nomes) e "estados" (divisas + nomes);
o resto é genérico: poligono (ucs, massas), linha (rios) e ponto (cidades, povos).
"""
import html, json, math, os

E = lambda s: html.escape(str(s), quote=True)
LARGURA = 4000   # unidades do viewBox; os caminhos usam inteiros relativos


def carregar(root, id):
    p = os.path.join(root, "data", "mapas", id + ".json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


class Proj:
    def __init__(self, bbox, pad=.03):
        x0, y0, x1, y1 = bbox
        dx, dy = (x1 - x0) * pad, (y1 - y0) * pad
        self.x0, self.y1, self.x1, self.y0 = x0 - dx, y1 + dy, x1 + dx, y0 - dy
        self.c = math.cos(math.radians((y0 + y1) / 2))
        self.k = LARGURA / ((x1 - x0 + 2 * dx) * self.c)
        self.w = LARGURA; self.h = round((y1 - y0 + 2 * dy) * self.k)
        self.u_por_km = self.k / 111.32   # unidades do viewBox por km (1° de latitude ≈ 111,32 km)

    def __call__(self, lon, lat):
        return round((lon - self.x0) * self.c * self.k), round((self.y1 - lat) * self.k)


def caminho(P, aneis, fechar):
    """'M x y l dx dy …' com inteiros relativos; descarta pontos repetidos após o arredondamento."""
    out = []
    for r in aneis:
        pts = [P(*p) for p in r]
        lim = [pts[0]]
        for q in pts[1:]:
            if q != lim[-1]: lim.append(q)
        if len(lim) < (3 if fechar else 2): continue
        s = f"M{lim[0][0]} {lim[0][1]}l" + " ".join(f"{b[0] - a[0]} {b[1] - a[1]}" for a, b in zip(lim, lim[1:]))
        out.append(s + ("z" if fechar else ""))
    return "".join(out)


def grade(P, passo=2):
    """Meridianos e paralelos a cada `passo` graus (retas nesta projeção) e rótulos nas bordas."""
    lon0, lon1, lat0, lat1 = P.x0, P.x1, P.y0, P.y1
    lons = [v for v in range(math.ceil(lon0 / passo) * passo, math.floor(lon1) + 1, passo) if lon0 < v < lon1]
    lats = [v for v in range(math.ceil(lat0 / passo) * passo, math.floor(lat1) + 1, passo) if lat0 < v < lat1]
    linhas = [[(v, lat0), (v, lat1)] for v in lons] + [[(lon0, v), (lon1, v)] for v in lats]
    rot = [{"t": f"{abs(v)}°{'O' if v < 0 else 'L'}", "p": [P(v, lat1)[0], 0], "eixo": "x"} for v in lons] + \
          [{"t": f"{abs(v)}°{'S' if v < 0 else 'N'}", "p": [0, P(lon0, v)[1]], "eixo": "y"} for v in lats]
    return {"d": caminho(P, linhas, False), "rotulos": rot}


def aneis(x):
    """Aceita um anel [[lon, lat], …] ou uma lista de anéis; devolve sempre a lista de anéis."""
    return [] if not x else (x if isinstance(x[0][0], (list, tuple)) else [x])


def dados_cliente(d):
    """JSON para o navegador: tudo projetado; massas d'água fundidas por tipo e rios por navegabilidade (poucos <path>)."""
    P = Proj(d["bbox"]); cam = []
    for c in d["camadas"]:
        o = {k: c[k] for k in ("id", "titulo", "tipo", "ligada", "nota", "fonte")}
        it = c["itens"]
        if c["id"] == "paises":
            o["itens"] = [{"nome": i["nome"], "d": caminho(P, i["rings"], True), "p": list(P(*i["rotulo"])) if i.get("rotulo") else None} for i in it]
            o["front"] = caminho(P, c.get("fronteiras", []), False)
        elif c["id"] in ("estados", "ecorregioes"):   # divisas com nomes (ecorregioes: só contornos, sem preenchimento)
            o["rotulos"] = [{"nome": i["nome"], "p": list(P(*i["rotulo"]))} for i in it if i.get("rotulo")]
            o["fills"] = [{"d": caminho(P, i["rings"], True), "i": i.get("cor", 0)} for i in it if i.get("rings")]   # estados pintados (cada um com sua cor); o bioma é desenhado por cima, de uma cor só
            o["front"] = caminho(P, c.get("fronteiras", []), False)
        elif c["tipo"] == "cobertura":   # cobertura (ex.: floresta remanescente): polígonos fundidos num caminho só
            o["d"] = caminho(P, [r for i in it for r in i["rings"]], True)
        elif c["id"] == "massas":
            g = {}
            for m in it: g.setdefault(m["tipo"], []).append(m["rings"])
            o["grupos"] = [{"tipo": t, "d": caminho(P, [r for rs in v for r in rs], True)} for t, v in g.items()]
        elif c.get("por_rio"):   # rios individuais (a camada "amazonas" é a fixa; "rios" são os afluentes, que entram nos filtros)
            # cada rio é um elemento próprio, com atributos para os filtros (valores múltiplos separados por "|", ex.: países e estados que ele atravessa)
            fixos = c.get("fixos", [])
            o["grupos"] = [{"nome": r["nome"], "attrs": r["attrs"], "fixo": r["attrs"].get("margem") in fixos, "texto": r.get("texto", ""), "d": caminho(P, r["linhas"], False)} for r in it]
            o["rotulos"] = [{"nome": r["nome"], "p": list(P(*r["rotulo"])), "attrs": r["attrs"], "fixo": r["attrs"].get("margem") in fixos} for r in it if r.get("rotulo")]
        elif c["id"] == "rios" and c.get("campo_grupo"):
            # rios agrupados por um campo próprio (ex.: margem do Amazonas); os valores em `fixos` (ex.: o rio principal) ignoram os filtros
            campo, fixos = c["campo_grupo"], c.get("fixos", [])
            vals = []
            for r in it:
                if r["g"] not in vals: vals.append(r["g"])
            o["grupos"] = [{"campo": campo, "v": v, "fixo": v in fixos, "d": caminho(P, [l for r in it if r["g"] == v for l in r["linhas"]], False)} for v in vals]
            o["rotulos"] = [{"nome": r["nome"], "p": list(P(*r["rotulo"])), "campo": campo, "v": r["g"], "fixo": r["g"] in fixos} for r in it if r.get("rotulo")]
        elif c["id"] == "rios":
            # navegável / não navegável (Brasil, por trecho) / "ext": rios de fora do Brasil, sem informação de navegabilidade
            o["grupos"] = [{"navegavel": v, "d": caminho(P, [l for r in it for l in r.get(k, [])], False)} for k, v in (("nav", "sim"), ("nao", "nao"), ("ext", "ext"))]
            nav = lambda r: "sim" if tuple(r["rotulo"]) in {tuple(p) for l in r.get("nav", []) for p in l} else "nao"   # o rótulo segue o filtro da linha onde está
            o["rotulos"] = [{"nome": r["nome"], "p": list(P(*r["rotulo"])), "navegavel": nav(r)} for r in it if r.get("rotulo")]
        elif c["tipo"] == "poligono":
            o["itens"] = [{**{k: i[k] for k in i if k != "rings"}, "d": caminho(P, i["rings"], True)} for i in it]
        else:
            o["itens"] = [{**{k: i[k] for k in i if k != "pt"}, "p": list(P(*i["pt"]))} for i in it]
        cam.append(o)
    return {"w": P.w, "h": P.h, "upk": round(P.u_por_km, 3), "limite": caminho(P, aneis(d["limite"]), True),
            "contorno": caminho(P, d.get("limite_contorno", []), False),   # contorno externo do bioma (linhas abertas), quando o limite vem de várias peças
            "limite_oficial": caminho(P, aneis(d.get("limite_oficial", [])), True), "oceano": bool(d.get("oceano")), "limite_nome": d.get("limite_nome", "Limite do bioma"),
            "limite_oficial_nome": d.get("limite_oficial_nome", ""), "grade": grade(P), "camadas": cam, "filtros": d["filtros"]}


def n_pt(n):
    return f"{n:,}".replace(",", ".")


def secao_html(d, nome_bioma):
    """Casca da seção: o SVG é montado pelo JS; sem JS ficam as listas, as fontes e as lacunas."""
    id = d["id"]
    por_id = {c["id"]: c for c in d["camadas"]}
    # camadas opcionais; "lista" = só as UCs que entram na lista em texto (as demais ficam fundidas no desenho)
    ucs = por_id["ucs"].get("lista", por_id["ucs"]["itens"]) if "ucs" in por_id else []
    cidades = por_id["cidades"]["itens"] if "cidades" in por_id else []
    povos = por_id["povos"]["itens"] if "povos" in por_id else []
    tis = por_id["tis"]["itens"] if "tis" in por_id else []
    afl = por_id["rios"]["itens"] if "rios" in por_id and por_id["rios"].get("lista") else []   # lista dos afluentes (camada com "lista": True)
    ligados = "".join(
        f'<label class="mt-chk"><input type="checkbox" data-camada="{E(c["id"])}"{" checked" if c["ligada"] else ""}> {E(c["titulo"])}</label>'
        for c in d["camadas"] if not c.get("fixa")) + '<label class="mt-chk"><input type="checkbox" data-camada="grade"> Grade de coordenadas</label>'   # camadas "fixas" não têm caixa de seleção: sempre aparecem
    filtros = "".join(
        f'<fieldset class="mt-filtro" data-filtro="{E(f["id"])}" data-camada="{E(f["camada"])}" data-campo="{E(f["campo"])}"><legend>{E(f["titulo"])}</legend>'
        + "".join(f'<label><input type="radio" name="mt-{E(id)}-{E(f["id"])}" value="{E(v)}"{" checked" if i == 0 else ""}> {E(t)}</label>' for i, (v, t) in enumerate(f["opcoes"]))
        + "</fieldset>" for f in d["filtros"])

    def tabela(cid, cab, linhas):
        return (f'<div class="mt-tw"><table class="mt-tab" data-camada="{cid}"><thead><tr>' + "".join(f'<th scope="col">{c}</th>' for c in cab)
                + f'</tr></thead><tbody>{linhas}</tbody></table></div>')
    t_uc = tabela("ucs", ["Nome", "Categoria", "Proteção", "Esfera", "UF", "Área (ha)", "Criada em"], "".join(
        f'<tr data-grupo="{E(u["grupo"])}" data-esfera="{E(u["esfera"])}"><th scope="row">{E(u["nome"])}</th><td>{E(u["categoria"])}</td>'
        f'<td>{"Proteção integral" if u["grupo"] == "PI" else "Uso sustentável"}</td><td>{E(u["esfera"])}</td><td>{E(u["uf"].title())}</td>'
        f'<td class="n">{n_pt(u["ha"])}</td><td>{E(u["ano"])}</td></tr>' for u in ucs))
    t_cid = tabela("cidades", ["Sede municipal", "UF"], "".join(f'<tr><th scope="row">{E(i["nome"])}</th><td>{E(i["uf"])}</td></tr>' for i in sorted(cidades, key=lambda i: i["nome"])))
    t_pov = tabela("povos", ["Localidade", "Tipo", "UF"], "".join(
        f'<tr data-tipo="{E(i["tipo"])}"><th scope="row">{E(i["nome"])}</th><td>{"Indígena" if i["tipo"] == "indigena" else "Quilombola"}</td><td>{E(i["uf"])}</td></tr>'
        for i in sorted(povos, key=lambda i: i["nome"])))
    if afl:
        MARGEM = {"esquerda": "esquerda (norte)", "direita": "direita (sul)"}; TRECHO = {"brasileiro": "dentro do Brasil (IBGE)", "estrangeiro": "fora do Brasil (Natural Earth)"}
        if any("bacia" in i["attrs"] for i in afl):   # rios agrupados por bacia hidrográfica (ex.: Cerrado)
            t_afl = tabela("rios", ["Rio", "Bacia hidrográfica", "Países", "Estados do Brasil"], "".join(
                f'<tr data-bacia="{E(i["attrs"]["bacia"])}"><th scope="row">{E(i["nome"])}</th><td>{E(i["attrs"]["bacia"])}</td>'
                f'<td>{E(", ".join(i.get("paises", [])))}</td><td>{E(", ".join(i.get("estados", [])))}</td></tr>' for i in sorted(afl, key=lambda i: i["nome"])))
        elif any("regime" in i["attrs"] for i in afl):   # rios classificados pelo regime (ex.: Caatinga)
            t_afl = tabela("rios", ["Rio", "Regime", "Curso sem vazão natural (Q95 = 0)", "Estados do Brasil"], "".join(
                f'<tr data-regime="{E(i["attrs"]["regime"])}"><th scope="row">{E(i["nome"])}</th><td>{E(i["classe"])}</td>'
                f'<td class="n">{i["pct_seco"]}%</td><td>{E(", ".join(i.get("estados", [])))}</td></tr>' for i in sorted(afl, key=lambda i: (-i["pct_seco"], i["nome"]))))
        else:
            t_afl = tabela("rios", ["Afluente", "Margem", "Trecho no mapa", "Países", "Estados do Brasil"], "".join(
                f'<tr data-margem="{E(i["attrs"]["margem"])}" data-origem="{E(i["attrs"]["origem"])}"><th scope="row">{E(i["nome"])}</th><td>{E(MARGEM.get(i["attrs"]["margem"], ""))}</td>'
                f'<td>{E(TRECHO.get(i["attrs"]["origem"], ""))}</td><td>{E(", ".join(i.get("paises", [])))}</td><td>{E(", ".join(i.get("estados", [])))}</td></tr>'
                for i in sorted(afl, key=lambda i: i["nome"])))
    listas = ""
    if afl: listas += '<details class="mt-det" open><summary>%s (%d) em lista</summary><p class="cap">A lista segue os filtros do mapa. Países e estados vêm dos limites do Natural Earth (aproximados).</p>%s</details>\n' % (por_id["rios"].get("lista_titulo", "Afluentes"), len(afl), t_afl)
    if ucs:
        nota = por_id["ucs"].get("nota_lista", "")
        listas += '<details class="mt-det"><summary>Unidades de conservação (%d) em lista</summary>%s%s</details>\n' % (len(ucs), ('<p class="cap">' + E(nota) + "</p>") if nota else "", t_uc)
    if tis: listas += '<details class="mt-det"><summary>Terras Indígenas (%d) em lista</summary>%s</details>\n' % (len(tis), t_ti)
    if cidades: listas += '<details class="mt-det"><summary>Cidades (%d) em lista</summary>%s</details>\n' % (len(cidades), t_cid)
    if povos: listas += '<details class="mt-det"><summary>Localidades indígenas e quilombolas (%d) em lista</summary>%s</details>\n' % (len(povos), t_pov)
    t_ti = tabela("tis", ["Terra Indígena", "Povo", "Situação"], "".join(
        f'<tr data-situacao="{E(i["situacao"])}"><th scope="row">{E(i["nome"])}</th><td>{E(i["povo"])}</td><td>{E(i["fase"])}</td></tr>' for i in sorted(tis, key=lambda i: i["nome"]))) if tis else ""
    fontes = "".join(
        f'<li><a href="{E(f["url"])}" target="_blank" rel="noopener">{E(f["titulo"])}</a> — dados de {E(f["data"])}; {E(f["licenca"])}.</li>' for f in d["fontes"].values())
    notas = "".join(f'<li><b>{E(c["titulo"])}:</b> {E(c["nota"])}</li>' for c in d["camadas"])
    lacunas = "".join(f"<li>{E(x)}</li>" for x in d.get("lacunas", []))
    curtos = []   # nomes curtos das instituições (a lista completa, com licenças, fica em "Sobre os dados deste mapa")
    for f in d["fontes"].values():
        n = f["titulo"].split(": ")[0].split(", ")[0].split(" (")[0]
        if n not in curtos: curtos.append(n)
    fontes_curtas = "Fontes: " + "; ".join(E(n) for n in curtos) + ". Detalhes e licenças em «Sobre os dados deste mapa»."
    return f"""<figure class="mt" data-mapa="{E(id)}">
<details class="mt-painel"><summary>Camadas e filtros</summary>
<div class="mt-ctl">
<fieldset class="mt-camadas"><legend>Camadas</legend>{ligados}</fieldset>
<div class="mt-filtros">{filtros}</div>
</div>
</details>
<div class="mt-vp" role="group" aria-label="{E(d.get("titulo", "Mapa temático"))}. Mapa visual; as listas abaixo trazem os mesmos dados em texto.">
<p class="mt-msg" role="status">Carregando o mapa…</p>
</div>
<div class="mt-leg" aria-hidden="true"></div>
<p class="mt-info" role="status" aria-live="polite">Toque ou passe o mouse sobre uma unidade de conservação, sede ou localidade para ver os detalhes.</p>
<figcaption class="cap">{E(d.get("titulo", ""))}. Mapa plano, sem zoom: use as camadas e os filtros. {E(d.get("aviso_escopo", ""))} <span class="mt-fonte-curta">{fontes_curtas}</span></figcaption>
{listas}<details class="mt-det"><summary>Sobre os dados deste mapa</summary>
<ul class="mt-fonte">{notas}</ul>
<h4>Fontes</h4><ul class="mt-fonte">{fontes}</ul>
<h4>Lacunas por validar</h4><ul class="mt-fonte">{lacunas}</ul>
</details>
<noscript><p class="cap">O mapa precisa de JavaScript; as listas e as fontes acima funcionam sem ele.</p></noscript>
</figure>"""
