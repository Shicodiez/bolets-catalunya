"""Reduce a 800 px (lado largo) las fotos propias de tools/banco/mis_fotos/, igual que hace la guía antes de mandarlas a la IA.

Las deja en tools/banco/mis_fotos_800/ (el banco de pruebas usa esa carpeta si existe). Lo lanza el workflow
«Probar lectura de fotos con IA»; necesita Pillow (pip install pillow).
"""
import os
import sys

from PIL import Image, ImageOps

ORIGEN, DESTINO = "tools/banco/mis_fotos", "tools/banco/mis_fotos_800"


def main():
    if not os.path.isdir(ORIGEN):
        print("No hay tools/banco/mis_fotos: nada que reducir.")
        return 0
    os.makedirs(DESTINO, exist_ok=True)
    n = 0
    for f in sorted(os.listdir(ORIGEN)):
        if not f.lower().endswith((".jpg", ".jpeg")):
            continue
        im = ImageOps.exif_transpose(Image.open(os.path.join(ORIGEN, f))).convert("RGB")
        im.thumbnail((800, 800))
        im.save(os.path.join(DESTINO, f), "JPEG", quality=82)
        print("reducida", f, im.size)
        n += 1
    print(n, "fotos reducidas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
