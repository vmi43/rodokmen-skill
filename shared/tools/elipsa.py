#!/usr/bin/env python3
"""Dům na mapě označený elipsou s popiskem („čp. 183“) – do PDF a na web, kde čtenář dům na staré mapě nenajde sám.

Použití (z kořene projektu):
  elipsa.py <mapa.jpg> <klic> cx,cy,a,b[,uhel] [--popisek "čp. 183"] [--text x,y] [--pismo px]
      cx,cy = střed elipsy, a,b = poloosy (vodorovná, svislá) v pixelech obrázku <mapa.jpg>; uhel = natočení
      ve stupních po směru hodinových ručiček (dům šikmo k ose mapy). Rozměr obrázku vypíše nástroj, když chybí čísla.
      --text x,y = levý horní roh popisku (výchozí vpravo nad elipsou); popisek spojí s elipsou vodicí čára.
      --pismo = výška písma v px (výchozí 1/30 šířky obrázku).
      Uloží zdroje/<klic>.jpg (plné rozlišení) a vyrezy/<klic>.jpg (max. 1800 px pro web) jako vyrez.py.
Elipsa obepíná celou parcelu domu, ne jen číslo; výsledek si VŽDY prohlédni. Do data/mapy.json k mapě zapiš
do „poznamka“ příkaz s čísly, ať jde označení zopakovat (např. po exportu mapy ve větším rozlišení).
Potřebuje Pillow (python3 -m pip install pillow).

Původ: převzato z vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/elipsa.py), commit e1cd204; úprava: podmínky obrázku
hlásí stejně jako vyrez.py (`podminky.hlaska_obrazku`).
"""
import math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
import podminky

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CERVENA, BILA = (215, 0, 0, 255), (255, 255, 255, 210)
PISMA = ("DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "arialbd.ttf",
         "Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf")
WEB_PX = 1800


def pismo(velikost):
    from PIL import ImageFont
    for p in PISMA:
        try:
            return ImageFont.truetype(p, velikost)
        except OSError:
            pass
    return ImageFont.load_default(size=velikost)   # bez diakritiky na některých systémech – zkontroluj popisek


def bod_elipsy(cx, cy, a, b, uhel, s):
    u = math.radians(uhel)
    return (cx + a * math.cos(s) * math.cos(u) - b * math.sin(s) * math.sin(u),
            cy + a * math.cos(s) * math.sin(u) + b * math.sin(s) * math.cos(u))


def nejblizsi_bod(cx, cy, a, b, uhel, cil):
    """Bod na obvodu elipsy nejblíž cíli (konec vodicí čáry u elipsy)."""
    return min((bod_elipsy(cx, cy, a, b, uhel, i / 180 * math.pi) for i in range(360)),
               key=lambda p: (p[0] - cil[0]) ** 2 + (p[1] - cil[1]) ** 2)


def oznac(im, cx, cy, a, b, uhel=0.0, popisek="", text=None, velikost=None):
    """Nakreslí do obrázku (RGBA) elipsu s bílým lemem, popisek a vodicí čáru. Tloušťky podle šířky obrázku."""
    from PIL import Image, ImageDraw
    cara = max(3, round(im.width / 330))
    for barva, sirka in ((BILA, 2 * cara), (CERVENA, cara)):   # bílý lem pod červenou: čitelné na tmavé i barevné mapě
        w, h = int(2 * a + 4 * sirka), int(2 * b + 4 * sirka)
        vrstva = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(vrstva).ellipse([2 * sirka, 2 * sirka, w - 2 * sirka, h - 2 * sirka], outline=barva, width=sirka)
        vrstva = vrstva.rotate(-uhel, expand=True, resample=Image.BICUBIC)
        im.alpha_composite(vrstva, (int(cx - vrstva.width / 2), int(cy - vrstva.height / 2)))
    if not popisek:
        return im
    f = pismo(velikost or max(14, im.width // 30))
    if text is None:   # vpravo nad elipsou
        text = (cx + a + f.size, cy - b - f.size)
    d = ImageDraw.Draw(im)
    l, t, r, bt = d.textbbox(text, popisek, font=f)
    stred_textu = ((l + r) / 2, (t + bt) / 2)
    cil = (l - f.size / 6 if stred_textu[0] >= cx else r + f.size / 6, stred_textu[1])   # bok popisku blíž elipse
    zacatek = nejblizsi_bod(cx, cy, a, b, uhel, cil)
    d.line([zacatek, cil], fill=BILA, width=round(1.5 * cara))
    d.line([zacatek, cil], fill=CERVENA, width=max(2, round(cara * 2 / 3)))
    d.text(text, popisek, font=f, fill=CERVENA, stroke_width=max(2, f.size // 14), stroke_fill=(255, 255, 255))
    return im


def cisla(text, kolik, co):
    try:
        v = [float(x) for x in text.split(",")]
    except ValueError:
        v = []
    if len(v) not in kolik:
        sys.exit(f"{co}: „{text}“ – čekám {' nebo '.join(map(str, kolik))} čísel oddělených čárkou (pixely)")
    return v


def volba(a, nazev):
    if nazev not in a:
        return None
    i = a.index(nazev)
    if i + 1 >= len(a):
        sys.exit(f"{nazev}: chybí hodnota")
    hodnota = a[i + 1]
    del a[i:i + 2]
    return hodnota


def main(a):
    if len(a) < 2:
        sys.exit(__doc__)
    if not os.path.exists(os.path.join(ROOT, "data", "STAV.md")):   # ze složky skillu by zapisoval do skillu
        sys.exit(f"elipsa.py: {ROOT} není složka projektu (chybí data/STAV.md). "
                 "Spusť projektovou kopii z kořene projektu: python3 -I tools/elipsa.py …")
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Chybí Pillow: python3 -m pip install pillow")
    a = list(a)
    popisek, text, velikost = volba(a, "--popisek") or "", volba(a, "--text"), volba(a, "--pismo")
    src, klic = a[0], a[1]
    if not re.fullmatch(r"[\w.-]+", klic):
        sys.exit(f"Klíč „{klic}“: jen písmena, číslice, _ - . (z něj je název souboru)")
    im = Image.open(src)
    if len(a) < 3:
        sys.exit(f"{src}: {im.width}×{im.height} px – zadej cx,cy,a,b[,uhel] v pixelech tohoto obrázku")
    cx, cy, osa_a, osa_b, *uhel = cisla(a[2], (4, 5), "elipsa")
    im = im.convert("RGBA")
    oznac(im, cx, cy, osa_a, osa_b, uhel[0] if uhel else 0.0, popisek,
          tuple(cisla(text, (2,), "--text")) if text else None, int(velikost) if velikost else None)
    im = im.convert("RGB")
    full, small = os.path.join(ROOT, "zdroje", klic + ".jpg"), os.path.join(ROOT, "vyrezy", klic + ".jpg")
    for p in (full, small):
        os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(full, quality=90)
    if max(im.size) > WEB_PX:
        im.thumbnail((WEB_PX, WEB_PX), Image.LANCZOS)
    im.save(small, quality=88)
    print("uloženo:", full, "a", small, "– prohlédni si, jestli elipsa obepíná celou parcelu domu")
    h = podminky.hlaska_obrazku(ROOT, klic)   # stejně jako vyrez.py: smí výřez na veřejný web?
    if h:
        print(f"POZOR: {h}")


if __name__ == "__main__":
    main(sys.argv[1:])
