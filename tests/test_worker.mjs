// Pruebas del Worker (sin red, sin Cloudflare): código de acceso uniforme,
// límite de intentos con un KV falso, y que sin KV el Worker siga funcionando.
// Uso (desde la carpeta tests/):  node test_worker.mjs
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "worker-"));
// El Worker está en ../worker/ (repositorio) o en ../3-worker-cloudflare/ (carpeta subir-a-github)
const candidates = ["../worker/index.js", "../3-worker-cloudflare/index.js"].map(r => new URL(r, import.meta.url));
const workerSrc = candidates.find(u => fs.existsSync(u));
if (!workerSrc) { console.log("No encuentro el index.js del Worker"); process.exit(2); }
fs.copyFileSync(workerSrc, path.join(tmp, "index.mjs"));
const worker = (await import(pathToFileURL(path.join(tmp, "index.mjs")).href)).default;

let ok = 0, bad = 0;
function check(name, cond, extra = "") {
  if (cond) { ok++; } else { bad++; console.log("FALLO:", name, extra); }
}

class FakeKV {
  constructor() { this.m = new Map(); this.writes = 0; }
  async get(k) { return this.m.has(k) ? this.m.get(k) : null; }
  async put(k, v) { this.writes++; this.m.set(k, v); }
}

// Brevo falso: guarda el último código enviado.
let lastMail = null;
globalThis.fetch = async (url, opts) => {
  if (String(url).includes("brevo")) {
    const body = JSON.parse(opts.body);
    lastMail = { to: body.to[0].email, code: /letter-spacing:4px">(\d{6})</.exec(body.htmlContent)?.[1] };
    return new Response("{}", { status: 201 });
  }
  return new Response("{}", { status: 500 });
};
// El Worker espera 1 s tras cada fallo; en las pruebas se acelera.
const realSetTimeout = globalThis.setTimeout;
globalThis.setTimeout = (fn, ms, ...a) => realSetTimeout(fn, ms > 50 ? 1 : ms, ...a);

const baseEnv = () => ({
  SESSION_SECRET: "secreto-de-prueba-0123456789",
  AUTHORIZED_EMAILS: "yo@example.com, otro@example.com",
  BREVO_API_KEY: "x", SENDER_EMAIL: "no@example.com",
});
function req(pathname, body, ip = "1.1.1.1") {
  return new Request("https://w.test" + pathname, {
    method: "POST",
    headers: { "Content-Type": "application/json", "CF-Connecting-IP": ip },
    body: JSON.stringify(body),
  });
}
async function call(env, pathname, body, ip) {
  const r = await worker.fetch(req(pathname, body, ip), env);
  return { status: r.status, json: await r.json().catch(() => ({})) };
}

// ---------- 1) Flujo normal sin KV: pide código y entra ----------
{
  const env = baseEnv();
  let r = await call(env, "/request-code", { email: "yo@example.com" });
  check("sin KV: request-code 200", r.status === 200, JSON.stringify(r));
  const code = lastMail.code;
  check("el código llega con 6 dígitos", /^\d{6}$/.test(code), code);
  r = await call(env, "/auth", { email: "YO@example.com", code });
  check("sin KV: auth correcto", r.status === 200 && r.json.token, JSON.stringify(r));
  const v = await worker.fetch(new Request("https://w.test/verify", { method: "POST", body: JSON.stringify({ token: r.json.token }) }), env);
  check("el token de sesión verifica", (await v.json()).valid === true);
  r = await call(env, "/auth", { email: "yo@example.com", code: code === "000000" ? "000001" : "000000" });
  check("código erróneo -> 401", r.status === 401);
  r = await call(env, "/request-code", { email: "intruso@example.com" });
  check("email no autorizado -> 403", r.status === 403);
}

// ---------- 2) Uniformidad del código ----------
{
  const env = baseEnv();
  const seen = new Set(); let leadingZero = 0, endsZeroZero = 0; const N = 3000;
  const digitCount = Array(10).fill(0);
  for (let i = 0; i < N; i++) {
    env.SESSION_SECRET = "s" + i;
    await call(env, "/request-code", { email: "yo@example.com" }, "9.9.9." + (i % 250));
    const c = lastMail.code; seen.add(c);
    if (c[0] === "0") leadingZero++;
    if (c.endsWith("00")) endsZeroZero++;
    for (const ch of c) digitCount[+ch]++;
  }
  // Uniforme: ~10% empiezan por 0 (antes ~31% acababan en ceros de relleno), ~1% acaban en 00
  check("uniforme: ~10% empiezan por 0", leadingZero / N > 0.07 && leadingZero / N < 0.13, leadingZero / N);
  check("uniforme: ~1% acaban en 00 (antes ~30%)", endsZeroZero / N < 0.025, endsZeroZero / N);
  const exp = (N * 6) / 10;
  check("uniforme: cada dígito ~10%", digitCount.every(c => Math.abs(c - exp) / exp < 0.07), digitCount.join(","));
  check("códigos casi todos distintos", seen.size > N * 0.99, seen.size);
}

// ---------- 3) Límite de intentos fallidos (con KV) ----------
{
  const env = { ...baseEnv(), LIMITS: new FakeKV() };
  const r0 = await call(env, "/request-code", { email: "yo@example.com" }, "2.2.2.2");
  const good = lastMail.code; const wrong = good === "123456" ? "123457" : "123456";
  let last;
  for (let i = 0; i < 5; i++) last = await call(env, "/auth", { email: "yo@example.com", code: wrong }, "3.3.3." + i);
  check("5 fallos seguidos siguen siendo 401", last.status === 401, last.status);
  // El sexto intento, aunque sea con el código CORRECTO y desde otra IP, queda bloqueado
  const blocked = await call(env, "/auth", { email: "yo@example.com", code: good }, "4.4.4.4");
  check("tras 5 fallos del email: bloqueo 429 incluso con el código bueno", blocked.status === 429, JSON.stringify(blocked));
  // Otro email autorizado no se ve afectado
  await call(env, "/request-code", { email: "otro@example.com" }, "5.5.5.5");
  const other = await call(env, "/auth", { email: "otro@example.com", code: lastMail.code }, "5.5.5.5");
  check("otro email sigue pudiendo entrar", other.status === 200, JSON.stringify(other));
}
{
  // Bloqueo por IP: 15 fallos con emails distintos/no autorizados desde la misma IP
  const env = { ...baseEnv(), LIMITS: new FakeKV() };
  let st = [];
  for (let i = 0; i < 17; i++) st.push((await call(env, "/auth", { email: `x${i}@example.com`, code: "111111" }, "6.6.6.6")).status);
  check("IP con 15 fallos queda bloqueada (429)", st[14] === 401 && st[15] === 429, st.join(","));
}

// ---------- 4) Límite de códigos solicitados ----------
{
  const env = { ...baseEnv(), LIMITS: new FakeKV() };
  const st = [];
  for (let i = 0; i < 7; i++) st.push((await call(env, "/request-code", { email: "yo@example.com" }, "7.7.7." + i)).status);
  check("máx. 5 códigos por hora y email (6º y 7º = 429)", st.slice(0, 5).every(s => s === 200) && st[5] === 429 && st[6] === 429, st.join(","));
  const env2 = { ...baseEnv(), LIMITS: new FakeKV() };
  const st2 = [];
  for (let i = 0; i < 12; i++) st2.push((await call(env2, "/request-code", { email: i % 2 ? "yo@example.com" : "otro@example.com" }, "8.8.8.8")).status);
  check("máx. 10 solicitudes por hora e IP", st2[9] === 200 && st2[10] === 429, st2.join(","));
}

// ---------- 5) Tope diario de /explain ----------
{
  const kv = new FakeKV();
  const env = { ...baseEnv(), LIMITS: kv, DEEPSEEK_API_KEY: "k" };
  await call(env, "/request-code", { email: "yo@example.com" }, "10.0.0.1");
  const token = (await call(env, "/auth", { email: "yo@example.com", code: lastMail.code }, "10.0.0.1")).json.token;
  // contador a 150 -> la siguiente llamada se rechaza sin llegar a DeepSeek
  const day = Math.floor(Date.now() / 86400000);
  kv.m.set(`rl:explainDay:all:${day}`, "150");
  const r = await worker.fetch(new Request("https://w.test/explain", {
    method: "POST", headers: { "Content-Type": "application/json", "X-Session-Token": token, "CF-Connecting-IP": "10.0.0.1" },
    body: JSON.stringify({ zoneName: "x", speciesName: "y", score: 80 }),
  }), env);
  check("explain: 429 al pasar el tope diario", r.status === 429, r.status);
}

// ---------- 6) KV roto: la autenticación falla cerrada ----------
{
  const broken = { get: async () => { throw new Error("KV caído"); }, put: async () => { throw new Error("KV caído"); } };
  const env = { ...baseEnv(), LIMITS: broken };
  const r = await call(env, "/auth", { email: "yo@example.com", code: "123456" }, "11.0.0.1");
  check("KV caído: auth se deniega (429), no se salta el límite", r.status === 429, r.status);
}

// ---------- 7) /identify (lectura de rasgos de una foto con Workers AI) ----------
{
  const FOTO = "data:image/jpeg;base64," + "A".repeat(300000);   // ~300 KB: mucho más que los 10 KB del resto de rutas
  const getToken = async (env, ip = "30.0.0.1") => {
    await call(env, "/request-code", { email: "yo@example.com" }, ip);
    return (await call(env, "/auth", { email: "yo@example.com", code: lastMail.code }, ip)).json.token;
  };
  const callId = async (env, token, body, headers = {}) => {
    const r = await worker.fetch(new Request("https://w.test/identify", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Session-Token": token || "", "CF-Connecting-IP": "30.0.0.1", ...headers },
      body: typeof body === "string" ? body : JSON.stringify(body),
    }), env);
    return { status: r.status, json: await r.json().catch(() => ({})) };
  };
  const respuesta = (obj) => ({ response: typeof obj === "string" ? obj : JSON.stringify(obj) });
  // lo que devolvería el modelo para la foto de DEBAJO, con basura mezclada
  const bueno = { parte_vista: "debajo", rasgos: { h_tipo: "laminas", h_color: "Blanco o crema", s_color: "verde", p_anillo: "si", h_inventado: "x" } };
  const env0 = { ...baseEnv() };
  const token = await getToken(env0);

  // sin sesión
  let r = await callId({ ...env0, AI: { run: async () => respuesta(bueno) } }, "", { image: FOTO, parte: "debajo" });
  check("identify: sin sesión → 401", r.status === 401, r.status);

  // sin el binding AI
  r = await callId(env0, token, { image: FOTO, parte: "debajo" });
  check("identify: sin binding AI → 503 con mensaje claro", r.status === 503 && /Workers AI/.test(r.json.error || ""), JSON.stringify(r));

  // caso normal + saneado: solo rasgos de la parte pedida y con valores del vocabulario
  const calls = [];
  const ai = { run: async (model, input) => { calls.push({ model, input }); return respuesta(bueno); } };
  const env1 = { ...baseEnv(), AI: ai };
  r = await callId(env1, token, { image: FOTO, parte: "debajo" });
  check("identify: 200 y ok", r.status === 200 && r.json.ok === true, JSON.stringify(r).slice(0, 200));
  const res = r.json.resultado || {};
  check("identify: devuelve parte, parte_vista y se_ve_seta", res.parte === "debajo" && res.parte_vista === "debajo" && res.se_ve_seta === true, JSON.stringify(res));
  check("identify: solo rasgos de la parte pedida (h_tipo, h_color); se tira s_color, p_anillo y los inventados",
        JSON.stringify(Object.keys(res.rasgos || {}).sort()) === '["h_color","h_tipo"]', JSON.stringify(res.rasgos));
  check("identify: acepta el id («laminas») y el texto completo («Blanco o crema» → blanco)", res.rasgos.h_tipo === "laminas" && res.rasgos.h_color === "blanco", JSON.stringify(res.rasgos));
  check("identify: NO devuelve candidatas ni dice qué seta es", !("candidatas" in res) && !("falta_ver" in res));
  check("identify: usa el modelo de visión de Llama y manda la imagen como data URI (formato del tutorial de Cloudflare)",
        calls.length === 1 && /llama-3\.2-11b-vision-instruct/.test(calls[0].model) && calls[0].input.image === FOTO &&
        typeof calls[0].input.messages[1].content === "string");
  const prompt = calls[0].input.messages[1].content;
  check("identify: el prompt de «debajo» lista solo sus rasgos y pide no adivinar (null)",
        /h_tipo \(/.test(prompt) && /h_color \(/.test(prompt) && !/s_color \(/.test(prompt) && !/p_anillo \(/.test(prompt) && /No adivines/.test(prompt) && /null/.test(prompt), prompt.slice(0, 200));
  check("identify: el mensaje del sistema prohíbe decir la especie o si se puede comer", /No dices qué especie es ni si se puede comer/.test(calls[0].input.messages[0].content));
  check("identify: tokens de salida acotados (300) y temperatura baja", calls[0].input.max_tokens === 300 && calls[0].input.temperature <= 0.2);

  // cada parte pide sus rasgos
  for (const [parte, dims, noDims] of [["sombrero", ["s_color", "s_super", "s_forma"], ["h_tipo", "p_anillo"]],
                                       ["pie", ["p_anillo", "p_base", "p_super", "p_color"], ["s_color", "h_tipo"]]]) {
    const c = [];
    r = await callId({ ...baseEnv(), AI: { run: async (m, i) => { c.push(i); return respuesta({ parte_vista: parte, rasgos: {} }); } } }, token, { image: FOTO, parte });
    const pr = c[0].messages[1].content;
    check(`identify: la parte «${parte}» pide sus ${dims.length} rasgos y ninguno de otra parte`,
          r.status === 200 && dims.every((d) => pr.includes(d + " (")) && noDims.every((d) => !pr.includes(d + " (")), pr.slice(0, 160));
  }

  // el modelo mete texto alrededor del JSON
  r = await callId({ ...baseEnv(), AI: { run: async () => respuesta('Claro, aquí tienes:\n```json\n' + JSON.stringify(bueno) + '\n```\nEspero que ayude') } }, token, { image: FOTO, parte: "debajo" });
  check("identify: lee el JSON aunque el modelo escriba texto alrededor", r.status === 200 && r.json.resultado.rasgos.h_tipo === "laminas", JSON.stringify(r).slice(0, 160));

  // valores que no están en el vocabulario, null, mayúsculas
  r = await callId({ ...baseEnv(), AI: { run: async () => respuesta({ parte_vista: "SOMBRERO", rasgos: { s_color: "morado", s_super: null, s_forma: "CONVEXO" } }) } }, token, { image: FOTO, parte: "sombrero" });
  check("identify: valor fuera del vocabulario (morado) y null se descartan; mayúsculas se aceptan",
        r.status === 200 && JSON.stringify(r.json.resultado.rasgos) === '{"s_forma":"convexo"}' && r.json.resultado.parte_vista === "sombrero", JSON.stringify(r.json));

  // parte_vista distinta de la pedida: se devuelve tal cual para que la guía avise
  r = await callId({ ...baseEnv(), AI: { run: async () => respuesta({ parte_vista: "pie", rasgos: { h_tipo: "poros" } }) } }, token, { image: FOTO, parte: "debajo" });
  check("identify: si la foto parece de otra parte, parte_vista lo dice (la guía avisa)", r.status === 200 && r.json.resultado.parte_vista === "pie" && r.json.resultado.parte === "debajo");
  r = await callId({ ...baseEnv(), AI: { run: async () => respuesta({ parte_vista: "inventada", rasgos: { h_tipo: "poros" } }) } }, token, { image: FOTO, parte: "debajo" });
  check("identify: parte_vista desconocida → «otra»", r.status === 200 && r.json.resultado.parte_vista === "otra");

  // basura
  r = await callId({ ...baseEnv(), AI: { run: async () => respuesta("no sé qué es eso") } }, token, { image: FOTO, parte: "debajo" });
  check("identify: respuesta ilegible → 502 con mensaje, sin romper", r.status === 502 && /no ha devuelto una respuesta/.test(r.json.error || ""), JSON.stringify(r));
  r = await callId({ ...baseEnv(), AI: { run: async () => respuesta({ hola: "mundo" }) } }, token, { image: FOTO, parte: "debajo" });
  check("identify: JSON sin ninguno de los campos esperados → 502", r.status === 502, JSON.stringify(r));
  r = await callId({ ...baseEnv(), AI: { run: async () => respuesta({ parte_vista: "debajo", rasgos: ["láminas"] }) } }, token, { image: FOTO, parte: "debajo" });
  check("identify: rasgos en formato antiguo (lista) → se ignoran, sin romper", r.status === 200 && JSON.stringify(r.json.resultado.rasgos) === "{}");

  // «no hay seta»
  r = await callId({ ...baseEnv(), AI: { run: async () => respuesta({ parte_vista: "no_es_seta", rasgos: { h_tipo: "laminas" } }) } }, token, { image: FOTO, parte: "debajo" });
  check("identify: «no es seta» → se_ve_seta=false y ningún rasgo aunque el modelo los ponga",
        r.status === 200 && r.json.resultado.se_ve_seta === false && JSON.stringify(r.json.resultado.rasgos) === "{}");
  r = await callId({ ...baseEnv(), AI: { run: async () => respuesta({ se_ve_seta: false, rasgos: {} }) } }, token, { image: FOTO, parte: "pie" });
  check("identify: se_ve_seta=false también vale", r.status === 200 && r.json.resultado.se_ve_seta === false && r.json.resultado.parte_vista === "no_es_seta");

  // formato alternativo si el primero falla
  const calls2 = [];
  const ai2 = { run: async (model, input) => { calls2.push(input); if (input.image) throw new Error("input.image no soportado"); return respuesta(bueno); } };
  r = await callId({ ...baseEnv(), AI: ai2 }, token, { image: FOTO, parte: "debajo" });
  check("identify: si falla el formato 1, prueba el 2 (imagen dentro del mensaje) y funciona",
        r.status === 200 && calls2.length === 2 && Array.isArray(calls2[1].messages[1].content) &&
        calls2[1].messages[1].content[1].image_url.url === FOTO, JSON.stringify(r).slice(0, 160) + calls2.length);

  // licencia de Meta: se acepta sola y se repite
  const calls3 = [];
  let aceptada = false;
  const ai3 = { run: async (model, input) => {
    calls3.push(input);
    if (input.prompt === "agree") { aceptada = true; return { response: "ok" }; }
    if (!aceptada) throw new Error("5016: Prior to using this model, you must agree to the license (send prompt 'agree')");
    return respuesta(bueno);
  } };
  r = await callId({ ...baseEnv(), AI: ai3 }, token, { image: FOTO, parte: "debajo" });
  check("identify: si el modelo pide aceptar la licencia, el Worker envía «agree» y repite la llamada",
        r.status === 200 && calls3.length === 3 && calls3[1].prompt === "agree", JSON.stringify(r).slice(0, 160) + calls3.length);

  // cupo gratuito agotado
  let n4 = 0;
  r = await callId({ ...baseEnv(), AI: { run: async () => { n4++; throw new Error("4006: you have used up your daily free allocation of 10,000 neurons"); } } }, token, { image: FOTO, parte: "debajo" });
  check("identify: cupo gratuito agotado → 502 «Se ha agotado el cupo» y no reintenta", r.status === 502 && /cupo gratuito/.test(r.json.error || "") && n4 === 1, JSON.stringify(r) + n4);

  // validación de la foto y de la parte
  const envV = { ...baseEnv(), AI: { run: async () => respuesta(bueno) } };
  for (const [nombre, body] of [["texto cualquiera", { image: "hola", parte: "debajo" }], ["SVG", { image: "data:image/svg+xml;base64,AAAA", parte: "debajo" }],
                                ["sin imagen", { parte: "debajo" }], ["no es JSON", "no json"], ["no es base64", { image: "data:image/jpeg;base64,@@@", parte: "debajo" }]]) {
    r = await callId(envV, token, body);
    check(`identify: foto no válida (${nombre}) → 400`, r.status === 400, r.status);
  }
  for (const [nombre, parte] of [["sin parte", undefined], ["parte desconocida", "raiz"], ["parte «otros» (no se lee de fotos)", "otros"],
                                 ["parte con prototipo", "constructor"], ["parte no es texto", 7]]) {
    r = await callId(envV, token, { image: FOTO, parte });
    check(`identify: ${nombre} → 400`, r.status === 400 && /parte/.test(r.json.error || ""), JSON.stringify(r));
  }
  r = await callId(envV, token, { image: "data:image/jpeg;base64," + "A".repeat(1600000), parte: "debajo" });
  check("identify: foto demasiado grande → 400", r.status === 400, r.status);
  r = await callId(envV, token, { image: FOTO, parte: "debajo" }, { "content-length": "2000000" });
  check("identify: petición de más de 1,6 MB → 413", r.status === 413, r.status);

  // el tope de 10 KB sigue valiendo para las demás rutas
  const r413 = await worker.fetch(new Request("https://w.test/explain", {
    method: "POST", headers: { "Content-Type": "application/json", "X-Session-Token": token, "content-length": "20000" }, body: "{}",
  }), envV);
  check("el tope de 10 KB sigue valiendo para el resto de rutas (/explain → 413)", r413.status === 413, r413.status);

  // tope diario con KV: cada FOTO cuenta 1
  const kv = new FakeKV();
  const envL = { ...baseEnv(), LIMITS: kv, AI: { run: async () => { throw new Error("no debería llamarse"); } } };
  const tokL = await getToken(envL, "31.0.0.1");
  kv.m.set(`rl:identifyDay:all:${Math.floor(Date.now() / 86400000)}`, "120");
  r = await callId(envL, tokL, { image: FOTO, parte: "debajo" }, { "CF-Connecting-IP": "31.0.0.1" });
  check("identify: tope diario (120) → 429 sin llegar a la IA", r.status === 429, r.status);
  const kv2 = new FakeKV();
  const envC = { ...baseEnv(), LIMITS: kv2, AI: { run: async () => respuesta(bueno) } };
  const tokC = await getToken(envC, "32.0.0.1");
  const clave = `rl:identifyDay:all:${Math.floor(Date.now() / 86400000)}`;
  for (const parte of ["sombrero", "debajo", "pie"]) await callId(envC, tokC, { image: FOTO, parte }, { "CF-Connecting-IP": "32.0.0.1" });
  check("identify: cada foto suma 1 al contador diario (3 fotos → 3)", kv2.m.get(clave) === "3", String(kv2.m.get(clave)));
  // una petición con parte inválida no gasta cupo
  const kv3 = new FakeKV();
  const envP = { ...baseEnv(), LIMITS: kv3, AI: { run: async () => respuesta(bueno) } };
  const tokP = await getToken(envP, "33.0.0.1");
  await callId(envP, tokP, { image: FOTO, parte: "raiz" }, { "CF-Connecting-IP": "33.0.0.1" });
  check("identify: una petición rechazada por parte inválida no gasta cupo diario", !kv3.m.get(clave), String(kv3.m.get(clave)));
}

console.log(ok + bad === 0 ? "sin pruebas" : `Worker: ${ok} comprobaciones OK, ${bad} fallos`);
process.exit(bad ? 1 : 0);
