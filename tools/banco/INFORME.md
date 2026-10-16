# Banco de pruebas de la lectura de fotos con IA

Generado: 2026-10-16T21:30:36.548Z

Fotos medidas por todas las configuraciones: **30**. Cada foto es de la propia guía (se sabe qué seta es). «Top 5» = la ficha correcta sale entre las 5 primeras al pasar los rasgos leídos por la comparación real de la guía (mismos umbrales que en producción). Referencia: con los rasgos PERFECTOS de cada ficha, la ficha correcta sale primera en 298 de 313 casos.

| Configuración | Fotos | Lectura OK | Rasgos leídos por foto | Rasgos leídos que encajan con la ficha | Top 1 | Top 5 | Top 10 | Sin rasgos suficientes | Neuronas por foto |
|---|---|---|---|---|---|---|---|---|---|
| llama32_v1 | 30 | 30 | 4.7 de 9 | 66 % (70/106) | 3 % | 7 % | 10 % | 0 | 40 |
| llama32_v2 | 30 | 30 | 8.6 de 9 | 65 % (90/138) | 0 % | 10 % | 17 % | 0 | 17 |
| scout_v2 | 30 | 30 | 6.9 de 9 | 74 % (87/117) | 3 % | 13 % | 17 % | 2 | 41 |
| gemma4_v2 | 30 | 30 | 7.4 de 9 | 74 % (88/119) | 13 % | 17 % | 20 % | 1 | 12 |

Qué es cada configuración:
- **llama32_v1**: Lo que hace la guía HOY: Llama 3.2 11B, prompt en castellano, un hueco por llamada (3 llamadas por foto) (@cf/meta/llama-3.2-11b-vision-instruct)
- **llama32_v2**: Llama 3.2 11B con el prompt nuevo (inglés, todos los rasgos, 1 llamada por foto) (@cf/meta/llama-3.2-11b-vision-instruct)
- **scout_v2**: Llama 4 Scout con el prompt nuevo (@cf/meta/llama-4-scout-17b-16e-instruct)
- **gemma4_v2**: Gemma 4 26B con el prompt nuevo (@cf/google/gemma-4-26b-a4b-it; neuronas estimadas)

## Acierto por rasgo (rasgos leídos que encajan con lo que dice la ficha)
| Rasgo | llama32_v1 | llama32_v2 | scout_v2 | gemma4_v2 |
|---|---|---|---|---|
| s_color | 76 % (leído 30/30) | 72 % (leído 30/30) | 85 % (leído 28/30) | 86 % (leído 29/30) |
| s_super | 44 % (leído 30/30) | 50 % (leído 30/30) | 41 % (leído 26/30) | 61 % (leído 28/30) |
| s_forma | 76 % (leído 30/30) | 76 % (leído 30/30) | 81 % (leído 28/30) | 82 % (leído 29/30) |
| h_tipo | 58 % (leído 26/30) | 84 % (leído 28/30) | 91 % (leído 25/30) | 78 % (leído 20/30) |
| h_color | 72 % (leído 26/30) | 68 % (leído 28/30) | 83 % (leído 18/30) | 82 % (leído 18/30) |
| p_anillo | — | 25 % (leído 28/30) | 33 % (leído 20/30) | 57 % (leído 24/30) |
| p_base | — | 0 % (leído 28/30) | 25 % (leído 21/30) | 0 % (leído 23/30) |
| p_super | — | 0 % (leído 28/30) | 0 % (leído 21/30) | 0 % (leído 24/30) |
| p_color | — | 69 % (leído 28/30) | 92 % (leído 21/30) | 75 % (leído 26/30) |

## Foto por foto
### agaricus-sylvicola-1.jpg → ficha «agaricus-sylvicola»
Ficha dice: s_color=blanco/amarillo, p_anillo=si, p_base=ensanchada, p_color=blanco/amarillo
- llama32_v1: s_color=blanco, s_super=lisa, s_forma=convexo → no_candidata
- llama32_v2: s_color=blanco, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → descartada · no encajan: p_anillo=no (ficha: si); p_base=normal (ficha: ensanchada)
- scout_v2: s_color=blanco, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=si, p_base=normal, p_super=lisa, p_color=blanco → puesto 85 · no encajan: p_base=normal (ficha: ensanchada)
- gemma4_v2: s_color=blanco, s_super=escamas, s_forma=convexo, p_anillo=si, p_super=lisa, p_color=blanco → puesto 1

### aleuria-aurantia-1.jpg → ficha «aleuria-aurantia»
Ficha dice: s_color=naranja, h_tipo=liso
- llama32_v1: s_color=naranja, s_super=lisa, s_forma=convexo → no_candidata
- llama32_v2: s_color=naranja, s_super=lisa, s_forma=convexo → no_candidata
- scout_v2: s_color=naranja, s_super=lisa, s_forma=convexo, h_tipo=liso → descartada
- gemma4_v2: s_color=naranja, s_super=lisa, s_forma=embudo, h_tipo=poros, h_color=naranja → descartada · no encajan: h_tipo=poros (ficha: liso)

### amanita-echinocephala-1.jpg → ficha «amanita-echinocephala»
Ficha dice: s_color=blanco/gris, s_super=escamas, h_tipo=laminas, h_color=blanco, p_anillo=si, p_color=blanco, p_base=ensanchada
- llama32_v1: s_color=blanco, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco → puesto 13
- llama32_v2: s_color=blanco, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → puesto 8 · no encajan: p_anillo=no (ficha: si); p_base=normal (ficha: ensanchada)
- scout_v2: s_color=blanco, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=ensanchada, p_super=lisa, p_color=blanco → puesto 1 · no encajan: p_anillo=no (ficha: si)
- gemma4_v2: s_color=blanco, s_super=escamas, s_forma=convexo, p_anillo=no, p_base=normal, p_super=puntos, p_color=blanco → descartada · no encajan: p_anillo=no (ficha: si); p_base=normal (ficha: ensanchada)

### camperol-1.jpg → ficha «camperol»
Ficha dice: s_color=blanco, s_super=lisa/escamas, s_forma=convexo, h_tipo=laminas, h_color=rosa/pardo, p_anillo=si
- llama32_v1: s_color=blanco, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco → descartada · no encajan: h_color=blanco (ficha: rosa/pardo)
- llama32_v2: s_color=blanco, s_super=lisa, s_forma=convexo, h_tipo=poros, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → descartada · no encajan: h_tipo=poros (ficha: laminas); h_color=blanco (ficha: rosa/pardo); p_anillo=no (ficha: si)
- scout_v2: s_color=blanco, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → descartada · no encajan: h_color=blanco (ficha: rosa/pardo); p_anillo=no (ficha: si)
- gemma4_v2: s_color=blanco, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → descartada · no encajan: h_color=blanco (ficha: rosa/pardo); p_anillo=no (ficha: si)

### chlorophyllum-rhacodes-1.jpg → ficha «chlorophyllum-rhacodes»
Ficha dice: s_color=blanco/pardo, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_base=ensanchada
- llama32_v1: s_color=blanco, s_super=escamas, s_forma=convexo → descartada
- llama32_v2: s_color=blanco, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → puesto 12 · no encajan: p_base=normal (ficha: ensanchada)
- scout_v2: s_color=blanco, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → puesto 12 · no encajan: p_base=normal (ficha: ensanchada)
- gemma4_v2: s_color=blanco, s_super=escamas, s_forma=convexo, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → descartada · no encajan: p_base=normal (ficha: ensanchada)

### colmenilles-2.jpg → ficha «colmenilles»
Ficha dice: s_forma=alveolado
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=pardo → no_candidata · no encajan: s_forma=convexo (ficha: alveolado)
- llama32_v2: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → no_candidata · no encajan: s_forma=convexo (ficha: alveolado)
- scout_v2: s_color=pardo, s_forma=cerebro, h_tipo=liso, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → no_candidata · no encajan: s_forma=cerebro (ficha: alveolado)
- gemma4_v2: s_color=pardo, s_super=escamas, s_forma=conico, h_tipo=pliegues, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → no_candidata · no encajan: s_forma=conico (ficha: alveolado)

### cortinarius-cinnamomeus-1.jpg → ficha «cortinarius-cinnamomeus»
Ficha dice: s_color=amarillo/pardo, s_super=fibrosa, s_forma=convexo, h_tipo=laminas, h_color=amarillo/pardo, p_color=amarillo
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=liso, h_color=pardo → descartada · no encajan: s_super=lisa (ficha: fibrosa); h_tipo=liso (ficha: laminas)
- llama32_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → puesto 50 · no encajan: s_super=lisa (ficha: fibrosa); p_color=pardo (ficha: amarillo)
- scout_v2: s_color=pardo, s_super=lisa, s_forma=convexo → descartada · no encajan: s_super=lisa (ficha: fibrosa)
- gemma4_v2: s_color=pardo, s_super=lisa, s_forma=convexo, p_anillo=no, p_base=normal, p_super=puntos, p_color=pardo → descartada · no encajan: s_super=lisa (ficha: fibrosa); p_color=pardo (ficha: amarillo)

### cortinarius-infractus-1.jpg → ficha «cortinarius-infractus»
Ficha dice: s_color=verde/amarillo/pardo, s_super=viscosa, s_forma=convexo, h_tipo=laminas, h_color=verde/pardo, p_color=blanco, p_base=ensanchada
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=liso, h_color=pardo → descartada · no encajan: s_super=lisa (ficha: viscosa); h_tipo=liso (ficha: laminas)
- llama32_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → descartada · no encajan: s_super=lisa (ficha: viscosa); p_base=normal (ficha: ensanchada); p_color=pardo (ficha: blanco)
- scout_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas → descartada · no encajan: s_super=lisa (ficha: viscosa)
- gemma4_v2: s_color=pardo, s_super=lisa, s_forma=convexo → descartada · no encajan: s_super=lisa (ficha: viscosa)

### daedaleopsis-confragosa-1.jpg → ficha «daedaleopsis-confragosa»
Ficha dice: s_color=pardo/rojo/gris, h_tipo=poros, h_color=blanco/pardo
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=liso, h_color=pardo → descartada · no encajan: h_tipo=liso (ficha: poros)
- llama32_v2: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=poros, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → puesto 23
- scout_v2: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=poros, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa → puesto 20
- gemma4_v2: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=poros, h_color=blanco → puesto 21

### hygrocybe-conica-1.jpg → ficha «hygrocybe-conica»
Ficha dice: s_color=amarillo/naranja/rojo, s_super=lisa, s_forma=conico, h_tipo=laminas, h_color=blanco/amarillo/gris, p_anillo=no, p_color=amarillo/naranja/rojo
- llama32_v1: s_color=rojo, s_super=lisa, s_forma=convexo → descartada · no encajan: s_forma=convexo (ficha: conico)
- llama32_v2: s_color=rojo, s_super=viscosa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=amarillo → descartada · no encajan: s_super=viscosa (ficha: lisa); s_forma=convexo (ficha: conico)
- scout_v2: s_color=rojo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=amarillo, p_anillo=no, p_base=normal, p_super=lisa, p_color=amarillo → descartada · no encajan: s_forma=convexo (ficha: conico)
- gemma4_v2: s_color=rojo, s_super=lisa, s_forma=conico, h_tipo=laminas, p_anillo=no, p_base=normal, p_super=lisa, p_color=naranja → puesto 1

### hypholoma-1.jpg → ficha «hypholoma»
Ficha dice: s_color=amarillo/naranja/pardo, s_super=lisa, h_tipo=laminas, h_color=amarillo/verde, p_color=amarillo/naranja/pardo
- llama32_v1: s_color=amarillo, s_super=lisa, s_forma=convexo, h_tipo=liso, h_color=amarillo → descartada · no encajan: h_tipo=liso (ficha: laminas)
- llama32_v2: s_color=amarillo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=amarillo → descartada · no encajan: h_color=pardo (ficha: amarillo/verde)
- scout_v2: s_color=pardo, s_forma=convexo, h_tipo=laminas, p_anillo=no, p_base=normal, p_super=lisa, p_color=amarillo → descartada
- gemma4_v2: s_color=amarillo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=amarillo, p_anillo=no, p_base=normal, p_super=lisa, p_color=amarillo → puesto 43

### inocybe-lacera-1.jpg → ficha «inocybe-lacera»
Ficha dice: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco/pardo, p_anillo=no, p_color=pardo
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=liso, h_color=pardo → descartada · no encajan: s_super=lisa (ficha: escamas); h_tipo=liso (ficha: laminas)
- llama32_v2: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → puesto 5
- scout_v2: s_color=pardo, s_super=fibrosa, s_forma=convexo, h_tipo=laminas → descartada · no encajan: s_super=fibrosa (ficha: escamas)
- gemma4_v2: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=poros, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → descartada · no encajan: h_tipo=poros (ficha: laminas)

### inocybe-rimosa-1.jpg → ficha «inocybe-rimosa»
Ficha dice: s_color=pardo, s_super=fibrosa, s_forma=conico, h_tipo=laminas, h_color=gris/pardo, p_color=blanco
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=pardo → puesto 21 · no encajan: s_super=lisa (ficha: fibrosa); s_forma=convexo (ficha: conico)
- llama32_v2: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → puesto 72 · no encajan: s_super=escamas (ficha: fibrosa); s_forma=convexo (ficha: conico); h_color=blanco (ficha: gris/pardo)
- scout_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=ensanchada, p_super=lisa, p_color=blanco → puesto 79 · no encajan: s_super=lisa (ficha: fibrosa); s_forma=convexo (ficha: conico); h_color=blanco (ficha: gris/pardo)
- gemma4_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → puesto 74 · no encajan: s_super=lisa (ficha: fibrosa); s_forma=convexo (ficha: conico); h_color=blanco (ficha: gris/pardo)

### lactarius-camphoratus-1.jpg → ficha «lactarius-camphoratus»
Ficha dice: s_color=naranja/pardo/rojo, s_forma=convexo, h_tipo=laminas
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=pardo → puesto 44
- llama32_v2: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → puesto 66
- scout_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → puesto 66
- gemma4_v2: s_color=pardo, s_super=lisa, s_forma=embudo, h_tipo=laminas, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → descartada · no encajan: s_forma=embudo (ficha: convexo)

### lactarius-salmonicolor-1.jpg → ficha «lactarius-salmonicolor»
Ficha dice: s_color=naranja/rojo, s_super=viscosa, s_forma=convexo/embudo, h_tipo=laminas, h_color=naranja
- llama32_v1: s_color=naranja, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=naranja → puesto 1 · no encajan: s_super=lisa (ficha: viscosa)
- llama32_v2: s_color=naranja, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=naranja, p_anillo=no, p_base=normal, p_super=lisa, p_color=naranja → puesto 3 · no encajan: s_super=escamas (ficha: viscosa)
- scout_v2: s_color=naranja, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=naranja, p_anillo=no, p_base=ensanchada, p_super=lisa, p_color=naranja → puesto 4 · no encajan: s_super=lisa (ficha: viscosa)
- gemma4_v2: s_color=naranja, s_super=lisa, s_forma=convexo, h_tipo=pliegues, h_color=naranja, p_anillo=no, p_base=normal, p_super=lisa, p_color=naranja → descartada · no encajan: s_super=lisa (ficha: viscosa); h_tipo=pliegues (ficha: laminas)

### lactarius-zonarius-1.jpg → ficha «lactarius-zonarius»
Ficha dice: s_color=amarillo/naranja/blanco, h_tipo=laminas
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco → descartada · no encajan: s_color=pardo (ficha: amarillo/naranja/blanco)
- llama32_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → descartada · no encajan: s_color=pardo (ficha: amarillo/naranja/blanco)
- scout_v2: s_color=blanco, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → descartada
- gemma4_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_super=lisa, p_color=blanco → descartada · no encajan: s_color=pardo (ficha: amarillo/naranja/blanco)

### lepiota-clypeolaria-1.jpg → ficha «lepiota-clypeolaria»
Ficha dice: s_color=pardo/amarillo, s_super=escamas, s_forma=conico/convexo, h_tipo=laminas, h_color=blanco, p_anillo=si, p_color=blanco
- llama32_v1: s_color=blanco, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco → descartada · no encajan: s_color=blanco (ficha: pardo/amarillo); s_super=lisa (ficha: escamas)
- llama32_v2: s_color=blanco, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → descartada · no encajan: s_color=blanco (ficha: pardo/amarillo); s_super=lisa (ficha: escamas); p_anillo=no (ficha: si)
- scout_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → puesto 66 · no encajan: s_super=lisa (ficha: escamas); p_anillo=no (ficha: si)
- gemma4_v2: s_color=blanco, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=puntos, p_color=blanco → puesto 44 · no encajan: s_color=blanco (ficha: pardo/amarillo); p_anillo=no (ficha: si)

### llenega-1.jpg → ficha «llenega»
Ficha dice: s_color=gris/pardo, s_super=viscosa, h_tipo=laminas, h_color=blanco, p_color=blanco
- llama32_v1: s_color=pardo, s_super=viscosa, s_forma=convexo, h_tipo=liso, h_color=pardo → descartada · no encajan: h_tipo=liso (ficha: laminas); h_color=pardo (ficha: blanco)
- llama32_v2: s_color=pardo, s_super=viscosa, s_forma=convexo, h_tipo=laminas, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → puesto 59 · no encajan: h_color=pardo (ficha: blanco); p_color=pardo (ficha: blanco)
- scout_v2: s_color=pardo, s_super=viscosa, s_forma=convexo, h_tipo=laminas → puesto 26
- gemma4_v2: s_color=pardo, s_super=viscosa, s_forma=convexo, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → descartada

### macrolepiota-excoriata-1.jpg → ficha «macrolepiota-excoriata»
Ficha dice: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=si, p_base=ensanchada, p_color=blanco
- llama32_v1: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco → descartada
- llama32_v2: s_color=blanco, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → descartada · no encajan: s_color=blanco (ficha: pardo); p_anillo=no (ficha: si); p_base=normal (ficha: ensanchada); p_color=pardo (ficha: blanco)
- scout_v2: s_color=blanco, s_super=escamas, s_forma=convexo, p_base=normal, p_color=pardo → descartada · no encajan: s_color=blanco (ficha: pardo); p_base=normal (ficha: ensanchada); p_color=pardo (ficha: blanco)
- gemma4_v2: s_color=pardo, s_super=escamas, s_forma=convexo, p_base=normal, p_super=lisa, p_color=pardo → descartada · no encajan: p_base=normal (ficha: ensanchada); p_color=pardo (ficha: blanco)

### molleric-1.jpg → ficha «molleric»
Ficha dice: s_color=pardo/naranja/amarillo/verde, s_super=viscosa, h_tipo=poros, h_color=amarillo/verde, p_super=puntos
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=liso, h_color=pardo → descartada · no encajan: s_super=lisa (ficha: viscosa); h_tipo=liso (ficha: poros); h_color=pardo (ficha: amarillo/verde)
- llama32_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=poros, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → descartada · no encajan: s_super=lisa (ficha: viscosa); h_color=pardo (ficha: amarillo/verde); p_super=lisa (ficha: puntos)
- scout_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=amarillo, p_anillo=no, p_base=ensanchada, p_super=lisa, p_color=blanco → descartada · no encajan: s_super=lisa (ficha: viscosa); h_tipo=laminas (ficha: poros); p_super=lisa (ficha: puntos)
- gemma4_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=poros, h_color=amarillo, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → descartada · no encajan: s_super=lisa (ficha: viscosa); p_super=lisa (ficha: puntos)

### pardinum-1.jpg → ficha «pardinum»
Ficha dice: s_color=gris, s_super=escamas
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=pardo → descartada · no encajan: s_color=pardo (ficha: gris); s_super=lisa (ficha: escamas)
- llama32_v2: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → descartada · no encajan: s_color=pardo (ficha: gris)
- scout_v2: s_color=pardo, s_super=fibrosa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → descartada · no encajan: s_color=pardo (ficha: gris); s_super=fibrosa (ficha: escamas)
- gemma4_v2: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → descartada · no encajan: s_color=pardo (ficha: gris)

### phaeolepiota-aurea-1.jpg → ficha «phaeolepiota-aurea»
Ficha dice: s_color=amarillo/naranja, s_super=escamas, h_tipo=laminas, p_anillo=si
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=liso, h_color=pardo → descartada · no encajan: s_color=pardo (ficha: amarillo/naranja); s_super=lisa (ficha: escamas); h_tipo=liso (ficha: laminas)
- llama32_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → descartada · no encajan: s_color=pardo (ficha: amarillo/naranja); s_super=lisa (ficha: escamas); p_anillo=no (ficha: si)
- scout_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → descartada · no encajan: s_color=pardo (ficha: amarillo/naranja); s_super=lisa (ficha: escamas); p_anillo=no (ficha: si)
- gemma4_v2: s_color=naranja, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=naranja, p_anillo=si, p_base=normal, p_color=naranja → puesto 1 · no encajan: s_super=lisa (ficha: escamas)

### phylloporus-rhodoxanthus-1.jpg → ficha «phylloporus-rhodoxanthus»
Ficha dice: s_color=rojo/pardo/verde, s_forma=convexo, h_tipo=laminas, h_color=amarillo, p_color=amarillo
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=amarillo → puesto 9
- llama32_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=amarillo, p_anillo=no, p_base=normal, p_super=lisa, p_color=amarillo → puesto 6
- scout_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=amarillo, p_anillo=no, p_base=normal, p_super=lisa, p_color=amarillo → puesto 6
- gemma4_v2: s_color=naranja, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=amarillo, p_anillo=no, p_base=normal, p_super=lisa, p_color=naranja → puesto 37 · no encajan: s_color=naranja (ficha: rojo/pardo/verde); p_color=naranja (ficha: amarillo)

### pycnoporus-cinnabarinus-1.jpg → ficha «pycnoporus-cinnabarinus»
Ficha dice: s_color=naranja/rojo, h_tipo=poros
- llama32_v1: s_color=naranja, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=naranja → descartada · no encajan: h_tipo=laminas (ficha: poros)
- llama32_v2: s_color=naranja, s_super=escamas, s_forma=convexo, h_tipo=poros, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → descartada
- scout_v2: s_color=naranja, s_super=escamas, s_forma=cerebro → no_candidata
- gemma4_v2: s_color=naranja, s_super=escamas, s_forma=convexo → no_candidata

### ramaria-formosa-1.jpg → ficha «ramaria-formosa»
Ficha dice: s_color=rosa/naranja/amarillo, h_tipo=liso, p_color=blanco
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=liso, h_color=blanco → descartada · no encajan: s_color=pardo (ficha: rosa/naranja/amarillo)
- llama32_v2: s_color=amarillo, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → descartada · no encajan: h_tipo=laminas (ficha: liso); p_color=pardo (ficha: blanco)
- scout_v2: (ningún rasgo) → pocos_rasgos
- gemma4_v2: h_color=amarillo, p_color=amarillo → pocos_rasgos · no encajan: p_color=amarillo (ficha: blanco)

### rossinyols-1.jpg → ficha «rossinyols»
Ficha dice: s_color=amarillo, h_tipo=pliegues, p_color=amarillo
- llama32_v1: s_color=amarillo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=amarillo → descartada · no encajan: h_tipo=laminas (ficha: pliegues)
- llama32_v2: s_color=amarillo, s_super=escamas, s_forma=alveolado, h_tipo=laminas, h_color=amarillo, p_anillo=no, p_base=normal, p_super=lisa, p_color=amarillo → descartada · no encajan: h_tipo=laminas (ficha: pliegues)
- scout_v2: s_color=amarillo, s_super=lisa, s_forma=embudo, h_tipo=laminas, h_color=amarillo, p_anillo=no, p_base=normal, p_super=lisa, p_color=amarillo → descartada · no encajan: h_tipo=laminas (ficha: pliegues)
- gemma4_v2: s_color=amarillo, s_super=lisa, s_forma=embudo, h_tipo=pliegues, h_color=amarillo, p_anillo=no, p_base=normal, p_super=lisa, p_color=amarillo → puesto 2

### russula-mustelina-1.jpg → ficha «russula-mustelina»
Ficha dice: s_color=amarillo/pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco/amarillo, p_color=blanco
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=amarillo → puesto 3
- llama32_v2: s_color=blanco, s_super=lisa, s_forma=convexo → descartada · no encajan: s_color=blanco (ficha: amarillo/pardo)
- scout_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, p_super=lisa, p_color=blanco → puesto 3
- gemma4_v2: s_color=amarillo, s_super=lisa, s_forma=convexo, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → descartada

### russula-ochroleuca-1.jpg → ficha «russula-ochroleuca»
Ficha dice: s_color=amarillo, s_forma=convexo, h_tipo=laminas, h_color=blanco/gris, p_color=blanco/gris
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco → puesto 55 · no encajan: s_color=pardo (ficha: amarillo)
- llama32_v2: s_color=blanco, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → puesto 28 · no encajan: s_color=blanco (ficha: amarillo)
- scout_v2: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=ensanchada, p_super=lisa, p_color=blanco → puesto 44 · no encajan: s_color=pardo (ficha: amarillo)
- gemma4_v2: s_color=amarillo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=ensanchada, p_super=lisa, p_color=blanco → puesto 10

### russula-xerampelina-1.jpg → ficha «russula-xerampelina»
Ficha dice: s_color=violeta/rojo/verde, s_super=viscosa, s_forma=convexo, h_tipo=laminas, h_color=blanco/amarillo, p_color=blanco/rojo
- llama32_v1: s_color=rojo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=rojo → puesto 11 · no encajan: s_super=lisa (ficha: viscosa); h_color=rojo (ficha: blanco/amarillo)
- llama32_v2: s_color=rojo, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → puesto 5 · no encajan: s_super=escamas (ficha: viscosa)
- scout_v2: s_color=rojo, s_super=lisa, s_forma=convexo, h_tipo=laminas, h_color=blanco, p_anillo=no, p_base=normal, p_super=lisa, p_color=blanco → puesto 5 · no encajan: s_super=lisa (ficha: viscosa)
- gemma4_v2: s_color=rojo, s_super=lisa, s_forma=convexo, h_tipo=poros, h_color=blanco, p_anillo=no, p_base=normal, p_super=puntos, p_color=blanco → descartada · no encajan: s_super=lisa (ficha: viscosa); h_tipo=poros (ficha: laminas)

### trompetes-1.jpg → ficha «trompetes»
Ficha dice: s_forma=embudo, s_color=gris/negro, h_tipo=liso, h_color=gris
- llama32_v1: s_color=pardo, s_super=lisa, s_forma=convexo, h_tipo=liso, h_color=pardo → descartada · no encajan: s_color=pardo (ficha: gris/negro); s_forma=convexo (ficha: embudo); h_color=pardo (ficha: gris)
- llama32_v2: s_color=pardo, s_super=escamas, s_forma=convexo, h_tipo=laminas, h_color=pardo, p_anillo=no, p_base=normal, p_super=lisa, p_color=pardo → descartada · no encajan: s_color=pardo (ficha: gris/negro); s_forma=convexo (ficha: embudo); h_tipo=laminas (ficha: liso); h_color=pardo (ficha: gris)
- scout_v2: (ningún rasgo) → pocos_rasgos
- gemma4_v2: s_color=gris, s_forma=embudo, h_tipo=liso, h_color=gris, p_anillo=no, p_base=normal, p_super=lisa, p_color=gris → puesto 1

Neuronas gastadas en esta ejecución: 3325 de 6000 de presupuesto.
