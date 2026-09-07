# Predictor de bolets — Catalunya

## Para quien la va a usar

Esta web te dice, según el tiempo real de los últimos días (lluvia,
temperatura, y hasta la humedad real de la tierra), en qué zonas de
Catalunya es más probable encontrar cada tipo de bolet ahora mismo.

**Cómo usarla:**
1. Entra con la contraseña que te han pasado.
2. En el mapa verás puntos de colores — cada uno es una zona donde alguna
   especie cumple bien las condiciones. Toca un punto para ver qué especie,
   con qué puntuación (0-100, cuanto más alto mejor) y por qué.
3. Puedes mover el deslizador de arriba para ver más o menos zonas (más
   exigente = menos puntos, pero más fiables).
4. Junto a cada puntuación verás un icono 🟢🟠🔴 — es la **confianza**: no es
   lo mismo una puntuación alta bien respaldada por datos reales que una
   basada solo en el cálculo del día. En verde, fíate más.
5. Si tocas "¿Por qué esta puntuación?" te da una explicación en lenguaje
   normal de qué la ha hecho subir o bajar.
6. Cuando salgáis al monte, marcad en el mapa lo que encontréis (o no
   encontréis) con "Marcar en el mapa" — cuantos más hallazgos registremos,
   mejor se irá afinando el modelo con datos reales vuestros. Los hallazgos
   se agrupan por zona (no verás una chincheta por cada uno) para que el
   mapa siga siendo legible aunque haya miles registrados.

Los datos se actualizan solos cada 6 horas. No hace falta hacer nada para
que esté al día.

---

## Para quien toque el código

**Web pública:** https://shicodiez.github.io/bolets-catalunya/web/ (protegida
con contraseña)
**Repositorio:** https://github.com/Shicodiez/bolets-catalunya
**Worker de Cloudflare:** https://bolets-hallazgos.shicoars.workers.dev/

### Qué es cada carpeta

- `backend/recollir_dades.py` — recoge datos de todas las fuentes, calcula
  la puntuación de cada bolet en cada zona, y guarda el resultado. Se
  ejecuta automáticamente cada 6 horas.
- `data/resultats.json` — el resultado del cálculo. La web lo lee.
- `data/bosc_cache.json` — caché del tipo de bosque genérico por zona (ICGC), 30 días.
- `data/vegetacio_layers_cache.json` — caché de capas de especie de árbol (VEGETACIO), 90 días.
- `data/gbif_cache.json` — caché de distribución mensual y de altitud de cada especie según GBIF/FungaCAT, 60 días.
- `data/historial_lluvia.json` — historial propio de lluvia diaria vía Meteoclimatic, 30 días.
- `data/geocode_cache.json` — caché permanente de coordenadas de estaciones de Meteoclimatic (Nominatim).
- `data/meteocat_stations_cache.json` — caché de metadatos de estaciones XEMA/Meteocat, 90 días.
- `data/zone_names_cache.json` — caché permanente de nombres reales de las 390 zonas (Nominatim, reverse geocoding).
- `data/evolucion.json` — snapshot diario de la mejor puntuación por zona, 30 días.
- `data/hallazgos.json` — hallazgos reales registrados por los usuarios. Se actualiza vía el Worker.
- `web/index.html` — la web: login, mapa, deslizador de umbral, formulario de hallazgos, panel de precisión histórica, explicaciones de DeepSeek.
- `worker/index.js` — código del Worker de Cloudflare.
- `.github/workflows/actualitzar.yml` — automatización que ejecuta el backend cada 6 horas.

### Fuentes de datos usadas (todas gratuitas)

| Fuente | Para qué se usa |
|---|---|
| **Open-Meteo** | Histórico de lluvia y temperatura (16 días); también humedad real del suelo y evapotranspiración, sin API key |
| **AEMET OpenData** | Estación real más cercana a cada zona, para la triangulación (API key, caduca cada 3 meses) |
| **Meteocat / XEMA** | Red oficial de la Generalitat (~190 estaciones), la más densa para Catalunya; misma triangulación (API key, caduca 31/08/2027) |
| **Meteoclimatic** | Red de estaciones amateur; se geocodifica con Nominatim porque el feed no da coordenadas |
| **ICGC** | Tipo de bosque genérico (coníferas/frondosas/perennifolias), vía WMS |
| **VEGETACIO** (Generalitat) | Especie exacta de árbol, refinando el dato del ICGC |
| **GBIF / FungaCAT** | Histórico real de avistamientos: temporada real (mes) y altitud típica de cada especie |
| **Nominatim (OpenStreetMap)** | Nombres de lugar ↔ coordenadas, en ambos sentidos (estaciones, zonas y formulario de hallazgos) |
| **DeepSeek** | Explicaciones en lenguaje natural del "por qué" de una puntuación, a petición del usuario — nunca decide el cálculo |

Se investigaron y descartaron por no ser viables sin coste o sin
intervención manual: **SIAR** (acceso API requiere aprobación previa, pocas
estaciones útiles en Catalunya), **Ecowitt** y **Weather Underground** (su
API solo da acceso a quien sea dueño de su propia estación física, no hay
endpoint público de todas las estaciones) y **Netatmo** (aunque tiene un
endpoint público real, exige login manual en navegador vía OAuth2,
incompatible con un backend que se ejecuta solo sin intervención humana).

### Cómo funciona el cálculo

Para cada uno de los ~390 puntos de la rejilla, y cada una de las 10
especies del catálogo, se calcula una **puntuación de 0 a 100** sumando
evidencia de seis componentes:

- **Lluvia acumulada** (0-22 pts) desde el inicio de la tanda de lluvias actual
- **Días desde que empezó a llover** (0-25 pts) — cada especie tiene su rango
- **Temperatura mínima nocturna** (0-20 pts) — no la media del día
- **Humedad real del suelo** (0-8 pts) — distingue si el agua caída sigue en
  la tierra o se ha perdido, con bonus si la tendencia es a humedecerse
- **Temporada real de la especie** (0-15 pts) según GBIF, por mes y altitud
- **Corroboración entre fuentes** (0-10 pts) — bonus si varias estaciones
  reales (triangulación IDW de AEMET+Meteocat+Meteoclimatic) confirman la lluvia

El único requisito "duro" (que descarta una especie por completo) es el
tipo de bosque — el resto es gradual, así que un solo dato flojo de una
fuente no hace desaparecer una especie con buena evidencia por lo demás.

Junto a cada puntuación se muestra un nivel de **confianza** (🟢🟠🔴),
independiente del valor numérico: refleja cuánta evidencia real la
respalda (registros GBIF, nº de estaciones triangulando).

La web muestra las zonas por encima de un **umbral ajustable** (por defecto
70, con deslizador).

### Triangulación de estaciones (IDW)

En vez de usar solo la estación real más cercana a cada zona, se combinan
hasta 4 estaciones (AEMET + Meteocat/XEMA + Meteoclimatic) ponderadas por
1/distancia² — las más cercanas pesan más, pero las algo más lejanas
también aportan. Se deduplica por nombre+distancia para que la misma
estación no cuente dos veces. Esto da una estimación de lluvia del día más
fiable que depender de una sola estación aislada, y aumenta la confianza
reportada cuando hay 2+ estaciones de acuerdo.

### Nombres de zona reales

Las 390 coordenadas fijas de la rejilla se resuelven a un nombre de lugar
real (pueblo, comarca) vía reverse geocoding (Nominatim), en vez de
mostrar "Punt 275". Como las coordenadas no cambian, el caché es
permanente — el proceso completa 20 nombres por ejecución (respetando el
límite de Nominatim para scripts automáticos) hasta resolver las 390, lo
que tarda unos días desde que se activó. Mientras un punto no tiene nombre
resuelto, se muestra como "Punt X" de forma temporal.

### Evolución, tasa de confirmación y cobertura de datos

Cada día se guarda un snapshot de la mejor puntuación de cada zona. La web
compara con hace 7 días y marca **▲/▼** en las zonas que más han subido o
bajado.

Cuando hay suficientes salidas registradas, el backend cruza cada una con
la puntuación que tenía esa zona ese día y calcula una **tasa de
confirmación** (deliberadamente no se llama "precisión": no es una
muestra representativa de todas las zonas, solo de las que alguien
visitó y registró — un matiz importante que la propia web explica).

El formulario permite registrar 4 resultados de una salida: encontré
mucho, encontré poco, busqué y no encontré nada, o no llegué a buscar
bien (esta última no se guarda como dato — no aporta información fiable
sobre el modelo, ya que no hubo búsqueda real). Con la opción de "no
encontré nada" de vuelta, la tasa de confirmación ya puede detectar
también cuando el modelo predice mal en sentido contrario (dice que hay
condiciones, pero no se encuentra nada), no solo confirmar aciertos.

La web también avisa cuando alguna fuente de datos (Open-Meteo, AEMET,
Meteocat, Meteoclimatic) ha fallado en la última actualización, para
dejar claro que las puntuaciones de ese momento pueden estar basadas en
menos fuentes de lo habitual — en vez de fallar en silencio.

### El Worker de Cloudflare (`worker/index.js`)

Como GitHub Pages solo sirve archivos estáticos, hay un Worker en
Cloudflare que hace de intermediario para:

1. **Guardar hallazgos de forma permanente** en `data/hallazgos.json`, vía
   un token de GitHub guardado como Secret.
2. **Control de acceso** — verifica la contraseña de entrada a la web.
3. **Explicaciones de DeepSeek** (endpoint `/explain`).

Secrets configurados en el Worker (Cloudflare → Workers & Pages →
`bolets-hallazgos` → Settings → Variables and Secrets):
- `GITHUB_TOKEN` — Contents read/write solo sobre `bolets-catalunya`. Caduca el 24/11/2026.
- `APP_PASSWORD` — la contraseña de acceso a la web.
- `DEEPSEEK_API_KEY` — key de la API de DeepSeek (modelo `deepseek-v4-flash`).

Secrets configurados en GitHub Actions (repositorio → Settings → Secrets
and variables → Actions):
- `AEMET_API_KEY` — caduca cada 3 meses (próxima: 25/11/2026).
- `METEOCAT_API_KEY` — caduca 31/08/2027.

**Seguridad del Worker** — el Worker nunca confía en lo que le manda el
navegador y lo valida todo por su cuenta: rango geográfico real de
Catalunya para las coordenadas, lista blanca de especies y tipos de
árbol válidos, límites de longitud en textos, formato de fecha (sin
fechas futuras ni de hace más de 10 años), límite de tamaño de payload
(10KB), y un pequeño retraso tras una contraseña incorrecta para
encarecer intentos automatizados. Un rate limiting completo por IP
requeriría añadir Cloudflare KV, que de momento no se ha considerado
necesario para el volumen de uso actual.

### Control de acceso

La web pide una contraseña antes de mostrar nada:
- Guardada como Secret `APP_PASSWORD` en el Worker — nunca en el código.
- Al introducirla, el navegador recibe un token de sesión firmado (30 días).
- **Para revocar el acceso a todo el mundo de golpe**: cambia
  `APP_PASSWORD` en el Worker. Todas las sesiones antiguas dejan de valer
  al instante.

### Registro de salidas propias

Desde la web se marca en el mapa el punto exacto y se elige el resultado
de la salida:
- **🍄 Encontré mucho / poco** — pide la especie, altitud (tramos de 50m) y
  tipo de árbol.
- **🔍 Busqué y no encontré nada** — misma información, pero la especie es
  opcional (puede ser una búsqueda sin objetivo concreto).
- **🚶 No llegué a buscar bien** — no se guarda como dato; sirve solo para
  que quien registra pueda "descartar" la salida sin que ensucie las
  estadísticas del modelo (una salida sin búsqueda real no dice nada
  sobre si el modelo acertó o no).

El nombre del lugar se rellena solo (geocodificación inversa) pero es
editable.

En el mapa, las salidas **no se muestran individualmente** — se agrupan
por proximidad (~2km) en un único círculo por zona, cuyo color y tamaño
reflejan cuántas hay y qué proporción son positivas. Al hacer clic se ve
el detalle completo del grupo (especie por especie, fecha por fecha), con
opción de borrar cada registro individual. Así el mapa sigue siendo
legible aunque haya miles de registros, sin perder ningún dato de cara al
análisis futuro (tasa de confirmación, zonas con salidas repetidas, etc.).

### Mantenimiento

- **API key de AEMET** caduca cada 3 meses (próxima: 25/11/2026) — renovar en
  https://opendata.aemet.es y actualizar el secreto `AEMET_API_KEY` en
  GitHub Secrets.
- **API key de Meteocat** caduca 31/08/2027 — renovar en
  https://apidocs.meteocat.gencat.cat y actualizar `METEOCAT_API_KEY`.
- **Token de GitHub del Worker** caduca el 24/11/2026 — regenerar en
  https://github.com/settings/tokens?type=beta (mismos permisos: Contents
  read/write solo en `bolets-catalunya`) y actualizar `GITHUB_TOKEN` en el
  Worker de Cloudflare.
- La web avisa automáticamente en rojo cuando a cualquiera de estas
  credenciales le quedan 15 días o menos.
- El backend se ejecuta cada 6 horas vía GitHub Actions; también se puede
  lanzar a mano desde "Actions" → "Actualitzar dades de bolets" → "Run workflow".

### Fallos reales detectados y corregidos durante el desarrollo

Por si hace falta depurar de nuevo: uso de temperatura media en vez de
mínima nocturna; "días desde lluvia" que solo miraba el último chubasco en
vez del inicio de la tanda completa; ventana de lluvia acumulada fija a 10
días que perdía agua real en tandas largas; funciones que quedaron
fusionadas o con su `def` accidentalmente borrado al editar el archivo
(dos veces — sin error de sintaxis, solo fallo en producción); Meteoclimatic
usando el campo de lluvia equivocado del XML y sin coordenadas en el feed;
API de Meteocat exigiendo el parámetro `data` junto con `estat`, y
anidando las lecturas dentro de `variables[0].lectures`; scoring
devolviendo menos valores de los esperados en el caso de hábitat
incompatible; triangulación contando la misma estación varias veces sin
deduplicar; modelo de DeepSeek retirado sin aviso (`deepseek-chat` →
`deepseek-v4-flash`).

### Ideas evaluadas y aparcadas deliberadamente

Un análisis externo detallado (ChatGPT) señaló varias mejoras de fondo que
se decidió no abordar todavía, por ser más apropiadas cuando haya bastante
más volumen de datos de campo real: pesos del scoring calibrados por
especie en vez de globales (actualmente los rangos de lluvia/temperatura
sí son por especie, pero los pesos de cada componente son iguales para
las 10); convertir los componentes en curvas de respuesta biológica en
vez de tramos lineales; una rejilla geográfica adaptativa en vez de
puntos fijos cada ~10km; orientación y pendiente del terreno vía modelo
digital de elevación; corregir el sesgo de que la gente solo visita zonas
con puntuación alta (podría atacarse en el futuro sugiriendo
deliberadamente "zonas de validación" con puntuación media, para no
sesgar el aprendizaje del sistema); incertidumbre explícita en la
estimación de lluvia triangulada (ej. "18mm ±9mm"); y evaluar modelos de
machine learning una vez exista un conjunto de datos de validación
suficientemente grande y no sesgado.
