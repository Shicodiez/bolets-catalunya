"""Especies añadidas a la guía el 16/10/2026 (ampliación de 50 a unas 300 fichas).

Cada especie se escribe UNA vez aquí con todo lo que necesita (texto de la ficha, rasgos para la comparación, nombres,
foto y fuente) y los módulos de siempre (guia_datos, rasgos_datos, nombres_datos, fotos_datos) la recogen al final.

Cómo se redactó (límites reconocidos):
  * El texto de cada ficha lo ha redactado una IA a partir de lo que dice la página de Wikipedia en inglés de la especie
    (consultada el 16/10/2026) y, para los nombres en catalán y el grado «a refusar / tòxic», de la tabla de la Enciclopèdia
    Catalana. Donde la fuente no dice algo (color de las láminas, esporada, anillo...), la ficha no lo dice y el rasgo no se pone.
  * NO lo ha revisado ningún micólogo. No hay una tabla «frase → párrafo exacto de la fuente».
  * La guía nunca dice «se puede comer»: de las especies buenas comestibles solo se avisa de lo que obliga a la cautela.
  * Las fichas «P» (peligrosas) salen cuando la fuente dice que la especie es tóxica o no se recomienda por riesgo; las «F»
    son el resto (riesgo de confusión bajo, medio o alto según las parecidas que cita la fuente).
  * Un nombre popular solo se escribe si lo da una fuente consultada (EC = Enciclopèdia Catalana; ESW = es.wikipedia.org).
Convenciones de «firma» (rasgos de comparación): ver rasgos_datos.py. «!» = rasgo clave (peso 3).
"""

ESPECIES = []


def P(id, cien, grav, cumple, confunde, firma, ca=(), ca_f="", es=(), es_f="", foto=None, nombre=None, src="WP"):
    """Ficha de una especie tóxica o que no se recomienda por riesgo (grav: mortal | muyt | toxica | nocom)."""
    assert grav in ("mortal", "muyt", "toxica", "nocom"), id
    assert isinstance(confunde, str) and isinstance(firma, dict) and all(isinstance(c, str) for c in cumple), id
    ESPECIES.append(dict(tipo="P", id=id, cien=cien, grav=grav, cumple=list(cumple), confunde=confunde, firma=firma,
                         ca=list(ca), ca_f=ca_f, es=list(es), es_f=es_f, foto=foto, nombre=nombre, src=src))


def F(id, cien, riesgo, cumple, descarta, confunde, donde, firma, ca=(), ca_f="", es=(), es_f="", foto=None, nombre=None, src="WP"):
    """Ficha «buscada» o sin riesgo propio (riesgo: bajo | medio | alto = riesgo de confundirla con algo peligroso)."""
    assert riesgo in ("bajo", "medio", "alto"), id
    assert isinstance(donde, str) and isinstance(firma, dict) and all(isinstance(c, str) for c in cumple + descarta), id
    assert all(isinstance(c, tuple) and len(c) == 3 and (c[1] is None or c[1] in ("mortal", "muyt", "toxica", "nocom", "ok")) for c in confunde), id
    ESPECIES.append(dict(tipo="F", id=id, cien=cien, riesgo=riesgo, cumple=list(cumple), descarta=list(descarta),
                         confunde=list(confunde), donde=donde, firma=firma, ca=list(ca), ca_f=ca_f, es=list(es), es_f=es_f,
                         foto=foto, nombre=nombre, src=src))


# ============================================================================================================
# AMANITAS (todas con bolsa o resto de volva: ver SOLO_EN en rasgos_datos.py)
# ============================================================================================================
P("amanita-citrina", "Amanita citrina", "toxica",
  ["Sombrero de unos 4-10 cm, amarillo pálido o a veces blanco, cubierto de parches irregulares (restos del velo).",
   "Láminas blancas; pie blanco, de unos 6-8 cm, con un anillo bien visible y una volva grande en la base.",
   "Bosques de planifolios y de coníferas (robledales y pinares), en verano y otoño.",
   "Según Wikipedia no es comestible por su toxicidad (se cita que contiene alfa-amanitina y bufotenina); la Enciclopèdia Catalana la pone «a refusar»."],
  "Con la oronja verde (Amanita phalloides): Wikipedia dice que el mayor peligro de esta seta es su gran parecido con ella. Compara con la ficha de la oronja verde.",
  dict(s_color="amarillo blanco", s_super="escamas", h_tipo="!laminas", h_color="blanco", p_anillo="!si", p_base="bolsa ensanchada",
       p_color="blanco", habitat="conifera planifolio", s_tam="pequeno mediano"),
  ca=["reig bord groc"], ca_f="EC")

P("amanita-gemmata", "Amanita gemmata", "toxica",
  ["Sombrero de unos 2,5-12 cm, amarillo crema a dorado o ante, pegajoso con humedad, con verrugas blancas que se lavan con facilidad.",
   "Láminas blancas, pegadas al pie; pie amarillento pálido de unos 4-12 cm, con un anillo frágil que se pierde con facilidad y una volva blanca que forma un pequeño reborde libre en la base.",
   "Suelos arenosos y algo ácidos, en bosques de coníferas y mixtos, sobre todo junto a caminos; verano y otoño.",
   "Wikipedia la da como tóxica (ácido iboténico y muscimol); dice que los casos graves, con coma, convulsiones o muerte, son «extremadamente raros»."],
  "Con la falsa oronja (Amanita citrina), la amanita pardo-anaranjada (Amanita fulva) y la amanita pantera: Wikipedia dice que su sombrero es más brillante que el de la primera y más amarillo que el de las otras dos.",
  dict(s_color="amarillo pardo", s_super="viscosa escamas", h_tipo="!laminas", h_color="blanco", p_anillo="si", p_base="bolsa",
       p_color="amarillo blanco", habitat="conifera"))

P("amanita-franchetii", "Amanita franchetii", "toxica",
  ["Sombrero de unos 5-12 cm, pardo amarillento a pardo, con las láminas apretadas y del color de la carne (blanca o amarillo pálido); olor suave.",
   "Pie grueso, blanco a amarillento, con un anillo grueso, ensanchado en la base y con restos amarillos sueltos del velo.",
   "Bajo robles, castaños y pinos, en Europa y el norte de África.",
   "Wikipedia dice que se considera no comestible y que se ha comunicado como tóxica cruda o poco cocinada; se vinculó a la muerte de diez personas en China en 2005, aunque la identificación de ese caso se ha puesto en duda."],
  "Wikipedia no cita una confusión concreta en Europa; como con cualquier amanita, si no tienes certeza total no se come.",
  dict(s_color="pardo amarillo", h_tipo="!laminas", h_color="blanco amarillo", p_anillo="si", p_base="ensanchada",
       p_color="blanco amarillo", habitat="planifolio conifera"))

F("amanita-vaginata", "Amanita vaginata", "alto",
  ["Sombrero de unos 5-10 cm, ovalado de joven y luego cónico a plano (a veces con un pequeño mamelón), gris o pardo, con el borde marcadamente estriado.",
   "Láminas blancas, libres o casi libres, y esporada blanca.",
   "Pie largo (8-22 cm), fino y SIN anillo, con una bolsa (volva) holgada y suelta en la base, no bulbosa.",
   "Micorrícica: sale en bosques de coníferas y de planifolios, en bordes herbosos y en céspedes; de primavera a otoño."],
  ["Pie con anillo (esta seta no lo tiene).", "Base sin bolsa."],
  [("Amanita fulva", None, "casi igual pero más anaranjada; Wikipedia la da como «muy parecida»."),
   ("Amanita crocea", None, "sombrero amarillo anaranjado."),
   ("Otras amanitas tóxicas", None, "Wikipedia avisa de especies tóxicas emparentadas; dentro del género Amanita hay especies mortales, por eso la bolsa en la base no basta para decidir.")],
  "Bosques de coníferas y de planifolios, bordes herbosos y césped. Wikipedia dice que, aunque no es venenosa, la mayoría de autores aconseja no consumirla, y que debe cocinarse a fondo.",
  dict(s_color="gris pardo", s_forma="convexo conico", h_tipo="!laminas", h_color="blanco gris", p_anillo="!no", p_base="!bolsa",
       esporada="blanca", habitat="conifera planifolio prado", s_tam="pequeno mediano"),
  ca=["pentinella"], ca_f="EC")

F("amanita-crocea", "Amanita crocea", "alto",
  ["Sombrero de unos 5-10 cm, amarillo anaranjado con tono albaricoque en el centro, aplanado y con un pequeño mamelón.",
   "Láminas libres, color crema; pie de 10-15 cm, con fibrillas anaranjadas en forma de llama y SIN anillo.",
   "En la base, una volva gruesa, membranosa y en forma de saco, de al menos 4-10 cm de ancho.",
   "Micorrícica con planifolios (abedul, haya), en claros; de julio a octubre; poco frecuente."],
  ["Pie con anillo.", "Base sin bolsa.", "Láminas y pie de color amarillo vivo (eso es el ou de reig, Amanita caesarea)."],
  [("Amanita fulva", None, "similar; no hay diferencia clara en la fuente consultada."),
   ("Oronja verde (Amanita phalloides)", "mortal", "Wikipedia dice que se puede confundir fácilmente, aunque la amanita azafranada es menos robusta."),
   ("Ou de reig (Amanita caesarea)", None, "sombrero naranja, pero láminas y pie amarillos.")],
  "Bajo abedul y haya, en claros; de julio a octubre en Europa. Wikipedia dice que es comestible pero que no se recomienda por su parecido con especies tóxicas del mismo género.",
  dict(s_color="naranja amarillo", s_forma="convexo conico", h_tipo="!laminas", h_color="blanco", p_anillo="!no", p_base="!bolsa",
       p_color="naranja blanco", esporada="blanca", habitat="planifolio", s_tam="pequeno mediano"),
  ca=["pentinella safranada"], ca_f="EC")

F("amanita-fulva", "Amanita fulva", "alto",
  ["Sombrero de hasta unos 10 cm, naranja-pardo a rojizo, liso, viscoso con humedad y con el borde muy estriado.",
   "Láminas libres, anchas y próximas; esporada blanca.",
   "Pie de hasta 15 cm, blanco (a veces teñido de naranja-pardo), hueco y frágil, SIN anillo, con una bolsa (volva) blanca con manchas de óxido en la base.",
   "Suelos ácidos, bajo roble, abedul, picea, pino, castaño o aliso; de mayo a noviembre en el Reino Unido."],
  ["Pie con anillo.", "Base sin bolsa."],
  [("Amanita vaginata", None, "muy parecida pero menos anaranjada."),
   ("Amanita gemmata", "toxica", "sombrero amarillo con verrugas blancas y anillo frágil.")],
  "Bosques de Europa sobre suelo ácido. Wikipedia dice que se considera comestible pero que consumirla puede ser peligroso, que no se recomienda y que es potencialmente tóxica cruda.",
  dict(s_color="naranja pardo", s_super="lisa viscosa", h_tipo="!laminas", p_anillo="!no", p_base="!bolsa", p_color="blanco naranja",
       interior="hueco", esporada="blanca", habitat="planifolio conifera", s_tam="pequeno mediano"),
  ca=["pentinella rogenca"], ca_f="EC")

F("amanita-ovoidea", "Amanita ovoidea", "alto",
  ["Seta grande (el ejemplar entero pasa de 15 cm), blanca o crema, con el sombrero hemisférico de joven, liso y sedoso, y restos algodonosos del velo colgando del borde.",
   "Láminas gruesas, anchas y libres; esporada blanca; carne gruesa, blanca, de olor fuerte y desagradable.",
   "Anillo frágil y algodonoso; volva grande, blanca a crema ocre, en la base.",
   "Suelos calizos y arenosos, bajo pinos y encinas o robles; Mediterráneo; a menudo semienterrada."],
  ["Seta de color distinto al blanco o crema.", "Base sin volva."],
  [("Amanitas blancas (Amanita verna y A. virosa)", "mortal", "también son todas blancas; Wikipedia no da cómo separarlas, por eso nunca se come una amanita blanca sin certeza total."),
   ("Amanita proxima", "toxica", "su volva es de color ocre-rojizo y tiene un anillo persistente y colgante, y el margen del sombrero liso, sin restos del velo.")],
  "Bosques mediterráneos de pinos y encinas; la Enciclopèdia Catalana la incluye entre las «acceptables». Wikipedia dice que su comestibilidad es «dudosa» (un estudio turco de 2008 la dio por segura) y cita como parecidas dos amanitas blancas mortales.",
  dict(s_color="blanco", s_super="lisa fibrosa", s_forma="convexo", h_tipo="!laminas", p_anillo="si", p_base="!bolsa", p_color="blanco",
       esporada="blanca", habitat="conifera planifolio", s_tam="grande"),
  ca_f="EC")

F("amanita-spissa", "Amanita spissa · Amanita excelsa", "alto",
  ["Sombrero de unos 10 cm, pardo o pardo grisáceo que puede aclarar a color ante, con restos grises del velo en parches planos que se lavan con el tiempo.",
   "Láminas blancas, apretadas, con un pequeño diente que baja por el pie; pie largo con un anillo grande y blanco, marcado por líneas, y estrías verticales por encima.",
   "Base bulbosa SIN volva visible: en su lugar hay varias zonas escamosas, como anillos.",
   "Carne blanca con olor a rábano; bosques de coníferas y de planifolios; verano y otoño."],
  ["Base con una bolsa (volva) bien visible.", "Pie sin anillo."],
  [("Amanita pantera (Amanita pantherina)", "toxica", "tiene restos blancos del velo en el sombrero y un reborde definido en la base del pie; parece una amanita muscaria parda."),
   ("Amanita vinosa (Amanita rubescens)", None, "con el tiempo puede quedar del mismo color."),
   ("Amanita excelsa var. excelsa", None, "es más esbelta y no tiene olor a rábano.")],
  "Bosques de coníferas y de planifolios de Europa y de América del Norte. Wikipedia dice que algunos la dan por comestible, pero que lo mejor es evitarla por si se confunde con la amanita pantera.",
  dict(s_color="pardo gris", s_super="escamas", h_tipo="!laminas", h_color="blanco", p_anillo="!si", p_base="ensanchada",
       p_color="blanco", habitat="conifera planifolio", s_tam="mediano grande"),
  ca=["cua de cavall grossa"], ca_f="EC")


# ============================================================================================================
# LEPIOTAS, CHAMPIÑONES, PARASOLES Y BOVISTAS
# ============================================================================================================
P("lepiota-clypeolaria", "Lepiota clypeolaria", "toxica",
  ["Sombrero de unos 4-7 cm, de huevo a campana, con escamas pardo-anaranjadas pálidas sobre fondo claro y un disco central bien delimitado del mismo color.",
   "Láminas blancas, apretadas y libres; esporada blanca.",
   "Pie de unos 5-12 cm, hueco, delgado, blanco, algo engrosado en la base; anillo poco claro, deshecho en forma de vaina y lanoso por debajo, como «con botas».",
   "En el suelo, solitaria o en grupos pequeños, en bosques de planifolios y de coníferas; otoño. Olor desagradable."],
  "Wikipedia la da como venenosa y dice que se parece a algunas de las especies más mortales de su género (las Lepiota pequeñas como L. brunneoincarnata). Compara con la ficha de las lepiotas pequeñas.",
  dict(s_color="pardo amarillo", s_super="escamas", s_forma="conico convexo", h_tipo="!laminas", h_color="blanco", p_anillo="si", p_color="blanco",
       esporada="blanca", interior="hueco", habitat="conifera planifolio", s_tam="pequeno"))

P("echinoderma-asperum", "Echinoderma asperum (Lepiota aspera)", "toxica",
  ["Sombrero de hasta unos 10 cm, de ovalado a campana, pardo rojizo uniforme en el centro y más pálido en el resto, con escamas piramidales erguidas.",
   "Láminas blancas, apretadas, libres y a menudo bifurcadas; esporada blanca.",
   "Pie de unos 10 cm, más claro que el sombrero, con un anillo grande y algodonoso que a veces se pega al borde del sombrero y debajo del cual hay escamas pardas dispersas.",
   "Sobre astillas de madera o corteza, o entre hojarasca de bosque de planifolios; otoño. Olor que recuerda al caucho."],
  "Wikipedia dice que, aunque a veces se cita como comestible, esta seta provoca intolerancia al alcohol y puede ser venenosa; la parecen algunas amanitas. Echinoderma calcicola tiene las verrugas del color del fondo y láminas no bifurcadas y menos apretadas; E. hystrix es más oscura y con el borde de las láminas oscuro.",
  dict(s_color="pardo rojo", s_super="escamas", s_forma="convexo conico", h_tipo="!laminas", h_color="blanco", p_anillo="si", esporada="blanca",
       habitat="planifolio madera", s_tam="mediano"))

F("cystoderma-amianthinum", "Cystoderma amianthinum", "alto",
  ["Sombrero pequeño (1-5 cm), de convexo a campana y luego plano con un mamelón bajo; amarillo azafrán a ocre anaranjado, seco y polvoriento, con el borde a menudo deshilachado.",
   "Láminas primero apretadas, blancas y luego cremas, estrechamente pegadas al pie; esporada blanca.",
   "Pie cilíndrico con un anillo fugaz y polvoriento, con una vaina escamosa-granulosa por debajo; olor desagradable o a maíz descascarillado.",
   "En prados húmedos con musgo, claros de bosque de coníferas y brezales, a menudo en suelos ácidos."],
  ["Sombrero rojizo y láminas anchamente pegadas (así son Cystodermella granulosa y C. cinnabarina).", "Sombrero sin aspecto polvoriento."],
  [("Lepiota castanea", "mortal", "Wikipedia la cita como parecida y «mortalmente tóxica»; no da cómo separarlas, así que no la recojas para comer."),
   ("Cystodermella granulosa y C. cinnabarina", None, "como regla son más rojizas y de láminas anchamente pegadas al pie.")],
  "Praderas con musgo y bosques de coníferas, de Europa y América del Norte. Wikipedia dice que no se recomienda comerla por su parecido con especies venenosas.",
  dict(s_color="amarillo naranja", s_super="lisa", s_forma="convexo conico", h_tipo="!laminas", h_color="blanco", p_anillo="si", esporada="blanca",
       habitat="prado conifera", s_tam="pequeno"))

F("cystoderma-carcharias", "Cystoderma carcharias", "bajo",
  ["Sombrero de hasta unos 6 cm, convexo y luego plano con un mamelón bajo, blanquecino con tono rosa pálido y una mancha central más oscura; cutícula polvorienta y borde a veces con restos del velo.",
   "Láminas blancas, apretadas y pegadas al pie; pie de hasta unos 7 cm, blanco, con un anillo blanco, vuelto hacia arriba y persistente, liso por encima y granuloso por debajo.",
   "Carne blanca y firme, con olor fuerte y desagradable a tierra y moho.",
   "En el suelo entre hierba o musgo, a menudo bajo picea, sola o en grupos; finales de verano y otoño."],
  ["Sombrero sin tono rosado ni mancha central.", "Pie sin anillo."],
  [("Otras setas pequeñas con anillo", None, "la fuente consultada no cita ninguna confusión concreta.")],
  "Praderas y bosques de Europa, América del Norte y Asia templada. Wikipedia dice que varios autores la consideran no comestible.",
  dict(s_color="blanco rosa", s_super="lisa", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_anillo="si", p_color="blanco",
       habitat="prado conifera", s_tam="pequeno"))

P("agaricus-moelleri", "Agaricus moelleri", "toxica",
  ["Sombrero de 5-9 cm, ovalado de joven y luego aplanado, con una mancha central pardo-grisácea y escamas grisáceas sobre fondo blanquecino; amarillea al tocarlo.",
   "Láminas libres y apretadas, rosadas de joven y pardas a negras de mayor; esporada que no se describe en la fuente (las esporas son pardas).",
   "Pie que amarillea con mucha facilidad al tocarlo y luego pasa a pardo, con un anillo colgante; carne blanca que no cambia al cortarla.",
   "Olor a tinta, yodoformo, fenol, sudor o paja mohosa; en bosques variados y parques de suelos ricos y alcalinos; finales de verano."],
  "Wikipedia dice que se considera tóxica y que puede dar síntomas digestivos a unas personas y a otras no. Con otros champiñones que amarillean: A. hondensis (tono rosado y carne más firme) y A. phaeolepidotus (escamas más pardas, amarillea menos). Compara con la ficha del champiñón amarilleante.",
  dict(s_color="blanco gris pardo", s_super="escamas", s_forma="convexo", h_tipo="!laminas", h_color="rosa pardo", p_anillo="!si", corte="amarillea",
       habitat="planifolio", s_tam="mediano"),
  ca=[], ca_f="")

F("agaricus-arvensis", "Agaricus arvensis", "alto",
  ["Sombrero grande (7-20 cm), blanquecino, liso y seco, que amarillea al tocarlo, sobre todo de joven.",
   "Láminas rosa pálido a blancas al principio y luego grises, pardas y por fin pardo chocolate; esporada pardo oscura.",
   "Anillo grande y extendido, blanco por arriba y a veces con escamas amarillentas por debajo, con dibujo de «rueda dentada».",
   "Olor a extracto de almendra o mazapán; carne que amarillea al golpearla; en prados y cerca de cuadras, a veces en corro, entre cipreses o piceas."],
  ["Láminas blancas a cualquier edad.", "Bolsa (volva) en la base del pie.", "Olor a fenol o a tinta, o carne que amarillea de forma muy viva al cortar la base."],
  [("Amanitas mortales (Amanita verna)", "mortal", "Wikipedia las cita como confusión peligrosa; las amanitas tienen láminas blancas y bolsa en la base."),
   ("Champiñón amarilleante (Agaricus xanthodermus)", "toxica", "puede dar molestias de estómago."),
   ("Agaricus osecanus", None, "raro; no tiene olor a almendra.")],
  "Praderas y pastos, a menudo cerca de cuadras o con ortigas; de julio a noviembre en Gran Bretaña. Wikipedia recuerda que los champiñones acumulan metales pesados si crecen en suelos contaminados.",
  dict(s_color="blanco", s_super="lisa", s_forma="convexo", h_tipo="!laminas", h_color="rosa pardo gris blanco", p_anillo="!si", corte="amarillea", esporada="chocolate",
       habitat="prado", s_tam="grande"),
  ca=["boles de neu (joves)"], ca_f="EC")

F("agaricus-bisporus", "Agaricus bisporus", "alto",
  ["Sombrero de unos 5-10 cm en la forma silvestre, primero hemisférico y luego plano, gris-pardo pálido, con escamas anchas y planas sobre fondo más claro que se difuminan hacia el borde.",
   "Láminas estrechas, apretadas y libres: rosadas de joven, luego pardo rojizas y por fin pardo oscuras con el filo blanquecino; esporada pardo oscura.",
   "Pie de hasta unos 6 cm, con un anillo grueso y estrecho que puede estar estriado por arriba; carne blanca que enrojece pálido al magullarla.",
   "En suelo rico, compost o estiércol, en pastos de Eurasia y América del Norte; otoño-invierno."],
  ["Láminas blancas a cualquier edad.", "Bolsa (volva) en la base del pie.", "Olor a fenol o carne que amarillea muy rápido."],
  [("Amanitas blancas (ángeles destructores)", "mortal", "Wikipedia las cita como parecidas; se distinguen por la volva en la base y las láminas blancas puras."),
   ("Champiñón amarilleante (Agaricus xanthodermus)", "toxica", "huele a fenol y la carne amarillea al magullarla; causa náuseas y vómitos a algunas personas."),
   ("Entoloma lívido (Entoloma sinuatum)", "toxica", "tiene láminas amarillentas que pasan a rosa y no tiene anillo.")],
  "Especie muy cultivada (champiñón de París, portobello); la forma silvestre sale en pastos y suelos ricos.",
  dict(s_color="gris pardo", s_super="escamas", s_forma="convexo", h_tipo="!laminas", h_color="rosa pardo", p_anillo="!si", corte="enrojece", esporada="chocolate",
       habitat="prado", s_tam="mediano"),
  ca=["xampinyó"], ca_f="EC")

F("agaricus-bitorquis", "Agaricus bitorquis", "alto",
  ["Sombrero de 4-18 cm, de convexo a plano, blanco que amarillea con la edad, seco y liso.",
   "Láminas libres, muy estrechas y apretadas: rosa pálido de joven y pardo rojizas oscuras después; esporada pardo chocolate.",
   "Pie de 3-11 cm, blanco y liso, con DOS anillos: uno superior ancho, en forma de embudo, y otro inferior más fino, en forma de falda.",
   "Crece en aceras, bordes de carreteras y donde se echa sal para el hielo, a veces empujando el asfalto; es raro en el bosque."],
  ["Un solo anillo fino y frágil (eso es el camperol).", "Láminas blancas a cualquier edad.", "Bolsa (volva) en la base del pie."],
  [("Agaricus bernardii", None, "se confunde a menudo; huele a salmuera."),
   ("Camperol (Agaricus campestris)", None, "algo parecido pero con un solo anillo frágil."),
   ("Amanitas blancas", "mortal", "como cualquier champiñón: láminas blancas y bolsa en la base → mortal (ver su ficha).")],
  "Suelos pisados y bordes de carreteras. Wikipedia advierte de que puede acumular metales pesados, sobre todo plomo, en zonas contaminadas, y que las setas silvestres pueden salir arenosas.",
  dict(s_color="blanco", s_super="lisa", s_forma="convexo", h_tipo="!laminas", h_color="rosa pardo", p_anillo="!si", p_color="blanco", esporada="chocolate",
       s_tam="mediano grande"),
  ca=["camperols"], ca_f="EC")

F("agaricus-sylvaticus", "Agaricus sylvaticus (A. silvaticus)", "alto",
  ["Sombrero de hasta unos 10 cm, hemisférico y luego plano, pardo grisáceo, cubierto de anchas escamas.",
   "Láminas grises de joven y mucho más oscuras con la edad; esporas pardo chocolate.",
   "Pie con un anillo colgante y una pequeña base bulbosa; carne blanca que se vuelve ROJIZA al cortarla; sabor suave.",
   "Bosques de coníferas de Europa, el norte de África y América del Norte; a principios de verano o de septiembre a noviembre en Europa."],
  ["Carne que NO enrojece al cortarla.", "Pie que amarillea al cortarlo y olor a yodo o tinta (eso es A. phaeolepidotus)."],
  [("Agaricus phaeolepidotus", None, "el pie amarillea además de enrojecer y huele a yodo o a tinta; el sombrero es más pardo."),
   ("Tricholoma vaccinum", None, "desde arriba se parece, pero no tiene anillo y las láminas se ponen pardo-rojizas.")],
  "Pinares y abetales. Wikipedia dice que es comestible cocinada pero que se parece a setas no comestibles y que algunas parecidas dan molestias de estómago. El rubiol de sang de la Enciclopèdia Catalana (A. haemorrhoidarius) se considera normalmente un sinónimo.",
  dict(s_color="gris pardo", s_super="escamas", s_forma="convexo", h_tipo="!laminas", h_color="gris pardo", p_anillo="!si", p_base="ensanchada", corte="enrojece",
       esporada="chocolate", habitat="conifera", s_tam="mediano"),
  ca=["rubiol"], ca_f="EC")

F("agaricus-sylvicola", "Agaricus sylvicola", "alto",
  ["Sombrero de 5-15 cm, crema claro que se vuelve ocre amarillento al dañarlo.",
   "Pie del mismo color que el sombrero, con un anillo frágil y colgante y una base normalmente bulbosa; carne blanca con olor a almendra o anís.",
   "Esporas pardas, lisas y elípticas; la fuente no describe las láminas.",
   "Bosques de planifolios y de coníferas, solitario o en pocos ejemplares; otoño."],
  ["Bolsa (volva) en la base del pie.", "Láminas blancas a cualquier edad.", "Olor a fenol o carne que amarillea de forma muy viva."],
  [("Oronja verde joven (Amanita phalloides)", "mortal", "Wikipedia dice que «se parece bastante»; la oronja tiene láminas blancas y bolsa en la base."),
   ("Agaricus arvensis", None, "pariente cercano, con el sombrero algo mayor."),
   ("Champiñón amarilleante (Agaricus xanthodermus)", "toxica", "también en la lista de parecidas de Wikipedia.")],
  "Bosques de Europa, América del Norte y Asia; en otoño. Wikipedia dice que es comestible y popular en Europa, y que se sospecha que ha causado reacciones adversas ocasionales en América del Norte.",
  dict(s_color="blanco amarillo", p_anillo="!si", p_base="ensanchada", p_color="blanco amarillo", habitat="conifera planifolio", s_tam="mediano grande"),
  ca=["bola de neu anisada"], ca_f="EC")

F("macrolepiota-excoriata", "Macrolepiota excoriata", "alto",
  ["Sombrero de 6-10 cm, convexo a casi en escudo, con el centro pardo y escamas ocre-amarillentas a pardo claro.",
   "Láminas blancas a crema, esporada blanca, amarilla o crema; carne blanca que no cambia al cortarla, olor suave y sabor a avellana.",
   "Pie blanco a crema, cilíndrico, con base bulbosa y anillo blanquecino; la seta entera mide unos 5-15 cm.",
   "En campos, céspedes y bordes de caminos, de mitad de verano a finales de otoño."],
  ["Pie con bandas o dibujo de «piel de serpiente» (eso es el apagallums grande).", "Seta mucho mayor de 15 cm."],
  [("Apagallums (Macrolepiota procera)", None, "parecida, pero mayor."),
   ("Especies tóxicas parecidas", "toxica", "Wikipedia dice que se parece a numerosas especies tóxicas y que por eso recogerla es problemático.")],
  "Campos y prados de Norteamérica y Europa. Wikipedia dice que es tierna y de sabor agradable cuando es joven.",
  dict(s_color="pardo", s_super="escamas", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_anillo="!si", p_base="ensanchada", p_color="blanco",
       corte="nada", esporada="blanca", habitat="prado", s_tam="mediano"),
  ca=["apagallums"], ca_f="EC")

F("chlorophyllum-rhacodes", "Chlorophyllum rhacodes (Macrolepiota rhacodes)", "alto",
  ["Sombrero de 6-20 cm, de huevo a ancho y aplanado, blanquecino con gruesas escamas pardas y protuberancias.",
   "Láminas blancas y esporada blanca.",
   "Pie de 5-20 cm, de color uniforme, con la base bulbosa; la carne se pone rojiza o granate al cortarla y huele fuerte.",
   "Prefiere la sombra y evita prados y campos abiertos."],
  ["Carne que no enrojece al cortarla.", "Esporada verde (eso es otra especie, Chlorophyllum molybdites)."],
  [("Apagallums (Macrolepiota procera)", None, "mayor, más abundante en zonas abiertas y sin las bandas pardas del pie."),
   ("Chlorophyllum molybdites", "toxica", "de joven es idéntica; se separa por la esporada (blanca aquí, verde en la molybdites).")],
  "Bosques sombríos de Norteamérica, Europa y el sur de África. Wikipedia dice que se alaba como comestible pero que contiene toxinas que pueden causar molestias de estómago; la variante C. brunneum se considera tóxica en algunos países europeos.",
  dict(s_color="blanco pardo", s_super="escamas", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_base="ensanchada", corte="enrojece", esporada="blanca",
       s_tam="grande"),
  ca=["apagallums"], ca_f="EC")

F("calvatia-utriformis", "Calvatia utriformis", "medio",
  ["Cuerpo de 6-12 cm de ancho de joven (hasta unos 25 cm), achatado y en forma de pera, blanco o gris pardusco, cubierto de pelillos finos que se rompen en placas poligonales («mosaico»).",
   "Interior blanco de joven, que pasa a pardo y polvoriento al madurar; la base estéril tiene forma de copa y puede retener agua.",
   "Sin sombrero ni pie: está sujeto al suelo por un cordón.",
   "En pastos arenosos abiertos y brezales, a menudo costeros; de julio a noviembre."],
  ["Interior que no sea blanco y macizo cuando es joven.", "Con láminas dentro (podría ser una amanita joven)."],
  [("Calvatia cyathiformis", None, "tiene el interior púrpura y la superficie lisa.")],
  "Praderas del hemisferio norte templado. Wikipedia dice que solo es comestible cuando el interior es joven y blanco, y que carece de textura y de sabor. Corta siempre por la mitad: el interior ha de ser blanco y macizo, sin láminas.",
  dict(s_color="blanco gris pardo", s_super="escamas", h_tipo="!liso", interior="macizo", habitat="prado", s_tam="grande"),
  ca=["pet de llop gros"], ca_f="EC")

F("calvatia-gigantea", "Calvatia gigantea (Langermannia gigantea)", "alto",
  ["Cuerpo enorme, de 10 a 50 cm de ancho y alto (puede pasar de 80 cm), redondeado, sin sombrero ni láminas ni pie.",
   "De joven el interior es blanco y macizo; al madurar se vuelve verde pardusco y suelta esporas amarillentas con un olor desagradable.",
   "Si se toca o se corta cuando está pasado, se deshace en polvo."],
  ["Interior con láminas, cámaras u otras irregularidades (podría ser una amanita joven).", "Interior gelatinoso (sería un falo).", "Interior firme, elástico y oscuro con vetas blancas (sería una escleroderma)."],
  [("Escleroderma (Scleroderma citrinum)", "toxica", "Wikipedia la da como venenosa; tiene el cuerpo firme y elástico y un interior púrpura negruzco con vetas blancas."),
   ("Amanitas jóvenes", "mortal", "se separan cortando: un bejín tiene el interior blanco y macizo, sin láminas ni formas definidas dentro.")],
  "Prados, campos y bosques de planifolios de zonas templadas, de finales de verano a otoño. Wikipedia dice que es comestible cuando es joven, que puede dar molestias digestivas si ya hay esporas y que a algunas personas les produce efecto laxante.",
  dict(s_color="blanco", h_tipo="!liso", interior="macizo", habitat="prado planifolio", s_tam="grande"),
  ca=["pet de llop gegant"], ca_f="EC")

F("bovista-plumbea", "Bovista plumbea", "bajo",
  ["Bola de 1,5-3,5 cm, esférica o algo aplastada, blanca que pasa a ante y luego a pardo claro, con la capa externa que se desprende en láminas y deja una capa interna gris plomo.",
   "Interior blanco de joven, luego amarillento sucio, pardo oliváceo y por fin pardo oscuro; firme.",
   "Sin sombrero ni pie: se sujeta al suelo con un mechón de micelio."],
  ["Seta con láminas.", "Interior ya pardo y polvoriento (pasada)."],
  [("Bovista dermoxantha inmadura", None, "es fácil de confundir; la fuente consultada no dice cómo separarlas.")],
  "Zonas alteradas con hierba escasa, en Europa occidental y California, durante toda la temporada de setas. Wikipedia dice que las bolas jóvenes pueden partirse y cocinarse, pero que son insípidas y poco sustanciosas.",
  dict(s_color="blanco gris pardo", h_tipo="!liso", interior="macizo", habitat="prado", s_tam="pequeno"),
  ca=["pet de llop gris"], ca_f="EC")


# ============================================================================================================
# GASTEROMICETOS: BEJINES, FALOS, ESTRELLAS DE TIERRA, ESCLERODERMAS
# ============================================================================================================
F("lycoperdon-perlatum", "Lycoperdon perlatum", "medio",
  ["Bola en forma de pera de 3-10 cm de alto y 1,5-6 cm de ancho, blanquecina de joven y parda al madurar, sin sombrero ni láminas.",
   "Superficie cubierta de pequeñas púas o granos que se desprenden y dejan un dibujo en red.",
   "Interior blanco y firme de joven; al madurar pasa a pardo y polvoriento, y se abre por un poro en la parte alta.",
   "Crece en prados, jardines, claros y bosques, suelta, en grupo o en corro."],
  ["Interior que no sea blanco y macizo (pardo, polvoriento o con láminas).", "Superficie lisa, sin púas ni granos."],
  [("Amanitas en estado de «huevo»", "mortal", "Wikipedia avisa de que los jóvenes parecen bejines: corta la seta por la mitad; si se ve la silueta de un sombrero y un pie, no es un bejín."),
   ("Lycoperdon umbrinum y L. pyriforme", None, "L. pyriforme crece en madera podrida y no tiene púas marcadas; L. umbrinum deja las púas sin cicatriz y tiene el interior marrón violáceo.")],
  "Prados, jardines y bosques de casi todo el mundo. Wikipedia la da como comestible solo mientras es joven y el interior es totalmente blanco; si ya es pardo y polvoriento, no. Sus esporas inhaladas pueden irritar mucho el pulmón.",
  dict(s_color="blanco pardo", s_super="escamas", h_tipo="!liso", interior="macizo", habitat="prado planifolio", s_tam="pequeno mediano"),
  )

F("lycoperdon-echinatum", "Lycoperdon echinatum", "medio",
  ["Bola de 2-4 cm de ancho, casi esférica o en pera, cubierta de espinas de hasta 6 mm que a menudo se sueldan por las puntas de tres en tres o de cuatro en cuatro.",
   "Blanca de joven y pardo oscura al madurar; las espinas pueden caer y dejar una superficie con aspecto de red.",
   "Interior blanco y firme de joven, luego amarillento y pardo-violeta y polvoriento; sabor suave.",
   "Suelta o en grupos pequeños, en el suelo de bosques de planifolios (le gusta el hayedo), claros y pastos; de finales de primavera al otoño."],
  ["Interior pardo o polvoriento.", "Superficie lisa sin espinas."],
  [("Amanitas en estado de «huevo»", "mortal", "Wikipedia avisa de que hay que cortar los bejines jóvenes por la mitad para descartar las amanitas mortales."),
   ("Lycoperdon pulcherrimum", None, "espinas más gruesas, no se oscurece con la edad y la superficie bajo las espinas es lisa.")],
  "Bosques de planifolios y pastos de Europa, América del Norte y otras zonas. Wikipedia la da como comestible solo cuando es joven; las viejas, con el interior ya no blanco, pueden sentar mal.",
  dict(s_color="blanco pardo", s_super="escamas", h_tipo="!liso", interior="macizo", habitat="planifolio prado", s_tam="pequeno"),
  )

F("apioperdon-pyriforme", "Apioperdon pyriforme (Lycoperdon pyriforme)", "medio",
  ["Bola en forma de pera de hasta 3 cm de ancho y 6 cm de alto, casi blanca a pardo amarillenta, con espinas blancas pequeñas que suelen caer antes de la madurez.",
   "Base pequeña y estrecha, unida a la madera por cordones blancos gruesos (rizomorfos).",
   "Interior blanco de joven y luego verdoso-amarillento y pardo oliváceo; se abre por un poro en la parte alta.",
   "Crece sobre madera en descomposición, en grupos muy numerosos; de julio a diciembre en Europa."],
  ["Seta que crezca en el suelo, no en madera.", "Interior ya pardo."],
  [("Escleroderma común (Scleroderma citrinum)", "toxica", "Wikipedia la da como venenosa; se rompe en vez de abrirse por un poro y tiene la carne mucho más firme y oscura por dentro desde joven."),
   ("Lycoperdon perlatum", None, "Wikipedia las da como parecidas; esta crece en madera.")],
  "Maderas muertas y troncos podridos de casi todo el mundo. Wikipedia la da como comestible solo mientras es joven y el interior blanco, y la compara con las esclerodermas venenosas.",
  dict(s_color="blanco pardo", h_tipo="!liso", interior="macizo", habitat="madera", grupo="mechon", s_tam="pequeno"),
  )

P("phallus-impudicus", "Phallus impudicus", "nocom",
  ["Seta con forma de falo de 10-30 cm de alto: pie blanco, esponjoso y hueco, con un sombrerillo cónico de 2-4 cm cubierto de una baba verdosa pardusca.",
   "Con el tiempo la baba desaparece y queda un sombrerillo amarillento, con hoyos y crestas.",
   "Olor muy fuerte a carroña, que atrae a las moscas.",
   "Sale de un «huevo» blanquecino de 4-6 cm con una volva gruesa; crece sobre madera podrida de bosques de planifolios y a veces de coníferas, de verano a finales de otoño."],
  "Wikipedia dice que el sombrerillo maduro se ha confundido con una colmenilla (la colmenilla es hueca y no tiene baba ni olor a carroña) y que Phallus hadriani es casi igual pero con la volva de tinte violáceo. Wikipedia también dice que «no suele ser venenoso» y que el «huevo» joven se toma cocinado en algunos lugares de Europa; esta guía no lo recomienda.",
  dict(s_color="verde pardo amarillo", s_forma="conico alveolado", h_tipo="!liso", p_anillo="no", p_base="!bolsa", p_color="blanco", habitat="planifolio conifera madera", s_tam="pequeno"))

F("mutinus-caninus", "Mutinus caninus", "bajo",
  ["Seta fina con forma de dedo, de 10-12 cm de alto, que sale de un «huevo» blanquecino de 2-4 cm.",
   "Columna de 1 cm de grosor, frágil, con hoyitos y casi siempre curvada; amarillo blanquecino a amarillo o naranja pálido, con la punta oscura (olivácea).",
   "Olor a heces de gato, más débil que el del falo común.",
   "En grupos pequeños, sobre hojarasca o restos de madera de bosques de planifolios o coníferas; de verano a finales de otoño."],
  ["Seta con sombrero.", "Punta rojiza o columna rosada (sería Mutinus ravenelii)."],
  [("Mutinus ravenelii", None, "más rosada y con la punta roja."),
   ("Mutinus elegans", None, "corta y robusta, con el ápice más puntiagudo.")],
  "Bosques de Eurasia y de América del Norte oriental. Wikipedia dice que no se considera comestible, aunque hay quien toma los «huevos» jóvenes; no se recomienda.",
  dict(s_color="amarillo naranja blanco", h_tipo="!liso", p_base="!bolsa", p_color="amarillo naranja blanco", habitat="planifolio conifera madera", s_tam="pequeno"),
  )

F("astraeus-hygrometricus", "Astraeus hygrometricus", "bajo",
  ["Estrella de tierra de 1-8 cm de ancho abierta: la capa externa se divide en 4-20 rayos gruesos, gris oscuro a negros y agrietados en la cara de arriba.",
   "Dentro queda una bola sin pie de 1-3 cm, gris claro a tostada, que se abre por un orificio en la parte alta.",
   "Interior blanco y macizo de joven, que pasa a pardo y polvoriento al madurar.",
   "Crece junto a robles y pinos en suelos arenosos pobres y sobre rocas ácidas como pizarra o granito; en otoño."],
  ["Seta con sombrero y pie.", "Rayos que no se abren con la humedad."],
  [("Estrellas de tierra del género Geastrum", None, "Wikipedia dice que de viejas son difíciles de separar en el campo; los Geastrum jóvenes no tienen columela y se abren por una sola rendija.")],
  "Suelos pobres con encinas y pinos. Wikipedia dice que las guías norteamericanas la dan como no comestible y que en algunos países de Asia se consume, pero esta guía no tiene datos que lo avalen.",
  dict(s_color="gris pardo", h_tipo="!liso", interior="macizo", habitat="conifera planifolio", s_tam="pequeno mediano"),
  )

F("geastrum-fimbriatum", "Geastrum fimbriatum", "bajo",
  ["Estrella de tierra de hasta unos 3 cm de ancho abierta, con 5-8 rayos curvados hacia abajo.",
   "Capa externa algodonosa con partículas de tierra, que luego se desprende y deja una superficie lisa gris pardusca.",
   "Bola central sin pie, con un poro cónico de bordes deshilachados; interior pardo amarillento.",
   "En el suelo, en grupos, cerca de tocones de planifolios."],
  ["Seta con sombrero y pie.", "Bola con un anillo bien marcado alrededor del poro (sería G. saccatum)."],
  [("Geastrum saccatum", None, "más grande, hasta 5 cm, con un anillo bien marcado alrededor del poro."),
   ("Geastrum rufescens", None, "tiene tonos rojizos que esta no tiene.")],
  "Europa, Asia, América del Norte y Sur. Wikipedia la da como no comestible.",
  dict(s_color="gris pardo", h_tipo="!liso", habitat="planifolio madera", grupo="mechon", s_tam="pequeno"),
  )

F("geastrum-triplex", "Geastrum triplex", "bajo",
  ["Estrella de tierra grande, de hasta 8-10 cm abierta, con 4-8 rayos de 2-4 cm y una capa interior que forma un platillo bajo la bola.",
   "Bola central de 1-3 cm de ancho, gris pardusca, sin pie, con un orificio puntiagudo de borde irregular rodeado de una zona más pálida.",
   "Interior blanco y firme de joven, y pardo y polvoriento de viejo.",
   "En hojarasca y madera podrida de bosques de planifolios, a menudo bajo hayas; los ejemplares secos duran todo el invierno."],
  ["Seta con sombrero y pie.", "Rayos que se abren y cierran con la humedad."],
  [("Geastrum saccatum y G. fimbriatum", None, "Wikipedia dice que esta es más grande que las dos.")],
  "Casi todo el mundo, en bosques ricos en humus. Wikipedia dice que no es venenosa pero que es dura y fibrosa y sin interés como alimento.",
  dict(s_color="pardo gris", h_tipo="!liso", interior="macizo", habitat="planifolio madera", s_tam="mediano"),
  )

F("pisolithus-arhizus", "Pisolithus arhizus (P. tinctorius)", "bajo",
  ["Cuerpo grande de 5-30 cm de alto y 4-20 cm de ancho, con una capa externa fina amarillo pardusca a parda.",
   "Sin sombrero ni láminas: dentro tiene una masa negra y viscosa que forma las esporas.",
   "Esporas pardas."],
  ["Seta con láminas o poros.", "Interior blanco y macizo (sería un bejín)."],
  [("Dictyocephalos attenuatus", None, "Wikipedia dice que es parecida pero no da cómo separarlas.")],
  "Muy extendida por el mundo. Wikipedia la da como no comestible.",
  dict(s_color="pardo amarillo", h_tipo="!liso", s_tam="grande"),
  )

P("scleroderma-citrinum", "Scleroderma citrinum", "toxica",
  ["Bola sin pie de hasta 10 cm de ancho y 6 de alto, amarillo ocre, con una piel gruesa y firme cubierta de verrugas irregulares.",
   "Se sujeta al suelo con cordones de micelio; el interior es oscuro desde joven y la carne mucho más firme que la de un bejín.",
   "Al madurar la piel se rompe y deja salir las esporas; no se abre por un solo poro.",
   "Bosques, brezales y césped corto, de otoño a invierno; es la esclerodermia más común del Reino Unido."],
  "Con los bejines (Apioperdon pyriforme, Lycoperdon): Wikipedia avisa de que se confunde con ellos; los bejines tienen el interior blanco de joven y se abren por un poro arriba. Wikipedia añade que los aficionados poco expertos pueden confundirla con trufas. Wikipedia la da como venenosa: puede causar molestias de estómago a personas y animales, y las esporas irritan ojos y nariz a algunas personas.",
  dict(s_color="amarillo pardo", s_super="escamas", h_tipo="!liso", interior="macizo", habitat="conifera planifolio prado"))

P("scleroderma-verrucosum", "Scleroderma verrucosum", "nocom",
  ["Bola de 2-7 cm de ancho, algo aplastada por arriba y con una base gruesa a modo de pie, color ocre o pardo sucio.",
   "Superficie con verrugas escamosas que acaban cayendo y la dejan casi lisa; la piel fina se tiñe de rosa a rojo al cortarla.",
   "Interior blanco de joven, luego pardo claro y polvoriento.",
   "En suelos arenosos ricos, a menudo en bosques de planifolios."],
  "Con la esclerodermia común (Scleroderma citrinum), que es más amarilla y tiene el interior oscuro desde joven. Wikipedia dice que esta parece causar en algunas personas síntomas parecidos a los de S. citrinum, por lo que «no se puede recomendar su consumo».",
  dict(s_color="pardo amarillo", s_super="escamas", h_tipo="!liso", interior="macizo", corte="enrojece", habitat="planifolio", s_tam="pequeno mediano"))

P("clathrus-ruber", "Clathrus ruber", "nocom",
  ["Cuerpo en forma de jaula o celosía hueca, rojo a naranja pálido, de 5-20 cm de alto, con 7-20 ventanas angulares y unos 80-120 huecos pequeños.",
   "Sale de un «huevo» blanquecino a grisáceo de hasta 6 cm; al abrirse queda una copa (volva) en la base.",
   "El interior de la celosía está cubierto de una masa viscosa verde oliva a parda, de olor fétido a carne podrida.",
   "Sobre restos de madera y hojarasca, en jardines y céspedes y en mantillo de corteza; de octubre a marzo en América del Norte."],
  "Con Clathrus crispus, que tiene unos bordes rugosos alrededor de cada hueco de la red. Wikipedia dice que su comestibilidad no está documentada, que las guías británicas la dan como no comestible o venenosa y que en 1854 se describió una intoxicación; la Enciclopèdia Catalana la pone «a refusar».",
  dict(s_color="rojo naranja", s_forma="alveolado", h_tipo="!liso", p_anillo="no", p_base="!bolsa", habitat="madera prado", s_tam="mediano"),
  ca=["cranc", "gita de bruixa"], ca_f="EC")



# ============================================================================================================
# TRICOLOMAS Y CLITOCIBES
# ============================================================================================================
P("tricholoma-saponaceum", "Tricholoma saponaceum", "toxica",
  ["Sombrero de unos 4-15 cm, convexo con un mamelón poco marcado que se aplana con la edad; color muy variable: grisáceo, verdoso, oliváceo, amarillento o pardusco.",
   "Láminas blancas, a veces con tinte verde pálido, separadas entre sí y que se ponen rosadas al tocarlas; esporada blanca.",
   "Pie de 4-12 cm, blanquecino, sin anillo, a veces hinchado hacia la mitad; la carne puede teñirse de rosa anaranjado, a veces ya en la base del pie.",
   "Olor característico a jabón o a suelo recién fregado; sabor suave. En bosques de coníferas y de planifolios (robles), de finales de verano a finales de otoño."],
  "Con algunos higróforos (por las láminas) y con Tricholoma griseoviolaceum, que Wikipedia cita como parecido sin decir cómo separarlos. Wikipedia dice que las guías suelen darla como no comestible o venenosa y que contiene toxinas que pueden causar molestias fuertes de estómago.",
  dict(s_color="gris verde amarillo pardo", s_forma="convexo", h_tipo="!laminas", h_color="blanco verde", p_anillo="!no", p_color="blanco", corte="nada enrojece", esporada="blanca",
       habitat="conifera planifolio", s_tam="mediano grande"))

F("tricholoma-album", "Tricholoma album", "medio",
  ["Sombrero de 3-7,5 cm, blanco con un tinte amarillo pálido que se vuelve amarillo u ocre en el centro con la edad; convexo con un mamelón suave y el borde enrollado.",
   "Láminas blancas, gruesas, separadas y de filo finamente aserrado; esporada blanca.",
   "Pie de 3-8,5 cm, blanco a amarillento u ocre pálido, sin anillo ni volva.",
   "Olor dulzón desagradable que recuerda a miel y rábano; sabor acre y desagradable."],
  ["Anillo en el pie.", "Bolsa (volva) en la base del pie.", "Sombrero sin tinte amarillento o con láminas que no sean blancas."],
  [("Otras setas blancas de láminas blancas", "mortal", "esta guía avisa de que las setas blancas con láminas blancas incluyen especies mortales (ver la ficha de las amanitas blancas); el olor y el sabor desagradables de esta no bastan para separarlas con seguridad.")],
  "Bosques de robles de toda Europa, de agosto a diciembre; puede formar corros grandes. La fuente consultada no dice nada sobre su comestibilidad, y su sabor acre y desagradable la hace poco apetecible.",
  dict(s_color="blanco amarillo", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_anillo="!no", p_base="normal", p_color="blanco amarillo", esporada="blanca", habitat="planifolio", grupo="corro", s_tam="pequeno mediano"))

P("tricholoma-virgatum", "Tricholoma virgatum", "nocom",
  ["Sombrero de hasta unos 10 cm, grisáceo y cónico, con fibras radiales; esporada blanca.",
   "Pie de hasta unos 15 cm, más claro que el sombrero.",
   "Olor suave a harina y sabor acre.",
   "En bosques de planifolios y de coníferas de Europa, Asia y América del Norte."],
  "Con Tricholoma sciodes, otra del mismo género que Wikipedia cita como parecida sin dar cómo separarlas. Wikipedia dice que se considera no comestible y posiblemente venenosa.",
  dict(s_color="gris", s_super="fibrosa", s_forma="conico", h_tipo="!laminas", esporada="blanca", habitat="conifera planifolio", s_tam="mediano"))

P("tricholoma-ustale", "Tricholoma ustale", "toxica",
  ["Sombrero de 3-10 cm, rojo anaranjado pardo, de campana a cónico o convexo, con el borde enrollado de joven y luego ondulado.",
   "Láminas algo apretadas, crema a amarillo pálido de joven y pardas con manchas pardas con la edad; pie de 3-9 cm, cilíndrico, algo más grueso en la base.",
   "Carne blanca que se pone parda donde se daña.",
   "Bajo hayas, en Europa, Asia y América del Norte."],
  "Con Tricholoma ezcarayense (descrita de España, también bajo haya), que es más delgada, tiene pequeñas escamas planas y tintes verdosos en el sombrero. Wikipedia dice que es una de las tres especies que más intoxicaciones causan en Japón: provoca vómitos y diarrea fuertes (ácido ustálico). Se desconoce la toxicidad de las poblaciones norteamericanas.",
  dict(s_color="naranja rojo pardo", s_forma="conico convexo", h_tipo="!laminas", h_color="blanco amarillo pardo", habitat="planifolio", s_tam="pequeno mediano"))

P("tricholoma-sejunctum", "Tricholoma sejunctum", "nocom",
  ["Sombrero de 3-8 cm, verdoso amarillento pardusco, algo húmedo, con fibrillas oscuras hacia el centro.",
   "Láminas y pie de 10 cm o menos, blanco amarillentos.",
   "Olor entre suave y a harina; sabor entre suave y desagradable.",
   "En bosques de pino de buena parte del hemisferio norte."],
  "Con la canario (Tricholoma flavovirens, el «seta de los caballeros»), que es mayor, más carnosa, con las láminas y el pie de un amarillo más uniforme y el sombrero menos fibroso. Wikipedia dice que se considera poco segura para comer y que algunas guías la dan por no comestible; la identifica como causa de intoxicaciones en Europa (dato sin referencia).",
  dict(s_color="verde amarillo pardo", s_super="fibrosa", h_tipo="!laminas", h_color="blanco amarillo", p_color="blanco amarillo", habitat="conifera", s_tam="pequeno mediano"))

F("tricholoma-atrosquamosum", "Tricholoma atrosquamosum", "alto",
  ["Sombrero de 4-10 cm, gris pardo oscuro, cónico de joven y luego convexo a plano, cubierto de escamas oscuras.",
   "Láminas gris pardo pálido, pegadas o libres; esporada blanca.",
   "Pie de 2,5-8 cm, gris, con diminutas escamas negruzcas y sin anillo; la base puede tener un tono verdoso o rosado.",
   "Olor a harina con un matiz afrutado o picante; sabor a harina. Suelta o en pequeños grupos en bosques de planifolios (haya) y de coníferas (abeto rojo), sobre suelos calizos."],
  ["Seta más grande y sin el olor picante (podría ser Tricholoma pardinum).", "Anillo en el pie."],
  [("Tricholoma pardinum", "toxica", "Wikipedia la cita como la venenosa con la que se confunde: suele ser más grande y no tiene el aroma picante.")],
  "Europa y América del Norte; rara en Europa y en peligro en los Países Bajos. Wikipedia la da como comestible y apreciada por algunos, pero su parecido con Tricholoma pardinum la hace una de las setas a revisar con más cuidado.",
  dict(s_color="gris pardo negro", s_super="escamas", s_forma="conico convexo", h_tipo="!laminas", h_color="gris pardo", p_anillo="!no", p_color="gris", esporada="blanca", olor="harina", habitat="planifolio conifera", s_tam="mediano"))

F("tricholoma-caligatum", "Tricholoma caligatum", "medio",
  ["Sombrero de 12-15 cm, hemisférico de joven y luego convexo a plano, castaño a pardo oscuro, con grandes escamas fibrosas o placas; borde enrollado con restos algodonosos del velo.",
   "Láminas apretadas, blanquecinas a crema con manchas pardo rojizas con la edad; esporada blanca.",
   "Pie de 4-12 cm, que se estrecha hacia abajo y echa raíz en la base, con un anillo bien formado y algodonoso que cubre las láminas de joven; debajo del anillo, bandas oscuras de escamas.",
   "Olor fuerte, especiado, que recuerda a la nuez moscada o a la pimienta de Jamaica. En bosques costeros y de altura con pinos, encinas y madroños; otoño e invierno."],
  ["Pie sin anillo.", "Olor a harina o a jabón.", "Sombrero liso y sin escamas."],
  [("Tricholoma magnivelare y T. murrilianum", None, "especies norteamericanas parecidas: la segunda no tiene escamas pardas."),
   ("Squamanita umbonata", None, "rara; tiene el sombrero pequeño y puntiagudo.")],
  "Especie del sur de Europa, común en bosques mediterráneos; los datos de América del Norte pueden referirse a otra especie. Wikipedia dice que se considera comestible, que a menudo es amarga (sobre todo bajo planifolios) y añade que es muy apreciada en Chipre.",
  dict(s_color="pardo", s_super="escamas", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_anillo="!si", esporada="blanca", habitat="conifera planifolio", s_tam="grande"))

F("tricholoma-aurantium", "Tricholoma aurantium", "bajo",
  ["Sombrero de 3-10 cm, naranja a rojo anaranjado apagado, de convexo a casi plano, liso de joven y con fibrillas y escamas luego; viscoso en fresco, y se oscurece a rojo al tocarlo.",
   "Láminas apretadas, blanquecinas con manchas pardo rojizas con la edad; esporada blanca.",
   "Pie de 4-8 cm, a menudo hueco, cubierto de escamas anaranjadas densas que acaban en una línea cerca del extremo superior, que es blanco.",
   "Carne blanca que no cambia al cortarla; olor desagradable a harina. En el suelo bajo coníferas (abetos, pinos), disperso o en grupos."],
  ["Pie liso, sin escamas anaranjadas.", "Carne que cambie de color al cortarla."],
  [("Otras setas de color naranja con láminas blancas", None, "la fuente consultada no cita ninguna parecida concreta.")],
  "Norteamérica, India y Pakistán, y la cita europea es de Italia (con abeto blanco). Wikipedia dice que no es comestible por lo desagradable de su sabor.",
  dict(s_color="naranja rojo", s_super="viscosa escamas", s_forma="convexo", h_tipo="!laminas", h_color="blanco", esporada="blanca", olor="harina", habitat="conifera", s_tam="pequeno mediano", p_color="naranja blanco"))

P("clitocybe-nebularis", "Clitocybe nebularis (Lepista nebularis)", "toxica",
  ["Sombrero grande, de 5-25 cm, convexo con el borde enrollado y luego plano o hundido, gris a pardo grisáceo claro, a menudo con un velo blanquecino de joven.",
   "Láminas pálidas, apretadas, a menudo bifurcadas, pegadas o algo decurrentes; esporada amarillenta clara.",
   "Pie de 5-10 cm, grueso, ensanchado hacia la base, hueco de viejo y fácil de romper, algo más claro que el sombrero.",
   "Carne blanca y muy gruesa, de olor fuerte y desagradable (algo a harina, picante o rancio). En bosques de coníferas y de planifolios; a menudo en corros; otoño."],
  "Con Entoloma sinuatum (venenosa, con láminas rosas y escotadas), Clitocybe robusta (sombrero blanco más macizo), Clitocybe irina (esporada rosada), Leucopaxillus giganteus (más blanca) e Infundibulicybe geotropa (sombrero pardo claro). Wikipedia la da como comestible pero advierte de que incluso una porción pequeña puede causar molestias digestivas a algunas personas, por lo que esta guía la trata como seta a evitar.",
  dict(s_color="gris pardo", s_super="lisa", s_forma="convexo embudo", h_tipo="!laminas", h_color="blanco amarillo", p_anillo="!no", p_base="ensanchada", interior="hueco", esporada="blanca", habitat="conifera planifolio", grupo="corro", s_tam="grande"))

F("clitocybe-odora", "Clitocybe odora", "alto",
  ["Sombrero de 3-8 cm, azul claro de joven que pasa a gris con la edad y azul verdoso en los ejemplares maduros; en forma de campana de joven y de copa después.",
   "Láminas blanco cremosas o azul verdosas, pegadas a algo decurrentes; esporada blanca a ligeramente rosada.",
   "Pie de hasta 6 cm y unos 2 cm de grosor, blanco a ante o del color del sombrero, sin anillo.",
   "Olor y sabor fuertes a anís. En grupos pequeños bajo árboles, junto a raíces o entre restos del suelo, en bosques de planifolios (robles) y de coníferas; de agosto a diciembre."],
  ["Pie con anillo.", "Sin olor a anís.", "Sombrero que no tenga ningún tono azul o verdoso."],
  [("Stropharia aeruginosa y otras setas venenosas", "toxica", "Wikipedia avisa de que los ejemplares jóvenes se parecen a Stropharia aeruginosa y a otras setas venenosas, y no da rasgos para separarlas.")],
  "Zonas templadas de Asia, Europa y América del Norte. Wikipedia dice que algunas guías la dan por comestible pero que otras aconsejan no comerla porque puede confundirse con setas venenosas.",
  dict(s_color="verde gris", s_forma="convexo embudo", h_tipo="!laminas", h_color="blanco verde", p_anillo="!no", esporada="blanca rosa", habitat="conifera planifolio", s_tam="pequeno mediano"))


# ============================================================================================================
# HIGRÓFOROS Y HIGRÓCIBES (MOCOSAS, PIXACANS, LLENEGUES)
# ============================================================================================================
F("hygrophorus-hypothejus", "Hygrophorus hypothejus", "medio",
  ["Sombrero de 3-6 cm, amarillento a pardo oliváceo con el centro oscuro, viscoso; borde enrollado de joven y con forma de embudo con la edad.",
   "Láminas amarillas, decurrentes; esporada blanca.",
   "Pie de 4-7 cm de alto y 0,7-1,4 cm de ancho; carne amarillo pálido que se pone anaranjada-roja al magullarla.",
   "En pinares y otros bosques de coníferas, en grupos grandes y entre las agujas, con las primeras heladas de octubre y noviembre (a veces diciembre)."],
  ["Láminas que se separan con facilidad del sombrero (así son las de Gomphidius glutinosus).", "Esporada que no sea blanca."],
  [("Gomphidius glutinosus", None, "Wikipedia la cita como parecida: en ella las láminas se separan con facilidad del sombrero."),
   ("Hygrophorus speciosus", None, "se cita como parecida sin decir cómo separarlas.")],
  "Nativa de Europa. Wikipedia dice que se considera comestible pero de calidad variable, porque algunos ejemplares son muy viscosos.",
  dict(s_color="amarillo verde pardo", s_super="viscosa", s_forma="convexo embudo", h_tipo="!laminas", h_color="amarillo", corte="enrojece", esporada="blanca", habitat="conifera", grupo="mechon", s_tam="pequeno"))

F("hygrocybe-coccinea", "Hygrocybe coccinea", "bajo",
  ["Sombrero de 2-5 cm, rojo escarlata, viscoso, en campana de joven y plano después.",
   "Láminas pegadas, gruesas y separadas, amarillo rojizas; esporada blanca.",
   "Pie de 2-5 cm de alto y 0,3-1 cm de ancho, rojo con la base amarillenta, sin anillo; carne amarillo rojiza, de olor y sabor débiles.",
   "En prados no abonados (en Europa, de agosto a octubre) y, en América del Norte, en bosques bajo secuoyas en invierno."],
  ["Pie con anillo.", "Láminas blancas puras."],
  [("Hygrocybe marchii e Hygrocybe punicea", "nocom", "Wikipedia las cita como bastante parecidas sin decir cómo separarlas; H. punicea acumula cadmio y no se recomienda.")],
  "Prados viejos y poco intervenidos de Europa; en declive por la pérdida de este hábitat. Wikipedia dice que se considera comestible, incluso cruda, pero de poco interés.",
  dict(s_color="rojo", s_super="viscosa", s_forma="conico convexo", h_tipo="!laminas", h_color="amarillo rojo", p_anillo="no", p_color="rojo amarillo", esporada="blanca", habitat="prado", s_tam="pequeno"))

F("hygrocybe-psittacina", "Gliophorus psittacinus (Hygrocybe psittacina)", "bajo",
  ["Sombrero de hasta 4 cm, convexo a con mamelón, verde de joven y luego amarillento o a veces con tinte rosado; viscoso.",
   "Láminas anchas y pegadas, verdosas con el filo amarillo; esporada blanca.",
   "Pie de 2-8 cm y 3-5 mm de ancho, verde a verde amarillento; el verde persiste en la parte alta del pie incluso en los ejemplares viejos.",
   "Olor y sabor suaves. En prados, de finales de verano a otoño (septiembre a noviembre)."],
  ["Seta sin ningún tono verde, ni en el sombrero ni en el pie.", "Pie con anillo."],
  [("Otros Gliophorus y Bolbitius callistus", None, "Wikipedia los cita como parecidos sin decir cómo separarlos.")],
  "Casi todo el mundo; en descenso en Europa por pérdida de hábitat. Wikipedia dice que se considera comestible pero que no merece la pena por pequeña y viscosa; la Enciclopèdia Catalana la pone «a refusar».",
  dict(s_color="verde amarillo rosa", s_super="viscosa", s_forma="convexo conico", h_tipo="!laminas", h_color="verde amarillo", p_color="amarillo", esporada="blanca", habitat="prado", s_tam="pequeno"),
  ca=["pixacà verd"], ca_f="EC")

F("hygrocybe-chlorophana", "Hygrocybe chlorophana", "bajo",
  ["Sombrero de hasta 7,5 cm, convexo (nunca cónico) y luego aplanado, amarillo limón a amarillo anaranjado, liso y bien viscoso con humedad.",
   "Láminas cerosas, pálidas o del color del sombrero, pegadas de forma estrecha; esporada blanca.",
   "Pie del color del sombrero, liso, cilíndrico o aplastado y con surcos, húmedo a algo viscoso; la seta entera mide hasta unos 10 cm de alto.",
   "En prados viejos y poco intervenidos de Europa y, en Norteamérica y el norte de Asia, en bosques; normalmente en otoño."],
  ["Seta cónica.", "Pie con anillo.", "Esporada que no sea blanca."],
  [("Hygrocybe glutinipes", None, "del mismo color, pero normalmente más pequeña, con el sombrero y el pie gelatinosos y algo translúcidos."),
   ("Hygrocybe ceracea", None, "con el sombrero y el pie cerosos (no viscosos) y las láminas anchamente pegadas, casi decurrentes.")],
  "Hemisferio norte templado. La fuente consultada no dice nada sobre su comestibilidad.",
  dict(s_color="amarillo naranja", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="amarillo", p_color="amarillo naranja", esporada="blanca", habitat="prado", s_tam="pequeno mediano"))

F("cuphophyllus-pratensis", "Cuphophyllus pratensis (Hygrocybe pratensis)", "bajo",
  ["Sombrero de hasta 6 cm, de convexo a plano o algo hundido, liso y seco, color salmón pálido a naranja ante.",
   "Láminas cerosas, pálidas y decurrentes (bajan por el pie); esporada blanca.",
   "Pie de hasta 7 cm, crema, liso, cilíndrico o más fino hacia abajo; carne blanquecina de olor y sabor suaves.",
   "En prados viejos y poco intervenidos de Europa y, en otros lugares, en bosques."],
  ["Láminas que no bajen por el pie.", "Sombrero de color rojo o amarillo vivo."],
  [("Hygrophorus nemoreus", None, "crece en robledales con olor claramente a harina."),
   ("Hygrophorus pudorinus", None, "se cita como parecida sin decir cómo separarlas."),
   ("Cuphophyllus berkeleyi", None, "casi igual pero toda blanca.")],
  "Europa, norte de África, América, norte de Asia, Australia y Nueva Zelanda. Wikipedia la da como comestible y a veces vendida, aunque las setas silvestres deben revisarse con cuidado.",
  dict(s_color="naranja pardo rosa", s_super="lisa", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_color="blanco", esporada="blanca", habitat="prado", s_tam="pequeno mediano"))

F("hygrophorus-eburneus", "Hygrophorus eburneus", "medio",
  ["Sombrero de 2-7 cm, blanco puro, de convexo a plano, liso y pegajoso con humedad; borde enrollado y fibroso de joven.",
   "Láminas blancas (algo amarillentas o ante con la edad), separadas y decurrentes; esporada blanca.",
   "Pie de 4-15 cm, blanco, cubierto de una capa viscosa, algodonoso por dentro de joven y hueco después; carne blanca, blanda, de olor y sabor suaves.",
   "En el suelo de bosques de coníferas sobre todo, en matorrales y zonas de hierba, con preferencia por suelos húmedos y calizos."],
  ["Pie y sombrero secos (no pegajosos).", "Láminas no pegadas al pie (podría ser Limacella).", "Olor agrio (sería Hygrophorus cossus)."],
  [("Hygrophorus cossus", None, "sombrero y láminas beige rosados, olor agrio claro, bajo robles."),
   ("Hygrophorus gliocyclus", None, "igual de viscosa pero con el sombrero crema y el pie más grueso, bajo pinos."),
   ("Limacella illinita", None, "las láminas no están pegadas al pie y no son cerosas."),
   ("Amanitas blancas", "mortal", "esta guía avisa de que cualquier seta blanca con láminas blancas puede ser una amanita mortal: comprueba la base del pie.")],
  "Muy extendida por Norteamérica, y también en Europa y el norte de África. Wikipedia dice que se considera comestible pero poco apetecible por lo viscosa.",
  dict(s_color="blanco", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_color="blanco", esporada="blanca", habitat="conifera", s_tam="pequeno mediano"),
  ca=["llenega blanca"], ca_f="EC")

F("cuphophyllus-virgineus", "Cuphophyllus virgineus (Hygrocybe virginea)", "medio",
  ["Sombrero de hasta 7,5 cm, blanco a marfil (a veces con tintes ocres), de convexo a plano o algo hundido, liso, ceroso con humedad y con el borde estriado.",
   "Láminas cerosas, del color del sombrero y decurrentes; esporada blanca.",
   "Pie de hasta 7 cm, liso, cilíndrico o más fino hacia abajo; carne blanca, de olor suave y sabor de amargo a acre.",
   "En prados viejos y poco intervenidos de Europa y, en otros lugares, en bosques; otoño."],
  ["Láminas no decurrentes.", "Seta de otro color que no sea blanco o marfil."],
  [("Cuphophyllus russocoriaceus", None, "casi igual, pero con un fuerte olor a sándalo."),
   ("Cuphophyllus berkeleyi", None, "algo mayor y sin el sombrero higrófano."),
   ("Amanitas blancas", "mortal", "esta guía avisa de que cualquier seta blanca con láminas blancas puede ser una amanita mortal: comprueba la base del pie.")],
  "Hemisferio norte templado. Wikipedia la da como comestible y buena, pero es pequeña y se parece a otras setas blancas.",
  dict(s_color="blanco", s_super="lisa", s_forma="convexo embudo", h_tipo="!laminas", h_color="blanco", p_color="blanco", esporada="blanca", habitat="prado", s_tam="pequeno mediano"),
  ca=["mocosa blanca petita"], ca_f="EC")

P("hygrocybe-punicea", "Hygrocybe punicea", "nocom",
  ["Sombrero de hasta 15 cm, rojo oscuro o carmesí apagado, de convexo a con mamelón y luego aplanado, graso y pegajoso; en seco se vuelve amarillo pálido a ante en parches.",
   "Láminas cerosas, rojo oscuro a ante con tintes violáceos y el filo amarillento; esporada blanca.",
   "Pie amarillo a rojo anaranjado y blanquecino hacia la base, sin anillo, liso pero fibroso y con vetas.",
   "En prados viejos y poco intervenidos, ampliamente repartida por Europa pero rara."],
  "Con Hygrocybe coccinea (normalmente mucho más pequeña) e Hygrocybe splendidissima (casi tan grande pero con el sombrero seco, el pie sin fibras y olor a miel al frotarla). Wikipedia dice que no se recomienda comerla porque acumula cadmio y que este metal puede causar intoxicación; la Enciclopèdia Catalana la pone «a refusar».",
  dict(s_color="rojo", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="rojo pardo violeta", p_anillo="no", p_color="amarillo naranja rojo", esporada="blanca", habitat="prado", s_tam="mediano grande"),
  ca=["pixadina vermella"], ca_f="EC")

F("hygrophorus-agathosmus", "Hygrophorus agathosmus", "bajo",
  ["Sombrero de 3-10 cm, gris ceniza apagado, de convexo con el borde enrollado a plano o algo hundido, pegajoso con humedad y liso.",
   "Láminas blancas que pasan a grisáceas, pegadas o algo decurrentes con la edad; esporada blanca.",
   "Pie de 4-15 cm, blanquecino y luego gris ceniza pálido, macizo; carne blanda, blanquecina o gris acuosa.",
   "Olor fuerte a hueso de cereza o a almendras amargas. Bajo abetos rojos y pinos y en bosques mixtos."],
  ["Seta sin olor a almendras.", "Sombrero seco, no pegajoso."],
  [("Hygrophorus marzuolus", None, "de aspecto parecido, sin olor distintivo y con esporas menores."),
   ("Hygrophorus odoratus", None, "con el mismo olor, pero más pequeña.")],
  "Estados Unidos, Europa, África e India. Wikipedia dice que se considera comestible pero insípida.",
  dict(s_color="gris", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco gris", p_color="blanco gris", esporada="blanca", olor="almendra", habitat="conifera", s_tam="pequeno mediano"),
  ca=["mocosa perfumada"], ca_f="EC")

F("hygrophorus-olivaceoalbus", "Hygrophorus olivaceoalbus", "bajo",
  ["Sombrero de 3-12 cm, hemisférico de joven y luego más extendido, pardo oliva a gris o pardo hollín, viscoso, con rayas oscuras y un mamelón oscuro.",
   "Láminas gruesas y separadas, blancas, algo grisáceas en la base; esporada blanca.",
   "Pie de 3-12 cm, a menudo ondulado, blanquecino por encima de una zona anular (una vaina viscosa) con bandas oscuras y desgarradas por debajo.",
   "Carne blanca, de olor y sabor suaves. Bajo coníferas, sobre todo en bosques de montaña, con frecuencia entre musgos."],
  ["Pie sin ninguna zona o vaina anular.", "Sombrero seco."],
  [("Hygrophorus persoonii", None, "difiere en la reacción al hidróxido de sodio (verde oliva en lugar de rojiza) y prefiere los robles."),
   ("Hygrophorus inocybiformis", None, "más pequeña, con el sombrero de 3-6 cm y el pie seco.")],
  "Norte y oeste de América del Norte, Europa (menos en la zona mediterránea) y Rusia. Wikipedia dice que se considera comestible, con opiniones divididas sobre su sabor, y que algunos autores aconsejan quitar la cutícula; dice también que «no hay riesgo de confundirla con hongos tóxicos».",
  dict(s_color="pardo gris verde", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_anillo="si", esporada="blanca", habitat="conifera", s_tam="mediano"),
  ca=["llenegall"], ca_f="EC")

P("hygrocybe-conica", "Hygrocybe conica", "nocom",
  ["Sombrero de hasta 10 cm, amarillo a naranja o escarlata, estrechamente cónico de joven y luego con mamelón y a menudo lobulado; liso, algo fibroso y viscoso al principio.",
   "Láminas cerosas, blanquecinas a amarillo pálido o grisáceas; esporada blanca.",
   "Pie de hasta 20 cm, amarillo a rojo anaranjado y blanquecino hacia la base, sin anillo, liso pero fibroso y con vetas.",
   "Carne amarillenta que se pone negra al magullarla. En prados viejos y poco intervenidos, dunas y bordes de caminos; en Norteamérica, a menudo en bosques de coníferas; verano y otoño."],
  "Con Hygrocybe astatogala, que Wikipedia cita como parecida (muchas colecciones australianas son de esta). Wikipedia dice que su comestibilidad se desconoce y que puede ser venenosa; David Arora apunta que las intoxicaciones citadas pudieron deberse a otras especies y que esta quizá solo cause efectos leves como mareo. La Enciclopèdia Catalana la pone «a refusar».",
  dict(s_color="amarillo naranja rojo", s_super="lisa", s_forma="!conico", h_tipo="!laminas", h_color="blanco amarillo gris", p_anillo="no", p_color="amarillo naranja rojo", esporada="blanca", habitat="prado", s_tam="pequeno mediano"),
  ca=["pixaconill"], ca_f="EC")

F("hygrophorus-chrysodon", "Hygrophorus chrysodon", "bajo",
  ["Sombrero de 4-14 cm, blanco, a veces con un tinte amarillo, con granos o pelillos dorados sobre todo cerca del borde.",
   "Láminas subdecurrentes a decurrentes; esporada blanca.",
   "Pie de 3-10 cm, también con granos o pelillos dorados; carne blanda y blanca, de sabor suave a amargo.",
   "Sobre el suelo con musgo, bajo coníferas o planifolios, en todo el hemisferio norte."],
  ["Seta sin granos dorados en el sombrero ni en el pie."],
  [("Hygrophorus discoxanthus", None, "poco común; Wikipedia no dice cómo separarlas."),
   ("Amanitas blancas", "mortal", "esta guía avisa de que cualquier seta blanca con láminas blancas puede ser una amanita mortal: comprueba la base del pie.")],
  "Wikipedia la da como comestible pero insípida; la Enciclopèdia Catalana la pone «a refusar».",
  dict(s_color="blanco amarillo", s_super="escamas", s_forma="convexo", h_tipo="!laminas", p_color="blanco amarillo", esporada="blanca", habitat="conifera planifolio", s_tam="mediano"),
  ca=["mocosa blanca tacada"], ca_f="EC")

F("hygrophorus-pudorinus", "Hygrophorus pudorinus", "bajo",
  ["Sombrero de 5-12 cm, rosado a dorado, convexo con el borde enrollado y más claro, pegajoso.",
   "Láminas de rosadas a blanco amarillentas, decurrentes; esporada blanca.",
   "Pie grueso, de 4-16 cm de alto y 1-3 cm de ancho; carne gruesa, de rosa pálido o naranja a blanca, que no enrojece al cortarla, sin olor claro y con sabor a trementina.",
   "En bosques de coníferas (abetos y piceas), a menudo en sitios encharcados entre musgo de turbera; en grupos o en corros; finales de verano y otoño."],
  ["Carne que enrojece al cortarla.", "Seta sin sabor a trementina."],
  [("Hygrophorus erubescens y H. purpurascens", None, "Wikipedia la agrupa con ellas como muy parecidas y dice que su aspecto variable hace difícil la identificación y arriesgada una confusión.")],
  "Oeste y noreste de América del Norte (sobre todo Canadá y las Rocosas). Wikipedia dice que se considera comestible tras cocinarla a pesar de su sabor; la Enciclopèdia Catalana la pone «a refusar».",
  dict(s_color="rosa naranja amarillo", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="rosa amarillo blanco", corte="nada", esporada="blanca", habitat="conifera", grupo="corro", s_tam="mediano"),
  ca=["mocosa de garric"], ca_f="EC")


# ============================================================================================================
# RÚSULAS
# ============================================================================================================
F("russula-aurea", "Russula aurea", "medio",
  ["Sombrero de 4-9 cm, rojo sangre a rojo anaranjado, convexo y luego plano o hundido, pegajoso con humedad y con el borde estriado; la cutícula se pela hasta la mitad.",
   "Láminas anchas y separadas, ocres con el filo amarillo; esporada ocre.",
   "Pie cilíndrico de 3-8 cm de alto y 1-2,5 cm de ancho, blanco, crema o amarillo dorado; carne amarilla, quebradiza, de sabor suave.",
   "Bajo planifolios, sobre todo hayas, robles y avellanos; verano y principios de otoño."],
  ["Carne blanca en lugar de amarilla.", "Láminas y pie blancos puros (podría ser Russula emetica).", "Sabor picante."],
  [("Russula sanguinaria, Russula emetica y Russula nobilis", "toxica", "Wikipedia dice que son rúsulas rojas de sabor picante y no comestibles; lo que separa a esta es el tono amarillo del conjunto (láminas ocres, pie y carne amarillos).")],
  "Europa, escasa en Gran Bretaña; llega hasta el mar Negro. Wikipedia dice que, a diferencia de muchas otras rúsulas de sombrero rojo, esta es de sabor suave.",
  dict(s_color="rojo naranja", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="amarillo pardo", p_color="blanco amarillo", habitat="planifolio", s_tam="pequeno mediano"),
  ca=["cualbra retgera"], ca_f="EC")

F("russula-virescens", "Russula virescens", "alto",
  ["Sombrero de hasta unos 15 cm, verde pálido con manchas verdes más oscuras (gris, verde cardenillo o verde hierba), de abombado a plano, a menudo hundido en el centro; la cutícula se rompe en placas («cuarteado»).",
   "Láminas blancas a crema, apretadas y casi libres, con venas entre sus bases; esporada blanca a amarillo pálido.",
   "Pie blanco de hasta 8 cm de alto y 4 de grosor, cilíndrico, a veces con polvo harinoso en lo alto; carne de sabor suave, algo a nuez o a fruta.",
   "En el suelo de bosques de planifolios y mixtos (robles, hayas), suelta o dispersa; verano y principios de otoño."],
  ["Anillo o volva (bolsa) en el pie.", "Sombrero liso y sin cuarteado.", "Sabor picante o desagradable."],
  [("Oronja verde (Amanita phalloides)", "mortal", "Wikipedia insiste en la «cautela vital» para no confundirlas: la oronja tiene anillo y volva (bolsa) en la base; la rúsula no tiene ninguno."),
   ("Russula aeruginea, R. heterophylla, R. cyanoxantha var. peltereaui", None, "rúsulas verdes de sombrero liso."),
   ("Russula crustosa", None, "el sombrero se vuelve pegajoso con humedad, más variable de color y esporada más amarilla."),
   ("Russula redolens", None, "sombrero liso, sabor desagradable y olor a perejil.")],
  "Eurasia y norte de África. Wikipedia la da como una de las mejores comestibles de su género, pero el parecido con la oronja verde obliga a comprobar siempre la base del pie.",
  dict(s_color="verde gris", s_super="escamas", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_anillo="!no", p_base="normal", p_color="blanco", esporada="blanca", habitat="planifolio", s_tam="grande"),
  ca=["llora verda"], ca_f="EC")

F("russula-delica", "Russula delica", "medio",
  ["Sombrero de hasta unos 16 cm, blanco (casi siempre con tinte ocre o pardo), convexo y luego aplanado y en forma de embudo; superficie rugosa que retiene hojas y tierra, borde enrollado y casi siempre blanco.",
   "Láminas decurrentes (bajan por el pie), bastante apretadas de joven; esporada blanco cremosa.",
   "Pie corto y grueso, de 2-6 cm de alto y 2-4 cm de ancho, blanco y firme; carne blanca que no cambia al cortarla.",
   "Olor agradable y afrutado de joven que puede volverse algo a pescado de viejo; sabor picante. En bosques de coníferas, planifolios o mixtos, a menudo medio enterrada; verano y otoño con calor."],
  ["Banda azul turquesa en la unión del sombrero con las láminas (sería Russula chloroides).", "Leche (látex) al cortar las láminas o la carne.", "Sombrero de colores vivos."],
  [("Russula chloroides", None, "se separa por la banda turquesa donde el sombrero se une a las láminas y por su olor desagradable y picante."),
   ("Lactarius piperatus y otros lactarios blancos", None, "sueltan leche por las láminas y la carne cortada."),
   ("Russula pallidospora y R. flavispora", None, "la primera tiene carne muy dura y esporada ocre; la segunda, rara, tiene láminas densas y esporada ocre intensa.")],
  "Zonas templadas del hemisferio norte, sobre todo mediterráneo oriental; rara en América del Norte. Wikipedia la da como comestible pero de gusto pobre, tanto que algunos la consideran no comestible; la Enciclopèdia Catalana la valora «bo» con el nombre «pebràs».",
  dict(s_color="blanco pardo", s_forma="embudo", h_tipo="!laminas", h_color="blanco", p_color="blanco", corte="nada", esporada="blanca", habitat="conifera planifolio", s_tam="grande"),
  ca=["pebràs"], ca_f="EC")

F("russula-olivacea", "Russula olivacea", "medio",
  ["Sombrero grande, de 10-30 cm, amarillo oliváceo de joven que pasa a pardo oxidado; convexo y pronto plano.",
   "Láminas crema que se vuelven ocre profundo al envejecer, algo apretadas y quebradizas; esporas amarillas.",
   "Pie de 7-18 cm de alto y 2-6 cm de ancho, fuerte y de grosor uniforme, a menudo rosa pálido; carne firme y blanca, de olor agradable o neutro y sabor suave o a nuez.",
   "En grupos desde junio, en bosques de planifolios y de coníferas, sobre todo bajo piceas y hayas; no es rara."],
  ["Sombrero de color púrpura a rojo sangre brillante y carne picante (sería Russula viscida)."],
  [("Russula viscida", None, "muy parecida en tamaño y hábitat, con el sombrero púrpura a rojo sangre y brillante, la base que se vuelve amarillo cuero con la edad y la carne bastante picante.")],
  "Wikipedia empieza diciendo que es «comestible y no venenosa», pero añade que algunas fuentes la dan por tóxica, con posibles molestias de estómago. La Enciclopèdia Catalana la valora «bo» con el nombre «cuagra vinosa».",
  dict(s_color="amarillo verde pardo", s_forma="convexo", h_tipo="!laminas", h_color="blanco amarillo pardo", p_color="blanco", habitat="conifera planifolio", grupo="mechon", s_tam="grande"),
  ca=["cuagra vinosa"], ca_f="EC")

F("russula-xerampelina", "Russula xerampelina", "medio",
  ["Sombrero de 5-20 cm, de color muy variable (sobre todo púrpura a rojo vino o verdoso, más oscuro en el centro), pegajoso, de abombado a plano o algo hundido, con finos surcos de hasta 1 cm hacia el borde.",
   "Láminas muy juntas que pasan a amarillo crema con la edad; esporada crema amarillenta a ocre.",
   "Pie cilíndrico de 4-12 cm de alto y 1,5-4 cm de ancho, blanco, a veces con un tinte rojizo, que se pone pardo al magullarlo.",
   "Olor a marisco o a cangrejo cocido, más fuerte con la edad; sabor suave. Bajo coníferas (prefiere el abeto de Douglas), a veces bajo hayas y robles; otoño."],
  ["Sin olor a marisco.", "Láminas y pie blancos puros con sombrero rojo (sería Russula emetica)."],
  [("Russula emetica", "toxica", "tiene el sombrero rojizo y el pie y las láminas siempre blancos."),
   ("Russula aeruginea y R. graveolens", None, "la primera es más verdosa; R. graveolens se parece pero la mayoría de las parecidas no tienen el olor a marisco."),
   ("Russula olivacea", None, "con el sombrero más aterciopelado.")],
  "Zonas templadas del hemisferio norte, de Europa a Costa Rica. Wikipedia la da como una de las rúsulas más apreciadas en la mesa; el olor a marisco persiste al cocinarla y es menos agradable en las viejas.",
  dict(s_color="violeta rojo verde", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco amarillo", p_color="blanco rojo", habitat="conifera", s_tam="mediano grande"),
  ca=["cuagra roja"], ca_f="EC")

P("russula-adusta", "Russula adusta (R. nigricans)", "toxica",
  ["Sombrero de 5-20 cm, blanco sucio de joven, luego pardo y por fin negro; algo brillante, con el centro hundido en los maduros; la cutícula se pela hasta tres cuartos.",
   "Láminas blanquecinas de joven, muy separadas y pegadas; al tocarlas pasan a rojas, luego a grises y por fin a negras.",
   "Pie de 5-8 cm de alto y 2-5 cm de ancho, blanco, firme y recto, que se ennegrece con la edad.",
   "La carne cortada pasa a rojo pálido, luego a gris y a negro en unos 20 minutos; olor afrutado. En bosques de coníferas y de planifolios, a finales de verano y otoño."],
  "Con Russula albonigra (láminas más juntas, mucho menos común; ennegrece directamente sin pasar por rojo) y con R. acrifolia y R. dissimulans (también enrojecen y luego ennegrecen). Wikipedia dice que contiene toxinas que podrían causar molestias de estómago; se usa en encurtidos; esta guía no te la recomienda.",
  dict(s_color="blanco pardo gris negro", s_super="lisa", s_forma="embudo", h_tipo="!laminas", h_color="blanco gris", p_color="blanco gris negro", corte="enrojece", esporada="blanca", habitat="conifera planifolio", s_tam="grande"))

P("russula-foetens", "Russula foetens", "nocom",
  ["Sombrero de hasta unos 10 cm, amarillo miel a pardo ocre, abombado al principio y muy viscoso (baboso) de joven.",
   "Láminas crema pálido.",
   "Pie fuerte, blanco o con manchas pardo amarillentas.",
   "Olor fuerte y acre de joven; de viejo, olor a pescado y mal sabor."],
  "Wikipedia dice que se considera no comestible, aunque en Rusia se usa en encurtidos; esta guía no te la recomienda. La Enciclopèdia Catalana la pone «a refusar».",
  dict(s_color="amarillo pardo", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco amarillo", p_color="blanco amarillo pardo", s_tam="mediano grande"),
  ca=["cualbra pudent"], ca_f="EC")

P("russula-fragilis", "Russula fragilis", "toxica",
  ["Sombrero pequeño de 2-5 cm, de color muy variable (púrpura oscuro con el centro casi negro, verde oliva, rosa violáceo o amarillo pálido; se descolora muy rápido), convexo y luego aplanado, con el borde acanalado en los viejos.",
   "Láminas blancas, algo pegadas, con muescas en el filo visibles con lupa; esporada blanca.",
   "Pie blanco, largo para el tamaño del sombrero, en forma de maza estrecha y frágil; carne blanca, de olor afrutado y sabor muy picante.",
   "En bosques mixtos y de planifolios (abedules, robles), a menudo sobre o cerca de madera podrida, en grupos pequeños; finales de verano y otoño."],
  "Con Russula betularum (suele estar bajo abedules, más pálida; se puede tomar por una R. fragilis descolorida) y R. gracillima (parecida y en los mismos sitios). Wikipedia dice que es no comestible por las toxinas que contiene y por su sabor muy picante, y que muchas rúsulas picantes causan diarrea y vómitos. La Enciclopèdia Catalana la pone «a refusar».",
  dict(s_color="violeta verde rosa amarillo", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_color="blanco", esporada="blanca", habitat="planifolio madera", s_tam="pequeno"),
  ca=["escaldabec fràgil"], ca_f="EC")

P("russula-sanguinea", "Russula sanguinea", "toxica",
  ["Sombrero de hasta 10 cm, rojo sangre vivo o rosado de joven, con zonas más pálidas, convexo y luego plano o en forma de platillo; la cutícula se pela solo en el borde.",
   "Láminas estrechas y bifurcadas, de crema a ocre pálido, pegadas o algo decurrentes; esporada crema a ocre pálido.",
   "Pie robusto con vetas verticales, normalmente del color del sombrero y a veces blanco; carne blanca, de sabor algo picante y a veces amargo.",
   "Micorriza con pinos y otras coníferas, en suelos arenosos; verano y otoño."],
  "Con Russula helodes (idéntica a simple vista, entre esfagnos y mucho más rara) y Russula emetica (mismo hábitat, sombrero rojo vivo, casi nunca con el pie coloreado y muy quebradiza). Wikipedia dice que es no comestible: las rúsulas de sabor parecido son venenosas crudas, con síntomas sobre todo digestivos. La Enciclopèdia Catalana la pone «a refusar».",
  dict(s_color="rojo rosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco amarillo", p_color="rojo blanco", habitat="conifera", s_tam="mediano"),
  ca=["escaldabec de pineda"], ca_f="EC")

F("russula-integra", "Russula integra", "medio",
  ["Sombrero de 6-12 cm, normalmente pardo con tintes violeta, púrpura, amarillo o verde; casi esférico al principio y luego aplanado o hundido, brillante.",
   "Láminas gruesas, separadas y quebradizas: blancas al principio y por fin amarillo vivo; esporada amarillo ocre.",
   "Pie de 5-12 cm de alto y 2-3 cm de grosor, blanco, que mancha de amarillo o rojizo con la edad.",
   "Carne blanca, muy firme y crujiente, de sabor suave o a nuez. Dispersa bajo coníferas, sobre todo en bosques de abeto y picea de montaña."],
  ["Sabor picante.", "Sombrero de colores rojos o rosados vivos."],
  [("Russula mustelina", None, "parecida, con sombrero pardo, pie blanco, esporas amarillas y carne firme."),
   ("Rúsulas parecidas de comestibilidad desconocida", None, "David Arora, citado por Wikipedia, avisa de que las parecidas tienen una comestibilidad desconocida.")],
  "Europa y toda América del Norte. Wikipedia dice que se considera comestible bien cocinada y que es popular en partes de Europa, pero también que las intoxicaciones fueron frecuentes en el pasado; esta guía no te la recomienda sin identificación experta.",
  dict(s_color="pardo violeta amarillo verde", s_super="lisa", s_forma="convexo embudo", h_tipo="!laminas", h_color="blanco amarillo", p_color="blanco amarillo", habitat="conifera", s_tam="mediano"))

P("russula-albonigra", "Russula albonigra", "nocom",
  ["Sombrero de hasta 20 cm, convexo a en forma de embudo, blanquecino y luego negro; a veces viscoso.",
   "Láminas decurrentes (bajan por el pie), apretadas, gruesas, desiguales y unidas por venas, blanquecinas o amarillentas sucias.",
   "Pie de hasta 13 cm, blanquecino arriba y gris ocráceo pálido hacia la base.",
   "Carne blanca que se vuelve negra o tiznada; sabor de algo amargo y desagradable a suave. Bajo planifolios y coníferas."],
  "Con una especie venenosa que Wikipedia no nombra ni explica cómo separar; a simple vista se confunde con las demás rúsulas que ennegrecen (Russula adusta, que pasa por una fase roja antes de negra). Wikipedia dice que «se recomienda no consumirla»: quizá se pueda comer bien cocida, pero no tiene interés y se parece a una especie venenosa.",
  dict(s_color="blanco gris negro", s_forma="convexo embudo", h_tipo="!laminas", h_color="blanco amarillo", p_color="blanco gris", habitat="conifera planifolio", s_tam="grande"),
  ca=["carboner"], ca_f="EC")

F("russula-heterophylla", "Russula heterophylla", "alto",
  ["Sombrero de 5-10 cm, de color verde, pardo u ocre, redondo al principio y luego aplanado y con el centro hundido.",
   "Láminas blancas y poco pegadas; esporada blanca.",
   "Pie blanco que se pone pardo, firme; al frotarlo con sulfato de hierro da una reacción salmón.",
   "Bajo planifolios, normalmente en grupos pequeños; de verano a principios de otoño, ocasional en Gran Bretaña, Europa y Escandinavia; las babosas la atacan con frecuencia."],
  ["Anillo o bolsa (volva) en el pie (sería una amanita).", "Sombrero con la superficie cuarteada (sería Russula virescens).", "Sabor picante."],
  [("Oronja verde (Amanita phalloides)", "mortal", "Wikipedia avisa de que de joven se parece mucho; la oronja verde tiene anillo y volva (bolsa), la rúsula no."),
   ("Russula cyanoxantha (formas verdes)", None, "reacciona poco o nada al sulfato de hierro y tiene las láminas flexibles y untuosas."),
   ("Russula aeruginea", None, "crece junto a abedules."),
   ("Russula langei", None, "reacciona en verde al sulfato de hierro, huele a marisco y la carne se mancha de naranja pardo.")],
  "Wikipedia la da como comestible y buena, pero insiste en el cuidado por su parecido con la oronja verde.",
  dict(s_color="verde pardo", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_color="blanco", esporada="blanca", habitat="planifolio", s_tam="mediano"))

F("russula-mustelina", "Russula mustelina", "medio",
  ["Sombrero de 7-12 cm (a veces hasta 16), convexo y luego aplanado, a veces algo hundido; seco y algo pegajoso con humedad; amarillo pálido a pardo amarillento, con el borde y manchas color vino que aparecen con la edad.",
   "Láminas crema, de pegadas a casi libres; esporada amarillenta.",
   "Pie de 4-9 cm de alto y 2-3 cm de grosor, duro, blanco, seco y liso; carne blanca de sabor suave y casi sin olor.",
   "Sale en otoño, a veces medio hundida en el suelo, en bosques de coníferas de montaña (por encima de 1.600 m en Sierra Nevada y las Cascadas) y en una turbera de los Cárpatos orientales con pícea."],
  ["Sabor picante.", "Anillo o bolsa (volva) en el pie."],
  [("Russula basifurcata", None, "parecida pero más pequeña, bajo robles y a menor altitud, con láminas bifurcadas cerca del pie.")],
  "Wikipedia solo dice que se recoge y se come en Costa de Marfil; no da una valoración general de comestibilidad.",
  dict(s_color="amarillo pardo", s_super="lisa", s_forma="convexo", h_tipo="!laminas", h_color="blanco amarillo", p_color="blanco", habitat="conifera", s_tam="mediano"))

P("russula-queletii", "Russula queletii", "toxica",
  ["Sombrero de 3-10 cm, rojo vino a púrpura, redondo o convexo de joven y luego aplanado u hundido.",
   "Láminas blancas a crema, pegadas, algo decurrentes o casi libres; esporada crema.",
   "Pie de 3-8 cm de alto y 0,5-1,8 cm de grosor, del color del sombrero.",
   "Carne blanca de olor afrutado y sabor acre. En grupos, sobre todo en bosques de pícea."],
  "Con Russula sardonia y Russula torulosa, que Wikipedia cita como parecidas sin explicar la diferencia. Wikipedia dice que es no comestible y que su consumo causa dolores abdominales.",
  dict(s_color="rojo violeta", s_forma="convexo", h_tipo="!laminas", h_color="blanco amarillo", p_color="rojo violeta", esporada="blanca", habitat="conifera", s_tam="pequeno mediano"))

F("russula-amethystina", "Russula amethystina", "bajo",
  ["Sombrero de 3-12 cm, violeta, lila, rojo vino o pardo vino; la cutícula se pela del borde al centro.",
   "Láminas de crema a amarillo vivo; esporada de crema a naranja claro.",
   "Pie hueco de 3-6 cm de alto y 1-2 cm de ancho, blanco al principio y luego amarillento o pardusco.",
   "Esporádica bajo píceas y abetos desde mediados de verano hasta el otoño; muy rara en el norte de Europa."],
  ["Pie macizo.", "Bajo planifolios."],
  [("Russula turci", None, "«prácticamente idéntica»: puede oler a yodo cerca de la base del pie y solo se separa con el microscopio."),
   ("Russula lilacea y Russula murrillii", None, "Wikipedia las da como parecidas sin explicar la diferencia.")],
  "Bosques de abetos y piceas del hemisferio norte. La fuente consultada no dice nada sobre su comestibilidad.",
  dict(s_color="violeta rojo pardo", s_forma="convexo", h_tipo="!laminas", h_color="blanco amarillo", p_color="blanco amarillo pardo", interior="hueco", habitat="conifera", s_tam="mediano"))

F("russula-caerulea", "Russula caerulea", "bajo",
  ["Sombrero de 3-10 cm, pardo purpúreo oscuro con el centro más oscuro, casi negro; convexo o casi campaniforme de joven y luego aplanado, que suele conservar un mamelón ancho y puntiagudo.",
   "Láminas ocre pálido, de casi libres a pegadas, apretadas de jóvenes; esporada ocre pálido.",
   "Pie de 4-9 cm de alto y 1-2 cm de ancho, en forma de maza estrecha, firme y blanco.",
   "La cutícula del sombrero se pela hasta dos tercios y es amarga al masticarla. Carne blanca y suave. Con coníferas, a finales de verano y otoño, probablemente con pino en suelos arenosos."],
  ["Sombrero sin mamelón y hundido (sería Russula atropurpurea)."],
  [("Russula atropurpurea", None, "es poco frecuente con coníferas, prefiere planifolios y su sombrero nunca tiene mamelón: suele estar hundido."),
   ("Russula viscida", None, "sin mamelón, muy rara, y la cutícula casi no se pela.")],
  "Zonas templadas del hemisferio norte, en Europa y América del Norte. Wikipedia la da como comestible, pero con la cutícula del sombrero amarga al masticarla.",
  dict(s_color="violeta pardo negro", s_forma="convexo conico", h_tipo="!laminas", h_color="amarillo pardo", p_color="blanco", habitat="conifera", s_tam="mediano"))

F("lactarius-volemus", "Lactifluus volemus (Lactarius volemus)", "medio",
  ["Sombrero de 5-11 cm, albaricoque a pardo anaranjado, aterciopelado o liso y carnoso; convexo con el borde enrollado de joven y luego plano con el centro hundido.",
   "Láminas amarillo dorado pálido, estrechas, apretadas y a veces bifurcadas, de pegadas a algo decurrentes; se ponen pardas al magullarlas; esporada blanquecina.",
   "Pie de 4-12 cm de alto y 1-1,5 cm de grosor, algo más claro que el sombrero, firme.",
   "Látex (leche) blanco muy abundante que «llora» al cortar las láminas y mancha de pardo; olor algo a pescado, que se concentra al secarla y desaparece al cocinarla. Bajo planifolios (más) y coníferas, en verano y otoño."],
  ["Látex que no sea blanco o que no sea abundante.", "Seta sin olor a pescado."],
  [("Lactifluus subvelutinus", None, "sin olor a pescado, con el sombrero amarillo naranja apagado a dorado, láminas estrechas y látex blanco que no cambia."),
   ("Lactifluus corrugis", None, "más arrugada, con láminas más oscuras, olor débil o ausente y menos anaranjada."),
   ("Lactifluus hygrophoroides", None, "láminas muy separadas.")],
  "Hemisferio norte templado. Wikipedia la da como comestible y recomendada; también cuenta dos casos de pancreatitis pasajera en dos personas mayores de Turquía tras comerla.",
  dict(s_color="naranja pardo", s_super="lisa", s_forma="convexo embudo", h_tipo="!laminas", h_color="amarillo pardo", p_color="naranja pardo", latex="!blanco", esporada="blanca", habitat="planifolio conifera", s_tam="mediano"),
  ca=["lleterola grossa"], ca_f="EC")

P("lactarius-piperatus", "Lactifluus piperatus (Lactarius piperatus)", "nocom",
  ["Sombrero de 6-16 cm, blanco crema que se tiñe de ante con la edad, de convexo con el centro hundido a embudo; liso y no brillante, a veces agrietado en tiempo seco.",
   "Láminas decurrentes (bajan por el pie), muy apretadas y estrechas, blancas que pasan a crema.",
   "Pie blanco de 2-8 cm de alto y 1-3 cm de grosor, cilíndrico, liso; carne blanca muy gruesa y firme.",
   "Látex blanco muy abundante, que al secarse se vuelve verde oliva; de sabor muy picante y acre al cortarla. Bajo planifolios, sobre todo hayas y avellanos; de verano a principios de invierno."],
  "Con Lactifluus vellereus (mayor, con el sombrero velloso y las láminas menos apretadas), Lactarius deceptivus, Lactarius glaucescens (el látex seca verdoso) y Russula delica (sin leche, con láminas pegadas y tinte azul verdoso). Wikipedia dice que a menudo se considera comestible pero que se informa de que contiene toxinas y tiene mal sabor; algunos autores la dan como no comestible o incluso venenosa. La Enciclopèdia Catalana la pone «acceptable».",
  dict(s_color="blanco", s_super="lisa", s_forma="embudo", h_tipo="!laminas", h_color="blanco", p_color="blanco", latex="!blanco", esporada="blanca", habitat="planifolio", s_tam="grande"),
  ca=["pebrás lleter"], ca_f="EC")

P("lactarius-vellereus", "Lactifluus vellereus (Lactarius vellereus)", "nocom",
  ["Sombrero de hasta 30 cm, blanco a crema, en forma de embudo, de aspecto velloso (de ahí su nombre).",
   "Láminas bastante separadas y estrechas, decurrentes, con manchas pardas de leche seca.",
   "Pie más corto que el ancho del sombrero; carne firme y quebradiza (no fibrosa).",
   "Leche que sale al romper la carne: suave sola, pero picante al probarla con la carne. En bosques de planifolios, una de las dos lactarias más comunes bajo hayas; de finales de verano a principios de invierno."],
  "Con Lactifluus bertillonii (muy parecida, con la leche más picante) y con Lactarius controversus (láminas blancas y sin manchas rosadas en lo alto del sombrero). Wikipedia dice que se considera no comestible por su sabor picante. La Enciclopèdia Catalana la pone «acceptable».",
  dict(s_color="blanco", s_forma="embudo", h_tipo="!laminas", h_color="blanco", latex="blanco", esporada="blanca", habitat="planifolio", s_tam="grande"),
  ca=["pebràs lleter vellutat"], ca_f="EC")


# ============================================================================================================
# LACTARIOS (LLETEROLES, PEBRASSOS)
# ============================================================================================================
P("lactarius-blennius", "Lactarius blennius", "nocom",
  ["Sombrero de 4-10 cm, de convexo aplanado a hundido en el centro, verde oliva pálido a gris verdoso, con manchas oscuras en círculos; muy baboso con humedad y con el borde enrollado hacia dentro.",
   "Láminas apretadas, blanquecinas y luego crema o ante pálido, algo decurrentes; se ponen gris pardas al dañarlas.",
   "Pie de 4-5 cm de alto y 1-1,7 cm de grosor, más claro que el sombrero y muy baboso; carne blanquecina.",
   "Látex blanco muy abundante, que seca gris, de sabor muy picante y acre. En bosques de planifolios, sobre todo hayedos (y también robles); de finales de verano a finales de otoño."],
  "Con Lactarius cinereus (emparentada y también del hayedo) y Lactarius fluens (borde del sombrero pálido, menos baboso y láminas de un crema más intenso). Wikipedia recoge opiniones distintas: «comestible cocinada, pero no se recomienda», «no comestible» y «venenosa».",
  dict(s_color="verde gris", s_super="viscosa", s_forma="convexo embudo", h_tipo="!laminas", h_color="blanco amarillo", p_color="blanco gris", latex="!blanco", esporada="blanca", habitat="planifolio", s_tam="pequeno mediano"))

F("lactarius-camphoratus", "Lactarius camphoratus", "alto",
  ["Sombrero de 2-7 cm, pardo anaranjado a pardo rojizo, ampliamente convexo de joven y plano o algo hundido después; nunca zonado ni viscoso.",
   "Láminas pegadas o algo decurrentes; pie de 3-6 cm, frágil y quebradizo.",
   "Látex blanquecino y aguado, como suero de leche, que no cambia de color ni mancha la carne; sabor suave a algo dulce, nunca amargo ni acre.",
   "Olor a jarabe de arce, alcanfor, curry o azúcar quemado: débil en fresco y fuerte al secarla. Con muchos árboles, a veces sobre madera podrida de coníferas."],
  ["Látex de otro color o que mancha la carne.", "Sabor amargo o acre.", "Pie flexible (no quebradizo)."],
  [("Galerina marginata y otras galerinas mortales", "mortal", "Wikipedia avisa de que crece en el mismo hábitat; la lactaria tiene el pie quebradizo y cartilaginoso (se parte limpio) y la galerina lo tiene flexible."),
   ("Lactarius helvus y L. aquifluus", "toxica", "Wikipedia las cita como tóxicas («levemente tóxica» y «sospechosa»); también son muy aromáticas."),
   ("Lactarius glyciosmus y L. cocosiolens", None, "huelen a coco; L. glyciosmus deja un regusto algo acre.")],
  "Costa oeste de América del Norte, en la fuente consultada. Wikipedia dice que no se come como otras setas y se usa sobre todo como aromatizante; que las lactarias de látex amarillo pueden ser peligrosas y que otras lactarias pequeñas pueden ser desagradables o tóxicas.",
  dict(s_color="naranja pardo rojo", s_forma="convexo", h_tipo="!laminas", latex="!blanco", habitat="conifera planifolio madera", s_tam="pequeno mediano"))

F("lactarius-glyciosmus", "Lactarius glyciosmus", "bajo",
  ["Sombrero pequeño de 2-6 cm, gris lila a veces ante pálido, convexo y con un hundimiento central que aparece con la edad, a veces con un mamelón; carne delgada y borde enrollado.",
   "Láminas apretadas y decurrentes, de amarillo pálido a color carne, que se vuelven gris lila con la edad; esporada blanco cremosa.",
   "Pie de 25-65 mm, cilíndrico o en maza, del color del sombrero o algo más pálido, blando y fácil de romper, a veces hueco.",
   "Látex blanco, suave al principio y luego picante y acre; olor fuerte a coco. Bajo planifolios, sobre todo abedules y a menudo entre esfagnos; verano y otoño."],
  ["Látex que seca gris (sería Lactarius vietus).", "Sin olor a coco."],
  [("Lactarius vietus", None, "su látex seca gris; el de esta seca blanco."),
   ("Lactarius cocosiolens", None, "también huele a coco, pero con el sombrero baboso pardo o naranja y no en abedulares.")],
  "América del Norte, Europa, Nueva Zelanda, Svalbard, Japón y China. Wikipedia dice que se considera comestible (a veces «semicomestible») y se vende en mercados de Yunnan, pero que algunos micólogos no la recomiendan.",
  dict(s_color="gris violeta amarillo", s_forma="convexo", h_tipo="!laminas", h_color="amarillo rosa violeta", p_color="gris violeta", interior="hueco", latex="!blanco", esporada="blanca", habitat="planifolio", s_tam="pequeno"))

F("lactarius-quietus", "Lactarius quietus", "medio",
  ["Sombrero de 5-8 cm, convexo y luego plano o con un pequeño hundimiento, pardo rojizo apagado con un matiz canela y bandas o manchas más oscuras; seco y mate, no pegajoso.",
   "Láminas blanco pardas, algo decurrentes, que con la edad pasan a pardo rojizo pálido con tonos malva; esporada crema.",
   "Pie de 4-9 cm de alto y 1-1,5 cm de grosor, cilíndrico, del color del sombrero o algo más oscuro, a veces hueco; sin anillo.",
   "Carne gruesa, firme, blanquecina; látex blanco o crema de sabor suave o algo amargo; olor fuerte y aceitoso (a chinches o a ropa mojada). Siempre al pie de robles, muy común en otoño."],
  ["Seta fuera de robledales.", "Anillo en el pie.", "Látex de otro color."],
  [("Lactarius aquifluus y L. mutabilis (var. incanus)", None, "crecen en coníferas y no bajo robles; la var. incanus es algo mayor, con velo blanquecino de joven y olor dulce a jarabe de arce.")],
  "Solo en Europa (la variedad incanus también en América del Norte oriental); una de las 100 setas más encontradas en el Reino Unido. Wikipedia dice que su comestibilidad se discute: se ha descrito como comestible y como no comestible, y la variedad incanus no se recomienda.",
  dict(s_color="pardo rojo", s_super="lisa", s_forma="convexo", h_tipo="!laminas", h_color="blanco pardo", p_anillo="no", p_color="pardo", latex="!blanco", esporada="blanca", habitat="planifolio", s_tam="mediano"))

P("lactarius-rufus", "Lactarius rufus", "toxica",
  ["Sombrero de hasta 10 cm, rojo ladrillo oscuro o pardo rojizo, convexo y a menudo con un pequeño mamelón, luego con un ligero hundimiento; seco y mate.",
   "Láminas ligeramente decurrentes, crema y luego del color del sombrero pero más pálidas; esporada crema con un matiz salmón.",
   "Pie más pálido que el sombrero, a menudo hueco con la edad; carne blanca.",
   "Látex blanco muy abundante que no cambia de color y que al principio es suave y a los pocos segundos muy picante y acre. Con pinos sobre todo (también abedules, piceas); de finales de primavera a finales de otoño."],
  "No se citan parecidas concretas. Wikipedia dice que generalmente no se recomienda consumirla, que se considera venenosa por toxinas que pueden causar molestias de estómago y que puede ser venenosa cruda; en Finlandia y otros países nórdicos se toma tras un tratamiento especial.",
  dict(s_color="rojo pardo", s_super="lisa", s_forma="convexo conico", h_tipo="!laminas", h_color="blanco pardo", latex="!blanco", esporada="blanca", habitat="conifera", s_tam="mediano"))

P("lactarius-scrobiculatus", "Lactarius scrobiculatus", "toxica",
  ["Sombrero de unos 15 cm, naranja a amarillo, con escamas pequeñas en círculos poco marcados, hundido en el centro y con el borde algo enrollado; brillante y baboso, sobre todo en tiempo húmedo.",
   "Láminas apretadas, crema a amarillas, a veces con manchas más oscuras.",
   "Pie corto y rechoncho, hueco, del color del sombrero, con pequeños hoyos llenos de líquido.",
   "Látex blanco a crema que pasa pronto a amarillo y que sale en abundancia de las láminas; sin olor; sabor amargo a acre. En bosques de coníferas y abedules, en sitios húmedos y umbríos; en grupos o corros; verano y otoño."],
  "Con Lactarius alnicola, L. controversus, L. plumbeus, L. repraesentaneus y L. torminosus, sin que Wikipedia diga cómo separarlas. Wikipedia dice que la mayoría de los autores la consideran no comestible, que en algunas zonas de Europa se consume tras tratarla, y que comerla causa molestias de estómago; esta guía no te la recomienda.",
  dict(s_color="naranja amarillo", s_super="viscosa escamas", s_forma="embudo", h_tipo="!laminas", h_color="blanco amarillo", p_color="naranja amarillo", interior="hueco", latex="!amarillea", habitat="conifera planifolio", grupo="corro", s_tam="grande"))

F("lactarius-subdulcis", "Lactarius subdulcis", "bajo",
  ["Sombrero de 3-7 cm, rojo pardo, óxido o canela oscuro, que se aclara hacia el ante y es más oscuro en el centro; convexo y luego hundido, a veces con un pequeño mamelón, liso o algo arrugado.",
   "Láminas apretadas, blancas o rosadas, de pegadas a algo decurrentes; esporada crema con un matiz salmón.",
   "Pie de 3-7 cm de alto y 6-13 mm de grosor, cilíndrico o en maza, del color del sombrero y más pálido arriba.",
   "Látex blanco y abundante, dulce y luego amargo en la boca; olor débil, aceitoso. En bosques de planifolios, sobre todo al pie de hayas, y a veces en campos; de finales de verano a finales de otoño."],
  ["Látex que manche las telas de amarillo (sería Lactarius decipiens).", "Látex de otro color."],
  [("Lactarius decipiens", None, "su látex mancha la tela de amarillo; el de esta no.")],
  "Solo en Europa. Wikipedia dice que, aunque se considera comestible tras cocinarla, no se recomienda.",
  dict(s_color="pardo rojo", s_super="lisa", s_forma="convexo", h_tipo="!laminas", h_color="blanco rosa", p_color="pardo rojo", latex="!blanco", esporada="blanca", habitat="planifolio", s_tam="pequeno mediano"))

P("lactarius-uvidus", "Lactarius uvidus", "toxica",
  ["Sombrero de hasta unos 10 cm, beige o gris con frecuencia con un tinte lila, de forma aplanada y a veces hundido; untuoso o viscoso con humedad.",
   "Láminas cremosas, algo decurrentes, que se manchan de violeta donde toca el látex.",
   "Pie de hasta unos 8 cm y 2 de grosor, pálido, que se vuelve hueco con la edad.",
   "El látex blanco pasa a violeta en el aire; la carne y el látex tienen un sabor algo amargo. En bosques de planifolios y de coníferas, sobre todo en suelos ácidos."],
  "Con Lactarius pseudouvidus (alpina, hasta 4 cm, láminas amarillo ocre), L. robertianus (alpina, más oscura, huele a cedro) y L. luridus (cuyo látex pasa a un violeta profundo). Wikipedia dice que se considera en general venenosa por sus toxinas, y también «comestible con reservas»; el grupo es difícil de separar de especies emparentadas.",
  dict(s_color="gris pardo violeta", s_super="viscosa", s_forma="convexo embudo", h_tipo="!laminas", h_color="blanco violeta", p_color="blanco", interior="hueco", latex="blanco", esporada="blanca", habitat="conifera planifolio", s_tam="mediano"))

P("lactarius-controversus", "Lactarius controversus", "nocom",
  ["Sombrero de 5-20 cm, blanquecino con zonas rosadas en círculos, cóncavo y en embudo en los maduros.",
   "Láminas decurrentes, color ante rosado; pie de hasta 7 cm.",
   "Carne firme y quebradiza (no fibrosa); látex blanco, lechoso, que sale de la carne y de las láminas al dañarlas, y de sabor muy acre con sensación de quemazón.",
   "En Europa, normalmente con sauces (Salix) en brezales y páramos, poco común; en América del Norte con álamos temblones, chopos y sauces."],
  "Con Lactifluus vellereus, L. bertillonii y L. piperatus (lactarias blancas solo lejanamente emparentadas), que no tienen las láminas rosadas ni las manchas rosadas del sombrero. Wikipedia lo clasifica como no comestible por su sabor muy acre, aunque se come y recolecta comercialmente en el sureste de Europa (Serbia, Turquía).",
  dict(s_color="blanco rosa", s_forma="embudo", h_tipo="!laminas", h_color="rosa", latex="!blanco", esporada="blanca rosa", habitat="planifolio", s_tam="grande"),
  ca=["pebrás de riberada"], ca_f="EC")

P("lactarius-zonarius", "Lactarius zonarius (Lactarius insulsus)", "toxica",
  ["Sombrero de 4-16 cm, de color crema amarillento a crema anaranjado.",
   "Pie de 2-5 cm de largo y 1-2 cm de grosor; carne blanca y carnosa.",
   "Látex blanco al cortarla."],
  "Wikipedia da pocos datos de esta seta: solo la describe como «un hongo raro y venenoso» de Europa y América del Norte. La Enciclopèdia Catalana la pone «a refusar» con el nombre «enganyapastors».",
  dict(s_color="amarillo naranja blanco", h_tipo="!laminas", latex="!blanco", s_tam="mediano grande"),
  ca=["enganyapastors"], ca_f="EC")

P("lactarius-pyrogalus", "Lactarius pyrogalus", "nocom",
  ["Sombrero de 5-10 cm, gris ante a veces con un tinte amarillento (los tintes rosas o púrpuras «no son desconocidos»), de convexo aplanado a plano y luego en embudo; a veces con bandas apenas visibles, de carne delgada, pegajoso con humedad y no brillante.",
   "Láminas algo decurrentes, bien separadas, amarillas a color carne y luego canela ocre; esporada ocre claro.",
   "Pie de 4-6 cm de alto y 7-15 mm de grosor, cilíndrico, a veces algo hinchado en la base, blanquecino o del color del sombrero.",
   "Sabor muy picante, acre y ácido. En el suelo de bosques mixtos, sobre todo al pie de avellanos y en avellanedas explotadas como monte bajo; solitaria o en grupos dispersos; de agosto a octubre."],
  "Con otras lactarias grisáceas, que Wikipedia no nombra: la distingue por las láminas amarillas y bien separadas. Wikipedia dice que, a pesar de no ser venenosa, no se considera comestible y debe evitarse. La Enciclopèdia Catalana la pone «a refusar».",
  dict(s_color="gris pardo", s_super="viscosa", s_forma="convexo embudo", h_tipo="!laminas", h_color="amarillo pardo", p_color="blanco gris", habitat="planifolio", s_tam="mediano"),
  ca=["lleterola verda"], ca_f="EC")

F("lactarius-salmonicolor", "Lactarius salmonicolor", "bajo",
  ["Sombrero naranja rojizo, a veces con raras manchas verdes en los ejemplares viejos y descompuestos; convexo y luego algo hundido, irregular y a veces lobulado, liso y viscoso.",
   "Láminas regulares, a veces bifurcadas, decurrentes, naranja salmón y algo más claras que el sombrero; se ponen rojas al magullarlas.",
   "Pie normalmente largo y delgado, rara vez corto y grueso, cilíndrico.",
   "Sabor suave y algo acre, que se vuelve amargo con el tiempo. Principalmente junto a abetos, de septiembre a noviembre."],
  ["Seta fuera de abetos (la fuente solo la cita con ellos).", "Láminas que no se enrojezcan al magullarlas."],
  [("Otras lactarias anaranjadas (Lactarius deliciosus y parecidas)", None, "la fuente consultada no cita ninguna parecida concreta ni cómo separarlas.")],
  "Casi toda Europa y turberas y bosques de coníferas de Canadá y el noreste de Estados Unidos. Wikipedia dice que tiene algunos usos culinarios en partes de Europa.",
  dict(s_color="naranja rojo", s_super="viscosa", s_forma="convexo embudo", h_tipo="!laminas", h_color="naranja", corte="enrojece", habitat="conifera"),
  ca=["pinetell d'avetosa"], ca_f="EC")

P("lactarius-fuliginosus", "Lactarius fuliginosus", "nocom",
  ["Sombrero de 4,5-12,5 cm, ante a pardo grisáceo a pardo oscuro, a veces con manchas más oscuras y borde más claro; convexo a aplanado, seco, liso y aterciopelado.",
   "Láminas apretadas, ante oliváceo a ante rosado, que se manchan de rosa; de pegadas a algo decurrentes; esporada ante rosada.",
   "Pie cilíndrico de 4-8,5 cm de alto y 1-2 cm de grosor, que se estrecha hacia la base, más pálido que el sombrero.",
   "Carne blanquecina que se tiñe de rosa donde se daña; látex escaso, blanco, que seca rosado; olor poco marcado y sabor suave a algo acre. Bajo planifolios."],
  "Con Lactarius azonites (borde del sombrero festoneado, láminas irregulares y a menudo unidas, pie casi blanco y carne que enrojece enseguida) y con Lactarius picinus (especie hermana imposible de separar con fiabilidad por la forma). Wikipedia dice que no es comestible y que puede ser algo venenosa. La Enciclopèdia Catalana la pone «acceptable» con el nombre «lleterola fosca».",
  dict(s_color="pardo gris", s_super="lisa", s_forma="convexo", h_tipo="!laminas", h_color="pardo rosa", p_color="blanco pardo", latex="!blanco", corte="enrojece", esporada="rosa", habitat="planifolio", s_tam="mediano"),
  ca=["lleterola fosca"], ca_f="EC")


# ============================================================================================================
# BOLETOS Y PARIENTES (POROS)
# ============================================================================================================
F("gyroporus-cyanescens", "Gyroporus cyanescens", "medio",
  ["Sombrero de 4-12 cm, convexo y luego aplanado, color paja a amarillento o verde oliva pálido, seco y de aspecto fibroso, áspero y a veces arrugado u hoyado.",
   "Debajo, tubos de 5-10 mm con poros pequeños (unos dos por mm), blancos a amarillentos, que al tocarlos pasan de verde amarillento a verde azulado o azul.",
   "Pie de 4-12 cm, del color del sombrero o más claro, seco y sin red; relleno de una médula blanda con cavidades de joven y hueco al madurar.",
   "Toda la carne, quebradiza y blanca a amarillo pálido, se vuelve azul intenso en segundos al cortarla; olor y sabor poco marcados. En suelo arenoso de bosques de coníferas y mixtos, a menudo con abedul y chopo; de julio a septiembre."],
  ["Carne que no se vuelve azul en segundos.", "Tubos o poros de color rojo o naranja.", "Sabor amargo."],
  [("Russula fellea joven", None, "Wikipedia dice que puede confundirse si solo se ve el sombrero desde arriba."),
   ("Suillus tomentosus", None, "con los poros pardos y el azuleo más lento."),
   ("Gyroporus phaeocyanescens", None, "más pequeña, de sombrero pardo amarillento apagado y poros amarillos que no azulean.")],
  "Europa, Asia, Australia y este de América del Norte. Wikipedia la da como comestible y «selecta» en varias fuentes; se reconoce en el campo por el color paja y por el azuleo casi instantáneo. La Enciclopèdia Catalana la pone en el grado más alto («excel·lent») con el nombre «mataparent groc».",
  dict(s_color="amarillo pardo verde", s_super="fibrosa", s_forma="convexo", h_tipo="!poros", h_color="blanco amarillo", p_color="amarillo pardo", p_super="lisa", corte="!azulea", interior="camaras hueco", habitat="conifera planifolio", s_tam="mediano"),
  ca=["mataparent groc"], ca_f="EC")

F("gyroporus-castaneus", "Gyroporus castaneus", "medio",
  ["Sombrero de 3-10 cm, pardo pálido a pardo rojizo que se oscurece con la edad; tiende a agrietarse en tiempo seco o con los años.",
   "Poros pequeños, blancos y que amarillean con la edad, que se oscurecen algo al presionarlos; tubos blanquecinos y no pegados al pie.",
   "Pie del color del sombrero, quizá más claro arriba; cortado a lo largo suele mostrar varias cavidades de distinto tamaño.",
   "Carne firme que no cambia de color al cortarla; esporada amarillo pálido a paja. Suelta o en grupos pequeños, con robles, en suelos ácidos y arenosos; de verano a otoño."],
  ["Carne que se vuelve azul al cortarla.", "Poros rojos o anaranjados.", "Pie macizo y sin cavidades."],
  [("Boletos de verdad (Boletus)", None, "Wikipedia la diferencia por la esporada: de color paja, no pardo oliváceo.")],
  "Rara en Gran Bretaña, repartida por Europa y el este de América del Norte. Wikipedia dice que la mayoría de los autores la valoran mucho como comestible, pero que Marcel Bon (1987) la consideró sospechosa y que se cita una cepa venenosa en la costa de Portugal. La Enciclopèdia Catalana la valora «molt bo» con el nombre «sureny castany».",
  dict(s_color="pardo", s_forma="convexo", h_tipo="!poros", h_color="blanco amarillo", p_color="pardo", interior="camaras", corte="nada", habitat="planifolio", s_tam="mediano"),
  ca=["sureny castany"], ca_f="EC")

F("hemileccinum-impolitum", "Hemileccinum impolitum (Boletus impolitus)", "medio",
  ["Sombrero de 5-12 cm (a veces 20), semiesférico de joven y luego convexo a plano, de ante claro a pardo oliváceo; de joven con una capa aterciopelada gris plateada que se pierde con la edad. La cutícula se pone violeta con una gota de amoníaco.",
   "Tubos amarillo limón con poros pequeños y redondos, amarillo limón a amarillo cromo, que no cambian de color al tocarlos (rara vez un leve verde pardo).",
   "Pie de 5-15 cm de alto y 2-6 cm de ancho, crema a amarillo pálido y amarillo limón arriba, sin red, con pequeñas pústulas bajo el ápice.",
   "Carne gruesa, blanda, amarillo pálido a blanquecina, que normalmente no cambia al cortarla; olor ácido, algo a yodo, más fuerte en la base del pie. Con planifolios, sobre todo robles (también hayas y castaños)."],
  ["Pie con red marcada.", "Carne que se vuelve azul en el corte.", "Poros rojos o naranjas."],
  [("Hemileccinum depilatum", None, "casi igual, con la superficie del sombrero arrugada «a martillazos» y bajo carpes."),
   ("Leccinellum lepidum", None, "con el sombrero viscoso y arrugado que no se pone violeta con amoníaco y la carne que se vuelve gris violácea y luego negruzca."),
   ("Xerocomus subtomentosus", None, "sin pústulas en el pie, con poros mayores y angulosos que azulean al tocarlos.")],
  "Sur y centro de Europa. Wikipedia dice que algunos autores la dan por comestible y otros por no comestible, probablemente por su olor, y avisa de que se debe obrar «con cuidado y criterio» si se piensa comerla.",
  dict(s_color="pardo amarillo gris", s_forma="convexo", h_tipo="!poros", h_color="amarillo", p_color="blanco amarillo", p_super="puntos", corte="nada", habitat="planifolio", s_tam="mediano grande"))

F("butyriboletus-appendiculatus", "Butyriboletus appendiculatus", "medio",
  ["Sombrero de 6-20 cm, marrón a pardo amarillento, de convexo a aplanado, seco a algo pegajoso, que puede agrietarse con la edad.",
   "Poros amarillo mantequilla, que pueden azulear al magullarlos (menos en los jóvenes).",
   "Pie de 5-15 cm de alto y 2-6 cm de grosor, amarillo con manchas pardas o rojizas, con una red fina en la parte alta; base variable, desde gruesa a afinada.",
   "Carne muy firme y amarillenta que puede volverse azul despacio; esporada pardo oliva oscuro. Bajo robles y otros planifolios (hayas); suelto, disperso o en colonias; a menudo junto a robles viejos."],
  ["Carne que se vuelve azul de golpe y poros rojos.", "Sabor amargo.", "Sombrero sin tonos pardos."],
  [("Butyriboletus subappendiculatus", None, "sin cambio de color al magullarla, con el sombrero más pálido y bajo coníferas."),
   ("Butyriboletus regius y Boletus edulis", None, "Wikipedia las cita como parecidas sin decir cómo separarlas.")],
  "Europa y América del Norte; relativamente rara en Gran Bretaña. Wikipedia la da como comestible y «selecta» según varias fuentes, con posibles reacciones alérgicas en algunas personas.",
  dict(s_color="pardo amarillo", s_forma="convexo", h_tipo="!poros", h_color="amarillo", p_color="amarillo", p_super="red", corte="azulea", habitat="planifolio", s_tam="grande"))

F("butyriboletus-regius", "Butyriboletus regius (Boletus regius)", "alto",
  ["Sombrero de 6-20 cm, de rosa a rojo, a veces con tonos amarillos o pardos sobre todo en el borde; convexo o plano, aterciopelado de joven, con arrugas y hoyuelos cuando se pierden los pelos.",
   "Poros angulosos, de 1-2 por mm, amarillo vivo que se oscurecen algo con la edad, con tubos de 0,8-2,5 cm; azulean al magullarlos.",
   "Pie de 5-14 cm de alto y 2,5-6 cm de grosor, macizo, con una base gruesa y abultada; amarillo vivo, a menudo rojizo hacia la base, con una red amarilla fina en todo el pie o solo arriba.",
   "Carne amarilla; en las poblaciones norteamericanas azulea despacio y de forma irregular, y en las europeas no azulea o muy poco. Esporada pardo oliva. Con robles y coníferas (sobre todo abeto)."],
  ["Poros rojos o anaranjados.", "Pie sin red.", "Sabor amargo."],
  [("Boletos de Satanás y de poros rojos", "toxica", "el sombrero rosado a rojo no debe hacer pensar en ellos sin mirar los poros: los de esta son amarillos (ver las fichas «Boleto de Satanás» y «Boletos de poros rojos»)."),
   ("Butyriboletus appendiculatus", None, "emparentada («boleto de mantequilla»); se separó con análisis moleculares.")],
  "Rara en Europa y en varias listas rojas (en peligro en la República Checa); en California, de «rara a localmente abundante». Wikipedia la da como comestible y «selecta»; las setas de California pueden estar agusanadas. Una gota de sulfato de hierro tiñe la cutícula de púrpura pálido y la carne de gris.",
  dict(s_color="rosa rojo", s_forma="convexo", h_tipo="!poros", h_color="amarillo", p_color="amarillo rojo", p_super="red", p_base="ensanchada", interior="macizo", corte="nada azulea", habitat="planifolio conifera", s_tam="grande"))

F("suillellus-queletii", "Suillellus queletii (Boletus queletii)", "alto",
  ["Sombrero semiesférico de joven y luego más plano, de oliva a pardo rojizo, rara vez rojo oscuro.",
   "Poros que al principio son amarillos, pronto naranja y por fin pueden ser rojizos; esporada oliva.",
   "Pie liso, amarillo dorado.",
   "Carne amarilla que se vuelve azul al cortarla, de sabor algo acre. En bosques de planifolios de zonas bajas, bajo hayas, robles o avellanos; poco común en Europa."],
  ["Poros siempre amarillos (no pasan a naranja o rojo con la edad).", "Pie con red marcada.", "Carne que no azulea."],
  [("Boletos de poros rojos (Suillellus luridus, Neoboletus erythropus)", "toxica", "Wikipedia no cita parecidas, pero los boletos de poros rojos o naranjas se confunden entre sí y algunos son tóxicos: compara con la ficha «Boletos de poros rojos»."),
   ("Boleto de Satanás (Rubroboletus satanas)", "toxica", "tiene el sombrero pálido y los poros rojos.")],
  "Uncommon en Europa (en peligro en la República Checa); registrada en Taiwán. Wikipedia dice que es un hongo «poco común, comestible» y que el nombre Boletus erythropus se ha aplicado a una especie de poros rojos distinta. La Enciclopèdia Catalana la valora «bo» con el nombre «mataparents de cama vermella».",
  dict(s_color="pardo rojo verde", s_forma="convexo", h_tipo="!poros", h_color="amarillo naranja rojo", p_color="amarillo", p_super="lisa", corte="!azulea", habitat="planifolio"),
  ca=["mataparents de cama vermella"], ca_f="EC")

F("leccinum-aurantiacum", "Leccinum aurantiacum (Leccinum quercinum)", "alto",
  ["Sombrero de 5-15 cm, naranja rojizo.",
   "Tubos con poros muy pequeños, blanquecinos, que se manchan de pardo oliva al tocarlos.",
   "Pie de 8-16 cm de alto y 2-3 cm de grosor, blanquecino, cubierto de pequeñas escamas rígidas que se vuelven de pardas a negras con la edad; azulea verdoso al tocarlo.",
   "Carne blanca que primero se vuelve burdeos y luego gris o negro púrpura; al cocinarla se pone muy oscura. Con álamo (tradicionalmente) y también con roble, haya, abedul, castaño, sauce y tilo; verano y otoño."],
  ["Carne que azulea con intensidad.", "Pie sin escamas rígidas."],
  [("Leccinum albostipitatum", None, "crece con álamo temblón y tiene escamas blancas en el pie."),
   ("Leccinum vulpinum", None, "crece bajo pinos y piceas, en bosques de coníferas."),
   ("Leccinum versipelle", None, "Wikipedia la cita como parecida sin decir cómo separarlas.")],
  "Europa y América del Norte. Wikipedia dice que se considera comestible pero que si no se cocina muy bien puede causar vómitos u otros efectos; que algunas personas tienen molestias digestivas, que se ha comunicado al menos una muerte ligada a esta especie y que algunos consideran los Leccinum posiblemente no seguros. La Enciclopèdia Catalana la valora «bo» con el nombre «abró».",
  dict(s_color="naranja rojo", s_forma="convexo", h_tipo="!poros", h_color="blanco pardo", p_color="blanco", p_super="puntos", corte="enrojece", habitat="planifolio", s_tam="mediano grande"),
  ca=["abró"], ca_f="EC")

F("leccinum-versipelle", "Leccinum versipelle", "medio",
  ["Sombrero de hasta 15 cm, de ante a amarillo anaranjado o rojo ladrillo, ampliamente convexo y aterciopelado.",
   "Poros muy pequeños (unos 0,5 mm), gris blanquecino a gris ocre; tubos de 8-22 mm, amarillo blanquecino a gris pardo; se manchan de pardo al tocarlos.",
   "Pie de hasta 15 cm, blanquecino, cubierto de finas escamas grisáceas a negruzcas (más gruesas en la base), con puntos negros elevados.",
   "Carne blanca a rosada que enrojece al cortarla, luego se pone ante y por fin pardo oscuro; al cocinarla se vuelve negra. Solo con abedul, en bosques y brezales de suelo arenoso y algo ácido; de julio a noviembre."],
  ["Seta bajo coníferas (no con abedul).", "Pie sin escamas."],
  [("Leccinum aurantiacum y L. albostipitatum", None, "emparentadas, con otros árboles asociados.")],
  "Toda Europa, y se recoge en Finlandia, los países bálticos, Bielorrusia y Rusia. Wikipedia dice que «puede ser comestible con la preparación adecuada», y que es levemente tóxica (náuseas y vómitos) si no se cuece bien; esta guía no da instrucciones de cocinado. La Enciclopèdia Catalana la valora «bo» con el nombre «molleric de peu raspós».",
  dict(s_color="naranja rojo pardo", s_forma="convexo", h_tipo="!poros", h_color="blanco gris", p_color="blanco", p_super="puntos", corte="enrojece", habitat="planifolio", s_tam="grande"),
  ca=["molleric de peu raspós"], ca_f="EC")

F("leccinum-scabrum", "Leccinum scabrum", "medio",
  ["Sombrero de 4-10 cm, canela o pardusco, normalmente con el borde más claro; convexo y luego plano, liso, sin pelillos, de seco a algo viscoso.",
   "Poros blanquecinos de joven y grises después; la capa de tubos se separa fácil de la cutícula; alrededor del pie los poros se hunden de forma marcada.",
   "Pie de 5-15 cm de alto y 1-3,5 cm de ancho, esbelto y más fino hacia arriba, con escamas blancas y negras a oscuras.",
   "Carne blanquecina, firme de joven y pronto esponjosa y empapada; a veces se oscurece; al cocinarla se vuelve negra. Solo en micorriza con abedul, también en ciudades; en Europa y otras zonas del hemisferio norte."],
  ["Seta bajo árboles que no sean abedul.", "Pie sin escamas."],
  [("Leccinum holopus", None, "más pálida, blanquecina en todas sus partes."),
   ("Leccinum variicolor", None, "con el pie azulado."),
   ("Leccinum oxydabile", None, "de carne más firme y rosada.")],
  "Wikipedia dice que es comestible si se usan solo ejemplares firmes y bien cocinados, y que algunas guías no la consideran digna de recoger.",
  dict(s_color="pardo", s_super="lisa", s_forma="convexo", h_tipo="!poros", h_color="blanco gris", p_color="blanco", p_super="puntos", habitat="planifolio", s_tam="mediano"))

P("caloboletus-calopus", "Caloboletus calopus", "nocom",
  ["Sombrero de hasta 15 cm, beis a oliva, casi globoso de joven, luego semiesférico y convexo, liso o con pelillos mínimos.",
   "Poros de amarillo pálido a amarillo oliva, que azulean enseguida; tubos de hasta 2 cm; esporada oliva a pardo oliva.",
   "Pie de 7-15 cm de alto y 2-5 cm de grosor, amarillo arriba y rosa rojizo debajo (a veces todo rojizo), con una red de color paja cerca de lo alto.",
   "Carne amarillo pálido que azulea, con olor fuerte a tinta y sabor muy amargo que no se quita al cocinarla. En bosques de coníferas y de planifolios, sobre todo bajo hayas y robles, a menudo en altura."],
  "Con Suillellus luridus (los ejemplares grandes y pálidos se le parecen), Rubroboletus satanas (sombrero parecido pero poros rojos), Boletus edulis (comestible, sin pie rojo), Caloboletus radicans (también no comestible, sin rojo en el pie) y Xerocomellus chrysenteron en mal estado (pie sin red). Wikipedia dice que normalmente no se considera comestible por su sabor muy amargo y que la variedad frustosus causa enfermedad grave en Europa. La Enciclopèdia Catalana la pone «a refusar».",
  dict(s_color="gris pardo verde", s_forma="convexo", h_tipo="!poros", h_color="amarillo verde", p_color="amarillo rojo", p_super="red", corte="!azulea", habitat="conifera planifolio", s_tam="grande"),
  ca=["mataparent amarg"], ca_f="EC")

P("chalciporus-piperatus", "Chalciporus piperatus", "nocom",
  ["Sombrero de 1,6-9 cm, naranja ante, convexo y luego aplanado; puede tener surcos, es brillante en seco, algo pegajoso con humedad y se agrieta con la edad.",
   "Poros angulosos de 0,5-2 mm, canela a pardos de jóvenes y de amarillentos a pardo rojizo oscuro al madurar; tubos de 3-10 mm; se manchan de pardo al tocarlos.",
   "Pie de 4-9,5 cm de alto y 0,6-1,2 cm de grosor, del color del sombrero o más claro, con micelio amarillo en la base.",
   "Carne amarilla (a veces con tonos rojizos), sin olor y de sabor muy picante; esporada parda a canela. En el suelo, en o junto a bosques de coníferas, hayas o robles, a menudo en suelo arenoso y junto a la amanita muscaria; en Europa, de agosto a noviembre."],
  "Con Chalciporus piperatoides (de Norteamérica, la carne y los poros azulean y es menos picante), C. rubinellus (colores más vivos, tubos totalmente rojos y sabor suave) y C. rubinus (poros rojos y pie con puntos rojos). Wikipedia dice que normalmente se considera no comestible y que contiene toxinas; esta guía no te la recomienda. La Enciclopèdia Catalana la pone «a refusar» con el nombre «pebreta».",
  dict(s_color="naranja pardo", s_forma="convexo", h_tipo="!poros", h_color="pardo naranja", p_color="naranja pardo", habitat="conifera planifolio", s_tam="pequeno mediano"),
  ca=["pebreta"], ca_f="EC")

F("imleria-badia", "Imleria badia (Boletus badius, Xerocomus badius)", "medio",
  ["Sombrero de 4-15 cm, castaño a pardo oscuro, casi esférico de joven y luego más ancho y plano; aterciopelado de joven y algo pegajoso con humedad o de viejo.",
   "Tubos y poros crema a amarillo pálido de jóvenes y amarillo verdosos u oliva con la edad, circulares y luego angulosos; se vuelven azul apagado a azul grisáceo al magullarlos.",
   "Pie de 4-9 cm de alto y 1-2 cm de grosor, parecido al sombrero pero más pálido (a veces con tinte rosa), liso, con estrías muy tenues y una red fina en lo alto.",
   "Carne blanquecina o amarillenta, firme de joven, que se tiñe de azul pálido de forma leve y poco persistente; olor afrutado. Sobre todo en bosques de coníferas (pino, pícea) y también bajo hayas; no en suelos calizos; de julio a noviembre."],
  ["Poros rojos o naranjas.", "Sabor amargo.", "Pie con red marcada y gruesa en todo el pie."],
  [("Boletus subtomentosus", None, "con el pie más fino, el sombrero pardo más pálido y poros mayores que no azulean."),
   ("Xerocomus bubalinus", None, "sombrero amarillo pardo más pálido con un tinte rojo rosado, y no pegajoso con humedad."),
   ("Boletus projectellus", None, "más robusto, con el pie reticulado y las esporas mayores de la familia.")],
  "Casi toda Europa (de las islas Británicas al mar Negro), Asia y América del Norte; Wikipedia dice que se vende en mercados de Europa y México y la da como comestible «selecta» según algunos (Carluccio) y «pariente pobre del cep» según otros; puede causar reacción alérgica en algunas personas.",
  dict(s_color="pardo", s_super="lisa", s_forma="convexo", h_tipo="!poros", h_color="amarillo verde", p_color="pardo", p_super="lisa", corte="azulea", habitat="conifera planifolio", s_tam="mediano grande"))

F("xerocomus-subtomentosus", "Xerocomus subtomentosus (Boletus subtomentosus)", "medio",
  ["Sombrero de 4-10 cm (excepcionalmente 20), oliva pálido o ante, convexo y luego aplanado, aterciopelado y a veces agrietado dejando ver la carne amarilla; la cutícula es difícil de pelar.",
   "Tubos y poros amarillos, que pueden pasar a azul o verde al tocarlos y luego se atenúan.",
   "Pie de hasta 12 cm de alto y 1-2 cm de ancho, sin anillo.",
   "Carne blanca, con poco olor y poco sabor; esporada pardo oliva. Con muchos árboles de hoja ancha y coníferas, en otoño, y asociada a arándanos y brezos."],
  ["Poros rojos o naranjas.", "Sabor amargo.", "Pie con anillo."],
  [("Xerocomus silwoodensis", None, "sombrero pardo rojizo más oscuro, prefiere chopos y la carne amarillea al aire."),
   ("Xerocomus ferrugineus", None, "solo bajo coníferas, con micelio amarillo."),
   ("Xerocomus chrysonemus", None, "carne y micelio de amarillo vivo.")],
  "Eurasia, América del Norte y Australia. Wikipedia dice que es comestible aunque poco apreciada, de sabor suave que va bien en platos de varias setas; la llaman también «el boleto pardo aburrido» (David Arora).",
  dict(s_color="pardo verde amarillo", s_forma="convexo", h_tipo="!poros", h_color="amarillo", p_anillo="no", corte="azulea", habitat="conifera planifolio", s_tam="mediano"))

F("xerocomellus-chrysenteron", "Xerocomellus chrysenteron (Boletus chrysenteron)", "bajo",
  ["Sombrero de 4-10 cm, pardusco, convexo y luego plano; de joven aterciopelado, que se agrieta y deja ver una carne rojiza fina.",
   "Poros grandes, amarillos y angulosos, que se desintegran pronto tras cogerla; tubos y poros azulean al magullarlos.",
   "Pie de 4-13 cm de alto y 1-2 cm de grosor, de un amarillo vivo con fibrillas de rojo coral en la parte baja; sin anillo.",
   "La carne del sombrero es fina y de color rojo claro en las grietas, y la del pie, crema, y azulea al cortarla. En bosques de planifolios y de coníferas, suelta o en pequeños grupos, de principios de verano a mediados de invierno."],
  ["Pie con anillo.", "Carne que no azulea al cortarla.", "Poros rojos."],
  [("Boletus pruinatus y Hortiboletus rubellus", None, "hay formas intermedias; sin microscopio no es segura la identificación."),
   ("Boletus porosporus", None, "con la capa inferior blanquecina y esporas truncadas."),
   ("Imleria badia", None, "sombrero parecido; Wikipedia no dice cómo separarlas.")],
  "Zonas templadas del hemisferio norte. Wikipedia dice que es comestible «pero no selecta», por su sabor soso y su carne blanda. La Enciclopèdia Catalana la valora «acceptable» con el nombre «mataparent de carn groga».",
  dict(s_color="pardo", s_forma="convexo", h_tipo="!poros", h_color="amarillo", p_anillo="no", p_color="amarillo rojo", corte="azulea", habitat="planifolio conifera", s_tam="mediano"),
  ca=["mataparent de carn groga"], ca_f="EC")

F("hortiboletus-rubellus", "Hortiboletus rubellus (Boletus rubellus, Xerocomus rubellus)", "medio",
  ["Sombrero que rara vez pasa de 6 cm, escarlata a frambuesa de joven, seco y aterciopelado, que a menudo se agrieta con la edad; el borde suele llevar una banda amarillo pálido o blanca. Se oscurece y ensucia con la edad.",
   "Poros amarillo pálido a amarillo limón (a veces verdosos de viejos) que azulean despacio al tocarlos.",
   "Pie largo y delgado de hasta 7,5 cm, amarillo limón arriba y rojo en el resto, que tiende a partirse a lo largo.",
   "Carne pajiza en el sombrero y amarilla en el pie, que azulea al cortarla; olor agradable pero poco marcado y sabor «ligeramente a jabón». En bosques de planifolios (sobre todo robles), en otoño."],
  ["Poros rojos.", "Pie con anillo.", "Sombrero de gran tamaño."],
  [("Baorangia bicolor", None, "Wikipedia la da como «casi idéntica» y no dice cómo separarlas."),
   ("Xerocomus armeniacus", None, "se confunde a menudo con ella en Europa; no tiene rojo en la base del pie."),
   ("Xerocomellus chrysenteron y Hortiboletus coccyginus", None, "figuran como parecidas sin explicación.")],
  "Europa, este de Estados Unidos y Canadá; poco común o rara en el sur de Inglaterra. Wikipedia dice que se cita como comestible pero a menudo agusanada y «de baja calidad, con sabor a jabón»; y que hay dudas sobre su comestibilidad. La Enciclopèdia Catalana la valora «acceptable» con el nombre «mataparent de carn groga».",
  dict(s_color="rojo", s_forma="convexo", h_tipo="!poros", h_color="amarillo", p_color="amarillo rojo", corte="azulea", habitat="planifolio", s_tam="pequeno"),
  ca=["mataparent de carn groga"], ca_f="EC")

P("tapinella-atrotomentosa", "Tapinella atrotomentosa (Paxillus atrotomentosus)", "toxica",
  ["Sombrero de hasta 20 cm, pardo sepia o nogal, con el borde enrollado y el centro hundido.",
   "Debajo, láminas (no poros) crema amarillentas y bifurcadas.",
   "Pie de hasta 12 cm, grueso, pardo oscuro con una cubierta aterciopelada pardo oscura, que sale hacia un lado (descentrado).",
   "Carne amarillenta de sabor acre. Saprofita sobre tocones de coníferas; verano y otoño, incluso en épocas secas."],
  "Con las setas del género Paxillus, que se separan porque crecen en madera, tienen esporas mucho menores, no tienen cistidios y su pie no está descentrado; y con Tapinella panuoides, del mismo género. Wikipedia dice que no se considera comestible: contiene toxinas que pueden causar molestias digestivas; los jóvenes se tendrían por comestibles y los viejos por posiblemente venenosos (Zeitlmayr); en partes de Europa oriental se usa como alimento, pero es indigesta para muchos; esta guía no te la recomienda.",
  dict(s_color="pardo", s_forma="embudo", h_tipo="!laminas", h_color="amarillo", p_color="pardo negro", habitat="conifera madera", s_tam="grande"))

F("suillus-bellinii", "Suillus bellinii", "bajo",
  ["Sombrero de hasta 15 cm, convexo e irregular de joven y aplanado después; cutícula parda gruesa jaspeada de blanco a gris hacia el borde, muy viscosa con humedad y que se pela fácil.",
   "Debajo, tubos cortos con poros pequeños, blanquecinos, beis y amarillentos con la madurez; los ejemplares frescos pueden soltar un látex rojizo.",
   "Pie corto y cilíndrico, blanquecino, con puntos rojizos.",
   "Carne firme y blanquecina, amarillenta en la base del pie; olor afrutado y sabor agradable; una gota de amoníaco la tiñe de carmesí. En pinares costeros mediterráneos (pino carrasco, marítimo y piñonero); amante del calor."],
  ["Carne amarilla (sería Suillus mediterraneensis).", "Pie con anillo."],
  [("Suillus mediterraneensis", None, "comparte hábitat; su carne es amarilla.")],
  "Pinares costeros del Mediterráneo del sur de Europa. Wikipedia dice que se considera comestible y que se recomienda quitar la cutícula viscosa; la Enciclopèdia Catalana la valora «acceptable» (con los nombres genéricos de los Suillus).",
  dict(s_color="pardo gris blanco", s_super="viscosa", s_forma="convexo", h_tipo="!poros", h_color="blanco amarillo", p_color="blanco", p_super="puntos", habitat="conifera", s_tam="grande"))

F("suillus-collinitus", "Suillus collinitus", "bajo",
  ["Sombrero de hasta 11 cm, rojizo a pardo castaño, redondeado y luego convexo y plano, con estrías radiales finas y viscoso con humedad; a menudo de forma irregular.",
   "Debajo, poros pequeños y angulosos, amarillo vivo de joven y pardo verdoso con la edad; los ejemplares jóvenes pueden tener gotitas de líquido claro.",
   "Pie cilíndrico, corto y rechoncho (4-7 cm de alto y 1-2 de grosor), amarillento con escasos gránulos pardo rojizos, SIN anillo; la base tiene un tono rosado y se une a hilos de micelio rosados.",
   "Carne amarillenta, gruesa y blanda, que se pone rojiza con amoníaco; olor agrio. En pinares europeos con pinos de dos agujas (sobre todo carrasco), en suelos calizos; común en el sur de Europa."],
  ["Pie con anillo.", "Micelio blanco en la base del pie (sería Suillus granulatus)."],
  [("Suillus granulatus", None, "tiene el sombrero pardo uniforme sin estrías y el micelio blanco; esta lo tiene rosa.")],
  "Wikipedia dice que varios autores la consideran comestible y aconseja recoger solo ejemplares jóvenes y pelar la cutícula; la Enciclopèdia Catalana la valora «acceptable» (con los nombres genéricos de los Suillus).",
  dict(s_color="pardo rojo", s_super="viscosa", s_forma="convexo", h_tipo="!poros", h_color="amarillo verde", p_anillo="!no", p_color="amarillo", p_super="puntos", habitat="conifera", s_tam="mediano grande"))

F("suillus-bovinus", "Suillus bovinus", "bajo",
  ["Sombrero de 3-10 cm, gris amarillento u ocre, a veces con tinte rosado; convexo y luego plano con el borde ondulado, de piel pegajosa.",
   "Debajo, poros generalmente decurrentes (bajan por el pie), gris a amarillo oliva, en dos capas: poros angulosos gruesos sobre otros más finos.",
   "Pie de 4-6 cm de alto y 0,5-0,8 cm de ancho, del color del sombrero y más fino hacia abajo, SIN anillo.",
   "Carne blanquecina a amarillenta o arcillosa, esponjosa y como de goma; a veces enrosa al magullarla; olor afrutado y sabor suave. En pinares y repoblaciones de pinos, a menudo en gran número."],
  ["Pie con anillo.", "Sombrero granuloso (sería Suillus variegatus)."],
  [("Suillus variegatus", None, "suele crecer en los mismos sitios pero tiene el sombrero granuloso y los poros oliva oscuro, más pequeños y no decurrentes, que pueden azulear.")],
  "Eurasia, e introducida en Norteamérica, Australia, Nueva Zelanda y Sudáfrica. Wikipedia dice que es comestible pero poco apreciada; los ejemplares viejos son casi inservibles por su textura y los gusanos. La Enciclopèdia Catalana la pone «a refusar» con el nombre «molleric de bou».",
  dict(s_color="amarillo pardo rosa", s_super="viscosa", s_forma="convexo", h_tipo="!poros", h_color="amarillo verde", p_anillo="!no", p_color="amarillo pardo", habitat="conifera", s_tam="pequeno mediano"),
  ca=["molleric de bou"], ca_f="EC")

F("suillus-variegatus", "Suillus variegatus", "bajo",
  ["Sombrero de 6-13 cm, de color óxido a leonado u ocre, aterciopelado de joven y luego más liso y grasiento, pegajoso con tiempo húmedo.",
   "Debajo, tubos con poros ocre que pasan a canela.",
   "Pie ocre, más amarillo arriba y a veces con tinte óxido en la base, a veces algo hinchado.",
   "Carne amarillo limón pálido que puede azular muy poco al cortarla; olor que recuerda a la esclerodermia y sabor algo metálico. Con pinos de dos agujas, a finales de verano, a menudo con brezos en suelos arenosos."],
  ["Sombrero y pie violetas o azules."],
  [("Suillus bovinus", None, "tiene los poros más grandes y decurrentes, y el sombrero gris amarillento viscoso.")],
  "Europa, Asia occidental y América del Norte. Wikipedia dice que es comestible pero que se le atribuye un olor desagradable y un sabor algo metálico. La Enciclopèdia Catalana la pone «a refusar» con el nombre «mataparent clapat».",
  dict(s_color="naranja pardo amarillo", s_forma="convexo", h_tipo="!poros", h_color="amarillo pardo", p_color="amarillo pardo", corte="nada azulea", habitat="conifera", s_tam="mediano grande"),
  ca=["mataparent clapat"], ca_f="EC")

F("gomphidius-glutinosus", "Gomphidius glutinosus", "medio",
  ["Sombrero de 3-12 cm, púrpura oscuro apagado, pardusco o grisáceo, con manchas negruzcas; convexo y luego aplanado, con un mamelón central y el borde enrollado; liso y pegajoso.",
   "Debajo, láminas (no poros) separadas, a veces ramificadas, decurrentes (bajan por el pie): blanquecinas de jóvenes, grises y por fin negras con las esporas.",
   "Pie de 4-10 cm de alto y 0,7-2 cm de ancho, blanco con la base amarilla y un anillo indistinto (solo restos de hilos del velo); cubierto de baba cuando es joven.",
   "Carne blanquecina, a veces con tinte vino, de olor y sabor casi nulos. Bajo coníferas (abeto, pícea, pino), en bosques naturales y plantaciones; otoño. Parece parásita de los boletos de micorriza."],
  ["Poros en lugar de láminas (sería un Suillus).", "Láminas amarillas que no se separan del sombrero (así es Hygrophorus hypothejus)."],
  [("Suillus luteus", None, "los ejemplares pardos se le parecen; mirando debajo del sombrero, esta tiene láminas y el Suillus tiene poros."),
   ("Hygrophorus hypothejus", None, "mismo hábitat, con las láminas amarillas que no se separan del sombrero."),
   ("Gomphidius smithii", None, "norteamericana, con el sombrero púrpura pálido a color vino.")],
  "Europa y América del Norte hasta 2.900 m. Wikipedia dice que las opiniones sobre su valor en la mesa están divididas y que acumula metales pesados. La Enciclopèdia Catalana la valora «bo» con el nombre «cama de perdiu mucosa».",
  dict(s_color="violeta pardo gris", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco gris", p_anillo="si", p_color="blanco amarillo", esporada="negra", habitat="conifera", s_tam="mediano"),
  ca=["cama de perdiu mucosa"], ca_f="EC")

F("porphyrellus-porphyrosporus", "Porphyrellus porphyrosporus", "medio",
  ["Sombrero de 6-15 cm, pardo oscuro a pardo púrpura, convexo.",
   "Debajo, tubos del color del sombrero, que pasan a azul verdoso al cortarlos o magullarlos.",
   "Pie de 5-16 cm de alto y 1-3 cm de ancho, pardo tabaco, algo aterciopelado de joven y liso después.",
   "Carne blanda ante con tinte vinoso en el sombrero y blanca en el pie, que da manchas azules cambiantes; olor de suave a penetrante y sabor de suave a amargo. Bajo planifolios (hayas, robles), en grupos pequeños, de finales de verano a otoño."],
  ["Poros de otro color que no sea pardo o grisáceo.", "Sabor muy amargo."],
  [("Porphyrellus atrofuscus y P. olivaceobrunneus", None, "Wikipedia dice que pueden solaparse con ella."),
   ("Tylopilus griseocarneus y T. indecisus", None, "parecidos; Wikipedia no dice cómo separarlos.")],
  "Europa (sobre todo el norte) y América del Norte. Wikipedia dice que una guía la da como «comestible» y otra como «probablemente comestible».",
  dict(s_color="pardo violeta", s_forma="convexo", h_tipo="!poros", h_color="pardo", p_color="pardo", corte="azulea", habitat="planifolio", s_tam="grande"))

F("phylloporus-rhodoxanthus", "Phylloporus rhodoxanthus", "bajo",
  ["Sombrero de 2-12 cm, rojo apagado a pardo rojizo, amarillo rojizo u oliva pardusco, convexo y luego aplanado, a veces hundido; seco, algo aterciopelado, agrietado en la madurez.",
   "Debajo, láminas (no poros) de amarillo intenso, algo decurrentes y separadas, que se manchan de verdoso a pardusco; a menudo arrugadas y con venas transversales que recuerdan poros.",
   "Pie de 4-10 cm de largo, cilíndrico, amarillo, macizo (no hueco), con surcos que bajan desde las láminas.",
   "Carne amarillo pálido, sin olor ni sabor claro. En bosques de robles y hayas, suelta o en pequeños grupos; julio a octubre."],
  ["Poros en lugar de láminas."],
  [("Phylloporus leucomycelinus y otros Phylloporus norteamericanos", None, "Wikipedia las cita: la primera tiene micelio blanco en la base del pie.")],
  "Datos de América del Norte (Wikipedia no cita Europa). Wikipedia dice que es comestible y «buena según algunos», de sabor «tierno y a nuez».",
  dict(s_color="rojo pardo verde", s_forma="convexo", h_tipo="!laminas", h_color="amarillo", p_color="amarillo", interior="macizo", habitat="planifolio", s_tam="mediano"))

F("strobilomyces-strobilaceus", "Strobilomyces strobilaceus (S. floccopus)", "bajo",
  ["Sombrero de 4-11 cm, convexo con el borde enrollado y peludo, cubierto de escamas erguidas en mechones, gris oscuro a pardo.",
   "Debajo, poros gris claro que se vuelven negruzcos con la edad.",
   "Pie de hasta 14 cm de alto y 2 de grosor, del color del sombrero, lanoso, con un anillo grueso y ascendente o solo bandas de color del velo.",
   "Carne gruesa, al principio blanca, que se tiñe de rosa y luego de negruzco al cortarla; esporada negruzca. En bosques de planifolios y coníferas, bajo robles y hayas, de julio a octubre."],
  ["Sombrero liso, sin escamas.", "Poros amarillos."],
  [("Strobilomyces confusus", None, "sombrero algo menor, con escamas más pequeñas y rígidas."),
   ("Strobilomyces dryophilus", None, "con el sombrero gris rosado a rosado ante.")],
  "Hayedos y robledales de Europa, Asia (Irán, Taiwán) y este de América del Norte. Wikipedia no da ningún dato de comestibilidad; la Enciclopèdia Catalana la pone «a refusar» con el nombre «cep de pinya».",
  dict(s_color="gris pardo negro", s_super="escamas", s_forma="convexo", h_tipo="!poros", h_color="gris", p_anillo="si", p_color="gris pardo", corte="enrojece", habitat="planifolio", s_tam="mediano"),
  ca=["cep de pinya"], ca_f="EC")

F("gyrodon-lividus", "Gyrodon lividus (Gyrodon rompelii)", "bajo",
  ["Sombrero de 4-10 cm, pardo pálido, ante u ocre, convexo y pegajoso con humedad.",
   "Debajo, poros grandes, amarillo vivo y decurrentes (bajan por el pie), que se ponen azul grisáceo al cortarlos o magullarlos; esporada pardo oliva.",
   "Pie de 3-7 cm de alto y 1-2 cm de ancho, SIN anillo, primero del color del sombrero y luego pardo rojizo.",
   "Carne fina y amarillo pálido, sin olor ni sabor claros. Solo en micorriza con aliso, suelto o en grupos; otoño."],
  ["Pie con anillo.", "Seta fuera de alisedas."],
  [("Boletinellus merulioides", None, "Wikipedia la cita (en EE. UU.): suele ser mayor, con esporas mayores y bajo fresno.")],
  "Europa, China, Japón y California. Wikipedia dice que algunos autores la dan por comestible y otros por no comestible; la Enciclopèdia Catalana la pone «a refusar» con el nombre «bolet lívid».",
  dict(s_color="pardo amarillo", s_super="viscosa", s_forma="convexo", h_tipo="!poros", h_color="amarillo", p_anillo="!no", p_color="pardo", corte="azulea", habitat="planifolio", s_tam="mediano"),
  ca=["bolet lívid"], ca_f="EC")

P("hygrophoropsis-aurantiaca", "Hygrophoropsis aurantiaca", "toxica",
  ["Sombrero de 2-10 cm, naranja dorado, convexo y luego en embudo, con el borde algo enrollado y luego ondulado; cubierto de pelusa fina, como fieltro.",
   "Láminas «como de rossinyol»: decurrentes, estrechas, apretadas y a menudo bifurcadas, de naranja azafrán, más intensas que el sombrero.",
   "Pie de 1,5-8 cm de alto y 0,5-1 cm de grosor, naranja con la base a menudo pardusca, sin anillo, liso y a menudo descentrado.",
   "Carne blanda y fina, de blanca a amarillenta o naranja dorado, de olor poco claro o «desagradable y terroso». En bosques y brezales, sobre el suelo o madera podrida, restos de quemas y astillas; verano y otoño."],
  "Con el rossinyol (Cantharellus cibarius): este es de un naranja más intenso, con la base del pie parda, sombrero aterciopelado, láminas bifurcadas (no pliegues), carne más blanda y fina y sin olor a albaricoque. Wikipedia lo trata como «considerado venenoso» y «puede causar problemas digestivos graves»; Wikipedia añade que fue descrito como comestible hasta 1999 y que se vende legalmente en Francia y Bélgica, pero que en Italia no se recomienda; por esa discrepancia, esta guía no te la recomienda. La Enciclopèdia Catalana la pone «a refusar» con el nombre «rossinyol ataronjat».",
  dict(s_color="naranja amarillo", s_super="fibrosa", s_forma="embudo", h_tipo="!laminas", h_color="naranja amarillo", p_anillo="!no", p_color="naranja pardo", p_super="lisa", esporada="blanca", habitat="conifera planifolio madera", s_tam="pequeno mediano"),
  ca=["rossinyol ataronjat"], ca_f="EC")

F("boletopsis-leucomelaena", "Boletopsis leucomelaena", "bajo",
  ["Sombrero de 4-10 cm, gris sepia o pardo negruzco, a veces con un tinte magenta; redondeado y luego plano, liso y mate, con pequeñas escamas en el centro de los viejos.",
   "Debajo, poros crema que pasan a gris lila pálido o gris humo y se ponen rosados al magullarlos; capa de tubos fina (1-2 mm).",
   "Pie de 3-10 cm de alto y 1-2,5 cm de ancho, cilíndrico o más fino hacia la base, crema de joven y pardo grisáceo pálido al madurar.",
   "Carne blanda y carnosa, crema que se vuelve gris lila al cortarla. En grupos densos de 3 a 10, en bosques con predominio de pícea; de finales de julio a octubre en el norte de Europa."],
  ["Seta con láminas.", "Poros amarillos."],
  [("Boletopsis grisea", None, "sombrero gris plateado a gris pardo sucio, más dura (se desgarra en radios en fresco), más ancha que alta y en pinares pobres y secos.")],
  "Costa noroeste de América del Norte, Japón y Europa (rara). Wikipedia no da datos de comestibilidad; la Enciclopèdia Catalana la pone «a refusar» con el nombre «mariner».",
  dict(s_color="gris pardo negro", s_super="lisa", s_forma="convexo", h_tipo="!poros", h_color="blanco gris", p_color="blanco gris pardo", grupo="mechon", habitat="conifera", s_tam="mediano"),
  ca=["mariner"], ca_f="EC")

F("cortinarius-caperatus", "Cortinarius caperatus (Rozites caperatus)", "alto",
  ["Sombrero de 5-12 cm, beis a pardo ocre (puede tener un tinte lila de joven), convexo y luego aplanado con un mamelón central; cubierto de fibras blanquecinas, arrugado y surcado.",
   "Debajo, láminas (no poros) color arcilla.",
   "Pie de 4-12 cm de alto y 1-2,2 cm de grosor, blanquecino a beis, algo hinchado en la base, CON un anillo blanquecino que de joven está pegado al sombrero.",
   "Carne crema, de olor y sabor suaves; esporada ocre pardo. En bosques de coníferas y hayas y en brezales, sobre suelos ácidos y arenosos; agosto a octubre en Europa."],
  ["Pie sin anillo.", "Sombrero liso, sin arrugas ni fibras blancas.", "Olor desagradable."],
  [("Inosperma erubescens", "mortal", "Wikipedia la cita como muy venenosa y dice que se confunde con ejemplares viejos en Europa central en verano; no da cómo separarlas."),
   ("Cortinarius traganus", "nocom", "no comestible; se confunde con ejemplares jóvenes y se distingue por su olor desagradable."),
   ("Agrocybe praecox", None, "no tiene el sombrero arrugado y crece en zonas cultivadas."),
   ("Phaeolepiota aurea", None, "tiene la superficie polvorienta-granulosa."),
   ("Cortinarius corrugatus", None, "sombrero arrugado pero sin anillo.")],
  "Norte de Europa (común en Escandinavia), norte de América del Norte y Asia templada. Wikipedia dice que es «una especie comestible muy apreciada por los recolectores europeos» (quitar los pies duros) y que acumula mercurio y cesio radiactivo y suele traer gusanos; la Enciclopèdia Catalana la valora «bo» con el nombre «foliota arrugada». El parecido con una especie muy venenosa es la razón del riesgo alto.",
  dict(s_color="pardo amarillo", s_super="fibrosa", s_forma="convexo", h_tipo="!laminas", h_color="pardo", p_anillo="!si", p_color="blanco pardo", esporada="marron", habitat="conifera planifolio", s_tam="mediano grande"),
  ca=["foliota arrugada"], ca_f="EC")

F("cortinarius-praestans", "Cortinarius praestans", "alto",
  ["Sombrero de 10-20 cm, castaño o chocolate con tinte violeta cobrizo, convexo, a menudo surcado en el borde enrollado; con fibrillas claras y restos del velo que parecen escamitas pegadas.",
   "Debajo, láminas (no poros) apretadas, de borde ondulado: blanquecinas con tinte amatista de jóvenes, luego crema arcilla a color óxido.",
   "Pie de hasta 15 cm de alto y 3-5 cm de grosor, macizo, sedoso-fibroso, blanquecino violáceo de muy joven y luego blanquecino con violeta arriba, con un bulbo en forma de maza en la base; cortina sedosa (no un anillo claro).",
   "Carne gruesa y blanquecina, sin olor y de sabor suave; esporada ocre óxido. En bosques de planifolios, sobre todo en suelos calizos; común en Europa occidental."],
  ["Sombrero pequeño (la especie es grande, 10-20 cm).", "Olor claro."],
  [("Cortinarius berkeleyi y C. torvus var. berkeleyi", None, "Wikipedia los cita solo como sinónimos de esta especie.")],
  "Wikipedia dice que «se considera una buena especie comestible» y que en Hungría está protegida por ley desde 2005 (recogerla es sancionable); la Enciclopèdia Catalana la valora «bo» con el nombre «cortinari gros». Wikipedia no cita especies parecidas, pero el género Cortinarius es enorme y difícil de separar sin microscopio, y por eso el riesgo se marca alto.",
  dict(s_color="pardo violeta", s_super="fibrosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco violeta pardo", p_color="blanco violeta", p_base="ensanchada", interior="macizo", esporada="marron", habitat="planifolio", s_tam="grande"),
  ca=["cortinari gros"], ca_f="EC")

P("cortinarius-trivialis", "Cortinarius trivialis", "nocom",
  ["Sombrero de 3-12 cm, gris azulado y luego pardo amarillento, convexo a plano, a veces con un mamelón suave.",
   "Debajo, láminas (no poros) pegadas, gris azuladas y luego pardas al madurar las esporas.",
   "Pie de 5-15 cm de alto y 1-2 cm de ancho, igual o más fino hacia abajo, blanco a amarillo, con un velo parcial blanquecino en la parte alta que se vuelve pardo con las esporas.",
   "Wikipedia no da color de la carne, olor, sabor ni hábitat."],
  "Con Cortinarius cliduchus y C. collinitus (Wikipedia no dice cómo separarlas). Wikipedia la describe como «hongo no comestible»: se dio por comestible todavía en 1991, pero las guías europeas la consideran venenosa. La Enciclopèdia Catalana la pone «a refusar» con el nombre «llenega borda».",
  dict(s_color="gris pardo amarillo", s_forma="convexo", h_tipo="!laminas", h_color="gris pardo", p_color="blanco amarillo"),
  ca=["llenega borda"], ca_f="EC")

F("cortinarius-purpurascens", "Cortinarius purpurascens", "alto",
  ["Sombrero de 3-10 cm, pardo apagado u ocre en el centro, a veces gris azulado, con el borde violeta o gris pardusco; pegajoso (viscoso), liso, con pequeñas motas viscosas del color del sombrero.",
   "Debajo, láminas (no poros) finas y apretadas, escotadas, violeta oscuro de jóvenes.",
   "Pie cilíndrico por debajo de un bulbo de 3-4 cm de ancho con el borde marcado, violeta vivo y luego violeta pardo; cortina violeta (no anillo claro); macizo.",
   "Carne violeta lila que se pone púrpura al romperla, de olor débil y desagradable y sabor suave; esporada pardo rojiza a pardo claro. En grupos en bosques de coníferas, sobre todo en suelos ácidos; bastante rara."],
  ["Carne que no cambia de color.", "Láminas que no son violetas de jóvenes."],
  [("Collybia nuda (Lepista nuda)", None, "Wikipedia solo dice que tiene un tinte violeta parecido; no da cómo separarlas (la esporada de la lepista es rosa pálido, no pardo rojiza)."),
   ("Cortinarius eumarginatus, C. occidentalis y C. subpurpurascens", None, "separadas de las variantes de esta especie; Wikipedia no da cómo distinguirlas.")],
  "Hemisferio norte templado (Europa y América del Norte). Wikipedia dice que es «una seta comestible de calidad media». Con tantos Cortinarius violetas parecidos, el riesgo se marca alto.",
  dict(s_color="pardo violeta", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="violeta", p_color="violeta", p_base="ensanchada", interior="macizo", corte="nada", esporada="marron", habitat="conifera", s_tam="mediano"))

P("cortinarius-infractus", "Cortinarius infractus", "nocom",
  ["Sombrero de 4-13 cm, amarillo oliváceo sucio a pardo oliva o gris verdoso, convexo y luego deprimido, liso y pegajoso.",
   "Debajo, láminas (no poros) pegadas y muy escotadas, olivas sucias que pasan a pardo oliva oscuro con el borde más pálido.",
   "Pie de hasta 13 cm, blanquecino sucio con tinte oliva y tonos azul verdosos arriba, con un bulbo ovoide en la base; cortina verde oliva que desaparece pronto; macizo mucho tiempo.",
   "Carne blanquecina con tinte azul verdoso, olor leve a rábano y sabor AMARGO; esporada pardo óxido. Dispersa en bosques de roble y haya."],
  "Con Cortinarius immixtus: algo parecido, pero con láminas jóvenes más vivas (amarillentas a verdes), sabor suave y esporas mayores. Wikipedia dice que es «no comestible» y que contiene alcaloides (infractopicrina) que inhiben la acetilcolinesterasa in vitro.",
  dict(s_color="verde amarillo pardo", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="verde pardo", p_color="blanco", p_base="ensanchada", interior="macizo", esporada="marron", habitat="planifolio", s_tam="mediano grande"))

P("cortinarius-cinnamomeus", "Cortinarius cinnamomeus", "nocom",
  ["Sombrero de 3-6 cm, esférico al principio y luego convexo a acampanado, con mamelón, seco y opaco, fibroso; amarillo ocre vivo de joven y luego pardo u oliva claro, a menudo azafranado en el borde.",
   "Debajo, láminas (no poros) apretadas y escotadas: amarillo vivo de jóvenes, luego pardo oliva y por fin canela óxido; cortina amarilla en ejemplares jóvenes.",
   "Pie de 8-12 cm de alto y 0,5-1 cm de ancho, cilíndrico, amarillo vivo y luego amarillo con tonos oliva, con fibrillas del velo que forman una o dos zonas oblicuas incompletas.",
   "Carne fina, amarilla con tonos oliva, de olor leve a rábano y sabor suave; esporada pardo óxido. Frecuente en lugares húmedos de bosques de coníferas."],
  "Con Cortinarius croceus, C. gentilis y otras Dermocybe y algunas Telamonia (Wikipedia no dice cómo separarlas). Wikipedia dice que «se ha afirmado que es comestible, pero puede parecerse a algunas especies mortales»; por eso aquí se trata como seta que no hay que comer.",
  dict(s_color="amarillo pardo", s_super="fibrosa", s_forma="convexo", h_tipo="!laminas", h_color="amarillo pardo", p_color="amarillo", interior="macizo", esporada="marron", habitat="conifera", s_tam="pequeno mediano"))

P("cortinarius-collinitus", "Cortinarius collinitus", "nocom",
  ["Sombrero de 3-10 cm, convexo a plano, de superficie gelatinosa y pegajosa con humedad (Wikipedia no da su color).",
   "Debajo, láminas (no poros) pegadas, apretadas, pálidas o violeta pálido.",
   "Pie de 5-15 cm de alto y 0,5-2 cm de grosor, macizo e igual, con bandas transversales que parecen escamas.",
   "Esporada pardo óxido; crece solo o en grupos con planifolios y coníferas."],
  "Con un complejo de especies emparentadas (Wikipedia no nombra ninguna); Cortinarius trivialis también tiene pie anillado de bandas. Wikipedia dice que «se considera no comestible», en parte porque el complejo de especies parecidas no se ha probado.",
  dict(s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco violeta", interior="macizo", esporada="marron", habitat="conifera planifolio", s_tam="mediano"))

P("cortinarius-anomalus", "Cortinarius anomalus", "nocom",
  ["Sombrero de hasta 5 cm, casi esférico y luego convexo a aplanado con un mamelón romo; pardo óxido sucio, pardo ceniza o canela grisáceo, seco, a veces con tinte gris violeta de joven.",
   "Debajo, láminas (no poros) medianamente apretadas, blanco azuladas, gris azuladas o lila pálido de jóvenes, que pasan a pardas y luego a arcilla óxido.",
   "Pie de 6-8 cm de alto y 0,5-0,8 cm de grosor, algo en maza y a menudo curvo, violeta o gris violeta arriba de joven, gris o gris pardo en la base; sin anillo verdadero (zona anular amarillo dorada y mechones amarillo azafrán).",
   "Carne fina, de olor ligeramente afrutado y sabor suave; esporada pardo óxido. Solitaria o en grupos dispersos en bosques de planifolios, mixtos y, más raro, de coníferas; fin de verano y otoño."],
  "Con Cortinarius alboviolaceus (blanco plateado a gris violeta de joven, velo blanco grueso y pie más voluminoso), con C. caninus (sombrero más pardo de joven y restos de velo más pardos) y con Laccaria ochropurpurea (esporada blanca). Wikipedia dice «se considera no comestible».",
  dict(s_color="pardo gris", s_forma="convexo", h_tipo="!laminas", h_color="gris violeta pardo", p_anillo="no", p_color="violeta gris pardo", esporada="marron", habitat="planifolio conifera", s_tam="pequeno"))

P("hebeloma-crustuliniforme", "Hebeloma crustuliniforme", "toxica",
  ["Sombrero de 3-11 cm, beis a pardo claro, convexo y luego con mamelón y el borde levantado con la edad.",
   "Debajo, láminas (no poros) apretadas, pegadas o escotadas, pálidas y pardas con la edad; en tiempo húmedo llevan gotitas.",
   "Pie de 4-13 cm de alto y 0,5-1,5 cm de grosor, más ancho en la base, SIN anillo.",
   "Carne gruesa y blanca, de olor a rábano y sabor amargo. En bosques abiertos y brezales; verano y otoño (en invierno en climas suaves como el de California)."],
  "Con Hebeloma sinapizans y H. insigne (Wikipedia no dice cómo separarlas). Wikipedia dice «este hongo es venenoso» y causa molestias digestivas de leves a graves (vómitos, diarrea, cólicos) unas horas después de comerlo. La Enciclopèdia Catalana la pone «a refusar» con el nombre «carlet bord».",
  dict(s_color="pardo", s_forma="convexo", h_tipo="!laminas", h_color="blanco pardo", p_anillo="no", p_base="ensanchada", habitat="conifera planifolio", s_tam="mediano"),
  ca=["carlet bord"], ca_f="EC")

P("inocybe-geophylla", "Inocybe geophylla", "toxica",
  ["Sombrero de 1-4 cm, blanco o crema, cónico y luego convexo con un mamelón marcado; sedoso y fibroso, con el borde que se raja con la edad.",
   "Debajo, láminas (no poros) apretadas, crema de jóvenes y pardas al madurar las esporas.",
   "Pie de 1-6 cm de alto y 0,3-0,6 cm de grosor, SIN anillo, con un bulbito en la base; a menudo no crece recto.",
   "Carne blanca o crema, que no cambia al cortarla; sabor acre; esporada parda. En bosques de coníferas y planifolios y en bordes de caminos y suelos removidos; verano y otoño."],
  "Con ejemplares grandes de Tricholoma y con Calocybe gambosa (estas tienen olor a harina y láminas que siguen blancas), con Inocybe umbratica e I. pudica (puede hacer falta microscopio) y, en la variedad lila (var. lilacina), con Laccaria amethystina (pie fibroso, olor afrutado, sin mamelón ocre) y con Collybia nuda (mucho mayor). Wikipedia dice «la seta es venenosa»: contiene muscarina (salivación, sudor y lagrimeo a los 15-30 minutos; antídoto atropina) y «no se ha registrado ninguna muerte por esta especie».",
  dict(s_color="blanco", s_super="fibrosa", s_forma="conico", h_tipo="!laminas", h_color="blanco pardo", p_anillo="no", p_base="ensanchada", corte="nada", esporada="marron", habitat="conifera planifolio", s_tam="pequeno"))

P("inocybe-lacera", "Inocybe lacera", "toxica",
  ["Sombrero de 1-3 cm, pardo rapé, en domo con un mamelón pequeño y el borde enrollado; fibroso y escamoso, con el borde que se rasga.",
   "Debajo, láminas (no poros) pegadas, blancas de jóvenes y luego arcilla ante con el borde blanco.",
   "Pie de 2-3 cm de alto y 3-6 mm de grosor, pardo en la base algo hinchada y más pálido arriba, fibroso, SIN anillo.",
   "Carne blanca de olor suave a harina y sabor suave; esporada parda. En suelo arenoso, sobre todo bajo pinos, bordes de caminos, antiguos fuegos, brezales y dunas; otoño."],
  "Con Inocybe hystrix: parecida, pero claramente más escamosa y mucho menos común. Wikipedia dice «se sabe que es venenosa»: contiene muscarina (salivación, lagrimeo, vómitos y, en casos graves, caída de la tensión y muerte por fallo respiratorio).",
  dict(s_color="pardo", s_super="escamas", s_forma="convexo", h_tipo="!laminas", h_color="blanco pardo", p_anillo="no", p_color="pardo", olor="harina", esporada="marron", habitat="conifera planifolio", s_tam="pequeno"))

P("cortinarius-mucosus", "Cortinarius mucosus", "nocom",
  ["Sombrero de 4-10 cm, pardo a naranja pegajoso, más oscuro hacia el centro, con el borde enrollado.",
   "Debajo, láminas (no poros) apretadas y pegadas, amarillentas pálidas al principio y pardo óxido al madurar las esporas.",
   "Pie de 5-15 cm de alto y 1,5-2,5 cm de grosor, blanquecino, VISCOSO (baboso); los ejemplares jóvenes tienen una cortina como telaraña.",
   "Olor y sabor sin nada característico; esporada ocre óxido. Bajo abedules y coníferas, sobre todo pinos, en suelos ácidos y arenosos."],
  "Con Cortinarius vibratilis (sombrero de sabor amargo) y con Pholiota velaglutinosa (suele ser menor y con láminas verdosas). Wikipedia dice que «no se recomienda en general comer ninguna especie de Cortinarius» por la abundancia de toxinas y la dificultad de identificarlas con seguridad; en ejemplares del norte de Polonia se midió más mercurio que en el suelo.",
  dict(s_color="naranja pardo", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="amarillo pardo", p_color="blanco", p_super="lisa", esporada="marron", habitat="conifera planifolio", s_tam="mediano"))

P("cortinarius-glaucopus", "Cortinarius glaucopus (Phlegmacium glaucopus)", "nocom",
  ["Sombrero de 4-12 cm, convexo, ocre o leonado con fibras pardas oscuras bien marcadas y el borde unido a una cortina como telaraña.",
   "Debajo, láminas (no poros) lila azuladas, pegadas o libres, que se ponen pardas al madurar las esporas.",
   "Pie de 4-10 cm de alto y 1-3 cm de ancho, con bulbo en la base; lila azulado pálido de joven, con la parte baja blanco amarillenta.",
   "Carne blanco amarillenta con un tono azul en la parte alta del pie, de olor poco claro (ligeramente a harina, si lo hay) y sabor suave; esporada pardo rojiza. En bosques de planifolios y coníferas, a menudo en gran número y a veces en corros de brujas; de agosto al otoño."],
  "Con Cortinarius caerulescens, C. pansa, C. sodagnitus y C. subfoetens (Wikipedia dice que es «relativamente difícil de identificar» y no explica cómo separarlas). Wikipedia dice que «se considera no comestible» y avisa de que no se coma por el parecido con otras especies, algunas mortales; los datos de distribución de Wikipedia son de Norteamérica occidental.",
  dict(s_color="pardo amarillo", s_super="fibrosa", s_forma="convexo", h_tipo="!laminas", h_color="violeta pardo", p_color="violeta blanco amarillo", p_base="ensanchada", esporada="marron", grupo="corro", habitat="planifolio conifera", s_tam="mediano grande"))

P("inosperma-maculatum", "Inosperma maculatum (Inocybe maculata)", "toxica",
  ["Sombrero de hasta 8 cm, cónico de joven y aplanado con la edad, con un mamelón ancho; pardo castaño, más pálido hacia el borde, con fibras radiales; el borde suele rajarse y el centro lleva restos blancos del velo en los ejemplares jóvenes.",
   "Debajo, láminas (no poros) pegadas y apretadas, con el borde blanco finamente dentado: gris blanquecinas de jóvenes y pardo oliva al madurar.",
   "Pie de hasta 8 cm, cilíndrico, a menudo más grueso en la base, crema que se vuelve más pardo; la base a veces es blanca y polvorienta; macizo y luego hueco; a menudo con un bulbito basal.",
   "Carne blanca de sabor suave y olor fuerte, penetrante y afrutado; esporada pardo rapé. En el suelo de bosques de planifolios o mixtos, sobre todo hayedos, en suelos calizos y entre hojarasca; solitaria o en grupos dispersos."],
  "Con Inocybe lacera (Wikipedia: parecida, pero I. maculata tiene el sombrero más oscuro y restos blancos del velo en el centro), con Inocybe lanatodisca (olor dulce a maíz verde y sombrero leonado) y con Inocybe fastigiata (fibrillas más claras). Wikipedia dice «la seta es venenosa»: contiene muscarina (salivación, lagrimeo, vómitos, y posible muerte por fallo respiratorio).",
  dict(s_color="pardo", s_super="fibrosa", s_forma="conico", h_tipo="!laminas", h_color="blanco gris pardo", p_color="blanco pardo", p_base="ensanchada", interior="hueco macizo", olor="fruta", esporada="marron", habitat="planifolio", s_tam="pequeno mediano"))

P("hebeloma-sinapizans", "Hebeloma sinapizans", "toxica",
  ["Sombrero de 4-16 cm, tostado a veces con tonos gris rosados, convexo de joven y aplanado con la edad (puede tener un mamelón bajo); liso, de húmedo a pegajoso, con el borde enrollado y luego levantado.",
   "Debajo, láminas (no poros) blanquecinas de jóvenes y pardo pálido al madurar, pegadas con una muesca justo antes del pie; el borde tiene flecos diminutos.",
   "Pie de 2-13 cm de largo y 1-3 cm de grosor, casi igual de ancho salvo una base hinchada.",
   "Carne blanquecina y gruesa, de olor y sabor de RÁBANO; esporada pardo pálida. En grupos o corros, en bosques de planifolios y de coníferas."],
  "Con Hebeloma crustuliniforme, parecida, algo más pequeña y también venenosa (Wikipedia no da más diferencias que el tamaño). Wikipedia dice que es «venenosa» y que «causa molestias gastrointestinales».",
  dict(s_color="pardo", s_super="lisa viscosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco pardo", p_base="ensanchada", grupo="corro", esporada="marron", habitat="conifera planifolio", s_tam="mediano grande"))

P("inocybe-rimosa", "Inocybe rimosa (Inocybe fastigiata)", "toxica",
  ["Sombrero color tostado (raras veces blanquecino), cónico y luego extendido, con un mamelón que conserva y un centro más oscuro; superficie fibrosa (Wikipedia no da el tamaño).",
   "Debajo, láminas (no poros) gris claras que se ponen pardas con la edad.",
   "Pie blanquecino, semifibroso y algo en maza (Wikipedia no da medidas ni dice si lleva anillo).",
   "Olor «espermático» (a menudo descrito así en Inocybe); micorrícica, fructifica en épocas secas con poca lluvia; en Israel bajo robles y pinos. Originaria de Europa."],
  "Con especies de Tricholoma, sobre todo T. terreum, y con Suillus granulatus (en Israel se confunde con ellas porque comparten hábitat), y con Inocybe sororia; Wikipedia no dice cómo separarlas. Wikipedia dice que es «una seta venenosa» con muscarina y que «puede haber una intoxicación grave con cualquier cantidad».",
  dict(s_color="pardo", s_super="fibrosa", s_forma="conico", h_tipo="!laminas", h_color="gris pardo", p_color="blanco"))

F("kuehneromyces-mutabilis", "Kuehneromyces mutabilis (Pholiota mutabilis)", "alto",
  ["Sombrero de hasta 8 cm, convexo, en grupos sobre madera; muy higrófano: húmedo es brillante y graso, naranja pardo profundo hacia el borde y a menudo con un disco más claro en el centro; seco es color canela, y se seca del centro hacia fuera.",
   "Debajo, láminas (no poros) claras al principio y luego pardas, a veces algo decurrentes.",
   "Pie de 4-9 cm de largo y menos de 1 cm de grosor, canela claro arriba y más oscuro abajo, CON un anillo que separa las dos partes; por encima del anillo liso y por debajo escamoso, «calzado».",
   "Olor agradable a seta y sabor suave; esporada pardo óxido. SIEMPRE sobre madera, en general tocones de planifolios (haya, abedul, aliso); de abril a finales de octubre y en invierno si es suave."],
  ["Que no crezca sobre madera.", "Sombrero seco que se aclara del borde hacia el centro (Galerina marginata se seca del borde hacia dentro).", "Olor y sabor a harina.", "Pie sin anillo."],
  [("Galerina marginata", "mortal", "Wikipedia la llama «mortalmente venenosa»: el pie «calzado» no es un criterio fiable porque ella también puede tener escamas (el de K. mutabilis es escamoso por debajo del anillo, el de ella normalmente fibroso-sedoso); se seca del borde hacia dentro y huele y sabe a harina."),
   ("Kuehneromyces lignicola, K. marginellus, Pholiota angustipes y P. terrestris", None, "Wikipedia las cita como parecidas sin explicar cómo separarlas.")],
  "Casi todo el hemisferio norte (Europa del sur a Islandia y Escandinavia, Asia, Norteamérica) y Australia. Wikipedia dice que «es comestible pero se parece mucho a Galerina marginata, mortalmente venenosa»; algunas guías advierten de que no es segura porque puede confundirse incluso por gente experta. La Enciclopèdia Catalana la valora «molt bo» con el nombre «pollatenc».",
  dict(s_color="naranja pardo", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco pardo", p_anillo="!si", p_color="pardo", esporada="marron", grupo="mechon", habitat="madera planifolio", s_tam="pequeno mediano"),
  ca=["pollatenc"], ca_f="EC")

F("hypholoma-capnoides", "Hypholoma capnoides", "alto",
  ["Sombrero de hasta 8 cm, amarillo a pardo anaranjado o amarillo mate, a veces pegajoso, convexo y luego aplanado.",
   "Debajo, láminas (no poros) naranja amarillento pálido al principio, gris pálido al madurar y luego pardo púrpura oscuro.",
   "Pie de hasta 12 cm, amarillento y pardo óxido hacia la base.",
   "Carne amarilla de sabor suave (a diferencia de la mayoría de Hypholoma, que son amargos); esporada burdeos oscuro a parda. En grupos o macollas sobre madera en descomposición, como tocones viejos."],
  ["Láminas verdosas (sería H. fasciculare).", "Sabor amargo.", "Que no crezca sobre madera."],
  [("Hypholoma fasciculare", "toxica", "Wikipedia la llama venenosa y más común: se distingue por las láminas verdosas, mientras que H. capnoides las tiene grisáceas por las esporas oscuras."),
   ("Galerina marginata", "mortal", "Wikipedia la cita como mortal; no da cómo separarlas."),
   ("Kuehneromyces mutabilis", "ok", "Wikipedia la cita como parecida y buena comestible; no da diferencias."),
   ("Pholiota y Flammula", None, "Wikipedia dice que se parecen; no da diferencias.")],
  "América del Norte, Europa y Asia. Wikipedia dice que «es comestible» cocinada y que «puede parecerse a algunas especies venenosas». La Enciclopèdia Catalana la valora «bo» con el nombre «bolet de pi dolç».",
  dict(s_color="amarillo naranja pardo", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="naranja gris pardo violeta", p_color="amarillo pardo", esporada="marron chocolate", grupo="mechon", habitat="madera", s_tam="mediano"),
  ca=["bolet de pi dolç"], ca_f="EC")

P("hypholoma-lateritium", "Hypholoma lateritium (Hypholoma sublateritium)", "nocom",
  ["Sombrero de 3,5-9 cm, normalmente rojo ladrillo en el centro y más pálido en el borde, liso, a veces con motas pardo rojizas al medio y restos escamosos del velo que la lluvia lava.",
   "Debajo, láminas (no poros) apretadas, amarillentas de jóvenes y grisáceas con la edad; NO verdes.",
   "Pie de hasta 12 cm, amarillo claro y más oscuro hacia abajo.",
   "Sabor de suave a algo amargo; esporada púrpura parda. En densas macollas sobre tocones y raíces; de octubre hasta mucho después de las heladas (Nordeste de EE. UU.)."],
  "Con Hypholoma fasciculare (se distingue por sus láminas verdes), Galerina marginata (Wikipedia las llama muy tóxicas), Pholiota mixta y especies de Pyrrhulomyces. Wikipedia dice «a veces se considera comestible», «hay que tener cuidado para no confundirla con especies mortales parecidas» y «en Europa suele considerarse no comestible o incluso venenosa»; es «una comestible selecta en Japón». La Enciclopèdia Catalana la pone «a refusar» con el nombre «pollancró amargant».",
  dict(s_color="rojo naranja", s_super="lisa", s_forma="convexo", h_tipo="!laminas", h_color="amarillo gris", p_color="amarillo", esporada="marron chocolate", grupo="mechon", habitat="madera", s_tam="mediano"),
  ca=["pollancró amargant"], ca_f="EC")

P("pholiota-squarrosa", "Pholiota squarrosa", "toxica",
  ["Sombrero de 3-12 cm, amarillo pardusco, de campana a redondeado y luego algo aplanado; cubierto de pequeñas escamas puntiagudas dirigidas hacia abajo y atrás, amarillentas a leonadas.",
   "Debajo, láminas (no poros) apretadas, pegadas y normalmente con una muesca: amarillentas y luego pardo óxido (verdosas de jóvenes bajo el velo).",
   "Pie de 4-12 cm de largo y 0,5-1,5 cm de grosor, casi igual de ancho, CON un anillo grueso y lanoso en la parte alta; liso por encima y escamoso por debajo como el sombrero.",
   "Olor descrito de varias maneras (ajo, rábano, limón, cebolla, mofeta) y sabor fuerte a rábano; esporada canela o pardo óxido. En macollas en la base de árboles y tocones, como parásita secundaria de árboles debilitados o sobre madera podrida."],
  "Con Pholiota squarrosoides (sombrero más pálido y pegajoso entre las escamas, esporas menores, sin olor y carne blanca), con Armillaria (esporada blanca), con Leucopholiota decorosa (láminas blancas; esporas blancas) y con P. aurivella, P. populnea y P. terrestris (Wikipedia no da diferencias). Wikipedia dice que, «aunque comestible para algunos, puede ser tóxica, sobre todo si se toma con alcohol»: se han dado casos de intoxicación con vómitos y diarrea unas diez horas después de comerla con alcohol.",
  dict(s_color="amarillo pardo", s_super="escamas", s_forma="convexo", h_tipo="!laminas", h_color="amarillo pardo verde", p_anillo="!si", esporada="marron", grupo="mechon", habitat="madera planifolio conifera", s_tam="mediano grande"))

F("pholiota-flammans", "Pholiota flammans", "bajo",
  ["Sombrero de hasta 8 cm, amarillo vivo a naranja, redondo y luego convexo y aplanado, con el borde algo enrollado; seco, mate, como de fieltro, cubierto de escamitas triangulares en anillos concéntricos que pueden perderse con la lluvia.",
   "Debajo, láminas (no poros) apretadas, amarillas y luego canela parduscas, pegadas con una muesca.",
   "Pie de hasta 12 cm de alto y 0,4-1 cm de grosor, amarillo con la base más naranja, con un anillo tenue y cubierto de escamitas amarillas por debajo.",
   "Carne amarilla, firme, que no cambia al cortarla; sin olor y sabor de suave a algo amargo; esporada parda a óxido. En macollas o sueltas sobre tocones y troncos de coníferas muertos; verano y otoño."],
  ["Sombrero viscoso o pegajoso.", "Crece sobre madera de planifolios.", "Sombrero liso, sin escamas."],
  [("Pholiota squarrosa", None, "forma grandes macollas en la base de árboles y es de un amarillo menos intenso."),
   ("Pholiota adiposa", None, "prefiere planifolios muertos y tiene escamas gelatinosas también en el pie."),
   ("Pholiota aurivella", None, "es mayor y menos brillante.")],
  "Europa (de las islas británicas a Rusia), América del Norte y Asia (India, China). Wikipedia dice que «no se ha aclarado su comestibilidad»: aunque no es venenosa, unos autores la llaman no comestible, otros comestible y otros dicen que se desconoce.",
  dict(s_color="amarillo naranja", s_super="escamas", s_forma="convexo", h_tipo="!laminas", h_color="amarillo pardo", p_anillo="si", p_color="amarillo naranja", corte="nada", esporada="marron", grupo="mechon", habitat="madera conifera", s_tam="mediano"))

P("stropharia-aeruginosa", "Stropharia aeruginosa", "nocom",
  ["Sombrero de 2-8 cm, convexo y luego con un mamelón; azul verdoso vivo de joven que se pasa a amarillo ocre (a veces a manchas, sobre todo en el centro) hasta perder el azul; MUY baboso, con restos blancos del velo en el borde.",
   "Debajo, láminas (no poros) blancas al principio y luego pardo arcilla, a veces con el borde blanco.",
   "Pie blanco, bastante largo y de grosor uniforme, CON un anillo frágil pardo o negruzco; por debajo del anillo está cubierto de escamas o copos blancos finos.",
   "Sabor «ligeramente picante»; esporada pardo púrpura. En bosques con hierba, bordes de caminos, céspedes, mantillos de astillas de madera en jardines y parques, y madera podrida; de primavera a otoño."],
  "Con Stropharia caerulea («prima más apagada») y con Stropharia pseudocyanea (más pequeña y delgada, de prados, con un anillo muy fugaz). Wikipedia dice que «la comestibilidad de esta seta es controvertida»: unas fuentes la dan por comestible y otras por venenosa; las guías del hemisferio occidental la dan por venenosa (sin aclarar efectos ni toxinas) y algunas guías europeas la dan por comestible pero poco deseable por su sabor.",
  dict(s_color="verde amarillo", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco pardo", p_anillo="si", p_color="blanco", esporada="marron chocolate", habitat="prado madera", s_tam="pequeno mediano"))

P("protostropharia-semiglobata", "Protostropharia semiglobata (Stropharia semiglobata)", "nocom",
  ["Sombrero de 1-4,5 cm, hemisférico a obtuso, amarillo paja a beis tostado (amarillo claro al principio y luego amarillo apagado o blanquecino); liso y pegajoso.",
   "Debajo, láminas (no poros) pegadas con un dientecillo decurrente, gris al principio y luego pardo púrpura a negro, con el borde blanco y flecoso; muy separadas.",
   "Pie de 3-12 cm de largo y 0,2-0,5 cm de grosor, con la base hinchada y un anillo delicado en la mitad superior que puede oscurecerse con las esporas; sedoso por encima del anillo y pegajoso por debajo.",
   "Sin olor claro y de sabor suave a algo amargo; esporada púrpura oscura. En pequeños grupos sobre estiércol, suelo con abono, céspedes y corrales; cosmopolita."],
  "Con Agrocybe pediades, Panaeolus semiovatus y varias Stropharia (puede hacer falta microscopio). Wikipedia dice que unos autores la dan por «comestible» y otros por «venenosa», y que las setas que crecen sobre estiércol «suelen considerarse poco apetecibles, aunque no sean tóxicas».",
  dict(s_color="amarillo blanco", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="gris violeta pardo", p_anillo="si", p_base="ensanchada", esporada="chocolate", habitat="prado", s_tam="pequeno"))

F("agrocybe-praecox", "Agrocybe praecox", "medio",
  ["Sombrero de hasta 10 cm, en forma de bollo y pardusco de joven y luego convexo y más claro, tostado (beis seco, amarillo pardo húmedo); liso, con restos del velo en el borde.",
   "Debajo, láminas (no poros) gris pálido al principio y luego pardas.",
   "Pie de 4-12 cm de largo y hasta unos 2 cm de grosor, pálido, CON un anillo frágil y a menudo con cordones blancos de micelio en la base.",
   "Olor y sabor a harina, a veces amargo; esporada parda. En bosques, jardines y campos, suelta o en grupos sobre hierba, compost o restos de madera; sale temprano en el año (primavera y verano)."],
  ["Pie sin anillo.", "Olor o sabor que no recuerda a harina.", "Esporada que no sea parda."],
  [("Agrocybe acericola, A. elatella, A. sphaleromorpha, A. molesta y A. smithii", None, "forman un complejo: Wikipedia dice que no se distinguen por rasgos superficiales y solo por hábitat y localidad."),
   ("Cortinarius caperatus", "ok", "tiene el sombrero arrugado, no liso."),
   ("Taxones no comestibles", None, "Wikipedia dice que la especie «puede solaparse con algunos taxones no comestibles».")],
  "Eurasia, norte de África y América del Norte. Wikipedia dice que «a veces se considera comestible» pero «sin sabor»: una fuente francesa aconseja dejarla por amarga y blanda; Roger Phillips la da por no comestible.",
  dict(s_color="pardo amarillo", s_super="lisa", s_forma="convexo", h_tipo="!laminas", h_color="gris pardo", p_anillo="si", p_color="blanco", olor="harina", esporada="marron", habitat="prado madera", s_tam="mediano"))

F("bolbitius-titubans", "Bolbitius titubans (B. vitellinus)", "bajo",
  ["Sombrero de 1,5-7 cm, amarillo (o amarillo vivo) de joven que pasa a blanquecino o grisáceo; en forma de huevo y luego convexo y casi plano.",
   "Debajo, láminas (no poros) blanquecinas o amarillentas pálidas que pasan a canela óxido con la edad; libres o apenas pegadas, frágiles y blandas.",
   "Pie de 3-12 cm de alto y 2-6 mm de ancho, blanco amarillento, con una fina pelusilla harinosa; muy delicado.",
   "Carne fina y frágil, que se estropea enseguida; esporada pardo canela. En prados, césped de jardín, paja, estiércol, astillas de madera y compost; sale en abundancia tras la lluvia en la estación cálida."],
  ["Seta grande y carnosa (esta es fina, frágil y se deshace en horas).", "Esporada que no sea pardo canela."],
  [("Bolbitius aleuriatus, B. coprophilus, B. lacteus y Conocybe apala", None, "Wikipedia las cita como parecidas sin dar diferencias.")],
  "Presente en todos los continentes salvo la Antártida. Wikipedia dice que los expertos «no aconsejan comerla» y que se considera no comestible «por su carne fina y frágil que se estropea enseguida»: no se sabe que sea tóxica.",
  dict(s_color="amarillo blanco gris", s_forma="convexo", h_tipo="!laminas", h_color="blanco amarillo pardo", p_color="blanco amarillo", esporada="marron", habitat="prado", s_tam="pequeno mediano"))

P("phaeolepiota-aurea", "Phaeolepiota aurea", "toxica",
  ["Seta grande y dorada: sombrero de hasta 20 cm, con la superficie polvorienta-granulosa.",
   "Debajo, láminas (no poros).",
   "Pie de hasta 20 cm de largo con un anillo grande, como una falda.",
   "Olor suave; esporada tostada. A menudo en grupos y junto a ortigas; presente en América del Norte y Eurasia."],
  "Con Cystoderma fallax y C. granosum, Gymnopilus spectabilis y Agrocybe praecox (Wikipedia no dice cómo separarlas). Wikipedia dice que se ha considerado comestible y se come en Rusia y China, pero «no se recomienda su consumo porque se sabe que causa molestias gastrointestinales» y contiene «cantidades inaceptables de cadmio y de compuestos de cianuro» (cocinarla reduce los cianuros).",
  dict(s_color="amarillo naranja", s_super="escamas", h_tipo="!laminas", p_anillo="!si", esporada="marron", s_tam="grande"))

P("gymnopus-dryophilus", "Gymnopus dryophilus (Collybia dryophila)", "toxica",
  ["Sombrero de 2-6 cm, pardo rojizo a ocre y tostado al secarse, convexo y luego más irregular con la edad.",
   "Debajo, láminas (no poros) blanquecinas y apretadas, finamente pegadas al pie y que se sueltan con la edad.",
   "Pie de 2-8 cm de largo y 3-6 mm de ancho, a veces más grueso en la base, liso y SIN pelos en la base.",
   "Esporada blanca. En bosques de planifolios y de coníferas (robles, pinos) y sobre mantillo de astillas, en arcos y corros; de abril a diciembre."],
  "Con Marasmius strictipes (Wikipedia no da diferencias) y con Rhodocollybia butyracea (esporada rosada y alguna espora que se pone pardo rojiza con el reactivo de Melzer). Wikipedia lo recoge con varias frases: «considerada comestible pero puede causar problemas gastrointestinales graves», «comestible según algunas fuentes aunque no merece la pena» y «contiene toxinas que pueden causar problemas gastrointestinales graves»; el pie es duro y puede acumular mercurio. La Enciclopèdia Catalana la valora «acceptable» con el nombre «cama-sec de bosc».",
  dict(s_color="pardo", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_base="normal", esporada="blanca", grupo="corro", habitat="planifolio conifera madera", s_tam="pequeno"),
  ca=["cama-sec de bosc"], ca_f="EC")

F("gymnopus-fusipes", "Gymnopus fusipes (Collybia fusipes)", "bajo",
  ["Sombrero de 3-10 cm, liso, pardo rojizo oscuro o más pálido, a veces con manchas oscuras.",
   "Debajo, láminas (no poros) normalmente muy separadas, blanquecinas, a veces manchadas.",
   "Pie de hasta 15 cm, pardo rojizo y más claro arriba, SIN anillo; con la edad se hincha, se surca profundamente y se pone duro.",
   "En macollas, a menudo grandes, en la base de los árboles, sobre raíces o tocones, siempre ligada a madera enterrada o visible; sobre todo robles, a veces hayas; verano y otoño."],
  ["Pie con anillo.", "Que no crezca ligada a un árbol o tocón."],
  [("Ejemplares viejos", None, "un olor a rancio indica que el ejemplar está demasiado pasado (Wikipedia no cita otras especies parecidas).")],
  "Europa entera, y se está extendiendo en América del Norte (sobre roble rojo). Wikipedia dice que «la mayoría de los autores no la consideran digna de la mesa», que los sombreros (solo) «se dicen comestibles y buenos de jóvenes» y que los viejos pueden causar gastroenteritis; es un parásito serio de la raíz del roble. La Enciclopèdia Catalana la valora «acceptable» con el nombre «flota de roure».",
  dict(s_color="pardo rojo", s_super="lisa", h_tipo="!laminas", h_color="blanco", p_anillo="no", p_color="pardo rojo", grupo="mechon", habitat="madera planifolio", s_tam="mediano"),
  ca=["flota de roure"], ca_f="EC")

F("mycetinis-alliaceus", "Mycetinis alliaceus (Marasmius alliaceus)", "bajo",
  ["Sombrero de 2-4 cm, beis, ocre o color carne, a veces arrugado y algo abombado en el centro.",
   "Debajo, láminas (no poros) blanquecinas, finamente pegadas al pie.",
   "Pie largo, tenaz y delgado, de hasta 15 cm de alto y 3 mm de grosor, oscuro: aterciopelado y negro en la parte baja, quizá pardo arriba.",
   "Olor y sabor FUERTES a ajo; esporada blanca; carne del sombrero escasa. Sobre hojas caídas y madera podrida en bosques europeos, sobre todo hayedos, de principios de verano al otoño."],
  ["Olor y sabor que no sean a ajo.", "Pie liso, brillante y rojo pardo (sería Mycetinis scorodonius)."],
  [("Mycetinis scorodonius", None, "su pie es liso, brillante y pardo rojizo."),
   ("Mycetinis querceus", None, "tiene el pie aterciopelado como esta, pero de color pardo púrpura.")],
  "Bastante común en algunas zonas de Europa y bastante rara en otras. Wikipedia dice que «el sombrero es comestible, pero de poco valor culinario por su carne escasa». La Enciclopèdia Catalana la pone «a refusar» con el nombre «allet».",
  dict(s_color="pardo amarillo", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_color="negro pardo", esporada="blanca", habitat="planifolio madera", s_tam="pequeno"),
  ca=["allet"], ca_f="EC")

F("mycetinis-scorodonius", "Mycetinis scorodonius (Marasmius scorodonius)", "bajo",
  ["Sombrero de 1-3 cm, pardo rojizo (a veces beis a ocre), higrófano que se aclara al secarse, a veces algo arrugado.",
   "Debajo, láminas (no poros) blancas y bastante apretadas, de pegadas a casi libres.",
   "Pie de hasta 6 cm de alto y 2 mm de grosor, pálido arriba, pardo rojizo en la parte baja y pardo oscuro o negruzco en la base; liso (sin pelos).",
   "Olor y sabor MUY fuertes a ajo; esporada blanca. Sobre agujas de coníferas, ramitas, corteza de coníferas y de planifolios, gramíneas y otras plantas; verano a finales de otoño."],
  ["Olor y sabor que no sean a ajo.", "Pie aterciopelado (sería Mycetinis alliaceus)."],
  [("Mycetinis virgultorum", None, "muy emparentada: tiene los cuerpos fructíferos menores, un pie escamoso y mate y esporas menores."),
   ("Mycetinis alliaceus", None, "tiene el pie aterciopelado, negro abajo.")],
  "Bastante común en el norte y centro de Europa, presente en el resto del continente, en el este de América del Norte, norte de África y Asia. Wikipedia dice que «aunque comestible, es demasiado pequeña para tener sustancia» y que su sabor se describe «a menudo como desagradable».",
  dict(s_color="pardo rojo", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_color="pardo negro", p_super="lisa", esporada="blanca", habitat="conifera planifolio", s_tam="pequeno"))

F("rhodocollybia-butyracea", "Rhodocollybia butyracea (Collybia butyracea)", "bajo",
  ["Sombrero de 2-10 cm, convexo y luego casi plano, liso y húmedo en fresco, pardo rojizo que se aclara a canela.",
   "Debajo, láminas (no poros) libres o apenas pegadas, apretadas, blanquecinas y a veces rosadas con la edad, con el borde fino y a veces desigual.",
   "Pie de hasta 10 cm de alto y 1 de grosor, normalmente algo en maza (ensanchado hacia la base).",
   "Carne blanca sin olor ni sabor claros; esporada de amarillenta pálida a rosada pálida o blanca. Sobre mantillo de coníferas (normalmente pinos) y a veces de planifolios."],
  ["Esporada de otro color que no sea blanca a rosada pálida.", "Olor o sabor claros."],
  [("Rhodocollybia badiialba, R. prolixa y Gymnopus dryophilus", None, "Wikipedia las cita como parecidas sin explicar cómo separarlas (la ficha de Gymnopus dryophilus dice que se separa por su esporada rosada).")],
  "Datos de América del Norte (Wikipedia dice «ampliamente distribuida»). Wikipedia dice que es «comestible, pero sin sustancia» y que «puede parecerse a especies no comestibles».",
  dict(s_color="pardo", s_super="lisa", s_forma="convexo", h_tipo="!laminas", h_color="blanco rosa", p_base="ensanchada", esporada="blanca rosa", habitat="conifera", s_tam="pequeno mediano"))

F("rhodocollybia-maculata", "Rhodocollybia maculata (Collybia maculata)", "bajo",
  ["Sombrero de hasta 9 cm, color crema con manchas pardo rojizas; el borde se mantiene enrollado mucho tiempo.",
   "Debajo, láminas (no poros) blanquecinas y apretadas, que se manchan con la edad.",
   "Pie de hasta 10 cm de largo, del color de las láminas, duro, hueco y afilado hacia abajo.",
   "Esporada de blanquecina a amarillenta. Suele salir en el mantillo de coníferas en descomposición. La variedad scorzonerea tiene las láminas amarillentas y a veces el pie amarillento."],
  ["Sombrero de un solo color, sin manchas pardo rojizas.", "Pie blando."],
  [("Wikipedia no cita especies parecidas", None, "")],
  "Datos de América del Norte (Wikipedia dice «ampliamente distribuida»). Wikipedia dice que, «aunque no es tóxica, se considera no comestible por su dureza y su sabor desagradable» (normalmente amarga).",
  dict(s_color="blanco pardo", h_tipo="!laminas", h_color="blanco", interior="hueco", esporada="blanca", habitat="conifera", s_tam="mediano"))

F("marasmius-rotula", "Marasmius rotula", "bajo",
  ["Sombrero muy pequeño (3-20 mm), amarillento pardo de joven y luego blanquecino a rosa blanquecino, a veces con el centro pardo más oscuro; convexo y algo hundido en el centro, fino y membranoso, con surcos marcados y borde festoneado.",
   "Debajo, láminas (no poros) muy separadas (unas 16-22), blanquecinas a amarillo pálido, unidas a un COLLAR que rodea el pie y nunca directamente al pie.",
   "Pie de 1,2-8 cm de largo y hasta 1,5 mm de grosor, pardo negruzco que se aclara casi translúcido arriba, liso y a veces brillante, hueco y tenaz; SIN anillo.",
   "Esporada blanca o amarillo pálido. En macollas sobre madera muerta (sobre todo de haya), ramitas, troncos con musgo y tocones; a menudo abundante tras las lluvias."],
  ["Láminas pegadas directamente al pie, sin collar.", "Seta grande."],
  [("Marasmius capillaris", None, "sombrero tostado pálido con el centro blanco, redondeado y no plegado, pie más fino (menos de 0,3 mm) y crece sobre hojas de roble, no en macollas."),
   ("Marasmius bulliardii", None, "es más pequeña y con menos láminas."),
   ("Tetrapyrgos nigripes", None, "sombreros blancos de 5-10 mm, a veces con láminas decurrentes y el pie con pelitos blancos."),
   ("Mycena corticola", None, "más pequeña, sombrero rosa pardo pálido, sobre corteza en la base de árboles vivos.")],
  "Muy extendida en América del Norte, Europa y el norte de Asia. Wikipedia dice que «generalmente se considera no comestible» y que no es venenosa.",
  dict(s_color="blanco pardo rosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco amarillo", p_anillo="no", p_color="negro pardo", p_super="lisa", interior="hueco", esporada="blanca", grupo="mechon", habitat="madera planifolio", s_tam="pequeno"))

F("oudemansiella-mucida", "Oudemansiella mucida", "bajo",
  ["Sombrero de 2-8 cm, muy convexo de joven y luego algo aplanado, gris pálido de joven que se aclara a blanco, cubierto de una membrana semitranslúcida y baboso, a menudo con un tinte ocráceo en el centro.",
   "Debajo, láminas (no poros) anchas y muy separadas, pegadas.",
   "Pie de 3-10 cm de alto y 3-10 mm de ancho, blanco por encima del anillo y grisáceo por debajo, CON un anillo membranoso bien marcado; estriado por encima del anillo y algo escamoso por debajo.",
   "Carne fina y blanca; esporada blanca. Sobre troncos muertos y ramas caídas de HAYA (a veces roble), a veces en ramas altas muertas de árboles vivos; finales de verano a finales de otoño."],
  ["Que no crezca sobre madera de haya o roble.", "Sombrero seco, sin baba.", "Pie sin anillo."],
  [("Wikipedia no cita especies parecidas", None, "dice que «rara vez se confunde con otros hongos».")],
  "Nativa de Europa (norte y centro). Wikipedia dice que «en general no se considera tóxica», que algunas fuentes la dan por «levemente tóxica» y otras por «comestible tras lavarla (quitar el moco)» o «buena seta culinaria».",
  dict(s_color="blanco gris", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", p_anillo="!si", p_color="blanco gris", esporada="blanca", habitat="madera planifolio", s_tam="pequeno mediano"))

P("mycena-pura", "Mycena pura", "toxica",
  ["Sombrero de 2-6 cm, violeta a púrpura de joven (puede cambiar con la edad, a menudo con tonos púrpura), convexo, plano o acampanado.",
   "Debajo, láminas (no poros) pálidas o rosadas, que con la edad se unen por venas transversales.",
   "Pie de 4-10 cm de alto y 2-6 mm de ancho, del color del sombrero, SIN anillo, hueco.",
   "Olor a rábano; esporada blanca. Bajo coníferas y a veces planifolios, sobre el mantillo del bosque en descomposición."],
  "Con Clitocybe nuda (Lepista nuda), Laccaria amethysteo-occidentalis, Mycena purpureofusca y M. pelianthina (Wikipedia no dice cómo separarlas). Wikipedia dice que «al contener muscarina, no debe consumirse» y que algunas guías la dan por comestible; sus datos de distribución son de Norteamérica.",
  dict(s_color="violeta", s_forma="convexo", h_tipo="!laminas", h_color="rosa blanco", p_anillo="no", p_color="violeta", interior="hueco", esporada="blanca", habitat="conifera planifolio", s_tam="pequeno"))

F("mycena-galericulata", "Mycena galericulata", "bajo",
  ["Sombrero de 2-5 cm, pardo grisáceo a pardo oscuro con el borde ante pardo, acampanado o cónico romo o aplanado con mamelón; surcos radiales casi hasta el centro, graso sin ser pegajoso, y que se raja radialmente con la edad.",
   "Debajo, láminas (no poros) blancas a grisáceas que pronto se tiñen de rosa pálido, con venas transversales muy marcadas.",
   "Pie de 5-9 cm de largo y 2-4 mm de grosor, igual de ancho, gris blanquecino pálido arriba y gris negruzco pálido abajo, SIN anillo, hueco, con una pseudorriza larga (prolongación bajo tierra) en la base.",
   "Carne gris acuosa de olor y sabor de harina a rábano; esporada blanca. En pequeñas macollas o sueltas sobre troncos, tocones, ramas y astillas descompuestas de planifolios y coníferas; de primavera a principios de invierno."],
  ["Pie con anillo.", "Láminas que no son blancas y rosadas.", "Que no crezca sobre madera."],
  [("Mycena inclinata", "nocom", "tiene manchas rojizas en las láminas, que pueden volverse enteramente rojas, y motas blanquecinas como hilos en el pie."),
   ("Mycena maculata", None, "las láminas se manchan de rosa al madurar y las esporas son mayores (7-9 por 4-5 µm)."),
   ("Mycena tintinnabulum", None, "mucho menor (sombrero hasta 2,6 cm), pardo, con pelos desordenados en la base; a finales de otoño en tocones de planifolios."),
   ("Mycena haematopus", "nocom", "sombrero pardo vinoso de borde festoneado y el pie suelta un jugo pardo rojizo al herirlo."),
   ("Especies de Pluteus", None, "Wikipedia avisa de que pueden confundirse por las láminas rosadas al madurar.")],
  "Hemisferio norte templado. Wikipedia la califica de «posiblemente comestible pero de poco interés»; algunas fuentes la dan por «no comestible» (olor «algo rancio»); David Arora: «comestible pero puede parecerse a especies dudosas».",
  dict(s_color="gris pardo", s_super="lisa", s_forma="conico", h_tipo="!laminas", h_color="blanco gris rosa", p_anillo="no", p_color="gris", interior="hueco", olor="harina", esporada="blanca", grupo="mechon", habitat="madera planifolio conifera", s_tam="pequeno"))

P("mycena-haematopus", "Mycena haematopus", "nocom",
  ["Sombrero de hasta 4 cm, pardo rojizo o rosado a menudo con tinte violeta, más pálido hacia el borde; de ovoide a cónico y luego acampanado y aplanado con mamelón; de joven seco y con fino polvillo blanquecino y luego pulido y húmedo; con la edad algo translúcido y surcado, con el borde festoneado y a veces desgarrado.",
   "Debajo, láminas (no poros) pegadas, blanquecinas o gris vinosas al principio y con manchas pardo rojizas después.",
   "Pie de 3-9 cm de alto y 1-2 mm de grosor, pardo rojizo oscuro, hueco y quebradizo, con pelos gruesos en la base.",
   "Carne pálida o rojo vino que, al cortarla o herirla, SUELTA un jugo rojo; sin olor y de sabor suave a algo amargo; esporada blanca. En pequeñas macollas unidas por la base sobre troncos y tocones de planifolios, sobre todo haya; todo el año si el tiempo es suave."],
  "Con Mycena sanguinolenta (más pequeña, 0,3-1 cm, en grupos y no en macollas, sobre hojas, ramas muertas, musgo o agujas de pino, con el borde de las láminas siempre pardo rojizo oscuro), y con M. californiensis y M. purpureofusca (Wikipedia no da diferencias). Wikipedia dice que «no se sabe con certeza su comestibilidad»: unas fuentes la dan por comestible pero sin sustancia, otras por no comestible o aconsejan evitarla por la posible toxicidad de especies emparentadas.",
  dict(s_color="rojo pardo violeta", s_forma="conico", h_tipo="!laminas", h_color="gris blanco", p_color="pardo rojo", interior="hueco", esporada="blanca", grupo="mechon", habitat="madera planifolio", s_tam="pequeno"))

F("mycena-epipterygia", "Mycena epipterygia", "bajo",
  ["Sombrero de 1-2 cm, pardo amarillento a pardo grisáceo, acampanado y luego convexo (a veces casi plano), pegajoso, con estrías y la cutícula que se pela.",
   "Debajo, láminas (no poros) bastante separadas, blancas a crema (a veces rosadas con la edad), pegadas o algo decurrentes.",
   "Pie de 4-9 cm de alto y 1-2 mm de ancho, largo y delgado, amarillento a amarillo verdoso: es su rasgo identificativo.",
   "Carne blanca y frágil; esporada de blanca a beis muy pálido. En el suelo de bosques de planifolios y de coníferas, brezales y pastos ácidos, entre hierbas y musgo; de agosto a noviembre en Gran Bretaña."],
  ["Pie que no sea amarillo o amarillo verdoso.", "Sombrero seco, no pegajoso."],
  [("Mycena aurantiidisca, M. clavicularis, M. leptocephala y Roridomyces roridus", None, "Wikipedia dice que se parece a ellas sin dar diferencias.")],
  "Europa occidental y noroeste del Pacífico de América del Norte. Wikipedia dice que «se considera comestible pero de poco interés culinario».",
  dict(s_color="amarillo pardo gris", s_super="viscosa", s_forma="conico convexo", h_tipo="!laminas", h_color="blanco", p_color="amarillo", esporada="blanca", habitat="conifera planifolio prado", s_tam="pequeno"))

F("mycena-polygramma", "Mycena polygramma", "bajo",
  ["Sombrero de 2-4 cm, de huevo o cono a acampanado y casi convexo, con un mamelón pequeño; pardo grisáceo oscuro a negro bajo un velillo, que se aclara a gris pálido o beis rosado; surcos finos y profundos en el borde.",
   "Debajo, láminas (no poros) apretadas, anchas (4-7 mm), blancas a blanquecinas, rosadas con la edad y a veces con manchas parduscas.",
   "Pie de 6-15 cm de largo y 2-5 mm de grosor, igual de ancho y tubular, muy quebradizo, gris ceniza a pardo grisáceo con finas estrías longitudinales; la base lleva pelos blancos tiesos y a menudo se mancha de pardo rojizo.",
   "Carne gris a blanca, acuosa y dura; olor agradable y sabor suave; esporada blanca. En pequeños grupos sobre tocones, ramas y madera enterrada de planifolios (roble, arce, tilo), a veces coníferas."],
  ["Pie liso, sin estrías.", "Que no crezca sobre madera."],
  [("Mycena pullata", None, "las formas altas y delgadas se parecen; se separa por el color."),
   ("Mycena praelonga", None, "se distingue por su relación con M. alcalina y su hábitat de esfagno.")],
  "Asia, Europa y América del Norte (rara en Norteamérica, común en Europa y Gran Bretaña). Wikipedia dice que «la seta no es comestible».",
  dict(s_color="gris negro pardo", s_forma="conico", h_tipo="!laminas", h_color="blanco rosa", p_color="gris pardo", interior="hueco", esporada="blanca", grupo="mechon", habitat="madera planifolio", s_tam="pequeno"))

P("mycena-inclinata", "Mycena inclinata", "nocom",
  ["Sombrero de 1-4,5 cm, pardo rojizo claro, de cónico a acampanado o convexo y luego aplanado, con surcos que siguen las láminas y el borde finamente festoneado; húmedo, liso e higrófano, a menudo rajado en el borde.",
   "Debajo, láminas (no poros) decurrentes (bajan por el pie), pardo pálido con tintes rojizos, anchas (3-6 mm).",
   "Pie de 3-9 cm de largo y 1,5-4 mm de grosor, frágil, amarillo a amarillo pardo arriba y pardo rojizo a naranja pardo en la mitad baja al madurar, con motas blancas de joven y la base cubierta de un micelio amarillento.",
   "Carne grisácea a blanquecina, de olor y sabor algo harinosos; esporada blanca. En grupos densos y macollas sobre troncos y tocones de planifolios, sobre todo roble y castaño; primavera y otoño."],
  "Con Mycena galericulata (se confunde a menudo con ella; esa tiene el sombrero cónico romo gris pardo apagado y venas transversales), con M. maculata (solo sobre troncos de planifolios; tiene manchas rojizas en las láminas que esta no tiene) y con M. polygramma (pie acanalado gris azulado). Wikipedia dice que su comestibilidad es «dudosa» y que «es mejor evitarla», aunque «se considera no venenosa».",
  dict(s_color="pardo rojo", s_super="lisa", s_forma="conico convexo", h_tipo="!laminas", h_color="pardo rosa", p_color="amarillo pardo naranja", olor="harina", esporada="blanca", grupo="mechon", habitat="madera planifolio", s_tam="pequeno"))

F("pleurotus-eryngii", "Pleurotus eryngii", "bajo",
  ["Sombrero de 4-15 cm, tostado, convexo y luego aplanado, con el borde fino enrollado al principio; liso y algo aterciopelado.",
   "Debajo, láminas (no poros) decurrentes (bajan por el pie), apretadas, unidas entre sí en red y blanquecinas.",
   "Pie de 3-10 cm de alto y 1-3 cm de ancho, blanquecino.",
   "Carne casi sin aroma en crudo. Crece en las raíces del cardo corredor (Eryngium campestre) u otras Eryngium: parásita débil de raíces de plantas herbáceas de la familia de las zanahorias."],
  ["Que no crezca sobre raíces de cardo corredor u otras umbelíferas.", "Láminas que no bajan por el pie."],
  [("Pleurotus nebrodensis", None, "estudios moleculares la separan de esta; Wikipedia no da cómo reconocerla en el campo."),
   ("Pleurotus fossulatus", None, "Wikipedia dice que «podría ser otra especie muy emparentada».")],
  "Región mediterránea, norte de África, Europa central, Asia occidental e India. Wikipedia dice que se produce comercialmente y que es «comestible»; cocinada «desarrolla un sabor umami rico y textura de carne». La Enciclopèdia Catalana la valora «molt bo» con el nombre «gírgola de panical».",
  dict(s_color="pardo", s_super="lisa", s_forma="convexo embudo", h_tipo="!laminas", h_color="blanco", p_color="blanco", habitat="prado", s_tam="mediano grande"),
  ca=["gírgola de panical"], ca_f="EC")

F("pleurotus-cornucopiae", "Pleurotus cornucopiae", "bajo",
  ["Sombrero de hasta unos 15 cm, blanquecino de joven y pardusco con la edad.",
   "Debajo, láminas (no poros) blanquecinas, muy decurrentes (bajan por el pie) y que en la base forman una red de crestas.",
   "Pie siempre presente, a veces bifurcado y de excéntrico a bastante central, de hasta unos 12 cm de largo y 2 de grosor.",
   "Carne firme y blanca, de olor fuerte con un matiz de anís y de harina al cortarla; sabor harinoso. Sobre tocones y troncos caídos de roble, haya, olmo y otros planifolios; de agosto a noviembre en Europa."],
  ["Láminas poco decurrentes y sombrero gris azulado pizarra (sería Pleurotus ostreatus).", "Sombrero amarillo (sería Pleurotus citrinopileatus).", "Que no crezca sobre madera."],
  [("Pleurotus ostreatus", "ok", "las láminas bajan poco por el pie y el sombrero es gris pizarra o azulado."),
   ("Pleurotus pulmonarius", "ok", "color del sombrero parecido, pero con láminas como las de P. ostreatus."),
   ("Pleurotus citrinopileatus", "ok", "su sombrero amarillo la distingue; algunos autores la tratan como variedad.")],
  "Toda Europa; también citada en EE. UU. y México. Wikipedia dice «esta seta es comestible», que se debe recoger joven y desechar los pies duros. La Enciclopèdia Catalana la valora «bo» con el nombre «orellana».",
  dict(s_color="blanco pardo", s_forma="embudo", h_tipo="!laminas", h_color="blanco", habitat="madera planifolio", s_tam="grande"),
  ca=["orellana"], ca_f="EC")

F("volvariella-bombycina", "Volvariella bombycina", "alto",
  ["Sombrero de 5-20 cm, blanco a amarillento (más pálido en el borde), ovalado de joven y luego acampanado a convexo, seco y cubierto de hilos sedosos.",
   "Debajo, láminas (no poros) apretadas, blancas al principio y rosadas al madurar las esporas, LIBRES (no tocan el pie).",
   "Pie de 6-20 cm de largo y 1-3 cm de grosor, blanco y liso, con una VOLVA en la base: una bolsa membranosa, a menudo agrietada o escamosa, blanca a amarillenta o pardo sucia, a menudo lobulada.",
   "Carne blanca, fina y blanda, de olor a patata cruda; esporada rosa a salmón. Suelta o en pequeños grupos sobre troncos y tocones muertos de planifolios (arce, magnolio, haya, roble, olmo), a veces vivos, en huecos y heridas."],
  ["Esporada blanca.", "Que crezca en el suelo y no sobre madera (así son las amanitas).", "Láminas que siguen blancas al madurar."],
  [("Especies de Pluteus", None, "tienen aspecto parecido y esporada rosada, pero NO tienen volva."),
   ("Especies de Amanita", "mortal", "crecen en el suelo y tienen esporada blanca (Wikipedia las cita como causa de confusión); con volva y láminas blancas de jóvenes se parecen."),
   ("Volvariella pusilla", None, "sombrero de 0,5-3 cm, con fibras sedosas y rayitas en el borde con humedad; crece en suelo, jardines e invernaderos."),
   ("Volvariella hypopithys", None, "sombrero de 2-5 cm, sedoso a escamoso, sin rayas en el borde; crece en el suelo de bosques."),
   ("Volvariella caesiotincta", None, "sombrero gris azulado."),
   ("Volvariella gloiocephala", None, "sombrero liso y pegajoso con humedad y volva blanca.")],
  "Poco común pero extendida (Europa, Asia, América, Australia). Wikipedia dice que es «comestible», «de buena calidad» y «excelente» o «sabrosa», y que Hungría la protege por ley desde 2005 (recogerla es ilegal). El parecido de la volva y las láminas jóvenes con una amanita es la razón del riesgo alto.",
  dict(s_color="blanco amarillo", s_super="fibrosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco rosa", p_color="blanco", p_base="!bolsa", esporada="rosa", habitat="madera planifolio", s_tam="grande"))

F("coprinellus-micaceus", "Coprinellus micaceus (Coprinus micaceus)", "medio",
  ["Sombrero de 0,8-5 cm, ovalado a cilíndrico de joven y luego acampanado; pardo amarillento o tostado, más oscuro en el centro y claro hacia el borde, higrófano; de joven lleva partículas blancas brillantes que se lavan; borde surcado casi hasta el centro que se desgarra en rayos.",
   "Debajo, láminas (no poros) muy apretadas y finamente pegadas: blancas de jóvenes y luego pardas y negras al madurar las esporas, y se parten por la mitad al abrirse el sombrero.",
   "Pie de 3-10 cm de largo y 2-5 mm de grosor, blanco, hueco y quebradizo, con polvillo blanquecino que se pierde; puede haber un anillo rudimentario en la base.",
   "Carne fina y frágil, de olor y sabor poco marcados; esporada pardo oscura a negra. Sobre o junto a tocones, troncos y madera enterrada de planifolios, y en suelo removido; de mayo a diciembre en Europa."],
  ["Seta grande y gris en macolla densa, sin partículas brillantes en el sombrero (sería Coprinopsis atramentaria).", "Esporada que no sea oscura."],
  [("Coprinopsis atramentaria", "toxica", "Wikipedia dice que es mayor y gris, crece en macollas densas, sin partículas brillantes, y su sombrero y láminas se disuelven; lleva coprina, la toxina que esta especie NO tiene."),
   ("Coprinellus truncorum", None, "casi indistinguible en el campo; hace falta microscopio."),
   ("Coprinellus bisporus", None, "casi idéntica, pero sin gránulos amarillentos en el sombrero y con dos esporas por basidio."),
   ("Coprinus variegatus (C. quadrifidus)", None, "sombrero gris pardusco con escamas blancas a parduscas y olor desagradable."),
   ("Coprinellus disseminatus", None, "menor, amarillo pardo a gris pardo; las láminas se ennegrecen pero no se disuelven; siempre en grandes grupos sobre madera podrida."),
   ("Coprinellus radians", None, "sale de una estera de micelio amarillo anaranjado.")],
  "Cosmopolita. Wikipedia dice que es «una especie comestible» siempre que se coma antes de que las láminas se ennegrezcan y se disuelvan, y que conviene evitar los ejemplares de cunetas y sitios contaminados por acumular metales pesados. La Enciclopèdia Catalana la pone «a refusar» con el nombre «bolets de femer».",
  dict(s_color="amarillo pardo", s_forma="conico", h_tipo="!laminas", h_color="blanco pardo", p_color="blanco", interior="hueco", esporada="negra marron", grupo="mechon", habitat="madera planifolio", s_tam="pequeno"),
  ca=["bolets de femer"], ca_f="EC")

F("pluteus-cervinus", "Pluteus cervinus", "medio",
  ["Sombrero de hasta 12 cm, color gamo: de ocre pardo claro a pardo oscuro, a veces con gris o negro y el centro más oscuro; acampanado y a menudo arrugado de joven y luego convexo; liso, de mate a sedoso.",
   "Debajo, láminas (no poros) blancas al principio que enseguida cogen un brillo rosado al madurar las esporas.",
   "Pie de 5-12 cm de largo y 0,5-2 cm de grosor, normalmente más grueso en la base, blanco con fibrillas pardas verticales.",
   "Carne blanda y blanca, de olor suave a rábano terroso y sabor suave que puede volverse algo amargo; esporada pardo rosada. Sobre troncos podridos, raíces, tocones, serrín y restos de madera; de abril a diciembre en Europa."],
  ["Que no crezca sobre madera o serrín.", "Esporada blanca.", "Láminas que no se tiñen de rosa."],
  [("Pluteus atromarginatus", None, "tiene el borde de las láminas pardo oscuro."),
   ("Pluteus hongoi", None, "sombrero típicamente más pálido."),
   ("Pluteus exilis y otros Pluteus", None, "Wikipedia los cita (exilis, de primavera, en el oeste de América del Norte) como parecidos."),
   ("Especies de Entoloma", "toxica", "Wikipedia dice que sus láminas «no son libres» (se unen al pie) y que tienen esporas angulosas; en esta guía Entoloma rhodopolium es venenosa y también tiene esporada rosada.")],
  "Común en Europa y en el este de América del Norte. Wikipedia dice «aunque es una seta comestible de baja calidad»: sabor poco notable y no se conserva bien. La Enciclopèdia Catalana la pone «a refusar» con el nombre «bolet de soca de làmines roses».",
  dict(s_color="pardo", s_super="lisa", s_forma="conico convexo", h_tipo="!laminas", h_color="blanco rosa", p_color="blanco pardo", p_base="ensanchada", esporada="rosa marron", habitat="madera", s_tam="mediano grande"),
  ca=["bolet de soca de làmines roses"], ca_f="EC")

F("panellus-stipticus", "Panellus stipticus", "bajo",
  ["Sombrero de 1,2-3,2 cm, en forma de riñón o concha, convexo a casi plano; fresco amarillo anaranjado a beis o canela, seco tostado o pardo; seco, agrietado en bloques y con pelillos finos que dan un tacto lanoso; borde festoneado y algo enrollado.",
   "Debajo, láminas (no poros) estrechas, apretadas y a menudo bifurcadas, de pardas a beis, con muchas venas transversales.",
   "Pie de 0,5-2 cm de largo y 3-8 mm de grosor, fijado de lado (excéntrico), blanco sucio y con fibrillas sedosas.",
   "Carne fina y tenaz, de sabor ácido, acre o astringente; esporada blanca. En macollas densas y solapadas sobre troncos y tocones de planifolios (haya, roble, abedul); septiembre a noviembre y a veces primavera; los cuerpos secos pueden durar todo el año."],
  ["Esporada parda (sería Crepidotus).", "Sabor suave."],
  [("Especies de Crepidotus", None, "forma parecida, pero con esporada parda y no blanca."),
   ("Schizophyllum commune", None, "sombrero muy peludo blanco a gris con pliegues de láminas partidas a lo largo."),
   ("Panus rudis", None, "mayor, con sombrero pardo rojizo que se aclara a rosa tostado, con tintes lila de joven.")],
  "Eurasia, Australia, Nueva Zelanda, Japón, China y América del Norte. Wikipedia dice que «se considera demasiado pequeña y amarga para comerse» y «no venenosa».",
  dict(s_color="amarillo naranja pardo", s_super="fibrosa", s_forma="convexo", h_tipo="!laminas", h_color="pardo amarillo", p_color="blanco", esporada="blanca", grupo="mechon", habitat="madera planifolio", s_tam="pequeno"))

F("phyllotopsis-nidulans", "Phyllotopsis nidulans", "bajo",
  ["Sombrero de 2-10 cm, naranja claro, en forma de abanico, con la superficie como de pelusa; suelto o en grupos solapados.",
   "Debajo, láminas (no poros) apretadas, naranjas.",
   "Pie muy corto o inexistente.",
   "Olor a tiol, como de col podrida o huevos podridos; esporada de rosa a tostada. Sobre madera muerta o en descomposición, en el hemisferio norte templado."],
  ["Olor agradable o inodoro.", "Láminas que no sean naranjas."],
  [("Phyllotopsis subnidulans", None, "del este de EE. UU.: naranja más intenso, láminas más finas y más separadas."),
   ("Lentinellus ursinus, Crepidotus mollis, Panus rudis, Panus conchatus y Pleurotus ostreatus", None, "Wikipedia las cita como parecidas sin dar diferencias.")],
  "Hemisferio norte templado (hasta Alaska) y Corea. Wikipedia dice que «se considera no comestible»; aunque «no se sabe que sea venenosa», su olor disuade a casi todos de comerla.",
  dict(s_color="naranja", s_super="fibrosa", h_tipo="!laminas", h_color="naranja", esporada="rosa", grupo="mechon", habitat="madera", s_tam="mediano"))

F("volvopluteus-gloiocephalus", "Volvopluteus gloiocephalus (Volvariella gloiocephala)", "alto",
  ["Sombrero de 5-15 cm, ovado o cónico de joven y luego convexo o plano, a veces algo hundido en los viejos; MUY pegajoso en fresco; de blanco a gris o pardo grisáceo.",
   "Debajo, láminas (no poros) apretadas, LIBRES (no tocan el pie), hinchadas en el medio y de hasta 2 cm de ancho: blancas de jóvenes y rosadas con la edad.",
   "Pie de 5-22 cm de largo y 0,7-2,5 cm de grosor, cilíndrico y más ancho hacia la base, blanco, liso o algo polvoriento, con una VOLVA blanca en bolsa de unos 2-3 cm de alto.",
   "Carne blanca que no cambia al cortarla; olor y sabor de indistintos a rábano o patata cruda pelada; esporada pardo rosada. En el suelo de jardines y prados, dentro o fuera de bosques, y sobre compost o astillas, suelta o en grupos."],
  ["Esporada blanca (sería una Amanita).", "Que no tenga volva en bolsa.", "Láminas que siguen blancas con la edad."],
  [("Especies de Amanita", "mortal", "Wikipedia avisa de que los ejemplares jóvenes de láminas blancas pueden confundirse y viceversa; en EE. UU. hubo casos de amanita mortal (Amanita phalloides) tomada por una Volvariella. No da cómo separarlas (aquí: esporada blanca y no rosada)."),
   ("Volvopluteus earlei", None, "menor (sombrero de menos de 5 cm)."),
   ("Volvariella acystidiata", None, "sombrero de hasta 3 cm."),
   ("Volvariella taylori y V. volvacea", None, "Wikipedia las cita como parecidas sin dar diferencias.")],
  "Presente en todos los continentes salvo la Antártida. Wikipedia dice que es «comestible, aunque se considera aguanosa y de baja calidad». El parecido de la volva y las láminas jóvenes con una amanita mortal es la razón del riesgo alto.",
  dict(s_color="blanco gris pardo", s_super="viscosa", s_forma="convexo conico", h_tipo="!laminas", h_color="blanco rosa", p_color="blanco", p_base="!bolsa", corte="nada", esporada="rosa marron", habitat="prado madera", s_tam="grande"))

P("coprinopsis-picacea", "Coprinopsis picacea", "toxica",
  ["Sombrero de hasta 8 cm, ovoide al principio y luego acampanado; blanco de muy joven, después sobre fondo pardo oscuro que se ennegrece, con restos del velo blancos, grises o crema en copos; borde dentado que se enrolla y se disuelve con la edad.",
   "Debajo, láminas (no poros) casi libres y muy apretadas, blancas al principio, luego rojizas, que acaban licuándose en un líquido negro que gotea.",
   "Pie de 12-20 (-30) cm de largo y 6-15 mm de grosor, blanquecino, hueco, algo más fino hacia arriba y cubierto de escamas o fibras finas.",
   "Carne blanquecina, fibrosa y acuosa, a veces con «olor desagradable a naftalina»; sabor desagradable; esporas pardo oscuras. Común en Europa (de Gran Bretaña y Francia a Polonia, Rumanía, España, Italia y Grecia)."],
  "Con Coprinus comatus (Wikipedia dice que se puede confundir a veces; no da cómo separarlas). Wikipedia dice «la especie no es comestible y causa molestias digestivas» y «se la considera venenosa para algunas personas».",
  dict(s_color="blanco pardo negro", s_super="escamas", s_forma="conico", h_tipo="!laminas", h_color="blanco rosa", p_color="blanco", interior="hueco", esporada="negra marron", s_tam="mediano"))

P("entoloma-rhodopolium", "Entoloma rhodopolium", "toxica",
  ["Sombrero de hasta 20 cm, convexo a con mamelón, gris a tostado.",
   "Debajo, láminas (no poros) más claras que el sombrero, que sueltan una esporada rosada.",
   "Pie blanquecino de hasta 13 cm de largo y 2 cm de grosor.",
   "Carne firme y blanca, «quizá con olor a harina». Eurasia; en grupos."],
  "Con Entoloma sarcopum (Wikipedia: «a menudo se confunde» con esta comestible; no da cómo separarlas). Wikipedia dice «la especie es venenosa y causa un trastorno gastrointestinal grave»; se aislaron muscarina, muscaridina y colina.",
  dict(s_color="gris pardo", s_forma="convexo", h_tipo="!laminas", h_color="blanco gris", p_color="blanco", olor="harina", esporada="rosa", s_tam="grande"))

F("entoloma-clypeatum", "Entoloma clypeatum", "alto",
  ["Sombrero de 10-12 cm, pardo o pardo grisáceo, convexo de joven y luego extendido de forma irregular con el borde ondulado en los ejemplares maduros; liso al tacto y con un mamelón central.",
   "Debajo, láminas (no poros) separadas, anchas y escotadas: blancas al principio y rosadas después.",
   "Pie de unos 10 cm de largo y 1-1,5 cm de grosor, blanco o grisáceo, a menudo torcido.",
   "Carnosa. Sale de primavera a principios de verano, normalmente bajo manzanos, perales u otras rosáceas, y a menudo también en bosques de roble o haya sobre suelo rico."],
  ["Esporada que no sea rosada.", "Láminas que no pasen de blancas a rosadas.", "Que no salga en primavera o a principios de verano."],
  [("Otras Entoloma de láminas rosadas", "toxica", "la fuente consultada no cita especies parecidas; en esta guía Entoloma rhodopolium es venenosa y tiene la esporada rosada, y por eso el riesgo se marca alto.")],
  "La Wikipedia en español dice «es comestible» y le da los nombres «macica» y «rodófilo en escudo»; la Enciclopèdia Catalana la valora «bo» con el nombre «bolet de ginesta». Los datos de la Wikipedia en inglés no estaban disponibles (404).",
  dict(s_color="pardo gris", s_super="lisa", s_forma="convexo", h_tipo="!laminas", h_color="blanco rosa", p_color="blanco gris", esporada="rosa", habitat="planifolio", s_tam="grande"),
  ca=["bolet de ginesta"], ca_f="EC", src="ESW")

F("mycena-crocata", "Mycena crocata", "bajo",
  ["Sombrero de hasta 2 cm, blanquecino, cónico de joven y acampanado al madurar.",
   "Debajo, láminas (la capa fértil es naranja).",
   "Pie de hasta 8 cm, hueco, gris crema; al cortarlo SUELTA un látex color azafrán (rojo o naranja).",
   "Aparece en otoño tras las primeras lluvias, entre ramas y hojas caídas en robledales y hayedos (restos de madera y hojarasca de planifolios)."],
  ["Pie que no suelte látex al cortarlo.", "Láminas que no sean naranjas."],
  [("Wikipedia no cita especies parecidas", None, "")],
  "Wikipedia no da datos de comestibilidad ni de toxicidad. Datos de las Wikipedias en inglés y en español.",
  dict(s_color="blanco", s_forma="conico", h_tipo="!laminas", h_color="naranja", p_color="gris blanco", interior="hueco", latex="naranja", habitat="planifolio", s_tam="pequeno"),
  src="ESW")

F("tubaria-furfuracea", "Tubaria furfuracea", "medio",
  ["Sombrero de 1-4 cm, pardo anaranjado, convexo a plano y hundido, con pequeños restos del velo en el borde que desaparecen con la edad o la lluvia.",
   "Debajo, láminas (no poros) pardas, pegadas a algo decurrentes.",
   "Pie de 1-6 cm de alto y 2-4 mm de ancho.",
   "Esporada parda; olor suave. Wikipedia dice que es una especie común, pero no da hábitat."],
  ["Esporada que no sea parda.", "Seta de más de 4 cm."],
  [("Galerina marginata", "mortal", "ambas páginas consultadas la citan como especie parecida (la inglesa dice «puede parecerse»); no dan cómo separarlas."),
   ("Tubaria confragosa y T. conspersa", None, "no se dan diferencias."),
   ("Psilocybe cyanescens y Laccaria", None, "citadas como parecidas, sin diferencias.")],
  "Wikipedia dice «esta especie se considera no comestible» (la española: «es incomestible»); por el parecido con una especie mortal el riesgo se marca medio.",
  dict(s_color="naranja pardo", s_forma="convexo", h_tipo="!laminas", h_color="pardo", esporada="marron", s_tam="pequeno"))

F("craterellus-tubaeformis", "Craterellus tubaeformis (Cantharellus tubaeformis)", "bajo",
  ["Seta en forma de trompeta; sombrero de 1-4 cm, amarillo con tonos pardo grisáceos, en general plano con el centro hundido, en embudo, ceroso y de borde ondulado, a veces hueco por el medio.",
   "Debajo, falsas láminas poco marcadas, decurrentes (bajan por el pie), bifurcadas, separadas y más pálidas que el sombrero (Wikipedia las llama «gills» y otras fuentes las tratan como pliegues).",
   "Pie hueco de 2-12 cm de alto y 1 cm o menos de ancho.",
   "Olor suave; sabor suave (crudo, algo ahumado y picante); esporada naranja rosada clara. En grandes grupos, a menudo tarde en la temporada, sobre musgo o madera podrida en bosques con mucha madera gruesa descompuesta; en conífera, sobre todo en turberas; en el noroeste del Pacífico de noviembre a enero."],
  ["Pliegues o láminas verdaderas apretadas.", "Seta grande y de color amarillo vivo (sería Cantharellus cibarius).", "Pie macizo."],
  [("Craterellus lutescens", "ok", "himenio arrugado sin láminas, color algo distinto y solo en sitios muy húmedos."),
   ("Craterellus odoratus", "ok", "amarillo vivo, con sombrero y pie sin separación."),
   ("Cantharellus cibarius", "ok", "mayor, amarillo y en embudo; sabor más débil pero afrutado."),
   ("Cantharellus californicus y C. formosus", "ok", "Wikipedia las cita como parecidas sin dar diferencias.")],
  "Zonas templadas y frías de América del Norte, Europa (Escandinavia, Finlandia, Rusia, Islas Británicas), Himalaya y Tailandia. Wikipedia dice que «es una excelente seta comestible» y que «aunque pequeña, es selecta». La Enciclopèdia Catalana la valora «bo» con el nombre «camagroc».",
  dict(s_color="amarillo pardo gris", s_forma="embudo", h_tipo="!pliegues laminas", h_color="blanco gris", interior="hueco", esporada="rosa", grupo="corro", habitat="conifera madera", s_tam="pequeno"),
  ca=["camagroc"], ca_f="EC")

F("craterellus-cinereus", "Craterellus cinereus (Cantharellus cinereus)", "bajo",
  ["Seta gris negruzca de hasta 12 cm de alto; sombrero de 1,5-5 cm, en embudo irregular con el borde ondulado y enrollado hacia dentro; negro con humedad y pardusco al secarse o envejecer.",
   "Debajo, venas o crestas (no láminas verdaderas) gris oscuras, bifurcadas e irregulares, separadas y decurrentes (bajan por el pie).",
   "Pie de 2-8 cm de largo y hasta 1,3 cm de grosor, de liso a algo aterciopelado, a veces con la base blanca y lanosa.",
   "Carne fina y gris oscura que se aclara al secarse, de olor indistinto y sabor suave; esporada blanquecina. En suelo con hojarasca de bosques de planifolios (también en coníferas en Europa), suelta o en pequeños grupos; ampliamente repartida pero poco común."],
  ["Láminas verdaderas.", "Seta amarilla o naranja.", "Esporada que no sea blanquecina."],
  [("Craterellus cornucopioides", "ok", "Wikipedia dice que tiene un sabor más intenso que este; no da más diferencias."),
   ("Pseudocraterellus undulatus", "ok", "citada sin diferencias."),
   ("Faerberia carbonaria", "ok", "citada sin diferencias.")],
  "Europa y América del Norte. Wikipedia dice que es «una seta comestible de buen sabor». La Enciclopèdia Catalana la valora «bo» con el nombre «trompeta gris».",
  dict(s_color="gris negro pardo", s_forma="embudo", h_tipo="!pliegues", h_color="gris", p_color="gris", esporada="blanca", habitat="planifolio conifera", s_tam="pequeno"),
  ca=["trompeta gris"], ca_f="EC")

F("gomphus-clavatus", "Gomphus clavatus", "medio",
  ["Cuerpo en forma de vaso o abanico de borde ondulado, de hasta unos 15 cm de ancho y 17-20 de alto; los jóvenes son en maza con un solo sombrero y los viejos se abren en varios sombreros en forma de vaso sobre un pie común; color naranja pardo a lila, que se aclara a pardo con la edad; superficie con motas pardas cerca del borde y capa de pelillos finos en el centro.",
   "Debajo, himenio ARRUGADO, con crestas, pliegues y hoyos (no láminas ni poros), violeta a pardo.",
   "Pie macizo de 1-10 cm de alto y 0,8-3 cm de ancho, continuo con el sombrero, cubierto de pelillos finos, a menudo compuesto (varios cuerpos de una misma base).",
   "Carne blanco rosada a lila o ante canela, crujiente y más blanda que la del rossinyol, que puede tomar tono pardo rojizo al manipularla; olor y sabor suaves; esporada amarilla a amarillo anaranjada. En el suelo, suelta, en grupos o corros, en coníferas (abetos, piceas) y a veces hayas, en sitios húmedos y sombríos; más común por encima de unos 600 m."],
  ["Láminas o poros verdaderos debajo.", "Sombrero con escamas.", "Cuerpo sin forma de vaso o abanico."],
  [("Gomphus crassipes", None, "solo se separa con seguridad con microscopio (esporas más largas)."),
   ("Gomphus ludovicianus", None, "muy parecida a simple vista; Wikipedia no dice cómo separarla."),
   ("Pseudocraterellus pseudoclavatus", None, "bajo coníferas del centro de EE. UU. al oeste; difiere al microscopio y con potasa."),
   ("Turbinellus floccosus y T. kauffmanii", None, "forma parecida pero con el sombrero escamoso."),
   ("Polyozellus multiplex", "ok", "azul violácea, se distingue por las esporas.")],
  "Eurasia y América del Norte. Wikipedia dice que es «comestible», selecta para unos y sin sabor para otros, que algunas personas sufren molestias gástricas, que se pone amarga con la edad y que ejemplares turcos acumulaban cadmio por encima de la ingesta máxima recomendada. La Enciclopèdia Catalana la valora «bo» con el nombre «gots de vi».",
  dict(s_color="naranja pardo violeta", s_forma="embudo", h_tipo="!pliegues", h_color="violeta pardo", interior="macizo", grupo="mechon corro", habitat="conifera planifolio", s_tam="grande"),
  ca=["gots de vi"], ca_f="EC")

F("ramaria-botrytis", "Ramaria botrytis", "alto",
  ["Cuerpo en forma de coral, de hasta 15 cm de ancho y 20 de alto, con ramas densas que salen de una base gruesa y maciza; las ramas están hinchadas en la punta y se dividen en ramitas pequeñas; blanquecinas de jóvenes y después beis o tostadas (su nombre en inglés habla de puntas rosadas).",
   "Sin sombrero ni láminas: las esporas se forman en la superficie exterior de las ramas.",
   "Base corta y gruesa (2-6 cm de largo y 1,5-6 de ancho), que se afina hacia abajo, blanca y luego amarillo pálido a beis o tostada.",
   "Carne gruesa, maciza y blanca, de olor indistinto o agradable y sabor suave o afrutado (ácido en los viejos); esporada amarillenta o amarillo pálido. En el suelo, sola o en pequeños grupos y a veces en corros, en bosques con planifolios (sobre todo haya) y a veces coníferas; en primavera cerca de la nieve que se funde."],
  ["Ramas rosadas con la punta amarilla (sería Ramaria formosa).", "Cuerpo sin ramificar.", "Olor desagradable o sabor amargo."],
  [("Ramaria formosa", "toxica", "Wikipedia dice que tiene las ramas más rosadas y con las puntas amarillas; una guía avisa de confundirla con ella por su toxicidad."),
   ("Ramaria subbotrytis", None, "rosa a rojizo uniforme."),
   ("Ramaria araiospora", None, "bajo cicuta; ramas magenta con puntas naranja a amarillentas y sin olor."),
   ("Otras Ramaria (rubrievanescens, strasseri, caulifloriformis, rielii…)", None, "se separan casi siempre por el color de las puntas y al microscopio.")],
  "América del Norte, Europa, Asia, Australia, África (Túnez), Chile, México y Guatemala. Wikipedia dice que es «comestible» y que algunos la tienen por selecta; una guía la da como «cuestionable» y avisa del parecido con la tóxica Ramaria formosa; algunos autores avisan de efectos laxantes y de que acumula arsénico. La Enciclopèdia Catalana la valora «bo» con el nombre «peu de rata col-i-flor».",
  dict(s_color="blanco pardo rosa", h_tipo="!liso", p_color="blanco pardo", interior="macizo", grupo="corro", habitat="planifolio conifera", s_tam="grande"),
  ca=["peu de rata col-i-flor"], ca_f="EC")

F("sparassis-crispa", "Sparassis crispa", "bajo",
  ["Cuerpo en forma de bola enmarañada de hasta 24 cm de ancho (los grandes pesan 14 kg o más), formado por lóbulos planos y ondulados que recuerdan láminas de lasaña; blanco a amarillo crema.",
   "Sin sombrero ni láminas: el himenio cubre los lóbulos.",
   "Carne dura y como de goma de joven y blanda después, de olor agradable y sabor suave; esporada crema.",
   "Parásita al pie de troncos de coníferas (a menudo pinos, también pícea, cedro, alerce), que produce podredumbre parda; de julio a noviembre en Gran Bretaña y Europa templada."],
  ["Lóbulos rizados muy finos y zonados (sería Sparassis brevipes).", "Que no crezca al pie de coníferas."],
  [("Sparassis brevipes", None, "en Europa: menos rizada, con pliegues zonados y sin conexiones en gancho."),
   ("Sparassis radicata y S. spathulata", None, "Wikipedia las cita (la primera quizá sinónima) sin decir cómo separarlas.")],
  "Europa, América del Norte. Wikipedia dice que «se considera una buena seta comestible cuando es joven y fresca» y que cuesta limpiarla. La Enciclopèdia Catalana la valora «bo» con el nombre «peu de rata de pi».",
  dict(s_color="blanco amarillo", h_tipo="!liso", esporada="blanca", habitat="conifera madera", s_tam="grande"),
  ca=["peu de rata de pi"], ca_f="EC")

P("ramaria-formosa", "Ramaria formosa", "toxica",
  ["Cuerpo en forma de coral rosado y muy ramificado, de hasta unos 20-30 cm de alto y 15 de ancho, con ramas rosadas de punta AMARILLA que salen de una base gruesa; las ramas terminales miden menos de 0,5 cm de grosor.",
   "Sin sombrero ni láminas.",
   "Carne blanca, con rosa en el medio o naranja pálido; puede tomar tono vino o negruzco al magullarla; los viejos se decoloran. Olor desagradable y sabor amargo.",
   "Sale en otoño asociada al haya en Europa (en Chipre, quizá al roble Quercus alnifolia). Las colecciones norteamericanas parecidas se consideran otra especie."],
  "Con Ramaria botrytis (que Wikipedia dice que tiene las ramas menos rosadas y sin puntas amarillas) y con R. leptoformosa, R. neoformosa, R. raveneliana y R. rubricarnata (ramas salmón de punta amarilla; se separan sobre todo al microscopio). Wikipedia dice que «se tiene por levemente venenosa»: provoca síntomas gastrointestinales agudos (náuseas, vómitos, cólicos, diarrea; toxinas desconocidas); se ha citado como comestible quitando las puntas acres, y una guía aconseja evitar todos los corales viejos. La Enciclopèdia Catalana la pone como tóxica con el nombre «peu de rata bord».",
  dict(s_color="rosa naranja amarillo", h_tipo="!liso", p_color="blanco", habitat="planifolio", s_tam="grande"),
  ca=["peu de rata bord"], ca_f="EC")

F("sarcodon-imbricatus", "Sarcodon imbricatus (Hydnum imbricatum)", "medio",
  ["Sombrero pardusco o beis de hasta 15 cm (Wikipedia dice que puede llegar a 30), en embudo y cubierto de escamas gruesas y más oscuras que se levantan y oscurecen con la edad.",
   "Debajo, PÚAS (no láminas) blandas, quebradizas, gris pálido, de 0,5-1,5 cm de largo, que se oscurecen a gris pardo con la edad.",
   "Pie gris pálido o pardo de hasta 10 cm de alto y 4 de ancho, a veces excéntrico y más fino en la base.",
   "Carne blanda, de blanquecina a tostada; sabor posiblemente amargo, sobre todo en los viejos; esporada parda. Con piceas (también pino y abeto), sobre todo en zonas de colinas o montaña; en suelos arenosos o calizos, a veces en corros; agosto a octubre en Europa."],
  ["Láminas o poros debajo.", "Raya azul negruzca en el pie (sería Sarcodon amarascens).", "Base del pie turquesa (sería Hydnellum scabrosum)."],
  [("Strobilomyces strobilaceus", None, "visto desde arriba tiene un sombrero peludo parecido."),
   ("Sarcodon amarascens", "nocom", "amarga y no comestible; se distingue por una raya azul negruzca."),
   ("Hydnellum scabrosum", None, "amarga; se distingue por la base turquesa.")],
  "Europa y América del Norte (las colecciones de las Islas Británicas se asignan ahora a S. squamosus). Wikipedia dice que «la seta es comestible, pero puede ser amarga y posiblemente cause molestias gastrointestinales»; algunas fuentes de EE. UU. la dan por comestible de mala calidad y otras por deliciosa.",
  dict(s_color="pardo", s_super="escamas", s_forma="embudo", h_tipo="!puas", h_color="gris pardo", p_color="gris pardo", esporada="marron", grupo="corro", habitat="conifera", s_tam="grande"))

F("hydnellum-ferrugineum", "Hydnellum ferrugineum", "bajo",
  ["Sombrero de 3-10 cm, convexo y luego en cojín, a veces aplanado o hundido en el centro; de joven con superficie irregular y de afelpada a como fieltro, blanquecina a rosa, que a veces suelta gotas rojo sangre; al madurar color carne a pardo rojizo oscuro, con el borde ondulado y blanquecino.",
   "Debajo, púas densas (no láminas), blancas a pardo rojizas, de hasta 6 mm, colgando hacia abajo.",
   "Pie robusto de 1-6 cm de alto y 1-3 de grosor, del color del sombrero; en los viejos la carne del pie puede ennegrecer.",
   "Carne rojiza o pardo púrpura con motas blancas, primero esponjosa y blanda y luego dura y corchosa, de olor claramente a harina. En el suelo de bosques de coníferas (sobre todo pinos), en suelos arenosos pobres; suelta o en grupos."],
  ["Láminas o poros debajo.", "Carne sin olor a harina."],
  [("Hydnellum peckii", None, "parecida, pero de sabor acre y con conexiones en gancho en las hifas."),
   ("Hydnellum spongiosipes", None, "se confunde fácilmente; sombrero joven y carne más oscuros, y crece en bosques caducifolios."),
   ("Hydnellum concrescens", None, "los ejemplares viejos pueden confundirse con esta.")],
  "Norte de África, Asia, Europa y América del Norte; en Gran Bretaña está provisionalmente en peligro y protegida por ley. Wikipedia dice «no comestible».",
  dict(s_color="rosa pardo rojo", s_forma="convexo", h_tipo="!puas", h_color="blanco pardo", p_color="pardo rojo", olor="harina", habitat="conifera", s_tam="mediano"))

F("pseudocraterellus-undulatus", "Pseudocraterellus undulatus (Craterellus sinuosus)", "bajo",
  ["Seta pequeña en embudo; sombrero de 1-5 cm, al principio convexo o hundido y luego en embudo con el borde irregular y arrugado (Wikipedia no da el color del sombrero).",
   "Debajo, himenio arrugado y ramificado (crestas, no láminas verdaderas), gris pardo, separado y decurrente (baja por el pie).",
   "Pie de 3-6 cm de largo, afilado hacia abajo, a menudo acanalado y torcido; ejemplares vecinos pueden fundirse por encima de la base.",
   "Carne tenaz y gris, de olor leve e indefinido y sabor suave; esporada blanca a amarillo pálido. En el suelo y la hojarasca de bosques de planifolios, con haya, avellano y roble; sola o en grupos pequeños a veces unidos; de verano a otoño; extendida pero solo ocasional."],
  ["Láminas verdaderas.", "Esporada que no sea blanca a amarillo pálido."],
  [("Craterellus cinereus", "ok", "la página de esa especie la cita como parecida sin dar diferencias.")],
  "Wikipedia dice que «se considera una seta comestible de sabor suave» y que «quizá crece demasiado raramente para que valga la pena recogerla».",
  dict(s_forma="embudo", h_tipo="!pliegues", h_color="gris pardo", esporada="blanca", habitat="planifolio", s_tam="pequeno"))

F("clavulina-coralloides", "Clavulina coralloides (Clavulina cristata)", "bajo",
  ["Seta en forma de coral, blanca a color crema, de hasta unos 8 cm de alto y 2,5-4 cm de ancho; los «brazos» se ramifican poco (3-4 veces), miden 2-4 mm de ancho, son lisos o algo arrugados a lo largo y tienen las puntas en forma de cresta con pequeñas puntas agudas; se oscurecen con la edad o el tiempo seco.",
   "Sin sombrero ni láminas.",
   "Base de 5-40 mm de largo y 5-20 de ancho, de forma variable.",
   "Carne tenaz, de olor poco claro y sabor suave; esporas blancas. En el suelo, sola o en grupos, a veces sobre madera podrida; en bosques de coníferas y planifolios; de junio a noviembre en Europa."],
  ["Ramas muy finas y paralelas sobre madera (sería Ramaria stricta).", "Cuerpo sin ramificar (sería Clavulina rugosa)."],
  [("Clavulina rugosa", None, "sin ramificar o poco ramificada."),
   ("Clavulina cinerea", None, "normalmente más oscura; esta puede oscurecerse y confundirse."),
   ("Ramaria stricta", None, "ramas paralelas y crece sobre madera."),
   ("Lentaria byssiseda", None, "pardo claro con puntas blancas."),
   ("Ramariopsis kunzei", None, "a menudo blanco brillante y liso."),
   ("Sebacina schweinitzii", None, "muy tenaz.")],
  "Común en América templada y Europa. Wikipedia dice que «este hongo es comestible», que su carne tenaz e insustancial lo hace poco apetecible para algunos y que «algunos lo consideran excelente».",
  dict(s_color="blanco", h_tipo="!liso", esporada="blanca", habitat="conifera planifolio madera", s_tam="pequeno"))

F("ramaria-stricta", "Ramaria stricta", "bajo",
  ["Cuerpo en forma de coral, tupido, de hasta unos 10 cm de alto y 10 x 7 de ancho, formado por varias ramas finas, compactas y erguidas, casi paralelas, ramificadas hasta 8 veces y que acaban cada una en 4-5 puntas como espinas; color tostado claro a pardo vinoso, más pardo o amarillento y más pálido hacia las puntas; correoso en fresco y quebradizo seco.",
   "Sin sombrero ni láminas.",
   "Base blanquecina, simple o ramificada, de la que salen micelio blanco y rizomorfos.",
   "Todo el cuerpo se mancha de pardo rojizo claro al manipularlo; olor a anís y sabor amargo; esporada amarillo oscuro. Sobre madera muerta, tocones, troncos y ramas de planifolios y coníferas (a veces en «líneas» sobre madera enterrada); cosmopolita."],
  ["Que no crezca sobre madera (así son las Ramaria de suelo).", "Sin sabor amargo."],
  [("Ramaria apiculata y R. gracilis", None, "sobre madera de coníferas; apiculata mancha pardo y tiene pigmento verde; gracilis tiene colores más claros."),
   ("Ramaria flava", None, "micorrícica bajo coníferas y planifolios, más alta, de olor desagradable más fuerte y menos amarga."),
   ("Ramaria rubella (R. acris)", None, "tostado rosado."),
   ("Ramaria tsugina", None, "mancha de verde.")],
  "Cosmopolita; común a finales de verano y otoño en bosques de coníferas de la costa del Pacífico y las Rocosas. Wikipedia dice que antes se daba por «comestible pero poco sabrosa», que las guías posteriores la dan por no comestible y que lo es «por su olor desagradable y su sabor amargo».",
  dict(s_color="pardo", h_tipo="!liso", p_color="blanco", corte="enrojece", habitat="madera conifera planifolio", s_tam="mediano"))

F("scutiger-pes-caprae", "Scutiger pes-caprae (Albatrellus pes-caprae)", "medio",
  ["Sombrero de 6-20 cm, pardusco, convexo y algo en forma de riñón, a veces lobulado, que se aplana con la edad.",
   "Debajo, POROS blanquecinos (1-2 por mm) que pueden volverse rosados o verdosos; tubos de hasta 5 mm, normalmente decurrentes (bajan por el pie).",
   "Pie de 2,5-8 cm de largo y 1-4 de grosor, normalmente más ancho en la base, donde pueden unirse varias setas.",
   "Carne de 5-20 mm de grosor, blanquecina, que se vuelve rosada despacio al herirla, de sabor suave; esporada blanquecina. Bajo coníferas y sobre madera podrida (en Norteamérica de agosto a febrero)."],
  ["Poros amarillos o láminas.", "Carne que se pone azul o negra al cortarla."],
  [("Scutiger ellisii, Laeticutis cristata y Jahnoporus hirtus", None, "Wikipedia dice que «guardan parecido» sin explicar cómo se separan.")],
  "Oeste de Norteamérica y Europa, ligada a coníferas y madera podrida. Wikipedia dice que los sombreros jóvenes europeos son «potencialmente comestibles» y que, tras cocinarlos a fondo, se dice que son comestibles «pero correosos». La Enciclopèdia Catalana la valora «molt bo» con el nombre «sabatera».",
  dict(s_color="pardo", s_forma="convexo", h_tipo="!poros", h_color="blanco", corte="enrojece", grupo="mechon", habitat="conifera madera", s_tam="grande"),
  ca=["sabatera"], ca_f="EC")

F("grifola-frondosa", "Grifola frondosa", "medio",
  ["Mata de hasta 50 cm (rara vez 150) formada por muchos sombreros pequeños de 2-10 cm, gris pardo, a menudo enrollados o en forma de cuchara, de borde ondulado; se ponen duros al madurar.",
   "Debajo, POROS (no láminas ni púas), 1-3 por mm, con tubos de menos de 3 mm.",
   "Pie crema y ramificado, común a toda la mata.",
   "Esporada blanca. Al pie de árboles viejos, sobre todo robles y arces; sale de un esclerocio subterráneo del tamaño de una patata; perenne (vuelve varios años al mismo sitio); de agosto a octubre en Europa."],
  ["Mata que se ennegrece al tocarla (sería Meripilus).", "Sombreros redondeados y bien separados (sería Polyporus umbellatus).", "Que no salga de la base de un árbol."],
  [("Meripilus sumstinei", None, "se tiñe de negro; su sabor es parecido pero es gomosa."),
   ("Polyporus umbellatus", None, "tiene sombreros redondeados bien diferenciados."),
   ("Sparassis spathulata y Laetiporus sulphureus", None, "Wikipedia las cita como parecidas sin explicar cómo se separan.")],
  "China, Europa y este de Norteamérica. Wikipedia dice que es «una seta comestible selecta», sobre todo los sombreros jóvenes cocinados despacio, «aunque algunas personas pueden ser alérgicas», y que no hay pruebas clínicas de calidad de que sirva como medicina. La Enciclopèdia Catalana la valora «molt bo» con los nombres «jove» y «gírgola de castanyer».",
  dict(s_color="gris pardo", h_tipo="!poros", p_color="blanco", esporada="blanca", grupo="mechon", habitat="planifolio madera", s_tam="pequeno mediano"),
  ca=["jove", "gírgola de castanyer"], ca_f="EC")

P("albatrellus-ovinus", "Albatrellus ovinus (Scutiger ovinus)", "nocom",
  ["Sombrero de 4-20 cm, convexo y luego plano o hundido; blanco que pasa a tostado o rosado; seco y liso, que se agrieta con la edad.",
   "Debajo, poros (Wikipedia solo lo cita en el pie de una foto).",
   "Pie de 2,5-10 cm de alto y 1-4 de ancho, blanquecino, quizá ramificado, igual o más ancho en la base.",
   "Esporada blanca. Terrestre, en el norte de Europa y en Norteamérica."],
  "Con Albatrellus subrubescens (colores algo distintos; solo las esporas de esta son amiloides; Wikipedia la da por no comestible y relativamente rara), y con A. flettii, Jahnoporus hirtus, Scutiger ellisii y S. pes-caprae (parecidas, sin diferencias). Wikipedia dice que «puede ser comestible si se cocina a fondo», que «suele ser viscosa y puede tener efecto laxante» y que «algunas guías no la recomiendan». La Enciclopèdia Catalana la valora «bo» con el nombre «barbes de boc».",
  dict(s_color="blanco pardo rosa", s_super="lisa", s_forma="convexo", h_tipo="!poros", p_color="blanco", esporada="blanca", s_tam="grande"),
  ca=["barbes de boc"], ca_f="EC")

F("auricularia-auricula-judae", "Auricularia auricula-judae", "bajo",
  ["Cuerpo de hasta 9 cm de ancho y 3 mm de grosor, a menudo con forma de oreja (a veces de copa); cara superior pardo rojiza con tinte púrpura, con fino pelo gris; liso de joven y ondulado con pliegues y arrugas de viejo; GELATINOSO y elástico en fresco, duro y quebradizo seco.",
   "Cara de abajo (el himenio) lisa, gris pardo más claro, a veces plegada o con «venas»; se une de lado a la madera, a veces por un pie muy corto.",
   "Carne tenaz, gelatinosa y elástica; sabor suave, «quizá insípido»; esporas en forma de salchicha.",
   "Sobre madera de planifolios y arbustos, sobre todo saúco (también sicomoro, haya, fresno y bonetero); casi sin excepción en coníferas no; todo el año, sobre todo en otoño."],
  ["Cuerpo duro y leñoso (no gelatinoso).", "Que crezca sobre conífera."],
  [("Auricularia cerrina", None, "europea sobre roble, de color gris oscuro a casi negro."),
   ("Auricularia heimuer", None, "asiática; se distingue al microscopio."),
   ("Auricularia angiospermarum", None, "americana; se distingue al microscopio.")],
  "Toda Europa (Wikipedia no la da en otros continentes). Wikipedia dice que «es comestible pero poco consumida», «no tiene gran valor culinario» y «no se puede comer cruda: hay que cocinarla a fondo». La Enciclopèdia Catalana la valora «acceptable» con el nombre «orella de Judes».",
  dict(s_color="pardo rojo violeta", s_super="fibrosa", h_tipo="!liso", h_color="gris pardo", grupo="mechon", habitat="madera planifolio", s_tam="pequeno mediano"),
  ca=["orella de Judes"], ca_f="EC")

F("fistulina-hepatica", "Fistulina hepatica", "bajo",
  ["Cuerpo de 7-30 cm de ancho y 2-6 de grosor, en forma de lengua y de superficie rugosa; rojo rosado de joven y pardo rojizo con la edad.",
   "Debajo, tubos (poros) de color blanco crema, formados por pequeñas copas lisas (no láminas).",
   "Pie, si lo hay, de hasta 5 cm de largo y 4 de ancho.",
   "Al cortarla «sangra» un jugo rojo apagado que mancha; la carne recuerda a carne cruda y su sabor es ácido; esporada rosada. En roble y castaño, vivos o muertos; de agosto a finales de otoño (julio a octubre en Europa)."],
  ["Que no «sangre» al cortarla.", "Que no crezca sobre roble o castaño."],
  [("Pseudofistulina radicata, Amylocystis lapponica, Ischnoderma resinosum, Leptoporus mollis y Rhodofomes cajanderi", None, "Wikipedia las cita como parecidas sin explicar cómo se separan.")],
  "Europa, África, Australia y Norteamérica. Wikipedia dice que «es comestible cocinada» y que el jugo de los ejemplares viejos puede causar molestias gástricas. La Enciclopèdia Catalana la valora «acceptable» con el nombre «fetge de vaca».",
  dict(s_color="rojo rosa pardo", h_tipo="!poros", h_color="blanco", esporada="rosa", habitat="madera planifolio", s_tam="grande"),
  ca=["fetge de vaca"], ca_f="EC")

F("pseudohydnum-gelatinosum", "Pseudohydnum gelatinosum", "bajo",
  ["Cuerpo gelatinoso, blanquecino a gris claro o tostado, de 2-7 cm de ancho y de alto.",
   "Debajo, PÚAS (no láminas) de hasta 3 mm de largo.",
   "Los ejemplares occidentales de Norteamérica suelen tener un pie vertical bien marcado y los orientales no.",
   "Consistencia gelatinosa; sabor «poco o nada»; esporada blanca. Sobre madera muerta de coníferas."],
  ["Cuerpo duro y no gelatinoso.", "Sin púas debajo."],
  [("Wikipedia no cita especies parecidas", None, "")],
  "Eurasia (los datos de ADN la sitúan en Europa y el norte de Asia). Wikipedia dice que es «comestible, quizá incluso cruda, aunque mejora marinada» y que se consume en Bulgaria, Rusia y Siberia. La Enciclopèdia Catalana la valora «acceptable» con el nombre «orella de vaca blanca».",
  dict(s_color="blanco gris pardo", h_tipo="!puas", esporada="blanca", habitat="conifera madera", s_tam="pequeno"),
  ca=["orella de vaca blanca"], ca_f="EC")

F("phlogiotis-helvelloides", "Phlogiotis helvelloides (Guepinia helvelloides)", "bajo",
  ["Cuerpo de 4-10 cm de alto y hasta 17 de ancho, en forma de oreja o cuchara, retorcido como un cuerno en un embudo estrecho y abierto por un lado, con el borde a menudo ondulado; flexible; color salmón rosado (de naranja rojizo transparente a rosa carne), pardo si es viejo.",
   "Sin láminas, poros ni púas: el himenio está en la cara de fuera, de color algo más vivo que la de dentro; lisa.",
   "Pie de hasta 5 cm de alto y 1,5 de grosor, con la base cubierta de pelusa blanca; sombrero y pie no se distinguen bien.",
   "Carne gelatinosa y de goma, de olor corriente y sabor acuoso; esporada blanca. En el suelo, con micelio en madera podrida enterrada, suelta o en pequeñas macollas; en primavera a veces, más común en verano y otoño; en América del Norte con coníferas."],
  ["Superficie arrugada y de textura no gelatinosa (sería Cantharellus cinnabarinus).", "Cuerpo pequeño y en espátula (sería Dacryopinax)."],
  [("Cantharellus cinnabarinus", None, "no es de goma ni gelatinosa y tiene el himenio de abajo arrugado, no liso."),
   ("Dacryopinax spathularia", None, "forma cuerpos pequeños."),
   ("Spathulariopsis velutipes", None, "tiene la cabeza blanca.")],
  "Muy extendida en el hemisferio norte (Norteamérica, Europa, Irán, Turquía, China). Wikipedia dice que es «comestible, pero insípida» y que las viejas son duras e indigestas. La Enciclopèdia Catalana la valora «acceptable» con el nombre «cresta de gall».",
  dict(s_color="rosa naranja", s_forma="embudo", h_tipo="!liso", esporada="blanca", habitat="conifera", s_tam="mediano"),
  ca=["cresta de gall"], ca_f="EC")

F("fomes-fomentarius", "Fomes fomentarius", "bajo",
  ["Cuerpo de 5-45 cm de ancho y 2-25 de grosor, normalmente en forma de pezuña (a veces más en repisa); de gris plateado a casi negro, normalmente pardo; superficie dura, leñosa y bultuda, con anchas crestas concéntricas, borde romo y redondeado y borde blanquecino mientras crece; corteza de 1-2 mm.",
   "Debajo, poros redondos, crema al principio y pardos con la madurez, que oscurecen al tocarlos; 2-3 por mm; tubos de 2-7 mm, pardo óxido.",
   "Sin pie: se fija ancho al árbol.",
   "Carne dura y fibrosa, canela pardo, de sabor acre y olor algo afrutado. En troncos de planifolios: abedul en el norte, haya en el sur, roble en el Mediterráneo; crece más de principios de verano a otoño."],
  ["Que crezca sobre suelo o que sea blando.", "Una gota de potasa (KOH) en la parte superior que no la tiña de rojo sangre oscuro."],
  [("Phellinus igniarius, especies de Ganoderma y Fomitopsis pinicola", None, "Wikipedia las cita como parecidas; una gota de potasa sobre la superficie superior se pone rojo sangre oscuro en Fomes fomentarius (por el fomentariol).")],
  "Circumboreal (Europa, Asia, África, Norteamérica). Wikipedia dice «la especie no se considera comestible».",
  dict(s_color="gris pardo negro", s_forma="convexo", h_tipo="!poros", h_color="blanco pardo", interior="macizo", habitat="madera planifolio", s_tam="grande"))

F("fomitopsis-pinicola", "Fomitopsis pinicola", "bajo",
  ["Cuerpo en forma de pezuña o triangular, a veces en repisa, duro y tenaz, de 30 cm o más de ancho y hasta 15 de grosor; superficie más o menos lisa; naranja amarillo con borde blanco al principio y luego rojo oscuro a pardo, a menudo con borde naranja.",
   "Debajo, poros pálidos a pardo cuero (3-4 por mm), blanquecinos de jóvenes y algo pardos con la edad; perenne (cada año se forma una capa nueva de poros).",
   "Sin pie: crece en repisas gruesas sobre los árboles o como una capa de tubos sobre madera caída.",
   "Carne leñosa y tenaz. Sobre coníferas vivas y muertas (sobre todo pinos muertos), menos en planifolios; heridas del tronco y copas rotas."],
  ["Que crezca sobre suelo o que sea blando."],
  [("Ganoderma lucidum, Laricifomes officinalis y Heterobasidion annosum", None, "Wikipedia las cita como parecidas sin explicar cómo se separan.")],
  "Muy común en la Eurasia templada. Wikipedia dice «esta seta no es comestible» (por su textura leñosa).",
  dict(s_color="naranja rojo pardo", s_super="lisa", s_forma="convexo", h_tipo="!poros", h_color="amarillo pardo", interior="macizo", habitat="conifera madera", s_tam="grande"))

F("trametes-versicolor", "Trametes versicolor (Coriolus versicolor)", "bajo",
  ["Cuerpo algo en forma de lengua, sin pie, de hasta 10 cm de ancho, plano, a menudo triangular o redondo; superficie con zonas de pelos finos de color pardo óxido o más oscuro, a veces con zonas negras; los viejos pueden llevar algas verdes.",
   "Debajo, poros (3-5 por mm) blanquecinos a pardo claro, redondos de jóvenes y torcidos y laberínticos con la edad, con zonas concéntricas y el borde más claro.",
   "Carne tenaz, de 1-3 mm de grosor, blanquecina bajo una capa negra.",
   "En grupos o filas en capas como tejas sobre troncos y tocones de planifolios; cosmopolita."],
  ["Superficie de abajo lisa y sin poros (sería Stereum ostrea).", "Que no crezca sobre madera."],
  [("Stereum ostrea (falsa cola de pavo)", None, "Wikipedia dice que las Stereum suelen tener la cara de abajo lisa, sin poros."),
   ("Trametes hirsuta, T. ochracea, T. suaveolens, Bjerkandera adusta, Cerrena unicolor, Lenzites betulinus y Stereum hirsutum", None, "Wikipedia las cita como parecidas sin dar más diferencias.")],
  "Se encuentra en todo el mundo. Wikipedia dice que se considera «demasiado dura para comerla», aunque se prepara como té o polvo.",
  dict(s_color="pardo negro gris", s_super="fibrosa", h_tipo="!poros", h_color="blanco pardo", grupo="mechon", habitat="madera planifolio", s_tam="pequeno mediano"))

F("trametes-gibbosa", "Trametes gibbosa", "bajo",
  ["Cuerpo de 8-15 cm de ancho (hasta 20), en repisa y semicircular; superficie gris o blanca, a veces verdosa en los viejos por las algas, irregular y aterciopelada, con pelos que piden aumento; los jóvenes son blancos o crema y con la edad se vuelven grisáceos.",
   "Debajo, poros alargados (1-3 por mm), blancos o crema y grisáceos con la edad; algunos ejemplares los tienen laberínticos o como láminas.",
   "Sin pie.",
   "Carne de textura leñosa y sin sabor claro; esporada blanca (difícil de obtener). Sobre tocones de haya y madera muerta de otros planifolios; todo el año."],
  ["Poros redondos o angulosos en vez de alargados (sería Trametes lactinea).", "Que no crezca sobre madera."],
  [("Trametes versicolor", None, "puede parecerse a algunas Stereum, que tienen la cara de abajo lisa y sin poros."),
   ("Trametes aesculi", None, "poros más variables, circulares o laberínticos; la superficie se vuelve lisa con la madurez; esporas mayores."),
   ("Trametes elegans", None, "parecida pero no se da ni en Europa ni en Norteamérica."),
   ("Trametes lactinea", None, "las formas blanquecinas o grises son iguales, con poros redondos o angulosos en vez de alargados.")],
  "Eurasia y Norteamérica. Wikipedia no da datos de comestibilidad; sí dice que la textura es leñosa.",
  dict(s_color="gris blanco", s_super="fibrosa", h_tipo="!poros", h_color="blanco", esporada="blanca", habitat="madera planifolio", s_tam="grande"))

F("ganoderma-lucidum", "Ganoderma lucidum", "bajo",
  ["Cuerpo de hasta 35 cm de ancho, en forma de abanico, rojizo (de rojo a pardo púrpura), con la superficie brillante como lacada (laqueada).",
   "Debajo, poros (4-5 por mm) con tubos pegados.",
   "Pie presente casi siempre, de 1,5 veces el diámetro del sombrero, color leonado a rojizo.",
   "Carne corchosa, de rosa ante a canela ante, con zonas de crecimiento concéntricas; muy dura al secarse; esporas pardas. Sobre madera de planifolios en descomposición, sobre todo tocones de ciruelo o roble; en Europa de distribución limitada."],
  ["Superficie mate y sin brillo de laca.", "Cuerpo blando o carnoso."],
  [("Ganoderma sichuanense (G. lingzhi)", None, "se confunde a menudo con ella y solo se separa con análisis de ADN."),
   ("Ganoderma tsugae y G. oregonense", None, "los parientes más cercanos; Wikipedia no da cómo reconocerlos."),
   ("Ganoderma applanatum y otras", None, "se han encontrado en productos vendidos como G. lucidum.")],
  "China, Japón, Norteamérica y selvas tropicales; en Europa limitada. Wikipedia dice «la especie no es comestible y es muy dura al secarse» y que su uso como complemento tiene «problemas de seguridad e interacciones con medicamentos»; no hay pruebas clínicas de calidad para ninguna enfermedad.",
  dict(s_color="rojo pardo violeta", s_super="lisa", h_tipo="!poros", p_color="pardo naranja", esporada="marron", habitat="madera planifolio", s_tam="grande"))

F("ganoderma-applanatum", "Ganoderma applanatum", "bajo",
  ["Cuerpo en repisa de 3-30 cm de ancho, 5-50 de largo y 1-10 de grosor (a veces hasta 75 cm); duro como el cuero, de textura leñosa; superficie pardo cubierta de pardo rojizo, con anillos concéntricos que marcan las capas anuales; perenne, persiste varios años.",
   "Debajo, poros redondos (4-6 por mm), tubos de 4-12 mm; blanco que se mancha de pardo, y al rascar el poro fresco aparece pardo oscuro debajo.",
   "Sin pie.",
   "Carne dura como cuero, leñosa; esporada pardo rojiza. Parásita y saprófita sobre madera de árboles vivos y muertos (sobre todo haya y álamo; también aliso, manzano, olmo, arce, roble, nogal, sauce, abeto, picea…); cosmopolita."],
  ["Poros que no manchan de pardo al rascarlos.", "Que no crezca sobre madera."],
  [("Ganoderma brownii", None, "más gruesa, con carne más oscura, a menudo poros amarillos y esporas mayores."),
   ("Fomes fasciatus", None, "esporada blanca."),
   ("Ganoderma oregonense, G. lucidum y Fomitopsis pinicola", None, "Wikipedia las cita como parecidas sin dar diferencias.")],
  "Cosmopolita. Wikipedia dice que «no es digerible cruda» por su dureza (se usa como cultivo medicinal y potenciador de sabor en la cocina asiática); no da más datos de comestibilidad.",
  dict(s_color="pardo", h_tipo="!poros", h_color="blanco", interior="macizo", esporada="marron", habitat="madera planifolio", s_tam="grande"))

F("laetiporus-sulphureus", "Laetiporus sulphureus", "medio",
  ["Repisas amarillo azufre a naranja vivo en capas solapadas, en abanico (al principio como un bulto), con superficie como de ante; cada repisa mide 5-60 cm de ancho y 4-12 de grosor; normalmente en macollas; las viejas se decoloran a tostado, blanquecino o gris pálido.",
   "Debajo, POROS (tubos) amarillo azufre, no láminas.",
   "Sin pie: se fija a troncos y ramas.",
   "Carne fresca jugosa, de olor fúngico fuerte, que suelta un jugo amarillento transparente y luego se seca y quiebra; esporada blanca. Sobre planifolios muertos o maduros (roble, cerezo, peral, álamo, sauce, robinia, haya) y a veces coníferas; en el Mediterráneo, sobre todo algarrobo y eucalipto; de abril a noviembre en Europa."],
  ["Que no crezca sobre madera.", "Poros blancos.", "Ejemplar viejo, seco y quebradizo."],
  [("Laetiporus persicinus", None, "«bastante distinta» pero puede parecerse; Wikipedia no da diferencias."),
   ("Laetiporus huroniensis", None, "crece sobre cicuta (se separa por el árbol)."),
   ("Laetiporus gilbertsonii", None, "crece sobre eucalipto (se separa por el árbol).")],
  "Europa y Norteamérica. Wikipedia dice: «a diferencia de muchos hongos de repisa, es comestible cuando es joven, aunque se han descrito reacciones adversas», que los jóvenes lo son «si sueltan mucho líquido claro a amarillo pálido», que «no debe comerse cruda», que algunas personas han tenido molestias gastrointestinales y que las reacciones graves (vómitos, fiebre) en un 10 % de personas se atribuyen ahora a confusión con especies parecidas.",
  dict(s_color="amarillo naranja", h_tipo="!poros", h_color="amarillo", esporada="blanca", grupo="mechon", habitat="planifolio madera", s_tam="grande"))

F("piptoporus-betulinus", "Fomitopsis betulina (Piptoporus betulinus)", "bajo",
  ["Cuerpo en repisa, pálido, con la parte de arriba pardo grisácea y lisa; crece saliendo de la corteza del abedul.",
   "Debajo, cientos de POROS blanco crema.",
   "Sin pie.",
   "Carne gomosa que se vuelve corchosa con la edad, con la superficie cortada «aterciopelada»; la madera podrida y los cultivos de micelio huelen a manzana verde. Casi exclusivamente sobre abedul (parásita de abedules debilitados y común en abedules muertos); el cuerpo puede durar más de un año."],
  ["Que no crezca sobre abedul."],
  [("Wikipedia no cita especies parecidas", None, "")],
  "Hemisferio norte (Norteamérica, Europa, Asia). Wikipedia dice «se considera no comestible» (excepto, quizá, joven).",
  dict(s_color="gris pardo blanco", s_super="lisa", h_tipo="!poros", h_color="blanco", interior="macizo", habitat="planifolio madera"))

F("meripilus-giganteus", "Meripilus giganteus", "bajo",
  ["Mata de muchos sombreros aplanados en abanico, en roseta; la mata mide 50-150 cm de ancho y 10-50 de alto, y cada sombrero 10-50 cm de ancho y 1-5 de grosor, unidos en una base común; pesa 10-50 kg; color tostado pálido a pardo castaño apagado, que se oscurece con zonas concéntricas pardas; superficie finamente fibrosa con escamitas.",
   "Debajo, POROS (3-6 por mm) que se ennegrecen enseguida al magullarlos o herirlos.",
   "Sin pie definido: los sombreros salen de una base común.",
   "Carne muy basta, de sabor algo ácido. Pudrición blanca de planifolios, sobre todo haya (también abeto, pícea, pino, roble, olmo); en grandes macollas al pie de los árboles; sale en otoño y se deshace en una masa negra viscosa con las primeras heladas."],
  ["Poros que no se ennegrecen al magullarlos.", "Que no crezca al pie de un árbol."],
  [("Grifola frondosa", "ok", "tiene el sombrero más grisáceo y los poros más grandes."),
   ("Bondarzewia berkeleyi", None, "en el este de Norteamérica: no ennegrece y tiene los poros mucho mayores."),
   ("Meripilus sumstinei", None, "en guías norteamericanas se confunde con esta; Wikipedia no da diferencias.")],
  "Circumboreal en el hemisferio norte (Europa extendida; Wikipedia dice que no está en América del Norte). Wikipedia dice que antes se tenía por no comestible, por su carne basta y sabor ácido, que «fuentes más recientes la dan por comestible» y que un autor dice que «se come en Japón».",
  dict(s_color="pardo", s_super="escamas", h_tipo="!poros", grupo="mechon", habitat="planifolio madera", s_tam="grande"))

F("phaeolus-schweinitzii", "Phaeolus schweinitzii", "bajo",
  ["Cuerpo que puede parecer terrestre cuando sale de las raíces o de la base del árbol, a diferencia de otras repisas; tostado con centros pardo más oscuros y márgenes naranjas a pálidos de joven; puede pasar de 25 cm; con la edad se oscurece; a menudo incorpora briznas de hierba, ramitas o agujas de pino.",
   "Debajo, POROS amarillos que pasan a amarillo verdoso con la edad y se manchan de pardo al magullarlos.",
   "Sin pie definido.",
   "Carne pardo amarillenta que se vuelve más dura y leñosa con la edad; esporas blancas. Pudrición de la base de coníferas (abeto de Douglas, pícea, abeto, cicuta, pino, alerce); fin de verano y otoño."],
  ["Poros blancos.", "Que no se asocie a coníferas."],
  [("Heterobasidion irregulare, H. occidentale, Inonotus dryophilus y Onnia tomentosa", None, "Wikipedia las cita como parecidas sin explicar cómo se separan.")],
  "Eurasia (exótica en Nueva Zelanda, Australia y Sudáfrica). Wikipedia dice «la especie no es comestible».",
  dict(s_color="pardo naranja", h_tipo="!poros", h_color="amarillo verde", habitat="conifera madera", s_tam="grande"))

F("daedaleopsis-confragosa", "Daedaleopsis confragosa", "bajo",
  ["Cuerpo en repisa en abanico a semicircular, de 5-15 cm de ancho y hasta 2 de grosor; cara de arriba convexa a plana, seca, de lisa a algo peluda, normalmente con zonas concéntricas; pardo rojizo, pardo o gris, a veces negruzco con la edad.",
   "Debajo, POROS de 0,5-1,5 mm de ancho con tubos de hasta 1,5 cm; redondos, alargados, laberínticos o como láminas; de blancos a tostados o pardos, y se manchan de ROSA o ROJO al tocarlos.",
   "Sin pie: se fija directamente a la madera.",
   "Carne blanca, rosada o parduzca y tenaz; sin olor claro y de sabor ligeramente amargo; esporada blanca. En heridas de planifolios, sobre todo sauce y abedul, sola, en grupos o en pisos; de junio a diciembre (la repisa dura todo el año)."],
  ["Poros que no cambian de color al tocarlos.", "Que crezca sobre conífera."],
  [("Cerrena unicolor", None, "cuerpos más finos, con una línea negra en la carne y tubos que se rompen en dientes planos."),
   ("Daedalea quercina", None, "mayor (hasta 20 cm, 1-8 de grosor), con poros más laberínticos, común en roble.")],
  "Zonas templadas del norte de Eurasia y este de Norteamérica. Wikipedia dice «no es comestible».",
  dict(s_color="pardo rojo gris", h_tipo="!poros", h_color="blanco pardo", corte="enrojece", esporada="blanca", habitat="planifolio madera", s_tam="mediano"))

F("schizophyllum-commune", "Schizophyllum commune", "bajo",
  ["Cuerpos de 1-4 cm de ancho que crecen en abanico o como corales ondulados y apretados, de textura densa pero esponjosa; superficie cubierta de pelos blancos o grisáceos; en repisas apretadas SIN pie.",
   "Debajo, láminas partidas a lo largo que salen desde el centro, de amarillo crema a blanco pálido; se dividen al secarse el cuerpo.",
   "Carne densa y esponjosa; esporada blanca.",
   "Sobre madera podrida, en todo el mundo, y todo el año en sitios como Norteamérica."],
  ["Que no tenga láminas partidas en dos.", "Que crezca en suelo."],
  [("Wikipedia no cita especies parecidas", None, "")],
  "Cosmopolita. Wikipedia dice que «es comestible cuando es joven» (se come en partes de México, se vende en Guatemala, se aprecia en Yunnan y se usa en el noreste de la India), pero que Miller y Miller y David Arora la consideran no comestible por pequeña y dura; la tienen por no venenosa.",
  dict(s_color="blanco gris", s_super="fibrosa", h_tipo="!laminas", h_color="blanco amarillo", esporada="blanca", grupo="mechon", habitat="madera", s_tam="pequeno"))

F("gloeophyllum-sepiarium", "Gloeophyllum sepiarium", "bajo",
  ["Cuerpo de 1,5-15 cm de ancho, en abanico suelto; pardo con el borde amarillo anaranjado mientras crece; aterciopelado de joven y liso después; correoso; dura un año.",
   "Debajo, LÁMINAS (no poros) pegadas y apretadas, pálidas en fresco y más oscuras cerca de la madera y con la edad.",
   "Sin pie.",
   "Carne tostada, de olor y sabor suaves; esporada blanca. Pudrición parda de coníferas muertas, en el monte y en madera aserrada; esporas a finales de verano y en otoño."],
  ["Poros en vez de láminas.", "Que no crezca sobre conífera o madera aserrada."],
  [("Gloeophyllum trabeum, Daedaleopsis confragosa, Daedalea quercina, Lenzites betulinus y Trametes versicolor", None, "Wikipedia las cita como parecidas sin explicar cómo se separan.")],
  "Toda Norteamérica. Wikipedia dice «la especie no es comestible».",
  dict(s_color="pardo naranja", s_super="fibrosa", h_tipo="!laminas", h_color="blanco pardo", esporada="blanca", habitat="conifera madera", s_tam="mediano"))

F("pycnoporus-cinnabarinus", "Pycnoporus cinnabarinus", "bajo",
  ["Repisa de color naranja vivo, de hasta 12 cm de ancho y 1,5 de grosor.",
   "Debajo, POROS (2-4 por mm).",
   "Sin pie.",
   "El cuerpo se tiñe de oscuro con potasa (KOH); esporada blanca. Pudrición blanca de madera muerta, sobre todo en bosques templados de planifolios."],
  ["Que no sea naranja vivo."],
  [("Wikipedia no cita especies parecidas", None, "")],
  "Wikipedia dice «es no comestible» (y marca como «cita necesaria» su distribución mundial).",
  dict(s_color="naranja rojo", h_tipo="!poros", esporada="blanca", habitat="planifolio madera", s_tam="mediano grande"))

F("trichaptum-abietinum", "Trichaptum abietinum", "bajo",
  ["Cuerpo blanco grisáceo de 1-4 cm de ancho y normalmente de menos de 0,5 de grosor, en repisa y en abanico.",
   "Debajo, poros (Wikipedia no da el color).",
   "Sin pie.",
   "Carne parda y correosa; esporas blancas, cilíndricas y lisas. Saprófita sobre madera muerta de coníferas."],
  ["Que crezca sobre planifolios (en esta especie, Wikipedia solo cita coníferas)."],
  [("Trichaptum biforme, Bjerkandera adusta y Trametes versicolor", None, "Wikipedia las cita como parecidas sin explicar cómo se separan.")],
  "Wikipedia dice «la especie no es comestible».",
  dict(s_color="blanco gris", h_tipo="!poros", esporada="blanca", habitat="conifera madera", s_tam="pequeno"))

F("cerioporus-squamosus", "Cerioporus squamosus (Polyporus squamosus)", "bajo",
  ["Cuerpo redondo de 8-30 cm de ancho (a veces 60) y hasta 10 de grosor, amarillo a pardo, cubierto de escamas pardo oscuras en el sombrero; crece en repisas; blando de joven y duro con la edad.",
   "Debajo, POROS de tubos apretados de 1-12 mm.",
   "Pie grueso de 3-12 cm de largo y 1,5-3,5 de ancho.",
   "Carne con olor a corteza de sandía, blanda de joven y gomosa o dura cuando está madura o con gusanos; esporada blanca. En troncos y tocones muertos o en planifolios vivos, sobre todo olmo muerto y arce vivo (también fresno, haya, castaño de Indias, nogal, tilo, plátano, álamo, sauce); sobre todo en primavera, a veces en otoño; de julio a noviembre en Europa."],
  ["Superficie sin escamas pardo oscuro.", "Que no crezca sobre madera."],
  [("Polyporus tuberaster", None, "sombrero más redondo, pie más central y escamas oscuras solo en la punta.")],
  "Eurasia y Norteamérica. Wikipedia dice que «es comestible cuando es joven» (cocinada) y «no comestible al madurar», y que los buscadores de colmenillas la encuentran porque fructifica a la vez, aunque no la presenta como parecida.",
  dict(s_color="amarillo pardo", s_super="escamas", h_tipo="!poros", esporada="blanca", habitat="planifolio madera", s_tam="grande"))

F("lentinus-arcularius", "Lentinus arcularius (Polyporus arcularius)", "bajo",
  ["Sombrero de 1-8 cm, convexo a hundido, de tostado pálido a pardo oscuro, a veces con escamitas pequeñas y el borde con pelillos finos.",
   "Debajo, POROS hexagonales (no láminas), decurrentes (bajan por el pie), de crema a pardos.",
   "Pie central, pardusco, sin pelos y escamoso.",
   "Olor poco claro; carne tenaz; esporada de crema a blanca. En todos los continentes."],
  ["Láminas en vez de poros."],
  [("Wikipedia no cita especies parecidas", None, "")],
  "Wikipedia dice que es «demasiado pequeña y dura para tener interés culinario».",
  dict(s_color="pardo", s_super="escamas", s_forma="convexo", h_tipo="!poros", h_color="blanco pardo", p_color="pardo", esporada="blanca", s_tam="pequeno mediano"))

# ---------------- ASCOMICETOS (cazoletas, orejas de gato, falsas colmenillas) ----------------
P("discina-gigas", "Discina gigas (Gyromitra gigas)", "nocom",
  ["Sombrero de color tostado y arrugado, de hasta 10 cm de ancho y 6 de alto (Wikipedia no da más detalle de la forma).",
   "Sin láminas ni poros: el himenio recubre la superficie arrugada.",
   "Pie blanquecino, casi tan grueso como el sombrero, de hasta 10 cm de largo y de ancho.",
   "Aparece en primavera y principios de verano, en hábitats parecidos a los de las colmenillas verdaderas; Europa. Wikipedia da el nombre inglés «calf brain» (cerebro de ternera)."],
  "Con las colmenillas verdaderas (Morchella), a las que se parece y por eso se llama «falsa colmenilla», con Gyromitra esculenta (que Wikipedia dice que tiene unas 1500 veces más giromitrina) y con otras Gyromitra tóxicas, sin explicar cómo separarlas. Wikipedia dice que contiene unos 1 mg/kg de giromitrina en fresco, que se cita como «comestible en pequeñas cantidades si se cocina a fondo» pero que «no se recomienda comerla por su parecido con especies más tóxicas», y que está prohibida su venta en Francia desde 1991 por su posible relación con la ELA. La Enciclopèdia Catalana recoge el grupo con el nombre «bolet de greix» y le da buena valoración culinaria; aun así, esta guía te dice que no la comas sin identificación experta.",
  dict(s_color="pardo", s_forma="cerebro", h_tipo="!liso", p_color="blanco", s_tam="mediano"),
  ca=["bolet de greix"], ca_f="EC")

P("paragyromitra-infula", "Paragyromitra infula (Gyromitra infula)", "nocom",
  ["Sombrero «de silla de montar» con 2-4 lóbulos de puntas afiladas, de 2,5-9 cm de ancho y de alto, rojizo a pardo anaranjado (a veces con manchas pardo negruzcas), hueco o con cámaras por dentro.",
   "Sin láminas ni poros: el himenio queda por fuera, ondulado o abollado (no arrugado como en Gyromitra esculenta).",
   "Pie de 2-8 cm de alto y 1-2,5 de grosor, casi siempre hueco con alguna cámara, blanco o con tinte pardo pálido, más claro que el sombrero.",
   "Carne blanquecina a parduzca, de 1-2 mm de grosor y quebradiza, sin olor ni sabor notables. Solitaria o dispersa en bosque de coníferas (a menudo sobre madera podrida) y en suelo compactado como bordes de camino; finales de verano y otoño. Wikipedia la cita en América del Norte y también en Europa, Asia y Sudamérica."],
  "Con Gyromitra esculenta (más arrugada, como un cerebro), con Paragyromitra ambigua (casi igual; solo se separa con el microscopio: pie con más tonos púrpura y esporas mayores), con Discina brunnea (más robusta, pie blanco y sombrero arrugado casi sin puntas) y con las Helvella (más grises, de pie acanalado y más fino). Wikipedia dice que «se ha considerado venenosa» porque se creía que contiene giromitrina, pero que un estudio de 2023 lo pone en duda al no encontrar rastros. Mientras esa duda siga abierta, esta guía la trata como NO comestible.",
  dict(s_color="pardo rojo naranja", h_tipo="!liso", p_color="blanco", interior="hueco camaras", habitat="conifera madera", s_tam="pequeno mediano"),
  ca=["bolet de greix"], ca_f="EC")

P("helvella-acetabulum", "Helvella acetabulum", "nocom",
  ["Seta con forma de copa profunda, de hasta 8 cm de ancho y 4 de fondo, tostada por dentro, con costillas ramificadas que recuerdan una hoja de col.",
   "Sin láminas ni poros: el himenio es la cara interior de la copa, pardusca, lisa o algo ondulada.",
   "Pie crema de 1-6 cm de alto y 1-3 de grosor, con las costillas subiendo casi hasta arriba de la copa.",
   "Olor y sabor poco marcados. Crece en suelo arenoso, suelto, disperso o en grupos, bajo coníferas y bajo planifolios; sobre todo primavera y verano. Eurasia y Norteamérica."],
  "Con Helvella queletii (costillas que no suben por el borde), H. griseoalba (copa gris, costillas hasta la mitad), H. solitaria y Dissingia leucomelaena (costillas que casi no llegan a la copa), H. costifera (himenio gris a gris pardo, con formas intermedias) y H. robusta (himenio más claro y pie robusto; su borde suele doblarse sobre el pie, lo que H. acetabulum nunca hace). Wikipedia dice que la comestibilidad suele figurar como desconocida, que «no se recomienda comerla» porque especies emparentadas contienen monometilhidracina (MMH) y que Roger Phillips la da como venenosa. La Enciclopèdia Catalana la recoge con el nombre «cassoleta bruna».",
  dict(s_color="pardo", h_tipo="!liso", p_color="blanco", habitat="conifera planifolio", s_tam="mediano"),
  ca=["cassoleta bruna"], ca_f="EC")

P("helvella-crispa", "Helvella crispa", "nocom",
  ["Sombrero irregular blanquecino, de 2-6 cm de ancho, con el borde enrollado hacia dentro de joven; el cuerpo entero mide 6-13 cm de alto.",
   "Sin láminas ni poros: el himenio queda por encima; la cara de abajo del sombrero es peluda.",
   "Pie de 3-10 cm, blanco o rosado, acanalado de forma muy marcada («fluted» en inglés), con la base robusta de 1-2,5 cm de grosor.",
   "Carne fina y quebradiza, con olor agradable. Entre la hierba y en planifolios húmedos (sobre todo haya), en caminos, setos y laderas; de finales de verano a finales de otoño. Esporada blanca."],
  "Con formas blancas de Helvella lacunosa (la de H. crispa tiene la cara inferior del sombrero peluda y el borde enrollado de joven). Wikipedia dice que algunas guías la daban como comestible hasta 2006, que se ha visto que provoca síntomas gastrointestinales cruda, que el pie «no es comestible crudo» y que se sospecha que contiene monometilhidracina sin análisis químicos amplios; no hay pruebas de que cocinarla quite las toxinas, y hay indicios que relacionan las setas con giromitrina con la ELA tras años o décadas de consumo. Esta guía no la recomienda. La Enciclopèdia Catalana la recoge como «orella de gat» o «barretet».",
  dict(s_color="blanco", h_tipo="!liso", p_color="blanco", esporada="blanca", habitat="planifolio prado", s_tam="pequeno mediano"),
  ca=["orella de gat", "barretet"], ca_f="EC")

P("helvella-elastica", "Helvella elastica", "nocom",
  ["Sombrero en forma de silla de montar o mitra, de 3,5 cm de ancho como mucho, amarillo pardusco a gris u oliváceo, unido al pie solo por arriba.",
   "Sin láminas ni poros: la cara de abajo es blanca.",
   "Pie blanco, liso, de hasta 8 cm de largo y 1 de grosor, macizo o relleno de hifas sueltas.",
   "Carne fina y quebradiza; olor y sabor sin nada especial. Solitaria, dispersa o en grupos sobre el suelo o la madera de bosques de coníferas y de planifolios; verano y otoño. Europa, Japón, China y oeste de Norteamérica."],
  "Con Helvella albipes (pie más grueso y sombrero de 2-4 lóbulos), H. compressa y H. latispora (el borde del sombrero se curva hacia arriba, no hacia dentro), H. maculata (sombrero parecido pero pie acanalado) y Gyromitra infula (anaranjada y de sombrero más definido). Wikipedia dice que «no se recomienda comerla» porque especies emparentadas contienen giromitrina. La Enciclopèdia Catalana la recoge con el nombre «orella de gat de peu llis».",
  dict(s_color="pardo amarillo gris", h_tipo="!liso", p_color="blanco", interior="macizo", habitat="conifera planifolio", s_tam="pequeno"),
  ca=["orella de gat de peu llis"], ca_f="EC")

P("helvella-lacunosa", "Helvella lacunosa", "nocom",
  ["Sombrero irregular con la superficie plegada o arrugada, gris pizarra a negro, de 1-10 cm de ancho (lo normal es 2-5), con el borde a veces soldado al pie.",
   "Sin láminas ni poros: la cara de abajo del sombrero es peluda.",
   "Pie de 3-15 cm de alto y 1-3 de ancho, sin anillo, arrugado y acanalado, blanco de joven y de cualquier tono de gris al envejecer, con cámaras por dentro.",
   "Aspecto a veces como de cera; esporada blanca. Cerca de planifolios y de coníferas (pino, roble, abeto de Douglas), en parques, césped y a menudo sobre suelo quemado; finales de verano y otoño. Frecuente en Europa y el este de Norteamérica."],
  "Con Helvella crispa (cremosa; tiene la cara inferior del sombrero peluda y el borde enrollado de joven), H. maculata (sombrero parduzco) y, en el oeste de Norteamérica, H. vespertina y H. dryophila; Wikipedia añade que a veces aparecen formas de sombrero blanco. Wikipedia dice que algunos la comen, pero que provoca síntomas gastrointestinales cruda, que puede contener algo de monometilhidracina y que el género se mira con sospecha por las toxinas de especies emparentadas; Roger Phillips la da como «comestible pero sin interés». Esta guía no la recomienda. La Enciclopèdia Catalana la recoge con el nombre «orella de gat negra».",
  dict(s_color="gris negro", h_tipo="!liso", p_color="gris blanco", interior="camaras", esporada="blanca", habitat="conifera planifolio", s_tam="pequeno mediano"),
  ca=["orella de gat negra"], ca_f="EC")

P("dissingia-leucomelaena", "Dissingia leucomelaena (Helvella leucomelaena)", "nocom",
  ["Seta con forma de copa profunda de hasta 3 cm de ancho; por fuera pardo negruzca arriba y blanca hacia el pie; por dentro negruzca.",
   "Sin láminas ni poros: el himenio es la cara interior de la copa.",
   "Pie blanco de hasta 4 cm de largo y 0,5 de grosor, con costillas que suben por debajo de la copa; puede quedar tapado por hojas o medio enterrado.",
   "Normalmente en bosques de coníferas, de primavera a principios de verano. Rara en Norteamérica; también citada en Sudamérica y Europa."],
  "Con otras Helvellaceae, que Wikipedia dice que contienen giromitrina, sin citar especies ni decir cómo separarlas (en la página de Helvella acetabulum, Wikipedia dice que Dissingia leucomelaena y H. solitaria tienen costillas que casi no llegan a la copa). Wikipedia dice que «no se recomienda comerla». La Enciclopèdia Catalana la recoge con el nombre «cassoleta grisa».",
  dict(s_color="negro pardo", h_tipo="!liso", p_color="blanco", habitat="conifera", s_tam="pequeno"),
  ca=["cassoleta grisa"], ca_f="EC")

P("peziza-vesiculosa", "Peziza vesiculosa", "toxica",
  ["Cuerpo con forma de copa pálida, de 1-6 cm de ancho, que sale a menudo en grupos apretados.",
   "Sin láminas ni poros: el himenio es la cara interior de la copa (Wikipedia no da más detalle).",
   "Wikipedia no describe ningún pie.",
   "Esporada blanca. Crece en suelos ricos, como estiércol y compost; en Norteamérica se ve todo el año (en la costa oeste sobre todo de diciembre a abril) y es común en Europa."],
  "Con otras Peziza: Wikipedia dice que cuesta identificarla sin microscopio, que las de tonos púrpura por dentro se han pasado al género Geoscypha y que puede haber parecidas en Tarzetta y Jafnea y especies púrpura de Legaliana y Phylloscypha. Wikipedia dice que «se considera venenosa»; esta guía no te recomienda probarla. La Enciclopèdia Catalana la recoge con el nombre «cassoleta groga».",
  dict(s_color="blanco", h_tipo="!liso", esporada="blanca", s_tam="pequeno mediano"),
  ca=["cassoleta groga"], ca_f="EC")

P("sarcosphaera-coronaria", "Sarcosphaera coronaria", "muyt",
  ["Cuerpo blanquecino o grisáceo que sale medio enterrado como una bola hueca y se abre desde arriba en una copa con 5-10 rayos puntiagudos, de hasta 12 cm de ancho; por fuera blanco.",
   "Sin láminas ni poros: el himenio es la cara interior de la copa, gris lila que con la edad se vuelve pardo lavanda.",
   "Pie: a veces un pie corto y rechoncho (Wikipedia no da más).",
   "Carne blanca, gruesa y frágil, sin olor ni sabor claros (los ejemplares viejos pueden recordar al ruibarbo). En montaña bajo coníferas, en hayedos y en otros bosques de hoja ancha, sobre todo en suelos calizos; en primavera, cerca de la nieve que se derrite, o a principios de verano. Pasa desapercibida de joven porque la cubre el mantillo."],
  "De joven, antes de abrirse, con las trufas (se distingue porque es hueca por dentro) y con los bejines (que no se abren de arriba abajo); de adulta, con Scleroderma polyrhizum (amarillo pardo y sin tono púrpura), Peziza ammophila (pardo a pardo oscuro por fuera), las Neournula (himenio rosado, más pequeñas y siempre en copa) y Geopora sumneriana (himenio crema con tintes ocres y exterior peludo pardo). Wikipedia cuenta que se tuvo por «buena comestible» pero ahora «no se recomienda comerla»: ha habido intoxicaciones con dolor de estómago y, en un caso, la muerte (Jura, 1920, tras lo cual se advirtió de no comerla), y concentra arsénico en forma de sales de ácido metilarsónico, «relativamente peligrosas, que nunca deben ingerirse». La Enciclopèdia Catalana la recoge con el nombre «cassoleta violàcia».",
  dict(s_color="blanco gris", h_color="violeta gris", h_tipo="!liso", habitat="conifera planifolio", s_tam="mediano grande"),
  ca=["cassoleta violàcia"], ca_f="EC")

F("legaliana-badia", "Legaliana badia (Peziza badia)", "medio",
  ["Copas irregulares de color pardo oscuro, de hasta 8 cm de ancho y 2 de alto, que salen a menudo en grupos pequeños.",
   "Sin láminas ni poros: el himenio es la cara interior de la copa (Wikipedia no da más detalle).",
   "Wikipedia no describe ningún pie.",
   "En el suelo del bosque, sobre todo en suelos arenosos y en terreno desnudo como los bordes de camino; de agosto a noviembre. Frecuente en Europa."],
  ["Que sea blanquecina o de otro color que no sea pardo oscuro.", "Que crezca sobre estiércol o compost (entonces recuerda más a Peziza vesiculosa)."],
  [("Peziza vesiculosa y otras Peziza", "toxica", "Wikipedia dice, en la ficha de P. vesiculosa, que cuesta separar las Peziza sin microscopio, y que P. vesiculosa «se considera venenosa».")],
  "Wikipedia no cita especies parecidas para esta ficha. Roger Phillips la da como «no comestible» y otra fuente dice que «puede cocinarse y mezclarse con otros ingredientes»; esta guía no la recomienda. La Enciclopèdia Catalana la recoge con el nombre «cassoleta bruna».",
  dict(s_color="pardo", h_tipo="!liso", s_tam="mediano"),
  ca=["cassoleta bruna"], ca_f="EC")

F("aleuria-aurantia", "Aleuria aurantia", "medio",
  ["Cuerpo de 1-10 cm de ancho con forma de copa, de color naranja vivo, peludo por fuera y a menudo deformado por el apiñamiento (recuerda a una piel de naranja tirada).",
   "Sin láminas ni poros: el himenio es la cara interior de la copa.",
   "Wikipedia no describe ningún pie.",
   "Carne frágil. Esporada blanca; las esporas salen en nubes visibles cuando se toca la seta. Sobre arcilla desnuda o suelo removido; en Norteamérica de noviembre a marzo (oeste) o de mayo a noviembre (este); también en Europa."],
  ["Que no sea naranja vivo.", "Que tenga pie claro o láminas."],
  [("Otidea y Caloscypha (Europa)", "nocom", "Wikipedia dice que en Europa puede confundirse con ellas, que son venenosas o de comestibilidad desconocida."),
   ("Aleuria rhenana, Melastiza chateri, Sarcoscypha coccinea y otras copas naranjas", None, "Wikipedia las cita como vagamente parecidas sin explicar cómo separarlas.")],
  "Wikipedia dice que «se considera generalmente comestible» pero que es difícil de recoger entera y «no necesariamente exquisita» (en láminas finas o seca). La Enciclopèdia Catalana la valora «acceptable» con el nombre «cassoleta taronja».",
  dict(s_color="naranja", h_tipo="!liso", esporada="blanca", s_tam="pequeno mediano"),
  ca=["cassoleta taronja"], ca_f="EC")

F("verpa-conica", "Verpa conica", "alto",
  ["Sombrero en forma de dedal, cónico o acampanado y liso, de 1-4 cm de ancho y de alto, unido al pie solo por arriba, con el borde colgando libre como una falda; la cara de abajo es de tostada a pardo oscura.",
   "Sin láminas ni poros.",
   "Pie blanquecino de 2-12 cm de largo y 1-3 de grosor, liso o algo velloso, generalmente hueco (de joven puede estar relleno de hifas como algodón).",
   "Carne fina y quebradiza; el sombrero se desprende con facilidad. Solitaria, dispersa o en grupos en suelo de bosques de planifolios y de coníferas, a menudo en valles de río o a orillas de arroyos; en primavera, cerca de la temporada de colmenillas (en Norteamérica de marzo a junio en la costa oeste)."],
  ["Sombrero unido al pie por abajo y hueco por completo (serían colmenillas verdaderas).", "Sombrero muy arrugado (sería Verpa bohemica)."],
  [("Verpa bohemica", None, "tiene el sombrero más arrugado."),
   ("Morchella semilibera", None, "se separa porque Verpa conica se une al pie por arriba del sombrero, no por la base ni a media altura."),
   ("Colmenillas verdaderas (Morchella)", None, "se unen por la base del sombrero y son huecas por dentro; la Verpa conica suele estar rellena de algodón."),
   ("Phallus", None, "se separan por su olor a alcantarilla o carne podrida."),
   ("Gyromitra", "mortal", "la variedad de sombrero arrugado se le parece algo, según Wikipedia.")],
  "Europa y Norteamérica. Wikipedia dice que «las Verpa siempre deben cocinarse a fondo»; esta guía no te la recomienda sin identificación experta. La Enciclopèdia Catalana la valora «acceptable» sin darle nombre popular.",
  dict(s_forma="conico", s_super="lisa", h_tipo="!liso", p_color="blanco", interior="hueco", habitat="conifera planifolio", s_tam="pequeno"))

P("verpa-bohemica", "Verpa bohemica", "toxica",
  ["Sombrero cónico o de dedal, de 2-4 cm de ancho y 2-5 de largo, plegado en crestas longitudinales que a menudo se unen en una red de venas («circunvoluciones de cerebro»), de pardo amarillento a pardo rojizo, con la cara de abajo pálida; unido al pie solo por arriba, con el borde libre y lobulado.",
   "Sin láminas ni poros: el himenio cubre las crestas y los huecos.",
   "Pie de 6-12 cm de largo y 1-2,5 de grosor, blanco crema, más claro que el sombrero, más fino hacia arriba; relleno de algodón de joven y hueco de maduro; quebradizo.",
   "Carne blanca y frágil; el sabor se describe como fuerte, agradable o sin nada especial según el autor. Esporada amarilla. A principios de primavera, tras el deshielo, solitaria o dispersa en bosques, a menudo junto a ríos bajo álamos, sauces y chopos, sobre restos vegetales; norte de Norteamérica, Europa y Asia."],
  "Con Verpa conica (por lo general de sombrero liso, aunque puede arrugarse; sus ascas tienen ocho esporas y las de V. bohemica dos), con las colmenillas «semilibres» (Morchella semilibera, M. populiphila, M. punctipes: sombrero en panal unido al pie por la mitad de su largo; M. semilibera tiene el pie hueco y perforaciones verticales cerca de la base, que V. bohemica no tiene) y con las colmenillas verdaderas (su sombrero cuelga libre del pie). Wikipedia dice que la única forma fiable de separarla de todas es por sus esporas mucho más grandes. Wikipedia dice que «se tiene por comestible», pero que una preparación incorrecta puede intoxicar a personas sensibles (molestias gastrointestinales y falta de coordinación muscular), que hay casos de coma por exceso, que se ha descrito una reacción tipo disulfiram con el alcohol, que debe cocinarse siempre a fondo y que algunos aconsejan comer solo los sombreros; la comestibilidad se discute. Esta guía no te la recomienda.",
  dict(s_color="pardo amarillo rojo", s_forma="conico", h_tipo="!liso", p_color="blanco", interior="hueco", habitat="planifolio", s_tam="pequeno"))

F("morchella-semilibera", "Morchella semilibera (Mitrophora semilibera)", "medio",
  ["Sombrero de hasta 5 cm de alto y de ancho, redondeado de joven y luego cónico, en panal con las crestas verticales algo más oscuras que los huecos (se vuelven negruzcas al secarse); la cara de abajo es blanquecina y el borde cuelga libre a media altura del sombrero («semilibre»).",
   "Sin láminas ni poros.",
   "Pie de color tostado claro, de hasta 10 cm de largo y 2,5 de grosor, hueco (Wikipedia lo dice en la ficha de Verpa bohemica), y en los ejemplares viejos más grande que la cabeza.",
   "Carne fina y frágil; sabor flojo. Solitaria o en grupos en zonas arboladas de Europa y Asia."],
  ["Sombrero unido al pie solo por arriba (sería Verpa).", "Pie relleno de algodón en vez de hueco."],
  [("Verpa bohemica y otras Verpa", "toxica", "los ejemplares viejos, de cabeza pequeña y pie largo, se parecen; la Verpa tiene el pie relleno de algodón y no tiene las perforaciones verticales cerca de la base que sí tiene la Morchella semilibera (Wikipedia, ficha de Verpa bohemica)."),
   ("Colmenillas negras (Morchella elata y similares)", None, "Wikipedia dice que están emparentadas, sin presentarlas como parecidas.")],
  "Wikipedia dice que «la especie es comestible, pero frágil y poco sabrosa». No da ningún aviso de cocinado, pero sí lo da para sus parecidas del género Verpa; esta guía no te la recomienda sin identificación experta.",
  dict(s_forma="alveolado conico", h_tipo="!liso", p_color="blanco amarillo", interior="hueco", s_tam="pequeno"))

F("sarcoscypha-coccinea", "Sarcoscypha coccinea", "bajo",
  ["Cuerpo que empieza esférico y luego se abre en copa o platillo poco profundo de 2-6 cm de ancho, con el borde enrollado hacia dentro; por dentro rojo intenso que se vuelve naranja al secarse, por fuera blanquecino y cubierto de pelillos finos apretados.",
   "Sin láminas ni poros: el himenio es la cara interior, lisa.",
   "A veces con un pie robusto de hasta 4 cm (si está enterrado), de 3-7 mm de grosor, blanquecino y peludo; muchos ejemplares no lo tienen.",
   "Carne tenaz y muy fina. Sobre ramas y palos caídos, normalmente enterrados bajo la hojarasca o el suelo en rincones húmedos del bosque (rosáceas, haya, avellano, sauce, olmo y, en el Mediterráneo, roble); de enero a abril. Hemisferio norte."],
  ["Interior que no sea rojo vivo.", "Que crezca sobre estiércol o suelo desnudo, en vez de sobre ramas caídas."],
  [("Otras Sarcoscypha (S. austriaca, S. dudleyi, S. occidentalis…)", None, "Wikipedia dice que a menudo hace falta el microscopio para separarlas."),
   ("Plectania melastoma, Plectania nannfeldtii y Scutellinia scutellata", None, "Wikipedia las cita como parecidas sin decir cómo separarlas.")],
  "Wikipedia dice que, según el autor, se «dice comestible» (quizá mejor seca), «no comestible» o «no recomendada», y que por pequeña, escasa y tenaz casi nadie la recoge para comerla. Esta guía no te la recomienda.",
  dict(s_color="rojo", h_color="rojo naranja", h_tipo="!liso", p_color="blanco", habitat="planifolio madera", s_tam="pequeno"))

F("scutellinia-scutellata", "Scutellinia scutellata", "bajo",
  ["Disco poco profundo de solo 0,2-1 cm de ancho (de joven casi esférico), con pelos oscuros y rígidos por fuera, de hasta 1 cm de largo.",
   "Sin láminas ni poros: el himenio es la cara interior, naranja rojizo vivo.",
   "Sin pie (Wikipedia dice que es sésil).",
   "Carne roja y fina, sin olor ni sabor claros; esporada blanca. Sobre madera podrida, tierra húmeda, cenizas, hojas mojadas y hongos de repisa, en grupos pequeños o densos, a menudo escondida entre musgo; en Europa de finales de primavera a finales de otoño."],
  ["Mayor de 1 cm o sin pelos oscuros en el borde.", "Que no sea naranja rojizo."],
  [("Scutellinia umbrarum", None, "mayor, de pelos más cortos y menos visibles."),
   ("Scutellinia erinaceus", None, "algo más pequeña, de naranja a amarilla."),
   ("Cheilymenia crucipila, Melastiza chateri y Lamprospora", None, "Wikipedia las cita como parecidas (más pequeñas, de pelos cortos y pálidos, o sin pelos, según el caso).")],
  "Wikipedia dice que algunas fuentes la dan como «no comestible» y otras como de «comestibilidad desconocida», y que Arora la considera demasiado pequeña para interesar en la cocina.",
  dict(s_color="rojo naranja", h_color="rojo naranja", h_tipo="!liso", esporada="blanca", habitat="madera", s_tam="pequeno"))

F("humaria-hemisphaerica", "Humaria hemisphaerica", "bajo",
  ["Copas de 5-30 mm de ancho y 10-15 de fondo, que empiezan esféricas y se abren con la edad; por fuera pardas y peludas.",
   "Sin láminas ni poros: el himenio es la cara interior, blanca y lisa.",
   "Normalmente sin pie (a veces una base pequeña y brusca).",
   "Solitaria, dispersa o en grupos en el suelo, a veces sobre madera podrida; Europa y Norteamérica (todo el año en la costa oeste; más al este de julio a octubre)."],
  ["Interior que no sea blanco.", "Más de 3 cm de ancho."],
  [("Jafnea semitosta", None, "mayor (2-5 cm), con el interior pardo y un pie corto."),
   ("Trichophaea (por ejemplo T. abundans, que prefiere suelos quemados)", None, "casi siempre de menos de 1 cm."),
   ("Chaetothiersia vernalis y Wilcoxina rehmii", None, "más en forma de disco o diminutas.")],
  "Wikipedia dice «el hongo es no comestible».",
  dict(s_color="pardo", h_color="blanco", h_tipo="!liso", s_tam="pequeno"))

F("disciotis-venosa", "Disciotis venosa", "medio",
  ["Copa o disco de hasta 20 cm de ancho; de joven en copa, hacia 7-8 cm se abre y se aplana contra el suelo; por fuera blanquecina y cubierta de pústulas.",
   "Sin láminas ni poros: el himenio es la cara interior, pardo oscura, que con la edad se pliega en marcas como venas (de ahí «venosa»).",
   "Pie corto que ancla la copa al suelo (Wikipedia no da más detalles).",
   "Carne muy quebradiza y con «olor a lejía» al romperla. Sobre suelo musgoso o con acículas, normalmente cerca de coníferas, en taludes y sitios abrigados; aparece en el borde de la nieve que se derrite (Norteamérica de abril a junio; Europa de marzo a mayo; citada en España)."],
  ["Interior que no sea pardo oscuro, o que sea liso y sin venas.", "Sin olor a lejía al romperla."],
  [("Peziza (otras cazoletas pardas)", "toxica", "suelen carecer de olor, tienen la carne más fina y se ponen azul oscuro con yodo; algunas son venenosas."),
   ("Discina ancilis", None, "interior pardo rojizo, plegado o arrugado (a veces liso) y no venoso; por fuera con mechones de pelos.")],
  "Wikipedia la llama «comestible selecta» y dice que solo deberían plantearse comerla quienes puedan comprobar rasgos microscópicos, porque se confunde con otras cazoletas pardas, y que «puede ser venenosa si no se cocina». Esta guía no te la recomienda sin identificación experta.",
  dict(s_color="pardo", h_color="pardo", h_tipo="!liso", habitat="conifera", s_tam="mediano grande"))

F("daedalea-quercina", "Daedalea quercina (Fomitopsis quercina)", "bajo",
  ["Repisa sin pie, en forma de abanico, de 3-20 cm de ancho y hasta 8 de grosor, sola o en pisos; superficie de tonos pardos, a veces con zonas.",
   "Debajo, al principio con poros; después las paredes se rompen en ranuras con tabiques romos que dan un aspecto de LABERINTO; blanco a tostado.",
   "Sin pie.",
   "Esporada blanca. Normalmente sobre roble podrido (a veces haya, fresno, nogal u olmo); produce podredumbre parda. Eurasia, norte de África, Norteamérica y Australia."],
  ["Poros regulares y pequeños sin laberinto.", "Que crezca sobre una conífera."],
  [("Wikipedia no cita especies parecidas", None, "(solo una variedad de poros grandes y angulares que recuerda a Trametes).")],
  "Wikipedia dice «aunque no comestible» (sin hablar de toxicidad).",
  dict(s_color="pardo", h_tipo="!poros pliegues", h_color="blanco pardo", esporada="blanca", habitat="planifolio madera"))

F("bondarzewia-mesenterica", "Bondarzewia mesenterica", "bajo",
  ["Masas de hasta 1 m de ancho formadas por sombreros en abanico de hasta 25 cm que se solapan y salen de una base común; superficie aterciopelada con zonas pardas.",
   "Debajo, POROS de color tostado de hasta 2 mm.",
   "Pie continuo con los sombreros, que sale de un esclerocio subterráneo de hasta 12 cm de largo y 5 de grosor.",
   "Carne blanquecina, de olor agradable en fresco. Crece en la base de coníferas y produce podredumbre blanca de tronco y raíces."],
  ["Poros de más de 2 mm o láminas.", "Que no crezca en la base de una conífera."],
  [("Meripilus giganteus", None, "Wikipedia dice que se le parece, sin explicar cómo se separan.")],
  "Wikipedia dice que «se considera comestible» pero «dura y a menudo amarga».",
  dict(s_color="pardo", h_tipo="!poros", h_color="blanco amarillo", habitat="conifera madera", s_tam="grande"))

F("auricularia-mesenterica", "Auricularia mesenterica", "bajo",
  ["Cuerpos gelatinosos en repisa de 3-7 cm de ancho que se endurecen con la edad; de grises a pardos o ante, con zonas concéntricas y superficie aterciopelada o con pelos; de jóvenes, pálidos, de goma y con forma de botón.",
   "Debajo, gelatinosa, pardo rojiza y con pliegues irregulares radiales.",
   "Wikipedia no describe pie.",
   "Gelatinosa y de goma de joven; esporada blanca. Sobre árboles y arbustos de hoja ancha muertos, en pisos que se juntan sobre tocones y troncos; Europa y Asia central."],
  ["Superficie lisa sin zonas ni pelos.", "Que no sea gelatinosa."],
  [("Stereum (especies de sombrero zonado parecido)", None, "son correosas y no gelatinosas, con la cara de abajo de amarillenta a naranja."),
   ("Otras Auricularia", None, "no tienen la parte de arriba zonada y peluda.")],
  "Wikipedia dice que «se dice que los ejemplares jóvenes son comestibles» (antes de madurar) y que algunas poblaciones locales acumulan mucho metal pesado. La Enciclopèdia Catalana no la recoge.",
  dict(s_color="gris pardo", h_tipo="!pliegues", h_color="pardo", esporada="blanca", habitat="planifolio madera", s_tam="pequeno mediano"))

F("chondrostereum-purpureum", "Chondrostereum purpureum", "bajo",
  ["Empieza como costra sobre la madera y luego forma repisas ondulantes y soldadas de hasta unos 3 cm de ancho, de goma dura; por arriba grises (a veces zonadas, de borde más pálido) y con pelos blanquecinos; secas se vuelven quebradizas y pardas o beige.",
   "Debajo (la parte fértil), VIOLETA vivo mientras crece.",
   "Wikipedia no describe pie.",
   "Carne tenaz y de goma. Sobre tocones y madera muerta, y a veces parásita de árboles vivos (ciruelo, manzano, peral, sauce, chopo, arce, carpe, plátano, roble, olmo, lila; en ocasiones abeto, pícea o tuya); común en bosques, huertos y plantaciones de clima templado."],
  ["Parte de abajo que no sea violeta mientras está fresca."],
  [("Amylostereum areolatum", None, "parecida, pero su sombrero suele estar cubierto de musgo."),
   ("Phlebiopsis crassa", None, "no forma sombreros."),
   ("Trichaptum", None, "forma una superficie continua cubierta de dientes o poros.")],
  "Wikipedia no dice nada de su comestibilidad. Se conoce como «enfermedad del plateado» (silver leaf) porque en los árboles infectados las hojas se vuelven plateadas.",
  dict(s_color="gris", h_color="!violeta", habitat="planifolio madera", s_tam="pequeno"))

F("lyophyllum-decastes", "Lyophyllum decastes", "alto",
  ["Sombrero liso de 4-12 cm de ancho, de color variable.",
   "Debajo, LÁMINAS blancas que amarillean algo con la edad.",
   "Pie de 5-10 cm de largo y 1-3 de ancho, blanquecino grisáceo.",
   "Carne blanca, firme, que no cambia de color al cortarla; esporada blanca. Sale en ramos densos, a veces enormes, sobre el suelo, a menudo removido (caminos, gravas, jardines), a veces en el bosque; en la costa oeste de Estados Unidos, en verano y otoño hasta la primavera. Europa, zonas templadas del norte, Norteamérica y Asia oriental."],
  ["Que crezca suelta, no en ramos densos.", "Láminas que no sean blancas."],
  [("Entoloma venenosas", "toxica", "Wikipedia las cita como posible confusión sin decir cómo separarlas."),
   ("Clitocybe dilatata", None, "citada como posible confusión sin más detalle."),
   ("Lyophyllum semitale y Pluteus petasatus", None, "de aspecto parecido, según Wikipedia."),
   ("Lyophyllum fumosum y L. loricatum", None, "se agrupan a veces con L. decastes en un mismo complejo de especies.")],
  "Wikipedia dice que «se considera comestible», pero que en Norteamérica se recoge poco y hay avisos de molestias gástricas. La Enciclopèdia Catalana la valora «molt bo» con el nombre «gírgola de bruc».",
  dict(s_super="lisa", h_tipo="!laminas", h_color="blanco amarillo", p_color="blanco gris", corte="nada", grupo="mechon", esporada="blanca"),
  ca=["gírgola de bruc"], ca_f="EC")

F("laccaria-amethystina", "Laccaria amethystina", "medio",
  ["Sombrero de hasta 6 cm de ancho, convexo y luego aplanado, a menudo con un ombligo en el centro, violeta lila intenso con la humedad y que se aclara al secarse; a veces algo escamoso en el centro y con estrías pálidas en el borde.",
   "Debajo, LÁMINAS del color del sombrero, a menudo muy separadas, con un hueco antes de unirse al pie.",
   "Pie de 0,6-7 cm de largo y 1-7 mm de grosor, del color del sombrero, fibroso, hueco y tenaz, con fibrillas blancas en la base.",
   "Carne lila pálida y fina, sin olor ni sabor claros; esporada blanca. En bosques de planifolios y de coníferas (sobre todo con hayas), solitaria o dispersa; de finales de verano a principios de invierno (de junio a diciembre en Europa)."],
  ["Sombrero que no sea violeta cuando está húmedo.", "Pie macizo o con anillo."],
  [("Laccaria laccata", None, "es de la misma familia y también pierde color; Wikipedia no da rasgos para separarlas."),
   ("Mycena pura", "toxica", "esta guía le dedica ficha: también es violácea, de olor a rábano, y Wikipedia dice que contiene muscarina; Wikipedia la compara con otra Laccaria violácea (L. amethysteo-occidentalis), no con L. amethystina."),
   ("Laccaria amethysteo-occidentalis, L. vinaceobrunnea y L. gomezii", None, "otras Laccaria violáceas de América (más grandes, o de otras zonas).")],
  "Wikipedia dice que «es comestible» pero «no se considera selecta», y que, aunque no es tóxica de por sí, en suelos contaminados con arsénico puede acumular mucho; hay que limpiar bien las láminas. La Enciclopèdia Catalana la valora «acceptable» con el nombre «pimpinella morada petita». Esta guía no te la recomienda sin identificación experta.",
  dict(s_color="violeta", s_forma="convexo", h_tipo="!laminas", h_color="violeta", p_color="violeta", interior="hueco", esporada="blanca", habitat="conifera planifolio", s_tam="pequeno"),
  ca=["pimpinella morada petita"], ca_f="EC")

F("laccaria-laccata", "Laccaria laccata", "alto",
  ["Sombrero de 2-6 cm de ancho, convexo y luego plano o hundido en el centro; de rosa salmón, rojo ladrillo, naranja o pardo si está joven o húmedo, y más apagado y pálido al secarse.",
   "Debajo, LÁMINAS irregulares y muy separadas, decurrentes o escotadas, del color del sombrero y que se blanquean con las esporas al madurar.",
   "Pie fibroso de 2-10 cm de alto y 3-10 mm de ancho.",
   "Carne fina y de poco sabor; esporada blanca. En grupos dispersos en bosques y brezales, a menudo en suelo pobre, con pinos, hayas y abedules; común en las zonas templadas del norte, mejor con tiempo fresco. Europa y Norteamérica."],
  ["Que crezca sobre madera.", "Láminas apretadas y de otro color."],
  [("Laccaria proxima", None, "se consideró subespecie; tiene el sombrero con escamitas finas, crece en sitios más húmedos y sus esporas son más estrechas y ovaladas."),
   ("Laccaria amethysteo-occidentalis y L. bicolor", None, "Wikipedia las cita como parecidas sin dar rasgos para separarlas."),
   ("Setas pardas pequeñas potencialmente mortales", "mortal", "Wikipedia avisa de que hay que separarla de ellas, sin nombrar especies ni rasgos.")],
  "Wikipedia dice «el sombrero es comestible»; «aunque pequeña, es comestible y de sabor suave» y los pies tenaces suelen no comerse, y añade que es importante distinguirla de pequeñas setas pardas potencialmente mortales. La Enciclopèdia Catalana la valora «acceptable» con el nombre «pimpinella rosada». Por eso el riesgo es alto: esta guía no te la recomienda sin identificación experta.",
  dict(s_color="rosa rojo naranja pardo", s_forma="convexo", h_tipo="!laminas", esporada="blanca", habitat="conifera planifolio", s_tam="pequeno"),
  ca=["pimpinella rosada"], ca_f="EC")

# ---------------- TRICOLOMATOIDES Y AMANITAS RAROS ----------------
P("amanita-strobiliformis", "Amanita strobiliformis", "nocom",
  ["Sombrero blanquecino (a veces con algo de pardo) de 7,5-25 cm de ancho, cubierto de verrugas grandes que a veces se caen y lo dejan liso.",
   "Debajo, LÁMINAS libres y redondeadas por detrás (Wikipedia no da su color).",
   "Pie blanco, grueso, de 7,5-20 cm de largo, con la base ENSANCHADA en bulbo; Wikipedia dice que un velo grande a veces se queda pegado al borde del sombrero.",
   "Micorrícica con planifolios; en bosques abiertos y bordes de bosque, normalmente en suelo calizo, sola o en grupos. Rara. Europa, del Mediterráneo a Holanda e Inglaterra."],
  "Wikipedia no cita especies parecidas. Dice que su comestibilidad es desconocida y que el género Amanita incluye algunas de las setas más tóxicas que se conocen, por lo que esta guía la trata como NO comestible. La Enciclopèdia Catalana la recoge con el nombre «farinera d'esquames».",
  dict(s_color="blanco", s_super="escamas", h_tipo="!laminas", p_color="blanco", p_base="ensanchada", habitat="planifolio", s_tam="grande"),
  ca=["farinera d'esquames"], ca_f="EC")

P("lepiota-cristata", "Lepiota cristata", "toxica",
  ["Sombrero de 1-5 cm de ancho, blanco a crema con escamas planas pardo rojizas dispuestas en círculos (centro más oscuro); de joven acampanado o convexo y luego aplanado con un pequeño mamelón.",
   "Debajo, LÁMINAS apretadas, blancas a crema, libres (no tocan el pie), que se oscurecen a pardas al madurar las esporas.",
   "Pie de 2-6 cm de largo y 2-7 mm de grosor, casi liso, pálido y blanquecino, con un anillo membranoso que se cae pronto.",
   "Carne fina y blanca, de olor fuerte y desagradable (a goma quemada, también descrito como a pescado, penetrante o afrutado) y sabor suave; esporada blanca. En suelo bajo planifolios y coníferas, solitaria o en grupos pequeños, en bosques, jardines húmedos y sombríos, restos de jardín, césped corto, hojarasca, caminos y zanjas. América del Norte, Europa, norte de Asia y Nueva Zelanda."],
  "Con Lepiota ignivolvata (anillo en la parte baja del pie y color naranja o pardo rojizo vivo), L. lilacea (rara y tóxica, de colores púrpuras), L. saponella (olor a jabón, láminas pardo sucio, escamas más pequeñas), L. cristatanea (cuerpos y esporas más pequeños) y, en Gran Bretaña, con las parasoles (Macrolepiota; mira la ficha de los apagallums). Wikipedia dice que «puede ser venenosa», que los micólogos al menos la tienen por sospechosa (su toxicidad en humanos no está confirmada) y que se ha citado con síntomas gastrointestinales. La Enciclopèdia Catalana la pone como tóxica con el nombre «lepiota pudent».",
  dict(s_color="blanco pardo rojo", s_super="escamas", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_color="blanco", esporada="blanca", habitat="conifera planifolio prado", s_tam="pequeno"),
  ca=["lepiota pudent"], ca_f="EC")

P("tricholoma-sulphureum", "Tricholoma sulphureum", "nocom",
  ["Sombrero de hasta 8 cm de ancho, amarillo azufre (a veces pardusco hacia el centro), convexo con un mamelón poco marcado.",
   "Debajo, LÁMINAS gruesas y separadas, unidas al pie con una muesca o estrechas (Wikipedia no da su color).",
   "Pie de hasta 10 cm de largo (Wikipedia no da más detalles).",
   "Carne fina, de olor complejo (se compara con jazmín, narciso y gas del alumbrado, debido al escatol) y sabor amargo; esporada blanca. En bosques de planifolios, sobre todo de haya, de primavera a otoño; Europa (confirmada hasta China) y Norteamérica, donde a veces crece con coníferas."],
  "Con Tricholoma inamoenum (Wikipedia dice «muy parecida» sin explicar cómo separarlas), con T. bufonium (quizá una variante) y con el Tricholoma equestre, más oscuro, de sombrero pegajoso, carne blanca, láminas finas y apretadas y olor a harina (ver su ficha en las peligrosas de esta guía). Wikipedia dice que «no es comestible o es levemente venenosa» y que suele clasificarse como no comestible y sospechosa de ser venenosa. La Enciclopèdia Catalana la pone como «a refusar» con el nombre «groguet pudent».",
  dict(s_color="amarillo", s_forma="convexo", h_tipo="!laminas", esporada="blanca", habitat="planifolio", s_tam="pequeno mediano"),
  ca=["groguet pudent"], ca_f="EC")

P("tricholoma-ustaloides", "Tricholoma ustaloides", "nocom",
  ["Sombrero de 4-8 cm de ancho, pardo rojizo o castaño con el borde más pálido, acampanado de joven y luego aplanado, irregular y a menudo lobulado, con el borde enrollado hacia dentro; MUY PEGAJOSO con humedad.",
   "Debajo, LÁMINAS apretadas, blancas o amarillo ocre claro, con manchas pardo oscuras cuando viejas o magulladas; unidas al pie o con muesca.",
   "Pie de 4-10 cm de largo y 1-2 de grosor, con fibrillas pardo rojizas, de forma de huso, con una zona blanca bien marcada arriba (sobre todo en adultos).",
   "Carne blanca o crema, con fuerte olor a harina y sabor amargo. Con roble y haya, normalmente en grupos pequeños (micorrícica). Europa, relativamente rara; en México se citó en 1984."],
  "Wikipedia no cita especies parecidas. Dice que «generalmente se considera no comestible», aunque la comen los habitantes de Ajusco y Topilejo (cerca de Ciudad de México); esta guía la trata como NO comestible. La Enciclopèdia Catalana la recoge con el nombre «bolet d'ovella».",
  dict(s_color="pardo rojo", s_super="viscosa", s_forma="convexo", h_tipo="!laminas", h_color="blanco amarillo", p_color="pardo", olor="harina", habitat="planifolio", s_tam="pequeno mediano"),
  ca=["bolet d'ovella"], ca_f="EC")

F("tricholomopsis-rutilans", "Tricholomopsis rutilans", "bajo",
  ["Sombrero de hasta 12 cm de ancho, convexo y luego acampanado y aplanado, con el borde enrollado; cubierto de pelillos rojos a rojo púrpura que con la edad se agrupan en escamitas y dejan ver el fondo amarillento.",
   "Debajo, LÁMINAS amarillas, unidas al pie y apretadas, con muchas láminas cortas.",
   "Pie de 5-11 cm de alto y 8-25 mm de grosor, con la base escamosa y roja que se aclara a amarillo hacia las láminas (puede acabar amarillo del todo).",
   "Carne de amarilla a crema; esporada blanca cremosa. Sobre tocones y troncos de coníferas (sobre todo pícea) bien podridos, y a veces sobre virutas o serrín; sola, dispersa o en grupos; de finales de verano a otoño (de junio a noviembre)."],
  ["Que crezca en el suelo sin madera enterrada.", "Pelillos que no sean rojos o púrpura rojizos."],
  [("Tricholomopsis decora", None, "dorada, en coníferas, mucho menos común y a más altitud."),
   ("Tricholomopsis flammula", None, "más pequeña, con el pie más amarillo."),
   ("Megacollybia fallax", None, "parecida, pero con el sombrero gris pardo."),
   ("Gymnopilus luteofolius", None, "crece en ramos y tiene escamas en el sombrero.")],
  "Wikipedia dice que los textos antiguos la dan como «aparentemente comestible hervida, aunque no se recomienda» y que otros libros recientes la valoran de mala calidad, según se cree por un sabor a madera podrida. La Enciclopèdia Catalana la pone como «a refusar» con el nombre «gírgola vermella».",
  dict(s_color="rojo violeta amarillo", s_super="escamas", s_forma="convexo", h_tipo="!laminas", h_color="amarillo", p_color="amarillo rojo", esporada="blanca", habitat="conifera madera", s_tam="mediano grande"),
  ca=["gírgola vermella"], ca_f="EC")

F("infundibulicybe-gibba", "Infundibulicybe gibba (Clitocybe gibba)", "medio",
  ["Sombrero de 3-9 cm de ancho, de beige a tostado (a veces con tinte rosado), mate y algo afieltrado, con un pequeño hundimiento en el centro que acaba en forma de EMBUDO.",
   "Debajo, LÁMINAS blancas, apretadas y muy decurrentes (bajan por el pie).",
   "Pie de 2-8 cm de largo y alrededor de 1 de grosor, blanco o blanquecino, SIN anillo ni restos de velo.",
   "Olor tenue «cianuro», como a heno recién segado; sabor suave (la variedad adstringens de Europa central, desagradable); esporada blanca. En grupos sobre el suelo de bosques de planifolios (menos de coníferas), a veces en corros de bruja; de verano a otoño; muy común en Europa, también en Norteamérica y Japón."],
  ["Anillo en el pie.", "Sombrero blanco puro o de color vivo."],
  [("Clitocybe catinus", None, "sombrero blanco (a veces con un tono rosado) y ligero olor a harina."),
   ("Infundibulicybe squamulosa, Pseudoclitocybe cyathiformis, Bonomyces sinopicus y Singerocybe adirondackensis", None, "Wikipedia las cita como parecidas sin explicar cómo se separan."),
   ("Otros clitocibes", "toxica", "Wikipedia dice que se parece a algunos que son venenosos; la guía tiene la ficha de los clitocibes blancos de prado en las peligrosas.")],
  "Wikipedia dice que «es comestible cuando es joven, pero se dice que de calidad mediocre» y que se parece a algunas especies venenosas; esta guía no te la recomienda sin identificación experta. La Enciclopèdia Catalana la valora «acceptable» con el nombre «tassa de bruc» u «orella de conill».",
  dict(s_color="pardo rosa", s_forma="embudo", h_tipo="!laminas", h_color="blanco", p_anillo="no", p_color="blanco", esporada="blanca", grupo="suelto corro", habitat="planifolio conifera", s_tam="pequeno mediano"),
  ca=["tassa de bruc", "orella de conill"], ca_f="EC")

F("aspropaxillus-giganteus", "Aspropaxillus giganteus (Leucopaxillus giganteus)", "medio",
  ["Sombrero enorme de 10-50 cm de ancho (a veces 70), de blanco crema a blanco, convexo con el borde enrollado de joven y luego aplanado y en forma de embudo poco profundo; liso, con manchas pardas y grietas circulares con la edad.",
   "Debajo, LÁMINAS estrechas, apretadas, crema, decurrentes (bajan por el pie), que se oscurecen a ante.",
   "Pie corto de 3-10 cm de alto y 2-5 de grosor, blanquecino con fibras pardo rojizas, SIN anillo, con micelio blanco denso en la base.",
   "Carne firme, blanca y fibrosa (la de los Lactarius y Russula blancos es quebradiza y se rompe limpia), de olor a harina o a harina de pescado y sabor poco claro («pobre», «dulce y bueno» o «suave y agradable» según la fuente); esporada blanca. En grupos o en corros de bruja en pastos, bordes de camino, setos y claros de bosque; verano y otoño; zonas templadas del norte."],
  ["Sombrero pequeño (menos de 10 cm).", "Carne que se rompe quebradiza como la tiza."],
  [("Leucopaxillus albissimus, Leucopaxillus gentianeus, Lactifluus vellereus e Infundibulicybe gibba", None, "Wikipedia las cita como posibles confusiones."),
   ("Lepista irina, Clitocybe praemagna y C. robusta", None, "los ejemplares jóvenes pueden confundirse con ellas."),
   ("Aspropaxillus candidus", None, "de colores más oscuros, de montaña y más pequeña (6-30 cm)."),
   ("Aspropaxillus septentrionalis", None, "olor desagradable, sombrero tostado y láminas unidas al pie o casi.")],
  "Wikipedia cita a una fuente que la da como «comestible selecta cuando es joven», a otras como «comestible» o «no venenosa», y a una que avisa de que «a veces su consumo produce retortijones y diarrea». La Enciclopèdia Catalana la valora «acceptable» con el nombre «candela de bruc gegant». Esta guía no te la recomienda sin identificación experta.",
  dict(s_color="blanco", s_forma="embudo convexo", s_super="lisa", h_tipo="!laminas", h_color="blanco amarillo", p_anillo="no", p_color="blanco", olor="harina", esporada="blanca", grupo="corro", habitat="prado", s_tam="grande"),
  ca=["candela de bruc gegant"], ca_f="EC")

F("paralepista-flaccida", "Paralepista flaccida (Lepista flaccida)", "alto",
  ["Sombrero convexo de hasta 10 cm de ancho, hundido o en embudo cuando es viejo; de color pardo variable (ocre, naranja o rojizo); la forma flaccida es mate y sedosa y la inversa, brillante.",
   "Debajo, LÁMINAS decurrentes (bajan por el pie), muy apretadas y más claras que el sombrero.",
   "Pie amarillento de hasta 10 cm de largo y 1 de grosor.",
   "Carne blanquecina de olor picante a pimienta; esporada de blanca a crema. Saprófita en suelos ricos en humus, compost o acículas de conífera; de verano a otoño, a menudo en grupos y a veces en corros de bruja; la forma flaccida en bosques de planifolios y la inversa bajo coníferas. Sobre todo en Europa."],
  ["Sombrero con anillo o escamas finas.", "Láminas que no bajen por el pie."],
  [("Paralepista gilva", None, "comestible según Wikipedia; sombrero y pie más amarillos y manchas oscuras en el sombrero."),
   ("Infundibulicybe gibba", None, "carne más fina, láminas menos apretadas y esporas lisas en forma de lágrima (solo al microscopio)."),
   ("Paralepistopsis amoenolens", "toxica", "Wikipedia la describe como venenosa: olor fuerte y característico, color beige, sombrero menos hundido y esporas lisas; limitada a norte de África, sur de Francia y sur de Italia.")],
  "Wikipedia dice que Marcel Bon la llama «buena comestible», que otros la ven pobre y que una fuente «no recomienda su consumo». La Enciclopèdia Catalana la valora «acceptable» con el nombre «pampeta». Por su parecido con una especie descrita como venenosa, esta guía no te la recomienda sin identificación experta.",
  dict(s_color="pardo naranja rojo", s_forma="convexo embudo", h_tipo="!laminas", p_color="amarillo", esporada="blanca", grupo="suelto corro", habitat="conifera planifolio", s_tam="mediano"),
  ca=["pampeta"], ca_f="EC")

F("pseudoclitocybe-cyathiformis", "Pseudoclitocybe cyathiformis", "medio",
  ["Sombrero de hasta 8 cm de ancho, pardo que se aclara con la edad, con un hundimiento central y el borde enrollado de joven y luego en EMBUDO.",
   "Debajo, LÁMINAS decurrentes o unidas al pie, pálidas que pasan a grises o pardas.",
   "Pie de hasta 12 cm de largo y alrededor de 1 de grosor, a veces más grueso en la base, a menudo algo más pálido que el sombrero.",
   "Esporada blanca. En el suelo del bosque o sobre madera podrida; de septiembre a diciembre; Norteamérica y Europa."],
  ["Sombrero que no sea pardo.", "Láminas que no bajen por el pie."],
  [("Varias especies de comestibilidad desconocida", None, "Wikipedia dice que se parece a varias y no las nombra ni explica cómo separarlas."),
   ("Infundibulicybe gibba", None, "Wikipedia la cita en su ficha como parecida, sin separarlas.")],
  "Wikipedia dice que es «comestible según se cuenta» y que se parece a varias especies de comestibilidad desconocida; esta guía no te la recomienda sin identificación experta. La Enciclopèdia Catalana la valora «acceptable» con el nombre «tassa de bruc fosca».",
  dict(s_color="pardo", s_forma="embudo", h_tipo="!laminas", h_color="blanco gris pardo", esporada="blanca", habitat="madera", s_tam="pequeno mediano"),
  ca=["tassa de bruc fosca"], ca_f="EC")

# ---------------- AMPLIACIÓN 2: más hongos conocidos ----------------
F("hericium-erinaceus", "Hericium erinaceus", "bajo",
  ["Masa grande, irregular y abultada, de 5-40 cm de ancho, normalmente una sola mata (Wikipedia no da el color).",
   "Debajo, no hay láminas ni poros: cuelgan PÚAS (espinas) de 1 a 5 cm o más de largo.",
   "Wikipedia no describe pie.",
   "Carne de textura «carnosa». Esporas blancas. Sobre planifolios, sobre todo haya y arce americanos (también fresno, roble y eucalipto), casi siempre en árboles muertos o en heridas de árboles vivos; de finales de verano a otoño (de agosto a noviembre en Europa). Norteamérica y Eurasia."],
  ["Con láminas o poros en vez de púas colgantes.", "Que crezca en el suelo, no sobre un árbol."],
  [("Hericium americanum y H. coralloides", None, "Wikipedia dice que puede confundirse con otros Hericium de las mismas zonas, sin explicar cómo separarlos."),
   ("Donkia pulcherrima, Radulomyces copelandii y algunas Sarcodontia", None, "Wikipedia las cita como parecidas sin más detalle.")],
  "Wikipedia dice «es una seta comestible» y «generalmente segura»; las propiedades medicinales y la seguridad de los suplementos no están demostradas. Nombres que cita: «melena de león», «yamabushitake».",
  dict(h_tipo="!puas", esporada="blanca", habitat="planifolio madera", s_tam="grande"))

F("hericium-coralloides", "Hericium coralloides", "bajo",
  ["Cuerpo blanquecino muy ramificado y con púas, de unos 4-18 cm de ancho.",
   "Debajo de las ramas cuelgan PÚAS (espinas); de jóvenes sin color indicado y con la edad pardo amarillento pálido.",
   "Wikipedia no describe pie.",
   "Carne blanca; esporada blanca. Saprófita sobre planifolios muertos; de julio a octubre en el este de Norteamérica y de noviembre a marzo en el oeste; Norteamérica, Eurasia y Australia."],
  ["Con láminas o poros.", "Que crezca en el suelo, no sobre madera."],
  [("Hericium abietis y H. erinaceus", None, "Wikipedia las cita como parecidas sin explicar cómo separarlas.")],
  "Wikipedia dice «la especie es comestible y buena» cuando es joven; se vuelve quebradiza y descolorida con la edad. Nombres que cita: «coral tooth fungus», «comb coral mushroom».",
  dict(s_color="blanco", h_tipo="!puas", esporada="blanca", habitat="planifolio madera"))

F("stropharia-rugosoannulata", "Stropharia rugosoannulata", "medio",
  ["Sombrero de hasta 30 cm de ancho, rojizo, convexo y luego aplanado.",
   "Debajo, LÁMINAS unidas al pie, pálidas al principio, luego grises y por fin pardo púrpura oscuras.",
   "Pie alto y blanco, con un ANILLO arrugado; toda la seta alcanza unos 20 cm de alto.",
   "Carne blanca y firme; esporada de pardo púrpura oscuro a negra. Sobre virutas de madera, en verano y otoño; Norteamérica, Europa, introducida en Australia y Nueva Zelanda."],
  ["Sin anillo en el pie.", "Láminas rosadas (sería un Agaricus)."],
  [("Stropharia hornemannii", None, "es del mismo género; Wikipedia no dice cómo separarlas."),
   ("Agaricus", None, "Wikipedia dice que se separan por tener normalmente las láminas más rosadas.")],
  "Wikipedia dice que «se considera una seta comestible selecta» y que algunos autores la llaman «muy sabrosa»; no habla de toxicidad.",
  dict(s_color="rojo pardo", s_forma="convexo", h_tipo="!laminas", h_color="gris violeta pardo", p_anillo="!si", p_color="blanco", esporada="chocolate negra", habitat="madera", s_tam="grande"))

P("gymnopilus-junonius", "Gymnopilus junonius (G. spectabilis)", "toxica",
  ["Sombrero de 5-30 cm de ancho, en forma de bollo y luego convexo a plano; amarillo anaranjado vivo de joven y pardo anaranjado o pardo rojizo de viejo; superficie seca y con escamas.",
   "Debajo, LÁMINAS unidas al pie o algo decurrentes (Wikipedia no da su color).",
   "Pie de 5-25 cm de largo y 1-5 de grosor, con un ANILLO frágil espolvoreado de esporas naranja oxidado; la base suele estrecharse.",
   "Carne amarilla, de olor suave y sabor amargo (con potasa se tiñe de rojo y al cocinarla se vuelve verde); esporada pardo óxido. En grupos de varios a decenas sobre tocones, troncos o bases de árboles, de planifolios y de coníferas, sobre todo en zonas húmedas de llanura junto a ríos. Europa, Australasia y Sudamérica (Wikipedia dice que no hay en Norteamérica)."],
  "Con Gymnopilus ventricosus (a menudo confundida con ella; tampoco tiene psilocibina), con G. luteus y G. subspectabilis (que sí contienen psilocibina), con la Armillaria mellea y con Omphalotus olivascens (Wikipedia no da rasgos para separarlas). Wikipedia dice que «no es comestible y contiene algunas neurotoxinas» y que además «no es comestible por su sabor amargo».",
  dict(s_color="amarillo naranja pardo rojo", s_super="escamas", s_forma="convexo", h_tipo="!laminas", p_anillo="si", esporada="marron", grupo="mechon", habitat="conifera planifolio madera", s_tam="grande"))

P("pleurocybella-porrigens", "Pleurocybella porrigens", "muyt",
  ["Sombrero blanquecino de 4-9 cm de ancho, «en forma de pétalo o abanico».",
   "Debajo, LÁMINAS apretadas, decurrentes si hay pie (Wikipedia no da su color).",
   "Pie muy corto o inexistente.",
   "Carne fina y frágil, más que la de los Pleurotus, de olor tenue y agradable; esporada blanca. Sobre madera de coníferas, sobre todo cicuta (Tsuga): pudrición blanca; de agosto a noviembre en Norteamérica; zonas templadas del hemisferio norte."],
  "Wikipedia no cita especies parecidas (solo compara su carne con la de los Pleurotus). Wikipedia dice que «antes se consideraba comestible, aunque insípida» y que se sospecha de ella en dos brotes en Japón con encefalopatía mortal, con víctimas que en su mayoría tenían enfermedad renal previa; el mecanismo de toxicidad no se ha establecido definitivamente. Nombre que cita: «angel wing» (ala de ángel).",
  dict(s_color="blanco", h_tipo="!laminas", esporada="blanca", habitat="conifera madera", s_tam="pequeno mediano"))

F("hypsizygus-ulmarius", "Hypsizygus ulmarius (Pleurotus ulmarius)", "bajo",
  ["Sombrero de 6-15 cm de ancho (a veces más), de blanco a crema, uniforme; convexo con el borde enrollado y a veces hundido; liso y con la edad con grietas como un mosaico (areolado).",
   "Debajo, LÁMINAS unidas al pie o apenas decurrentes (Wikipedia no da el color).",
   "Pie SIN anillo, sin adornos; sale del árbol y se curva hacia arriba para unirse cerca del centro del sombrero.",
   "Esporada de blanca a crema pálido. Sobre olmo, negundo y haya (otros árboles también), en heridas altas de árboles vivos y también en muertos; en grupos de 1 a 3 o algo más; zonas templadas de Norteamérica, Europa y Asia."],
  ["Con anillo o con el pie central y sin curva.", "Que crezca en el suelo sin madera."],
  [("Pleurotus (gírgolas)", None, "tienen las láminas profundamente decurrentes; las de Hypsizygus ulmarius no."),
   ("Hypsizygus tessulatus", None, "suele crecer más en ramos."),
   ("Ossicaulis lignatilis", None, "más pequeña y sale de cavidades de la madera."),
   ("Pleurotus levis", None, "también tiene las láminas decurrentes.")],
  "Wikipedia dice «es una especie comestible»; muchos buscadores la encuentran más dura y de menos sabor que la gírgola. La Enciclopèdia Catalana la valora «bo» con el nombre «gírgola d'om».",
  dict(s_color="blanco", s_super="lisa", s_forma="convexo", h_tipo="!laminas", p_anillo="no", esporada="blanca", habitat="planifolio madera", s_tam="mediano grande"),
  ca=["gírgola d'om"], ca_f="EC")

P("ampulloclitocybe-clavipes", "Ampulloclitocybe clavipes (Clitocybe clavipes)", "toxica",
  ["Sombrero de 4-8 cm de ancho, convexo con un pequeño mamelón y luego plano o hundido; superficie lisa, a menudo con fibrillas, normalmente húmeda; gris pardo (a veces con tinte oliváceo) y borde pálido.",
   "Debajo, LÁMINAS muy decurrentes (bajan por el pie), crema amarillentas, con laminillas intercaladas y algunas bifurcadas cerca del pie.",
   "Pie de 3-7 cm de alto y 1-1,5 de ancho, con la base MUY ENSANCHADA en bulbo, cubierto de fibras sedosas y del color del sombrero.",
   "Carne gruesa, blanca y algo amarilla en la base; el pie es tenaz por fuera y esponjoso y blando por dentro; acuosa; olor ligeramente dulce (se compara con almendra amarga, azahar, canela o chicle de uva); esporada blanca. En bosques de coníferas y de planifolios, sobre todo bajo hayas; agosto a noviembre en el norte de Europa."],
  "Con Ampulloclitocybe avellaneialba (oeste de Estados Unidos; más grande, de sombrero más oscuro y láminas blancas) y con Clitocybe nebularis (que se separa por su pie ensanchado, sus láminas muy decurrentes y su color más oscuro). Wikipedia la describe como «potencialmente comestible» o comestible pero poco agradable, aunque otros la dan por no comestible; se parece a especies venenosas y contiene toxinas que la hacen peligrosa si se toma con alcohol (reacción tipo disulfiram). Por eso esta guía la trata como NO comestible.",
  dict(s_color="gris pardo verde", s_forma="convexo embudo", s_super="lisa", h_tipo="!laminas", h_color="amarillo blanco", p_color="gris pardo", p_base="ensanchada", olor="almendra", esporada="blanca", habitat="conifera planifolio", s_tam="pequeno mediano"))

P("leucoagaricus-leucothites", "Leucoagaricus leucothites (Leucocoprinus leucothites)", "toxica",
  ["Sombrero de 4-15 cm de ancho, de superficie granulosa, blanco o gris pardo (a veces grisáceo o rosado).",
   "Debajo, LÁMINAS (Wikipedia menciona su color rojizo al magullarlas; no da más).",
   "Pie de 5-12 cm de largo, con la base ancha y que se magulla amarillo o pardo, con un ANILLO normalmente presente.",
   "Carne que se magulla amarillenta al cortarla; esporada blanca. En zonas de hierba removida como jardines y parques, y a veces en bosques; en todo el mundo, sobre todo Europa y Norteamérica."],
  "Con especies de Agaricus y con la mortal Amanita ocreata (Wikipedia no dice cómo separarlas). Wikipedia dice que «a veces se considera comestible» pero que «se sospecha que es venenosa» por toxinas que dan molestias gástricas. Nombres que cita: «smooth parasol», «white dapperling».",
  dict(s_color="blanco gris pardo", h_tipo="!laminas", p_anillo="si", corte="amarillea", esporada="blanca", habitat="prado", s_tam="mediano grande"))

P("leucocoprinus-birnbaumii", "Leucocoprinus birnbaumii", "toxica",
  ["Sombrero de 2,5-6 cm de ancho, que pasa de forma de huevo o cilindro a acampanado y plano, a veces con mamelón; amarillo limón a amarillo azufre, liso o algo polvoriento, con escamas fibrosas irregulares que se desprenden fácilmente y se oscurecen hacia el centro; borde estriado.",
   "Debajo, LÁMINAS libres, amarillo azufre, hasta 4 mm de ancho.",
   "Pie de 3-10 cm de largo y fino, con la base ensanchada como maza, hueco, amarillo limón a azufre con escamas finas polvorientas; ANILLO fino, membranoso y móvil, amarillo arriba y blanquecino abajo, que puede desaparecer.",
   "Carne del sombrero blanquecina y blanda con la edad; esporada blanca. Saprófita en materia vegetal muy descompuesta (humus, compost); común en el trópico y subtrópico; en Europa y Norteamérica, casi siempre en invernaderos, macetas y terrarios; sola o en grupitos."],
  "Con Leucocoprinus straminellus (algo más pálido o blanquecino; se separa solo con microscopio), L. flavescens (sombrero amarillo pálido a blanco con el centro pardusco), L. brunneoluteus (sudamericano, de mamelón pardo marcado) y Leucoagaricus sulphurellus (del Caribe, con láminas que se ponen azul verdoso al magullarlas). Wikipedia dice «es tóxica si se ingiere» y que puede causar síntomas de gastroenteritis; una universidad de Estados Unidos la clasifica como de «gravedad media» y otra dice que el nivel de toxicidad es «simplemente desconocido». Nombres que cita: «flowerpot parasol» (parasol de maceta).",
  dict(s_color="amarillo", s_super="escamas", s_forma="conico convexo", h_tipo="!laminas", h_color="amarillo", p_anillo="si", p_color="amarillo", p_base="ensanchada", interior="hueco", esporada="blanca", s_tam="pequeno"))

F("coprinellus-disseminatus", "Coprinellus disseminatus", "bajo",
  ["Sombrero acampanado de color tostado que se vuelve gris con la edad; toda la seta mide hasta unos 4 cm de alto.",
   "Wikipedia no describe las láminas (solo dice que la foto las muestra).",
   "Wikipedia no describe el pie.",
   "Esporada pardo negruzca. Sobre madera muerta como tocones podridos; en grupos muy numerosos («trooping»: raramente solitaria). En Europa y Norteamérica; de mayo a noviembre en el este de Norteamérica."],
  ["Que crezca sola, no en grupo numeroso.", "Que se disuelva en tinta negra al madurar (esta especie NO se deshace)."],
  [("Tulosesus y otras setas parecidas", None, "Wikipedia dice que cuesta separarla de especies relacionadas y no explica cómo; sí dice que, a diferencia de casi todos los coprinoides, no se deshace en tinta al madurar.")],
  "Wikipedia dice «la especie no es venenosa» y que es demasiado pequeña para interesar.",
  dict(s_color="pardo gris", s_forma="conico", esporada="chocolate negra", grupo="!mechon", habitat="!madera", s_tam="pequeno"))

P("cortinarius-violaceus", "Cortinarius violaceus", "nocom",
  ["Sombrero de 3,5-15 cm de ancho, violeta oscuro a negro azulado, convexo y luego aplanado o con mamelón, con el borde enrollado; cubierto de escamas finas aterciopeladas, no pegajoso (a veces algo graso).",
   "Debajo, LÁMINAS violeta oscuro que con la edad pasan a pardo purpúreas, unidas al pie.",
   "Pie de 6-18 cm de alto (hasta 12 en el texto introductorio) y 1-2 de grosor, con la base HINCHADA en bulbo de hasta 4 cm, del color del sombrero y cubierto de fibrillas lanosas; de joven con una cortina que desaparece pronto.",
   "Carne violeta, más oscura bajo la piel y en el pie, de olor y sabor suaves y agradables (recuerdan al cedro); con potasa se tiñe de rojo; esporada de color óxido. Solitaria o en grupos pequeños, a menudo junto a madera podrida y a veces en corros. En Europa bajo planifolios (roble, abedul, haya), a veces coníferas, en suelos ácidos y en otoño; en Norteamérica prefiere coníferas. Micorrícica."],
  "Con Cortinarius iodes (sombrero violeta viscoso y pie violeta más pálido), con otros Cortinarius de la sección Cortinarius (se separan por el árbol y por la zona), con Leptonia carnea y L. nigroviolacea (color parecido; esporada rosa) y con C. cotoneus, Entoloma bloxamii y E. parvum (Wikipedia las cita sin explicar cómo separarlas). Wikipedia dice que «a veces se describe como comestible», que «a veces se considera no comestible» y «comestible pero sin interés», que cocinada es «según se cuenta amarga» y que su parecido con otros Cortinarius no comestibles o tóxicos «hace arriesgado comerla».",
  dict(s_color="violeta negro", s_super="escamas", s_forma="convexo", h_tipo="!laminas", h_color="violeta pardo", p_color="violeta", p_base="ensanchada", esporada="marron", habitat="planifolio conifera", s_tam="mediano grande"))

P("cortinarius-armillatus", "Cortinarius armillatus", "toxica",
  ["Sombrero de 4-13 cm de ancho, pardo anaranjado, de forma de bollo o campana y luego aplanado, a veces con escamitas.",
   "Debajo, LÁMINAS tostadas de jóvenes y pardo óxido después, algo apretadas, unidas al pie con una curva suave.",
   "Pie de hasta 15 cm de largo y unos 2,5 de grosor, tostado, normalmente más ancho en la base, con 1-5 BANDAS rojizas.",
   "Carne parda clara, de olor suave a rábano; esporada pardo óxido. Bajo abedules; de agosto a septiembre; Norteamérica (sobre todo el noreste) y Europa."],
  "Con Cortinarius bolaris, C. boulderensis, C. haematochelis, C. paragaudis, C. rubicundulus y C. subtestaceus (Wikipedia no dice cómo separarlas). Wikipedia dice que «a veces se cita como comestible» pero contiene la micotoxina orellanina, en concentraciones mucho menores que las del Cortinarius orellanus (ver la ficha de peligrosas de esta guía); la considera comestible mediocre a buena «con cuidado de confirmar su identificación», y algunas guías la dan por no comestible. Nombres que cita: «red-banded cort», «bracelet cortinarius».",
  dict(s_color="naranja pardo", s_forma="convexo", h_tipo="!laminas", h_color="pardo", p_color="pardo", p_base="ensanchada", esporada="marron", habitat="planifolio", s_tam="mediano grande"))

P("rubroboletus-legaliae", "Rubroboletus legaliae", "toxica",
  ["Sombrero de hasta 14 cm de ancho, blanco roto o color café de joven, a menudo gris ratón pálido en la madurez (no siempre) y rosa viejo con la edad.",
   "Debajo, POROS rojos de joven y naranjas al madurar (existe una forma amarilla en Windsor Great Park); se vuelven AZULES al magullarlos.",
   "Pie rechoncho, naranja arriba y pálido hacia el medio, vinoso oscuro en la base, con una red roja fina arriba (más marcada cuando se aclara el naranja; falta en la base y puede quedar tapada por tierra u hojarasca).",
   "Carne azul pálido al cortarla, a veces despacio (un minuto) y a veces casi al instante, vinoso oscuro en la base del pie; olor a achicoria. Bajo roble y haya, en suelo neutro a ácido, en bosque abierto o parque soleado. Poco común en el sur de Inglaterra y Europa; considerada vulnerable en Chequia y en Gran Bretaña."],
  "Con Rubroboletus satanas, muy emparentado (en bosque de hoja ancha sobre suelo calizo; se separa por su sombrero más blanco que pasa a pardo ocre sin los tonos rojizos de la madurez y por un olor más desagradable). Wikipedia dice que «es venenosa, con síntomas sobre todo gastrointestinales».",
  dict(s_color="blanco gris rosa pardo", h_tipo="!poros", h_color="rojo naranja", p_color="naranja violeta", p_super="red", corte="!azulea", habitat="planifolio", s_tam="grande"))

P("amanita-porphyria", "Amanita porphyria", "nocom",
  ["Sombrero de 4-10 cm de ancho, pardo con un tinte violáceo o grisáceo, hemisférico de joven y plano después, liso y a veces con restos de velo grises.",
   "Debajo, LÁMINAS blanquecinas, libres (no tocan el pie), que se oscurecen al magullarlas.",
   "Pie de 5-12 cm de alto y 0,6-1,5 de grosor, con un ANILLO frágil gris violáceo o ennegrecido y la base en BULBO, que puede o no estar envuelto en una volva blanca membranosa.",
   "Carne blanca con olor a patata cruda o a rábano; esporas blancas. En suelos pobres, sobre todo bajo pícea (también abeto, cicuta y algún planifolio como abedul); micorrícica; de verano a otoño; más común en montaña y en el norte. Muy común en los bosques boreales de Europa."],
  "Con Amanita citrina (de forma y olor parecidos; se separa por el color del sombrero y el anillo gris violeta), con Amanita pantherina y con la mortal Amanita phalloides (Wikipedia no dice cómo separarlas). Wikipedia la describe como «no comestible» y «no apta para el consumo», y avisa de que se confunde fácilmente con especies mucho más venenosas.",
  dict(s_color="pardo violeta gris", s_super="lisa", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_anillo="si", p_base="bolsa ensanchada", esporada="blanca", habitat="conifera", s_tam="pequeno mediano"))

P("amanita-echinocephala", "Amanita echinocephala (A. solitaria)", "toxica",
  ["Sombrero de hasta 15 cm de ancho, de blanco a marfil o gris plata, cubierto de verrugas piramidales levantadas que se hacen más pequeñas y escasas hacia el borde (restos del velo); de joven, botones más oscuros y a veces «en dos pisos».",
   "Debajo, LÁMINAS crema, a veces con un tinte verdoso, casi libres, con a veces un pequeño diente decurrente.",
   "Pie de 8-16 cm de alto y 2-3 de ancho, blanco a marfil, con varios anillos de escamas vueltas hacia arriba cerca del BULBO de la base (sin volva bien formada) y bastante enterrado; ANILLO fino y frágil que a menudo se pega al pie.",
   "Carne blanca, de olor desagradable. En suelos calizos, ligeros y secos, bajo haya y otros planifolios y también coníferas (en Chequia, a menudo con tilos); en verano y principios de otoño; sola o en grupos pequeños; resiste muy bien la sequía. Gran Bretaña, Europa, oeste de Asia y norte de África; rara y protegida."],
  "Con Amanita strobiliformis (más robusta, con placas planas y gruesas en el sombrero, restos de velo colgando en el borde y anillo harinoso; suele crecer a su lado) y con Amanita vittadinii (verrugas cónicas y escamas curvadas hasta la cara inferior del anillo, en suelos más pesados). Wikipedia dice que «algunos la dan por comestible, pero probablemente es mejor evitarla por si se confunde con otras Amanita venenosas», y que hay informes de efectos nefrotóxicos (daño en el riñón) parecidos a los de Amanita smithiana.",
  dict(s_color="blanco gris", s_super="escamas", h_tipo="!laminas", h_color="blanco", p_anillo="si", p_color="blanco", p_base="ensanchada", habitat="planifolio conifera", s_tam="grande"))

P("lactarius-turpis", "Lactarius turpis (L. necator)", "nocom",
  ["Sombrero de 4-20 cm de ancho, verde oliva a pardo amarillento que se oscurece hasta casi negro con la edad; con el borde enrollado y el centro algo hundido de joven y luego en embudo; pegajoso o viscoso en el centro, con zonas aterciopeladas de joven, a veces peludo en el borde y lleno de restos.",
   "Debajo, LÁMINAS apretadas, blanco sucio, algo decurrentes, que la leche vieja tiñe de pardo oliváceo.",
   "Pie de hasta 7 cm de alto y 3 de ancho, de color parecido al sombrero pero mucho más claro, a veces con hoyuelos poco profundos.",
   "Carne blanco sucio que tiende a volverse parda, de poco olor y sabor ACRE, sobre todo la leche, que es abundante, blanca al aire y tiñe las láminas de pardo oliváceo; se tiñe de púrpura con potasa o amoníaco; esporada crema. Sobre todo con abedul, también con pícea, pino y otros en bosque mixto. Europa y Siberia; introducida en Australia y Nueva Zelanda; también en Norteamérica."],
  "Con Lactarius olivaceoumbrinus (noroeste de Estados Unidos: color oliva pardo más fuerte, manchas oscuras en el pie, normalmente solitaria) y Lactarius atroviridis (parecida, sin más detalle). Wikipedia dice que contiene la sustancia mutágena necatorina, por lo que «no se puede recomendar su consumo»; la mayoría de autoridades de Europa occidental la clasifican como «no comestible» o «pobre», aunque en Rusia y el norte y este de Europa se consume. Nombres que cita: «ugly milk-cap», «green birch milk cap».",
  dict(s_color="verde pardo negro", s_super="viscosa", s_forma="embudo", h_tipo="!laminas", h_color="blanco", latex="blanco", esporada="blanca", habitat="planifolio conifera", s_tam="mediano grande"))

F("lactarius-deterrimus", "Lactarius deterrimus", "bajo",
  ["Sombrero de 3-10 cm de ancho (a veces 12), convexo de joven y luego plano, en embudo y hundido; de color mandarina a pardo anaranjado, más oscuro hacia el borde y que acaba amarillo pardo; sin pelillos, graso con humedad y algo brillante en seco; con la edad, tras el frío o la helada, se vuelve verdoso sucio o con manchas verdes.",
   "Debajo, LÁMINAS apretadas, naranja pálido a ocre pálido, frágiles, algo decurrentes, con láminas cortas intercaladas y algunas bifurcadas cerca del pie; se ponen rojo oscuro y luego gris verdoso al envejecer o dañarse.",
   "Pie sobre todo largo y cilíndrico, naranja rojizo, de 4-8 cm de largo (a veces 10) y 1-1,5 de ancho, con hoyuelos apenas marcados; la base suele engrosarse y se vuelve hueca.",
   "Carne frágil, amarillenta pálida y a menudo con gusanos, que se pone rojo zanahoria, luego granate y luego verde sucio en horas; olor fuerte afrutado; sabor primero suave y luego algo resinoso amargo; la LECHE es naranja y se pone rojo zanahoria y después granate en 10-30 minutos, de sabor claramente amargo; esporada ocre pálido. Micorrícica con la pícea de Noruega, en pícea-abeto y en plantaciones de pícea (también en hayedos y robledales con pícea, bordes y claros); de finales de junio a noviembre, sobre todo de agosto a octubre. Sobre todo Europa."],
  ["Leche que se queda naranja o roja sin pasar a granate en 30 minutos (sería Lactarius deliciosus).", "Que crezca con pinos y no con pícea."],
  [("Lactarius deliciosus", None, "su leche se queda naranja o enrojece en 30 minutos (no granate) y es de sabor suave; el sombrero verdea con los pinos, no con la pícea. Mira la ficha de los rovellones de esta guía."),
   ("Lactarius semisanguifluus", None, "muy rara; la leche se pone granate en 5-8 minutos, el sombrero viejo se vuelve casi todo verdoso y crece bajo pinos."),
   ("Lactarius fennoscandicus", None, "boreal a subalpina; sombrero claramente zonado pardo anaranjado, a veces con tonos gris púrpura; pie ocre naranja pálido.")],
  "Wikipedia dice «Lactarius deterrimus es una seta comestible», mucho menos apreciada que el rovelló (Lactarius deliciosus): la leche es amarga y suele tener gusanos. Wikipedia dice que se separa de las parecidas por el árbol con el que vive o por el color de la leche.",
  dict(s_color="naranja pardo", s_forma="convexo embudo", h_tipo="!laminas", h_color="naranja amarillo", p_color="naranja", latex="!naranja", corte="enrojece", olor="fruta", esporada="blanca", habitat="conifera", s_tam="pequeno mediano"))

F("lactarius-pallidus", "Lactarius pallidus", "medio",
  ["Sombrero de 4-10 cm de ancho, convexo aplanado que acaba en embudo, con el borde enrollado de joven; color ante pálido (a veces apagado y con un tono rosado), a veces pardo pálido o carne claro; liso, firme y pegajoso.",
   "Debajo, LÁMINAS apretadas, bastante decurrentes (bajan por el pie), de ante rosado a ante amarillento; sueltan LECHE blanca al cortarlas.",
   "Pie de 3-8 cm de alto y 6-28 mm de grosor, cilíndrico o algo estrechado en la base, del color del sombrero o blanquecino.",
   "Carne blanca a ante, gruesa; leche blanca, de sabor suave a moderadamente picante; esporada ocre pálido con un ligero tinte salmón. Micorrícica, normalmente bajo haya (también abedul), a medio enterrar entre la hojarasca; puede salir en grupos grandes; verano y otoño. Común en Europa, menos en Norteamérica y también en Australia."],
  ["Leche que no sea blanca.", "Sabor muy picante (sería otra especie)."],
  [("Lactarius affinis", None, "parecida; la L. pallidus no tiene el sabor picante de la L. affinis.")],
  "Wikipedia dice que «generalmente se considera comestible», sobre todo después de cocinarla, que «no se recomienda comerla cruda» y que algunos micólogos la tienen por no comestible. Esta guía no te la recomienda sin identificación experta.",
  dict(s_color="pardo rosa", s_super="viscosa", s_forma="embudo", h_tipo="!laminas", h_color="rosa amarillo", p_color="pardo blanco", latex="!blanco", esporada="blanca", habitat="planifolio", s_tam="pequeno mediano"))

F("russula-vesca", "Russula vesca", "medio",
  ["Sombrero de 5-10 cm de ancho, plano, convexo o algo hundido en el centro, ligeramente pegajoso, de pardusco a rojo ladrillo oscuro; la cutícula normalmente no llega hasta el borde.",
   "Debajo, LÁMINAS apretadas y blancas.",
   "Pie de 2-7 cm de largo y 1,5-2,5 de ancho, blanco y más estrecho hacia la base.",
   "Carne de sabor suave; con sales de hierro se pone salmón profundo; esporada blanca. Sobre todo en bosques de planifolios de Europa y Norteamérica, en verano u otoño."],
  ["Sabor picante o amargo.", "Sombrero rojo vivo, o láminas que no sean blancas."],
  [("Otras rúsulas", "toxica", "Wikipedia no cita parecidas, pero en esta guía hay rúsulas picantes (por ejemplo la Russula emetica) que dan molestias digestivas; la ficha de peligrosas explica cómo se reconocen.")],
  "Wikipedia dice que «se considera comestible y buena, de sabor suave a nuez» y que en Rusia, Ucrania y Finlandia «se considera totalmente comestible incluso cruda»; no habla de toxicidad. Nombres que cita: «bare-toothed russula», «the flirt».",
  dict(s_color="pardo rojo", s_forma="convexo", h_tipo="!laminas", h_color="blanco", p_color="blanco", esporada="blanca", habitat="planifolio", s_tam="pequeno mediano"))

F("russula-ochroleuca", "Russula ochroleuca", "medio",
  ["Sombrero de 5-12 cm de ancho, amarillo apagado, convexo y luego plano o algo hundido, con el borde acanalado de maduro y la cutícula que se pela unos dos tercios.",
   "Debajo, LÁMINAS de blancas a blanco grisáceo, unidas al pie con una muesca.",
   "Pie de 3-7 cm de largo y 1-2 de ancho, cilíndrico, blanco y luego grisáceo.",
   "Sabor de suave a moderadamente picante. En bosques de planifolios y de coníferas; muy común en el noroeste de Europa; en Estados Unidos, bajo coníferas, abedules y álamos temblones del norte."],
  ["Sombrero que no sea amarillo.", "Sabor dulce y agradable, que sería Russula claroflava."],
  [("Russula claroflava", None, "de aspecto parecido; Wikipedia dice que solo se separa por el sabor, «mucho mejor» que el de R. ochroleuca.")],
  "Wikipedia no usa palabras de comestibilidad ni de toxicidad para esta especie. Por su sabor de suave a picante, esta guía no te la recomienda.",
  dict(s_color="amarillo", s_forma="convexo", h_tipo="!laminas", h_color="blanco gris", p_color="blanco gris", habitat="conifera planifolio", s_tam="pequeno mediano"))

F("russula-fellea", "Russula fellea", "bajo",
  ["Sombrero de 4-9 cm de ancho, convexo y luego aplanado, a menudo con un mamelón ancho; color paja o miel; a veces surcado en el borde al madurar.",
   "Debajo, LÁMINAS unidas al pie con muesca, del color del pie.",
   "Pie firme y robusto, de 2-6 cm de alto y 1-2 de ancho, más pálido que el sombrero.",
   "Carne blanca que no cambia de color al cortarla, con olor a geranio o a compota de manzana y sabor PICANTE y amargo; esporada de blanca a crema pálido. En otoño, con haya en Gran Bretaña y a veces con pícea en Europa, en suelos ácidos bien drenados; bosques de planifolios y de coníferas. Zonas templadas del norte de Europa y Asia; falta en Norteamérica."],
  ["Sabor suave y no amargo.", "Olor que no sea afrutado."],
  [("Russula simillima", None, "especie emparentada que la sustituye en Norteamérica; Wikipedia no da rasgos para separarlas.")],
  "Wikipedia dice «esta seta es no comestible», con «sabor muy picante y amargo»; no habla de toxicidad. La Enciclopèdia Catalana no la recoge.",
  dict(s_color="amarillo pardo", s_forma="convexo", h_tipo="!laminas", corte="nada", olor="fruta", esporada="blanca", habitat="planifolio conifera", s_tam="pequeno mediano"))

F("russula-rosea", "Russula rosea (R. lepida)", "bajo",
  ["Sombrero de hasta 10 cm de ancho, convexo y luego aplanado, sobre todo rojo vivo (del rojo cinabrio al carmín), a menudo con manchas amarillas.",
   "Debajo, LÁMINAS frágiles, amarillo paja pálido, a veces con el borde rojo en el borde del sombrero.",
   "Pie normalmente teñido de carmín, pero a veces blanco puro.",
   "Carne de sabor duro y amargo; esporas de crema pálido. Común en las regiones templadas del norte."],
  ["Pie y sombrero sin nada de rojo.", "Sabor suave."],
  [("Russula pseudointegra", None, "rara; se separa por su carne picante."),
   ("Russula xerampelina", None, "puede confundirse con las formas de pie rojo de R. rosea; se separa por su carne más blanda y la falta de sabor leñoso.")],
  "Wikipedia dice que «algunos la consideran comestible y otros no comestible». Con ese sabor duro y amargo, esta guía no te la recomienda.",
  dict(s_color="rojo", s_forma="convexo", h_tipo="!laminas", h_color="amarillo", p_color="rojo blanco", esporada="blanca", s_tam="pequeno mediano"))

P("tricholoma-vaccinum", "Tricholoma vaccinum", "nocom",
  ["Sombrero de 2,5-8 cm de ancho, canela rojizo a naranja pardusco o tostado, primero cónico ancho, luego convexo y por fin aplanado; borde peludo de joven por restos del velo parcial; superficie fibrosa a escamosa, con escamas planas con la edad.",
   "Debajo, LÁMINAS blanco sucio, a menudo con manchas pardo rojizas, unidas al pie o con muesca, apretadas.",
   "Pie de 3-8 cm de largo y 1-2 de grosor, blanquecino o del color del sombrero pero más claro (blanco arriba y pardo rojizo abajo), fibroso a escamoso, hueco con la edad, SIN anillo.",
   "Carne de olor desagradable; esporada blanca. Micorrícica con coníferas (sobre todo pino y pícea), en el suelo, en grupos o mechones, a veces entre musgo; de finales de verano a otoño. Norte de Asia, Europa y Norteamérica; común en Centroeuropa; rara en el Reino Unido."],
  "Con Tricholoma imbricatum (más pardo apagado, menos robusto, con el pie macizo y no hueco), con T. inodermeum (sombrero menos lanoso, carne que se pone rosa rojizo al dañarla, solo con pinos y en suelo calizo), con T. fracticum, T. dryophilum y T. muricatum (otros Tricholoma pardos, sin rasgos para separarlos) y con los Inocybe (el sombrero escamoso puede confundir; se separan por la esporada parda). Wikipedia dice que algunas fuentes la dan por comestible, pero que es «de baja calidad» y «se dice que levemente venenosa», y «no se recomienda su consumo» por su parecido con Tricholoma pardos tóxicos; Miller la da como «amarga y no comestible».",
  dict(s_color="naranja pardo rojo", s_super="escamas", s_forma="conico convexo", h_tipo="!laminas", h_color="blanco pardo", p_anillo="no", p_color="blanco pardo", interior="hueco", esporada="blanca", grupo="mechon", habitat="conifera", s_tam="pequeno mediano"))

F("tricholoma-imbricatum", "Tricholoma imbricatum", "medio",
  ["Sombrero de 6-18 cm de ancho, pardo a pardo rojizo, a menudo escamoso.",
   "Debajo, LÁMINAS blanquecinas que con la edad se manchan de pardo rojizo, unidas al pie o con muesca.",
   "Pie de 3,5-12 cm de largo y 1-3 de grosor (Wikipedia no da el color).",
   "Esporada blanca. En el suelo de bosques de coníferas de Norteamérica y Europa."],
  ["Sombrero viscoso (serían otros Tricholoma de sombrero pegajoso).", "Láminas que mantienen un blanco puro con la edad."],
  [("Tricholoma dryophilum, T. fracticum, T. manzanitae y T. vaccinum", None, "Wikipedia las cita como parecidas sin dar rasgos para separarlas; el T. vaccinum de esta guía tiene el pie hueco, el T. imbricatum macizo."),
   ("Tricholoma muricatum, T. populinum y T. ustale", None, "tienen el sombrero viscoso y suelen vivir en otros ambientes."),
   ("Leucopaxillus amarus", None, "conserva las láminas blancas con la edad."),
   ("Tricholoma del grupo pessundatum", "toxica", "Wikipedia dice que podría confundirse con miembros venenosos de este grupo.")],
  "Wikipedia dice que «la especie puede ser comestible, pero tiene una textura dura y poco agradable». Nombre que cita: «matt knight».",
  dict(s_color="pardo rojo", s_super="escamas", h_tipo="!laminas", h_color="blanco pardo", esporada="blanca", habitat="conifera", s_tam="grande"))
