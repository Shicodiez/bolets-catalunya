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
async function hmacSign(secret, message) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(message));
  return btoa(String.fromCharCode(...new Uint8Array(sig)));
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
  const sig = await hmacSign(env.SESSION_SECRET, `${normalizeEmail(email)}:${windowIndex}`);
  // Es fan servir els primers dígits del hash com a codi de 6 xifres.
  const digits = sig.replace(/[^0-9]/g, "");
  const padded = (digits + "000000").slice(0, 6);
  return padded;
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
    if (expected === code) return true;
  }
  return false;
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
  if (sig !== expected) return false;
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
    daysSinceRain: typeof zoneData.daysSinceRain === "number" ? zoneData.daysSinceRain : 0,
    treeLabel: sanitizeForPrompt(zoneData.treeLabel, 60),
    scoreChange: typeof zoneData.scoreChange === "object" ? zoneData.scoreChange : null,
  };
}

async function explainWithDeepSeek(env, zoneData) {
  const { zoneName, speciesName, score, confidence, breakdown, rain10d, minTemp, daysSinceRain, treeLabel, scoreChange } = zoneData;

  const changeText = scoreChange
    ? `La puntuación ha cambiado ${scoreChange.change >= 0 ? '+' : ''}${scoreChange.change} puntos en los últimos 7 días (de ${scoreChange.previous} a ${scoreChange.current}).`
    : '';

  const prompt = `Eres un asistente que explica, en 2-3 frases claras y en castellano, por qué una zona de Catalunya tiene una puntuación concreta para encontrar una especie de bolet. NO decides ni recalculas nada, solo interpretas los datos que te doy. No inventes datos que no aparezcan aquí.

Zona: ${zoneName} (${treeLabel})
Especie: ${speciesName}
Puntuación: ${score}/100
Confianza: ${confidence}
Desglose de la puntuación: lluvia=${breakdown.pluja}, días desde lluvia=${breakdown.dies_pluja}, temperatura=${breakdown.temperatura}, temporada=${breakdown.temporada}, corroboración entre fuentes=${breakdown.corroboracio}
Datos meteorológicos: ${rain10d}mm de lluvia acumulada, ${minTemp}°C de mínima nocturna, ${daysSinceRain} días desde el inicio de la lluvia
${changeText}

Escribe la explicación en tono cercano, como si hablaras con un aficionado a los bolets, sin tecnicismos innecesarios.`;

  const res = await fetch(DEEPSEEK_URL, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${env.DEEPSEEK_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "deepseek-v4-flash",
      messages: [{ role: "user", content: prompt }],
      temperature: 0.5,
      max_tokens: 200,
    }),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`DeepSeek ha fallat (status ${res.status}): ${errText}`);
  }
  const data = await res.json();
  return data.choices?.[0]?.message?.content?.trim() || "No se ha podido generar una explicación.";
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
  "rovellons", "ceps", "camagrocs", "trompetes", "oureig", "rossinyols",
  "colmenilles", "llengua", "pinetell", "fredolic",
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
  // Amb "nada" (buscat i no trobat) l'espècie és opcional: pot ser una
  // cerca general sense objectiu concret. Amb "mucho"/"poco" cal indicar
  // quina espècie s'ha trobat.
  if (h.amount === "nada") {
    if (h.speciesId !== "" && (typeof h.speciesId !== "string" || !VALID_SPECIES_IDS.has(h.speciesId))) return false;
  } else {
    if (typeof h.speciesId !== "string" || !VALID_SPECIES_IDS.has(h.speciesId)) return false;
  }
  if (typeof h.speciesName !== "string" || h.speciesName.length > 80) return false;
  if (typeof h.place !== "string" || !h.place.trim() || h.place.length > 120) return false;
  if (!isValidDateString(h.date)) return false;
  if (h.tree !== undefined && !VALID_TREE_IDS.has(h.tree)) return false;
  if (h.treeName !== undefined && (typeof h.treeName !== "string" || h.treeName.length > 60)) return false;
  if (h.alt !== undefined && (typeof h.alt !== "string" && typeof h.alt !== "number")) return false;
  return true;
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    // Límit de mida del payload (10KB és més que suficient per a un
    // hallazgo o una petició d'autenticació/explicació) — evita que algú
    // enviï cossos enormes per esgotar recursos del Worker.
    const contentLength = request.headers.get("content-length");
    if (contentLength && parseInt(contentLength, 10) > 10240) {
      return new Response(JSON.stringify({ error: "Petición demasiado grande" }), {
        status: 413,
        headers: { ...corsHeaders(), "Content-Type": "application/json" },
      });
    }

    const url = new URL(request.url);

    try {
      // --- Ruta per demanar un codi d'accés: no requereix sessió prèvia ---
      if (url.pathname === "/request-code" && request.method === "POST") {
        const body = await request.json();
        const email = normalizeEmail(body.email);
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
          return new Response(JSON.stringify({ error: "Email inválido" }), {
            status: 400,
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        }
        if (!isEmailAuthorized(env, email)) {
          // Mateixa mitigació que abans amb la contrasenya: petit retard per
          // encarir intents automatitzats, i el mateix missatge tant si
          // l'email no existeix com si no està autoritzat (no revelar quins
          // emails concrets són vàlids).
          await new Promise((resolve) => setTimeout(resolve, 1000));
          return new Response(JSON.stringify({ error: "Este email no tiene acceso autorizado" }), {
            status: 403,
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        }
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
        if (!email || !code || !isEmailAuthorized(env, email)) {
          await new Promise((resolve) => setTimeout(resolve, 1000));
          return new Response(JSON.stringify({ error: "Código o email incorrectos" }), {
            status: 401,
            headers: { ...corsHeaders(), "Content-Type": "application/json" },
          });
        }
        const valid = await verifyLoginCode(env, email, code);
        if (!valid) {
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

      if (url.pathname === "/explain" && request.method === "POST") {
        if (!env.DEEPSEEK_API_KEY) {
          return new Response(JSON.stringify({ error: "Explicación no disponible ahora mismo (falta configurar DEEPSEEK_API_KEY)" }), {
            status: 503,
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
        await saveFile(env, hallazgos, sha, `Nuevo hallazgo: ${newHallazgo.speciesName} en ${newHallazgo.place}`);

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
