#!/usr/bin/env python3
"""Staré mapy z Geolabu UJEP (geolab.cz/stare-mapy): I. a II. vojenské mapování, Müllerovo mapování, část III. mapování.

Listy nejsou georeferencované: list s obcí najdi v kladu (obrázek s čísly listů a názvy měst), pak náhled listu
a výřez obce. Smí do PDF i na web s citací Rakouského státního archivu (číslo listu), Geolabu a MŽP (reference/podminky.md).

Díla: 1vm-ce 1vm-mo 1vm-sl (I. mapování Čechy, Morava, Slezsko), 2vm-ce 2vm-mo (II. mapování), 3vm-25 3vm-75
(III. mapování, neúplné), mul-ce mul-mo (Müllerovo mapování).

Použití:
  geolab.py listy <dílo>                                   – kódy listů s rozměry
  geolab.py klad <dílo> <klad.jpg>                         – přehled listů (najdi list podle měst)
  geolab.py export <dílo> <list> <výstup.jpg> [x0,y0,x1,y1] [--redukce N]
      celý list bez výřezu je náhled (redukce 4, asi 700 px); výřez v podílech 0–1 jako u vyrez.py, výchozí plné rozlišení.
      Vadná dlaždice na serveru (obrázek nejde přečíst) → nástroj sám zkusí poloviční rozlišení (redukce + 1) a řekne to.
Příklad (Hlína u Ivančic): klad 2vm-mo → list O_10_I (sekce 10, východní kolona I) → náhled → výřez
  geolab.py export 2vm-mo O_10_I hlina.jpg 0.185,0.80,0.32,0.885

Původ: převzato z vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/geolab.py), commit 32bef07; úprava: slusne.py se u nás zapíná importem (bez instaluj())."""
import io, math, os, re, sys, urllib.error, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne   # společný limit rychlosti (slusne.py; u nás se zapíná importem)

WEB = "https://geolab.cz"
DILA = {"1vm-ce": "I. vojenské mapování, Čechy", "1vm-mo": "I. vojenské mapování, Morava", "1vm-sl": "I. vojenské mapování, Slezsko",
        "2vm-ce": "II. vojenské mapování, Čechy", "2vm-mo": "II. vojenské mapování, Morava",
        "3vm-25": "III. vojenské mapování 1 : 25 000", "3vm-75": "III. vojenské mapování 1 : 75 000",
        "mul-ce": "Müllerovo mapování, Čechy", "mul-mo": "Müllerovo mapování, Morava"}
NAHLED = 4   # redukce celého listu: 11 000 px / 16 ≈ 700 px
GEOLAB = "© Laboratoř geoinformatiky UJEP (Geolab); © Ministerstvo životního prostředí ČR"
KRIEGSARCHIV = "© Österreichisches Staatsarchiv/Kriegsarchiv, Wien"   # originály I. a II. mapování (reference/podminky.md)


def citace(dilo, list_):
    """I. a II. mapování z Vídně; u Müllerova a III. mapování původ listů Geolab uvádí u díla, nástroj ho nedomýšlí."""
    puvod = KRIEGSARCHIV if dilo[:3] in ("1vm", "2vm") else "původ listu viz geolab.cz/stare-mapy/" + dilo
    return f"{DILA[dilo]}, list {list_}, {puvod}; {GEOLAB}"


def stahni(url):
    req = urllib.request.Request(url, headers={"User-Agent": slusne.UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def nacti_dilo(html):
    """Ze stránky díla (Next.js) adresa dlaždic, klad a listy {kód: (šířka, výška, dlaždice, cesta)}."""
    t = html.replace('\\"', '"')
    base = re.search(r'"tilesBase":"([^"]+)"', t)
    klad = re.search(r'"index":\{"src":"([^"]+)"', t)
    if not base:
        sys.exit("Geolab: ve stránce díla chybí tilesBase – web se změnil, uprav geolab.py")
    listy = {}
    for m in re.finditer(r'\{"code":"([^"]+)"([^}]*)\}', t):
        pole = dict(re.findall(r'"(\w+)":"?([^",]+)"?', m.group(2)))
        if "width" in pole:
            cesta = pole.get("tiles") or f"{m.group(1)}/zoomify/"
            listy[m.group(1)] = (int(pole["width"]), int(pole["height"]), int(pole.get("tileSize", 256)), cesta)
    return base.group(1), (klad.group(1) if klad else None), listy


def urovne(w, h, t):
    """Rozměry úrovní Zoomify od nejmenší (celý obrázek v jedné dlaždici) po plné rozlišení."""
    u = [(w, h)]
    while w > t or h > t:
        w, h = math.ceil(w / 2), math.ceil(h / 2)
        u.append((w, h))
    return u[::-1]


def dlazdice(w, h, t, redukce, x0, y0, x1, y1):
    """Dlaždice výřezu: [(url_cesta, x, y)] a velikost výsledku. TileGroup = pořadí dlaždice napříč úrovněmi / 256."""
    u = urovne(w, h, t)
    z = max(0, len(u) - 1 - redukce)
    lw, lh = u[z]
    pred = sum(math.ceil(a / t) * math.ceil(b / t) for a, b in u[:z])
    sloupcu = math.ceil(lw / t)
    px0, py0, px1, py1 = int(x0 * lw), int(y0 * lh), min(lw, math.ceil(x1 * lw)), min(lh, math.ceil(y1 * lh))
    out = []
    for ty in range(py0 // t, (py1 - 1) // t + 1):
        for tx in range(px0 // t, (px1 - 1) // t + 1):
            i = pred + ty * sloupcu + tx
            out.append((f"TileGroup{i // 256}/{z}-{tx}-{ty}.jpg", tx * t - px0, ty * t - py0))
    return out, (px1 - px0, py1 - py0)


def export(dilo, base, listy, a):
    """a = <list> <výstup.jpg> [x0,y0,x1,y1] [--redukce N]; celý list bez výřezu je náhled."""
    if len(a) < 2 or a[0] not in listy:
        sys.exit(f"export: neznámý list {a[0] if a else ''} (geolab.py listy {dilo})")
    from PIL import Image, UnidentifiedImageError
    list_, vystup, zbytek = a[0], a[1], a[2:]
    ramec = next((x for x in zbytek if re.fullmatch(r"[\d.]+,[\d.]+,[\d.]+,[\d.]+", x)), "0,0,1,1")
    if "--redukce" in zbytek:
        i = zbytek.index("--redukce") + 1
        if i >= len(zbytek) or not zbytek[i].isdigit():
            sys.exit("export: --redukce chce číslo (0 = plné rozlišení, 1 = poloviční…)")
        redukce = int(zbytek[i])
    else:
        redukce = NAHLED if ramec == "0,0,1,1" else 0
    w, h, t, cesta = listy[list_]
    while True:
        seznam, velikost = dlazdice(w, h, t, redukce, *(float(v) for v in ramec.split(",")))
        slusne.strop_dlazdic(len(seznam), f"Geolab {list_}")
        img = Image.new("RGB", velikost, "white")
        try:
            for c, x, y in seznam:
                img.paste(Image.open(io.BytesIO(stahni(base + cesta + c))).convert("RGB"), (x, y))
            break
        except (UnidentifiedImageError, urllib.error.HTTPError) as e:   # vadná dlaždice (Olomouc 1vm-mo m039, plné rozlišení)
            if redukce >= len(urovne(w, h, t)) - 1 or (isinstance(e, urllib.error.HTTPError) and e.code != 404):
                raise   # jen nečitelná nebo chybějící dlaždice; nejmenší úroveň nemá kam ustoupit
            print(f"Dlaždice {c} (redukce {redukce}) je vadná ({type(e).__name__}) – zkouším redukci {redukce + 1} "
                  "(poloviční rozlišení).", file=sys.stderr)
            redukce += 1
    if redukce:
        print(f"Výřez má redukci {redukce} (1/{2 ** redukce} plného rozlišení).")
    img.save(vystup, quality=90)
    print(f"{vystup} {velikost[0]}×{velikost[1]}")
    print("Citace: " + citace(dilo, list_))


def main(a):
    if len(a) < 2 or a[0] not in ("listy", "klad", "export") or a[1] not in DILA:
        sys.exit(__doc__)
    prikaz, dilo = a[0], a[1]
    base, klad, listy = nacti_dilo(stahni(f"{WEB}/stare-mapy/{dilo}").decode("utf-8", "replace"))
    if prikaz == "listy":
        for k, (w, h, _, _) in listy.items():
            print(f"{k}  {w}×{h}")
        print(f"{len(listy)} listů, {DILA[dilo]}")
    elif prikaz == "klad":
        if not klad or len(a) < 3:
            sys.exit("klad: chybí výstupní soubor (nebo dílo klad nemá)")
        from PIL import Image
        Image.open(io.BytesIO(stahni(WEB + klad))).convert("RGB").save(a[2], quality=90)
        print(a[2])
    else:
        export(dilo, base, listy, a[2:])

if __name__ == "__main__":
    main(sys.argv[1:])
