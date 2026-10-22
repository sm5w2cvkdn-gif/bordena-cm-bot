"""Renderiza una historia de Instagram (1080x1920) con el estilo de Bordena Studio:
azul marino y crema, títulos en Cinzel, texto en Roboto, arco y ola griega (Santorini).

Uso:
    python render.py historias/2026-10-13.json            -> historias/2026-10-13.jpg
    python render.py historias/2026-10-13.json salida.jpg

Diseños (campo "diseno"; ver README.md para los campos de cada uno):
    foto     foto de fondo con velo azul, texto a la izquierda y caja con borde fino
    marco    fondo crema con marco azul fino, todo centrado, tarjeta azul opcional
    lista    fondo blanco, opciones numeradas separadas por líneas
    arco     fondo crema, arco mediterráneo azul con el contenido adentro
    navy     fondo azul marino entero, texto crema, ola griega
    ventana  foto (o ola griega) dentro de un arco arriba, texto centrado abajo

Si el texto no entra, el script termina con error: acortá el texto o cambiá de diseño.
"""

import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 1080, 1920
RAIZ = Path(__file__).resolve().parent
FUENTES = RAIZ / "fuentes"
MARCA = RAIZ / "marca"

NAVY = (21, 51, 94)
NAVY_HONDO = (14, 36, 70)
CREMA = (245, 240, 232)
BLANCO = (255, 255, 255)
BLANCO_CALIDO = (250, 247, 241)
TEXTO = (38, 38, 40)
GRIS_AZUL = (96, 106, 122)
SECUNDARIO = (70, 82, 100)

DISENOS = ("foto", "marco", "lista", "arco", "navy", "ventana")


# ---------------------------------------------------------------- tipografía

def cinzel(tam, peso=500):
    f = ImageFont.truetype(str(FUENTES / "Cinzel.ttf"), int(tam))
    f.set_variation_by_axes([peso])
    return f


def roboto(tam, peso=400):
    f = ImageFont.truetype(str(FUENTES / "Roboto.ttf"), int(tam))
    f.set_variation_by_axes([peso, 100])
    return f


def espaciado(d, x, y, txt, f, color, esp, alinear="izq"):
    w = sum(d.textlength(ch, font=f) for ch in txt) + esp * (len(txt) - 1)
    if alinear == "centro":
        x -= w / 2
    for ch in txt:
        d.text((x, y), ch, font=f, fill=color)
        x += d.textlength(ch, font=f) + esp
    return w


def envolver(d, txt, f, max_w):
    lineas = []
    for parrafo in str(txt).split("\n"):
        actual = ""
        for palabra in parrafo.split():
            prueba = (actual + " " + palabra).strip()
            if d.textlength(prueba, font=f) <= max_w or not actual:
                actual = prueba
            else:
                lineas.append(actual)
                actual = palabra
        lineas.append(actual)
    return lineas


def titulo_a_medida(d, txt, max_w, tams, max_lineas=3, peso=500):
    """Elige el tamaño de título más grande que entra en `max_lineas`."""
    for t in tams:
        f = cinzel(t, peso)
        lineas = envolver(d, txt, f, max_w)
        if len(lineas) <= max_lineas and all(d.textlength(l, font=f) <= max_w for l in lineas):
            return f, lineas
    f = cinzel(tams[-1], peso)
    return f, envolver(d, txt, f, max_w)


def rico(d, txt, tam, max_w, color, peso=400):
    """Texto con **negritas**. Devuelve (alto, dibujar(x, y, alinear))."""
    f_n, f_b = roboto(tam, peso), roboto(tam, 600)
    tokens = []  # (palabra, negrita, pegada_a_la_anterior)
    trozos = re.split(r"\*\*", str(txt))
    for i, trozo in enumerate(trozos):
        pegar_primera = bool(trozo) and not trozo[0].isspace() and i > 0 and trozos[i - 1] and not trozos[i - 1][-1].isspace()
        for j, palabra in enumerate(trozo.split()):
            tokens.append((palabra, i % 2 == 1, pegar_primera and j == 0))
    lineas, actual, ancho = [], [], 0
    esp = d.textlength(" ", font=f_n)
    for palabra, neg, pegada in tokens:
        w = d.textlength(palabra, font=f_b if neg else f_n)
        sep = 0 if pegada else esp
        if actual and not pegada and ancho + sep + w > max_w:
            lineas.append((actual, ancho))
            actual, ancho = [], 0
            sep = 0
        ancho += (sep if actual else 0) + w
        actual.append((palabra, neg, w, sep))
    if actual:
        lineas.append((actual, ancho))
    inter = tam * 1.42

    def dibujar(x, y, alinear="izq"):
        for palabras, ancho_l in lineas:
            px = x - ancho_l / 2 if alinear == "centro" else x
            for k, (palabra, neg, w, sep) in enumerate(palabras):
                if k:
                    px += sep
                d.text((px, y), palabra, font=f_b if neg else f_n, fill=color)
                px += w
            y += inter
    return len(lineas) * inter, dibujar


# ---------------------------------------------------------------- piezas gráficas

def ola_griega(d, x0, x1, y, alto, color):
    """Guarda de ola griega (como la de la tarjeta de membresía)."""
    paso = alto * 1.25
    grosor = max(3, int(alto * 0.16))
    n = int((x1 - x0) // paso)
    x = x0 + ((x1 - x0) - n * paso) / 2
    base = y + alto
    for _ in range(n):
        cx, cy = x + paso * 0.55, y + alto * 0.45
        r0 = alto * 0.42
        pts = [(x, base - grosor / 2), (x + paso * 0.18, base - grosor / 2)]
        for i in range(0, 61):
            t = i / 60
            ang = math.radians(90 + 330 * t) * -1 + math.pi
            r = r0 * (1 - 0.62 * t)
            pts.append((cx + math.cos(ang) * r * 1.05, cy + math.sin(ang) * r))
        d.line(pts, fill=color, width=grosor, joint="curve")
        d.line([(x, base - grosor / 2), (x + paso, base - grosor / 2)], fill=color, width=grosor)
        x += paso


def logo(img, cx, cy, color):
    """Logo oficial si existe marca/logo-<color>.png; si no, logotipo en texto."""
    nombre = "logo-blanco.png" if color != NAVY else "logo-navy.png"
    archivo = MARCA / nombre
    if archivo.exists():
        lg = Image.open(archivo).convert("RGBA")
        lg.thumbnail((360, 110))
        img.paste(lg, (int(cx - lg.width / 2), int(cy - lg.height / 2)), lg)
        return
    d = ImageDraw.Draw(img)
    f = cinzel(44, 500)
    w1 = sum(d.textlength(c, font=f) for c in "BORDENA") + 10 * 6
    x = cx - w1 / 2
    espaciado(d, x, cy - 50, "BORDENA", f, color, 10)
    espaciado(d, x, cy + 2, "STUDIO", f, color, 10 + (w1 - (sum(d.textlength(c, font=f) for c in "STUDIO") + 60)) / 5)


def foto_cubriendo(ruta, caja):
    x0, y0, x1, y1 = caja
    im = Image.open(RAIZ / ruta)
    im = ImageOps.exif_transpose(im).convert("RGB")
    return ImageOps.fit(im, (int(x1 - x0), int(y1 - y0)), Image.LANCZOS, centering=(0.5, 0.45))


def velo(img, arriba, abajo, color=NAVY_HONDO):
    """Velo azul en degradé (más denso arriba, donde va el texto)."""
    a = Image.new("L", (1, H))
    for y in range(H):
        t = y / (H - 1)
        a.putpixel((0, y), int(arriba + (abajo - arriba) * t))
    capa = Image.new("RGBA", (W, H), color + (0,))
    capa.putalpha(a.resize((W, H)))
    img.paste(capa, (0, 0), capa)


def mascara_arco(caja):
    x0, y0, x1, y1 = caja
    r = (x1 - x0) / 2
    m = Image.new("L", (W, H), 0)
    dm = ImageDraw.Draw(m)
    dm.pieslice([x0, y0, x1, y0 + 2 * r], 180, 360, fill=255)
    dm.rectangle([x0, y0 + r, x1, y1], fill=255)
    return m


def contorno_arco(d, caja, color, ancho=3):
    x0, y0, x1, y1 = caja
    r = (x1 - x0) / 2
    d.arc([x0, y0, x1, y0 + 2 * r], 180, 360, fill=color, width=ancho)
    for xx in (x0, x1):
        d.line([(xx, y0 + r), (xx, y1)], fill=color, width=ancho)
    d.line([(x0, y1), (x1, y1)], fill=color, width=ancho)


def sombra(img, caja, radio=0, desplaz=18, blur=26, alfa=70):
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x0, y0, x1, y1 = caja
    ImageDraw.Draw(capa).rounded_rectangle([x0, y0 + desplaz, x1, y1 + desplaz], radius=radio, fill=(20, 30, 50, alfa))
    capa = capa.filter(ImageFilter.GaussianBlur(blur))
    img.paste(capa, (0, 0), capa)


# ---------------------------------------------------------------- pila vertical de contenido

class Pila:
    """Acumula bloques (alto, dibujar(y)) y los ubica dentro de un rango vertical."""

    def __init__(self):
        self.bloques = []

    def agregar(self, alto, dibujar, despues=40):
        self.bloques.append((alto, dibujar, despues))

    def alto(self):
        if not self.bloques:
            return 0
        return sum(a + e for a, _, e in self.bloques) - self.bloques[-1][2]

    def dibujar(self, y0, y1, vertical="centro"):
        total = self.alto()
        if total > y1 - y0 + 1:
            raise SystemExit(
                f"ERROR: el contenido no entra ({int(total)}px > {int(y1 - y0)}px). "
                "Acortá el texto o elegí otro diseño."
            )
        y = y0 + (y1 - y0 - total) / 2 if vertical == "centro" else y0
        for a, dib, e in self.bloques:
            dib(y)
            y += a + e
        return total, y1 - y0


def bloque_etiqueta(p, d, x, txt, color, alinear="izq", tam=32, esp=11, despues=22):
    f = roboto(tam, 500)
    txt = txt.upper()
    p.agregar(tam * 1.05, lambda y: espaciado(d, x, y, txt, f, color, esp, alinear), despues)


def bloque_titulo(p, d, x, txt, color, max_w, tams, alinear="izq", max_lineas=3, despues=50):
    f, lineas = titulo_a_medida(d, txt, max_w, tams, max_lineas)
    inter = f.size * 1.02

    def dib(y):
        for ln in lineas:
            d.text((x, y), ln, font=f, fill=color, anchor="ma" if alinear == "centro" else "la")
            y += inter
    p.agregar(len(lineas) * inter, dib, despues)


def bloque_texto(p, d, x, txt, color, max_w, tam=42, alinear="izq", peso=400, despues=36):
    alto, dib = rico(d, txt, tam, max_w, color, peso)
    p.agregar(alto - tam * 0.3, lambda y: dib(x, y, alinear), despues)


# ---------------------------------------------------------------- diseños

def d_foto(spec):
    """Como tu historia de 'Feliz lunes': foto + velo azul, texto a la izquierda."""
    if spec.get("foto"):
        img = foto_cubriendo(spec["foto"], (0, 0, W, H))
        velo(img, 215, 150)
    else:
        img = Image.new("RGB", (W, H), NAVY)
        velo(img, 0, 120, NAVY_HONDO)
    d = ImageDraw.Draw(img)
    x, mw = 80, W - 160
    arriba = Pila()
    if spec.get("etiqueta"):
        bloque_etiqueta(arriba, d, x, spec["etiqueta"], BLANCO_CALIDO, despues=40)
    if spec.get("titulo"):
        bloque_titulo(arriba, d, x, spec["titulo"], BLANCO_CALIDO, mw - 300, [150, 130, 112, 96], max_lineas=3, despues=70)
    if spec.get("texto"):
        bloque_texto(arriba, d, x, spec["texto"], BLANCO_CALIDO, mw, 40)
    arriba.dibujar(140, 900, vertical="arriba")

    caja = spec.get("caja")
    if caja:
        cx0, cx1 = 80, W - 80
        interior = Pila()
        ix, iw = cx0 + 52, cx1 - cx0 - 104
        if caja.get("etiqueta"):
            bloque_etiqueta(interior, d, ix, caja["etiqueta"], BLANCO_CALIDO, tam=30, esp=10, despues=26)
        if caja.get("titulo"):
            bloque_titulo(interior, d, ix, caja["titulo"], BLANCO_CALIDO, iw, [96, 84, 72], max_lineas=2, despues=44)
        if caja.get("texto"):
            bloque_texto(interior, d, ix, caja["texto"], BLANCO_CALIDO, iw, 36)
        alto = interior.alto() + 120
        y0 = 1010
        d.rectangle([cx0, y0, cx1, y0 + alto], outline=(235, 235, 240), width=2)
        interior.dibujar(y0 + 60, y0 + alto - 60)
    logo(img, W / 2, 1790, BLANCO_CALIDO)
    return img, (0, 0)


def d_marco(spec):
    """Como tu 'Día de la Madre / Gift card': crema, marco azul fino, centrado."""
    img = Image.new("RGB", (W, H), CREMA)
    d = ImageDraw.Draw(img)
    d.rectangle([50, 50, W - 50, H - 50], outline=NAVY, width=3)
    cx, mw = W / 2, W - 220
    p = Pila()
    if spec.get("etiqueta"):
        bloque_etiqueta(p, d, cx, spec["etiqueta"], NAVY, "centro", despues=30)
    if spec.get("titulo"):
        bloque_titulo(p, d, cx, spec["titulo"], NAVY, mw, [120, 108, 96, 84], "centro", despues=110)
    tarjeta = spec.get("caja")
    if tarjeta:
        alto_t = 420

        def dib_tarjeta(y):
            caja = (130, y, W - 130, y + alto_t)
            sombra(img, caja)
            d.rectangle(caja, fill=NAVY)
            d.rectangle([148, y + 18, W - 148, y + alto_t - 18], outline=(150, 165, 190), width=2)
            interior = Pila()
            if tarjeta.get("etiqueta"):
                bloque_etiqueta(interior, d, cx, tarjeta["etiqueta"], BLANCO_CALIDO, "centro", tam=30, esp=12, despues=30)
            if tarjeta.get("titulo"):
                bloque_titulo(interior, d, cx, tarjeta["titulo"], BLANCO_CALIDO, W - 380, [100, 88, 76, 64], "centro", 2, despues=24)
            if tarjeta.get("texto"):
                bloque_texto(interior, d, cx, tarjeta["texto"], (220, 226, 236), W - 380, 32, "centro")
            interior.dibujar(y + 40, y + alto_t - 40)
        p.agregar(alto_t + 20, dib_tarjeta, 110)
    if spec.get("texto"):
        bloque_texto(p, d, cx, spec["texto"], NAVY, mw - 40, 42, "centro", despues=40)
    if spec.get("texto_secundario"):
        bloque_texto(p, d, cx, spec["texto_secundario"], SECUNDARIO, mw, 38, "centro")
    p.dibujar(160, 1620)
    logo(img, cx, 1790, NAVY)
    return img, None


def d_lista(spec):
    """Como tu 'Regalos para mamá': blanco, opciones numeradas con líneas."""
    img = Image.new("RGB", (W, H), BLANCO)
    d = ImageDraw.Draw(img)
    x, x1 = 90, W - 90
    p = Pila()
    if spec.get("etiqueta"):
        bloque_etiqueta(p, d, x, spec["etiqueta"], NAVY, despues=34)
    if spec.get("titulo"):
        bloque_titulo(p, d, x, spec["titulo"], NAVY, x1 - x - 300, [96, 84, 76], max_lineas=2, despues=60)
    linea = lambda y: d.line([(x, y), (x1, y)], fill=NAVY, width=2)
    p.agregar(2, linea, 60)
    items = spec.get("items", [])[:4]
    for i, it in enumerate(items, 1):
        sub = Pila()
        tx, tw = 250, x1 - 250
        if it.get("etiqueta"):
            bloque_etiqueta(sub, d, tx, it["etiqueta"], GRIS_AZUL, tam=26, esp=9, despues=14)
        if it.get("titulo"):
            bloque_titulo(sub, d, tx, it["titulo"], NAVY, tw, [58, 52, 46], max_lineas=2, despues=26)
        if it.get("texto"):
            bloque_texto(sub, d, tx, it["texto"], TEXTO, tw, 36)
        alto = sub.alto()

        def dib(y, sub=sub, alto=alto, n=i):
            d.text((x, y - 6), str(n), font=cinzel(120, 500), fill=NAVY)
            sub.dibujar(y, y + alto, vertical="arriba")
        p.agregar(max(alto, 110), dib, 56)
        p.agregar(2, linea, 50)
    if spec.get("cierre"):
        bloque_texto(p, d, x, spec["cierre"], NAVY, x1 - x, 40)
    p.dibujar(130, 1650, vertical="arriba")
    logo(img, W / 2, 1790, NAVY)
    return img, None


def d_arco(spec):
    """Arco mediterráneo azul sobre crema, con ola griega en la base."""
    img = Image.new("RGB", (W, H), CREMA)
    d = ImageDraw.Draw(img)
    caja = (110, 170, W - 110, 1640)
    contorno_arco(d, caja, NAVY, 3)
    contorno_arco(d, (caja[0] + 18, caja[1] + 18, caja[2] - 18, caja[3] - 18), NAVY, 1)
    ola_griega(d, caja[0] + 40, caja[2] - 40, caja[3] - 110, 46, NAVY)
    cx, mw = W / 2, caja[2] - caja[0] - 140
    p = Pila()
    if spec.get("etiqueta"):
        bloque_etiqueta(p, d, cx, spec["etiqueta"], NAVY, "centro", tam=30, despues=30)
    if spec.get("titulo"):
        bloque_titulo(p, d, cx, spec["titulo"], NAVY, mw, [112, 100, 88, 76], "centro", despues=60)
    if spec.get("caja", {}).get("titulo"):
        c = spec["caja"]
        f = cinzel(64, 500)

        def dib(y):
            d.line([(cx - 60, y), (cx + 60, y)], fill=NAVY, width=2)
            if c.get("etiqueta"):
                espaciado(d, cx, y + 34, c["etiqueta"].upper(), roboto(26, 500), GRIS_AZUL, 9, "centro")
            d.text((cx, y + 80), c["titulo"], font=f, fill=NAVY, anchor="ma")
        p.agregar(170, dib, 50)
    if spec.get("texto"):
        bloque_texto(p, d, cx, spec["texto"], NAVY, mw, 40, "centro")
    if spec.get("texto_secundario"):
        bloque_texto(p, d, cx, spec["texto_secundario"], SECUNDARIO, mw, 34, "centro")
    p.dibujar(caja[1] + (caja[2] - caja[0]) / 2 * 0.45, caja[3] - 170)
    logo(img, W / 2, 1790, NAVY)
    return img, None


def d_navy(spec):
    """Fondo azul marino entero con marco crema, ola griega arriba y abajo."""
    img = Image.new("RGB", (W, H), NAVY)
    velo(img, 0, 90, NAVY_HONDO)
    d = ImageDraw.Draw(img)
    d.rectangle([50, 50, W - 50, H - 50], outline=(200, 200, 205), width=2)
    ola_griega(d, 110, W - 110, 120, 40, (205, 195, 175))
    ola_griega(d, 110, W - 110, 1620, 40, (205, 195, 175))
    cx, mw = W / 2, W - 240
    p = Pila()
    if spec.get("etiqueta"):
        bloque_etiqueta(p, d, cx, spec["etiqueta"], CREMA, "centro", despues=30)
    if spec.get("titulo"):
        bloque_titulo(p, d, cx, spec["titulo"], CREMA, mw, [130, 116, 100, 88], "centro", despues=70)
    if spec.get("caja"):
        c = spec["caja"]
        interior = Pila()
        if c.get("etiqueta"):
            bloque_etiqueta(interior, d, cx, c["etiqueta"], CREMA, "centro", tam=28, esp=10, despues=24)
        if c.get("titulo"):
            bloque_titulo(interior, d, cx, c["titulo"], CREMA, mw - 120, [88, 76, 64], "centro", 2, despues=30)
        if c.get("texto"):
            bloque_texto(interior, d, cx, c["texto"], CREMA, mw - 120, 34, "centro")
        alto = interior.alto() + 110

        def dib(y):
            d.rectangle([130, y, W - 130, y + alto], outline=(225, 225, 230), width=2)
            interior.dibujar(y + 55, y + alto - 55)
        p.agregar(alto, dib, 60)
    if spec.get("texto"):
        bloque_texto(p, d, cx, spec["texto"], CREMA, mw, 40, "centro")
    if spec.get("texto_secundario"):
        bloque_texto(p, d, cx, spec["texto_secundario"], (200, 205, 215), mw, 34, "centro")
    p.dibujar(260, 1560)
    logo(img, cx, 1790, BLANCO_CALIDO)
    return img, None


def d_ventana(spec):
    """Foto dentro de un arco arriba (o ola griega si no hay foto), texto abajo."""
    img = Image.new("RGB", (W, H), CREMA)
    d = ImageDraw.Draw(img)
    caja = (230, 130, W - 230, 900)
    if spec.get("foto"):
        sombra(img, caja, radio=300, desplaz=14, blur=22, alfa=55)
        img.paste(foto_cubriendo(spec["foto"], caja), (caja[0], caja[1]), mascara_arco(caja).crop(caja))
    else:
        relleno = Image.new("RGB", (W, H), NAVY)
        dr = ImageDraw.Draw(relleno)
        for i, yy in enumerate(range(caja[1] + 60, caja[3], 110)):
            ola_griega(dr, caja[0], caja[2], yy, 38, (60, 92, 136) if i % 2 else (44, 76, 120))
        img.paste(relleno, (0, 0), mascara_arco(caja))
    d = ImageDraw.Draw(img)
    contorno_arco(d, (caja[0] - 20, caja[1] - 20, caja[2] + 20, caja[3] + 20), NAVY, 2)
    cx, mw = W / 2, W - 200
    p = Pila()
    if spec.get("etiqueta"):
        bloque_etiqueta(p, d, cx, spec["etiqueta"], NAVY, "centro", tam=30, despues=26)
    if spec.get("titulo"):
        bloque_titulo(p, d, cx, spec["titulo"], NAVY, mw, [104, 92, 80, 70], "centro", max_lineas=2, despues=44)
    if spec.get("texto"):
        bloque_texto(p, d, cx, spec["texto"], NAVY, mw - 40, 38, "centro")
    if spec.get("texto_secundario"):
        bloque_texto(p, d, cx, spec["texto_secundario"], SECUNDARIO, mw, 32, "centro")
    p.dibujar(960, 1650)
    logo(img, cx, 1790, NAVY)
    return img, None


CONSTRUCTORES = {
    "foto": d_foto, "marco": d_marco, "lista": d_lista,
    "arco": d_arco, "navy": d_navy, "ventana": d_ventana,
}


def render(spec, salida):
    diseno = spec.get("diseno", "marco")
    if diseno not in CONSTRUCTORES:
        raise SystemExit(f"diseño desconocido: {diseno} (opciones: {', '.join(DISENOS)})")
    if spec.get("foto") and not (RAIZ / spec["foto"]).exists():
        raise SystemExit(f"no existe la foto {spec['foto']}")
    img, _ = CONSTRUCTORES[diseno](spec)
    guardar(img, salida)


def guardar(img, salida):
    """JPEG en la máxima calidad útil para historias de Instagram: 1080x1920 exactos,
    sin submuestreo de color (textos y líneas finas nítidas), perfil sRGB y < 8 MB."""
    img = img.convert("RGB")
    assert img.size == (W, H), f"tamaño inesperado {img.size}"
    extra = {}
    try:
        from PIL import ImageCms
        extra["icc_profile"] = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    except Exception:
        pass
    for calidad in (97, 95, 92, 90):
        img.save(salida, "JPEG", quality=calidad, subsampling=0, optimize=True, **extra)
        if Path(salida).stat().st_size < 8 * 1024 * 1024:
            return
    raise SystemExit("ERROR: la imagen supera 8 MB, el límite de Instagram para historias.")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    entrada = Path(sys.argv[1])
    salida = Path(sys.argv[2]) if len(sys.argv) > 2 else entrada.with_suffix(".jpg")
    render(json.loads(entrada.read_text(encoding="utf-8")), salida)
    print(f"OK {salida} ({salida.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
