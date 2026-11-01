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
  const hasSeal = id => { const q = getProg(id).quiz; return !!q && q.ok / q.n >= .6; };
  const fmt = n => n.toLocaleString("pt-BR");
  const regioes = D ? D.regioes : [];
  const lida = r => getProg(r.id).lidas.length >= r.secoes;

  const passou = id => { const q = getProg(id).quiz; return !!q && q.ok / q.n >= .6; };
  function estado(r) {
    const pr = getProg(r.id);
    if (hasSeal(r.id)) return "Carimbado";
    if (lida(r)) return "Lido";
    return pr.lidas.length ? `${pr.lidas.length} de ${r.secoes} seções` : "";
  }
  function cartao(r) {
    const li = el("li"); const a = el("a", { class: "card" + (lida(r) ? " lido" : ""), href: r.url, style: `--col:${r.cor}` });
    a.append(el("h3", {}, r.nome), el("p", {}, r.intro));
    const meta = el("span", { class: "meta" }); const est = estado(r); if (est) meta.appendChild(el("span", { class: "selo", style: "margin-left:0" }, est));
    a.appendChild(meta); li.appendChild(a); return li;
  }

  // ---- passaporte: folha com um carimbo por bioma completado (quiz com nota mínima) ----
  function carimbados() { const o = {}; regioes.forEach(r => { if (passou(r.id)) o[r.id] = getProg(r.id).quiz.em || ""; }); return o; }
  function passaporte(box) {
    const reg = regioes.filter(r => r.id !== "brasil"); const c = carimbados(); const n = reg.filter(r => r.id in c).length;
    box.appendChild(el("p", { class: "kicker" }, "Passaporte"));
    box.appendChild(el("p", { class: "lead" }, `${n} de ${reg.length} biomas carimbados. Acerte o quiz de um bioma para carimbá-lo na folha.`));
    box.appendChild(BiomasUI.folha(D.passaporte, c));
  }

  // ---- sugestões no rodapé: não lidos primeiro ----
  function proximos(box) {
    const outros = regioes.filter(r => r.id !== D.id);
    const ordem = [...outros.filter(r => !lida(r)), ...outros.filter(lida)];
    box.appendChild(el("h2", {}, ordem.some(r => !lida(r)) ? "Continue explorando" : "Você leu tudo. Releia o que quiser"));
    const pb = el("div", { class: "pass-bloco" }); passaporte(pb); box.appendChild(pb);
    const ul = el("ul", { class: "cards" });
    ordem.forEach(r => ul.appendChild(cartao(r)));
    box.appendChild(ul);
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
            const sel = ok / D.quiz.length >= .6;
            res.hidden = false;
            res.replaceChildren(document.createTextNode(`Você acertou ${ok} de ${D.quiz.length}. ${sel ? (id === "brasil" ? "Carimbo do Brasil conquistado!" : "Carimbo conquistado!") : "Releia as seções e tente de novo para ganhar o carimbo."}`));
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
    document.querySelectorAll("a.card").forEach(a => {
      const r = regioes.find(x => x.id === a.dataset.id); if (!r) return;
      if (lida(r)) a.classList.add("lido");
      const est = estado(r); if (est) a.querySelector(".estado").replaceChildren(el("span", { class: "selo", style: "margin-left:0" }, est));
    });
  } else {
    leitura(); videos(); quiz(); comparador(); chuvas();
    proximos(document.getElementById("proximos"));
  }
})();
