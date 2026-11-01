"""Exporta os textos de conteúdo do site para arquivos Markdown (textos/*.md) e importa de volta.

    python3 build/conteudo_md.py exportar            # data/conteudo/*.json e data/sobre.json -> textos/*.md
    python3 build/conteudo_md.py importar            # textos/*.md -> JSONs (valida tudo antes de gravar)
    python3 build/conteudo_md.py importar --simular  # só valida e mostra o que mudaria

Só conteúdo: textos de interface (botões, rótulos, menus) não entram. Os vídeos (título, canal, duração) ficam no JSON, fora dos md.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jsonfmt

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDEM = ["brasil", "amazonia", "cerrado", "mata-atlantica", "caatinga", "pampa", "pantanal", "costeiro"]
NOMES = {"brasil": "Brasil", "amazonia": "Amazônia", "cerrado": "Cerrado", "mata-atlantica": "Mata Atlântica", "caatinga": "Caatinga",
         "pampa": "Pampa", "pantanal": "Pantanal", "costeiro": "Costeiro-marinho"}
PAINEL_BIOMA = [("states", "Estados"), ("abroad", "Fora do Brasil"), ("climate", "Clima"), ("veg", "Vegetação"), ("curio", "Curiosidade"), ("endem", "Endemismo")]
PAINEL_BRASIL = [("lead", "Abertura do painel"), ("diverso_titulo", "Título do 1º bloco"), ("diverso", "Texto do 1º bloco"), ("nota", "Nota sobre as contagens"),
                 ("mar_titulo", "Título do 2º bloco"), ("mar", "Texto do 2º bloco"), ("fonte_chuva", "Fonte da chuva"), ("fonte_geral", "Fontes gerais")]
DIR_MD = os.path.join(RAIZ, "textos")
DIR_JSON = os.path.join(RAIZ, "data", "conteudo")


class Erro(Exception):
    pass


# ----------------------------------------------------------------------------- exportar
def paragrafos(lista):
    return "\n\n".join(lista)


def md_pagina(id, d):
    o = [f"# {NOMES[id]}", f"<!-- id: {id} -->", "", "## Chamada", d["intro"], ""]
    p = d.get("painel")
    if p:
        o += ["## Painel do mapa", ""]
        for k, rot in (PAINEL_BRASIL if id == "brasil" else PAINEL_BIOMA):
            if k in p:
                o += [f"### {rot}", p[k], ""]
    if d.get("emblema"):
        o += ["## Espécie mais emblemática", "", f"**Espécie:** {d['emblema']['n']}", "", d["emblema"]["porque"], ""]
    if d.get("secoes"):
        o += ["## Seções", ""]
        for s in d["secoes"]:
            o += [f"### {s['titulo']}", f"<!-- secao: {s['id']}{' | chuva' if s.get('chuva') else ''} -->", "", paragrafos(s["p"]), ""]
    if d.get("especies"):
        o += ["## Fichas de espécies", ""]
        for e in d["especies"]:
            o += [f"### {e['n']}", "", f"- **Nome científico:** {e['c']}", f"- **Tipo:** {e['t']}", "", e["d"], ""]
    if d.get("leitura"):
        l = d["leitura"]
        o += ["## Leitura", "", f"**Autor:** {l['autor']}", f"**Obra:** {l['obra']}", ""] + [("> " + v).rstrip() for v in l["texto"].split("\n")] + [""]
    if d.get("glossario"):
        o += ["## Glossário", ""]
        for g in d["glossario"]:
            o += [f"### {g['t']}", g["d"], ""]
    if d.get("linha"):
        o += ["## Linha do tempo", ""]
        for g in d["linha"]:
            o += [f"### {g['a']}", g["t"], ""]
    if d.get("quiz"):
        o += ["## Quiz", ""]
        for i, q in enumerate(d["quiz"], 1):
            o += [f"### Pergunta {i}", q["q"], ""] + [f"- [{'x' if k == q['c'] else ' '}] {op}" for k, op in enumerate(q["o"])] + ["", f"**Explicação:** {q['e']}", ""]
    if d.get("fontes"):
        o += ["## Fontes", d["fontes"], ""]
    if d.get("creditos"):
        o += ["## Créditos e fontes", ""]
        for g in d["creditos"]:
            o += [f"### {g['t']}"] + [(f"- [{x['n']}]({x['u']}) — {x['d']}" if x.get("u") else f"- {x['n']} — {x['d']}") for x in g["i"]] + [""]
        o += ["### Nota sobre os créditos", d["creditos_nota"], ""]
    return "\n".join(o).rstrip("\n") + "\n"


def md_sobre(d):
    o = ["# Sobre", "<!-- id: sobre -->", "", "## Chamada", d["intro"], "", "## Tecnologias", ""]
    for t in d["tecnologias"]:
        o += [f"### {t['t']}", t["d"], ""]
    return "\n".join(o).rstrip("\n") + "\n"


LEIA_ME = """# Textos do site Biomas do Brasil

Estes arquivos têm todos os textos de conteúdo do site, um por página: `brasil.md`, um para cada bioma e `sobre.md`.
Textos de interface (botões, menus, rótulos) não estão aqui. Os vídeos (título, canal, duração) também não.

## Como editar

- Reescreva só o texto. Não é Markdown renderizado: o site mostra o texto como está, então não use `*`, `_` ou `#` para formatar.
- **Parágrafos** de uma seção são separados por uma linha em branco. Nos outros campos, o texto é um parágrafo só.
- Os títulos em Markdown (`#`, `##`, `###`) e as linhas `<!-- ... -->` são a estrutura do arquivo: **não apague nem mude os comentários `<!-- ... -->`**.
  - Dá para mudar o texto dos títulos de seção, de ficha de espécie, de termo do glossário e de ano da linha do tempo (é o que o site mostra).
  - Os títulos fixos (`## Chamada`, `## Painel do mapa`, `### Estados` etc.) devem ficar como estão.
- **Seções**: para criar uma, copie um bloco `### Título` + `<!-- secao: id -->` e use um id novo, sem acento nem espaço. Para apagar, remova o bloco inteiro.
  `| chuva` no comentário mostra o gráfico de chuva naquela seção (só a primeira de cada bioma).
- **Fichas de espécies**: cada `### Nome` é uma espécie, com nome científico e tipo (`fauna` ou `flora`). Pode adicionar, remover e reordenar.
  A espécie mais emblemática precisa ter uma ficha com o mesmo nome.
- **Quiz**: cada `### Pergunta N` tem o enunciado, as opções e a explicação. Marque a opção correta com `[x]` (uma só) e as demais com `[ ]`.
  Pode ter 2 a 5 opções.
- **Leitura** (só em `brasil.md`): os versos ficam em linhas que começam com `> `.
- **Créditos** (só em `brasil.md`): uma linha por item: `- [Nome](endereço) — descrição`, ou `- Nome — descrição` se não houver link.
  O travessão ` — ` separa o nome da descrição.

## Como voltar para o site

Quando terminar, é só avisar: o comando `python3 build/conteudo_md.py importar` confere o formato (apontando arquivo e linha de qualquer problema),
atualiza os JSONs de `data/` e o site é reconstruído com os textos novos.
`importar --simular` só confere e mostra o que mudaria, sem gravar.
"""


def exportar():
    os.makedirs(DIR_MD, exist_ok=True)
    for id in ORDEM:
        d = json.load(open(os.path.join(DIR_JSON, f"{id}.json"), encoding="utf-8"))
        open(os.path.join(DIR_MD, f"{id}.md"), "w", encoding="utf-8").write(md_pagina(id, d))
    sobre = json.load(open(os.path.join(RAIZ, "data", "sobre.json"), encoding="utf-8"))
    open(os.path.join(DIR_MD, "sobre.md"), "w", encoding="utf-8").write(md_sobre(sobre))
    open(os.path.join(DIR_MD, "LEIA-ME.md"), "w", encoding="utf-8").write(LEIA_ME)
    print("exportado:", ", ".join(ORDEM + ["sobre"]), "->", os.path.relpath(DIR_MD, RAIZ) + "/")


# ----------------------------------------------------------------------------- importar
def ler_blocos(caminho):
    """Lê um md em {nivel2: {'linhas': [...], 'subs': [(titulo, linhas, n_linha)]}} mantendo a numeração de linha para os erros."""
    nome = os.path.basename(caminho)
    linhas = open(caminho, encoding="utf-8").read().split("\n")
    titulo, id = None, None
    blocos, atual, sub = [], None, None   # blocos: [(titulo2, linhas_soltas, [subs])]
    for n, l in enumerate(linhas, 1):
        if l.startswith("# ") and titulo is None:
            titulo = l[2:].strip(); continue
        m = re.match(r"<!--\s*id:\s*(\S+)\s*-->$", l.strip())
        if m and id is None and atual is None:
            id = m.group(1); continue
        if l.startswith("## "):
            atual = [l[3:].strip(), [], [], n]; blocos.append(atual); sub = None; continue
        if l.startswith("### "):
            if atual is None:
                raise Erro(f"{nome}:{n}: título `###` fora de uma seção `##`")
            sub = [l[4:].strip(), [], n]; atual[2].append(sub); continue
        if atual is None:
            if l.strip():
                raise Erro(f"{nome}:{n}: texto antes do primeiro título `##`")
            continue
        (sub[1] if sub is not None else atual[1]).append((n, l))
    return nome, titulo, id, blocos


def paras(linhas):
    """Linhas (n, texto) -> lista de parágrafos (blocos separados por linha em branco; linhas internas viram um parágrafo só)."""
    out, cur = [], []
    for _, l in linhas:
        if l.strip() == "":
            if cur: out.append(" ".join(x.strip() for x in cur)); cur = []
        elif l.strip().startswith("<!--"):
            continue
        else:
            cur.append(l)
    if cur: out.append(" ".join(x.strip() for x in cur))
    return out


def um(linhas, onde):
    p = paras(linhas)
    if not p:
        raise Erro(f"{onde}: texto vazio")
    return " ".join(p)


def comentario(linhas, nome):
    for n, l in linhas:
        m = re.match(r"<!--\s*(.*?)\s*-->$", l.strip())
        if m and m.group(1).startswith(nome + ":"):
            return n, m.group(1)[len(nome) + 1:].strip()
    return None, None


def importar_pagina(caminho, id_esperado, atual):
    nome, titulo, id, blocos = ler_blocos(caminho)
    if id != id_esperado:
        raise Erro(f"{nome}: o comentário `<!-- id: {id_esperado} -->` do começo do arquivo está ausente ou mudou")
    novo = json.loads(json.dumps(atual))   # cópia; campos não exportados (vídeos etc.) ficam como estão
    por = {b[0]: b for b in blocos}

    def bloco(nome2, obrigatorio=True):
        if nome2 not in por:
            if obrigatorio: raise Erro(f"{nome}: falta a seção `## {nome2}`")
            return None
        return por[nome2]

    novo["intro"] = um(bloco("Chamada")[1], f"{nome}: ## Chamada")
    if "painel" in atual:
        b = bloco("Painel do mapa"); subs = {s[0]: s for s in b[2]}
        p = {}
        for k, rot in (PAINEL_BRASIL if id == "brasil" else PAINEL_BIOMA):
            if rot in subs: p[k] = um(subs[rot][1], f"{nome}:{subs[rot][2]}: {rot}")
            elif k in atual["painel"]: raise Erro(f"{nome}: falta `### {rot}` em `## Painel do mapa`")
        novo["painel"] = p
    if "emblema" in atual:
        b = bloco("Espécie mais emblemática"); linhas = b[1]
        esp = None
        for n, l in linhas:
            m = re.match(r"\*\*Espécie:\*\*\s*(.+)$", l.strip())
            if m: esp = m.group(1).strip()
        if not esp: raise Erro(f"{nome}:{b[3]}: falta a linha `**Espécie:** Nome`")
        corpo = [(n, l) for n, l in linhas if not re.match(r"\*\*Espécie:\*\*", l.strip())]
        novo["emblema"] = {**atual["emblema"], "n": esp, "porque": um(corpo, f"{nome}:{b[3]}: espécie emblemática")}
    if "secoes" in atual:
        b = bloco("Seções"); secs, ids = [], set()
        for t, linhas, n0 in b[2]:
            n, c = comentario(linhas, "secao")
            if c is None: raise Erro(f"{nome}:{n0}: a seção `### {t}` precisa do comentário `<!-- secao: id -->` logo abaixo do título")
            partes = [x.strip() for x in c.split("|")]
            sid = partes[0]
            if not re.fullmatch(r"[a-z0-9-]+", sid): raise Erro(f"{nome}:{n}: id de seção inválido `{sid}` (use letras minúsculas sem acento, números e hífen)")
            if sid in ids: raise Erro(f"{nome}:{n}: id de seção repetido `{sid}`")
            ids.add(sid)
            ps = paras(linhas)
            if not ps: raise Erro(f"{nome}:{n0}: a seção `### {t}` está sem texto")
            sec = {"id": sid, "titulo": t}
            if "chuva" in partes[1:]: sec["chuva"] = True
            sec["p"] = ps
            secs.append(sec)
        novo["secoes"] = secs
    if "especies" in atual:
        b = bloco("Fichas de espécies"); esp = []
        for t, linhas, n0 in b[2]:
            c = tp = None; corpo = []
            for n, l in linhas:
                m = re.match(r"-\s*\*\*Nome científico:\*\*\s*(.+)$", l.strip()); m2 = re.match(r"-\s*\*\*Tipo:\*\*\s*(.+)$", l.strip())
                if m: c = m.group(1).strip()
                elif m2: tp = m2.group(1).strip().lower()
                else: corpo.append((n, l))
            if not c or tp not in ("fauna", "flora"): raise Erro(f"{nome}:{n0}: a ficha `### {t}` precisa de `- **Nome científico:** ...` e `- **Tipo:** fauna` (ou flora)")
            esp.append({"n": t, "c": c, "t": tp, "d": um(corpo, f"{nome}:{n0}: ficha {t}")})
        novo["especies"] = esp
        if "emblema" in novo and novo["emblema"]["n"] not in [e["n"] for e in esp]:
            raise Erro(f"{nome}: a espécie emblemática `{novo['emblema']['n']}` não tem ficha em `## Fichas de espécies` com o mesmo nome")
    if "leitura" in atual:
        b = bloco("Leitura"); autor = obra = None; versos = []
        for n, l in b[1]:
            m = re.match(r"\*\*Autor:\*\*\s*(.+)$", l.strip()); m2 = re.match(r"\*\*Obra:\*\*\s*(.+)$", l.strip())
            if m: autor = m.group(1).strip()
            elif m2: obra = m2.group(1).strip()
            elif l.startswith(">"): versos.append(l[1:][1:] if l.startswith("> ") else l[1:])
        if not (autor and obra and versos): raise Erro(f"{nome}:{b[3]}: `## Leitura` precisa de `**Autor:**`, `**Obra:**` e o texto em linhas que começam com `> `")
        novo["leitura"] = {**atual["leitura"], "autor": autor, "obra": obra, "texto": "\n".join(versos)}
    if "glossario" in atual:
        b = bloco("Glossário"); novo["glossario"] = [{"t": t, "d": um(l, f"{nome}:{n0}: {t}")} for t, l, n0 in b[2]]
    if "linha" in atual:
        b = bloco("Linha do tempo"); novo["linha"] = [{"a": t, "t": um(l, f"{nome}:{n0}: {t}")} for t, l, n0 in b[2]]
    if "quiz" in atual:
        b = bloco("Quiz"); qs = []
        for t, linhas, n0 in b[2]:
            enun, ops, cor, exp = [], [], None, None
            for n, l in linhas:
                m = re.match(r"-\s*\[( |x|X)\]\s*(.+)$", l.strip()); m2 = re.match(r"\*\*Explicação:\*\*\s*(.+)$", l.strip())
                if m:
                    if m.group(1).lower() == "x":
                        if cor is not None: raise Erro(f"{nome}:{n}: mais de uma opção marcada com [x] em `### {t}`")
                        cor = len(ops)
                    ops.append(m.group(2).strip())
                elif m2: exp = m2.group(1).strip()
                elif l.strip() and not ops and exp is None: enun.append((n, l))
            if cor is None: raise Erro(f"{nome}:{n0}: `### {t}` não tem a opção correta marcada com [x]")
            if not (2 <= len(ops) <= 5): raise Erro(f"{nome}:{n0}: `### {t}` precisa de 2 a 5 opções")
            if not exp: raise Erro(f"{nome}:{n0}: `### {t}` está sem `**Explicação:**`")
            qs.append({"q": um(enun, f"{nome}:{n0}: enunciado de {t}"), "o": ops, "c": cor, "e": exp})
        novo["quiz"] = qs
    if "fontes" in atual:
        novo["fontes"] = um(bloco("Fontes")[1], f"{nome}: ## Fontes")
    if "creditos" in atual:
        b = bloco("Créditos e fontes"); grupos = []
        for t, linhas, n0 in b[2]:
            if t == "Nota sobre os créditos":
                novo["creditos_nota"] = um(linhas, f"{nome}:{n0}: nota sobre os créditos"); continue
            itens = []
            for n, l in linhas:
                if not l.strip(): continue
                m = re.match(r"-\s*\[(.+?)\]\((.+?)\)\s+—\s+(.+)$", l.strip()) ; m2 = re.match(r"-\s*(.+?)\s+—\s+(.+)$", l.strip())
                if m: itens.append({"n": m.group(1), "u": m.group(2), "d": m.group(3)})
                elif m2: itens.append({"n": m2.group(1), "u": "", "d": m2.group(2)})   # sem link: "u" vazio, como nos dados
                else: raise Erro(f"{nome}:{n}: linha de crédito fora do formato `- [Nome](endereço) — descrição`")
            grupos.append({"t": t, "i": itens})
        novo["creditos"] = grupos
    return novo


def importar_sobre(caminho, atual):
    nome, titulo, id, blocos = ler_blocos(caminho)
    if id != "sobre": raise Erro(f"{nome}: o comentário `<!-- id: sobre -->` do começo do arquivo está ausente ou mudou")
    por = {b[0]: b for b in blocos}
    for k in ("Chamada", "Tecnologias"):
        if k not in por: raise Erro(f"{nome}: falta a seção `## {k}`")
    return {"intro": um(por["Chamada"][1], f"{nome}: ## Chamada"), "tecnologias": [{"t": t, "d": um(l, f"{nome}:{n0}: {t}")} for t, l, n0 in por["Tecnologias"][2]]}


def importar(simular=False, dir_md=DIR_MD, dir_json=DIR_JSON, arq_sobre=None):
    arq_sobre = arq_sobre or os.path.join(RAIZ, "data", "sobre.json")
    novos, mudou = {}, []
    for id in ORDEM:
        f = os.path.join(dir_json, f"{id}.json"); atual = json.load(open(f, encoding="utf-8"))
        novos[f] = importar_pagina(os.path.join(dir_md, f"{id}.md"), id, atual)
        if novos[f] != atual: mudou.append(id)
    atual = json.load(open(arq_sobre, encoding="utf-8")); novos[arq_sobre] = importar_sobre(os.path.join(dir_md, "sobre.md"), atual)
    if novos[arq_sobre] != atual: mudou.append("sobre")
    if simular:
        print("simulação: nada foi gravado. Páginas com texto diferente do site:", ", ".join(mudou) or "nenhuma")
        return mudou
    for f, d in novos.items():
        jsonfmt.salvar(f, d)
    print("importado. Páginas atualizadas:", ", ".join(mudou) or "nenhuma (os md são iguais aos JSONs)")
    return mudou


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "exportar": exportar()
        elif cmd == "importar": importar(simular="--simular" in sys.argv)
        else: print(__doc__); sys.exit(2)
    except Erro as e:
        print("ERRO:", e); sys.exit(1)
