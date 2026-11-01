/* Mapas temáticos das páginas de bioma (planos, com camadas e filtros). JS puro; não tem relação com o HERO MAP.
   Carrega /assets/mapas/<id>.json quando a figura chega perto da tela e monta um SVG com poucos <path>. */
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
        .catch(() => { vp.querySelector(".mt-msg").textContent = "Não foi possível carregar o mapa agora. A lista de unidades de conservação abaixo continua disponível."; });
    };
    if ("IntersectionObserver" in window) { const o = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { o.disconnect(); ir(); } }, { rootMargin: "700px" }); o.observe(fig); } else ir();
  });

  function montar(fig, vp, d) {
    const id = fig.dataset.mapa, info = fig.querySelector(".mt-info");
    const svg = sv("svg", { viewBox: `0 0 ${d.w} ${d.h}`, class: "mt-svg", "aria-hidden": "true", focusable: "false" });
    const clip = `mt-clip-${id}`;
    svg.append(sv("defs", {},
      sv("clipPath", { id: clip }, sv("path", { d: d.limite })),
      sv("pattern", { id: `mt-hach-${id}`, width: 8, height: 8, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" }, sv("rect", { width: 8, height: 8, class: "mt-hach-bg" }), sv("line", { x1: 0, y1: 0, x2: 0, y2: 8, class: "mt-hach-ln" }))));
    svg.append(sv("path", { d: d.limite, class: "mt-limite-fundo" }));

    const grupo = {};    // id da camada -> <g>
    const pins = [];     // marcadores e rótulos, com escala em px (acompanha o tamanho real do mapa)
    const sel = { el: null };
    const ucPorEl = new Map();

    const camada = (c, filho) => { const g = sv("g", { class: `mt-cam mt-cam-${c.id}`, "data-camada": c.id }); if (filho) g.append(...filho); if (!c.ligada) g.style.display = "none"; return g; };
    const recortada = g => { g.setAttribute("clip-path", `url(#${clip})`); return g; };
    const mostrar = (txt, el) => { info.textContent = txt; if (sel.el) sel.el.classList.remove("mt-sel"); sel.el = el; if (el) el.classList.add("mt-sel"); };

    for (const c of d.camadas) {
      if (c.id === "massas") {
        grupo[c.id] = recortada(camada(c, c.grupos.map(g => sv("path", { d: g.d, class: "mt-agua", "fill-rule": "evenodd", "data-tipo": g.tipo }))));
      } else if (c.id === "rios") {
        const g = camada(c, c.grupos.map(x => sv("path", { d: x.d, class: "mt-rio", "data-navegavel": x.navegavel, "vector-effect": "non-scaling-stroke" })));
        grupo[c.id] = recortada(g);
      } else if (c.tipo === "poligono") {
        grupo[c.id] = recortada(camada(c, c.itens.map(u => {
          const p = sv("path", { d: u.d, class: `mt-uc mt-uc-${u.grupo}`, "fill-rule": "evenodd", "data-grupo": u.grupo, "data-esfera": u.esfera, "vector-effect": "non-scaling-stroke" });
          if (u.grupo === "PI") p.style.fill = `url(#mt-hach-${id})`;
          const t = `${u.nome} — ${u.categoria}, ${u.grupo === "PI" ? "proteção integral" : "uso sustentável"}, ${u.esfera.toLowerCase()} (${titulo(u.uf)}), ${fmt(u.ha)} ha${u.ano ? `, criada em ${u.ano}` : ""}.`;
          p.addEventListener("pointerenter", () => mostrar(t, p)); p.addEventListener("click", () => mostrar(t, p));
          ucPorEl.set(u.nome + "|" + u.ha, { p, t });
          return p;
        })));
      } else {   // pontos: marcadores em px, com forma própria (círculo = sede; triângulo = indígena; losango = quilombola)
        const g = camada(c);
        for (const it of c.itens) {
          const forma = c.id === "cidades" ? "circle" : it.tipo === "indigena" ? "tri" : "losango";
          const m = forma === "circle" ? sv("circle", { r: 4.5, class: "mt-pt mt-pt-cid" }) : sv("path", { d: forma === "tri" ? "M0-6L5.5 4.5h-11z" : "M0-6L5 0 0 6-5 0z", class: `mt-pt mt-pt-${it.tipo}` });
          m.setAttribute("data-tipo", it.tipo || ""); m.setAttribute("data-campo", c.id);
          const rot = c.id === "cidades" ? sv("text", { class: "mt-rot mt-rot-cid", x: 8, y: 4 }, it.nome) : null;
          const pin = sv("g", { class: "mt-pin", "data-x": it.p[0], "data-y": it.p[1], "data-tipo": it.tipo || "" }, m); if (rot) pin.append(rot);
          const t = c.id === "cidades" ? `${it.nome} (${it.uf}) — sede municipal.` : `${it.nome} (${it.uf}) — localidade ${it.tipo === "indigena" ? "indígena" : "quilombola"}, Censo 2022 (IBGE); ponto, não é o limite do território.`;
          pin.addEventListener("pointerenter", () => mostrar(t, pin)); pin.addEventListener("click", () => mostrar(t, pin));
          pins.push({ pin, rot, camada: c.id });
          g.append(pin);
        }
        grupo[c.id] = g;
      }
    }
    // ordem de desenho: água, rios, UCs, depois pontos e rótulos de rios por cima
    ["massas", "rios", "ucs"].forEach(k => grupo[k] && svg.append(grupo[k]));
    const rotRios = d.camadas.find(c => c.id === "rios");
    const gr = sv("g", { class: "mt-cam mt-cam-rotrios" });
    if (rotRios) for (const r of rotRios.rotulos || []) { const p = sv("g", { class: "mt-pin", "data-x": r.p[0], "data-y": r.p[1] }, sv("text", { class: "mt-rot mt-rot-rio", x: 0, y: 0, "text-anchor": "middle" }, r.nome)); pins.push({ pin: p, rot: p.firstChild, camada: "rios", rio: true }); gr.append(p); }
    svg.append(gr, ...["cidades", "povos"].map(k => grupo[k]).filter(Boolean));
    svg.append(sv("path", { d: d.limite, class: "mt-limite" }));
    vp.replaceChildren(svg);

    // legenda (visual; a informação em texto está no painel e na lista)
    const leg = fig.querySelector(".mt-leg");
    const item = (icone, txt) => { const s = document.createElement("span"); s.className = "mt-li"; s.append(icone, txt); return s; };
    const mini = (...f) => sv("svg", { viewBox: "0 0 20 14", width: 22, height: 15, "aria-hidden": "true" }, ...f);
    leg.replaceChildren(
      item(mini(sv("rect", { x: 1, y: 1, width: 18, height: 12, class: "mt-agua" })), "água permanente"),
      item(mini(sv("path", { d: "M1 11C7 11 8 3 19 3", class: "mt-rio", fill: "none" })), "rio ou córrego"),
      item(mini(sv("rect", { x: 1, y: 1, width: 18, height: 12, class: "mt-uc mt-uc-PI", style: `fill:url(#mt-hach-${id})` })), "proteção integral"),
      item(mini(sv("rect", { x: 1, y: 1, width: 18, height: 12, class: "mt-uc mt-uc-US" })), "uso sustentável"),
      item(mini(sv("circle", { cx: 10, cy: 7, r: 4.5, class: "mt-pt-cid" })), "sede municipal"),
      item(mini(sv("path", { d: "M10 1L15.5 11.5h-11z", class: "mt-pt-indigena" })), "localidade indígena"),
      item(mini(sv("path", { d: "M10 1L15 7 10 13 5 7z", class: "mt-pt-quilombola" })), "localidade quilombola"));
    leg.removeAttribute("aria-hidden");

    // camadas
    fig.querySelectorAll("input[data-camada]").forEach(cb => cb.addEventListener("change", () => {
      const k = cb.dataset.camada, on = cb.checked;
      if (grupo[k]) grupo[k].style.display = on ? "" : "none";
      if (k === "rios") gr.style.display = on ? "" : "none";
      organizar();
    }));
    // filtros: cada elemento comparado com TODOS os filtros da sua camada
    const filtros = [...fig.querySelectorAll("fieldset[data-filtro]")];
    const valor = f => (f.querySelector("input:checked") || {}).value || "";
    function filtrar() {
      for (const k in grupo) {
        const fs = filtros.filter(f => f.dataset.camada === k);
        grupo[k].querySelectorAll(":scope > *").forEach(n => {
          const ok = fs.every(f => !valor(f) || (n.dataset[f.dataset.campo] || "") === valor(f));
          n.style.display = ok ? "" : "none";
        });
      }
      const fu = filtros.filter(f => f.dataset.camada === "ucs");
      fig.querySelectorAll(".mt-tab tbody tr").forEach(tr => { tr.hidden = !fu.every(f => !valor(f) || tr.dataset[f.dataset.campo] === valor(f)); });
      organizar();
    }
    filtros.forEach(f => f.addEventListener("change", filtrar));

    // tabela de UCs: o nome vira botão que destaca a unidade no mapa
    fig.querySelectorAll(".mt-tab tbody tr").forEach(tr => {
      const th = tr.querySelector("th"), nome = th.textContent, ha = Number(tr.children[5].textContent.replace(/\./g, ""));
      const b = document.createElement("button"); b.type = "button"; b.className = "mt-lnk"; b.textContent = nome; th.replaceChildren(b);
      b.addEventListener("click", () => {
        const u = ucPorEl.get(nome + "|" + ha); if (!u) return;
        const cb = fig.querySelector('input[data-camada="ucs"]'); if (cb && !cb.checked) { cb.checked = true; cb.dispatchEvent(new Event("change")); }
        mostrar(u.t, u.p); vp.scrollIntoView({ block: "nearest", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
      });
    });

    // escala dos marcadores e rótulos em px, e rótulos sem sobreposição (maiores primeiro)
    function organizar() {
      const r = svg.getBoundingClientRect(); if (!r.width) return;
      const esc = Math.min(r.width / d.w, r.height / d.h), u = 1 / esc;
      svg.style.setProperty("--u", u);
      const caixas = [];
      const cabe = (x, y, w, h) => !caixas.some(b => x < b[0] + b[2] && x + w > b[0] && y < b[1] + b[3] && y + h > b[1]);
      pins.forEach(p => {
        const x = +p.pin.dataset.x, y = +p.pin.dataset.y;
        p.pin.setAttribute("transform", `translate(${x} ${y}) scale(${u})`);
        if (!p.rot) return;
        p.rot.style.display = "";
        const vis = p.pin.style.display !== "none" && (p.pin.parentNode.style.display !== "none");
        if (!vis) { p.rot.style.display = "none"; return; }
        const px = x / u, py = y / u, w = p.rot.textContent.length * 6.4 + 4;
        const tent = p.rio ? [[px - w / 2, py - 8]] : [[px + 7, py - 8], [px - 7 - w, py - 8], [px - w / 2, py + 8]];
        const ok = tent.find(t => cabe(t[0], t[1], w, 14));
        if (!ok) { p.rot.style.display = "none"; return; }
        caixas.push([ok[0], ok[1], w, 14]);
        if (!p.rio) { p.rot.setAttribute("x", ok[0] - px + 2); p.rot.setAttribute("text-anchor", "start"); p.rot.setAttribute("y", ok[1] - py + 11); }
      });
    }
    "ResizeObserver" in window ? new ResizeObserver(organizar).observe(svg) : addEventListener("resize", organizar);
    filtrar(); organizar();
    info.textContent = "Toque ou passe o mouse sobre uma unidade de conservação, sede ou localidade para ver os detalhes.";
  }
})();
