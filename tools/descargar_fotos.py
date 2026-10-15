"""Descarga las fotos de la guía desde Wikimedia Commons y las guarda en web/fotos/.

Uso (lo ejecuta el GitHub Action «Descargar fotos de la guía»; no hace falta correrlo a mano):
    python3 tools/descargar_fotos.py

Qué hace, para cada ficha de fotos_datos.FOTOS:
  1. Busca en Wikipedia (en, es, ca, fr, de, it) el artículo del nombre científico y saca la lista de imágenes
     (primero la imagen principal del artículo).
  2. Pide a Commons los datos de cada candidata: licencia, autor, tamaño y la miniatura de 500 px.
  3. Se queda con la primera que sea JPEG, tenga tamaño suficiente y tenga licencia LIBRE (CC BY, CC BY-SA, CC0 o
     dominio público; se rechaza todo lo que lleve NC o ND).
  4. Descarga la miniatura a web/fotos/<id>-<n>.jpg y apunta autor y licencia en web/fotos/creditos.json.
  5. Escribe web/fotos/informe.txt con lo que ha ido bien y lo que no.

Solo usa la librería estándar de Python. Si una especie falla, las demás siguen; si falla una que ya tenía foto,
se conserva la anterior.
"""
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from fotos_datos import FOTOS, FORZAR  # noqa: E402

DESTINO = os.path.normpath(os.path.join(AQUI, "..", "web", "fotos"))
UA = "bolets-catalunya/1.0 (https://github.com/Shicodiez/bolets-catalunya; uso personal) python-urllib"
WIKIS = ["en", "es", "ca", "fr", "de", "it"]
ANCHO = 500            # ancho de la miniatura (Wikimedia solo sirve anchos estándar: 250, 330, 500, 960...)
ANCHO_MIN = 500        # se rechazan fotos originales más pequeñas
MAX_CANDIDATAS = 14    # cuántas imágenes de un artículo se miran como máximo por hueco
PAUSA = 0.35           # segundos entre peticiones (cortesía con Wikimedia)

# Imágenes de interfaz y de relleno que aparecen en los artículos y no son fotos de la seta.
# Se buscan como PALABRA SUELTA (sin letras pegadas) para no descartar, por ejemplo, «Orange_milk_cap» por llevar «range».
_PALABRAS = (
    "logo|icon|symbol|flag|map|range|distribution|ambox|edit|question|disambig|stub|status|portal|crystal|"
    "folder|wikidata|wikispecies|commons|pencil|lock|padlock|nuvola|spore|spores|microscopy|cystidia|basidia|"
    "diagram|drawing|illustration|painting|plate|chemical|structure|cladogram|phylogeny"
)
NO_FOTO = re.compile(r"(?<![a-z])(?:" + _PALABRAS + r")(?![a-z])|\.(?:svg|png|gif|tiff?)$", re.I)


def peticion(url, binario=False, intentos=4):
    """GET con reintentos. Devuelve JSON (dict) o bytes. Lanza la última excepción si no hay manera."""
    ultimo = None
    for n in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=30) as r:
                datos = r.read()
            return datos if binario else json.loads(datos.decode("utf-8"))
        except urllib.error.HTTPError as e:
            ultimo = e
            if e.code in (404, 400, 403):   # no tiene sentido reintentar
                break
            time.sleep(2 * (n + 1))
        except Exception as e:  # red, JSON roto...
            ultimo = e
            time.sleep(2 * (n + 1))
    raise ultimo


def api(host, params):
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode({**params, "format": "json", "formatversion": "2"})
    time.sleep(PAUSA)
    return peticion(url)


def candidatas_de_articulo(wiki, titulo):
    """Nombres de archivo («File:...») del artículo de Wikipedia, con la imagen principal primero."""
    try:
        d = api(f"{wiki}.wikipedia.org", {
            "action": "query", "titles": titulo, "redirects": "1",
            "prop": "pageimages|images", "piprop": "name", "imlimit": "50",
        })
    except Exception as e:
        print(f"    {wiki}.wikipedia «{titulo}»: error ({e})")
        return []
    paginas = (d.get("query") or {}).get("pages") or []
    if not paginas or paginas[0].get("missing"):
        return []
    p = paginas[0]
    salida = []
    principal = p.get("pageimage")
    if principal:
        salida.append("File:" + principal.replace("_", " "))
    for im in p.get("images") or []:
        t = im.get("title", "")
        if t and t not in salida and not NO_FOTO.search(t):
            salida.append(t)
    return salida[:MAX_CANDIDATAS]


def limpia_html(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def licencia_libre(nombre):
    """True si la licencia permite reutilizar la foto con atribución (CC BY, CC BY-SA, CC0, dominio público)."""
    n = (nombre or "").strip().lower()
    if not n:
        return False
    if re.search(r"(^|[\s-])(nc|nd)([\s-]|$)", n):
        return False
    return n.startswith(("cc by", "cc0", "cc-by", "public domain", "pd"))


def info_commons(titulo_archivo):
    """Datos de una imagen de Commons, o None si no sirve (no existe, no es JPEG, pequeña o sin licencia libre)."""
    try:
        d = api("commons.wikimedia.org", {
            "action": "query", "titles": titulo_archivo, "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata", "iiurlwidth": str(ANCHO),
            "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist|Credit|ObjectName|UsageTerms",
        })
    except Exception as e:
        print(f"    commons «{titulo_archivo}»: error ({e})")
        return None
    paginas = (d.get("query") or {}).get("pages") or []
    if not paginas or paginas[0].get("missing") or not paginas[0].get("imageinfo"):
        return None
    ii = paginas[0]["imageinfo"][0]
    if ii.get("mime") != "image/jpeg":
        return None
    if (ii.get("width") or 0) < ANCHO_MIN:
        return None
    meta = ii.get("extmetadata") or {}
    lic = limpia_html((meta.get("LicenseShortName") or {}).get("value"))
    if not licencia_libre(lic):
        return None
    thumb = ii.get("thumburl") or ii.get("url")
    if not thumb:
        return None
    autor = limpia_html((meta.get("Artist") or {}).get("value")) or limpia_html((meta.get("Credit") or {}).get("value"))
    return {
        "thumb": thumb,
        "autor": (autor or "autor desconocido")[:120],
        "lic": lic[:40],
        "licurl": limpia_html((meta.get("LicenseUrl") or {}).get("value")),
        "pagina": ii.get("descriptionurl") or "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(titulo_archivo.replace(" ", "_")),
        "archivo": titulo_archivo,
    }


def descarga_jpeg(url):
    datos = peticion(url, binario=True)
    if not datos.startswith(b"\xff\xd8") or not (4_000 <= len(datos) <= 900_000):
        raise ValueError(f"no parece una foto válida ({len(datos)} bytes)")
    return datos


def buscar_foto(alternativas, forzada=None):
    """Devuelve (nombre_cientifico, info) de la primera foto buena, o (None, None)."""
    if forzada:
        info = info_commons("File:" + forzada.replace("_", " ").removeprefix("File:"))
        return (alternativas[0], info) if info else (None, None)
    for titulo in alternativas:
        for wiki in WIKIS:
            lista = candidatas_de_articulo(wiki, titulo)
            if not lista:
                continue
            for cand in lista:
                info = info_commons(cand)
                if info:
                    return titulo, info
            # El artículo existe pero ninguna imagen valía: se prueba con otro idioma.
    return None, None


def main():
    os.makedirs(DESTINO, exist_ok=True)
    ruta_cred = os.path.join(DESTINO, "creditos.json")
    try:
        with open(ruta_cred, encoding="utf-8") as fh:
            creditos = json.load(fh)
    except Exception:
        creditos = {}

    informe, total_ok, total = [], 0, 0
    for ficha_id, huecos in FOTOS.items():
        nuevos = []
        for n, alternativas in enumerate(huecos):
            total += 1
            forzada = (FORZAR.get(ficha_id) or {}).get(n)
            print(f"[{ficha_id} #{n + 1}] {' / '.join(alternativas)}" + (f"  (forzada: {forzada})" if forzada else ""))
            titulo, info = buscar_foto(alternativas, forzada)
            if not info:
                informe.append(f"FALLO  {ficha_id} #{n + 1}  ({' / '.join(alternativas)}): sin foto libre utilizable")
                print("    -> sin foto")
                continue
            nombre_f = f"{ficha_id}-{n + 1}.jpg"
            try:
                datos = descarga_jpeg(info["thumb"])
            except Exception as e:
                informe.append(f"FALLO  {ficha_id} #{n + 1}  ({titulo}): no se pudo descargar ({e})")
                print(f"    -> descarga fallida: {e}")
                continue
            with open(os.path.join(DESTINO, nombre_f), "wb") as fh:
                fh.write(datos)
            nuevos.append({
                "f": "fotos/" + nombre_f, "sp": titulo, "autor": info["autor"], "lic": info["lic"],
                "licurl": info["licurl"], "pagina": info["pagina"], "archivo": info["archivo"],
            })
            total_ok += 1
            informe.append(f"OK     {ficha_id} #{n + 1}  {titulo}: {info['archivo']}  ({info['lic']}, {len(datos) // 1024} KB)")
            print(f"    -> {info['archivo']} · {info['lic']} · {len(datos) // 1024} KB")
        # Si esta vez no se ha conseguido ninguna foto de la ficha, se conserva lo que ya hubiera.
        if nuevos or ficha_id not in creditos:
            creditos[ficha_id] = nuevos
    with open(ruta_cred, "w", encoding="utf-8") as fh:
        json.dump(creditos, fh, ensure_ascii=False, indent=1, sort_keys=True)
    resumen = f"Fotos: {total_ok} de {total} huecos cubiertos ({time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())})"
    with open(os.path.join(DESTINO, "informe.txt"), "w", encoding="utf-8") as fh:
        fh.write(resumen + "\n" + "\n".join(informe) + "\n")
    print("\n" + resumen)
    return 0 if total_ok else 1


if __name__ == "__main__":
    sys.exit(main())
