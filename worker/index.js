/**
 * Worker de Cloudflare: recibe una salida des de la web de bolets-catalunya
 * i el desa de forma permanent i IRREVERSIBLE al fitxer data/hallazgos.json
 * del repositori de GitHub, fent servir un token guardat de forma segura
 * com a "Secret" (GITHUB_TOKEN), mai visible des del navegador.
 *
 * Flux:
 *  1. La web envia un POST amb la salida (JSON).
 *  2. Aquest Worker llegeix el fitxer actual de GitHub (per obtenir el sha).
 *  3. Afegeix la salida nova a la llista.
 *  4. Torna a pujar el fitxer sencer a GitHub amb el sha correcte.
 *
 * No existeix cap endpoint per esborrar: un cop registrada, una salida
 * queda per sempre — decisió deliberada per protegir l'historial que
 * alimenta l'evolució i la tasa de confirmació del model.
 */

/**
 * Utilitat de firma HMAC, base tant del sistema de sessió com del sistema
 * de codis d'un sol ús per email.
 */
async function hmacBytes(secret, message) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  return new Uint8Array(await crypto.subtle.sign("HMAC", key, enc.encode(message)));
}

async function hmacSign(secret, message) {
  const bytes = await hmacBytes(secret, message);
  return btoa(String.fromCharCode(...bytes));
}

// Comparació en temps constant (evita filtrar, pel temps de resposta, quants
// caràcters d'un codi o d'una signatura coincideixen).
function timingSafeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/**
 * Sistema d'autenticació per email amb codi d'un sol ús (substitueix la
 * contrasenya compartida — el Master controla qui pot entrar mitjançant
 * una llista d'emails autoritzats, no una contrasenya que es pugui
 * compartir sense control).
 *
 * El codi de 6 xifres es genera de forma "sense estat" (no es desa enlloc):
 * es deriva amb HMAC de l'email + una finestra de temps de 10 minuts +
 * un secret intern del Worker. Per verificar-lo, el Worker torna a calcular
 * quin codi esperaria per a aquell email en aquesta finestra (i l'anterior,
 * per tolerància si el codi va arribar just al canvi de finestra) i
 * comprova si coincideix — no cal Cloudflare KV ni cap base de dades.
 */

const CODE_WINDOW_MINUTES = 10;

function normalizeEmail(email) {
  return typeof email === "string" ? email.trim().toLowerCase() : "";
}

function isEmailAuthorized(env, email) {
  const list = (env.AUTHORIZED_EMAILS || "")
    .split(",")
    .map((e) => e.trim().toLowerCase())
    .filter(Boolean);
  return list.includes(normalizeEmail(email));
}

async function computeCodeForWindow(env, email, windowIndex) {
  // Codi de 6 xifres UNIFORME (000000-999999): es llegeixen paraules de 32 bits
  // del HMAC i es descarten les que caurien en el "residu" final que
  // faria alguns codis una mica més probables (rebuig de biaix). Abans es
  // treien els dígits del Base64 del hash: en ~31% dels casos hi havia menys
  // de 6 dígits i el codi s'omplia amb zeros (menys entropia real).
  const bytes = await hmacBytes(env.SESSION_SECRET, `code:${normalizeEmail(email)}:${windowIndex}`);
  const LIMIT = 4294000000; // el múltiple de 1.000.000 més gran que cap dins de 2^32
  for (let i = 0; i + 4 <= bytes.length; i += 4) {
    const n = ((bytes[i] << 24) | (bytes[i + 1] << 16) | (bytes[i + 2] << 8) | bytes[i + 3]) >>> 0;
    if (n < LIMIT) return String(n % 1000000).padStart(6, "0");
  }
  // Pràcticament impossible (probabilitat ~1e-70): torna a derivar amb un sufix.
  const extra = await hmacBytes(env.SESSION_SECRET, `code2:${normalizeEmail(email)}:${windowIndex}`);
  const n = ((extra[0] << 24) | (extra[1] << 16) | (extra[2] << 8) | extra[3]) >>> 0;
  return String(n % 1000000).padStart(6, "0");
}

async function generateLoginCode(env, email) {
  const windowIndex = Math.floor(Date.now() / (CODE_WINDOW_MINUTES * 60 * 1000));
  return computeCodeForWindow(env, email, windowIndex);
}

async function verifyLoginCode(env, email, code) {
  const currentWindow = Math.floor(Date.now() / (CODE_WINDOW_MINUTES * 60 * 1000));
  // S'accepta també la finestra anterior, per si el codi va arribar just
  // quan estava a punt de canviar (marge de fins a ~10 minuts addicionals).
  for (const w of [currentWindow, currentWindow - 1]) {
    const expected = await computeCodeForWindow(env, email, w);
    if (timingSafeEqual(expected, code)) return true;
  }
  return false;
}

/**
 * LIMITACIÓ D'INTENTS (anti força bruta i anti abús). Necessita un "KV namespace"
 * de Cloudflare (gratuït) enllaçat al Worker amb el nom LIMITS. Si no està
 * enllaçat, el Worker funciona igual però SENSE límits (es deixa constància
 * al log). Els comptadors són per finestra fixa i caduquen soles.
 *
 *  - Codis demanats:  5 per hora per email i 10 per hora per IP
 *  - Intents fallits: 5 per 15 min per email i 15 per 15 min per IP (després, bloqueig)
 *  - Explicacions DeepSeek: 150 per dia en total (protegeix el cost de l'API)
 *  - Identificacions per foto: 120 per dia en total (a més, Workers AI té el seu propi cupo gratuït diari)
 *
 * KV no és atòmic: dues peticions simultànies podrien colar-se una xifra més
 * enllà del límit. Per a aquest ús és irrellevant.
 */
const LIMITS_CFG = {
  codeReqEmail: { max: 5, windowSec: 3600 },
  codeReqIp: { max: 10, windowSec: 3600 },
  authFailEmail: { max: 5, windowSec: 900 },
  authFailIp: { max: 15, windowSec: 900 },
  explainDay: { max: 150, windowSec: 86400 },
  identifyDay: { max: 120, windowSec: 86400 },
};

function clientIp(request) {
  return request.headers.get("CF-Connecting-IP") || "unknown";
}

function limitKey(name, id, windowSec) {
  const windowIndex = Math.floor(Date.now() / (windowSec * 1000));
  return `rl:${name}:${id}:${windowIndex}`;
}

// Mira si encara hi ha marge (sense comptar-hi). Retorna {allowed, enabled}.
async function limitCheck(env, name, id) {
  const cfg = LIMITS_CFG[name];
  if (!env.LIMITS) return { allowed: true, enabled: false };
  try {
    const raw = await env.LIMITS.get(limitKey(name, id, cfg.windowSec));
    const count = raw ? parseInt(raw, 10) || 0 : 0;
    return { allowed: count < cfg.max, enabled: true };
  } catch (e) {
    // Si el KV falla, per a l'autenticació és més segur denegar que deixar passar.
    return { allowed: false, enabled: true, error: true };
  }
}

// Suma 1 al comptador. No llança mai (un error de KV no ha de trencar la resposta).
async function limitHit(env, name, id) {
  const cfg = LIMITS_CFG[name];
  if (!env.LIMITS) return;
  try {
    const key = limitKey(name, id, cfg.windowSec);
    const raw = await env.LIMITS.get(key);
    const count = raw ? parseInt(raw, 10) || 0 : 0;
    await env.LIMITS.put(key, String(count + 1), { expirationTtl: Math.max(cfg.windowSec * 2, 60) });
  } catch (e) {
    console.log(`Límit ${name}: no s'ha pogut escriure al KV (${e.message})`);
  }
}

function tooManyRequests(message) {
  return new Response(JSON.stringify({ error: message }), {
    status: 429,
    headers: { ...corsHeaders(), "Content-Type": "application/json", "Retry-After": "900" },
  });
}

async function sendLoginCodeEmail(env, email, code) {
  const res = await fetch("https://api.brevo.com/v3/smtp/email", {
    method: "POST",
    headers: {
      "api-key": env.BREVO_API_KEY,
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
    body: JSON.stringify({
      sender: { email: env.SENDER_EMAIL, name: "Predictor de Setas" },
      to: [{ email }],
      subject: "Tu código de acceso — Predictor de Setas",
      htmlContent: `<p>Tu código de acceso es:</p><p style="font-size:28px;font-weight:bold;letter-spacing:4px">${code}</p><p>Caduca en ${CODE_WINDOW_MINUTES} minutos.</p>`,
    }),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Brevo ha fallat (status ${res.status}): ${errText}`);
  }
}

/**
 * Sistema de sessió: un cop verificat el codi, es genera un token signat
 * (HMAC amb un secret intern del Worker) amb una data de caducitat. El
 * navegador el desa i el reenvia a cada petició; el Worker només ha de
 * verificar la signatura, sense estat.
 */

const SESSION_DAYS = 30;

async function createSessionToken(env) {
  const expires = Date.now() + SESSION_DAYS * 24 * 60 * 60 * 1000;
  const payload = `${expires}`;
  const sig = await hmacSign(env.SESSION_SECRET, payload);
  return `${payload}.${sig}`;
}

async function verifySessionToken(env, token) {
  if (!token || !token.includes(".")) return false;
  const [payload, sig] = token.split(".");
  const expected = await hmacSign(env.SESSION_SECRET, payload);
  if (!timingSafeEqual(sig, expected)) return false;
  const expires = parseInt(payload, 10);
  if (isNaN(expires) || Date.now() > expires) return false;
  return true;
}

const DEEPSEEK_URL = "https://api.deepseek.com/chat/completions";

function sanitizeForPrompt(value, maxLen) {
  if (typeof value === "number") return isFinite(value) ? value : 0;
  if (typeof value === "string") return value.slice(0, maxLen);
  return "";
}

function validateExplainRequest(zoneData) {
  if (typeof zoneData !== "object" || zoneData === null) return null;
  return {
    zoneName: sanitizeForPrompt(zoneData.zoneName, 80),
    speciesName: sanitizeForPrompt(zoneData.speciesName, 60),
    score: typeof zoneData.score === "number" ? Math.max(0, Math.min(100, zoneData.score)) : 0,
    confidence: ["alta", "mitjana", "baja"].includes(zoneData.confidence) ? zoneData.confidence : "baja",
    breakdown: typeof zoneData.breakdown === "object" && zoneData.breakdown !== null ? zoneData.breakdown : {},
    rain10d: typeof zoneData.rain10d === "number" ? zoneData.rain10d : 0,
    minTemp: typeof zoneData.minTemp === "number" ? zoneData.minTemp : 0,
    maxTemp: typeof zoneData.maxTemp === "number" ? zoneData.maxTemp : null,
    // Textos cortos del backend con lo que FRENA la puntuación (todavía pronto,
    // época, altitud, calor, suelo...). Se limpian y se acotan antes de usarlos en el prompt.
    limits: Array.isArray(zoneData.limits) ? zoneData.limits.slice(0, 3).map(t => sanitizeForPrompt(t, 240)).filter(t => t) : [],
    daysSinceRain: typeof zoneData.daysSinceRain === "number" ? zoneData.daysSinceRain : 0,
    treeLabel: sanitizeForPrompt(zoneData.treeLabel, 60),
    scoreChange: typeof zoneData.scoreChange === "object" ? zoneData.scoreChange : null,
  };
}

async function explainWithDeepSeek(env, zoneData) {
  const { zoneName, speciesName, score, confidence, breakdown, rain10d, minTemp, maxTemp, limits, daysSinceRain, treeLabel, scoreChange } = zoneData;

  const changeText = scoreChange
    ? `La puntuación ha cambiado ${scoreChange.change >= 0 ? '+' : ''}${scoreChange.change} puntos en los últimos 7 días (de ${scoreChange.previous} a ${scoreChange.current}).`
    : '';

  const prompt = `Eres un asistente que explica, en 2-3 frases claras y en castellano, por qué una zona de Catalunya tiene una puntuación concreta para encontrar una especie de bolet. NO decides ni recalculas nada, solo interpretas los datos que te doy. No inventes datos que no aparezcan aquí.

Zona: ${zoneName} (${treeLabel})
Especie: ${speciesName}
Puntuación: ${score}/100
Confianza: ${confidence}
Desglose de la puntuación (suma de evidencias): lluvia=${breakdown.pluja}, días desde lluvia=${breakdown.dies_pluja}, temperatura=${breakdown.temperatura}, temporada=${breakdown.temporada}, corroboración entre fuentes=${breakdown.corroboracio}
Factor limitante final: ${breakdown.limitants !== undefined ? breakdown.limitants : 1} (1 = nada frena la puntuación; 0,5 = la puntuación se reduce a la mitad por los motivos de abajo)
Datos meteorológicos: ${rain10d}mm de lluvia desde el inicio de la lluvia principal, ${minTemp}°C de mínima nocturna${maxTemp !== null ? " y " + maxTemp + "°C de máxima (medias de los últimos 7 días)" : ""}, ${daysSinceRain} días desde la lluvia principal (el grueso del agua, no el último chubasco)
${limits && limits.length ? "Lo que frena la puntuación: " + limits.join("; ") : "Nada frena especialmente la puntuación."}
${changeText}

Si hay factores que frenan la puntuación, explícalos primero y con claridad (por ejemplo, que todavía es pronto o que el suelo no le conviene): es lo más útil para el aficionado.

Escribe la explicación en tono cercano, como si hablaras con un aficionado a los bolets, sin tecnicismos innecesarios.`;

  const res = await fetch(DEEPSEEK_URL, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${env.DEEPSEEK_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "deepseek-flash", // deepseek-v4-flash es va retirar el 10/09/2026 (substituït per V4.1 Flash);
      // "deepseek-flash" és el nom de model oficial actual — l'antic queda enrutat
      // temporalment per compatibilitat, però pot donar respostes inesperades
      messages: [{ role: "user", content: prompt }],
      temperature: 0.5,
      max_tokens: 300,
      thinking: { type: "disabled" }, // IMPORTANT: els models V4/V4.1 Flash tenen el "thinking
      // mode" activat per defecte i poden gastar-se centenars de tokens "pensant" abans de
      // respondre — amb max_tokens=200 això esgotava tot el pressupost sense arribar mai a
      // escriure la resposta final (content buit). Confirmat amb la documentació oficial de
      // DeepSeek: la manera correcta de desactivar-ho és aquest paràmetre explícit.
    }),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`DeepSeek ha fallat (status ${res.status}): ${errText}`);
  }
  const data = await res.json();
  const content = data.choices?.[0]?.message?.content?.trim();
  if (!content) {
    // Abans es retornava silenciosament "No se ha podido generar una
    // explicación." com si fos un èxit (ok:true) — l'usuari ho veia com
    // l'explicació real sense cap pista de què havia fallat. Ara es
    // llança una excepció amb el cos real de la resposta, que la ruta
    // /explain ja captura i retorna com a error 502 amb el motiu.
    throw new Error(`DeepSeek ha respost sense contingut útil: ${JSON.stringify(data).slice(0, 300)}`);
  }
  return content;
}

const OWNER = "Shicodiez";
const REPO = "bolets-catalunya";
const FILE_PATH = "data/hallazgos.json";
const BRANCH = "main";

// Orígens permesos per fer peticions (evita que qualsevol web faci servir
// aquest Worker per escriure al teu repositori).
const ALLOWED_ORIGIN = "https://shicodiez.github.io";

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-Session-Token",
  };
}

async function githubRequest(env, method, body) {
  const url = `https://api.github.com/repos/${OWNER}/${REPO}/contents/${FILE_PATH}`;
  const headers = {
    "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
    "Accept": "application/vnd.github+json",
    "User-Agent": "bolets-hallazgos-worker",
    "Content-Type": "application/json",
  };
  const res = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  return res;
}

async function getCurrentFile(env) {
  const res = await githubRequest(env, "GET");
  if (res.status === 404) {
    return { sha: null, hallazgos: [] };
  }
  if (!res.ok) {
    throw new Error(`No s'ha pogut llegir el fitxer de GitHub (status ${res.status})`);
  }
  const data = await res.json();
  const decoded = atob(data.content.replace(/\n/g, ""));
  const utf8Decoded = decodeURIComponent(escape(decoded));
  let hallazgos = [];
  try {
    hallazgos = JSON.parse(utf8Decoded);
    if (!Array.isArray(hallazgos)) hallazgos = [];
  } catch (e) {
    hallazgos = [];
  }
  return { sha: data.sha, hallazgos };
}

function encodeUtf8Base64(str) {
  const utf8Bytes = new TextEncoder().encode(str);
  let binary = "";
  utf8Bytes.forEach((b) => (binary += String.fromCharCode(b)));
  return btoa(binary);
}

async function saveFile(env, hallazgos, sha, commitMessage) {
  const content = encodeUtf8Base64(JSON.stringify(hallazgos, null, 2));
  const body = {
    message: commitMessage,
    content,
    branch: BRANCH,
  };
  if (sha) body.sha = sha;
  const res = await githubRequest(env, "PUT", body);
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`No s'ha pogut desar a GitHub (status ${res.status}): ${errText}`);
  }
  return res.json();
}

// Rang geogràfic aproximat de Catalunya — qualsevol coordenada fora d'aquí
// es rebutja (evita que algú enviï coordenades absurdes o d'un altre lloc).
const CATALUNYA_BOUNDS = { latMin: 40.4, latMax: 42.95, lonMin: 0.05, lonMax: 3.4 };

// Llista blanca d'ids d'espècie vàlids — ha de coincidir amb SPECIES del backend.
const VALID_SPECIES_IDS = new Set([
  "rovellons", "ceps", "cep", "cepfosc", "cepestiu", "camagrocs", "trompetes", "oureig", "rossinyols",
  "colmenilles", "llengua", "pinetell", "fredolic", "escarlet", "llenega",
]);

const VALID_TREE_IDS = new Set(["pi", "roure", "alzina", "madrono", "suro", "faig", "avet", "mixt"]);

function isValidDateString(s) {
  if (typeof s !== "string") return false;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return false;
  const d = new Date(s + "T00:00:00Z");
  if (isNaN(d.getTime())) return false;
  // No s'accepten dates futures ni excessivament antigues (marge ampli per
  // permetre carregar hallazgos històrics reals).
  const now = new Date();
  const tenYearsAgo = new Date(now);
  tenYearsAgo.setFullYear(now.getFullYear() - 10);
  return d <= now && d >= tenYearsAgo;
}

function validateHallazgo(h) {
  if (typeof h !== "object" || h === null) return false;
  if (typeof h.lat !== "number" || typeof h.lng !== "number") return false;
  if (h.lat < CATALUNYA_BOUNDS.latMin || h.lat > CATALUNYA_BOUNDS.latMax) return false;
  if (h.lng < CATALUNYA_BOUNDS.lonMin || h.lng > CATALUNYA_BOUNDS.lonMax) return false;
  if (!["mucho", "poco", "nada"].includes(h.amount)) return false;

  // Fins a 5 espècies per sortida (speciesIds/speciesNames, arrays). Amb
  // "nada" (buscat i no trobat) la llista pot ser buida — pot ser una
  // cerca general sense objectiu concret. Amb "mucho"/"poco" cal indicar
  // com a mínim una espècie trobada.
  if (!Array.isArray(h.speciesIds) || !Array.isArray(h.speciesNames)) return false;
  if (h.speciesIds.length > 5 || h.speciesNames.length > 5) return false;
  if (h.speciesIds.length !== h.speciesNames.length) return false;
  if (h.amount !== "nada" && h.speciesIds.length === 0) return false;
  for (const id of h.speciesIds) {
    if (typeof id !== "string" || !VALID_SPECIES_IDS.has(id)) return false;
  }
  for (const name of h.speciesNames) {
    if (typeof name !== "string" || name.length > 80) return false;
  }

  if (typeof h.place !== "string" || !h.place.trim() || h.place.length > 120) return false;
  if (!isValidDateString(h.date)) return false;
  if (h.tree !== undefined && !VALID_TREE_IDS.has(h.tree)) return false;
  if (h.treeName !== undefined && (typeof h.treeName !== "string" || h.treeName.length > 60)) return false;
  if (h.alt !== undefined && (typeof h.alt !== "string" && typeof h.alt !== "number")) return false;
  return true;
}

// ---------------------------------------------------------------------------
// LECTURA DE RASGOS DE FOTOS (Cloudflare Workers AI: model de visió general, GRATUÏT dins del cupo diari de
// del compte; en el pla gratuït, quan s'acaba el cupo la crida falla i no es cobra res).
//
// Requereix enllaçar al Worker el "binding" de Workers AI amb el nom AI (Settings → Bindings). Sense ell, el
// Worker funciona igual i /identify respon que no està disponible.
//
// IMPORTANT: la IA NO identifica l'espècie ni diu mai que una cosa sigui comestible. Només LLEGEIX trets senzills
// (color del barret, làmines o porus, anell...) triant entre opcions tancades (IDENT_VOCAB). La comparació amb les
// fitxes i el percentatge de coincidència els calcula la pàgina de la guia (web/guia.html), no el model.
// Cada petició porta UNA foto i el forat on l'ha posat la persona (sombrero | debajo | pie), que només és una pista:
// el model llegeix TOTS els trets que es vegin clarament (una foto de la seta sencera ensenya barret, peu i de vegades
// làmines) i la guia ajunta els de les 3 fotos. Al model se li parla en anglès (Llama 3.2 Vision només el suporta amb
// fotos) i el model es tria amb el banc de proves tools/banco_ia.mjs. El vocabulari es genera amb
// `python3 tools/generar_guia.py --vocab` i una prova (tests/test_model.py) comprova que coincideix amb tools/rasgos_datos.py.
// ---------------------------------------------------------------------------
const IDENT_MODEL = "@cf/meta/llama-3.2-11b-vision-instruct";
const IDENT_MAX_CHARS = 1500000;          // mida màxima de la foto (text base64) — el navegador la redueix a ~800 px
const IDENT_MAX_BODY = 1600000;           // mida màxima de la petició (només per a /identify)
const IDENT_VOCAB = {
  "sombrero": {
    "titulo": "Sombrero, visto desde arriba",
    "descripcion": "la parte de ARRIBA del sombrero (color, superficie y forma)",
    "dims": {
      "s_color": {
        "etq": "Color del sombrero",
        "valores": {
          "blanco": "Blanco o crema",
          "amarillo": "Amarillo",
          "naranja": "Naranja",
          "rojo": "Rojo o rojo vinoso",
          "rosa": "Rosa o asalmonado",
          "pardo": "Marrón, ocre o castaño",
          "gris": "Gris",
          "verde": "Verde u oliva",
          "negro": "Negro u oscuro",
          "violeta": "Violeta o lila"
        }
      },
      "s_super": {
        "etq": "Superficie del sombrero",
        "valores": {
          "lisa": "Lisa y seca",
          "viscosa": "Viscosa (pegajosa o babosa)",
          "escamas": "Con escamas, verrugas o motas",
          "fibrosa": "Con fibrillas (como pelitos finos)"
        }
      },
      "s_forma": {
        "etq": "Forma del sombrero",
        "valores": {
          "convexo": "Convexo o plano (el normal)",
          "conico": "Cónico o de campana",
          "embudo": "En embudo o trompeta",
          "alveolado": "Con alvéolos, como un panal",
          "cerebro": "Con pliegues como un cerebro"
        }
      }
    }
  },
  "debajo": {
    "titulo": "Debajo del sombrero",
    "descripcion": "la parte de DEBAJO del sombrero, donde se ven las láminas, los poros, los pliegues o las púas",
    "dims": {
      "h_tipo": {
        "etq": "Qué hay debajo del sombrero",
        "valores": {
          "laminas": "Láminas (como hojitas finas)",
          "poros": "Poros (como una esponja de tubitos)",
          "pliegues": "Pliegues gruesos, venosos y ramificados",
          "puas": "Púas (como agujitas)",
          "liso": "Liso o casi liso, sin láminas ni poros ni púas"
        }
      },
      "h_color": {
        "etq": "Color de lo de debajo",
        "valores": {
          "blanco": "Blanco o crema",
          "amarillo": "Amarillo",
          "naranja": "Naranja",
          "rojo": "Rojo",
          "rosa": "Rosa o salmón",
          "pardo": "Marrón u óxido",
          "gris": "Gris",
          "verde": "Verde oliva",
          "violeta": "Violeta o lila"
        }
      }
    }
  },
  "pie": {
    "titulo": "Pie y base",
    "descripcion": "el PIE y su BASE (si tiene anillo, si hay bolsa o bulbo, y cómo es la superficie)",
    "dims": {
      "p_anillo": {
        "etq": "Anillo en el pie",
        "valores": {
          "si": "Sí, tiene anillo (falda o collar)",
          "no": "No tiene anillo"
        }
      },
      "p_base": {
        "etq": "Base del pie",
        "valores": {
          "bolsa": "Dentro de una bolsa o saco (volva)",
          "ensanchada": "Ensanchada (bulbo o panza), sin bolsa",
          "normal": "Normal: recta o afinada"
        }
      },
      "p_super": {
        "etq": "Superficie del pie",
        "valores": {
          "lisa": "Lisa",
          "red": "Con una red (malla fina)",
          "puntos": "Con puntitos, escamas o bandas"
        }
      },
      "p_color": {
        "etq": "Color del pie",
        "valores": {
          "blanco": "Blanco o crema",
          "amarillo": "Amarillo",
          "naranja": "Naranja",
          "rojo": "Rojo o rojizo",
          "pardo": "Marrón",
          "gris": "Gris",
          "negro": "Negro",
          "violeta": "Violeta o lila"
        }
      }
    }
  }
};
// Traducción al inglés de los rasgos, SOLO para hablarle al modelo: la ficha técnica de Llama 3.2 Vision dice que con fotos
// «English is the only language supported». Cada opción lleva [palabra que debe devolver el modelo, descripción]. Lo que
// devuelve se traduce de nuevo a los ids de IDENT_VOCAB (identValor), así que el resto de la guía no cambia.
// Una prueba (tests/test_model.py) comprueba que cubre EXACTAMENTE los mismos rasgos y opciones que IDENT_VOCAB.
const IDENT_EN = {
  s_color: { q: "cap colour, seen from above", o: {
    blanco: ["white", "white or cream"], amarillo: ["yellow", "yellow"], naranja: ["orange", "orange"],
    rojo: ["red", "red or wine-red"], rosa: ["pink", "pink or salmon"], pardo: ["brown", "brown, tan, ochre or chestnut"],
    gris: ["grey", "grey"], verde: ["green", "green or olive"], negro: ["black", "black or very dark"],
    violeta: ["violet", "violet or lilac"] } },
  s_super: { q: "cap surface", o: {
    lisa: ["smooth", "smooth and dry"], viscosa: ["sticky", "sticky or slimy (shiny, wet-looking)"],
    escamas: ["scaly", "with scales, warts or patches"], fibrosa: ["fibrous", "with fine fibres, like tiny hairs"] } },
  s_forma: { q: "cap shape", o: {
    convexo: ["convex", "convex or flat (the usual cap shape)"], conico: ["conical", "conical or bell-shaped"],
    embudo: ["funnel", "funnel- or trumpet-shaped"], alveolado: ["honeycomb", "with pits like a honeycomb"],
    cerebro: ["brain", "with folds like a brain"] } },
  h_tipo: { q: "what is under the cap", o: {
    laminas: ["gills", "gills (thin blades radiating from the stem)"], poros: ["pores", "pores (a sponge of tiny tubes, looks like fine dots)"],
    pliegues: ["ridges", "thick, vein-like, forked ridges"], puas: ["spines", "spines or teeth (like small needles)"],
    liso: ["smooth", "smooth or almost smooth, no gills, pores or spines"] } },
  h_color: { q: "colour of what is under the cap", o: {
    blanco: ["white", "white or cream"], amarillo: ["yellow", "yellow"], naranja: ["orange", "orange"], rojo: ["red", "red"],
    rosa: ["pink", "pink or salmon"], pardo: ["brown", "brown or rust"], gris: ["grey", "grey"],
    verde: ["green", "olive green"], violeta: ["violet", "violet or lilac"] } },
  p_anillo: { q: "ring on the stem", o: {
    si: ["yes", "yes, there is a ring (skirt or collar) on the stem"], no: ["no", "no ring"] } },
  p_base: { q: "base of the stem", o: {
    bolsa: ["sack", "inside a sack or cup (volva)"], ensanchada: ["swollen", "swollen (bulb or belly), without a sack"],
    normal: ["normal", "normal: straight or tapering"] } },
  p_super: { q: "stem surface", o: {
    lisa: ["smooth", "smooth"], red: ["net", "with a net (fine mesh)"], puntos: ["dotted", "with small dots, scales or bands"] } },
  p_color: { q: "stem colour", o: {
    blanco: ["white", "white or cream"], amarillo: ["yellow", "yellow"], naranja: ["orange", "orange"],
    rojo: ["red", "red or reddish"], pardo: ["brown", "brown"], gris: ["grey", "grey"], negro: ["black", "black"],
    violeta: ["violet", "violet or lilac"] } },
};
const IDENT_HINT = {
  sombrero: "the cap seen from above",
  debajo: "the underside of the cap (gills, pores, ridges or spines)",
  pie: "the stem and its base",
};

const IDENT_SYSTEM =
  "You are an assistant that describes photos of mushrooms for a hobbyist. You NEVER say which species it is and NEVER say whether it is edible: " +
  "you only record traits that are visible, choosing from closed lists of options. " +
  "Reply ALWAYS and ONLY with one valid JSON object, with no text before or after it.";

// Todas las dimensiones que se pueden leer de una foto, en el orden de IDENT_VOCAB.
function identDimsTodas() {
  const out = [];
  for (const parte of Object.keys(IDENT_VOCAB)) for (const id of Object.keys(IDENT_VOCAB[parte].dims)) out.push([id, parte]);
  return out;
}

// Una sola petición por foto: se piden TODOS los rasgos que se vean con claridad, sea cual sea el hueco donde la puso la
// persona (una foto de la seta entera enseña sombrero, pie y a veces láminas). El hueco solo se usa como pista.
function identUserPrompt(parte) {
  const hint = IDENT_HINT[parte] || "a mushroom";
  const lineas = identDimsTodas().map(([id]) => {
    const en = IDENT_EN[id];
    return `- ${id} (${en.q}): ` + Object.values(en.o).map(([w, t]) => `${w} = ${t}`).join(" | ");
  });
  const ejemplo = identDimsTodas().map(([id]) => `"${id}": null`).join(", ");
  return (
    `This is ONE photo of a mushroom taken by a hobbyist. They meant it to show: ${hint}.\n` +
    "First decide whether a mushroom is visible at all. Then record every trait below that you can CLEARLY see in this photo, " +
    "whichever part of the mushroom it belongs to (cap from above, underside of the cap, stem and base). " +
    "Use null for any trait you cannot clearly see. Do not guess: null is better than a lucky guess.\n" +
    "Reply with ONLY this JSON, and for each trait use exactly one of the option words listed (or null):\n" +
    `{"mushroom_visible": true, "traits": {${ejemplo}}}\n` +
    "Traits and options:\n" + lineas.join("\n")
  );
}

function validIdentImage(img) {
  return typeof img === "string" && img.length <= IDENT_MAX_CHARS &&
    /^data:image\/(?:jpeg|png|webp);base64,[A-Za-z0-9+/]+={0,2}$/.test(img);
}

function validIdentParte(parte) {
  return typeof parte === "string" && Object.prototype.hasOwnProperty.call(IDENT_VOCAB, parte);
}

// Acepta lo que devuelva el modelo: la palabra en inglés («brown»), su descripción, el id («pardo») o el texto en castellano
// («Marrón, ocre o castaño»), sin mirar mayúsculas. Devuelve el id de IDENT_VOCAB o null.
function identValor(dimId, parte, val) {
  if (typeof val === "boolean") val = val ? "si" : "no";   // un «yes/no» que el modelo devuelva como true/false (solo vale para el anillo)
  if (typeof val !== "string") return null;
  const v = val.trim().toLowerCase();
  if (!v) return null;
  const def = IDENT_VOCAB[parte].dims[dimId];
  const en = IDENT_EN[dimId];
  for (const [id, texto] of Object.entries(def.valores)) {
    if (v === id.toLowerCase() || v === texto.toLowerCase()) return id;
    const e = en && en.o[id];
    if (e && (v === e[0].toLowerCase() || v === e[1].toLowerCase())) return id;
  }
  return null;
}

// Convierte la respuesta del modelo (texto con un JSON dentro) en un resultado SEGURO: solo rasgos conocidos y solo con valores
// de las listas cerradas. Devuelve null si no hay manera de leerla. `parte` es el hueco donde estaba la foto (solo informativo).
function parseIdentResponse(raw, parte) {
  let obj = raw;
  if (typeof raw === "string") {
    const a = raw.indexOf("{");
    const b = raw.lastIndexOf("}");
    if (a < 0 || b <= a) return null;
    try { obj = JSON.parse(raw.slice(a, b + 1)); } catch (e) { return null; }
  }
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) return null;
  const rasgosIn = obj.traits && typeof obj.traits === "object" && !Array.isArray(obj.traits) ? obj.traits
    : obj.rasgos && typeof obj.rasgos === "object" && !Array.isArray(obj.rasgos) ? obj.rasgos : null;
  if (!rasgosIn && !("mushroom_visible" in obj) && !("se_ve_seta" in obj)) return null;
  const noEsSeta = obj.mushroom_visible === false || obj.se_ve_seta === false;
  const rasgos = {};
  if (!noEsSeta && rasgosIn) {
    for (const [dim, p] of identDimsTodas()) {
      const id = identValor(dim, p, rasgosIn[dim]);
      if (id) rasgos[dim] = id;
    }
  }
  return { parte, se_ve_seta: !noEsSeta, rasgos };
}

// Modo de pasar la foto y parámetros extra de cada modelo. Los fija el banco de pruebas (tools/banco_ia.mjs): Cloudflare
// documenta formas distintas según el modelo, y se prueba la primera y, si falla, la siguiente.
const IDENT_MODOS = {
  "@cf/meta/llama-3.2-11b-vision-instruct": ["image", "image_url"],
};
const IDENT_EXTRA = {};

function identInputs(model, dataUrl, user) {
  const base = { max_tokens: 400, temperature: 0.1, ...(IDENT_EXTRA[model] || {}) };
  const sys = { role: "system", content: IDENT_SYSTEM };
  const formas = {
    image: { ...base, messages: [sys, { role: "user", content: user }], image: dataUrl },
    image_url: { ...base, messages: [sys, { role: "user", content: [{ type: "text", text: user }, { type: "image_url", image_url: { url: dataUrl } }] }] },
  };
  return (IDENT_MODOS[model] || ["image_url", "image"]).map((m) => formas[m]);
}

// Texto de la respuesta: Cloudflare devuelve {response: ...} en unos modelos y el formato «chat completions» en otros.
function identTexto(out) {
  if (out && typeof out === "object") {
    if ("response" in out && out.response != null) return out.response;
    const m = out.choices && out.choices[0] && out.choices[0].message;
    if (m && m.content != null) {
      return Array.isArray(m.content) ? m.content.map((p) => (p && p.text) || "").join("") : m.content;
    }
  }
  return out;
}

// Llama al modelo de visión. Si el modelo pide aceptar la licencia de Meta (una sola vez por cuenta), se acepta
// automáticamente y se repite.
async function runVision(env, dataUrl, parte) {
  const user = identUserPrompt(parte);
  let ultimo;
  for (const input of identInputs(IDENT_MODEL, dataUrl, user)) {
    try {
      try {
        return await env.AI.run(IDENT_MODEL, input);
      } catch (e) {
        if (!/agree|licen[cs]e|5016/i.test(String(e && e.message))) throw e;
        await env.AI.run(IDENT_MODEL, { prompt: "agree" });
        return await env.AI.run(IDENT_MODEL, input);
      }
    } catch (e) {
      ultimo = e;
      if (/allocation|quota|neurons|daily/i.test(String(e && e.message))) break;   // reintentar no sirve
    }
  }
  throw ultimo;
}

async function identifyWithAI(env, dataUrl, parte) {
  const out = await runVision(env, dataUrl, parte);
  const resultado = parseIdentResponse(identTexto(out), parte);
  if (!resultado) throw new Error("La IA no ha devuelto una respuesta que se pueda leer. Prueba con otra foto.");
  return resultado;
}

function identErrorMessage(e) {
  const m = String(e && e.message);
  if (/allocation|quota|neurons|daily/i.test(m)) {
    return "Se ha agotado el cupo gratuito de IA de hoy. Vuelve a probar mañana.";
  }
  return `No se ha podido identificar la foto: ${m}`;
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    // Límit de mida del payload (10KB és més que suficient per a un
    // hallazgo o una petició d'autenticació/explicació) — evita que algú
    // enviï cossos enormes per esgotar recursos del Worker.
    // (Solo /identify admite una petición mayor: lleva una foto reducida y exige sesión iniciada.)
    const url = new URL(request.url);
    const contentLength = request.headers.get("content-length");
    const maxBody = url.pathname === "/identify" ? IDENT_MAX_BODY : 10240;
    if (contentLength && parseInt(contentLength, 10) > maxBody) {
      return new Response(JSON.stringify({ error: "Petición demasiado grande" }), {
        status: 413,
        headers: { ...corsHeaders(), "Content-Type": "application/json" },
      });
    }

    try {
      // --- Ruta per demanar un codi d'accés: no requereix sessió prèvia ---
      if (url.pathname === "/request-code" && request.method === "POST") {
        const body = await request.json();
        const email = normalizeEmail(body.email);
        const ip = clientIp(request);
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
          return new Response(JSON.stringify({ error: "Email inválido" }), {
            status: 400,
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        }
        // Límit per IP abans de res més (també frena la prova d'emails a l'engròs)
        const ipOk = await limitCheck(env, "codeReqIp", ip);
        if (!ipOk.allowed) return tooManyRequests("Demasiadas solicitudes de código. Espera un rato e inténtalo de nuevo.");
        await limitHit(env, "codeReqIp", ip);

        if (!isEmailAuthorized(env, email)) {
          // Petit retard per encarir intents automatitzats, i el mateix
          // missatge tant si l'email no existeix com si no està autoritzat.
          await new Promise((resolve) => setTimeout(resolve, 1000));
          return new Response(JSON.stringify({ error: "Este email no tiene acceso autorizado" }), {
            status: 403,
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        }
        // Límit per email: evita que algú inundi la teva bústia o gasti la quota d'enviaments de Brevo
        const emailOk = await limitCheck(env, "codeReqEmail", email);
        if (!emailOk.allowed) return tooManyRequests("Ya se han enviado varios códigos a este email. Espera un rato e inténtalo de nuevo.");
        await limitHit(env, "codeReqEmail", email);
        try {
          const code = await generateLoginCode(env, email);
          await sendLoginCodeEmail(env, email, code);
          return new Response(JSON.stringify({ ok: true }), {
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        } catch (e) {
          return new Response(JSON.stringify({ error: `No se ha podido enviar el código: ${e.message}` }), {
            status: 502,
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        }
      }

      // --- Ruta d'autenticació (email + codi rebut): no requereix sessió prèvia ---
      if (url.pathname === "/auth" && request.method === "POST") {
        const body = await request.json();
        const email = normalizeEmail(body.email);
        const code = typeof body.code === "string" ? body.code.trim().slice(0, 10) : "";
        const ip = clientIp(request);

        // Bloqueig per massa intents fallits (per email i per IP) ABANS de comprovar res
        const lockEmail = await limitCheck(env, "authFailEmail", email || "-");
        const lockIp = await limitCheck(env, "authFailIp", ip);
        if (!lockEmail.allowed || !lockIp.allowed) {
          return tooManyRequests("Demasiados intentos fallidos. Espera unos 15 minutos e inténtalo de nuevo.");
        }

        if (!email || !code || !isEmailAuthorized(env, email)) {
          await limitHit(env, "authFailIp", ip);
          await new Promise((resolve) => setTimeout(resolve, 1000));
          return new Response(JSON.stringify({ error: "Código o email incorrectos" }), {
            status: 401,
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        }
        const valid = await verifyLoginCode(env, email, code);
        if (!valid) {
          await limitHit(env, "authFailEmail", email);
          await limitHit(env, "authFailIp", ip);
          await new Promise((resolve) => setTimeout(resolve, 1000));
          return new Response(JSON.stringify({ error: "Código incorrecto o caducado" }), {
            status: 401,
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        }
        const token = await createSessionToken(env);
        return new Response(JSON.stringify({ ok: true, token }), {
          headers: { ...corsHeaders(), "Content-Type": "application/json" },
        });
      }

      if (url.pathname === "/verify" && request.method === "POST") {
        const { token } = await request.json();
        const valid = await verifySessionToken(env, token);
        return new Response(JSON.stringify({ valid }), {
          headers: { ...corsHeaders(), "Content-Type": "application/json" },
        });
      }

      // --- A partir d'aquí, cal sessió vàlida (header X-Session-Token) ---
      const sessionToken = request.headers.get("X-Session-Token");
      const validSession = await verifySessionToken(env, sessionToken);
      if (!validSession) {
        return new Response(JSON.stringify({ error: "No autenticado" }), {
          status: 401,
          headers: { ...corsHeaders(), "Content-Type": "application/json" },
        });
      }

      if (url.pathname === "/identify" && request.method === "POST") {
        const enJson = (obj, status) => new Response(JSON.stringify(obj), {
          status, headers: { ...corsHeaders(), "Content-Type": "application/json" },
        });
        if (!env.AI) {
          return enJson({ error: "La identificación por foto no está activada en el Worker (falta añadir «Workers AI»)." }, 503);
        }
        const dayOk = await limitCheck(env, "identifyDay", "all");
        if (!dayOk.allowed) {
          return enJson({ error: "Se ha alcanzado el límite diario de identificaciones. Vuelve a probar mañana." }, 429);
        }
        const body = await request.json().catch(() => null);
        if (!body || !validIdentImage(body.image)) {
          return enJson({ error: "Foto no válida: tiene que ser JPG, PNG o WebP y no demasiado grande." }, 400);
        }
        if (!validIdentParte(body.parte)) {
          return enJson({ error: "Falta indicar qué parte de la seta enseña la foto (sombrero, debajo o pie)." }, 400);
        }
        try {
          await limitHit(env, "identifyDay", "all");
          const resultado = await identifyWithAI(env, body.image, body.parte);
          return enJson({ ok: true, resultado }, 200);
        } catch (e) {
          return enJson({ error: identErrorMessage(e) }, 502);
        }
      }

      if (url.pathname === "/explain" && request.method === "POST") {
        if (!env.DEEPSEEK_API_KEY) {
          return new Response(JSON.stringify({ error: "Explicación no disponible ahora mismo (falta configurar DEEPSEEK_API_KEY)" }), {
            status: 503,
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        }
        // Tope diari de llamadas a DeepSeek (protege el coste de la API)
        const dayOk = await limitCheck(env, "explainDay", "all");
        if (!dayOk.allowed) {
          return new Response(JSON.stringify({ error: "Se ha alcanzado el límite diario de explicaciones. Vuelve a probar mañana." }), {
            status: 429,
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        }
        const rawZoneData = await request.json();
        const zoneData = validateExplainRequest(rawZoneData);
        if (!zoneData) {
          return new Response(JSON.stringify({ error: "Datos de la petición inválidos" }), {
            status: 400,
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        }
        try {
          await limitHit(env, "explainDay", "all");
          const explanation = await explainWithDeepSeek(env, zoneData);
          return new Response(JSON.stringify({ ok: true, explanation }), {
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        } catch (e) {
          // Es retorna el motiu real de l'error (visible també als logs del
          // Worker) en comptes d'un missatge genèric, per poder diagnosticar
          // sense haver d'endevinar la causa.
          return new Response(JSON.stringify({ error: `No se ha podido generar la explicación: ${e.message}` }), {
            status: 502,
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        }
      }

      if (request.method === "POST") {
        const newHallazgo = await request.json();
        if (!validateHallazgo(newHallazgo)) {
          return new Response(JSON.stringify({ error: "Datos de hallazgo inválidos" }), {
            status: 400,
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        }
        newHallazgo.id = crypto.randomUUID();
        newHallazgo.createdAt = new Date().toISOString();

        const { sha, hallazgos } = await getCurrentFile(env);
        hallazgos.push(newHallazgo);
        const speciesLabel = (newHallazgo.speciesNames && newHallazgo.speciesNames.length > 0)
          ? newHallazgo.speciesNames.join(", ")
          : "sin especie";
        await saveFile(env, hallazgos, sha, `Nueva salida: ${speciesLabel} en ${newHallazgo.place}`);

        return new Response(JSON.stringify({ ok: true, hallazgo: newHallazgo }), {
          status: 201,
          headers: { ...corsHeaders(), "Content-Type": "application/json" },
        });
      }

      // NOTA: no hi ha endpoint DELETE — les salides registrades són
      // permanents a propòsit (decisió de l'usuari): un cop guardades,
      // no es poden esborrar per cap via, ni des de la web ni cridant
      // directament el Worker. Això protegeix l'historial de dades reals
      // que alimenta l'evolució i la tasa de confirmació del model.

      if (request.method === "GET") {
        const { hallazgos } = await getCurrentFile(env);
        return new Response(JSON.stringify(hallazgos), {
          headers: { ...corsHeaders(), "Content-Type": "application/json" },
        });
      }

      return new Response("Método no soportado", { status: 405, headers: corsHeaders() });
    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: { ...corsHeaders(), "Content-Type": "application/json" },
      });
    }
  },
};
