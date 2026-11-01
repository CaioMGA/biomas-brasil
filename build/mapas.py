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
        elif c["id"] == "estados":
            o["rotulos"] = [{"nome": i["nome"], "p": list(P(*i["rotulo"]))} for i in it if i.get("rotulo")]
            o["fills"] = [{"d": caminho(P, i["rings"], True), "i": i.get("cor", 0)} for i in it if i.get("rings")]   # estados pintados (cada um com sua cor); o bioma é desenhado por cima, de uma cor só
            o["front"] = caminho(P, c.get("fronteiras", []), False)
        elif c["id"] == "massas":
            g = {}
            for m in it: g.setdefault(m["tipo"], []).append(m["rings"])
            o["grupos"] = [{"tipo": t, "d": caminho(P, [r for rs in v for r in rs], True)} for t, v in g.items()]
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
            "limite_oficial": caminho(P, aneis(d.get("limite_oficial", [])), True), "limite_nome": d.get("limite_nome", "Limite do bioma"),
            "limite_oficial_nome": d.get("limite_oficial_nome", ""), "grade": grade(P), "camadas": cam, "filtros": d["filtros"]}


def n_pt(n):
    return f"{n:,}".replace(",", ".")


def secao_html(d, nome_bioma):
    """Casca da seção: o SVG é montado pelo JS; sem JS ficam as listas, as fontes e as lacunas."""
    id = d["id"]
    por_id = {c["id"]: c for c in d["camadas"]}
    ucs, cidades, povos = (por_id[k]["itens"] for k in ("ucs", "cidades", "povos"))
    ligados = "".join(
        f'<label class="mt-chk"><input type="checkbox" data-camada="{E(c["id"])}"{" checked" if c["ligada"] else ""}> {E(c["titulo"])}</label>'
        for c in d["camadas"]) + '<label class="mt-chk"><input type="checkbox" data-camada="grade"> Grade de coordenadas</label>'
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
<details class="mt-det"><summary>Unidades de conservação ({len(ucs)}) em lista</summary>{t_uc}</details>
<details class="mt-det"><summary>Sedes municipais ({len(cidades)}) em lista</summary>{t_cid}</details>
<details class="mt-det"><summary>Localidades indígenas e quilombolas ({len(povos)}) em lista</summary>{t_pov}</details>
<details class="mt-det"><summary>Sobre os dados deste mapa</summary>
<ul class="mt-fonte">{notas}</ul>
<h4>Fontes</h4><ul class="mt-fonte">{fontes}</ul>
<h4>Lacunas por validar</h4><ul class="mt-fonte">{lacunas}</ul>
</details>
<noscript><p class="cap">O mapa precisa de JavaScript; as listas e as fontes acima funcionam sem ele.</p></noscript>
</figure>"""
