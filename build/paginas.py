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
       "pantanal": (138, 196), "costeiro": (322, 222), "brasil": (52, 292)}


def _dp(pts, eps):
    """Douglas-Peucker (iterativo) em uma lista de pontos."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True; st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop(); (x1, y1), (x2, y2) = pts[a], pts[b]; L = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** .5 or 1
        dm, im = 0, -1
        for i in range(a + 1, b):
            dd = abs((y2 - y1) * pts[i][0] - (x2 - x1) * pts[i][1] + x2 * y1 - y2 * x1) / L
            if dd > dm: dm, im = dd, i
        if dm > eps and im > 0:
            keep[im] = True; st += [(a, im), (im, b)]
    return [p for p, k in zip(pts, keep) if k]


def contornos_biomas(root, x0, y0, eps=1.1, min_size=5):
    """Contorno dos 6 biomas continentais (data/outlines.json) no sistema de coordenadas do contorno do Brasil, como um caminho SVG."""
    from PIL import Image
    m = json.load(open(os.path.join(root, "data/map.json")))
    k = Image.open(os.path.join(root, "data/ids.png")).width / m["w"] / 6   # coordenadas do mapa -> mesma grade do contorno do Brasil (build/loader_path.py)
    out = []
    for r in json.load(open(os.path.join(root, "data/outlines.json"))):
        if not 1 <= r["n"] <= 6:
            continue
        pts = [(r["p"][i] * k - x0, r["p"][i + 1] * k - y0) for i in range(0, len(r["p"]), 2)]
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        if max(max(xs) - min(xs), max(ys) - min(ys)) < min_size:   # ilhotas viram ruído na folha
            continue
        h2 = len(pts) // 2   # anel fechado: simplifica as duas metades separadamente
        pts = _dp(pts[:h2 + 1], eps)[:-1] + _dp(pts[h2:] + [pts[0]], eps)[:-1]
        if len(pts) >= 3:
            out.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(out)


def passaporte(root, br_path):
    """Dados da folha do passaporte (contorno do Brasil, contorno dos biomas e posição dos carimbos), para o mapa e para as páginas."""
    d, w, h = br_path[:3]
    _, _, _, x0, y0 = brasil_path(root, with_offset=True)
    nomes = {b["id"]: b["name"] for b in biomas_do_template(root)}
    regs = [{"id": i, "nome": "Brasil" if i == "brasil" else nomes[i], "pos": list(POS[i])} for i in ORDEM + ["brasil"]]
    return {"vb": [-24, -26, w + 136, h + 60], "d": d, "bio": contornos_biomas(root, x0, y0), "r": 44, "regs": regs}


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
    p.append({"id": "creditos", "titulo": "Créditos e fontes", "min": 2 if id == "brasil" else 1, "kind": "creditos"})   # última seção de todas as páginas
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
        for b in self.B:   # textos do painel (estados, clima, vegetação…) vêm dos JSONs
            b.update(self.C.get(b["id"], {}).get("painel", {}))
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
                      for k, h, t in [("mapa", "/", "Mapa"), ("biomas", "/biomas/", "Biomas"), ("sobre", "/sobre/", "Sobre"), ("tutorial", "/?tutorial", "Tutorial")])
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

    @staticmethod
    def dobra(titulo, conteudo, extra=""):
        """Bloco dobrável (details) que começa fechado; o título é um h2 dentro do summary."""
        return f'<details class="creditos-dobra"><summary><h2>{extra}{E(titulo)}</h2></summary>{conteudo}</details>'

    def creditos(self, id=None):
        """Créditos e fontes. Com id de bioma, lista só os vídeos dele e inclui a frase de fontes da página; sem id (Brasil, Sobre, hub), todos os vídeos."""
        c = self.C["brasil"]
        so = id if id and id != "brasil" else None
        out = []
        for g in c["creditos"]:
            out.append(f'<h3 class="cred-h">{E(g["t"])}</h3><ul class="cred">')
            for x in g["i"]:
                nome = f'<a href="{E(x["u"])}" target="_blank" rel="noopener">{E(x["n"])}</a>' if x.get("u") else f'<b>{E(x["n"])}</b>'
                out.append(f'<li>{nome} — {E(x["d"])}</li>')
            out.append("</ul>")
        out.append('<h3 class="cred-h">Vídeos</h3><ul class="cred">')
        for k in ([so] if so else self.C):
            for v in self.C[k].get("videos", []):
                out.append(f'<li><a href="https://www.youtube.com/watch?v={E(v["id"])}" target="_blank" rel="noopener">{E(v["titulo"])}</a> — {E(v["canal"])} ({E(self.nome(k))})</li>')
        out.append("</ul>")
        out.append('<p class="cap">Os vídeos pertencem aos respectivos canais e são exibidos pelo player oficial do YouTube. A escolha deles ainda precisa de aprovação editorial.</p>')
        out.append(f'<p class="cap">{E(c["creditos_nota"])}</p>')
        page = self.C.get(id or "brasil", {}).get("fontes")
        if page:
            out.append(f'<p class="cap">{E(page)}</p>')
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
            corpo += self.creditos(id)
        if k == "creditos":   # dobrável, começa fechado; o sentinela de leitura fica fora do bloco para continuar visível quando ele está fechado
            return f'<section id="sec-{s["id"]}">{self.dobra(s["titulo"], corpo, f"<small>{i + 1} de {n}</small>")}<div data-end="{s["id"]}" aria-hidden="true"></div></section>'
        return f'<section id="sec-{s["id"]}">{h}{corpo}<div data-end="{s["id"]}" aria-hidden="true"></div></section>'

    # ---- páginas ----
    def pagina_conteudo(self, id):
        c, p = self.C[id], self.plan[id]
        nome = self.nome(id)
        kicker = "País" if id == "brasil" else ("Sistema" if self.byId[id].get("marine") else "Bioma")
        toc = "".join(f'<a href="#sec-{s["id"]}" data-sec="{s["id"]}">{E(s["titulo"])}</a>' for s in p)
        secs = "".join(self.secao(id, i, len(p), s) for i, s in enumerate(p))
        corpo = f"""<div class="rd-bar"><i></i></div>
<div class="rd-wrap">
<nav class="rd-toc" aria-label="Seções">{toc}</nav>
<main class="rd-main">
<p class="kicker">{kicker}</p>
<h1>{E(nome)}</h1>
<p class="intro">{E(c.get("intro", ""))}</p>
<p><span class="tm" style="color:var(--muted);font-size:14px">{fmt_min(self.total[id])} de leitura</span></p>
<a class="voltar" href="/#{"" if id == "brasil" else id}">← Ver no mapa</a>
{secs}
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
<section id="sec-creditos" class="hub-creditos">{self.dobra("Créditos e fontes", self.creditos())}</section>
</div>
<div class="rodape">{self.foot()}</div>"""
        return self.casca("Biomas — Biomas do Brasil", "Todos os biomas do Brasil e o sistema costeiro-marinho: textos, espécies, vídeos e quizzes.", corpo, "biomas", "var(--ink)", {"id": "hub", "regioes": self.regioes, "passaporte": self.P})

    def lab_carimbo(self):
        """Lab para ajustar o timing das animações de carimbo e a intensidade e duração do tremor (só no build de desenvolvimento)."""
        corpo = """<style>
.lc { display: grid; grid-template-columns: minmax(300px, 380px) minmax(0, 1fr); gap: 36px; max-width: 1180px; margin: 0 auto; padding: 32px 24px 80px; }
.lc h1 { margin: 0 0 6px; font: 400 44px/1 var(--display); } .lc > div > p.lead { margin: 0 0 18px; }
.lc-grupo { margin: 0 0 20px; padding: 0 0 14px; border-bottom: 1px solid var(--rule); } .lc-grupo h2 { margin: 0 0 10px; font: 500 12px var(--body); letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }
.lc-campo { margin-top: 10px; } .lc-campo label { display: block; font-size: 14px; } .lc-campo p { margin: 3px 0 0; font-size: 12px; color: var(--muted); }
.lc-linha { display: flex; align-items: center; gap: 8px; margin-top: 4px; } .lc-linha input[type=range] { flex: 1; accent-color: var(--ink); }
.lc-linha input[type=number] { width: 74px; padding: 4px 6px; font: inherit; color: var(--ink); background: rgba(255,255,255,.06); border: 1px solid var(--rule); } .lc-linha span { width: 24px; font-size: 12px; color: var(--muted); }
.lc-btns { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 14px; } .lc-btns button, .lc-fim button { padding: 8px 14px; font-size: 14px; cursor: pointer; color: var(--ink); background: transparent; border: 1px solid var(--rule); } .lc-btns button:hover, .lc-fim button:hover { background: rgba(255,255,255,.1); }
.lc-btns .p { color: #11160f; background: var(--ink); font-weight: 600; } .lc-btns .p:hover { background: var(--ink); filter: brightness(1.1); }
.lc-prev { position: sticky; top: 74px; } .lc-prev .folha { width: 100%; max-width: none; margin-top: 0; }
.lc-fim { margin-top: 18px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; } #msg { margin: 10px 0 0; min-height: 1.4em; font-size: 14px; color: var(--muted); }
#saida { width: 100%; height: 150px; margin-top: 10px; padding: 8px; font: 12px/1.4 ui-monospace, monospace; color: var(--ink); background: rgba(255,255,255,.05); border: 1px solid var(--rule); resize: vertical; }
@media (max-width: 860px) { .lc { grid-template-columns: minmax(0, 1fr); } .lc-prev { position: static; } }
</style>
<div class="lc">
<div>
<h1>Lab dos carimbos</h1>
<p class="lead">Ajuste o timing das animações de carimbo e a intensidade e a duração do tremor do passaporte. Os botões à direita testam na folha ou rodam as cenas de verdade, sem gravar nada.</p>
<div id="ctl"></div>
</div>
<div class="lc-prev">
<div class="lc-btns">
<button type="button" class="p" id="leve">Bater carimbo (tremor leve)</button>
<button type="button" class="p" id="forte">Bater carimbo de jornada completa (tremor forte)</button>
<button type="button" id="limpar">Limpar folha</button>
</div>
<div id="prev"></div>
<div class="lc-fim">
<button type="button" id="cenaBio">Testar cena de biomas</button>
<button type="button" id="cenaFim">Testar cena da jornada completa</button>
<label style="font-size:14px;margin-left:6px"><input type="checkbox" id="auto" checked> bater ao mexer nos controles</label>
</div>
<div class="lc-fim">
<button type="button" id="aplicar">Aplicar neste navegador</button>
<button type="button" id="padrao">Restaurar padrões</button>
<button type="button" id="copiar">Copiar valores</button>
</div>
<p id="msg" role="status"></p>
<textarea id="saida" readonly spellcheck="false" aria-label="Valores atuais em JSON"></textarea>
</div>
</div>
<script id="lab-dados" type="application/json">""" + json.dumps(self.P, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + """</script>"""
        html_ = self.casca("Lab dos carimbos — Biomas do Brasil", "Ajuste de timing e tremor das animações de carimbo.", corpo, "lab", "var(--ink)")
        return html_.replace("</body>", '<script src="/assets/lab-carimbo.js"></script>\n</body>')

    def sobre(self):
        c = self.C["brasil"]
        sobre = json.load(open(os.path.join(self.root, "data/sobre.json"), encoding="utf-8"))   # textos do Sobre
        tecno = [(x["t"], x["d"]) for x in sobre["tecnologias"]]
        lt = "".join(f"<dt>{E(a)}</dt><dd>{E(b)}</dd>" for a, b in tecno)
        corpo = f"""<div class="rd-wrap simples">
<main class="rd-main">
<p class="kicker">Sobre</p>
<h1>Como foi feito</h1>
<p class="intro">{E(sobre["intro"])}</p>
<section id="sec-tecnologias"><h2>Tecnologias</h2><dl class="gl">{lt}</dl></section>
<section id="sec-contato"><h2>Contato</h2>
<p>Site criado por Caio Amaral.</p>
<ul class="contato">
<li><a href="mailto:{CONTATO['email']}">{CONTATO['email']}</a></li>
<li><a href="{CONTATO['pessoal']}" target="_blank" rel="noopener">caiomga.com</a> — site pessoal</li>
<li><a href="{CONTATO['projetos']}" target="_blank" rel="noopener">brchad.com</a> — projetos</li>
</ul></section>
<section id="sec-creditos">{self.dobra("Créditos e fontes", self.creditos())}</section>
</main>
</div>
<div class="rodape">{self.foot()}</div>"""
        return self.casca("Sobre — Biomas do Brasil", "Tecnologias, dados, créditos e contato do site Biomas do Brasil.", corpo, "sobre")

    def escrever(self, publish=False):
        def w(rel, txt):
            p = os.path.join(self.dest, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8").write(txt)
        for id in self.C:
            w(self.url(id).strip("/") + "/index.html", self.pagina_conteudo(id))
        w("biomas/index.html", self.hub())
        w("sobre/index.html", self.sobre())
        if not publish:   # o lab não vai para a versão final
            w("lab-carimbo/index.html", self.lab_carimbo())
        os.makedirs(os.path.join(self.dest, "assets"), exist_ok=True)
        rd = lambda f: open(os.path.join(self.root, f), encoding="utf-8").read()
        open(os.path.join(self.dest, "assets/site.css"), "w", encoding="utf-8").write(rd("src/pagina.css") + "\n" + rd("src/comum.css"))
        open(os.path.join(self.dest, "assets/site.js"), "w", encoding="utf-8").write(rd("src/comum.js") + "\n" + rd("src/pagina.js"))
        if not publish:
            shutil.copy(os.path.join(self.root, "src/lab-carimbo.js"), os.path.join(self.dest, "assets/lab-carimbo.js"))
        for src, dst in (("data/icon.svg", "assets/icon.svg"), ("brchad-2026.png", "assets/brchad.png")):
            shutil.copy(os.path.join(self.root, src), os.path.join(self.dest, dst))


def gerar(root, dest, br_path, publish=False):
    s = Site(root, dest, br_path, "/assets/brchad.png")
    s.escrever(publish)
    print("páginas:", ", ".join(s.url(i) for i in s.C), "/biomas/ /sobre/")
