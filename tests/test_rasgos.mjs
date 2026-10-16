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
// Las 50 fichas de siempre (rasgos_datos.FIRMAS_BASE); las demás son la ampliación del 16/10/2026 (especies_extra.py).
const BASE = JSON.parse(execFileSync("python3", ["-c", "import sys; sys.path.insert(0, 'tools'); import rasgos_datos as r, json; print(json.dumps(r.FIRMAS_BASE))"],
  { encoding: "utf-8", cwd: path.join(aqui, "..") }));
const EXTRA = ids.filter((i) => !BASE.includes(i));
const tipico = (id) => Object.fromEntries(Object.entries(D.firmas[id]).map(([dim, [vals]]) => [dim, vals[0]]));
const enCand = (g, id) => g.candidatas.some((r) => r.id === id);
const enDud = (g, id) => g.dudosas.some((r) => r.id === id);

check("hay 313 fichas con firma (50 de siempre + 263 de la ampliación del 16/10/2026) y todas tienen datos de gravedad",
      BASE.length === 50 && EXTRA.length === 263 && ids.length === 313 && ids.every((i) => D.cartas[i]), `${BASE.length} ${EXTRA.length} ${ids.length}`);

// 1) Cada ficha, con sus propios rasgos, sale como candidata
let primeros = 0, primerosBase = 0;
for (const id of ids) {
  const obs = tipico(id);
  if (Object.keys(obs).length < D.min_rasgos) obs.s_color = obs.s_color || "pardo";   // la colmenilla solo describe 2 rasgos: se añade uno que no la contradice
  const { g, por } = evalua(obs);
  check(`ejemplar tipo de «${id}»: sale como candidata con ≥ ${D.min_pct} %`, enCand(g, id) && por[id].pct >= D.min_pct, JSON.stringify(por[id]));
  check(`ejemplar tipo de «${id}»: ningún rasgo en contra`, por[id].no.length === 0);
  if (g.candidatas[0] && g.candidatas[0].id === id) { primeros++; if (BASE.includes(id)) primerosBase++; }
}
check("la ficha propia es la primera de la lista en al menos 48 de las 50 de siempre (la clitocibe y el cama-sec se confunden por diseño): la ampliación no desplaza a las antiguas", primerosBase >= 48, String(primerosBase));
check("…y en al menos 290 de las 313 (las demás empatan con una ficha casi igual: es lo esperable con tantas fichas parecidas)", primeros >= 290, String(primeros));

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

// 9) Las 20 fichas añadidas el 15/10/2026: confusiones que deben salir en las listas (coherencia del cálculo, no validación con setas reales)
{
  const NUEVAS = ["hypholoma", "chrysorrheus", "paxillus", "xanthodermus", "equestre", "atramentaria", "emetica", "vinosa", "camperol", "pimpinella",
    "alzinoi", "molleric", "coprinus", "orellana", "llora", "molinera", "fredolic-gros", "pampa", "pollancro", "marcot"];
  check("las 20 fichas nuevas tienen firma y datos de gravedad", NUEVAS.every((i) => D.firmas[i] && D.cartas[i]));
  check("las 7 fichas nuevas de «peligrosas» están marcadas como peligro y la rúsula emética es «no comer» pero no «peligro»",
        ["hypholoma", "chrysorrheus", "paxillus", "xanthodermus", "equestre", "atramentaria"].every((i) => D.cartas[i].peligro) &&
        D.cartas.emetica.grav === "nocom" && !D.cartas.emetica.peligro);
  const vocab = Object.fromEntries(D.dims.map((d) => [d.id, new Set(d.valores.map((v) => v[0]))]));
  check("vocabulario nuevo: violeta (sombrero, láminas, pie), amarillea (corte y látex), fenol, chocolate y negra",
        ["s_color", "h_color", "p_color"].every((d) => vocab[d].has("violeta")) && vocab.corte.has("amarillea") && vocab.latex.has("amarillea") &&
        vocab.olor.has("fenol") && vocab.esporada.has("chocolate") && vocab.esporada.has("negra"));
  // falso níscalo (Lactarius chrysorrheus) y níscalo: el látex que amarillea los separa en las dos direcciones
  const A = evalua(tipico("chrysorrheus")), B = evalua(tipico("rovellons"));
  check("falso níscalo con látex que amarillea: el rovelló queda descartado (no candidata ni dudosa)", !enCand(A.g, "rovellons") && !enDud(A.g, "rovellons") && A.por.rovellons.clave.includes("latex"));
  check("rovelló típico: el falso níscalo queda descartado por el látex", !enCand(B.g, "chrysorrheus") && B.por.chrysorrheus.clave.includes("latex"));
  // confusiones peligrosas conocidas
  const C = evalua(tipico("camperol")), X = evalua(tipico("xanthodermus"));
  check("camperol típico: las amanitas blancas salen como «dudosas» (no se pueden descartar)", enDud(C.g, "amanitas-blancas"));
  check("champiñón amarilleante típico: el camperol sale como candidata y las amanitas blancas como dudosas", enCand(X.g, "camperol") && enDud(X.g, "amanitas-blancas"));
  const V = evalua(tipico("vinosa"));
  check("Amanita vinosa/rubescens típica: la amanita muscaria sale como candidata (confusión descrita en las fichas)", enCand(V.g, "muscaria"));
  const M = evalua(tipico("molinera"));
  check("molinera típica: el entoloma lívido y el moixernó de tardor salen como candidatas, la clitocibe blanca también", enCand(M.g, "entoloma") && enCand(M.g, "moixerno") && enCand(M.g, "clitocybe"));
  const K = evalua(tipico("coprinus")), T = evalua(tipico("atramentaria"));
  check("coprino pelucón típico: el coprino entintado sale como «dudosa»", enDud(K.g, "atramentaria"));
  check("coprino entintado típico: él mismo es candidata con 100 %", enCand(T.g, "atramentaria") && T.por.atramentaria.pct === 100);
  const H = evalua(tipico("hypholoma"));
  check("hifoloma de láminas verdes típico: la seta del olivo sale como «dudosa»", enDud(H.g, "omphalotus"));
  const L = evalua(tipico("pollancro"));
  check("pollancro típico: la galerina marginada sale como candidata (se parece de joven en troncos)", enCand(L.g, "galerina"));
  // fichas con poco peso: no deben llegar a 100 % con solo 3 rasgos sueltos
  const P3 = evalua({ s_color: "pardo", s_forma: "convexo", h_tipo: "laminas" });
  check("con solo 3 rasgos genéricos ninguna ficha nueva llega a 100 %", NUEVAS.every((i) => P3.por[i].pct < 100));
}


// 7) «Bolsa» (volva): en esta guía solo la tienen las amanitas (D.solo_en). Caso real de una persona que marcó «bolsa» y solo
//    le salía la seta enrollada (Paxillus involutus, cuya ficha no dice nada de la base del pie) con un 50 %.
{
  const AM = D.solo_en.p_base.bolsa;
  const AM5 = ["phalloides", "amanitas-blancas", "oureig", "muscaria", "vinosa"];
  const nombraBolsa = (i) => (D.firmas[i].p_base || [[]])[0].includes("bolsa");
  check("solo_en: «bolsa» solo en las fichas que la tienen (las 5 amanitas de siempre + 12 de la ampliación: amanitas, falos y volvarias) y todas existen",
        AM.length === 17 && AM.every((i) => ids.includes(i)) && AM5.every((i) => AM.includes(i)) && new Set(AM).size === AM.length, JSON.stringify(AM));
  check("solo_en: toda ficha que nombra «bolsa» en su firma está en la lista, y las que están en la lista nombran bolsa o son las 5 de siempre",
        ids.filter(nombraBolsa).every((i) => AM.includes(i)) && AM.filter((i) => !AM5.includes(i)).every(nombraBolsa));
  check("solo_en_nota existe para cada rasgo de solo_en", Object.keys(D.solo_en).every((d) => typeof D.solo_en_nota[d] === "string" && D.solo_en_nota[d].length > 10));
  // la captura exacta
  const captura = { s_color: "naranja", s_super: "lisa", s_forma: "conico", h_tipo: "laminas", h_color: "amarillo", p_anillo: "no", p_base: "bolsa", p_color: "blanco" };
  const Cp = evalua(captura);
  check("captura de la persona: la seta enrollada ya NO sale como candidata", !enCand(Cp.g, "paxillus"));
  check("captura: ahora salen candidatas de la ampliación (naranja, sin anillo, con bolsa = amanitas como la A. crocea y la A. fulva) y TODAS tienen bolsa en la guía",
        Cp.g.candidatas.length > 0 && Cp.g.candidatas.every((r) => AM.includes(r.id)) && enCand(Cp.g, "amanita-crocea") && enCand(Cp.g, "amanita-fulva"),
        JSON.stringify(Cp.g.candidatas.map((r) => r.id)));
  check("captura: la seta enrollada queda descartada por la base del pie con el motivo de «solo amanitas»",
        Cp.g.descartadas.some((r) => r.id === "paxillus") && Cp.por.paxillus.excl.join() === "p_base" && Cp.por.paxillus.clave.includes("p_base"));
  check("captura: el porcentaje de la seta enrollada no ha cambiado (sigue 50 %): el descarte no toca el denominador", Cp.por.paxillus.pct === 50);
  check("captura: el ou de reig sigue descartado, pero por el color del pie y el anillo (rasgos de su ficha), no por la bolsa",
        !enCand(Cp.g, "oureig") && Cp.por.oureig.excl.length === 0 && Cp.por.oureig.clave.includes("p_color") && Cp.por.oureig.clave.includes("p_anillo"));
  // ningún otro caso cambia: con «bolsa» las fichas de amanitas no se tocan y todas las demás quedan con la base como clave en contra
  const base = Cp.res;
  check("con «bolsa»: las fichas que la tienen no llevan descarte por la base", AM.every((i) => Cp.por[i].excl.length === 0));
  check("con «bolsa»: las otras 296 fichas llevan el descarte por la base (clave en contra y en «no encaja»)",
        ids.filter((i) => !AM.includes(i)).every((i) => Cp.por[i].excl.join() === "p_base" && Cp.por[i].clave.includes("p_base") && Cp.por[i].no.includes("p_base")));
  check("con «bolsa»: ninguna ficha de las que no tienen bolsa es candidata", ids.filter((i) => !AM.includes(i)).every((i) => !enCand(Cp.g, i)));
  check("con «bolsa»: son 296 las fichas sin bolsa", ids.filter((i) => !AM.includes(i)).length === 296);
  // sin «bolsa» (en blanco, «ensanchada» o «normal») el descarte nunca actúa
  for (const v of [undefined, "ensanchada", "normal"]) {
    const obs = { ...captura }; if (v) obs.p_base = v; else delete obs.p_base;
    const E = evalua(obs);
    check(`sin «bolsa» (${v || "en blanco"}): ninguna ficha tiene descarte por la base`, ids.every((i) => E.por[i].excl.length === 0));
  }
  // el porcentaje de cualquier ficha que no habla de la base no depende de marcar «bolsa»
  const sinBase = { ...captura }; delete sinBase.p_base;
  const S0 = evalua(sinBase);
  check("marcar «bolsa» no cambia el porcentaje de las fichas que no describen la base del pie",
        ids.filter((i) => !D.firmas[i].p_base).every((i) => S0.por[i].pct === Cp.por[i].pct));
  // el ou de reig de manual sigue siendo el primero con 100 %
  const OR = evalua(tipico("oureig"));
  check("ou de reig de manual (con bolsa): primero y con 100 %", OR.g.candidatas[0].id === "oureig" && OR.por.oureig.pct === 100);
  // una peligrosa que no es amanita y encaja del todo salvo la bolsa: sigue avisando como «dudosa» (no se esconde)
  const GA = tipico("galerina"); GA.p_base = "bolsa";
  const Ga = evalua(GA);
  check("galerina típica pero con «bolsa»: no es candidata, sigue saliendo como «dudosa» (peligrosa que casi encaja)", !enCand(Ga.g, "galerina") && enDud(Ga.g, "galerina"));
  // un rasgo de la propia ficha manda: ninguna ficha del conjunto pierde su valor si ella misma lo lista
  check("si la propia ficha lista el valor marcado, no se descarta por solo_en (comprobación de la regla)",
        ids.every((i) => !(D.firmas[i].p_base && D.firmas[i].p_base[0].includes("bolsa")) || AM.includes(i)));
}

// 10) Ampliación del 16/10/2026: 263 fichas más (coherencia del cálculo con las fichas nuevas, no validación con setas reales)
{
  check("las 263 fichas nuevas describen al menos 2 rasgos y tienen al menos uno clave",
        EXTRA.every((i) => Object.keys(D.firmas[i]).length >= 2 && Object.values(D.firmas[i]).some(([, w]) => w === 3)));
  const peligroExtra = EXTRA.filter((i) => D.cartas[i].peligro);
  check("fichas nuevas: 45 de gravedad «peligro» (43 tóxicas + 2 muy tóxicas); ninguna nueva marcada «mortal» (ninguna fuente consultada lo dice de ellas)",
        peligroExtra.length === 45 && EXTRA.every((i) => D.cartas[i].grav !== "mortal") && EXTRA.filter((i) => D.cartas[i].grav === "muyt").length === 2,
        String(peligroExtra.length));
  check("fichas nuevas: 44 «no comestible» (no cuentan como peligro) y 174 sin gravedad propia (ok)",
        EXTRA.filter((i) => D.cartas[i].grav === "nocom").length === 44 && EXTRA.filter((i) => D.cartas[i].grav === "ok").length === 174);
  // Parecidos que las propias fichas nuevas citan como el peligro principal
  const A = evalua(tipico("amanita-citrina"));
  check("falsa oronja (A. citrina) típica: la oronja verde mortal sale como candidata (la ficha dice que ese es su mayor peligro)", enCand(A.g, "phalloides") && A.por.phalloides.pct >= 80, JSON.stringify(A.por.phalloides));
  const Ar = evalua(tipico("agaricus-arvensis"));
  check("Agaricus arvensis típico: el camperol sale como candidata y las amanitas blancas siguen apareciendo (candidata o dudosa)",
        enCand(Ar.g, "camperol") && (enCand(Ar.g, "amanitas-blancas") || enDud(Ar.g, "amanitas-blancas")), JSON.stringify(Ar.g.dudosas.map((r) => r.id)));
  const Lc = evalua(tipico("lepiota-clypeolaria"));
  check("Lepiota clypeolaria típica: la lepiota mortal y las amanitas blancas siguen apareciendo (candidata o dudosa)",
        (enCand(Lc.g, "lepiota") || enDud(Lc.g, "lepiota")) && (enCand(Lc.g, "amanitas-blancas") || enDud(Lc.g, "amanitas-blancas")));
  const Km = evalua(tipico("kuehneromyces-mutabilis"));
  check("Kuehneromyces mutabilis típica: la galerina mortal sale (candidata o dudosa), que es la confusión clásica de las setas de mechón sobre madera",
        enCand(Km.g, "galerina") || enDud(Km.g, "galerina"), JSON.stringify(Km.por.galerina));
  // nada llega a 100 con solo 3 rasgos genéricos
  const P3x = evalua({ s_color: "pardo", s_forma: "convexo", h_tipo: "laminas" });
  check("con solo 3 rasgos genéricos ninguna ficha de la ampliación llega a 100 %", EXTRA.every((i) => P3x.por[i].pct < 100));
  // «láminas» contra «poros»: sigue sin colar peligrosas de láminas cuando se ven poros (también con las nuevas)
  const Ce = evalua({ ...tipico("cep") });
  check("cep típico: ninguna peligrosa (nueva o antigua) sale como dudosa por tener poros en contra", Ce.g.dudosas.every((r) => !r.clave.includes("h_tipo")));
}

console.log(`Rasgos: ${ok} comprobaciones OK, ${bad} fallos`);
process.exit(bad ? 1 : 0);
