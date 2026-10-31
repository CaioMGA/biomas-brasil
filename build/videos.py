"""Verifica candidatos a vídeo do YouTube: título, canal, duração, data, visualizações e se a incorporação é permitida.

Lê os dados que a própria página do vídeo publica (ytInitialPlayerResponse). Não avalia o conteúdo: isso fica com quem edita o site.
Uso: python3 -I videos.py data/videos_candidatos.json ID [ID ...]   (acrescenta ao arquivo, sem repetir IDs)
"""
import json, os, re, sys, time, urllib.request

out = sys.argv[1]; ids = sys.argv[2:]
db = json.load(open(out)) if os.path.exists(out) else {}

def get(i):
    req = urllib.request.Request(f"https://www.youtube.com/watch?v={i}", headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9", "Cookie": "CONSENT=YES+1"})
    try:
        h = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    except Exception as e:
        return i, {"erro": str(e)}
    def f(pat, cast=str):
        m = re.search(pat, h); return cast(m.group(1)) if m else None
    unesc = lambda s: json.loads('"' + s + '"') if s else s
    return i, {
        "titulo": unesc(f(r'"videoDetails":\{.*?"title":"((?:[^"\\]|\\.)*)"')),
        "canal": unesc(f(r'"videoDetails":\{.*?"author":"((?:[^"\\]|\\.)*)"')),
        "segundos": f(r'"lengthSeconds":"(\d+)"', int),
        "visualizacoes": f(r'"viewCount":"(\d+)"', int),
        "publicado": f(r'"publishDate":"([^"]+)"'),
        "incorporavel": f(r'"playableInEmbed":(true|false)') == "true",
        "status": f(r'"playabilityStatus":\{"status":"([A-Z_]+)"'),
    }

todo = [i for i in ids if i not in db or "erro" in db[i]]
for n, i in enumerate(todo):
    _, d = get(i)
    if "erro" in d:
        print(i, "ERRO", d["erro"], "- parando (aguarde alguns minutos e rode de novo; os já verificados ficam salvos)")
        db.pop(i, None); break
    db[i] = d
    time.sleep(2.5)   # cadência lenta: o YouTube bloqueia (429) quando se pede demais
json.dump(db, open(out, "w"), ensure_ascii=False, indent=1)
for i in ids:
    d = db.get(i)
    if d is None: print(i, "(ainda não verificado)"); continue
    if "erro" in d: print(i, "ERRO", d["erro"]); continue
    m, s = divmod(d["segundos"] or 0, 60)
    print(f'{i}  {m:3d}:{s:02d}  {"emb" if d.get("incorporavel") else "NAO-EMB"}  {(d.get("publicado") or "?")[:10]}  {(d.get("visualizacoes") or 0):>10,}  {d.get("canal")} | {d.get("titulo")}')
