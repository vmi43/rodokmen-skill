#!/usr/bin/env python3
"""Místa předků pro mapu na webu (data/mista.json); souřadnice z Mapy.com (REST API, geokódování); k tomu RÚIAN pro dům.

Použití (z kořene projektu: python3 -I tools/slusne.py tools/mista.py …):
  mista.py pridej "Název" ["regulární výraz"] ["dotaz pro vyhledání"]
      přidá obec; výraz se hledá v údajích osob (výchozí = prvních 5 písmen názvu, aby sedělo i skloňování),
      dotaz pro Mapy.com (výchozí = „Název“, když nic nenajde, zkusí i mimo Česko);
      u víceznačných názvů (Podolí, Dub) přidej sousední obec: "Podolí, Odlochovice" – a ve výpisu vždy zkontroluj okres
  mista.py ruian "Horní Lhota 12"
      dům podle RÚIAN (ČÚZK, bez klíče; najde i malé osady): adresa s dnešní obcí, lat/lon, parcela pod domem a katastrální
      území. Dotaz = "Osada čp", "Ulice čp", "Ulice čp/čo" nebo ve městě i "Ulice čo"; obec za čárkou zúží výběr
      ("Husova 66, Beroun"). Dnešní obec a k. ú. se často liší od toho, co uživatel čeká.
  mista.py okoli <"Ulice čp/čo" | lat,lon> [polomer_m=80]
      všechny dnešní adresy v okolí (RÚIAN) podle čp.; adresy jedné budovy (roh) označí – pro tabulku adres domu v čase.
  mista.py parcely <"Osada čp" | lat,lon> [polomer_m=60] [vse]
      dnešní stavební parcely kolem domu s odstupem v metrech (E/N): podle čísel stavebních parcel najdeš dům na staré mapě.
      „vse“ = i ostatní pozemkové parcely.
  mista.py nova
      projde události osob (fakta začínající * × †, např. „† 4. 8. 1891 Biskupice čp. 14“), najde místa, která na mapě chybí
      (u osob, které tam mají událost), přidá je (výraz = prvních 5 písmen) a dohledá souřadnice. Co se nenajde, vypíše;
      nic se nepřidá naslepo – když dotaz vyjde jinde než ve zdejší krajině, zkontroluj okres ve výpisu a oprav.
      Pouští se po každé změně osob (viz data/STAV.md); `chybejici()` používá i kontrola.py jako varování.
  mista.py
      dohledá souřadnice obcí, které je ještě nemají, a **přesný bod každé adresy** („Biskupice čp. 14“) uvedené
      ve faktech osob; vypíše seznam. Adresa, kterou Mapy.com nezná (zaniklé domy), se vypíše – bod doplň ručně.
  mista.py znovu
      zahodí dosavadní souřadnice (kromě těch s "rucne": true) a dohledá je znovu z Mapy.com – pro převod starého projektu.

Souřadnice pro adresu jsou v mista.json v klíči "adresy": {"14": {"lat": …, "lon": …, "mapy": "Biskupice 14, …"}}.
Ruční bod (např. zaniklý dům podle mapy z rodinné kroniky): přidej "rucne": true, nástroj ho nepřepíše.
Původ bloku RÚIAN (`ruian`, `okoli`, `parcely`, odkazy na panorama): vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/mista.py), commit 32bef07. Zbytek je náš.

API klíč Mapy.com (zdarma, základní tarif 250 000 kreditů měsíčně, jedno hledání = 4 kredity): založ si účet a projekt
na https://developer.mapy.com/portal-muj-ucet/ a vytvoř klíč. Dej ho do proměnné prostředí MAPY_API_KEY nebo do souboru
pracovni/.mapy_klic (složka pracovni/ je v .gitignore). Klíč nikdy nepiš do chatu, kódu ani commitu.
"""
import json, math, os, re, statistics, sys, time, urllib.parse, urllib.request
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (tools/slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "mista.json")
API = "https://api.mapy.com/v1/geocode"
VZDALENE_KM = 50   # nový bod dál než tohle od všech ostatních míst projektu = asi jiná obec stejného jména
MAX_KM = 8   # adresa dál od středu obce je jiná obec stejného jména


def klic():
    k = os.environ.get("MAPY_API_KEY", "").strip()
    f = os.path.join(ROOT, "pracovni", ".mapy_klic")
    if not k and os.path.exists(f):
        k = open(f, encoding="utf-8").read().strip()
    if not k:
        sys.exit("Chybí API klíč Mapy.com. Založ ho zdarma na https://developer.mapy.com/portal-muj-ucet/ "
                 "a dej ho do proměnné MAPY_API_KEY nebo do souboru pracovni/.mapy_klic.")
    return k


def mapy(query, **par):
    """Položky odpovědi geokódování Mapy.com (seznam slovníků; prázdný, když nic nenašlo)."""
    par = {"query": query, "lang": "cs", "limit": 5} | par
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(par),
                                 headers={"X-Mapy-Api-Key": klic(), "User-Agent": "rodokmen-skill/1.1 (family genealogy map)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    time.sleep(0.3)
    return d.get("items", [])


def bod(it):
    return round(float(it["position"]["lat"]), 6), round(float(it["position"]["lon"]), 6)


def km(a, b):
    p = math.pi / 180
    x = math.sin((b[0] - a[0]) * p / 2) ** 2 + math.cos(a[0] * p) * math.cos(b[0] * p) * math.sin((b[1] - a[1]) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))


def popis(it):
    return f"{it.get('name', '')}, {it.get('location', '')}".strip(", ")


def geocode(q, zeme="cz"):
    """Střed obce (lat, lon, popis) nebo None. Nejdřív jen v dané zemi, pak kdekoli."""
    for loc in ([zeme] if zeme else []) + [None]:
        its = mapy(q, **({"locality": loc} if loc else {}), type="regional.municipality,regional.municipality_part")
        its = its or mapy(q, **({"locality": loc} if loc else {}))
        if its:
            return (*bod(its[0]), popis(its[0])) + (("MIMO",) if not loc and zeme else ())
    return None


def adresa(obec, cp, stred):
    """Přesný bod domu s číslem popisným `cp` v obci poblíž `stred` = (lat, lon); (lat, lon, popis) nebo None."""
    its = mapy(f"{obec} {cp}", type="regional.address", preferNear=f"{stred[1]},{stred[0]}", limit=10)
    best = None
    for it in its:
        # číslo popisné je před lomítkem: „14“ nebo „14/2“; shoda čísla chrání před jiným domem stejné ulice
        if "ev." in it.get("name", ""):   # „ev. č. 5“ = evidenční číslo (chata), ne číslo popisné
            continue
        if not re.search(rf"(?<![\d/]){re.escape(str(cp))}(?:/|\s|$)", it.get("name", "")):
            continue
        d = km(stred, bod(it))
        if d <= MAX_KM and (best is None or d < best[0]):
            best = (d, it)
    return (*bod(best[1]), popis(best[1])) if best else None


def adresy_osob(P, name, e):
    """Čísla popisná uvedená ve faktech osob u místa: {„14“, „77“}."""
    rx = re.compile(rf"(?:{e.get('re') or re.escape(name)})\w*\s+čp\.\s*(\d+)")
    return {m for p in P.values() for f in p.get("f", []) for m in rx.findall(f)}


_EVENT = re.compile(r"^[*×†]\s*(?:(?:asi|kolem|před|po)\s+)?[\d./–\s]*(?:\(\?\)\s*)?"
                    r"([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][\w\-]*(?: (?:nad|pod|u|na)? ?[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][\w\-]*)*)(?=\s+čp\.|\s*[,(;]|$)")


def chybejici(P, mista):
    """Místa z událostí osob (* × †), která nejsou v mista.json; jména osob se přeskočí."""
    jmena = " ".join(p.get("n", "") for p in P.values())
    out = {}
    for k, p in P.items():
        for f in p.get("f", []):
            m = _EVENT.match(f)
            if not m:
                continue
            name = m.group(1).strip()
            if name in jmena or any(re.search(e.get("re") or re.escape(n), name) for n, e in mista.items()):
                continue
            out.setdefault(name, []).append(k)
    return out


def uloz(cache):
    json.dump(cache, open(OUT, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)


# --- RÚIAN (ČÚZK, bez klíče): adresy, parcely a okolí domu. Převzato z vzoha/dejiny-domu-skill
# (skills/dejiny-domu/tools/mista.py), commit bda6028; do našeho mista.py přidáno vedle Mapy.com, nic z něj se nenahrazuje.
RUIAN = "https://ags.cuzk.cz/arcgis/rest/services/RUIAN/Prohlizeci_sluzba_nad_daty_RUIAN/MapServer"
GEOMETRIE = "https://ags.cuzk.gov.cz/arcgis/rest/services/Utilities/Geometry/GeometryServer/project"
STAVEBNI = 1            # druhcislovanikod: 1 stavební, 2 pozemková parcela
ZASTAVENA_PLOCHA = 13   # druhpozemkukod „zastavěná plocha a nádvoří“


def cislo_parcely(a):
    """„st. 12/3“; k. ú. s jednou číselnou řadou stavební parcely nemá, „st.“ tam správně chybí."""
    cislo = f"{a['kmenovecislo']}" + (f"/{a['poddelenicisla']}" if a.get("poddelenicisla") else "")
    return ("st. " if a.get("druhcislovanikod") == STAVEBNI else "") + cislo


def sjtsk(lat, lon):
    """WGS 84 → S-JTSK (m) přes geometrickou službu ČÚZK. Bez transformace datumu 1623 by bod ujel o ~10 m."""
    g = json.dumps({"geometryType": "esriGeometryPoint", "geometries": [{"x": lon, "y": lat}]})
    q = urllib.parse.urlencode({"inSR": 4326, "outSR": 5514, "geometries": g, "f": "json",
                                "transformation": 1623, "transformForward": "false"})
    with urllib.request.urlopen(f"{GEOMETRIE}?{q}", timeout=60) as r:
        p = json.load(r)["geometries"][0]
    return p["x"], p["y"]


def ruian_q(vrstva, where, pole, geo=False):
    q = urllib.parse.urlencode({"where": where, "outFields": pole, "returnGeometry": str(geo).lower(),
                                "outSR": 4326, "f": "json"})
    with urllib.request.urlopen(f"{RUIAN}/{vrstva}/query?{q}", timeout=60) as r:
        return json.load(r).get("features", [])


def adresni_mista(dotaz, pole, obec=""):
    """Adresní místa RÚIAN pro „Osada čp“, „Ulice čp“, „Ulice čp/čo“ i „Ulice čo“, jen v obci „obec“ (je-li zadaná).
    Velikost písmen RÚIAN rozlišuje („Na kopečku“) – bez nálezu hledá znovu bez ní (pomalé, ~7 s na dotaz)."""
    d = dotaz.replace(chr(39), "")
    ulice, _, cislo = d.rpartition(" ")
    vzory = [f"{d},%"]
    if ulice and cislo.isdigit():
        vzory += [f"{ulice} %/{cislo},%",   # „Ulice čo“ – v RÚIAN je „Ulice čp/čo, Část obce, …“
                  # obec bez ulic: „č.p. 29, 39301 Pavlov“; osada pod jinou obcí: „Švihov 47, 53825 Miřetice“
                  f"č.p. {cislo}, % {ulice}", f"č.p. {cislo}, % {ulice},%"]
    for podminka in ("adresa LIKE '{}'", "UPPER(adresa) LIKE UPPER('{}')"):
        adr, videno = [], set()
        for vzor in vzory:   # všechny tvary, ne jen první: „Hlína 1, Horka“ i „č.p. 1, 66491 Hlína“ jsou různé vsi
            for a in ruian_q(1, podminka.format(vzor), pole, True):
                if a["attributes"].get("adresa", id(a)) not in videno:
                    videno.add(a["attributes"].get("adresa", id(a)))
                    adr.append(a)
        if not adr and ulice and cislo.isdigit():
            adr = ruian_q(1, podminka.format(f"%{ulice} {cislo}, %"), pole, True)
        adr = [a for a in adr if not obec or v_obci(a["attributes"]["adresa"], obec)]
        if adr:
            return adr
    return []


def adresa_a_obec(misto):
    """„Ulice čp, Obec“ → („Ulice čp“, „Obec“); bez čárky obec prázdná."""
    dotaz, _, obec = misto.partition(",")
    return dotaz.strip(), obec.strip()


def odkazy_panorama(lat, lon):
    """Odkazy na dům ve Street View a Mapy.com – prochází jen uživatel, snímky do výstupu ne (reference/portaly.md)."""
    return (f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat:.6f},{lon:.6f}"
            f"  |  https://mapy.com/cs/zakladni?x={lon:.6f}&y={lat:.6f}&z=19 (tlačítko Panorama)")


def ruian(dotaz):
    ulice_cislo, obec = adresa_a_obec(dotaz)
    adr = adresni_mista(ulice_cislo, "adresa,stavebniobjekt", obec)
    if not adr:
        sys.exit(f"RÚIAN „{dotaz}“ nezná – zkus jiný tvar (\"Osada čp\", \"Ulice čp\") nebo jen \"Osada\" v nahlizenidokn.cuzk.cz")
    if len(adr) > 1:
        print(f"POZOR: {len(adr)} míst se stejnou adresou – vyber podle PSČ a okresu ze zadání (fara, panství, archiv)")
    for a in adr[:8]:
        at, g = a["attributes"], a["geometry"]
        print(f"{at['adresa']}   lat={g['y']:.5f}, lon={g['x']:.5f}")
        print(f"   panorama (prochází uživatel): {odkazy_panorama(g['y'], g['x'])}")
        so = ruian_q(3, f"kod={at['stavebniobjekt']}", "identifikacniparcela")
        if not so or not so[0]["attributes"].get("identifikacniparcela"):
            continue
        par = ruian_q(5, f"id={int(so[0]['attributes']['identifikacniparcela'])}",
                      "kmenovecislo,poddelenicisla,druhcislovanikod,katastralniuzemi")
        if par:
            pa = par[0]["attributes"]
            ku = ruian_q(7, f"kod={pa['katastralniuzemi']}", "nazev")
            print(f"   parcela {cislo_parcely(pa)}, "
                  f"k. ú. {ku[0]['attributes']['nazev'] if ku else '?'} ({pa['katastralniuzemi']})")


SOUSEDNI_PSC_M = 12000   # PSČ jedné obce (Blíževedly 47104 a 47002, Opava 5 PSČ) mají středy blíž, stejnojmenné obce dál


def obec_stred(nazev):
    """Obce a části obce jménem „nazev“ → [(„Část, PSČ Obec“, lat, lon)], střed = medián jejich adresních bodů RÚIAN.
    Adresa v RÚIAN: „Ulice čp, [Část, ]PSČ Obec“ nebo „Část čp, PSČ Obec“ (část bez ulic)."""
    n = nazev.replace(chr(39), "").strip()
    body = {}
    for a in ruian_q(1, f"adresa LIKE '% {n}' OR adresa LIKE '%, {n}, %' OR adresa LIKE '{n} %'", "adresa", True):
        if not a.get("geometry"):   # pár adresních míst RÚIAN nemá polohu
            continue
        casti = a["attributes"]["adresa"].split(", ")
        psc, _, obec = casti[-1].partition(" ")
        if obec == n or (len(casti) > 2 and casti[-2] == n) or re.fullmatch(rf"{re.escape(n)} \d+[a-z]?", casti[0]):
            body.setdefault((obec, psc), []).append((a["geometry"]["y"], a["geometry"]["x"]))
    skupiny = []   # [obec, [PSČ], body]
    for (obec, psc), b in sorted(body.items()):
        stejna = next((g for g in skupiny if g[0] == obec and math.hypot(*odstup(*median(g[2]), *median(b))) < SOUSEDNI_PSC_M), None)
        if stejna:
            stejna[1].append(psc)
            stejna[2] += b
        else:
            skupiny.append([obec, [psc], b])
    return [(f"{n}, {'/'.join(pscs)} {obec}", *median(b)) for obec, pscs, b in skupiny]


def median(body):
    return statistics.median(y for y, _ in body), statistics.median(x for _, x in body)


def patri_k_nazvu(cast, obec):
    """„Praha 8“, „Beroun-Zavadilka“ i „Beroun“ patří k obci „Praha“ / „Beroun“, „Bílá Hlína“ k „Hlína“ ne."""
    cast, obec = cast.lower(), obec.lower()
    return cast == obec or cast.startswith((obec + " ", obec + "-"))


def v_obci(adresa, obec):
    """Leží adresa („Ulice čp, [Část, ]PSČ Obec“ nebo „Osada čp, PSČ Obec“) v obci nebo části „obec“?
    Porovnává celé části adresy, ne podřetězec."""
    prvni, *dalsi = adresa.split(", ")
    casti = [re.sub(r" [\d/]+[a-z]?$", "", prvni)] + [re.sub(r"^\d{5} ", "", c) for c in dalsi]
    return any(patri_k_nazvu(c, obec) for c in casti)


def stred(misto):
    """lat, lon z „lat,lon“, z jediné adresy RÚIAN („Ulice čp“, „Ulice čp, Obec“), nebo z názvu obce či části obce
    (střed jejích adresních bodů). Víc míst se stejnou adresou nebo stejnojmenných obcí = skončí, ať se nevybere náhodné."""
    if "," in misto and all(c in "0123456789., -" for c in misto):
        return tuple(float(v) for v in misto.split(","))
    dotaz, obec = adresa_a_obec(misto)
    f = [a for a in adresni_mista(dotaz, "adresa", obec) if a.get("geometry")]
    if not f and not obec and not misto.rstrip()[-1:].isdigit():
        obce = obec_stred(misto)
        if len(obce) > 1:
            sys.exit(f"RÚIAN má {len(obce)} obcí nebo částí jménem „{misto}“ – vyber podle PSČ a okresu a zadej lat,lon:\n"
                     + "\n".join(f"  {k}   {y:.5f},{x:.5f}" for k, y, x in obce))
        if obce:
            nazev, lat, lon = obce[0]
            print("střed obce:", nazev)
            return lat, lon
    if not f:
        sys.exit(f"RÚIAN „{misto}“ nezná – zadej „Ulice čp/čo“, „Ulice čp, Obec“, název obce nebo lat,lon.")
    if len(f) > 1:
        sys.exit(f"RÚIAN má {len(f)} míst s adresou „{misto}“ – vyber podle PSČ a okresu a zadej ho jako lat,lon\n"
                 f"nebo „{dotaz}, Obec“:\n"
                 + "\n".join(f"  {a['attributes']['adresa']}   {a['geometry']['y']:.5f},{a['geometry']['x']:.5f}" for a in f))
    print("střed:", f[0]["attributes"]["adresa"])
    return f[0]["geometry"]["y"], f[0]["geometry"]["x"]


def v_obdelniku(vrstva, lat, lon, polomer, dotaz):
    """Prvky vrstvy RÚIAN v obdélníku kolem středu. Obdélník je větší než kruh – vzdálenost filtruje volající."""
    dlat = polomer / 111320
    dlon = dlat / math.cos(math.radians(lat))
    q = {"geometry": f"{lon - dlon},{lat - dlat},{lon + dlon},{lat + dlat}", "geometryType": "esriGeometryEnvelope",
         "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "returnGeometry": "true", "outSR": 4326, "f": "json", **dotaz}
    with urllib.request.urlopen(f"{RUIAN}/{vrstva}/query?{urllib.parse.urlencode(q)}", timeout=60) as r:
        res = json.load(r)
    if res.get("exceededTransferLimit"):
        print(f"POZOR: služba vrátila jen prvních {len(res.get('features', []))} prvků – zmenši poloměr")
    return res.get("features", [])


def odstup(lat, lon, lat2, lon2):
    """(na východ, na sever) v metrech."""
    return round((lon2 - lon) * 111320 * math.cos(math.radians(lat))), round((lat2 - lat) * 111320)


def okoli(misto, polomer=80):
    lat, lon = stred(misto)
    feats = v_obdelniku(1, lat, lon, polomer, {"outFields": "adresa,stavebniobjekt"})

    def cislo_popisne(adresa):   # „Ulice 12/3, Obec, …“ → 12
        c = adresa.split(",")[0].rsplit(" ", 1)[-1].split("/")[0]
        return int(c) if c.isdigit() else 0
    rows = []
    for f in feats:
        m = round(math.hypot(*odstup(lat, lon, f["geometry"]["y"], f["geometry"]["x"])))
        if m <= polomer:
            a = f["attributes"]
            rows.append((cislo_popisne(a["adresa"]), a["adresa"].split(",")[0], m, a.get("stavebniobjekt")))
    adres_budovy = {}
    for *_, so in rows:
        adres_budovy[so] = adres_budovy.get(so, 0) + 1
    for c, a, m, so in sorted(rows):
        print(f"čp. {c:<6} {a:40} {m:>4} m" + ("   ← víc adres jedné budovy" if so and adres_budovy[so] > 1 else ""))
    print(f"{len(rows)} adres do {polomer:g} m. „Víc adres jedné budovy“ = tentýž stavební objekt RÚIAN (roh nebo dva vchody);"
          " stejné čp. bez té značky může být jiná budova.")


def parcely(misto, polomer=60, vse=False):
    lat, lon = stred(misto)
    q = {"outFields": "kmenovecislo,poddelenicisla,druhcislovanikod,vymeraparcely"}
    if not vse:
        # v k. ú. s jednou číselnou řadou jsou všechny parcely pozemkové, dům poznáš jen podle druhu pozemku
        q["where"] = f"druhcislovanikod={STAVEBNI} OR druhpozemkukod={ZASTAVENA_PLOCHA}"
    rows = []
    for f in v_obdelniku(5, lat, lon, polomer, q):
        a, ring = f["attributes"], f["geometry"]["rings"][0]
        cy, cx = sum(p[1] for p in ring) / len(ring), sum(p[0] for p in ring) / len(ring)
        rows.append((a["druhcislovanikod"] != STAVEBNI, a["kmenovecislo"], cislo_parcely(a),
                     a.get("vymeraparcely"), *odstup(lat, lon, cy, cx)))
    for _, _, c, v, e, n in sorted(rows):
        print(f"{c:12} {v or 0:>7.0f} m²   E {e:>4} m  N {n:>4} m")
    print(f"{len(rows)} parcel v okolí ±{polomer:g} m od středu. Nízká čísla stavebních parcel = starší zástavba.")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "parcely":
        parcely(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != "vse" else 60, "vse" in sys.argv[3:])
        return
    if len(sys.argv) > 2 and sys.argv[1] == "okoli":
        okoli(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 80)
        return
    if len(sys.argv) > 2 and sys.argv[1] == "ruian":
        ruian(sys.argv[2])
        return
    cache = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "pridej" and len(sys.argv) > 2:
        name = sys.argv[2]
        stem = re.escape(name.split()[0][:5]) if len(name.split()) == 1 else re.escape(name)
        cache[name] = dict(cache.get(name, {}), re=sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else stem,
                           dotaz=sys.argv[4] if len(sys.argv) > 4 else name)
    ns = {}
    exec(open(os.path.join(ROOT, "data", "osoby.py"), encoding="utf-8").read(), ns)
    P = dict(ns["P"])
    if isinstance(ns.get("SIDE"), dict):
        P.update({"s%s" % k: v for k, v in ns["SIDE"].items()})
    if arg == "nova":
        nova = chybejici(ns["P"], cache)
        for name, ks in nova.items():
            stem = re.escape(name.split()[0][:5]) if len(name.split()) == 1 else re.escape(name)
            cache[name] = dict(re=stem, dotaz=name)
            print(f"NOVÉ MÍSTO: {name} (osoby {ks})")
        if not nova:
            print("Na mapě nic nechybí.")
    for name, e in list(cache.items()):
        if arg == "znovu" and not e.get("rucne"):
            for k in ("lat", "lon", "osm", "mapy"):
                e.pop(k, None)
        if "lat" not in e:
            dotaz = e.get("dotaz") or name
            g = geocode(dotaz)
            if g and len(g) > 3:
                print("MIMO ČESKO:", name, "→", g[2][:80], "– zkontroluj, že je to ono")
            if g:
                e["lat"], e["lon"], e["mapy"] = g[:3]
                e.pop("osm", None)
                dalsi = [(km((e["lat"], e["lon"]), (o["lat"], o["lon"])), n) for n, o in cache.items()
                         if n != name and isinstance(o.get("lat"), (int, float)) and isinstance(o.get("lon"), (int, float))]
                if dalsi and min(dalsi)[0] > VZDALENE_KM:   # jiná obec stejného jména? (převzato z upstreamu 0.8.0, #81)
                    d = min(dalsi)
                    print(f"POZOR: {name} je {d[0]:.0f} km od nejbližšího místa ({d[1]}) – je to ono? {e['mapy'][:80]}")
            else:
                print("NENALEZENO:", name, "– upravte 'dotaz' nebo doplňte lat/lon ručně")
                if arg == "nova":
                    cache.pop(name)   # bez souřadnic by zůstalo viset; příště se zkusí znovu
                continue
        if e.get("hypoteza"):
            continue
        ad = e.setdefault("adresy", {})
        for cp in sorted(adresy_osob(P, name, e), key=int):
            a = ad.get(cp, {})
            if arg == "znovu" and not a.get("rucne"):
                a = {}
            if "lat" in a:
                continue
            g = adresa(name, cp, (e["lat"], e["lon"]))
            if g:
                ad[cp] = {"lat": g[0], "lon": g[1], "mapy": g[2]}
            else:
                print(f"ADRESA NENALEZENA: {name} čp. {cp} – Mapy.com dům nezná, doplňte bod ručně "
                      f"(\"adresy\": {{\"{cp}\": {{\"lat\": …, \"lon\": …, \"rucne\": true}}}}); mapa ukáže střed obce")
        if not ad:
            e.pop("adresy")
        uloz(cache)   # po každém místě, ať se při přerušení nic neztratí
    uloz(cache)
    for n, e in cache.items():
        print(f"{n:28} {e.get('lat', '?'):>9} {e.get('lon', '?'):>9}  hledá „{e.get('re')}“  {e.get('mapy', '')[:60]}")
        for cp, a in e.get("adresy", {}).items():
            print(f"{'':4}čp. {cp:6} {a.get('lat', '?'):>10} {a.get('lon', '?'):>10}  {a.get('mapy', 'ručně' if a.get('rucne') else '')[:60]}")


if __name__ == "__main__":
    main()
