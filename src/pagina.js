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
  const MES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  const dataCarimbo = r => { const c = BiomasUI.carimbos()[r.id], m = /^(\d{4})-(\d\d)-(\d\d)/.exec((c && c.em) || ""); return m ? `${+m[3]} ${MES[+m[2] - 1]} ${m[1]}` : ""; };
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
    if (ok) { const d = dataCarimbo(r); meta.appendChild(el("span", { class: "data-carimbo" }, d ? `Carimbado em ${d}` : "Carimbado")); }
    else meta.appendChild(el("span", { class: "dica-quiz" }, r.id === "brasil" ? "Faça o Quiz final para carimbar \u2192" : "Faça o quiz para carimbar \u2192"));
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
  function jornada(box) {
    const intro = document.getElementById("jornada-intro"), v = verCarimbos();
    const texto = () => { if (intro) intro.textContent = BiomasUI.carimbos().completa ? "Parabéns! Seu passaporte está completo. Revisite qualquer bioma quando quiser." : "Aqui ficam os carimbos que você reuniu. Vença o quiz de cada bioma, e o Quiz final do Brasil, para completar seu passaporte. Você consegue?"; };
    passaporte(box, { capa: true, kicker: false, extra: [v.b], depois: [v.msg], proximo: () => { const r = proximoSemCarimbo(); return r && { nome: r.id === "brasil" ? "Brasil (Quiz final)" : r.nome, href: r.url }; } });
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
