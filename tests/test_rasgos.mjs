// Pruebas de la comparación de rasgos con las fichas (tools/puntuar.js + tools/rasgos_datos.py).
// Uso (desde la carpeta tests/):  node test_rasgos.mjs
//
// OJO: estas pruebas comprueban que el CÁLCULO hace lo que se ha diseñado (coherencia). NO miden cuánto acierta la
// identificación con setas reales: los «ejemplares tipo» salen de las propias fichas, así que no son una validación.
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const aqui = path.dirname(fileURLToPath(import.meta.url));
const tools = path.join(aqui, "..", "tools");
const D = JSON.parse(execFileSync("python3", [path.join(tools, "generar_guia.py"), "--rasgos"], { encoding: "utf-8" }));
const P = createRequire(import.meta.url)(path.join(tools, "puntuar.js"));

let ok = 0, bad = 0;
function check(name, cond, extra = "") {
  if (cond) ok++; else { bad++; console.log("FALLO:", name, extra); }
}
const evalua = (obs) => {
  const res = P.comparar(obs, D);
  return { res, g: P.agrupar(res, Object.keys(obs).length, D), por: Object.fromEntries(res.map((r) => [r.id, r])) };
};
const ids = Object.keys(D.firmas);
const tipico = (id) => Object.fromEntries(Object.entries(D.firmas[id]).map(([dim, [vals]]) => [dim, vals[0]]));
const enCand = (g, id) => g.candidatas.some((r) => r.id === id);
const enDud = (g, id) => g.dudosas.some((r) => r.id === id);

check("hay 30 fichas con firma y todas tienen datos de gravedad", ids.length === 30 && ids.every((i) => D.cartas[i]));

// 1) Cada ficha, con sus propios rasgos, sale como candidata
let primeros = 0;
for (const id of ids) {
  const obs = tipico(id);
  if (Object.keys(obs).length < D.min_rasgos) obs.s_color = obs.s_color || "pardo";   // la colmenilla solo describe 2 rasgos: se añade uno que no la contradice
  const { g, por } = evalua(obs);
  check(`ejemplar tipo de «${id}»: sale como candidata con ≥ ${D.min_pct} %`, enCand(g, id) && por[id].pct >= D.min_pct, JSON.stringify(por[id]));
  check(`ejemplar tipo de «${id}»: ningún rasgo en contra`, por[id].no.length === 0);
  if (g.candidatas[0] && g.candidatas[0].id === id) primeros++;
}
check("la ficha propia es la primera de la lista en al menos 28 de 30 ejemplares tipo (la clitocibe y el cama-sec se confunden por diseño)", primeros >= 28, String(primeros));

// 2) Un rasgo no indicado ni suma ni resta; ningún % pasa de 100
{
  const t = tipico("cep");
  const a = evalua(t).por.cep;
  const t2 = { ...t }; delete t2.olor;
  const b = evalua(t2).por.cep;
  check("quitar un rasgo que encajaba baja el % pero no lo convierte en un rasgo en contra", b.pct < a.pct && b.no.length === 0 && b.falta.some((f) => f.dim === "olor"));
  check("ningún % pasa de 100 ni baja de 0 con ningún ejemplar tipo",
        ids.every((id) => evalua(tipico(id)).res.every((r) => r.pct >= 0 && r.pct <= 100)));
  check("con menos de 3 rasgos no se hace ninguna lista", evalua({ s_color: "verde", h_tipo: "laminas" }).g.pocosDatos === true);
  check("sin ningún rasgo tampoco", evalua({}).g.pocosDatos === true && evalua({}).g.candidatas.length === 0);
}

// 3) El % tiene en cuenta lo que falta por confirmar: una ficha larga no llega a 100 con pocos rasgos
{
  const { por } = evalua({ s_color: "pardo", h_tipo: "poros", h_color: "blanco" });
  check("cep con solo 3 rasgos: menos de 60 % (faltan casi todos por confirmar)", por.cep.pct < 60, String(por.cep.pct));
  const { por: p2 } = evalua({ s_forma: "alveolado", interior: "hueco", s_color: "pardo" });
  check("colmenilla (ficha de 2 rasgos): no pasa del 60 % por el peso mínimo del retrato", p2.colmenilles.pct === 60, String(p2.colmenilles.pct));
}

// 4) Rasgos clave: una ficha comestible con un rasgo clave en contra queda descartada
{
  const t = { ...tipico("cep"), h_tipo: "laminas" };
  const { g, por } = evalua(t);
  check("cep con «láminas» (poros es clave) → descartada, no candidata", !enCand(g, "cep") && por.cep.clave.includes("h_tipo"));
  const t2 = { ...tipico("oureig"), h_color: "blanco" };
  const e2 = evalua(t2);
  check("ou de reig con láminas BLANCAS → descartada", !enCand(e2.g, "oureig") && e2.por.oureig.clave.includes("h_color"));
  check("…y con ese mismo fallo de lectura la oronja verde pasa a ser la primera candidata (el error va hacia el lado seguro)",
        e2.g.candidatas[0] && e2.g.candidatas[0].id === "phalloides", JSON.stringify(e2.g.candidatas.map((r) => r.id)));
}

// 5) Peligrosas: aparecen aunque fallen un rasgo clave, salvo láminas contra poros
{
  const e = evalua(tipico("oureig"));
  check("ou de reig típico: la oronja verde (mortal) sale como «no puedes descartar el parecido»", enDud(e.g, "phalloides") || enCand(e.g, "phalloides"), JSON.stringify(e.g.dudosas.map((r) => r.id)));
  check("ou de reig típico: las amanitas blancas también salen como dudosas", enDud(e.g, "amanitas-blancas") || enCand(e.g, "amanitas-blancas"));
  const c = evalua(tipico("cep"));
  check("cep típico: el boleto amargo sale en la lista (confusión de la ficha)", enCand(c.g, "tylopilus"));
  check("cep típico: ninguna peligrosa de láminas aparece como dudosa por tener poros en contra (muscaria, etc.)",
        c.g.dudosas.every((r) => !r.clave.includes("h_tipo")), JSON.stringify(c.g.dudosas.map((r) => r.id)));
  const a = evalua(tipico("apagallums"));
  check("apagallums típico: lepiota y amanitas blancas salen en la lista (confusiones de la ficha)", enCand(a.g, "lepiota") && (enCand(a.g, "amanitas-blancas") || enDud(a.g, "amanitas-blancas")));
  const k = evalua(tipico("camasec"));
  check("cama-sec típico: la clitocibe de prado sale en la lista (confusión de la ficha)", enCand(k.g, "clitocybe"));
  const s = evalua(tipico("satanas"));
  check("boleto de Satanás típico: los boletos de poros rojos salen en la lista", enCand(s.g, "luridos"));
  const l = evalua(tipico("luridos"));
  check("boleto de poros rojos típico: el boleto de Satanás sale en la lista", enCand(l.g, "satanas"));
  const m = evalua({ ...tipico("muscaria"), h_tipo: "poros" });
  check("matamoscas con «poros» (todo lo demás igual, 75 % sin ese fallo): NO sale como dudosa, porque láminas contra poros no se confunde",
        !enDud(m.g, "muscaria") && !enCand(m.g, "muscaria") && m.por.muscaria.pct >= D.min_pct_dudosa && m.por.muscaria.clave.join() === "h_tipo", JSON.stringify(m.por.muscaria));
  const m2 = evalua({ ...tipico("muscaria"), s_color: "verde" });
  check("matamoscas con sombrero verde (otro rasgo clave en contra, pero por lo demás igual): SÍ sale como dudosa", enDud(m2.g, "muscaria"), JSON.stringify(m2.por.muscaria));
  check("todas las que salen como dudosas son peligrosas", ids.every((id) => evalua(tipico(id)).g.dudosas.every((r) => D.cartas[r.id].peligro)));
}

// 6) Orden: de mayor a menor %; a igualdad, primero las peligrosas
{
  const { g } = evalua(tipico("apagallums"));
  const pcts = g.candidatas.map((r) => r.pct);
  check("la lista está ordenada de mayor a menor %", pcts.every((p, i) => i === 0 || pcts[i - 1] >= p), JSON.stringify(pcts));
  const fake = { ...D, firmas: { a: { h_tipo: [["laminas"], 3], s_color: [["pardo"], 3], p_anillo: [["si"], 4] }, b: { h_tipo: [["laminas"], 3], s_color: [["pardo"], 3], p_anillo: [["si"], 4] } },
                 cartas: { a: { grav: "ok", peligro: false }, b: { grav: "mortal", peligro: true } }, min_peso: 0 };
  const res = P.comparar({ h_tipo: "laminas", s_color: "pardo", p_anillo: "si" }, fake);
  const gg = P.agrupar(res, 3, fake);
  check("a igualdad de % y de rasgos, la peligrosa va antes que la comestible", gg.candidatas.map((r) => r.id).join() === "b,a", gg.candidatas.map((r) => r.id).join());
}

// 7) Sugerencias para afinar
{
  const { g, res } = evalua({ s_color: "verde", h_tipo: "laminas", h_color: "blanco" });
  const sig = P.siguientes(g, 4);
  check("«para afinar» solo propone rasgos que aún no se han indicado", sig.length > 0 && sig.every((d) => !["s_color", "h_tipo", "h_color"].includes(d)), JSON.stringify(sig));
  check("«para afinar» propone como mucho 4", sig.length <= 4);
  const vacio = P.siguientes({ candidatas: [], dudosas: [], descartadas: [] }, 4);
  check("sin fichas no hay sugerencias y no rompe", Array.isArray(vacio) && vacio.length === 0);
}

// 8) Datos: cada valor de cada firma existe y las partes están bien
{
  const valoresDe = Object.fromEntries(D.dims.map((d) => [d.id, new Set(d.valores.map((v) => v[0]))]));
  let malos = [];
  for (const [id, f] of Object.entries(D.firmas)) for (const [dim, [vals, w]] of Object.entries(f)) {
    if (!valoresDe[dim]) malos.push([id, dim]);
    else for (const v of vals) if (!valoresDe[dim].has(v)) malos.push([id, dim, v]);
    if (w !== 1 && w !== 3) malos.push([id, dim, "peso " + w]);
  }
  check("todos los valores de todas las firmas existen en el vocabulario y los pesos son 1 o 3", malos.length === 0, JSON.stringify(malos));
  check("«qué hay debajo del sombrero» es clave en TODAS las fichas que lo nombran",
        Object.values(D.firmas).every((f) => !f.h_tipo || f.h_tipo[1] === 3));
  check("las partes de la IA son sombrero, debajo y pie; el resto lo rellena la persona",
        D.dims.filter((d) => d.parte !== "otros").every((d) => ["sombrero", "debajo", "pie"].includes(d.parte)) &&
        D.dims.filter((d) => d.parte === "otros").length === 8);
}

console.log(`Rasgos: ${ok} comprobaciones OK, ${bad} fallos`);
process.exit(bad ? 1 : 0);
