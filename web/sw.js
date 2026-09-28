// Service worker mínimo: existe solo para que el navegador permita instalar
// la web como app. NO cachea nada a propósito — la web y los datos se piden
// siempre en vivo, para no repetir el problema de ver una versión antigua.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => { /* pasa directo a la red, sin caché */ });
