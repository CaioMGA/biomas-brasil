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

  function carimbo(reg, idx, pos, r, em) {
    const id = reg.id, cor = id === "brasil" ? "#1b2f8a" : `var(--c-${id})`, nome = reg.nome.toUpperCase(), data = fmtData(em);
    const rot = ((rnd(id, 1) - .5) * 34).toFixed(1), dx = ((rnd(id, 2) - .5) * 10).toFixed(1), dy = ((rnd(id, 3) - .5) * 10).toFixed(1), sc = (.95 + rnd(id, 4) * .1).toFixed(3);
    const seed = 1 + hash(id) % 90, forma = id === "brasil" ? "brasil" : FORMAS[idx % FORMAS.length];
    const TX = `fill="${cor}" stroke="none"`;
    const txt = (t, y, fs, extra = "") => `<text x="0" y="${y}" text-anchor="middle" font-size="${fs.toFixed(1)}" ${extra}>${t}</text>`;
    const dupla = (draw) => draw(1, 2.6) + draw(0, 1);   // contorno grosso + fio interno
    let g = "";
    if (forma === "circulo" || forma === "circulo2" || forma === "brasil") {
      const R = forma === "brasil" ? r * 1.12 : r, a = R - 12.5, b = R - 8.5;
      g += `<circle r="${R}" stroke-width="${forma === "brasil" ? 3.2 : 2.6}"/><circle r="${R - 5}" stroke-width="1" ${forma === "circulo2" ? 'stroke-dasharray="1.3 2.6"' : ""}/>`;
      g += `<path id="at-${id}" d="M ${-a},0 A ${a} ${a} 0 0 1 ${a},0" fill="none" stroke="none"/><path id="ab-${id}" d="M ${-b},0 A ${b} ${b} 0 0 0 ${b},0" fill="none" stroke="none"/>`;
      g += `<text font-size="7.2" font-weight="700" letter-spacing="1.5" ${TX}><textPath href="#at-${id}" startOffset="50%" text-anchor="middle">BIOMAS DO BRASIL</textPath></text>`;
      g += `<text font-size="6.8" font-weight="700" letter-spacing="1.8" ${TX}><textPath href="#ab-${id}" startOffset="50%" text-anchor="middle">★ CARIMBADO ★</textPath></text>`;
      g += `<line x1="${-(R - 9)}" x2="${R - 9}" y1="-9" y2="-9" stroke-width="1"/><line x1="${-(R - 9)}" x2="${R - 9}" y1="9" y2="9" stroke-width="1"/>`;
      g += txt(nome, 4.5, fit(nome, 2 * R - 20, 13), `font-weight="800" ${TX}`);
      if (data) g += txt(data, 18.5, 7.6, `font-weight="700" letter-spacing=".6" ${TX}`);
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
    const defs = `<filter id="tt-${id}" x="-15%" y="-15%" width="130%" height="130%"><feTurbulence type="fractalNoise" baseFrequency="0.38" numOctaves="3" seed="${seed}" result="n"/><feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  2.6 0 0 0 -0.42" result="m"/><feComposite in="SourceGraphic" in2="m" operator="in" result="g"/><feTurbulence type="turbulence" baseFrequency="0.035" numOctaves="2" seed="${seed + 5}" result="w"/><feDisplacementMap in="g" in2="w" scale="2.6" xChannelSelector="R" yChannelSelector="G"/></filter>`;
    return { defs, g: `<g style="mix-blend-mode:multiply" filter="url(#tt-${id})" opacity=".9"><g transform="translate(${(pos[0] + +dx).toFixed(1)} ${(pos[1] + +dy).toFixed(1)}) rotate(${rot}) scale(${sc})" fill="none" stroke="${cor}" stroke-linecap="round" stroke-linejoin="round" style="color:${cor}" font-family="'Instrument Sans',system-ui,sans-serif">${g}</g></g>` };
  }

  /* P = {vb, d, r, regs: [{id, nome, pos}]}; carimbados = {id: "AAAA-MM-DD" | ""} (só os biomas que passaram no quiz) */
  function folha(P, carimbados) {
    const [vx, vy, vw, vh] = P.vb;
    let defs = `<filter id="falha" x="-2%" y="-2%" width="104%" height="104%"><feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="2" seed="11" result="n"/><feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  4 0 0 0 -1.15" result="m"/><feComposite in="SourceGraphic" in2="m" operator="in" result="g"/><feTurbulence type="turbulence" baseFrequency="0.06" numOctaves="1" seed="4" result="w"/><feDisplacementMap in="g" in2="w" scale="1.6" xChannelSelector="R" yChannelSelector="G"/></filter>`;
    let marks = "";
    P.regs.forEach((rg, i) => { if (carimbados[rg.id] == null) return; const c = carimbo(rg, i, rg.pos, P.r, carimbados[rg.id]); defs += c.defs; marks += c.g; });
    const svg = `<svg viewBox="${vx} ${vy} ${vw} ${vh}" role="img" aria-label="Folha do passaporte: contorno do Brasil e os carimbos dos biomas já completados" style="isolation:isolate"><defs>${defs}</defs>
<rect x="${vx}" y="${vy}" width="${vw}" height="${vh}" fill="#f6f1e4"/>
<path d="${P.d}" fill="none" stroke="#161616" stroke-width=".85" stroke-linejoin="round" stroke-dasharray="13 1.6 7 2.4 19 1.2 5 2 10 1.4 25 2.8 8 1.8" filter="url(#falha)"/>${marks}</svg>`;
    return wrap("folha", svg);
  }

  return { graficoChuva, folha };
})();
