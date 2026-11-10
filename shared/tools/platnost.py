"""Pravidla platnosti dat domů a map pro export_web.py (a jednou i kontrola.py).

Jen funkce, nic nespouští. Každá vrací text chyby, nebo None, když je hodnota v pořádku.

Původ: převzato z tools/platnost.py projektu dejiny-domu-skill (https://github.com/vzoha/dejiny-domu-skill),
commit bda6028bae08307727a4449931497c9f163ea691. Vynecháno: kontroly kalendářních dat (`nemozna_data`,
`obracene_rozpeti`, `obraceny_interval`; kontrola.py má vlastní).
"""

import math, os, re, unicodedata

BEZPECNY_ODKAZ = re.compile(r"(?i)https?://|/(?!/)|#")   # začátek: web, stránka vlastního webu, kotva


def slugify(text):
    """Adresa stránky domu: bez diakritiky a interpunkce („ev. 3“ → „ev-3“)."""
    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def norm_answer(text):
    """Stejná normalizace jako v prihlaseni.html: bez diakritiky, malá písmena, jen a-z0-9."""
    t = unicodedata.normalize("NFD", str(text))
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]", "", t)


def chyba_odpovedi(login):
    """Odpověď, ze které normalizace nic nenechá („漢字“, „???“): přihlásit by se nešlo a web by vypadal otevřený."""
    odpoved = (login or {}).get("odpoved")
    if odpoved and not norm_answer(odpoved):
        return (f"prihlaseni.odpoved {str(odpoved)[:30]!r} nemá žádné písmeno a–z ani číslici (diakritika a jiná písma"
                " se odstraňují) – zvol odpověď z latinky nebo čísel")
    return None


# Jistota zvlášť od původu údaje (st): přečtené ze snímku může být nejisté čtením i přiřazením k domu.
VYHRADY = {"cteni": "nejisté čtení", "dum": "k domu přiřazeno nejistě"}


def vyhrady(x):
    """Štítky pro web: [„nejisté čtení“, …] podle polí cteni="nejiste" a dum="nejiste"."""
    return [stitek for pole, stitek in VYHRADY.items() if x.get(pole) == "nejiste"]


def chyby_vyhrad(x):
    """(chyby, upozornění) k polím cteni a dum."""
    chyby = [f"pole '{p}' smí být jen \"nejiste\" (nebo chybět), je tam {x[p]!r}"
             for p in VYHRADY if p in x and x[p] != "nejiste"]
    upozorneni = ["dum=\"nejiste\" bez 'note' – napiš, proč se zápis k domu váže jen nejistě"] \
        if x.get("dum") == "nejiste" and not x.get("note") else []
    return chyby, upozorneni


def chyba_odkazu(url):
    """Odkaz na webu smí vést jen na http(s) nebo na stránku webu. javascript:, data: ap. by se po kliknutí spustily."""
    if url and not BEZPECNY_ODKAZ.match(str(url).strip()):
        return f"odkaz {str(url)[:60]!r} nevede na http(s):// ani na stránku webu (/…)"
    return None


def chyba_polohy(x):
    """lat a lon buď obě chybí, nebo jsou obě čísla v rozsahu. Jen jedna nebo text rozbije export a mapy."""
    lat, lon = x.get("lat"), x.get("lon")
    if lat is None and lon is None:
        return None
    if lat is None or lon is None:
        return f"má jen {'lat' if lon is None else 'lon'} – doplň i {'lon' if lon is None else 'lat'}, nebo smaž obě"
    for nazev, v, mez in (("lat", lat, 90), ("lon", lon, 180)):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v) > mez:
            return f"{nazev} {v!r} není číslo v rozsahu ±{mez} (zapiš číslo bez uvozovek, např. 49.41)"
    return None


def chyby_adres_domu(klice):
    """Klíče domů, které dají stejnou adresu stránky („12a“ a „12á“, na webu by zůstal jen jeden) nebo žádnou („?“)."""
    podle = {}
    for k in klice:
        podle.setdefault(slugify(k), []).append(str(k))
    return [f"domy {', '.join(ks)}: stejná adresa stránky /dum/{s}/, na webu by zůstal jen jeden – přejmenuj klíč" if s
            else f"dům {', '.join(ks)}: klíč bez písmen a číslic nedá adresu stránky"
            for s, ks in podle.items() if len(ks) > 1 or not s]


def cislo_domu(klic, d):
    """Zobrazené číslo domu: pole `cp`, chybí-li, klíč (klíč = čp. je výchozí zápis)."""
    return str(d.get("cp") or klic)


def chyby_cisel_domu(D):
    """(chyby, upozornění): `cp` a `cast` jen text; dva domy se stejným číslem ve stejné části obce bez období v `cisla`."""
    chyby, podle = [], {}
    for k, d in D.items():
        chyby += [f"dům {k}: pole '{p}' piš jako text (\"12\"), ne {type(d[p]).__name__}"
                  for p in ("cp", "cast") if p in d and not isinstance(d[p], str)]
        podle.setdefault((cislo_domu(k, d), str(d.get("cast") or "")), []).append(k)
    upozorneni = [f"domy {', '.join(map(str, ks))}: stejné čp. {cp}{f' ({cast})' if cast else ''} – jiná část obce? Doplň"
                  " 'cast'. Nový dům na místě starého? Doplň oběma 'cisla' s obdobím (reference/data.md)"
                  for (cp, cast), ks in podle.items() if len(ks) > 1 and not all(D[k].get("cisla") for k in ks)]
    return chyby, upozorneni


def jpeg_rozmery(d):
    """(šířka, výška) z hlavičky JPEG, None když to JPEG není."""
    if d[:3] != b"\xff\xd8\xff":
        return None
    i = 2
    while i + 9 <= len(d) and d[i] == 0xFF:
        znacka, delka = d[i + 1], int.from_bytes(d[i + 2:i + 4], "big")
        if 0xC0 <= znacka <= 0xCF and znacka not in (0xC4, 0xC8, 0xCC):   # SOF: rozměry obrázku
            return int.from_bytes(d[i + 7:i + 9], "big"), int.from_bytes(d[i + 5:i + 7], "big")
        i += 2 + delka
    return None


def rozmery_obrazku(cesta):
    """(šířka, výška) JPEG souboru, None když chybí nebo to JPEG není."""
    try:
        with open(cesta, "rb") as f:
            return jpeg_rozmery(f.read())
    except FileNotFoundError:
        return None


def vyrez_sjtsk(bbox):
    """Pole `vyrez` mapy stažené z mapového serveru v S-JTSK (bbox v metrech)."""
    return {"crs": "EPSG:5514", "bbox": [round(v, 1) for v in bbox]}


def chyba_vyrezu(v):
    """Pole `vyrez` mapy: {"crs": "EPSG:5514", "bbox": [x0, y0, x1, y1]}, x0 < x1 a y0 < y1. Chybí = v pořádku."""
    if v is None:
        return None
    b = v.get("bbox") if isinstance(v, dict) else None
    cisla = isinstance(b, list) and len(b) == 4 and all(
        isinstance(c, (int, float)) and not isinstance(c, bool) and math.isfinite(c) for c in b)
    if not (cisla and b[0] < b[2] and b[1] < b[3] and isinstance(v.get("crs"), str) and v["crs"]):
        return (f"vyrez {str(v)[:80]!r} má být {{\"crs\": \"EPSG:5514\", \"bbox\": [x0, y0, x1, y1]}}"
                " s x0 < x1 a y0 < y1 (vypíše ho cuzk_archiv.py mapa, ipr_praha.py ho zapíše sám)")
    return None


def skupiny_map(mapy):
    """{skupina: [mapy]} jen se dvěma a více mapami – jedna mapa nemá s čím se porovnat."""
    podle = {}
    for m in mapy:
        if m.get("skupina"):
            podle.setdefault(m["skupina"], []).append(m)
    return {g: ms for g, ms in podle.items() if len(ms) > 1}


PRESNOST_VYREZU = 0.01   # rohy a poměr stran smí ujet o 1 % šířky výřezu (3 m u 300 m)


def proc_neprolinat(mapy, vyrezy):
    """Proč mapy jedné skupiny nejde prolínat (web je dá vedle sebe), None = jde.

    mapy mají platný nebo chybějící `vyrez`, vyrezy = složka s obrázky map pro web.
    Stejný výřez je jen předpoklad: mapa může mít polohové chyby nebo zachycovat plán místo skutečnosti.
    """
    bez = [m["img"] for m in mapy if not m.get("vyrez")]
    if bez:
        return f"bez pole 'vyrez': {', '.join(bez)}"
    vzor = mapy[0]["vyrez"]["bbox"]
    tolerance = PRESNOST_VYREZU * (vzor[2] - vzor[0])
    for m in mapy:
        v = m["vyrez"]
        if v["crs"] != mapy[0]["vyrez"]["crs"] or any(abs(a - b) > tolerance for a, b in zip(v["bbox"], vzor)):
            return f"{m['img']} má jiný výřez než {mapy[0]['img']}"
        r = rozmery_obrazku(os.path.join(vyrezy, m["img"] + ".jpg"))
        pomer_vyrezu = (v["bbox"][2] - v["bbox"][0]) / (v["bbox"][3] - v["bbox"][1])
        if r and abs(r[0] / r[1] / pomer_vyrezu - 1) > PRESNOST_VYREZU:
            return f"{m['img']}: obrázek {r[0]}×{r[1]} px nemá poměr stran výřezu (oříznutý?)"
    return None
