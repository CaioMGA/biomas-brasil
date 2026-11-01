"""Gera as páginas estáticas de conteúdo (hub, biomas, Brasil e Sobre) ao lado do index.html do mapa.
Chamado por build.py: gerar(root, dest_dir, br_path, brchad_uri). Plano em docs/plano-de-navegacao.md.
"""
import html, json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loader_path import brasil_path

E = html.escape
WPM, VIDEO_MIN, SPECIES_MIN, QUIZ_MIN = 200, 5, 2.5, 2
MES_LONGO = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
ORDEM = ["amazonia", "cerrado", "mata-atlantica", "caatinga", "pampa", "pantanal", "costeiro"]
CONTATO = {"email": "caiomga@gmail.com", "pessoal": "https://caiomga.com", "projetos": "https://brchad.com"}


# Centro de cada carimbo no sistema de coordenadas do contorno do Brasil (centroides dos biomas em data/ids.png, ajustados à mão)
POS = {"amazonia": (121, 87), "cerrado": (202, 162), "mata-atlantica": (216, 232), "caatinga": (268, 124), "pampa": (165, 296),
       "pantanal": (138, 196), "costeiro": (322, 222), "brasil": (64, 288)}


def passaporte(root, br_path):
    """Dados da folha do passaporte (contorno do Brasil e posição dos carimbos), para o mapa e para as páginas."""
    d, w, h = br_path
    nomes = {b["id"]: b["name"] for b in biomas_do_template(root)}
    regs = [{"id": i, "nome": "Brasil" if i == "brasil" else nomes[i], "pos": list(POS[i])} for i in ORDEM + ["brasil"]]
    return {"vb": [-24, -26, w + 136, h + 60], "d": d, "r": 44, "regs": regs}


def rmin(x):
    return max(1, int(x + 0.5))


def words(ps):
    return len(" ".join(ps).split()) / WPM


def fmt_min(m):
    return f"{m // 60} h {m % 60:02d} min" if m >= 60 else f"{m} min"


def fmt_n(n):
    return f"{n:,}".replace(",", ".")


def biomas_do_template(root):
    """Lê o array `const B = [...]` do template (JS) e devolve como lista de dicts, via node."""
    src = open(os.path.join(root, "src/template.html"), encoding="utf-8").read()
    bloco = re.search(r"^const B = \[.*?^\];", src, re.S | re.M).group(0)
    js = bloco + "\nprocess.stdout.write(JSON.stringify(B));"
    return json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)


def plano(id, c):
    """Seções da página, na mesma ordem e com os mesmos minutos do antigo modo leitura."""
    p = [{"id": s["id"], "titulo": s["titulo"], "min": rmin(words(s["p"])), "kind": "texto", "s": s} for s in c.get("secoes", [])]
    if c.get("especies"):
        p.append({"id": "especies", "titulo": "Fichas de espécies", "kind": "especies",
                  "min": rmin(len(c["especies"]) / 8 * SPECIES_MIN + words([e["d"] for e in c["especies"]]) * .6)})
    if c.get("videos"):
        p.append({"id": "videos", "titulo": "Vídeos" if len(c["videos"]) > 1 else "Vídeo", "min": len(c["videos"]) * VIDEO_MIN, "kind": "videos"})
    if c.get("leitura"):
        p.append({"id": "leitura", "titulo": "Leitura", "min": rmin(words([c["leitura"]["texto"]]) + 1), "kind": "leitura"})
    if id == "brasil":
        p.append({"id": "comparador", "titulo": "Comparador de biomas", "min": 3, "kind": "comparador"})
        if c.get("glossario"):
            p.append({"id": "glossario", "titulo": "Glossário", "min": rmin(words([g["d"] for g in c["glossario"]]) + 1), "kind": "glossario"})
        if c.get("linha"):
            p.append({"id": "linha", "titulo": "Linha do tempo", "min": rmin(words([g["t"] for g in c["linha"]]) + 1), "kind": "linha"})
    if c.get("quiz"):
        p.append({"id": "quiz", "titulo": "Quiz final" if id == "brasil" else "Quiz do bioma", "min": max(QUIZ_MIN, round(len(c["quiz"]) * .4)), "kind": "quiz"})
    if id == "brasil" and c.get("creditos"):
        p.append({"id": "creditos", "titulo": "Créditos e fontes", "min": 2, "kind": "creditos"})
    return p


class Site:
    def __init__(self, root, dest, br_path, brchad):
        self.root, self.dest = root, dest
        self.br_d, self.br_w, self.br_h = br_path
        self.brchad = brchad
        self.B = biomas_do_template(root)
        self.byId = {b["id"]: b for b in self.B}
        self.rain = json.load(open(os.path.join(root, "data/rain.json"), encoding="utf-8"))
        cdir = os.path.join(root, "data/conteudo")
        self.C = {f[:-5]: json.load(open(os.path.join(cdir, f), encoding="utf-8")) for f in sorted(os.listdir(cdir)) if f.endswith(".json")}
        self.outl = json.load(open(os.path.join(root, "data/outlines.json")))
        self.plan = {i: plano(i, self.C[i]) for i in self.C}
        self.total = {i: sum(s["min"] for s in p) for i, p in self.plan.items()}
        self.regioes = [self.regiao(i) for i in ["brasil"] + ORDEM if i in self.C]
        self.P = passaporte(root, br_path)

    # ---- dados de cada região ----
    def nome(self, id):
        return "Brasil" if id == "brasil" else self.byId[id]["name"]

    def cor(self, id):
        return "var(--ink)" if id == "brasil" else f"var(--c-{id})"

    def url(self, id):
        return "/brasil/" if id == "brasil" else f"/biomas/{id}/"

    def regiao(self, id):
        return {"id": id, "nome": self.nome(id), "intro": self.C[id].get("intro", ""), "min": self.total[id],
                "secoes": sum(1 for x in self.plan[id] if x["kind"] != "quiz"),   # o quiz não conta como seção lida
                "url": self.url(id), "cor": self.cor(id)}

    def silhueta(self, id):
        if id == "brasil":
            return f'<svg viewBox="-8 -8 {self.br_w + 14} {self.br_h + 14}" aria-hidden="true"><path d="{self.br_d}"/></svg>'
        n = self.byId[id]["n"]
        if self.byId[id].get("marine"):   # faixa litorânea: os contornos de outlines.json vêm em 169 pedaços, então traça a máscara
            d, w, h = brasil_path(self.root, F=4, eps=.8, ids={n})
            return f'<svg viewBox="0 0 {w} {h}" aria-hidden="true" preserveAspectRatio="xMidYMid meet"><path d="{d}"/></svg>'
        rings = [o for o in self.outl if o["n"] == n]
        if not rings:
            return ""
        xs = [v for o in rings for v in o["p"][0::2]]
        ys = [v for o in rings for v in o["p"][1::2]]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        d = "".join("M" + "L".join(f"{o['p'][i]},{o['p'][i + 1]}" for i in range(0, len(o["p"]), 2)) + "Z" for o in rings)
        pad = max(x1 - x0, y1 - y0) * .04
        return f'<svg viewBox="{x0 - pad:.0f} {y0 - pad:.0f} {x1 - x0 + 2 * pad:.0f} {y1 - y0 + 2 * pad:.0f}" aria-hidden="true" preserveAspectRatio="xMidYMid meet"><path d="{d}"/></svg>'

    # ---- peças de HTML ----
    def casca(self, titulo, descricao, corpo, ativo, accent="var(--ink)", dados=None, extra_body=""):
        nav = "".join(f'<a class="nav" href="{h}"{" aria-current=\"page\"" if k == ativo else ""}>{t}</a>'
                      for k, h, t in [("mapa", "/", "Mapa"), ("biomas", "/biomas/", "Biomas"), ("sobre", "/sobre/", "Sobre")])
        js = f'<script id="dados" type="application/json">{json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")}</script>\n' if dados else ""
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(titulo)}</title>
<meta name="description" content="{E(descricao)}">
<link rel="icon" type="image/svg+xml" href="/assets/icon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
</head>
<body style="--accent:{accent}">
<header class="topo"><a class="marca" href="/">Biomas do Brasil</a>{nav}</header>
{corpo}
{js}<script src="/assets/site.js"></script>
</body>
</html>
"""

    def foot(self):
        return (f'<div class="brfoot"><span>Site criado por Caio Amaral</span>'
                f'<img class="brchad" src="{self.brchad}" width="80" height="15" alt="brchad 2026"></div>')

    def creditos(self):
        c = self.C["brasil"]
        out = []
        for g in c["creditos"]:
            out.append(f'<h3 class="cred-h">{E(g["t"])}</h3><ul class="cred">')
            for x in g["i"]:
                nome = f'<a href="{E(x["u"])}" target="_blank" rel="noopener">{E(x["n"])}</a>' if x.get("u") else f'<b>{E(x["n"])}</b>'
                out.append(f'<li>{nome} — {E(x["d"])}</li>')
            out.append("</ul>")
        out.append('<h3 class="cred-h">Vídeos</h3><ul class="cred">')
        for k in self.C:
            for v in self.C[k].get("videos", []):
                out.append(f'<li><a href="https://www.youtube.com/watch?v={E(v["id"])}" target="_blank" rel="noopener">{E(v["titulo"])}</a> — {E(v["canal"])} ({E(self.nome(k))})</li>')
        out.append("</ul>")
        out.append('<p class="cap">Os vídeos pertencem aos respectivos canais e são exibidos pelo player oficial do YouTube. A escolha deles ainda precisa de aprovação editorial.</p>')
        out.append(f'<p class="cap">{E(c["creditos_nota"])}</p>')
        return "".join(out)

    def secao(self, id, i, n, s):
        c = self.C[id]
        h = (f'<h2><small>{i + 1} de {n}</small>{E(s["titulo"])}</h2>')
        k, corpo = s["kind"], ""
        if k == "texto":
            if s["s"].get("chuva") and id != "brasil":
                corpo += f'<div class="chuva-bioma" data-bioma="{id}"></div>'
            corpo += "".join(f"<p>{E(t)}</p>" for t in s["s"]["p"])
        elif k == "especies":
            corpo += '<div class="sp-grid">' + "".join(
                f'<div class="sp"><h3>{E(e["n"])}<small>{E(e["t"])}</small></h3><em>{E(e["c"])}</em><p>{E(e["d"])}</p></div>' for e in c["especies"]) + "</div>"
            corpo += '<p class="cap">Fotos de licença livre ainda não foram incluídas; use o nome científico para buscar imagens no Wikimedia Commons.</p>'
        elif k == "videos":
            corpo += '<div class="vid-grid">' + "".join(
                f'<figure class="vid"><button type="button" class="fr" data-yt="{E(v["id"])}" data-titulo="{E(v["titulo"])}" aria-label="Assistir: {E(v["titulo"])}" '
                f'style="background-image:url(https://i.ytimg.com/vi/{E(v["id"])}/hqdefault.jpg)"></button>'
                f'<figcaption><b>{E(v["titulo"])}</b> · {E(v["canal"])} · {E(v["tipo"])}{" · " + E(v["dur"]) if v.get("dur") else ""} · '
                f'<a href="https://www.youtube.com/watch?v={E(v["id"])}" target="_blank" rel="noopener" style="color:inherit">abrir no YouTube</a></figcaption></figure>' for v in c["videos"]) + "</div>"
            corpo += '<p class="cap">Vídeos de terceiros, incorporados do YouTube só quando você clica.</p>'
        elif k == "leitura":
            L = c["leitura"]
            corpo += f'<blockquote class="lit">{E(L["texto"])}<cite>{E(L["autor"])}, {E(L["obra"])} (domínio público)</cite></blockquote>'
        elif k == "comparador":
            corpo += '<div id="comparador"></div>'
        elif k == "glossario":
            corpo += '<dl class="gl">' + "".join(f"<dt>{E(g['t'])}</dt><dd>{E(g['d'])}</dd>" for g in c["glossario"]) + "</dl>"
        elif k == "linha":
            corpo += '<ul class="tl">' + "".join(f"<li><b>{E(g['a'])}</b>{E(g['t'])}</li>" for g in c["linha"]) + "</ul>"
        elif k == "quiz":
            corpo += '<div id="quiz" class="quiz"></div>'
        elif k == "creditos":
            corpo += self.creditos()
        return f'<section id="sec-{s["id"]}">{h}{corpo}<div data-end="{s["id"]}" aria-hidden="true"></div></section>'

    # ---- páginas ----
    def pagina_conteudo(self, id):
        c, p = self.C[id], self.plan[id]
        nome = self.nome(id)
        kicker = "País" if id == "brasil" else ("Sistema" if self.byId[id].get("marine") else "Bioma")
        toc = "".join(f'<a href="#sec-{s["id"]}" data-sec="{s["id"]}">{E(s["titulo"])}</a>' for s in p)
        secs = "".join(self.secao(id, i, len(p), s) for i, s in enumerate(p))
        fontes = f'<p class="rd-src">{E(c["fontes"])}</p>' if c.get("fontes") else ""
        corpo = f"""<div class="rd-bar"><i></i></div>
<div class="rd-wrap">
<nav class="rd-toc" aria-label="Seções">{toc}</nav>
<main class="rd-main">
<p class="kicker">{kicker}</p>
<h1>{E(nome)}</h1>
<p class="intro">{E(c.get("intro", ""))}</p>
<p><span class="tm" style="color:var(--muted);font-size:14px">{fmt_min(self.total[id])} de leitura</span></p>
<a class="voltar" href="/#{"" if id == "brasil" else id}">← Ver no mapa</a>
{secs}{fontes}
</main>
</div>
<section class="prox" id="proximos" aria-label="Continue explorando"></section>
<div class="rodape">{self.foot()}</div>"""
        dados = {"id": id, "regioes": self.regioes, "passaporte": self.P, "chuva": {k: {"mm": v["mm"], "ano": v["ano"], "seco": v["seco"], "pico": v["pico"]} for k, v in self.rain.items()}, "plano": [{"id": s["id"], "kind": s["kind"]} for s in p], "quiz": c.get("quiz", [])}
        if id == "brasil":
            dados["bio"] = [{k: b.get(k) for k in ("id", "name", "km", "pct", "sp", "climate", "veg", "states", "spp")} for b in self.B]
        desc = c.get("intro", "") or f"{nome}: conteúdo do site Biomas do Brasil."
        return self.casca(f"{nome} — Biomas do Brasil", desc, corpo, "biomas" if id != "brasil" else "biomas", self.cor(id), dados)

    def cartao(self, r):
        return (f'<li><a class="card" href="{r["url"]}" data-id="{r["id"]}" style="--col:{r["cor"]}">{self.silhueta(r["id"])}'
                f'<h3>{E(r["nome"])}</h3><p>{E(r["intro"])}</p>'
                f'<span class="meta"><span class="estado"></span></span></a></li>')

    def hub(self):
        corpo = f"""<div class="hub">
<div class="hub-topo">
<div>
<p class="kicker">Conteúdo</p>
<h1>Biomas do Brasil</h1>
<p class="intro">Seis biomas continentais e o sistema costeiro-marinho, em textos, espécies, vídeos e quizzes. Comece por onde tiver mais curiosidade.</p>
</div>
<div class="pass-bloco" id="passaporte"></div>
</div>
<ul class="cards">{"".join(self.cartao(r) for r in self.regioes)}</ul>
</div>
<div class="rodape">{self.foot()}</div>"""
        return self.casca("Biomas — Biomas do Brasil", "Todos os biomas do Brasil e o sistema costeiro-marinho: textos, espécies, vídeos e quizzes.", corpo, "biomas", "var(--ink)", {"id": "hub", "regioes": self.regioes, "passaporte": self.P})

    def sobre(self):
        c = self.C["brasil"]
        tecno = [
            ("Mapa 3D", "three.js e shaders próprios, com relevo real e um efeito de fundo para cada bioma."),
            ("Relevo", "Terrain Tiles da AWS (SRTM, GMTED e ETOPO1), reamostrados para a grade do mapa."),
            ("Dados geográficos", "Biomas, estados e áreas do IBGE (via geobr/Ipea); rios e cidades do Natural Earth 1:10m; chuva do WorldClim 2.1."),
            ("Build", "Python gera o mapa e estas páginas estáticas a partir de um template e dos dados em JSON."),
            ("Hospedagem", "Cloudflare Pages."),
        ]
        lt = "".join(f"<dt>{E(a)}</dt><dd>{E(b)}</dd>" for a, b in tecno)
        corpo = f"""<div class="rd-wrap simples">
<main class="rd-main">
<p class="kicker">Sobre</p>
<h1>Como foi feito</h1>
<p class="intro">Um mapa 3D dos biomas do Brasil e uma biblioteca de textos para ler sem passar por ele.</p>
<section id="sec-tecnologias"><h2>Tecnologias</h2><dl class="gl">{lt}</dl></section>
<section id="sec-creditos"><h2>Dados, fontes e créditos</h2>{self.creditos()}</section>
<section id="sec-contato"><h2>Contato</h2>
<p>Site criado por Caio Amaral.</p>
<ul class="contato">
<li><a href="mailto:{CONTATO['email']}">{CONTATO['email']}</a></li>
<li><a href="{CONTATO['pessoal']}" target="_blank" rel="noopener">caiomga.com</a> — site pessoal</li>
<li><a href="{CONTATO['projetos']}" target="_blank" rel="noopener">brchad.com</a> — projetos</li>
</ul></section>
</main>
</div>
<div class="rodape">{self.foot()}</div>"""
        return self.casca("Sobre — Biomas do Brasil", "Tecnologias, dados, créditos e contato do site Biomas do Brasil.", corpo, "sobre")

    def escrever(self):
        def w(rel, txt):
            p = os.path.join(self.dest, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8").write(txt)
        for id in self.C:
            w(self.url(id).strip("/") + "/index.html", self.pagina_conteudo(id))
        w("biomas/index.html", self.hub())
        w("sobre/index.html", self.sobre())
        os.makedirs(os.path.join(self.dest, "assets"), exist_ok=True)
        rd = lambda f: open(os.path.join(self.root, f), encoding="utf-8").read()
        open(os.path.join(self.dest, "assets/site.css"), "w", encoding="utf-8").write(rd("src/pagina.css") + "\n" + rd("src/comum.css"))
        open(os.path.join(self.dest, "assets/site.js"), "w", encoding="utf-8").write(rd("src/comum.js") + "\n" + rd("src/pagina.js"))
        for src, dst in (("data/icon.svg", "assets/icon.svg"), ("brchad-2026.png", "assets/brchad.png")):
            shutil.copy(os.path.join(self.root, src), os.path.join(self.dest, dst))


def gerar(root, dest, br_path):
    s = Site(root, dest, br_path, "/assets/brchad.png")
    s.escrever()
    print("páginas:", ", ".join(s.url(i) for i in s.C), "/biomas/ /sobre/")
