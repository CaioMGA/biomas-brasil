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
<defs><linearGradient id="moldura" gradientUnits="userSpaceOnUse" x1="${vx}" y1="${vy}" x2="${vx + vw}" y2="${vy + vh}"><stop offset="0" stop-color="#9c7424"/><stop offset=".5" stop-color="#c9a24a"/><stop offset="1" stop-color="#8f6a1f"/></linearGradient></defs>
<g fill="none" stroke="url(#moldura)" opacity=".85"><rect x="${vx + 5}" y="${vy + 5}" width="${vw - 10}" height="${vh - 10}" rx="2" stroke-width="1.6"/><rect x="${vx + 9}" y="${vy + 9}" width="${vw - 18}" height="${vh - 18}" rx="1" stroke-width=".55"/></g>
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
  async function compartilhar(P, c, btn, formato) {
    const sp = btn.querySelector("span") || btn, lbl = sp.textContent; btn.disabled = true; sp.textContent = "Gerando imagem…";
    try {
      const blob = await imagemPassaporte(P, c, formato), file = new File([blob], "passaporte-biomas-do-brasil.jpg", { type: "image/jpeg" });
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
      mostrar("Jornada completa!", ["Você reuniu todos os carimbos e completou sua jornada pelos Biomas do Brasil, parabéns!"], true);
      botao("Compartilhar", "sim", ev => escolherFormato(P, ev.currentTarget)); botao("Fechar", "", fechar).focus({ preventScroll: true });
    }
    async function roteiro() {
      if (tipo === "completa") {
        const c = {}; pintar(c); await esperar(A.pausaInicioFinal);
        // ordem: os carimbos mais antigos, o último vencido como penúltimo e o de jornada completa por último
        const todos = P.regs.map(r => r.id).filter(id => depois[id] != null), novos2 = ids.filter(id => id !== "completa" && depois[id] != null);
        const ts = ler(KC, {}), cmp = (x, y) => (depois[x] < depois[y] ? -1 : depois[x] > depois[y] ? 1 : 0) || ((ts[x] && ts[x].ts) || 0) - ((ts[y] && ts[y].ts) || 0);   // por dia e, no mesmo dia, pela hora em que foi ganho
        const velhos = todos.filter(id => !novos2.includes(id)).sort(cmp), ultimos = novos2.sort(cmp);
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
      if (document.querySelector(".fmt-ov")) return;   // com o popup de formato aberto, as teclas são dele
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

  /* Popup do compartilhar: o visitante escolhe o formato da imagem e só então ela é gerada. */
  function escolherFormato(P, btn) {
    const mk = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
    const foco = document.activeElement, atual = formatoAtual();
    const ov = mk("div", "fmt-ov"), cx = mk("div", "fmt-cx"), h = mk("h2", "", "Compartilhar passaporte"), p = mk("p", "", "Escolha o formato da imagem:"), lista = mk("div", "fmt-lista"), cancelar = mk("button", "fmt-cancelar", "Cancelar");
    ov.setAttribute("role", "dialog"); ov.setAttribute("aria-modal", "true"); ov.setAttribute("aria-label", "Formato da imagem para compartilhar"); cancelar.type = "button";
    const bs = [["quadrado", "Quadrada", "1080 × 1080, boa para o feed"], ["stories", "Stories", "1080 × 1920, tela cheia no celular"], ["paisagem", "Horizontal", "1600 px de largura, boa para mensagens"]].map(([k, t, d]) => {
      const b = mk("button", "fmt-op"); b.type = "button"; b.setAttribute("aria-pressed", String(atual === k)); b.append(mk("strong", "", t), mk("span", "", d));
      b.addEventListener("click", () => { FORMATO = k; gravar("biomas:formato", k); fechar(); compartilhar(P, aceitos(), btn, k); }); lista.appendChild(b); return b;
    });
    function fechar() { document.removeEventListener("keydown", tecla, true); ov.remove(); if (foco && foco.isConnected) foco.focus({ preventScroll: true }); }
    function tecla(e) {
      if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); fechar(); }
      else if (e.key === "Tab") { const f = [...bs, cancelar]; e.preventDefault(); const k = f.indexOf(document.activeElement); f[(k + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus(); }
    }
    cancelar.addEventListener("click", fechar); ov.addEventListener("click", e => { if (e.target === ov) fechar(); }); document.addEventListener("keydown", tecla, true);
    cx.append(h, p, lista, cancelar); ov.appendChild(cx); document.body.appendChild(ov); (bs.find(b => b.getAttribute("aria-pressed") === "true") || bs[0]).focus({ preventScroll: true });
  }

  /* Capa do passaporte: couro verde com friso e emblema dourados (o losango e o círculo do ícone do site), do mesmo tamanho da folha. */
  function capaSvg(P) {
    const [, , vw, vh] = P.vb, W = 100, H = +(100 * vh / vw).toFixed(2), cx = W / 2, cy = +(H * .42).toFixed(2), ouro = "url(#ouro)";
    return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true" focusable="false"><defs>
<linearGradient id="couro" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1a5a3c"/><stop offset=".55" stop-color="#0f3d2a"/><stop offset="1" stop-color="#0a2b1d"/></linearGradient>
<linearGradient id="ouro" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f3dc8f"/><stop offset=".5" stop-color="#c9a24a"/><stop offset="1" stop-color="#e8cb7c"/></linearGradient>
<linearGradient id="lombada" x1="0" x2="1"><stop offset="0" stop-color="#000" stop-opacity=".5"/><stop offset=".07" stop-color="#000" stop-opacity=".12"/><stop offset=".12" stop-color="#fff" stop-opacity=".08"/><stop offset=".2" stop-color="#000" stop-opacity="0"/></linearGradient>
<filter id="grao" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3" seed="5" result="n"/><feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  .0 .0 .0 .5 -.12"/></filter>
<filter id="relevo" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur in="SourceAlpha" stdDeviation=".12" result="b"/><feOffset in="b" dx=".15" dy=".25" result="o"/><feComponentTransfer in="o" result="s"><feFuncA type="linear" slope=".7"/></feComponentTransfer><feMerge><feMergeNode in="s"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<rect width="${W}" height="${H}" rx="2" fill="url(#couro)"/><rect width="${W}" height="${H}" rx="2" filter="url(#grao)"/><rect width="${W}" height="${H}" rx="2" fill="url(#lombada)"/>
<g fill="none" stroke="${ouro}" filter="url(#relevo)"><rect x="5" y="5" width="${W - 10}" height="${H - 10}" rx="1" stroke-width=".7"/><rect x="7" y="7" width="${W - 14}" height="${H - 14}" stroke-width=".25"/>
<g transform="translate(${cx} ${cy})"><polygon points="0,-17 24,0 0,17 -24,0" stroke-width=".7"/><polygon points="0,-13.5 19,0 0,13.5 -19,0" stroke-width=".25"/><circle r="9.5" stroke-width=".7"/><path d="M-9 1.5Q0 -3.2 9 2.6" stroke-width="1.4" stroke-linecap="round"/></g></g>
<g fill="${ouro}" text-anchor="middle" filter="url(#relevo)"><text x="${cx}" y="${(H * .72).toFixed(2)}" font-family="'Instrument Serif',Georgia,serif" font-size="9.2" letter-spacing="1.2">PASSAPORTE</text>
<text x="${cx}" y="${(H * .8).toFixed(2)}" font-family="'Instrument Sans',system-ui,sans-serif" font-weight="600" font-size="3" letter-spacing="1.6">BIOMAS DO BRASIL</text></g></svg>`;
  }

  /* Bloco do passaporte: progresso (ou a tela de conquista), a folha com todos os carimbos e os botões.
     opts: { capa: true mostra o passaporte fechado, com capa que abre ao clicar nela; kicker: false tira o rótulo "Passaporte"; proximo(c) => {nome, href} sugere o próximo bioma; extra: botões ao lado do compartilhar; depois: nós abaixo dos botões } */
  function passaporte(P, opts = {}) {
    const box = document.createElement("div");
    const mk = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
    let confetiFeito = false, anterior = null, aberta = !opts.capa;   // com capa, o passaporte sempre começa fechado
    function desenhar() {
      const c = aceitos(), tot = P.regs.length, n = P.regs.filter(r => c[r.id] != null).length, completo = c.completa != null;
      box.replaceChildren();
      if (opts.kicker !== false) box.appendChild(mk("p", "kicker", "Passaporte"));
      if (completo) {
        const m = mk("div", "pass-fim"); m.append(mk("span", "pass-selo", "Jornada completa"), mk("strong", "", "Você completou a jornada!"), mk("span", "pass-fim-txt", "Todos os carimbos estão no seu passaporte. Parabéns!"));
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
      const fo = folha(P, c);
      if (opts.capa) {
        const lv = mk("div", "livreto" + (aberta ? " aberto" : "")), cv = mk("button", "capa"); lv.style.aspectRatio = `${P.vb[2]} / ${P.vb[3]}`;
        cv.type = "button"; cv.setAttribute("aria-label", "Abrir o passaporte"); cv.innerHTML = capaSvg(P); if (aberta) cv.hidden = true;
        const abrir = () => {
          if (aberta) return; aberta = true; lv.classList.add("aberto");
          setTimeout(() => { cv.hidden = true; entrada(box); }, reduzido() ? 0 : 1000);
        };
        cv.addEventListener("click", abrir);
        lv.append(fo, cv); box.appendChild(lv);
      } else box.appendChild(fo);
      const ac = mk("div", "pass-acoes");
      if (n) { const b = botaoIcone("pass-btn principal", "compartilhar", "Compartilhar"); b.addEventListener("click", () => escolherFormato(P, b)); ac.appendChild(b); }
      (opts.extra || []).forEach(x => ac.appendChild(x));
      if (ac.children.length) box.appendChild(ac);
      (opts.depois || []).forEach(x => box.appendChild(x));
      if (anterior === null && aberta) setTimeout(() => entrada(box), 0);
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

/* Interatividade das páginas estáticas: progresso, quiz, vídeos, comparador, passaporte e sugestões. */
(() => {
  // altura real do header (o menu pode quebrar de linha no celular): a barra de leitura gruda logo abaixo dele
  const topoEl = document.querySelector(".topo"); if (topoEl && window.ResizeObserver) new ResizeObserver(() => document.documentElement.style.setProperty("--topo-h", topoEl.offsetHeight + "px")).observe(topoEl);
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
  const nLidas = id => getProg(id).lidas.filter(s => s !== "mapa").length;   // o mapa temático não conta como seção lida
  const lida = r => nLidas(r.id) >= r.secoes;

  const carimbadoR = r => !!BiomasUI.carimbos()[r.id];
  function estado(r) {
    if (carimbadoR(r)) return "";   // o mini-carimbo do card já diz que está carimbado
    if (lida(r)) return "Lido";
    return nLidas(r.id) ? `${nLidas(r.id)} de ${r.secoes} seções` : "";
  }
  // estados do card: carimbado (mini-carimbo inclinado na cor do bioma) ou sem carimbo (silhueta apagada, contorno tracejado e convite ao quiz)
  function marcarCartao(a, r) {
    const ok = carimbadoR(r); a.classList.toggle("carimbado", ok); a.classList.toggle("sem-carimbo", !ok); a.classList.toggle("lido", lida(r));
    let mini = a.querySelector(".mini-carimbo"); if (ok && !mini) { mini = el("span", { class: "mini-carimbo", "aria-label": "Carimbado" }, "Carimbado"); a.appendChild(mini); } else if (!ok && mini) mini.remove();
    const meta = a.querySelector(".meta"); if (!meta) return;
    meta.replaceChildren(); const est = estado(r); if (est) meta.appendChild(el("span", { class: "selo", style: "margin-left:0" }, est));
    if (!ok) meta.appendChild(el("span", { class: "dica-quiz" }, r.id === "brasil" ? "Faça o Quiz final para carimbar \u2192" : "Faça o quiz para carimbar \u2192"));
  }
  function cartao(r) {
    const li = el("li"); const a = el("a", { class: "card", href: r.url, style: `--col:${r.cor}` });
    a.append(el("h3", {}, r.nome), el("p", {}, r.intro), el("span", { class: "meta" })); li.appendChild(a); marcarCartao(a, r); return li;
  }

  // ---- passaporte: folha com os carimbos do visitante ----
  function passaporte(box, opts) { box.appendChild(BiomasUI.passaporte(D.passaporte, opts)); }

  // ---- rodapé: biomas ainda sem carimbo e já carimbados, em grupos separados (atualiza quando um carimbo é aceito) ----
  function proximos(box) {
    const topo = el("div"), pb = el("div", { class: "pass-bloco" }), gr = el("div"); passaporte(pb); box.append(topo, pb, gr);
    const draw = () => {
      const cs = BiomasUI.carimbos(), feito = id => !!cs[id], completo = BiomasUI.todosCarimbados(D.passaporte), outros = regioes.filter(r => r.id !== D.id);
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
        if (sid === "mapa") return;   // o mapa temático não é gravado no progresso compartilhado com o HERO MAP
        if (!lidas.has(sid)) { lidas.add(sid); setProg(id, p => { p.lidas = [...lidas]; }); }
      }));
      document.querySelectorAll("[data-end]").forEach(n => obs.observe(n));
    }
    const bi = document.querySelector(".rd-bar i");
    const onScroll = () => { const d = document.documentElement; bi.style.width = (d.scrollTop / Math.max(1, d.scrollHeight - d.clientHeight) * 100).toFixed(1) + "%"; };
    addEventListener("scroll", onScroll, { passive: true }); onScroll();
  }

  // ---- telas estreitas: botão fixo que abre o painel de seções (o índice lateral some) ----
  function painelSecoes() {
    const toc = document.querySelector(".rd-toc"); if (!toc) return;
    const orig = [...toc.querySelectorAll("a[data-sec]")]; if (!orig.length) return;
    const html = document.documentElement, estreita = matchMedia("(max-width: 860px)");
    const reduz = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
    const secs = orig.map(a => document.getElementById("sec-" + a.dataset.sec));
    const fab = el("button", { type: "button", class: "toc-fab", "aria-haspopup": "dialog", "aria-expanded": "false", "aria-controls": "toc-painel" });
    const atualTxt = el("span", { class: "toc-fab-atual" }, orig[0].textContent);
    const txt = el("span", { class: "toc-fab-txt" }); txt.append(el("span", { class: "toc-fab-rot" }, "Seções"), atualTxt);
    fab.append(el("span", { class: "toc-fab-icone", "aria-hidden": "true" }), txt);
    const fundo = el("div", { class: "toc-fundo", hidden: "" });
    const painel = el("div", { class: "toc-painel", id: "toc-painel", role: "dialog", "aria-modal": "true", "aria-label": "Seções desta página", hidden: "" });
    const cab = el("div", { class: "toc-cab" }), min = el("button", { type: "button", class: "toc-min", "aria-label": "Minimizar painel de seções" });
    min.append(el("span", { class: "toc-min-seta", "aria-hidden": "true" }), el("span", {}, "Minimizar"));
    cab.append(el("strong", {}, "Seções"), min);
    const lista = el("nav", { class: "toc-lista", "aria-label": "Seções" });
    const links = orig.map(a => {
      const l = el("a", { href: "#sec-" + a.dataset.sec, "data-sec": a.dataset.sec }, a.firstChild.textContent);
      const m = a.querySelector("small"); if (m) l.appendChild(el("small", {}, m.textContent));
      lista.appendChild(l); return l;
    });
    painel.append(cab, lista); document.body.append(fundo, painel, fab);

    let aberto = false, atual = -1;
    const marcar = i => {
      if (i === atual) return; atual = i;
      atualTxt.textContent = orig[i].firstChild.textContent;
      links.forEach((l, k) => { if (k === i) l.setAttribute("aria-current", "location"); else l.removeAttribute("aria-current"); });
    };
    let raf = 0;
    const medir = () => {
      raf = 0; let i = 0;
      secs.forEach((s, k) => { if (s && s.getBoundingClientRect().top <= 140) i = k; });
      if (innerHeight + scrollY >= html.scrollHeight - 4) i = secs.length - 1;
      marcar(i);
    };
    addEventListener("scroll", () => { if (!raf) raf = requestAnimationFrame(medir); }, { passive: true }); medir();

    function abrir() {
      if (aberto) return; aberto = true;
      links.forEach((l, k) => l.classList.toggle("vis", orig[k].classList.contains("vis")));   // seções já lidas
      fundo.hidden = painel.hidden = false; fab.hidden = true; fab.setAttribute("aria-expanded", "true"); html.classList.add("toc-aberto");
      const alvo = links[Math.max(0, atual)]; alvo.focus({ preventScroll: true }); alvo.scrollIntoView({ block: "center" });
    }
    function fechar(devolverFoco) {   // sem transição de saída: o painel some na hora
      if (!aberto) return; aberto = false;
      fundo.hidden = painel.hidden = true; fab.hidden = false; fab.setAttribute("aria-expanded", "false"); html.classList.remove("toc-aberto");
      if (devolverFoco) fab.focus({ preventScroll: true });
    }
    fab.addEventListener("click", abrir); min.addEventListener("click", () => fechar(true)); fundo.addEventListener("click", () => fechar(true));
    document.addEventListener("keydown", e => {
      if (!aberto) return;
      if (e.key === "Escape") { e.preventDefault(); fechar(true); }
      else if (e.key === "Tab") { const f = [min, ...links]; const k = f.indexOf(document.activeElement); e.preventDefault(); f[(k + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus(); }
    });
    estreita.addEventListener("change", () => { if (!estreita.matches) fechar(false); });
    links.forEach((l, k) => l.addEventListener("click", ev => {
      ev.preventDefault(); const alvo = secs[k]; fechar(false);   // fecha primeiro (destrava a rolagem) e rola em seguida
      if (!alvo) return;
      if (l.dataset.sec === "creditos") { const d = alvo.querySelector("details"); if (d) d.open = true; }
      alvo.scrollIntoView({ behavior: reduz() ? "auto" : "smooth", block: "start" });
      try { history.replaceState(null, "", "#" + alvo.id); } catch (e) {}   // endereço da seção, sem recarregar a página
    }));
  }

  // ---- página final da jornada: "Ver carimbos" refaz a animação com os carimbos que o visitante já tem ----
  function verCarimbos() {
    const b = BiomasUI.botaoIcone("pass-btn", "tocar", "Ver carimbos"), msg = el("p", { class: "pass-sem", role: "alert" });
    const primeiro = regioes.find(r => r.id !== "brasil");
    b.addEventListener("click", () => {
      if (BiomasUI.rever(D.passaporte)) { msg.replaceChildren(); return; }
      msg.replaceChildren(document.createTextNode("Você ainda não venceu nenhum quiz. "), el("a", { href: primeiro.url }, `Comece pelo bioma ${primeiro.nome}`), document.createTextNode("."));
    });
    return { b, msg };
  }
  // primeiro bioma da fila (na ordem do site) que ainda não tem carimbo; o Brasil (Quiz final) fica por último
  const proximoSemCarimbo = () => { const cs = BiomasUI.carimbos(); return regioes.find(r => r.id !== "brasil" && !cs[r.id]) || (cs.brasil ? null : regioes.find(r => r.id === "brasil")); };
  // checklist: um slot por carimbo (os 7 biomas e o Quiz final); o carimbado mostra a data, o vazio leva ao quiz
  function checklist() {
    const ul = el("ul", { class: "pass-lista", "aria-label": "Carimbos do passaporte" });
    const MES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
    const data = iso => { const m = /^(\d{4})-(\d\d)-(\d\d)/.exec(iso || ""); return m ? `${+m[3]} ${MES[+m[2] - 1]} ${m[1]}` : ""; };
    const desenhar = () => {
      const cs = BiomasUI.carimbos(); ul.replaceChildren();
      regioes.forEach(r => {
        const ok = !!cs[r.id], a = el("a", { class: "pass-slot " + (ok ? "carimbado" : "vazio"), href: r.url, style: `--col:${r.cor}` });
        const nome = r.id === "brasil" ? "Brasil" : r.nome, sub = ok ? (data(cs[r.id].em) || "Carimbado") : (r.id === "brasil" ? "Fazer o Quiz final \u2192" : "Fazer o quiz \u2192");
        a.append(el("span", { class: "pass-slot-ico", "aria-hidden": "true" }, ok ? "\u2713" : ""), (() => { const t = el("span", { class: "pass-slot-txt" }); t.append(el("b", {}, nome), el("small", {}, sub)); return t; })());
        const li = el("li"); li.appendChild(a); ul.appendChild(li);
      });
    };
    desenhar(); addEventListener("biomas:carimbos", desenhar); return ul;
  }
  function jornada(box) {
    const intro = document.getElementById("jornada-intro"), v = verCarimbos();
    const texto = () => { if (intro) intro.textContent = BiomasUI.carimbos().completa ? "Parabéns! Seu passaporte está completo. Revisite qualquer bioma quando quiser." : "Aqui ficam os carimbos que você reuniu. Vença o quiz de cada bioma, e o Quiz final do Brasil, para completar seu passaporte. Você consegue?"; };
    passaporte(box, { capa: true, kicker: false, extra: [v.b], depois: [v.msg, checklist()], proximo: () => { const r = proximoSemCarimbo(); return r && { nome: r.id === "brasil" ? "Brasil (Quiz final)" : r.nome, href: r.url }; } });
    texto(); addEventListener("biomas:carimbos", texto);
  }

  // ---- fim da página do Brasil: o "próximo" é o primeiro bioma sem carimbo; com todos os biomas carimbados, leva ao hub ----
  function proximoDinamico() {
    const box = document.getElementById("prox-dinamico"); if (!box) return;
    const mostrar = () => {
      const r = regioes.find(x => x.id !== "brasil" && !BiomasUI.carimbos()[x.id]), alvo = r ? r.id : "hub";
      box.querySelectorAll("[data-prox]").forEach(n => { n.hidden = n.dataset.prox !== alvo; });
    };
    mostrar(); addEventListener("biomas:carimbos", mostrar);
  }

  // ---- mapa de localização (não interativo): clique abre num overlay, o maior possível, com o mesmo recorte e proporção ----
  function mapaAmpliavel() {
    document.querySelectorAll(".loc-mapa").forEach(box => {
      const svg = box.querySelector("svg"); if (!svg) return;
      box.classList.add("loc-zoom"); box.setAttribute("role", "button"); box.setAttribute("tabindex", "0"); box.setAttribute("aria-haspopup", "dialog"); box.setAttribute("aria-label", "Ampliar o mapa");
      const abrir = () => {
        const html = document.documentElement, foco = document.activeElement;
        const ov = el("div", { class: "loc-ov", role: "dialog", "aria-modal": "true", "aria-label": "Mapa ampliado" });
        const fechar = el("button", { type: "button", class: "loc-ov-fechar" }, "Fechar"), caixa = el("div", { class: "loc-ov-mapa" });
        const grande = svg.cloneNode(true); grande.removeAttribute("width"); grande.removeAttribute("height"); caixa.appendChild(grande);
        const fonte = document.querySelector(".loc-fonte"), fontes = fonte && el("p", { class: "loc-ov-fonte" }); if (fontes) fontes.innerHTML = fonte.innerHTML;   // as fontes do mapa, abaixo dele
        ov.append(fechar, caixa); if (fontes) ov.append(fontes); document.body.appendChild(ov); html.classList.add("loc-aberto"); fechar.focus({ preventScroll: true });
        const fim = () => { document.removeEventListener("keydown", tecla, true); ov.remove(); html.classList.remove("loc-aberto"); if (foco && foco.isConnected) foco.focus({ preventScroll: true }); };
        const tecla = e => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); fim(); } else if (e.key === "Tab") { e.preventDefault(); fechar.focus(); } };
        fechar.addEventListener("click", fim); ov.addEventListener("click", e => { if (e.target === ov) fim(); }); document.addEventListener("keydown", tecla, true);
      };
      box.addEventListener("click", abrir);
      const dica = box.closest(".hero-loc"); if (dica) dica.querySelectorAll(".loc-dica").forEach(b => b.addEventListener("click", abrir));   // "Mais detalhes" abre o mesmo mapa grande
      box.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); abrir(); } });
    });
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
            res.replaceChildren(document.createTextNode(`Você acertou ${ok} de ${D.quiz.length}. ${sel ? "Carimbo conquistado! Ele já está no seu passaporte." : "Releia as seções e tente de novo para ganhar o carimbo."}`));
            if (sel) res.appendChild(el("a", { class: "res-link", href: "/biomas/jornada/" }, "Ver no passaporte"));
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

  // Carrossel de fichas de espécies: rolagem com snap; aqui entram botões, contador "i de n" e setas do teclado
  function carrosseis() {
    const reduz = matchMedia("(prefers-reduced-motion: reduce)").matches;
    document.querySelectorAll(".car").forEach(car => {
      const tr = car.querySelector(".car-track"), n = tr.children.length, ctl = car.querySelector(".car-ctl");
      const cnt = car.querySelector(".car-n"), pv = car.querySelector(".car-prev"), nx = car.querySelector(".car-next"); let raf = 0;
      const idx = () => Math.round(tr.scrollLeft / Math.max(1, tr.clientWidth));
      const ir = i => tr.scrollTo({ left: Math.max(0, Math.min(n - 1, i)) * tr.clientWidth, behavior: reduz ? "auto" : "smooth" });
      const atual = () => { const i = idx(); cnt.textContent = `${i + 1} de ${n}`; pv.disabled = i <= 0; nx.disabled = i >= n - 1; };
      tr.addEventListener("scroll", () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(atual); }, { passive: true });
      pv.addEventListener("click", () => ir(idx() - 1)); nx.addEventListener("click", () => ir(idx() + 1));
      tr.addEventListener("keydown", e => { if (e.key === "ArrowRight") { e.preventDefault(); ir(idx() + 1); } else if (e.key === "ArrowLeft") { e.preventDefault(); ir(idx() - 1); } });
      addEventListener("resize", atual); ctl.hidden = false; atual();
    });
  }

  if (!D) return;
  // Créditos e fontes começam fechados; abrem quando o endereço ou o link do índice apontam para eles
  const abrirCreditos = () => { if (location.hash === "#sec-creditos") { const d = document.querySelector("#sec-creditos details"); if (d) d.open = true; } };
  abrirCreditos(); addEventListener("hashchange", abrirCreditos);
  document.querySelectorAll('a[href="#sec-creditos"]').forEach(a => a.addEventListener("click", () => { const d = document.querySelector("#sec-creditos details"); if (d) d.open = true; }));

  BiomasUI.iniciar(D.passaporte);   // em qualquer página: se há carimbo novo (ou a jornada completa), a cena do overlay abre
  // menu em uma linha com rolagem horizontal nas telas estreitas: a página atual aparece à vista
  const atual = topoEl && topoEl.querySelector("a.nav[aria-current]"); if (atual) requestAnimationFrame(() => { if (topoEl.scrollWidth > topoEl.clientWidth) topoEl.scrollLeft = atual.offsetLeft - topoEl.clientWidth / 2 + atual.offsetWidth / 2; });
  if (D.id === "hub" || D.id === "jornada") {
    if (D.id === "jornada") jornada(document.getElementById("passaporte"));
    else {   // hub: o card do passaporte mostra só a folha com os carimbos, sem botões nem animação
      const slot = document.getElementById("card-folha");
      const folha = () => { const cs = BiomasUI.carimbos(), ac = {}; for (const k in cs) ac[k] = cs[k].em; slot.replaceChildren(BiomasUI.folha(D.passaporte, ac)); };
      folha(); addEventListener("biomas:carimbos", folha);
    }
    const decorar = () => document.querySelectorAll("a.card").forEach(a => { const r = regioes.find(x => x.id === a.dataset.id); if (r) marcarCartao(a, r); });
    decorar(); addEventListener("biomas:carimbos", decorar);
  } else {
    const prox = document.getElementById("proximos"); if (prox) { proximoDinamico(); proximos(prox); }   // só a página do Brasil termina com passaporte e cards
    leitura(); videos(); quiz(); comparador(); chuvas(); carrosseis(); mapaAmpliavel(); painelSecoes();
  }
})();
