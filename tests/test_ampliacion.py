"""Auditoría de la ampliación de la guía (16/10/2026): las 263 fichas de tools/especies_extra.py.

No comprueba que lo que dice cada ficha sea cierto (eso solo lo puede hacer una persona que sepa de setas): comprueba reglas
que se pueden automatizar y que protegen a quien lee la guía:
  * que ninguna ficha diga «se puede comer» ni afirme que una seta es comestible sin atribuirlo a una fuente (o con una negación);
  * que cada ficha diga de dónde sale (Wikipedia o Enciclopèdia Catalana);
  * que cada ficha tenga un retrato comparable (≥ 2 rasgos, ≥ 1 clave, valores del vocabulario);
  * que los nombres, los títulos y las fotos sean coherentes con el nombre científico;
  * que la página generada diga que el texto lo ha escrito una IA sin revisión micológica.

Uso (desde la raíz del repositorio):  python3 tests/test_ampliacion.py
"""
import os
import re
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(AQUI, ".."))
sys.path.insert(0, os.path.join(RAIZ, "tools"))

import especies_extra as ee            # noqa: E402
import guia_datos as gd                # noqa: E402
import rasgos_datos as rd              # noqa: E402
import nombres_datos as nd             # noqa: E402
import fotos_datos as fd               # noqa: E402
import nombres_es_wikipedia as esw     # noqa: E402

fallos = []
n_ok = 0


def check(nombre, cond, extra=""):
    global n_ok
    if cond:
        n_ok += 1
        print("OK   " + nombre)
    else:
        fallos.append(nombre)
        print("FAIL " + nombre + (("   [" + str(extra)[:600] + "]") if extra else ""))


def textos(s):
    """Todas las frases de una especie, con el campo del que salen."""
    out = [("cumple", t) for t in s["cumple"]]
    if s["tipo"] == "P":
        out.append(("confunde", s["confunde"]))
    else:
        out += [("descarta", t) for t in s["descarta"]]
        out += [("confunde", " ".join(x for x in c if x)) for c in s["confunde"]]
        out.append(("donde", s["donde"]))
        out.append(("riesgo", s["riesgo"] if isinstance(s["riesgo"], str) else ""))
    return out


def frases(t):
    """Frases separadas por punto (no por «;» ni por «EE. UU.»): la atribución a la fuente suele estar al principio de la frase."""
    return [x.strip() for x in re.split(r"(?<=[.!?])(?<!EE\.)\s+(?=[A-ZÁÉÍÓÚ¿¡«])", t) if x.strip()]


ESP = ee.ESPECIES
F = [s for s in ESP if s["tipo"] == "F"]
P = [s for s in ESP if s["tipo"] == "P"]
base_ids = {p[0] for p in gd.PELIGROSAS_BASE} | {f["ids"][0] for f in gd.FICHAS_BASE}

# ---------- estructura ----------
check("263 especies de la ampliación: 174 fichas para comparar y 89 tóxicas o no recomendables", (len(ESP), len(F), len(P)) == (263, 174, 89), str((len(ESP), len(F), len(P))))
check("ningún id de la ampliación se repite ni coincide con los 50 de siempre", len({s["id"] for s in ESP}) == 263 and not ({s["id"] for s in ESP} & base_ids))
check("313 fichas en total (50 + 263) y 112 peligrosas + 201 fichas", len(gd.PELIGROSAS) + len(gd.FICHAS) == 313 and len(gd.PELIGROSAS) == 112 and len(gd.FICHAS) == 201)
check("cada especie lleva su nombre científico (género + especie) y una fuente declarada (WP = Wikipedia)",
      all(re.match(r"^[A-Z][a-z]+ [a-z\-]+", s["cien"]) and s["src"] for s in ESP), [s["id"] for s in ESP if not re.match(r"^[A-Z][a-z]+ [a-z\-]+", s["cien"])])
check("las tóxicas llevan una gravedad válida y las fichas para comparar un riesgo válido",
      all(s["grav"] in ("mortal", "muyt", "toxica", "nocom") for s in P) and all(s["riesgo"] in ("bajo", "medio", "alto") for s in F),
      [(s["id"], s.get("riesgo")) for s in F if s["riesgo"] not in ("bajo", "medio", "alto")])
check("cada especie tiene al menos 2 frases de «cómo reconocerla» y todas acaban en punto", all(len(s["cumple"]) >= 2 and all(t.rstrip().endswith((".", "»", ")")) for t in s["cumple"]) for s in ESP),
      [s["id"] for s in ESP if len(s["cumple"]) < 2])

# ---------- que no se afirme que algo se puede comer ----------
SE_PUEDE = re.compile(r"se puede comer|se pueden comer|puedes comerl|es seguro comer|sin peligro|no tiene riesgo|(?<!poco )segura para comer", re.I)
quitar_neg = re.compile(r"\b(no|nunca|ni)\s+(se\s+)?(puede|pueden)\s+comer", re.I)
malas = [(s["id"], c, t) for s in ESP for c, t in textos(s) if SE_PUEDE.search(quitar_neg.sub("", t))]
check("ninguna ficha de la ampliación dice «se puede comer» (solo «no se puede comer…»)", not malas, malas[:5])

EDI = re.compile(r"comestible|se come\b|se comen\b|se consume|consumid|culinari|apreciad|sabros|\bdelicios[oa]s?\b|gastronom|excelente|se vende|mercado", re.I)
ATTR = re.compile(r"Wikipedia|Enciclop|\bEC\b|según|segun|dice|dicen|indica|indican|afirma|cita|clasifica|considera|describe|recomienda|guías|guias|fuente|la pone|lo pone|las pone|«", re.I)
NEG = re.compile(r"no se come\b|no comestible|no es comestible|no son comestibles|incomestible|no se recomienda|no te la recomienda|no la recomienda|a refusar|no la comas|no comas|no se puede comer|no se consume|no hay datos|sin datos|ni comestible|tampoco|nada comestible|poco comestible|sin valor", re.I)
sin_atribuir = []
for s in ESP:
    for c, t in textos(s):
        for fr in frases(t):
            if EDI.search(fr) and not ATTR.search(fr) and not NEG.search(fr):
                sin_atribuir.append((s["id"], c, fr))
check("toda frase que habla de comer o de comestibilidad la atribuye a una fuente o la niega (nada de «es comestible» en voz de la guía)", not sin_atribuir, sin_atribuir[:6])

RECETA = re.compile(r"hay que (escald|herv|fre[ií]r|cocer|remoj|quitar)|hervirla|hervirlas|escaldarla|escald[áa]ndola|remojarl|fre[ií]rla|(herv|fre[ií]|cocer|cocin|escald)\w*[^.]{0,60}\d+(-\d+)? minutos|tras salarla|"
                    r"porción pequeña para ver|sobre todo frita|se fr[ií]en|a la plancha|en sartén|guisos|conservarla en|se conserva en sal|para quien empieza", re.I)
recetas = [(s["id"], c, fr) for s in ESP for c, t in textos(s) for fr in frases(t) if RECETA.search(fr)]
check("ninguna ficha de la ampliación da instrucciones de cocinado, de remojo ni de prueba de una porción (la guía identifica, no cocina)", not recetas, recetas[:5])

# ---------- que cada ficha diga de dónde sale ----------
sin_fuente = [s["id"] for s in ESP if not re.search(r"Wikipedia|Enciclop", " ".join(t for _, t in textos(s)))]
check("cada ficha cita Wikipedia o la Enciclopèdia Catalana al menos una vez en su texto", len(sin_fuente) <= 4 and not [x for x in sin_fuente if x not in ("agaricus-bisporus", "tricholoma-album", "hygrocybe-chlorophana", "russula-amethystina")], sin_fuente)
check("las fichas «tóxica» no recomiendan nada: ninguna P empieza diciendo que es buena", not [s["id"] for s in P if re.search(r"\bbuena comestible\b|\bexcelente comestible\b", " ".join(s["cumple"]), re.I)])

# ---------- retratos comparables ----------
vocab = {d[0]: {v[0] for v in d[3]} for d in rd.DIMS}
mal = []
for s in ESP:
    f = rd.FIRMAS[s["id"]]
    claves = [k for k in f if k.endswith("!")]
    if len(f) < 2 or not claves:
        mal.append((s["id"], "pocos rasgos o sin rasgo clave"))
    for k, v in f.items():
        dim = k.rstrip("!")
        if dim not in vocab:
            mal.append((s["id"], "dimensión desconocida " + dim))
        else:
            for x in v.split():
                if x not in vocab[dim]:
                    mal.append((s["id"], dim + "=" + x))
check("cada ficha de la ampliación tiene ≥ 2 rasgos, ≥ 1 rasgo clave y solo valores del vocabulario", not mal, mal[:6])
check("el rasgo clave «h_tipo» (láminas/poros/...) está en todas menos en las que no tienen nada debajo del sombrero", sum(1 for s in ESP if "h_tipo!" in rd.FIRMAS[s["id"]]) >= 200)

# ---------- títulos, nombres y fotos ----------
guia_path = os.path.join(RAIZ, "web", "guia.html")
guia = open(guia_path, encoding="utf-8").read() if os.path.exists(guia_path) else ""
tit = {}
for m in re.finditer(r'<details class="card[^"]*" id="([^"]+)"[^>]*>\s*<summary>(.*?)</summary>', guia, re.S):
    nm = re.search(r'<span class="nm">(.*?)</span>', m.group(2), re.S)
    tit[m.group(1)] = re.sub(r"<[^>]+>", "", nm.group(1)).strip() if nm else ""
check("la página tiene los 313 títulos de ficha", len(tit) == 313 and all(tit.values()), len(tit))
vistos = {}
for k, v in tit.items():
    vistos.setdefault(re.sub(r"\s*\(.*?\)", "", v).lower().replace("&amp;", "&"), []).append(k)
dup = {v: ks for v, ks in vistos.items() if len(ks) > 1 and any(k not in base_ids for k in ks)}
check("ningún título de la ampliación coincide con el de otra ficha (si coincide, se usa el nombre científico)", not dup, dup)


def sci(n):
    return unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode().lower()


bad = []
for s in ESP:
    nm = nd.NOMBRES[s["id"]]
    for lang in ("ca", "es"):
        for x in nm[lang]:
            if len(x) < 3 or x != x.strip() or "  " in x:
                bad.append((s["id"], lang, x))
    if nm["es"] and nm.get("es_f") not in ("ESW", "ES", "WP", "EC", None, "") and not str(nm.get("es_f", "")):
        bad.append((s["id"], "es_f"))
check("los nombres populares tienen forma válida (sin espacios dobles, mínimo 3 letras)", not bad, bad[:5])
check("los nombres en castellano de es.wikipedia (nombres_es_wikipedia.py) están en las fichas de la ampliación y solo en ellas",
      set(esw.ES_WIKI) <= {s["id"] for s in ESP} and all(nd.NOMBRES[i]["es"][:len(v)] == v for i, v in esw.ES_WIKI.items() if not [s for s in ESP if s["id"] == i][0]["es"]),
      [i for i in esw.ES_WIKI if i not in {s["id"] for s in ESP}])
check("las especies sin artículo en es.wikipedia no llevan nombre en castellano inventado", all(not nd.NOMBRES[i]["es"] for i in esw.SIN_ARTICULO if i in nd.NOMBRES and not [s for s in ESP if s["id"] == i and s["es"]][0:1]),
      [i for i in esw.SIN_ARTICULO if nd.NOMBRES.get(i, {}).get("es")])
n_es = sum(1 for s in ESP if nd.NOMBRES[s["id"]]["es"])
n_ca = sum(1 for s in ESP if nd.NOMBRES[s["id"]]["ca"])
print("     (nombres: %d de 263 con nombre en castellano, %d con nombre en catalán)" % (n_es, n_ca))
check("cada ficha de la ampliación tiene un hueco de foto cuyo nombre es el científico (o un sinónimo) de su ficha",
      all(fd.FOTOS[s["id"]] and all(any(x.split()[0] in s["cien"] or x.split()[-1] in s["cien"] for x in alt) for alt in fd.FOTOS[s["id"]]) for s in ESP),
      [s["id"] for s in ESP if not fd.FOTOS.get(s["id"])])
check("los nombres que comparten dos fichas llevan el aviso «fíate del nombre científico»",
      all("fíate del nombre científico" in nd.NOMBRES[i].get("nota", "") for i in {s["id"] for s in ESP}
          for lang in ("ca", "es") for x in nd.NOMBRES[i][lang]
          if sum(1 for j, d in nd.NOMBRES.items() if j != i and any(re.sub(r"\s*\(.*?\)", "", y).strip().lower() == re.sub(r"\s*\(.*?\)", "", x).strip().lower() for y in d[lang])) > 0))

# ---------- avisos de la página ----------
check("la página dice que las fichas añadidas las ha redactado una IA y que no las ha revisado ningún micólogo", "ha redactado una IA" in guia and "ningún micólogo" in guia)
check("la página dice que las fotos de la ampliación no se han revisado a ojo", "no se han revisado a ojo una por una" in guia)
check("la página dice que no da instrucciones de cocinado", "no da instrucciones de cocinado ni de conservación" in guia)
check("la página no dice «se puede comer» (salvo en «no se puede comer…» o en la regla «Nunca dice esta se puede comer»)",
      "se puede comer" not in re.sub(r"Nunca dice «esta se puede comer»|\bno se puede comer", "", guia))
check("la página sigue diciendo que el porcentaje NO es una probabilidad", "NO es la probabilidad" in guia)

print("\n%d OK, %d FAIL" % (n_ok, len(fallos)))
sys.exit(1 if fallos else 0)
