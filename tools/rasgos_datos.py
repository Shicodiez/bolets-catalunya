"""Rasgos que se comparan en la identificación por fotos (lo leen generar_guia.py y, por --vocab, el Worker).

IDEA: la IA de la foto NO dice qué seta es. Solo lee rasgos sencillos (color del sombrero, láminas o poros, anillo...)
eligiendo entre opciones cerradas. Después la propia guía compara esos rasgos con la «firma» de cada ficha y calcula
una COINCIDENCIA (%). Así el porcentaje se puede explicar y comprobar: sale de contar qué rasgos encajan con la ficha.

IMPORTANTE (honestidad):
  * La coincidencia NO es la probabilidad de que sea esa seta ni dice que se pueda comer. Solo cuenta cuántos de los
    rasgos que se han indicado encajan con lo que dice la ficha.
  * Las firmas se han sacado SOLO del texto de las fichas de guia_datos.py («cumple», «descarta», «confunde»), que está
    redactado por una IA y NO lo ha revisado ningún micólogo. Donde la ficha no dice nada de un rasgo, no se pone.
  * Nunca se ha medido cuánto acierta la lectura de las fotos con setas reales de Catalunya.

Formato de FIRMAS:  id de ficha -> {rasgo: "valor1 valor2 ..."}
  Una «!» al final del nombre del rasgo (por ejemplo "h_tipo!") lo marca como CLAVE (peso 3): si no encaja, la ficha
  queda descartada. Sin «!» el peso es 1. Un rasgo que no está en la firma no cuenta ni a favor ni en contra.
  Lo que debajo del sombrero hay (láminas, poros, pliegues, púas) es SIEMPRE clave cuando la ficha lo dice.
"""

# Partes en las que se reparten los rasgos. Las tres primeras son las que puede leer la IA de una foto.
PARTES = [
    ("sombrero", "Sombrero, visto desde arriba",
     "la parte de ARRIBA del sombrero (color, superficie y forma)"),
    ("debajo", "Debajo del sombrero",
     "la parte de DEBAJO del sombrero, donde se ven las láminas, los poros, los pliegues o las púas"),
    ("pie", "Pie y base",
     "el PIE y su BASE (si tiene anillo, si hay bolsa o bulbo, y cómo es la superficie)"),
    ("otros", "Lo que no sale en una foto (lo compruebas tú)", ""),
]
PARTES_IA = ("sombrero", "debajo", "pie")

# (id, parte, pregunta corta, [(valor, nombre corto, texto largo para el desplegable), ...])
DIMS = [
    ("s_color", "sombrero", "Color del sombrero", [
        ("blanco", "blanco o crema", "Blanco o crema"),
        ("amarillo", "amarillo", "Amarillo"),
        ("naranja", "naranja", "Naranja"),
        ("rojo", "rojo", "Rojo o rojo vinoso"),
        ("rosa", "rosa o asalmonado", "Rosa o asalmonado"),
        ("pardo", "marrón u ocre", "Marrón, ocre o castaño"),
        ("gris", "gris", "Gris"),
        ("verde", "verde u oliva", "Verde u oliva"),
        ("negro", "negro u oscuro", "Negro u oscuro"),
    ]),
    ("s_super", "sombrero", "Superficie del sombrero", [
        ("lisa", "lisa y seca", "Lisa y seca"),
        ("viscosa", "viscosa", "Viscosa (pegajosa o babosa)"),
        ("escamas", "con escamas o verrugas", "Con escamas, verrugas o motas"),
        ("fibrosa", "con fibrillas", "Con fibrillas (como pelitos finos)"),
    ]),
    ("s_forma", "sombrero", "Forma del sombrero", [
        ("convexo", "convexo o plano", "Convexo o plano (el normal)"),
        ("conico", "cónico o de campana", "Cónico o de campana"),
        ("embudo", "en embudo", "En embudo o trompeta"),
        ("alveolado", "con alvéolos", "Con alvéolos, como un panal"),
        ("cerebro", "con pliegues de cerebro", "Con pliegues como un cerebro"),
    ]),
    ("h_tipo", "debajo", "Qué hay debajo del sombrero", [
        ("laminas", "láminas", "Láminas (como hojitas finas)"),
        ("poros", "poros", "Poros (como una esponja de tubitos)"),
        ("pliegues", "pliegues", "Pliegues gruesos, venosos y ramificados"),
        ("puas", "púas", "Púas (como agujitas)"),
        ("liso", "liso", "Liso o casi liso, sin láminas ni poros ni púas"),
    ]),
    ("h_color", "debajo", "Color de lo de debajo", [
        ("blanco", "blanco o crema", "Blanco o crema"),
        ("amarillo", "amarillo", "Amarillo"),
        ("naranja", "naranja", "Naranja"),
        ("rojo", "rojo", "Rojo"),
        ("rosa", "rosa o salmón", "Rosa o salmón"),
        ("pardo", "marrón u óxido", "Marrón u óxido"),
        ("gris", "gris", "Gris"),
        ("verde", "verde oliva", "Verde oliva"),
    ]),
    ("p_anillo", "pie", "Anillo en el pie", [
        ("si", "con anillo", "Sí, tiene anillo (falda o collar)"),
        ("no", "sin anillo", "No tiene anillo"),
    ]),
    ("p_base", "pie", "Base del pie", [
        ("bolsa", "dentro de una bolsa (volva)", "Dentro de una bolsa o saco (volva)"),
        ("ensanchada", "ensanchada, sin bolsa", "Ensanchada (bulbo o panza), sin bolsa"),
        ("normal", "normal", "Normal: recta o afinada"),
    ]),
    ("p_super", "pie", "Superficie del pie", [
        ("lisa", "lisa", "Lisa"),
        ("red", "con red", "Con una red (malla fina)"),
        ("puntos", "con puntos, escamas o bandas", "Con puntitos, escamas o bandas"),
    ]),
    ("p_color", "pie", "Color del pie", [
        ("blanco", "blanco o crema", "Blanco o crema"),
        ("amarillo", "amarillo", "Amarillo"),
        ("naranja", "naranja", "Naranja"),
        ("rojo", "rojizo", "Rojo o rojizo"),
        ("pardo", "marrón", "Marrón"),
        ("gris", "gris", "Gris"),
        ("negro", "negro", "Negro"),
    ]),
    # ---- Lo que no sale en una foto: lo rellena la persona ----
    ("s_tam", "otros", "Tamaño del sombrero", [
        ("pequeno", "pequeño (menos de 6 cm)", "Pequeño (menos de 6 cm)"),
        ("mediano", "mediano (6-10 cm)", "Mediano (6-10 cm)"),
        ("grande", "grande (más de 10 cm)", "Grande (más de 10 cm)"),
    ]),
    ("corte", "otros", "Carne al cortarla", [
        ("nada", "no cambia de color", "No cambia de color"),
        ("azulea", "se vuelve azul", "Se vuelve azul"),
        ("enrojece", "se vuelve roja o rosa", "Se vuelve roja o rosa"),
    ]),
    ("latex", "otros", "Leche (látex) al cortar o rascar", [
        ("no", "no sale nada", "No sale nada"),
        ("blanco", "leche blanca", "Sale leche blanca"),
        ("naranja", "látex naranja o rojo vino", "Sale látex naranja o rojo vino"),
    ]),
    ("interior", "otros", "Interior (cortada a lo largo)", [
        ("hueco", "hueca de arriba abajo", "Hueca de arriba abajo, una sola cavidad"),
        ("camaras", "con cámaras o relleno", "Con cámaras, tabiques o relleno algodonoso"),
        ("macizo", "maciza", "Maciza (llena)"),
    ]),
    ("grupo", "otros", "Cómo crecen", [
        ("suelto", "sueltas o dispersas", "Sueltas o dispersas"),
        ("mechon", "en mechones soldados por la base", "En mechones soldados por la base"),
        ("corro", "en corro o círculo", "En corro o círculo"),
    ]),
    ("habitat", "otros", "Dónde crece", [
        ("conifera", "bajo coníferas", "Bajo pinos u otras coníferas"),
        ("planifolio", "bajo planifolios", "Bajo hayas, robles, encinas, castaños..."),
        ("prado", "en prado", "En prado, pasto o claro"),
        ("madera", "sobre madera", "Sobre madera, tocón o raíz"),
    ]),
    ("olor", "otros", "Olor", [
        ("harina", "a harina", "A harina (fresca o rancia)"),
        ("fruta", "afrutado", "Afrutado o a albaricoque"),
        ("almendra", "a almendra o avellana", "A almendra o avellana"),
    ]),
    ("esporada", "otros", "Color de la esporada", [
        ("blanca", "blanca o crema", "Blanca o crema"),
        ("rosa", "rosa", "Rosa"),
        ("marron", "marrón óxido", "Marrón óxido"),
    ]),
]

# Firmas: salen de los textos «cumple», «descarta» y «confunde» de guia_datos.py. Un comentario al lado de cada
# línea dice de qué frase de la ficha sale. Donde la ficha no dice nada, no se pone nada.
FIRMAS = {
    # ------------------------------ Peligrosas ------------------------------
    "phalloides": {  # verde oliváceo (a veces amarillento o casi blanco), liso con fibrillas; láminas y pie blancos, anillo, bolsa
        "s_color": "verde amarillo blanco", "s_super": "lisa fibrosa", "h_tipo!": "laminas", "h_color!": "blanco",
        "p_anillo!": "si", "p_base!": "bolsa", "p_color": "blanco"},
    "amanitas-blancas": {  # enteramente blancas, láminas blancas, anillo y bolsa
        "s_color!": "blanco", "h_tipo!": "laminas", "h_color!": "blanco", "p_anillo!": "si", "p_base!": "bolsa",
        "p_color": "blanco"},
    "lepiota": {  # pequeñas (2-6 cm), escamas marrón-vinosas sobre fondo crema, láminas blancas, esporada blanca
        "s_tam": "pequeno", "s_color": "blanco pardo", "s_super": "escamas", "h_tipo!": "laminas",
        "h_color": "blanco", "esporada": "blanca"},
    "cortinarius": {  # pardo-anaranjadas u óxido; láminas pardo-óxido al madurar; esporada marrón óxido
        "s_color": "pardo naranja", "h_tipo!": "laminas", "h_color": "pardo naranja", "esporada!": "marron"},
    "galerina": {  # pequeña, miel-ocre, sobre madera muerta, en mechones, esporada marrón óxido
        "s_tam": "pequeno", "s_color": "amarillo pardo", "habitat!": "madera", "grupo": "mechon", "esporada!": "marron"},
    "gyromitra": {  # cerebriforme, rojo-pardo, interior con cámaras y tabiques
        "s_forma!": "cerebro", "s_color": "rojo pardo", "interior!": "camaras"},
    "inosperma": {  # fibroso-radial, crema que se enrojece; láminas que se oscurecen y manchan de rojo
        "s_super!": "fibrosa", "s_color": "blanco rojo", "h_tipo!": "laminas", "corte": "enrojece"},
    "clitocybe": {  # pequeño, blanquecino con zonas rosadas o grisáceas, láminas apretadas, de prado
        "s_tam": "pequeno", "s_color": "blanco rosa gris", "h_tipo!": "laminas", "habitat": "prado"},
    "entoloma": {  # grande, blanquecino-grisáceo a ocre; láminas amarillentas que viran a rosa; esporada rosa; olor a harina rancia
        "s_tam": "grande", "s_color": "blanco gris pardo", "h_tipo!": "laminas", "h_color": "amarillo rosa",
        "esporada!": "rosa", "olor": "harina"},
    "satanas": {  # blanquecino-grisáceo; poros rojos o naranja; pie abultado amarillo con red roja; azulea
        "s_color": "blanco gris", "h_tipo!": "poros", "h_color!": "rojo naranja", "p_base": "ensanchada",
        "p_color": "amarillo", "p_super": "red", "corte": "azulea", "habitat": "planifolio"},
    "luridos": {  # sombrero pardo; poros rojo-anaranjados; azulea intensamente; pie con red o puntos rojizos
        "s_color": "pardo", "h_tipo!": "poros", "h_color!": "rojo naranja", "corte!": "azulea", "p_super": "red puntos"},
    "tylopilus": {  # parecido a un cep; poros que se vuelven rosados con la edad; red del pie oscura
        "h_tipo!": "poros", "h_color": "blanco rosa", "p_super": "red"},
    "pardinum": {  # más grande y robusto que el fredolic; gris con escamas oscuras marcadas; olor a harina
        "s_tam": "mediano grande", "s_color!": "gris", "s_super!": "escamas", "olor": "harina"},
    "omphalotus": {  # naranja vivo, en mechones soldados por la base sobre troncos o raíces; láminas finas
        "s_color!": "naranja", "grupo!": "mechon", "habitat!": "madera", "h_tipo!": "laminas"},
    "muscaria": {  # sombrero rojo (o pardo en la pantera) con verrugas blancas; láminas, pie y anillo blancos
        "s_color!": "rojo pardo", "s_super!": "escamas", "h_tipo!": "laminas", "h_color": "blanco", "p_color": "blanco",
        "p_anillo": "si"},
    "torminosus": {  # rosado-asalmonado, látex blanco, bajo abedules
        "s_color": "rosa", "latex!": "blanco", "habitat": "planifolio"},
    # ------------------------------ Setas del predictor ------------------------------
    "rovellons": {  # bajo pinos; naranja o rojizo-vinoso y verdoso; látex naranja o rojo vino; láminas
        "habitat!": "conifera", "s_color": "naranja rojo verde", "latex!": "naranja", "h_tipo!": "laminas"},
    "cep": {  # tubos con poros blancos→amarillentos→verde-oliva; pie panzudo con red clara; carne que NO azulea; olor a avellana
        "h_tipo!": "poros", "h_color!": "blanco amarillo verde", "p_base": "ensanchada normal", "p_super": "red",
        "p_color": "blanco pardo", "corte!": "nada", "s_color": "pardo blanco negro", "olor": "almendra",
        "habitat": "conifera planifolio"},
    "camagrocs": {  # embudo pequeño pardo-grisáceo u oliva; pliegues casi lisos amarillo a rosado-anaranjado; pie amarillo-anaranjado; afrutado
        "s_forma!": "embudo", "s_tam": "pequeno", "s_color": "pardo gris verde", "h_tipo!": "pliegues liso",
        "h_color": "amarillo rosa naranja", "p_color": "amarillo naranja", "olor": "fruta"},
    "rossinyols": {  # amarillo huevo; pliegues gruesos y ramificados; sobre el suelo, suelto; olor a albaricoque
        "s_color": "amarillo", "h_tipo!": "pliegues", "p_color": "amarillo", "grupo!": "suelto", "olor": "fruta",
        "habitat": "conifera planifolio"},
    "trompetes": {  # trompeta negro-grisácea, hueca hasta la base; cara de abajo lisa gris-ceniza; afrutado
        "s_forma!": "embudo", "s_color!": "gris negro", "h_tipo!": "liso", "h_color": "gris", "interior!": "hueco",
        "olor": "fruta", "habitat": "planifolio"},
    "oureig": {  # rojo-anaranjado brillante, liso; láminas, pie y anillo amarillos; bolsa blanca en la base
        "s_color!": "rojo naranja", "s_super": "lisa", "h_tipo!": "laminas", "h_color!": "amarillo",
        "p_color!": "amarillo", "p_anillo!": "si", "p_base!": "bolsa", "habitat": "planifolio"},
    "colmenilles": {  # sombrero con alvéolos; una sola cavidad hueca continua
        "s_forma!": "alveolado", "interior!": "hueco"},
    "llengua": {  # púas frágiles; sombrero crema-anaranjado pálido; pie blanco
        "h_tipo!": "puas", "s_color": "blanco amarillo naranja", "p_color": "blanco", "habitat": "conifera planifolio"},
    "fredolic": {  # cónico o campanulado, gris ratón, fibroso y seco; láminas blancas a gris claro; pie blanco; harina; pinos
        "s_forma": "conico", "s_color!": "gris", "s_super!": "fibrosa", "h_color": "blanco gris", "p_color": "blanco",
        "olor": "harina", "s_tam": "pequeno mediano", "habitat": "conifera"},
    "escarlet": {  # rojo vinoso con manchas rosadas; láminas blancas a crema; esporada blanca; encinares y robledales
        "s_color!": "rojo rosa", "h_tipo!": "laminas", "h_color": "blanco amarillo", "esporada!": "blanca",
        "habitat": "planifolio"},
    "llenega": {  # grande, gris-pardo, MUY viscoso; láminas blancas; pie blanco; esporada blanca; pinares
        "s_tam": "grande", "s_color": "gris pardo", "s_super!": "viscosa", "h_tipo!": "laminas", "h_color": "blanco",
        "p_color": "blanco", "esporada!": "blanca", "habitat": "conifera"},
    "apagallums": {  # GRANDE, escamas marrones sobre fondo claro; pie con piel de serpiente; anillo; láminas blancas; prados
        "s_tam!": "grande", "s_color": "blanco pardo", "s_super": "escamas", "p_super!": "puntos", "p_anillo!": "si",
        "h_tipo!": "laminas", "h_color": "blanco", "esporada": "blanca", "habitat": "prado"},
    "camasec": {  # pequeño (2-5 cm), crema a pardo claro; láminas separadas; en corros en prados; olor a almendra
        "s_tam!": "pequeno", "s_color": "blanco amarillo pardo", "h_tipo!": "laminas", "grupo!": "corro",
        "habitat!": "prado", "olor": "almendra"},
    "moixerno": {  # blanco-crema, convexo; láminas apretadas blancas; harina fresca; corros en prados; no fibroso ni enrojece
        "s_color": "blanco", "s_forma": "convexo", "h_tipo!": "laminas", "h_color": "blanco", "olor!": "harina",
        "grupo": "corro", "habitat": "prado", "s_super": "lisa viscosa escamas", "corte": "nada"},
}

PESO_NORMAL = 1
PESO_CLAVE = 3
# Peso mínimo del «retrato» de una ficha. Si una ficha solo nombra pocos rasgos (por ejemplo la colmenilla: 2), se divide
# igualmente por este número: así no puede llegar a 100 % con solo dos o tres rasgos y no gana a una ficha más detallada.
MIN_PESO = 10
# Con menos de este número de rasgos indicados no se enseña ninguna lista (no tendría sentido).
MIN_RASGOS = 3
# Una ficha solo entra en la lista si se han podido comparar al menos este número de rasgos y la coincidencia (qué parte
# del retrato de la ficha está confirmada) llega a este %.
MIN_COMPARADOS = 2
MIN_PCT = 50
# Además, para entrar en la lista hay que tener al menos este número de rasgos que encajen (o todos los que la ficha describe,
# si describe menos).
MIN_ENCAJAN = 3
# Una peligrosa que falla en algún rasgo clave sigue avisándose (como «no la puedes descartar tan rápido») si aun así llega a este %.
MIN_PCT_DUDOSA = 55


def firma_normalizada(cid):
    """{rasgo: ([valores], peso)} de una ficha."""
    out = {}
    for k, v in FIRMAS[cid].items():
        clave = k.endswith("!")
        out[k.rstrip("!")] = (v.split(), PESO_CLAVE if clave else PESO_NORMAL)
    return out


def exportar(cartas):
    """Datos para el navegador. cartas = {id: gravedad} (gravedad de guia_datos: mortal|muyt|toxica|nocom|ok)."""
    dims = []
    for did, parte, etq, vals in DIMS:
        dims.append({"id": did, "parte": parte, "etq": etq, "valores": [[v, corto, largo] for v, corto, largo in vals]})
    firmas = {cid: {k: [vals, w] for k, (vals, w) in firma_normalizada(cid).items()} for cid in FIRMAS}
    return {
        "dims": dims,
        "firmas": firmas,
        "cartas": {cid: {"grav": g, "peligro": g in ("mortal", "muyt", "toxica")} for cid, g in cartas.items()},
        "min_peso": MIN_PESO, "min_rasgos": MIN_RASGOS, "min_comparados": MIN_COMPARADOS, "min_pct": MIN_PCT, "min_encajan": MIN_ENCAJAN, "min_pct_dudosa": MIN_PCT_DUDOSA,
    }


def vocab_worker():
    """Vocabulario que puede leer la IA de una foto, para el Worker: {parte: {titulo, descripcion, dims: {id: {etq, valores: {v: largo}}}}}."""
    out = {}
    for pid, titulo, desc in PARTES:
        if pid not in PARTES_IA:
            continue
        d = {}
        for did, parte, etq, vals in DIMS:
            if parte == pid:
                d[did] = {"etq": etq, "valores": {v: largo for v, corto, largo in vals}}
        out[pid] = {"titulo": titulo, "descripcion": desc, "dims": d}
    return out


def vocab_js():
    import json
    return "const IDENT_VOCAB = " + json.dumps(vocab_worker(), ensure_ascii=False, indent=2) + ";"
