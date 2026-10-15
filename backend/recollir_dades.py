"""
Predictor de bolets a Catalunya — recollida de dades i càlcul de puntuació.

Aquest script:
1. Genera (o carrega del cache) una GRAELLA ADAPTATIVA sobre Catalunya en
   dues fases: sondeig a 5km (verificant bosc real amb 5 consultes ICGC
   per cel·la) i densificació a 2.5km només a les cel·les confirmades
   forestals (les no forestals es descarten). El nombre final de punts
   depèn de quanta superfície forestal real detecta el sondeig (consultar
   ZONES en temps d'execució amb len(ZONES), NO fixar aquest número al
   docstring — ja ha quedat desactualitzat més d'un cop). Cada punt porta
   altitud real (Copernicus DEM via Open-Meteo Elevation API) i nom de
   lloc real (reverse geocoding).
2. Consulta dades meteorològiques en viu (Open-Meteo): pluja, temperatura,
   humitat del sòl, evapotranspiració i humitat relativa de l'aire.
3. Contrasta amb estacions reals mitjançant triangulació IDW combinant
   AEMET, Meteocat/XEMA i Meteoclimatic — i amb radar de superfície
   (RainViewer; el radar d'AEMET queda desactivat, ver AEMET_RADAR_ENABLED).
4. Consulta el WMS de cobertes del sòl de l'ICGC per al tipus de bosc
   genèric de cada punt, refinat a espècie exacta d'arbre amb el servei
   VEGETACIO de la Generalitat.
5. Consulta el WMS geològic de l'ICGC per a la litologia del sòl
   (silici/calcari/mixt), amb un petit ajust al scoring per a les espècies
   amb preferència de sòl coneguda.
6. Consulta GBIF/FungaCAT per a la distribució mensual i d'altitud real
   de cada espècie de bolet, en comptes d'una estimació manual.
7. Calcula una puntuació de 0-100 per a cada espècie de bolet en cada punt
   (evidència acumulada, no tot-o-res), amb un nivell de confiança
   independent de la puntuació.
8. Compara amb l'històric propi (evolució 7 dies) i amb les sortides reals
   registrades pels usuaris (tasa de confirmació).
9. Desa el resultat en un fitxer JSON (data/resultats.json) que la web
   llegeix, junt amb diversos fitxers de cache a data/.

Pensat per executar-se automàticament cada 3 hores via GitHub Actions
(veure .github/workflows/actualitzar.yml i README.md per al detall complet
de cada font de dades).
"""

import json
import math
import os
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# 1. GRAELLA ADAPTATIVA DE PUNTS DE CATALUNYA
# ---------------------------------------------------------------------------
# Sistema de dues fases perquè la densitat de punts es concentri on
# realment hi ha bosc (on poden créixer bolets), en comptes de malgastar
# densitat uniforme sobre mar, ciutats, conreus o roca:
#
#   FASE DE SONDEIG (5km): es genera la graella base (com abans) i per a
#   cada cel·la es consulten l'ICGC en el punt central MÉS 4 punts de
#   verificació (N/S/E/O a 1.5km) — si CAP dels 5 punts és bosc real, la
#   cel·la es descarta; verificar amb 5 punts en comptes d'1 de sol evita
#   perdre zones forestals reals només perquè el punt central caigui per
#   casualitat en un clar o un camí dins del bosc.
#
#   FASE DE DENSIFICACIÓ (2.5km): per a cada cel·la de 5km confirmada com a
#   forestal (almenys 1 dels 5 punts de sondeig ho era), es genera una
#   micro-graella de 9 punts (3x3, espaiats 2.5km) dins d'aquella cel·la,
#   substituint el punt únic original. Les cel·les no forestals es
#   descarten del tot (no hi surten bolets ni val la pena mantenir-hi cap
#   punt).
#
# Resultat estimat: ~1.660 punts finals (davant dels ~1.470 amb 5km
# uniforme a tota Catalunya) — més densitat real (2.5km) allà on importa,
# sense el salt de mida (~10.000 punts) que suposaria 2.5km arreu.

GRID_SPACING_KM = 5  # espaiat de la graella de sondeig
DENSE_SPACING_KM = 2.5  # espaiat de la micro-graella dins de cel·les forestals
VERIFICATION_OFFSET_KM = 1.5  # distància dels 4 punts de verificació al centre de cada cel·la
GRID_CACHE_PATH = "../data/zones_grid.json"
FOREST_SURVEY_CACHE_PATH = "../data/forest_survey_cache.json"
FOREST_SURVEY_MAX_SECONDS = 600  # límit de temps per execució per a la fase de sondeig (reduït de 900 per deixar marge a les altres fases ICGC de la mateixa execució: bosc detallat ~1000s, VEGETACIO ~400s)
FOREST_SURVEY_MAX_DAYS = 365  # el bosc real no canvia sovint; cache llarg

CATALUNYA_LAT_MIN, CATALUNYA_LAT_MAX = 40.50, 42.95
CATALUNYA_LON_MIN, CATALUNYA_LON_MAX = -0.05, 3.30

# Polígon aproximat de Catalunya (vèrtexs principals de costa i fronteres),
# per evitar generar massa punts al mar en comptes d'un simple rectangle.
CATALUNYA_POLYGON = [
    (42.90, 0.65), (42.85, 1.70), (42.45, 2.90), (41.75, 3.15),
    (41.35, 2.30), (41.15, 1.20), (40.55, 0.55), (40.75, 0.10),
    (41.40, 0.05), (42.30, 0.60), (42.90, 0.65),
]


def point_in_catalunya_polygon(lat, lon):
    """Ray casting simple per saber si un punt cau dins el polígon aproximat."""
    polygon = CATALUNYA_POLYGON
    n = len(polygon)
    inside = False
    p1lat, p1lon = polygon[0]
    lat_intersect = None
    for i in range(n + 1):
        p2lat, p2lon = polygon[i % n]
        if lon > min(p1lon, p2lon):
            if lon <= max(p1lon, p2lon):
                if lat <= max(p1lat, p2lat):
                    if p1lon != p2lon:
                        lat_intersect = (lon - p1lon) * (p2lat - p1lat) / (p2lon - p1lon) + p1lat
                    if p1lat == p2lat or lat_intersect is None or lat <= lat_intersect:
                        inside = not inside
        p1lat, p1lon = p2lat, p2lon
    return inside


def generate_grid_points(spacing_km=GRID_SPACING_KM):
    """Genera coordenades en graella regular sobre Catalunya, filtrant amb el
    polígon aproximat per no generar massa punts al mar."""
    lat_step = spacing_km / 111.0
    avg_lat = (CATALUNYA_LAT_MIN + CATALUNYA_LAT_MAX) / 2
    lon_step = spacing_km / (111.0 * math.cos(math.radians(avg_lat)))

    points = []
    lat = CATALUNYA_LAT_MIN
    while lat <= CATALUNYA_LAT_MAX:
        lon = CATALUNYA_LON_MIN
        while lon <= CATALUNYA_LON_MAX:
            if point_in_catalunya_polygon(lat, lon):
                points.append((round(lat, 4), round(lon, 4)))
            lon += lon_step
        lat += lat_step
    return points


def generate_verification_points(center_lat, center_lon, offset_km=VERIFICATION_OFFSET_KM):
    """Genera 4 punts de verificació N/S/E/O al voltant del centre d'una
    cel·la, per comprovar si hi ha bosc real sense dependre només del punt
    central exacte (que pot caure per casualitat en un clar o un camí)."""
    lat_offset = offset_km / 111.0
    lon_offset = offset_km / (111.0 * math.cos(math.radians(center_lat)))
    return [
        (round(center_lat + lat_offset, 4), round(center_lon, 4)),
        (round(center_lat - lat_offset, 4), round(center_lon, 4)),
        (round(center_lat, 4), round(center_lon + lon_offset, 4)),
        (round(center_lat, 4), round(center_lon - lon_offset, 4)),
    ]


def generate_dense_subgrid(center_lat, center_lon, cell_size_km=GRID_SPACING_KM, sub_spacing_km=DENSE_SPACING_KM):
    """Genera una micro-graella (normalment 3x3=9 punts) dins d'una cel·la
    de cell_size_km, amb espaiat sub_spacing_km, per substituir el punt
    únic original en cel·les confirmades com a forestals."""
    half_cell = cell_size_km / 2
    lat_range = half_cell / 111.0
    lon_range = half_cell / (111.0 * math.cos(math.radians(center_lat)))
    sub_lat_step = sub_spacing_km / 111.0
    sub_lon_step = sub_spacing_km / (111.0 * math.cos(math.radians(center_lat)))

    points = []
    lat = center_lat - lat_range
    while lat <= center_lat + lat_range + 1e-9:
        lon = center_lon - lon_range
        while lon <= center_lon + lon_range + 1e-9:
            if point_in_catalunya_polygon(lat, lon):
                points.append((round(lat, 4), round(lon, 4)))
            lon += sub_lon_step
        lat += sub_lat_step
    return points


def load_forest_survey_cache():
    """Cache del sondeig forestal: {codi_cel·la: True/False}, indica si una
    cel·la de la graella de 5km té bosc real confirmat (almenys 1 dels 5
    punts de verificació ho era). Cache llarg (365 dies) — el bosc real no
    canvia d'una execució a una altra."""
    try:
        with open(FOREST_SURVEY_CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    cached_at = cache.get("cached_at")
    if not cached_at:
        return {}
    try:
        age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(cached_at)).days
    except ValueError:
        return {}
    if age_days > FOREST_SURVEY_MAX_DAYS:
        return {}
    return cache.get("cells", {})


def save_forest_survey_cache(cells):
    cache = {"cached_at": datetime.now(timezone.utc).isoformat(), "cells": cells}
    with open(FOREST_SURVEY_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def cell_key(lat, lon):
    return f"{lat:.4f},{lon:.4f}"


def survey_forest_cells(base_points, layer_name):
    """
    FASE DE SONDEIG: per a cada punt base (cel·la de 5km) encara no
    cacuejat, consulta el punt central + 4 punts de verificació a l'ICGC.
    Si CAP dels 5 és bosc real, la cel·la es marca com a no forestal
    (es descartarà). Es processa per lots amb límit de temps, com
    VEGETACIO/ICGC — amb ~1470 cel·les x 5 consultes, es completa en
    diverses execucions successives.

    IMPORTANT: si les 5 consultes d'una cel·la fallen totes (timeout,
    error de xarxa...), NO es marca com a no forestal — es deixa sense
    resoldre perquè es torni a intentar la propera execució. Es va
    detectar un cas real: tot el Pirineu (Val d'Aran, Pallars, Alta
    Ribagorça) va quedar sense cap zona a la graella final perquè les
    seves cel·les es van marcar silenciosament com "no forestal" quan en
    realitat les consultes ICGC hi fallaven (timeout=5s de fetch_tree_type,
    probablement per més latència/complexitat de dades en zona de
    muntanya) — el codi antic no distingia "confirmat sense bosc" de "no
    s'ha pogut confirmar".
    """
    cache = load_forest_survey_cache()
    missing = [p for p in base_points if cell_key(*p) not in cache]

    if not missing:
        print("  Sondeig forestal: totes les cel·les ja són al cache")
        return cache

    print(f"  Sondeig forestal: {len(missing)} cel·les sense cache — consultant...")
    start = time.time()
    consulted = 0
    unresolved = 0
    for lat, lon in missing:
        if time.time() - start > FOREST_SURVEY_MAX_SECONDS:
            print(f"  Sondeig forestal: límit de temps ({FOREST_SURVEY_MAX_SECONDS}s) assolit a {consulted} cel·les — es continua la propera execució")
            break
        points_to_check = [(lat, lon)] + generate_verification_points(lat, lon)
        is_forest = False
        any_success = False
        for vlat, vlon in points_to_check:
            try:
                tree, _ = fetch_tree_type(vlat, vlon, layer_name, timeout=12)
                any_success = True
                if tree not in NON_FOREST and tree != UNRESOLVED_TREE:
                    is_forest = True
                    break  # ja no cal comprovar la resta d'aquesta cel·la
            except Exception:
                continue
        consulted += 1
        if not any_success:
            # Les 5 consultes han fallat — no es pot confirmar res, es deixa
            # pendent per reintentar (NO es guarda al cache com a False).
            unresolved += 1
            continue
        cache[cell_key(lat, lon)] = is_forest
    save_forest_survey_cache(cache)
    forest_count = sum(1 for v in cache.values() if v)
    print(f"  Sondeig forestal: {consulted} cel·les processades ({forest_count}/{len(cache)} forestals fins ara, {unresolved} sense resoldre per fallada de xarxa — es reintentaran)")
    return cache


def fetch_elevations_batch(points, timeout=20):
    """Consulta l'altitud REAL (Copernicus DEM, 90m) de fins a 100 punts de
    cop via l'Elevation API d'Open-Meteo (gratuïta, sense clau, el mateix
    proveïdor que ja fem servir per a la resta de dades meteorològiques)."""
    lats = ",".join(str(p[0]) for p in points)
    lons = ",".join(str(p[1]) for p in points)
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lats}&longitude={lons}"
    req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("elevation", [])


ELEVATION_CACHE_PATH = "../data/elevation_cache.json"


def load_elevation_cache():
    try:
        with open(ELEVATION_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("points", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_elevation_cache(points):
    with open(ELEVATION_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump({"points": points}, f, ensure_ascii=False)


def fetch_elevations_for_points(points, max_seconds=300):
    """
    Consulta l'altitud real per als punts encara no cacuejats, en lots de
    100, amb cache permanent (l'altitud del terreny no canvia mai).

    IMPORTANT: si un lot falla (timeout, 429...) els seus punts NO es
    marquen com a resolts amb un valor fals — es deixen pendents per
    reintentar la propera execució. Es va detectar un cas real: amb
    l'antic disseny (sense cache ni reintents per punt), un lot fallat
    descartava els seus punts per sempre — això va fer que TOT EL PIRINEU
    (Val d'Aran, Pallars, Alta Ribagorça) desaparegués de la graella final,
    perquè les seves cel·les SÍ eren forestals (confirmat al sondeig) però
    els seus punts densificats van caure en lots d'altitud que van fallar
    per un 429 de l'Elevation API just en aquella franja de l'execució.
    """
    cache = load_elevation_cache()
    point_keys = [cell_key(lat, lon) for lat, lon in points]
    missing_points = [(lat, lon) for (lat, lon), key in zip(points, point_keys) if key not in cache]

    if missing_points:
        print(f"  Altitud: {len(missing_points)} punts sense cache — consultant...")
        start = time.time()
        batch_size = 100
        consulted = 0
        for i in range(0, len(missing_points), batch_size):
            if time.time() - start > max_seconds:
                print(f"  Altitud: límit de temps ({max_seconds}s) assolit a {consulted} punts — es continua la propera execució")
                break
            batch = missing_points[i:i + batch_size]
            try:
                elevs = retry_with_backoff(
                    lambda b=batch: fetch_elevations_batch(b),
                    max_attempts=5,
                    description=f"Elevation API lot {i // batch_size + 1}",
                )
                for (lat, lon), elev in zip(batch, elevs):
                    if elev is not None:
                        cache[cell_key(lat, lon)] = elev
                    # Si elev és None (dada no disponible per a aquest punt
                    # concret), NO es guarda — es deixa pendent, no és el
                    # mateix que "el lot sencer ha fallat".
                consulted += len(batch)
            except Exception as e:
                print(f"  AVÍS: lot d'altituds {i // batch_size + 1} ha fallat del tot ({e}) — es deixen pendents per reintentar, NO es descarten")
                # No es guarda res per a aquest lot — es reintentarà.
            time.sleep(1)  # cortesia amb el servei gratuït
        save_elevation_cache(cache)
        print(f"  Altitud: {consulted} punts nous consultats aquesta execució")
    else:
        print("  Altitud: tots els punts ja són al cache")

    elevations = [cache.get(cell_key(lat, lon)) for lat, lon in points]
    return elevations


def build_zones_with_real_elevation():
    """
    Genera la graella adaptativa completa:
    1. Graella base de sondeig (5km).
    2. Per a cada cel·la, sondeig forestal (5 punts de verificació) via
       ICGC — amb cache propi de llarga durada, es completa per lots en
       diverses execucions.
    3. Cel·les forestals confirmades -> es densifiquen amb una micro-graella
       de 2.5km (9 punts). Cel·les no forestals -> es descarten del tot.
    4. Altitud REAL (Copernicus DEM) per a tots els punts finals, amb
       cache propi permanent — un punt mai es descarta per un fallo
       temporal de xarxa, només si de debò no té dada vàlida un cop
       consultat amb èxit (probablement mar).

    Retorna (zones, is_complete). is_complete és False si el sondeig
    forestal encara no ha cobert totes les cel·les base, O si encara falta
    consultar l'altitud d'algun punt densificat — en qualsevol dels dos
    casos, la graella final NO es fixa al cache fins que tot estigui
    complet, per no perdre zones boscoses reals de manera permanent (com
    va passar amb el Pirineu).
    """
    base_points = generate_grid_points()
    print(f"  Graella de sondeig generada: {len(base_points)} cel·les (5km)")

    layer_name, _ = discover_icgc_layer()
    forest_survey = survey_forest_cells(base_points, layer_name)

    final_points = []
    forest_cells, non_forest_cells, pending_cells = 0, 0, 0
    for lat, lon in base_points:
        key = cell_key(lat, lon)
        is_forest = forest_survey.get(key)
        if is_forest is True:
            final_points.extend(generate_dense_subgrid(lat, lon))
            forest_cells += 1
        elif is_forest is False:
            non_forest_cells += 1
        else:
            pending_cells += 1  # encara no sondejada — es descarta per ara, conservador

    print(f"  Cel·les: {forest_cells} forestals (densificades), {non_forest_cells} no forestals (descartades), {pending_cells} pendents de sondeig")
    print(f"  Punts totals abans de consultar altitud: {len(final_points)}")

    survey_complete = pending_cells == 0
    if not survey_complete:
        print(f"  AVÍS: {pending_cells} cel·les encara no sondejades — la graella NO es fixarà al cache fins que el sondeig estigui complet")

    all_elevations = fetch_elevations_for_points(final_points)
    elevation_complete = all(e is not None for e in all_elevations)
    if not elevation_complete:
        pending_elev = sum(1 for e in all_elevations if e is None)
        print(f"  AVÍS: {pending_elev} punts encara sense altitud — la graella NO es fixarà al cache fins que estigui completa")

    zones = []
    for idx, ((lat, lon), elev) in enumerate(zip(final_points, all_elevations), start=1):
        if elev is None:
            continue  # pendent de consultar (es reintentarà) o mar (elevació negativa ja filtrada a fetch_elevations_for_points... es manté aquí per seguretat)
        if elev < 0:
            continue  # probablement mar
        zones.append({"id": idx, "lat": lat, "lon": lon, "alt": round(elev)})

    print(f"  Zones finals amb altitud real vàlida: {len(zones)}")
    is_complete = survey_complete and elevation_complete
    return zones, is_complete


def load_or_build_zones():
    """
    Carrega la graella des del cache si existeix (mai caduca un cop fixada
    — les coordenades i l'altitud del terreny no canvien), o la genera/
    avança la primera vegada.

    IMPORTANT: la graella final NOMÉS es fixa al cache un cop el sondeig
    forestal (survey_forest_cells) ha cobert el 100% de les cel·les base.
    Fixar-la abans (amb cel·les encara pendents tractades com "no
    forestal") perdria zones boscoses reals de manera permanent. Mentre el
    sondeig no estigui complet, cada execució avança el sondeig una mica
    més (per lots, com VEGETACIO) i usa una graella "provisional" (només
    amb les cel·les ja confirmades) sense desar-la — un cop el sondeig
    arribi al 100%, la següent execució la fixa i totes les posteriors la
    carreguen del cache a l'instant.
    """
    try:
        with open(GRID_CACHE_PATH, "r", encoding="utf-8") as f:
            cached = json.load(f)
        zones = cached.get("zones")
        if zones and len(zones) > 100 and cached.get("survey_complete"):
            print(f"  Graella carregada des del cache (sondeig complet): {len(zones)} punts")
            return zones
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    print("  Graella encara no fixada (sondeig forestal i/o altitud en curs) — generant/avançant...")
    zones, is_complete = build_zones_with_real_elevation()
    try:
        with open(GRID_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "zones": zones,
                "survey_complete": is_complete,
            }, f, ensure_ascii=False)
        if is_complete:
            print(f"  Sondeig i altitud complets — graella fixada amb {len(zones)} punts (les properes execucions la carregaran del cache)")
        else:
            print(f"  Encara incomplet (sondeig i/o altitud) — graella provisional d'aquesta execució: {len(zones)} punts (no fixada del tot)")
    except Exception as e:
        print(f"  AVÍS: no s'ha pogut desar el cache de la graella ({e})")
    return zones


# ZONES es carrega/genera al final del fitxer (després que totes les
# funcions auxiliars, incloent retry_with_backoff, ja estiguin definides).


# ---------------------------------------------------------------------------
# 2. ESPÈCIES DE BOLETS I LA SEVA LÒGICA
# ---------------------------------------------------------------------------
SPECIES = [
    {"id": "rovellons",   "name": "Rovellons",           "scientific": ["Lactarius deliciosus", "Lactarius sanguifluus"],      "trees": ["pi_roig", "pi_negre", "pi_pinyer", "pi_blanc", "pi_altres"], "rain_days": [7, 15],  "temp_range": [4, 16],  "min_rain": 20},
    {"id": "ceps",        "name": "Ceps",                 "scientific": ["Boletus edulis", "Boletus aereus", "Boletus pinophilus"], "trees": ["roure", "faig", "pi_roig", "pi_negre", "avet", "pi_altres"], "rain_days": [8, 16],  "temp_range": [6, 18],  "min_rain": 25},
    {"id": "camagrocs",   "name": "Camagrocs",            "scientific": ["Craterellus lutescens"],                              "trees": ["faig", "roure", "pi_roig", "pi_negre", "pi_blanc", "pi_altres", "avet"], "rain_days": [10, 20], "temp_range": [6, 16],  "min_rain": 20},
    {"id": "trompetes",   "name": "Trompetes de la mort", "scientific": ["Craterellus cornucopioides"],                         "trees": ["faig", "roure"],                                            "rain_days": [10, 20], "temp_range": [5, 15],  "min_rain": 25},
    {"id": "oureig",      "name": "Ou de reig",           "scientific": ["Amanita caesarea"],                                   "trees": ["alzina", "roure", "suro"],                                  "rain_days": [15, 20], "temp_range": [12, 22], "min_rain": 18},
    {"id": "rossinyols",  "name": "Rossinyols",           "scientific": ["Cantharellus cibarius"],                              "trees": ["faig", "roure", "pi_roig", "pi_negre", "avet", "pi_altres"], "rain_days": [7, 16],  "temp_range": [6, 17],  "min_rain": 20},
    {"id": "colmenilles", "name": "Colmenilles",          "scientific": ["Morchella esculenta", "Morchella elata"],             "trees": ["roure", "pi_blanc", "pi_roig", "pi_negre", "pi_altres"], "rain_days": [8, 18],  "temp_range": [2, 13],  "min_rain": 15},
    {"id": "llengua",     "name": "Llengua de bou",       "scientific": ["Hydnum repandum"],                                    "trees": ["roure", "faig", "suro"],                                    "rain_days": [10, 20], "temp_range": [8, 18],  "min_rain": 20},
    {"id": "pinetell",    "name": "Pinetell",             "scientific": ["Lactarius deliciosus"],                               "trees": ["pi_roig", "pi_negre", "pi_pinyer", "pi_blanc", "pi_altres"], "rain_days": [7, 14],  "temp_range": [4, 15],  "min_rain": 20},
    {"id": "fredolic",    "name": "Fredolic",             "scientific": ["Tricholoma terreum"],                                 "trees": ["pi_blanc", "pi_roig", "pi_negre", "pi_pinyer", "alzina", "pi_altres"], "rain_days": [9, 18],  "temp_range": [3, 14],  "min_rain": 18},
]

# ---------------------------------------------------------------------------
# 2b. PERFIL BIOLÒGIC PER ESPÈCIE (LIMITANTS DURS)
# ---------------------------------------------------------------------------
# Fins ara la puntuació era una SUMA de factors: una espècie podia superar el
# llindar (70) encara que fallés el més important. Casos reals detectats el
# 15/10/2026 amb dades de producció:
#   - Ou de reig a Montnegre amb 88-92 punts només 7 dies després de la
#     pluja, quan triga 15-20 dies i necessita calor.
#   - Ou de reig a Matadepera / Sant Llorenç (conglomerats amb ciment
#     calcari) classificat com a sòl "silici" i amb la geologia pesant ±1.5
#     punts sobre 100.
#   - Ou de reig fins a 1.986 m i colmenilles (bolet de primavera) amb 71
#     punts a l'octubre.
# Ara, a més de la suma d'evidència, cada espècie té LIMITANTS que
# MULTIPLIQUEN el resultat (valors 0-1): moment respecte a la pluja
# principal, època de l'any, altitud, calor i geologia. Si un limitant és
# 0.3, la puntuació no pot passar de 30 per bones que siguin les altres
# condicions — com al bosc: un ou de reig no surt si encara és massa aviat,
# o si fa massa fred, o en un sòl calcari, encara que hagi plogut molt.
#
# Els punts de cada corba són (valor, multiplicador) amb interpolació lineal.
# Fonts: bolets.com, Associació Boletaire Independent, sporas.io,
# Enciclopèdia Catalana, GBIF/FungaCAT i observacions de camp de l'usuari
# (Ou de reig: 15-20 dies després de la pluja, necessita calor). Són valors
# de partida calibrables: si les sortides reals (hallazgos) els contradiuen,
# aquest és l'únic lloc on cal tocar.
SPECIES_BIO = {
    "oureig": {
        # dies des de la PLUJA PRINCIPAL (no des de l'últim ruixat)
        "timing": [(4, 0.05), (8, 0.25), (12, 0.65), (15, 1.0), (21, 1.0), (28, 0.65), (38, 0.25), (50, 0.10)],
        # gairebé no passa de 1.000 m (ocasionalment fins a 1.400)
        "alt": [(0, 1.0), (800, 1.0), (1000, 0.45), (1150, 0.15), (1300, 0.0)],
        # termòfil: mínimes nocturnes i màximes diürnes dels darrers 7 dies
        "heat": {"tmin": [(6, 0.0), (9, 0.45), (11, 0.85), (12, 1.0)],
                 "tmax": [(13, 0.0), (17, 0.45), (20, 0.85), (22, 1.0)]},
        # acidòfil (pH 4-6, pissarres/granits): molt rar en sòls calcaris
        "soil": {"silici": 1.0, "silici_prov": 0.85, "mixt": 0.60, "calcari": 0.12, None: 0.85},
        "season_manual": ((8, 5), (10, 31)),
    },
    "rovellons": {
        "alt": [(0, 0.8), (200, 1.0), (1700, 1.0), (2000, 0.35), (2250, 0.0)],
        "season_manual": ((9, 15), (12, 15)),
    },
    "ceps": {
        "alt": [(0, 0.8), (250, 1.0), (1700, 1.0), (2000, 0.40), (2300, 0.0)],
        "soil": {"silici": 1.0, "silici_prov": 1.0, "mixt": 0.97, "calcari": 0.90, None: 0.97},
        "season_manual": ((6, 15), (11, 30)),
    },
    "camagrocs": {
        "alt": [(0, 0.30), (300, 0.65), (600, 1.0), (1700, 1.0), (2000, 0.40), (2300, 0.0)],
        "soil": {"calcari": 1.0, "mixt": 1.0, "silici": 0.85, "silici_prov": 0.90, None: 0.95},
        "season_manual": ((9, 10), (1, 5)),
    },
    "trompetes": {
        "alt": [(0, 0.20), (300, 0.60), (500, 1.0), (1500, 1.0), (1800, 0.40), (2100, 0.0)],
        "season_manual": ((9, 15), (12, 20)),
    },
    "rossinyols": {
        "alt": [(0, 0.70), (300, 1.0), (1800, 1.0), (2100, 0.40), (2400, 0.0)],
        "season_manual": ((6, 10), (11, 10)),
    },
    "colmenilles": {
        "alt": [(0, 0.90), (200, 1.0), (1600, 1.0), (1900, 0.40), (2200, 0.0)],
        "season_manual": ((3, 5), (5, 31)),
    },
    "llengua": {
        "alt": [(0, 0.70), (300, 1.0), (1600, 1.0), (1900, 0.40), (2200, 0.0)],
        "season_manual": ((8, 20), (12, 20)),
    },
    "pinetell": {
        "alt": [(0, 0.80), (200, 1.0), (1700, 1.0), (2000, 0.40), (2250, 0.0)],
        "season_manual": ((9, 25), (12, 15)),
    },
    "fredolic": {
        # bolet tardà de terra baixa (fins poc abans de Nadal)
        "alt": [(0, 1.0), (900, 1.0), (1300, 0.50), (1700, 0.15), (2000, 0.0)],
        "season_manual": ((10, 1), (12, 31)),
    },
}

# Corba de moment per defecte (derivada de rain_days de cada espècie) per a
# les espècies sense "timing" propi: pocs dies després de la pluja encara no
# han sortit; molts dies després la tanda s'està acabant.
def default_timing_curve(rain_days):
    lo, hi = rain_days
    return [(max(1, lo - 6), 0.15), (max(2, lo - 3), 0.60), (lo, 1.0), (hi, 1.0), (hi + 8, 0.55), (hi + 20, 0.20)]


def interp_curve(points, x):
    """Interpolació lineal sobre una llista de (x, y) ordenada per x;
    fora dels extrems es manté el valor de l'extrem."""
    if x <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x <= x1:
            if x1 == x0:
                return y1
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return points[-1][1]


TREE_LABELS = {
    "pi_roig": "pinar de pino rojo", "pi_negre": "pinar de pino negro", "avet": "abetal",
    "pi_blanc": "pinar de pino blanco", "pi_pinyer": "pinar de pino piñonero",
    "pi_altres": "bosque de coníferas (especie no diferenciada)",
    "alzina": "encinar/bosque de perennifolios", "roure": "robledal/bosque de caducifolios",
    "faig": "hayedo", "suro": "alcornocal", "mixt": "bosque mixto",
    "matollar": "matorral", "prat": "prado/pastizal", "desconegut": "tipo de bosque desconocido",
}

# IMPORTANT (llistes "trees" de SPECIES): una espècie només puntua en un punt
# si el seu tipus d'arbre és a la llista. Quan VEGETACIO afina un "pi_altres"
# a pi_roig / pi_negre / pi_blanc / pi_pinyer / avet, un "roure" a faig o un
# "alzina" a suro, el punt deixa de ser el genèric. Per no perdre espècies que
# sí hi creixen, cada llista inclou els fills del genèric on l'espècie
# realment es fa (p. ex. cep i rossinyol també a l'abetar; llengua de bou a la
# fageda; pinetell i fredolic a qualsevol pineda). Prova a tests/test_model.py.

# Mapa de tipus de bosc CONFIRMATS com a no forestals (mai assignem cap espècie).
# "desconegut" NO hi és inclòs a propòsit: significa "encara no s'ha pogut
# determinar" (timeout, error de xarxa, límit de temps assolit...), no
# "confirmat que no hi ha bosc" — són coses molt diferents. Es va detectar un
# cas real: zones amb bosc real (confirmat per coneixement de camp de
# l'usuari a la zona de Berga) quedaven marcades "desconegut" per fallades
# de l'ICGC/límit de temps, i en tractar "desconegut" igual que "conreu"
# desapareixien silenciosament de la graella densificada per sempre.
NON_FOREST = {"conreu", "urba", "aigua", "roca", "matollar", "prat"}
UNRESOLVED_TREE = "desconegut"  # pendent de determinar — mai s'ha de tractar com a "confirmat sense bosc"

# Llindar de puntuació per defecte per considerar una espècie "probable" en una
# zona. La web permet ajustar-lo amb un control lliscant sense recalcular:
# es desen totes les puntuacions >0 i el filtratge final es fa al navegador.
DEFAULT_SCORE_THRESHOLD = 70

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
AEMET_STATIONS_URL = "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"
ICGC_WMS_URL = "https://geoserveis.icgc.cat/servei/catalunya/cobertes-sol/wms"

# Noms candidats per a la capa detallada del MCSC (241 categories), de més a menys
# recent. Es descobreix quin és vàlid consultant GetCapabilities (veure discover_icgc_layer).
ICGC_LAYER_CANDIDATES = [
    "cobertes2023", "cobertes_2023", "mcsc_2023",
    "cobertes2019_2022", "cobertes_2019_2022", "mcsc_2019_2022",
    "cobertes2018", "cobertes_2018", "mcsc_2018",
]
ICGC_LAYER_FALLBACK = "cobertes_2009"


def discover_icgc_layer(timeout=15):
    """
    Consulta GetCapabilities del WMS de l'ICGC per trobar el nom tècnic real de la
    capa més detallada disponible (MCSC amb ~241 categories). Si no es pot determinar,
    torna la capa de 41 classes que ja sabem que funciona (ICGC_LAYER_FALLBACK).
    """
    url = f"{ICGC_WMS_URL}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities"
    req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            xml_text = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  AVÍS: no s'ha pogut consultar GetCapabilities de l'ICGC ({e}) — s'usa la capa de 41 classes")
        return ICGC_LAYER_FALLBACK, []

    # Extreu tots els noms <Name>...</Name> dins de <Layer> (aproximació senzilla per regex,
    # evitem dependències externes de parsing XML).
    import re
    names = re.findall(r"<Name>([^<]+)</Name>", xml_text)
    print(f"  ICGC GetCapabilities: {len(names)} capes trobades")

    for candidate in ICGC_LAYER_CANDIDATES:
        if candidate in names:
            print(f"  ICGC: s'usarà la capa detallada '{candidate}'")
            return candidate, names

    print(f"  AVÍS: cap capa detallada coneguda trobada entre les {len(names)} disponibles — s'usa la capa de 41 classes")
    return ICGC_LAYER_FALLBACK, names


# ---------------------------------------------------------------------------
# UTILITATS GEOGRÀFIQUES
# ---------------------------------------------------------------------------

def retry_with_backoff(func, max_attempts=3, base_delay=2, description="operació"):
    """
    Executa 'func' (sense arguments — fer servir lambda o functools.partial
    si en necessita) i reintenta fins a max_attempts vegades si falla, amb
    espera creixent entre intents (2s, 4s, 8s...). Si tots els intents
    fallen, es propaga l'última excepció perquè el crida decideixi què fer
    (normalment continuar sense aquella font, com ja es feia abans).

    Cas especial: HTTP 429 (Too Many Requests) — molts serveis (Open-Meteo
    inclòs) no tenen un límit fix per minut documentat, sinó que apliquen
    "throttling" temporal si detecten ràfegues de peticions seguides. En
    aquest cas s'espera més temps del backoff normal (respectant la
    capçalera Retry-After si el servidor la envia) perquè un backoff curt
    no dona temps real a que es desbloquegi.
    """
    last_exception = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_attempts:
                is_429 = isinstance(e, urllib.error.HTTPError) and e.code == 429
                if is_429:
                    retry_after = None
                    try:
                        retry_after = int(e.headers.get("Retry-After", "0"))
                    except (ValueError, AttributeError, TypeError):
                        pass
                    delay = retry_after if retry_after and retry_after > 0 else base_delay * (2 ** (attempt - 1)) * 5
                    print(f"    AVÍS: {description} ha rebut 429 (massa peticions) — esperant {delay}s abans de reintentar...")
                else:
                    delay = base_delay * (2 ** (attempt - 1))
                    print(f"    AVÍS: {description} ha fallat (intent {attempt}/{max_attempts}: {type(e).__name__}) — reintentant en {delay}s...")
                time.sleep(delay)
    raise last_exception


def haversine_km(lat1, lon1, lat2, lon2):
    """Distància aproximada en km entre dos punts."""
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(min(1, a ** 0.5))


# ---------------------------------------------------------------------------
# 3. METEOROLOGIA — OPEN-METEO
# ---------------------------------------------------------------------------

def fetch_weather_batch(zones, timeout=60):
    """Consulta Open-Meteo per a un grup de zones en una sola petició.
    Inclou humitat del sòl (soil_moisture_9_27cm, capa on viu el miceli de
    la majoria d'espècies) i evapotranspiració, per saber si l'aigua caiguda
    realment ha quedat al sòl o s'ha perdut — la pluja per si sola no ho
    distingeix (50mm sobre sòl ja humit no és el mateix que 50mm sobre sòl
    ressec, encara que la suma de pluja sigui idèntica). També humitat
    relativa de l'aire (relative_humidity_2m) — complementa la del sòl: un
    aire molt sec pot ressecar la capa més superficial i el mateix barret
    del bolet encara que el sòl profund segueixi humit."""
    lats = ",".join(str(z["lat"]) for z in zones)
    lons = ",".join(str(z["lon"]) for z in zones)
    params = (
        f"?latitude={lats}&longitude={lons}"
        f"&daily=precipitation_sum,temperature_2m_max,temperature_2m_min"
        f"&hourly=soil_moisture_9_27cm,et0_fao_evapotranspiration,relative_humidity_2m"
        f"&past_days=16&forecast_days=1&timezone=Europe%2FMadrid"
    )
    url = OPEN_METEO_URL + params
    req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data if isinstance(data, list) else [data]


# ---------------------------------------------------------------------------
# BLOCS ROTATIUS GEOGRÀFICS PER A OPEN-METEO
# ---------------------------------------------------------------------------
# Amb la graella adaptativa (~7300 punts), consultar Open-Meteo sencer cada
# execució satura el servei gratuït (confirmat amb un patró real de fallades
# massives — la majoria de lots fallant el primer intent). En comptes de
# reduir la graella, es reparteix la càrrega: la graella es divideix en 3
# blocs geogràfics compactes (k-means simple per proximitat, sense cap
# llibreria externa), i cada execució només refresca UN bloc, rotant
# 0→1→2→0... Els punts dels blocs que no toquen mantenen el seu últim valor
# meteorològic vàlid (cache propi) — amb execucions cada 4h i 3 blocs, cada
# punt es refresca cada ~12h, acceptable per a dades que ja són un històric
# de 16 dies, no només l'instant actual (el radar, que sí és molt sensible
# al moment exacte, es consulta sencer cada execució, sense rotar).

WEATHER_N_BLOCKS = 3
WEATHER_BLOCK_CACHE_PATH = "../data/weather_block_cache.json"
WEATHER_TURN_PATH = "../data/weather_turn.json"


def simple_kmeans(points, k, iterations=15, seed=42):
    """K-means simple sense dependències externes, per agrupar punts per
    proximitat geogràfica en k blocs compactes."""
    import random
    rng = random.Random(seed)
    centroids = rng.sample(points, k)

    for _ in range(iterations):
        clusters = [[] for _ in range(k)]
        for p in points:
            distances = [(p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 for c in centroids]
            closest = distances.index(min(distances))
            clusters[closest].append(p)
        new_centroids = []
        for cluster in clusters:
            if cluster:
                avg_lat = sum(p[0] for p in cluster) / len(cluster)
                avg_lon = sum(p[1] for p in cluster) / len(cluster)
                new_centroids.append((avg_lat, avg_lon))
            else:
                new_centroids.append(rng.choice(points))
        centroids = new_centroids

    labels = []
    for p in points:
        distances = [(p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 for c in centroids]
        labels.append(distances.index(min(distances)))
    return labels


def assign_weather_blocks(zones):
    """Assigna cada zona a un dels WEATHER_N_BLOCKS blocs geogràfics.
    Determinista (seed fixa): la mateixa graella sempre dona els mateixos
    blocs, així que no cal cache — es recalcula cada execució (és barat,
    pur càlcul local sense xarxa)."""
    points = [(z["lat"], z["lon"]) for z in zones]
    labels = simple_kmeans(points, WEATHER_N_BLOCKS)
    return {z["id"]: label for z, label in zip(zones, labels)}


def load_weather_turn():
    try:
        with open(WEATHER_TURN_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("next_block", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def save_weather_turn(next_block):
    with open(WEATHER_TURN_PATH, "w", encoding="utf-8") as f:
        json.dump({"next_block": next_block}, f, ensure_ascii=False)


def load_weather_block_cache():
    try:
        with open(WEATHER_BLOCK_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("points", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_weather_block_cache(points):
    with open(WEATHER_BLOCK_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump({"points": points}, f, ensure_ascii=False)


def fetch_weather(zones, batch_size=50, delay_between_batches=2.5):
    """Open-Meteo accepta moltes coordenades per petició.

    IMPORTANT: si un lot esgota tots els seus reintents (max_attempts),
    ABANS es propagava l'excepció i avortava TOT el procés (incloent tot
    el treball ja fet de sondeig/altitud d'aquesta execució, que sí s'havia
    desat correctament però la resta de fonts no arribaven a consultar-se
    ni a desar-se). Ara, un lot que falla del tot es marca amb valors buits
    per als seus punts (es tracten com "sense dada" en aquesta execució,
    reintentats la propera) i el procés CONTINUA amb la resta — un fallo
    puntual d'Open-Meteo no ha de bloquejar tota la resta del pipeline
    (radar, GBIF, VEGETACIO, geologia...)."""
    all_results = []
    n_batches = -(-len(zones) // batch_size)
    failed_batches = 0
    for i in range(0, len(zones), batch_size):
        batch = zones[i:i + batch_size]
        batch_num = i // batch_size + 1
        try:
            results = retry_with_backoff(
                lambda b=batch: fetch_weather_batch(b),
                max_attempts=6,
                description=f"Open-Meteo lot {batch_num}/{n_batches}",
            )
            all_results.extend(results)
        except Exception as e:
            print(f"    AVÍS: Open-Meteo lot {batch_num}/{n_batches} ha fallat del tot ({e}) — {len(batch)} punts sense dada meteorològica aquesta execució")
            failed_batches += 1
            all_results.extend([{}] * len(batch))  # placeholder buit, compute_rain_stats ja gestiona dades absents
        if batch_num < n_batches:
            time.sleep(delay_between_batches)
    if failed_batches:
        print(f"  Open-Meteo: {failed_batches}/{n_batches} lots han fallat del tot — aquests punts es reintentaran a la propera execució")
    return all_results


def fetch_weather_rotating(zones):
    """
    Orquestra el sistema de blocs rotatius: només el bloc del torn actual es
    consulta de debò a Open-Meteo; la resta de zones usen el seu últim
    resum guardat al cache (data/weather_block_cache.json).

    IMPORTANT: es desa només el RESUM compacte (rain_10d, avg_temp,
    min_temp, days_since_rain + soil_stats — uns 10 números per punt), NO
    el bloc 'daily'/'hourly' complet tal com arriba d'Open-Meteo (17 dies
    x 24h x 3 variables = 1275 valors per punt). Es va detectar un cas
    real: guardant l'històric complet per als ~7300 punts, el fitxer de
    cache pesava 108 MB — GitHub rebutja fitxers de més de 100 MB. Amb el
    resum, el pes és uns 100x més petit.

    Retorna una llista de tuples (rain_stats, soil_stats) en el mateix
    ordre que 'zones', ja processades — build_results() ja no ha de cridar
    compute_rain_stats/compute_soil_moisture_stats pel seu compte.

    Si una zona encara no té cap valor al cache (per exemple, punts nous
    del Pirineu recuperats fa poc), es consulta igualment encara que no li
    toqui el torn — millor una petició extra que una zona sense cap dada.
    """
    blocks = assign_weather_blocks(zones)
    current_block = load_weather_turn()
    cache = load_weather_block_cache()

    zones_to_fetch = [z for z in zones if blocks[z["id"]] == current_block or cell_key(z["lat"], z["lon"]) not in cache]
    ids_to_fetch = {z["id"] for z in zones_to_fetch}
    zones_from_cache = [z for z in zones if z["id"] not in ids_to_fetch]

    print(f"  Blocs rotatius: torn del bloc {current_block}/{WEATHER_N_BLOCKS - 1} — "
          f"{len(zones_to_fetch)} punts a refrescar, {len(zones_from_cache)} des del cache")

    fresh_raw = fetch_weather(zones_to_fetch)
    for z, raw in zip(zones_to_fetch, fresh_raw):
        if not raw:
            continue  # placeholder buit d'un lot fallat — no es desa, es reintenta la propera
        daily = raw.get("daily", {})
        hourly = raw.get("hourly", {})
        key = cell_key(z["lat"], z["lon"])
        rain_10d, avg_temp, min_temp, days_since_rain = compute_rain_stats(daily)
        soil_stats = compute_soil_moisture_stats(hourly)
        entry = {
            "rain_10d": rain_10d, "avg_temp": avg_temp, "min_temp": min_temp,
            "days_since_rain": days_since_rain, "soil_stats": soil_stats,
        }
        # Sèrie diària pròpia (veure "3b"): fusiona els 16 dies nous amb els
        # que el punt ja tenia, fins a SERIES_MAX_DAYS.
        series = merge_daily_series((cache.get(key) or {}).get("series"), daily)
        if series:
            entry["series"] = series
        cache[key] = entry

    # La graella pot haver canviat (p. ex. en eliminar punts duplicats):
    # no s'arrosseguen entrades de punts que ja no existeixen.
    valid_keys = {cell_key(z["lat"], z["lon"]) for z in zones}
    cache = {k: v for k, v in cache.items() if k in valid_keys}
    save_weather_block_cache(cache)

    next_block = (current_block + 1) % WEATHER_N_BLOCKS
    save_weather_turn(next_block)

    # Reconstrueix la llista final en el mateix ordre que 'zones'
    all_results = []
    for z in zones:
        key = cell_key(z["lat"], z["lon"])
        all_results.append(cache.get(key, {}))
    return all_results


def compute_soil_moisture_stats(hourly):
    """
    A partir del bloc 'hourly' d'Open-Meteo (soil_moisture_9_27cm,
    et0_fao_evapotranspiration i relative_humidity_2m), calcula:
    - soil_moisture_now: valor més recent d'humitat del sòl (m³/m³, 0-1)
    - soil_moisture_avg_7d: mitjana dels últims 7 dies
    - soil_moisture_trend: diferència entre la mitjana dels últims 3 dies i
      la dels 3 dies anteriors — positiu si el sòl s'està humitejant, negatiu
      si s'està assecant, encara que hagi plogut recentment
    - evapotranspiration_7d: evapotranspiració acumulada 7 dies (quanta
      aigua "es perd" cap a l'atmosfera/plantes — a més evapotranspiració,
      menys queda realment disponible al sòl per molt que hagi plogut)
    - air_humidity_avg_3d: mitjana d'humitat relativa de l'aire dels últims
      3 dies (%) — complementa la del sòl: un aire molt sec pot ressecar la
      capa més superficial i el mateix barret del bolet encara que el sòl
      profund segueixi humit

    Aquestes dades permeten distingir "50mm sobre sòl ja humit" de "50mm
    sobre sòl ressec que se'ls beu" — la pluja per si sola no ho fa.
    """
    moisture = hourly.get("soil_moisture_9_27cm") or []
    evapo = hourly.get("et0_fao_evapotranspiration") or []
    air_humidity = hourly.get("relative_humidity_2m") or []

    valid_moisture = [v for v in moisture if v is not None]
    if not valid_moisture:
        return None

    soil_moisture_now = round(valid_moisture[-1], 3)

    last_7d_hours = 7 * 24
    last_3d_hours = 3 * 24
    recent_window = [v for v in moisture[-last_7d_hours:] if v is not None]
    soil_moisture_avg_7d = round(sum(recent_window) / len(recent_window), 3) if recent_window else None

    last_3d = [v for v in moisture[-last_3d_hours:] if v is not None]
    prev_3d = [v for v in moisture[-2 * last_3d_hours:-last_3d_hours] if v is not None]
    trend = None
    if last_3d and prev_3d:
        trend = round((sum(last_3d) / len(last_3d)) - (sum(prev_3d) / len(prev_3d)), 4)

    evapo_7d_values = [v for v in evapo[-last_7d_hours:] if v is not None]
    evapotranspiration_7d = round(sum(evapo_7d_values), 1) if evapo_7d_values else None

    air_humidity_values = [v for v in air_humidity[-last_3d_hours:] if v is not None]
    air_humidity_avg_3d = round(sum(air_humidity_values) / len(air_humidity_values), 1) if air_humidity_values else None

    return {
        "soil_moisture_now": soil_moisture_now,
        "soil_moisture_avg_7d": soil_moisture_avg_7d,
        "soil_moisture_trend": trend,
        "evapotranspiration_7d": evapotranspiration_7d,
        "air_humidity_avg_3d": air_humidity_avg_3d,
    }


def compute_rain_stats(daily):
    """A partir del bloc 'daily' d'Open-Meteo, calcula pluja acumulada, temperatures i
    dies des de l'inici de la tanda de pluges.

    IMPORTANT: per al scoring de bolets s'usa min_temp (mitjana de les mínimes nocturnes),
    no la mitjana dia/nit. Un bolet reacciona al fred de la matinada després de la pluja,
    no a la temperatura de la tarda — una mitjana dia/nit pot amagar nits ja prou fresques
    encara que les tardes segueixin sent caloroses (típic de finals d'estiu al Pirineu).

    IMPORTANT: la pluja acumulada es compta des de l'INICI de la tanda de pluges actual
    (no una finestra fixa de 10 dies), perquè amb tandes llargues (pluges repetides durant
    12-14 dies, com és habitual al Pirineu a finals d'estiu) una finestra fixa perdria
    pluja real caiguda a l'inici de la tanda. Es limita a un màxim de 16 dies (l'històric
    disponible) per no arrossegar pluja d'una tanda anterior ja seca fa temps.
    """
    precip = daily.get("precipitation_sum") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []

    days_since_rain = compute_days_since_rain_episode_start(precip)

    # Pluja acumulada des de l'inici de la tanda (mínim 10 dies, màxim tot l'històric)
    window = max(10, min(days_since_rain, len(precip) - 1 if precip else 10))
    rain_window = precip[-(window + 1):-1] if len(precip) >= window + 1 else precip[:-1]
    rain_10d = round(sum(p or 0 for p in rain_window))

    # Temperatures: es calculen sobre els mateixos dies que la pluja acumulada
    temp_window_max = tmax[-(window + 1):-1] if len(tmax) >= window + 1 else tmax[:-1]
    temp_window_min = tmin[-(window + 1):-1] if len(tmin) >= window + 1 else tmin[:-1]
    n = max(len(temp_window_max), 1)
    avg_temp = round(
        (sum(t or 0 for t in temp_window_max) / n + sum(t or 0 for t in temp_window_min) / n) / 2
    )
    min_temp = round(sum(t or 0 for t in temp_window_min) / n)

    return rain_10d, avg_temp, min_temp, days_since_rain


def compute_days_since_rain_episode_start(precip):
    """
    Calcula els dies transcorreguts des de l'INICI de la darrera tanda de pluges,
    no des de l'últim xàfec puntual. Amb pluges repetides en pocs dies (típic de
    tempestes d'estiu/tardor al Pirineu), l'última pluja forta pot haver caigut
    ahir mateix, però si la tanda va començar fa 8-10 dies el sòl porta prou temps
    humit perquè el bolet hagi pogut sortir — comptar només des de l'últim xàfec
    donaria sempre "fa 0-1 dies", cosa que no reflecteix la realitat.

    Mètode: partint del dia més recent amb pluja, es retrocedeix comptant dies,
    permetent com a màxim 1 dia sec seguit enmig de la tanda (típic entre xàfecs
    d'un mateix episodi). Es compten TOTS els dies recorreguts (plujosos o no)
    fins que es troben 2 dies secs seguits — aquest total és l'antiguitat de la
    tanda, no només la posició del primer dia amb pluja.
    """
    if not precip or len(precip) < 2:
        return 20

    # precip[-1] és avui/parcial, l'ignorem; treballem amb els dies complets anteriors
    days = precip[:-1]
    n = len(days)
    if n == 0:
        return 20

    i = n - 1
    # Si el dia més recent no ha plogut gens, no estem en una tanda activa ara mateix
    if (days[i] or 0) < 3:
        for j in range(i, -1, -1):
            if (days[j] or 0) >= 5:
                return n - j
        return 20

    # Estem en una tanda activa: comptem dies enrere (incloent els secs intermedis)
    # fins trobar 2 dies secs seguits, que marquen el final de la tanda anterior.
    dry_streak = 0
    days_counted = 0
    while i >= 0:
        if (days[i] or 0) < 3:
            dry_streak += 1
            if dry_streak >= 2:
                days_counted -= 1  # el dia sec que confirma el final no forma part de la tanda
                break
        else:
            dry_streak = 0
        days_counted += 1
        i -= 1

    return max(1, days_counted)


# ---------------------------------------------------------------------------
# 3b. SÈRIE DIÀRIA PRÒPIA I ESDEVENIMENTS DE PLUJA
# ---------------------------------------------------------------------------
# Problemes reals detectats el 15/10/2026 comparant amb estacions:
#
# 1) El "temps des de la pluja" es comptava des de l'ÚLTIM dia amb >= 5 mm.
#    El 4/10 van caure ~170 mm a Montnegre i ~100 mm a Castellar/Matadepera
#    (Meteoclimatic), però un ruixat de 3-7 mm el dia 8 reiniciava el rellotge
#    i el model deia "fa 7 dies" quan la pluja forta era de fa 11. Ara es
#    detecten ESDEVENIMENTS de pluja (tandes de dies plujosos amb buits
#    curts) i es data cada un pel dia en què havia caigut la meitat de
#    l'aigua (el "gruix" de la remullada), no pel primer ni l'últim dia.
#
# 2) Open-Meteo només dona 16 dies d'històric, però espècies com l'ou de
#    reig (15-20 dies) o els camagrocs/trompetes (fins a 20) necessiten
#    veure més enrere. Demanar 30+ dies a Open-Meteo multiplica el cost de
#    cada crida (el servei gratuït ja s'havia saturat), així que en comptes
#    d'això cada punt acumula la seva PRÒPIA sèrie diària (pluja, màx i mín)
#    fusionant cada refresc de 16 dies amb el que ja tenia, fins a 45 dies.
#    Els primers dies després de desplegar-ho només hi haurà els 16 dies
#    habituals; la memòria va creixent sola.
SERIES_MAX_DAYS = 45
RAIN_WET_DAY_MM = 2.0        # dia "plujós" (per agrupar esdeveniments)
RAIN_EVENT_GAP_DAYS = 4      # fins a 4 dies secs seguits dins del mateix esdeveniment
RAIN_EVENT_MIN_MM = 8.0      # menys d'això no és una remullada rellevant
NO_EVENT_DAYS = 20           # sentinella heretada: "cap pluja rellevant visible"


def today_madrid():
    """Data d'avui a Catalunya (Open-Meteo dona els dies en Europe/Madrid;
    el servidor de GitHub va en UTC, que pot anar 1-2h per darrere)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Madrid")).date()
    except Exception:
        return (datetime.now(timezone.utc) + timedelta(hours=2)).date()


def _round1(v):
    return None if v is None else round(float(v), 1)


def merge_daily_series(old_series, daily):
    """Fusiona la sèrie diària ja guardada d'un punt amb el bloc 'daily'
    acabat de rebre d'Open-Meteo (els valors nous manen sobre els vells).
    Retorna {"d0": "YYYY-MM-DD", "p": [...], "x": [...], "n": [...]}:
    pluja (mm), temperatura màxima i mínima diàries, dies consecutius, amb
    None quan no hi ha dada, com a molt SERIES_MAX_DAYS dies."""
    by_date = {}
    if old_series and old_series.get("d0"):
        try:
            d0 = datetime.fromisoformat(old_series["d0"]).date()
            for i, (p, x, n) in enumerate(zip(old_series["p"], old_series["x"], old_series["n"])):
                by_date[d0 + timedelta(days=i)] = (p, x, n)
        except (ValueError, KeyError, TypeError):
            by_date = {}

    times = (daily or {}).get("time") or []
    prec = (daily or {}).get("precipitation_sum") or []
    tmax = (daily or {}).get("temperature_2m_max") or []
    tmin = (daily or {}).get("temperature_2m_min") or []
    for i, t in enumerate(times):
        try:
            d = datetime.fromisoformat(t).date()
        except (ValueError, TypeError):
            continue
        new = (
            _round1(prec[i]) if i < len(prec) else None,
            _round1(tmax[i]) if i < len(tmax) else None,
            _round1(tmin[i]) if i < len(tmin) else None,
        )
        if all(v is None for v in new):
            continue  # no s'esborra una dada bona amb un forat nou
        by_date[d] = new

    if not by_date:
        return old_series
    last = max(by_date)
    first = max(min(by_date), last - timedelta(days=SERIES_MAX_DAYS - 1))
    p_list, x_list, n_list = [], [], []
    d = first
    while d <= last:
        p, x, n = by_date.get(d, (None, None, None))
        p_list.append(p); x_list.append(x); n_list.append(n)
        d += timedelta(days=1)
    return {"d0": first.isoformat(), "p": p_list, "x": x_list, "n": n_list}


def detect_rain_events(precip):
    """
    Detecta esdeveniments de pluja a una llista de mm/dia en ordre
    cronològic on l'ÚLTIM element és AHIR. Un esdeveniment és un grup de dies
    plujosos (>= RAIN_WET_DAY_MM) amb com a molt RAIN_EVENT_GAP_DAYS dies
    secs seguits entre ells; es descarten els de menys de RAIN_EVENT_MIN_MM.

    Per a cada un retorna (més antic primer):
    - age_start / age_end: dies des del primer / últim dia plujós fins avui
      (ahir = 1)
    - age_mid: dies des del dia en què ja havia caigut la meitat de l'aigua
      (el "gruix" de la remullada; és la referència per a la fructificació)
    - mm: pluja de l'esdeveniment; mm_since: pluja des de l'inici fins ahir
      (inclou ruixats lleus posteriors)
    """
    vals = [(p or 0.0) for p in precip]
    n = len(vals)
    wet_idx = [i for i, v in enumerate(vals) if v >= RAIN_WET_DAY_MM]
    groups = []
    for i in wet_idx:
        if groups and i - groups[-1][1] - 1 <= RAIN_EVENT_GAP_DAYS:
            groups[-1][1] = i
        else:
            groups.append([i, i])
    events = []
    for s, e in groups:
        mm = sum(vals[s:e + 1])
        if mm < RAIN_EVENT_MIN_MM:
            continue
        half, cum, mid = mm / 2.0, 0.0, s
        for i in range(s, e + 1):
            cum += vals[i]
            if cum >= half:
                mid = i
                break
        events.append({
            "age_start": n - s, "age_end": n - e, "age_mid": n - mid,
            "mm": round(mm, 1), "mm_since": round(sum(vals[s:]), 1),
        })
    return events


def derive_weather_view(entry, today=None):
    """
    A partir de l'entrada del cache de blocs d'un punt retorna el que necessita
    el scoring, calculat sempre amb la DATA D'AVUI (no amb la del moment del
    refresc, que pot tenir fins a 12h):
    - events: esdeveniments de pluja (veure detect_rain_events)
    - tmin_7d / tmax_7d: mitjana de mínimes i màximes dels darrers 7 dies
    - rain_10d / days_since_rain / min_temp / avg_temp: camps heretats que la
      web mostra (rain_10d = pluja des de l'inici de l'últim esdeveniment;
      days_since_rain = dies des del gruix d'aquest esdeveniment)
    - has_series: False si el punt encara no té sèrie pròpia (primeres
      execucions després d'actualitzar): llavors es fa servir el resum antic.
    """
    today = today or today_madrid()
    series = (entry or {}).get("series")
    legacy = {
        "rain_10d": (entry or {}).get("rain_10d", 0),
        "avg_temp": (entry or {}).get("avg_temp", 0),
        "min_temp": (entry or {}).get("min_temp", 0),
        "days_since_rain": (entry or {}).get("days_since_rain", NO_EVENT_DAYS),
        "soil_stats": (entry or {}).get("soil_stats"),
    }
    if not series or not series.get("d0"):
        view = dict(legacy)
        view.update({"events": None, "tmin_7d": None, "tmax_7d": None, "has_series": False})
        return view

    try:
        d0 = datetime.fromisoformat(series["d0"]).date()
    except (ValueError, TypeError):
        view = dict(legacy)
        view.update({"events": None, "tmin_7d": None, "tmax_7d": None, "has_series": False})
        return view

    # Només dies COMPLETS (fins ahir): el d'avui és parcial / previsió.
    n_days = (today - d0).days            # nombre de dies des de d0 fins ahir
    n_days = max(0, n_days)
    p, x, n = series["p"], series["x"], series["n"]
    precip = [(p[i] if i < len(p) else None) for i in range(n_days)]
    tmax_l = [(x[i] if i < len(x) else None) for i in range(n_days)]
    tmin_l = [(n[i] if i < len(n) else None) for i in range(n_days)]

    events = detect_rain_events(precip)

    def avg_last(lst, k):
        vals = [v for v in lst[-k:] if v is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    tmin_7d, tmax_7d = avg_last(tmin_l, 7), avg_last(tmax_l, 7)
    view = dict(legacy)
    if events:
        last = events[-1]
        view["days_since_rain"] = last["age_mid"]
        view["rain_10d"] = round(last["mm_since"])
    else:
        view["days_since_rain"] = NO_EVENT_DAYS
        view["rain_10d"] = round(sum((v or 0.0) for v in precip[-10:]))
    if tmin_7d is not None and tmax_7d is not None:
        view["min_temp"] = round(tmin_7d)
        view["avg_temp"] = round((tmin_7d + tmax_7d) / 2)
    view.update({"events": events, "tmin_7d": tmin_7d, "tmax_7d": tmax_7d, "has_series": True})
    return view


# ---------------------------------------------------------------------------
# 4. AEMET — ESTACIONS REALS DE CONTRAST
# ---------------------------------------------------------------------------

def fetch_aemet_observations(api_key, timeout=20):
    """Consulta AEMET OpenData (observació convencional, totes les estacions)."""
    if not api_key:
        return []
    req1 = urllib.request.Request(
        f"{AEMET_STATIONS_URL}?api_key={api_key}",
        headers={"User-Agent": "bolets-catalunya-app/1.0"},
    )
    with urllib.request.urlopen(req1, timeout=timeout) as resp:
        meta = json.loads(resp.read().decode("utf-8"))

    data_url = meta.get("datos")
    if not data_url:
        return []

    req2 = urllib.request.Request(data_url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    with urllib.request.urlopen(req2, timeout=timeout) as resp:
        raw = resp.read().decode("latin-1")
    stations = json.loads(raw)

    parsed = []
    for st in stations:
        try:
            lat = float(st.get("lat", 0))
            lon = float(st.get("lon", 0))
        except (TypeError, ValueError):
            continue
        if lat == 0 or lon == 0:
            continue
        parsed.append({
            "lat": lat, "lon": lon, "name": st.get("ubi", "?"),
            "prec_1h": st.get("prec"), "fint": st.get("fint"),
        })
    return parsed


def nearest_aemet_station(lat, lon, stations, max_km=40):
    best, best_dist = None, max_km
    for st in stations:
        d = haversine_km(lat, lon, st["lat"], st["lon"])
        if d < best_dist:
            best, best_dist = st, d
    if best:
        return {**best, "distance_km": round(best_dist, 1)}
    return None


# ---------------------------------------------------------------------------
# 4c. AEMET — RADAR REGIONAL (precipitació acumulada, cobertura de superfície)
# ---------------------------------------------------------------------------
# A diferència de les estacions puntuals (per moltes que en tinguem, sempre
# hi ha "punts cecs" entre elles), el radar dona cobertura contínua de
# superfície — important per detectar tempestes molt localitzades que caiguin
# entre estacions. Format GeoTIFF (EPSG:4326), es processa amb rasterio.
# Codi de radar "ba" (Barcelona) confirmat contra la documentació oficial.
#
# DESACTIVAT A PROPÒSIT (AEMET_RADAR_ENABLED = False): la imatge que retorna
# l'endpoint /api/red/radar/regional/{radar} NO porta georeferenciació real
# (verificat: CRS=None, transform=identitat) — descartar-la evita fer servir
# coordenades incorrectes. El codi es conserva intacte per si en el futur es
# descobreix com obtenir el producte realment georeferenciat d'AEMET; per
# reactivar-lo només cal canviar aquesta constant a True.
AEMET_RADAR_ENABLED = False

AEMET_RADAR_CODE = "ba"  # Barcelona — confirmat contra la documentació oficial d'AEMET OpenData
AEMET_RADAR_MAX_AGE_MINUTES = 30  # el radar s'actualitza cada ~10 min; si la imatge és més vella, es descarta


def fetch_aemet_radar_geotiff(api_key, radar_code=AEMET_RADAR_CODE, timeout=25):
    """
    Descarrega la imatge de precipitació acumulada del radar regional
    d'AEMET, seguint el mateix patró de dues peticions que la resta de
    l'API d'AEMET (primera petició retorna una URL temporal amb les dades
    reals, vàlida ~5 minuts).

    Retorna els bytes de la imatge GeoTIFF, o None si no s'ha pogut obtenir.
    """
    url = f"https://opendata.aemet.es/opendata/api/red/radar/regional/{radar_code}"
    req = urllib.request.Request(url, headers={"api_key": api_key, "User-Agent": "bolets-catalunya-app/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        meta = json.loads(resp.read().decode("utf-8"))

    if meta.get("estado") != 200:
        raise Exception(f"AEMET radar ha retornat estat {meta.get('estado')}: {meta.get('descripcion')}")

    data_url = meta["datos"]
    data_req = urllib.request.Request(data_url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    with urllib.request.urlopen(data_req, timeout=timeout) as resp:
        content_type = resp.headers.get("Content-Type", "")
        image_bytes = resp.read()

    if "image" not in content_type and not image_bytes[:4] in (b"II*\x00", b"MM\x00*"):
        # Capçalera TIFF esperada; si no hi és, probablement s'ha rebut un
        # error JSON en comptes de la imatge (per exemple, radar fora de servei).
        raise Exception(f"La resposta no sembla un GeoTIFF vàlid (content-type: {content_type})")

    return image_bytes


def extract_radar_value_at_point(geotiff_bytes, lat, lon):
    """
    Llegeix un GeoTIFF (en memòria, sense escriure a disc) i retorna el
    valor de precipitació acumulada en unes coordenades concretes, o None
    si el punt cau fora de la imatge o la banda no té dada vàlida allà.
    """
    from rasterio.io import MemoryFile

    with MemoryFile(geotiff_bytes) as memfile:
        with memfile.open() as src:
            try:
                row, col = src.index(lon, lat)
            except Exception:
                return None
            if row < 0 or row >= src.height or col < 0 or col >= src.width:
                return None
            window = src.read(1, window=((row, row + 1), (col, col + 1)))
            if window.size == 0:
                return None
            value = float(window[0, 0])
            nodata = src.nodata
            if nodata is not None and value == nodata:
                return None
            return value


def build_radar_lookup(api_key, zones):
    """
    Descarrega la imatge de radar un cop, i extreu el valor de precipitació
    acumulada per a totes les zones de cop (molt més eficient que descarregar
    la imatge sencera per cada punt). Retorna un diccionari {zone_id: mm} —
    només amb els punts on s'ha pogut extreure un valor vàlid.

    Si la descàrrega o el processament falla per qualsevol motiu (imatge no
    disponible, format inesperat, llibreria no disponible, o la imatge no
    porta georeferenciació real), es retorna un diccionari buit i es
    continua sense radar — mai trenca la resta del càlcul, i mai s'usen
    valors que podrien no correspondre a les coordenades correctes.
    """
    try:
        geotiff_bytes = fetch_aemet_radar_geotiff(api_key)
    except Exception as e:
        print(f"  AVÍS: no s'ha pogut descarregar el radar AEMET ({e}) — es continua sense radar")
        return {}

    from rasterio.io import MemoryFile
    with MemoryFile(geotiff_bytes) as memfile:
        with memfile.open() as src:
            has_crs = src.crs is not None
            is_identity = src.transform.is_identity if src.transform else True
            print(f"  Radar diagnòstic: CRS={src.crs}, transform_identity={is_identity}, bounds={src.bounds}")
            if not has_crs or is_identity:
                print("  AVÍS: la imatge del radar no porta georeferenciació real (CRS absent o transform identitat) "
                      "— es descarta per complet per no fer servir coordenades incorrectes")
                return {}

    lookup = {}
    errors = 0
    for z in zones:
        try:
            value = extract_radar_value_at_point(geotiff_bytes, z["lat"], z["lon"])
            if value is not None and value >= 0:
                lookup[z["id"]] = round(value, 1)
        except Exception:
            errors += 1
    if errors:
        print(f"  AVÍS: {errors} punts han fallat en extreure el valor del radar")
    return lookup


# ---------------------------------------------------------------------------
# 4d. RAINVIEWER — RADAR AGREGAT (mosaic europeu, sense clau, cobertura de superfície)
# ---------------------------------------------------------------------------
# Alternativa al radar d'AEMET (que no dona la imatge realment georeferenciada
# en l'endpoint que fem servir). RainViewer agrega dades de moltes xarxes de
# radar (incloent AEMET i Meteocat) en un mosaic amb teseŀles XYZ estàndard
# (Web Mercator), documentat oficialment i sense necessitat de clau.
#
# El valor que es rep és un COLOR (RGBA), no un mm directe — es tradueix a
# dBZ buscant el color més proper a la taula oficial "Universal Blue" (l'únic
# esquema realment documentat per RainViewer), i després es converteix dBZ a
# mm/h amb la relació de Marshall-Palmer (la mateixa que fa servir AEMET):
# Z = 200 * R^1.6  →  R = (Z/200)^(1/1.6), on Z = 10^(dBZ/10).
#
# Nota: la taula de colors pel tram de dBZ molt baixos (-10 a 14, semi-
# transparent, sense pluja significativa) és una aproximació dins d'aquest
# rang — el tram que realment importa per detectar pluja (15-95 dBZ) prové
# exactament del CSV oficial de RainViewer.

RAINVIEWER_UNIVERSAL_BLUE_TABLE = (
    (-32, 0, 0, 0, 0), (-31, 0, 0, 0, 0), (-30, 0, 0, 0, 0), (-29, 0, 0, 0, 0),
    (-28, 0, 0, 0, 0), (-27, 0, 0, 0, 0), (-26, 0, 0, 0, 0), (-25, 0, 0, 0, 0),
    (-24, 0, 0, 0, 0), (-23, 0, 0, 0, 0), (-22, 0, 0, 0, 0), (-21, 0, 0, 0, 0),
    (-20, 0, 0, 0, 0), (-19, 0, 0, 0, 0), (-18, 0, 0, 0, 0), (-17, 0, 0, 0, 0),
    (-16, 0, 0, 0, 0), (-15, 0, 0, 0, 0), (-14, 0, 0, 0, 0), (-13, 0, 0, 0, 0),
    (-12, 0, 0, 0, 0), (-11, 0, 0, 0, 0), (-10, 99, 97, 89, 20), (-9, 102, 99, 90, 25),
    (-8, 105, 102, 92, 30), (-7, 108, 104, 93, 36), (-6, 111, 107, 95, 41), (-5, 114, 110, 97, 46),
    (-4, 117, 112, 98, 52), (-3, 120, 115, 100, 57), (-2, 124, 117, 101, 62), (-1, 127, 120, 103, 68),
    (0, 130, 123, 105, 73), (1, 133, 125, 106, 78), (2, 136, 128, 108, 84), (3, 139, 130, 109, 89),
    (4, 142, 133, 111, 94), (5, 146, 136, 113, 100), (6, 158, 147, 117, 110), (7, 170, 158, 121, 120),
    (8, 182, 169, 126, 130), (9, 194, 180, 130, 140), (10, 206, 192, 135, 150), (11, 210, 196, 139, 160),
    (12, 214, 200, 143, 170), (13, 218, 204, 147, 180), (14, 222, 208, 151, 190), (15, 136, 221, 238, 255),
    (16, 108, 209, 235, 255), (17, 81, 197, 232, 255), (18, 54, 186, 229, 255), (19, 27, 174, 226, 255),
    (20, 0, 163, 224, 255), (21, 0, 154, 213, 255), (22, 0, 145, 202, 255), (23, 0, 136, 191, 255),
    (24, 0, 127, 180, 255), (25, 0, 119, 170, 255), (26, 0, 112, 163, 255), (27, 0, 105, 156, 255),
    (28, 0, 98, 149, 255), (29, 0, 91, 142, 255), (30, 0, 85, 136, 255), (31, 0, 81, 128, 255),
    (32, 0, 78, 120, 255), (33, 0, 74, 112, 255), (34, 0, 71, 104, 255), (35, 255, 238, 0, 255),
    (36, 255, 224, 0, 255), (37, 255, 210, 0, 255), (38, 255, 197, 0, 255), (39, 255, 183, 0, 255),
    (40, 255, 170, 0, 255), (41, 255, 159, 0, 255), (42, 255, 149, 0, 255), (43, 255, 139, 0, 255),
    (44, 255, 129, 0, 255), (45, 255, 68, 0, 255), (46, 242, 54, 0, 255), (47, 230, 40, 0, 255),
    (48, 217, 27, 0, 255), (49, 205, 13, 0, 255), (50, 193, 0, 0, 255), (51, 168, 0, 0, 255),
    (52, 143, 0, 0, 255), (53, 118, 0, 0, 255), (54, 93, 0, 0, 255), (55, 255, 170, 255, 255),
    (56, 255, 159, 255, 255), (57, 255, 149, 255, 255), (58, 255, 139, 255, 255), (59, 255, 129, 255, 255),
    (60, 255, 119, 255, 255), (61, 255, 108, 255, 255), (62, 255, 98, 255, 255), (63, 255, 88, 255, 255),
    (64, 255, 78, 255, 255), (65, 255, 255, 255, 255), (66, 255, 255, 255, 255), (67, 255, 255, 255, 255),
    (68, 255, 255, 255, 255), (69, 255, 255, 255, 255), (70, 255, 255, 255, 255), (71, 255, 255, 255, 255),
    (72, 255, 255, 255, 255), (73, 255, 255, 255, 255), (74, 255, 255, 255, 255), (75, 0, 255, 0, 255),
    (76, 0, 255, 0, 255), (77, 0, 255, 0, 255), (78, 0, 255, 0, 255), (79, 0, 255, 0, 255),
    (80, 0, 255, 0, 255), (81, 0, 255, 0, 255), (82, 0, 255, 0, 255), (83, 0, 255, 0, 255),
    (84, 0, 255, 0, 255), (85, 0, 255, 0, 255), (86, 0, 255, 0, 255), (87, 0, 255, 0, 255),
    (88, 0, 255, 0, 255), (89, 0, 255, 0, 255), (90, 0, 255, 0, 255), (91, 0, 255, 0, 255),
    (92, 0, 255, 0, 255), (93, 0, 255, 0, 255), (94, 0, 255, 0, 255), (95, 0, 255, 0, 255),
)

RAINVIEWER_ZOOM = 7  # màxim permès pel pla gratuït/ús personal
RAINVIEWER_TILE_SIZE = 256


def latlon_to_tile_pixel(lat, lon, zoom=RAINVIEWER_ZOOM, tile_size=RAINVIEWER_TILE_SIZE):
    """Converteix lat/lon al sistema estàndard de teseŀles Web Mercator
    (el mateix que Google Maps, OpenStreetMap i RainViewer)."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    tile_x, tile_y = int(x), int(y)
    pixel_x = int((x - tile_x) * tile_size)
    pixel_y = int((y - tile_y) * tile_size)
    return tile_x, tile_y, pixel_x, pixel_y


def rgba_to_dbz(r, g, b, a, max_distance=60):
    """Troba el dBZ de la taula Universal Blue amb el color RGBA més proper
    (distància euclidiana). Si el píxel és transparent (a=0) o el color no
    s'assembla prou a cap entrada de la taula (per exemple, és el mapa base,
    no radar), retorna None — no s'inventa un valor de pluja."""
    if a is not None and a < 10:
        return None  # transparent = sense cobertura de radar en aquest punt
    best_dbz, best_dist = None, max_distance
    for dbz, tr, tg, tb, ta in RAINVIEWER_UNIVERSAL_BLUE_TABLE:
        dist = ((r - tr) ** 2 + (g - tg) ** 2 + (b - tb) ** 2) ** 0.5
        if dist < best_dist:
            best_dbz, best_dist = dbz, dist
    return best_dbz


def dbz_to_mm_per_hour(dbz):
    """Relació de Marshall-Palmer (Z=200·R^1.6), la mateixa que fa servir
    AEMET per convertir reflectivitat a intensitat de pluja."""
    if dbz is None or dbz < 0:
        return 0.0
    z = 10 ** (dbz / 10)
    r = (z / 200) ** (1 / 1.6)
    return round(r, 2)


def fetch_rainviewer_frame_info(timeout=15):
    """Consulta quin és el fotograma de radar més recent disponible."""
    url = "https://api.rainviewer.com/public/weather-maps.json"
    req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    past_frames = data.get("radar", {}).get("past", [])
    if not past_frames:
        raise Exception("RainViewer no ha retornat cap fotograma disponible")
    latest = past_frames[-1]
    return data["host"], latest["path"]


def fetch_rainviewer_tile(host, path, tile_x, tile_y, zoom=RAINVIEWER_ZOOM, timeout=15):
    """Descarrega una tessel·la PNG concreta amb l'esquema de color Universal
    Blue (color=2, l'únic realment documentat per RainViewer)."""
    url = f"{host}{path}/{RAINVIEWER_TILE_SIZE}/{zoom}/{tile_x}/{tile_y}/2/1_1.png"
    req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def build_rainviewer_lookup(zones):
    """
    Per a totes les zones, calcula quina tessel·la (x,y a zoom 7) els
    correspon, descarrega només les tessel·les úniques necessàries (moltes
    zones cauen a la mateixa tessel·la, ja que Catalunya és petita a zoom 7),
    i extreu el valor de pluja (mm/h) de cada punt llegint el píxel exacte.

    Retorna (lookup, connection_ok). connection_ok reflecteix si el servei
    ha respost correctament — és independent de si hi havia pluja: un dia
    sense pluja a Catalunya és una resposta vàlida (tots els punts
    transparents), no un error, i no s'ha de comptar com a "font incompleta".

    Si qualsevol pas falla de debò (servei caigut, format inesperat), es
    retorna un diccionari buit amb connection_ok=False — mai trenca la resta.
    """
    try:
        from PIL import Image
        import io
    except ImportError:
        print("  AVÍS: Pillow no disponible — es continua sense RainViewer")
        return {}, False

    try:
        host, path = fetch_rainviewer_frame_info()
    except Exception as e:
        print(f"  AVÍS: no s'ha pogut consultar RainViewer ({e}) — es continua sense aquesta font")
        return {}, False

    zone_tiles = {}
    for z in zones:
        tx, ty, px, py = latlon_to_tile_pixel(z["lat"], z["lon"])
        zone_tiles.setdefault((tx, ty), []).append((z["id"], px, py))

    lookup = {}
    tiles_ok, tiles_failed = 0, 0
    transparent_count, no_match_count, sample_pixels = 0, 0, []
    for (tx, ty), points in zone_tiles.items():
        try:
            png_bytes = fetch_rainviewer_tile(host, path, tx, ty)
            img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            tiles_ok += 1
        except Exception:
            tiles_failed += 1
            continue
        for zone_id, px, py in points:
            try:
                r, g, b, a = img.getpixel((px, py))
                if len(sample_pixels) < 5:
                    sample_pixels.append((zone_id, r, g, b, a))
                if a is not None and a < 10:
                    transparent_count += 1
                    continue
                dbz = rgba_to_dbz(r, g, b, a)
                if dbz is not None:
                    lookup[zone_id] = dbz_to_mm_per_hour(dbz)
                else:
                    no_match_count += 1
            except Exception:
                continue

    print(f"  RainViewer: {tiles_ok} tessel·les llegides, {tiles_failed} fallades")
    print(f"  RainViewer diagnòstic: {transparent_count} punts transparents (sense pluja), "
          f"{no_match_count} punts amb color sense coincidència a la taula, {len(lookup)} amb valor")
    print(f"  RainViewer mostra de píxels (zone_id, r, g, b, a): {sample_pixels}")
    # La connexió es considera correcta si s'ha llegit almenys una tessel·la
    # (independentment de si aquell dia hi havia pluja o no).
    connection_ok = tiles_ok > 0
    return lookup, connection_ok


# ---------------------------------------------------------------------------
# 4b. METEOCAT / XEMA — TERCERA XARXA D'ESTACIONS REALS
# ---------------------------------------------------------------------------
# Xarxa oficial de la Generalitat (~190 estacions), la més densa de les tres
# que fem servir. A diferència de Meteoclimatic, l'API ja dona coordenades
# directament — no cal geocodificar res. El codi de variable de precipitació
# és el 35 (confirmat contra la documentació oficial i un client de tercers
# independent). Les metadades d'estacions es cauegen (les coordenades no
# canvien mai) i les lectures es consulten fresques cada execució.

METEOCAT_BASE_URL = "https://api.meteo.cat/xema/v1"
METEOCAT_PRECIP_VARIABLE = 35
METEOCAT_STATIONS_CACHE_PATH = "../data/meteocat_stations_cache.json"
METEOCAT_STATIONS_CACHE_MAX_DAYS = 90


def fetch_meteocat_station_metadata(api_key, timeout=20):
    """Consulta les metadades de totes les estacions XEMA operatives (codi,
    nom, coordenades, altitud) — inclou lat/lon directament, no cal geocodificar."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d") + "Z"
    url = f"{METEOCAT_BASE_URL}/estacions/metadades?estat=ope&data={today_str}"
    req = urllib.request.Request(url, headers={
        "X-Api-Key": api_key, "User-Agent": "bolets-catalunya-app/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        print(f"    [DEBUG Meteocat] HTTP {e.code} a {url}")
        print(f"    [DEBUG Meteocat] Cos de l'error: {error_body[:500]}")
        raise

    parsed = []
    for st in data:
        coords = st.get("coordenades", {})
        lat, lon = coords.get("latitud"), coords.get("longitud")
        if lat is None or lon is None:
            continue
        parsed.append({
            "codi": st.get("codi"), "nom": st.get("nom", "?"),
            "lat": float(lat), "lon": float(lon), "alt": st.get("altitud"),
        })
    return parsed


def load_meteocat_stations_cache():
    try:
        with open(METEOCAT_STATIONS_CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    cached_at = cache.get("cached_at")
    if not cached_at:
        return None
    try:
        age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(cached_at)).days
    except ValueError:
        return None
    if age_days > METEOCAT_STATIONS_CACHE_MAX_DAYS:
        return None
    return cache.get("stations")


def save_meteocat_stations_cache(stations):
    cache = {"cached_at": datetime.now(timezone.utc).isoformat(), "stations": stations}
    with open(METEOCAT_STATIONS_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def fetch_meteocat_latest_precipitation(api_key, timeout=25):
    """Consulta l'última lectura de precipitació (variable 35) per a totes
    les estacions XEMA en una sola petició."""
    url = f"{METEOCAT_BASE_URL}/variables/mesurades/{METEOCAT_PRECIP_VARIABLE}/ultimes"
    req = urllib.request.Request(url, headers={
        "X-Api-Key": api_key, "User-Agent": "bolets-catalunya-app/1.0",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    entries = data if isinstance(data, list) else [data]

    # L'API retorna, per a cada estació, un objecte amb 'codi' i una llista
    # 'variables' (una per variable consultada); les lectures viuen dins de
    # cada variable, no directament a l'arrel de l'entrada de l'estació:
    # {"codi": "C6", "variables": [{"codi": 35, "lectures": [{"valor": 0, ...}]}]}
    readings = {}
    for entry in entries:
        codi = entry.get("codi")
        variables = entry.get("variables", [])
        if codi is None or not variables:
            continue
        lectures = variables[0].get("lectures", [])
        if not lectures:
            continue
        last = lectures[-1]
        readings[codi] = {"valor": last.get("valor"), "data": last.get("data"), "estat": last.get("estat")}
    return readings


def fetch_meteocat_observations(api_key):
    """
    Combina metadades d'estacions (cauejades) amb les últimes lectures de
    precipitació (sempre fresques), en el mateix format que fem servir per
    a AEMET perquè es puguin combinar directament a la triangulació.
    """
    if not api_key:
        return []

    stations = load_meteocat_stations_cache()
    if stations is None:
        print("  Meteocat: metadades d'estacions no cauejades, consultant...")
        stations = fetch_meteocat_station_metadata(api_key)
        save_meteocat_stations_cache(stations)
        print(f"  Meteocat: {len(stations)} estacions XEMA trobades")
    else:
        print(f"  Meteocat: {len(stations)} estacions XEMA (des de cache)")

    readings = fetch_meteocat_latest_precipitation(api_key)

    parsed = []
    for st in stations:
        reading = readings.get(st["codi"])
        if reading is None or reading.get("valor") is None:
            continue
        # S'estandarditza al mateix format que fem servir per a AEMET
        # (lat, lon, name, prec_1h) perquè triangulate_rain els pugui
        # combinar sense distingir la font.
        parsed.append({
            "lat": st["lat"], "lon": st["lon"], "name": st["nom"],
            "prec_1h": reading["valor"], "fint": reading.get("data"),
        })
    return parsed


# ---------------------------------------------------------------------------
# 5. ICGC — TIPUS DE BOSC REAL (WMS GetFeatureInfo)
# ---------------------------------------------------------------------------

def parse_tree_from_text(txt):
    """
    Interpreta la resposta de GetFeatureInfo del WMS de l'ICGC (capa 'cobertes_2009',
    simplificada a 41 classes). La resposta inclou una línia 'class = "CODI. (N) Nom"'.
    Com que aquesta capa és més general que la llegenda de 241 categories, es reconeixen
    també termes genèrics de tipus de bosc a més dels específics per espècie.
    """
    if not txt:
        return "desconegut", None

    # Extreu el contingut de la línia 'class = ...'
    class_label = None
    for line in txt.splitlines():
        line = line.strip()
        if line.lower().startswith("class"):
            class_label = line.split("=", 1)[-1].strip().strip("'\"")
            break

    low = (class_label or txt).lower()

    # Ordre important: primer les coincidències específiques d'espècie (pineda de pi
    # roig, alzinar, roureda...), després les genèriques (aciculifoli, caducifoli...)
    # que només s'activaran amb la capa simplificada de 41 classes.
    checks = [
        (["pi roig", "sylvestris"], "pi_roig"),
        (["pi negre", "uncinata"], "pi_negre"),
        (["avet", "abies alba", "avetosa"], "avet"),
        (["pi blanc", "halepensis"], "pi_blanc"),
        (["pi pinyer", "pinea"], "pi_pinyer"),
        (["alzinar", "carrascar", " ilex", "quercus ilex"], "alzina"),
        (["roureda", "quercus", "martinenc", "fulla petita", "pènol", "penol"], "roure"),
        (["fageda", "fagus"], "faig"),
        (["surededa", "suber"], "suro"),
        (["aciculifoli"], "pi_altres"),
        (["caducifoli", "planifoli"], "roure"),
        (["esclerofil", "laurifoli"], "alzina"),
        (["alzina"], "alzina"),
        (["roure"], "roure"),
        (["fag"], "faig"),
        (["sur"], "suro"),
        (["conífer", "conifer", "pinassa", "pineda"], "pi_altres"),
        (["mixt"], "mixt"),
        (["conreu", "vinyes", "oliverars", "fruiter", "herbaci", "llenyós", "llenyos"], "conreu"),
        (["urbà", "urba", "edificat", "industrial", "vial", "nucli", "eixample", "residencial", "extracció", "extraccio", "abocador"], "urba"),
        (["aigua", "embassament", "curs", "llacuna", "estany", "humi"], "aigua"),
        (["roquissar", "congesta", "tartera", "glacera", "platg", "sorral"], "roca"),
        (["matollar", "bosquina", "brolla", "landa", "garriga"], "matollar"),
        (["prat", "pastura", "herbassar"], "prat"),
    ]
    for keywords, tree in checks:
        if any(k in low for k in keywords):
            return tree, class_label
    return "desconegut", class_label


def fetch_tree_type(lat, lon, layer_name, timeout=5, debug=False):
    """Consulta el WMS de l'ICGC (GetFeatureInfo) per saber el tipus de bosc en un punt."""
    d = 0.01
    params = (
        f"?REQUEST=GetFeatureInfo&SERVICE=WMS&VERSION=1.1.1&LAYERS={layer_name}"
        f"&STYLES=&FORMAT=image/png&SRS=EPSG:4326"
        f"&BBOX={lon-d},{lat-d},{lon+d},{lat+d}&WIDTH=101&HEIGHT=101"
        f"&QUERY_LAYERS={layer_name}&X=50&Y=50&INFO_FORMAT=text/plain"
    )
    url = ICGC_WMS_URL + params
    req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            txt = resp.read().decode("utf-8", errors="ignore")
        tree, class_label = parse_tree_from_text(txt)
        if debug:
            print(f"    [DEBUG] status={status} class_label={class_label!r} -> tree={tree}")
        return tree, class_label
    except urllib.error.HTTPError as e:
        if debug:
            print(f"    [DEBUG] HTTPError {e.code}: {e.reason}")
        return "desconegut", None
    except Exception as e:
        if debug:
            print(f"    [DEBUG] {type(e).__name__}: {e}")
        return "desconegut", None


def fetch_all_tree_types(zones, layer_name, delay=0.05, max_total_seconds=280):
    """Consulta el tipus de bosc per a totes les zones, una a una (el WMS no admet lots).
    Té un límit de temps total: si es supera, es continua amb 'desconegut' per a la resta
    (millor tenir dades parcials que deixar tot el procés penjat)."""
    results = {}
    start = time.time()
    for i, z in enumerate(zones):
        if time.time() - start > max_total_seconds:
            print(f"  ICGC: límit de temps ({max_total_seconds}s) assolit a {i}/{len(zones)} — es continua sense la resta")
            for remaining in zones[i:]:
                results[remaining["id"]] = ("desconegut", None)
            break
        results[z["id"]] = fetch_tree_type(z["lat"], z["lon"], layer_name, debug=False)
        if delay:
            time.sleep(delay)
        if (i + 1) % 25 == 0:
            print(f"  ICGC: {i + 1}/{len(zones)} punts consultats...")
    return results


# ---------------------------------------------------------------------------
# 6. SCORING
# ---------------------------------------------------------------------------

def _rain_component(ratio):
    """Puntuació de pluja (0-22) segons ratio = pluja / pluja mínima de l'espècie."""
    if ratio >= 1:
        return 22.0
    if ratio >= 0.7:
        return 22 * ((ratio - 0.7) / 0.3) * 0.6 + 9
    if ratio >= 0.4:
        return 9 * ((ratio - 0.4) / 0.3)
    return 0.0


def _days_component(sp, days):
    """Puntuació de dies des de la pluja principal (0-25), amb marges tous."""
    lo, hi = sp["rain_days"]
    if lo <= days <= hi:
        return 25.0
    mid = (lo + hi) / 2
    dist = abs(days - mid) - (hi - lo) / 2
    return max(0.0, 25 - (dist / 5) * 12)


def _day_of_year_pair(month, day):
    return month * 31 + day  # ordre cronològic suficient per comparar (no és un dia de l'any real)


def season_multiplier(sp, today, gbif_data=None):
    """
    Limitant d'ÈPOCA (0.03-1). Fa servir la distribució mensual REAL de
    registres GBIF/FungaCAT si n'hi ha prou (>= 15); si no, la finestra
    manual de SPECIES_BIO. Amb GBIF s'interpola entre els centres de mes per
    dia (el 31 d'octubre ja és mig camí cap al novembre), i es compara amb el
    mes de màxim: un mes amb >= 50% del màxim compta com a plena temporada.
    Retorna (multiplicador, text o None).
    """
    counts = None
    if gbif_data:
        raw = gbif_data.get("month_counts") or {}
        counts = {m: (raw.get(m, 0) or raw.get(str(m), 0) or 0) for m in range(1, 13)}
        if sum(counts.values()) < 15:
            counts = None

    if counts:
        peak = max(counts.values()) or 1
        m, d = today.month, today.day
        # interpolació entre centres de mes (dia 15)
        if d >= 15:
            m2 = 1 if m == 12 else m + 1
            frac = (d - 15) / 30.0
        else:
            m2 = 12 if m == 1 else m - 1
            frac = (15 - d) / 30.0
        value = counts[m] * (1 - frac) + counts[m2] * frac
        ratio = value / peak
        mult = max(0.03, min(1.0, ratio / 0.5))
    else:
        bio = SPECIES_BIO.get(sp["id"], {})
        window = bio.get("season_manual")
        if not window:
            return 1.0, None
        start, end = _day_of_year_pair(*window[0]), _day_of_year_pair(*window[1])
        now = _day_of_year_pair(today.month, today.day)
        inside = (start <= now <= end) if start <= end else (now >= start or now <= end)
        if inside:
            mult = 1.0
        else:
            # marge de ~15 dies a cada banda amb caiguda lineal
            def gap(a, b):
                return abs(a - b) if abs(a - b) < 200 else 372 - abs(a - b)
            dist = min(gap(now, start), gap(now, end))
            mult = max(0.05, 1.0 - dist / 15.0 * 0.8)
    text = None
    if mult < 0.9:
        text = "Fuera de su época habitual" if mult < 0.5 else "Cerca del final (o del inicio) de su época"
    return mult, text


def timing_multiplier(sp, age):
    """Limitant de MOMENT: dies des de la pluja principal respecte al que
    necessita l'espècie. Retorna (multiplicador, text o None)."""
    bio = SPECIES_BIO.get(sp["id"], {})
    curve = bio.get("timing") or default_timing_curve(sp["rain_days"])
    mult = interp_curve(curve, age)
    lo, hi = sp["rain_days"]
    text = None
    if mult < 0.9:
        if age < lo:
            text = f"Aún pronto: la lluvia principal fue hace {age} días y suele salir a los {lo}-{hi} días"
        else:
            text = f"La lluvia principal fue hace {age} días; lo habitual es {lo}-{hi}, la tanda puede estar acabando"
    return mult, text


def altitude_multiplier(sp, alt):
    bio = SPECIES_BIO.get(sp["id"], {})
    curve = bio.get("alt")
    if not curve:
        return 1.0, None
    mult = interp_curve(curve, alt)
    text = None
    if mult < 0.9:
        text = f"Altitud poco habitual para esta especie ({int(alt)} m)"
    return mult, text


def heat_multiplier(sp, tmin, tmax):
    """Limitant de CALOR per a espècies termòfiles (ou de reig). tmin/tmax:
    mitjana dels darrers 7 dies. Si no hi ha tmax es dedueix de la mitjana."""
    heat = SPECIES_BIO.get(sp["id"], {}).get("heat")
    if not heat or tmin is None:
        return 1.0, None
    m_min = interp_curve(heat["tmin"], tmin)
    m_max = interp_curve(heat["tmax"], tmax) if tmax is not None else 1.0
    mult = min(m_min, m_max)
    text = None
    if mult < 0.9:
        t_full_min, t_full_max = heat["tmin"][-1][0], heat["tmax"][-1][0]
        mx = f"{tmax:.0f}" if tmax is not None else "?"
        intro = "Demasiado fresco" if mult < 0.7 else "Algo justo de calor"
        text = (f"{intro} para esta especie, que necesita calor "
                f"(últimos 7 días: mínimas {tmin:.0f}°C y máximas {mx}°C; "
                f"lo ideal es ≥{t_full_min}°C y ≥{t_full_max}°C)")
    return mult, text


def soil_multiplier(sp, geologia):
    soil = SPECIES_BIO.get(sp["id"], {}).get("soil")
    if not soil:
        return 1.0, None
    mult = soil.get(geologia, soil.get(None, 1.0))
    text = None
    if mult < 0.9:
        if geologia == "calcari":
            text = "Suelo calcáreo: poco favorable para esta especie"
        elif geologia in ("mixt",):
            text = "Geología mixta o de cemento calcáreo: poco favorable para esta especie"
        elif geologia in ("silici_prov",):
            text = "Geología aún por confirmar"
        elif geologia is None:
            text = "Geología sin clasificar: no se puede confirmar el tipo de suelo"
        elif geologia == "silici":
            text = None
    return mult, text


def species_score(sp, rain_10d, min_temp, tree, days_since_rain, alt, month, aemet_rain_1h=None, mc_rain_today=None, gbif_distributions=None, triangulation=None, soil_stats=None, radar_value=None, geologia=None, wx=None, today=None):
    """
    Sistema de puntuació 0-100 per evidència acumulada MÉS limitants
    biològics que la multipliquen (veure SPECIES_BIO): moment respecte a la
    pluja principal, època, altitud, calor i geologia. Cada factor suma
    punts segons com d'a prop està del rang òptim (amb tolerància als
    marges), i després els limitants poden reduir el total — una espècie no
    pot sortir "probable" només perquè la pluja i la temperatura vagin bé
    si encara és massa aviat, o massa a dalt, o en un sòl que no li va.

    Retorna 0 si l'hàbitat és incompatible (requisit dur: un rovelló no surt
    sota una alzina). Retorna (puntuació, desglossament, confiança, limitants)
    on 'limitants' és una llista de textos curts (castellà, per a la web)
    amb el que frena la puntuació.

    'wx' (opcional): vista meteorològica de derive_weather_view amb els
    esdeveniments de pluja i les temperatures dels darrers 7 dies. Si no hi
    és (punts sense sèrie pròpia encara), s'usen els valors resumits.
    """
    if tree not in sp["trees"]:
        return 0, {}, "baja", []

    today = today or today_madrid()
    breakdown = {}
    limits = []
    score = 0.0

    # --- Esdeveniment de pluja determinant ---
    # Candidats: tots els esdeveniments rellevants dels darrers dies. Se'n
    # tria el que millor encaixa amb l'espècie (pluja suficient i moment
    # adequat). Sense sèrie pròpia: l'únic esdeveniment és el del resum.
    if wx and wx.get("events") is not None:
        candidates = [(e["age_mid"], e["mm_since"]) for e in wx["events"]]
    elif days_since_rain is not None and days_since_rain < NO_EVENT_DAYS:
        candidates = [(days_since_rain, rain_10d)]
    else:
        candidates = []

    min_rain = sp["min_rain"]
    best = None
    for age, mm in candidates:
        r = _rain_component(mm / min_rain if min_rain else 1)
        d = _days_component(sp, age)
        t_mult, _ = timing_multiplier(sp, age)
        fitness = (r + d) * t_mult
        if best is None or fitness > best[0]:
            best = (fitness, age, mm, r, d)

    if best is None:
        rain_score, days_score, event_age, event_mm = 0.0, 0.0, None, rain_10d
    else:
        _, event_age, event_mm, rain_score, days_score = best

    breakdown["pluja"] = round(rain_score, 1)
    score += rain_score
    breakdown["dies_pluja"] = round(days_score, 1)
    score += days_score

    # --- Temperatura mínima (0-20 punts, amb marges tous) ---
    tmin_now = wx.get("tmin_7d") if wx and wx.get("tmin_7d") is not None else min_temp
    tmax_now = wx.get("tmax_7d") if wx and wx.get("tmax_7d") is not None else None
    tlo, thi = sp["temp_range"]
    if tlo <= tmin_now <= thi:
        temp_score = 20
    else:
        tmid = (tlo + thi) / 2
        dist = abs(tmin_now - tmid) - (thi - tlo) / 2
        temp_score = max(0, 20 - (dist / 3) * 10)
    breakdown["temperatura"] = round(temp_score, 1)
    score += temp_score

    # --- Humitat real del sòl (0-8 punts) ---
    soil_score = 0
    if soil_stats and soil_stats.get("soil_moisture_avg_7d") is not None:
        moisture = soil_stats["soil_moisture_avg_7d"]
        trend = soil_stats.get("soil_moisture_trend") or 0
        if moisture >= 0.30:
            soil_score = 8
        elif moisture >= 0.15:
            soil_score = 8 * ((moisture - 0.15) / 0.15)
        else:
            soil_score = 0
        if trend > 0.01:
            soil_score = min(8, soil_score + 1.5)
        elif trend < -0.02:
            soil_score = max(0, soil_score - 1.5)
        air_humidity = soil_stats.get("air_humidity_avg_3d")
        if air_humidity is not None:
            if air_humidity < 50:
                soil_score = max(0, soil_score - 1)
            elif air_humidity >= 80:
                soil_score = min(8, soil_score + 1)
    breakdown["humitat_sol"] = round(soil_score, 1)
    score += soil_score

    # --- Climatologia de temporada per altitud (0-15 punts) ---
    season_score = seasonal_climate_score(sp, alt, month, gbif_distributions)
    breakdown["temporada"] = round(season_score, 1)
    score += season_score

    # --- Corroboració entre fonts (0-10 punts bonus) ---
    corrob_score = 0
    if radar_value is not None and radar_value >= 3:
        corrob_score = 10
    elif triangulation and triangulation.get("estimated_rain_mm") is not None:
        tri_rain = triangulation["estimated_rain_mm"]
        n_stations = len(triangulation.get("stations_used", []))
        if tri_rain >= 5:
            corrob_score = 10 if n_stations >= 2 else 7
        elif tri_rain > 0:
            corrob_score = 5 if n_stations >= 2 else 3
    else:
        if aemet_rain_1h is not None and aemet_rain_1h > 0:
            corrob_score += 5
        if mc_rain_today is not None and mc_rain_today >= 5:
            corrob_score += 5
    breakdown["corroboracio"] = corrob_score
    score += corrob_score

    # --- LIMITANTS BIOLÒGICS (multipliquen la suma anterior) ---
    gbif_data = gbif_distributions.get(sp["id"]) if gbif_distributions else None
    factors = []   # (multiplicador, text)
    if event_age is None:
        factors.append((0.30, "Sin una lluvia suficiente en las últimas semanas"))
    else:
        factors.append(timing_multiplier(sp, event_age))
    factors.append(season_multiplier(sp, today, gbif_data))
    factors.append(altitude_multiplier(sp, alt))
    factors.append(heat_multiplier(sp, tmin_now, tmax_now))
    factors.append(soil_multiplier(sp, geologia))

    limit_mult = 1.0
    for mult, _text in factors:
        limit_mult *= mult
    for mult, text in sorted(factors, key=lambda f: f[0]):
        if text and len(limits) < 3:
            limits.append(text)
    breakdown["limitants"] = round(limit_mult, 2)
    if event_age is not None:
        breakdown["edat_pluja"] = event_age

    final_score = max(0, min(100, round(score * limit_mult)))
    confidence = compute_confidence(sp, gbif_distributions, aemet_rain_1h, mc_rain_today, triangulation, radar_value)
    # La geologia desconeguda o provisional resta fiabilitat a les espècies que en depenen
    if SPECIES_BIO.get(sp["id"], {}).get("soil") and geologia in (None, "silici_prov") and confidence == "alta":
        confidence = "mitjana"

    return final_score, breakdown, confidence, limits


def compute_confidence(sp, gbif_distributions, aemet_rain_1h, mc_rain_today, triangulation=None, radar_value=None):
    """
    Nivell de confiança ("alta"/"mitjana"/"baixa") de la puntuació, INDEPENDENT
    del seu valor. Una puntuació de 84 basada en pocs registres històrics i
    cap corroboració és menys fiable que un 84 recolzat per molta evidència,
    encara que el número sigui idèntic — això evita transmetre una falsa
    sensació de precisió (una puntuació alta no és el mateix que una
    puntuació fiable).

    Factors que sumen confiança:
    - Prou registres GBIF per a aquesta espècie (>= 30 és "molts")
    - Radar disponible per a aquest punt (cobertura de superfície directa)
    - Triangulació amb 2+ estacions reals properes (més fiable que una sola font)
    - Si no hi ha triangulació, alguna font aïllada (AEMET o Meteoclimatic) corrobora
    """
    points = 0
    species_gbif_data = gbif_distributions.get(sp["id"]) if gbif_distributions else None
    total_gbif = sum(species_gbif_data.get("month_counts", {}).values()) if species_gbif_data else 0
    if total_gbif >= 30:
        points += 2
    elif total_gbif >= 15:
        points += 1

    if radar_value is not None:
        points += 2

    n_triangulation_stations = len(triangulation.get("stations_used", [])) if triangulation else 0
    if n_triangulation_stations >= 2:
        points += 2
    elif n_triangulation_stations == 1:
        points += 1
    else:
        if aemet_rain_1h is not None:
            points += 1
        if mc_rain_today is not None:
            points += 1

    if points >= 3:
        return "alta"
    elif points >= 1:
        return "mitjana"
    else:
        return "baja"


# ---------------------------------------------------------------------------
# 9. GBIF — HISTÒRIC REAL D'AVISTAMENTS (FungaCAT i altres datasets)
# ---------------------------------------------------------------------------
# GBIF és una base de dades pública i gratuïta (sense clau) amb milions de
# registres d'observacions de fongs, incloent el dataset FungaCAT (Catalunya,
# des de 1752). Es fa servir per calcular la distribució mensual REAL
# d'aparicions de cada espècie a Catalunya, en comptes d'una estimació manual.

GBIF_API_URL = "https://api.gbif.org/v1/occurrence/search"
GBIF_CACHE_PATH = "../data/gbif_cache.json"
GBIF_CACHE_MAX_DAYS = 60  # l'estacionalitat històrica no canvia sovint


def fetch_gbif_monthly_distribution(scientific_name, timeout=20):
    """
    Consulta GBIF per a una espècie (nom científic) amb coordenades a
    Catalunya, i retorna:
    - month_counts: {mes: nombre_de_registres}
    - alt_bucket_counts: {tram_altitud: nombre_de_registres} — trams de 250m,
      a partir del camp 'elevation' de GBIF quan hi és disponible
    - total_with_elevation: quants registres tenien dada d'altitud (per saber
      si val la pena confiar en alt_bucket_counts)

    S'usa geometry (bounding box aproximat de Catalunya) en comptes de
    country=ES per no incloure la resta d'Espanya.
    """
    catalunya_bbox = "POLYGON((0.10 40.50, 3.35 40.50, 3.35 42.90, 0.10 42.90, 0.10 40.50))"
    month_counts = {m: 0 for m in range(1, 13)}
    alt_bucket_counts = {}
    total_with_elevation = 0
    offset = 0
    limit = 300
    max_records = 3000  # límit de seguretat per no fer massa peticions per espècie

    while offset < max_records:
        params = (
            f"?scientificName={urllib.parse.quote(scientific_name)}"
            f"&geometry={urllib.parse.quote(catalunya_bbox)}"
            f"&hasCoordinate=true&limit={limit}&offset={offset}"
        )
        url = GBIF_API_URL + params
        req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            break

        results = data.get("results", [])
        if not results:
            break
        for rec in results:
            month = rec.get("month")
            if month and 1 <= month <= 12:
                month_counts[month] += 1

            elevation = rec.get("elevation")
            if elevation is not None:
                try:
                    bucket = int(float(elevation) // 250) * 250
                    alt_bucket_counts[bucket] = alt_bucket_counts.get(bucket, 0) + 1
                    total_with_elevation += 1
                except (TypeError, ValueError):
                    pass

        if data.get("endOfRecords", True):
            break
        offset += limit

    return {
        "month_counts": month_counts,
        "alt_bucket_counts": alt_bucket_counts,
        "total_with_elevation": total_with_elevation,
    }


def load_gbif_cache():
    """Carrega el cache de distribució mensual GBIF si existeix i no ha caducat."""
    try:
        with open(GBIF_CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    cached_at = cache.get("cached_at")
    if not cached_at:
        return {}
    try:
        cached_date = datetime.fromisoformat(cached_at)
    except ValueError:
        return {}
    age_days = (datetime.now(timezone.utc) - cached_date).days
    if age_days > GBIF_CACHE_MAX_DAYS:
        print(f"  Cache de GBIF caducat ({age_days} dies) — es torna a consultar")
        return {}

    print(f"  Cache de GBIF trobat ({age_days} dies)")
    # Es va detectar que el cache de producció tenia un FORMAT ANTIC (només
    # els comptes mensuals plans {"1": n, ...}, sense "month_counts" ni
    # "alt_bucket_counts"): el codi nou no hi trobava res i, en silenci, el
    # GBIF no s'usava mai (calia el calendari manual). Es normalitza aquí i
    # les entrades antigues es marquen "legacy" perquè es reconsultin.
    normalized = {}
    for sid, data in cache.get("species", {}).items():
        if not isinstance(data, dict):
            continue
        if "month_counts" in data:
            normalized[sid] = data
        else:
            normalized[sid] = {
                "month_counts": {str(k): v for k, v in data.items() if str(k).isdigit()},
                "alt_bucket_counts": {},
                "total_with_elevation": 0,
                "legacy": True,
            }
    return normalized


def save_gbif_cache(species_distributions):
    cache = {
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "species": species_distributions,
    }
    with open(GBIF_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def build_gbif_distributions():
    """
    Per a cada espècie del catàleg, consulta (o recupera del cache) la
    distribució mensual i d'altitud real de GBIF, combinant tots els noms
    científics (sinònims/espècies properes) d'aquella espècie.
    """
    cache = load_gbif_cache()
    missing = [sp for sp in SPECIES if sp["id"] not in cache or cache[sp["id"]].get("legacy")]

    if missing:
        print(f"  GBIF: consultant {len(missing)} espècies sense cache...")
        for sp in missing:
            combined_months = {m: 0 for m in range(1, 13)}
            combined_alt_buckets = {}
            total_elevation = 0
            for name in sp.get("scientific", []):
                try:
                    result = fetch_gbif_monthly_distribution(name)
                    for m, c in result["month_counts"].items():
                        combined_months[m] += c
                    for bucket, c in result["alt_bucket_counts"].items():
                        combined_alt_buckets[bucket] = combined_alt_buckets.get(bucket, 0) + c
                    total_elevation += result["total_with_elevation"]
                except Exception as e:
                    print(f"    AVÍS: GBIF ha fallat per '{name}' ({e})")
            total = sum(combined_months.values())
            if total < 15 and sp["id"] in cache:
                # Si la consulta ha fallat (xarxa) NO es sobreescriu una dada
                # antiga bona amb zeros: es manté i es reintenta.
                print(f"    {sp['name']}: GBIF no ha respost ({total} registres) — es manté la dada anterior i es reintenta")
                continue
            entry = {
                "month_counts": combined_months,
                "alt_bucket_counts": {str(k): v for k, v in combined_alt_buckets.items()},
                "total_with_elevation": total_elevation,
            }
            if total >= 15:
                cache[sp["id"]] = entry
            else:
                print(f"    {sp['name']}: només {total} registres — no es desa al cache (es reintenta la propera execució)")
                continue
            print(f"    {sp['name']}: {total} registres GBIF trobats ({total_elevation} amb altitud)")
        save_gbif_cache(cache)
    else:
        print("  GBIF: totes les espècies trobades al cache")

    return cache


def gbif_seasonal_score(species_gbif_data, month):
    """
    Puntuació 0-15 basada en la proporció real de registres GBIF que cauen
    en aquest mes (i els adjacents amb pes reduït), respecte al total anual
    de l'espècie. Si no hi ha prou registres (< 15), no es pot confiar en
    la distribució i es retorna None perquè el crida faci servir el fallback.
    """
    if not species_gbif_data:
        return None
    monthly_counts = species_gbif_data.get("month_counts", {})
    if not monthly_counts:
        return None
    total = sum(monthly_counts.values())
    if total < 15:
        return None

    prev_m = 12 if month == 1 else month - 1
    next_m = 1 if month == 12 else month + 1
    weighted = (
        monthly_counts.get(month, 0) * 1.0
        + monthly_counts.get(str(month), 0) * 1.0
        + monthly_counts.get(prev_m, 0) * 0.4
        + monthly_counts.get(str(prev_m), 0) * 0.4
        + monthly_counts.get(next_m, 0) * 0.4
        + monthly_counts.get(str(next_m), 0) * 0.4
    )
    ratio = weighted / total if total else 0
    # Escala calibrada: un mes que concentri ~35% o més del pes anual (habitual
    # en el mes de màxima temporada) arriba al màxim de 15; per sota, escala lineal.
    return round(min(15, (ratio / 0.35) * 15), 1)


def gbif_altitude_bonus(species_gbif_data, alt):
    """
    Bonus de 0-5 punts si l'altitud del punt coincideix amb el tram
    d'altitud on GBIF té més registres reals d'aquesta espècie. Requereix
    almenys 15 registres amb dada d'altitud per confiar-hi (si no, retorna 0
    sense penalitzar).
    """
    if not species_gbif_data:
        return 0
    alt_buckets = species_gbif_data.get("alt_bucket_counts", {})
    total_elev = species_gbif_data.get("total_with_elevation", 0)
    if not alt_buckets or total_elev < 15:
        return 0

    point_bucket = int(alt // 250) * 250
    counts_by_bucket = {int(k): v for k, v in alt_buckets.items()}
    best_bucket = max(counts_by_bucket, key=counts_by_bucket.get)

    dist_buckets = abs(point_bucket - best_bucket) // 250
    if dist_buckets == 0:
        return 5
    elif dist_buckets == 1:
        return 2
    return 0


def seasonal_climate_score(sp, alt, month, gbif_distributions=None):
    """
    Puntuació de temporada segons altitud i mes. Si hi ha prou dades reals
    de GBIF per a l'espècie, es fa servir la distribució real d'aparicions
    (mes + bonus d'altitud real); si no, es fa servir l'estimació manual
    basada en coneixement general (altitud/mes) com a reserva.
    """
    species_gbif_data = gbif_distributions.get(sp["id"]) if gbif_distributions else None

    if species_gbif_data:
        gbif_score = gbif_seasonal_score(species_gbif_data, month)
        if gbif_score is not None:
            alt_bonus = gbif_altitude_bonus(species_gbif_data, alt)
            return min(15, gbif_score + alt_bonus)

    # --- Fallback: estimació manual ---
    if alt >= 1200:
        peak_months = [8, 9, 10]
    elif alt >= 700:
        peak_months = [9, 10, 11]
    else:
        peak_months = [10, 11]

    if sp["id"] == "colmenilles":  # espècie de primavera, no de tardor
        peak_months = [4, 5]

    if month in peak_months:
        return 15
    adjacent = {m - 1 for m in peak_months} | {m + 1 for m in peak_months}
    if month in adjacent:
        return 7
    return 0



# ---------------------------------------------------------------------------
# 7. PROCÉS PRINCIPAL
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 10. VEGETACIO (sig.gencat.cat) — CAPES PER ESPÈCIE D'ARBRE
# ---------------------------------------------------------------------------
# Servei WMS de la Generalitat amb una capa WMS separada per a cada espècie
# d'arbre (VEGETACIO_ABIESALBA, VEGETACIO_FAGUSSYLVATICA, VEGETACIO_PINUS...).
# Dona detall real d'espècie que la capa del ICGC no dona. Es descobreixen les
# capes de manera automàtica (filtrant les d'incendis/risc/perímetres, que no
# són d'espècie) i es consulten només les rellevants segons el grup genèric
# (conífera/caducifoli/perennifoli) ja conegut via ICGC, per no disparar el
# nombre de peticions.

VEGETACIO_WMS_URL = "https://sig.gencat.cat/ows/VEGETACIO/wms"
VEGETACIO_LAYERS_CACHE_PATH = "../data/vegetacio_layers_cache.json"
VEGETACIO_LAYERS_CACHE_MAX_DAYS = 90

# Paraules que indiquen que la capa NO és d'una espècie d'arbre (incendis,
# riscos, perímetres administratius, etc.) — es descarten en el descobriment.
VEGETACIO_NON_SPECIES_KEYWORDS = [
    "INCENDI", "RISC", "PERIMETRE", "PERILL", "MUNALTRISC", "AGRUDEFENFOREST",
    "INSTRORDENFOREST", "INVFORESTNAC", "HERBASSARS", "FONTSLLAVORERES",
    "INFLAMABILITAT",
]

# Mapa de nom científic (part del nom de capa) -> grup genèric ICGC, per saber
# quines capes val la pena consultar per a un punt segons el seu tipus de
# bosc ja conegut. S'amplia automàticament amb qualsevol espècie descoberta
# que continguí aquestes arrels.
VEGETACIO_SPECIES_TO_GROUP = {
    "ABIESALBA": "pi_altres", "PINUSHALEPENSIS": "pi_altres", "PINUSSYLVESTRIS": "pi_altres",
    "PINUSNIGRA": "pi_altres", "PINUSUNCINATA": "pi_altres", "PINUSPINEA": "pi_altres",
    "PINUSPINASTER": "pi_altres",
    "FAGUSSYLVATICA": "roure", "QUERCUS": "roure",
    "QUERCUSILEX": "alzina", "QUERCUSSUBER": "alzina",
}


def discover_vegetacio_species_layers(timeout=15):
    """Consulta GetCapabilities del servei VEGETACIO i retorna la llista de
    noms de capa que semblen ser d'espècie d'arbre (prefixades VEGETACIO_ i
    sense cap paraula de la llista d'exclusió)."""
    url = f"{VEGETACIO_WMS_URL}?request=GetCapabilities&service=wms&version=1.3.0"
    req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            xml_text = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  AVÍS: no s'ha pogut consultar GetCapabilities de VEGETACIO ({e})")
        return []

    import re
    names = re.findall(r"<Name>([^<]+)</Name>", xml_text)
    species_layers = []
    for name in names:
        if not name.startswith("VEGETACIO_"):
            continue
        if any(kw in name for kw in VEGETACIO_NON_SPECIES_KEYWORDS):
            continue
        species_layers.append(name)
    return sorted(set(species_layers))


def load_vegetacio_layers_cache():
    try:
        with open(VEGETACIO_LAYERS_CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    cached_at = cache.get("cached_at")
    if not cached_at:
        return None
    try:
        age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(cached_at)).days
    except ValueError:
        return None
    if age_days > VEGETACIO_LAYERS_CACHE_MAX_DAYS:
        return None
    return cache.get("layers")


def _read_vegetacio_file():
    try:
        with open(VEGETACIO_LAYERS_CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
        return cache if isinstance(cache, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_vegetacio_layers_cache(layers):
    # El mateix fitxer també guarda el resultat del refinament per punt
    # ("points"): es conserva en renovar la llista de capes. (S'aprofita
    # aquest fitxer perquè ja és al "git add" del workflow.)
    cache = _read_vegetacio_file()
    cache["cached_at"] = datetime.now(timezone.utc).isoformat()
    cache["layers"] = layers
    with open(VEGETACIO_LAYERS_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def load_vegetacio_points():
    points = _read_vegetacio_file().get("points")
    return points if isinstance(points, dict) else {}


def save_vegetacio_points(points):
    cache = _read_vegetacio_file()
    cache.setdefault("cached_at", datetime.now(timezone.utc).isoformat())
    cache["points"] = points
    with open(VEGETACIO_LAYERS_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def vegetacio_group_of_layer(layer_name):
    """Grup genèric ICGC (pi_altres/roure/alzina) al qual pertany una capa
    d'espècie, o None si la capa no és d'espècie d'arbre (PTGMFC, RPALTRESESP,
    XARXAPUNTSAIGUA, ZONESACTUACIOURG...). Es tria la clau més LLARGA que
    coincideix: abans "QUERCUS" (roure) guanyava a "QUERCUSILEX" /
    "QUERCUSSUBER" (alzina), de manera que per als punts d'alzinar mai es
    consultava l'alzina ni el suro (i per això no sortia mai "suro")."""
    best = None
    for species_key, group in VEGETACIO_SPECIES_TO_GROUP.items():
        if species_key in layer_name and (best is None or len(species_key) > len(best[0])):
            best = (species_key, group)
    return best[1] if best else None


# Ordre de consulta dins de cada grup: primer les espècies més esteses a
# Catalunya, així la majoria de punts es resolen amb 1-3 peticions en comptes
# de 7. (Només afecta a quina es mira primer si en un punt se'n solapen dues.)
VEGETACIO_LAYER_PRIORITY = [
    "PINUSHALEPENSIS", "PINUSSYLVESTRIS", "PINUSNIGRA", "PINUSUNCINATA", "PINUSPINEA", "PINUSPINASTER", "ABIESALBA",
    "QUERCUSHUMILIS", "QUERCUSFAGINEA", "FAGUSSYLVATICA", "QUERCUSPETRAEA", "QUERCUSROBUR", "QUERCUSPYRENAICA",
    "QUERCUSCANARIENSIS",
    "QUERCUSILEX", "QUERCUSSUBER",
]


def layers_for_group(layers, tree_group):
    """Capes d'espècie que cal consultar per a un grup genèric, ordenades per
    prioritat."""
    def rank(name):
        for i, key in enumerate(VEGETACIO_LAYER_PRIORITY):
            if key in name:
                return i
        return len(VEGETACIO_LAYER_PRIORITY)
    return sorted((l for l in layers if layer_relevant_for_group(l, tree_group)), key=rank)


def layer_relevant_for_group(layer_name, tree_group):
    """Decideix si val la pena consultar aquesta capa d'espècie per a un punt
    del grup genèric donat, per no fer peticions innecessàries. Les capes que
    no són d'espècie d'arbre ja no es consulten mai (abans es consultaven per
    a tots els punts i una coincidència en una d'elles aturava la cerca)."""
    return vegetacio_group_of_layer(layer_name) == tree_group


def fetch_vegetacio_species_for_point(lat, lon, layer_name, timeout=6):
    """Consulta si una capa d'espècie concreta té presència en un punt."""
    d = 0.01
    params = (
        f"?REQUEST=GetFeatureInfo&SERVICE=WMS&VERSION=1.1.1&LAYERS={layer_name}"
        f"&STYLES=&FORMAT=image/png&SRS=EPSG:4326"
        f"&BBOX={lon-d},{lat-d},{lon+d},{lat+d}&WIDTH=101&HEIGHT=101"
        f"&QUERY_LAYERS={layer_name}&X=50&Y=50&INFO_FORMAT=text/plain"
    )
    url = VEGETACIO_WMS_URL + params
    # IMPORTANT: ja NO es captura l'excepció aquí. Abans qualsevol error de
    # xarxa/timeout retornava False ("aquesta espècie no hi és"), igual que
    # una resposta buida real; en refinar-ho tot en memòria cada execució no
    # es notava, però en cachejar-ho s'haurien fixat falsos negatius. Ara el
    # cridant distingeix "no hi és" (False) de "no s'ha pogut saber" (excepció).
    req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        txt = resp.read().decode("utf-8", errors="ignore")
    low = txt.lower()
    if "serviceexception" in low or "<html" in low:
        raise RuntimeError("resposta d'error del servei VEGETACIO")
    return "Feature" in txt or "<gml" in low


def species_layer_to_tree_key(layer_name):
    """Tradueix un nom de capa VEGETACIO_XXX al mateix vocabulari de tree que
    ja fem servir per al scoring (pi_roig, roure, faig, alzina, suro...)."""
    mapping = {
        "PINUSSYLVESTRIS": "pi_roig", "PINUSUNCINATA": "pi_negre", "ABIESALBA": "avet",
        "PINUSHALEPENSIS": "pi_blanc", "PINUSPINEA": "pi_pinyer", "PINUSNIGRA": "pi_altres",
        "PINUSPINASTER": "pi_altres", "FAGUSSYLVATICA": "faig", "QUERCUSILEX": "alzina",
        "QUERCUSSUBER": "suro",
    }
    for key, tree in mapping.items():
        if key in layer_name:
            return tree
    if "QUERCUS" in layer_name:
        return "roure"
    return None


VEGETACIO_GENERIC_GROUPS = ("pi_altres", "roure", "alzina")


def refine_tree_species(zones, tree_types, layers, max_seconds=900, save_every=100):
    """
    Afina el tipus de bosc genèric de l'ICGC (pi_altres / roure / alzina) a
    l'espècie exacta de VEGETACIO, AMB MEMÒRIA entre execucions.

    Abans el resultat només vivia en memòria i la tanda tenia un límit de
    temps: cada execució tornava a començar pels mateixos primers punts i la
    resta no s'arribava mai a afinar (a producció, ~158 punts de ~3.000).
    Ara cada punt resolt es desa a data/vegetacio_layers_cache.json ("points")
    i les execucions següents només consulten els pendents, fins completar-ho.

    Regles:
      - Només es desa un punt si TOTES les capes consultades han respost
        (una fallada de xarxa no es pot confondre amb "aquesta espècie no hi
        és"); si un punt falla, es reintenta la propera execució.
      - Si fallen 8 punts seguits, s'atura la tanda (servei caigut).
      - La memòria és vàlida només si el tipus base del punt no ha canviat.
      - Es consulten només les capes d'espècie del grup del punt (no PTGMFC,
        RPALTRESESP, XARXAPUNTSAIGUA...).
    Retorna (aplicats_de_la_memoria, resolts_ara, pendents_restants).
    """
    points = load_vegetacio_points()
    applied = 0
    pending = []
    for z in zones:
        base = tree_types.get(z["id"])
        if base not in VEGETACIO_GENERIC_GROUPS:
            continue
        key = cell_key(z["lat"], z["lon"])
        entry = points.get(key)
        if isinstance(entry, dict) and entry.get("b") == base:
            found = entry.get("t")
            if found and found != base:
                tree_types[z["id"]] = found
                applied += 1
            continue
        pending.append((z, base, key))

    if not pending:
        print(f"  VEGETACIO: tots els punts ja són afinats (memòria: {applied} amb espècie exacta)")
        return applied, 0, 0

    print(f"  VEGETACIO: {applied} punts ja afinats de la memòria; {len(pending)} pendents — tanda de com a molt {max_seconds}s")
    start = time.time()
    resolved = failed = consecutive_fail = 0
    stopped_early = False
    for z, base, key in pending:
        if time.time() - start > max_seconds:
            print(f"  VEGETACIO: límit de temps ({max_seconds}s) assolit — la resta es farà les properes execucions")
            stopped_early = True
            break
        found = None
        incomplete = False
        for layer in layers_for_group(layers, base):
            try:
                hit = fetch_vegetacio_species_for_point(z["lat"], z["lon"], layer)
            except Exception:
                incomplete = True
                break
            if hit:
                found = species_layer_to_tree_key(layer)
                break
        if incomplete:
            failed += 1
            consecutive_fail += 1
            if consecutive_fail >= 8:
                print("  VEGETACIO: 8 fallades seguides — servei no disponible, s'atura la tanda (es reintentarà)")
                stopped_early = True
                break
            continue
        consecutive_fail = 0
        points[key] = {"b": base, "t": found if found and found != base else None}
        resolved += 1
        if points[key]["t"]:
            tree_types[z["id"]] = points[key]["t"]
            applied += 1
        if resolved % save_every == 0:
            save_vegetacio_points(points)
    if resolved:
        save_vegetacio_points(points)
    remaining = len(pending) - resolved
    print(f"  VEGETACIO: {resolved} punts resolts ara, {failed} fallades (no desades), {remaining} pendents"
          + (" (tanda aturada)" if stopped_early else ""))
    return applied, resolved, remaining


TREE_CACHE_PATH = "../data/bosc_cache.json"
# Abans eren 30 dies. Com que el cache només es re-desa mentre queden punts
# per resoldre, un cop complet envellia i als 30 dies s'ometia sencer: calia
# tornar a consultar l'ICGC per als ~8000 punts d'un cop (i els que fallessin
# quedaven "desconegut" i sortien de la graella). La cobertura forestal no
# canvia en un mes: un any, com el sondeig forestal.
TREE_CACHE_MAX_DAYS = 365


def load_tree_cache():
    """Carrega el cache de tipus de bosc si existeix i no ha caducat."""
    try:
        with open(TREE_CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    cached_at = cache.get("cached_at")
    if not cached_at:
        return {}
    try:
        cached_date = datetime.fromisoformat(cached_at)
    except ValueError:
        return {}
    age_days = (datetime.now(timezone.utc) - cached_date).days
    if age_days > TREE_CACHE_MAX_DAYS:
        print(f"  Cache de bosc caducat ({age_days} dies) — es torna a consultar l'ICGC")
        return {}

    trees = cache.get("trees", {})
    print(f"  Cache de bosc trobat ({age_days} dies) amb {len(trees)} punts")
    return {int(k): v for k, v in trees.items()}


def save_tree_cache(tree_types):
    """Desa el cache de tipus de bosc per no haver de reconsultar l'ICGC cada cop."""
    cache = {
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "trees": {str(k): v for k, v in tree_types.items()},
    }
    with open(TREE_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 8. METEOCLIMATIC — XARXA D'ESTACIONS AMATEUR (contrast del dia actual)
# ---------------------------------------------------------------------------
# Meteoclimatic només dona el valor acumulat d'AVUI (no històric). Per tenir
# un històric propi, cada execució es desa el valor d'avui a HISTORY_PATH i es
# descarten les entrades de més de HISTORY_MAX_DAYS. Pensat perquè Meteocat
# (quan arribi l'accés) s'integri al mateix fitxer com una font més.

METEOCLIMATIC_XML_URL = "http://www.meteoclimatic.net/feed/xml/ESCAT"
HISTORY_PATH = "../data/historial_lluvia.json"
HISTORY_MAX_DAYS = 30


GEOCODE_CACHE_PATH = "../data/geocode_cache.json"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
GEOCODE_BATCH_PER_RUN = 20  # respecta el límit de Nominatim (4/min) sense allargar massa l'execució
GEOCODE_DELAY_SECONDS = 15  # ~4 peticions/minut


def load_geocode_cache():
    """Cache permanent (no caduca): nom de lloc -> {lat, lon} o None si no s'ha trobat."""
    try:
        with open(GEOCODE_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_geocode_cache(cache):
    with open(GEOCODE_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def geocode_place(location_name, timeout=10):
    """Geocodifica un nom de lloc de Catalunya via Nominatim (OSM), gratuït
    i sense clau. S'acota la cerca a Catalunya afegint ', Catalunya' i
    limitant per bounding box aproximat, per evitar coincidències d'altres
    llocs del món amb el mateix nom."""
    query = f"{location_name}, Catalunya, Spain"
    params = (
        f"?q={urllib.parse.quote(query)}&format=json&limit=1"
        f"&viewbox=0.10,42.90,3.35,40.50&bounded=1"
    )
    url = NOMINATIM_URL + params
    req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0 (github.com/Shicodiez/bolets-catalunya)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data:
            return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# NOMS DE ZONA REALS (reverse geocoding de les coordenades fixes de la graella)
# ---------------------------------------------------------------------------
# Substitueix "Punt 275" per un nom de lloc reconeixible (poble, comarca...).
# Com que les coordenades no canvien mai (~1470 punts), el cache és permanent
# i només cal completar-lo una vegada — es fa per lots per respectar el
# límit de Nominatim (4 peticions/minut per a scripts automàtics; amb la
# graella actual, completar tots els noms tarda ~2-3 setmanes).

ZONE_NAMES_CACHE_PATH = "../data/zone_names_cache.json"
ZONE_NAMES_BATCH_PER_RUN = 60  # es manté en 60/execució (~15min per execució, límit dur de Nominatim 4 peticions/min) — amb la graella adaptativa (~6200 punts) i execucions cada 3h (8/dia), es completarà en ~11 dies


def reverse_geocode_place(lat, lon, timeout=10):
    """Retorna un nom de lloc reconeixible per a unes coordenades (poble,
    llogaret o, si no n'hi ha, comarca/paratge), via Nominatim (OSM).

    zoom=14 (nivell "suburb/barri") en comptes de zoom=12 (nivell
    "town/municipi"): amb zoom=12, en zones rurals poc mapejades a OSM,
    Nominatim pot retornar el municipi/entitat administrativa més propera
    a la seva base de dades encara que estigui a força distància real del
    punt (confirmat amb un cas real: un punt a la Ribera d'Ebre va rebre
    el nom "Ribera d'Ondara", una entitat de la Segarra, molt lluny). Amb
    zoom=14 es prioritzen nuclis de població més petits i propers abans
    de caure en una entitat administrativa àmplia."""
    params = f"?lat={lat}&lon={lon}&format=json&zoom=14&accept-language=ca"
    url = "https://nominatim.openstreetmap.org/reverse" + params
    req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0 (github.com/Shicodiez/bolets-catalunya)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        addr = data.get("address", {})
        name = (
            addr.get("hamlet") or addr.get("village") or addr.get("suburb")
            or addr.get("town") or addr.get("municipality") or addr.get("city")
            or addr.get("county")
        )
        return name
    except Exception:
        return None


def load_zone_names_cache():
    try:
        with open(ZONE_NAMES_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_zone_names_cache(cache):
    with open(ZONE_NAMES_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def geocode_zones_batch(zones):
    """
    Completa per lots (respectant el límit de Nominatim) el nom real de
    cada zona de la graella. Cache permanent — les coordenades de les
    zones no canvien mai, així que un cop resolt un punt no cal repetir-ho.
    """
    cache = load_zone_names_cache()
    missing = [z for z in zones if str(z["id"]) not in cache]

    if not missing:
        print("  Noms de zona: totes ja són al cache")
    else:
        batch = missing[:ZONE_NAMES_BATCH_PER_RUN]
        print(f"  Noms de zona: {len(missing)} pendents, resolent {len(batch)} aquesta execució...")
        for i, z in enumerate(batch):
            name = reverse_geocode_place(z["lat"], z["lon"])
            cache[str(z["id"])] = name  # es desa també si és None, per no reintentar
            if i < len(batch) - 1:
                time.sleep(GEOCODE_DELAY_SECONDS)
        save_zone_names_cache(cache)
        found = sum(1 for z in batch if cache.get(str(z["id"])))
        print(f"  Noms de zona: {found}/{len(batch)} trobats aquesta execució")

    return cache


def geocode_meteoclimatic_batch(stations):
    """
    Geocodifica un lot limitat d'estacions de Meteoclimatic per execució,
    respectant el límit de Nominatim (4 peticions/minut per a scripts
    automàtics). El cache és permanent — un cop geocodificat un lloc, no cal
    tornar-ho a fer mai més (les estacions no es mouen). Amb el temps,
    totes les estacions del feed queden geocodificades.
    """
    cache = load_geocode_cache()
    to_geocode = [s for s in stations if s["location"] and s["location"].strip() not in cache]

    if not to_geocode:
        print("  Geocodificació: totes les ubicacions ja són al cache")
    else:
        batch = to_geocode[:GEOCODE_BATCH_PER_RUN]
        print(f"  Geocodificació: {len(to_geocode)} ubicacions pendents, geocodificant {len(batch)} aquesta execució...")
        for i, st in enumerate(batch):
            place = st["location"].strip()
            result = geocode_place(place)
            cache[place] = result  # es desa també si és None, per no reintentar llocs que no es troben
            if i < len(batch) - 1:
                time.sleep(GEOCODE_DELAY_SECONDS)
        save_geocode_cache(cache)
        found = sum(1 for st in batch if cache.get(st["location"].strip()))
        print(f"  Geocodificació: {found}/{len(batch)} trobades aquesta execució")

    # Aplica el cache a les estacions
    for st in stations:
        place = st["location"].strip() if st["location"] else ""
        coords = cache.get(place)
        if coords:
            st["lat"] = coords["lat"]
            st["lon"] = coords["lon"]

    return stations


def fetch_meteoclimatic_stations(timeout=20):
    """
    Consulta el XML públic de Meteoclimatic per a totes les estacions de
    Catalunya (codi d'àrea ESCAT). Retorna una llista de diccionaris amb
    id, location, lat/lon (si estan disponibles al XML) i pluja d'avui (mm).
    Meteoclimatic no dona sempre lat/lon explícits al XML bàsic — si no hi
    són, la funció que fa servir aquestes dades ha de treballar per location.
    """
    req = urllib.request.Request(METEOCLIMATIC_XML_URL, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        xml_text = resp.read().decode("utf-8", errors="ignore")

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_text)
    all_stations = root.findall(".//station")

    stations = []
    for st in all_stations:
        st_id = st.findtext("id", default="")
        location = st.findtext("location", default="")
        pub_date = st.findtext("pubDate", default=None)  # RFC 822, ex: "Mon, 09 Sep 2026 14:00:00 GMT"
        lat = None  # es completa després via geocodificació (el feed no dona coordenades)
        lon = None

        rain_now = None
        rain_el = st.find(".//stationdata/rain")
        if rain_el is not None:
            total_txt = rain_el.findtext("total")
            try:
                rain_now = float(total_txt) if total_txt is not None else None
            except ValueError:
                rain_now = None

        stations.append({
            "id": st_id, "location": location,
            "lat": lat, "lon": lon, "rain_today_mm": rain_now,
            "updated_at": pub_date,
        })
    return stations


def nearest_meteoclimatic_station(lat, lon, stations, max_km=25):
    """Retorna l'estació Meteoclimatic més propera amb coordenades i dada de pluja vàlida."""
    best, best_dist = None, max_km
    for st in stations:
        if st["lat"] is None or st["lon"] is None or st["rain_today_mm"] is None:
            continue
        d = haversine_km(lat, lon, st["lat"], st["lon"])
        if d < best_dist:
            best, best_dist = st, d
    if best:
        return {**best, "distance_km": round(best_dist, 1)}
    return None


def triangulate_rain(lat, lon, aemet_stations, mc_stations, meteocat_stations=None, max_km=30, max_stations=4, min_distance_km=0.5):
    """
    Estima la pluja d'avui a un punt combinant les estacions reals més
    properes (AEMET + Meteoclimatic + Meteocat/XEMA juntes) mitjançant IDW
    (Inverse Distance Weighting): cada estació pesa segons 1/distància², de
    manera que les més properes dominen l'estimació però les llunyanes
    encara hi aporten.

    És una millora del "agafar només l'estació més propera": suavitza dades
    puntuals estranyes d'una sola estació i dona una estimació més fiable
    quan n'hi ha diverses a prop, sense inventar-se res si no n'hi ha cap.

    Retorna None si no hi ha cap estació prou a prop (max_km), perquè el
    crida ha de saber distingir "no hi ha dada" de "0mm reals".
    """
    candidates = []

    for st in aemet_stations or []:
        rain = st.get("prec_1h")
        if rain is None:
            continue
        d = haversine_km(lat, lon, st["lat"], st["lon"])
        if d <= max_km:
            candidates.append({"rain": rain, "distance_km": d, "source": "aemet", "name": st.get("name")})

    for st in mc_stations or []:
        if st.get("lat") is None or st.get("lon") is None or st.get("rain_today_mm") is None:
            continue
        d = haversine_km(lat, lon, st["lat"], st["lon"])
        if d <= max_km:
            candidates.append({"rain": st["rain_today_mm"], "distance_km": d, "source": "meteoclimatic", "name": st.get("location")})

    for st in meteocat_stations or []:
        rain = st.get("prec_1h")
        if rain is None:
            continue
        d = haversine_km(lat, lon, st["lat"], st["lon"])
        if d <= max_km:
            candidates.append({"rain": rain, "distance_km": d, "source": "meteocat", "name": st.get("name")})

    if not candidates:
        return None

    # Deduplicació: la mateixa estació (mateix nom i coordenades pràcticament
    # idèntiques, arrodonides a 3 decimals ~110m) no ha de comptar dues
    # vegades encara que aparegui repetida a la font (s'ha observat que
    # passa, per exemple amb AEMET). Es queda amb la primera aparició un cop
    # ordenat per distància.
    candidates.sort(key=lambda c: c["distance_km"])
    seen = set()
    deduped = []
    for c in candidates:
        key = (c.get("name"), round(c["distance_km"], 2))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)
    candidates = deduped[:max_stations]

    weighted_sum = 0.0
    weight_total = 0.0
    used_stations = []
    for c in candidates:
        d = max(c["distance_km"], min_distance_km)  # evita dividir per (gairebé) zero
        weight = 1 / (d ** 2)
        weighted_sum += c["rain"] * weight
        weight_total += weight
        used_stations.append({"source": c["source"], "name": c["name"], "distance_km": round(c["distance_km"], 1), "rain": c["rain"]})

    estimated_rain = round(weighted_sum / weight_total, 1) if weight_total else None
    return {"estimated_rain_mm": estimated_rain, "stations_used": used_stations}


def load_history():
    """Carrega l'historial propi de pluja per zona/dia. Estructura:
    { "2026-08-25": {"390": {"meteoclimatic": 12.1}, ...}, "2026-08-24": {...} }
    Cada dia pot tenir aportacions de diverses fonts per zona — pensat per
    afegir Meteocat com una font més quan hi hagi accés."""
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_history(history):
    """Desa l'historial, descartant les entrades de més de HISTORY_MAX_DAYS."""
    today = datetime.now(timezone.utc).date()
    pruned = {}
    for date_str, day_data in history.items():
        try:
            d = datetime.fromisoformat(date_str).date()
        except ValueError:
            continue
        if (today - d).days <= HISTORY_MAX_DAYS:
            pruned[date_str] = day_data
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(pruned, f, ensure_ascii=False)
    return pruned


def update_history_with_meteoclimatic(history, zones, mc_stations):
    """Afegeix la pluja d'avui de Meteoclimatic a l'historial per a cada zona
    que tingui una estació prou a prop."""
    valid_coords = sum(1 for s in mc_stations if s["lat"] is not None and s["lon"] is not None)
    valid_rain = sum(1 for s in mc_stations if s["rain_today_mm"] is not None)
    print(f"  Meteoclimatic diagnòstic: {valid_coords}/{len(mc_stations)} amb coordenades, {valid_rain}/{len(mc_stations)} amb dada de pluja")

    today_str = datetime.now(timezone.utc).date().isoformat()
    day_entry = history.get(today_str, {})
    matched = 0
    for z in zones:
        nearest = nearest_meteoclimatic_station(z["lat"], z["lon"], mc_stations)
        if nearest:
            zone_entry = day_entry.get(str(z["id"]), {})
            zone_entry["meteoclimatic"] = nearest["rain_today_mm"]
            zone_entry["meteoclimatic_station"] = nearest["location"]
            zone_entry["meteoclimatic_distance_km"] = nearest["distance_km"]
            day_entry[str(z["id"])] = zone_entry
            matched += 1
    history[today_str] = day_entry
    print(f"  Meteoclimatic: {matched}/{len(zones)} punts amb estació propera trobada")
    return history


def own_history_days_count(history, zone_id):
    """Compta quants dies d'historial propi tenim per a una zona (útil per
    saber quan l'historial ja és prou llarg per fer-lo servir en el scoring)."""
    zid = str(zone_id)
    return sum(1 for day_data in history.values() if zid in day_data)


# ---------------------------------------------------------------------------
# 11. AVISOS DE CADUCITAT DE CREDENCIALS
# ---------------------------------------------------------------------------
# Dates de caducitat conegudes (s'han d'actualitzar a mà quan es renovi cada
# credencial). Es genera un avís quan falten poques dies, perquè es mostri
# a la web i no calgui recordar-ho de memòria.

CREDENTIAL_EXPIRATIONS = [
    {"name": "API key d'AEMET", "expires_on": "2026-11-25", "renew_url": "https://opendata.aemet.es"},
    {"name": "Token de GitHub (Worker d'hallazgos)", "expires_on": "2026-11-24", "renew_url": "https://github.com/settings/tokens?type=beta"},
    {"name": "API key de Meteocat", "expires_on": "2027-08-31", "renew_url": "https://apidocs.meteocat.gencat.cat"},
]

CREDENTIAL_WARNING_DAYS = 15


def check_credential_expirations():
    """Retorna una llista d'avisos per a les credencials que caduquen en
    menys de CREDENTIAL_WARNING_DAYS dies (o que ja han caducat)."""
    warnings = []
    today = datetime.now(timezone.utc).date()
    for cred in CREDENTIAL_EXPIRATIONS:
        try:
            expires = datetime.fromisoformat(cred["expires_on"]).date()
        except ValueError:
            continue
        days_left = (expires - today).days
        if days_left <= CREDENTIAL_WARNING_DAYS:
            warnings.append({
                "name": cred["name"],
                "expires_on": cred["expires_on"],
                "days_left": days_left,
                "renew_url": cred["renew_url"],
                "expired": days_left < 0,
            })
    return warnings


def build_results():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Graella de {len(ZONES)} punts")

    print("Consultant Open-Meteo (meteorologia)...")
    weather_results = fetch_weather_rotating(ZONES)  # sistema de blocs rotatius (3 blocs, un per execució) per no saturar Open-Meteo

    print("Consultant Meteoclimatic (contrast estacions amateur, historial propi)...")
    history = load_history()
    data_coverage = {
        "open_meteo": {"ok": True, "detail": f"{len(ZONES)} zones"},
    }
    try:
        mc_stations = retry_with_backoff(fetch_meteoclimatic_stations, description="Meteoclimatic")
        print(f"  Meteoclimatic: {len(mc_stations)} estacions rebudes")
        mc_stations = geocode_meteoclimatic_batch(mc_stations)
        history = update_history_with_meteoclimatic(history, ZONES, mc_stations)
        history = save_history(history)
        data_coverage["meteoclimatic"] = {"ok": True, "detail": f"{len(mc_stations)} estacions"}
    except Exception as e:
        print(f"  AVÍS: no s'ha pogut consultar Meteoclimatic ({e}) — es continua sense actualitzar l'historial")
        mc_stations = []
        data_coverage["meteoclimatic"] = {"ok": False, "detail": str(e)}

    print("Resolent noms de zona reals...")
    zone_names = geocode_zones_batch(ZONES)

    print("Consultant tipus de bosc (amb cache)...")
    tree_types = load_tree_cache()
    missing_zones = [z for z in ZONES if z["id"] not in tree_types]

    if missing_zones:
        print(f"  {len(missing_zones)} punts sense cache — consultant ICGC...")
        layer_name, available_layers = discover_icgc_layer()
        icgc_start = time.time()
        icgc_max_seconds = 2200  # augmentat de 1000 a 2200: amb la graella adaptativa (~6200 punts,
        # 4.2x més gran que quan es va fixar en 1000s), calia més marge
        unresolved_this_run = {}  # 'desconegut' d'aquesta execució — NO es guarden al cache permanent
        for i, z in enumerate(missing_zones):
            if time.time() - icgc_start > icgc_max_seconds:
                print(f"  ICGC: límit de temps ({icgc_max_seconds}s) assolit a {i}/{len(missing_zones)} — es continua sense la resta (es reintentaran, no es fixen com a 'desconegut')")
                for remaining in missing_zones[i:]:
                    unresolved_this_run[remaining["id"]] = UNRESOLVED_TREE
                break
            tree, _label = fetch_tree_type(z["lat"], z["lon"], layer_name, debug=False)
            if tree == UNRESOLVED_TREE:
                # Fallada puntual (timeout, error de xarxa...) — no és el
                # mateix que "confirmat sense bosc". No es guarda al cache
                # perquè es reintenti la propera execució (un cas real: aixi
                # es van perdre silenciosament zones amb bosc real confirmat
                # per coneixement de camp, a la zona de Berga).
                unresolved_this_run[z["id"]] = tree
            else:
                tree_types[z["id"]] = tree
            time.sleep(0.05)
            if (i + 1) % 50 == 0:
                print(f"  ICGC: {i + 1}/{len(missing_zones)} punts consultats...")
        if unresolved_this_run:
            print(f"  ICGC: {len(unresolved_this_run)} punts sense resoldre aquesta execució (timeout/error) — es reintentaran, NO es fixen al cache")
        save_tree_cache(tree_types)
        tree_types.update(unresolved_this_run)  # per usar-los NOMÉS en aquesta execució, no s'han desat
    else:
        print("  Tots els punts trobats al cache — no cal consultar l'ICGC")

    known_trees = sum(1 for z in ZONES if tree_types.get(z["id"], UNRESOLVED_TREE) not in NON_FOREST
                      and tree_types.get(z["id"], UNRESOLVED_TREE) != UNRESOLVED_TREE)
    print(f"Bosc: {known_trees}/{len(ZONES)} punts forestals identificats")

    print("Refinant espècie exacta amb VEGETACIO (sig.gencat.cat)...")
    vegetacio_layers = load_vegetacio_layers_cache()
    if vegetacio_layers is None:
        vegetacio_layers = discover_vegetacio_species_layers()
        if vegetacio_layers:
            save_vegetacio_layers_cache(vegetacio_layers)
    print(f"  VEGETACIO: {len(vegetacio_layers)} capes d'espècie disponibles")

    if vegetacio_layers:
        refine_tree_species(ZONES, tree_types, vegetacio_layers, max_seconds=900)
    else:
        print("  VEGETACIO: sense llista de capes — no es refina l'espècie en aquesta execució")

    aemet_key = os.environ.get("AEMET_API_KEY")
    aemet_stations = []
    if aemet_key:
        try:
            print("Consultant AEMET (estacions reals) per contrastar...")
            aemet_stations = retry_with_backoff(lambda: fetch_aemet_observations(aemet_key), description="AEMET")
            print(f"AEMET: {len(aemet_stations)} estacions amb dades rebudes")
            data_coverage["aemet"] = {"ok": True, "detail": f"{len(aemet_stations)} estacions"}
        except Exception as e:
            print(f"AVÍS: no s'ha pogut consultar AEMET ({e}) — es continua sense contrast")
            data_coverage["aemet"] = {"ok": False, "detail": str(e)}
    else:
        print("AVÍS: no hi ha AEMET_API_KEY configurada — es continua sense contrast")
        data_coverage["aemet"] = {"ok": False, "detail": "sense API key configurada"}

    radar_lookup = {}
    if AEMET_RADAR_ENABLED and aemet_key:
        try:
            print("Consultant radar AEMET (cobertura de superfície, no només punts)...")
            radar_lookup = build_radar_lookup(aemet_key, ZONES)
            print(f"  Radar: {len(radar_lookup)}/{len(ZONES)} punts amb valor extret")
            data_coverage["radar_aemet"] = {"ok": len(radar_lookup) > 0, "detail": f"{len(radar_lookup)} punts"}
        except Exception as e:
            print(f"  AVÍS: no s'ha pogut processar el radar AEMET ({e}) — es continua sense radar")
            data_coverage["radar_aemet"] = {"ok": False, "detail": str(e)}
    else:
        print("Radar AEMET desactivat a propòsit (georeferenciació no fiable) — no es compta com a font incompleta")

    print("Consultant geologia del sòl (silici/calcari) amb l'ICGC...")
    try:
        geologia_lookup, geologia_points = build_geologia_lookup(ZONES, tree_types=tree_types)
        confirmed = sum(1 for e in geologia_points.values() if not e.get("legacy"))
        classified = sum(1 for v in geologia_lookup.values() if v is not None)
        print(f"  Geologia: {classified}/{len(geologia_lookup)} punts classificats ({confirmed} reconfirmats amb les regles noves)")
        data_coverage["geologia"] = {"ok": True, "detail": f"{classified} punts classificats, {confirmed} reconfirmats"}
    except Exception as e:
        print(f"  AVÍS: no s'ha pogut consultar la geologia ({e}) — es continua sense aquest ajust")
        geologia_lookup = {}
        data_coverage["geologia"] = {"ok": False, "detail": str(e)}

    print("Consultant RainViewer (mosaic de radar europeu, cobertura de superfície)...")
    try:
        rainviewer_lookup, rainviewer_ok = build_rainviewer_lookup(ZONES)
        print(f"  RainViewer: {len(rainviewer_lookup)}/{len(ZONES)} punts amb valor extret")
        if rainviewer_ok:
            detail = f"{len(rainviewer_lookup)} punts amb pluja" if rainviewer_lookup else "sense pluja detectada (resposta correcta)"
        else:
            detail = "no s'ha pogut connectar"
        data_coverage["rainviewer"] = {"ok": rainviewer_ok, "detail": detail}
        # Si AEMET no ha donat valor per a un punt (o no estava disponible),
        # es completa amb RainViewer — no se sobreescriu si AEMET sí en tenia.
        for zid, mm in rainviewer_lookup.items():
            radar_lookup.setdefault(zid, mm)
    except Exception as e:
        print(f"  AVÍS: no s'ha pogut consultar RainViewer ({e}) — es continua sense aquesta font")
        data_coverage["rainviewer"] = {"ok": False, "detail": str(e)}

    meteocat_key = os.environ.get("METEOCAT_API_KEY")
    meteocat_stations = []
    if meteocat_key:
        try:
            print("Consultant Meteocat/XEMA (estacions reals oficials) per contrastar...")
            meteocat_stations = retry_with_backoff(lambda: fetch_meteocat_observations(meteocat_key), description="Meteocat")
            print(f"Meteocat: {len(meteocat_stations)} estacions amb dades de pluja rebudes")
            data_coverage["meteocat"] = {"ok": True, "detail": f"{len(meteocat_stations)} estacions"}
        except Exception as e:
            print(f"AVÍS: no s'ha pogut consultar Meteocat ({e}) — es continua sense contrast")
            data_coverage["meteocat"] = {"ok": False, "detail": str(e)}
    else:
        print("AVÍS: no hi ha METEOCAT_API_KEY configurada — es continua sense contrast")
        data_coverage["meteocat"] = {"ok": False, "detail": "sense API key configurada"}

    print("Consultant GBIF (històric real d'avistaments, FungaCAT)...")
    gbif_distributions = build_gbif_distributions()

    today_local = today_madrid()
    current_month = today_local.month
    today_str = datetime.now(timezone.utc).date().isoformat()
    today_history = history.get(today_str, {})

    zones_out = []
    for zone, weather_summary in zip(ZONES, weather_results):
        # weather_summary és l'entrada del cache de blocs d'aquest punt
        # (resum + sèrie diària pròpia). derive_weather_view la converteix
        # en esdeveniments de pluja i temperatures dels darrers 7 dies
        # calculats amb la data d'AVUI, no la del darrer refresc.
        wx = derive_weather_view(weather_summary, today_local)
        rain_10d = wx["rain_10d"]
        avg_temp = wx["avg_temp"]
        min_temp = wx["min_temp"]
        days_since_rain = wx["days_since_rain"]
        soil_stats = wx.get("soil_stats")
        tree = tree_types.get(zone["id"], "desconegut")

        aemet_info = None
        aemet_rain_1h = None
        if aemet_stations:
            nearest = nearest_aemet_station(zone["lat"], zone["lon"], aemet_stations)
            if nearest:
                aemet_info = {
                    "station_name": nearest["name"],
                    "distance_km": nearest["distance_km"],
                    "prec_1h_mm": nearest["prec_1h"],
                    "observed_at": nearest["fint"],
                }
                aemet_rain_1h = nearest["prec_1h"]

        mc_rain_today = today_history.get(str(zone["id"]), {}).get("meteoclimatic")
        radar_value = radar_lookup.get(zone["id"])
        geologia = geologia_lookup.get(cell_key(zone["lat"], zone["lon"]))

        triangulation = triangulate_rain(zone["lat"], zone["lon"], aemet_stations, mc_stations, meteocat_stations=meteocat_stations)

        species_scores = []
        if tree not in NON_FOREST and tree != UNRESOLVED_TREE:
            for sp in SPECIES:
                s, breakdown, confidence, limits = species_score(
                    sp, rain_10d, min_temp, tree, days_since_rain, zone["alt"], current_month,
                    aemet_rain_1h=aemet_rain_1h, mc_rain_today=mc_rain_today,
                    gbif_distributions=gbif_distributions, triangulation=triangulation,
                    soil_stats=soil_stats, radar_value=radar_value, geologia=geologia,
                    wx=wx, today=today_local,
                )
                if s > 0:
                    species_scores.append({"id": sp["id"], "name": sp["name"], "score": s, "confidence": confidence, "breakdown": breakdown, "limits": limits})
        species_scores.sort(key=lambda x: x["score"], reverse=True)
        matching_species = [s for s in species_scores if s["score"] >= DEFAULT_SCORE_THRESHOLD]

        real_name = zone_names.get(str(zone["id"]))
        zones_out.append({
            "id": zone["id"],
            "name": real_name if real_name else f"Punt {zone['id']}",
            "lat": zone["lat"],
            "lon": zone["lon"],
            "alt": zone["alt"],
            "tree": tree,
            "tree_label": TREE_LABELS.get(tree, tree),
            "is_forest": tree not in NON_FOREST and tree != UNRESOLVED_TREE,
            "rain_10d": rain_10d,
            "avg_temp": avg_temp,
            "min_temp": min_temp,
            "max_temp": round(wx["tmax_7d"]) if wx.get("tmax_7d") is not None else None,
            "days_since_rain": days_since_rain,
            "species_scores": species_scores,
            "aemet_check": aemet_info,
            "own_history_days": own_history_days_count(history, zone["id"]),
            "triangulation": triangulation,
            "radar_mm": radar_value,
            "geologia": geologia,
            "soil_stats": soil_stats,
        })

    credential_warnings = check_credential_expirations()
    if credential_warnings:
        print(f"AVÍS: {len(credential_warnings)} credencial(s) a punt de caducar o caducades:")
        for w in credential_warnings:
            estat = "JA HA CADUCAT" if w["expired"] else f"caduca en {w['days_left']} dies"
            print(f"  - {w['name']}: {estat} ({w['expires_on']})")

    zone_names_with_real_name = sum(1 for z in zones_out if not z["name"].startswith("Punt "))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "default_threshold": DEFAULT_SCORE_THRESHOLD,
        "credential_warnings": credential_warnings,
        "data_coverage": data_coverage,
        "zones": zones_out,
        "species_catalog": [{"id": sp["id"], "name": sp["name"]} for sp in SPECIES],
        "all_stations": build_all_stations_list(aemet_stations, meteocat_stations, mc_stations),
        "zone_names_progress": {"done": zone_names_with_real_name, "total": len(zones_out)},
    }


def build_all_stations_list(aemet_stations, meteocat_stations, mc_stations):
    """
    Combina les tres xarxes d'estacions en una llista única i uniforme,
    per exposar-la al resultat final i que la web pugui oferir un
    desplegable amb totes elles (l'usuari tria una i veu les seves dades
    reals, en comptes de només veure-les indirectament via triangulació).

    Filtra per el bounding box de Catalunya (AEMET dona TOTES les
    estacions d'Espanya, no només les catalanes — sense filtrar sortien
    estacions de Galícia, Canàries, etc.) i dedup·lica per nom+coordenades
    (AEMET dona diverses lectures/hores de la mateixa estació com si fossin
    entrades diferents), quedant-se amb la primera trobada de cadascuna.
    """
    def in_catalunya(lat, lon):
        return (CATALUNYA_LAT_MIN <= lat <= CATALUNYA_LAT_MAX
                and CATALUNYA_LON_MIN <= lon <= CATALUNYA_LON_MAX)

    all_stations = []
    seen = set()

    def add_station(source, name, lat, lon, rain_mm, updated_at):
        if lat is None or lon is None or not in_catalunya(lat, lon):
            return
        key = (name, round(lat, 3), round(lon, 3))
        if key in seen:
            return
        seen.add(key)
        all_stations.append({
            "source": source, "name": name, "lat": lat, "lon": lon,
            "rain_mm": rain_mm, "updated_at": updated_at,
        })

    for st in aemet_stations or []:
        add_station("aemet", st.get("name", "?"), st.get("lat"), st.get("lon"), st.get("prec_1h"), st.get("fint"))
    for st in meteocat_stations or []:
        add_station("meteocat", st.get("name", "?"), st.get("lat"), st.get("lon"), st.get("prec_1h"), st.get("fint"))
    for st in mc_stations or []:
        add_station("meteoclimatic", st.get("location", "?"), st.get("lat"), st.get("lon"), st.get("rain_today_mm"), st.get("updated_at"))

    # Ordenades per nom perquè el desplegable de la web sigui fàcil de cercar
    all_stations.sort(key=lambda s: s["name"] or "")
    return all_stations


EVOLUTION_PATH = "../data/evolucion.json"
EVOLUTION_MAX_DAYS = 30


def load_evolution():
    try:
        with open(EVOLUTION_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_evolution(results):
    """
    Desa un resum diari (millor puntuació per zona) per poder calcular
    l'evolució (avui vs. fa X dies) a la web. Es guarda només un cop al dia
    (si ja hi ha una entrada d'avui, es sobreescriu amb la darrera execució
    del dia en comptes d'acumular una entrada per cada execució de 6h).
    """
    evolution = load_evolution()
    today_str = datetime.now(timezone.utc).date().isoformat()

    day_snapshot = {}
    for z in results["zones"]:
        if not z["is_forest"] or not z["species_scores"]:
            continue
        day_snapshot[str(z["id"])] = z["species_scores"][0]["score"]
    evolution[today_str] = day_snapshot

    today = datetime.now(timezone.utc).date()
    pruned = {}
    for date_str, snapshot in evolution.items():
        try:
            d = datetime.fromisoformat(date_str).date()
        except ValueError:
            continue
        if (today - d).days <= EVOLUTION_MAX_DAYS:
            pruned[date_str] = snapshot

    with open(EVOLUTION_PATH, "w", encoding="utf-8") as f:
        json.dump(pruned, f, ensure_ascii=False)
    return pruned


def compute_score_changes(evolution, results, days_back=7):
    """
    Per a cada zona, calcula el canvi de puntuació respecte a 'days_back' dies
    enrere (si hi ha aquella data a l'historial). Retorna un diccionari
    {zone_id: {"previous": X, "current": Y, "change": Y-X}} només per a les
    zones on hi ha dada prèvia real (no s'inventa cap valor).
    """
    today = datetime.now(timezone.utc).date()
    target_date = (today - timedelta(days=days_back)).isoformat()
    previous_snapshot = evolution.get(target_date)
    if not previous_snapshot:
        return {}

    changes = {}
    for z in results["zones"]:
        if not z["is_forest"] or not z["species_scores"]:
            continue
        zid = str(z["id"])
        prev = previous_snapshot.get(zid)
        if prev is None:
            continue
        curr = z["species_scores"][0]["score"]
        changes[zid] = {"previous": prev, "current": curr, "change": curr - prev}
    return changes


# ---------------------------------------------------------------------------
# 12. PRECISIÓ HISTÒRICA DEL MODEL — contrastar prediccions amb hallazgos reals
# ---------------------------------------------------------------------------
# Es llegeixen els hallazgos guardats pel Worker (fitxer públic al repositori)
# i es comparen amb la puntuació que tenia aquella zona/dia a l'historial
# d'evolució, per calcular quina precisió té realment el model amb dades
# de camp reals — no una suposició.

HALLAZGOS_RAW_URL = "https://raw.githubusercontent.com/Shicodiez/bolets-catalunya/main/data/hallazgos.json"


def fetch_hallazgos(timeout=15):
    """Llegeix els hallazgos guardats (fitxer públic al repositori, servit
    per raw.githubusercontent.com — no cal autenticació per llegir-lo)."""
    req = urllib.request.Request(HALLAZGOS_RAW_URL, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"  AVÍS: no s'han pogut llegir els hallazgos ({e})")
        return []


def nearest_zone_id(lat, lon, zones, max_km=8):
    """Troba l'id de la zona de la graella més propera a unes coordenades
    d'un hallazgo, per poder-lo comparar amb la puntuació d'aquella zona."""
    best_id, best_dist = None, max_km
    for z in zones:
        d = haversine_km(lat, lon, z["lat"], z["lon"])
        if d < best_dist:
            best_id, best_dist = z["id"], d
    return best_id


def compute_model_accuracy(hallazgos, evolution):
    """
    Per a cada hallazgo amb prou informació (data + coordenades), busca la
    puntuació que el model donava a la zona més propera aquell dia (segons
    l'historial d'evolució) i comprova si l'encert coincideix:
    - amount 'mucho'/'poco' + puntuació >= llindar -> encert
    - amount 'nada' + puntuació < llindar -> encert (l'opció 'nada' ja no es
      pot triar des del formulari, però es respecta si queda algun hallazgo
      antic amb aquest valor)
    - la resta -> desencert

    Retorna un resum global i desglossat per franja de puntuació, només amb
    els hallazgos que realment es poden contrastar (no s'inventa res). Com
    que la majoria d'hallazgos ara només confirmen troballes positives
    ('mucho'/'poco'), es guarda també quants dels comparables eren positius
    vs negatius perquè la web pugui explicar què mesura realment la xifra.
    """
    results = {"total_comparable": 0, "aciertos": 0, "por_franja": {}, "positivos": 0, "negativos": 0}
    if not hallazgos or not evolution:
        return results

    for h in hallazgos:
        date = h.get("date")
        lat, lng = h.get("lat"), h.get("lng")
        amount = h.get("amount")
        if not date or lat is None or lng is None or amount not in ("mucho", "poco", "nada"):
            continue

        day_snapshot = evolution.get(date)
        if not day_snapshot:
            continue

        zone_id = nearest_zone_id(lat, lng, ZONES)
        if zone_id is None:
            continue
        score = day_snapshot.get(str(zone_id))
        if score is None:
            continue

        expected_found = amount in ("mucho", "poco")
        predicted_found = score >= DEFAULT_SCORE_THRESHOLD
        hit = expected_found == predicted_found

        results["total_comparable"] += 1
        if expected_found:
            results["positivos"] += 1
        else:
            results["negativos"] += 1
        if hit:
            results["aciertos"] += 1

        franja = f"{(score // 10) * 10}-{(score // 10) * 10 + 9}"
        franja_stats = results["por_franja"].setdefault(franja, {"total": 0, "aciertos": 0})
        franja_stats["total"] += 1
        if hit:
            franja_stats["aciertos"] += 1

    if results["total_comparable"] > 0:
        tasa = round(results["aciertos"] / results["total_comparable"] * 100, 1)
        results["tasa_confirmacion"] = tasa
        results["precision_global"] = tasa  # alias per compatibilitat, mateix valor
    return results


# ---------------------------------------------------------------------------
# GEOLOGIA DEL SÒL (silici vs calcari) — WMS geologia-territorial de l'ICGC
# ---------------------------------------------------------------------------
# Confirmat contra la documentació oficial de l'ICGC (URL i nom de capa
# reals, els dos intents anteriors amb "icgc_mg50m"/"UGEO_PA" eren un servei
# antic ja donat de baixa). La capa "unitats-geologiques-50000" retorna un
# text estructurat amb els camps Descripcio i Descripcio_protolit — es
# classifica per paraules clau litològiques presents en aquest text.
#
# Verificat amb 5 punts reals: Val d'Aran (marbres/calcàries → calcari, no
# l'esperat "silici" — la geologia real hi és mixta, confirma que la capa
# funciona per coordenada real, no per suposició geogràfica general),
# Berguedà (margues/gresos → mixt), Montseny (fil·lites/pissarres → silici),
# Priorat (gresos/pissarres → silici), Garrotxa (basalts → silici).

# REVISIÓ 15/10/2026 — tres problemes reals detectats amb dades de producció:
#
# 1) CLASSIFICACIÓ: "conglomerat" i "gres" comptaven com a silici segur. Però
#    els conglomerats de Sant Llorenç del Munt / Montserrat (Matadepera) són
#    de ciment calcari, i molts gresos (Prepirineu, Vallès) també. Resultat:
#    l'ou de reig, acidòfil, sortia a Matadepera. Ara hi ha TRES nivells:
#    roques silícies segures (granit, pissarra, fil·lita, esquist, gneis,
#    quarsita, basalt...), calcàries segures (calcària, dolomia, marga, guix,
#    marbre...) i roques DETRÍTIQUES ambigües (gres, conglomerat, argila,
#    sorra...) que, soles, es classifiquen com a "mixt" (no es pot assegurar
#    que siguin àcides).
# 2) FALLADES DE XARXA GUARDADES COM A "SENSE DADA": una excepció es desava
#    com a None per sempre ("per no reintentar"). Ara una fallada NO es desa:
#    es reintenta la propera execució. Només es desa un resultat confirmat.
# 3) CLAU PER id: el cache anava per id de zona; qualsevol canvi de graella
#    (com treure els punts duplicats) desalinea tot el cache. Ara va per
#    coordenades, igual que la resta de caches de la graella. També es desa un
#    fragment del text original de l'ICGC per poder reclassificar sense tornar
#    a consultar si es retoquen les paraules clau.
#
# El cache antic (per id, classificat amb les regles velles) es migra a
# coordenades i es continua usant mentre es reconsulta: els "silici" antics
# queden com a "silici_prov" (provisional, pes menor) fins que es confirmen,
# perquè podien ser conglomerats/gresos; calcari i mixt antics es mantenen.

import re

GEOLOGIA_WMS_URL = "https://geoserveis.icgc.cat/servei/catalunya/geologia-territorial/wms"
GEOLOGIA_LAYER = "unitats-geologiques-50000"
GEOLOGIA_CACHE_PATH = "../data/geologia_cache.json"
GEOLOGIA_CACHE_MAX_DAYS = 3650  # la geologia del terreny no canvia mai (abans 180: caducava de cop un cop completat)
GEOLOGIA_CACHE_VERSION = 2

# Silici SEGUR (roques àcides): intrusives, metamòrfiques, volcàniques.
GEO_SILICI = [
    r"granit", r"granodiorit", r"tonalit", r"diorit", r"gabre", r"pegmatit", r"aplit",
    r"pissarr", r"fil[·.]?lit", r"filit", r"esquist", r"micaesquist", r"gneis", r"ortogneis",
    r"migmatit", r"quarsit", r"cornubianit", r"corneana", r"llicorell", r"riolit",
    r"riodacit", r"dacit", r"andesit", r"porfir", r"basalt", r"ignimbrit", r"lidit",
    r"saul[óo]", r"buntsandstein", r"gres(os)? vermell", r"volc[àa]n",
]
# Calcari SEGUR
GEO_CALCARI = [
    r"calc[àa]", r"calci", r"marbre", r"dolom", r"guix", r"margu", r"\bmarga",
    r"travert", r"carbonat", r"oolit", r"muschelkalk", r"keuper",
]
# DETRÍTIC ambigu: pot ser àcid o amb ciment calcari — soles no es consideren silici
GEO_DETRITIC = [
    r"\bgres", r"conglomerat", r"arenisc", r"lutit", r"\bargil", r"\bllim", r"\bsorr",
    r"\bgrav", r"bretx", r"arcos",
]


def classify_geologia_text(text):
    """Retorna 'silici', 'calcari', 'mixt' o None segons la litologia.
    - silici SEGUR sol -> silici; calcari SEGUR sol -> calcari
    - silici i calcari junts, o calcari + detrític (margues i gresos) -> mixt
    - només detrític (gres, conglomerat, argila...) -> mixt (ambigu)
    - res reconeixible -> None"""
    if not text:
        return None
    lower = text.lower()
    has_si = any(re.search(p, lower) for p in GEO_SILICI)
    has_ca = any(re.search(p, lower) for p in GEO_CALCARI)
    has_de = any(re.search(p, lower) for p in GEO_DETRITIC)
    if has_si and has_ca:
        return "mixt"
    if has_ca:
        return "mixt" if has_de else "calcari"
    if has_si:
        return "silici"
    if has_de:
        return "mixt"
    return None


def extract_geologia_description(txt):
    """Fragment curt del text de l'ICGC (camps de descripció), per desar-lo al
    cache i poder reclassificar més endavant sense tornar a consultar."""
    parts = []
    for line in txt.splitlines():
        l = line.strip()
        low = l.lower()
        if low.startswith("descripcio") or low.startswith("descripció") or "litolog" in low:
            parts.append(l[:160])
    snippet = " | ".join(parts) if parts else " ".join(txt.split())[:200]
    return snippet[:260]


def fetch_geologia_at_point(lat, lon, timeout=10):
    """Consulta la unitat geològica en un punt. Retorna (classe, fragment de
    text). LLANÇA excepció si el servei falla o respon amb un error: el
    cridant NO ha de desar res en aquest cas (no és el mateix que 'sense
    roca reconeguda')."""
    d = 0.01
    params = (
        f"?REQUEST=GetFeatureInfo&SERVICE=WMS&VERSION=1.1.1&LAYERS={GEOLOGIA_LAYER}"
        f"&STYLES=&FORMAT=image/png&SRS=EPSG:4326"
        f"&BBOX={lon-d},{lat-d},{lon+d},{lat+d}"
        f"&WIDTH=101&HEIGHT=101&QUERY_LAYERS={GEOLOGIA_LAYER}&X=50&Y=50&INFO_FORMAT=text/plain"
    )
    url = GEOLOGIA_WMS_URL + params
    req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        txt = resp.read().decode("utf-8", errors="ignore")
    low = txt.lower()
    if "serviceexception" in low or "<html" in low or "exception" in low[:300]:
        raise RuntimeError("resposta d'error del servei de geologia")
    return classify_geologia_text(txt), extract_geologia_description(txt)


def load_geologia_cache(zones=None):
    """Carrega el cache de geologia (versió 2, per coordenades). Si troba el
    format antic (per id de zona, sense versió) el migra a coordenades fent
    servir 'zones' i marca cada entrada com a 'legacy'. Retorna {cellkey:
    {"c": classe, "t": text, "legacy": bool}}."""
    try:
        with open(GEOLOGIA_CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    cached_at = cache.get("cached_at")
    if cached_at:
        try:
            age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(cached_at)).days
        except ValueError:
            age_days = 0
        if age_days > GEOLOGIA_CACHE_MAX_DAYS:
            print(f"  Cache de geologia caducat ({age_days} dies) — es torna a consultar")
            return {}

    points = cache.get("points", {})
    if cache.get("version") == GEOLOGIA_CACHE_VERSION:
        return points

    # Format antic: {id: classe}. Es migra a coordenades.
    if not zones:
        return {}
    by_id = {str(z["id"]): cell_key(z["lat"], z["lon"]) for z in zones}
    migrated = {}
    for zid, cls in points.items():
        key = by_id.get(zid)
        if key is None:
            continue
        migrated[key] = {"c": cls, "t": "", "legacy": True}
    print(f"  Geologia: cache antic (per id) migrat a coordenades — {len(migrated)} punts, a reconfirmar amb les regles noves")
    return migrated


def save_geologia_cache(points):
    cache = {
        "version": GEOLOGIA_CACHE_VERSION,
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "points": points,
    }
    with open(GEOLOGIA_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def geologia_label(entry):
    """Etiqueta que usa el scoring per a una entrada del cache. Un 'silici'
    antic (no reconfirmat) és 'silici_prov': podia ser conglomerat o gres."""
    if not entry:
        return None
    cls = entry.get("c")
    if entry.get("legacy") and cls == "silici":
        return "silici_prov"
    return cls


def build_geologia_lookup(zones, tree_types=None, max_seconds=700, batch_per_run=350):
    """
    Completa / reconfirma el cache de geologia per lots (com el refinament de
    VEGETACIO): consulta els punts sense dada i els antics encara
    provisionals, amb un límit de temps i de quantitat per execució.
    Prioritat: punts forestals primer; sense dada abans que reconfirmar; entre
    els reconfirmables, primer els 'silici' antics i els que van quedar None
    (podien ser fallades de xarxa). Els calcari / mixt antics es mantenen.

    Una fallada de xarxa NO es desa (es reintenta la propera execució) i, si
    fallen 8 consultes seguides, s'atura la tanda (servei caigut).
    """
    points = load_geologia_cache(zones)
    tree_types = tree_types or {}

    def forest_rank(z):
        t = tree_types.get(z["id"])
        return 0 if (t and t not in NON_FOREST and t != UNRESOLVED_TREE) else 1

    pending = []
    for z in zones:
        key = cell_key(z["lat"], z["lon"])
        entry = points.get(key)
        if entry is None:
            pending.append((0, forest_rank(z), z))
        elif entry.get("legacy"):
            if entry.get("c") == "silici":
                pending.append((1, forest_rank(z), z))
            elif entry.get("c") is None:
                pending.append((2, forest_rank(z), z))
    pending.sort(key=lambda t: (t[1], t[0]))  # forestals primer; dins, sense dada > silici antic > None antic

    if pending:
        print(f"  Geologia: {len(pending)} punts per consultar/reconfirmar — fent una tanda de com a molt {batch_per_run}...")
        start = time.time()
        consulted = failed = consecutive_fail = 0
        for _rank, _forest, z in pending[:batch_per_run]:
            if time.time() - start > max_seconds:
                print(f"  Geologia: límit de temps ({max_seconds}s) assolit a {consulted} punts — es continua la propera execució")
                break
            try:
                cls, snippet = fetch_geologia_at_point(z["lat"], z["lon"])
                points[cell_key(z["lat"], z["lon"])] = {"c": cls, "t": snippet}
                consulted += 1
                consecutive_fail = 0
            except Exception:
                failed += 1
                consecutive_fail += 1
                if consecutive_fail >= 8:
                    print("  Geologia: 8 fallades seguides — servei no disponible, s'atura la tanda (es reintentarà)")
                    break
        save_geologia_cache(points)
        print(f"  Geologia: {consulted} punts consultats, {failed} fallades (no desades, es reintenten)")
    else:
        print("  Geologia: tots els punts ja són al cache i reconfirmats")

    return {key: geologia_label(entry) for key, entry in points.items()}, points


def main():
    try:
        results = build_results()
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"ERROR consultant dades meteorològiques: {e}")
        return

    evolution = save_evolution(results)
    score_changes = compute_score_changes(evolution, results, days_back=7)
    results["score_changes_7d"] = score_changes
    if score_changes:
        risers = sorted(score_changes.items(), key=lambda kv: kv[1]["change"], reverse=True)[:5]
        print(f"Evolució 7 dies: {len(score_changes)} zones amb comparativa, top pujades: " +
              ", ".join(f"{zid}(+{c['change']})" for zid, c in risers if c["change"] > 0))

    print("Contrastant precisió del model amb hallazgos reals...")
    hallazgos = fetch_hallazgos()
    accuracy = compute_model_accuracy(hallazgos, evolution)
    results["model_accuracy"] = accuracy
    if accuracy["total_comparable"] > 0:
        print(f"  Precisió: {accuracy['precision_global']}% ({accuracy['aciertos']}/{accuracy['total_comparable']} hallazgos contrastables)")
    else:
        print("  Encara no hi ha prou hallazgos contrastables (calen data + coordenades que coincideixin amb dies de l'historial)")

    out_path = "../data/resultats.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    forest_count = sum(1 for z in results["zones"] if z["is_forest"])
    print(f"Fet. {len(results['zones'])} zones desades a {out_path} ({forest_count} boscoses)")
    print(f"Generat: {results['generated_at']}")


def dedupe_zones(zones, min_km=0.5):
    """
    Elimina els punts de la graella que cauen gairebé al mateix lloc.

    Es va detectar (15/10/2026) que ~70% dels punts tenien un "bessó" a menys
    de 100 m (la densificació a 2.5 km tornava a incloure els nodes de la
    graella base de 5 km i els punts de verificació del sondeig): 8285 punts
    eren només ~4900 llocs diferents. Efectes: consultes duplicades a
    Open-Meteo / ICGC, resultats.json el doble de gran, i quatre marcadors
    "Matadepera" apilats al mapa. Entre els punts no hi ha cap distància
    entre 200 m i 2 km, així que qualsevol llindar entre 0.2 i 2 km és segur;
    0.5 km.

    No es renumera res: es conserva l'id original del punt que es queda (de
    cada parell, un de forestal abans que un de no forestal, i si empaten
    l'id més baix), perquè els caches indexats per id (bosc, noms de zona,
    evolució) segueixin sent vàlids.
    """
    try:
        tree_cache = load_tree_cache()
    except Exception:
        tree_cache = {}

    def rank(z):
        t = tree_cache.get(z["id"])
        is_forest = bool(t) and t not in NON_FOREST and t != UNRESOLVED_TREE
        return (0 if is_forest else 1, z["id"])

    cell = 0.01  # ~1.1 km
    grid = {}
    kept = []
    for z in sorted(zones, key=rank):
        ci, cj = int(z["lat"] / cell), int(z["lon"] / cell)
        duplicate = False
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for k in grid.get((ci + di, cj + dj), ()):
                    if haversine_km(z["lat"], z["lon"], k["lat"], k["lon"]) < min_km:
                        duplicate = True
                        break
                if duplicate:
                    break
            if duplicate:
                break
        if not duplicate:
            kept.append(z)
            grid.setdefault((ci, cj), []).append(z)
    kept.sort(key=lambda z: z["id"])
    if len(kept) < len(zones):
        print(f"  Graella: {len(zones) - len(kept)} punts duplicats (< {min_km} km d'un altre) descartats — {len(kept)} llocs diferents")
    return kept


# Es carrega/genera aquí (i no a l'inici del fitxer) perquè depèn de
# retry_with_backoff, definida més amunt però després del punt on abans
# s'executava aquesta línia.
ZONES = dedupe_zones(load_or_build_zones())


if __name__ == "__main__":
    main()
