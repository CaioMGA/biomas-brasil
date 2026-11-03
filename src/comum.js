/* Código compartilhado pelo painel do mapa e pelas páginas: gráfico de chuva com escala e folha do passaporte (carimbos).
   Inlinado no template do mapa (__COMUM__) e no início de assets/site.js. Não declara nada além de BiomasUI. */
const BiomasUI = (() => {
  const NS = "http://www.w3.org/2000/svg";
  const MES3C = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"];   // abreviações de 3 letras do gráfico de chuva
  const MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
  const n1 = v => v.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const hash = s => { let h = 2166136261; for (const c of s) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; };
  const rnd = (s, k) => { const x = Math.sin(hash(s) % 9973 + k * 12.9898) * 43758.5453; return x - Math.floor(x); };   // [0,1) estável por bioma
  const wrap = (cls, html) => { const d = document.createElement("div"); d.className = cls; d.innerHTML = html; return d; };

  /* ---------- Gráfico de chuva: eixo em mm por mês, valor sobre cada barra e % do ano embaixo ---------- */
  function graficoChuva(r, topo, nome) {
    const max = Math.ceil(topo / 100) * 100;                  // mesmo eixo para todos os biomas, para comparar
    const W = 430, H = 216, L = 38, T = 24, Bt = 60, ph = H - T - Bt, base = T + ph;
    const y = v => T + ph * (1 - v / max);
    const total = r.mm.reduce((a, b) => a + b, 0);
    const col = (W - L) / 12, bw = col * .66;
    let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${nome ? "Chuva média mensal no bioma " + nome + ", em mm e em % do total anual: " : ""}${r.mm.map((v, k) => `${MESES[k]} ${v} mm (${n1(v / total * 100)}%)`).join("; ")}">`;
    s += `<text x="0" y="${T - 10}" class="ch-ax">mm/mês</text>`;
    for (let t = 0; t <= max; t += 100) s += `<line x1="${L}" x2="${W}" y1="${y(t)}" y2="${y(t)}" class="${t === 0 ? "ch-ax0" : "ch-gr"}"/><text x="${L - 6}" y="${y(t) + 3.5}" text-anchor="end" class="ch-ax">${t}</text>`;
    r.mm.forEach((v, k) => {
      const x = L + k * col + (col - bw) / 2, pk = k === r.pico;
      s += `<rect x="${x.toFixed(1)}" y="${y(v).toFixed(1)}" width="${bw.toFixed(1)}" height="${(base - y(v)).toFixed(1)}" class="ch-b${pk ? " ch-pk" : ""}"><title>${MESES[k]}: ${v} mm (${n1(v / total * 100)}% do ano)</title></rect>`;
      s += `<text x="${(x + bw / 2).toFixed(1)}" y="${(y(v) - 4).toFixed(1)}" text-anchor="middle" class="ch-v${pk ? " ch-pk" : ""}">${v}</text>`;
      const cx = (x + bw / 2).toFixed(1);
      s += `<text transform="translate(${(+cx + 3.5).toFixed(1)} ${base + 6}) rotate(-90)" text-anchor="end" class="ch-m">${MES3C[k]}</text>`;   // abreviação de 3 letras, na vertical
      s += `<text x="${cx}" y="${base + 44}" text-anchor="middle" class="ch-p">${n1(v / total * 100)}%</text>`;
    });
    s += `<text x="${L - 6}" y="${base + 44}" text-anchor="end" class="ch-ax">% ano</text></svg>`;
    const d = wrap("chuva", s); d.setAttribute("data-nocount", "");   // o painel do mapa anima números; aqui eles ficam fixos
    const cap = document.createElement("p"); cap.className = "cap";
    cap.textContent = `Chuva média mensal (WorldClim 2.1, 1970–2000). Eixo e valores sobre as barras: milímetros por mês. Linha de baixo: parte da chuva do ano, que soma ${total.toLocaleString("pt-BR")} mm.`;
    d.appendChild(cap);
    return d;
  }

  /* ---------- Folha do passaporte ---------- */
  const MES3 = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"];
  const fmtData = iso => { const m = /^(\d{4})-(\d\d)-(\d\d)/.exec(iso || ""); return m ? `${+m[3]} ${MES3[+m[2] - 1]} ${m[1]}` : ""; };
  const fit = (txt, w, max) => Math.min(max, w / (txt.length * .66));
  const FORMAS = ["circulo", "retangulo", "circulo2", "octogono", "elipse", "corte", "elipse2"];

  // mesmas cores do :root do mapa (--c-*), em hex: a imagem de compartilhamento é um SVG isolado, sem variáveis CSS
  const COR = { amazonia: "#5ea56e", cerrado: "#b38b3c", "mata-atlantica": "#2da895", caatinga: "#cb7a61", pampa: "#9486cf", pantanal: "#25a3ba", costeiro: "#5f96d2", brasil: "#1b2f8a", completa: "#c8352b" };

  /* Aplica a tinta (falhas e borda irregular), a rotação e a mistura por multiplicação: onde dois carimbos se sobrepõem, as cores se somam. */
  let novos = new Set();   // carimbos aceitos agora: entram na folha com a animação de carimbada
  function acabar(id, cor, pos, g, rot, dx, dy, sc, seed) {
    const defs = `<filter id="tt-${id}" x="-15%" y="-15%" width="130%" height="130%"><feTurbulence type="fractalNoise" baseFrequency="0.38" numOctaves="3" seed="${seed}" result="n"/><feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  2.6 0 0 0 -0.42" result="m"/><feComposite in="SourceGraphic" in2="m" operator="in" result="g"/><feTurbulence type="turbulence" baseFrequency="0.035" numOctaves="2" seed="${seed + 5}" result="w"/><feDisplacementMap in="g" in2="w" scale="2.6" xChannelSelector="R" yChannelSelector="G"/></filter>`;
    return { defs, g: `<g class="marca${novos.has(id) ? " novo" : ""}" style="mix-blend-mode:multiply" filter="url(#tt-${id})" opacity=".9"><g transform="translate(${(pos[0] + +dx).toFixed(1)} ${(pos[1] + +dy).toFixed(1)}) rotate(${rot}) scale(${sc})" fill="none" stroke="${cor}" stroke-linecap="round" stroke-linejoin="round" font-family="'Instrument Sans',system-ui,sans-serif">${g}</g></g>` };
  }

  function carimbo(reg, idx, pos, r, em) {
    const id = reg.id, cor = COR[id], nome = reg.nome.toUpperCase(), data = fmtData(em);
    const rot = ((rnd(id, 1) - .5) * 34).toFixed(1), dx = ((rnd(id, 2) - .5) * 10).toFixed(1), dy = ((rnd(id, 3) - .5) * 10).toFixed(1), sc = (.95 + rnd(id, 4) * .1).toFixed(3);
    const seed = 1 + hash(id) % 90, forma = id === "brasil" ? "brasil" : FORMAS[idx % FORMAS.length];
    const TX = `fill="${cor}" stroke="none"`;
    const txt = (t, y, fs, extra = "") => `<text x="0" y="${y}" text-anchor="middle" font-size="${fs.toFixed(1)}" ${extra}>${t}</text>`;
    const dupla = (draw) => draw(1, 2.6) + draw(0, 1);   // contorno grosso + fio interno
    let g = "";
    if (forma === "circulo" || forma === "circulo2") {
      const R = r, a = R - 12.5, b = R - 8.5;
      g += `<circle r="${R}" stroke-width="2.6"/><circle r="${R - 5}" stroke-width="1" ${forma === "circulo2" ? 'stroke-dasharray="1.3 2.6"' : ""}/>`;
      g += `<path id="at-${id}" d="M ${-a},0 A ${a} ${a} 0 0 1 ${a},0" fill="none" stroke="none"/><path id="ab-${id}" d="M ${-b},0 A ${b} ${b} 0 0 0 ${b},0" fill="none" stroke="none"/>`;
      g += `<text font-size="7.2" font-weight="700" letter-spacing="1.5" ${TX}><textPath href="#at-${id}" startOffset="50%" text-anchor="middle">BIOMAS DO BRASIL</textPath></text>`;
      g += `<text font-size="6.8" font-weight="700" letter-spacing="1.8" ${TX}><textPath href="#ab-${id}" startOffset="50%" text-anchor="middle">★ CARIMBADO ★</textPath></text>`;
      g += `<line x1="${-(R - 9)}" x2="${R - 9}" y1="-9" y2="-9" stroke-width="1"/><line x1="${-(R - 9)}" x2="${R - 9}" y1="9" y2="9" stroke-width="1"/>`;
      g += txt(nome, 4.5, fit(nome, 2 * R - 20, 13), `font-weight="800" ${TX}`);
      if (data) g += txt(data, 18.5, 7.6, `font-weight="700" letter-spacing=".6" ${TX}`);
    } else if (forma === "brasil") {   // losango alongado na horizontal, na proporção do da bandeira (cerca de 1,4 : 1)
      const Rx = r * 1.62, Ry = r * 1.16, rombo = k => `0,${-(Ry - k * .72)} ${Rx - k},0 0,${Ry - k * .72} ${-(Rx - k)},0`;
      g += `<polygon points="${rombo(0)}" stroke-width="3.2"/><polygon points="${rombo(6)}" stroke-width="1"/>`;
      // "BIOMAS DO BRASIL" corre pelas duas arestas superiores, por dentro: caminho paralelo às arestas (70% do losango) com o ápice arredondado
      const sx = Rx * .7, sy = Ry * .7, f = .16, A = [-sx, 0], T = [0, -sy], Z = [sx, 0], p = (u, v) => `${(u[0] + (v[0] - u[0]) * f).toFixed(2)},${(u[1] + (v[1] - u[1]) * f).toFixed(2)}`;
      g += `<path id="ar-${id}" d="M ${A[0]},${A[1]} L ${p(T, A)} Q ${T[0]},${T[1]} ${p(T, Z)} L ${Z[0]},${Z[1]}" fill="none" stroke="none"/>`;
      g += `<text font-size="7" font-weight="700" letter-spacing="1.3" ${TX}><textPath href="#ar-${id}" startOffset="50%" text-anchor="middle">BIOMAS DO BRASIL</textPath></text>`;
      g += `<line x1="${-Rx * .36}" x2="${Rx * .36}" y1="-9" y2="-9" stroke-width="1"/><line x1="${-Rx * .5}" x2="${Rx * .5}" y1="15" y2="15" stroke-width="1"/>`;
      g += txt(nome, 7, fit(nome, Rx * 1.0, 17), `font-weight="900" ${TX}`);
      g += txt(data || "★ ★ ★", 27, 7.8, `font-weight="700" letter-spacing=".6" ${TX}`);
    } else if (forma === "retangulo" || forma === "corte") {
      const w = r * 2.25, h = r * 1.5;
      if (forma === "retangulo") g += `<rect x="${-w / 2}" y="${-h / 2}" width="${w}" height="${h}" rx="5" stroke-width="2.6"/><rect x="${-w / 2 + 4.5}" y="${-h / 2 + 4.5}" width="${w - 9}" height="${h - 9}" rx="2.5" stroke-width="1"/>`;
      else { const c = 11, p = (k) => `${-w / 2 + k},${-h / 2} ${w / 2 - k},${-h / 2} ${w / 2},${-h / 2 + k} ${w / 2},${h / 2 - k} ${w / 2 - k},${h / 2} ${-w / 2 + k},${h / 2} ${-w / 2},${h / 2 - k} ${-w / 2},${-h / 2 + k}`; g += `<polygon points="${p(c)}" stroke-width="2.6"/><polygon points="${p(c - 3.5).replace(/,/g, ",")}" transform="scale(.93)" stroke-width="1"/>`; }
      g += txt("BIOMAS DO BRASIL", -h / 2 + 15, 7.2, `font-weight="700" letter-spacing="1.6" ${TX}`);
      g += `<line x1="${-w / 2 + 9}" x2="${w / 2 - 9}" y1="${-h / 2 + 20}" y2="${-h / 2 + 20}" stroke-width="1"/>`;
      g += txt(nome, 6, fit(nome, w - 24, 15), `font-weight="800" ${TX}`);
      g += `<line x1="${-w / 2 + 9}" x2="${w / 2 - 9}" y1="${h / 2 - 22}" y2="${h / 2 - 22}" stroke-width="1"/>`;
      g += txt(data || "★ ★ ★", h / 2 - 11, 7.8, `font-weight="700" letter-spacing=".6" ${TX}`);
    } else if (forma === "octogono") {
      const pts = k => Array.from({ length: 8 }, (_, i) => { const a = Math.PI / 8 + i * Math.PI / 4; return `${(Math.cos(a) * (r - k)).toFixed(1)},${(Math.sin(a) * (r - k)).toFixed(1)}`; }).join(" ");
      g += `<polygon points="${pts(-2)}" stroke-width="2.6"/><polygon points="${pts(4)}" stroke-width="1"/>`;
      g += txt("BIOMAS DO BRASIL", -r * .5, 6.8, `font-weight="700" letter-spacing="1.3" ${TX}`);
      g += txt(nome, 5, fit(nome, 2 * r - 22, 13.5), `font-weight="800" ${TX}`);
      g += txt(data || "★ ★ ★", r * .55, 7.6, `font-weight="700" letter-spacing=".6" ${TX}`);
    } else {   // elipse, elipse2
      const rx = r * 1.22, ry = r * .8;
      g += `<ellipse rx="${rx}" ry="${ry}" stroke-width="2.6"/><ellipse rx="${rx - 5}" ry="${ry - 5}" stroke-width="1" ${forma === "elipse2" ? 'stroke-dasharray="1.3 2.6"' : ""}/>`;
      g += txt("BIOMAS DO BRASIL", -ry * .42, 6.8, `font-weight="700" letter-spacing="1.4" ${TX}`);
      g += txt(nome, 5, fit(nome, 2 * rx - 30, 14), `font-weight="800" ${TX}`);
      g += txt(data || "★ ★ ★", ry * .62, 7.6, `font-weight="700" letter-spacing=".6" ${TX}`);
    }
    return acabar(id, cor, pos, g, rot, dx, dy, sc, seed);
  }

  /* Carimbo vermelho de conclusão: aparece quando todos os biomas foram carimbados, no canto superior direito da folha. */
  function carimboCompleta(P, c) {
    const [vx, vy, vw] = P.vb, cor = COR.completa, id = "completa", W = 136, H = 82, pos = [vx + vw - W / 2 - 15, vy + H / 2 + 12];
    const data = fmtData(c.completa);
    const TX = `fill="${cor}" stroke="none"`, tx = (t, y, fs, ex) => `<text x="0" y="${y}" text-anchor="middle" font-size="${fs.toFixed(1)}" ${ex} ${TX}>${t}</text>`;
    let g = `<rect x="${-W / 2}" y="${-H / 2}" width="${W}" height="${H}" rx="5" stroke-width="3"/><rect x="${-W / 2 + 5}" y="${-H / 2 + 5}" width="${W - 10}" height="${H - 10}" rx="2.5" stroke-width="1.1"/>`;
    g += tx("JORNADA PELOS", -H / 2 + 18, 8.4, 'font-weight="700" letter-spacing="1.8"') + tx("BIOMAS DO BRASIL", -H / 2 + 30, 9.4, 'font-weight="800" letter-spacing="1"');
    g += `<line x1="${-W / 2 + 10}" x2="${W / 2 - 10}" y1="${-H / 2 + 36}" y2="${-H / 2 + 36}" stroke-width="1.1"/>` + tx("COMPLETA", 14, fit("COMPLETA", W - 22, 25), 'font-weight="900" letter-spacing="1.2"');
    g += `<line x1="${-W / 2 + 10}" x2="${W / 2 - 10}" y1="22" y2="22" stroke-width="1.1"/>` + tx(data || "★ ★ ★", H / 2 - 11, 8, 'font-weight="700" letter-spacing=".8"');
    return acabar(id, cor, pos, g, -8, 0, 0, 1, 37);
  }

  const PAPEL = `<filter id="papel" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB"><feTurbulence type="fractalNoise" baseFrequency="0.012 0.017" numOctaves="4" seed="7" result="n"/><feDiffuseLighting in="n" surfaceScale="2.4" diffuseConstant="1.12" lighting-color="#fcf7e8" result="l"><feDistantLight azimuth="228" elevation="56"/></feDiffuseLighting><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="3" result="g"/><feColorMatrix in="g" type="matrix" values="0 0 0 0 .25  0 0 0 0 .2  0 0 0 0 .12  .16 0 0 0 0" result="gr"/><feBlend in="gr" in2="l" mode="normal"/></filter><radialGradient id="vig" cx="50%" cy="50%" r="75%"><stop offset="60%" stop-color="#7a5c28" stop-opacity="0"/><stop offset="100%" stop-color="#7a5c28" stop-opacity=".2"/></radialGradient>`;

  /* Papel timbrado: nome do site em fonte do site, no canto inferior direito. Medidas em unidades do viewBox da folha. */
  const TIMBRE = { dir: 14, base: 24, fs: 22, larg: 124, barra: 3.6, folga: 5 };
  const BANDEIRA = [["#009c3b", 0], ["#ffdf00", .3333], ["#002776", .6667], ["#fff", 1]];   // mesmo degradê da faixa do painel do Brasil na home
  function timbre(P) {   // o nome do site (na imagem de compartilhar ele é desenhado no canvas, que enxerga a fonte do site)
    const [vx, vy, vw, vh] = P.vb, lx = vx + vw - TIMBRE.dir, ly = vy + vh - TIMBRE.base;
    return `<text x="${lx}" y="${ly}" text-anchor="end" font-size="${TIMBRE.fs}" font-family="'Instrument Serif',Georgia,serif" fill="#23241f" textLength="${TIMBRE.larg}" lengthAdjust="spacingAndGlyphs">Biomas do Brasil</text>`;
  }
  /* Barra de gradiente abaixo do nome, com a mesma textura de tinta dos carimbos (mesmas falhas e borda irregular, com menos deslocamento
     porque a barra é fina) e a mesma mistura por multiplicação. */
  function barraTimbre(P) {
    const [vx, vy, vw, vh] = P.vb, lx = vx + vw - TIMBRE.dir, ly = vy + vh - TIMBRE.base, x0 = lx - TIMBRE.larg, y0 = ly + TIMBRE.folga;
    const defs = `<linearGradient id="bandeira" gradientUnits="userSpaceOnUse" x1="${x0}" x2="${lx}" y1="0" y2="0">${BANDEIRA.map(([c, o]) => `<stop offset="${o}" stop-color="${c}"/>`).join("")}</linearGradient>
<filter id="tt-barra" filterUnits="userSpaceOnUse" x="${x0 - 6}" y="${y0 - 5}" width="${TIMBRE.larg + 12}" height="${TIMBRE.barra + 10}"><feTurbulence type="fractalNoise" baseFrequency="0.38" numOctaves="3" seed="61" result="n"/><feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  2.6 0 0 0 -0.42" result="m"/><feComposite in="SourceGraphic" in2="m" operator="in" result="g"/><feTurbulence type="turbulence" baseFrequency="0.035" numOctaves="2" seed="66" result="w"/><feDisplacementMap in="g" in2="w" scale="1.4" xChannelSelector="R" yChannelSelector="G"/></filter>`;
    const el = `<g style="mix-blend-mode:multiply" filter="url(#tt-barra)" opacity=".9"><rect x="${x0}" y="${y0}" width="${TIMBRE.larg}" height="${TIMBRE.barra}" fill="url(#bandeira)" stroke="rgba(0,0,0,.28)" stroke-width=".3"/></g>`;
    return { defs, el };
  }

  /* SVG da folha: papel levemente amassado, contorno do Brasil e dos biomas em traço fino e falho, e os carimbos. */
  function svgFolha(P, c, isolado) {
    const [vx, vy, vw, vh] = P.vb;
    const bar = barraTimbre(P);
    let defs = PAPEL + bar.defs + `<filter id="falha" x="-2%" y="-2%" width="104%" height="104%"><feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="2" seed="11" result="n"/><feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  4 0 0 0 -1.15" result="m"/><feComposite in="SourceGraphic" in2="m" operator="in" result="g"/><feTurbulence type="turbulence" baseFrequency="0.06" numOctaves="1" seed="4" result="w"/><feDisplacementMap in="g" in2="w" scale="1.6" xChannelSelector="R" yChannelSelector="G"/></filter>`;
    let marks = "";
    P.regs.forEach((rg, i) => { if (c[rg.id] == null) return; const k = carimbo(rg, i, rg.pos, P.r, c[rg.id]); defs += k.defs; marks += k.g; });
    if (c.completa != null) { const k = carimboCompleta(P, c); defs += k.defs; marks += k.g; }   // só depois que o visitante aceita o carimbo de jornada completa
    return `<svg ${isolado ? `xmlns="http://www.w3.org/2000/svg" width="${vw * 4}" height="${vh * 4}" ` : ""}viewBox="${vx} ${vy} ${vw} ${vh}" role="img" aria-label="Folha do passaporte: contorno do Brasil e dos biomas e os carimbos dos biomas já completados" style="isolation:isolate"><defs>${defs}</defs>
<rect x="${vx}" y="${vy}" width="${vw}" height="${vh}" fill="#f1ebda" filter="url(#papel)"/><rect x="${vx}" y="${vy}" width="${vw}" height="${vh}" fill="url(#vig)"/>
<path d="${P.bio}" fill="none" stroke="#1c1c1c" stroke-width=".6" stroke-linejoin="round" stroke-dasharray="9 1.4 5 2.2 14 1 4 1.6 8 1.2 18 2.4" opacity=".8" filter="url(#falha)"/>
<path d="${P.d}" fill="none" stroke="#161616" stroke-width=".9" stroke-linejoin="round" stroke-dasharray="13 1.6 7 2.4 19 1.2 5 2 10 1.4 25 2.8 8 1.8" filter="url(#falha)"/>${isolado ? "" : timbre(P)}${bar.el}${marks}</svg>`;
  }

  /* P = {vb, d, bio, r, regs: [{id, nome, pos}]}; carimbados = {id: "AAAA-MM-DD" | ""} (só os biomas que passaram no quiz) */
  function folha(P, carimbados) { return wrap("folha", svgFolha(P, carimbados, false)); }

  /* JPEG com no máximo `max` bytes: baixa a qualidade aos poucos e, se ainda passar, reduz as dimensões. O canvas precisa estar opaco (JPEG não tem transparência). */
  const MAX_IMAGEM = 500000;
  async function jpegAte(cv, max) {
    const blob = (c, q) => new Promise(r => c.toBlob(r, "image/jpeg", q));
    let c = cv, esc = 1;
    for (let t = 0; t < 8; t++) {
      for (let q = .92; q >= .5; q -= .06) { const b = await blob(c, q); if (b && b.size <= max) return b; }
      esc *= .85; const n = document.createElement("canvas"); n.width = Math.round(cv.width * esc); n.height = Math.round(cv.height * esc);
      const x = n.getContext("2d"); x.imageSmoothingQuality = "high"; x.drawImage(cv, 0, 0, n.width, n.height); c = n;
    }
    return blob(c, .5);
  }

  /* Imagem do passaporte para compartilhar: a folha (SVG) sobre fundo escuro, com título e endereço do site.
     formato: "quadrado" (1080x1080), "stories" (1080x1920) ou "paisagem" (1600 de largura, altura pela folha). */
  let FORMATO = null;   // lido do localStorage só quando precisa (ler é declarado mais abaixo)
  const formatoAtual = () => FORMATO || (FORMATO = (v => ["quadrado", "stories", "paisagem"].includes(v) ? v : "quadrado")(ler("biomas:formato", "quadrado")));
  async function imagemPassaporte(P, c, formato = formatoAtual()) {
    const svg = svgFolha(P, c, true), [, , vw, vh] = P.vb;
    const img = await new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = no; i.src = URL.createObjectURL(new Blob([svg], { type: "image/svg+xml" })); });
    const n = P.regs.filter(r => c[r.id] != null).length, completo = c.completa != null;   // "completa" só existe depois de ganho
    const paisagem = formato === "paisagem", W = paisagem ? 1600 : 1080, m = paisagem ? 70 : 60;
    const titulo = paisagem ? ["Meu passaporte dos Biomas do Brasil"] : ["Meu passaporte dos", "Biomas do Brasil"], fs = paisagem ? 64 : 68, cab = paisagem ? 170 : (formato === "stories" ? 330 : 40 + titulo.length * 76 + 30), rod = paisagem ? 130 : (formato === "stories" ? 330 : 110);
    let sw = W - 2 * m, sh = Math.round(sw * vh / vw), H, top;
    if (paisagem) { H = cab + sh + rod; top = cab; }
    else { H = formato === "stories" ? 1920 : 1080; const livre = H - cab - rod; if (sh > livre) { sh = livre; sw = Math.round(sh * vw / vh); } top = cab + Math.round((livre - sh) / 2); }
    const sx = Math.round((W - sw) / 2);
    const cv = document.createElement("canvas"); cv.width = W; cv.height = H; const x = cv.getContext("2d");
    x.fillStyle = "#0b100c"; x.fillRect(0, 0, W, H);
    x.fillStyle = "#ece6d4"; x.textBaseline = "alphabetic"; x.font = `400 ${fs}px "Instrument Serif", Georgia, serif`;
    const y0 = paisagem ? 112 : (formato === "stories" ? 200 : 40 + fs);
    titulo.forEach((t, i) => { if (paisagem) x.fillText(t, m, y0); else { x.textAlign = "center"; x.fillText(t, W / 2, y0 + i * 76); } });
    x.textAlign = "left";
    x.save(); x.shadowColor = "rgba(0,0,0,.7)"; x.shadowBlur = 50; x.shadowOffsetY = 18; x.drawImage(img, sx, top, sw, sh); x.restore();
    {   // papel timbrado (o SVG isolado não enxerga as fontes da página, então ele é desenhado aqui)
      const k = sw / vw, rx = sx + sw - TIMBRE.dir * k, by = top + sh - TIMBRE.base * k;
      x.save(); x.fillStyle = "#23241f"; x.textAlign = "right"; x.font = `400 ${TIMBRE.fs * k}px "Instrument Serif", Georgia, serif`;
      const natural = x.measureText("Biomas do Brasil").width;   // o canvas só encolhe com maxWidth: aqui o texto é ajustado ao comprimento exato da barra, como o textLength do SVG
      x.translate(rx, by); x.scale(TIMBRE.larg * k / natural, 1); x.fillText("Biomas do Brasil", 0, 0);
      x.restore();
    }
    const yRodape = top + sh + (paisagem ? 70 : (formato === "stories" ? 110 : 62));
    x.font = '500 30px "Instrument Sans", system-ui, sans-serif'; x.textAlign = "left";
    if (completo) {   // cores da bandeira: a frase em amarelo e "completa" em verde (um peso acima)
      const frase = "Jornada pelos Biomas do Brasil ";
      x.fillStyle = "#ffdf00"; x.fillText(frase, sx, yRodape);
      const larg = x.measureText(frase).width;
      x.font = '600 30px "Instrument Sans", system-ui, sans-serif'; x.fillStyle = "#009c3b"; x.fillText("completa", sx + larg, yRodape);
      x.font = '500 30px "Instrument Sans", system-ui, sans-serif';
    } else { x.fillStyle = "#b6bba4"; x.fillText(`${n} de ${P.regs.length} carimbos`, sx, yRodape); }
    x.fillStyle = "#ece6d4"; x.textAlign = "right"; x.fillText(location.host, sx + sw, yRodape);
    URL.revokeObjectURL(img.src);
    return jpegAte(cv, MAX_IMAGEM);
  }
  async function compartilhar(P, c, btn) {
    const sp = btn.querySelector("span") || btn, lbl = sp.textContent; btn.disabled = true; sp.textContent = "Gerando imagem…";
    try {
      const blob = await imagemPassaporte(P, c), file = new File([blob], "passaporte-biomas-do-brasil.jpg", { type: "image/jpeg" });
      const completo = c.completa != null;
      const dados = { files: [file], title: "Meu passaporte dos Biomas do Brasil", text: completo ? "Completei minha jornada pelos Biomas do Brasil!" : "Meu passaporte dos Biomas do Brasil" };
      let enviado = false;
      if (navigator.canShare && navigator.canShare(dados)) { try { await navigator.share(dados); enviado = true; } catch (e) { if (e && e.name === "AbortError") enviado = true; } }
      if (!enviado) { const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = file.name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 5000); }
    } catch (e) { console.error(e); sp.textContent = "Não foi possível gerar"; setTimeout(() => { sp.textContent = lbl; btn.disabled = false; }, 2500); return; }
    sp.textContent = lbl; btn.disabled = false;
  }

  /* ---------- Estado dos carimbos (localStorage) ----------
     biomas:carimbos = { <bioma | "completa">: { em: "AAAA-MM-DD", ts: milissegundos, visto: true | false } }
     bioma: em = dia em que o quiz foi vencido. completa: em = dia do último carimbo, e só existe depois que os 8 carimbos (7 biomas + Quiz final do Brasil) foram ganhos.
     Todo carimbo entra direto na folha. "visto" só diz se a cena do overlay já foi mostrada para ele (false = a cena ainda vai acontecer). */
  const BIOMAS = ["amazonia", "cerrado", "mata-atlantica", "caatinga", "pampa", "pantanal", "costeiro", "brasil"];   // os 8 carimbos que levam ao de jornada completa
  const ler = (k, d, area = localStorage) => { try { const v = area.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const gravar = (k, v, area = localStorage) => { try { area.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const hoje = () => new Date().toLocaleDateString("sv-SE");
  const KC = "biomas:carimbos", KP = "biomas:prog";
  const avisar = () => dispatchEvent(new CustomEvent("biomas:carimbos"));
  function carimbos() {   // sincroniza com os quizzes já vencidos e cria o carimbo de jornada completa quando os 8 foram ganhos
    const c = ler(KC, {}), prog = ler(KP, {}); let mudou = false;
    for (const k in c) {   // formato antigo ({ aceito }): carimbo aceito ou pendente vira carimbo já visto; a "completa" nunca aceita some (agora ela exige os 8)
      if (c[k].visto !== undefined) continue;
      if (k === "completa" && !c[k].aceito) delete c[k]; else { c[k].visto = true; delete c[k].aceito; }
      mudou = true;
    }
    for (const id in prog) { const q = prog[id] && prog[id].quiz; if (q && q.ok / q.n >= .6 && !c[id]) { c[id] = { em: q.em || hoje(), ts: Date.now(), visto: false }; mudou = true; } }
    if (!c.completa && BIOMAS.every(id => c[id])) { c.completa = { em: BIOMAS.map(id => c[id].em).sort().pop(), ts: Date.now(), visto: false }; mudou = true; }
    if (mudou) gravar(KC, c);
    return c;
  }
  let PG = null, emCena = false;   // PG = dados do passaporte da página (definidos em iniciar)
  function registrarGanho(id) { const c = carimbos(); if (!c[id]) { c[id] = { em: hoje(), ts: Date.now(), visto: false }; gravar(KC, c); } avisar(); verificar(); }   // chamado quando o visitante vence o quiz
  const carimbado = id => !!carimbos()[id];
  const aceitos = () => { const o = {}, c = carimbos(); for (const id in c) o[id] = c[id].em; return o; };
  function marcarVistos(ids) { const c = carimbos(); ids.forEach(id => { if (c[id]) c[id].visto = true; }); gravar(KC, c); }
  /* Abre a cena do overlay quando há carimbo ainda não visto: em qualquer página, ao carregar ou logo depois de vencer um quiz. */
  function verificar() {
    if (!PG || emCena || /^\/lab-carimbo/.test(location.pathname)) return;
    const c = carimbos(), novos = BIOMAS.filter(id => c[id] && !c[id].visto);
    if (c.completa && !c.completa.visto) cena(PG, "completa", novos);
    else if (novos.length) cena(PG, "bioma", novos);
  }
  function iniciar(P) { PG = P; const ir = () => verificar(); if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ir); else setTimeout(ir, 0); }

  /* ---------- Parâmetros da animação (ajustáveis no lab-carimbo; o lab grava em localStorage "biomas:anim") ---------- */
  const ANIM_PADRAO = {
    suspense: 2000,            // cena de biomas: passaporte sozinho na tela antes do primeiro carimbo (ms)
    intervalo: 1000,           // cena de biomas: entre um carimbo e o próximo (ms)
    pausaMsg: 300,             // cena de biomas: do último carimbo até a mensagem (ms)
    pausaInicioFinal: 1500,    // jornada completa: papel em branco antes do primeiro carimbo (ms)
    intervaloFinal: 900,       // jornada completa: entre os carimbos de bioma (ms)
    suspenseVermelho: 2000,    // jornada completa: do último carimbo de bioma até o vermelho (ms)
    pausaMsgFinal: 1700,       // jornada completa: do vermelho até a mensagem (ms)
    queda: 200,                // duração da queda do carimbo na folha (ms)
    escalaQueda: 1.7,          // tamanho com que o carimbo começa a cair (1 = tamanho final)
    impacto: 50,               // do carimbo começar a cair até o passaporte tremer (ms)
    leve: { amp: 5, rot: .5, dur: 500 },      // tremor dos carimbos de bioma: deslocamento (px), giro (graus) e duração (ms)
    forte: { amp: 15, rot: 0, dur: 1540 },  // tremor do carimbo de jornada completa
    clarao: 3000               // duração do clarão vermelho do carimbo de jornada completa (ms)
  };
  function animAtual() { const o = ler("biomas:anim", {}); return { ...ANIM_PADRAO, ...o, leve: { ...ANIM_PADRAO.leve, ...(o.leve || {}) }, forte: { ...ANIM_PADRAO.forte, ...(o.forte || {}) } }; }
  function quedaCarimbo(raiz, A) {     // o carimbo recém-aceito cai sobre a folha
    const m = raiz.querySelector(".marca.novo"); if (!m || !m.animate) return;
    m.animate([{ transform: `scale(${A.escalaQueda})`, opacity: 0 }, { opacity: .9, offset: .5 }, { transform: "scale(1)", opacity: .9 }], { duration: Math.max(1, A.queda), easing: "cubic-bezier(.2,.9,.3,1.1)" });
  }
  function tremor(el, t) {             // oscilação amortecida do passaporte: amplitude (px), giro (graus) e duração (ms)
    if (!el || !el.animate || t.dur <= 0 || (t.amp <= 0 && t.rot <= 0) || (matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches)) return;
    const N = Math.max(6, Math.round(t.dur / 55)), kf = [];
    for (let i = 0; i <= N; i++) { const env = Math.pow(1 - i / N, 1.25), sg = i % 2 ? -1 : 1, z = i === 0 || i === N ? 0 : 1; kf.push({ offset: i / N, transform: `translate(${(sg * t.amp * env * z).toFixed(2)}px, ${(-sg * t.amp * .75 * env * z).toFixed(2)}px) rotate(${(sg * t.rot * env * z).toFixed(3)}deg)` }); }
    el.animate(kf, { duration: t.dur, easing: "linear" });
  }
  // Uma batida isolada (usada pelo lab): refaz a folha com o carimbo novo, deixa-o cair e faz o papel tremer.
  function demo(papel, fol, P, c, id, forte, A) {
    novos = new Set([id]); fol.innerHTML = svgFolha(P, c, false); novos = new Set(); quedaCarimbo(fol, A);
    setTimeout(() => tremor(papel, forte ? A.forte : A.leve), A.impacto);
  }

  /* ---------- A cena do carimbo ----------
     Overlay escuro em tela cheia com o passaporte no centro. Após 2 s de suspense o carimbo aparece e o passaporte treme; vários carimbos entram um após o outro.
     A cena da jornada completa refaz todos os carimbos em sequência e, depois de mais 2 s, bate o carimbo vermelho, com um tremor bem mais forte. */
  function cena(P, tipo, ids, sim) {   // sim: { antes, depois, anim } roda a cena sem tocar no armazenamento (lab)
    const mk = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
    const nomeDe = id => id === "brasil" ? "Brasil (Quiz final)" : P.regs.find(r => r.id === id).nome;
    const lista = a => a.length > 1 ? a.slice(0, -1).join(", ") + " e " + a[a.length - 1] : a[0];
    const A = sim ? sim.anim : animAtual();
    let antes, depois;
    if (sim) { antes = sim.antes; depois = sim.depois; }
    else {   // marca como visto já: se a página for fechada no meio da cena, ela não se repete
      depois = aceitos(); antes = { ...depois }; ids.forEach(i => { delete antes[i]; }); if (tipo === "completa") delete antes.completa;
      marcarVistos(tipo === "completa" ? [...ids, "completa"] : ids); emCena = true;
    }
    const foco = document.activeElement, root = document.documentElement;
    const ov = mk("div", "cena"), flash = mk("div", "cena-flash"), papel = mk("div", "cena-papel"), fol = wrap("folha", ""), msg = mk("div", "cena-msg"), bt = mk("div", "cena-bt"), pul = mk("button", "cena-pular", "Pular");
    ov.setAttribute("role", "dialog"); ov.setAttribute("aria-modal", "true"); ov.setAttribute("aria-label", tipo === "completa" ? "Carimbo de jornada completa" : "Carimbando o passaporte");
    msg.setAttribute("aria-live", "polite"); pul.type = "button";
    papel.appendChild(fol); ov.append(flash, papel, msg, pul); document.body.appendChild(ov); root.classList.add("cena-aberta");

    let pulou = false, fim = false; const espera = new Set();
    const esperar = ms => pulou ? Promise.resolve() : new Promise(r => { const t = setTimeout(feito, ms); function feito() { clearTimeout(t); espera.delete(feito); r(); } espera.add(feito); });
    const pintar = (c, novo) => { novos = new Set(novo ? [novo] : []); fol.innerHTML = svgFolha(P, c, false); };
    function batida(forte) {            // o carimbo cai, e o passaporte treme (mais forte no de jornada completa)
      if (pulou) return;
      quedaCarimbo(fol, A);
      setTimeout(() => {
        tremor(papel, forte ? A.forte : A.leve);
        if (forte && flash.animate) flash.animate([{ opacity: 1 }, { opacity: 0 }], { duration: Math.max(1, A.clarao), easing: "ease-out" });
      }, A.impacto);
    }
    const botao = (txt, cls, fn) => { const b = mk("button", cls, txt); b.type = "button"; b.addEventListener("click", fn); bt.appendChild(b); return b; };
    function fechar() { document.removeEventListener("keydown", tecla, true); ov.remove(); root.classList.remove("cena-aberta"); novos = new Set(); if (foco && foco.isConnected) foco.focus({ preventScroll: true }); if (!sim) { emCena = false; avisar(); } }
    function mostrar(titulo, linhas, final) {
      fim = true; pul.remove(); msg.classList.toggle("final", !!final);
      msg.append(mk("strong", "", titulo), ...linhas.map(t => mk("p", "", t)), bt); msg.classList.add("visivel");
    }
    function msgBioma() {
      const rec = ids.length, faltam = P.regs.filter(r => depois[r.id] == null).length;
      const quem = `${rec > 1 ? "Carimbos" : "Carimbo"}: ${lista(ids.map(nomeDe))}.`;
      const resto = faltam > 1 ? `Faltam ${faltam} carimbos para completar a jornada.` : faltam === 1 ? "Falta 1 carimbo para completar a jornada." : "Você reuniu todos os carimbos!";
      mostrar(rec > 1 ? `Você recebeu ${rec} carimbos!` : "Você recebeu 1 carimbo!", [quem, resto]);
      botao("Continuar", "sim", fechar).focus({ preventScroll: true });
    }
    function msgFinal(c) {
      mostrar("Jornada completa!", ["Você reuniu os oito carimbos e completou sua jornada pelos Biomas do Brasil, parabéns!"], true);
      botao("Compartilhar passaporte", "sim", ev => compartilhar(P, c, ev.currentTarget)); botao("Fechar", "", fechar).focus({ preventScroll: true });
    }
    async function roteiro() {
      if (tipo === "completa") {
        const c = {}; pintar(c); await esperar(A.pausaInicioFinal);
        // ordem: os carimbos mais antigos, o último vencido como penúltimo e o de jornada completa por último
        const todos = P.regs.map(r => r.id).filter(id => depois[id] != null), novos2 = ids.filter(id => id !== "completa" && depois[id] != null);
        const velhos = todos.filter(id => !novos2.includes(id)).sort((x, y) => depois[x] < depois[y] ? -1 : depois[x] > depois[y] ? 1 : 0);
        const ultimos = novos2.sort((x, y) => depois[x] < depois[y] ? -1 : depois[x] > depois[y] ? 1 : 0);
        for (const id of [...velhos, ...ultimos]) { c[id] = depois[id]; pintar(c, id); batida(false); await esperar(A.intervaloFinal); }
        await esperar(A.suspenseVermelho);            // suspense antes do carimbo de jornada completa
        c.completa = depois.completa; pintar(c, "completa"); batida(true); await esperar(A.pausaMsgFinal);
        msgFinal(c);
      } else {
        const c = { ...antes }; pintar(c); await esperar(A.suspense);   // suspense com o passaporte sozinho na tela
        for (const id of ids) { c[id] = depois[id]; pintar(c, id); batida(false); await esperar(A.intervalo); }
        await esperar(A.pausaMsg); msgBioma();
      }
    }
    function pular() { pulou = true; [...espera].forEach(f => f()); }
    function tecla(e) {
      if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); if (fim) fechar(); else pular(); }
      else if (e.key === "Tab") { const f = [...ov.querySelectorAll("button")]; if (!f.length) return; e.preventDefault(); const k = f.indexOf(document.activeElement); f[(k + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus(); }
    }
    pul.addEventListener("click", pular); document.addEventListener("keydown", tecla, true); pul.focus({ preventScroll: true });
    roteiro();
  }

  const ICO = {
    compartilhar: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 10.5l6.8-4M8.6 13.5l6.8 4"/></svg>',
    tocar: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor"><path d="M7 4.5v15a1 1 0 0 0 1.5.9l12-7.5a1 1 0 0 0 0-1.8l-12-7.5A1 1 0 0 0 7 4.5z"/></svg>'
  };
  const reduzido = () => matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const botaoIcone = (cls, icone, txt) => { const b = document.createElement("button"); b.type = "button"; b.className = cls; b.innerHTML = ICO[icone]; const t = document.createElement("span"); t.textContent = txt; b.appendChild(t); return b; };

  /* Confete (folhas e papéis nas cores dos biomas) que cai uma única vez sobre o selo de jornada completa. */
  function confete(alvo) {
    if (reduzido() || !alvo.animate) return;
    const cores = Object.values(COR), caixa = document.createElement("div"); caixa.className = "pass-confete"; caixa.setAttribute("aria-hidden", "true"); alvo.appendChild(caixa);
    for (let i = 0; i < 26; i++) {
      const e = document.createElement("i"), x = Math.random() * 100, r = (Math.random() - .5) * 720, dx = (Math.random() - .5) * 90, dur = 2200 + Math.random() * 1800, atraso = Math.random() * 700;
      e.style.cssText = `left:${x}%;background:${cores[i % cores.length]};border-radius:${i % 3 ? "2px" : "50% 0 50% 0"}`; caixa.appendChild(e);
      e.animate([{ transform: "translate(0,-10px) rotate(0)", opacity: 0 }, { opacity: 1, offset: .12 }, { transform: `translate(${dx}px,${alvo.offsetHeight + 40}px) rotate(${r}deg)`, opacity: 0 }], { duration: dur, delay: atraso, easing: "ease-in", fill: "both" });
    }
    setTimeout(() => caixa.remove(), 5000);
  }

  /* Na primeira vez que o passaporte aparece na sessão, os carimbos que o visitante já tem caem em sequência (rápido; desligado com prefers-reduced-motion). */
  function entrada(box) {
    if (reduzido() || ler("biomas:entrou", false, sessionStorage)) return;
    const f = box.querySelector(".folha"); if (!f || !f.querySelector(".marca") || !f.animate || !("IntersectionObserver" in window)) return;
    const io = new IntersectionObserver(es => {
      if (!es.some(e => e.isIntersecting)) return;
      io.disconnect(); gravar("biomas:entrou", true, sessionStorage);
      f.querySelectorAll(".marca").forEach((m, i) => m.animate([{ transform: `scale(1.4) rotate(${((Math.random() - .5) * 12).toFixed(1)}deg)`, opacity: 0 }, { opacity: .9, offset: .6 }, { transform: "scale(1) rotate(0)", opacity: .9 }], { duration: 260, delay: i * 120, easing: "cubic-bezier(.2,.9,.3,1.1)", fill: "backwards" }));
    }, { threshold: .4 });
    io.observe(f);
  }

  /* Bloco do passaporte: progresso (ou a tela de conquista), a folha com todos os carimbos e os botões.
     opts: { kicker: false tira o rótulo "Passaporte"; proximo(c) => {nome, href} sugere o próximo bioma; extra: botões ao lado do compartilhar; depois: nós abaixo dos botões } */
  function passaporte(P, opts = {}) {
    const box = document.createElement("div");
    const mk = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
    let confetiFeito = false, anterior = null;
    function desenhar() {
      const c = aceitos(), tot = P.regs.length, n = P.regs.filter(r => c[r.id] != null).length, completo = c.completa != null;
      box.replaceChildren();
      if (opts.kicker !== false) box.appendChild(mk("p", "kicker", "Passaporte"));
      if (completo) {
        const m = mk("div", "pass-fim"); m.append(mk("span", "pass-selo", "Jornada completa"), mk("strong", "", "Você completou a jornada!"), mk("span", "pass-fim-txt", "Os oito carimbos estão no seu passaporte. Parabéns!"));
        box.appendChild(m); if (!confetiFeito) { confetiFeito = true; confete(m); }
      } else {
        const pg = mk("div", "pass-prog"), barra = mk("div", "pass-barra"), i = document.createElement("i"); i.style.width = (n / tot * 100) + "%";
        barra.setAttribute("role", "progressbar"); barra.setAttribute("aria-valuemin", "0"); barra.setAttribute("aria-valuemax", String(tot)); barra.setAttribute("aria-valuenow", String(n)); barra.setAttribute("aria-label", "Carimbos do passaporte"); barra.appendChild(i);
        pg.append(mk("p", "lead", `${n} de ${tot} carimbos`), barra);
        const prox = opts.proximo && opts.proximo(c);
        if (prox) { const pp = mk("p", "pass-prox", "Próximo carimbo: "), a = mk("a", "", prox.nome); a.href = prox.href; pp.appendChild(a); pg.appendChild(pp); }
        else if (!opts.proximo) pg.appendChild(mk("p", "pass-prox", "Acerte o quiz de um bioma para ganhar o carimbo dele."));
        box.appendChild(pg);
      }
      box.appendChild(folha(P, c));
      const ac = mk("div", "pass-acoes");
      if (n) { const b = botaoIcone("pass-btn principal", "compartilhar", "Compartilhar passaporte"); b.addEventListener("click", () => compartilhar(P, aceitos(), b)); ac.appendChild(b); }
      (opts.extra || []).forEach(x => ac.appendChild(x));
      if (ac.children.length) box.appendChild(ac);
      if (n) {
        const fm = mk("div", "pass-formato"); fm.setAttribute("role", "group"); fm.setAttribute("aria-label", "Formato da imagem de compartilhar");
        fm.appendChild(mk("span", "", "Imagem:"));
        [["quadrado", "Quadrada"], ["stories", "Stories"], ["paisagem", "Horizontal"]].forEach(([k, t]) => {
          const x = mk("button", "", t); x.type = "button"; x.setAttribute("aria-pressed", String(formatoAtual() === k));
          x.addEventListener("click", () => { FORMATO = k; gravar("biomas:formato", k); fm.querySelectorAll("button").forEach(y => y.setAttribute("aria-pressed", String(y === x))); });
          fm.appendChild(x);
        });
        box.appendChild(fm);
      }
      (opts.depois || []).forEach(x => box.appendChild(x));
      if (anterior === null) setTimeout(() => entrada(box), 0);
      anterior = n;
    }
    const on = () => { if (box.__visto && !box.isConnected) { removeEventListener("biomas:carimbos", on); return; } if (box.isConnected) box.__visto = true; desenhar(); };
    addEventListener("biomas:carimbos", on); desenhar();
    return box;
  }

  /* Dados de teste do lab: roda a cena de verdade, mas sem gravar nada. */
  function simular(P, tipo, anim) {
    const A = anim || animAtual(), datas = ["2026-10-12", "2026-10-13", "2026-10-15", "2026-10-20", "2026-10-21", "2026-10-30", "2026-10-31"], bio = P.regs.filter(r => r.id !== "brasil");
    const todos = {}; bio.forEach((r, i) => { todos[r.id] = datas[i]; }); todos.brasil = "2026-10-31";
    if (tipo === "completa") { const d = { ...todos, completa: "2026-10-31" }; cena(P, "completa", ["completa"], { antes: todos, depois: d, anim: A }); }
    else { const antes = {}; bio.slice(0, 2).forEach(r => { antes[r.id] = todos[r.id]; }); const ids = bio.slice(2, 4).map(r => r.id), depois = { ...antes }; ids.forEach(i => { depois[i] = todos[i]; }); cena(P, "bioma", ids, { antes, depois, anim: A }); }
  }

  /* Refaz a animação com todos os carimbos já aceitos pelo visitante (nada é gravado). Devolve false se ele ainda não tem nenhum. */
  function rever(P) {
    const c = aceitos(), ids = P.regs.map(r => r.id).filter(id => c[id] != null);
    if (!ids.length && c.completa == null) return false;
    if (c.completa != null) cena(P, "completa", ["completa"], { antes: {}, depois: c, anim: animAtual() });
    else cena(P, "bioma", ids, { antes: {}, depois: c, anim: animAtual() });
    return true;
  }

  return { rever, iniciar, verificar, jpegAte, MAX_IMAGEM, ANIM_PADRAO, animAtual, demo, simular, graficoChuva, folha, passaporte, botaoIcone, carimbos, carimbado, registrarGanho, todosCarimbados: P => { const c = aceitos(); return P.regs.every(r => c[r.id] != null); } };
})();
