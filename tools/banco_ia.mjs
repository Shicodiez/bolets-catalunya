// Banco de pruebas de la lectura de rasgos de fotos con IA (Cloudflare Workers AI, por la API REST).
//
// Qué mide: coge fotos de la propia guía (de las que SABEMOS qué seta son), se las da a cada combinación de modelo + prompt,
// y mira (1) si los rasgos que lee encajan con lo que dice la ficha de esa seta y (2) lo más importante: si, pasando esos
// rasgos por la comparación REAL de la guía (tools/puntuar.js, con los umbrales de producción), la ficha correcta sale
// entre las 5 primeras. No cambia nada de producción: solo escribe tools/banco/*.
//
// Uso (lo lanza el workflow «Probar lectura de fotos con IA»; las claves vienen de los secretos del repositorio):
//   CF_ACCOUNT_ID=… CF_API_TOKEN=… node tools/banco_ia.mjs [--fotos 30] [--presupuesto 6000] [--configs a,b] [--dir-fotos web/fotos]
//   node tools/banco_ia.mjs --solo-informe        (rehace el informe con lo ya medido, sin gastar nada)
//   node tools/banco_ia.mjs --simular             (sin red: respuestas inventadas, para probar que todo el circuito funciona)
//
// Es REANUDABLE: cada medida se guarda en tools/banco/resultados.jsonl y no se repite. Cloudflare da 10.000 «neuronas»
// gratis al día (se reinician a las 00:00 UTC); el banco se para al llegar al presupuesto indicado o cuando Cloudflare
// diga que se ha acabado el cupo, y se puede volver a lanzar otro día para completar.
//
// Los prompts y el lector de respuestas del prompt «v2» son LOS MISMOS que usa el Worker (se extraen de worker/index.js);
// el «v1» es una copia congelada de lo que hacía la guía antes (castellano, un hueco por llamada) para tener con qué comparar.

import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const RAIZ = path.resolve(AQUI, "..");
const DIR_BANCO = path.join(AQUI, "banco");
const F_RES = path.join(DIR_BANCO, "resultados.jsonl");
const F_FORMATO = path.join(DIR_BANCO, "formato.json");
const F_SONDEO = path.join(DIR_BANCO, "sondeo.json");
const F_INFORME = path.join(DIR_BANCO, "INFORME.md");
const F_RESUMEN = path.join(DIR_BANCO, "resumen.json");

// ------------------------------------------------------------------ argumentos
const args = process.argv.slice(2);
const flag = (n) => args.includes("--" + n);
const valor = (n, def) => { const i = args.indexOf("--" + n); return i >= 0 && args[i + 1] !== undefined ? args[i + 1] : def; };
const N_FOTOS = Math.max(1, parseInt(valor("fotos", process.env.BANCO_FOTOS || "30"), 10) || 30);
const PRESUPUESTO = Math.max(0, parseFloat(valor("presupuesto", process.env.BANCO_PRESUPUESTO || "6000")) || 6000);
const CONFIGS_PEDIDAS = String(valor("configs", process.env.BANCO_CONFIGS || "todas")).split(",").map((s) => s.trim()).filter(Boolean);
const DIR_FOTOS = path.resolve(RAIZ, valor("dir-fotos", "web/fotos"));
const SIMULAR = flag("simular");
const SOLO_INFORME = flag("solo-informe") || flag("reparsear");
const REPARSEAR = flag("reparsear");
const ACC = process.env.CF_ACCOUNT_ID || "";
const TOKEN = process.env.CF_API_TOKEN || "";

// ------------------------------------------------------------------ modelos y configuraciones
// Neuronas por millón de tokens (página de precios de Cloudflare). Las de Gemma 4 se calculan a partir de su precio en
// dólares (0,10 $ y 0,30 $ por millón, a 0,011 $ por 1.000 neuronas) porque la página no las da: son una estimación.
const MODELOS = {
  llama32: { id: "@cf/meta/llama-3.2-11b-vision-instruct", nin: 4410, nout: 61493, variantes: ["img_campo", "img_url"] },
  scout: { id: "@cf/meta/llama-4-scout-17b-16e-instruct", nin: 24545, nout: 77273, variantes: ["img_url", "img_campo"] },
  gemma4: { id: "@cf/google/gemma-4-26b-a4b-it", nin: 9091, nout: 27273, estimado: true,
    variantes: ["img_url_sinpensar", "img_url_mct_sinpensar", "img_url", "img_url_mct", "img_url_largo", "img_url_mct_largo"] },
};
const CONFIGS = {
  llama32_v1: { modelo: "llama32", prompt: "v1", descripcion: "Lo que hace la guía HOY: Llama 3.2 11B, prompt en castellano, un hueco por llamada (3 llamadas por foto)" },
  llama32_v2: { modelo: "llama32", prompt: "v2", descripcion: "Llama 3.2 11B con el prompt nuevo (inglés, todos los rasgos, 1 llamada por foto)" },
  scout_v2: { modelo: "scout", prompt: "v2", descripcion: "Llama 4 Scout con el prompt nuevo" },
  gemma4_v2: { modelo: "gemma4", prompt: "v2", descripcion: "Gemma 4 26B con el prompt nuevo" },
};
const ORDEN_CONFIGS = Object.keys(CONFIGS);
const configsActivas = CONFIGS_PEDIDAS.includes("todas") ? ORDEN_CONFIGS : ORDEN_CONFIGS.filter((c) => CONFIGS_PEDIDAS.includes(c));

// ------------------------------------------------------------------ el código del Worker (los mismos prompts y el mismo lector)
const srcWorker = fs.readFileSync(path.join(RAIZ, "worker/index.js"), "utf8");
const a0 = srcWorker.indexOf("const IDENT_MODEL");
const b0 = srcWorker.indexOf("async function runVision");
if (a0 < 0 || b0 < 0) throw new Error("No encuentro la parte de lectura de fotos en worker/index.js");
const W = new Function(srcWorker.slice(a0, b0) +
  "; return { IDENT_VOCAB, IDENT_SYSTEM, identUserPrompt, parseIdentResponse, identTexto, identDimsTodas };")();

// --- «v1»: copia congelada de lo que hacía la guía antes de este cambio (no tocar: es el punto de comparación) ---
const SYSTEM_V1 =
  "Eres un ayudante que describe fotos de setas para un aficionado. No dices qué especie es ni si se puede comer: " +
  "solo marcas rasgos que se ven, eligiendo entre opciones cerradas. " +
  "Responde SIEMPRE y SOLO con un objeto JSON válido, sin texto antes ni después.";
function promptV1(parte) {
  const v = W.IDENT_VOCAB[parte];
  const dims = Object.entries(v.dims).map(([id, d]) =>
    `- ${id} (${d.etq}): ` + Object.entries(d.valores).map(([k, t]) => `${k} = ${t}`).join(" | ")).join("\n");
  const ejemplo = Object.keys(v.dims).map((id) => `"${id}": null`).join(", ");
  return (
    `Esta foto debería enseñar ${v.descripcion}.\n` +
    "Devuelve SOLO este JSON:\n" +
    `{"parte_vista": "sombrero" | "debajo" | "pie" | "otra" | "no_es_seta", "rasgos": {${ejemplo}}}\n` +
    "En parte_vista pon lo que enseña de verdad la foto: sombrero = la cara de arriba del sombrero; " +
    "debajo = la cara de abajo del sombrero (láminas, poros, pliegues...); pie = el pie y su base; " +
    "otra = la seta entera u otra cosa; no_es_seta = no hay ninguna seta.\n" +
    "En cada rasgo pon UNA de las opciones (la palabra de antes del signo =) o null si no se ve con claridad en esta foto. " +
    "No adivines: es mejor null que acertar por suerte.\n" +
    "Rasgos y opciones:\n" + dims
  );
}
function parseV1(raw, parte) {
  let obj = raw;
  if (typeof raw === "string") {
    const a = raw.indexOf("{"), b = raw.lastIndexOf("}");
    if (a < 0 || b <= a) return null;
    try { obj = JSON.parse(raw.slice(a, b + 1)); } catch (e) { return null; }
  }
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) return null;
  if (!("rasgos" in obj) && !("parte_vista" in obj) && !("se_ve_seta" in obj)) return null;
  const vista = typeof obj.parte_vista === "string" ? obj.parte_vista.trim().toLowerCase() : "";
  const noEsSeta = vista === "no_es_seta" || obj.se_ve_seta === false;
  const rasgos = {};
  if (!noEsSeta && obj.rasgos && typeof obj.rasgos === "object" && !Array.isArray(obj.rasgos)) {
    for (const [dim, def] of Object.entries(W.IDENT_VOCAB[parte].dims)) {
      const val = obj.rasgos[dim];
      if (typeof val !== "string") continue;
      const v = val.trim().toLowerCase();
      for (const [id, texto] of Object.entries(def.valores)) if (v === id.toLowerCase() || v === texto.toLowerCase()) rasgos[dim] = id;
    }
  }
  return { se_ve_seta: !noEsSeta, rasgos };
}

// ------------------------------------------------------------------ datos de la guía (fichas, rasgos) y comparador real
const D = JSON.parse(execFileSync("python3", [path.join(AQUI, "generar_guia.py"), "--rasgos"], { encoding: "utf-8", cwd: RAIZ, maxBuffer: 1 << 28 }));
const P = createRequire(import.meta.url)(path.join(AQUI, "puntuar.js"));
const PARTE_DE_DIM = Object.fromEntries(D.dims.map((d) => [d.id, d.parte]));

// ------------------------------------------------------------------ fotos de la muestra
function prng(seed) { // mulberry32: mismo orden siempre, para poder reanudar y ampliar
  let t = seed >>> 0;
  return () => { t = (t + 0x6D2B79F5) >>> 0; let x = Math.imul(t ^ (t >>> 15), 1 | t); x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x; return ((x ^ (x >>> 14)) >>> 0) / 4294967296; };
}
function listarMuestra() {
  const out = [];
  const nombres = fs.existsSync(DIR_FOTOS) ? fs.readdirSync(DIR_FOTOS).filter((f) => /\.(jpe?g)$/i.test(f)).sort() : [];
  const base = [];
  for (const f of nombres) {
    const m = /^(.+)-(\d+)\.jpe?g$/i.exec(f);
    if (!m || !D.firmas[m[1]]) continue;
    base.push({ foto: f, ficha: m[1], origen: "guia", ruta: path.join(DIR_FOTOS, f), hueco: "entera" });
  }
  const r = prng(20261016);
  for (let i = base.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [base[i], base[j]] = [base[j], base[i]]; }
  out.push(...base.slice(0, N_FOTOS));
  // Fotos propias (de Sergio u otras) con la seta conocida: tools/banco/mis_fotos/<ficha>__<hueco>[__lo-que-sea].jpg
  const dirMis = path.join(DIR_BANCO, "mis_fotos_800");
  const dirMisOrig = path.join(DIR_BANCO, "mis_fotos");
  const dirUsar = fs.existsSync(dirMis) ? dirMis : dirMisOrig;
  if (fs.existsSync(dirUsar)) {
    for (const f of fs.readdirSync(dirUsar).filter((x) => /\.(jpe?g)$/i.test(x)).sort()) {
      const m = /^([^_]+)__(sombrero|debajo|pie)/i.exec(f);
      if (!m || !D.firmas[m[1]]) { console.log("  (mis_fotos: ignoro " + f + ": el nombre debe ser <ficha>__<sombrero|debajo|pie>….jpg y la ficha existir)"); continue; }
      out.push({ foto: "mis_fotos/" + f, ficha: m[1], origen: "mia", ruta: path.join(dirUsar, f), hueco: m[2].toLowerCase() });
    }
  }
  return out;
}

// ------------------------------------------------------------------ llamadas a Cloudflare
function entrada(variante, sistema, usuario, dataUrl) {
  const base = { temperature: 0.1 };
  const msgs = (conImagen) => [{ role: "system", content: sistema },
    conImagen ? { role: "user", content: [{ type: "text", text: usuario }, { type: "image_url", image_url: { url: dataUrl } }] }
      : { role: "user", content: usuario }];
  switch (variante) {
    case "img_campo": return { ...base, max_tokens: 400, messages: msgs(false), image: dataUrl };
    case "img_url": return { ...base, max_tokens: 400, messages: msgs(true) };
    case "img_url_mct": return { ...base, max_completion_tokens: 400, messages: msgs(true) };
    case "img_url_largo": return { ...base, max_tokens: 2000, messages: msgs(true) };           // por si el modelo «piensa» antes de contestar y se queda sin espacio
    case "img_url_mct_largo": return { ...base, max_completion_tokens: 2000, messages: msgs(true) };
    case "img_url_sinpensar": return { ...base, max_tokens: 400, messages: msgs(true), chat_template_kwargs: { enable_thinking: false } };
    case "img_url_mct_sinpensar": return { ...base, max_completion_tokens: 400, messages: msgs(true), chat_template_kwargs: { enable_thinking: false } };
    default: throw new Error("variante desconocida " + variante);
  }
}

class CupoAgotado extends Error {}

async function llamarCF(modelo, cuerpo) {
  if (SIMULAR) return simularRespuesta(modelo, cuerpo);
  for (let intento = 0; intento < 2; intento++) {
    let r, j;
    try {
      r = await fetch(`https://api.cloudflare.com/client/v4/accounts/${ACC}/ai/run/${modelo.id}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" },
        body: JSON.stringify(cuerpo),
        signal: AbortSignal.timeout(90000),
      });
      j = await r.json().catch(() => null);
    } catch (e) {
      if (intento === 0) { await dormir(2000); continue; }
      return { ok: false, status: 0, error: "red: " + String(e && e.message).slice(0, 160) };
    }
    const errTxt = j && Array.isArray(j.errors) && j.errors.length ? j.errors.map((x) => `${x.code}: ${x.message}`).join(" | ").slice(0, 300) : "";
    if (/neurons|daily free allocation|quota|allocation/i.test(errTxt) || r.status === 429) {
      if (/neurons|allocation|quota/i.test(errTxt)) throw new CupoAgotado(errTxt);
      if (intento === 0) { await dormir(5000); continue; }
    }
    if (r.status >= 500 && intento === 0) { await dormir(3000); continue; }
    if (!r.ok || !j || j.success === false) return { ok: false, status: r.status, error: errTxt || "sin detalle" };
    return { ok: true, status: r.status, resultado: j.result };
  }
  return { ok: false, status: 0, error: "sin respuesta" };
}
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));

function tokensDe(resultado) {
  const u = resultado && resultado.usage;
  if (u && (u.prompt_tokens != null || u.completion_tokens != null)) return { pt: u.prompt_tokens || 0, ct: u.completion_tokens || 0, real: true };
  return { pt: 0, ct: 0, real: false };
}
function neuronas(modelo, t) {
  if (!t.real) return 40;  // sin «usage» se apunta una cifra prudente para que el tope siga funcionando
  return (t.pt * modelo.nin + t.ct * modelo.nout) / 1e6;
}

// ------------------------------------------------------------------ simulación (solo para probar el circuito sin red)
let _simVerdad = null;
function simularRespuesta(modelo, cuerpo) {
  const verdad = _simVerdad || {};
  const sesgo = modelo.id.includes("gemma") ? 0.1 : modelo.id.includes("scout") ? 0.2 : 0.4;
  const txt = JSON.stringify(cuerpo);
  const v1 = txt.includes("parte_vista");
  const traits = {};
  let k = 0;
  for (const [dim] of W.identDimsTodas()) {
    k++;
    const firma = D.firmas[verdad.ficha] && D.firmas[verdad.ficha][dim];
    const roll = ((k * 7919 + (verdad.ficha || "").length * 104729) % 100) / 100;
    if (!firma || roll < sesgo * 0.5) { traits[dim] = null; continue; }
    const en = {
      pardo: "brown", blanco: "white", amarillo: "yellow", naranja: "orange", rojo: "red", rosa: "pink", gris: "grey", verde: "green",
      negro: "black", violeta: "violet", lisa: "smooth", viscosa: "sticky", escamas: "scaly", fibrosa: "fibrous", convexo: "convex",
      conico: "conical", embudo: "funnel", alveolado: "honeycomb", cerebro: "brain", laminas: "gills", poros: "pores", pliegues: "ridges",
      puas: "spines", liso: "smooth", si: "yes", no: "no", bolsa: "sack", ensanchada: "swollen", normal: "normal", red: "net", puntos: "dotted",
    };
    const val = roll < sesgo ? (dim.endsWith("color") ? "grey" : null) : firma[0][0];
    traits[dim] = val == null ? null : (v1 ? val : (en[val] || val));
  }
  let texto;
  if (v1) {
    const parte = /DEBAJO/.test(txt) ? "debajo" : /PIE y su BASE|el PIE/.test(txt) ? "pie" : "sombrero";
    const ids = Object.keys(W.IDENT_VOCAB[parte].dims);
    const r = {}; ids.forEach((d) => { r[d] = traits[d]; });
    texto = JSON.stringify({ parte_vista: parte, rasgos: r });
  } else texto = JSON.stringify({ mushroom_visible: true, traits });
  const usage = { prompt_tokens: 1900, completion_tokens: 110 };
  return { ok: true, status: 200, resultado: modelo.id.includes("llama-3.2") ? { response: texto, usage } : { choices: [{ message: { content: texto } }], usage } };
}

// ------------------------------------------------------------------ resultados guardados
fs.mkdirSync(DIR_BANCO, { recursive: true });
function leerResultados() {
  if (!fs.existsSync(F_RES)) return [];
  return fs.readFileSync(F_RES, "utf8").split("\n").filter(Boolean).map((l) => { try { return JSON.parse(l); } catch (e) { return null; } }).filter(Boolean);
}
function guardar(reg) { fs.appendFileSync(F_RES, JSON.stringify(reg) + "\n"); }
function leerJson(f, def) { try { return JSON.parse(fs.readFileSync(f, "utf8")); } catch (e) { return def; } }

// ------------------------------------------------------------------ sondeo: qué forma de pasar la foto acepta cada modelo
async function sondear(modeloKey, muestra) {
  const formato = leerJson(F_FORMATO, {});
  if (formato[modeloKey]) return formato[modeloKey];
  const modelo = MODELOS[modeloKey];
  const dataUrl = "data:image/jpeg;base64," + fs.readFileSync(muestra.ruta).toString("base64");
  const sondeo = leerJson(F_SONDEO, {});
  sondeo[modeloKey] = sondeo[modeloKey] || [];
  _simVerdad = { ficha: muestra.ficha };
  let gastadas = 0;
  for (const variante of modelo.variantes) {
    let rep;
    try { rep = await llamarCF(modelo, entrada(variante, W.IDENT_SYSTEM, W.identUserPrompt("sombrero"), dataUrl)); }
    catch (e) { if (e instanceof CupoAgotado) throw e; rep = { ok: false, status: 0, error: String(e.message) }; }
    let texto = "", vistos = null, neu = 0;
    if (rep.ok) {
      const t = tokensDe(rep.resultado);
      neu = neuronas(modelo, t); gastadas += neu;
      texto = W.identTexto(rep.resultado);
      if (typeof texto !== "string") texto = JSON.stringify(texto);
      const p = W.parseIdentResponse(texto, "sombrero");
      vistos = p ? Object.keys(p.rasgos).length : null;
      const msg = rep.resultado && rep.resultado.choices && rep.resultado.choices[0] && rep.resultado.choices[0].message;
      sondeo[modeloKey].push({ variante, status: rep.status, ok: !!(texto && p), rasgos_leidos: vistos, tokens: t, neuronas: Math.round(neu * 10) / 10,
        claves_resultado: rep.resultado && typeof rep.resultado === "object" ? Object.keys(rep.resultado) : typeof rep.resultado,
        claves_mensaje: msg ? Object.keys(msg) : undefined, fin: rep.resultado && rep.resultado.choices && rep.resultado.choices[0] ? rep.resultado.choices[0].finish_reason : undefined,
        texto: String(texto).slice(0, 1500) });
      if (String(texto).trim()) { formato[modeloKey] = variante; break; }
    } else {
      sondeo[modeloKey].push({ variante, status: rep.status, ok: false, error: rep.error });
    }
  }
  fs.writeFileSync(F_SONDEO, JSON.stringify(sondeo, null, 2));
  if (formato[modeloKey]) fs.writeFileSync(F_FORMATO, JSON.stringify(formato, null, 2));
  return { variante: formato[modeloKey] || null, gastadas };
}

// ------------------------------------------------------------------ una medida: una foto con una configuración
async function medir(cfgKey, muestra, variante, estado) {
  const cfg = CONFIGS[cfgKey], modelo = MODELOS[cfg.modelo];
  const dataUrl = "data:image/jpeg;base64," + fs.readFileSync(muestra.ruta).toString("base64");
  _simVerdad = { ficha: muestra.ficha };
  const huecos = cfg.prompt === "v1" ? ["sombrero", "debajo", "pie"] : [muestra.hueco];
  const reg = { cfg: cfgKey, foto: muestra.foto, ficha: muestra.ficha, origen: muestra.origen, t: new Date().toISOString(), variante, llamadas: [], rasgos: {}, neuronas: 0, ms: 0 };
  const ini = Date.now();
  let algunExito = false, todasFallan = true;
  for (const hueco of huecos) {
    if (estado.gastadas >= PRESUPUESTO) { estado.parar = "presupuesto"; return null; }
    const sistema = cfg.prompt === "v1" ? SYSTEM_V1 : W.IDENT_SYSTEM;
    const usuario = cfg.prompt === "v1" ? promptV1(hueco) : W.identUserPrompt(hueco);
    const rep = await llamarCF(modelo, entrada(variante, sistema, usuario, dataUrl));
    if (!rep.ok) { reg.llamadas.push({ hueco, error: rep.error, status: rep.status }); continue; }
    todasFallan = false;
    const t = tokensDe(rep.resultado);
    const neu = neuronas(modelo, t);
    estado.gastadas += neu; reg.neuronas += neu;
    let texto = W.identTexto(rep.resultado);
    if (typeof texto !== "string") texto = JSON.stringify(texto);
    const p = cfg.prompt === "v1" ? parseV1(texto, hueco) : W.parseIdentResponse(texto, hueco);
    reg.llamadas.push({ hueco, tokens: t, neuronas: Math.round(neu * 10) / 10, texto: String(texto).slice(0, 1500), parseado: !!p, se_ve_seta: p ? p.se_ve_seta : null });
    if (p) {
      algunExito = true;
      if (p.se_ve_seta === false) { reg.no_es_seta = true; continue; }
      for (const [dim, val] of Object.entries(p.rasgos)) {
        // En «v1» cada llamada solo trae los rasgos de su hueco; en «v2» (una llamada) traen todos.
        if (reg.rasgos[dim] === undefined) reg.rasgos[dim] = val;
      }
    }
    await dormir(250);
  }
  reg.ms = Date.now() - ini;
  reg.neuronas = Math.round(reg.neuronas * 10) / 10;
  reg.ok = algunExito;
  if (todasFallan) reg.fallo_total = true;
  return reg;
}

// ------------------------------------------------------------------ informe
function posicion(rasgos, ficha) {
  const n = Object.keys(rasgos).length;
  if (n < D.min_rasgos) return { rank: null, motivo: "pocos_rasgos", n };
  const res = P.comparar(rasgos, D);
  const g = P.agrupar(res, n, D);
  const i = g.candidatas.findIndex((x) => x.id === ficha);
  const p = g.candidatas.find((x) => x.id === ficha);
  const descartada = g.descartadas && g.descartadas.some((x) => x.id === ficha);
  const dud = g.dudosas && g.dudosas.some((x) => x.id === ficha);
  return { rank: i >= 0 ? i : null, motivo: i >= 0 ? "candidata" : dud ? "dudosa" : descartada ? "descartada" : "no_candidata", n, pct: p ? p.pct : null, n_cand: g.candidatas.length };
}
function comparaConFicha(rasgos, ficha) {
  let ok = 0, mal = 0; const malos = [];
  for (const [dim, val] of Object.entries(rasgos)) {
    const f = D.firmas[ficha][dim];
    if (!f) continue;                       // la ficha no dice nada de ese rasgo: no se puede valorar
    if (f[0].indexOf(val) >= 0) ok++; else { mal++; malos.push(dim + "=" + val + " (ficha: " + f[0].join("/") + ")"); }
  }
  return { ok, mal, malos };
}
function resumirConfig(regs) {
  const r = { fotos: regs.length, ok: 0, fallos: 0, rasgos_leidos: 0, comparables: 0, acierta: 0, top1: 0, top5: 0, top10: 0, pocos_rasgos: 0, sin_candidata: 0, neuronas: 0, ms: 0, por_dim: {} };
  for (const g of regs) {
    r.neuronas += g.neuronas || 0; r.ms += g.ms || 0;
    if (!g.ok) { r.fallos++; continue; }
    r.ok++;
    const n = Object.keys(g.rasgos).length;
    r.rasgos_leidos += n;
    const c = comparaConFicha(g.rasgos, g.ficha);
    r.comparables += c.ok + c.mal; r.acierta += c.ok;
    for (const [dim, val] of Object.entries(g.rasgos)) {
      const f = D.firmas[g.ficha][dim]; const pd = (r.por_dim[dim] = r.por_dim[dim] || { leido: 0, comparable: 0, ok: 0 });
      pd.leido++; if (f) { pd.comparable++; if (f[0].indexOf(val) >= 0) pd.ok++; }
    }
    const pos = posicion(g.rasgos, g.ficha);
    if (pos.motivo === "pocos_rasgos") r.pocos_rasgos++;
    else if (pos.rank === null) r.sin_candidata++;
    else { if (pos.rank === 0) r.top1++; if (pos.rank < 5) r.top5++; if (pos.rank < 10) r.top10++; }
  }
  return r;
}
const pct = (a, b) => (b ? Math.round((100 * a) / b) + " %" : "—");

function escribirInforme(regs, estado) {
  const porCfg = {};
  for (const r of regs) (porCfg[r.cfg] = porCfg[r.cfg] || []).push(r);
  // Solo se comparan las fotos medidas por TODAS las configuraciones que tienen datos (si no, la comparación no es justa).
  const cfgsConDatos = ORDEN_CONFIGS.filter((c) => porCfg[c] && porCfg[c].length);
  let comunes = null;
  for (const c of cfgsConDatos) { const s = new Set(porCfg[c].map((x) => x.foto)); comunes = comunes ? new Set([...comunes].filter((x) => s.has(x))) : s; }
  comunes = comunes || new Set();
  const L = [];
  L.push("# Banco de pruebas de la lectura de fotos con IA");
  L.push("");
  L.push("Generado: " + new Date().toISOString() + (SIMULAR ? "  **(SIMULADO: respuestas inventadas, solo para probar el circuito)**" : ""));
  L.push("");
  L.push(`Fotos medidas por todas las configuraciones: **${comunes.size}**. Cada foto es de la propia guía (se sabe qué seta es). ` +
    "«Top 5» = la ficha correcta sale entre las 5 primeras al pasar los rasgos leídos por la comparación real de la guía (mismos umbrales que en producción). " +
    "Referencia: con los rasgos PERFECTOS de cada ficha, la ficha correcta sale primera en 298 de 313 casos.");
  L.push("");
  L.push("| Configuración | Fotos | Lectura OK | Rasgos leídos por foto | Rasgos leídos que encajan con la ficha | Top 1 | Top 5 | Top 10 | Sin rasgos suficientes | Neuronas por foto |");
  L.push("|---|---|---|---|---|---|---|---|---|---|");
  const resumen = {};
  for (const c of cfgsConDatos) {
    const sub = porCfg[c].filter((x) => comunes.has(x.foto));
    const r = resumirConfig(sub);
    resumen[c] = r;
    L.push(`| ${c} | ${r.fotos} | ${r.ok} | ${r.ok ? (r.rasgos_leidos / r.ok).toFixed(1) : "—"} de 9 | ${pct(r.acierta, r.comparables)} (${r.acierta}/${r.comparables}) | ${pct(r.top1, r.fotos)} | ${pct(r.top5, r.fotos)} | ${pct(r.top10, r.fotos)} | ${r.pocos_rasgos} | ${r.fotos ? (r.neuronas / r.fotos).toFixed(0) : "—"} |`);
  }
  L.push("");
  L.push("Qué es cada configuración:");
  for (const c of cfgsConDatos) L.push(`- **${c}**: ${CONFIGS[c].descripcion} (${MODELOS[CONFIGS[c].modelo].id}${MODELOS[CONFIGS[c].modelo].estimado ? "; neuronas estimadas" : ""})`);
  L.push("");
  L.push("## Acierto por rasgo (rasgos leídos que encajan con lo que dice la ficha)");
  const dimsOrden = W.identDimsTodas().map((x) => x[0]);
  L.push("| Rasgo | " + cfgsConDatos.join(" | ") + " |");
  L.push("|---|" + cfgsConDatos.map(() => "---").join("|") + "|");
  for (const d of dimsOrden) {
    L.push(`| ${d} | ` + cfgsConDatos.map((c) => { const p = resumen[c].por_dim[d]; return p ? `${pct(p.ok, p.comparable)} (leído ${p.leido}/${resumen[c].ok})` : "—"; }).join(" | ") + " |");
  }
  L.push("");
  L.push("## Foto por foto");
  const fotos = [...comunes].sort();
  for (const f of fotos) {
    const reg0 = porCfg[cfgsConDatos[0]].find((x) => x.foto === f);
    L.push(`### ${f} → ficha «${reg0.ficha}»`);
    const tip = Object.fromEntries(Object.entries(D.firmas[reg0.ficha]).map(([d, v]) => [d, v[0].join("/")]));
    L.push("Ficha dice: " + Object.entries(tip).filter(([d]) => PARTE_DE_DIM[d] !== "otros").map(([d, v]) => `${d}=${v}`).join(", "));
    for (const c of cfgsConDatos) {
      const g = porCfg[c].find((x) => x.foto === f);
      if (!g) continue;
      const pos = g.ok ? posicion(g.rasgos, g.ficha) : { rank: null, motivo: "fallo" };
      const cm = g.ok ? comparaConFicha(g.rasgos, g.ficha) : { malos: [] };
      L.push(`- ${c}: ` + (g.ok ? Object.entries(g.rasgos).map(([d, v]) => `${d}=${v}`).join(", ") || "(ningún rasgo)" : "FALLÓ") +
        ` → ${pos.rank === null ? pos.motivo : "puesto " + (pos.rank + 1)}` + (cm.malos.length ? ` · no encajan: ${cm.malos.join("; ")}` : ""));
    }
    L.push("");
  }
  const mias = regs.filter((x) => x.origen === "mia");
  if (mias.length) {
    L.push("## Fotos propias");
    for (const g of mias) {
      const pos = g.ok ? posicion(g.rasgos, g.ficha) : { rank: null, motivo: "fallo" };
      L.push(`- ${g.foto} (${g.cfg}): ` + (g.ok ? Object.entries(g.rasgos).map(([d, v]) => `${d}=${v}`).join(", ") || "(ningún rasgo)" : "FALLÓ") + ` → ${pos.rank === null ? pos.motivo : "puesto " + (pos.rank + 1)}`);
    }
    L.push("");
  }
  const fallos = regs.filter((x) => !x.ok);
  if (fallos.length) {
    L.push("## Fallos");
    for (const g of fallos.slice(0, 20)) L.push(`- ${g.cfg} · ${g.foto}: ` + g.llamadas.map((l) => l.error || ("no se pudo leer: " + (l.texto || "").slice(0, 120).replace(/\s+/g, " "))).join(" | "));
    L.push("");
  }
  L.push(`Neuronas gastadas en esta ejecución: ${Math.round(estado.gastadas)} de ${PRESUPUESTO} de presupuesto${estado.parar ? " · parada: " + estado.parar : ""}.`);
  fs.writeFileSync(F_INFORME, L.join("\n") + "\n");
  fs.writeFileSync(F_RESUMEN, JSON.stringify({ generado: new Date().toISOString(), simulado: SIMULAR, fotos_comunes: comunes.size, configs: resumen }, null, 2));
}

// Vuelve a leer los textos que dio el modelo con el lector actual (sin gastar nada): sirve si se ajusta el lector.
function reparsear() {
  const regs = leerResultados();
  for (const g of regs) {
    const cfg = CONFIGS[g.cfg]; if (!cfg) continue;
    g.rasgos = {}; g.ok = false; delete g.no_es_seta;
    for (const l of g.llamadas) {
      if (!l.texto) continue;
      const p = cfg.prompt === "v1" ? parseV1(l.texto, l.hueco) : W.parseIdentResponse(l.texto, l.hueco);
      l.parseado = !!p;
      if (!p) continue;
      g.ok = true;
      if (p.se_ve_seta === false) { g.no_es_seta = true; continue; }
      for (const [dim, val] of Object.entries(p.rasgos)) if (g.rasgos[dim] === undefined) g.rasgos[dim] = val;
    }
  }
  fs.writeFileSync(F_RES, regs.map((r) => JSON.stringify(r)).join("\n") + (regs.length ? "\n" : ""));
  console.log("Releídos " + regs.length + " resultados con el lector actual.");
}

// ------------------------------------------------------------------ principal
async function main() {
  const estado = { gastadas: 0, parar: "" };
  if (!SOLO_INFORME) {
    if (!SIMULAR && (!ACC || !TOKEN)) { console.error("Faltan CF_ACCOUNT_ID y CF_API_TOKEN (secretos del repositorio)."); process.exit(2); }
    const muestra = listarMuestra();
    if (!muestra.length) { console.error("No hay fotos en " + DIR_FOTOS); process.exit(2); }
    console.log(`Muestra: ${muestra.length} fotos · configuraciones: ${configsActivas.join(", ")} · presupuesto: ${PRESUPUESTO} neuronas${SIMULAR ? " · SIMULADO" : ""}`);
    const hechos = new Set(leerResultados().map((r) => r.cfg + "|" + r.foto));
    try {
      // 1) sondeo de formato, una vez por modelo
      const formatos = {};
      for (const mk of [...new Set(configsActivas.map((c) => CONFIGS[c].modelo))]) {
        const s = await sondear(mk, muestra[0]);
        if (s && s.gastadas) estado.gastadas += s.gastadas;
        const v = typeof s === "string" ? s : s && s.variante;
        formatos[mk] = v;
        console.log(`  sondeo ${mk}: ` + (v ? "forma que funciona = " + v : "NINGUNA forma funciona (mira tools/banco/sondeo.json)"));
      }
      // 2) medidas, foto a foto y repartiendo entre configuraciones (si se corta, queda equilibrado)
      for (const m of muestra) {
        for (const c of configsActivas) {
          const variante = formatos[CONFIGS[c].modelo];
          if (!variante || hechos.has(c + "|" + m.foto)) continue;
          if (estado.gastadas >= PRESUPUESTO) { estado.parar = "presupuesto"; break; }
          const reg = await medir(c, m, variante, estado);
          if (!reg) break;
          guardar(reg); hechos.add(c + "|" + m.foto);
          console.log(`  ${c} · ${m.foto} (${m.ficha}): ` + (reg.ok ? Object.keys(reg.rasgos).length + " rasgos" : "FALLO") + ` · ${reg.neuronas} neuronas · total ${Math.round(estado.gastadas)}`);
        }
        if (estado.parar) break;
      }
    } catch (e) {
      if (e instanceof CupoAgotado) { estado.parar = "Cloudflare dice que se ha acabado el cupo gratuito de hoy: " + e.message.slice(0, 120); console.log("  " + estado.parar); }
      else throw e;
    }
  }
  if (REPARSEAR) reparsear();
  escribirInforme(leerResultados(), estado);
  console.log("Informe: tools/banco/INFORME.md · neuronas gastadas ahora: " + Math.round(estado.gastadas));
}
main().catch((e) => { console.error("Error: " + (e && e.stack ? e.stack.split("\n").slice(0, 4).join("\n") : e)); process.exit(1); });
