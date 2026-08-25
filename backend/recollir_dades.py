"""
Predictor de bolets a Catalunya — recollida de dades i càlcul de puntuació.

Aquest script:
1. Consulta dades meteorològiques en viu (Open-Meteo, i opcionalment AEMET/Meteocat)
   per a una graella de punts de Catalunya.
2. Assigna el tipus de bosc dominant a cada punt (mapa forestal simplificat;
   preparat per connectar-se al WMS de l'ICGC en el futur).
3. Calcula una puntuació de 0-100 per a cada espècie de bolet en cada punt,
   segons pluja acumulada, dies des de l'última pluja forta, temperatura i
   compatibilitat d'hàbitat.
4. Desa el resultat en un fitxer JSON (data/resultats.json) que la web llegeix.

Pensat per executar-se automàticament cada poques hores (veure README.md).
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# 1. GRAELLA DE PUNTS DE CATALUNYA
# ---------------------------------------------------------------------------
# Cada punt: nom, latitud, longitud, altitud (m), tipus de bosc dominant.
# El tipus de bosc és una assignació geogràfica coneguda (Institut Cartogràfic,
# CREAF, bibliografia micològica). Es pot substituir en el futur per una
# consulta real al WMS de l'ICGC (Mapa de cobertes del sòl).

ZONES = [
    {"name": "Val d'Aran",        "lat": 42.70, "lon": 0.85, "alt": 1200, "tree": "pi_negre"},
    {"name": "Pallars Sobirà N",  "lat": 42.58, "lon": 1.10, "alt": 1400, "tree": "pi_negre"},
    {"name": "Pallars Sobirà S",  "lat": 42.45, "lon": 1.05, "alt": 1300, "tree": "avet"},
    {"name": "Alta Ribagorça",    "lat": 42.48, "lon": 0.75, "alt": 1500, "tree": "pi_negre"},
    {"name": "Pallars Jussà",     "lat": 42.35, "lon": 0.90, "alt": 1000, "tree": "pi_roig"},
    {"name": "Alt Urgell N",      "lat": 42.35, "lon": 1.35, "alt": 900,  "tree": "pi_roig"},
    {"name": "Alt Urgell S",      "lat": 42.20, "lon": 1.45, "alt": 800,  "tree": "pi_roig"},
    {"name": "Cerdanya",          "lat": 42.40, "lon": 1.90, "alt": 1150, "tree": "pi_negre"},
    {"name": "Solsonès",          "lat": 41.99, "lon": 1.52, "alt": 850,  "tree": "pi_roig"},
    {"name": "Berguedà N",        "lat": 42.15, "lon": 1.85, "alt": 750,  "tree": "pi_roig"},
    {"name": "Berguedà S",        "lat": 42.05, "lon": 1.70, "alt": 650,  "tree": "roure"},
    {"name": "Ripollès",          "lat": 42.28, "lon": 2.20, "alt": 900,  "tree": "faig"},
    {"name": "Garrotxa",          "lat": 42.18, "lon": 2.49, "alt": 450,  "tree": "faig"},
    {"name": "Alt Empordà",       "lat": 42.27, "lon": 2.90, "alt": 180,  "tree": "alzina"},
    {"name": "Osona N",           "lat": 41.98, "lon": 2.30, "alt": 600,  "tree": "roure"},
    {"name": "Osona S",           "lat": 41.85, "lon": 2.20, "alt": 500,  "tree": "roure"},
    {"name": "Bages",             "lat": 41.79, "lon": 1.83, "alt": 450,  "tree": "pi_blanc"},
    {"name": "Vallès Oriental",   "lat": 41.68, "lon": 2.30, "alt": 350,  "tree": "alzina"},
    {"name": "Montseny",          "lat": 41.77, "lon": 2.43, "alt": 850,  "tree": "faig"},
    {"name": "Selva",             "lat": 41.85, "lon": 2.55, "alt": 300,  "tree": "alzina"},
    {"name": "Anoia",             "lat": 41.60, "lon": 1.55, "alt": 400,  "tree": "pi_blanc"},
    {"name": "Priorat",           "lat": 41.23, "lon": 0.82, "alt": 500,  "tree": "alzina"},
    {"name": "Conca de Barberà",  "lat": 41.42, "lon": 1.15, "alt": 600,  "tree": "pi_blanc"},
    {"name": "Baix Camp",         "lat": 41.15, "lon": 0.95, "alt": 450,  "tree": "alzina"},
    {"name": "Terra Alta",        "lat": 41.05, "lon": 0.45, "alt": 400,  "tree": "pi_pinyer"},
]

# ---------------------------------------------------------------------------
# 2. ESPÈCIES DE BOLETS I LA SEVA LÒGICA
# ---------------------------------------------------------------------------
SPECIES = [
    {"id": "rovellons",   "name": "Rovellons",           "trees": ["pi_roig", "pi_negre", "pi_pinyer", "pi_blanc"], "rain_days": [7, 15],  "temp_range": [8, 18],  "min_rain": 20},
    {"id": "ceps",        "name": "Ceps",                 "trees": ["roure", "faig", "pi_roig", "pi_negre"],        "rain_days": [8, 16],  "temp_range": [10, 20], "min_rain": 25},
    {"id": "camagrocs",   "name": "Camagrocs",            "trees": ["faig", "roure", "alzina"],                     "rain_days": [10, 20], "temp_range": [10, 18], "min_rain": 20},
    {"id": "trompetes",   "name": "Trompetes de la mort", "trees": ["faig", "roure"],                               "rain_days": [10, 20], "temp_range": [9, 17],  "min_rain": 25},
    {"id": "oureig",      "name": "Ou de reig",           "trees": ["alzina", "roure", "suro"],                     "rain_days": [6, 14],  "temp_range": [14, 24], "min_rain": 18},
    {"id": "rossinyols",  "name": "Rossinyols",           "trees": ["faig", "roure", "pi_roig"],                    "rain_days": [7, 16],  "temp_range": [10, 19], "min_rain": 20},
    {"id": "colmenilles", "name": "Colmenilles",          "trees": ["roure", "pi_blanc"],                           "rain_days": [8, 18],  "temp_range": [6, 15],  "min_rain": 15},
    {"id": "llengua",     "name": "Llengua de bou",       "trees": ["roure", "suro"],                               "rain_days": [10, 20], "temp_range": [12, 20], "min_rain": 20},
    {"id": "pinetell",    "name": "Pinetell",             "trees": ["pi_roig", "pi_negre"],                         "rain_days": [7, 14],  "temp_range": [8, 17],  "min_rain": 20},
    {"id": "fredolic",    "name": "Fredolic",             "trees": ["pi_blanc", "alzina"],                          "rain_days": [9, 18],  "temp_range": [7, 16],  "min_rain": 18},
]

TREE_LABELS = {
    "pi_roig": "pineda de pi roig", "pi_negre": "pineda de pi negre", "avet": "avetosa",
    "pi_blanc": "pineda de pi blanc", "pi_pinyer": "pineda de pi pinyer", "alzina": "alzinar",
    "roure": "roureda", "faig": "fageda", "suro": "surededa",
}

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather(zones, timeout=20):
    """Consulta Open-Meteo per a totes les zones en una sola petició."""
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


def build_results():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Consultant Open-Meteo per {len(ZONES)} punts...")
    weather_results = fetch_weather(ZONES)

    zones_out = []
    for zone, daily_wrapper in zip(ZONES, weather_results):
        daily = daily_wrapper.get("daily", {})
        rain_10d, avg_temp, days_since_rain = compute_rain_stats(daily)

        species_scores = []
        for sp in SPECIES:
            s = score_species(sp, rain_10d, avg_temp, zone["tree"], days_since_rain)
            if s > 0:
                species_scores.append({"id": sp["id"], "name": sp["name"], "score": s})
        species_scores.sort(key=lambda x: x["score"], reverse=True)

        zones_out.append({
            "name": zone["name"],
            "lat": zone["lat"],
            "lon": zone["lon"],
            "alt": zone["alt"],
            "tree": zone["tree"],
            "tree_label": TREE_LABELS.get(zone["tree"], zone["tree"]),
            "rain_10d": rain_10d,
            "avg_temp": avg_temp,
            "days_since_rain": days_since_rain,
            "species_scores": species_scores,
            "best_score": species_scores[0]["score"] if species_scores else 0,
            "best_species": species_scores[0]["name"] if species_scores else None,
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
        print(f"ERROR consultant Open-Meteo: {e}")
        return

    out_path = "../data/resultats.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Fet. {len(results['zones'])} zones desades a {out_path}")
    print(f"Generat: {results['generated_at']}")


if __name__ == "__main__":
    main()
