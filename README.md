# Predictor de bolets — Catalunya

Web que calcula, según datos meteorológicos y de vegetación reales, en qué
zonas de Catalunya hay más probabilidad de encontrar cada tipo de bolet.

**Web pública:** https://shicodiez.github.io/bolets-catalunya/web/
**Repositorio:** https://github.com/Shicodiez/bolets-catalunya

## Qué es cada carpeta

- `backend/recollir_dades.py` — el programa que recoge datos de todas las
  fuentes, calcula la puntuación de cada bolet en cada zona, y guarda el
  resultado. Se ejecuta automáticamente cada 6 horas (ver más abajo).
- `data/resultats.json` — el resultado del cálculo. La web lo lee.
- `data/bosc_cache.json` — caché del tipo de bosque genérico por zona (ICGC),
  válido 30 días.
- `data/vegetacio_layers_cache.json` — caché de las capas de especie de árbol
  descubiertas en el servicio VEGETACIO, válido 90 días.
- `data/gbif_cache.json` — caché de la distribución mensual real de cada
  especie de bolet según GBIF/FungaCAT, válido 60 días.
- `data/historial_lluvia.json` — historial propio de lluvia diaria, construido
  poco a poco con Meteoclimatic (se conserva 30 días).
- `data/geocode_cache.json` — caché permanente de coordenadas de las
  estaciones de Meteoclimatic (geocodificadas vía Nominatim/OSM).
- `web/index.html` — la web: mapa interactivo, lista de zonas, deslizador de
  umbral de sensibilidad, y formulario para registrar hallazgos propios.
- `.github/workflows/actualitzar.yml` — la automatización que ejecuta el
  backend cada 6 horas y guarda los resultados en el repositorio.

## Fuentes de datos usadas (todas gratuitas)

| Fuente | Para qué se usa |
|---|---|
| **Open-Meteo** | Histórico de lluvia y temperatura (16 días), sin API key |
| **AEMET OpenData** | Contraste con la estación real más cercana a cada zona (requiere API key, caduca cada 3 meses) |
| **Meteoclimatic** | Segunda red de estaciones (amateur) para contrastar lluvia del día; se geocodifica con Nominatim porque el feed no da coordenadas |
| **ICGC** (Institut Cartogràfic i Geològic de Catalunya) | Tipo de bosque genérico (coníferas/frondosas/perennifolias) de cada punto, vía WMS |
| **VEGETACIO** (Generalitat, sig.gencat.cat) | Especie exacta de árbol (pi roig, pi negre, alzina, faig...) cuando está disponible, refinando el dato del ICGC |
| **GBIF / FungaCAT** | Histórico real de avistamientos de cada especie de bolet en Catalunya, usado para calcular su temporada real (mes del año) en vez de una estimación manual |
| **Nominatim (OpenStreetMap)** | Convierte nombres de lugar de Meteoclimatic en coordenadas |

## Cómo funciona el cálculo

Para cada uno de los ~390 puntos de la rejilla que cubre Catalunya, y para
cada una de las 10 especies de bolet del catálogo, se calcula una
**puntuación de 0 a 100** sumando evidencia de varios factores:

- Lluvia acumulada desde el inicio de la tanda de lluvias actual (no una
  ventana fija de días)
- Días transcurridos desde que empezó a llover (cada especie tiene su rango)
- Temperatura mínima nocturna (no la media del día — es la que refleja el
  frescor que activa la salida del bolet)
- Temporada típica de la especie según altitud y mes (con datos reales de
  GBIF cuando hay suficientes registros históricos)
- Bonus si AEMET o Meteoclimatic corroboran la lluvia que ve Open-Meteo

El único requisito "duro" (que descarta una especie por completo) es el tipo
de bosque — el resto de factores son graduales y se compensan entre sí, así
que un solo dato flojo de una fuente no hace desaparecer una especie que por
lo demás tiene buena evidencia a favor.

La web muestra las zonas cuya puntuación supera un **umbral ajustable** (por
defecto 70) con un deslizador, para que cada persona decida cuánta
sensibilidad quiere.

## Registro de hallazgos propios

Desde la web, se puede marcar en el mapa el punto exacto donde se ha
encontrado (o no) algo, indicando especie, lugar, altitud, tipo de árbol,
fecha y cantidad. Se guarda en el navegador de quien lo usa (no es
compartido entre usuarios) y sirve como base para ir calibrando el modelo
con datos reales de campo con el tiempo.

## Mantenimiento

- La **API key de AEMET caduca cada 3 meses** — hay que renovarla en
  https://opendata.aemet.es y actualizar el secreto `AEMET_API_KEY` en
  GitHub (Settings → Secrets and variables → Actions).
- Meteocat (XEMA) está pendiente de aprobación — cuando llegue el acceso,
  se puede sumar como fuente adicional de contraste de lluvia junto a
  AEMET y Meteoclimatic.
- El proceso se ejecuta solo cada 6 horas vía GitHub Actions; también se
  puede lanzar a mano desde la pestaña "Actions" del repositorio → workflow
  "Actualitzar dades de bolets" → "Run workflow".
