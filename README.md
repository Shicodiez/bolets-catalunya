# Predictor de bolets — Catalunya

## Para quien la va a usar

Esta web (y también una app Android instalable) te dice, según el tiempo
real de los últimos días (lluvia, temperatura, humedad de la tierra y del
aire, y radar en tiempo real), en qué zonas de Catalunya es más probable
encontrar cada tipo de bolet ahora mismo.

**Cómo usarla:**
1. Escribe tu email (tiene que ser uno de los autorizados) y te llegará un
   código de acceso por correo — introdúcelo para entrar.
2. En el mapa verás puntos de colores — cada uno es una zona de nuestra
   rejilla de predicción (no son estaciones meteorológicas reales: son
   unos 4.250 puntos por Catalunya, de los cuales unos 2.050 caen en bosque y
   son los que tienen predicción; ver «La rejilla»). Toca un punto para
   ver qué especie cumple bien las condiciones, con qué puntuación (0-100,
   cuanto más alto mejor) y por qué.
3. Puedes mover el deslizador de arriba para ver más o menos zonas (más
   exigente = menos puntos, pero más fiables).
4. Junto a cada puntuación verás un icono 🟢🟠🔴 — es la **confianza**: no es
   lo mismo una puntuación alta bien respaldada por datos reales que una
   basada solo en el cálculo del día. En verde, fíate más.
5. Si tocas "¿Por qué esta puntuación?" te da una explicación en lenguaje
   normal de qué la ha hecho subir o bajar.
6. Cuando salgáis al monte, registrad el resultado de la salida
   (encontrasteis mucho, poco, o buscasteis sin encontrar nada). Con **«📡 Usar mi
   ubicación»** (GPS del móvil; o «📍 Marcar en el mapa») se rellenan solos el
   lugar, la altitud, el tipo de árbol y la fecha; tú eliges la seta y el
   resultado, y puedes corregir lo rellenado. Los ceps se registran como «Cep» a
   secas (no importa la variedad). Cuantos
   más registremos, mejor se irá afinando el modelo con datos reales
   vuestros. Estas salidas no se ven en el mapa (para no saturarlo), pero
   sí cuentan por detrás.
7. Más abajo hay un desplegable de "Estaciones meteorológicas" donde
   puedes elegir cualquiera de las estaciones reales que usa el sistema
   (AEMET, Meteocat, Meteoclimatic) y ver sus datos tal cual llegan.
8. **Guía de identificación** (enlace arriba y en la pantalla de acceso, y
   «📖 Cómo reconocerla» en cada especie de una zona): 313 fichas **desplegables
   con foto**, cada una con su nombre en **latín, catalán y castellano** (las setas del predictor y las peligrosas con las que se
   confunden). Arriba hay **📷 Identificar con fotos**: haces hasta **3 fotos**
   de la misma seta (arriba, debajo del sombrero, pie con la base); la app lee
   de cada una unos rasgos sencillos (color, láminas o poros, anillo, bolsa...),
   los enseña en un panel que **puedes corregir** (y rellenar a mano: olor,
   látex, esporada, dónde crece...) y los compara con las 313 fichas, con un
   **porcentaje de coincidencia** y con lo que encaja, lo que no y lo que falta
   comprobar. Ese porcentaje **no es la probabilidad** de que sea esa seta ni
   quiere decir que se pueda comer: mide qué parte de lo que pide la ficha está
   confirmada con los rasgos indicados. Si marcas **«bolsa» (volva)** en la base del
   pie, las fichas que no son amanitas quedan descartadas (en esta guía solo las
   amanitas la tienen; si la seta tiene bolsa y no es una amanita, no está en la
   guía), así que marca «bolsa» solo si has excavado y la has visto, y si no has
   desenterrado la base déjalo en «no lo sé». Leer las fotos necesita cobertura y
   haber entrado antes en el predictor; el panel de rasgos funciona **sin cobertura**.
   La guía en sí funciona sin cobertura una vez abierta con conexión (guarda
   también las fotos) y no pide iniciar sesión. Ojo: el texto lo ha redactado una
   IA y **no lo ha revisado ningún micólogo**, y la lectura de las fotos la hace
   un modelo de IA general que puede equivocarse.

Los datos se actualizan solos cada 3 horas. No hace falta hacer nada para
que esté al día.

---

## Para quien toque el código

**Web pública:** https://shicodiez.github.io/bolets-catalunya/web/ (protegida
con verificación de email)
**Repositorio:** https://github.com/Shicodiez/bolets-catalunya
**Worker de Cloudflare:** https://bolets-hallazgos.shicoars.workers.dev/

### Qué es cada carpeta

- `backend/recollir_dades.py` — recoge datos de todas las fuentes, calcula
  la puntuación de cada bolet en cada zona, y guarda el resultado. Se
  ejecuta automáticamente cada 3 horas.
- `backend/requirements.txt` — dependencias externas (rasterio, Pillow).
- `data/resultats.json` — el resultado del cálculo. La web lo lee.
- `data/zones_grid.json` — caché permanente de la rejilla (coordenadas y
  altitud real de cada punto — nunca caduca, se genera una sola vez).
- `data/bosc_cache.json` — caché del tipo de bosque genérico por zona (ICGC), 1 año.
- `data/vegetacio_layers_cache.json` — lista de capas de especie de árbol (VEGETACIO, 90 días) **y** la especie exacta ya resuelta de cada punto (`points`, se completa por lotes y se conserva entre ejecuciones).
- `data/weather_block_cache.json` — caché de tiempo por punto. Se refresca por **bloques rotatorios** (3 bloques geográficos, uno por ejecución, así que todos los puntos se renuevan cada ~9 h) y cada punto guarda además su **serie diaria propia** (lluvia y temperaturas; arranca con los ~16 días que devuelve Open-Meteo y acumula hasta 45) para detectar episodios de lluvia. Mientras un punto aún no tiene serie, se usa el resumen compacto (`rain_10d`, `days_since_rain`).
- `data/gbif_cache.json` — caché de distribución mensual y de altitud de cada especie según GBIF/FungaCAT, 60 días.
- `data/historial_lluvia.json` — historial propio de lluvia diaria vía Meteoclimatic, 30 días.
- `data/geocode_cache.json` — caché permanente de coordenadas de estaciones de Meteoclimatic (Nominatim).
- `data/meteocat_stations_cache.json` — caché de metadatos de estaciones XEMA/Meteocat, 90 días.
- `data/geologia_cache.json` — caché permanente de litología (silici/calcari/mixt) por coordenadas, con el texto original del ICGC para poder reclasificar sin volver a consultar.
- `data/zone_names_cache.json` — caché permanente de nombres reales de las zonas (Nominatim, reverse geocoding).
- `data/evolucion.json` — snapshot diario de la mejor puntuación por zona, 30 días (solo para las flechas ▲/▼).
- `data/validacio.json` — **predicciones congeladas** de cada salida registrada: la puntuación de cada especie en la zona más cercana el día en que el backend ve la salida (ver «Validación»). Permanente.
- `data/hallazgos.json` — salidas reales registradas por los usuarios. Se actualiza vía el Worker.
- `web/index.html` — la web: login, mapa, deslizador de umbral, formulario de salidas, panel de tasa de confirmación, explicaciones de DeepSeek.
- `web/guia.html` — guía de identificación (una sola página, sin librerías externas; las fotos las carga de `web/fotos/`). **Se genera** con `python3 tools/generar_guia.py` a partir de `tools/guia_datos.py` (texto), `tools/rasgos_datos.py` (rasgos de cada ficha) y `tools/puntuar.js` (cálculo de la coincidencia): se editan esos archivos y se vuelve a generar, no el HTML a mano.
- `web/fotos/` — fotos de las fichas (`<id>-<n>.jpg`), `creditos.json` (autor y licencia de cada una) e `informe.txt`. **No se escriben a mano**: las genera el workflow «Descargar fotos de la guia».
- `web/sw.js` — service worker: guarda `guia.html`, sus fotos y la pantalla de la app para verlas sin cobertura (red primero, copia guardada como plan B; las fotos desde la copia guardada y se refrescan en segundo plano; los datos del mapa y la identificación por foto no se guardan).
- `tools/` — `generar_guia.py` y `guia_datos.py` (contenido de la guía), `rasgos_datos.py` (vocabulario de rasgos y «firma» de cada ficha), `puntuar.js` (cálculo de la coincidencia), `fotos_datos.py` (qué foto lleva cada ficha) y `descargar_fotos.py` (descarga de Wikimedia Commons).
- `FUENTES-REVISADAS.md` — revisión de 35 webs, foros y artículos (15/10/2026): qué dice cada uno, qué sirve para el modelo y la guía, qué no se pudo leer y el aviso sobre la peste porcina africana.
- `worker/index.js` — código del Worker de Cloudflare. **Se despliega directamente en el editor de Cloudflare, subirlo a GitHub NO lo actualiza en producción.**
- `.github/workflows/actualitzar.yml` — automatización que ejecuta el backend cada 3 horas.
- `.github/workflows/descargar_fotos.yml` — se lanza **a mano** (Actions → «Descargar fotos de la guia» → Run workflow): descarga las fotos de la guía de Wikimedia Commons (solo licencias libres) y las guarda en `web/fotos/`.

### La rejilla de predicción

La rejilla es **adaptativa** (no son estaciones meteorológicas reales):
sondeo a 5 km por toda Catalunya, y densificación a 2,5 km (3×3 puntos) solo
en las celdas con bosque. **Cifras reales a 15/10/2026** (las que aparecían
en versiones antiguas —1.470, 1.660, 3.000, 7.300— eran de etapas anteriores o
estimaciones de diseño):

| Etapa | Puntos |
|---|---|
| Rejilla generada (5 km + densificación 2,5 km, con los puntos de verificación del sondeo) | 8.285 |
| Tras descartar los que están a menos de 0,5 km de otro (`dedupe_zones`; se conservan los `id`) | **4.248** (los que procesa el backend) |
| De ellos, con bosque y predicción por especie | **≈ 2.050** |
| Puntos con árbol genérico (`pi_altres`, `roure`, `alzina`) aún por afinar con VEGETACIO | se afinan por lotes de 900 s en cada ejecución (≈ 1-2 días hasta terminar) |

Para saber la cifra exacta de hoy: `len(ZONES)` en el log de la Action
(«… llocs diferents») o el número de zonas de `data/resultats.json`.
Se generan una sola vez con:
- **Filtro de polígono** aproximado de Catalunya, para no generar puntos
  en el mar (verificado dando ~393 puntos con espaciado de 10km, casi
  idéntico a la rejilla original manual de 390 puntos).
- **Altitud real** vía la Elevation API de Open-Meteo (Copernicus DEM,
  90m de resolución) — sustituye a una aproximación por bloques que tenía
  la rejilla original (69 de 390 puntos originales compartían
  literalmente la misma altitud aproximada).

Se cachean en `data/zones_grid.json` de forma permanente (las coordenadas
y la altitud del terreno no cambian). Aumentar la densidad más allá de
esto tiene un límite real: la geocodificación de nombres de zona respeta
el límite de Nominatim (4 peticiones/minuto para scripts automáticos),
así que completar todos los nombres de los miles de puntos lleva semanas
(mientras tanto una zona sin nombre muestra sus coordenadas).

### Fuentes de datos usadas (todas gratuitas)

| Fuente | Para qué se usa |
|---|---|
| **Open-Meteo** | Histórico de lluvia y temperatura (16 días); humedad real del suelo, evapotranspiración y humedad relativa del aire; altitud real de la rejilla (Elevation API) |
| **AEMET OpenData** | Estación real más cercana a cada zona, para la triangulación (API key, caduca cada 3 meses) |
| **Meteocat / XEMA** | Red oficial de la Generalitat (~190 estaciones), la más densa para Catalunya; misma triangulación (API key, caduca 31/08/2027) |
| **Meteoclimatic** | Red de estaciones amateur; se geocodifica con Nominatim porque el feed no da coordenadas |
| **RainViewer** | Mosaico de radar europeo (agrega AEMET, Meteocat y redes europeas), cobertura de superficie en tiempo real. Sin API key |
| **ICGC** | Tipo de bosque genérico y geología del suelo (silici/calcari), vía WMS |
| **VEGETACIO** (Generalitat) | Especie exacta de árbol, refinando el dato del ICGC |
| **GBIF / FungaCAT** | Histórico real de avistamientos: temporada real (mes) y altitud típica de cada especie |
| **Nominatim (OpenStreetMap)** | Nombres de lugar ↔ coordenadas, en ambos sentidos |
| **DeepSeek** | Explicaciones en lenguaje natural del "por qué" de una puntuación, a petición del usuario — nunca decide el cálculo |

Se investigaron y descartaron por no ser viables sin coste o sin
intervención manual: **SIAR**, **Ecowitt**, **Weather Underground**,
**Netatmo** (login manual vía OAuth2), **el radar de AEMET vía API REST**,
**Meteocat/XRAD** y **Tempestes.cat** (ver apartado de radar más abajo).

### Cómo funciona el cálculo

Para cada punto de la rejilla (~4.250 tras eliminar duplicados a menos de
0,5 km), y cada una de las 14 especies del catálogo, se calcula una
**puntuación de 0 a 100** en dos pasos: primero se suma evidencia de seis
componentes y después se **multiplica por los limitantes biológicos**
(ver más abajo). Componentes de la suma:

- **Lluvia acumulada** (0-22 pts) del episodio de lluvia elegido
- **Días desde la lluvia principal** (0-25 pts) — cada especie tiene su rango.
  Ya NO se mide desde el último chubasco: un episodio es un grupo de días
  mojados (≥2 mm, huecos de hasta 4 días secos, ≥8 mm en total) y se
  fecha por el día en que había caído la mitad del agua. Un chubasco
  posterior de 3 mm no «reinicia» el reloj. Cada especie elige el episodio
  que mejor le encaja.
- **Temperatura mínima nocturna** (0-20 pts) — no la media del día
- **Humedad real del suelo** (0-8 pts) — distingue si el agua caída sigue
  en la tierra o se ha perdido, con bonus si la tendencia es a
  humedecerse. Incluye un pequeño ajuste (±1 pt) por humedad relativa del
  aire: un aire muy seco puede resecar la capa más superficial y el
  sombrero del bolet aunque el suelo profundo siga húmedo.
- **Temporada real de la especie** (0-15 pts) según GBIF, por mes y
  altitud. Incluye un pequeño ajuste (±1.5 pts) por geología del suelo,
  solo para las 3 especies con evidencia clara (Cep y Ou de reig
  prefieren silici, Camagrocs prefiere calcari).
- **Corroboración entre fuentes** (0-10 pts) — orden de comprobación: 1) radar
  (un fotograma instantáneo; si indica ≥ 3 mm/h → 10 pts); 2) si no, la
  triangulación de estaciones (AEMET+Meteocat+Meteoclimatic); 3) si no, lecturas
  sueltas de estación. Es un **bonus** de confianza: el radar NO entra en la
  detección de episodios de lluvia ni en la cantidad de lluvia.

### Limitantes biológicos (`SPECIES_BIO`)

Antes todo era una suma: una especie podía llegar a 90 aunque fallara lo
más importante. Ahora cada especie tiene limitantes que **multiplican**
(0-1) el resultado: **momento** respecto a la lluvia principal, **época
del año**, **altitud**, **calor** (mínimas y máximas de los últimos 7 días)
y **geología**. Si un limitante vale 0,3 la puntuación no pasa de 30. La
web muestra los que están actuando (⚠️) y el Worker se los pasa a la IA
para que explique el porqué.

Ejemplo, Ou de reig (*Amanita caesarea*): sale **15-20 días** después de la
lluvia principal, necesita **noches ≥ ~12 °C y máximas ≥ ~22 °C**, casi no
pasa de **1.000 m**, es de **agosto a octubre** y prefiere suelos **ácidos**
(silici). Casos reales que lo motivaron (15/10/2026): Montnegre marcaba 88-92
solo 7 días después de ~170 mm; Matadepera (conglomerados con cemento
calcáreo) salía como «silici»; salían ou de reig a 1.986 m y colmenilles
(seta de primavera) a 71 en octubre. Con las mismas condiciones hoy puntúan
~25-38. Las curvas son valores de partida **calibrables** con las salidas
reales (`hallazgos`): `SPECIES_BIO` es el único sitio donde tocar.

Además de los limitantes, el tipo de bosque sigue siendo un requisito duro:
si el árbol no está en la lista `trees` de la especie, puntúa 0. Algunas
especies aceptan un árbol «menos habitual» con una rebaja (`tree_factor`):
Trompetes bajo encina/alzina (×0,85), Cep fosc bajo haya (×0,85) y Cep d'estiu
bajo encina (×0,85) — añadido tras salidas reales (ver «Validación»). Cuando
VEGETACIO afina el tipo (pino rojo, pino blanco, abeto, haya, alcornoque…),
las listas incluyen esos «hijos» donde la especie de verdad crece, para no
perder avisos (comprobado en `tests/test_model.py`).

Junto a cada puntuación se muestra un nivel de **confianza** (🟢🟠🔴),
independiente del valor numérico: refleja cuánta evidencia real la
respalda.

La web muestra las zonas por encima de un **umbral ajustable** con deslizador.
Desde el 15/10/2026 **arranca en 90** (antes 70), a petición de Sergio: es un valor
solo de pantalla. Con los datos del 15/10/2026 (2.052 zonas forestales) había 1.454
zonas con alguna especie ≥ 70 y **109 con ≥ 90**; de estas, sobre todo Cep fosc
(perfil provisional, confianza baja) y Llengua de bou, y la nota máxima era 94. El
backend sigue usando su propio 70 (`DEFAULT_SCORE_THRESHOLD`) para la tasa de
confirmación — así esa estadística no cambia con lo que ponga cada persona en
pantalla — y el campo `default_threshold` del JSON ya no manda sobre el
deslizador. Bajar el deslizador enseña más zonas (con 80 salen 986).

**La pantalla recuerda lo que has elegido** mientras la app/pestaña siga abierta
(`sessionStorage`): especie, umbral, orden, posición y zoom del mapa, posición de
la página y la ficha de zona que tuvieras abierta. Así, al ir a «📖 Cómo
reconocerla» (la guía) y volver, el mapa está como lo dejaste. Al abrir la app de
nuevo, empieza otra vez en 90 y todas las especies. En la guía, los enlaces del
índice (#cep, #phalloides…) ya no añaden entradas al historial y «← Volver al
predictor» usa el historial: con **un solo «atrás»** (el del móvil o el enlace) se
vuelve al mapa. En la **APK** (versión 1.1) el botón «atrás» del móvil retrocede por
el historial de la web (`MainActivity.java`) y solo sale de la app cuando no hay nada
que retroceder.

### Radar meteorológico

Da cobertura de **superficie continua** en vez de solo puntos con
estación — importante porque una tormenta muy localizada puede caer justo
entre dos estaciones y no detectarse de otro modo. Es una estimación (no
tan exacta como un pluviómetro físico) del instante actual (no
acumulado), pero cubre cualquiera de los puntos de la rejilla, tengan o no
una estación cerca. Solo se usa en el bonus de corroboración (y en la
confianza); **no** decide la lluvia del episodio.

- **RainViewer (activo)**: mosaico europeo gratuito, sin API key. Da un
  color (RGBA) por píxel, traducido a dBZ (tabla oficial "Universal Blue")
  y luego a mm/h (Marshall-Palmer). Si un día no llueve en ningún punto,
  es una respuesta válida (no un fallo) — el sistema lo distingue
  correctamente. En el código sus valores se vuelcan con `setdefault`: rellenan
  los puntos que no tienen lectura de radar y **no sustituyen** una lectura que
  ya existiera. Como el radar de AEMET está desactivado, hoy RainViewer es la
  única fuente de radar y el «orden de prioridad» es solo el del bonus.
- **AEMET (implementado pero desactivado)**: el endpoint
  `/api/red/radar/regional/{radar}` no devuelve la imagen realmente
  georreferenciada (verificado: sin CRS, transform de identidad). Hay un
  interruptor `AEMET_RADAR_ENABLED = False` en `recollir_dades.py`;
  cambiarlo a `True` reactiva el intento si algún día se resuelve.
- **Meteocat/XRAD y Tempestes.cat (descartados, cerrado definitivamente)**:
  Meteocat tiene la mejor cobertura teórica para Catalunya (4 radares
  propios), pero confirmado dos veces con acceso directo a la cuenta real
  (secciones "Operacions" y "Plans i registre" de `apidocs.meteocat.gencat.cat`)
  que el radar no está disponible bajo ningún plan de la API — solo las
  categorías XEMA, XDDE y Dades de Predicció. Tempestes.cat (portal
  catalán con radar) tampoco es una alternativa real: su propia web
  confirma que combina AEMET + Meteo-France, sin API pública para
  desarrolladores — es un agregador como RainViewer, no una fuente nueva.

### Geología del suelo (silici / calcari)

Como iFong, distingue suelo silíceo de calcáreo — un factor biológico
real que determina qué especies pueden fructificar. Servicio WMS del ICGC
(`geoserveis.icgc.cat/servei/catalunya/geologia-territorial/wms`, capa
`unitats-geologiques-50000`) — confirmado en la práctica tras dos
intentos fallidos con URLs de un servicio antiguo ya dado de baja
(`icgc_mg50m`/`icgc_mg250m`/`UGEO_PA`).

Se clasifica por palabras clave del texto de respuesta (`Descripcio` y
`Descripcio_protolit`): "calcària", "marbre", "guix"... → calcari;
"granit", "pissarra", "gres", "basalt"... → silici; ambos tipos presentes
→ mixt. Clasificación en tres niveles: palabras de silici claras, palabras de
calcari claras, y ambiguas («conglomerat», «detrític»… → mixt, porque
pueden tener cemento calcáreo, como en Matadepera). Caché por **coordenadas**
(no por id) con el texto original, que se completa por lotes; una caída de
red nunca se guarda como «sin dato» y 8 fallos seguidos paran la tanda.
En el scoring la geología ya no es un ajuste de ±1,5: es un limitante
fuerte para las especies acidófilas (Ou de reig).

Preferencias usadas: **Ou de reig** acidófilo (limitante fuerte), **Cep**
ligera preferencia por silici, **Camagrocs** por calcari. El resto no tiene
ajuste (no hay evidencia fiable para inventar una preferencia).

### Estaciones meteorológicas: consulta directa

En la web, entre el formulario de "Registrar salida" y la lista de zonas,
hay un desplegable con todas las estaciones reales que usa el sistema
(AEMET + Meteocat/XEMA + Meteoclimatic) — al elegir una se muestra su
fuente, coordenadas, lluvia registrada y hora de la última actualización
(cuando la fuente la da). Combina las tres redes con `build_all_stations_list()`,
filtrando solo estaciones dentro del bounding box de Catalunya (AEMET
devuelve estaciones de toda España) y deduplicando por nombre+coordenadas
(AEMET puede dar varias lecturas horarias de la misma estación como si
fueran entradas distintas).

### Evolución, tasa de confirmación y cobertura de datos

Cada día se guarda un snapshot de la mejor puntuación de cada zona. La web
compara con hace 7 días y marca **▲/▼**.

Cuando hay salidas contrastables, el backend calcula una **tasa de
confirmación** (no "precisión": no es una muestra representativa de todas las
zonas, solo de las visitadas). Cómo se calcula exactamente, y por qué todavía
no demuestra nada, se explica en «Validación».

La web avisa cuando alguna fuente de datos ha fallado de verdad (no
cuando simplemente no hay lluvia que detectar).

### El Worker de Cloudflare (`worker/index.js`)

Como GitHub Pages solo sirve archivos estáticos, hay un Worker en
Cloudflare que hace de intermediario para:
1. **Guardar salidas de forma permanente** en `data/hallazgos.json`.
2. **Control de acceso** — genera y verifica códigos de un solo uso por email.
3. **Explicaciones de DeepSeek** (endpoint `/explain`).

Secrets configurados en el Worker (Cloudflare → Workers & Pages →
`bolets-hallazgos` → Settings → Variables and Secrets):
- `GITHUB_TOKEN` — Contents read/write solo sobre `bolets-catalunya`. Caduca el 24/11/2026.
- `SESSION_SECRET` — texto aleatorio largo, firma las sesiones y los códigos de acceso.
- `AUTHORIZED_EMAILS` — lista de emails con acceso, separados por comas.
- `BREVO_API_KEY` — key de la API de Brevo, usada para enviar los códigos de acceso por email.
- `SENDER_EMAIL` — el email verificado en Brevo desde el que se envían los códigos.
- `DEEPSEEK_API_KEY` — key de la API de DeepSeek. El Worker usa el modelo `deepseek-flash` (V4.1 Flash). El identificador antiguo `deepseek-v4-flash` se retiró el 10/09/2026 y solo se enruta temporalmente al nuevo; no hay que usarlo.
- `LIMITS` *(opcional pero recomendado)* — un «KV namespace» de Cloudflare (gratuito) enlazado al Worker con ese nombre. Activa los límites de intentos (ver «Seguridad»). Sin él, el Worker funciona igual pero sin límites.

Secrets configurados en GitHub Actions (repositorio → Settings → Secrets
and variables → Actions):
- `AEMET_API_KEY` — caduca cada 3 meses (próxima: 25/11/2026).
- `METEOCAT_API_KEY` — caduca 31/08/2027.

**Seguridad del Worker** — nunca confía en lo que le manda el navegador:
rango geográfico real de Catalunya, lista blanca de especies/árboles,
límites de longitud, formato de fecha válido, límite de tamaño de payload
(10KB), retraso tras un intento fallido, comparación de códigos y firmas en
tiempo constante, y (con el KV `LIMITS` enlazado) límites reales de uso:
5 códigos/hora por email y 10/hora por IP; bloqueo de 15 min tras 5 intentos
fallidos por email o 15 por IP; tope de 150 explicaciones DeepSeek por día.
Limitaciones asumidas: el KV no es atómico (dos peticiones simultáneas pueden
pasarse un intento del límite); si alguien conoce tu email puede bloquearte el
acceso 15 min a base de fallos (la sesión dura 30 días, así que casi no se
nota); y el repositorio es público, así que `data/hallazgos.json` (las
coordenadas exactas de tus salidas) es visible para cualquiera.

**IMPORTANTE — `worker/index.js` no se despliega solo:** el archivo en
GitHub es solo la copia de referencia. Para que un cambio tenga efecto de
verdad, hay que pegarlo directamente en Cloudflare (Edit code → Deploy).

### Control de acceso

La web pide un email antes de mostrar nada:
1. El Worker comprueba si el email está en `AUTHORIZED_EMAILS`.
2. Si está autorizado, genera un código de 6 dígitos **uniforme**
   (000000-999999; antes salía de los dígitos de un Base64 y en ~31 % de los
   casos se rellenaba con ceros, ≈ 16,8 bits de entropía frente a 19,9) válido
   10-20 minutos, y lo envía por email vía Brevo.
3. El navegador recibe un token de sesión firmado (30 días).

El código no se guarda en ningún sitio: se deriva con HMAC (email +
ventana de 10 min + `SESSION_SECRET`) y se acepta el de la ventana actual y el
de la anterior. Lo que protege contra la fuerza bruta no es el código sino el
**límite de intentos** del KV `LIMITS` (ver «Seguridad del Worker»).

- **Dar acceso**: añadir el email a `AUTHORIZED_EMAILS`.
- **Quitar acceso**: quitar el email de esa lista.
- **Revocar todo de golpe**: cambiar `SESSION_SECRET`.

### Registro de salidas propias

Se marca en el mapa el punto exacto y se elige el resultado: 🍄 mucho/poco
(especie obligatoria), 🔍 busqué y no encontré nada (especie opcional), o
🚶 no llegué a buscar bien (no se guarda). Las salidas **no se muestran en
el mapa** y **no se pueden borrar nunca** una vez registradas (decisión
deliberada, protege el historial de datos reales).

### App Android (APK)

APK real generado con [Capacitor](https://capacitorjs.com/), que carga la
web en vivo (`server.url` en `capacitor.config.json`) — los cambios en la
web se reflejan solos, sin regenerar el APK. Para generar uno nuevo:
`npx cap sync android` → `npx cap open android` → Android Studio → Build →
Generate APK(s).

### Comparativa con trobarbolets.cat (15/10/2026)

Proyecto aficionado parecido (no oficial, sin autor nombrado). Mapa diario de
«probabilidad» por municipio con dos fases: reglas de época, altitud y sequía y
después *gradient boosting* entrenado con observaciones GBIF e iNaturalist; 29
variables (lluvia acumulada de 3 a 30 días, días desde la última lluvia con
umbrales de 2, 5 y 10 mm, temperatura, altitud, hábitat CORINE) y ~240
estaciones oficiales interpoladas. Declara AUC 0,956 en validación cruzada pero
solo ~0,81 en años no vistos (cifras suyas, no verificadas por nosotros).
Aprendido de ahí: (1) una validación cruzada normal engaña, la validación debe
hacerse **por años** (entrenar con ≤2020, evaluar con 2021 en adelante) y
**por zonas**; (2) sus meses de mayor actividad coinciden con los de nuestro
GBIF (cep, ou de reig, trompeta, rovelló, fredolic, llengua de bou; el camagroc
difiere un mes); (3) separan *cep fosc* (72-1.405 m, sep-oct), *cep* (679-2.451 m)
y *cep d'estiu*, lo que apoya la duda M4; (4) casi no registran pinetell (1
observación, todo va a «rovelló»), así que con datos públicos rovelló y pinetell
no se pueden separar para validar (duda M5). Nuestro punto distinto: no
presentamos la puntuación como probabilidad.

### Comparativa con bolets.app (15/10/2026)

Otra web aficionada (se llama a sí misma «Bolets Atles»). Lo que declara —son
cifras suyas, **no verificadas por nosotros**—: un índice 0-100 explícitamente
«no una probabilidad», con bandas (0-19 muy bajo, 20-49 bajo, 50-69 moderado,
70-79 alto, 80-100 muy alto) y un estado aparte «sin datos»; reconocimiento de
setas por foto (438 especies, 98 % de acierto entre las 3 primeras, 0,8 % de
errores «mortal tomada por comestible») con un modelo de 31 MB que funciona sin
conexión; 62 fichas de especie, una página de 14 confusiones peligrosas, un método
de campo en 7 pasos; mapa de hallazgos públicos a 10 × 10 km; y un aviso claro de
que el contenido tiene «revisión editorial, sin revisión micológica
independiente». Usa pH de SoilGrids, temperaturas de la XEMA y los modelos
AROME/ECMWF.

**Qué hemos cogido:**
- La frase «la puntuación es un índice, no una probabilidad» (ahora en la leyenda de la web) y recordar que la app dice *dónde mirar*, no *qué se puede comer*.
- Una **guía de identificación** (`web/guia.html`): las confusiones peligrosas primero, el método de campo en 7 pasos con esporada, teléfonos de urgencias y mitos desmentidos. Con el mismo aviso honesto: texto de IA, sin revisión micológica.
- **Funcionamiento sin cobertura** (`web/sw.js`).

**Reconocimiento por foto:** al principio no se hizo a propósito (una IA de fotos
que se equivoque con una *Amanita phalloides* mata, y no podemos validar ni medir
su error). El 15/10/2026 Sergio pidió expresamente poder identificar con la cámara
y se hizo **como sugerencia, no como veredicto**. Después pidió 3 fotos (arriba,
debajo, pie) y un porcentaje por ficha; se rehízo así: la IA **solo lee rasgos**
(opciones cerradas) y es la propia guía la que los compara con cada ficha y calcula
una **coincidencia (%)** que se puede explicar (ver «Guía de identificación»). Por
debajo sigue siendo un modelo de visión general de Cloudflare, no un modelo
entrenado con setas, y **su acierto no está medido**. El porcentaje **no es una
probabilidad**: un modelo general no da probabilidades calibradas, y por eso no se
le pide un «73 %» inventado.

**Ideas apuntadas (sin hacer):** bandas de interpretación y un estado «sin datos»
cuando faltan fuentes; pH real del suelo (SoilGrids) para afinar las especies
acidófilas; un mapa público de hallazgos a baja resolución (10 × 10 km rompería
nuestro emparejamiento a 3,5 km, así que solo serviría para mostrar, no para
validar). Esto último enlaza con la decisión pendiente de **privacidad de las
coordenadas**: los hallazgos exactos están hoy en el repositorio público y en su
historial.

### Guía de identificación y modo sin conexión

- `web/guia.html` se **genera** (`python3 tools/generar_guia.py`) con el texto de `tools/guia_datos.py`. Tiene 313 fichas **desplegables** (se toca la cabecera: miniatura, nombre y nombre científico): 112 «peligrosas o con las que se confunden» y 201 de setas para comparar (las 50 de siempre —23 y 27— más las 263 de la ampliación del 16/10/2026, ver más abajo). Las 30 primeras (16 peligrosas y 14 buscadas) son las del 15/10/2026 por la mañana; **el mismo día se añadieron 20 más**, elegidas por ser típicas de Catalunya (listas de la Comunidad de Madrid y de La Rioja, Enciclopèdia Catalana, bolets.com y recuento de observaciones en GBIF): 7 peligrosas o no comestibles (hifoloma de láminas verdes, falso níscalo *L. chrysorrheus*, seta enrollada, champiñón amarilleante, seta de los caballeros, coprino entintado, rúsula emética) y 13 buscadas (vinosa, camperol, pie azul, alzinoi, molleric, barbuda, seta de ostra, carbonera, molinera, capuchina, platera, seta de chopo, marçot). Las que no están en el mapa del predictor lo dicen («no está en el mapa»).
- Cada ficha empieza por *lo que tiene que cumplir* y *lo que la descarta*, y lista las confusiones con su gravedad. Los **nombres científicos** son la referencia; se evitaron nombres comunes de los que no hay certeza.
- **Secciones quitadas a petición de Sergio (15/10/2026):** «Léelo antes de nada» y «Si has comido una seta y tienes dudas» (con los teléfonos de urgencias). Se mantienen la franja roja de una línea de arriba, el método de campo en 7 pasos y los mitos (ahora plegados al final) y el aviso de «sin revisión micológica independiente» en el pie.
- Los `id` de las fichas coinciden con los ids de especie del predictor, así que la ventana de cada zona enlaza con `guia.html#<id>` y el enlace abre la ficha (también con los alias `#cepfosc`, `#cepestiu`, `#pinetell`). Una prueba (`tests/test_model.py`) falla si se añade una especie sin ficha o sin foto asignada.
- **Fotos:** vienen de **Wikimedia Commons** (vía Wikipedia) y solo se aceptan licencias libres (CC BY, CC BY-SA, CC0, dominio público; nada con NC ni ND). Debajo de cada foto se ve autor y licencia con enlace, como exigen esas licencias. `tools/fotos_datos.py` dice qué nombre científico se busca para cada ficha (y `FORZAR` permite fijar un archivo concreto si la foto automática no es buena); `tools/descargar_fotos.py` la descarga (miniaturas de 500 px) y se ejecuta desde el workflow `descargar_fotos.yml`, porque el entorno de desarrollo no tiene acceso a esas webs. Las fotos ya descargadas no se vuelven a buscar (solo los huecos de `FORZAR` o todos con `--todo`), y el informe (`web/fotos/informe.txt`) marca con `[REVISAR]` las que tienen un nombre de archivo que no menciona la especie. Si no hay fotos, la guía funciona igual sin ellas.
- **Identificar con fotos (3 huecos + panel de rasgos):** hay tres huecos —1 arriba, 2 debajo del sombrero, 3 pie y base— y cada uno tiene botón de cámara y de galería. El navegador reduce cada foto a 800 px y la envía **sola** al Worker (`POST /identify` con `{image, parte}`, exige sesión); el Worker se la pasa al modelo de visión de **Cloudflare Workers AI** (desde el 17/10/2026 `@cf/google/gemma-4-26b-a4b-it`, elegido con el banco de pruebas, con `@cf/meta/llama-3.2-11b-vision-instruct` de reserva si falla o contesta algo ilegible; hasta entonces era Llama 3.2) y le pide un JSON con **solo rasgos** de esa parte, eligiendo entre opciones cerradas (`IDENT_VOCAB`, generado con `python3 tools/generar_guia.py --vocab`) o `null` si no se ve. El modelo **no dice qué seta es**. El resultado se **sanea**: solo los rasgos de la parte pedida y solo valores del vocabulario. Se hace una consulta por foto (el modelo gratuito se usa con una imagen por consulta; no se ha probado con varias a la vez). **Lectura v2 (16/10/2026):** Sergio probó la guía con tres fotos de un boleto (un *Boletus edulis*, fotos buenas) y la IA no acertó: leyó 3, 2 y 0 rasgos y, además, la guía decía «hay dos fotos mal». Causas encontradas: (1) el prompt iba en **castellano** y la ficha de Llama 3.2 Vision dice que con fotos «English is the only language supported»; (2) a cada foto solo se le pedían los rasgos de **su** hueco, así que una foto de la seta entera en el hueco del pie se quedaba sin leer; (3) se le preguntaba qué parte enseñaba la foto, la IA gratuita se equivocaba (en esa prueba llamó «sombrero» a las de debajo y del pie) y la guía se lo enseñaba a la persona como «foto mal». Ahora: el prompt va en **inglés** (`IDENT_EN`, con la palabra que debe devolver el modelo y su descripción; el Worker las traduce a los ids de la guía, y también acepta los ids y los textos en castellano), se piden **los 9 rasgos de foto en cada petición** («lo que se vea con claridad, sea de la parte que sea; null si no») y **ya no se pregunta qué parte enseña la foto** (el hueco solo es una pista en el prompt). En la guía, `recalcularIA()` junta lo leído en las tres fotos: cada rasgo sale de la foto de **su** hueco; si esa no lo enseña, se mira en las otras y solo se acepta si todas las que lo leen **coinciden**; lo que la persona pone **o deja vacío a propósito** no se toca, y al quitar una foto se recalcula. Ya no hay aviso de «foto mal». **No está medido todavía si esto acierta más**: para eso está el banco de pruebas (siguiente apartado).
- **Panel de rasgos:** 17 desplegables en 4 grupos (sombrero, debajo, pie, y «lo que no sale en una foto»: tamaño, carne al cortarla, látex, interior, cómo crecen, dónde crece, olor y esporada, que rellena la persona). Lo que lee la IA lleva la marca «IA»; lo que pone la persona **no lo pisa la IA**. Sirve también **sin fotos y sin cobertura**.
- **Coincidencia (%):** `tools/puntuar.js` compara los rasgos con la «firma» de cada ficha (`tools/rasgos_datos.py`, sacada solo del texto de las fichas: «cumple», «descarta», «confunde»). Cada rasgo pesa 1, o 3 si es **clave** (p. ej. poros o láminas). **Coincidencia = peso de los rasgos que encajan ÷ peso del retrato de la ficha** (con un mínimo de 10, para que una ficha con pocos rasgos no llegue a 100 % con dos). Un rasgo sin indicar no suma ni descarta: se lista como «sin comprobar aún». Un rasgo clave en contra **descarta** la ficha (no sale en la lista). Una **peligrosa** que falla en algún rasgo clave pero por lo demás encaja (≥ 55 %) sale aparte como «peligrosa con la que aún no puedes descartar el parecido» (salvo láminas contra poros, que no se confunden). Entran en la lista las fichas con ≥ 50 % y ≥ 3 rasgos que encajen; hace falta indicar ≥ 3 rasgos; a igualdad, la peligrosa va antes. Cada tarjeta muestra lo que encaja (✔), lo que no (✖), lo que falta, y los «Descártala si ves…»/«Con qué se confunde» de su ficha. Estos umbrales son **decisiones de diseño, no están medidos**. Además, si se marca **«bolsa» (volva)** en la base del pie, las fichas que no son amanitas cuentan como rasgo clave en contra aunque su ficha no nombre la base (`SOLO_EN` en `tools/rasgos_datos.py`): una ficha que no dice nada de un rasgo lo dejaba «sin comprobar» y se colaba con un 50 %. La regla es de **esta guía** (entre sus 50 fichas solo las amanitas tienen bolsa), no una afirmación general: hay setas con volva fuera de *Amanita*. No cambia ningún porcentaje; una peligrosa que por lo demás encaje ≥ 55 % sigue saliendo como «dudosa». La pantalla dice siempre que la coincidencia **no es la probabilidad** de que sea esa seta ni que se pueda comer, y que la guía solo tiene 50 fichas (una seta que no esté en ellas no sale).
- **Coste:** **0 €** en el plan gratuito de Workers AI (10.000 «neuronas» al día según su tabla de precios; al agotarse, la llamada falla y no se cobra). El Worker añade un tope propio de **120 fotos al día** (cada foto cuenta 1: unas 40 identificaciones de 3 fotos). Requiere el *binding* **Workers AI** con el nombre `AI` (Settings → Bindings); sin él, `/identify` responde que no está activada. El Worker acepta aquí cuerpos de hasta 1,6 MB; el resto de rutas siguen en 10 KB. Las pruebas del Worker usan una IA simulada (desde el entorno de desarrollo no hay acceso a Cloudflare). Los modelos sí se han medido por la API REST de Cloudflare con el banco de pruebas (ver más abajo), pero el Worker con el *binding* `AI` y Gemma 4 **no se ha probado en vivo** hasta que Sergio lo pegue en Cloudflare. El acierto de la lectura con fotos de móvil de setas catalanas **no está medido**.
- **Nombres en tres idiomas (15/10/2026):** cada ficha lleva un bloque **Latín / Català / Castellano** y debajo las fuentes de esos nombres. Los datos están en `tools/nombres_datos.py`: el **nombre científico es la referencia**; un nombre popular solo se escribe si aparece en una fuente consultada (Enciclopèdia Catalana, bolets.com / boletaires.cat, Canal Salut, 3Cat, Institut Català d'Història Natural, listas de la Comunidad de Madrid y del Gobierno de La Rioja, Wikipedia en español) y se anota el código de esa fuente; si ninguna lo da, se muestra «—» (no se inventa). El buscador de la guía encuentra por cualquiera de los tres idiomas. Los nombres que usa el predictor (por ejemplo «Escarlet», «Cep fosc», «Cep d'estiu») **no se han cambiado**; las fichas lo explican en una nota. Recuento y fuentes en `NOMBRES-FUENTES.md` y `FUENTES-REVISADAS.md` (§7). Los nombres populares **varían según la zona** y no son oficiales: fíate del nombre científico.
- **Ampliación de la guía a 313 fichas (16/10/2026):** Sergio pidió poder comparar con unas 300 especies, con «fichas completas» (el mismo texto que las de siempre, foto y nombres en tres idiomas) y «todas de golpe». Se añadieron **263 fichas** a las 50 de siempre: **174 «para comparar»** (setas buscadas o sin riesgo propio) y **89 «tóxicas o que no se recomiendan»** (45 con aviso de peligro —43 tóxicas y 2 muy tóxicas— y 44 no comestibles). Alguna de las 50 de siempre agrupa varias especies (por ejemplo «ceps» o «colmenilles»), así que hay algo más de especies que de fichas. **Cómo está hecho:** las 263 especies viven en **un solo archivo**, `tools/especies_extra.py` (una entrada por especie: nombre científico, texto, rasgos y nombres); `tools/guia_ampliada.py` lo convierte en lo que ya leían `guia_datos.py`, `rasgos_datos.py`, `nombres_datos.py` y `fotos_datos.py` (esos cuatro lo importan al final y **añaden** las fichas nuevas; las 50 de siempre no se tocan: sus tablas siguen intactas como `PELIGROSAS_BASE`, `FICHAS_BASE` y `FIRMAS_BASE`). Los nombres en castellano salen de `tools/nombres_es_wikipedia.py`. **Fuentes:** el texto de cada ficha lo redactó una IA a partir de la página de **Wikipedia en inglés** de la especie (consultada el 16/10/2026); el nombre en catalán y el grado «a refusar»/«tòxic» salen de la tabla de la **Enciclopèdia Catalana**; el nombre en castellano, solo del artículo de **es.wikipedia** de esa especie (74 de las 263 lo tienen: si no hay artículo o el artículo no da un nombre común, se escribe «—», nada se inventa; 110 tienen nombre en catalán). **Reglas del texto:** (1) la guía nunca dice «se puede comer»: si una fuente habla de comestibilidad, la frase empieza atribuyéndola («Wikipedia dice…», «la Enciclopèdia Catalana la pone…»); (2) **no hay instrucciones de cocinado, remojo ni «prueba una porción»** (se quitaron 24 pasajes de ese tipo que venían de las fuentes: escaldar, hervir, remojar, freír, «probar una porción»...); (3) una especie va a «tóxicas o que no se recomiendan» si la fuente dice que es tóxica, que no se recomienda o que es no comestible con riesgo, y a «para comparar» en el resto, con el riesgo (bajo/medio/alto) sacado de las confusiones peligrosas que la propia fuente nombra; (4) si la fuente no dice un rasgo (color de las láminas, esporada...), la ficha no lo dice. **Qué se descartó:** de una lista inicial de 319 candidatas, **79 no tienen ficha** (la página de en.wikipedia era escueta, no existía o redirigía a otra especie, o se quedaron fuera al cerrar la lista; la lista está en `FUENTES-REVISADAS.md` §9). **Cambios en la página:** (a) las miniaturas son perezosas y las fotos grandes se piden **al abrir cada ficha** (la página pesa unos 885 KB, unos 165 KB con gzip); (b) las especies nuevas van en subsecciones plegadas («Más especies tóxicas o que no se recomiendan» y «Más especies para comparar») con su índice, que se ocultan solas al buscar; (c) tras identificar se enseñan las **5 primeras** candidatas y, aparte, hasta 6 **peligrosas que también encajan** con menos coincidencia (una peligrosa que encaja nunca se queda escondida en la lista larga); (d) la regla «bolsa» (volva) ya no es «solo amanitas»: en la guía tienen bolsa **17 fichas** —las 5 amanitas de siempre, 7 amanitas más, *Phallus impudicus*, *Mutinus caninus*, *Clathrus ruber*, *Volvariella bombycina* y *Volvopluteus gloiocephalus*— y el aviso lo dice con esas palabras; (e) botón **«Guardar todas las fotos en el móvil»** (al final de la guía, solo si hay fotos y service worker). **Lo que NO cambió:** los parámetros de la coincidencia (3 rasgos para empezar, 2 comparados, 3 que encajen, 50 %, 55 % para las dudosas, peso mínimo 10) ni el Worker (el vocabulario de rasgos es el mismo: **no hay que pegar de nuevo `worker/index.js`**). **Comprobado:** para un ejemplar «típico» de cada ficha (construido desde su propia firma) la ficha sale la primera en 298 de 313 (en 49 de las 50 de siempre; la clitocibe, que ya se confundía por diseño con el cama-sec, sale la segunda) y en las demás, entre las primeras (la peor, *Legaliana badia*, la séptima); ninguna ficha de las 50 de siempre sale peor que antes. 32 de las 59 confusiones peligrosas que las fichas nuevas documentan aparecen como candidata o dudosa para un ejemplar típico; las demás tienen rasgos distintos a propósito. En Chromium con CPU 6 veces más lenta, buscar o filtrar las 313 fichas tarda menos de 0,2 s. **Límites:** el texto lo ha redactado una IA a partir de Wikipedia, que puede ser incorrecta o incompleta, **sin revisión de un micólogo**; no se contrastó cada frase con su fuente; **las fotos de las 263 fichas nuevas se descargan automáticamente (workflow) y no se han revisado a ojo**; el acierto de la lectura de rasgos con setas catalanas sigue sin medirse; no probado en un móvil real. Pruebas nuevas: `tests/test_ampliacion.py` (25 comprobaciones: estructura, que ninguna frase afirme comestibilidad sin fuente, sin instrucciones de cocinado, retratos válidos, nombres y avisos de la página).
- **Ampliar la guía:** una especie más de las 263 de la ampliación solo necesita **una entrada en `tools/especies_extra.py`** (copiar una parecida; la ficha, la firma, los nombres y la foto se derivan solos y `tests/test_ampliacion.py` la revisa). Para una ficha de las 50 de siempre, una seta nueva necesita (1) su ficha en `tools/guia_datos.py`, (2) su firma en `tools/rasgos_datos.py` (`FIRMAS`, usando solo lo que dice la ficha), (3) su hueco de foto en `tools/fotos_datos.py`, (4) sus nombres en `tools/nombres_datos.py` (con el código de la fuente); luego `python3 tools/generar_guia.py`, pegar el nuevo `worker/index.js` solo si cambió el vocabulario de rasgos (`--vocab`), y lanzar el workflow de fotos. `tests/test_model.py` falla si una ficha no tiene firma, foto o nombres, o si un nombre cita una fuente que no existe. **Vocabulario nuevo del 15/10/2026:** «violeta» (sombrero, láminas, pie), «amarillea» (carne al cortarla y látex), «fenol» (olor) y «chocolate»/«negra» (esporada); «violeta» es un valor que lee la IA, así que cambia `IDENT_VOCAB` del Worker y **hay que pegar de nuevo `worker/index.js`**.
- **Sin conexión:** `sw.js` (caché `bolets-offline-v2`) guarda `guia.html`, los créditos y las fotos, la pantalla de la app, el manifiesto y un icono. Desde la ampliación a 313 fichas las fotos ya no se piden todas al abrir la página (miniaturas perezosas, fotos grandes al abrir la ficha), así que **sin cobertura solo se ven las fotos de lo que se abrió antes con conexión**; el botón **«Guardar todas las fotos en el móvil»** (al final de la guía) las pide todas para que el service worker las guarde (son muchas fotos: mejor con wifi; lo probado en Chromium es que tras pulsarlo quedan todas en la caché y la guía abre sin red). Las páginas van red primero (4 s de espera) con la copia como plan B; las fotos salen de la copia y se refrescan en segundo plano. No guarda datos del mapa, así que no puede enseñar una puntuación antigua. Comprobado en Chromium con el servidor apagado de verdad (guía + 37 fotos); **no probado aún en un móvil real**: hay que abrir la guía una vez con cobertura y luego probar en modo avión. La identificación por foto necesita cobertura.
- **Límites reconocidos:** texto redactado por una IA y **sin revisión de un micólogo** (conviene que la revise una sociedad micológica antes de difundirla); las fotos se buscan automáticamente (imagen principal del artículo de Wikipedia de cada especie) y el 15/10/2026 se **revisaron a ojo las 37 primeras**: 34 eran la seta correcta y 3 no (cep fosc con una foto de *B. pinophilus*, cep d'estiu con un archivo de nombre genérico y lactario torminoso con una foto de *Lactarius mairei*), que se corrigieron fijando el archivo con `FORZAR`. La revisión la hizo una IA mirando las fotos, **no un micólogo**; si ves una foto que no es, dímelo y se fija otra; Las **21 fotos de las 20 fichas nuevas** (el molleric lleva 2) se descargaron con el workflow el 15/10/2026 y se **revisaron a ojo** (otra vez una IA mirándolas, **no un micólogo**): las 21 parecen la especie de su ficha y no hizo falta `FORZAR`. Con una sola foto no se puede asegurar la especie en parejas como falso níscalo/níscalo (el informe avisó de que el archivo de *L. chrysorrheus* no lleva el nombre completo; su nombre abreviado sí coincide) o molinera/clitocibes blancas. Los textos de las 20 fichas nuevas están redactados por una IA a partir de las fuentes consultadas (fichas de especies de Wikipedia, listas oficiales, Enciclopèdia Catalana, bolets.com), **sin revisión de un micólogo**; el recuento de observaciones de GBIF solo indica esfuerzo de observación, no abundancia. Algunas fichas con pocos rasgos (marçot, carbonera) dan coincidencias holgadas por diseño. No cubre todas las setas (Catalunya tiene más de 2.000 especies): las 313 fichas nombran algo más de 320 especies (alguna ficha agrupa dos o más), y una seta que no esté entre ellas puede salir con una coincidencia alta con otra ficha parecida. **Las 263 fichas de la ampliación del 16/10/2026** las ha redactado una IA a partir de Wikipedia (en inglés y, para los nombres, en español) y la Enciclopèdia Catalana, **sin revisión de un micólogo y sin contrastar cada frase con su fuente**, y **sus fotos se descargan automáticamente y no se han revisado a ojo**. Si ves una foto que no es la seta, dímelo y se fija otra con `FORZAR`.

### Banco de pruebas de la lectura de fotos (16/10/2026)

**Para qué:** hasta ahora la lectura de fotos con IA no estaba medida; solo se había probado a mano con fotos reales de Sergio (y fallaba). El banco (`tools/banco_ia.mjs`, workflow **«Probar lectura de fotos con IA»**, solo a mano) mide, con fotos de la propia guía de las que se **sabe qué seta son**, cuatro configuraciones: `llama32_v1` (lo que hacía la guía antes: Llama 3.2 11B, prompt en castellano, un hueco por llamada), `llama32_v2` (el prompt nuevo con el mismo modelo), `scout_v2` (Llama 4 Scout) y `gemma4_v2` (Gemma 4 26B A4B, modelo de abril de 2026 que Cloudflare recomienda para visión). Gemma 3 12B quedó fuera: Cloudflare lo dio de baja el 30/05/2026.

**Qué mide:** (1) qué parte de los rasgos que lee encaja con lo que dice la ficha de esa seta, y (2) lo importante: pasando esos rasgos por la comparación **real** de la guía (`tools/puntuar.js`, mismos umbrales de producción), en qué porcentaje de fotos la ficha correcta sale **primera / entre las 5 primeras / entre las 10 primeras**. Referencia: con los rasgos perfectos de cada ficha sale primera en 298 de 313 casos. Los prompts y el lector de respuestas son **los mismos que usa el Worker** (se extraen de `worker/index.js`); lo de «v1» es una copia congelada del comportamiento anterior.

**Cómo funciona:** llama a la API REST de Cloudflare con dos secretos del repositorio (`CF_ACCOUNT_ID`, `CF_API_TOKEN`; token de plantilla «Workers AI»), primero hace un **sondeo** (qué forma de pasar la foto acepta cada modelo: Cloudflare no lo documenta igual en todos) y luego mide foto a foto repartiendo entre configuraciones. Es **reanudable** (`tools/banco/resultados.jsonl`, no repite), tiene **tope de neuronas** (por defecto 6.000 de las 10.000 gratuitas diarias, que se reinician a las 00:00 UTC) y se para si Cloudflare dice que el cupo se ha acabado. Escribe `tools/banco/INFORME.md` (tablas y detalle foto a foto), `resumen.json`, `sondeo.json` y `formato.json`. `--solo-informe` rehace el informe sin gastar; `--reparsear` vuelve a leer los textos guardados con el lector actual (por si se ajusta el lector); `--simular` ejecuta todo el circuito sin red (así se probó aquí).

**Fotos propias:** se pueden subir a `tools/banco/mis_fotos/` con el nombre `<ficha>__<sombrero|debajo|pie>.jpg` (p. ej. `cep__pie.jpg`); el workflow las reduce a 800 px (como la guía) y las mide aparte.

**Límites que conviene recordar:** las fotos de referencia son de Wikimedia Commons (más limpias que las de un móvil en el monte), la «verdad» de cada foto es lo que dice la ficha (hay ejemplares que no se parecen al retrato típico) y la muestra es pequeña (30 fotos por defecto): sirve para **comparar configuraciones entre sí**, no para prometer un porcentaje de acierto en el monte. Las neuronas se calculan con las cifras de la tabla de precios de Cloudflare (las de Gemma 4 son una estimación a partir de su precio en dólares).

### Resultado del banco de pruebas (ejecutado el 16/10/2026)

Ejecución #1 del workflow, con los valores por defecto (30 fotos de la guía, tope de 6.000 neuronas): gastó 3.325 neuronas (cifra estimada por el propio banco con la tabla de precios; Cloudflare puede contar algo distinto). Informe completo y foto a foto en `tools/banco/INFORME.md`; lo que dijo el sondeo de cada modelo, en `tools/banco/sondeo.json` y `formato.json`.

| Configuración | Rasgos leídos por foto (de 9) | Rasgos leídos que encajan con la ficha | Ficha correcta primera | Entre las 5 primeras | Entre las 10 primeras | Neuronas por foto |
|---|---|---|---|---|---|---|
| `llama32_v1` (lo de antes) | 4,7 | 66 % | 1 de 30 | 2 de 30 | 3 de 30 | 40 |
| `llama32_v2` | 8,6 | 65 % | 0 de 30 | 3 de 30 | 5 de 30 | 17 |
| `scout_v2` (Llama 4 Scout) | 6,9 | 74 % | 1 de 30 | 4 de 30 | 5 de 30 | 41 |
| `gemma4_v2` (Gemma 4 26B) | 7,4 | 74 % | **4 de 30** | **5 de 30** | **6 de 30** | 12 (estimada) |

(Los puestos salen de repetir la comparación con los rasgos guardados, `puntuar.js` con los umbrales de producción; el informe redondea a porcentajes y marca «Top 1 13 %, Top 5 17 %, Top 10 20 %» para Gemma 4.)

**Lo que se aprende, con las cautelas debidas (30 fotos son pocas: una diferencia de una o dos fotos no demuestra nada):**
- **Ninguna configuración identifica por sí sola con una foto.** En la mejor, la ficha correcta sale entre las 5 primeras en 5 de 30 fotos. Es coherente con lo que vio Sergio.
- **El techo de leer solo rasgos de foto no es alto.** Con los 9 rasgos de foto *perfectos* de cada ficha (283 fichas que tienen ≥ 3 de esos rasgos), la ficha correcta sale primera en 144 (51 %), entre las 5 primeras en 242 (85 %) y entre las 10 primeras en 264 (93 %). Los 298 de 313 de la referencia usan además lo que no sale en una foto (olor, carne al cortar, hábitat…). Por eso la guía pide completar a mano lo que la foto no enseña.
- **El problema está en la lectura**: ~65-74 % de los rasgos leídos encajan con la ficha, y en 13-19 de 30 fotos algún rasgo mal leído **descarta** la ficha correcta.
- **Gemma 4 fue la mejor en todo lo agregado y la más barata**; Llama 3.2 con el prompt nuevo fue la peor leyendo los rasgos (65 % de acierto) y la que menos `null` devuelve. Con 30 fotos la ventaja es pequeña; se eligió porque no empeora en nada, es más barata y Cloudflare la recomienda para visión.
- **Los tres modelos nuevos contestan «sin anillo / base normal / pie liso» casi siempre** que pueden: Llama 3.2 en 84 de 84 lecturas del pie, Scout en 56 de 62 y Gemma 4 en 64 de 71 (de 90 huecos posibles cada uno). Como en una foto de la seta entera el pie casi nunca se ve bien, eso no es una lectura fiable: de ahí el filtro de la guía que se describe abajo.
- **Nadie lee la superficie ni la base del pie** (acierto 0 % en `p_super` y `p_base` en las fichas que los llevan, muestras de 3 a 5 fotos): justo lo que separa un cep (red blanca) de un *Leccinum* (puntos oscuros).
- Probar **otra forma de puntuar** (contar solo lo comparado, o contar a medias lo que falta) con las mismas lecturas **no mejoró**; se deja la actual.

**Decisiones tomadas:** (1) el Worker pasa a Gemma 4 (`IDENT_MODEL`), con Llama 3.2 de reserva (`IDENT_MODEL_RESERVA`) cuando falla por un error normal o contesta algo ilegible (no cuando se acaba el cupo, que es de toda la cuenta); forma de pasar la foto y parámetros según el sondeo: Gemma 4 con la imagen dentro del mensaje (`image_url`) y el «pensar» apagado (`chat_template_kwargs.enable_thinking=false`), Llama 3.2 con el campo `image`. (2) En la guía, **«sin anillo», «base normal» y «pie liso» solo se aceptan de la foto del pie**: de las otras dos fotos no, porque «no se ve» no es «no está» y un «sin anillo» inventado descarta una amanita. Quitando esas tres lecturas de las del banco (como si vinieran de una foto que no es la del pie), la ficha correcta pasa a salir primera en una foto más con Llama 3.2 y con Scout, y con Gemma 4 no cambia nada: una mejora pequeña; se mantiene sobre todo por lógica. **No se cambió** ningún umbral de producción. (3) El Worker añade al resultado de `/identify` el campo `modelo` y la guía lo enseña en el mensaje del hueco («leído con Gemma 4» o «leído con Llama 3.2, el modelo de reserva»), para ver enseguida si la reserva está entrando en juego.

**Siguiente prueba pendiente:** medir con las **fotos reales de móvil de Sergio** (subirlas a `tools/banco/mis_fotos/`, p. ej. `cep__sombrero.jpg`, `cep__debajo.jpg`, `cep__pie.jpg`), que son las que de verdad importan.

### Primera prueba con Gemma 4 en vivo y tres arreglos de la guía (17/10/2026)

Sergio probó el Worker con Gemma 4 y sus tres fotos de un *Boletus edulis*: las tres dijeron «leído con Gemma 4» y la IA leyó 3, 4 y 8 rasgos (antes 3, 2 y 0), incluido el pie «con red». Con solo la lectura de la IA el cep salía **cuarto** (67 %, los 6 rasgos comparados encajaban); al completar a mano lo que la foto no enseña, el Leccinum scabrum salía por encima (91 % frente a 87 %). Se reprodujo con los mismos datos: ese 87/91 sale al marcar, además, «lisa» en la superficie del pie. **Causas, comprobadas con `puntuar.js`:** (1) la IA había leído bien la red del pie y la persona la cambió a «lisa» (de lejos el pie del cep parece liso: la red es muy fina y clara y se ve sobre todo arriba); (2) el % es el peso de lo que encaja entre el peso de **todo** el retrato de la ficha, y la del cep tiene rasgos que ninguna foto enseña (carne al cortarla, olor, hábitat) mientras que la del *Leccinum* tiene menos «sin comprobar»; «lisa» y «en blanco» dan **el mismo** porcentaje (un rasgo que no encaja no resta, solo no suma). Con la red leída por la IA y lo demás igual, el cep sale primero (93 % frente a 91 %).

**Otras formas de ordenar** (puntos que encajan menos puntos en contra, restar el doble, solo puntos que encajan) ponen el cep primero en este caso, pero con los mismos datos del banco **no son mejores en general**: con rasgos perfectos las dos primeras suben el «entre las 5 primeras» (242 → 261-263 de 283) pero bajan el «primera» (144 → 133-139), la tercera baja ambos (255 y 116), y con un rasgo mal leído las tres empeoran el «entre las 5 primeras» (135 → 104-130 de 283). **No se cambió la forma de puntuar.**

**Lo que sí se cambió (solo `tools/generar_guia.py` y la guía generada; el Worker no cambia):**
- **Botón «atrás»:** los enlaces de los resultados de «Identificar con fotos» (los de dentro de `#idres`, p. ej. «Abrir la ficha con fotos») ahora **añaden** una entrada al historial; antes la reemplazaban y «atrás» salía al predictor y se perdía la identificación. Como solo cambia el `#` de la URL, la página no se recarga: las fotos, los rasgos y la lista siguen como estaban, y se recupera la posición de la pantalla. Los demás enlaces internos (el índice, `#cep`…) siguen reemplazando la entrada, como antes. Probado en Chromium (no en un móvil real).
- **«Hasta qué % subiría»:** debajo de «Sin comprobar aún», cada tarjeta dice hasta qué porcentaje subiría la coincidencia si todo lo que falta por comprobar encajase (`techoPct`). Es un techo para entender la cuenta, no una predicción.
- **Panel de rasgos:** explica qué es «con red» y «con puntos, escamas o bandas» en el pie (`AYUDAS_PANEL`) y avisa de que, si no se está seguro de un rasgo, se deje en «no lo sé»: sin marcar no descarta ninguna ficha, mal marcado sí puede descartar la buena (los rasgos clave).

**Pendiente de decidir (no se ha tocado):** la ficha de *Leccinum scabrum* dice en «Descártala si ves…» «Pie sin escamas», pero su firma solo marca como clave los poros; hacer clave el pie descartaría esa ficha cuando la persona marca «lisa», pero también cuando la IA lea mal el pie (el banco: nadie lo lee bien). Y la ficha del cep no describe forma, superficie ni tamaño del sombrero, así que no puede sumar por ellos.

### Comparativa con otras apps (iFong)

iFong (app catalana de setas ya publicada, ~8 especies) usa datos de
~497 estaciones, mapa de hábitats de 2018, y geología del suelo
silici/calcari. Ese último punto, que era su ventaja diferencial, ya está
también integrado aquí (ver apartado de geología más arriba). Nuestro
proyecto sigue siendo más rico en número de fuentes cruzadas (radar de
superficie, humedad de suelo y aire, histórico real de avistamientos vía
GBIF) y más transparente (nivel de confianza explícito, explicaciones en
lenguaje natural, aprendizaje real de las salidas propias registradas) —
algo que iFong no menciona tener.

### Mantenimiento

- **API key de AEMET** caduca cada 3 meses (próxima: 25/11/2026).
- **API key de Meteocat** caduca 31/08/2027.
- **Token de GitHub del Worker** caduca el 24/11/2026.
- La web avisa automáticamente en rojo cuando a cualquiera de estas
  credenciales le quedan 15 días o menos.
- El backend se ejecuta cada 3 horas vía GitHub Actions; también se puede
  lanzar a mano desde "Actions" → "Actualitzar dades de bolets" → "Run workflow".

### Fallos reales detectados y corregidos durante el desarrollo

Uso de temperatura media en vez de mínima nocturna; "días desde lluvia"
que solo miraba el último chubasco; funciones que quedaron fusionadas o
con su `def` accidentalmente borrado al editar (sin error de sintaxis);
Meteoclimatic usando el campo de lluvia equivocado y sin coordenadas; API
de Meteocat exigiendo `data` junto con `estat`; triangulación contando la
misma estación varias veces; radar de AEMET sin georreferenciación real;
aviso de "cobertura incompleta" de RainViewer confundiendo "sin lluvia"
con "fallo de conexión"; rejilla original con altitud aproximada por
bloques (69 de 390 puntos con la misma altitud exacta); timeout de
Open-Meteo por ráfagas de peticiones sin pausa al aumentar la densidad de
la rejilla (confirmado con un HTTP 429 explícito); docstring de cabecera
del script desactualizado durante meses (citaba "~150 puntos" y solo
2 fuentes, cuando ya eran ~1.470 puntos y 8+ fuentes) — vale la pena
revisar los comentarios del código de vez en cuando, no solo el
comportamiento real; el desplegable de estaciones mostraba de entrada
todas las estaciones de AEMET (España entera, no solo Catalunya) y
repetidas varias veces (AEMET da varias lecturas horarias de la misma
estación como si fueran entradas distintas) — corregido con un filtro
geográfico por bounding box y deduplicación por nombre+coordenadas;
Meteoclimatic y Meteocat no exponían la hora real de su última lectura
en el desplegable (el dato sí existía en sus respuestas — `pubDate` en
el XML de Meteoclimatic, `data` en la lectura de Meteocat — solo faltaba
leerlo). Nota operativa real: una corrección de este mismo desplegable se
perdió una vez porque se aplicó sobre una copia local del archivo en vez
del archivo real subido a GitHub — para casos así, la forma fiable de
confirmar es pedir directamente el contenido del archivo en producción
(o del propio `resultats.json` generado) antes de asumir que un cambio
"debería" estar aplicado.

### Perfiles biológicos por especie (auditoría del 15/10/2026)

Los perfiles viven en `SPECIES` y `SPECIES_BIO` de `backend/recollir_dades.py`
(cada línea lleva la fuente y si es **[FONT]** —confirmado en fuentes— o
**[EST]** —estimación razonada; las fuentes dan la dirección pero no la cifra—).
Además del tiempo tras la lluvia, altitud, suelo y temporada, hay ahora
limitantes de **calor excesivo** (`tmax_hot`, `tmin_hot`), **frío sostenido**
(`cold`) y **helada** (`frost`, sobre la noche más fría de los últimos 7 días).

| Seta | Tras la lluvia principal | Temperatura | Suelo | Árboles | Altitud |
|---|---|---|---|---|---|
| Rovellons | pleno a los 14 d, dura hasta ~5 semanas | frena si máx. > 24 °C o noches > 15 °C; helada < −2 °C | indiferente (*L. deliciosus* silicícola, *L. sanguifluus* calcícola) | pinos (rojo, negro, blanco, piñonero, otros) | 200-1.700 m |
| Pinetell | 14 d (pinar de montaña) | frena si máx. > 22 °C; tolera algo más de frío | silici (calcari ×0,85) | pinos | 700-1.700 m |
| Cep (*B. edulis*, *B. pinophilus*) | 9-12 d, hasta ~20 d | óptimo medias ~13 °C (10-15); frena > 25 °C; heladas muy mal | silici (calcari ×0,75) | roble, haya, pino rojo/negro, abeto | 700-1.700 m, baja hasta 2.400 m (tierra baja muy penalizada) |
| Cep fosc *(provisional)* (*B. aereus*) | 8 d, hasta ~18 d | calor tolerado (frena > 28 °C); necesita noches ≥ 6 °C | silici ≥ mixt > calcari (×0,85) | encina, alcornoque, roble (haya ×0,85) | 350-1.000 m, cae desde ~1.300 m (72-1.405 m según trobarbolets), sep-oct |
| Cep d'estiu *(provisional)* (*B. reticulatus*) | 8 d, hasta ~20 d | calor tolerado (frena > 29 °C); necesita noches ≥ 8 °C | silici ≥ mixt > calcari (×0,85) | roble, haya (encina ×0,85) | 450-1.700 m, cae hasta 2.400 m (433-2.228 m según trobarbolets), jul-sep |
| Camagrocs | 16 d, dura hasta ~6 semanas; necesita mucha humedad | frío: aguanta heladas; frena si máx. > 18 °C o noches > 11 °C | calcari ≥ mixt > silici | pinos, haya, roble, abeto | 400-1.500 m |
| Trompetes de la mort | 16 d | frena si máx. > 20 °C | casi indiferente (silici ×0,95) | haya y roble; encina (×0,85) | desde ~100 m (tierra baja frenada), hasta 1.500 m |
| Ou de reig | 15-21 d | necesita noches ≥ 12 °C y días ≥ 22 °C; helada lo mata | silici (calcari ×0,12) | encina, roble, alcornoque | < 800 m |
| Rossinyols | 7-9 d, hasta ~18 d | frena si máx. > 26 °C; heladas mal | silici (calcari ×0,8) | haya, roble, pinos, abeto | 600-1.800 m |
| Colmenilles | 8 d (primavera) | necesita días ≥ 15 °C; frena si máx. > 20 °C; marzo-mayo | calcari ≥ silici | roble, pinos | < 1.600 m |
| Llengua de bou | 12 d, hasta ~28 d | frena si máx. > 24 °C; heladas mal | silici/mixt (calcari ×0,8) | roble, haya, alcornoque, pino rojo/negro, abeto | 500-1.600 m |
| Fredolic | 12 d, hasta ~32 d | necesita frío: frena si máx. > 20 °C; aguanta heladas | indiferente | pinos, encina | tierra baja (< 900 m) |
| Escarlet *(provisional)* | 16 d, hasta ~40 d | frena si máx. > 20 °C; aguanta heladas suaves | calcari ≥ mixt > silici (×0,70) | encina, roble (haya y alcornoque ×0,85) | 100-1.000 m, hasta 1.650 m |
| Llenega negra *(provisional)* | 14 d, hasta ~35 d | frena si máx. > 21 °C; aguanta bien el frío | calcari > mixt > silici (×0,65) | pinos (todos) | 150-1.200 m, hasta 1.650 m |

**Escarlet** (*Hygrophorus russula*) y **llenega negra** (*Hygrophorus
latitabundus*) se añadieron el 15/10/2026 a partir de las fichas públicas de
trobarbolets.cat (hábitat, suelo, altitudes y meses de las observaciones
GBIF/iNaturalist). Son **perfiles provisionales**: lo único con fuente es el
hábitat, el suelo, el rango de altitud y los meses; los días tras la lluvia, la
lluvia mínima y las temperaturas son **[EST]** y no hay ninguna salida de campo.
Por eso su confianza es siempre 🔴 (baja) y la web les añade el aviso «Perfil
provisional: sin datos de campo todavía». Las 9 especies
anteriores que no son el cep no cambian (comprobado con una prueba de regresión).

**Ceps separados en tres (15/10/2026).** Antes había un único «Ceps» que juntaba
*B. edulis*, *B. pinophilus* y *B. aereus*; sus ecologías son distintas
(según trobarbolets.cat: el cep fosc es de encinar y alcornocal a
baja altitud y en septiembre-octubre; el cep d'estiu, de verano; el cep, de
montaña). Ahora son `cep`, `cepfosc` y `cepestiu`. El `cep` conserva el perfil
anterior salvo que ya no acepta encina ni alcornoque y que la tierra baja
(< 500 m) puntúa mucho menos (a 600 m pasa de 90 a 74 en el escenario ideal; a
nivel del mar de 27 a 9): eso era precisamente lo que mezclaba al cep fosc. Para
las especies sin datos de GBIF suficientes, `peak_months` en `SPECIES_BIO` fija
los meses de pico de la climatología de reserva. Cep fosc y cep d'estiu son
**provisionales** (solo hábitat, suelo, altitud y meses tienen fuente; el resto
es [EST]) y nacen con confianza 🔴. El id antiguo `ceps` ya no existe en el
catálogo: las salidas antiguas con `ceps` se comparan con el máximo de las tres
(`LEGACY_SPECIES_ALIASES`, así no se pierde ninguna validación). El Worker sigue
aceptando `ceps` por compatibilidad. El GBIF de las especies nuevas se descarga
solo en la primera ejecución de la Action.

**Formulario de hallazgos (15/10/2026, `web/index.html`):** el botón «Usar mi
ubicación» pide el GPS (`getCurrentPosition`, 20 s de espera) y rechaza puntos fuera
de Catalunya (los mismos límites que el Worker). Al fijar el punto —por GPS, por clic
en el mapa o con el botón de la ventana de una zona— se rellenan: **lugar** (Nominatim;
si falla, el nombre de la zona más cercana), **altitud** (servicio de elevación de
Open-Meteo; si falla, la de la zona más cercana, redondeada a 50 m), **árbol** (el tipo
de bosque de la zona más cercana a ≤ 6 km: pino, encina o roble; cultivo, matorral, etc.
→ «mixto / no lo sé») y **fecha** de hoy. No se rellenan ni la seta ni el resultado. Son
estimaciones (la zona más cercana está a unos 3,5 km) y el formulario lo dice. El árbol y
la altitud del hallazgo solo se guardan como dato; el backend contrasta cada hallazgo con
la zona más cercana. En la lista de setas del formulario, **cep, cep fosc y cep d'estiu
son una sola opción «Cep»** (id `ceps`, que el backend contrasta con la mejor puntuación
de los tres); el filtro del mapa sigue separándolos. **Límites:** la llamada a Open-Meteo
no se ha podido probar contra el servicio real desde el entorno de desarrollo (en las
pruebas está simulada; si falla, se usa la altitud de la zona); el relleno del árbol es
muy grueso (no distingue haya, alcornoque ni madroño). Las fotos de la guía no se
guardan con el hallazgo.

**No añadidas (apagallums, cama-sec, moixernó):** son de **prado** (*Macrolepiota
procera*, *Marasmius oreades*, *Calocybe gambosa*). La rejilla se construye solo
sobre celdas con bosque y la web solo dibuja puntos forestales, así que solo
quedarían ~224 puntos de «prado» dentro de celdas con bosque (5 %) y casi nada
de los prados de alta montaña (donde está el moixernó). Mostrarlas así daría
falsos negativos silenciosos. Para hacerlo bien hace falta una rejilla propia de
prados (más consultas y más tiempo de la Action): decisión pendiente.

Pendiente de calibrar con salidas reales (`hallazgos`): todas las cifras
**[EST]**. `tests/audit_species.py` imprime una tabla por especie (puntuación
según días tras la lluvia, calor, frío, helada, altitud, suelo y mes) para
ver de un vistazo si un cambio de perfil tiene sentido.

### Auditoría del 15/10/2026 (Ou de reig en Montnegre y Matadepera)

El usuario comprobó en el campo que el modelo daba Ou de reig donde no
había. Causas encontradas y corregidas:

- **Días desde lluvia**: se contaban desde el último día con ≥5 mm, no desde
  la lluvia principal. Ahora, episodios de lluvia + memoria propia de la
  serie diaria (`weather_block_cache.json`).
- **Una suma sin frenos**: los limitantes biológicos multiplican (ver arriba).
- **Geología**: conglomerados y rocas detríticas con cemento calcáreo se
  tomaban por silici; un fallo de red se guardaba como «sin dato».
- **Cachés con caducidad escondida**: bosque (30 d), geología (180 d) y
  GBIF caducaban de golpe y volvían a pedir miles de consultas.
- **GBIF**: la caché antigua en formato plano no se leía, por lo que la
  temporada real nunca se aplicaba y colmenilles puntuaba en otoño.
- **Puntos duplicados**: 8.285 → 4.248 al descartar puntos a menos de 0,5 km
  (se conservan los `id` originales para no invalidar cachés).
- **VEGETACIO** (especie exacta del árbol): el resultado solo vivía en
  memoria y la tanda de 900 s empezaba cada vez por los mismos puntos
  (~158 de ~3.000 afinados). Además el emparejamiento por nombre de capa
  hacía que `QUERCUSILEX/SUBER` (encinar/alcornocal) se tomaran por
  `QUERCUS` (roble) y que capas que no son de especie (`PTGMFC`,
  `RPALTRESESP`…) cortaran la búsqueda. Ahora: emparejamiento por clave más
  larga, solo capas de especie, resultado por punto guardado en
  `vegetacio_layers_cache.json`, y un fallo de red nunca se confunde con
  «esa especie no está».
- **Pruebas**: `tests/test_model.py` (sin red, desde `backend/`:
  `python3 -I ../tests/test_model.py`) cubre episodios de lluvia con el caso
  real de Montnegre, curvas, limitantes, GBIF, duplicados y VEGETACIO, y además la
  guía, las fotos, los rasgos y el vocabulario del Worker. Otras dos baterías,
  desde `tests/` con Node: `node test_worker.mjs` (Worker: acceso, límites e
  `/identify` con una IA simulada) y `node test_rasgos.mjs` (cálculo de la
  coincidencia: comprueba que el cálculo hace lo diseñado, **no** cuánto acierta con
  setas reales). La pantalla de identificación se probó además en Chromium con un
  Worker simulado (prueba fuera del repositorio).

Pendiente / conocido (revisado el 15/10/2026 con datos reales de producción):
la estación de Vallgorguina midió ~170 mm el 4/10 (≈206 mm entre el 29/9 y el
8/10). La suma de Open-Meteo para la tanda en los puntos del Montnegre
(162-177 mm en 11 días) queda un ~10-20 % por debajo de la estación (≈183 mm):
**no hay una infravaloración grande del acumulado**. La cifra «24-32 mm» de un
día concreto que se anotó antes **no se ha podido reproducir** (la caché
antigua no guardaba la serie diaria; con la serie propia ya será comprobable).
En los 1.636 puntos con estación Meteoclimatic a ≤6 km, Open-Meteo suma de
media ~22-34 mm MÁS que la estación vecina (436 puntos con >60 mm más, solo 51
con >60 mm menos) y las estaciones aficionadas dan ceros (Terrassa y Sabadell
0 mm frente a ~190) y picos de 333 mm. Fusionar sin filtrar empeoraría el
modelo, por eso `historial_lluvia.json` solo se usa como contraste (bono de
corroboración), no para rehacer los episodios de lluvia.

### Validación: qué está demostrado y qué no (15/10/2026)

**Lo que NO está demostrado:** que una puntuación de 85 signifique más
probabilidad real de encontrar setas que una de 65. Las puntuaciones son un
**modelo heurístico** (reglas biológicas con cifras mayormente **[EST]**,
estimadas), no probabilidades calibradas. Que el código funcione y las fuentes
se actualicen demuestra *fiabilidad técnica*, no *validez predictiva*.

**Datos reales que existen hoy:** 6 salidas en `data/hallazgos.json`, todas
positivas (4 «mucho», 2 «poco», ninguna «nada»), de dos épocas (octubre-noviembre
de 2025 y agosto de 2026). Con 6 positivos no se puede medir ni acierto ni
calibración; la tasa de confirmación de la web aún no tiene datos.

**Primera comprobación retrospectiva (ya hecha):** ¿habría podido el modelo
marcar esos 6 sitios con lluvia y temperatura ideales? (`tests/test_model.py`,
sección «Troballa real»). Antes de esta revisión, **de las 5 salidas dentro de
la rejilla, 4 eran imposibles de marcar** y la quinta solo desde un pinar genérico
vecino —no por el tiempo, sino por reglas fijas—:
- Ceps a ~2.000 m en pino negro (Ger, 25/08/2026): la curva de altitud ya
  frenaba a ×0,40 a 2.000 m (sostre ≈ 21). Ahora la caída empieza más arriba
  (×0,95 a 2.000 m, ×0,80 a 2.200 m, 0 a 2.550 m).
- Ceps en encinar a ~400-500 m (Sant Celoni, 9/10/2025): `alzina` no estaba
  en la lista de árboles de los ceps (aunque *Boletus aereus* —el cep negro—
  ya figuraba en la especie), así que las zonas de encinar más cercanas daban 0
  y solo un pinar genérico a 2,2 km podía marcar. Ahora se acepta con ×0,90.
- Trompetes de la mort a 90-170 m (la Batllòria, Gualba; 3 salidas «mucho»):
  la altitud ya frenaba a ×0,2-0,4 y `alzina` no estaba en la lista; además el
  suelo silíceo (granito de la vall de la Tordera) las rebajaba por una
  preferencia por el calcari que las propias salidas contradicen. Ahora:
  altitud desde ~100 m, `alzina` ×0,85 y silici ×0,95. Resultado con tiempo
  ideal: Gualba ≈ 73; la Batllòria sigue **marginal** (≈ 57-67 en octubre,
  ≈ 70+ en noviembre) porque su punto más cercano (0,1 km) es un pinar
  genérico (`pi_altres`, 0 para trompetes) pendiente de afinar con VEGETACIO.
  No se ha forzado más el modelo: se deja anotado en las pruebas.
- La 6.ª salida (Les Angles, 26/08/2026) cae fuera de la rejilla (Catalunya
  Nord, a 9,5 km del punto más cercano): no es comparable.

Esto se hizo **por evidencia de campo, no por ajuste fino**: son cambios
mínimos para que el modelo *pueda* marcar lo que se sabe que existe. Hay un
riesgo inverso (más falsos positivos), por eso hay pruebas de contención
(trompetes bajo encina en la costa, en agosto, ceps bajo encina a baja altitud).
Con 6 salidas de una sola persona, sobre todo en una comarca, esto NO es una
calibración.

*Nota (15/10/2026):* el «ceps» de estas salidas es hoy `cep`, `cepfosc` y
`cepestiu`. El cep de encinar (Sant Celoni) corresponde ahora al **cep fosc**,
que sí acepta encina; el cep a 2.000 m en pino negro, al **cep**. La validación
de salidas antiguas con `ceps` usa el máximo de las tres.

**Cómo se mide ahora la tasa de confirmación** (`freeze_predictions` y
`compute_model_accuracy` en `backend/recollir_dades.py`):
1. En cuanto el backend ve una salida nueva (registrada como mucho 3 días
   después de la troballa), **congela** la puntuación de *todas las especies*
   en la zona más cercana (≤ 3,5 km) en `data/validacio.json`.
2. Se compara **la especie encontrada** (antes se comparaba con «la mejor
   especie de la zona», lo que inflaba los aciertos) con el umbral (70).
3. Salidas «nada» (buscado y no encontrado) cuentan como acierto si la
   puntuación era < umbral; si no se indica especie, cuenta la mejor de la zona.
4. Visitas repetidas (misma zona, día, especie y resultado) cuentan **una**.
5. Las no contrastables (sin predicción guardada, fuera de rejilla, registradas
   tarde) se declaran aparte (`no_contrastables`), no se cuentan.
6. Se desglosa por especie y por franja de puntuación.

Errores del método anterior que se corrigieron: solo comparaba con la mejor
especie; el historial se borraba a los 30 días, así que cualquier salida más
antigua era incomparable; la zona «más cercana» podía estar a 8 km; la cifra
se llamaba `precision_global` aunque con solo positivos mide sensibilidad.
(La clave `precision_global` se mantiene solo por compatibilidad con la web.)

**Cómo hacer que la validación valga algo (protocolo propuesto):**
- Registrar **también las búsquedas sin resultado** («busqué y no encontré
  nada»), sobre todo en zonas que el modelo daba como buenas **y** en zonas
  que daba como malas. Sin negativos no se puede saber si el modelo se
  equivoca marcando zonas vacías.
- Salir de vez en cuando a zonas con puntuación baja o media, no solo a las
  recomendadas (el sesgo de selección es el mayor enemigo de esta validación).
- Registrar la salida el mismo día o al siguiente.
- No tocar las reglas biológicas por una sola salida: esperar a tener varias por
  especie. Evaluar siempre por especie y por temporada, y comparar con una
  referencia simple (p. ej. «sólo mes + altitud + árbol, sin tiempo»).
- Con ~30 salidas por especie (positivas y negativas) ya se puede mirar si las
  franjas altas rinden más que las bajas.

### Ideas evaluadas y aparcadas deliberadamente

Una revisión posterior del propio README (ChatGPT, 15/10/2026), contrastada con
el código: acertó en el código de acceso (sin límite de intentos y no
uniforme), en la tasa de confirmación y en que el modelo no está validado;
estaba desactualizada en cifras de puntos, en `deepseek-v4-flash` y, en parte,
en la caché meteorológica. Lo corregido está arriba.

Un análisis externo detallado (ChatGPT) señaló mejoras de fondo aparcadas:
pesos del scoring calibrados por especie en vez de globales; curvas de
respuesta biológica en vez de tramos lineales; rejilla geográfica
adaptativa; orientación y pendiente del terreno; corregir el sesgo de que
la gente solo visita zonas con puntuación alta; incertidumbre explícita
en la estimación de lluvia; machine learning una vez haya datos no
sesgados suficientes.
