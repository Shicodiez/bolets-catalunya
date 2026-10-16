"""Ampliación de la guía (16/10/2026): de las 50 fichas de siempre a unas 300.

Aquí NO hay contenido nuevo: este módulo solo convierte las especies de especies_extra.py (+ los nombres en castellano
de nombres_es_wikipedia.py) en las estructuras que ya leían guia_datos, rasgos_datos, nombres_datos y fotos_datos. Esos
cuatro módulos lo importan al final y AÑADEN las fichas nuevas a sus tablas (las 50 de siempre no se tocan).

Qué sale de cada especie de especies_extra.py:
  * tipo «P»  -> una tupla de PELIGROSAS (tóxica o no recomendable por riesgo)
  * tipo «F»  -> un dict de FICHAS (mapa=None: no se predice en el mapa y no se pinta la etiqueta «no está en el mapa»)
  * firma     -> rasgos_datos.FIRMAS
  * nombres   -> nombres_datos.NOMBRES (catalán de la Enciclopèdia Catalana; castellano de es.wikipedia: solo lo que da el texto)
  * foto      -> fotos_datos.FOTOS (un hueco con el nombre científico y sus sinónimos, todo sacado del campo «cien»)
"""
import re

from especies_extra import ESPECIES
from nombres_es_wikipedia import ES_WIKI

ORDEN_GRAV = {"mortal": 0, "muyt": 1, "toxica": 2, "nocom": 3}
IDS_EXTRA = [s["id"] for s in ESPECIES]


def _cap(s):
    return s[:1].upper() + s[1:]


def nombres_de(s):
    """dict(ca, ca_f, es, es_f) de una especie: catalán de especies_extra; castellano de es.wikipedia si la especie no lo trae."""
    ca = list(s["ca"])
    es, es_f = list(s["es"]), s["es_f"]
    if not es and s["id"] in ES_WIKI:
        es, es_f = list(ES_WIKI[s["id"]]), "ESW"
    return dict(ca=ca, ca_f=s["ca_f"] if ca else "", es=es, es_f=es_f if es else "")


def _titulo_propio(s):
    """Título de la ficha: lo que diga la especie; si no, el nombre en castellano (y el catalán entre paréntesis); si no, el catalán; si no, el científico."""
    if s["nombre"]:
        return s["nombre"]
    n = nombres_de(s)
    if n["es"] and n["ca"]:
        return "%s (%s)" % (_cap(n["es"][0]), n["ca"][0])
    if n["es"]:
        return _cap(n["es"][0])
    if n["ca"]:
        return _cap(n["ca"][0])
    return s["cien"]


def titulos(base_titulos=()):
    """{id: título}. Si el título de una ficha nueva coincide con el de otra (de las de siempre o de las nuevas), esa ficha
    nueva se llama por su nombre científico: dos fichas con el mismo título no se distinguirían en la lista."""
    t = {s["id"]: _titulo_propio(s) for s in ESPECIES}
    usados = {}
    for x in base_titulos:
        usados[x.split(" (")[0].lower()] = usados.get(x.split(" (")[0].lower(), 0) + 1
    for s in ESPECIES:
        k = t[s["id"]].split(" (")[0].lower()
        usados[k] = usados.get(k, 0) + 1
    for s in ESPECIES:
        k = t[s["id"]].split(" (")[0].lower()
        if usados[k] > 1:
            t[s["id"]] = s["cien"]
    return t


def peligrosas(base_titulos=()):
    """Tuplas (id, nombre, cien, grav, cómo reconocerla, con qué se confunde) de las especies tipo P, de más a menos grave."""
    t = titulos(base_titulos)
    ps = [s for s in ESPECIES if s["tipo"] == "P"]
    ps.sort(key=lambda s: ORDEN_GRAV[s["grav"]])   # estable: dentro de cada gravedad se queda el orden del archivo (por grupos)
    return [(s["id"], t[s["id"]], s["cien"], s["grav"], list(s["cumple"]), s["confunde"]) for s in ps]


def fichas(base_titulos=()):
    t = titulos(base_titulos)
    return [dict(ids=[s["id"]], nombre=t[s["id"]], cien=s["cien"], mapa=None, riesgo=s["riesgo"], cumple=list(s["cumple"]),
                 descarta=list(s["descarta"]), confunde=list(s["confunde"]), donde=s["donde"])
            for s in ESPECIES if s["tipo"] == "F"]


def firma_a_firmas(firma):
    """En especies_extra.py el rasgo clave se marca con «!» DELANTE del valor (h_tipo="!laminas"); en rasgos_datos.FIRMAS se marca con «!»
    DETRÁS del nombre del rasgo ("h_tipo!": "laminas"). Aquí se pasa de un formato al otro."""
    out = {}
    for k, v in firma.items():
        if v.startswith("!"):
            assert not k.endswith("!"), (k, v)
            out[k + "!"] = v[1:]
        else:
            out[k] = v
    return out


def firmas():
    return {s["id"]: firma_a_firmas(s["firma"]) for s in ESPECIES}


def nombres():
    return {s["id"]: nombres_de(s) for s in ESPECIES}


def _nombres_cientificos(cien):
    """'Imleria badia (Boletus badius, Xerocomus badius)' -> ['Imleria badia', 'Boletus badius', 'Xerocomus badius'];
    'Agaricus sylvaticus (A. silvaticus)' -> ['Agaricus sylvaticus', 'Agaricus silvaticus']; 'A · B' -> ['A', 'B']."""
    out = []
    genero = ""
    partes = re.split(r"\s+·\s+|\s*\(|\)\s*|,\s*", cien)
    for p in partes:
        p = p.strip()
        if not p:
            continue
        m = re.match(r"^([A-Z])\.\s+(.+)$", p)
        if m and genero.startswith(m.group(1)):
            p = genero + " " + m.group(2)
        if not out:
            genero = p.split()[0]
        if p not in out:
            out.append(p)
    return out


def fotos():
    """Un hueco de foto por ficha, con el nombre científico y sus sinónimos (en ese orden) como alternativas."""
    return {s["id"]: [s["foto"] if s["foto"] else _nombres_cientificos(s["cien"])] for s in ESPECIES}


def _clave_nombre(n):
    return re.sub(r"\s*\(.*?\)", "", n).strip().lower()


def anadir_notas_compartidas(NOMBRES, titulos_por_id):
    """Si un nombre popular lo llevan dos o más fichas y al menos una es de la ampliación, ambas lo avisan en su nota
    («fíate del nombre científico»). No toca las notas que ya había: añade una frase detrás."""
    extra = set(IDS_EXTRA)
    for lang in ("ca", "es"):
        idx = {}
        for cid, d in NOMBRES.items():
            for nom in d[lang]:
                idx.setdefault(_clave_nombre(nom), []).append((cid, nom))
        for clave, lista in idx.items():
            ids = sorted({c for c, _ in lista})
            if len(ids) < 2 or not (set(ids) & extra):
                continue
            for cid in ids:
                nom = next(n for c, n in lista if c == cid)
                otros = [titulos_por_id.get(o, o) for o in ids if o != cid]
                frase = "«%s» se usa también para otras fichas de esta guía (%s): fíate del nombre científico." % (clave, "; ".join(otros))
                d = NOMBRES[cid]
                if frase in d.get("nota", ""):
                    continue
                d["nota"] = (d["nota"] + " " + frase).strip() if d.get("nota") else frase
