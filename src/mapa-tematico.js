/* Mapas temáticos das páginas de bioma (planos, com camadas e filtros). JS puro; não tem relação com o HERO MAP.
   Carrega /assets/mapas/<id>.json quando a figura chega perto da tela e monta um SVG com poucos <path>.
   Duas "máscaras" independentes escondem elementos: .mt-oc (camada desligada) e .mt-fil (filtro). */
(() => {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const sv = (tag, at = {}, ...kids) => { const n = document.createElementNS(NS, tag); for (const k in at) n.setAttribute(k, at[k]); kids.forEach(c => n.append(c)); return n; };
  const fmt = n => n.toLocaleString("pt-BR");
  const titulo = s => s.toLowerCase().replace(/(^|\s)\S/g, m => m.toUpperCase());

  document.querySelectorAll("figure.mt[data-mapa]").forEach(fig => {
    const vp = fig.querySelector(".mt-vp"); let iniciado = false;
    const ir = () => {
      if (iniciado) return; iniciado = true;
      fetch(`/assets/mapas/${fig.dataset.mapa}.json`).then(r => { if (!r.ok) throw 0; return r.json(); }).then(d => montar(fig, vp, d))
        .catch(() => { vp.querySelector(".mt-msg").textContent = "Não foi possível carregar o mapa agora. As listas abaixo continuam disponíveis."; });
    };
    if ("IntersectionObserver" in window) { const o = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { o.disconnect(); ir(); } }, { rootMargin: "700px" }); o.observe(fig); } else ir();
  });

  function montar(fig, vp, d) {
    const info = fig.querySelector(".mt-info"), por = k => d.camadas.find(c => c.id === k);
    const svg = sv("svg", { viewBox: `0 0 ${d.w} ${d.h}`, class: "mt-svg", "aria-hidden": "true", focusable: "false" });
    const camadas = {};   // id da camada -> elementos que ligam/desligam juntos
    const itens = {};     // id da camada -> elementos que os filtros podem esconder (têm data-*)
    const pins = [];      // marcadores e rótulos em px (a escala acompanha o tamanho real do mapa)
    const sel = { el: null };
    const add = (k, ...els) => { (camadas[k] = camadas[k] || []).push(...els); };
    const item = (k, el) => { (itens[k] = itens[k] || []).push(el); return el; };
    const mostrar = (txt, el) => { info.textContent = txt; if (sel.el) sel.el.classList.remove("mt-sel"); sel.el = el; if (el) el.classList.add("mt-sel"); };
    const gpins = sv("g", { class: "mt-pins" });
    const pino = (k, x, y, ...kids) => { const g = sv("g", { class: "mt-pin", "data-x": x, "data-y": y }, ...kids); add(k, g); gpins.append(g); return g; };
    const rotulo = (txt, cls, at = {}) => sv("text", { class: `mt-rot ${cls}`, x: 0, y: 0, ...at }, txt);

    // ---- fundo: terra, países (preenchimento), grade
    svg.append(sv("rect", { width: d.w, height: d.h, class: "mt-terra" }));
    const cp = por("paises");
    if (cp) { const g = sv("g", { class: "mt-cam-paises" }); cp.itens.forEach((p, i) => g.append(sv("path", { d: p.d, class: `mt-pais mt-pais-${i % 6}` }))); svg.append(g); add("paises", g); }
    const gg = sv("g", { class: "mt-cam-grade" }); gg.append(sv("path", { d: d.grade.d, class: "mt-grade" })); svg.append(gg); add("grade", gg);
    d.grade.rotulos.forEach(r => { const p = pino("grade", r.p[0], r.p[1], rotulo(r.t, "mt-rot-grade", r.eixo === "x" ? { x: 3, y: 13 } : { x: 4, y: -4 })); pins.push({ pin: p, camada: "grade" }); });

    // ---- a região (o bioma inteiro) e a água
    if (d.limite_oficial) svg.append(sv("path", { d: d.limite_oficial, class: "mt-regiao" }));   // a parte brasileira (IBGE) também é preenchida; as duas bases não coincidem exatamente
    svg.append(sv("path", { d: d.limite, class: "mt-regiao" }));
    const cm = por("massas");
    if (cm) { const g = sv("g", { class: "mt-cam-massas" }); cm.grupos.forEach(x => g.append(item("massas", sv("path", { d: x.d, class: "mt-agua", "fill-rule": "evenodd", "data-tipo": x.tipo })))); svg.append(g); add("massas", g); }
    const cr = por("rios");
    if (cr) { const g = sv("g", { class: "mt-cam-rios" }); cr.grupos.forEach(x => g.append(item("rios", sv("path", { d: x.d, class: "mt-rio", "data-navegavel": x.navegavel, "vector-effect": "non-scaling-stroke" })))); svg.append(g); add("rios", g); }

    // ---- unidades de conservação (PI: contorno contínuo; US: tracejado)
    const cu = por("ucs");
    if (cu) {
      const g = sv("g", { class: "mt-cam-ucs" }); const ucPorEl = new Map();
      cu.itens.forEach(u => {
        const p = item("ucs", sv("path", { d: u.d, class: `mt-uc mt-uc-${u.grupo}`, "fill-rule": "evenodd", "data-grupo": u.grupo, "data-esfera": u.esfera, "vector-effect": "non-scaling-stroke" }));
        const t = `${u.nome} — ${u.categoria}, ${u.grupo === "PI" ? "proteção integral" : "uso sustentável"}, ${u.esfera.toLowerCase()} (${titulo(u.uf)}), ${fmt(u.ha)} ha${u.ano ? `, criada em ${u.ano}` : ""}.`;
        p.addEventListener("pointerenter", () => mostrar(t, p)); p.addEventListener("click", () => mostrar(t, p));
        ucPorEl.set(u.nome + "|" + u.ha, { p, t }); g.append(p);
      });
      svg.append(g); add("ucs", g); fig._ucs = ucPorEl;
    }

    // ---- divisas (estados e departamentos) e fronteiras entre países, por cima da água e das UCs
    const ce = por("estados");
    if (ce && ce.front) { const g = sv("g", { class: "mt-cam-estados" }); g.append(sv("path", { d: ce.front, class: "mt-uf", "vector-effect": "non-scaling-stroke" })); svg.append(g); add("estados", g); }
    if (cp && cp.front) { const g = sv("g", { class: "mt-cam-fronteiras" }); g.append(sv("path", { d: cp.front, class: "mt-front", "vector-effect": "non-scaling-stroke" })); svg.append(g); add("paises", g); }
    if (d.limite_oficial) svg.append(sv("path", { d: d.limite_oficial, class: "mt-oficial", "vector-effect": "non-scaling-stroke" }));
    svg.append(sv("path", { d: d.limite, class: "mt-regiao-borda", "vector-effect": "non-scaling-stroke" }));

    // ---- rótulos e marcadores (px), do mais ao menos prioritário para a colisão
    if (cr) for (const r of cr.rotulos || []) { const p = pino("rios", r.p[0], r.p[1], rotulo(r.nome, "mt-rot-rio", { "text-anchor": "middle" })); p.dataset.navegavel = r.navegavel; item("rios", p); pins.push({ pin: p, rot: p.firstChild, camada: "rios", centro: true }); }
    const ccid = por("cidades");
    if (ccid) for (const it of ccid.itens) {
      const p = pino("cidades", it.p[0], it.p[1], sv("circle", { r: 4.5, class: "mt-pt mt-pt-cid" }), rotulo(it.nome, "mt-rot-cid", { x: 8, y: 4 }));
      const t = `${it.nome} (${it.uf}) — sede municipal.`; p.addEventListener("pointerenter", () => mostrar(t, p)); p.addEventListener("click", () => mostrar(t, p));
      pins.push({ pin: p, rot: p.lastChild, camada: "cidades" });
    }
    if (ce) for (const r of ce.rotulos || []) { const p = pino("estados", r.p[0], r.p[1], rotulo(r.nome, "mt-rot-uf", { "text-anchor": "middle" })); pins.push({ pin: p, rot: p.firstChild, camada: "estados", centro: true }); }
    const cpov = por("povos");
    if (cpov) for (const it of cpov.itens) {
      const forma = it.tipo === "indigena" ? "M0-6L5.5 4.5h-11z" : "M0-6L5 0 0 6-5 0z";
      const p = pino("povos", it.p[0], it.p[1], sv("path", { d: forma, class: `mt-pt mt-pt-${it.tipo}` })); p.dataset.tipo = it.tipo; item("povos", p);
      const t = `${it.nome} (${it.uf}) — localidade ${it.tipo === "indigena" ? "indígena" : "quilombola"}, Censo 2022 (IBGE); ponto, não é o limite do território.`;
      p.addEventListener("pointerenter", () => mostrar(t, p)); p.addEventListener("click", () => mostrar(t, p)); pins.push({ pin: p, camada: "povos" });
    }
    if (cp) cp.itens.forEach(p => { if (!p.p) return; const g = pino("paises", p.p[0], p.p[1], rotulo(p.nome, "mt-rot-pais", { "text-anchor": "middle" })); pins.push({ pin: g, camada: "paises" }); });

    // ---- escala e norte (sempre visíveis)
    const kmAlvo = (d.w / d.upk) * .16, kms = [10, 20, 50, 100, 200, 500], km = kms.reduce((a, b) => Math.abs(b - kmAlvo) < Math.abs(a - kmAlvo) ? b : a);
    const barra = sv("line", { x1: 0, y1: 0, x2: 60, y2: 0, class: "mt-escala" });
    const esc = sv("g", { class: "mt-pin", "data-x": 70, "data-y": d.h - 70 }, barra, rotulo(`${km} km`, "mt-rot-esc", { x: 0, y: -8 })); gpins.append(esc); pins.push({ pin: esc, barra, km, escala: true });
    const nor = sv("g", { class: "mt-pin", "data-x": d.w - 80, "data-y": 90 }, sv("path", { d: "M0-18L8 10 0 4-8 10z", class: "mt-norte" }), rotulo("N", "mt-rot-esc", { x: 0, y: 28, "text-anchor": "middle" })); gpins.append(nor); pins.push({ pin: nor });
    svg.append(gpins);
    vp.replaceChildren(svg);

    // ---- legenda
    const leg = fig.querySelector(".mt-leg");
    const li = (ic, txt) => { const s = document.createElement("span"); s.className = "mt-li"; s.append(ic, txt); return s; };
    const mini = (...f) => sv("svg", { viewBox: "0 0 20 14", width: 22, height: 15, "aria-hidden": "true" }, ...f);
    const ret = c => sv("rect", { x: 1, y: 1, width: 18, height: 12, class: c });
    const L = [li(mini(ret("mt-regiao mt-leg-reg")), d.limite_nome)];
    if (d.limite_oficial) L.push(li(mini(sv("path", { d: "M1 7h18", class: "mt-oficial" })), d.limite_oficial_nome || "limite oficial"));
    L.push(li(mini(ret("mt-agua")), "água permanente"), li(mini(sv("path", { d: "M1 11C7 11 8 3 19 3", class: "mt-rio", fill: "none" })), "rio ou córrego"),
      li(mini(ret("mt-uc mt-uc-PI")), "proteção integral (contorno contínuo)"), li(mini(ret("mt-uc mt-uc-US")), "uso sustentável (tracejado)"),
      li(mini(sv("circle", { cx: 10, cy: 7, r: 4.5, class: "mt-pt mt-pt-cid" })), "sede municipal"),
      li(mini(sv("path", { d: "M10 1L15.5 11.5h-11z", class: "mt-pt mt-pt-indigena" })), "localidade indígena"),
      li(mini(sv("path", { d: "M10 1L15 7 10 13 5 7z", class: "mt-pt mt-pt-quilombola" })), "localidade quilombola"),
      li(mini(sv("path", { d: "M1 7h18", class: "mt-front" })), "fronteira entre países"), li(mini(sv("path", { d: "M1 7h18", class: "mt-uf" })), "divisa de estados"));
    leg.replaceChildren(...L); leg.removeAttribute("aria-hidden");

    // ---- camadas (checkbox) e filtros (radios); cada um usa a sua própria máscara
    const liga = (k, on) => (camadas[k] || []).forEach(e => e.classList.toggle("mt-oc", !on));
    fig.querySelectorAll("input[data-camada]").forEach(cb => { liga(cb.dataset.camada, cb.checked); cb.addEventListener("change", () => { liga(cb.dataset.camada, cb.checked); organizar(); }); });
    const filtros = [...fig.querySelectorAll("fieldset[data-filtro]")];
    const valor = f => (f.querySelector("input:checked") || {}).value || "";
    const passa = (el, fs) => fs.every(f => !valor(f) || (el.dataset[f.dataset.campo] || "") === valor(f));
    function filtrar() {
      for (const k in itens) { const fs = filtros.filter(f => f.dataset.camada === k); itens[k].forEach(el => el.classList.toggle("mt-fil", !passa(el, fs))); }
      fig.querySelectorAll(".mt-tab[data-camada]").forEach(tb => { const fs = filtros.filter(f => f.dataset.camada === tb.dataset.camada); tb.querySelectorAll("tbody tr").forEach(tr => { tr.hidden = !passa(tr, fs); }); });
      organizar();
    }
    filtros.forEach(f => f.addEventListener("change", filtrar));

    // lista de UCs: o nome vira botão que destaca a unidade no mapa
    fig.querySelectorAll('.mt-tab[data-camada="ucs"] tbody tr').forEach(tr => {
      const th = tr.querySelector("th"), nome = th.textContent, ha = Number(tr.children[5].textContent.replace(/\./g, ""));
      const b = document.createElement("button"); b.type = "button"; b.className = "mt-lnk"; b.textContent = nome; th.replaceChildren(b);
      b.addEventListener("click", () => {
        const u = fig._ucs && fig._ucs.get(nome + "|" + ha); if (!u) return;
        const cb = fig.querySelector('input[data-camada="ucs"]'); if (cb && !cb.checked) { cb.checked = true; cb.dispatchEvent(new Event("change")); }
        mostrar(u.t, u.p); vp.scrollIntoView({ block: "nearest", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
      });
    });

    // ---- escala dos marcadores e rótulos em px, e rótulos sem sobreposição (os primeiros da lista têm prioridade)
    const oculto = el => el.classList.contains("mt-oc") || el.classList.contains("mt-fil");
    function organizar() {
      const r = svg.getBoundingClientRect(); if (!r.width) return;
      const u = 1 / Math.min(r.width / d.w, r.height / d.h);
      const caixas = [], cabe = (x, y, w, h) => !caixas.some(b => x < b[0] + b[2] && x + w > b[0] && y < b[1] + b[3] && y + h > b[1]);
      pins.forEach(p => {
        const x = +p.pin.dataset.x, y = +p.pin.dataset.y;
        p.pin.setAttribute("transform", `translate(${x} ${y}) scale(${u})`);
        if (p.escala) p.barra.setAttribute("x2", (p.km * d.upk) / u);
        if (!p.rot) return;
        if (oculto(p.pin)) { p.rot.style.display = "none"; return; }
        p.rot.style.display = "";
        const px = x / u, py = y / u, w = p.rot.textContent.length * 6.4 + 4;
        const tent = p.centro ? [[px - w / 2, py - 8]] : [[px + 7, py - 8], [px - 7 - w, py - 8], [px - w / 2, py + 8]];
        const ok = tent.find(t => cabe(t[0], t[1], w, 14));
        if (!ok) { p.rot.style.display = "none"; return; }
        caixas.push([ok[0], ok[1], w, 14]);
        if (!p.centro) { p.rot.setAttribute("x", ok[0] - px + 2); p.rot.setAttribute("text-anchor", "start"); p.rot.setAttribute("y", ok[1] - py + 11); }
      });
    }
    "ResizeObserver" in window ? new ResizeObserver(organizar).observe(svg) : addEventListener("resize", organizar);
    filtrar();
    info.textContent = "Toque ou passe o mouse sobre uma unidade de conservação, sede ou localidade para ver os detalhes.";
  }
})();
