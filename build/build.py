"""Monta index.html (arquivo único) a partir de src/template.html e data/.
Uso: python3 build/build.py             -> index.html (desenvolvimento, com o lab de textos)
     python3 build/build.py --publish   -> dist/index.html (versão final, sem o lab)
"""
import base64, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loader_path import brasil_path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rd = lambda p: open(os.path.join(root, p), "rb").read()
uri = lambda p: "data:image/png;base64," + base64.b64encode(rd(p)).decode()
m = json.loads(rd("data/map.json"))

# Rótulo do Sistema Costeiro-Marinho: centro da parte mais "funda" do mar (erosão repetida da máscara id 7)
from PIL import Image, ImageFilter
im = Image.open(os.path.join(root, "data/ids.png"))
sea = Image.frombytes("L", im.size, im.point([255 if i == 7 else 0 for i in range(256)]).tobytes()).resize((im.width // 4, im.height // 4), Image.NEAREST)
last = sea
while True:
    nxt = last.filter(ImageFilter.MinFilter(5))
    if nxt.getbbox() is None: break
    last = nxt
px = [(i % last.width, i // last.width) for i, v in enumerate(last.tobytes()) if v]
cx = sum(p[0] for p in px) / len(px); cy = sum(p[1] for p in px) / len(px)
best = min(px, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
m["centroid"]["Sistema Costeiro"] = [round(best[0] * 8 + 4), round(best[1] * 8 + 4)]
print("pixels marinhos", sum(1 for v in sea.tobytes() if v)); print("rótulo marinho", m["centroid"]["Sistema Costeiro"])
html = rd("src/template.html").decode()
EQ_Y = round((0 - m["miny"]) * m["S"], 1); TR_Y = round((23.4366 - m["miny"]) * m["S"], 1)
_ids = im.load()
def free(y, gap=40):
    """Faixa [oeste, leste] ocupada por biomas (ids 1-7 e a extensão 11-16) na linha y, em unidades do mapa, com folga: fora dela não há bioma."""
    j = min(im.height - 1, int(y / (m["w"] / im.width))); sc = m["w"] / im.width
    xs = [i for i in range(im.width) if 1 <= _ids[i, j] <= 7 or 11 <= _ids[i, j] <= 16]
    return [round(min(xs) * sc - gap), round(max(xs) * sc + gap)]
BR_D, BR_W, BR_H = brasil_path(root)   # contorno do Brasil para a tela de carregamento
import urllib.parse
from PIL import ImageDraw
def icon_png(n=180, ss=4):
    S = n * ss; k = S / 64; im2 = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im2)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=14 * k, fill="#009c3b")
    d.polygon([(32 * k, 7 * k), (58 * k, 32 * k), (32 * k, 57 * k), (6 * k, 32 * k)], fill="#ffdf00")
    d.ellipse([18 * k, 18 * k, 46 * k, 46 * k], fill="#002776")
    band = Image.new("L", (S, S), 0); bd = ImageDraw.Draw(band)
    pts = [((1-t)**2*16 + 2*(1-t)*t*32 + t*t*48, (1-t)**2*34 + 2*(1-t)*t*24 + t*t*36) for t in [i / 80 for i in range(81)]]
    bd.line([(x * k, y * k) for x, y in pts], fill=255, width=round(3.6 * k)); 
    disc = Image.new("L", (S, S), 0); ImageDraw.Draw(disc).ellipse([18 * k, 18 * k, 46 * k, 46 * k], fill=255)
    mask = Image.composite(band, Image.new("L", (S, S), 0), disc)
    im2.paste((255, 255, 255, 255), mask=mask)
    import io; buf = io.BytesIO(); im2.resize((n, n), Image.LANCZOS).save(buf, "PNG"); return buf.getvalue()
_svg = rd("data/icon.svg").decode()
rep = {
    "__ICONSVG__": "data:image/svg+xml," + urllib.parse.quote(_svg, safe="/:=,;"),
    "__ICONPNG__": "data:image/png;base64," + base64.b64encode(icon_png()).decode(),
    "__BRD__": BR_D, "__BRVB__": f"-8 -8 {BR_W + 14} {BR_H + 14}",
    "__W__": str(m["w"]), "__H__": str(m["h"]),
    "__CENT__": json.dumps(m["centroid"], ensure_ascii=False, separators=(",", ":")),
    "__DEM__": uri("data/dem.png"), "__IDS__": uri("data/ids.png"),
    "__LAYERS__": rd("data/layers.json").decode(),
    "__FOCUS__": rd("data/focus.json").decode(),
    "__RAIN__": rd("data/rain.json").decode(),
    "__LABELCFG__": json.dumps(json.loads(rd("data/labels.json").decode()).get("textos", json.loads(rd("data/labels.json").decode())), ensure_ascii=False) if os.path.exists(os.path.join(root, "data/labels.json")) else "{}",
    "__GEO__": json.dumps({"eq": EQ_Y, "tr": TR_Y, "eqFree": free(EQ_Y), "trFree": free(TR_Y),
                           # "América do Sul": do sul de Porto Velho (Bolívia, 11,5°S) até a Argentina (região de Córdoba, 32°S)
                           "sa": [[round((lon * m["K"] - m["minx"]) * m["S"], 1), round((-lat - m["miny"]) * m["S"], 1)] for lon, lat in [(-66.8, -11.5), (-64.5, -32.0)]]}),   # y = (-latitude - miny) * escala
}
for k, v in rep.items():
    assert k in html, k
    html = html.replace(k, v)
publish = "--publish" in sys.argv
if publish:   # versão final: remove o lab de textos (HTML, CSS e JS entre os marcadores LAB)
    for pat in (r"<!--LAB:HTML-->.*?<!--LAB:HTML-END-->", r"/\*LAB:CSS\*/.*?/\*LAB:CSS-END\*/", r"/\*LAB:JS\*/.*?/\*LAB:JS-END\*/"):
        html, n = re.subn(pat, "", html, flags=re.S); assert n == 1, pat
    assert "labBtn" not in html and "Lab de textos" not in html and "biomas-lab-textos" not in html
    os.makedirs(os.path.join(root, "dist"), exist_ok=True)
    dest = os.path.join(root, "dist", "index.html")
else:
    dest = os.path.join(root, "index.html")
open(dest, "w", encoding="utf-8").write(html)
print(os.path.relpath(dest, root), len(html) // 1024, "KB", "(versão final, sem lab)" if publish else "(desenvolvimento, com lab)")
