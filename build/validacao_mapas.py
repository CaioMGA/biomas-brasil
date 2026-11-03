"""Página única de validação dos mapas de localização (América do Sul), os mapas não interativos.

    python3 -I build/validacao_mapas.py            -> docs/validacao-mapas.html

Autocontido (CSS embutido, sem JS); abre direto do disco e NÃO vai para dist/.
"""
import html, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import localizacao

E = lambda s: html.escape(str(s), quote=True)
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BIOMAS = [("amazonia", "Amazônia"), ("caatinga", "Caatinga"), ("cerrado", "Cerrado"), ("mata-atlantica", "Mata Atlântica"), ("pampa", "Pampas"), ("pantanal", "Pantanal")]
COR = {"amazonia": "#5ea56e", "cerrado": "#b38b3c", "mata-atlantica": "#2da895", "caatinga": "#cb7a61", "pampa": "#9486cf", "pantanal": "#25a3ba"}   # --c-<bioma> de src/pagina.css


def ler(*p):
    return open(os.path.join(RAIZ, *p), encoding="utf-8").read()


def main():
    css = ler("src", "pagina.css")
    locs = []
    for id, nome in BIOMAS:
        if not os.path.exists(os.path.join(RAIZ, "data", "localizacao", id + ".json")): continue
        locs.append(f'<div class="v-loc" style="--accent:{COR[id]}">{localizacao.figura(RAIZ, id, nome)}</div>')
    pagina = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Biomas do Brasil — validação dos mapas de localização</title>
<style>{css}
.v-main {{ max-width: 1180px; margin: 0 auto; padding: 28px 22px 80px; }}
.v-main h1 {{ margin: 0; font: 400 clamp(36px, 5vw, 60px)/1 var(--display); }}
.v-main p {{ margin: 10px 0 0; max-width: 78ch; }}
.v-lista {{ margin: 10px 0 0; padding-left: 20px; max-width: 80ch; }} .v-lista li {{ margin-top: 4px; }}
.v-locs {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(560px, 1fr)); gap: 28px 24px; margin-top: 26px; }}
.v-loc .loc {{ margin: 0; align-items: flex-start; }}
@media (max-width: 640px) {{ .v-locs {{ grid-template-columns: 1fr; }} }}
</style></head>
<body><main class="v-main rd-main">
<p class="kicker">Biomas do Brasil · validação</p>
<h1>Mapas de localização atualizados</h1>
<p class="lead">Mapas estáticos da América do Sul, um por bioma. Os mapas temáticos interativos e o HERO MAP não foram alterados. Arquivo só para conferência; não faz parte de <code>dist/</code>.</p>
<ul class="v-lista">
<li><b>Coordenadas:</b> grade a cada 10° com graus nas bordas.</li>
<li><b>Linha do Equador</b> (vermelha tracejada) e <b>Trópico de Capricórnio</b> (magenta, traço-ponto, 23°26′ S).</li>
<li><b>Oceano Pacífico</b> e <b>Oceano Atlântico</b> nomeados; <b>seta do norte</b> no canto superior direito.</li>
<li>Legenda continua só com o bioma.</li>
</ul>
<div class="v-locs">{"".join(locs)}</div>
</main></body></html>"""
    out = os.path.join(RAIZ, "docs", "validacao-mapas.html")
    open(out, "w", encoding="utf-8").write(pagina)
    print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
