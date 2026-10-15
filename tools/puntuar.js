// Comparación de rasgos con las fichas de la guía (la usa web/guia.html; generar_guia.py la copia dentro de la página).
//
// La «coincidencia» de una ficha es: peso de los rasgos que encajan / peso total del retrato de la ficha (con un mínimo
// de min_peso, para que una ficha que solo nombra dos o tres rasgos no llegue a 100 % con solo dos o tres rasgos).
// Es decir, qué parte de lo que pide la ficha está ya confirmada por lo que se ha indicado. Los rasgos clave pesan 3 y los
// normales 1. Un rasgo sin indicar no encaja, pero tampoco descarta: simplemente falta por confirmar. Un rasgo que
// contradice la ficha no suma, y si es clave deja la ficha descartada.
// NO es la probabilidad de que sea esa seta: solo mide cuánto de la ficha se ha confirmado.
//
// Es una función pura (sin DOM) para poder probarla con Node (tests/test_rasgos.mjs) y usarla en el navegador.
(function (root) {
  'use strict';

  // obs = { rasgo: valor }  ·  D = datos exportados por tools/rasgos_datos.py
  function comparar(obs, D) {
    var out = [];
    Object.keys(D.firmas).forEach(function (id) {
      var firma = D.firmas[id], tot = 0, ok = 0, si = [], no = [], clave = [], falta = [];
      Object.keys(firma).forEach(function (dim) {
        var vals = firma[dim][0], w = firma[dim][1], v = obs[dim];
        tot += w;
        if (!v) { falta.push({ dim: dim, w: w }); return; }
        if (vals.indexOf(v) >= 0) { ok += w; si.push(dim); }
        else { no.push(dim); if (w >= 3) clave.push(dim); }
      });
      falta.sort(function (a, b) { return (b.w - a.w) || (a.dim < b.dim ? -1 : 1); });
      var n = si.length + no.length;
      var c = D.cartas[id] || {};
      out.push({
        id: id, n: n, nok: si.length, pct: Math.round(100 * ok / Math.max(tot, D.min_peso || 0)),
        si: si, no: no, clave: clave, falta: falta, peligro: !!c.peligro, grav: c.grav || '',
        dimsFicha: Object.keys(firma).length
      });
    });
    return out;
  }

  // Reparte las fichas en grupos:
  //  candidatas  = ningún rasgo clave en contra, coincidencia >= min_pct y al menos min_encajan rasgos que encajan
  //                (de mayor a menor; a igualdad, primero las peligrosas)
  //  dudosas     = PELIGROSAS que fallan en algún rasgo clave (salvo lo de debajo del sombrero: láminas contra poros no se confunde)
  //                pero por lo demás encajan bastante (>= min_pct_dudosa): no se pueden descartar tan rápido
  //  descartadas = el resto (con al menos min_comparados rasgos comparados)
  //  sinDatos    = fichas con menos de min_comparados rasgos comparables (no se puede decir nada)
  function agrupar(res, nObs, D) {
    var g = { pocosDatos: nObs < D.min_rasgos, candidatas: [], dudosas: [], descartadas: [], sinDatos: 0 };
    if (g.pocosDatos) return g;
    res.forEach(function (r) {
      if (r.n < D.min_comparados) { g.sinDatos++; return; }
      var enough = r.nok >= Math.min(D.min_encajan || 0, r.dimsFicha);
      var buena = r.pct >= D.min_pct && enough;
      if (!r.clave.length && buena) g.candidatas.push(r);
      else if (r.peligro && r.clave.length && r.clave.indexOf('h_tipo') < 0 && r.pct >= (D.min_pct_dudosa || D.min_pct) && enough) g.dudosas.push(r);
      else g.descartadas.push(r);
    });
    var ord = function (a, b) {
      return (b.pct - a.pct) || (b.n - a.n) || ((b.peligro ? 1 : 0) - (a.peligro ? 1 : 0)) || (a.id < b.id ? -1 : 1);
    };
    g.candidatas.sort(ord); g.dudosas.sort(ord); g.descartadas.sort(ord);
    return g;
  }

  // Rasgos que aún no se han indicado y que más ayudarían a decidir entre las primeras fichas.
  function siguientes(g, max) {
    var base = g.candidatas.slice(0, 3).concat(g.dudosas.slice(0, 2));
    // Si no hay candidatas, se mira lo que falta en las fichas más cercanas (sin rasgos clave en contra).
    if (!base.length) base = g.descartadas.filter(function (r) { return !r.clave.length; }).slice(0, 3);
    var top = base;
    var acum = {};
    top.forEach(function (r) { r.falta.forEach(function (f) { acum[f.dim] = (acum[f.dim] || 0) + f.w; }); });
    return Object.keys(acum).sort(function (a, b) { return (acum[b] - acum[a]) || (a < b ? -1 : 1); }).slice(0, max || 4);
  }

  var api = { comparar: comparar, agrupar: agrupar, siguientes: siguientes };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.Puntuar = api;
})(typeof window !== 'undefined' ? window : this);
