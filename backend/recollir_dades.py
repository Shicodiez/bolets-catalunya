"""
Predictor de bolets a Catalunya — recollida de dades i càlcul de puntuació.

Aquest script:
1. Genera una graella densa de punts sobre Catalunya (~150 punts, cada ~16km).
2. Consulta dades meteorològiques en viu (Open-Meteo) per a tota la graella.
3. Consulta AEMET OpenData per contrastar amb l'estació real més propera a cada punt.
4. Consulta el WMS de cobertes del sòl de l'ICGC per obtenir el tipus de bosc
   real de cada punt (pi roig, alzinar, fageda, etc.).
5. Calcula una puntuació de 0-100 per a cada espècie de bolet en cada punt,
   segons pluja acumulada, dies des de l'última pluja forta, temperatura i
   compatibilitat d'hàbitat.
6. Desa el resultat en un fitxer JSON (data/resultats.json) que la web llegeix.

Pensat per executar-se automàticament cada poques hores (veure README.md).
"""

import json
import math
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# 1. GRAELLA DE PUNTS DE CATALUNYA (~150 punts, generada automàticament)
# ---------------------------------------------------------------------------
# Cada punt: id, latitud, longitud, altitud aproximada (m).
# L'altitud és una estimació geogràfica (nord=més alt, costa=més baix);
# el tipus de bosc es consulta en viu al WMS de l'ICGC per a cada punt.

ZONES = [
    {"id": 1, "lat": 40.664, "lon": 0.685, "alt": 250},
    {"id": 2, "lat": 40.664, "lon": 0.88, "alt": 250},
    {"id": 3, "lat": 40.808, "lon": 0.49, "alt": 250},
    {"id": 4, "lat": 40.808, "lon": 0.685, "alt": 250},
    {"id": 5, "lat": 40.808, "lon": 0.88, "alt": 250},
    {"id": 6, "lat": 40.808, "lon": 1.076, "alt": 250},
    {"id": 7, "lat": 40.952, "lon": 0.295, "alt": 250},
    {"id": 8, "lat": 40.952, "lon": 0.49, "alt": 250},
    {"id": 9, "lat": 40.952, "lon": 0.685, "alt": 250},
    {"id": 10, "lat": 40.952, "lon": 0.88, "alt": 250},
    {"id": 11, "lat": 40.952, "lon": 1.076, "alt": 250},
    {"id": 12, "lat": 40.952, "lon": 1.271, "alt": 250},
    {"id": 13, "lat": 40.952, "lon": 1.466, "alt": 250},
    {"id": 14, "lat": 41.097, "lon": 0.295, "alt": 250},
    {"id": 15, "lat": 41.097, "lon": 0.49, "alt": 250},
    {"id": 16, "lat": 41.097, "lon": 0.685, "alt": 250},
    {"id": 17, "lat": 41.097, "lon": 0.88, "alt": 250},
    {"id": 18, "lat": 41.097, "lon": 1.076, "alt": 250},
    {"id": 19, "lat": 41.097, "lon": 1.271, "alt": 250},
    {"id": 20, "lat": 41.097, "lon": 1.466, "alt": 250},
    {"id": 21, "lat": 41.097, "lon": 1.661, "alt": 250},
    {"id": 22, "lat": 41.241, "lon": 0.295, "alt": 250},
    {"id": 23, "lat": 41.241, "lon": 0.49, "alt": 250},
    {"id": 24, "lat": 41.241, "lon": 0.685, "alt": 250},
    {"id": 25, "lat": 41.241, "lon": 0.88, "alt": 250},
    {"id": 26, "lat": 41.241, "lon": 1.076, "alt": 250},
    {"id": 27, "lat": 41.241, "lon": 1.271, "alt": 250},
    {"id": 28, "lat": 41.241, "lon": 1.466, "alt": 250},
    {"id": 29, "lat": 41.241, "lon": 1.661, "alt": 250},
    {"id": 30, "lat": 41.241, "lon": 1.856, "alt": 30},
    {"id": 31, "lat": 41.241, "lon": 2.051, "alt": 30},
    {"id": 32, "lat": 41.241, "lon": 2.246, "alt": 30},
    {"id": 33, "lat": 41.385, "lon": 0.295, "alt": 330},
    {"id": 34, "lat": 41.385, "lon": 0.49, "alt": 330},
    {"id": 35, "lat": 41.385, "lon": 0.685, "alt": 330},
    {"id": 36, "lat": 41.385, "lon": 0.88, "alt": 330},
    {"id": 37, "lat": 41.385, "lon": 1.076, "alt": 330},
    {"id": 38, "lat": 41.385, "lon": 1.271, "alt": 330},
    {"id": 39, "lat": 41.385, "lon": 1.466, "alt": 330},
    {"id": 40, "lat": 41.385, "lon": 1.661, "alt": 330},
    {"id": 41, "lat": 41.385, "lon": 1.856, "alt": 80},
    {"id": 42, "lat": 41.385, "lon": 2.051, "alt": 80},
    {"id": 43, "lat": 41.385, "lon": 2.246, "alt": 80},
    {"id": 44, "lat": 41.385, "lon": 2.441, "alt": 30},
    {"id": 45, "lat": 41.385, "lon": 2.637, "alt": 30},
    {"id": 46, "lat": 41.529, "lon": 0.295, "alt": 460},
    {"id": 47, "lat": 41.529, "lon": 0.49, "alt": 460},
    {"id": 48, "lat": 41.529, "lon": 0.685, "alt": 460},
    {"id": 49, "lat": 41.529, "lon": 0.88, "alt": 460},
    {"id": 50, "lat": 41.529, "lon": 1.076, "alt": 460},
    {"id": 51, "lat": 41.529, "lon": 1.271, "alt": 460},
    {"id": 52, "lat": 41.529, "lon": 1.466, "alt": 460},
    {"id": 53, "lat": 41.529, "lon": 1.661, "alt": 460},
    {"id": 54, "lat": 41.529, "lon": 1.856, "alt": 210},
    {"id": 55, "lat": 41.529, "lon": 2.051, "alt": 210},
    {"id": 56, "lat": 41.529, "lon": 2.246, "alt": 210},
    {"id": 57, "lat": 41.529, "lon": 2.441, "alt": 60},
    {"id": 58, "lat": 41.529, "lon": 2.637, "alt": 60},
    {"id": 59, "lat": 41.673, "lon": 0.295, "alt": 590},
    {"id": 60, "lat": 41.673, "lon": 0.49, "alt": 590},
    {"id": 61, "lat": 41.673, "lon": 0.685, "alt": 590},
    {"id": 62, "lat": 41.673, "lon": 0.88, "alt": 590},
    {"id": 63, "lat": 41.673, "lon": 1.076, "alt": 590},
    {"id": 64, "lat": 41.673, "lon": 1.271, "alt": 590},
    {"id": 65, "lat": 41.673, "lon": 1.466, "alt": 590},
    {"id": 66, "lat": 41.673, "lon": 1.661, "alt": 590},
    {"id": 67, "lat": 41.673, "lon": 1.856, "alt": 340},
    {"id": 68, "lat": 41.673, "lon": 2.051, "alt": 340},
    {"id": 69, "lat": 41.673, "lon": 2.246, "alt": 340},
    {"id": 70, "lat": 41.673, "lon": 2.441, "alt": 190},
    {"id": 71, "lat": 41.673, "lon": 2.637, "alt": 190},
    {"id": 72, "lat": 41.673, "lon": 2.832, "alt": 190},
    {"id": 73, "lat": 41.817, "lon": 0.295, "alt": 720},
    {"id": 74, "lat": 41.817, "lon": 0.49, "alt": 720},
    {"id": 75, "lat": 41.817, "lon": 0.685, "alt": 720},
    {"id": 76, "lat": 41.817, "lon": 0.88, "alt": 720},
    {"id": 77, "lat": 41.817, "lon": 1.076, "alt": 720},
    {"id": 78, "lat": 41.817, "lon": 1.271, "alt": 720},
    {"id": 79, "lat": 41.817, "lon": 1.466, "alt": 720},
    {"id": 80, "lat": 41.817, "lon": 1.661, "alt": 720},
    {"id": 81, "lat": 41.817, "lon": 1.856, "alt": 470},
    {"id": 82, "lat": 41.817, "lon": 2.051, "alt": 470},
    {"id": 83, "lat": 41.817, "lon": 2.246, "alt": 470},
    {"id": 84, "lat": 41.817, "lon": 2.441, "alt": 320},
    {"id": 85, "lat": 41.817, "lon": 2.637, "alt": 320},
    {"id": 86, "lat": 41.817, "lon": 2.832, "alt": 320},
    {"id": 87, "lat": 41.817, "lon": 3.027, "alt": 320},
    {"id": 88, "lat": 41.961, "lon": 0.49, "alt": 840},
    {"id": 89, "lat": 41.961, "lon": 0.685, "alt": 840},
    {"id": 90, "lat": 41.961, "lon": 0.88, "alt": 840},
    {"id": 91, "lat": 41.961, "lon": 1.076, "alt": 840},
    {"id": 92, "lat": 41.961, "lon": 1.271, "alt": 840},
    {"id": 93, "lat": 41.961, "lon": 1.466, "alt": 840},
    {"id": 94, "lat": 41.961, "lon": 1.661, "alt": 840},
    {"id": 95, "lat": 41.961, "lon": 1.856, "alt": 840},
    {"id": 96, "lat": 41.961, "lon": 2.051, "alt": 840},
    {"id": 97, "lat": 41.961, "lon": 2.246, "alt": 840},
    {"id": 98, "lat": 41.961, "lon": 2.441, "alt": 440},
    {"id": 99, "lat": 41.961, "lon": 2.637, "alt": 440},
    {"id": 100, "lat": 41.961, "lon": 2.832, "alt": 440},
    {"id": 101, "lat": 41.961, "lon": 3.027, "alt": 440},
    {"id": 102, "lat": 42.106, "lon": 0.49, "alt": 980},
    {"id": 103, "lat": 42.106, "lon": 0.685, "alt": 980},
    {"id": 104, "lat": 42.106, "lon": 0.88, "alt": 980},
    {"id": 105, "lat": 42.106, "lon": 1.076, "alt": 980},
    {"id": 106, "lat": 42.106, "lon": 1.271, "alt": 980},
    {"id": 107, "lat": 42.106, "lon": 1.466, "alt": 980},
    {"id": 108, "lat": 42.106, "lon": 1.661, "alt": 980},
    {"id": 109, "lat": 42.106, "lon": 1.856, "alt": 980},
    {"id": 110, "lat": 42.106, "lon": 2.051, "alt": 980},
    {"id": 111, "lat": 42.106, "lon": 2.246, "alt": 980},
    {"id": 112, "lat": 42.106, "lon": 2.441, "alt": 980},
    {"id": 113, "lat": 42.106, "lon": 2.637, "alt": 980},
    {"id": 114, "lat": 42.106, "lon": 2.832, "alt": 980},
    {"id": 115, "lat": 42.106, "lon": 3.027, "alt": 980},
    {"id": 116, "lat": 42.25, "lon": 0.49, "alt": 1110},
    {"id": 117, "lat": 42.25, "lon": 0.685, "alt": 1110},
    {"id": 118, "lat": 42.25, "lon": 0.88, "alt": 1110},
    {"id": 119, "lat": 42.25, "lon": 1.076, "alt": 1110},
    {"id": 120, "lat": 42.25, "lon": 1.271, "alt": 1110},
    {"id": 121, "lat": 42.25, "lon": 1.466, "alt": 1110},
    {"id": 122, "lat": 42.25, "lon": 1.661, "alt": 1110},
    {"id": 123, "lat": 42.25, "lon": 1.856, "alt": 1110},
    {"id": 124, "lat": 42.25, "lon": 2.051, "alt": 1110},
    {"id": 125, "lat": 42.25, "lon": 2.246, "alt": 1110},
    {"id": 126, "lat": 42.25, "lon": 2.441, "alt": 1110},
    {"id": 127, "lat": 42.25, "lon": 2.637, "alt": 1110},
    {"id": 128, "lat": 42.25, "lon": 2.832, "alt": 1110},
    {"id": 129, "lat": 42.25, "lon": 3.027, "alt": 1110},
    {"id": 130, "lat": 42.25, "lon": 3.222, "alt": 1110},
    {"id": 131, "lat": 42.394, "lon": 0.295, "alt": 1230},
    {"id": 132, "lat": 42.394, "lon": 0.49, "alt": 1230},
    {"id": 133, "lat": 42.394, "lon": 0.685, "alt": 1230},
    {"id": 134, "lat": 42.394, "lon": 0.88, "alt": 1230},
    {"id": 135, "lat": 42.394, "lon": 1.076, "alt": 1230},
    {"id": 136, "lat": 42.394, "lon": 1.271, "alt": 1230},
    {"id": 137, "lat": 42.394, "lon": 1.466, "alt": 1230},
    {"id": 138, "lat": 42.394, "lon": 1.661, "alt": 1230},
    {"id": 139, "lat": 42.394, "lon": 1.856, "alt": 1230},
    {"id": 140, "lat": 42.394, "lon": 2.051, "alt": 1230},
    {"id": 141, "lat": 42.394, "lon": 2.246, "alt": 1230},
    {"id": 142, "lat": 42.394, "lon": 2.441, "alt": 1230},
    {"id": 143, "lat": 42.394, "lon": 2.637, "alt": 1230},
    {"id": 144, "lat": 42.394, "lon": 2.832, "alt": 1230},
    {"id": 145, "lat": 42.394, "lon": 3.027, "alt": 1230},
    {"id": 146, "lat": 42.538, "lon": 0.49, "alt": 1360},
    {"id": 147, "lat": 42.538, "lon": 0.685, "alt": 1360},
    {"id": 148, "lat": 42.538, "lon": 0.88, "alt": 1360},
    {"id": 149, "lat": 42.538, "lon": 1.076, "alt": 1360},
    {"id": 150, "lat": 42.538, "lon": 1.271, "alt": 1360},
    {"id": 151, "lat": 42.538, "lon": 1.466, "alt": 1360},
    {"id": 152, "lat": 42.682, "lon": 0.685, "alt": 1490},
    {"id": 153, "lat": 42.682, "lon": 0.88, "alt": 1490},
]

# ---------------------------------------------------------------------------
# 2. ESPÈCIES DE BOLETS I LA SEVA LÒGICA
# ---------------------------------------------------------------------------
SPECIES = [
    {"id": "rovellons",   "name": "Rovellons",           "trees": ["pi_altres"],           "rain_days": [7, 15],  "temp_range": [8, 18],  "min_rain": 20},
    {"id": "ceps",        "name": "Ceps",                 "trees": ["roure", "pi_altres"],  "rain_days": [8, 16],  "temp_range": [10, 20], "min_rain": 25},
    {"id": "camagrocs",   "name": "Camagrocs",            "trees": ["roure", "alzina"],     "rain_days": [10, 20], "temp_range": [10, 18], "min_rain": 20},
    {"id": "trompetes",   "name": "Trompetes de la mort", "trees": ["roure"],               "rain_days": [10, 20], "temp_range": [9, 17],  "min_rain": 25},
    {"id": "oureig",      "name": "Ou de reig",           "trees": ["alzina", "roure"],     "rain_days": [6, 14],  "temp_range": [14, 24], "min_rain": 18},
    {"id": "rossinyols",  "name": "Rossinyols",           "trees": ["roure", "pi_altres"],  "rain_days": [7, 16],  "temp_range": [10, 19], "min_rain": 20},
    {"id": "colmenilles", "name": "Colmenilles",          "trees": ["roure", "pi_altres"],  "rain_days": [8, 18],  "temp_range": [6, 15],  "min_rain": 15},
    {"id": "llengua",     "name": "Llengua de bou",       "trees": ["roure"],               "rain_days": [10, 20], "temp_range": [12, 20], "min_rain": 20},
    {"id": "pinetell",    "name": "Pinetell",             "trees": ["pi_altres"],           "rain_days": [7, 14],  "temp_range": [8, 17],  "min_rain": 20},
    {"id": "fredolic",    "name": "Fredolic",             "trees": ["pi_altres", "alzina"], "rain_days": [9, 18],  "temp_range": [7, 16],  "min_rain": 18},
]

TREE_LABELS = {
    "pi_altres": "bosc de coníferes", "roure": "bosc de caducifolis (roure, faig...)",
    "alzina": "bosc de perennifolis (alzina...)", "mixt": "bosc mixt",
    "matollar": "matollar", "prat": "prat/pastura", "desconegut": "tipus de bosc desconegut",
}

# Mapa de tipus de bosc no forestal / desconegut que no assignem a cap espècie
NON_FOREST = {"conreu", "urba", "desconegut", "aigua", "roca", "matollar", "prat"}

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
AEMET_STATIONS_URL = "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"
ICGC_WMS_URL = "https://geoserveis.icgc.cat/servei/catalunya/cobertes-sol/wms"


# ---------------------------------------------------------------------------
# UTILITATS GEOGRÀFIQUES
# ---------------------------------------------------------------------------

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

def fetch_weather_batch(zones, timeout=30):
    """Consulta Open-Meteo per a un grup de zones en una sola petició."""
    lats = ",".join(str(z["lat"]) for z in zones)
    lons = ",".join(str(z["lon"]) for z in zones)
    params = (
        f"?latitude={lats}&longitude={lons}"
        f"&daily=precipitation_sum,temperature_2m_max,temperature_2m_min"
        f"&past_days=16&forecast_days=1&timezone=Europe%2FMadrid"
    )
    url = OPEN_METEO_URL + params
    req = urllib.request.Request(url, headers={"User-Agent": "bolets-catalunya-app/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data if isinstance(data, list) else [data]


def fetch_weather(zones, batch_size=100):
    """Open-Meteo accepta moltes coordenades per petició, però separem en lots
    per seguretat i per no fer una URL massa llarga."""
    all_results = []
    for i in range(0, len(zones), batch_size):
        batch = zones[i:i + batch_size]
        all_results.extend(fetch_weather_batch(batch))
    return all_results


def compute_rain_stats(daily):
    """A partir del bloc 'daily' d'Open-Meteo, calcula pluja 10d, temp mitjana i dies des de pluja forta."""
    precip = daily.get("precipitation_sum") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []

    last10_precip = precip[-11:-1] if len(precip) >= 11 else precip[:-1]
    rain_10d = round(sum(p or 0 for p in last10_precip))

    last10_tmax = tmax[-11:-1] if len(tmax) >= 11 else tmax[:-1]
    last10_tmin = tmin[-11:-1] if len(tmin) >= 11 else tmin[:-1]
    n = max(len(last10_tmax), 1)
    avg_temp = round(
        (sum(t or 0 for t in last10_tmax) / n + sum(t or 0 for t in last10_tmin) / n) / 2
    )

    days_since_rain = 20
    for i in range(len(precip) - 2, -1, -1):
        if (precip[i] or 0) >= 5:
            days_since_rain = len(precip) - 1 - i
            break

    return rain_10d, avg_temp, days_since_rain


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

    checks = [
        (["aciculifoli"], "pi_altres"),
        (["caducifoli", "planifoli"], "roure"),
        (["esclerofil", "laurifoli"], "alzina"),
        (["pi roig", "sylvestris"], "pi_roig"),
        (["pi negre", "uncinata"], "pi_negre"),
        (["avet", "abies"], "avet"),
        (["pi blanc", "halepensis"], "pi_blanc"),
        (["pi pinyer", "pinea"], "pi_pinyer"),
        (["alzina", " ilex"], "alzina"),
        (["roure", "quercus"], "roure"),
        (["fag", "fagus"], "faig"),
        (["sur", "suber"], "suro"),
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


def fetch_tree_type(lat, lon, timeout=5, debug=False):
    """Consulta el WMS de l'ICGC (GetFeatureInfo) per saber el tipus de bosc en un punt."""
    d = 0.01
    params = (
        f"?REQUEST=GetFeatureInfo&SERVICE=WMS&VERSION=1.1.1&LAYERS=cobertes_2009"
        f"&STYLES=&FORMAT=image/png&SRS=EPSG:4326"
        f"&BBOX={lon-d},{lat-d},{lon+d},{lat+d}&WIDTH=101&HEIGHT=101"
        f"&QUERY_LAYERS=cobertes_2009&X=50&Y=50&INFO_FORMAT=text/plain"
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


def fetch_all_tree_types(zones, delay=0.05, max_total_seconds=240):
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
        results[z["id"]] = fetch_tree_type(z["lat"], z["lon"], debug=False)
        if delay:
            time.sleep(delay)
        if (i + 1) % 25 == 0:
            print(f"  ICGC: {i + 1}/{len(zones)} punts consultats...")
    return results


# ---------------------------------------------------------------------------
# 6. SCORING
# ---------------------------------------------------------------------------

def score_species(sp, rain_10d, avg_temp, tree, days_since_rain):
    if tree not in sp["trees"]:
        return 0
    score = 35
    if rain_10d >= sp["min_rain"]:
        score += 25
    else:
        score += max(0, 25 * (rain_10d / sp["min_rain"]))

    lo, hi = sp["rain_days"]
    if lo <= days_since_rain <= hi:
        score += 25
    else:
        mid = (lo + hi) / 2
        score += max(0, 15 - abs(days_since_rain - mid))

    tlo, thi = sp["temp_range"]
    if tlo <= avg_temp <= thi:
        score += 15
    else:
        tmid = (tlo + thi) / 2
        score += max(0, 8 - abs(avg_temp - tmid))

    return max(0, min(100, round(score)))


# ---------------------------------------------------------------------------
# 7. PROCÉS PRINCIPAL
# ---------------------------------------------------------------------------

def build_results():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Graella de {len(ZONES)} punts")

    print("Consultant Open-Meteo (meteorologia)...")
    weather_results = fetch_weather(ZONES)

    print("Consultant ICGC (tipus de bosc real per a cada punt)...")
    tree_results = fetch_all_tree_types(ZONES)
    tree_types = {zid: t for zid, (t, _label) in tree_results.items()}
    known_trees = sum(1 for t in tree_types.values() if t not in NON_FOREST)
    print(f"ICGC: {known_trees}/{len(ZONES)} punts amb tipus de bosc identificat")

    aemet_key = os.environ.get("AEMET_API_KEY")
    aemet_stations = []
    if aemet_key:
        try:
            print("Consultant AEMET (estacions reals) per contrastar...")
            aemet_stations = fetch_aemet_observations(aemet_key)
            print(f"AEMET: {len(aemet_stations)} estacions amb dades rebudes")
        except Exception as e:
            print(f"AVÍS: no s'ha pogut consultar AEMET ({e}) — es continua sense contrast")
    else:
        print("AVÍS: no hi ha AEMET_API_KEY configurada — es continua sense contrast")

    zones_out = []
    for zone, daily_wrapper in zip(ZONES, weather_results):
        daily = daily_wrapper.get("daily", {})
        rain_10d, avg_temp, days_since_rain = compute_rain_stats(daily)
        tree = tree_types.get(zone["id"], "desconegut")

        aemet_info = None
        if aemet_stations:
            nearest = nearest_aemet_station(zone["lat"], zone["lon"], aemet_stations)
            if nearest:
                aemet_info = {
                    "station_name": nearest["name"],
                    "distance_km": nearest["distance_km"],
                    "prec_1h_mm": nearest["prec_1h"],
                    "observed_at": nearest["fint"],
                }

        species_scores = []
        if tree not in NON_FOREST:
            for sp in SPECIES:
                s = score_species(sp, rain_10d, avg_temp, tree, days_since_rain)
                if s > 0:
                    species_scores.append({"id": sp["id"], "name": sp["name"], "score": s})
            species_scores.sort(key=lambda x: x["score"], reverse=True)

        zones_out.append({
            "id": zone["id"],
            "name": f"Punt {zone['id']}",
            "lat": zone["lat"],
            "lon": zone["lon"],
            "alt": zone["alt"],
            "tree": tree,
            "tree_label": TREE_LABELS.get(tree, tree),
            "is_forest": tree not in NON_FOREST,
            "rain_10d": rain_10d,
            "avg_temp": avg_temp,
            "days_since_rain": days_since_rain,
            "species_scores": species_scores,
            "best_score": species_scores[0]["score"] if species_scores else 0,
            "best_species": species_scores[0]["name"] if species_scores else None,
            "aemet_check": aemet_info,
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "zones": zones_out,
        "species_catalog": [{"id": sp["id"], "name": sp["name"]} for sp in SPECIES],
    }


def main():
    try:
        results = build_results()
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"ERROR consultant dades meteorològiques: {e}")
        return

    out_path = "../data/resultats.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    forest_count = sum(1 for z in results["zones"] if z["is_forest"])
    print(f"Fet. {len(results['zones'])} zones desades a {out_path} ({forest_count} boscoses)")
    print(f"Generat: {results['generated_at']}")


if __name__ == "__main__":
    main()
