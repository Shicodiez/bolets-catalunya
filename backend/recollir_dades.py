"""
Predictor de bolets a Catalunya — recollida de dades i càlcul de puntuació.

Aquest script:
1. Genera (o carrega del cache) una graella densa de punts sobre Catalunya
   (~1470 punts vàlids, cada ~5km), amb altitud real (Copernicus DEM via
   Open-Meteo Elevation API) i nom de lloc real (reverse geocoding).
2. Consulta dades meteorològiques en viu (Open-Meteo): pluja, temperatura,
   humitat del sòl, evapotranspiració i humitat relativa de l'aire.
3. Contrasta amb estacions reals mitjançant triangulació IDW combinant
   AEMET, Meteocat/XEMA i Meteoclimatic — i amb radar de superfície
   (RainViewer; el radar d'AEMET queda desactivat, ver AEMET_RADAR_ENABLED).
4. Consulta el WMS de cobertes del sòl de l'ICGC per al tipus de bosc
   genèric de cada punt, refinat a espècie exacta d'arbre amb el servei
   VEGETACIO de la Generalitat.
5. Consulta GBIF/FungaCAT per a la distribució mensual i d'altitud real
   de cada espècie de bolet, en comptes d'una estimació manual.
6. Calcula una puntuació de 0-100 per a cada espècie de bolet en cada punt
   (evidència acumulada, no tot-o-res), amb un nivell de confiança
   independent de la puntuació.
7. Compara amb l'històric propi (evolució 7 dies) i amb les sortides reals
   registrades pels usuaris (tasa de confirmació).
8. Desa el resultat en un fitxer JSON (data/resultats.json) que la web
   llegeix, junt amb diversos fitxers de cache a data/.

Pensat per executar-se automàticament cada 6 hores via GitHub Actions
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
# 1. GRAELLA DE PUNTS DE CATALUNYA (~1470 punts, generada i cacheada automàticament)
# ---------------------------------------------------------------------------
# Cada punt: id, latitud, longitud, altitud REAL (m, Copernicus DEM via
# Open-Meteo Elevation API — no una estimació). Es genera un cop (filtrant
# amb un polígon aproximat de Catalunya per no caure al mar) i es guarda en
# cache permanent (data/zones_grid.json); el tipus de bosc es consulta en
# viu al WMS de l'ICGC per a cada punt per separat, més avall.

GRID_SPACING_KM = 5  # densitat de la graella (5km, ~1570 punts generats, ~1470 vàlids tras filtrar mar/altitud invàlida)
GRID_CACHE_PATH = "../data/zones_grid.json"

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
    polígon aproximat per no generar massa punts al mar. La graella
    resultant (~1570 punts a 5km) és 4x més densa que l'anterior (390 a
    10km), verificada perquè amb 10km dona ~393 punts (gairebé idèntic als
    390 originals, confirma que el polígon és prou fidel)."""
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


def build_zones_with_real_elevation():
    """
    Genera la graella de punts i consulta l'altitud REAL de cadascun (en
    comptes de l'aproximació per blocs que es feia servir abans — es va
    detectar que 69 dels 390 punts originals compartien exactament la
    mateixa altitud "250", senyal que no era una dada real per coordenada).
    Es couen 100 punts per petició (16 peticions per a ~1570 punts).
    """
    grid_points = generate_grid_points()
    print(f"  Graella generada: {len(grid_points)} punts (abans de consultar altitud)")

    all_elevations = []
    batch_size = 100
    for i in range(0, len(grid_points), batch_size):
        batch = grid_points[i:i + batch_size]
        try:
            elevs = retry_with_backoff(
                lambda b=batch: fetch_elevations_batch(b),
                description=f"Elevation API lot {i // batch_size + 1}",
            )
            all_elevations.extend(elevs)
        except Exception as e:
            print(f"  AVÍS: lot d'altituds {i // batch_size + 1} ha fallat ({e}) — es descarten aquests punts")
            all_elevations.extend([None] * len(batch))
        time.sleep(1)  # cortesia amb el servei gratuït

    zones = []
    for idx, ((lat, lon), elev) in enumerate(zip(grid_points, all_elevations), start=1):
        if elev is None or elev < 0:
            continue  # probablement mar o dada no disponible
        zones.append({"id": idx, "lat": lat, "lon": lon, "alt": round(elev)})

    print(f"  Zones finals amb altitud real vàlida: {len(zones)}")
    return zones


def load_or_build_zones():
    """
    Carrega la graella des del cache si existeix (mai caduca — les
    coordenades i l'altitud del terreny no canvien), o la genera de nou la
    primera vegada (o si el fitxer no existeix / està malmès).
    """
    try:
        with open(GRID_CACHE_PATH, "r", encoding="utf-8") as f:
            cached = json.load(f)
        zones = cached.get("zones")
        if zones and len(zones) > 100:  # comprovació bàsica de sanitat
            print(f"  Graella carregada des del cache: {len(zones)} punts")
            return zones
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    print("  Graella no trobada al cache — generant-la de nou (només passa un cop)...")
    zones = build_zones_with_real_elevation()
    try:
        with open(GRID_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({"generated_at": datetime.now(timezone.utc).isoformat(), "zones": zones}, f, ensure_ascii=False)
    except Exception as e:
        print(f"  AVÍS: no s'ha pogut desar el cache de la graella ({e}) — es tornarà a generar la propera execució")
    return zones


# ZONES es carrega/genera al final del fitxer (després que totes les
# funcions auxiliars, incloent retry_with_backoff, ja estiguin definides).


# ---------------------------------------------------------------------------
# 2. ESPÈCIES DE BOLETS I LA SEVA LÒGICA
# ---------------------------------------------------------------------------
SPECIES = [
    {"id": "rovellons",   "name": "Rovellons",           "scientific": ["Lactarius deliciosus", "Lactarius sanguifluus"],      "trees": ["pi_roig", "pi_negre", "pi_pinyer", "pi_blanc", "pi_altres"], "rain_days": [7, 15],  "temp_range": [4, 16],  "min_rain": 20},
    {"id": "ceps",        "name": "Ceps",                 "scientific": ["Boletus edulis", "Boletus aereus", "Boletus pinophilus"], "trees": ["roure", "faig", "pi_roig", "pi_negre", "pi_altres"],        "rain_days": [8, 16],  "temp_range": [6, 18],  "min_rain": 25},
    {"id": "camagrocs",   "name": "Camagrocs",            "scientific": ["Craterellus lutescens"],                              "trees": ["faig", "roure", "alzina"],                                  "rain_days": [10, 20], "temp_range": [6, 16],  "min_rain": 20},
    {"id": "trompetes",   "name": "Trompetes de la mort", "scientific": ["Craterellus cornucopioides"],                         "trees": ["faig", "roure"],                                            "rain_days": [10, 20], "temp_range": [5, 15],  "min_rain": 25},
    {"id": "oureig",      "name": "Ou de reig",           "scientific": ["Amanita caesarea"],                                   "trees": ["alzina", "roure", "suro"],                                  "rain_days": [6, 14],  "temp_range": [10, 22], "min_rain": 18},
    {"id": "rossinyols",  "name": "Rossinyols",           "scientific": ["Cantharellus cibarius"],                              "trees": ["faig", "roure", "pi_roig", "pi_altres"],                    "rain_days": [7, 16],  "temp_range": [6, 17],  "min_rain": 20},
    {"id": "colmenilles", "name": "Colmenilles",          "scientific": ["Morchella esculenta", "Morchella elata"],             "trees": ["roure", "pi_blanc", "pi_altres"],                           "rain_days": [8, 18],  "temp_range": [2, 13],  "min_rain": 15},
    {"id": "llengua",     "name": "Llengua de bou",       "scientific": ["Hydnum repandum"],                                    "trees": ["roure", "suro"],                                            "rain_days": [10, 20], "temp_range": [8, 18],  "min_rain": 20},
    {"id": "pinetell",    "name": "Pinetell",             "scientific": ["Lactarius deliciosus"],                               "trees": ["pi_roig", "pi_negre", "pi_altres"],                         "rain_days": [7, 14],  "temp_range": [4, 15],  "min_rain": 20},
    {"id": "fredolic",    "name": "Fredolic",             "scientific": ["Tricholoma terreum"],                                 "trees": ["pi_blanc", "alzina", "pi_altres"],                          "rain_days": [9, 18],  "temp_range": [3, 14],  "min_rain": 18},
]

TREE_LABELS = {
    "pi_roig": "pinar de pino rojo", "pi_negre": "pinar de pino negro", "avet": "abetal",
    "pi_blanc": "pinar de pino blanco", "pi_pinyer": "pinar de pino piñonero",
    "pi_altres": "bosque de coníferas (especie no diferenciada)",
    "alzina": "encinar/bosque de perennifolios", "roure": "robledal/bosque de caducifolios",
    "faig": "hayedo", "suro": "alcornocal", "mixt": "bosque mixto",
    "matollar": "matorral", "prat": "prado/pastizal", "desconegut": "tipo de bosque desconocido",
}

# Mapa de tipus de bosc no forestal / desconegut que no assignem a cap espècie
NON_FOREST = {"conreu", "urba", "desconegut", "aigua", "roca", "matollar", "prat"}

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


def fetch_weather(zones, batch_size=40, delay_between_batches=3):
    """Open-Meteo accepta moltes coordenades per petició, però es fan lots
    més petits (40, abans 100) i amb una pausa entre ells (3s, abans 1.5s).
    Confirmat amb un HTTP 429 explícit que Open-Meteo aplica "throttling"
    temporal si detecta ràfegues de peticions seguides (no documenten un
    límit fix per minut, però avisen que "excessive bursting may be
    throttled") — amb ~1570 punts i 37 lots calia més marge del que dona
    una pausa curta. Cada lot es reintenta amb retry_with_backoff, que ara
    tracta el 429 amb una espera més llarga."""
    all_results = []
    n_batches = -(-len(zones) // batch_size)
    for i in range(0, len(zones), batch_size):
        batch = zones[i:i + batch_size]
        batch_num = i // batch_size + 1
        results = retry_with_backoff(
            lambda b=batch: fetch_weather_batch(b),
            max_attempts=5,
            description=f"Open-Meteo lot {batch_num}/{n_batches}",
        )
        all_results.extend(results)
        if batch_num < n_batches:
            time.sleep(delay_between_batches)
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

def species_score(sp, rain_10d, min_temp, tree, days_since_rain, alt, month, aemet_rain_1h=None, mc_rain_today=None, gbif_distributions=None, triangulation=None, soil_stats=None, radar_value=None, geologia=None):
    """
    Sistema de puntuació 0-100 per evidència acumulada, no tot-o-res. Cada
    factor suma punts segons com d'a prop està del rang òptim (amb tolerància
    als marges, no un tall sec), i s'hi afegeixen factors climàtics/geogràfics
    que no depenen només de la lectura meteorològica exacta d'un dia concret.

    Retorna 0 si l'hàbitat és incompatible (això sí és un requisit dur —
    un rovelló no surt sota una alzina, per molt bones que siguin la resta
    de condicions). La resta de factors són graduals.
    """
    if tree not in sp["trees"]:
        return 0, {}, "baja"

    breakdown = {}
    score = 0.0

    # --- Pluja acumulada (0-22 punts, amb tolerància) ---
    # Es redueix respecte al disseny anterior (0-30) perquè ara la humitat
    # real del sòl (component nou, més avall) recull part d'aquesta
    # evidència de forma més directa quan hi ha dada disponible.
    min_rain = sp["min_rain"]
    ratio = rain_10d / min_rain if min_rain else 1
    if ratio >= 1:
        rain_score = 22
    elif ratio >= 0.7:
        rain_score = 22 * ((ratio - 0.7) / 0.3) * 0.6 + 9
    elif ratio >= 0.4:
        rain_score = 9 * ((ratio - 0.4) / 0.3)
    else:
        rain_score = 0
    breakdown["pluja"] = round(rain_score, 1)
    score += rain_score

    # --- Dies des de la pluja (0-25 punts, amb marges tous) ---
    lo, hi = sp["rain_days"]
    if lo <= days_since_rain <= hi:
        days_score = 25
    else:
        mid = (lo + hi) / 2
        span = (hi - lo) / 2 + 5  # marge de tolerància més enllà del rang
        dist = abs(days_since_rain - mid) - (hi - lo) / 2
        days_score = max(0, 25 - (dist / 5) * 12)
    breakdown["dies_pluja"] = round(days_score, 1)
    score += days_score

    # --- Temperatura mínima (0-20 punts, amb marges tous) ---
    tlo, thi = sp["temp_range"]
    if tlo <= min_temp <= thi:
        temp_score = 20
    else:
        tmid = (tlo + thi) / 2
        dist = abs(min_temp - tmid) - (thi - tlo) / 2
        temp_score = max(0, 20 - (dist / 3) * 10)
    breakdown["temperatura"] = round(temp_score, 1)
    score += temp_score

    # --- Humitat real del sòl (0-8 punts) — distingeix "pluja que ha quedat
    # al sòl" de "pluja que se l'ha begut la terra ressecada o l'ha perdut
    # l'evapotranspiració". Nomes s'aplica si hi ha dada (Open-Meteo pot no
    # donar-la per a tots els punts); si no n'hi ha, aquests punts es
    # reparteixen proporcionalment entre els altres components perquè el
    # total segueixi sent 100 com a màxim teòric.
    soil_score = 0
    if soil_stats and soil_stats.get("soil_moisture_avg_7d") is not None:
        moisture = soil_stats["soil_moisture_avg_7d"]
        trend = soil_stats.get("soil_moisture_trend") or 0
        # Llindars orientatius: per sobre de 0.30 m³/m³ el sòl sol estar prou
        # humit per a la majoria de sòls forestals catalans; per sota de 0.15
        # sol estar sec. S'hi suma un petit bonus si la tendència és a l'alça
        # (el sòl s'està humitejant, no només "ja ho estava").
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
        # Humitat relativa de l'aire (complementa la del sòl, no la
        # substitueix): un aire molt sec pot ressecar la capa més
        # superficial i el barret del bolet encara que el sòl profund
        # segueixi humit — petit ajust dins del mateix component, no un de
        # nou, perquè el total de 100 punts no es descompensi.
        air_humidity = soil_stats.get("air_humidity_avg_3d")
        if air_humidity is not None:
            if air_humidity < 50:
                soil_score = max(0, soil_score - 1)
            elif air_humidity >= 80:
                soil_score = min(8, soil_score + 1)
    breakdown["humitat_sol"] = round(soil_score, 1)
    score += soil_score

    # --- Climatologia de temporada per altitud (0-15 punts) ---
    # Coneixement micològic establert: cada espècie té una temporada més
    # probable segons l'altitud, independentment del detall exacte del dia.
    season_score = seasonal_climate_score(sp, alt, month, gbif_distributions)
    # Ajust petit i honest per geologia del sòl (silici/calcari): només per
    # a les espècies amb evidència clara i consistent trobada (ceps i ou de
    # reig prefereixen sòl silici; camagrocs prefereix calcari). Per a la
    # resta d'espècies, o si no hi ha dada de geologia, no s'aplica cap
    # ajust — millor no ajustar que inventar una preferència dubtosa.
    preferred_soil = SPECIES_SOIL_PREFERENCE.get(sp["id"])
    if preferred_soil and geologia:
        if geologia == preferred_soil:
            season_score = min(15, season_score + 1.5)
        elif geologia not in ("mixt", None):
            season_score = max(0, season_score - 1.5)
    breakdown["temporada"] = round(season_score, 1)
    score += season_score

    # --- Corroboració entre fonts (0-10 punts bonus) ---
    # El radar dona cobertura de superfície directa del propi punt (no d'una
    # estació propera), així que és la senyal més fiable quan hi és
    # disponible — detecta tempestes molt localitzades que cap estació
    # puntual pot haver captat. Si no hi ha radar, es fa servir la
    # triangulació d'estacions com abans.
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

    final_score = max(0, min(100, round(score)))
    confidence = compute_confidence(sp, gbif_distributions, aemet_rain_1h, mc_rain_today, triangulation, radar_value)

    return final_score, breakdown, confidence


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
    return cache.get("species", {})


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
    missing = [sp for sp in SPECIES if sp["id"] not in cache]

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
            cache[sp["id"]] = {
                "month_counts": combined_months,
                "alt_bucket_counts": {str(k): v for k, v in combined_alt_buckets.items()},
                "total_with_elevation": total_elevation,
            }
            total = sum(combined_months.values())
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


def save_vegetacio_layers_cache(layers):
    cache = {"cached_at": datetime.now(timezone.utc).isoformat(), "layers": layers}
    with open(VEGETACIO_LAYERS_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def layer_relevant_for_group(layer_name, tree_group):
    """Decideix si val la pena consultar aquesta capa d'espècie per a un punt
    del grup genèric donat (pi_altres/roure/alzina), per no fer peticions
    innecessàries. Si l'espècie no està mapejada, es consulta igualment
    (millor un punt de més que perdre'n un de vàlid)."""
    for species_key, group in VEGETACIO_SPECIES_TO_GROUP.items():
        if species_key in layer_name:
            return group == tree_group
    return True


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
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            txt = resp.read().decode("utf-8", errors="ignore")
        return "Feature" in txt or "<gml" in txt.lower()
    except Exception:
        return False


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


TREE_CACHE_PATH = "../data/bosc_cache.json"
TREE_CACHE_MAX_DAYS = 30


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
ZONE_NAMES_BATCH_PER_RUN = 20


def reverse_geocode_place(lat, lon, timeout=10):
    """Retorna un nom de lloc reconeixible per a unes coordenades (poble,
    llogaret o, si no n'hi ha, comarca/paratge), via Nominatim (OSM)."""
    params = f"?lat={lat}&lon={lon}&format=json&zoom=12&accept-language=ca"
    url = "https://nominatim.openstreetmap.org/reverse" + params
    req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0 (github.com/Shicodiez/bolets-catalunya)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        addr = data.get("address", {})
        name = (
            addr.get("village") or addr.get("town") or addr.get("hamlet")
            or addr.get("municipality") or addr.get("city") or addr.get("county")
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
    weather_results = fetch_weather(ZONES)  # cada lot ja es reintenta individualment dins de fetch_weather

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
        icgc_max_seconds = 1000  # augmentat de 280 a 1000: amb la graella nova (~1570 punts),
        # la primera execució té TOTS els punts sense cache de cop — cal prou marge
        for i, z in enumerate(missing_zones):
            if time.time() - icgc_start > icgc_max_seconds:
                print(f"  ICGC: límit de temps ({icgc_max_seconds}s) assolit a {i}/{len(missing_zones)} — es continua sense la resta")
                for remaining in missing_zones[i:]:
                    tree_types[remaining["id"]] = "desconegut"
                break
            tree, _label = fetch_tree_type(z["lat"], z["lon"], layer_name, debug=False)
            tree_types[z["id"]] = tree
            time.sleep(0.05)
            if (i + 1) % 50 == 0:
                print(f"  ICGC: {i + 1}/{len(missing_zones)} punts consultats...")
        save_tree_cache(tree_types)
    else:
        print("  Tots els punts trobats al cache — no cal consultar l'ICGC")

    known_trees = sum(1 for t in tree_types.values() if t not in NON_FOREST)
    print(f"Bosc: {known_trees}/{len(ZONES)} punts amb tipus de bosc identificat")

    print("Refinant espècie exacta amb VEGETACIO (sig.gencat.cat)...")
    vegetacio_layers = load_vegetacio_layers_cache()
    if vegetacio_layers is None:
        vegetacio_layers = discover_vegetacio_species_layers()
        if vegetacio_layers:
            save_vegetacio_layers_cache(vegetacio_layers)
    print(f"  VEGETACIO: {len(vegetacio_layers)} capes d'espècie disponibles")

    refined_count = 0
    if vegetacio_layers:
        veg_start = time.time()
        veg_max_seconds = 400  # augmentat de 200 a 400 en passar de 390 a ~1570 punts
        for zone in ZONES:
            if time.time() - veg_start > veg_max_seconds:
                print(f"  VEGETACIO: límit de temps ({veg_max_seconds}s) assolit — es continua sense refinar la resta")
                break
            current_tree = tree_types.get(zone["id"], "desconegut")
            if current_tree in NON_FOREST:
                continue
            for layer in vegetacio_layers:
                if not layer_relevant_for_group(layer, current_tree):
                    continue
                if fetch_vegetacio_species_for_point(zone["lat"], zone["lon"], layer):
                    refined_tree = species_layer_to_tree_key(layer)
                    if refined_tree:
                        tree_types[zone["id"]] = refined_tree
                        refined_count += 1
                    break  # ja trobada una espècie coincident per aquest punt
    print(f"  VEGETACIO: {refined_count} punts refinats amb espècie exacta")

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
        geologia_lookup = build_geologia_lookup(ZONES)
        found_count = sum(1 for v in geologia_lookup.values() if v is not None)
        print(f"  Geologia: {found_count}/{len(geologia_lookup)} punts classificats")
        data_coverage["geologia"] = {"ok": True, "detail": f"{found_count} punts classificats"}
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

    current_month = datetime.now(timezone.utc).month
    today_str = datetime.now(timezone.utc).date().isoformat()
    today_history = history.get(today_str, {})

    zones_out = []
    for zone, daily_wrapper in zip(ZONES, weather_results):
        daily = daily_wrapper.get("daily", {})
        hourly = daily_wrapper.get("hourly", {})
        rain_10d, avg_temp, min_temp, days_since_rain = compute_rain_stats(daily)
        soil_stats = compute_soil_moisture_stats(hourly)
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
        geologia = geologia_lookup.get(str(zone["id"]))

        triangulation = triangulate_rain(zone["lat"], zone["lon"], aemet_stations, mc_stations, meteocat_stations=meteocat_stations)

        species_scores = []
        if tree not in NON_FOREST:
            for sp in SPECIES:
                s, breakdown, confidence = species_score(
                    sp, rain_10d, min_temp, tree, days_since_rain, zone["alt"], current_month,
                    aemet_rain_1h=aemet_rain_1h, mc_rain_today=mc_rain_today,
                    gbif_distributions=gbif_distributions, triangulation=triangulation,
                    soil_stats=soil_stats, radar_value=radar_value, geologia=geologia,
                )
                if s > 0:
                    species_scores.append({"id": sp["id"], "name": sp["name"], "score": s, "confidence": confidence, "breakdown": breakdown})
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
            "is_forest": tree not in NON_FOREST,
            "rain_10d": rain_10d,
            "avg_temp": avg_temp,
            "min_temp": min_temp,
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

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "default_threshold": DEFAULT_SCORE_THRESHOLD,
        "credential_warnings": credential_warnings,
        "data_coverage": data_coverage,
        "zones": zones_out,
        "species_catalog": [{"id": sp["id"], "name": sp["name"]} for sp in SPECIES],
        "all_stations": build_all_stations_list(aemet_stations, meteocat_stations, mc_stations),
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
        add_station("meteocat", st.get("name", "?"), st.get("lat"), st.get("lon"), st.get("prec_1h"), None)
    for st in mc_stations or []:
        add_station("meteoclimatic", st.get("location", "?"), st.get("lat"), st.get("lon"), st.get("rain_today_mm"), None)

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

GEOLOGIA_WMS_URL = "https://geoserveis.icgc.cat/servei/catalunya/geologia-territorial/wms"
GEOLOGIA_LAYER = "unitats-geologiques-50000"
GEOLOGIA_CACHE_PATH = "../data/geologia_cache.json"
GEOLOGIA_CACHE_MAX_DAYS = 180  # la geologia del terreny no canvia mai

GEOLOGIA_KEYWORDS_CALCARI = [
    "calcària", "calcàries", "calcaria", "marbre", "guix", "dolomia", "margu",
    "marga", "travertí",
]
GEOLOGIA_KEYWORDS_SILICI = [
    "granit", "pissarra", "gres", "quarsita", "fil·lit", "filita", "basalt",
    "andesita", "esquist", "gneis", "conglomerat", "llicorella",
]

# Ajust petit i honest al bonus de temporada/hàbitat — només per a les 3
# espècies amb evidència clara i consistent trobada (ceps i ou de reig
# prefereixen sòl silici/àcid; camagrocs prefereix sòl calcari). Per a la
# resta d'espècies no s'aplica cap ajust (no hi ha prou evidència fiable).
SPECIES_SOIL_PREFERENCE = {
    "ceps": "silici",
    "oureig": "silici",
    "camagrocs": "calcari",
}


def classify_geologia_text(text):
    """Retorna 'silici', 'calcari', 'mixt' o None segons quines paraules
    clau apareixen al text de la resposta GetFeatureInfo."""
    if not text:
        return None
    lower = text.lower()
    has_calcari = any(kw in lower for kw in GEOLOGIA_KEYWORDS_CALCARI)
    has_silici = any(kw in lower for kw in GEOLOGIA_KEYWORDS_SILICI)
    if has_calcari and has_silici:
        return "mixt"
    if has_calcari:
        return "calcari"
    if has_silici:
        return "silici"
    return None


def fetch_geologia_at_point(lat, lon, timeout=10):
    """Consulta la unitat geològica en un punt concret i la classifica."""
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
    return classify_geologia_text(txt)


def load_geologia_cache():
    try:
        with open(GEOLOGIA_CACHE_PATH, "r", encoding="utf-8") as f:
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
    if age_days > GEOLOGIA_CACHE_MAX_DAYS:
        print(f"  Cache de geologia caducat ({age_days} dies) — es torna a consultar")
        return {}
    print(f"  Cache de geologia trobat ({age_days} dies)")
    return cache.get("points", {})


def save_geologia_cache(points):
    cache = {"cached_at": datetime.now(timezone.utc).isoformat(), "points": points}
    with open(GEOLOGIA_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def build_geologia_lookup(zones, max_seconds=300, batch_per_run=150):
    """
    Completa el cache de geologia per lots (com el refinament de VEGETACIO):
    consulta només els punts encara no cacheados, amb un límit de temps i
    de quantitat per execució perquè no allargui massa el procés — amb
    ~1470 punts, es completarà en diverses execucions successives.
    """
    cache = load_geologia_cache()
    missing = [z for z in zones if str(z["id"]) not in cache]

    if missing:
        print(f"  Geologia: {len(missing)} punts sense cache — consultant...")
        start = time.time()
        consulted = 0
        for z in missing[:batch_per_run]:
            if time.time() - start > max_seconds:
                print(f"  Geologia: límit de temps ({max_seconds}s) assolit a {consulted} punts — es continua la propera execució")
                break
            try:
                classification = fetch_geologia_at_point(z["lat"], z["lon"])
                cache[str(z["id"])] = classification  # es desa també si és None, per no reintentar
            except Exception:
                cache[str(z["id"])] = None
            consulted += 1
        save_geologia_cache(cache)
        print(f"  Geologia: {consulted} punts nous consultats aquesta execució")
    else:
        print("  Geologia: tots els punts ja són al cache")

    return cache


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


# Es carrega/genera aquí (i no a l'inici del fitxer) perquè depèn de
# retry_with_backoff, definida més amunt però després del punt on abans
# s'executava aquesta línia.
ZONES = load_or_build_zones()


if __name__ == "__main__":
    main()
