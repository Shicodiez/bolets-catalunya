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
   encontréis) con el botón de "Marcar en el mapa" — cuantos más hallazgos
   registremos, mejor se irá afinando el modelo con datos reales vuestros,
   no solo con teoría.

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
- `data/evolucion.json` — snapshot diario de la mejor puntuación por zona, 30 días.
- `data/hallazgos.json` — hallazgos reales registrados por los usuarios. Se actualiza vía el Worker.
- `web/index.html` — la web: login, mapa, deslizador de umbral, formulario de hallazgos, panel de precisión histórica, explicaciones de DeepSeek.
- `worker/index.js` — código del Worker de Cloudflare.
- `.github/workflows/actualitzar.yml` — automatización que ejecuta el backend cada 6 horas.

### Fuentes de datos usadas (todas gratuitas)

| Fuente | Para qué se usa |
|---|---|
| **Open-Meteo** | Histórico de lluvia y temperatura (16 días); también humedad real del suelo y evapotranspiración (variables `hourly`), sin API key |
| **AEMET OpenData** | Contraste con la estación real más cercana a cada zona (API key, caduca cada 3 meses) |
| **Meteoclimatic** | Segunda red de estaciones amateur; se geocodifica con Nominatim porque el feed no da coordenadas |
| **ICGC** | Tipo de bosque genérico (coníferas/frondosas/perennifolias), vía WMS |
| **VEGETACIO** (Generalitat) | Especie exacta de árbol, refinando el dato del ICGC |
| **GBIF / FungaCAT** | Histórico real de avistamientos: temporada real (mes) y altitud típica de cada especie |
| **Nominatim (OpenStreetMap)** | Nombres de lugar ↔ coordenadas, en ambos sentidos |
| **DeepSeek** | Explicaciones en lenguaje natural del "por qué" de una puntuación, a petición del usuario — nunca decide el cálculo |

### Cómo funciona el cálculo

Para cada uno de los ~390 puntos de la rejilla, y cada una de las 10
especies del catálogo, se calcula una **puntuación de 0 a 100** sumando
evidencia de seis componentes:

- **Lluvia acumulada** (0-22 pts) desde el inicio de la tanda de lluvias actual
- **Días desde que empezó a llover** (0-25 pts) — cada especie tiene su rango
- **Temperatura mínima nocturna** (0-20 pts) — no la media del día
- **Humedad real del suelo** (0-8 pts) — distingue si el agua caída sigue en
  la tierra o se ha perdido (sequía previa, evapotranspiración), con bonus
  si la tendencia es a humedecerse y penalización si se está secando
- **Temporada real de la especie** (0-15 pts) según GBIF, por mes y altitud
- **Corroboración entre fuentes** (0-10 pts) — bonus si varias estaciones
  reales (triangulación IDW de AEMET+Meteoclimatic) confirman la lluvia

El único requisito "duro" (que descarta una especie por completo) es el
tipo de bosque — el resto es gradual, así que un solo dato flojo de una
fuente no hace desaparecer una especie con buena evidencia por lo demás.

Junto a cada puntuación se muestra un nivel de **confianza** (🟢🟠🔴),
independiente del valor numérico: refleja cuánta evidencia real la
respalda (registros GBIF, estaciones triangulando), para no transmitir una
falsa sensación de precisión.

La web muestra las zonas por encima de un **umbral ajustable** (por defecto
70, con deslizador).

### Triangulación de estaciones (IDW)

En vez de usar solo la estación real más cercana a cada zona, se combinan
hasta 4 estaciones (AEMET + Meteoclimatic) ponderadas por 1/distancia² —
las más cercanas pesan más, pero las algo más lejanas también aportan.
Esto da una estimación de lluvia del día más fiable que depender de una
sola estación aislada, y aumenta la confianza reportada cuando hay 2+
estaciones de acuerdo.

### Evolución y precisión histórica

Cada día se guarda un snapshot de la mejor puntuación de cada zona. La web
compara con hace 7 días y marca **▲/▼** en las zonas que más han subido o
bajado. Además, cuando hay suficientes hallazgos registrados, el backend
cruza cada uno con la puntuación que tenía esa zona ese día y calcula un
**% de precisión real** del modelo, desglosado por franja de puntuación.

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
- `DEEPSEEK_API_KEY` — key de la API de DeepSeek.

### Control de acceso

La web pide una contraseña antes de mostrar nada:
- Guardada como Secret `APP_PASSWORD` en el Worker — nunca en el código.
- Al introducirla, el navegador recibe un token de sesión firmado (30 días).
- **Para revocar el acceso a todo el mundo de golpe**: cambia
  `APP_PASSWORD` en el Worker. Todas las sesiones antiguas dejan de valer
  al instante.

### Registro de hallazgos propios

Desde la web se marca en el mapa el punto exacto: especie, altitud (tramos
de 50m), tipo de árbol, fecha, cantidad (mucho/poco/nada). El nombre del
lugar se rellena solo (geocodificación inversa) pero es editable. Cada
hallazgo aparece como marcador propio en el mapa, guardado de forma
permanente vía el Worker.

### Mantenimiento

- **API key de AEMET** caduca cada 3 meses (próxima: 25/11/2026) — renovar en
  https://opendata.aemet.es y actualizar `AEMET_API_KEY` en GitHub Secrets.
- **Token de GitHub del Worker** caduca el 24/11/2026 — regenerar en
  https://github.com/settings/tokens?type=beta y actualizar `GITHUB_TOKEN`
  en el Worker.
- La web avisa automáticamente en rojo cuando a cualquiera de estas
  credenciales le quedan 15 días o menos.
- Meteocat (XEMA) pendiente de aprobación — cuando llegue, se puede sumar
  como fuente adicional de contraste.
- El backend se ejecuta cada 6 horas vía GitHub Actions; también se puede
  lanzar a mano desde "Actions" → "Actualitzar dades de bolets" → "Run workflow".

### Fallos reales detectados y corregidos durante el desarrollo

Por si hace falta depurar de nuevo: uso de temperatura media en vez de
mínima nocturna; "días desde lluvia" que solo miraba el último chubasco en
vez del inicio de la tanda completa; ventana de lluvia acumulada fija a 10
días que perdía agua real en tandas largas; un bug de edición donde una
función quedó fusionada dentro de otra sin dar error de sintaxis;
Meteoclimatic usando el campo de lluvia equivocado del XML; el feed de
Meteoclimatic sin coordenadas (requirió geocodificación); y una función de
scoring que devolvía menos valores de los esperados en el caso de hábitat
incompatible, rompiendo el proceso completo en producción.
