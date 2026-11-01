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
