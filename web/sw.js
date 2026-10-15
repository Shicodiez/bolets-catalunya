// Service worker de la app de setas.
//
// Qué hace (y solo esto): guarda en el móvil la página de la guía de identificación (guia.html), sus fotos
// (carpeta fotos/) y la propia pantalla de la app, para poder abrirlas SIN cobertura una vez se han abierto
// alguna vez con conexión.
//
// Qué NO hace, a propósito: no guarda los datos del mapa ni las puntuaciones. Esos se piden siempre en vivo,
// para no volver a ver una versión antigua. Con conexión, las páginas también se piden primero a la red
// («network-first»): la caché es solo el plan B cuando no hay red o tarda demasiado.
// Las fotos de la guía (que casi nunca cambian) se sirven al instante desde la copia guardada y se refrescan
// en segundo plano. La identificación por foto (Worker) NO pasa por aquí: va siempre directa a la red.

const CACHE = 'bolets-offline-v2';
const PRECACHE = ['./', 'guia.html', 'manifest.json', 'icon-192.png', 'fotos/creditos.json'];
const ESPERA_RED_MS = 4000; // sin cobertura buena la red puede colgarse: pasado este tiempo usamos la copia guardada

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    // Uno a uno: si un archivo falla (por ejemplo no existe) no se pierde el resto.
    await Promise.all(PRECACHE.map(async (url) => {
      try { await cache.add(new Request(url, { cache: 'reload' })); } catch (e) { /* se ignora */ }
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

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (!esPaginaOfflineable(event.request, url)) return; // todo lo demás (datos, mapas, Worker) va directo a la red
  event.respondWith(esFoto(url) ? copiaPrimero(event) : redPrimero(event.request));
});
