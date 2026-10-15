"""Genera web/guia.html (guía de identificación) a partir de los datos de guia_datos.py.

Uso, desde la raíz del proyecto:   python3 tools/generar_guia.py
Para sacar el vocabulario de rasgos que usa la lectura de fotos del Worker:   python3 tools/generar_guia.py --vocab
Para sacar los datos de rasgos en JSON (los usan las pruebas):                 python3 tools/generar_guia.py --rasgos

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
from guia_datos import PELIGROSAS, FICHAS  # noqa: E402
from nombres_datos import NOMBRES, FUENTES, fuentes_texto, fuente_larga  # noqa: E402
import rasgos_datos as RD  # noqa: E402

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


def nombres_html(clave, cien):
    """Bloque «Nombres» de una ficha: latín, català y castellano (cada uno con «—» si ninguna fuente da nombre) y las fuentes.
    Devuelve (html, texto para el buscador)."""
    n = NOMBRES[clave]

    def fila(etq, txt, lista, vacio):
        if lista:
            return f'<p><span class="nl">{etq}</span>{txt}</p>'
        return f'<p><span class="nl">{etq}</span><span class="nada">{vacio}</span></p>'

    ca = "; ".join(e(x) for x in n["ca"])
    es = "; ".join(e(x) for x in n["es"])
    filas = [
        f'<p><span class="nl">Latín</span><i>{e(cien)}</i></p>',
        fila("Català", ca, n["ca"], "— (ninguna fuente consultada le da nombre en catalán)"),
        fila("Castellano", es, n["es"], "— (ninguna fuente consultada le da nombre en castellano)"),
    ]
    fuentes = []
    if n["ca"]:
        fuentes.append("catalán: " + e(fuentes_texto(n["ca_f"])))
    if n["es"]:
        fuentes.append("castellano: " + e(fuentes_texto(n["es_f"])))
    if fuentes:
        filas.append(f'<p class="nfuente">Nombres según — {"; ".join(fuentes)}.</p>')
    if n.get("nota"):
        filas.append(f'<p class="nnota">{e(n["nota"])}</p>')
    busca = " " + " ".join(n["ca"] + n["es"])
    return f'<div class="nombres">{"".join(filas)}</div>', busca


def resumen(cid, nombre_html, cien):
    """Cabecera de una ficha desplegable: miniatura (la pone el navegador), nombre y nombre científico."""
    return (
        f'<summary><span class="thumb" data-thumb="{cid}"><span class="ph">🍄</span></span>'
        f'<span class="ttl"><span class="nm">{nombre_html}</span><span class="sci">{e(cien)}</span></span>'
        f'<span class="chev" aria-hidden="true"></span></summary>'
    )


def render_peligrosa(p):
    pid, nombre, cien, grav, reco, confunde = p
    nom_html, nom_busca = nombres_html(pid, cien)
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
        f"<li><strong>{e(n)}</strong> {badge(k) + ' ' if k else ''}— {e(t)}</li>" for n, k, t in f["confunde"]
    )
    mapa = "" if f["mapa"] else ' <span class="badge b-nomap">no está en el mapa</span>'
    nom_html, nom_busca = nombres_html(cid, f["cien"])
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


def fuentes_pie():
    """Lista de las fuentes de nombres que se usan de verdad en alguna ficha, con enlace (en el orden de FUENTES)."""
    usados = set()
    for n in NOMBRES.values():
        usados.update((n["ca_f"] + " " + n["es_f"]).split())
    return "; ".join(
        f'<a href="{e(FUENTES[c][1])}" target="_blank" rel="noopener">{e(fuente_larga(c))}</a>' for c in FUENTES if c in usados
    )


def cartas_gravedad():
    """{id de ficha: gravedad}. Las fichas del predictor cuentan como «ok» (comestible con cautela); la guía nunca lo da por seguro."""
    c = {p[0]: p[3] for p in PELIGROSAS}
    c.update({f["ids"][0]: "ok" for f in FICHAS})
    return c


def rasgos_json():
    """Datos de rasgos para el navegador (dims, firmas, gravedad, umbrales). Se incrustan en la página."""
    return RD.exportar(cartas_gravedad())


def slots_html():
    """Los tres huecos de foto: sombrero desde arriba, debajo del sombrero, pie y base."""
    titulos = {
        "sombrero": ("1 · Arriba", "el sombrero visto desde arriba"),
        "debajo": ("2 · Debajo", "láminas, poros o pliegues"),
        "pie": ("3 · Pie y base", "con la base entera"),
    }
    out = []
    for pid in RD.PARTES_IA:
        t, s = titulos[pid]
        out.append(
            f'<div class="slot" data-parte="{pid}">'
            f'<div class="slot-img" data-img><span class="ph">🍄</span></div>'
            f'<div class="slot-t"><strong>{t}</strong><span>{s}</span></div>'
            f'<div class="slot-b">'
            f'<label class="btn btn-s" title="Hacer foto">📷<input type="file" id="foto-{pid}-cam" accept="image/*" capture="environment" hidden></label>'
            f'<label class="btn btn-s btn-sec" title="Elegir de la galería">🖼️<input type="file" id="foto-{pid}-gal" accept="image/*" hidden></label>'
            f'<button type="button" class="btn btn-s btn-sec" data-quitar title="Quitar la foto" hidden>✕</button>'
            f'</div><p class="slot-msg" aria-live="polite"></p></div>'
        )
    return "".join(out)


def panel_html():
    """Panel de rasgos: un desplegable por rasgo. Lo que lea la IA de una foto se escribe aquí y la persona lo puede corregir."""
    out = []
    for pid, titulo, _desc in RD.PARTES:
        filas = []
        for did, parte, etq, vals in RD.DIMS:
            if parte != pid:
                continue
            opts = '<option value="">— no lo sé —</option>' + "".join(
                f'<option value="{v}">{e(largo)}</option>' for v, _corto, largo in vals
            )
            filas.append(
                f'<label class="rasgo"><span class="rl">{e(etq)}</span>'
                f'<select data-dim="{did}">{opts}</select><span class="orig" data-orig></span></label>'
            )
        extra = ""
        if pid == "otros":
            extra = '<p class="sub">Esto no se ve en una foto. Rellénalo solo si lo has comprobado (cortar la seta, olerla, mirar dónde crece...).</p>'
        out.append(f'<fieldset data-parte="{pid}"><legend>{e(titulo)}</legend>{extra}{"".join(filas)}</fieldset>')
    return "".join(out)


def datos_script():
    """Datos de rasgos dentro de la página (JSON). Se escapa «</» para que no cierre la etiqueta script."""
    return json.dumps(rasgos_json(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def puntuar_js():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "puntuar.js"), encoding="utf-8") as fh:
        return fh.read()


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

  /* Identificar con fotos */
  .idbox h2 { margin: 0 0 4px; }
  .btn { display: inline-block; padding: 12px 16px; border-radius: 10px; background: var(--green); color: #fff;
         font-weight: 600; font-size: 15px; cursor: pointer; border: 0; font-family: inherit; }
  .btn-sec { background: #fff; color: var(--green-text); border: 1px solid #A9DCC9; }
  .btn-s { padding: 8px 12px; font-size: 16px; line-height: 1.2; }
  .slots { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 10px 0 4px; }
  .slot { background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 6px; color: var(--text); min-width: 0; }
  .slot-img { aspect-ratio: 1 / 1; border-radius: 8px; background: var(--gray-bg); overflow: hidden; display: flex;
              align-items: center; justify-content: center; }
  .slot-img img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .slot-img .ph { font-size: 30px; opacity: .45; }
  .slot-t { margin: 5px 0 4px; line-height: 1.2; }
  .slot-t strong { display: block; font-size: 13px; }
  .slot-t span { display: block; font-size: 11px; color: var(--muted); }
  .slot-b { display: flex; gap: 4px; flex-wrap: wrap; }
  .slot-b .btn { flex: 1 1 auto; text-align: center; padding: 8px 4px; }
  .slot-msg { font-size: 12px; margin: 5px 0 0; color: var(--muted); line-height: 1.3; }
  .slot-msg:empty { display: none; }
  .slot-msg.err { color: var(--red-text); background: var(--red-bg); padding: 5px 6px; border-radius: 6px; }
  .idtools { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0 0; }
  details.rasgos { margin-top: 12px; }
  details.rasgos fieldset { border: 1px solid var(--line); border-radius: 10px; margin: 10px 0 0; padding: 4px 10px 8px; }
  details.rasgos legend { font-size: 13px; font-weight: 700; padding: 0 6px; color: var(--muted); }
  details.rasgos .sub { margin: 4px 0; font-size: 13px; }
  .rasgo { display: grid; grid-template-columns: 1fr; gap: 2px; margin: 8px 0; font-size: 14px; position: relative; }
  .rasgo .rl { font-weight: 600; }
  .rasgo select { width: 100%; padding: 9px 8px; border: 1px solid var(--line); border-radius: 8px; background: #fff;
                  font-size: 15px; font-family: inherit; color: var(--text); }
  .rasgo .orig { position: absolute; right: 2px; top: 0; font-size: 11px; font-weight: 700; color: var(--green-text);
                 background: var(--green-bg); border-radius: 999px; padding: 1px 7px; }
  .rasgo .orig:empty { display: none; }
  #idres { margin-top: 10px; }
  #idres .msg { margin: 8px 0; font-size: 15px; }
  #idres .msg.err { color: var(--red-text); background: var(--red-bg); padding: 8px 10px; border-radius: 8px; }
  #idres .peligro-aviso { background: var(--red-bg); color: var(--red-text); border: 1px solid #E8A09A; border-radius: 10px;
                          padding: 8px 10px; margin: 8px 0; font-size: 14px; font-weight: 600; }
  #idres .cand { background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; margin: 8px 0; color: var(--text); }
  #idres .cand-peligro { border-left: 5px solid var(--red); }
  #idres .cand .nm { font-weight: 700; }
  #idres .cand .pct { font-size: 14px; margin: 5px 0 2px; }
  #idres .cand .pct strong { font-size: 20px; }
  #idres .barra { height: 8px; border-radius: 6px; background: var(--gray-bg); overflow: hidden; }
  #idres .barra span { display: block; height: 100%; background: var(--green); }
  #idres .cand-peligro .barra span { background: var(--red); }
  #idres .cand .rz { list-style: none; margin: 6px 0 2px; padding: 0; font-size: 13px; }
  #idres .cand .rz li { margin: 2px 0; padding-left: 0; }
  #idres .cand .rz li.no { color: var(--red-text); }
  #idres .cand .falta { font-size: 13px; color: var(--muted); margin: 4px 0; }
  #idres .cand .sec h4 { margin-top: 8px; }
  #idres .cand .sec p { font-size: 14px; margin: 2px 0; }
  #idres .cand details.mini { margin: 8px 0 6px; padding: 6px 10px; font-size: 14px; }
  #idres .cand ul { margin: 2px 0 2px 18px; padding: 0; font-size: 14px; }
  #idres .cand ul.rz { margin-left: 0; }
  #idres .que-es { font-size: 13px; background: var(--amber-bg); color: var(--amber-text); border-radius: 8px; padding: 7px 10px; margin: 8px 0; }
  #idres .aviso { font-size: 13px; color: var(--muted); margin-top: 8px; }
  #idres details.mini { font-size: 14px; }
  #idres details.mini li { margin: 3px 0; }

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
  .nombres { margin: 8px 0 4px; padding: 8px 10px; background: #f3f1ea; border-radius: 8px; font-size: 14px; }
  .nombres p { margin: 2px 0; }
  .nombres p:not(.nfuente):not(.nnota) { display: grid; grid-template-columns: 6.4em 1fr; column-gap: 8px; align-items: baseline; }
  .nombres .nl { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .03em; color: var(--muted); }
  .nombres .nada { color: var(--muted); }
  .nombres .nfuente, .nombres .nnota { font-size: 12px; color: var(--muted); margin-top: 4px; }
  .nombres .nnota { color: var(--amber-text); background: var(--amber-bg); border-radius: 6px; padding: 4px 8px; }
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

  // ---------- Identificar con fotos: 3 huecos (arriba / debajo / pie) + panel de rasgos + comparación con las fichas ----------
  // La IA de la foto solo LEE rasgos (opciones cerradas). Quién compara con las fichas y calcula la coincidencia es esta página
  // (Puntuar), así que también funciona sin fotos y sin cobertura: basta con rellenar el panel de rasgos a mano.
  var box = $('idres');
  var DATOS = JSON.parse($('rasgos-datos').textContent);
  var P = window.Puntuar;
  var dimPorId = {};
  DATOS.dims.forEach(function (d) { dimPorId[d.id] = d; });
  var PARTE_TXT = { sombrero: 'sombrero visto desde arriba', debajo: 'debajo del sombrero', pie: 'pie y base' };
  var obs = {};          // rasgo -> { v: valor, src: 'ia' | 'tu' }
  var selects = {};      // rasgo -> <select>
  Array.prototype.forEach.call(document.querySelectorAll('select[data-dim]'), function (s) { selects[s.getAttribute('data-dim')] = s; });

  function token() {
    try { return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY) || ''; } catch (e) { return ''; }
  }
  function nombreValor(dim, v) {
    var d = dimPorId[dim];
    if (d) for (var i = 0; i < d.valores.length; i++) if (d.valores[i][0] === v) return d.valores[i][1];
    return v;
  }
  function valorValido(dim, v) {
    var d = dimPorId[dim];
    if (!d || typeof v !== 'string') return false;
    for (var i = 0; i < d.valores.length; i++) if (d.valores[i][0] === v) return true;
    return false;
  }
  function valores() {
    var o = {};
    Object.keys(obs).forEach(function (k) { o[k] = obs[k].v; });
    return o;
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

  // ----- Resultados -----
  function lista(items, cls) {
    var u = el('ul', cls);
    items.forEach(function (t) { u.appendChild(el('li', null, t)); });
    return u;
  }
  function tarjeta(r, o, abierta) {
    var card = porId[r.id];
    var d = el('div', 'cand' + (r.peligro ? ' cand-peligro' : ''));
    var nm = card.querySelector('.nm');
    var cab = el('div', 'nm');
    if (nm) cab.innerHTML = nm.innerHTML;
    d.appendChild(cab);
    var sci = card.querySelector('.ttl > .sci');
    if (sci) d.appendChild(el('div', 'sci', sci.textContent));
    var pc = el('div', 'pct');
    pc.appendChild(el('strong', null, r.pct + ' %'));
    pc.appendChild(document.createTextNode(' de coincidencia · encajan ' + r.nok + ' de los ' + r.n + ' rasgos que has indicado y que esta ficha describe'));
    d.appendChild(pc);
    var barra = el('div', 'barra'), rel = el('span');
    rel.style.width = Math.max(2, Math.min(100, r.pct)) + '%';
    barra.appendChild(rel);
    d.appendChild(barra);
    var u = el('ul', 'rz');
    r.si.forEach(function (dim) { u.appendChild(el('li', null, '✔ ' + dimPorId[dim].etq + ': ' + nombreValor(dim, o[dim]))); });
    r.no.forEach(function (dim) {
      var esperado = DATOS.firmas[r.id][dim][0].map(function (v) { return nombreValor(dim, v); }).join(' / ');
      u.appendChild(el('li', 'no', '✖ ' + dimPorId[dim].etq + ': tú indicas «' + nombreValor(dim, o[dim]) + '» y la ficha dice «' + esperado + '»'));
    });
    if (u.childNodes.length) d.appendChild(u);
    if (r.falta.length) {
      d.appendChild(el('p', 'falta', 'Sin comprobar aún: ' + r.falta.slice(0, 5).map(function (f) { return dimPorId[f.dim].etq.toLowerCase(); }).join(', ') + (r.falta.length > 5 ? '…' : '') + '.'));
    }
    var det = el('details', 'mini');
    det.open = !!abierta;
    det.appendChild(el('summary', null, card.getAttribute('data-kind') === 'peligrosa' ? 'Cómo reconocerla y con qué se confunde' : 'Lo que la descarta y con qué se confunde'));
    card.querySelectorAll('.sec[data-res]').forEach(function (s) { det.appendChild(s.cloneNode(true)); });
    d.appendChild(det);
    var ab = el('a', 'chip', 'Abrir la ficha con fotos');
    ab.href = '#' + card.id;
    d.appendChild(ab);
    return d;
  }
  function pintaResultados() {
    box.textContent = '';
    var o = valores();
    var n = Object.keys(o).length;
    if (!n) {
      box.appendChild(el('p', 'msg', 'Haz una foto en cualquiera de los tres huecos, o rellena los rasgos de abajo, y te enseño con qué fichas encaja y en qué porcentaje.'));
      return;
    }
    if (n < DATOS.min_rasgos) {
      box.appendChild(el('p', 'msg', 'Tienes ' + n + (n === 1 ? ' rasgo indicado' : ' rasgos indicados') + '. Hacen falta al menos ' + DATOS.min_rasgos + ' para poder comparar: haz más fotos o rellena el panel de rasgos.'));
      return;
    }
    var g = P.agrupar(P.comparar(o, DATOS), n, DATOS);
    box.appendChild(el('p', 'que-es', 'La coincidencia dice qué parte de lo que pide cada ficha encaja con los rasgos que has indicado. NO es la probabilidad de que sea esa seta ni quiere decir que se pueda comer: es una forma de ordenar con qué fichas comparar. Con pocos rasgos no vale casi nada.'));
    if (g.candidatas.some(function (r) { return r.peligro; }) || g.dudosas.length) {
      box.appendChild(el('p', 'peligro-aviso', '⚠️ Entre los resultados hay setas peligrosas. Mientras no las hayas descartado una por una, no la comas.'));
    }
    if (g.candidatas.length) {
      box.appendChild(el('h4', null, 'Fichas que encajan (de más a menos)'));
      g.candidatas.slice(0, 5).forEach(function (r, i) { box.appendChild(tarjeta(r, o, i === 0)); });
    } else if (n < 5) {
      box.appendChild(el('p', 'msg', 'Con tan pocos rasgos todavía no se puede afinar ninguna ficha. Indica más: haz las tres fotos o rellena el panel de rasgos.'));
    } else {
      box.appendChild(el('p', 'msg', 'Con estos rasgos no encaja bien ninguna de las ' + Object.keys(DATOS.firmas).length + ' fichas. Eso NO quiere decir que sea comestible: puede ser una seta que la guía no tiene.'));
    }
    if (g.dudosas.length) {
      box.appendChild(el('h4', null, 'Peligrosas con las que aún no puedes descartar el parecido'));
      box.appendChild(el('p', 'sub', 'Fallan en algún rasgo, pero por lo demás se parecen. Si te has equivocado al indicar ese rasgo, encajarían.'));
      g.dudosas.slice(0, 3).forEach(function (r) { box.appendChild(tarjeta(r, o)); });
    }
    var sig = P.siguientes(g, 4);
    if (sig.length) {
      box.appendChild(el('h4', null, 'Para afinar, comprueba'));
      box.appendChild(lista(sig.map(function (d) { return dimPorId[d].etq; })));
      var ir = el('a', 'chip', 'Ir al panel de rasgos ↓');
      ir.href = '#panel-rasgos';
      ir.addEventListener('click', function () { $('panel-rasgos').open = true; });
      box.appendChild(ir);
    }
    var resto = g.candidatas.slice(5).concat(g.dudosas.slice(3), g.descartadas);
    if (resto.length) {
      var det = el('details', 'mini');
      det.appendChild(el('summary', null, 'Descartadas o con poca coincidencia (' + resto.length + ')'));
      var ul = el('ul');
      resto.forEach(function (r) {
        var card = porId[r.id], nm = card.querySelector('.nm');
        var motivo = r.clave.length
          ? 'no encaja: ' + dimPorId[r.clave[0]].etq.toLowerCase() + ' (la ficha dice «' + DATOS.firmas[r.id][r.clave[0]][0].map(function (v) { return nombreValor(r.clave[0], v); }).join(' / ') + '»)'
          : r.pct + ' % de coincidencia';
        var li = el('li');
        li.appendChild(document.createTextNode((nm ? nm.firstChild.textContent.trim() : r.id) + ' — ' + motivo));
        ul.appendChild(li);
      });
      det.appendChild(ul);
      box.appendChild(det);
    }
    box.appendChild(el('p', 'aviso', 'Los rasgos leídos de las fotos los saca un modelo de IA general y se puede equivocar: corrígelos en el panel. La guía solo tiene ' + Object.keys(DATOS.firmas).length + ' fichas, y su texto no lo ha revisado ningún micólogo.'));
  }

  // ----- Panel de rasgos -----
  function sincronizar() {
    Object.keys(selects).forEach(function (dim) {
      var s = selects[dim];
      s.value = obs[dim] ? obs[dim].v : '';
      var marca = s.parentNode.querySelector('[data-orig]');
      if (marca) marca.textContent = obs[dim] && obs[dim].src === 'ia' ? 'IA' : '';
    });
    var cont = $('n-rasgos');
    if (cont) cont.textContent = Object.keys(obs).length;
  }
  function actualizar() { sincronizar(); pintaResultados(); }
  Object.keys(selects).forEach(function (dim) {
    selects[dim].addEventListener('change', function () {
      if (selects[dim].value) obs[dim] = { v: selects[dim].value, src: 'tu' };
      else delete obs[dim];
      actualizar();
    });
  });
  function quitarIA(parte) {
    DATOS.dims.forEach(function (d) { if (d.parte === parte && obs[d.id] && obs[d.id].src === 'ia') delete obs[d.id]; });
  }
  function aplicarIA(parte, rasgos) {
    var n = 0;
    DATOS.dims.forEach(function (d) {
      if (d.parte !== parte) return;
      var v = rasgos[d.id];
      if (!valorValido(d.id, v)) return;
      if (obs[d.id] && obs[d.id].src === 'tu') return;   // lo que ha puesto la persona no se pisa
      obs[d.id] = { v: v, src: 'ia' };
      n++;
    });
    return n;
  }

  // ----- Huecos de foto -----
  var slots = Array.prototype.slice.call(document.querySelectorAll('.slot'));
  function msgSlot(slot, texto, error) {
    var m = slot.querySelector('.slot-msg');
    m.textContent = texto || '';
    m.className = 'slot-msg' + (error ? ' err' : '');
    return m;
  }
  function ponerMiniatura(slot, dataUrl) {
    var cont = slot.querySelector('[data-img]');
    cont.textContent = '';
    if (dataUrl) {
      var im = new Image();
      im.alt = 'Tu foto';
      im.src = dataUrl;
      cont.appendChild(im);
    } else {
      cont.appendChild(el('span', 'ph', '🍄'));
    }
    slot.querySelector('[data-quitar]').hidden = !dataUrl;
  }
  function recibir(slot, parte, o) {
    if (o.status === 401) return msgSlot(slot, 'La sesión ha caducado: entra otra vez en el predictor y vuelve.', true);
    if (o.status >= 400 || !o.json || !o.json.ok) {
      return msgSlot(slot, (o.json && o.json.error) || 'No se ha podido leer ahora mismo. Inténtalo más tarde.', true);
    }
    var res = o.json.resultado || {};
    if (!res.rasgos || typeof res.rasgos !== 'object' || Array.isArray(res.rasgos)) {
      return msgSlot(slot, 'El Worker de Cloudflare es de la versión anterior: hay que pegar la última versión de worker/index.js.', true);
    }
    quitarIA(parte);
    if (res.se_ve_seta === false) {
      actualizar();
      return msgSlot(slot, 'No parece que haya una seta en esta foto. Prueba con otra, de cerca y con buena luz.', true);
    }
    var vista = res.parte_vista;
    if (PARTE_TXT[vista] && vista !== parte) {
      actualizar();
      return msgSlot(slot, 'Esta foto parece «' + PARTE_TXT[vista] + '», no «' + PARTE_TXT[parte] + '». No la he usado: ponla en su hueco.', true);
    }
    var n = aplicarIA(parte, res.rasgos);
    actualizar();
    msgSlot(slot, n ? 'He leído ' + n + (n === 1 ? ' rasgo' : ' rasgos') + '. Revísalos en el panel.' : 'No he podido leer rasgos claros en esta foto. Indícalos tú en el panel.');
  }
  function leerFoto(slot, file) {
    var parte = slot.getAttribute('data-parte');
    if (!file) return;
    if (!navigator.onLine) {
      msgSlot(slot, 'Sin cobertura: leer fotos necesita internet. El panel de rasgos sí funciona sin cobertura.', true);
      return;
    }
    var tk = token();
    if (!tk) {
      var m = msgSlot(slot, '', true);
      m.appendChild(document.createTextNode('Para leer fotos entra primero en el '));
      var a = el('a', null, 'predictor'); a.href = 'index.html';
      m.appendChild(a);
      m.appendChild(document.createTextNode(' (te pide el código del email) y vuelve.'));
      return;
    }
    slot._gen = (slot._gen || 0) + 1;
    var gen = slot._gen;
    reducir(file, 800).then(function (dataUrl) {
      if (slot._gen !== gen) return;
      ponerMiniatura(slot, dataUrl);
      msgSlot(slot, 'Leyendo la foto… (unos segundos)');
      var ctl = (typeof AbortController !== 'undefined') ? new AbortController() : null;
      var reloj = setTimeout(function () { if (ctl) ctl.abort(); }, 60000);
      return fetch(WORKER + 'identify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Session-Token': tk },
        body: JSON.stringify({ image: dataUrl, parte: parte }),
        signal: ctl ? ctl.signal : undefined
      }).then(function (r) {
        clearTimeout(reloj);
        return r.json().catch(function () { return {}; }).then(function (j) { return { status: r.status, json: j }; });
      }).then(function (o) {
        if (slot._gen !== gen) return;
        recibir(slot, parte, o);
      }).catch(function () {
        clearTimeout(reloj);
        if (slot._gen !== gen) return;
        msgSlot(slot, 'No se ha podido contactar con el servidor (¿sin cobertura?). Inténtalo de nuevo o rellena el panel a mano.', true);
      });
    }).catch(function (err) {
      if (slot._gen !== gen) return;
      msgSlot(slot, err && err.message ? err.message : 'No he podido leer la foto.', true);
    });
  }
  slots.forEach(function (slot) {
    var parte = slot.getAttribute('data-parte');
    Array.prototype.forEach.call(slot.querySelectorAll('input[type=file]'), function (inp) {
      inp.addEventListener('change', function () {
        var f = inp.files && inp.files[0];
        inp.value = '';
        leerFoto(slot, f);
      });
    });
    slot.querySelector('[data-quitar]').addEventListener('click', function () {
      slot._gen = (slot._gen || 0) + 1;
      ponerMiniatura(slot, null);
      msgSlot(slot, '');
      quitarIA(parte);
      actualizar();
    });
  });
  $('btn-reset').addEventListener('click', function () {
    obs = {};
    slots.forEach(function (slot) {
      slot._gen = (slot._gen || 0) + 1;
      ponerMiniatura(slot, null);
      msgSlot(slot, '');
    });
    actualizar();
  });
  actualizar();
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
    <h2>📷 Identificar con fotos</h2>
    <p>Haz hasta 3 fotos de la misma seta (arriba, debajo del sombrero, pie con su base). La aplicación lee los rasgos y los compara con las fichas, con un porcentaje de coincidencia. Lo que lea mal lo corriges abajo, y sin fotos ni cobertura también puedes rellenar los rasgos a mano.</p>
    <div class="slots">@@SLOTS@@</div>
    <div class="idtools"><button type="button" class="btn btn-s btn-sec" id="btn-reset">Borrar todo y empezar de nuevo</button></div>
    <div id="idres" aria-live="polite"></div>
    <details class="mini rasgos" id="panel-rasgos" open>
      <summary>Rasgos de la seta (<span id="n-rasgos">0</span> indicados) · revisa y corrige aquí</summary>
      <p class="sub">Lo que ha leído la IA de las fotos lleva la marca «IA». Si ves algo distinto, cámbialo: lo que pones tú no lo pisa la IA.</p>
      @@PANEL@@
    </details>
  </section>

  <h2>Buscar</h2>
  <input type="search" id="q" placeholder="Nombre en latín, catalán o castellano (rossinyol, níscalo, Amanita...)" autocomplete="off">
  <div class="tabs">
    <button class="tab on" data-f="all">Todo</button>
    <button class="tab" data-f="peligrosa">⚠️ Peligrosas</button>
    <button class="tab" data-f="ficha">Setas buscadas</button>
  </div>

  <div id="sec-peligrosas">
    <h2>⚠️ Las peligrosas, primero</h2>
    <p class="sub">Las setas con las que más se confunden las comestibles. Toca una para ver cómo es y con qué se confunde.</p>
    <div class="chips">@@INDICE_P@@</div>
    @@PELIGROSAS@@
  </div>

  <div id="sec-fichas">
    <h2>Las setas más buscadas</h2>
    <p class="sub">Cada ficha empieza por lo que tiene que cumplir y por lo que la descarta. Las marcadas «no está en el mapa» todavía no las predice el predictor (las de prado y las que aún no tienen datos). Que una ficha esté aquí NO quiere decir que la seta se pueda comer.</p>
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

  <p class="foot">Fotos: Wikimedia Commons, con licencias libres (el autor y la licencia están debajo de cada foto). Texto de redacción propia, sin revisión micológica independiente. Como referencia de qué confusiones peligrosas importan se consultó (15/10/2026) la página de confusiones de bolets.app. Los nombres comunes cambian de una zona a otra: fíate del nombre científico. La lectura de rasgos de las fotos la hace un modelo de IA general y puede equivocarse; el porcentaje de coincidencia no es una probabilidad.</p>
  <p class="foot">Nombres populares (consultados el 15/10/2026; solo se escribe el que aparece en una fuente): @@FUENTES@@.</p>
</div>
<script id="rasgos-datos" type="application/json">@@DATOS@@</script>
<script>@@PUNTUAR@@</script>
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
        "@@SLOTS@@": slots_html(),
        "@@PANEL@@": panel_html(),
        "@@DATOS@@": datos_script(),
        "@@PUNTUAR@@": puntuar_js(),
        "@@JS@@": JS.replace("@@WORKER@@", WORKER_URL),
        "@@REVISION@@": REVISION,
        "@@INDICE_P@@": indice_p,
        "@@INDICE_F@@": indice_f,
        "@@PELIGROSAS@@": "".join(render_peligrosa(p) for p in PELIGROSAS),
        "@@FICHAS@@": "".join(render_ficha(f) for f in FICHAS),
        "@@PASOS@@": pasos,
        "@@MITOS@@": mitos,
        "@@FUENTES@@": fuentes_pie(),
    }
    out = PLANTILLA
    for k, v in reemplazos.items():
        out = out.replace(k, v)
    assert "@@" not in out, "queda un marcador sin sustituir"
    return out


if __name__ == "__main__":
    if "--vocab" in sys.argv:
        print(RD.vocab_js())
        sys.exit(0)
    if "--rasgos" in sys.argv:
        print(json.dumps(rasgos_json(), ensure_ascii=False))
        sys.exit(0)
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "guia.html")
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(build())
    print("Escrito", os.path.normpath(destino))
