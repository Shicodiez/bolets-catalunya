# Predictor de bolets — Catalunya

## Para quien la va a usar

Esta web (y también una app Android instalable) te dice, según el tiempo
real de los últimos días (lluvia, temperatura, y hasta la humedad real de
la tierra), en qué zonas de Catalunya es más probable encontrar cada tipo
de bolet ahora mismo.

**Cómo usarla:**
1. Escribe tu email (tiene que ser uno de los autorizados) y te llegará un
   código de acceso por correo — introdúcelo para entrar.
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
6. Cuando salgáis al monte, marcad en el mapa el resultado de la salida
   (encontrasteis mucho, poco, o buscasteis sin encontrar nada) — cuantos
   más registremos, mejor se irá afinando el modelo con datos reales
   vuestros. Estas salidas no se ven en el mapa (para no saturarlo), pero
   sí cuentan por detrás.

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
- `SESSION_SECRET` — texto aleatorio largo, firma las sesiones y los códigos de acceso. No lo escribe ni conoce nadie, solo lo usa el Worker internamente.
- `AUTHORIZED_EMAILS` — lista de emails con acceso, separados por comas.
- `BREVO_API_KEY` — key de la API de Brevo, usada para enviar los códigos de acceso por email.
- `SENDER_EMAIL` — el email verificado en Brevo desde el que se envían los códigos.
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
(10KB), y un pequeño retraso tras un intento fallido para encarecer
intentos automatizados. Un rate limiting completo por IP requeriría
añadir Cloudflare KV, que de momento no se ha considerado necesario para
el volumen de uso actual.

**IMPORTANTE — `worker/index.js` no se despliega solo:** el archivo en el
repositorio de GitHub es solo la copia de referencia. Para que un cambio
en el Worker tenga efecto de verdad, hay que pegarlo directamente en
Cloudflare (Workers & Pages → `bolets-hallazgos` → Edit code → pegar →
Deploy). Subirlo a GitHub por sí solo no actualiza el Worker real.

### Control de acceso

La web pide un email antes de mostrar nada — no hay contraseña compartida:
1. La persona escribe su email.
2. El Worker comprueba si ese email está en `AUTHORIZED_EMAILS`. Si no,
   se rechaza directamente, sin enviar nada.
3. Si está autorizado, se genera un código de 6 dígitos (válido 10
   minutos) y se envía por email vía Brevo.
4. Al introducir el código correcto, el navegador recibe un token de
   sesión firmado (30 días).

El código no se guarda en ningún sitio (ni base de datos ni caché): se
deriva con HMAC del email y una ventana de tiempo de 10 minutos usando
`SESSION_SECRET`, y se vuelve a calcular para comprobarlo — así no hace
falta Cloudflare KV ni ningún almacenamiento adicional.

- **Para dar acceso a alguien nuevo**: añade su email a `AUTHORIZED_EMAILS`
  en el Worker (separados por comas, con o sin espacios, da igual).
- **Para quitarle el acceso a alguien**: quita su email de esa lista. No
  podrá pedir un código nuevo, pero una sesión ya activa suya seguirá
  siendo válida hasta que expire (máximo 30 días).
- **Para revocar el acceso a todo el mundo de golpe**, incluidas sesiones
  ya activas: cambia `SESSION_SECRET` en el Worker. Todos los tokens
  firmados con el valor anterior dejan de ser válidos al instante.

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

Las salidas guardadas **no se muestran en el mapa** — a propósito, para
que no compitan visualmente con los puntos de predicción del modelo (con
miles de registros, el mapa quedaría inservible). Los datos siguen
alimentando la tasa de confirmación y la detección de zonas con salidas
repetidas por detrás, simplemente no hay representación visual de cada
salida individual.

Una vez guardada, **una salida no se puede borrar por ningún medio** — ni
desde la web ni llamando directamente al Worker (no existe endpoint para
ello). Es una decisión deliberada: protege el historial real que alimenta
la evolución y la tasa de confirmación del modelo, evitando que datos
incómodos (una mala predicción, por ejemplo) se puedan eliminar
selectivamente.

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

### App Android (APK)

Existe un APK Android real de la app, generado con
[Capacitor](https://capacitorjs.com/). No es una reescritura — es un
envoltorio nativo que abre la misma web en vivo
(`https://shicodiez.github.io/bolets-catalunya/web/`), configurado en
`server.url` dentro de `capacitor.config.json`. Esto significa que
**cualquier cambio en `web/index.html` (o en cómo se genera
`resultats.json`) se ve reflejado automáticamente la próxima vez que se
abre la app**, sin tener que generar ni reinstalar un APK nuevo.

Solo hace falta generar un APK nuevo si se cambia algo "nativo" de verdad:
el icono, el nombre de la app, la URL a la que apunta, o si en el futuro
se añaden capacidades que una web normal no tiene (notificaciones push,
cámara, etc.).

**Proyecto fuente del APK**: carpeta separada (`bolets-apk` en el
ordenador del usuario, no forma parte de este repositorio) con
`capacitor.config.json`, `package.json`, y la carpeta `android/` generada
por Capacitor. El icono se generó con
[icon.kitchen](https://icon.kitchen) a partir de un diseño simple (fondo
verde, seta naranja con tallo blanco).

Para generar un APK nuevo (solo si hace falta): `npx cap sync android` →
abrir con `npx cap open android` → en Android Studio, **Build → Generate
App Bundles or APKs → Generate APK(s)**. El archivo queda en
`android/app/build/outputs/apk/debug/app-debug.apk`, listo para compartir
e instalar directamente (Android pedirá permitir "fuentes desconocidas"
la primera vez, por no venir de Google Play).

**Nota real del proceso**: la primera vez que se generó, `capacitor.config.ts`
(formato TypeScript) dio un error de compatibilidad con la versión de
Node/TypeScript del sistema — se resolvió usando `capacitor.config.json`
(JSON puro) en su lugar, que Capacitor acepta igual de bien y no necesita
compilarse.

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
