"""Busca e baixa fotos de licença livre do Wikimedia Commons para as seções das páginas.
  python3 build/fotos_commons.py buscar "consulta" [n]      -> lista candidatos (só CC BY, CC BY-SA, CC0 e domínio público; largura >= 1200)
  python3 build/fotos_commons.py especie <bioma> "<nome científico>" "File:Nome.jpg" "texto alternativo" [x [y]]   -> grava data/fotos/<bioma>/<slug>.jpg (3:2, 1200 px, recorte em torno de x,y em 0-1) e a chave <nome científico> em data/fotos/<bioma>.json
  python3 build/fotos_commons.py aerea <bioma> "File:Nome.jpg" "legenda" "texto alternativo" [x [y]]   -> grava data/fotos/<bioma>/vista-aerea.jpg (16:9, até 1600 px) e a chave _vista_aerea
  python3 build/fotos_commons.py baixar <bioma> <secao> "File:Nome.jpg" "legenda" "texto alternativo"   -> grava data/fotos/<bioma>/secao-<secao>.jpg e a chave _secoes.<secao> em data/fotos/<bioma>.json
Autor, licença e links vêm da API do Commons (extmetadata); nada é digitado à mão."""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request, io
from PIL import Image
API = "https://commons.wikimedia.org/w/api.php"
OK = re.compile(r"^(CC BY(-SA)? [0-9.]+|CC0.*|Public domain.*|PD.*)$", re.I)
UA = {"User-Agent": "biomas-brasil-fotos/1.0 (projeto educativo; contato via github.com/CaioMGA/biomas-brasil)"}
txt = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def abrir(req, timeout=60):
    """urlopen com espera e nova tentativa quando o Commons responde 429 (limite de requisições)."""
    for k in range(6):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code != 429 or k == 5: raise
            time.sleep(float(e.headers.get("Retry-After") or 10 * (k + 1)))


def api(**p):
    p["format"] = "json"
    return json.load(abrir(urllib.request.Request(API + "?" + urllib.parse.urlencode(p), headers=UA)))


def info(titles):
    r = api(action="query", titles="|".join(titles), prop="imageinfo", iiprop="url|size|extmetadata|mime", iiurlwidth=1600)
    return {p["title"]: p for p in r["query"]["pages"].values() if "imageinfo" in p}


def lic_ok(m):
    return OK.match(txt(m.get("LicenseShortName", {}).get("value", ""))) is not None


def buscar(q, n=8):
    r = api(action="query", generator="search", gsrsearch=q + " filetype:bitmap", gsrnamespace=6, gsrlimit=30, prop="imageinfo", iiprop="url|size|extmetadata|mime", iiurlwidth=400)
    out = []
    for p in sorted(r.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0)):
        ii = p["imageinfo"][0]; m = ii["extmetadata"]
        if ii["mime"] != "image/jpeg" or ii["width"] < 1200 or ii["width"] < ii["height"] or not lic_ok(m): continue
        out.append((p["title"], ii["width"], ii["height"], txt(m["LicenseShortName"]["value"]), txt(m.get("Artist", {}).get("value", ""))[:30], txt(m.get("ImageDescription", {}).get("value", ""))[:90]))
        if len(out) >= n: break
    return out


def baixar(bioma, secao, titulo, legenda, alt, raiz=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")):
    p = info([titulo])[titulo]; ii = p["imageinfo"][0]; m = ii["extmetadata"]
    assert lic_ok(m), "licença não aceita: " + txt(m.get("LicenseShortName", {}).get("value", ""))
    img = Image.open(io.BytesIO(abrir(urllib.request.Request(ii["thumburl"], headers=UA), 90).read())).convert("RGB")
    W, H = img.size; h = min(H, int(W * 9 / 16)); top = (H - h) // 2; img = img.crop((0, top, W, top + h))   # recorte 16:9, centrado
    if W > 1600: img = img.resize((1600, round(h * 1600 / W)), Image.LANCZOS)
    d = os.path.join(raiz, "data/fotos", bioma); os.makedirs(d, exist_ok=True); arq = f"secao-{secao}.jpg"; img.save(os.path.join(d, arq), quality=84, optimize=True, progressive=True)
    lic = txt(m["LicenseShortName"]["value"]); url = txt(m.get("LicenseUrl", {}).get("value", "")) or ("https://creativecommons.org/publicdomain/zero/1.0/" if lic.upper().startswith("CC0") else "")
    reg = dict(arquivo=arq, w=img.size[0], h=img.size[1], alt=alt, legenda=legenda, autor=txt(m.get("Artist", {}).get("value", "")) or "autor não informado", licenca=lic, licenca_url=url,
               fonte_url=ii["descriptionurl"], arquivo_commons=titulo[5:])
    jp = os.path.join(raiz, "data/fotos", bioma + ".json"); J = json.load(open(jp, encoding="utf-8")) if os.path.exists(jp) else {}
    J.setdefault("_secoes", {})[secao] = reg
    json.dump(J, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1); open(jp, "a").write("\n")
    print("ok", bioma, secao, titulo, lic, reg["autor"])


def _reg(bioma, raiz, chave, arq, img, titulo, ii, m, extra):
    lic = txt(m["LicenseShortName"]["value"]); url = txt(m.get("LicenseUrl", {}).get("value", "")) or ("https://creativecommons.org/publicdomain/zero/1.0/" if lic.upper().startswith("CC0") else "")
    reg = dict(arquivo=arq, w=img.size[0], h=img.size[1], **extra, autor=txt(m.get("Artist", {}).get("value", "")) or "autor não informado", licenca=lic, licenca_url=url,
               fonte_url=ii["descriptionurl"], arquivo_commons=titulo[5:])
    jp = os.path.join(raiz, "data/fotos", bioma + ".json"); J = json.load(open(jp, encoding="utf-8")) if os.path.exists(jp) else {}
    J[chave] = reg
    json.dump(J, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1); open(jp, "a").write("\n")
    print("ok", bioma, chave, titulo, lic, reg["autor"], img.size)


def _recorte(img, prop, larg, x, y):
    """Recorta na proporção `prop` (largura/altura) em torno do ponto (x, y) em 0-1 e reduz para no máximo `larg` px de largura."""
    W, H = img.size
    w, h = (W, round(W / prop)) if W / H < prop else (round(H * prop), H)
    l = min(max(round(x * W - w / 2), 0), W - w); t = min(max(round(y * H - h / 2), 0), H - h)
    img = img.crop((l, t, l + w, t + h))
    return img.resize((larg, round(larg / prop)), Image.LANCZOS) if img.size[0] > larg else img


def _baixar_img(titulo):
    p = info([titulo])[titulo]; ii = p["imageinfo"][0]; m = ii["extmetadata"]
    assert lic_ok(m), "licença não aceita: " + txt(m.get("LicenseShortName", {}).get("value", ""))
    return Image.open(io.BytesIO(abrir(urllib.request.Request(ii["thumburl"], headers=UA), 90).read())).convert("RGB"), ii, m


def especie(bioma, cientifico, titulo, alt, x=.5, y=.5, raiz=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")):
    img, ii, m = _baixar_img(titulo); img = _recorte(img, 3 / 2, 1200, float(x), float(y))
    arq = re.sub(r"[^a-z0-9]+", "-", cientifico.lower()).strip("-") + ".jpg"
    d = os.path.join(raiz, "data/fotos", bioma); os.makedirs(d, exist_ok=True); img.save(os.path.join(d, arq), quality=84, optimize=True, progressive=True)
    _reg(bioma, raiz, cientifico, arq, img, titulo, ii, m, {"alt": alt})


def aerea(bioma, titulo, legenda, alt, x=.5, y=.5, raiz=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")):
    img, ii, m = _baixar_img(titulo); img = _recorte(img, 16 / 9, 1600, float(x), float(y))
    d = os.path.join(raiz, "data/fotos", bioma); os.makedirs(d, exist_ok=True); img.save(os.path.join(d, "vista-aerea.jpg"), quality=84, optimize=True, progressive=True)
    _reg(bioma, raiz, "_vista_aerea", "vista-aerea.jpg", img, titulo, ii, m, {"alt": alt, "legenda": legenda})


if __name__ == "__main__":
    if sys.argv[1] == "buscar":
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 8
        for q in sys.argv[2].split(";"):   # várias consultas separadas por ";"
            print("##", q.strip())
            for t in buscar(q.strip(), n): print(" | ".join(map(str, t)))
            time.sleep(3)
    elif sys.argv[1] == "especie":
        especie(*sys.argv[2:])
    elif sys.argv[1] == "aerea":
        aerea(*sys.argv[2:])
    else:
        baixar(*sys.argv[2:7])
