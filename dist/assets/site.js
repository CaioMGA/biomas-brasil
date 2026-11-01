/* Código compartilhado pelo painel do mapa e pelas páginas: gráfico de chuva com escala e folha do passaporte (carimbos).
   Inlinado no template do mapa (__COMUM__) e no início de assets/site.js. Não declara nada além de BiomasUI. */
const BiomasUI = (() => {
  const NS = "http://www.w3.org/2000/svg";
  const MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
  const n1 = v => v.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const hash = s => { let h = 2166136261; for (const c of s) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; };
  const rnd = (s, k) => { const x = Math.sin(hash(s) % 9973 + k * 12.9898) * 43758.5453; return x - Math.floor(x); };   // [0,1) estável por bioma
  const wrap = (cls, html) => { const d = document.createElement("div"); d.className = cls; d.innerHTML = html; return d; };

  /* ---------- Gráfico de chuva: eixo em mm por mês, valor sobre cada barra e % do ano embaixo ---------- */
  function graficoChuva(r, topo, nome) {
    const max = Math.ceil(topo / 100) * 100;                  // mesmo eixo para todos os biomas, para comparar
    const W = 430, H = 200, L = 38, T = 24, Bt = 44, ph = H - T - Bt, base = T + ph;
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
      s += `<text x="${(x + bw / 2).toFixed(1)}" y="${base + 13}" text-anchor="middle" class="ch-m">${"JFMAMJJASOND"[k]}</text>`;
      s += `<text x="${(x + bw / 2).toFixed(1)}" y="${base + 27}" text-anchor="middle" class="ch-p">${n1(v / total * 100)}%</text>`;
    });
    s += `<text x="${L - 6}" y="${base + 27}" text-anchor="end" class="ch-ax">% ano</text></svg>`;
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

  /* Imagem do passaporte para compartilhar: a folha (SVG) sobre fundo escuro, com título e endereço do site. */
  async function imagemPassaporte(P, c) {
    const svg = svgFolha(P, c, true), [, , vw, vh] = P.vb;
    const img = await new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = no; i.src = URL.createObjectURL(new Blob([svg], { type: "image/svg+xml" })); });
    const reg = P.regs.filter(r => r.id !== "brasil"), n = reg.filter(r => c[r.id] != null).length, completo = c.completa != null;   // "completa" só existe depois de aceito
    const W = 1600, m = 70, sw = W - 2 * m, sh = Math.round(sw * vh / vw), top = 170, H = top + sh + 130;
    const cv = document.createElement("canvas"); cv.width = W; cv.height = H; const x = cv.getContext("2d");
    x.fillStyle = "#0b100c"; x.fillRect(0, 0, W, H);
    x.fillStyle = "#ece6d4"; x.textBaseline = "alphabetic";
    x.font = '400 64px "Instrument Serif", Georgia, serif'; x.fillText("Meu passaporte dos Biomas do Brasil", m, 112);
    x.save(); x.shadowColor = "rgba(0,0,0,.7)"; x.shadowBlur = 50; x.shadowOffsetY = 18; x.drawImage(img, m, top, sw, sh); x.restore();
    {   // papel timbrado (o SVG isolado não enxerga as fontes da página, então ele é desenhado aqui)
      const k = sw / vw, rx = m + sw - TIMBRE.dir * k, by = top + sh - TIMBRE.base * k;
      x.save(); x.fillStyle = "#23241f"; x.textAlign = "right"; x.font = `400 ${TIMBRE.fs * k}px "Instrument Serif", Georgia, serif`;
      const natural = x.measureText("Biomas do Brasil").width;   // o canvas só encolhe com maxWidth: aqui o texto é ajustado ao comprimento exato da barra, como o textLength do SVG
      x.translate(rx, by); x.scale(TIMBRE.larg * k / natural, 1); x.fillText("Biomas do Brasil", 0, 0);
      x.restore();
    }
    const yRodape = top + sh + 70;
    x.font = '500 30px "Instrument Sans", system-ui, sans-serif';
    if (completo) {   // cores da bandeira: a frase em amarelo e "completa" em verde (um peso acima)
      const frase = "Jornada pelos Biomas do Brasil ";
      x.fillStyle = "#ffdf00"; x.fillText(frase, m, yRodape);
      const larg = x.measureText(frase).width;
      x.font = '600 30px "Instrument Sans", system-ui, sans-serif'; x.fillStyle = "#009c3b"; x.fillText("completa", m + larg, yRodape);
      x.font = '500 30px "Instrument Sans", system-ui, sans-serif';
    } else { x.fillStyle = "#b6bba4"; x.fillText(`${n} de ${reg.length} biomas carimbados`, m, yRodape); }
    x.fillStyle = "#ece6d4"; x.textAlign = "right"; x.fillText(location.host, W - m, yRodape);
    URL.revokeObjectURL(img.src);
    return jpegAte(cv, MAX_IMAGEM);
  }
  async function compartilhar(P, c, btn) {
    const lbl = btn.textContent; btn.disabled = true; btn.textContent = "Gerando imagem…";
    try {
      const blob = await imagemPassaporte(P, c), file = new File([blob], "passaporte-biomas-do-brasil.jpg", { type: "image/jpeg" });
      const completo = c.completa != null;
      const dados = { files: [file], title: "Meu passaporte dos Biomas do Brasil", text: completo ? "Completei minha jornada pelos Biomas do Brasil!" : "Meu passaporte dos Biomas do Brasil" };
      let enviado = false;
      if (navigator.canShare && navigator.canShare(dados)) { try { await navigator.share(dados); enviado = true; } catch (e) { if (e && e.name === "AbortError") enviado = true; } }
      if (!enviado) { const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = file.name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 5000); }
    } catch (e) { console.error(e); btn.textContent = "Não foi possível gerar"; setTimeout(() => { btn.textContent = lbl; btn.disabled = false; }, 2500); return; }
    btn.textContent = lbl; btn.disabled = false;
  }

  /* ---------- Estado dos carimbos (localStorage) ----------
     biomas:carimbos = { <bioma | "completa">: { em: "AAAA-MM-DD", aceito: true | false } }
     bioma: em = dia em que o quiz foi vencido. completa: em = dia do último carimbo de bioma, e só existe depois que os 7 biomas foram aceitos.
     Todo carimbo só entra na folha depois que o visitante aceita. */
  const BIOMAS = ["amazonia", "cerrado", "mata-atlantica", "caatinga", "pampa", "pantanal", "costeiro"];   // os 7 que contam para a jornada
  const ler = (k, d, area = localStorage) => { try { const v = area.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const gravar = (k, v, area = localStorage) => { try { area.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const hoje = () => new Date().toLocaleDateString("sv-SE");
  const KC = "biomas:carimbos", KP = "biomas:prog", KA = "biomas:adiado";
  const avisar = () => dispatchEvent(new CustomEvent("biomas:carimbos"));
  function carimbos() {   // sincroniza com os quizzes já vencidos e cria o carimbo de jornada completa quando os 7 biomas estão aceitos
    const c = ler(KC, {}), prog = ler(KP, {}); let mudou = false;
    for (const id in prog) { const q = prog[id] && prog[id].quiz; if (q && q.ok / q.n >= .6 && !c[id]) { c[id] = { em: q.em || hoje(), aceito: false }; mudou = true; } }
    if (!c.completa && BIOMAS.every(id => c[id] && c[id].aceito)) { c.completa = { em: BIOMAS.map(id => c[id].em).sort().pop(), aceito: false }; mudou = true; }
    if (mudou) gravar(KC, c);
    return c;
  }
  function registrarGanho(id) { const c = carimbos(); if (!c[id]) { c[id] = { em: hoje(), aceito: false }; gravar(KC, c); } avisar(); }   // chamado quando o visitante vence o quiz
  const carimbado = id => !!(carimbos()[id] && carimbos()[id].aceito);
  const aceitos = () => { const o = {}, c = carimbos(); for (const id in c) if (c[id].aceito) o[id] = c[id].em; return o; };
  const pendentes = ids => { const c = carimbos(); return ids.filter(id => c[id] && !c[id].aceito); };
  const completaPendente = () => { const x = carimbos().completa; return !!x && !x.aceito; };
  function marcar(ids) { const c = carimbos(); ids.forEach(id => { if (c[id]) c[id].aceito = true; }); gravar(KC, c); avisar(); }
  function adiar(ids) { gravar(KA, [...new Set([...ler(KA, [], sessionStorage), ...ids])], sessionStorage); avisar(); }   // "Depois": não pergunta de novo nesta sessão

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
    const nomeDe = id => P.regs.find(r => r.id === id).nome, regsBio = P.regs.filter(r => r.id !== "brasil");
    const lista = a => a.length > 1 ? a.slice(0, -1).join(", ") + " e " + a[a.length - 1] : a[0];
    const A = sim ? sim.anim : animAtual();
    let antes, depois;
    if (sim) { antes = sim.antes; depois = sim.depois; }
    else { antes = aceitos(); marcar(ids); depois = aceitos(); }   // aceita já: se a página for fechada no meio da cena, nada se perde
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
    function fechar() { document.removeEventListener("keydown", tecla, true); ov.remove(); root.classList.remove("cena-aberta"); novos = new Set(); if (foco && foco.isConnected) foco.focus({ preventScroll: true }); if (!sim) avisar(); }
    function mostrar(titulo, linhas, final) {
      fim = true; pul.remove(); msg.classList.toggle("final", !!final);
      msg.append(mk("strong", "", titulo), ...linhas.map(t => mk("p", "", t)), bt); msg.classList.add("visivel");
    }
    function msgBioma() {
      const rec = ids.length, bio = ids.filter(i => i !== "brasil").map(nomeDe), faltam = regsBio.filter(r => depois[r.id] == null).length;
      const quem = bio.length ? `${bio.length > 1 ? "Biomas" : "Bioma"}: ${lista(bio)}${ids.includes("brasil") ? " e o carimbo do Brasil" : ""}.` : "O carimbo do Brasil.";
      const resto = faltam > 1 ? `Faltam ${faltam} carimbos de biomas para completar a jornada.` : faltam === 1 ? "Falta 1 carimbo de bioma para completar a jornada." : "Você reuniu os carimbos de todos os biomas! Falta só carimbar a jornada completa.";
      mostrar(rec > 1 ? `Você recebeu ${rec} carimbos!` : "Você recebeu 1 carimbo!", [quem, resto]);
      botao("Continuar", "sim", fechar).focus({ preventScroll: true });
    }
    function msgFinal(c) {
      mostrar("Você carimbou todos os biomas!", ["Você completou sua jornada pelos Biomas do Brasil, parabéns!"], true);
      botao("Compartilhar passaporte", "sim", ev => compartilhar(P, c, ev.currentTarget)); botao("Fechar", "", fechar).focus({ preventScroll: true });
    }
    async function roteiro() {
      if (tipo === "completa") {
        const c = {}; pintar(c); await esperar(A.pausaInicioFinal);
        for (const r of P.regs.filter(r => depois[r.id] != null)) { c[r.id] = depois[r.id]; pintar(c, r.id); batida(false); await esperar(A.intervaloFinal); }
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

  /* Pergunta sobre a folha: aparece quando há carimbos ganhos e ainda não aceitos (e, depois de todos os biomas, o de jornada completa). */
  function aviso(P, tipo, pend, nomeDe) {
    let t;
    if (tipo === "completa") t = "Você coletou os carimbos de todos os biomas! Deseja carimbar sua jornada como COMPLETA agora?";
    else {
      const bi = pend.filter(i => i !== "brasil").map(nomeDe), br = pend.includes("brasil");
      const lista = a => a.length > 1 ? a.slice(0, -1).join(", ") + " e " + a[a.length - 1] : a[0];
      t = "Você recebeu ";
      if (!bi.length) t += "o carimbo do Brasil";
      else t += `${bi.length > 1 ? "os carimbos dos biomas" : "o carimbo do bioma"} ${lista(bi)}${br ? " e o carimbo do Brasil" : ""}`;
      t += ". Deseja carimbar seu passaporte agora?";
    }
    const box = document.createElement("div"); box.className = "folha-aviso"; box.setAttribute("role", "alertdialog"); box.setAttribute("aria-label", tipo === "completa" ? "Carimbo de jornada completa" : "Carimbos recebidos");
    const p = document.createElement("p"); p.textContent = t;
    const bs = document.createElement("div"); bs.className = "folha-aviso-bt";
    const sim = document.createElement("button"), dep = document.createElement("button"); sim.type = dep.type = "button"; sim.className = "sim"; sim.textContent = "Sim"; dep.textContent = "Depois";
    sim.addEventListener("click", () => cena(P, tipo, pend)); dep.addEventListener("click", () => adiar(pend));
    bs.append(sim, dep); box.append(p, bs); return box;
  }

  /* Bloco do passaporte: texto de progresso (ou a mensagem de jornada completa), a folha com os carimbos aceitos, a pergunta sobre os pendentes e o botão de compartilhar. */
  function passaporte(P) {
    const box = document.createElement("div"), ids = P.regs.map(r => r.id), nomeDe = id => P.regs.find(r => r.id === id).nome;
    const mk = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; e.textContent = txt; return e; };
    function desenhar() {
      const c = aceitos(), reg = P.regs.filter(r => r.id !== "brasil"), n = reg.filter(r => c[r.id] != null).length, completo = c.completa != null;
      box.replaceChildren(mk("p", "kicker", "Passaporte"));
      if (completo) { const m = mk("div", "pass-fim"); m.append(mk("strong", "", "Você carimbou todos os biomas!"), mk("span", "", "Você completou sua jornada pelos Biomas do Brasil, parabéns!")); box.appendChild(m); }
      else box.appendChild(mk("p", "lead", `${n} de ${reg.length} biomas carimbados. Acerte o quiz de um bioma para ganhar o carimbo dele.`));
      const f = folha(P, c), pend = pendentes(ids), adiados = ler(KA, [], sessionStorage);
      if (pend.length) { if (pend.some(id => !adiados.includes(id))) f.appendChild(aviso(P, "bioma", pend, nomeDe)); }
      else if (completaPendente() && !adiados.includes("completa")) f.appendChild(aviso(P, "completa", ["completa"], nomeDe));   // a jornada completa só é carimbada quando não há carimbo de bioma pendente
      box.appendChild(f);
      if (n || c.brasil != null) { const b = mk("button", "pass-btn", "Compartilhar passaporte"); b.type = "button"; b.addEventListener("click", () => compartilhar(P, c, b)); box.appendChild(b); }
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

  return { jpegAte, MAX_IMAGEM, ANIM_PADRAO, animAtual, demo, simular, graficoChuva, folha, passaporte, carimbos, carimbado, registrarGanho, todosCarimbados: P => { const c = aceitos(); return P.regs.filter(r => r.id !== "brasil").every(r => c[r.id] != null); } };
})();

/* Interatividade das páginas estáticas: progresso, quiz, vídeos, comparador, passaporte e sugestões. */
(() => {
  const D = (() => { try { return JSON.parse(document.getElementById("dados").textContent); } catch (e) { return null; } })();
  const el = (tag, attrs = {}, text) => {
    const e = document.createElement(tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  };
  // Mesmo armazenamento do mapa (chave "biomas:prog"), para o progresso valer nas duas pontas.
  const store = {
    get(k, d) { try { const v = localStorage.getItem("biomas:" + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("biomas:" + k, JSON.stringify(v)); } catch (e) {} }
  };
  const getProg = id => store.get("prog", {})[id] || { lidas: [], quiz: null };
  const setProg = (id, fn) => { const all = store.get("prog", {}); const p = all[id] || { lidas: [], quiz: null }; fn(p); all[id] = p; store.set("prog", all); };
  const fmt = n => n.toLocaleString("pt-BR");
  const regioes = D ? D.regioes : [];
  const lida = r => getProg(r.id).lidas.length >= r.secoes;

  function estado(r) {
    const pr = getProg(r.id);
    const cs = BiomasUI.carimbos(); if (cs[r.id]) return cs[r.id].aceito ? "\u2713 Carimbado" : "Carimbo a receber";   // ✓ só quando o carimbo já foi aceito
    if (lida(r)) return "Lido";
    return pr.lidas.length ? `${pr.lidas.length} de ${r.secoes} seções` : "";
  }
  function cartao(r) {
    const li = el("li"); const a = el("a", { class: "card" + (lida(r) ? " lido" : ""), href: r.url, style: `--col:${r.cor}` });
    a.append(el("h3", {}, r.nome), el("p", {}, r.intro));
    const meta = el("span", { class: "meta" }); const est = estado(r); if (est) meta.appendChild(el("span", { class: "selo", style: "margin-left:0" }, est));
    a.appendChild(meta); li.appendChild(a); return li;
  }

  // ---- passaporte: folha com um carimbo por bioma completado, aceito pelo visitante ----
  function passaporte(box) { box.appendChild(BiomasUI.passaporte(D.passaporte)); }

  // ---- rodapé: biomas ainda sem carimbo e já carimbados, em grupos separados (atualiza quando um carimbo é aceito) ----
  function proximos(box) {
    const topo = el("div"), pb = el("div", { class: "pass-bloco" }), gr = el("div"); passaporte(pb); box.append(topo, pb, gr);
    const draw = () => {
      const cs = BiomasUI.carimbos(), feito = id => !!(cs[id] && cs[id].aceito), completo = BiomasUI.todosCarimbados(D.passaporte), outros = regioes.filter(r => r.id !== D.id);
      const faltam = [...outros.filter(r => !feito(r.id) && !lida(r)), ...outros.filter(r => !feito(r.id) && lida(r))], feitos = outros.filter(r => feito(r.id));
      topo.replaceChildren(el("h2", {}, completo ? "Revisite seus biomas" : "Continue explorando")); gr.replaceChildren();
      const grupo = (titulo, lista) => { if (!lista.length) return; gr.appendChild(el("h3", { class: "grupo-titulo" }, titulo)); const ul = el("ul", { class: "cards" }); lista.forEach(r => ul.appendChild(cartao(r))); gr.appendChild(ul); };
      grupo("Ainda sem carimbo", faltam); grupo("Já carimbados", feitos);
    };
    draw(); addEventListener("biomas:carimbos", draw);
  }

  // ---- gráficos de chuva (eixo comum a todos os biomas) ----
  function chuvas() {
    const topo = Math.max(...Object.values(D.chuva).map(x => Math.max(...x.mm)));
    document.querySelectorAll(".chuva-bioma").forEach(box => { const r = D.chuva[box.dataset.bioma]; if (r) box.replaceWith(BiomasUI.graficoChuva(r, topo, (D.regioes.find(x => x.id === box.dataset.bioma) || {}).nome)); });
  }

  // ---- progresso de leitura ----
  function leitura() {
    const id = D.id; const lidas = new Set(getProg(id).lidas);
    const links = {}; document.querySelectorAll(".rd-toc a").forEach(a => { links[a.dataset.sec] = a; if (lidas.has(a.dataset.sec)) a.classList.add("vis"); });
    if ("IntersectionObserver" in window) {
      const obs = new IntersectionObserver(es => es.forEach(en => {
        if (!en.isIntersecting) return;
        const sid = en.target.dataset.end; if (sid === "quiz") return;   // o quiz só conta quando respondido
        if (links[sid]) links[sid].classList.add("vis");
        if (!lidas.has(sid)) { lidas.add(sid); setProg(id, p => { p.lidas = [...lidas]; }); }
      }));
      document.querySelectorAll("[data-end]").forEach(n => obs.observe(n));
    }
    const bi = document.querySelector(".rd-bar i");
    const onScroll = () => { const d = document.documentElement; bi.style.width = (d.scrollTop / Math.max(1, d.scrollHeight - d.clientHeight) * 100).toFixed(1) + "%"; };
    addEventListener("scroll", onScroll, { passive: true }); onScroll();
  }

  function videos() {
    document.querySelectorAll("button[data-yt]").forEach(btn => btn.addEventListener("click", () => {
      const f = el("iframe", { src: `https://www.youtube-nocookie.com/embed/${btn.dataset.yt}?autoplay=1&rel=0`, title: btn.dataset.titulo, allow: "autoplay; encrypted-media; picture-in-picture; fullscreen", allowfullscreen: "", referrerpolicy: "strict-origin-when-cross-origin" });
      btn.replaceWith(f);
    }));
  }

  function quiz() {
    const box = document.getElementById("quiz"); if (!box || !D.quiz.length) return;
    const id = D.id; let ok = 0, done = 0;
    const prev = getProg(id).quiz;
    if (prev) box.appendChild(el("p", { class: "cap" }, `Seu último resultado: ${prev.ok} de ${prev.n}.`));
    const res = el("div", { class: "res", hidden: "" });
    D.quiz.forEach((q, qi) => {
      const wrap = el("div", { class: "qq" }); wrap.appendChild(el("p", {}, `${qi + 1}. ${q.q}`));
      const opts = el("div", { class: "opts" }); const exp = el("p", { class: "exp", hidden: "" }, q.e);
      q.o.forEach((o, oi) => {
        const b = el("button", { type: "button" }, o);
        b.addEventListener("click", () => {
          opts.querySelectorAll("button").forEach((x, xi) => { x.disabled = true; if (xi === q.c) x.classList.add("certa"); });
          if (oi === q.c) ok++; else b.classList.add("errada");
          exp.hidden = false; done++;
          if (done === D.quiz.length) {
            const sel0 = ok / D.quiz.length >= .6;
            setProg(id, p => { const antes = p.quiz; if (antes && antes.ok / antes.n >= .6 && !sel0) return; p.quiz = { ok, n: D.quiz.length }; if (sel0) p.quiz.em = (antes && antes.em) || new Date().toLocaleDateString("sv-SE"); });
            const sel = sel0; if (sel0) BiomasUI.registrarGanho(id);   // guarda o carimbo ganho e o dia em que o quiz foi vencido
            res.hidden = false;
            res.replaceChildren(document.createTextNode(`Você acertou ${ok} de ${D.quiz.length}. ${sel ? "Carimbo conquistado! Ele espera por você no passaporte, no fim da página." : "Releia as seções e tente de novo para ganhar o carimbo."}`));
            const again = el("button", { type: "button" }, "Refazer o quiz"); again.addEventListener("click", () => location.reload()); res.appendChild(again);
          }
        });
        opts.appendChild(b);
      });
      wrap.append(opts, exp); box.appendChild(wrap);
    });
    box.appendChild(res);
  }

  function comparador() {
    const box = document.getElementById("comparador"); if (!box || !D.bio) return;
    const byId = Object.fromEntries(D.bio.map(b => [b.id, b]));
    const mk = def => { const s = el("select", { "aria-label": "Escolher bioma" }); D.bio.forEach(b => s.appendChild(el("option", { value: b.id }, b.name))); s.value = def; return s; };
    const a = mk("amazonia"), b = mk("cerrado"); const tbl = el("table", { class: "cmp" });
    const draw = () => {
      const A = byId[a.value], Bb = byId[b.value];
      const ch = x => D.chuva[x.id] ? `${fmt(D.chuva[x.id].ano)} mm, ${D.chuva[x.id].seco} ${D.chuva[x.id].seco === 1 ? "mês seco" : "meses secos"}` : "Não se aplica";
      const rows = [
        ["Área", x => x.km ? `${fmt(x.km)} km² (${x.pct}% do país)` : "Quase todo marítimo"],
        ["Espécies de plantas, algas e fungos", x => x.sp ? fmt(x.sp) : "Sem contagem comparável"],
        ["Chuva por ano", ch], ["Clima", x => x.climate], ["Vegetação", x => x.veg], ["Estados", x => x.states],
        ["Espécies emblemáticas", x => x.spp.map(s => s[0]).join(", ")]
      ];
      const thead = el("tr"); thead.append(el("th"), el("th", {}, A.name), el("th", {}, Bb.name)); tbl.replaceChildren(thead);
      rows.forEach(([k, f]) => { const tr = el("tr"); tr.append(el("th", {}, k), el("td", {}, f(A)), el("td", {}, f(Bb))); tbl.appendChild(tr); });
    };
    a.addEventListener("change", draw); b.addEventListener("change", draw); draw();
    const sel = el("div", { class: "cmp-sel" }); sel.append(a, el("span", { style: "align-self:center;color:var(--muted)" }, "contra"), b);
    box.append(sel, tbl);
  }

  if (!D) return;
  if (D.id === "hub") {
    passaporte(document.getElementById("passaporte"));
    const decorar = () => document.querySelectorAll("a.card").forEach(a => {
      const r = regioes.find(x => x.id === a.dataset.id); if (!r) return;
      a.classList.toggle("lido", lida(r));
      const est = estado(r), slot = a.querySelector(".estado"); slot.replaceChildren(); if (est) slot.appendChild(el("span", { class: "selo", style: "margin-left:0" }, est));
    });
    decorar(); addEventListener("biomas:carimbos", decorar);
  } else {
    leitura(); videos(); quiz(); comparador(); chuvas();
    proximos(document.getElementById("proximos"));
  }
})();
