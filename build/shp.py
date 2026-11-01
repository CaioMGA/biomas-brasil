"""Leitor mínimo de shapefile (Python puro, sem dependências), para os mapas temáticos.

Lê pontos (1), linhas (3) e polígonos (5) e o .dbf com a codificação do .cpg (padrão UTF-8).
`read(base)` devolve [(atributos, geometria)], onde a geometria é:
  - ponto:   [(x, y)]
  - linha:   [[(x, y), ...], ...]   (uma lista por parte)
  - polígono: [[(x, y), ...], ...]  (anéis; o primeiro de cada parte é o externo, sentido horário no shapefile)
`bbox` opcional = (minx, miny, maxx, maxy) em graus: descarta feições cujo envelope não toca a caixa.
"""
import os, struct


def _dbf(base, only=None):
    enc = "utf-8"
    if os.path.exists(base + ".cpg"):
        enc = open(base + ".cpg").read().strip().lower() or enc
        enc = {"utf8": "utf-8", "latin1": "latin-1", "1252": "cp1252"}.get(enc, enc)
    b = open(base + ".dbf", "rb").read()
    n, hl, rl = struct.unpack("<IHH", b[4:12])
    fields, o = [], 32
    while b[o] != 0x0D:
        fields.append((b[o:o + 11].split(b"\0")[0].decode("ascii", "replace"), b[o + 16])); o += 32
    rows = {} if only is not None else []
    for i in (only if only is not None else range(n)):
        r = b[hl + i * rl + 1: hl + (i + 1) * rl]; d = {}; p = 0
        for name, ln in fields:
            d[name] = r[p:p + ln].decode(enc, "replace").replace("\x00", "").strip(); p += ln
        if only is not None: rows[i] = d
        else: rows.append(d)
    return rows


def _shp(base, bbox):
    b = open(base + ".shp", "rb").read(); o = 100; out = []
    while o < len(b):
        clen = struct.unpack(">i", b[o + 4:o + 8])[0] * 2; o += 8
        st = struct.unpack("<i", b[o:o + 4])[0]; g = None
        if st == 1:
            x, y = struct.unpack("<dd", b[o + 4:o + 20]); g = [(x, y)]
            if bbox and not (bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]): g = None
        elif st in (3, 5):
            x0, y0, x1, y1 = struct.unpack("<4d", b[o + 4:o + 36])
            if not bbox or not (x1 < bbox[0] or x0 > bbox[2] or y1 < bbox[1] or y0 > bbox[3]):
                np_, npt = struct.unpack("<ii", b[o + 36:o + 44])
                parts = list(struct.unpack("<%di" % np_, b[o + 44:o + 44 + 4 * np_])) + [npt]
                pp = o + 44 + 4 * np_
                pts = struct.unpack("<%dd" % (2 * npt), b[pp:pp + 16 * npt])
                pts = [(pts[2 * i], pts[2 * i + 1]) for i in range(npt)]
                g = [pts[parts[i]:parts[i + 1]] for i in range(np_)]
        out.append(g)
        o += clen
    return out


def read(base, bbox=None):
    geoms = _shp(base, bbox)
    attrs = _dbf(base, [i for i, g in enumerate(geoms) if g])   # só decodifica os atributos de quem passou no filtro
    return [(attrs[i], g) for i, g in enumerate(geoms) if g]


def read_por_nome(base, campo, nomes):
    """Lê só as feições cujo atributo `campo` está em `nomes` (conjunto), usando o índice .shx para decodificar apenas elas.
    Serve para bases enormes (ex.: drenagem do IBGE, ~2,5 milhões de trechos), onde ler tudo estouraria a memória.
    Devolve [(atributos, geometria)] com a mesma geometria de `read` (linhas: lista de partes)."""
    enc = "utf-8"
    if os.path.exists(base + ".cpg"):
        enc = open(base + ".cpg").read().strip().lower() or enc
        enc = {"utf8": "utf-8", "latin1": "latin-1", "1252": "cp1252"}.get(enc, enc)
    d = open(base + ".dbf", "rb").read()
    n, hl, rl = struct.unpack("<IHH", d[4:12])
    campos, o, off = [], 32, 1
    while d[o] != 0x0D:
        campos.append((d[o:o + 11].split(b"\0")[0].decode("ascii", "replace"), d[o + 16], off)); off += d[o + 16]; o += 32
    ini, ln = next((c[2], c[1]) for c in campos if c[0] == campo)
    alvo = {s.encode(enc) for s in nomes}
    idx = [i for i in range(n) if d[hl + i * rl + ini: hl + i * rl + ini + ln].replace(b"\x00", b"").strip() in alvo]
    atrs = {}
    for i in idx:
        r = d[hl + i * rl + 1: hl + (i + 1) * rl]; a = {}; p = 0
        for nome, tam, _ in campos: a[nome] = r[p:p + tam].decode(enc, "replace").replace("\x00", "").strip(); p += tam
        atrs[i] = a
    del d
    shx = open(base + ".shx", "rb").read(); shp_ = open(base + ".shp", "rb").read(); out = []
    for i in idx:
        off_ = struct.unpack(">i", shx[100 + 8 * i: 104 + 8 * i])[0] * 2 + 8   # pula o cabeçalho do registro (8 bytes)
        st = struct.unpack("<i", shp_[off_:off_ + 4])[0]
        if st not in (3, 5): continue
        np_, npt = struct.unpack("<ii", shp_[off_ + 36:off_ + 44])
        partes = list(struct.unpack("<%di" % np_, shp_[off_ + 44:off_ + 44 + 4 * np_])) + [npt]
        pp = off_ + 44 + 4 * np_
        pts = struct.unpack("<%dd" % (2 * npt), shp_[pp:pp + 16 * npt]); pts = [(pts[2 * k], pts[2 * k + 1]) for k in range(npt)]
        out.append((atrs[i], [pts[partes[k]:partes[k + 1]] for k in range(np_)]))
    return out
