"""Genera web/guia.html (guía de identificación) a partir de los datos de guia_datos.py.

Uso, desde la raíz del proyecto:   python3 tools/generar_guia.py
Para sacar el catálogo que usa la identificación por foto del Worker:   python3 tools/generar_guia.py --catalogo

La guía es una sola página (sin librerías externas). Las fichas son desplegables; las fotos las pone el navegador
al abrirla, leyendo web/fotos/creditos.json (que genera tools/descargar_fotos.py). Si no hay fotos, la guía
funciona igual, solo sin ellas.

IMPORTANTE: el texto lo ha redactado una IA a partir de conocimiento micológico general y de la consulta
(15/10/2026) de fuentes públicas (trobarbolets.cat y bolets.app para contrastar qué confusiones peligrosas
importan). NO ha sido revisado por ningún micólogo.
Regla de diseño: la guía ayuda a DESCARTAR y a saber qué comprobar; nunca dice "esto se puede comer".
"""
import html
import json
import os
import sys

REVISION = "15/10/2026"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guia_datos import PELIGROSAS, FICHAS, NOMBRES  # noqa: E402

WORKER_URL = "https://bolets-hallazgos.shicoars.workers.dev/"

SIETE_PASOS = [
    ("Recógela ENTERA", "Excava alrededor de la base, no la cortes por el pie: ahí está la volva (la bolsa) de las Amanita. Recoge varios ejemplares de distinta edad y fotografía el sitio."),
    ("Tamaño y silueta", "Fíjate en el tamaño, en si es joven o vieja y en si crece suelta, en grupo o en mechón."),
    ("Mira debajo del sombrero", "¿Láminas, tubos con poros, pliegues, púas o liso? ¿De qué color? ¿Cambia de color al tocarlo?"),
    ("El pie", "Forma, red, anillo y base (bulbo, bolsa, enterrada). ¿Hueco o macizo?"),
    ("Córtala", "Color de la carne y si cambia (azul, rojo, amarillo). Si sale látex (leche), su color. Olor."),
    ("Esporada", "Pon el sombrero con las láminas hacia abajo sobre un papel mitad blanco y mitad negro y déjalo unas horas. Color del polvo: blanco, crema, rosa, marrón óxido o negro. Cambia mucho el diagnóstico."),
    ("Hábitat y época", "Árbol cercano, suelo, madera o prado, altitud y mes. Si UN solo rasgo no cuadra, descártala."),
]

MITOS = [
    "«Si la comen los bichos o las babosas, es buena.» Falso: muchas setas mortales las comen.",
    "«La cuchara de plata, el ajo o el vinagre detectan las tóxicas.» Falso.",
    "«Pelar el sombrero, hervirla o congelarla la hace segura.» Falso: las amatoxinas resisten el calor.",
    "«Si la he comido otros años, es buena.» Una confusión con una especie mortal solo hace falta una vez.",
    "«Una foto o una aplicación bastan para saberlo.» Falso: ninguna aplicación puede garantizarlo.",
]

ETIQUETAS = {
    "mortal": ("MORTAL", "b-mortal"),
    "muyt": ("MUY TÓXICA", "b-muyt"),
    "toxica": ("TÓXICA", "b-toxica"),
    "nocom": ("NO COMESTIBLE", "b-nocom"),
    "ok": ("comestible", "b-ok"),
}
RIESGO = {"bajo": "bajo", "medio": "medio", "alto": "alto"}


def e(s):
    return html.escape(s, quote=True)


def ul(items, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f"<ul{c}>" + "".join(f"<li>{e(i)}</li>" for i in items) + "</ul>"


def badge(kind):
    txt, cls = ETIQUETAS[kind]
    return f'<span class="badge {cls}">{txt}</span>'


def nombres_html(clave):
    n = NOMBRES.get(clave)
    if not n:
        return "", ""
    return (f'<span class="sci">También se le llama: {e(", ".join(n))}</span>', " " + " ".join(n))


def resumen(cid, nombre_html, cien):
    """Cabecera de una ficha desplegable: miniatura (la pone el navegador), nombre y nombre científico."""
    return (
        f'<summary><span class="thumb" data-thumb="{cid}"><span class="ph">🍄</span></span>'
        f'<span class="ttl"><span class="nm">{nombre_html}</span><span class="sci">{e(cien)}</span></span>'
        f'<span class="chev" aria-hidden="true"></span></summary>'
    )


def render_peligrosa(p):
    pid, nombre, cien, grav, reco, confunde = p
    nom_html, nom_busca = nombres_html(pid)
    return f"""
<details class="card danger" id="{pid}" data-kind="peligrosa" data-search="{e((nombre + ' ' + cien + nom_busca).lower())}">
  {resumen(pid, e(nombre) + ' ' + badge(grav), cien)}
  <div class="body">
    <div class="fotos" data-fotos="{pid}"></div>
    {nom_html}
    <div class="sec" data-res><h4>Cómo reconocerla</h4>{ul(reco)}</div>
    <div class="sec" data-res><h4>Con qué se confunde</h4><p>{e(confunde)}</p></div>
  </div>
</details>"""


def render_ficha(f):
    cid = f["ids"][0]
    anchors = "".join(f'<a id="{i}"></a>' for i in f["ids"][1:])
    conf = "".join(
        f"<li><strong>{e(n)}</strong> {badge(k)} — {e(t)}</li>" for n, k, t in f["confunde"]
    )
    mapa = "" if f["mapa"] else ' <span class="badge b-nomap">no está en el mapa</span>'
    nom_html, nom_busca = nombres_html(cid)
    search = (f["nombre"] + " " + f["cien"] + nom_busca).lower()
    return f"""
{anchors}<details class="card" id="{cid}" data-kind="ficha" data-search="{e(search)}">
  {resumen(cid, e(f['nombre']) + mapa, f['cien'])}
  <div class="body">
    <div class="fotos" data-fotos="{cid}"></div>
    {nom_html}
    <p class="risk risk-{f['riesgo']}">Riesgo de confusión: <strong>{RIESGO[f['riesgo']]}</strong></p>
    <h4>Tiene que cumplir TODO esto</h4>
    {ul(f['cumple'])}
    <div class="sec" data-res><h4>Descártala si ves…</h4>{ul(f['descarta'])}</div>
    <div class="sec" data-res><h4>Se confunde con</h4><ul>{conf}</ul></div>
    <h4>Dónde y cuándo</h4>
    <p>{e(f['donde'])}</p>
  </div>
</details>"""


def catalogo_ident():
    """Lista (id, nombre, científico) de todas las fichas: es lo que el Worker enseña al modelo de visión."""
    cat = [(p[0], p[1], p[2]) for p in PELIGROSAS]
    cat += [(f["ids"][0], f["nombre"], f["cien"]) for f in FICHAS]
    return cat


def catalogo_js():
    filas = ",\n".join("  " + json.dumps(list(c), ensure_ascii=False) for c in catalogo_ident())
    return "const IDENT_CATALOGO = [\n" + filas + ",\n];"


CSS = r"""
  :root {
    --bg: #f7f6f2; --card: #ffffff; --text: #1a1a18; --muted: #5f5e5a; --line: rgba(11,11,11,.12);
    --green: #1D9E75; --green-bg: #E1F5EE; --green-text: #04342C;
    --red: #B3261E; --red-bg: #FCE8E6; --red-text: #5C0F0A;
    --amber: #EF9F27; --amber-bg: #FAEEDA; --amber-text: #412402;
    --gray-bg: #EFEEE8; --radius: 12px;
  }
  * { box-sizing: border-box; }
  body { margin: 0; padding: 0 0 60px; background: var(--bg); color: var(--text);
         font-family: -apple-system, "Segoe UI", Roboto, sans-serif; font-size: 16px; line-height: 1.5; }
  .top-alert { background: var(--red); color: #fff; padding: 7px 14px; font-size: 13px; font-weight: 600; text-align: center; }
  .wrap { max-width: 760px; margin: 0 auto; padding: 12px 14px 0; }
  h1 { font-size: 24px; margin: 10px 0 2px; }
  h2 { font-size: 19px; margin: 22px 0 8px; }
  h4 { font-size: 13px; margin: 14px 0 4px; text-transform: uppercase; letter-spacing: .03em; color: var(--muted); }
  .sub { color: var(--muted); font-size: 14px; margin: 0 0 10px; }
  .sci { display: block; font-size: 13px; font-weight: 400; font-style: italic; color: var(--muted); margin-top: 1px; }
  .box { border-radius: var(--radius); padding: 12px 14px; margin: 12px 0; }
  .box-green { background: var(--green-bg); color: var(--green-text); border: 1px solid #A9DCC9; }
  .box-amber { background: var(--amber-bg); color: var(--amber-text); border: 1px solid #EBC789; }
  .box ul, .body ul { margin: 4px 0 4px 20px; padding: 0; }
  .box li, .body li { margin: 3px 0; }
  .box p { margin: 6px 0; }
  .back { display: inline-block; margin: 6px 0 0; font-size: 14px; color: var(--green); }

  /* Identificar con foto */
  .idbox h2 { margin: 0 0 4px; }
  .idbtns { display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0 4px; }
  .btn { display: inline-block; padding: 12px 16px; border-radius: 10px; background: var(--green); color: #fff;
         font-weight: 600; font-size: 15px; cursor: pointer; }
  .btn-sec { background: #fff; color: var(--green-text); border: 1px solid #A9DCC9; }
  #idres { margin-top: 10px; }
  #idres .preview { width: 100%; max-height: 260px; object-fit: contain; background: #fff; border-radius: 10px; border: 1px solid var(--line); }
  #idres .msg { margin: 8px 0; font-size: 15px; }
  #idres .msg.err { color: var(--red-text); background: var(--red-bg); padding: 8px 10px; border-radius: 8px; }
  #idres .cand { background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; margin: 8px 0; color: var(--text); }
  #idres .cand .nm { font-weight: 700; }
  #idres .cand .why { font-size: 14px; color: var(--muted); margin: 3px 0 6px; }
  #idres .cand .sec h4 { margin-top: 8px; }
  #idres .cand ul { margin: 2px 0 2px 18px; padding: 0; font-size: 14px; }
  #idres .aviso { font-size: 13px; color: var(--muted); margin-top: 8px; }

  input[type=search] { width: 100%; padding: 12px; border: 1px solid var(--line); border-radius: var(--radius);
                       font-size: 16px; background: #fff; }
  .tabs { display: flex; gap: 8px; margin: 10px 0; flex-wrap: wrap; }
  .tab { flex: 1 1 auto; padding: 10px 12px; border: 1px solid var(--line); border-radius: var(--radius);
         background: #fff; font-size: 14px; cursor: pointer; font-family: inherit; }
  .tab.on { background: var(--green); color: #fff; border-color: var(--green); }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 6px 0 12px; }
  .chip { padding: 5px 10px; border-radius: 999px; background: var(--green-bg); color: var(--green-text);
          text-decoration: none; font-size: 13px; display: inline-block; }
  .chip-danger { background: var(--red-bg); color: var(--red-text); }

  /* Fichas desplegables */
  .card { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius);
          margin: 10px 0; scroll-margin-top: 10px; overflow: hidden; }
  .card.danger { border-left: 5px solid var(--red); }
  .card > summary { list-style: none; display: flex; align-items: center; gap: 12px; padding: 10px 12px; cursor: pointer; }
  .card > summary::-webkit-details-marker { display: none; }
  .card > summary:active { background: var(--gray-bg); }
  .thumb { flex: 0 0 60px; width: 60px; height: 60px; border-radius: 10px; background: var(--gray-bg); overflow: hidden;
           display: flex; align-items: center; justify-content: center; }
  .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .thumb .ph { font-size: 26px; opacity: .55; }
  .ttl { flex: 1 1 auto; min-width: 0; font-size: 17px; font-weight: 700; line-height: 1.25; }
  .ttl .sci { font-weight: 400; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .body > .sci { margin-top: 8px; }
  .chev { flex: 0 0 auto; width: 10px; height: 10px; border-right: 2px solid var(--muted); border-bottom: 2px solid var(--muted);
          transform: rotate(45deg); margin: 0 6px 4px 0; transition: transform .15s; }
  .card[open] > summary .chev { transform: rotate(-135deg); margin-bottom: -4px; }
  .card[open] > summary { border-bottom: 1px solid var(--line); }
  .body { padding: 4px 14px 14px; }
  .fotos { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 8px; margin: 10px 0 2px; }
  .fotos:empty { display: none; }
  .fotos figure { margin: 0; }
  .fotos img { width: 100%; height: auto; display: block; border-radius: 8px; background: var(--gray-bg); }
  .fotos figcaption { font-size: 11px; color: var(--muted); margin-top: 3px; line-height: 1.3; }
  .fotos figcaption a { color: var(--muted); }
  .badge { display: inline-block; vertical-align: middle; font-size: 11px; font-weight: 700; padding: 2px 7px;
           border-radius: 999px; margin-left: 4px; letter-spacing: .02em; }
  .b-mortal { background: #7A0C05; color: #fff; }
  .b-muyt { background: var(--red); color: #fff; }
  .b-toxica { background: #E8743B; color: #fff; }
  .b-nocom { background: #6b6a65; color: #fff; }
  .b-ok { background: var(--green); color: #fff; }
  .b-nomap { background: var(--gray-bg); color: var(--muted); font-weight: 600; }
  .risk { font-size: 13px; margin: 8px 0 0; color: var(--muted); }
  .risk-alto strong { color: var(--red); }
  .risk-medio strong { color: #B26A00; }
  .risk-bajo strong { color: var(--green); }
  a[id] { scroll-margin-top: 10px; }
  .hidden { display: none !important; }
  details.mini { margin: 10px 0; background: #fff; border: 1px solid var(--line); border-radius: var(--radius); padding: 10px 14px; }
  details.mini > summary { cursor: pointer; font-weight: 600; }
  details.mini ol, details.mini ul { margin: 8px 0 2px 20px; padding: 0; }
  details.mini li { margin: 4px 0; }
  .foot { font-size: 12px; color: var(--muted); margin-top: 24px; }
  #empty { display: none; padding: 16px; text-align: center; color: var(--muted); }
"""

JS = r"""
// Registra el service worker (guarda esta página y sus fotos para verlas sin cobertura). Si falla, la guía funciona igual con conexión.
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('sw.js').catch(function () {});
  });
}
(function () {
  var WORKER = '@@WORKER@@';
  var TOKEN_KEY = 'bolets_session_token';
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var porId = {};
  cards.forEach(function (c) { porId[c.id] = c; });

  function $(id) { return document.getElementById(id); }
  function norm(s) { return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); }
  function el(tag, cls, txt) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (txt != null) n.textContent = txt;
    return n;
  }

  // ---------- Abrir la ficha que pide el enlace (#cep, #phalloides...) ----------
  function fichaDeHash() {
    var id = ''; try { id = decodeURIComponent((location.hash || '').slice(1)); } catch (e) { return null; }
    if (!id) return null;
    var x = document.getElementById(id);
    if (!x) return null;
    if (x.tagName === 'DETAILS') return x;
    var d = x.closest('details');
    if (d) return d;
    var sig = x.nextElementSibling;   // alias de una ficha compartida (#pinetell → rovellons; #cepfosc y #cepestiu → ceps)
    while (sig && sig.tagName === 'A') sig = sig.nextElementSibling;
    return sig && sig.tagName === 'DETAILS' ? sig : null;
  }
  function abrirPorHash() {
    var d = fichaDeHash();
    if (!d) return;
    d.classList.remove('hidden');
    d.open = true;
    setTimeout(function () { d.scrollIntoView({ block: 'start' }); }, 30);
  }
  window.addEventListener('hashchange', abrirPorHash);
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest ? ev.target.closest('a.chip') : null;
    if (a) setTimeout(abrirPorHash, 0);   // por si el enlace apunta a la misma ficha que ya estaba en la barra
  });
  abrirPorHash();

  // ---------- Fotos (de fotos/creditos.json; si no hay, la guía queda sin fotos) ----------
  function pintaFotos(cred) {
    cards.forEach(function (card) {
      var lista = cred[card.id];
      if (!lista || !lista.length) return;
      var thumb = card.querySelector('[data-thumb]');
      var cont = card.querySelector('[data-fotos]');
      lista.forEach(function (f, i) {
        if (i === 0 && thumb) {
          var t = new Image();
          t.alt = '';
          t.onload = function () { thumb.textContent = ''; thumb.appendChild(t); };
          t.src = f.f;
        }
        if (!cont) return;
        var fig = el('figure');
        var im = new Image();
        im.alt = f.sp || '';
        im.onerror = function () { fig.parentNode && fig.parentNode.removeChild(fig); };
        im.src = f.f;
        fig.appendChild(im);
        var cap = el('figcaption');
        cap.appendChild(document.createTextNode((f.sp ? f.sp + ' · ' : '') + 'Foto: ' + (f.autor || 'desconocido') + ' · '));
        if (f.pagina && /^https:\/\/commons\.wikimedia\.org\//.test(f.pagina)) {
          var a = el('a', null, f.lic || 'licencia');
          a.href = f.pagina; a.target = '_blank'; a.rel = 'noopener';
          cap.appendChild(a);
        } else {
          cap.appendChild(document.createTextNode(f.lic || ''));
        }
        fig.appendChild(cap);
        cont.appendChild(fig);
      });
    });
  }
  fetch('fotos/creditos.json').then(function (r) { return r.ok ? r.json() : null; })
    .then(function (c) { if (c) pintaFotos(c); }).catch(function () {});

  // ---------- Buscar y filtrar ----------
  var q = $('q');
  var tabs = document.querySelectorAll('.tab');
  var mode = 'all';
  function apply() {
    var term = norm(q.value.trim());
    var shown = 0, shownP = 0, shownF = 0;
    cards.forEach(function (c) {
      var kind = c.getAttribute('data-kind');
      var okMode = mode === 'all' || mode === kind;
      var okTerm = !term || norm(c.getAttribute('data-search')).indexOf(term) !== -1;
      var show = okMode && okTerm;
      c.classList.toggle('hidden', !show);
      if (show) { shown++; if (kind === 'peligrosa') shownP++; else shownF++; }
    });
    $('sec-peligrosas').classList.toggle('hidden', shownP === 0);
    $('sec-fichas').classList.toggle('hidden', shownF === 0);
    $('empty').style.display = shown === 0 ? 'block' : 'none';
  }
  q.addEventListener('input', apply);
  tabs.forEach(function (t) {
    t.addEventListener('click', function () {
      tabs.forEach(function (x) { x.classList.remove('on'); });
      t.classList.add('on');
      mode = t.getAttribute('data-f');
      apply();
    });
  });

  // ---------- Identificar con una foto ----------
  var box = $('idres');
  function token() {
    try { return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY) || ''; } catch (e) { return ''; }
  }
  function mensaje(texto, error) {
    var m = el('p', 'msg' + (error ? ' err' : ''), texto);
    box.appendChild(m);
    return m;
  }
  function reducir(file, lado) {
    return new Promise(function (resolve, reject) {
      var url = URL.createObjectURL(file);
      var img = new Image();
      img.onload = function () {
        var k = Math.min(1, lado / Math.max(img.naturalWidth, img.naturalHeight));
        var c = document.createElement('canvas');
        c.width = Math.max(1, Math.round(img.naturalWidth * k));
        c.height = Math.max(1, Math.round(img.naturalHeight * k));
        c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
        URL.revokeObjectURL(url);
        resolve(c.toDataURL('image/jpeg', 0.82));
      };
      img.onerror = function () { URL.revokeObjectURL(url); reject(new Error('No he podido leer la foto.')); };
      img.src = url;
    });
  }
  function lista(items) {
    var u = el('ul');
    items.forEach(function (t) { u.appendChild(el('li', null, t)); });
    return u;
  }
  function pinta(res) {
    if (res.se_ve_seta === false) {
      mensaje('No parece que haya una seta en la foto. Prueba con otra, de cerca y con buena luz.', true);
      return;
    }
    if (res.rasgos && res.rasgos.length) {
      box.appendChild(el('h4', null, 'Lo que se ve en la foto'));
      box.appendChild(lista(res.rasgos));
    }
    var cands = (res.candidatas || []).filter(function (c) { return porId[c.id]; });
    if (!cands.length) {
      mensaje('No veo una candidata clara entre las fichas. Mira las fichas por tu cuenta o prueba con otra foto (por debajo del sombrero y de la base del pie).');
    } else {
      box.appendChild(el('h4', null, 'Candidatas para comparar'));
      cands.forEach(function (c) {
        var card = porId[c.id];
        var d = el('div', 'cand');
        var nm = card.querySelector('.nm');
        var cab = el('div', 'nm');
        if (nm) cab.innerHTML = nm.innerHTML;
        d.appendChild(cab);
        var sci = card.querySelector('.ttl > .sci');
        if (sci) d.appendChild(el('div', 'sci', sci.textContent));
        if (c.motivo) d.appendChild(el('div', 'why', c.motivo));
        card.querySelectorAll('.sec[data-res]').forEach(function (s) { d.appendChild(s.cloneNode(true)); });
        var ab = el('a', 'chip', 'Abrir la ficha con fotos');
        ab.href = '#' + card.id;
        d.appendChild(ab);
        box.appendChild(d);
      });
    }
    if (res.falta_ver && res.falta_ver.length) {
      box.appendChild(el('h4', null, 'Lo que la foto no enseña y hay que comprobar'));
      box.appendChild(lista(res.falta_ver));
    }
    box.appendChild(el('p', 'aviso', 'Es una sugerencia automática de un modelo de IA general: puede equivocarse. Sirve para saber con qué fichas comparar, no para decidir.'));
  }
  function identificar(file) {
    box.textContent = '';
    if (!file) return;
    if (!navigator.onLine) {
      mensaje('Sin cobertura: la identificación por foto necesita internet. Usa las fichas y el método de 7 pasos.', true);
      return;
    }
    var tk = token();
    if (!tk) {
      var m = el('p', 'msg err');
      m.appendChild(document.createTextNode('Para identificar con foto entra primero en el '));
      var a = el('a', null, 'predictor'); a.href = 'index.html';
      m.appendChild(a);
      m.appendChild(document.createTextNode(' (te pide el código del email) y vuelve aquí.'));
      box.appendChild(m);
      return;
    }
    reducir(file, 800).then(function (dataUrl) {
      var pv = el('img', 'preview'); pv.src = dataUrl; pv.alt = 'Tu foto';
      box.appendChild(pv);
      var espera = mensaje('Analizando la foto… (puede tardar unos segundos)');
      var ctl = (typeof AbortController !== 'undefined') ? new AbortController() : null;
      var reloj = setTimeout(function () { if (ctl) ctl.abort(); }, 60000);
      return fetch(WORKER + 'identify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Session-Token': tk },
        body: JSON.stringify({ image: dataUrl }),
        signal: ctl ? ctl.signal : undefined
      }).then(function (r) {
        clearTimeout(reloj);
        return r.json().catch(function () { return {}; }).then(function (j) { return { status: r.status, json: j }; });
      }).then(function (o) {
        if (espera.parentNode) espera.parentNode.removeChild(espera);
        if (o.status === 401) return mensaje('La sesión ha caducado: entra otra vez en el predictor y vuelve.', true);
        if (o.status === 429 || o.status === 503 || o.status >= 400 || !o.json || !o.json.ok) {
          return mensaje((o.json && o.json.error) || 'No se ha podido identificar ahora mismo. Inténtalo más tarde.', true);
        }
        pinta(o.json.resultado || {});
      }).catch(function () {
        if (espera.parentNode) espera.parentNode.removeChild(espera);
        mensaje('No se ha podido contactar con el servidor (¿sin cobertura?). Inténtalo de nuevo.', true);
      });
    }).catch(function (err) {
      mensaje(err && err.message ? err.message : 'No he podido leer la foto.', true);
    });
  }
  ['foto-cam', 'foto-gal'].forEach(function (id) {
    var inp = $(id);
    inp.addEventListener('change', function () {
      var f = inp.files && inp.files[0];
      inp.value = '';
      identificar(f);
    });
  });
})();
"""

PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>Guía de identificación de setas</title>
<meta name="theme-color" content="#1D9E75">
<link rel="manifest" href="manifest.json">
<link rel="icon" type="image/png" href="icon-192.png">
<style>@@CSS@@</style>
</head>
<body>
<div class="top-alert">No comas nada identificado solo con esta guía, una foto o una aplicación.</div>
<div class="wrap">
  <a class="back" href="index.html">← Volver al predictor</a>
  <h1>📖 Guía de identificación</h1>
  <p class="sub">Funciona sin cobertura una vez abierta con conexión (las fotos se guardan al abrirla). Última revisión del texto: @@REVISION@@.</p>

  <section class="box box-green idbox" id="identificar">
    <h2>📷 Identificar con una foto</h2>
    <p>Haz una foto de la seta (mejor entera y vista por debajo) y te digo con qué fichas compararla.</p>
    <div class="idbtns">
      <label class="btn">📷 Hacer foto<input type="file" id="foto-cam" accept="image/*" capture="environment" hidden></label>
      <label class="btn btn-sec">🖼️ Elegir de la galería<input type="file" id="foto-gal" accept="image/*" hidden></label>
    </div>
    <div id="idres" aria-live="polite"></div>
  </section>

  <h2>Buscar</h2>
  <input type="search" id="q" placeholder="Nombre en catalán o científico (rossinyol, Amanita...)" autocomplete="off">
  <div class="tabs">
    <button class="tab on" data-f="all">Todo</button>
    <button class="tab" data-f="peligrosa">⚠️ Peligrosas</button>
    <button class="tab" data-f="ficha">Setas del predictor</button>
  </div>

  <div id="sec-peligrosas">
    <h2>⚠️ Las peligrosas, primero</h2>
    <p class="sub">Las setas con las que más se confunden las comestibles. Toca una para ver cómo es y con qué se confunde.</p>
    <div class="chips">@@INDICE_P@@</div>
    @@PELIGROSAS@@
  </div>

  <div id="sec-fichas">
    <h2>Las setas del predictor</h2>
    <p class="sub">Cada ficha empieza por lo que tiene que cumplir y por lo que la descarta. Las del apartado «no está en el mapa» son de prado y todavía no se predicen.</p>
    <div class="chips">@@INDICE_F@@</div>
    @@FICHAS@@
  </div>

  <p id="empty">No hay resultados.</p>

  <details class="mini">
    <summary>Método de campo en 7 pasos</summary>
    <ol>@@PASOS@@</ol>
  </details>
  <details class="mini">
    <summary>Cosas que se creen y son falsas</summary>
    <ul>@@MITOS@@</ul>
  </details>

  <p class="foot">Fotos: Wikimedia Commons, con licencias libres (el autor y la licencia están debajo de cada foto). Texto de redacción propia, sin revisión micológica independiente. Como referencia de qué confusiones peligrosas importan se consultó (15/10/2026) la página de confusiones de bolets.app. Los nombres comunes cambian de una zona a otra: fíate del nombre científico. La identificación por foto es una sugerencia automática de un modelo de IA general y puede equivocarse.</p>
</div>
<script>@@JS@@</script>
</body>
</html>
"""


def build():
    indice_f = "".join(
        f'<a class="chip" href="#{f["ids"][0]}">{e(f["nombre"].split(" (")[0])}</a>' for f in FICHAS
    )
    indice_p = "".join(
        f'<a class="chip chip-danger" href="#{p[0]}">{e(p[1].split(" (")[0])}</a>' for p in PELIGROSAS
    )
    pasos = "".join(f"<li><strong>{e(t)}.</strong> {e(d)}</li>" for t, d in SIETE_PASOS)
    mitos = "".join(f"<li>{e(m)}</li>" for m in MITOS)
    reemplazos = {
        "@@CSS@@": CSS,
        "@@JS@@": JS.replace("@@WORKER@@", WORKER_URL),
        "@@REVISION@@": REVISION,
        "@@INDICE_P@@": indice_p,
        "@@INDICE_F@@": indice_f,
        "@@PELIGROSAS@@": "".join(render_peligrosa(p) for p in PELIGROSAS),
        "@@FICHAS@@": "".join(render_ficha(f) for f in FICHAS),
        "@@PASOS@@": pasos,
        "@@MITOS@@": mitos,
    }
    out = PLANTILLA
    for k, v in reemplazos.items():
        out = out.replace(k, v)
    assert "@@" not in out, "queda un marcador sin sustituir"
    return out


if __name__ == "__main__":
    if "--catalogo" in sys.argv:
        print(catalogo_js())
        sys.exit(0)
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "guia.html")
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(build())
    print("Escrito", os.path.normpath(destino))
