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
