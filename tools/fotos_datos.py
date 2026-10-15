"""Qué foto lleva cada ficha de la guía (lo lee descargar_fotos.py).

Clave = id de la ficha en la guía (el primer id de cada ficha de guia_datos.py).
Valor = lista de «huecos de foto». Cada hueco es una lista de nombres científicos alternativos: el script usa el
primero que encuentre con una foto de licencia libre. Más de un hueco = más de una foto en la ficha.

Las fotos salen de Wikimedia Commons (vía Wikipedia). Solo se aceptan licencias libres (CC BY, CC BY-SA, CC0 o
dominio público) y en cada foto se enseña autor y licencia, como exigen esas licencias.

FORZAR: si una foto automática no es buena (porque no es la seta, es un dibujo, es una foto mala...), se pone aquí el
nombre exacto del archivo de Commons para esa ficha y esa posición y el script lo usa en lugar de buscar.
Formato:  "id": {0: "Nombre del archivo.jpg"}   (0 = primer hueco, 1 = segundo...).
Si el archivo forzado no sirve (no existe, licencia no libre...), ese hueco se queda SIN foto: nunca se deja la anterior.
"""

FOTOS = {
    # --- Peligrosas ---
    "phalloides": [["Amanita phalloides"]],
    "amanitas-blancas": [["Amanita verna"], ["Amanita virosa"]],
    "lepiota": [["Lepiota brunneoincarnata"]],
    "cortinarius": [["Cortinarius orellanus"]],
    "galerina": [["Galerina marginata"]],
    "gyromitra": [["Gyromitra esculenta"]],
    "inosperma": [["Inosperma erubescens", "Inocybe erubescens"]],
    "clitocybe": [["Clitocybe rivulosa", "Clitocybe dealbata"]],
    "entoloma": [["Entoloma sinuatum"]],
    "satanas": [["Rubroboletus satanas", "Boletus satanas"]],
    "luridos": [["Suillellus luridus", "Boletus luridus"], ["Neoboletus erythropus", "Boletus erythropus"]],
    "tylopilus": [["Tylopilus felleus"]],
    "pardinum": [["Tricholoma pardinum"]],
    "omphalotus": [["Omphalotus olearius"]],
    "muscaria": [["Amanita muscaria"], ["Amanita pantherina"]],
    "torminosus": [["Lactarius torminosus"]],
    # --- Setas del predictor ---
    "rovellons": [["Lactarius deliciosus"], ["Lactarius sanguifluus"]],
    "cep": [["Boletus edulis"], ["Boletus aereus"], ["Boletus reticulatus"]],
    "camagrocs": [["Craterellus lutescens", "Cantharellus lutescens"]],
    "rossinyols": [["Cantharellus cibarius"]],
    "trompetes": [["Craterellus cornucopioides"]],
    "oureig": [["Amanita caesarea"]],
    "colmenilles": [["Morchella esculenta"], ["Morchella elata"]],
    "llengua": [["Hydnum repandum"]],
    "fredolic": [["Tricholoma terreum"]],
    "escarlet": [["Hygrophorus russula"]],
    "llenega": [["Hygrophorus latitabundus"]],
    "apagallums": [["Macrolepiota procera"]],
    "camasec": [["Marasmius oreades"]],
    "moixerno": [["Calocybe gambosa", "Tricholoma georgii"]],
    # --- Añadidas el 15/10/2026 (las fotos se descargan con el workflow y se revisan a ojo después) ---
    "hypholoma": [["Hypholoma fasciculare"]],
    "chrysorrheus": [["Lactarius chrysorrheus"]],
    "paxillus": [["Paxillus involutus"]],
    "xanthodermus": [["Agaricus xanthodermus"]],
    "equestre": [["Tricholoma equestre", "Tricholoma flavovirens"]],
    "atramentaria": [["Coprinopsis atramentaria", "Coprinus atramentarius"]],
    "emetica": [["Russula emetica"]],
    "vinosa": [["Amanita rubescens"]],
    "camperol": [["Agaricus campestris"]],
    "pimpinella": [["Lepista nuda", "Clitocybe nuda"]],
    "alzinoi": [["Armillaria mellea"]],
    "molleric": [["Suillus luteus"], ["Suillus granulatus"]],
    "coprinus": [["Coprinus comatus"]],
    "orellana": [["Pleurotus ostreatus"]],
    "llora": [["Russula cyanoxantha"]],
    "molinera": [["Clitopilus prunulus"]],
    "fredolic-gros": [["Tricholoma portentosum"]],
    "pampa": [["Infundibulicybe geotropa", "Clitocybe geotropa"]],
    "pollancro": [["Cyclocybe cylindracea", "Agrocybe aegerita"]],
    "marcot": [["Hygrophorus marzuolus"]],
}

FORZAR = {
    # Revisadas a ojo el 15/10/2026: la foto automática del cep fosc era de B. pinophilus, la del cep d'estiu tenía un
    # nombre genérico («Boletus.JPG») y la del lactario torminoso era de Lactarius mairei (otra especie).
    "cep": {1: "Boletus aereus IT.JPG", 2: "Boletus reticulatus (28576784573).jpg"},
    "torminosus": {0: "Lactarius torminosus 041031w.jpg"},
}
