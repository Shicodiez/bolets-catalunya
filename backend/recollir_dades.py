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
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

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
AEMET_API_KEY = None  # Es defineix a través de la variable d'entorn AEMET_API_KEY
AEMET_STATIONS_URL = "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"


def haversine_km(lat1, lon1, lat2, lon2):
    """Distància aproximada en km entre dos punts (per trobar l'estació AEMET més propera)."""
    import math
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(min(1, a ** 0.5))


def fetch_aemet_observations(api_key, timeout=20):
    """
    Consulta AEMET OpenData (observació convencional, totes les estacions).
    Retorna una llista de diccionaris amb lat, lon, precipitació (mm/60min) i data.
    AEMET requereix dues peticions: la primera dona una URL temporal amb les dades reals.
    """
    if not api
