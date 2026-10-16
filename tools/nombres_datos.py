"""Nombres populares en catalán y castellano de cada ficha de la guía (lo lee generar_guia.py).

REGLA: un nombre popular solo se escribe si aparece en una fuente que se consultó (15/10/2026). El nombre científico es la
referencia (sale de guia_datos.py: campo «cien»). Si ninguna fuente da un nombre en un idioma, la lista queda vacía y la
guía enseña «—». Nunca se inventa un nombre para rellenar.

De las fuentes se toman SOLO los nombres, no lo que dicen de si la seta es comestible.

Formato:  id de ficha -> dict(ca=[...], ca_f="códigos de fuente", es=[...], es_f="códigos", nota="aviso opcional")
Los códigos de fuente están en FUENTES. Los nombres que valen solo para una de las especies de una ficha agrupada llevan
la especie entre paréntesis.
"""

FUENTES = {
    "EC": ("Enciclopèdia Catalana", "https://www.enciclopedia.cat/historia-natural-dels-paisos-catalans/grau-de-comestibilitat-i-toxicitat-de-diferents-bolets-dels"),
    "BOLETS": ("bolets.com y boletaires.cat", "https://boletaires.cat"),
    "3CAT": ("3Cat", "https://www.3cat.cat/3catinfo/trucs-i-advertencies-a-lhora-de-collir-bolets-cuinar-los-i-conservar-los/noticia/3311967/"),
    "CS": ("Canal Salut (Generalitat)", "https://canalsalut.gencat.cat/ca/detalls/article/Intoxicacions_per_bolets"),
    "ICHN": ("Institució Catalana d'Història Natural", "https://ichn2.iec.cat/pdf/flbprot.pdf"),
    "MAD-C": ("Comunidad de Madrid (Real Decreto 30/2009)", "https://www.comunidad.madrid/node/74536", "Comunidad de Madrid: setas comercializables (Real Decreto 30/2009)"),
    "MAD-N": ("Comunidad de Madrid (Real Decreto 30/2009)", "https://www.comunidad.madrid/node/74537", "Comunidad de Madrid: setas no comercializables (Real Decreto 30/2009)"),
    "MAD-T": ("Comunidad de Madrid (Real Decreto 30/2009)", "https://www.comunidad.madrid/node/73272", "Comunidad de Madrid: setas comercializables tras un tratamiento (Real Decreto 30/2009)"),
    "RIO": ("Gobierno de La Rioja", "https://www.larioja.org/medio-ambiente/es/gestion-forestal/aprovechamiento-setas/contenido/especies-recolectables"),
    "ESW": ("es.wikipedia.org", "https://es.wikipedia.org"),
}

NOMBRES = {
    # ------------------------------ Peligrosas ------------------------------
    "phalloides": dict(ca=["farinera borda", "cogoma verda"], ca_f="EC BOLETS CS 3CAT",
                       es=["cicuta verde", "oronja verde o mortal"], es_f="MAD-N"),
    "amanitas-blancas": dict(ca=["cogomassa (A. verna)", "farinera pudent (A. virosa)"], ca_f="EC",
                             es=["cicuta blanca, oronja blanca (A. verna)", "oronja o cicuta fétida, oronja cheposa (A. virosa)"], es_f="MAD-N"),
    "lepiota": dict(ca=["lepiota metzinosa"], ca_f="EC", es=["mucerón"], es_f="MAD-N"),
    "cortinarius": dict(ca=["cortinari metzinós"], ca_f="EC", es=["cortinario de la montaña"], es_f="ESW"),
    "galerina": dict(ca=["galerina marginada"], ca_f="EC", es=["seta rebordeada"], es_f="MAD-N"),
    "gyromitra": dict(ca=["bolet de greix"], ca_f="EC", es=["falsa colmenilla", "hongo bonete"], es_f="ESW",
                      nota="Las listas de Madrid también le llaman «cagarria» o «sombrerete», pero «cagarria» es además un nombre de las colmenillas: no te fíes de ese nombre."),
    "inosperma": dict(ca=[], ca_f="", es=[], es_f=""),
    "clitocybe": dict(ca=["clitocibe blanc"], ca_f="EC", es=["seta de cunetas (C. rivulosa)"], es_f="MAD-N"),
    "entoloma": dict(ca=["fals carlet", "carlet bord"], ca_f="EC", es=["seta engañosa", "pérfida"], es_f="MAD-N ESW"),
    "satanas": dict(ca=["matagent", "mataparent de Satanàs"], ca_f="EC BOLETS", es=["boleto de Satanás", "mataparientes"], es_f="MAD-N"),
    "luridos": dict(ca=["mataparent lívid (S. luridus)", "mataparents de cama vermella (N. erythropus)"], ca_f="EC",
                    es=["boleto de pie rojo (N. erythropus)"], es_f="RIO"),
    "tylopilus": dict(ca=["molleric amarg", "sureny amarg", "siuró amarg"], ca_f="EC ICHN", es=["boleto amargo"], es_f="ESW"),
    "pardinum": dict(ca=["fredolic metzinós", "fredolic bord"], ca_f="EC BOLETS", es=["atigrado", "falsa negrilla"], es_f="MAD-N"),
    "omphalotus": dict(ca=["bolet d'oliu", "gírgola d'olivera"], ca_f="EC", es=["seta de olivo"], es_f="MAD-N ESW"),
    "muscaria": dict(ca=["reig bord (A. muscaria)", "pixacà, reig bru (A. pantherina)"], ca_f="EC BOLETS",
                     es=["falsa oronja, matamoscas (A. muscaria)", "oronja pantera, falso galipierno (A. pantherina)"], es_f="MAD-N"),
    "torminosus": dict(ca=["bolet de cabra"], ca_f="EC", es=["níscalo de abedul", "falso níscalo"], es_f="MAD-N ESW",
                       nota="«Falso níscalo» se usa también para otra especie (Lactarius chrysorrheus): fíate del nombre científico."),
    # ------------------------------ Peligrosas nuevas (15/10) ------------------------------
    "hypholoma": dict(ca=["bolet de pi"], ca_f="EC", es=["seta fasciculada", "hifoloma de láminas verdes"], es_f="MAD-N ESW"),
    "chrysorrheus": dict(ca=["pinetell bord", "rovelló de cabra"], ca_f="EC", es=["falso níscalo"], es_f="MAD-N",
                         nota="«Falso níscalo» se usa también para otra especie (Lactarius torminosus): fíate del nombre científico. Y «rovelló de cabra» NO es un rovelló."),
    "paxillus": dict(ca=[], ca_f="", es=["seta enrollada", "pasillo enrollado"], es_f="MAD-N ESW"),
    "xanthodermus": dict(ca=["bola de neu pudent"], ca_f="EC", es=["champiñón amarilleante"], es_f="MAD-N"),
    "equestre": dict(ca=["groguet", "verderol"], ca_f="EC", es=["seta de los caballeros", "verderol"], es_f="MAD-N",
                     nota="Esos mismos nombres se usan también para Tricholoma auratum y T. flavovirens: fíate del nombre científico."),
    "atramentaria": dict(ca=["bolet de femer"], ca_f="EC", es=["seta antialcohólica"], es_f="MAD-N",
                         nota="La Enciclopèdia Catalana usa «bolet de femer» también para otra especie (Coprinus micaceus)."),
    "emetica": dict(ca=["escaldabecs"], ca_f="EC", es=[], es_f=""),
    # ------------------------------ Setas del predictor ------------------------------
    "rovellons": dict(ca=["rovelló, esclatasangs (L. sanguifluus)", "pinetell (L. deliciosus)"], ca_f="EC",
                      es=["níscalo vinoso (L. sanguifluus)", "níscalo, robellón (L. deliciosus)"], es_f="MAD-C RIO"),
    "cep": dict(ca=["cep (B. edulis y B. pinophilus)", "cep vermell (B. pinophilus)", "sureny fosc, cep negre (B. aereus)", "sureny (B. reticulatus = B. aestivalis)"],
                ca_f="EC BOLETS",
                es=["boleto comestible, hongo, calabaza (B. edulis)", "boleto rojizo, boleto u hongo de pino (B. pinophilus)",
                    "boleto bronceado, boleto u hongo negro (B. aereus)", "boleto reticulado o de verano (B. reticulatus)"], es_f="MAD-C",
                nota="El predictor los llama «cep», «cep fosc» (B. aereus) y «cep d'estiu» (B. reticulatus)."),
    "camagrocs": dict(ca=["camagroc"], ca_f="EC", es=["angula de monte", "rebozuelo anaranjado", "trompeta amarilla"], es_f="MAD-C"),
    "rossinyols": dict(ca=["rossinyol"], ca_f="EC", es=["rebozuelo", "cabrilla", "seta de San Juan"], es_f="MAD-C"),
    "trompetes": dict(ca=["trompeta", "orella d'ase"], ca_f="EC", es=["trompeta de los muertos", "cuerno de la abundancia"], es_f="MAD-C RIO"),
    "oureig": dict(ca=["reig", "ou de reig"], ca_f="EC", es=["amanita de los césares", "oronja", "tana"], es_f="MAD-C",
                   nota="Ojo: «oronja» a secas es la A. caesarea, pero «oronja verde» es la mortal Amanita phalloides."),
    "colmenilles": dict(ca=["múrgola", "rabassola (M. esculenta)", "arigany (M. conica)"], ca_f="EC", es=["colmenilla", "morilla"], es_f="MAD-T RIO",
                        nota="Las listas de Madrid también le llaman «cagarria», nombre que se usa además para la giromitra (tóxica): no te fíes de ese nombre."),
    "llengua": dict(ca=["llengua de bou", "llémena"], ca_f="EC", es=["gamuza", "lengua de gato", "lengua de vaca"], es_f="MAD-C"),
    "fredolic": dict(ca=["fredolic", "negret", "brunet"], ca_f="EC", es=["negrilla", "ratón"], es_f="MAD-C"),
    "escarlet": dict(ca=["carlet"], ca_f="EC 3CAT", es=["seta cardenal", "hongo escarlata"], es_f="MAD-C RIO",
                     nota="El predictor la llama «Escarlet». «Escarlot» es otra especie (Hygrophorus penarius)."),
    "llenega": dict(ca=["llenega negra"], ca_f="EC", es=["llanega negra", "babosa", "mocosa"], es_f="MAD-C"),
    "apagallums": dict(ca=["apagallums"], ca_f="EC", es=["apagador", "galamperna", "matacandelas", "parasol"], es_f="MAD-C"),
    "camasec": dict(ca=["cama-sec", "carrereta"], ca_f="EC", es=["senderuela", "seta de carrerilla"], es_f="MAD-C"),
    "moixerno": dict(ca=["moixernó"], ca_f="EC", es=["seta de San Jorge", "perrechico", "mansarón"], es_f="MAD-C RIO",
                     nota="«Moixernó de tardor» no es esta seta: según bolets.com es Clitocybe nebularis y según la Enciclopèdia Catalana es Lepista luscina."),
    # ------------------------------ Setas nuevas (15/10) ------------------------------
    "vinosa": dict(ca=["vinosa", "cua de cavall"], ca_f="EC", es=["amanita rojiza"], es_f="RIO"),
    "camperol": dict(ca=["camperols"], ca_f="EC", es=["champiñón silvestre"], es_f="MAD-C"),
    "pimpinella": dict(ca=["pimpinella morada"], ca_f="EC", es=["pie azul", "borracha", "pezón azul"], es_f="MAD-C RIO"),
    "alzinoi": dict(ca=["alzinoi"], ca_f="EC", es=[], es_f=""),
    "molleric": dict(ca=["pinetell de calceta (S. luteus)", "molleric, moixí, pinetell (S. granulatus)"], ca_f="EC",
                     es=["babosa, boleto anillado (S. luteus)", "boleto granulado (S. granulatus)"], es_f="MAD-C RIO"),
    "coprinus": dict(ca=["bolet de tinta"], ca_f="EC", es=["barbuda"], es_f="RIO"),
    "orellana": dict(ca=["orellana"], ca_f="EC", es=["seta de ostra", "seta de concha", "seta de alpaca"], es_f="MAD-C"),
    "llora": dict(ca=["llores"], ca_f="EC", es=["carbonera", "seta de los cerdos"], es_f="MAD-C RIO"),
    "molinera": dict(ca=["moixernó blanc de tardor"], ca_f="EC", es=["molinera"], es_f="RIO",
                     nota="«Moixernó de tardor» se usa para especies distintas según la fuente: fíate del nombre científico."),
    "fredolic-gros": dict(ca=["fredolic gros"], ca_f="EC", es=["capuchina", "seta de charol"], es_f="MAD-C RIO"),
    "pampa": dict(ca=["pampa"], ca_f="EC", es=["cabeza de fraile", "platera"], es_f="MAD-C"),
    "pollancro": dict(ca=["pollancró"], ca_f="EC", es=["seta de chopo"], es_f="MAD-C RIO"),
    "marcot": dict(ca=["marçot"], ca_f="EC BOLETS", es=["seta de marzo", "marzuelo", "seta de ardilla"], es_f="MAD-C RIO"),
}


def fuente_larga(codigo):
    """Nombre largo de una fuente (el tercer campo si existe; si no, el corto)."""
    f = FUENTES[codigo]
    return f[2] if len(f) > 2 else f[0]


def fuentes_texto(codigos):
    """'EC CS' -> 'Enciclopèdia Catalana, Canal Salut (Generalitat)' (sin repetir)."""
    out = []
    for c in codigos.split():
        n = FUENTES[c][0]
        if n not in out:
            out.append(n)
    return ", ".join(out)


# ---- Ampliación del 16/10/2026: nombres de las fichas nuevas (catalán de la Enciclopèdia Catalana; castellano de es.wikipedia) ----
import guia_ampliada as _ga  # noqa: E402
import guia_datos as _gd  # noqa: E402

_nuevos = _ga.nombres()
assert not set(_nuevos) & set(NOMBRES), "nombre repetido en la ampliación"
NOMBRES.update(_nuevos)
_tit = {p_[0]: p_[1].split(" (")[0] for p_ in _gd.PELIGROSAS}
_tit.update({f_["ids"][0]: f_["nombre"].split(" (")[0] for f_ in _gd.FICHAS})
_ga.anadir_notas_compartidas(NOMBRES, _tit)
