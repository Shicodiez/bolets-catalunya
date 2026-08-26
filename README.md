# Predictor de bolets — Catalunya

Web que calcula, según datos meteorológicos y de vegetación reales, en qué
zonas de Catalunya hay más probabilidad de encontrar cada tipo de bolet, y
permite registrar hallazgos propios para ir afinando el modelo con el tiempo.

**Web pública:** https://shicodiez.github.io/bolets-catalunya/web/ (protegida
con contraseña, ver "Control de acceso" más abajo)
**Repositorio:** https://github.com/Shicodiez/bolets-catalunya
**Worker de Cloudflare:** https://bolets-hallazgos.shicoars.workers.dev/

## Qué es cada carpeta

- `backend/recollir_dades.py` — el programa que recoge datos de todas las
  fuentes, calcula la puntuación de cada bolet en cada zona, y guarda el
  resultado. Se ejecuta automáticamente cada 6 horas.
- `data/resultats.json` — el resultado del cálculo. La web lo lee.
- `data/bosc_cache.json` — caché del tipo de bosque genérico por zona (ICGC), 30 días.
- `data/vegetacio_layers_cache.json` — caché de capas de especie de árbol (VEGETACIO), 90 días.
- `data/gbif_cache.json` — caché de distribución mensual y de altitud de cada especie según GBIF/FungaCAT, 60 días.
- `data/historial_lluvia.json` — historial propio de lluvia diaria vía Meteoclimatic, 30 días.
- `data/geocode_cache.json` — caché permanente de coordenadas de estaciones de Meteoclimatic (Nominatim).
- `data/evolucion.json` — snapshot diario de la mejor puntuación por zona, 30 días, para calcular subidas/bajadas.
- `data/hallazgos.json` — hallazgos reales registrados por los usuarios desde la web. Se actualiza vía el Worker, no directamente por el backend.
- `web/index.html` — la web: login, mapa interactivo, deslizador de umbral, formulario de hallazgos, panel de precisión histórica, explicaciones de DeepSeek, banner de caducidad de credenciales.
- `worker/index.js` — código del Worker de Cloudflare (ver más abajo).
- `.github/workflows/actualitzar.yml` — automatización que ejecuta el backend cada 6 horas.

## Fuentes de datos usadas (todas gratuitas)

| Fuente | Para qué se usa |
|---|---|
| **Open-Meteo** | Histórico de lluvia y temperatura (16 días), sin API key |
| **AEMET OpenData** | Contraste con la estación real más cercana a cada zona (API key, caduca cada 3 meses) |
| **Meteoclimatic** | Segunda red de estaciones amateur para contrastar lluvia del día; se geocodifica con Nominatim porque el feed no da coordenadas |
| **ICGC** | Tipo de bosque genérico (coníferas/frondosas/perennifolias) de cada punto, vía WMS |
| **VEGETACIO** (Generalitat) | Especie exacta de árbol (pi roig, pi negre, alzina, faig...), refinando el dato del ICGC |
| **GBIF / FungaCAT** | Histórico real de avistamientos: temporada real (mes) y altitud típica de cada especie en Catalunya |
| **Nominatim (OpenStreetMap)** | Nombres de lugar ↔ coordenadas, en ambos sentidos |
| **DeepSeek** | Explicaciones en lenguaje natural del "por qué" de una puntuación, a petición del usuario — nunca decide el cálculo |

## Cómo funciona el cálculo

Para cada uno de los ~390 puntos de la rejilla, y cada una de las 10 especies
del catálogo, se calcula una **puntuación de 0 a 100** sumando evidencia:
lluvia acumulada desde el inicio de la tanda de lluvias, días desde que
empezó a llover, temperatura mínima nocturna, temporada real de la especie
(GBIF, por mes y altitud), y un bonus si AEMET o Meteoclimatic corroboran la
lluvia que ve Open-Meteo. El único requisito "duro" es el tipo de bosque —
el resto es gradual, así que un solo dato flojo no hace desaparecer una
especie con buena evidencia por lo demás.

Junto a cada puntuación se muestra un nivel de **confianza** (🟢🟠🔴),
independiente del valor numérico: refleja cuánta evidencia real la respalda
(registros GBIF, corroboración entre fuentes), para no transmitir una falsa
sensación de precisión.

La web muestra las zonas por encima de un **umbral ajustable** (por defecto
70, con deslizador).

## Evolución y precisión histórica

Cada día se guarda un snapshot de la mejor puntuación de cada zona. La web
compara con hace 7 días y marca **▲/▼** en las zonas que más han subido o
bajado — útil para detectar "dónde está empezando ahora". Además, cuando hay
suficientes hallazgos registrados con fecha y ubicación, el backend cruza
cada uno con la puntuación que tenía esa zona ese día concreto y calcula un
**% de precisión real** del modelo, desglosado por franja de puntuación —
para saber si el umbral de 70 tiene sentido de verdad, con datos, no con
suposiciones.

## El Worker de Cloudflare (`worker/index.js`)

Como GitHub Pages solo sirve archivos estáticos, hay un Worker en Cloudflare
que hace de intermediario para:

1. **Guardar hallazgos de forma permanente** en `data/hallazgos.json` del
   repositorio, vía un token de GitHub guardado como Secret.
2. **Control de acceso** — verifica la contraseña de entrada a la web.
3. **Explicaciones de DeepSeek** (endpoint `/explain`) — recibe el desglose
   de una puntuación y genera una explicación en 2-3 frases.

Secrets configurados en el Worker (Cloudflare → Workers & Pages →
`bolets-hallazgos` → Settings → Variables and Secrets):
- `GITHUB_TOKEN` — fine-grained token, Contents read/write solo sobre
  `bolets-catalunya`. Caduca el 24/11/2026.
- `APP_PASSWORD` — la contraseña de acceso a la web.
- `DEEPSEEK_API_KEY` — key de la API de DeepSeek para las explicaciones.

## Control de acceso

La web pide una contraseña antes de mostrar nada. Solo quien la conozca
puede entrar:
- Guardada como Secret `APP_PASSWORD` en el Worker — nunca en el código.
- Al introducirla, el navegador recibe un token de sesión firmado (30 días).
- **Para revocar el acceso a todo el mundo de golpe**: cambia
  `APP_PASSWORD` en el Worker. Todas las sesiones antiguas dejan de valer
  al instante.

## Registro de hallazgos propios

Desde la web, se marca en el mapa el punto exacto: especie, altitud (tramos
de 50m), tipo de árbol, fecha, cantidad (mucho/poco/nada). El nombre del
lugar se rellena solo (geocodificación inversa) pero es editable. Cada
hallazgo aparece como un marcador propio en el mapa (no en lista, para
escalar a miles de registros), guardado de forma permanente vía el Worker.

## Mantenimiento

- **API key de AEMET** caduca cada 3 meses (próxima: 25/11/2026) — renovar en
  https://opendata.aemet.es y actualizar el Secret `AEMET_API_KEY` en GitHub
  (Settings → Secrets and variables → Actions).
- **Token de GitHub del Worker** caduca el 24/11/2026 — regenerar en
  https://github.com/settings/tokens?type=beta (mismos permisos) y
  actualizar `GITHUB_TOKEN` en el Worker.
- La web avisa automáticamente en rojo cuando a cualquiera de estas
  credenciales le quedan 15 días o menos.
- Meteocat (XEMA) pendiente de aprobación — cuando llegue, se puede sumar
  como fuente adicional de contraste junto a AEMET y Meteoclimatic.
- El backend se ejecuta solo cada 6 horas vía GitHub Actions; también se
  puede lanzar a mano desde "Actions" → "Actualitzar dades de bolets" →
  "Run workflow".

## Ideas futuras (aparcadas, no implementadas)

- **Humedad del suelo / balance hídrico** (Sentinel/Copernicus, ERA5-Land):
  identificado como la mejora de mayor impacto potencial, pero de coste de
  implementación bastante más alto que las fuentes actuales.
- **Triangulación real de estaciones meteorológicas**: en vez de usar solo
  la estación más cercana de cada red, interpolar entre varias estaciones
  próximas (AEMET + Meteoclimatic + futura Meteocat) ponderando por
  distancia, para estimar la lluvia real de un punto sin estación propia
  con más precisión que "coger el dato del vecino más cercano".
