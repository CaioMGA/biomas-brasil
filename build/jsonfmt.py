"""Escreve os JSONs de data/conteudo no estilo do projeto: objetos pequenos em uma linha, parágrafos um por linha."""
import json


def _dump(v):
    return json.dumps(v, ensure_ascii=False)


def _inline(v, limite):
    s = _dump(v)
    if isinstance(v, dict):
        s = "{ " + ", ".join(f"{_dump(k)}: {_dump(x)}" for k, x in v.items()) + " }" if v else "{}"
    elif isinstance(v, list):
        s = "[" + ", ".join(_dump(x) if not isinstance(x, dict) else _inline(x, limite) for x in v) + "]"
    return s if len(s) <= limite else None


def formatar(v, nivel=0):
    pad, pad2 = "  " * nivel, "  " * (nivel + 1)
    if isinstance(v, dict):
        if not v:
            return "{}"
        folha = all(not isinstance(x, (dict,)) and (not isinstance(x, list) or all(not isinstance(y, (dict, list)) for y in x)) for x in v.values())
        if folha and nivel > 0:   # objeto simples (sem objetos dentro): uma linha, se couber
            s = _inline(v, 700)
            if s:
                return s
        itens = [f"{pad2}{_dump(k)}: {formatar(x, nivel + 1)}" for k, x in v.items()]
        return "{\n" + ",\n".join(itens) + f"\n{pad}}}"
    if isinstance(v, list):
        if not v:
            return "[]"
        if all(not isinstance(x, (dict, list)) for x in v):
            s = _inline(v, 300)
            if s:
                return s
        return "[\n" + ",\n".join(f"{pad2}{formatar(x, nivel + 1)}" for x in v) + f"\n{pad}]"
    return _dump(v)


def salvar(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(formatar(dados) + "\n")
