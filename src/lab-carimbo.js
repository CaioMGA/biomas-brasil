/* Lab dos carimbos: ajusta o timing das animações de carimbo e a intensidade e duração do tremor do passaporte.
   Só existe no build de desenvolvimento (/lab-carimbo/). "Aplicar neste navegador" grava em localStorage "biomas:anim", e as cenas reais passam a usar esses valores. */
(() => {
  const P = JSON.parse(document.getElementById("lab-dados").textContent), U = BiomasUI;
  const $ = id => document.getElementById(id);
  const clone = o => JSON.parse(JSON.stringify(o));
  let A = clone(U.animAtual());

  const GRUPOS = [
    { t: "Queda do carimbo", c: [
      { k: "queda", l: "Duração da queda", min: 0, max: 1500, step: 10, u: "ms" },
      { k: "escalaQueda", l: "Tamanho com que começa a cair", min: 1, max: 3, step: .05, u: "×" },
      { k: "impacto", l: "Atraso até o passaporte tremer", min: 0, max: 1500, step: 10, u: "ms", n: "Do carimbo começar a cair até o tremor. Igualar à duração da queda faz o tremor coincidir com o pouso." }] },
    { t: "Tremor leve (carimbos de bioma)", c: [
      { k: "leve.amp", l: "Intensidade (deslocamento)", min: 0, max: 40, step: .5, u: "px" },
      { k: "leve.rot", l: "Giro", min: 0, max: 6, step: .05, u: "°" },
      { k: "leve.dur", l: "Duração", min: 0, max: 2000, step: 10, u: "ms" }] },
    { t: "Tremor forte (jornada completa)", c: [
      { k: "forte.amp", l: "Intensidade (deslocamento)", min: 0, max: 60, step: .5, u: "px" },
      { k: "forte.rot", l: "Giro", min: 0, max: 10, step: .05, u: "°" },
      { k: "forte.dur", l: "Duração", min: 0, max: 3000, step: 10, u: "ms" },
      { k: "clarao", l: "Duração do clarão vermelho", min: 0, max: 3000, step: 10, u: "ms" }] },
    { t: "Cena de biomas", c: [
      { k: "suspense", l: "Suspense antes do 1º carimbo", min: 0, max: 5000, step: 50, u: "ms" },
      { k: "intervalo", l: "Entre um carimbo e o próximo", min: 100, max: 3000, step: 50, u: "ms" },
      { k: "pausaMsg", l: "Do último carimbo até a mensagem", min: 0, max: 2000, step: 50, u: "ms" }] },
    { t: "Cena da jornada completa", c: [
      { k: "pausaInicioFinal", l: "Papel em branco antes do 1º carimbo", min: 0, max: 4000, step: 50, u: "ms" },
      { k: "intervaloFinal", l: "Entre os carimbos de bioma", min: 100, max: 3000, step: 50, u: "ms" },
      { k: "suspenseVermelho", l: "Suspense até o carimbo vermelho", min: 0, max: 5000, step: 50, u: "ms" },
      { k: "pausaMsgFinal", l: "Do vermelho até a mensagem", min: 0, max: 4000, step: 50, u: "ms" }] }
  ];
  const get = k => k.split(".").reduce((o, p) => o[p], A);
  const set = (k, v) => { const p = k.split("."), ult = p.pop(); p.reduce((o, q) => o[q], A)[ult] = v; };

  // ---- controles ----
  const lista = $("ctl"), campos = {};
  GRUPOS.forEach(g => {
    const sec = document.createElement("section"); sec.className = "lc-grupo"; const h = document.createElement("h2"); h.textContent = g.t; sec.appendChild(h);
    g.c.forEach(f => {
      const w = document.createElement("div"); w.className = "lc-campo";
      w.innerHTML = `<label for="r-${f.k}">${f.l}</label><div class="lc-linha"><input type="range" id="r-${f.k}" min="${f.min}" max="${f.max}" step="${f.step}"><input type="number" id="n-${f.k}" min="${f.min}" max="${f.max}" step="${f.step}"><span>${f.u}</span></div>${f.n ? `<p>${f.n}</p>` : ""}`;
      sec.appendChild(w); campos[f.k] = { r: w.querySelector("input[type=range]"), n: w.querySelector("input[type=number]"), f };
      const mudou = v => { v = Math.min(f.max, Math.max(f.min, +v)); if (Number.isNaN(v)) return; set(f.k, v); campos[f.k].r.value = campos[f.k].n.value = v; saida(); auto(f.k); };
      campos[f.k].r.addEventListener("input", e => mudou(e.target.value)); campos[f.k].n.addEventListener("change", e => mudou(e.target.value));
    });
    lista.appendChild(sec);
  });
  function atualizar() { for (const k in campos) campos[k].r.value = campos[k].n.value = get(k); saida(); }
  function saida() { $("saida").value = JSON.stringify(A, null, 2); }

  // ---- folha de teste: cada clique bate um carimbo ----
  const fol = U.folha(P, {}), papel = document.createElement("div"); papel.className = "cena-papel"; papel.appendChild(fol); $("prev").appendChild(papel);
  const ids = P.regs.map(r => r.id), datas = ["2026-10-12", "2026-10-13", "2026-10-15", "2026-10-20", "2026-10-21", "2026-10-30", "2026-10-31", "2026-10-31"];
  let c = {}, prox = 0;
  const todosBiomas = () => { const o = {}; P.regs.forEach((r, i) => { o[r.id] = datas[i]; }); return o; };
  function bater(forte) {
    if (forte) { if (c.completa == null) c = todosBiomas(); c.completa = "2026-10-31"; U.demo(papel, fol, P, c, "completa", true, A); prox = 0; return; }
    delete c.completa;
    const livres = ids.filter(i => c[i] == null); if (!livres.length) { c = {}; return bater(false); }
    const id = livres[0]; c[id] = datas[ids.indexOf(id)]; U.demo(papel, fol, P, c, id, false, A);
  }
  let t = 0; function auto(k) { if (!$("auto").checked) return; clearTimeout(t); t = setTimeout(() => { c = {}; bater(/^(forte|clarao)/.test(k)); }, 350); }

  $("leve").addEventListener("click", () => bater(false));
  $("forte").addEventListener("click", () => bater(true));
  $("limpar").addEventListener("click", () => { c = {}; fol.innerHTML = U.folha(P, {}).innerHTML; });
  $("cenaBio").addEventListener("click", () => U.simular(P, "bioma", clone(A)));
  $("cenaFim").addEventListener("click", () => U.simular(P, "completa", clone(A)));
  $("padrao").addEventListener("click", () => { A = clone(U.ANIM_PADRAO); try { localStorage.removeItem("biomas:anim"); } catch (e) {} atualizar(); msg("Valores padrão restaurados e ajuste removido deste navegador."); });
  $("aplicar").addEventListener("click", () => { try { localStorage.setItem("biomas:anim", JSON.stringify(A)); msg("Aplicado neste navegador: as cenas reais do site passam a usar esses valores."); } catch (e) { msg("Não foi possível gravar no navegador."); } });
  $("copiar").addEventListener("click", async () => { try { await navigator.clipboard.writeText($("saida").value); msg("Valores copiados."); } catch (e) { $("saida").select(); msg("Selecione e copie o texto abaixo (Ctrl+C)."); } });
  const msg = t => { $("msg").textContent = t; };
  atualizar();
})();
