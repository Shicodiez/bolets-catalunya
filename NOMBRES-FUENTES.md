# Nombres en latín, catalán y castellano — fuentes (IMPLEMENTADO el 15/10/2026)

Estado: **implementado**. La guía tiene 50 fichas (30 anteriores + 20 nuevas) y todas llevan su nombre en latín, catalán y castellano.
Los datos están en `tools/nombres_datos.py` (la tabla de abajo se ha generado a partir de ese archivo); `web/guia.html` se genera con `python3 tools/generar_guia.py`.
Fecha de la consulta: 15-oct-2026.

## Regla de trabajo
- El **nombre científico** es la referencia. Los nombres populares **solo** se escriben si aparecen en una fuente consultada; si no, se deja «—» (no se inventa). Los nombres populares **varían según la zona** y no son oficiales.
- De las fuentes se toman **solo los nombres**, no su valoración de «comestible». (La Enciclopèdia Catalana, por ejemplo, da como comestibles *Gyromitra esculenta* y *Tricholoma equestre*, que nuestra guía trata como de riesgo.)
- Los nombres que usa el **predictor** (backend) no se han cambiado («Escarlet», «Cep fosc», «Cep d'estiu»…). Cuando difieren de los de las fuentes, la ficha lo explica en una nota.

## Corrección de un error mío
En el borrador de este documento dije que «mataparent de Satanàs», «cep vermell» y «cep negre» no aparecían en ninguna fuente. **Era incorrecto**: sí aparecen en títulos de bolets.com y boletaires.cat (código BOLETS), así que se han **mantenido** con esa fuente. Lo que sí se corrigió porque ninguna fuente consultada lo daba: «Escarlet» (la ficha se titula ahora «Carlet», y *H. russula* figura como «carlet»), «Trompeta de la muerte» (→ «trompeta de los muertos») y «corro de bruja» (→ «senderuela»).

## Fuentes (códigos)
| Código | Fuente | URL |
|---|---|---|
| EC | Enciclopèdia Catalana | https://www.enciclopedia.cat/historia-natural-dels-paisos-catalans/grau-de-comestibilitat-i-toxicitat-de-diferents-bolets-dels |
| BOLETS | bolets.com y boletaires.cat | https://boletaires.cat |
| 3CAT | 3Cat | https://www.3cat.cat/3catinfo/trucs-i-advertencies-a-lhora-de-collir-bolets-cuinar-los-i-conservar-los/noticia/3311967/ |
| CS | Canal Salut (Generalitat) | https://canalsalut.gencat.cat/ca/detalls/article/Intoxicacions_per_bolets |
| ICHN | Institució Catalana d'Història Natural | https://ichn2.iec.cat/pdf/flbprot.pdf |
| MAD-C | Comunidad de Madrid: setas comercializables (Real Decreto 30/2009) | https://www.comunidad.madrid/node/74536 |
| MAD-N | Comunidad de Madrid: setas no comercializables (Real Decreto 30/2009) | https://www.comunidad.madrid/node/74537 |
| MAD-T | Comunidad de Madrid: setas comercializables tras un tratamiento (Real Decreto 30/2009) | https://www.comunidad.madrid/node/73272 |
| RIO | Gobierno de La Rioja | https://www.larioja.org/medio-ambiente/es/gestion-forestal/aprovechamiento-setas/contenido/especies-recolectables |
| ESW | es.wikipedia.org | https://es.wikipedia.org |

Otras fuentes que se usaron solo para elegir especies: Piqueras, *Butlletí Soc. Cat. Micologia* 1983 (65 casos en dos hospitales de Barcelona, 1972-1982: dato antiguo y pequeño) y GBIF (recuento de registros, ver abajo).

### Límites de los recuentos GBIF
Son **registros de observación**, no abundancia real: dependen de cuánta gente fotografía y sube cada especie. El rectángulo incluye algo de fuera de Cataluña. El recuento separa a veces sinónimos y hay especies con pocos registros que no aparecen en la lista. Se comprobaron 3 cifras sueltas con consultas individuales y coincidieron. Úsese como indicio, no como medida.


## A) Las 50 fichas: nombres con fuente
(— = sin nombre en las fuentes consultadas; entre paréntesis, el código de la fuente)

| Ficha (id) | Latín | Català | Castellano | Nota en la ficha |
|---|---|---|---|---|
| phalloides | *Amanita phalloides* | farinera borda; cogoma verda (EC, BOLETS, CS, 3CAT) | cicuta verde; oronja verde o mortal (MAD-N) |  |
| amanitas-blancas | *Amanita verna · Amanita virosa · A. phalloides var. alba* | cogomassa (A. verna); farinera pudent (A. virosa) (EC) | cicuta blanca, oronja blanca (A. verna); oronja o cicuta fétida, oronja cheposa (A. virosa) (MAD-N) |  |
| lepiota | *Lepiota brunneoincarnata y otras Lepiota* | lepiota metzinosa (EC) | mucerón (MAD-N) |  |
| cortinarius | *Cortinarius orellanus, C. rubellus y afines* | cortinari metzinós (EC) | cortinario de la montaña (ESW) |  |
| galerina | *Galerina marginata* | galerina marginada (EC) | seta rebordeada (MAD-N) |  |
| gyromitra | *Gyromitra esculenta* | bolet de greix (EC) | falsa colmenilla; hongo bonete (ESW) | Las listas de Madrid también le llaman «cagarria» o «sombrerete», pero «cagarria» es además un nombre de las colmenillas: no te fíes de ese nombre. |
| inosperma | *Inosperma erubescens (Inocybe patouillardii)* | — | — |  |
| clitocybe | *Clitocybe rivulosa · Clitocybe dealbata* | clitocibe blanc (EC) | seta de cunetas (C. rivulosa) (MAD-N) |  |
| entoloma | *Entoloma sinuatum* | fals carlet; carlet bord (EC) | seta engañosa; pérfida (MAD-N, ESW) |  |
| satanas | *Rubroboletus satanas* | matagent; mataparent de Satanàs (EC, BOLETS) | boleto de Satanás; mataparientes (MAD-N) |  |
| luridos | *Suillellus luridus · Neoboletus erythropus* | mataparent lívid (S. luridus); mataparents de cama vermella (N. erythropus) (EC) | boleto de pie rojo (N. erythropus) (RIO) |  |
| tylopilus | *Tylopilus felleus* | molleric amarg; sureny amarg; siuró amarg (EC, ICHN) | boleto amargo (ESW) |  |
| pardinum | *Tricholoma pardinum* | fredolic metzinós; fredolic bord (EC, BOLETS) | atigrado; falsa negrilla (MAD-N) |  |
| omphalotus | *Omphalotus olearius* | bolet d'oliu; gírgola d'olivera (EC) | seta de olivo (MAD-N, ESW) |  |
| muscaria | *Amanita muscaria · Amanita pantherina* | reig bord (A. muscaria); pixacà, reig bru (A. pantherina) (EC, BOLETS) | falsa oronja, matamoscas (A. muscaria); oronja pantera, falso galipierno (A. pantherina) (MAD-N) |  |
| torminosus | *Lactarius torminosus* | bolet de cabra (EC) | níscalo de abedul; falso níscalo (MAD-N, ESW) | «Falso níscalo» se usa también para otra especie (Lactarius chrysorrheus): fíate del nombre científico. |
| hypholoma | *Hypholoma fasciculare* | bolet de pi (EC) | seta fasciculada; hifoloma de láminas verdes (MAD-N, ESW) |  |
| chrysorrheus | *Lactarius chrysorrheus* | pinetell bord; rovelló de cabra (EC) | falso níscalo (MAD-N) | «Falso níscalo» se usa también para otra especie (Lactarius torminosus): fíate del nombre científico. Y «rovelló de cabra» NO es un rovelló. |
| paxillus | *Paxillus involutus* | — | seta enrollada; pasillo enrollado (MAD-N, ESW) |  |
| xanthodermus | *Agaricus xanthodermus* | bola de neu pudent (EC) | champiñón amarilleante (MAD-N) |  |
| equestre | *Tricholoma equestre* | groguet; verderol (EC) | seta de los caballeros; verderol (MAD-N) | Esos mismos nombres se usan también para Tricholoma auratum y T. flavovirens: fíate del nombre científico. |
| atramentaria | *Coprinopsis atramentaria (Coprinus atramentarius)* | bolet de femer (EC) | seta antialcohólica (MAD-N) | La Enciclopèdia Catalana usa «bolet de femer» también para otra especie (Coprinus micaceus). |
| emetica | *Russula emetica* | escaldabecs (EC) | — |  |
| rovellons | *Lactarius deliciosus · Lactarius sanguifluus* | rovelló, esclatasangs (L. sanguifluus); pinetell (L. deliciosus) (EC) | níscalo vinoso (L. sanguifluus); níscalo, robellón (L. deliciosus) (MAD-C, RIO) |  |
| cep | *Boletus edulis · B. pinophilus · B. aereus · B. reticulatus* | cep (B. edulis y B. pinophilus); cep vermell (B. pinophilus); sureny fosc, cep negre (B. aereus); sureny (B. reticulatus = B. aestivalis) (EC, BOLETS) | boleto comestible, hongo, calabaza (B. edulis); boleto rojizo, boleto u hongo de pino (B. pinophilus); boleto bronceado, boleto u hongo negro (B. aereus); boleto reticulado o de verano (B. reticulatus) (MAD-C) | El predictor los llama «cep», «cep fosc» (B. aereus) y «cep d'estiu» (B. reticulatus). |
| camagrocs | *Craterellus lutescens* | camagroc (EC) | angula de monte; rebozuelo anaranjado; trompeta amarilla (MAD-C) |  |
| rossinyols | *Cantharellus cibarius* | rossinyol (EC) | rebozuelo; cabrilla; seta de San Juan (MAD-C) |  |
| trompetes | *Craterellus cornucopioides* | trompeta; orella d'ase (EC) | trompeta de los muertos; cuerno de la abundancia (MAD-C, RIO) |  |
| oureig | *Amanita caesarea* | reig; ou de reig (EC) | amanita de los césares; oronja; tana (MAD-C) | Ojo: «oronja» a secas es la A. caesarea, pero «oronja verde» es la mortal Amanita phalloides. |
| colmenilles | *Morchella esculenta · M. elata* | múrgola; rabassola (M. esculenta); arigany (M. conica) (EC) | colmenilla; morilla (MAD-T, RIO) | Las listas de Madrid también le llaman «cagarria», nombre que se usa además para la giromitra (tóxica): no te fíes de ese nombre. |
| llengua | *Hydnum repandum* | llengua de bou; llémena (EC) | gamuza; lengua de gato; lengua de vaca (MAD-C) |  |
| fredolic | *Tricholoma terreum* | fredolic; negret; brunet (EC) | negrilla; ratón (MAD-C) |  |
| escarlet | *Hygrophorus russula* | carlet (EC, 3CAT) | seta cardenal; hongo escarlata (MAD-C, RIO) | El predictor la llama «Escarlet». «Escarlot» es otra especie (Hygrophorus penarius). |
| llenega | *Hygrophorus latitabundus* | llenega negra (EC) | llanega negra; babosa; mocosa (MAD-C) |  |
| apagallums | *Macrolepiota procera* | apagallums (EC) | apagador; galamperna; matacandelas; parasol (MAD-C) |  |
| camasec | *Marasmius oreades* | cama-sec; carrereta (EC) | senderuela; seta de carrerilla (MAD-C) |  |
| moixerno | *Calocybe gambosa* | moixernó (EC) | seta de San Jorge; perrechico; mansarón (MAD-C, RIO) | «Moixernó de tardor» no es esta seta: según bolets.com es Clitocybe nebularis y según la Enciclopèdia Catalana es Lepista luscina. |
| vinosa | *Amanita rubescens* | vinosa; cua de cavall (EC) | amanita rojiza (RIO) |  |
| camperol | *Agaricus campestris* | camperols (EC) | champiñón silvestre (MAD-C) |  |
| pimpinella | *Lepista nuda* | pimpinella morada (EC) | pie azul; borracha; pezón azul (MAD-C, RIO) |  |
| alzinoi | *Armillaria mellea* | alzinoi (EC) | — |  |
| molleric | *Suillus luteus · Suillus granulatus* | pinetell de calceta (S. luteus); molleric, moixí, pinetell (S. granulatus) (EC) | babosa, boleto anillado (S. luteus); boleto granulado (S. granulatus) (MAD-C, RIO) |  |
| coprinus | *Coprinus comatus* | bolet de tinta (EC) | barbuda (RIO) |  |
| orellana | *Pleurotus ostreatus* | orellana (EC) | seta de ostra; seta de concha; seta de alpaca (MAD-C) |  |
| llora | *Russula cyanoxantha* | llores (EC) | carbonera; seta de los cerdos (MAD-C, RIO) |  |
| molinera | *Clitopilus prunulus* | moixernó blanc de tardor (EC) | molinera (RIO) | «Moixernó de tardor» se usa para especies distintas según la fuente: fíate del nombre científico. |
| fredolic-gros | *Tricholoma portentosum* | fredolic gros (EC) | capuchina; seta de charol (MAD-C, RIO) |  |
| pampa | *Infundibulicybe geotropa (Clitocybe geotropa)* | pampa (EC) | cabeza de fraile; platera (MAD-C) |  |
| pollancro | *Cyclocybe cylindracea (Agrocybe aegerita)* | pollancró (EC) | seta de chopo (MAD-C, RIO) |  |
| marcot | *Hygrophorus marzuolus* | marçot (EC, BOLETS) | seta de marzo; marzuelo; seta de ardilla (MAD-C, RIO) |  |

## B) Las 20 especies añadidas (criterio y recuento GBIF)
Esta sección conserva el criterio de elección y los recuentos de GBIF del borrador. **Los nombres definitivos son los de la tabla A** (algunos se ajustaron al redactar las fichas).
Criterio: (1) aparece en la Enciclopèdia Catalana y/o en las listas oficiales; (2) muchos registros en Cataluña (GBIF) o es una confusión peligrosa con otra ficha; (3) peligrosas y confusiones primero.

### Primeras 10 (criterio: peligrosas y confusiones primero)
| Latín | Català | Castellano | GBIF≈ | Por qué |
|---|---|---|---|---|
| *Hypholoma fasciculare* | bolet de pi (EC) | seta fasciculada (MAD-N) | 552 | muy común, tóxica (no comercializable) |
| *Lactarius chrysorrheus* | pinetell bord, rovelló de cabra (EC) | falso níscalo (MAD-N) | 463 | se confunde con rovelló/pinetell; no comercializable |
| *Paxillus involutus* | — | seta enrollada (MAD-N) | 200 | común, tóxica (no comercializable) |
| *Agaricus xanthodermus* | bola de neu pudent (EC) | champiñón amarilleante (MAD-N) | 163 | se confunde con el champiñón silvestre |
| *Tricholoma equestre* | groguet, verderol (EC) | seta de los caballeros, verderol (MAD-N) | 225-234 | no comercializable en España (RD 30/2009) |
| *Coprinopsis atramentaria* | bolet de femer (EC) | seta antialcohólica (MAD-N) | 75 | tóxica con alcohol |
| *Russula emetica* | escaldabecs (EC) | — | 70 | tóxica (no comercializable) |
| *Amanita rubescens* | vinosa, cua de cavall (EC) | amanita rojiza (RIO) | 487 | se confunde con *A. pantherina* |
| *Agaricus campestris* | camperol(s) (EC) | champiñón silvestre (MAD-C) | 221 | se confunde con amanitas blancas y *A. xanthodermus* |
| *Lepista nuda* | pimpinella morada (EC) | pie azul, borracha, pezón azul (MAD-C, RIO) | 623 | muy común |

### Otras 10
| Latín | Català | Castellano | GBIF≈ |
|---|---|---|---|
| *Armillaria mellea* | alzinoi (EC) | — | 635 |
| *Suillus luteus* (+ *S. granulatus*) | pinetell de calceta (luteus); molleric (granulatus) (EC) | babosa (luteus, MAD-C); boleto anillado (RIO); boleto granulado (granulatus, RIO) | 403 / 417 |
| *Coprinus comatus* | bolet de tinta (EC) | barbuda (RIO) | 410 |
| *Pleurotus ostreatus* | orellana (EC) | seta de ostra, seta de concha (MAD-C) | 319 |
| *Russula cyanoxantha* (+ *R. vesca*) | llora, llores (EC) | carbonera, seta de los cerdos (MAD-C); rúsula comestible (vesca, RIO) | 217 / 162 |
| *Clitopilus prunulus* | moixernó blanc de tardor (EC) | molinera (RIO) | 225 |
| *Tricholoma portentosum* | fredolic gros (EC) | capuchina, seta de charol (MAD-C) | 127 |
| *Clitocybe geotropa* | pampa (EC) | cabeza de fraile, platera (MAD-C) | 72 |
| *Agrocybe aegerita* (*cylindracea*) | pollancró (EC) | seta de chopo (MAD-C) | 293 |
| *Hygrophorus marzuolus* | marçot (EC) | seta de marzo, marzuelo, seta de ardilla (MAD-C) | 56 |

### Reserva (no incluidas)
*Leccinum aurantiacum* (abró), *Pleurotus eryngii* (gírgola de panical / seta de cardo; pocos registros GBIF), *Chroogomphus rutilus* (cama de perdiu; muy registrada pero poco buscada), *Amanita ovoidea*, *Amanita citrina*, *Clitocybe nebularis* (pardilla: Madrid la lista como NO comercializable y La Rioja como recolectable → fuentes contradictorias).

## C) Cómo se muestra
Cada ficha: **Latín · Català · Castellano**, cada uno con «—» si no hay nombre en las fuentes, y una línea «Nombres según …» con las fuentes. Los tres nombres entran en el buscador de la guía. El pie de la guía lista las fuentes con enlace y la fecha de consulta.
