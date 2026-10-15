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
   rejilla de predicción (no son estaciones meteorológicas reales, son
   ~1.470 puntos repartidos cada ~5km por Catalunya). Toca un punto para
   ver qué especie cumple bien las condiciones, con qué puntuación (0-100,
   cuanto más alto mejor) y por qué.
3. Puedes mover el deslizador de arriba para ver más o menos zonas (más
   exigente = menos puntos, pero más fiables).
4. Junto a cada puntuación verás un icono 🟢🟠🔴 — es la **confianza**: no es
   lo mismo una puntuación alta bien respaldada por datos reales que una
   basada solo en el cálculo del día. En verde, fíate más.
5. Si tocas "¿Por qué esta puntuación?" te da una explicación en lenguaje
   normal de qué la ha hecho subir o bajar.
6. Cuando salgáis al monte, marcad en el mapa el resultado de la salida
   (encontrasteis mucho, poco, o buscasteis sin encontrar nada) — cuantos
   más registremos, mejor se irá afinando el modelo con datos reales
   vuestros. Estas salidas no se ven en el mapa (para no saturarlo), pero
   sí cuentan por detrás.
7. Más abajo hay un desplegable de "Estaciones meteorológicas" donde
   puedes elegir cualquiera de las estaciones reales que usa el sistema
   (AEMET, Meteocat, Meteoclimatic) y ver sus datos tal cual llegan.

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
- `data/weather_block_cache.json` — caché de tiempo por punto, con su **serie diaria propia** (hasta 45 días de lluvia y temperaturas) para detectar episodios de lluvia sin pedir más datos a Open-Meteo.
- `data/gbif_cache.json` — caché de distribución mensual y de altitud de cada especie según GBIF/FungaCAT, 60 días.
- `data/historial_lluvia.json` — historial propio de lluvia diaria vía Meteoclimatic, 30 días.
- `data/geocode_cache.json` — caché permanente de coordenadas de estaciones de Meteoclimatic (Nominatim).
- `data/meteocat_stations_cache.json` — caché de metadatos de estaciones XEMA/Meteocat, 90 días.
- `data/geologia_cache.json` — caché permanente de litología (silici/calcari/mixt) por coordenadas, con el texto original del ICGC para poder reclasificar sin volver a consultar.
- `data/zone_names_cache.json` — caché permanente de nombres reales de las zonas (Nominatim, reverse geocoding).
- `data/evolucion.json` — snapshot diario de la mejor puntuación por zona, 30 días.
- `data/hallazgos.json` — salidas reales registradas por los usuarios. Se actualiza vía el Worker.
- `web/index.html` — la web: login, mapa, deslizador de umbral, formulario de salidas, panel de tasa de confirmación, explicaciones de DeepSeek.
- `worker/index.js` — código del Worker de Cloudflare. **Se despliega directamente en el editor de Cloudflare, subirlo a GitHub NO lo actualiza en producción.**
- `.github/workflows/actualitzar.yml` — automatización que ejecuta el backend cada 3 horas.

### La rejilla de predicción

~1.470 puntos repartidos cada ~5km por Catalunya (no son estaciones
meteorológicas reales — ver más abajo). Se generan una sola vez con:
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
así que con ~1.470 puntos completar todos los nombres tarda unas 2-3
semanas — es el máximo defendible sin alargar esa espera de forma
excesiva.

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
0,5 km), y cada una de las 10 especies del catálogo, se calcula una
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
  solo para las 3 especies con evidencia clara (Ceps y Ou de reig
  prefieren silici, Camagrocs prefiere calcari).
- **Corroboración entre fuentes** (0-10 pts) — el radar tiene prioridad
  máxima (cobertura directa del punto exacto); si no hay radar, se usa la
  triangulación de estaciones (AEMET+Meteocat+Meteoclimatic)

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
si el árbol no está en la lista `trees` de la especie, puntúa 0. Cuando
VEGETACIO afina el tipo (pino rojo, pino blanco, abeto, haya, alcornoque…),
las listas incluyen esos «hijos» donde la especie de verdad crece, para no
perder avisos (comprobado en `tests/test_model.py`).

Junto a cada puntuación se muestra un nivel de **confianza** (🟢🟠🔴),
independiente del valor numérico: refleja cuánta evidencia real la
respalda.

La web muestra las zonas por encima de un **umbral ajustable** (por defecto
70, con deslizador).

### Radar meteorológico

Da cobertura de **superficie continua** en vez de solo puntos con
estación — importante porque una tormenta muy localizada puede caer justo
entre dos estaciones y no detectarse de otro modo. Es una estimación (no
tan exacta como un pluviómetro físico) del instante actual (no
acumulado), pero cubre cualquiera de los ~1.470 puntos, tengan o no una
estación cerca.

- **RainViewer (activo)**: mosaico europeo gratuito, sin API key. Da un
  color (RGBA) por píxel, traducido a dBZ (tabla oficial "Universal Blue")
  y luego a mm/h (Marshall-Palmer). Si un día no llueve en ningún punto,
  es una respuesta válida (no un fallo) — el sistema lo distingue
  correctamente. Tiene prioridad máxima en el bonus de corroboración
  cuando detecta lluvia, por dar cobertura directa del punto exacto.
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

Preferencias usadas: **Ou de reig** acidófilo (limitante fuerte), **Ceps**
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

Cuando hay suficientes salidas registradas, el backend calcula una **tasa
de confirmación** (no "precisión": no es una muestra representativa de
todas las zonas, solo de las visitadas).

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
- `DEEPSEEK_API_KEY` — key de la API de DeepSeek (modelo `deepseek-v4-flash`).

Secrets configurados en GitHub Actions (repositorio → Settings → Secrets
and variables → Actions):
- `AEMET_API_KEY` — caduca cada 3 meses (próxima: 25/11/2026).
- `METEOCAT_API_KEY` — caduca 31/08/2027.

**Seguridad del Worker** — nunca confía en lo que le manda el navegador:
rango geográfico real de Catalunya, lista blanca de especies/árboles,
límites de longitud, formato de fecha válido, límite de tamaño de payload
(10KB), retraso tras un intento fallido.

**IMPORTANTE — `worker/index.js` no se despliega solo:** el archivo en
GitHub es solo la copia de referencia. Para que un cambio tenga efecto de
verdad, hay que pegarlo directamente en Cloudflare (Edit code → Deploy).

### Control de acceso

La web pide un email antes de mostrar nada:
1. El Worker comprueba si el email está en `AUTHORIZED_EMAILS`.
2. Si está autorizado, genera un código de 6 dígitos (válido 10 minutos) y
   lo envía por email vía Brevo.
3. El navegador recibe un token de sesión firmado (30 días).

El código no se guarda en ningún sitio: se deriva con HMAC (email +
ventana de 10 min + `SESSION_SECRET`).

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
| Ceps | 9-12 d, hasta ~20 d | óptimo medias ~13 °C (10-15); frena > 25 °C; heladas muy mal | silici (calcari ×0,75) | roble, haya, pino rojo/negro, abeto, alcornoque | 550-1.700 m (tierra baja penalizada) |
| Camagrocs | 16 d, dura hasta ~6 semanas; necesita mucha humedad | frío: aguanta heladas; frena si máx. > 18 °C o noches > 11 °C | calcari ≥ mixt > silici | pinos, haya, roble, abeto | 400-1.500 m |
| Trompetes de la mort | 16 d | frena si máx. > 20 °C | calcari (silici ×0,85) | haya y roble | 500-1.500 m |
| Ou de reig | 15-21 d | necesita noches ≥ 12 °C y días ≥ 22 °C; helada lo mata | silici (calcari ×0,12) | encina, roble, alcornoque | < 800 m |
| Rossinyols | 7-9 d, hasta ~18 d | frena si máx. > 26 °C; heladas mal | silici (calcari ×0,8) | haya, roble, pinos, abeto | 600-1.800 m |
| Colmenilles | 8 d (primavera) | necesita días ≥ 15 °C; frena si máx. > 20 °C; marzo-mayo | calcari ≥ silici | roble, pinos | < 1.600 m |
| Llengua de bou | 12 d, hasta ~28 d | frena si máx. > 24 °C; heladas mal | silici/mixt (calcari ×0,8) | roble, haya, alcornoque, pino rojo/negro, abeto | 500-1.600 m |
| Fredolic | 12 d, hasta ~32 d | necesita frío: frena si máx. > 20 °C; aguanta heladas | indiferente | pinos, encina | tierra baja (< 900 m) |

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
  real de Montnegre, curvas, limitantes, GBIF, duplicados y VEGETACIO.

Pendiente / conocido: Open-Meteo infravalora lluvias convectivas muy
localizadas (el 4/10: 24-32 mm frente a ~170 mm medidos en Montnegre); se
podría fusionar con el historial de estaciones (`historial_lluvia.json`).

### Ideas evaluadas y aparcadas deliberadamente

Un análisis externo detallado (ChatGPT) señaló mejoras de fondo aparcadas:
pesos del scoring calibrados por especie en vez de globales; curvas de
respuesta biológica en vez de tramos lineales; rejilla geográfica
adaptativa; orientación y pendiente del terreno; corregir el sesgo de que
la gente solo visita zonas con puntuación alta; incertidumbre explícita
en la estimación de lluvia; machine learning una vez haya datos no
sesgados suficientes.
