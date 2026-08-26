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
import urllib.parse
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# 1. GRAELLA DE PUNTS DE CATALUNYA (~150 punts, generada automàticament)
# ---------------------------------------------------------------------------
# Cada punt: id, latitud, longitud, altitud aproximada (m).
# L'altitud és una estimació geogràfica (nord=més alt, costa=més baix);
# el tipus de bosc es consulta en viu al WMS de l'ICGC per a cada punt.

ZONES = [
    {"id": 1, "lat": 40.61, "lon": 0.832, "alt": 250},
    {"id": 2, "lat": 40.7, "lon": 0.588, "alt": 250},
    {"id": 3, "lat": 40.7, "lon": 0.71, "alt": 250},
    {"id": 4, "lat": 40.7, "lon": 0.832, "alt": 250},
    {"id": 5, "lat": 40.7, "lon": 0.954, "alt": 250},
    {"id": 6, "lat": 40.79, "lon": 0.466, "alt": 250},
    {"id": 7, "lat": 40.79, "lon": 0.588, "alt": 250},
    {"id": 8, "lat": 40.79, "lon": 0.71, "alt": 250},
    {"id": 9, "lat": 40.79, "lon": 0.832, "alt": 250},
    {"id": 10, "lat": 40.79, "lon": 0.954, "alt": 250},
    {"id": 11, "lat": 40.79, "lon": 1.076, "alt": 250},
    {"id": 12, "lat": 40.88, "lon": 0.344, "alt": 250},
    {"id": 13, "lat": 40.88, "lon": 0.466, "alt": 250},
    {"id": 14, "lat": 40.88, "lon": 0.588, "alt": 250},
    {"id": 15, "lat": 40.88, "lon": 0.71, "alt": 250},
    {"id": 16, "lat": 40.88, "lon": 0.832, "alt": 250},
    {"id": 17, "lat": 40.88, "lon": 0.954, "alt": 250},
    {"id": 18, "lat": 40.88, "lon": 1.076, "alt": 250},
    {"id": 19, "lat": 40.88, "lon": 1.198, "alt": 250},
    {"id": 20, "lat": 40.88, "lon": 1.32, "alt": 250},
    {"id": 21, "lat": 40.97, "lon": 0.222, "alt": 250},
    {"id": 22, "lat": 40.97, "lon": 0.344, "alt": 250},
    {"id": 23, "lat": 40.97, "lon": 0.466, "alt": 250},
    {"id": 24, "lat": 40.97, "lon": 0.588, "alt": 250},
    {"id": 25, "lat": 40.97, "lon": 0.71, "alt": 250},
    {"id": 26, "lat": 40.97, "lon": 0.832, "alt": 250},
    {"id": 27, "lat": 40.97, "lon": 0.954, "alt": 250},
    {"id": 28, "lat": 40.97, "lon": 1.076, "alt": 250},
    {"id": 29, "lat": 40.97, "lon": 1.198, "alt": 250},
    {"id": 30, "lat": 40.97, "lon": 1.32, "alt": 250},
    {"id": 31, "lat": 40.97, "lon": 1.441, "alt": 250},
    {"id": 32, "lat": 41.061, "lon": 0.222, "alt": 250},
    {"id": 33, "lat": 41.061, "lon": 0.344, "alt": 250},
    {"id": 34, "lat": 41.061, "lon": 0.466, "alt": 250},
    {"id": 35, "lat": 41.061, "lon": 0.588, "alt": 250},
    {"id": 36, "lat": 41.061, "lon": 0.71, "alt": 250},
    {"id": 37, "lat": 41.061, "lon": 0.832, "alt": 250},
    {"id": 38, "lat": 41.061, "lon": 0.954, "alt": 250},
    {"id": 39, "lat": 41.061, "lon": 1.076, "alt": 250},
    {"id": 40, "lat": 41.061, "lon": 1.198, "alt": 250},
    {"id": 41, "lat": 41.061, "lon": 1.32, "alt": 250},
    {"id": 42, "lat": 41.061, "lon": 1.441, "alt": 250},
    {"id": 43, "lat": 41.061, "lon": 1.563, "alt": 250},
    {"id": 44, "lat": 41.151, "lon": 0.222, "alt": 250},
    {"id": 45, "lat": 41.151, "lon": 0.344, "alt": 250},
    {"id": 46, "lat": 41.151, "lon": 0.466, "alt": 250},
    {"id": 47, "lat": 41.151, "lon": 0.588, "alt": 250},
    {"id": 48, "lat": 41.151, "lon": 0.71, "alt": 250},
    {"id": 49, "lat": 41.151, "lon": 0.832, "alt": 250},
    {"id": 50, "lat": 41.151, "lon": 0.954, "alt": 250},
    {"id": 51, "lat": 41.151, "lon": 1.076, "alt": 250},
    {"id": 52, "lat": 41.151, "lon": 1.198, "alt": 250},
    {"id": 53, "lat": 41.151, "lon": 1.32, "alt": 250},
    {"id": 54, "lat": 41.151, "lon": 1.441, "alt": 250},
    {"id": 55, "lat": 41.151, "lon": 1.563, "alt": 250},
    {"id": 56, "lat": 41.151, "lon": 1.685, "alt": 250},
    {"id": 57, "lat": 41.151, "lon": 1.807, "alt": 30},
    {"id": 58, "lat": 41.151, "lon": 1.929, "alt": 30},
    {"id": 59, "lat": 41.241, "lon": 0.222, "alt": 250},
    {"id": 60, "lat": 41.241, "lon": 0.344, "alt": 250},
    {"id": 61, "lat": 41.241, "lon": 0.466, "alt": 250},
    {"id": 62, "lat": 41.241, "lon": 0.588, "alt": 250},
    {"id": 63, "lat": 41.241, "lon": 0.71, "alt": 250},
    {"id": 64, "lat": 41.241, "lon": 0.832, "alt": 250},
    {"id": 65, "lat": 41.241, "lon": 0.954, "alt": 250},
    {"id": 66, "lat": 41.241, "lon": 1.076, "alt": 250},
    {"id": 67, "lat": 41.241, "lon": 1.198, "alt": 250},
    {"id": 68, "lat": 41.241, "lon": 1.32, "alt": 250},
    {"id": 69, "lat": 41.241, "lon": 1.441, "alt": 250},
    {"id": 70, "lat": 41.241, "lon": 1.563, "alt": 250},
    {"id": 71, "lat": 41.241, "lon": 1.685, "alt": 250},
    {"id": 72, "lat": 41.241, "lon": 1.807, "alt": 30},
    {"id": 73, "lat": 41.241, "lon": 1.929, "alt": 30},
    {"id": 74, "lat": 41.241, "lon": 2.051, "alt": 30},
    {"id": 75, "lat": 41.241, "lon": 2.173, "alt": 30},
    {"id": 76, "lat": 41.331, "lon": 0.222, "alt": 280},
    {"id": 77, "lat": 41.331, "lon": 0.344, "alt": 280},
    {"id": 78, "lat": 41.331, "lon": 0.466, "alt": 280},
    {"id": 79, "lat": 41.331, "lon": 0.588, "alt": 280},
    {"id": 80, "lat": 41.331, "lon": 0.71, "alt": 280},
    {"id": 81, "lat": 41.331, "lon": 0.832, "alt": 280},
    {"id": 82, "lat": 41.331, "lon": 0.954, "alt": 280},
    {"id": 83, "lat": 41.331, "lon": 1.076, "alt": 280},
    {"id": 84, "lat": 41.331, "lon": 1.198, "alt": 280},
    {"id": 85, "lat": 41.331, "lon": 1.32, "alt": 280},
    {"id": 86, "lat": 41.331, "lon": 1.441, "alt": 280},
    {"id": 87, "lat": 41.331, "lon": 1.563, "alt": 280},
    {"id": 88, "lat": 41.331, "lon": 1.685, "alt": 280},
    {"id": 89, "lat": 41.331, "lon": 1.807, "alt": 30},
    {"id": 90, "lat": 41.331, "lon": 1.929, "alt": 30},
    {"id": 91, "lat": 41.331, "lon": 2.051, "alt": 30},
    {"id": 92, "lat": 41.331, "lon": 2.173, "alt": 30},
    {"id": 93, "lat": 41.331, "lon": 2.295, "alt": 30},
    {"id": 94, "lat": 41.331, "lon": 2.417, "alt": 30},
    {"id": 95, "lat": 41.331, "lon": 2.539, "alt": 30},
    {"id": 96, "lat": 41.421, "lon": 0.222, "alt": 360},
    {"id": 97, "lat": 41.421, "lon": 0.344, "alt": 360},
    {"id": 98, "lat": 41.421, "lon": 0.466, "alt": 360},
    {"id": 99, "lat": 41.421, "lon": 0.588, "alt": 360},
    {"id": 100, "lat": 41.421, "lon": 0.71, "alt": 360},
    {"id": 101, "lat": 41.421, "lon": 0.832, "alt": 360},
    {"id": 102, "lat": 41.421, "lon": 0.954, "alt": 360},
    {"id": 103, "lat": 41.421, "lon": 1.076, "alt": 360},
    {"id": 104, "lat": 41.421, "lon": 1.198, "alt": 360},
    {"id": 105, "lat": 41.421, "lon": 1.32, "alt": 360},
    {"id": 106, "lat": 41.421, "lon": 1.441, "alt": 360},
    {"id": 107, "lat": 41.421, "lon": 1.563, "alt": 360},
    {"id": 108, "lat": 41.421, "lon": 1.685, "alt": 360},
    {"id": 109, "lat": 41.421, "lon": 1.807, "alt": 110},
    {"id": 110, "lat": 41.421, "lon": 1.929, "alt": 110},
    {"id": 111, "lat": 41.421, "lon": 2.051, "alt": 110},
    {"id": 112, "lat": 41.421, "lon": 2.173, "alt": 110},
    {"id": 113, "lat": 41.421, "lon": 2.295, "alt": 110},
    {"id": 114, "lat": 41.421, "lon": 2.417, "alt": 30},
    {"id": 115, "lat": 41.421, "lon": 2.539, "alt": 30},
    {"id": 116, "lat": 41.421, "lon": 2.661, "alt": 30},
    {"id": 117, "lat": 41.511, "lon": 0.344, "alt": 440},
    {"id": 118, "lat": 41.511, "lon": 0.466, "alt": 440},
    {"id": 119, "lat": 41.511, "lon": 0.588, "alt": 440},
    {"id": 120, "lat": 41.511, "lon": 0.71, "alt": 440},
    {"id": 121, "lat": 41.511, "lon": 0.832, "alt": 440},
    {"id": 122, "lat": 41.511, "lon": 0.954, "alt": 440},
    {"id": 123, "lat": 41.511, "lon": 1.076, "alt": 440},
    {"id": 124, "lat": 41.511, "lon": 1.198, "alt": 440},
    {"id": 125, "lat": 41.511, "lon": 1.32, "alt": 440},
    {"id": 126, "lat": 41.511, "lon": 1.441, "alt": 440},
    {"id": 127, "lat": 41.511, "lon": 1.563, "alt": 440},
    {"id": 128, "lat": 41.511, "lon": 1.685, "alt": 440},
    {"id": 129, "lat": 41.511, "lon": 1.807, "alt": 190},
    {"id": 130, "lat": 41.511, "lon": 1.929, "alt": 190},
    {"id": 131, "lat": 41.511, "lon": 2.051, "alt": 190},
    {"id": 132, "lat": 41.511, "lon": 2.173, "alt": 190},
    {"id": 133, "lat": 41.511, "lon": 2.295, "alt": 190},
    {"id": 134, "lat": 41.511, "lon": 2.417, "alt": 40},
    {"id": 135, "lat": 41.511, "lon": 2.539, "alt": 40},
    {"id": 136, "lat": 41.511, "lon": 2.661, "alt": 40},
    {"id": 137, "lat": 41.601, "lon": 0.344, "alt": 520},
    {"id": 138, "lat": 41.601, "lon": 0.466, "alt": 520},
    {"id": 139, "lat": 41.601, "lon": 0.588, "alt": 520},
    {"id": 140, "lat": 41.601, "lon": 0.71, "alt": 520},
    {"id": 141, "lat": 41.601, "lon": 0.832, "alt": 520},
    {"id": 142, "lat": 41.601, "lon": 0.954, "alt": 520},
    {"id": 143, "lat": 41.601, "lon": 1.076, "alt": 520},
    {"id": 144, "lat": 41.601, "lon": 1.198, "alt": 520},
    {"id": 145, "lat": 41.601, "lon": 1.32, "alt": 520},
    {"id": 146, "lat": 41.601, "lon": 1.441, "alt": 520},
    {"id": 147, "lat": 41.601, "lon": 1.563, "alt": 520},
    {"id": 148, "lat": 41.601, "lon": 1.685, "alt": 520},
    {"id": 149, "lat": 41.601, "lon": 1.807, "alt": 270},
    {"id": 150, "lat": 41.601, "lon": 1.929, "alt": 270},
    {"id": 151, "lat": 41.601, "lon": 2.051, "alt": 270},
    {"id": 152, "lat": 41.601, "lon": 2.173, "alt": 270},
    {"id": 153, "lat": 41.601, "lon": 2.295, "alt": 270},
    {"id": 154, "lat": 41.601, "lon": 2.417, "alt": 120},
    {"id": 155, "lat": 41.601, "lon": 2.539, "alt": 120},
    {"id": 156, "lat": 41.601, "lon": 2.661, "alt": 120},
    {"id": 157, "lat": 41.601, "lon": 2.783, "alt": 120},
    {"id": 158, "lat": 41.691, "lon": 0.344, "alt": 600},
    {"id": 159, "lat": 41.691, "lon": 0.466, "alt": 600},
    {"id": 160, "lat": 41.691, "lon": 0.588, "alt": 600},
    {"id": 161, "lat": 41.691, "lon": 0.71, "alt": 600},
    {"id": 162, "lat": 41.691, "lon": 0.832, "alt": 600},
    {"id": 163, "lat": 41.691, "lon": 0.954, "alt": 600},
    {"id": 164, "lat": 41.691, "lon": 1.076, "alt": 600},
    {"id": 165, "lat": 41.691, "lon": 1.198, "alt": 600},
    {"id": 166, "lat": 41.691, "lon": 1.32, "alt": 600},
    {"id": 167, "lat": 41.691, "lon": 1.441, "alt": 600},
    {"id": 168, "lat": 41.691, "lon": 1.563, "alt": 600},
    {"id": 169, "lat": 41.691, "lon": 1.685, "alt": 600},
    {"id": 170, "lat": 41.691, "lon": 1.807, "alt": 350},
    {"id": 171, "lat": 41.691, "lon": 1.929, "alt": 350},
    {"id": 172, "lat": 41.691, "lon": 2.051, "alt": 350},
    {"id": 173, "lat": 41.691, "lon": 2.173, "alt": 350},
    {"id": 174, "lat": 41.691, "lon": 2.295, "alt": 350},
    {"id": 175, "lat": 41.691, "lon": 2.417, "alt": 200},
    {"id": 176, "lat": 41.691, "lon": 2.539, "alt": 200},
    {"id": 177, "lat": 41.691, "lon": 2.661, "alt": 200},
    {"id": 178, "lat": 41.691, "lon": 2.783, "alt": 200},
    {"id": 179, "lat": 41.691, "lon": 2.905, "alt": 200},
    {"id": 180, "lat": 41.781, "lon": 0.344, "alt": 680},
    {"id": 181, "lat": 41.781, "lon": 0.466, "alt": 680},
    {"id": 182, "lat": 41.781, "lon": 0.588, "alt": 680},
    {"id": 183, "lat": 41.781, "lon": 0.71, "alt": 680},
    {"id": 184, "lat": 41.781, "lon": 0.832, "alt": 680},
    {"id": 185, "lat": 41.781, "lon": 0.954, "alt": 680},
    {"id": 186, "lat": 41.781, "lon": 1.076, "alt": 680},
    {"id": 187, "lat": 41.781, "lon": 1.198, "alt": 680},
    {"id": 188, "lat": 41.781, "lon": 1.32, "alt": 680},
    {"id": 189, "lat": 41.781, "lon": 1.441, "alt": 680},
    {"id": 190, "lat": 41.781, "lon": 1.563, "alt": 680},
    {"id": 191, "lat": 41.781, "lon": 1.685, "alt": 680},
    {"id": 192, "lat": 41.781, "lon": 1.807, "alt": 430},
    {"id": 193, "lat": 41.781, "lon": 1.929, "alt": 430},
    {"id": 194, "lat": 41.781, "lon": 2.051, "alt": 430},
    {"id": 195, "lat": 41.781, "lon": 2.173, "alt": 430},
    {"id": 196, "lat": 41.781, "lon": 2.295, "alt": 430},
    {"id": 197, "lat": 41.781, "lon": 2.417, "alt": 280},
    {"id": 198, "lat": 41.781, "lon": 2.539, "alt": 280},
    {"id": 199, "lat": 41.781, "lon": 2.661, "alt": 280},
    {"id": 200, "lat": 41.781, "lon": 2.783, "alt": 280},
    {"id": 201, "lat": 41.781, "lon": 2.905, "alt": 280},
    {"id": 202, "lat": 41.871, "lon": 0.222, "alt": 760},
    {"id": 203, "lat": 41.871, "lon": 0.344, "alt": 760},
    {"id": 204, "lat": 41.871, "lon": 0.466, "alt": 760},
    {"id": 205, "lat": 41.871, "lon": 0.588, "alt": 760},
    {"id": 206, "lat": 41.871, "lon": 0.71, "alt": 760},
    {"id": 207, "lat": 41.871, "lon": 0.832, "alt": 760},
    {"id": 208, "lat": 41.871, "lon": 0.954, "alt": 760},
    {"id": 209, "lat": 41.871, "lon": 1.076, "alt": 760},
    {"id": 210, "lat": 41.871, "lon": 1.198, "alt": 760},
    {"id": 211, "lat": 41.871, "lon": 1.32, "alt": 760},
    {"id": 212, "lat": 41.871, "lon": 1.441, "alt": 760},
    {"id": 213, "lat": 41.871, "lon": 1.563, "alt": 760},
    {"id": 214, "lat": 41.871, "lon": 1.685, "alt": 760},
    {"id": 215, "lat": 41.871, "lon": 1.807, "alt": 510},
    {"id": 216, "lat": 41.871, "lon": 1.929, "alt": 510},
    {"id": 217, "lat": 41.871, "lon": 2.051, "alt": 510},
    {"id": 218, "lat": 41.871, "lon": 2.173, "alt": 510},
    {"id": 219, "lat": 41.871, "lon": 2.295, "alt": 510},
    {"id": 220, "lat": 41.871, "lon": 2.417, "alt": 360},
    {"id": 221, "lat": 41.871, "lon": 2.539, "alt": 360},
    {"id": 222, "lat": 41.871, "lon": 2.661, "alt": 360},
    {"id": 223, "lat": 41.871, "lon": 2.783, "alt": 360},
    {"id": 224, "lat": 41.871, "lon": 2.905, "alt": 360},
    {"id": 225, "lat": 41.871, "lon": 3.027, "alt": 360},
    {"id": 226, "lat": 41.961, "lon": 0.344, "alt": 840},
    {"id": 227, "lat": 41.961, "lon": 0.466, "alt": 840},
    {"id": 228, "lat": 41.961, "lon": 0.588, "alt": 840},
    {"id": 229, "lat": 41.961, "lon": 0.71, "alt": 840},
    {"id": 230, "lat": 41.961, "lon": 0.832, "alt": 840},
    {"id": 231, "lat": 41.961, "lon": 0.954, "alt": 840},
    {"id": 232, "lat": 41.961, "lon": 1.076, "alt": 840},
    {"id": 233, "lat": 41.961, "lon": 1.198, "alt": 840},
    {"id": 234, "lat": 41.961, "lon": 1.32, "alt": 840},
    {"id": 235, "lat": 41.961, "lon": 1.441, "alt": 840},
    {"id": 236, "lat": 41.961, "lon": 1.563, "alt": 840},
    {"id": 237, "lat": 41.961, "lon": 1.685, "alt": 840},
    {"id": 238, "lat": 41.961, "lon": 1.807, "alt": 840},
    {"id": 239, "lat": 41.961, "lon": 1.929, "alt": 840},
    {"id": 240, "lat": 41.961, "lon": 2.051, "alt": 840},
    {"id": 241, "lat": 41.961, "lon": 2.173, "alt": 840},
    {"id": 242, "lat": 41.961, "lon": 2.295, "alt": 840},
    {"id": 243, "lat": 41.961, "lon": 2.417, "alt": 440},
    {"id": 244, "lat": 41.961, "lon": 2.539, "alt": 440},
    {"id": 245, "lat": 41.961, "lon": 2.661, "alt": 440},
    {"id": 246, "lat": 41.961, "lon": 2.783, "alt": 440},
    {"id": 247, "lat": 41.961, "lon": 2.905, "alt": 440},
    {"id": 248, "lat": 41.961, "lon": 3.027, "alt": 440},
    {"id": 249, "lat": 41.961, "lon": 3.149, "alt": 440},
    {"id": 250, "lat": 42.052, "lon": 0.466, "alt": 930},
    {"id": 251, "lat": 42.052, "lon": 0.588, "alt": 930},
    {"id": 252, "lat": 42.052, "lon": 0.71, "alt": 930},
    {"id": 253, "lat": 42.052, "lon": 0.832, "alt": 930},
    {"id": 254, "lat": 42.052, "lon": 0.954, "alt": 930},
    {"id": 255, "lat": 42.052, "lon": 1.076, "alt": 930},
    {"id": 256, "lat": 42.052, "lon": 1.198, "alt": 930},
    {"id": 257, "lat": 42.052, "lon": 1.32, "alt": 930},
    {"id": 258, "lat": 42.052, "lon": 1.441, "alt": 930},
    {"id": 259, "lat": 42.052, "lon": 1.563, "alt": 930},
    {"id": 260, "lat": 42.052, "lon": 1.685, "alt": 930},
    {"id": 261, "lat": 42.052, "lon": 1.807, "alt": 930},
    {"id": 262, "lat": 42.052, "lon": 1.929, "alt": 930},
    {"id": 263, "lat": 42.052, "lon": 2.051, "alt": 930},
    {"id": 264, "lat": 42.052, "lon": 2.173, "alt": 930},
    {"id": 265, "lat": 42.052, "lon": 2.295, "alt": 930},
    {"id": 266, "lat": 42.052, "lon": 2.417, "alt": 530},
    {"id": 267, "lat": 42.052, "lon": 2.539, "alt": 530},
    {"id": 268, "lat": 42.052, "lon": 2.661, "alt": 530},
    {"id": 269, "lat": 42.052, "lon": 2.783, "alt": 530},
    {"id": 270, "lat": 42.052, "lon": 2.905, "alt": 530},
    {"id": 271, "lat": 42.052, "lon": 3.027, "alt": 530},
    {"id": 272, "lat": 42.052, "lon": 3.149, "alt": 530},
    {"id": 273, "lat": 42.142, "lon": 0.466, "alt": 1010},
    {"id": 274, "lat": 42.142, "lon": 0.588, "alt": 1010},
    {"id": 275, "lat": 42.142, "lon": 0.71, "alt": 1010},
    {"id": 276, "lat": 42.142, "lon": 0.832, "alt": 1010},
    {"id": 277, "lat": 42.142, "lon": 0.954, "alt": 1010},
    {"id": 278, "lat": 42.142, "lon": 1.076, "alt": 1010},
    {"id": 279, "lat": 42.142, "lon": 1.198, "alt": 1010},
    {"id": 280, "lat": 42.142, "lon": 1.32, "alt": 1010},
    {"id": 281, "lat": 42.142, "lon": 1.441, "alt": 1010},
    {"id": 282, "lat": 42.142, "lon": 1.563, "alt": 1010},
    {"id": 283, "lat": 42.142, "lon": 1.685, "alt": 1010},
    {"id": 284, "lat": 42.142, "lon": 1.807, "alt": 1010},
    {"id": 285, "lat": 42.142, "lon": 1.929, "alt": 1010},
    {"id": 286, "lat": 42.142, "lon": 2.051, "alt": 1010},
    {"id": 287, "lat": 42.142, "lon": 2.173, "alt": 1010},
    {"id": 288, "lat": 42.142, "lon": 2.295, "alt": 1010},
    {"id": 289, "lat": 42.142, "lon": 2.417, "alt": 1010},
    {"id": 290, "lat": 42.142, "lon": 2.539, "alt": 1010},
    {"id": 291, "lat": 42.142, "lon": 2.661, "alt": 1010},
    {"id": 292, "lat": 42.142, "lon": 2.783, "alt": 1010},
    {"id": 293, "lat": 42.142, "lon": 2.905, "alt": 1010},
    {"id": 294, "lat": 42.142, "lon": 3.027, "alt": 1010},
    {"id": 295, "lat": 42.142, "lon": 3.149, "alt": 1010},
    {"id": 296, "lat": 42.232, "lon": 0.344, "alt": 1090},
    {"id": 297, "lat": 42.232, "lon": 0.466, "alt": 1090},
    {"id": 298, "lat": 42.232, "lon": 0.588, "alt": 1090},
    {"id": 299, "lat": 42.232, "lon": 0.71, "alt": 1090},
    {"id": 300, "lat": 42.232, "lon": 0.832, "alt": 1090},
    {"id": 301, "lat": 42.232, "lon": 0.954, "alt": 1090},
    {"id": 302, "lat": 42.232, "lon": 1.076, "alt": 1090},
    {"id": 303, "lat": 42.232, "lon": 1.198, "alt": 1090},
    {"id": 304, "lat": 42.232, "lon": 1.32, "alt": 1090},
    {"id": 305, "lat": 42.232, "lon": 1.441, "alt": 1090},
    {"id": 306, "lat": 42.232, "lon": 1.563, "alt": 1090},
    {"id": 307, "lat": 42.232, "lon": 1.685, "alt": 1090},
    {"id": 308, "lat": 42.232, "lon": 1.807, "alt": 1090},
    {"id": 309, "lat": 42.232, "lon": 1.929, "alt": 1090},
    {"id": 310, "lat": 42.232, "lon": 2.051, "alt": 1090},
    {"id": 311, "lat": 42.232, "lon": 2.173, "alt": 1090},
    {"id": 312, "lat": 42.232, "lon": 2.295, "alt": 1090},
    {"id": 313, "lat": 42.232, "lon": 2.417, "alt": 1090},
    {"id": 314, "lat": 42.232, "lon": 2.539, "alt": 1090},
    {"id": 315, "lat": 42.232, "lon": 2.661, "alt": 1090},
    {"id": 316, "lat": 42.232, "lon": 2.783, "alt": 1090},
    {"id": 317, "lat": 42.232, "lon": 2.905, "alt": 1090},
    {"id": 318, "lat": 42.232, "lon": 3.027, "alt": 1090},
    {"id": 319, "lat": 42.232, "lon": 3.149, "alt": 1090},
    {"id": 320, "lat": 42.322, "lon": 0.344, "alt": 1170},
    {"id": 321, "lat": 42.322, "lon": 0.466, "alt": 1170},
    {"id": 322, "lat": 42.322, "lon": 0.588, "alt": 1170},
    {"id": 323, "lat": 42.322, "lon": 0.71, "alt": 1170},
    {"id": 324, "lat": 42.322, "lon": 0.832, "alt": 1170},
    {"id": 325, "lat": 42.322, "lon": 0.954, "alt": 1170},
    {"id": 326, "lat": 42.322, "lon": 1.076, "alt": 1170},
    {"id": 327, "lat": 42.322, "lon": 1.198, "alt": 1170},
    {"id": 328, "lat": 42.322, "lon": 1.32, "alt": 1170},
    {"id": 329, "lat": 42.322, "lon": 1.441, "alt": 1170},
    {"id": 330, "lat": 42.322, "lon": 1.563, "alt": 1170},
    {"id": 331, "lat": 42.322, "lon": 1.685, "alt": 1170},
    {"id": 332, "lat": 42.322, "lon": 1.807, "alt": 1170},
    {"id": 333, "lat": 42.322, "lon": 1.929, "alt": 1170},
    {"id": 334, "lat": 42.322, "lon": 2.051, "alt": 1170},
    {"id": 335, "lat": 42.322, "lon": 2.173, "alt": 1170},
    {"id": 336, "lat": 42.322, "lon": 2.295, "alt": 1170},
    {"id": 337, "lat": 42.322, "lon": 2.417, "alt": 1170},
    {"id": 338, "lat": 42.322, "lon": 2.539, "alt": 1170},
    {"id": 339, "lat": 42.322, "lon": 2.661, "alt": 1170},
    {"id": 340, "lat": 42.322, "lon": 2.783, "alt": 1170},
    {"id": 341, "lat": 42.322, "lon": 2.905, "alt": 1170},
    {"id": 342, "lat": 42.322, "lon": 3.027, "alt": 1170},
    {"id": 343, "lat": 42.322, "lon": 3.149, "alt": 1170},
    {"id": 344, "lat": 42.412, "lon": 0.222, "alt": 1250},
    {"id": 345, "lat": 42.412, "lon": 0.344, "alt": 1250},
    {"id": 346, "lat": 42.412, "lon": 0.466, "alt": 1250},
    {"id": 347, "lat": 42.412, "lon": 0.588, "alt": 1250},
    {"id": 348, "lat": 42.412, "lon": 0.71, "alt": 1250},
    {"id": 349, "lat": 42.412, "lon": 0.832, "alt": 1250},
    {"id": 350, "lat": 42.412, "lon": 0.954, "alt": 1250},
    {"id": 351, "lat": 42.412, "lon": 1.076, "alt": 1250},
    {"id": 352, "lat": 42.412, "lon": 1.198, "alt": 1250},
    {"id": 353, "lat": 42.412, "lon": 1.32, "alt": 1250},
    {"id": 354, "lat": 42.412, "lon": 1.441, "alt": 1250},
    {"id": 355, "lat": 42.412, "lon": 1.563, "alt": 1250},
    {"id": 356, "lat": 42.412, "lon": 1.685, "alt": 1250},
    {"id": 357, "lat": 42.412, "lon": 1.807, "alt": 1250},
    {"id": 358, "lat": 42.412, "lon": 1.929, "alt": 1250},
    {"id": 359, "lat": 42.412, "lon": 2.051, "alt": 1250},
    {"id": 360, "lat": 42.412, "lon": 2.173, "alt": 1250},
    {"id": 361, "lat": 42.412, "lon": 2.295, "alt": 1250},
    {"id": 362, "lat": 42.412, "lon": 2.417, "alt": 1250},
    {"id": 363, "lat": 42.412, "lon": 2.539, "alt": 1250},
    {"id": 364, "lat": 42.412, "lon": 2.661, "alt": 1250},
    {"id": 365, "lat": 42.412, "lon": 2.783, "alt": 1250},
    {"id": 366, "lat": 42.412, "lon": 2.905, "alt": 1250},
    {"id": 367, "lat": 42.502, "lon": 0.344, "alt": 1330},
    {"id": 368, "lat": 42.502, "lon": 0.466, "alt": 1330},
    {"id": 369, "lat": 42.502, "lon": 0.588, "alt": 1330},
    {"id": 370, "lat": 42.502, "lon": 0.71, "alt": 1330},
    {"id": 371, "lat": 42.502, "lon": 0.832, "alt": 1330},
    {"id": 372, "lat": 42.502, "lon": 0.954, "alt": 1330},
    {"id": 373, "lat": 42.502, "lon": 1.076, "alt": 1330},
    {"id": 374, "lat": 42.502, "lon": 1.198, "alt": 1330},
    {"id": 375, "lat": 42.502, "lon": 1.32, "alt": 1330},
    {"id": 376, "lat": 42.502, "lon": 1.441, "alt": 1330},
    {"id": 377, "lat": 42.502, "lon": 1.563, "alt": 1330},
    {"id": 378, "lat": 42.502, "lon": 1.685, "alt": 1330},
    {"id": 379, "lat": 42.592, "lon": 0.466, "alt": 1410},
    {"id": 380, "lat": 42.592, "lon": 0.588, "alt": 1410},
    {"id": 381, "lat": 42.592, "lon": 0.71, "alt": 1410},
    {"id": 382, "lat": 42.592, "lon": 0.832, "alt": 1410},
    {"id": 383, "lat": 42.592, "lon": 0.954, "alt": 1410},
    {"id": 384, "lat": 42.592, "lon": 1.076, "alt": 1410},
    {"id": 385, "lat": 42.592, "lon": 1.198, "alt": 1410},
    {"id": 386, "lat": 42.592, "lon": 1.32, "alt": 1410},
    {"id": 387, "lat": 42.592, "lon": 1.441, "alt": 1410},
    {"id": 388, "lat": 42.682, "lon": 0.588, "alt": 1490},
    {"id": 389, "lat": 42.682, "lon": 0.71, "alt": 1490},
    {"id": 390, "lat": 42.682, "lon": 0.832, "alt": 1490},
]

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
    """
    last_exception = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_attempts:
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

def species_score(sp, rain_10d, min_temp, tree, days_since_rain, alt, month, aemet_rain_1h=None, mc_rain_today=None, gbif_distributions=None, triangulation=None):
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

    # --- Pluja acumulada (0-30 punts, amb tolerància) ---
    min_rain = sp["min_rain"]
    ratio = rain_10d / min_rain if min_rain else 1
    if ratio >= 1:
        rain_score = 30
    elif ratio >= 0.7:
        rain_score = 30 * ((ratio - 0.7) / 0.3) * 0.6 + 12  # 70-100% del mínim -> 12-30 punts
    elif ratio >= 0.4:
        rain_score = 12 * ((ratio - 0.4) / 0.3)  # 40-70% del mínim -> 0-12 punts
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

    # --- Climatologia de temporada per altitud (0-15 punts) ---
    # Coneixement micològic establert: cada espècie té una temporada més
    # probable segons l'altitud, independentment del detall exacte del dia.
    season_score = seasonal_climate_score(sp, alt, month, gbif_distributions)
    breakdown["temporada"] = round(season_score, 1)
    score += season_score

    # --- Corroboració entre fonts (0-10 punts bonus) ---
    # Si el valor triangulat (combinació ponderada de diverses estacions
    # reals AEMET+Meteoclimatic) confirma pluja recent, és evidència més
    # fiable que una sola font aïllada — es prioritza sobre el bonus simple.
    corrob_score = 0
    if triangulation and triangulation.get("estimated_rain_mm") is not None:
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
    confidence = compute_confidence(sp, gbif_distributions, aemet_rain_1h, mc_rain_today, triangulation)

    return final_score, breakdown, confidence


def compute_confidence(sp, gbif_distributions, aemet_rain_1h, mc_rain_today, triangulation=None):
    """
    Nivell de confiança ("alta"/"mitjana"/"baixa") de la puntuació, INDEPENDENT
    del seu valor. Una puntuació de 84 basada en pocs registres històrics i
    cap corroboració és menys fiable que un 84 recolzat per molta evidència,
    encara que el número sigui idèntic — això evita transmetre una falsa
    sensació de precisió (una puntuació alta no és el mateix que una
    puntuació fiable).

    Factors que sumen confiança:
    - Prou registres GBIF per a aquesta espècie (>= 30 és "molts")
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


def triangulate_rain(lat, lon, aemet_stations, mc_stations, max_km=30, max_stations=4, min_distance_km=0.5):
    """
    Estima la pluja d'avui a un punt combinant les estacions reals més
    properes (AEMET + Meteoclimatic juntes) mitjançant IDW (Inverse Distance
    Weighting): cada estació pesa segons 1/distància², de manera que les més
    properes dominen l'estimació però les llunyanes encara hi aporten.

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

    if not candidates:
        return None

    candidates.sort(key=lambda c: c["distance_km"])
    candidates = candidates[:max_stations]

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
    weather_results = retry_with_backoff(lambda: fetch_weather(ZONES), description="Open-Meteo")

    print("Consultant Meteoclimatic (contrast estacions amateur, historial propi)...")
    history = load_history()
    try:
        mc_stations = retry_with_backoff(fetch_meteoclimatic_stations, description="Meteoclimatic")
        print(f"  Meteoclimatic: {len(mc_stations)} estacions rebudes")
        mc_stations = geocode_meteoclimatic_batch(mc_stations)
        history = update_history_with_meteoclimatic(history, ZONES, mc_stations)
        history = save_history(history)
    except Exception as e:
        print(f"  AVÍS: no s'ha pogut consultar Meteoclimatic ({e}) — es continua sense actualitzar l'historial")

    print("Consultant tipus de bosc (amb cache)...")
    tree_types = load_tree_cache()
    missing_zones = [z for z in ZONES if z["id"] not in tree_types]

    if missing_zones:
        print(f"  {len(missing_zones)} punts sense cache — consultant ICGC...")
        layer_name, available_layers = discover_icgc_layer()
        icgc_start = time.time()
        icgc_max_seconds = 280
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
        veg_max_seconds = 200
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
        except Exception as e:
            print(f"AVÍS: no s'ha pogut consultar AEMET ({e}) — es continua sense contrast")
    else:
        print("AVÍS: no hi ha AEMET_API_KEY configurada — es continua sense contrast")

    print("Consultant GBIF (històric real d'avistaments, FungaCAT)...")
    gbif_distributions = build_gbif_distributions()

    current_month = datetime.now(timezone.utc).month
    today_str = datetime.now(timezone.utc).date().isoformat()
    today_history = history.get(today_str, {})

    zones_out = []
    for zone, daily_wrapper in zip(ZONES, weather_results):
        daily = daily_wrapper.get("daily", {})
        rain_10d, avg_temp, min_temp, days_since_rain = compute_rain_stats(daily)
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

        triangulation = triangulate_rain(zone["lat"], zone["lon"], aemet_stations, mc_stations)

        species_scores = []
        if tree not in NON_FOREST:
            for sp in SPECIES:
                s, breakdown, confidence = species_score(
                    sp, rain_10d, min_temp, tree, days_since_rain, zone["alt"], current_month,
                    aemet_rain_1h=aemet_rain_1h, mc_rain_today=mc_rain_today,
                    gbif_distributions=gbif_distributions, triangulation=triangulation,
                )
                if s > 0:
                    species_scores.append({"id": sp["id"], "name": sp["name"], "score": s, "confidence": confidence, "breakdown": breakdown})
        species_scores.sort(key=lambda x: x["score"], reverse=True)
        matching_species = [s for s in species_scores if s["score"] >= DEFAULT_SCORE_THRESHOLD]

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
            "min_temp": min_temp,
            "days_since_rain": days_since_rain,
            "species_scores": species_scores,
            "aemet_check": aemet_info,
            "own_history_days": own_history_days_count(history, zone["id"]),
            "triangulation": triangulation,
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
        "zones": zones_out,
        "species_catalog": [{"id": sp["id"], "name": sp["name"]} for sp in SPECIES],
    }


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
    - amount 'nada' + puntuació < llindar -> encert
    - la resta -> desencert

    Retorna un resum global i desglossat per franja de puntuació, només amb
    els hallazgos que realment es poden contrastar (no s'inventa res).
    """
    results = {"total_comparable": 0, "aciertos": 0, "por_franja": {}}
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
        if hit:
            results["aciertos"] += 1

        franja = f"{(score // 10) * 10}-{(score // 10) * 10 + 9}"
        franja_stats = results["por_franja"].setdefault(franja, {"total": 0, "aciertos": 0})
        franja_stats["total"] += 1
        if hit:
            franja_stats["aciertos"] += 1

    if results["total_comparable"] > 0:
        results["precision_global"] = round(results["aciertos"] / results["total_comparable"] * 100, 1)
    return results


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


if __name__ == "__main__":
    main()
