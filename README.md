# Predictor de bolets — Catalunya

## Què és cada carpeta

- `backend/recollir_dades.py` — el programa que consulta el temps (pluja,
  temperatura) i calcula la puntuació de cada bolet a cada zona. Cal
  executar-lo perquè les dades s'actualitzin.
- `data/resultats.json` — el resultat del càlcul. La web el llegeix.
- `web/index.html` — la pàgina que veuran els teus amics, amb el mapa/llista
  de zones i puntuacions.

## Com funciona (idea general)

1. El programa Python es connecta a Open-Meteo (temps) i calcula quina
   puntuació té cada bolet a cada zona.
2. Guarda el resultat en un fitxer.
3. La pàgina web llegeix aquest fitxer i el mostra de forma bonica.

Aquest procés (pas 1 i 2) s'ha d'executar de tant en tant (per exemple cada 6
hores) perquè les dades no quedin desactualitzades. Per això necessitem un
lloc "sempre encès" a internet en comptes del teu ordinador — es diu
"desplegar al núvol".

---

## Pas a pas per posar-ho en marxa (sense experiència tècnica)

Anirem fent-ho junts, aquest README és només de referència perquè ho tinguis
tot en un lloc. No cal que facis res d'això encara — quan arribem a aquesta
fase de la conversa, t'aniré dient exactament què clicar.

Resum del que farem:

1. Crear un compte gratuït a GitHub (per guardar el codi)
2. Pujar aquests fitxers a GitHub (t'ho automatitzo jo)
3. Crear un compte gratuït a un servei que executi el programa Python cada
   poques hores (per exemple Render.com)
4. Connectar-ho amb GitHub Pages (gratuït) perquè la web sigui accessible amb
   un enllaç que puguis enviar als teus amics
