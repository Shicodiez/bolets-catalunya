"""Qué foto lleva cada ficha de la guía (lo lee descargar_fotos.py).

Clave = id de la ficha en la guía (el primer id de cada ficha de guia_datos.py).
Valor = lista de «huecos de foto». Cada hueco es una lista de nombres científicos alternativos: el script usa el
primero que encuentre con una foto de licencia libre. Más de un hueco = más de una foto en la ficha.

Las fotos salen de Wikimedia Commons (vía Wikipedia). Solo se aceptan licencias libres (CC BY, CC BY-SA, CC0 o
dominio público) y en cada foto se enseña autor y licencia, como exigen esas licencias.

FORZAR: si una foto automática no es buena (porque no es la seta, es un dibujo, es una foto mala...), se pone aquí el
nombre exacto del archivo de Commons para esa ficha y esa posición y el script lo usa en lugar de buscar.
Formato:  "id": {0: "Nombre del archivo.jpg"}   (0 = primer hueco, 1 = segundo...).
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
}

FORZAR = {}
