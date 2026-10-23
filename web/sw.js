// Service worker de la app de setas.
//
// Qué hace: guarda en el móvil, para poder abrirlos SIN cobertura una vez se han abierto alguna vez con conexión:
//   · la página de la guía de identificación (guia.html), sus fotos (carpeta fotos/) y la propia pantalla de la app;
//   · la librería del mapa (Leaflet, de unpkg.com), sin la cual la pantalla de la app no arranca;
//   · la ÚLTIMA copia de los datos del predictor (data/resultats.json), que SOLO se usa cuando no hay red.
//
// Qué NO hace, a propósito: no guarda los mapas de fondo ni la identificación por foto. Con conexión, las páginas y los
// datos se piden primero a la red («network-first»): la copia guardada es solo el plan B cuando no hay red o tarda demasiado,
// y la app avisa («Sin conexión… datos guardados de …») para que no se confunda con datos de hoy.
// Las fotos de la guía (que casi nunca cambian) se sirven al instante desde la copia guardada y se refrescan
// en segundo plano. La identificación por foto (Worker) NO pasa por aquí: va siempre directa a la red.

const CACHE = 'bolets-offline-v2';
const PRECACHE = ['./', 'index.html', 'guia.html', 'manifest.json', 'icon-192.png', 'fotos/creditos.json'];
const ESPERA_RED_MS = 4000; // sin cobertura buena la red puede colgarse: pasado este tiempo usamos la copia guardada
const ESPERA_DATOS_MS = 10000; // los datos pesan bastante: damos más margen antes de usar la copia
const LEAFLET = ['https://unpkg.com/leaflet@1.9.4/dist/leaflet.js', 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    // Uno a uno: si un archivo falla (por ejemplo no existe) no se pierde el resto.
    await Promise.all(PRECACHE.map(async (url) => {
      try { await cache.add(new Request(url, { cache: 'reload' })); } catch (e) { /* se ignora */ }
    }));
    // Leaflet viene de otro dominio: se guarda con fetch + put (cache.add no admite respuestas «opacas»).
    await Promise.all(LEAFLET.map(async (url) => {
      try { const r = await fetch(url); if (r && r.ok) await cache.put(url, r); } catch (e) { /* se ignora */ }
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const nombres = await caches.keys();
    await Promise.all(nombres.filter((n) => n !== CACHE).map((n) => caches.delete(n)));
    await self.clients.claim();
  })());
});

function esPaginaOfflineable(request, url) {
  if (request.method !== 'GET') return false;
  if (url.origin !== self.location.origin) return false;
  if (request.mode === 'navigate') return true;
  return /(?:^|\/)(guia\.html|index\.html|manifest\.json|icon-192\.png)$/.test(url.pathname) || esCreditos(url) || esFoto(url);
}
function esLeaflet(url) { return url.hostname === 'unpkg.com' && url.pathname.indexOf('/leaflet@1.9.4/dist/') === 0; }
function esDatos(url) { return url.origin === self.location.origin && /(?:^|\/)data\/resultats\.json$/.test(url.pathname); }
// Los datos se guardan SIEMPRE bajo la misma dirección, sin el «?t=…» con que la app evita copias viejas del navegador
// (si no, cada apertura de la app guardaría otra copia de 16 MB).
function claveDatos(url) { return new Request(url.origin + url.pathname); }

function esCreditos(url) { return /(?:^|\/)fotos\/creditos\.json$/.test(url.pathname); }
function esFoto(url) { return /(?:^|\/)fotos\/[^/]+\.jpg$/.test(url.pathname); }

// Fotos: copia guardada primero (rápido y sin cobertura), y se actualiza en segundo plano si hay red.
async function copiaPrimero(event) {
  const cache = await caches.open(CACHE);
  const copia = await cache.match(event.request);
  const actualizar = fetch(event.request).then((r) => {
    if (r && r.ok) cache.put(event.request, r.clone()).catch(() => {});
    return r;
  }).catch(() => null);
  if (copia) { event.waitUntil(actualizar); return copia; }
  return (await actualizar) || Response.error();
}

async function redPrimero(request) {
  const cache = await caches.open(CACHE);
  try {
    const respuesta = await new Promise((resolve, reject) => {
      const reloj = setTimeout(() => reject(new Error('timeout')), ESPERA_RED_MS);
      fetch(request).then((r) => { clearTimeout(reloj); resolve(r); }, (e) => { clearTimeout(reloj); reject(e); });
    });
    if (respuesta && respuesta.ok) {
      cache.put(request, respuesta.clone()).catch(() => {});
      return respuesta;
    }
    // Respuesta con error del servidor: si hay copia buena, mejor esa.
    const copia = await cache.match(request, { ignoreSearch: true });
    return copia || respuesta;
  } catch (e) {
    const copia = await cache.match(request, { ignoreSearch: true });
    if (copia) return copia;
    if (request.mode === 'navigate') {
      const guia = await cache.match('guia.html');
      if (guia) return guia;
    }
    return Response.error();
  }
}

// Leaflet: copia guardada primero (no cambia nunca: la versión va en la dirección), y se guarda lo que llegue de la red.
async function leafletCopiaPrimero(request) {
  const cache = await caches.open(CACHE);
  const copia = await cache.match(request.url);
  if (copia) return copia;
  const r = await fetch(request);
  if (r && (r.ok || r.type === 'opaque')) cache.put(request.url, r.clone()).catch(() => {});
  return r;
}

// Datos del predictor: primero la red (con margen) y, si no hay o no llega, la última copia guardada, marcada con la
// cabecera X-Bolets-Copia para que la pantalla avise de que no son datos de hoy.
async function datosRedPrimero(request, url) {
  const cache = await caches.open(CACHE);
  const clave = claveDatos(url);
  try {
    const respuesta = await new Promise((resolve, reject) => {
      const reloj = setTimeout(() => reject(new Error('timeout')), ESPERA_DATOS_MS);
      fetch(request).then((r) => { clearTimeout(reloj); resolve(r); }, (e) => { clearTimeout(reloj); reject(e); });
    });
    if (respuesta && respuesta.ok) { cache.put(clave, respuesta.clone()).catch(() => {}); return respuesta; }
    const copia = await cache.match(clave);
    return copia ? marcarCopia(copia) : respuesta;
  } catch (e) {
    const copia = await cache.match(clave);
    return copia ? marcarCopia(copia) : Response.error();
  }
}
function marcarCopia(copia) {
  const cab = new Headers(copia.headers);
  cab.set('X-Bolets-Copia', '1');
  return new Response(copia.body, { status: copia.status, statusText: copia.statusText, headers: cab });
}

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (event.request.method === 'GET' && esLeaflet(url)) { event.respondWith(leafletCopiaPrimero(event.request)); return; }
  if (event.request.method === 'GET' && esDatos(url)) { event.respondWith(datosRedPrimero(event.request, url)); return; }
  if (!esPaginaOfflineable(event.request, url)) return; // todo lo demás (mapas, Worker) va directo a la red
  event.respondWith(esFoto(url) ? copiaPrimero(event) : redPrimero(event.request));
});
