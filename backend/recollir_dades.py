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
    {"id": "rovellons",   "name": "Rovellons",           "trees": ["pi_roig", "pi_negre", "pi_pinyer", "pi_blanc", "pi_altres"], "rain_days": [7, 15],  "temp_range": [8, 18],  "min_rain": 20},
    {"id": "ceps",        "name": "Ceps",                 "trees": ["roure", "faig", "pi_roig", "pi_negre", "pi_altres"],        "rain_days": [8, 16],  "temp_range": [10, 20], "min_rain": 25},
    {"id": "camagrocs",   "name": "Camagrocs",            "trees": ["faig", "roure", "alzina"],                                  "rain_days": [10, 20], "temp_range": [10, 18], "min_rain": 20},
    {"id": "trompetes",   "name": "Trompetes de la mort", "trees": ["faig", "roure"],                                            "rain_days": [10, 20], "temp_range": [9, 17],  "min_rain": 25},
    {"id": "oureig",      "name": "Ou de reig",           "trees": ["alzina", "roure", "suro"],                                  "rain_days": [6, 14],  "temp_range": [14, 24], "min_rain": 18},
    {"id": "rossinyols",  "name": "Rossinyols",           "trees": ["faig", "roure", "pi_roig", "pi_altres"],                    "rain_days": [7, 16],  "temp_range": [10, 19], "min_rain": 20},
    {"id": "colmenilles", "name": "Colmenilles",          "trees": ["roure", "pi_blanc", "pi_altres"],                           "rain_days": [8, 18],  "temp_range": [6, 15],  "min_rain": 15},
    {"id": "llengua",     "name": "Llengua de bou",       "trees": ["roure", "suro"],                                            "rain_days": [10, 20], "temp_range": [12, 20], "min_rain": 20},
    {"id": "pinetell",    "name": "Pinetell",             "trees": ["pi_roig", "pi_negre", "pi_altres"],                         "rain_days": [7, 14],  "temp_range": [8, 17],  "min_rain": 20},
    {"id": "fredolic",    "name": "Fredolic",             "trees": ["pi_blanc", "alzina", "pi_altres"],                          "rain_days": [9, 18],  "temp_range": [7, 16],  "min_rain": 18},
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

def species_matches(sp, rain_10d, avg_temp, tree, days_since_rain):
    """
    Comprovació binària: l'espècie només es dona per probable si es compleixen
    TOTS els requisits alhora (hàbitat, pluja, dies des de la pluja, temperatura).
    No hi ha puntuació intermèdia ni compensació entre factors — o hi ha
    condicions o no n'hi ha.
    """
    if tree not in sp["trees"]:
        return False
    if rain_10d < sp["min_rain"]:
        return False
    lo, hi = sp["rain_days"]
    if not (lo <= days_since_rain <= hi):
        return False
    tlo, thi = sp["temp_range"]
    if not (tlo <= avg_temp <= thi):
        return False
    return True


# ---------------------------------------------------------------------------
# 7. PROCÉS PRINCIPAL
# ---------------------------------------------------------------------------

def build_results():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Graella de {len(ZONES)} punts")

    print("Consultant Open-Meteo (meteorologia)...")
    weather_results = fetch_weather(ZONES)

    print("Consultant ICGC (tipus de bosc real per a cada punt)...")
    layer_name, available_layers = discover_icgc_layer()
    tree_results = {}
    icgc_start = time.time()
    icgc_max_seconds = 280
    for i, z in enumerate(ZONES):
        if time.time() - icgc_start > icgc_max_seconds:
            print(f"  ICGC: límit de temps ({icgc_max_seconds}s) assolit a {i}/{len(ZONES)} — es continua sense la resta")
            for remaining in ZONES[i:]:
                tree_results[remaining["id"]] = ("desconegut", None)
            break
        tree_results[z["id"]] = fetch_tree_type(z["lat"], z["lon"], layer_name, debug=(i < 5))
        time.sleep(0.05)
        if (i + 1) % 50 == 0:
            print(f"  ICGC: {i + 1}/{len(ZONES)} punts consultats...")
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

        matching_species = []
        if tree not in NON_FOREST:
            for sp in SPECIES:
                if species_matches(sp, rain_10d, avg_temp, tree, days_since_rain):
                    matching_species.append({"id": sp["id"], "name": sp["name"]})

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
            "matching_species": matching_species,
            "has_match": len(matching_species) > 0,
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
