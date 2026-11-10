#!/usr/bin/env python3
"""Staré mapy z Archivu ČÚZK (ags.cuzk.gov.cz/archiv) bez prohlížeče: stabilní katastr, indikační skici, pozemkový katastr,
seznam leteckých měřických snímků.

Archiv ČÚZK je webová aplikace nad službami ArcGIS. Token pro ně vydává veřejná služba ČÚZK (stejně jako v aplikaci),
nástroj si ho obstará sám a uloží na hodinu do pracovni/.cuzk_token.

Původ: převzato z vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/cuzk_archiv.py), commit bda6028; úprava: bez
závislosti na platnost.py (vyrez_sjtsk je tady) a na slusne.instaluj() (slusne.py se u nás zapíná importem).

Použití (z kořene projektu):
  cuzk_archiv.py listy "Horní Lhota 12" | "Ulice čp, Obec" | "Obec" | lat,lon
      které listy stabilního katastru pokrývají místo: katastrální obec stabilního katastru (často jiná než dnes – malá ves
      bývala součástí sousední), originální mapa (om_SIGN_INV, rok reambulace, listy om_SOUB), císařský otisk
      (cio_SIGN_INV), evidenční mapa (změny 1883–1956, je-li naskenovaná) a indikační skica (S0X = předpona
      rastrů ve službě skici).
  cuzk_archiv.py rastry <sluzba> "vzor"
      rastry (listy) ve službě: stable = originální mapy a císařské otisky (vzor např. B2_a_4C_518),
      skici = indikační skici (vzor = S0X bez „c|“, např. BUD286018270), nonstable = ostatní
      (mj. evidenční mapy, vzor např. B2_a_14C_1223-1).
      Vypíše id | název | rozměr listu (v jednotkách listu).
  cuzk_archiv.py prehled <sluzba> "vzor" <vystup.jpg> [sirka_px=600]
      všechny listy najednou v malém náhledu (pod každým id a název listu) – najdi ves, pak export výřezu.
      Potřebuje ImageMagick. Obálku vynechá.
  cuzk_archiv.py export <sluzba> <id> <vystup.jpg> [x0,y0,x1,y1] [sirka_px]
      list v plném rozlišení nebo jeho výřez. Výřez jako u vyrez.py: podíly 0–1 od levého horního rohu
      (celý list = 0,0,1,1; výchozí). Výchozí šířka 4000 px, max. asi 15000. Nejdřív stáhni celý list menší
      (sirka 1500), najdi ves, pak výřez ve velkém.
  cuzk_archiv.py mapa <vrstva> "Horní Lhota 12" | lat,lon <vystup.jpg> [polomer_m] [px]
      georeferencovaná (spojená) vrstva kolem místa: pk = pozemkový katastr (~1900–1950, v S-JTSK, sedí na dnešní
      domy), originalni_mapy, cisarske_otisky, cenia50 = ortofoto CENIA z 50. let (většinou 1952–54, vypíše rok
      a citaci; CC BY, smí i do PDF), vm3 = III. vojenské mapování, speciální mapa 1 : 75 000 (CENIA, jen ke čtení –
      do výstupu topografická sekce z `rady`). Malé obce spojené vrstvy ČÚZK často nepokrývají (bílý obrázek) –
      pak listy + export. Výchozí poloměr 150 m, 1500 px. Vypíše i dnešní adresní body RÚIAN (čísla domů)
      v pixelech obrázku a s ImageMagickem je zakreslí do <vystup>_adresy.jpg: na které staré stavební parcele
      dnešní číslo stojí (ztotožnění domu, přečíslování). Vypíše „vyrez“ do mapy.json (prolínání na webu).
  cuzk_archiv.py rady "Horní Lhota 12" | lat,lon
      všechny mapové řady Archivu ČÚZK k místu (jako panel „Archivní mapy“ v aplikaci), nejen stabilní katastr:
      otisky katastrálních map (města často 1 : 1000, stav 1. pol. 20. stol.), mapa evidence nemovitostí, mapa
      kultur, Státní mapa 1 : 5000 (víc vydání), Základní a vojenské mapy. U podrobných map najde id rastrů
      ve službě nonstable pro export (rastry se jmenují jinak než klad, proto hledání podle části názvu).
  cuzk_archiv.py lms "Horní Lhota 12" | lat,lon
      které ročníky leteckých měřických snímků z 30.–60. let (armáda, © MO ČR) místo pokrývají – jen seznam.
      Snímky si uživatel prohlédne v aplikaci Archiv ČÚZK; soubor je placený a jen pro vlastní potřebu (reference/podminky.md).
Ber ohled na server: stahuj jen listy a výřezy, které čteš. Výsledek ulož do dokumentů a dál vyrez.py + mapy.json.
"""
import glob, json, math, os, re, shutil, subprocess, sys, time, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import mista  # noqa: E402
import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "data", "STAV.md")):   # spuštěno ze složky skillu: data projektu tam nejsou, zápis by šel do skillu
    sys.exit(f"{os.path.basename(__file__)}: {ROOT} není složka projektu (chybí data/STAV.md). "
             f"Spusť projektovou kopii z kořene projektu: python3 -I tools/{os.path.basename(__file__)} …")
REFERER = "https://ags.cuzk.gov.cz/archiv/"
ARCHIV = "https://ags.cuzk.gov.cz/arcgis4/rest/services/Archiv"
CENIA = "https://gis.cenia.cz"
CENIA_WMS = {"cenia50": ("ortofotomapa_historicka", "orto"),   # vrstva mapa → (služba mapcache, vrstva WMS)
             "vm3": ("III_vojenske_mapovani", "III_vojenske_mapovani")}
CENIA_CITACE = ("Historická ortofotomapa © CENIA 2010 a © GEODIS BRNO, spol. s r.o. 2010, Podkladové letecké snímky "
                "poskytl VGHMÚř Dobruška, © MO ČR 2009")
GEN = "https://ags.cuzk.gov.cz/arcgis2/rest/services/GenerateToken/Token/GPServer/GenerateToken"
RUIAN = "https://ags.cuzk.cz/arcgis/rest/services/RUIAN/Prohlizeci_sluzba_nad_daty_RUIAN/MapServer"
TOKEN = os.path.join(ROOT, "pracovni", ".cuzk_token")


def vyrez_sjtsk(bbox):
    """Pole `vyrez` mapy stažené z mapového serveru v S-JTSK (bbox v metrech)."""
    return {"crs": "EPSG:5514", "bbox": [round(v, 1) for v in bbox]}


def get(url, params=None, binary=False):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Referer": REFERER, "User-Agent": slusne.UA})
    for pokus in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = r.read()
                return d if binary else json.loads(d)
        except OSError:
            if pokus == 2:
                raise
            time.sleep(2)


def token():
    if os.path.exists(TOKEN) and time.time() - os.path.getmtime(TOKEN) < 50 * 60:
        return open(TOKEN).read().strip()
    job = get(f"{GEN}/submitJob", {"GenerateTokenURL": "https://ags.cuzk.gov.cz/arcgis4/tokens/", "referer": REFERER,
                                   "parametr": "", "expiration": 60, "f": "json"})["jobId"]
    for _ in range(20):
        time.sleep(1)
        if get(f"{GEN}/jobs/{job}", {"f": "json"}).get("jobStatus") == "esriJobSucceeded":
            break
    else:
        sys.exit("ČÚZK nevydal token do 20 s – zkus to za chvíli znovu")
    t = get(f"{GEN}/jobs/{job}/results/Token", {"f": "json"})["value"]
    os.makedirs(os.path.dirname(TOKEN), exist_ok=True)
    open(TOKEN, "w").write(t)
    return t


def archiv(cesta, params, binary=False):
    d = get(f"{ARCHIV}/{cesta}", dict(params, token=token()), binary)
    if not binary and "error" in d:
        sys.exit(f"ČÚZK: {d['error']}")
    return d


def save_jpeg(img, out):
    if not img.startswith(b"\xff\xd8"):
        sys.exit("ČÚZK nevrátil obrázek: " + img[:300].decode("utf-8", "replace"))
    open(out, "wb").write(img)


def klady(lat, lon, vrstvy="all"):
    """Klady mapových listů Archivu ČÚZK, které pokrývají bod (vrstva 3 = stabilní katastr)."""
    return archiv("klady/MapServer/identify", {
        "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "sr": 4326, "layers": vrstvy,
        "tolerance": 0, "mapExtent": f"{lon - .01},{lat - .01},{lon + .01},{lat + .01}",
        "imageDisplay": "1000,1000,96", "returnGeometry": "false", "f": "json"})


def listy(m):
    d = klady(*mista.stred(m), "all:3")
    if not d.get("results"):
        print("stabilní katastr: žádný list (zkus jiné místo)")
    for r in d.get("results", []):
        a = {k: v for k, v in r["attributes"].items() if v and v.strip() and v != "Null"}
        print(f"katastrální obec (stabilní katastr): {a.get('NAZ_PUV_CS', '?')} ({a.get('NAZ_PUV_NE', '')})")
        print(f"  originální mapa: {a.get('om_NAZEV_JEDNOTKY', '–')}, sign. {a.get('om_SIGNATURA', '?')}, "
              f"inv. č. {a.get('om_INV_CISLO', '?')}, mapováno {a.get('om_ROZPIS_DAT', '?')}, "
              f"reambulace {a.get('om_REAMBULACE', '–')}")
        print(f"     → rastry stable \"{a.get('om_SIGN_INV', '')}\", listy {a.get('om_SOUB', '?')}")
        print(f"  císařský otisk: sign. {a.get('cio_SIGNATURA', '?')}, inv. č. {a.get('cio_INV_CISLO', '?')}, "
              f"{a.get('cio_DAT_OD', '?')}, listů {a.get('cio_LISTU_CELK', '?')} → rastry stable \"{a.get('cio_SIGN_INV', '')}\"")
        if a.get("kme_SIGN_NOMEN"):
            print(f"  evidenční mapa (změny do 20. stol.): sign. {a.get('kme_SIGNATURA', '?')}, inv. č. {a.get('kme_INV_CISLO', '?')}, "
                  f"{a.get('kme_DAT_OD', '?')}–{a.get('kme_DAT_DO', '?')} → rastry nonstable \"{a['kme_SIGN_NOMEN']}\"")
        s0x = a.get("S0X", "").split("|")[-1]
        if not s0x:
            print("  indikační skica: není v kladu")
        elif s0x.startswith("MOR"):   # služba skici moravské skici nemá (Hlína MOR067318731, 5. 11. 2026)
            print(f"  indikační skica: {s0x} – ve službě skici Morava není, najít ručně v aplikaci Archiv ČÚZK")
        else:
            print(f"  indikační skica: → rastry skici \"{s0x}\"")


def najdi_rastry(sluzba, vzor):
    d = archiv(f"archiv_nespojene_{sluzba}/ImageServer/query", {
        "where": f"Name LIKE '{vzor.replace(chr(39), '')}%'", "outFields": "OBJECTID,Name",
        "returnGeometry": "true", "f": "json"})
    feats = [f for f in d.get("features", []) if f["attributes"]["Name"].startswith(vzor)
             and not f["attributes"]["Name"][len(vzor):len(vzor) + 1].isdigit()]   # 518 ≠ 5180
    return feats


def rastry(sluzba, vzor):
    feats = najdi_rastry(sluzba, vzor)
    for f in feats:
        r = f["geometry"]["rings"][0]
        xs, ys = [p[0] for p in r], [p[1] for p in r]
        print(f"{f['attributes']['OBJECTID']} | {f['attributes']['Name']} | {max(xs) - min(xs):.1f} × {max(ys) - min(ys):.1f}")
    if not feats:
        print("nic – zkus kratší vzor")


def export(sluzba, rid, out, vyrez="0,0,1,1", sirka=4000):
    d = archiv(f"archiv_nespojene_{sluzba}/ImageServer/query", {"objectIds": rid, "outFields": "OBJECTID",
                                                                "returnGeometry": "true", "f": "json"})
    r = d["features"][0]["geometry"]["rings"][0]
    X0, X1 = min(p[0] for p in r), max(p[0] for p in r)
    Y0, Y1 = min(p[1] for p in r), max(p[1] for p in r)
    a, b, c, e = (float(x) for x in vyrez.split(","))
    bbox = (X0 + a * (X1 - X0), Y1 - e * (Y1 - Y0), X0 + c * (X1 - X0), Y1 - b * (Y1 - Y0))   # y roste nahoru
    sirka = int(sirka)
    vyska = round(sirka * (bbox[3] - bbox[1]) / (bbox[2] - bbox[0]))
    img = archiv(f"archiv_nespojene_{sluzba}/ImageServer/exportImage", {
        "f": "image", "bbox": ",".join(f"{v:.4f}" for v in bbox), "size": f"{sirka},{vyska}", "format": "jpg",
        "compressionQuality": 92,
        "mosaicRule": json.dumps({"ascending": True, "lockRasterIds": [int(rid)], "mosaicMethod": "esriMosaicLockRaster"})},
        binary=True)
    save_jpeg(img, out)
    print(f"{out} {sirka}×{vyska}")


def prehled(sluzba, vzor, out, sirka=600):
    """Všechny listy (rastry) najednou v malém náhledu s názvem listu – ves najdeš na jednom obrázku."""
    import glob, shutil, subprocess, tempfile
    m = shutil.which("magick") or shutil.which("montage") or next(iter(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe")), None)
    if not m:
        sys.exit("Chybí ImageMagick (příkaz magick). Nainstaluj ho a spusť znovu, nebo stáhni listy po jednom přes export.")
    feats = najdi_rastry(sluzba, vzor)
    if not feats:
        sys.exit("nic – zkus kratší vzor")
    tmp = tempfile.mkdtemp(prefix="prehled_")
    try:
        soubory = []
        for f in feats:
            jmeno = f["attributes"]["Name"]
            if re.search(r"obalka|obálka", jmeno, re.I):
                continue
            cil = os.path.join(tmp, f"{len(soubory) // 3:02d}.jpg")
            import contextlib, io
            with contextlib.redirect_stdout(io.StringIO()):
                export(sluzba, f["attributes"]["OBJECTID"], cil, "0,0,1,1", sirka)
            soubory += ["-label", f'{f["attributes"]["OBJECTID"]} {jmeno}', cil]
        cmd = ([m, "montage"] if os.path.basename(m).lower().startswith("magick") else [m]) + soubory + [
            "-tile", "4x", "-geometry", f"{int(sirka)}x{int(sirka)}+6+6", "-pointsize", "18", out]
        subprocess.run(cmd, check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{out} – {len(soubory) // 3} listů; pod náhledem je id pro export")


def obalka(bbox):
    return ",".join(f"{v:.1f}" for v in bbox)


def mapa(vrstva, m, out, polomer=150, px=1500):
    px, r = int(px), float(polomer)
    x, y = mista.sjtsk(*mista.stred(m))
    bbox = (x - r, y - r, x + r, y + r)   # v S-JTSK (ne WGS 84: server by ho převedl bez datumu, ~110 m vedle)
    if vrstva in CENIA_WMS:
        sluzba, vrstvy = CENIA_WMS[vrstva]
        img = get(f"{CENIA}/mapcache/{sluzba}/wms", {
            "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "LAYERS": vrstvy, "STYLES": "", "SRS": "EPSG:5514",
            "BBOX": obalka(bbox), "WIDTH": px, "HEIGHT": px, "FORMAT": "image/jpeg"}, binary=True)
        save_jpeg(img, out)
        if vrstva == "cenia50":
            print(f"{out} – snímek z roku {cenia_rok(x, y)}. Citace: {CENIA_CITACE}")
        else:
            print(f"{out} – jen ke čtení (podmínky CENIA u vojenských mapování si odporují). Do výstupu topografickou "
                  "sekci 1 : 25 000 z ÚAZK: rady → export nonstable D1_21__…")
    else:
        img = archiv(f"archiv_spojene_{vrstva}/MapServer/export", {
            "bbox": obalka(bbox), "bboxSR": 5514, "imageSR": 5514,
            "size": f"{px},{px}", "format": "jpg", "dpi": 96, "f": "image"}, binary=True)
        save_jpeg(img, out)
        print(f"{out} – zkontroluj, jestli není bílý (vrstva tu nemusí být)")
    print(f'Do data/mapy.json k mapě (celý obrázek, vyrez.py … 0,0,1,1): "vyrez": {json.dumps(vyrez_sjtsk(bbox))}'
          ' – stejný výřez = web prolíná')
    adresy(bbox, px, out)


def cenia_rok(x, y):
    """Rok snímku ortofota 50. let v bodě (S-JTSK) – mozaika je z různých let."""
    v = "ortofotomapa_historicka_roky"
    d = get(f"{CENIA}/geoserver/{v}/wms", {
        "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetFeatureInfo", "LAYERS": v, "QUERY_LAYERS": v, "STYLES": "",
        "SRS": "EPSG:5514", "BBOX": obalka((x - 1, y - 1, x + 1, y + 1)), "WIDTH": 3, "HEIGHT": 3, "X": 1, "Y": 1,
        "INFO_FORMAT": "application/json"})
    return next((f["properties"]["rok"] for f in d.get("features", [])), "?")


def adresy(bbox, px, out):
    """Dnešní adresní body RÚIAN (číslo domovní) v pixelech obrázku: na které staré parcele dnešní číslo stojí."""
    f = get(f"{RUIAN}/1/query", {"geometry": obalka(bbox), "geometryType": "esriGeometryEnvelope",
                                 "inSR": 5514, "outSR": 5514, "outFields": "cislodomovni,adresa", "f": "json"}).get("features", [])
    body = []
    for a in f:
        x = round((a["geometry"]["x"] - bbox[0]) / (bbox[2] - bbox[0]) * px)
        y = round((bbox[3] - a["geometry"]["y"]) / (bbox[3] - bbox[1]) * px)
        evidencni = a["attributes"].get("adresa", "").startswith("č.ev.")   # chaty: číslo evidenční místo popisného
        body.append((evidencni, a["attributes"]["cislodomovni"], x, y))
    if not body:
        return print("adresní body RÚIAN: žádné v obrázku")
    body = [(("ev." if ev else "") + str(c), x, y) for ev, c, x, y in sorted(body)]   # nejdřív čp., pak č. ev.
    print("adresní body RÚIAN (dnešní čp., pixel x,y v obrázku):", ", ".join(f"{c} {x},{y}" for c, x, y in body))
    mg = (shutil.which("magick") or next(iter(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe")), None)
          or (os.name != "nt" and shutil.which("convert")))   # ImageMagick 6 bez magick; na Windows je convert.exe jiný program
    if not mg:
        return print("(bez ImageMagicku body nezakreslím, polohy výše)")
    kresba = []
    for c, x, y in body:
        kresba += ["-fill", "blue", "-draw", f"circle {x},{y} {x + 5},{y}",
                   "-stroke", "white", "-strokewidth", "4", "-annotate", f"+{x + 8}+{y - 6}", c,
                   "-stroke", "none", "-annotate", f"+{x + 8}+{y - 6}", c]
    cil = os.path.splitext(out)[0] + "_adresy.jpg"
    if subprocess.run([mg, out, "-pointsize", "22"] + kresba + [cil]).returncode:
        return print("(ImageMagick body nezakreslil, polohy výše)")
    print(f"{cil} – modře dnešní čísla domů (pracovní obrázek; vrstva sedí na dnešní mapu zpravidla do pár metrů)")


def lms(m):
    """Ročníky leteckých měřických snímků nad místem (katalog, žádné obrázky)."""
    x, y = mista.sjtsk(*mista.stred(m))
    d = archiv("LMS_1930_40_50_60s/ImageServer/query", {
        "geometry": json.dumps({"x": x, "y": y, "spatialReference": {"wkid": 5514}}), "geometryType": "esriGeometryPoint",
        "spatialRel": "esriSpatialRelIntersects", "outFields": "Name", "returnGeometry": "false", "f": "json"})
    rocniky = {}
    for f in d.get("features", []):   # Name = mise.rok.řada.snímek, např. WMSA08.1949.TSVI81.04066
        rocniky.setdefault(f["attributes"]["Name"].split(".")[1], []).append(f["attributes"]["Name"])
    if not rocniky:
        return print("letecké měřické snímky: místo nepokrývají")
    for rok, snimky in sorted(rocniky.items()):
        print(f"{rok}: {len(snimky)}× ({', '.join(sorted(snimky)[:3])}{', …' if len(snimky) > 3 else ''})")
    print(f"Prohlédni v aplikaci: {REFERER}?start=lms (snímky jen prohlížet a popsat, výřez do výstupu ne)")


# vrstva kladu → (popis, jak z atributů poskládat části názvů rastrů ve službě nonstable)
RADY = {
    16: ("otisk katastrální mapy",   # klad „c0131-1“, rastr „B3_3C_131-1__2_25“
         lambda a: [f"{a['SIGN']}_{re.sub(r'^c0*', '', a['AEC_CM'])}__{a['cislo_sloz']}_{a['list']}"]),
    7: ("mapa evidence nemovitostí", lambda a: [a["SIGN_NOMEN"]]),   # Čechy
    8: ("mapa evidence nemovitostí", lambda a: [a["SIGN_NOMEN"]]),   # Morava
    9: ("mapa kultur", lambda a: [a["SKENY"].split("|")[0]]),
    10: ("Státní mapa 1 : 5000", lambda a: [a["NOMEN"]]),
    # III. vojenské mapování: sekce 1 : 25 000 (klad „4453-4“, rastry „D1_21__4453-5“ a „-6“ = vydání podle KLD25no)
    5: ("III. vojenské mapování",
        lambda a: [f"D1_21__{a['KLD75']}-{n}" for n in a["KLD25no"].split("|")]),
    6: ("III. vojenské mapování", lambda a: [a["SIGN_NOMEN"]]),   # rastry „D1_22__4453_01“ … = vydání
}
BEZ_RASTRU = {0, 3, 11}   # letecké snímky (lms), stabilní katastr (listy), sbírka map celých zemí


def rady(m):
    d = klady(*mista.stred(m))
    drobne = set()   # malá měřítka (ZM, vojenské, generální) – k domu nic, jen zmínit
    for r in d.get("results", []):
        lid, a = r["layerId"], {k: v for k, v in r["attributes"].items() if v and str(v).strip() not in ("", "Null")}
        if lid in BEZ_RASTRU:
            continue
        if lid not in RADY:
            drobne.add(r["layerName"].replace("archiv_nespojene_", "").replace("_klady", ""))
            continue
        nazev = (a.get("NAZEV_JEDNOTKY") or a.get("NML") or a.get("MAPNAME") or "").strip()
        roky = a.get("ROKY") or a.get("ROZP_DAT") or a.get("DAT_OD") or a.get("meritko") or ""
        print(f"{RADY[lid][0]}: {nazev} {roky}".rstrip())
        try:
            vzory = RADY[lid][1](a)
        except KeyError:   # prázdné pole (list bez skenu) výš vypadlo z atributů
            print("   → list není naskenovaný (prohlédni v aplikaci)")
            continue
        nalez = [f"{f['attributes']['OBJECTID']} {f['attributes']['Name']}" for vzor in vzory for f in archiv(
            "archiv_nespojene_nonstable/ImageServer/query", {
                "where": f"Name LIKE '%{vzor.replace(chr(39), '')}%'", "outFields": "OBJECTID,Name",
                "returnGeometry": "false", "f": "json"}).get("features", [])]
        print("   → export nonstable " + (" | ".join(nalez[:8]) + (f" | … ({len(nalez)})" if len(nalez) > 8 else "")
                                         if nalez else f"rastr „{' | '.join(vzory)}“ nenalezen"))
    if drobne:
        print("malá měřítka (rastry hledej v aplikaci): " + ", ".join(sorted(drobne)))
    print("Stabilní katastr: listy; letecké snímky: lms.")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "listy":
        listy(a[1])
    elif len(a) >= 3 and a[0] == "rastry":
        rastry(a[1], a[2])
    elif len(a) >= 4 and a[0] == "export":
        export(*a[1:6])
    elif len(a) >= 4 and a[0] == "prehled":
        prehled(*a[1:5])
    elif len(a) >= 4 and a[0] == "mapa":
        mapa(*a[1:6])
    elif len(a) >= 2 and a[0] == "rady":
        rady(a[1])
    elif len(a) >= 2 and a[0] == "lms":
        lms(a[1])
    else:
        sys.exit(__doc__)
