#!/usr/bin/env python3
"""Staré fotky, pohlednice, kresby a mapy obce z Wikimedia Commons, každý soubor s licencí, autorem a datem.

Kategorii obce najde přes Wikidata (vlastnost „kategorie na Commons“), stejnojmenné obce rozliší polohou z RÚIAN.
Projde strom kategorií (nejdřív historické: History, Postcards, Old…, desetiletí 1900s–1950s), vynechá lidi,
silnice, zastávky, znaky a přírodu, a nechá soubory datované do roku DO (výchozí 1960) a všechny soubory
z historických kategorií (pohlednice bývají bez data).

Použití:
  commons.py "<obec>" [od-do] [--kategorie "Název"] [--kategorii 60]   – rok | soubor | kategorie | licence | odkaz
  commons.py "<obec>" --adresa "Panská 11" [--adresa "Školní"] [--cp 183]
      ve městě: projde i kategorie domu a ulic („Panská 11 (Olomouc)“, „Panská (Olomouc)“, „Žerotínovo náměstí
      (Olomouc)“) a vypíše soubory s domem (podle čísla v názvu, „čp. 183“) bez ohledu na rok – v kategorii obce
      je ulice hluboko a 60 kategorií na ni nedojde.
  commons.py detail "<soubor>"                                  – popis, datum, autor, licence, obrázek, citace
Commons přijímá jen volné licence: obrázek smí i do placeného výstupu, u CC BY a CC BY-SA s autorem a licencí.
Větší města mají stovky kategorií: nástroj jich projde 60 (asi minuta), víc --kategorii.

Původ: převzato z vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/commons.py), commit 32bef07; úprava: slusne.py se u nás zapíná importem (bez instaluj())."""
import argparse, html, http.client, json, os, re, sys, time, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne   # společný limit rychlosti (slusne.py; u nás se zapíná importem)
from vzdalenost import km

COMMONS = "https://commons.wikimedia.org"
WIKIDATA = "https://www.wikidata.org/w/api.php"
DO = 1960
MAX_KATEGORII = 60
HLOUBKA = 3
NEJDAL_KM = 5          # položka Wikidat dál od středu obce z RÚIAN je jiná stejnojmenná obec
OBRAZEK = re.compile(r"\.(jpe?g|png|tiff?|gif|svg|webp|djvu|pdf)$", re.I)   # ne zvuk a video
METADATA = "DateTimeOriginal|LicenseShortName|Artist|ImageDescription|ObjectName|Credit|LicenseUrl"
HISTORICKA = re.compile(r"\bhistor|\bold\b|\bformer\b|postcards?|\b1[89][0-6]0s\b|\b1[89]th[- ]century|"
                        r"\bin 1[89]\d\d\b|daguerreotyp|lithograph|\bmaps? of\b", re.I)
VYNECHAT = re.compile(r"\bpeople (of|from)|\bnamed after|bus stops|\broads?\b|\broute|coats of arms|\bflags? of|"
                      r"\bnature of|natural monuments?|\bsports?\b|\bvehicles?\b|\bplants\b|\banimals\b|"
                      r"\bwiki ?loves|\bquality images|\bsound|\baudio|\bvideo", re.I)


def _verze():
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "VERZE"), encoding="utf-8") as f:
            return f.read().strip() or "0"
    except OSError:
        return "0"


# Wikimedia chce od klientů API identifikaci s kontaktem (policy „User-Agent“); bez ní vrací 403. Kontakt je adresa
# repozitáře, ne osobní e-mail. Platí jen pro Wikimedii (ostatní portály se představují přes slusne.UA).
UA_WIKIMEDIA = f"rodokmen-skill/{_verze()} (https://github.com/vmi43/rodokmen-skill; genealogical tool, rate-limited)"


def api(adresa, **parametry):
    parametry.update(format="json", formatversion=2)
    req = urllib.request.Request(f"{adresa}?{urllib.parse.urlencode(parametry)}", headers={"User-Agent": UA_WIKIMEDIA})
    for pokus in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except (http.client.RemoteDisconnected, http.client.IncompleteRead):
            if pokus == 2:   # Wikimedie občas zavře spojení; jeden pokus znovu (zpomalení hlídá slusne), pak ať chyba vyjde
                raise
            time.sleep(5)


ZKRATKY = ((re.compile(r"\bnám\.?(?=\s|$)", re.I), "náměstí"), (re.compile(r"\btř\.?(?=\s|$)", re.I), "třída"))


def adresa_z(text):
    """„Panská 11“ → („Panská“, „11“); „Žerotínovo nám.“ → („Žerotínovo náměstí“, None)."""
    text = re.sub(r"\s+", " ", text).strip().strip(",")
    for vzor, cele in ZKRATKY:
        text = vzor.sub(cele, text)
    m = re.fullmatch(r"(.+?)\s+(\d+[a-zA-Z]?)(?:/\d+[a-zA-Z]?)?", text)
    return (m.group(1), m.group(2)) if m else (text, None)


def kategorie_adres(obec, adresy):
    """Kategorie domů a ulic na Commons, které existují: vzor „Ulice číslo (Obec)“ a „Ulice (Obec)“ (Olomouc 10. 11. 2026),
    co neexistuje, dohledá hledáním v názvech kategorií. Vrací [(kategorie, druh)], dům napřed."""
    kandidati = []
    for ulice, cislo in adresy:
        if cislo:
            kandidati.append((f"Category:{ulice} {cislo} ({obec})", "dům"))
        kandidati.append((f"Category:{ulice} ({obec})", "ulice"))
    stranky = api(f"{COMMONS}/w/api.php", action="query", titles="|".join(k for k, _ in kandidati))["query"]["pages"]
    existuji = {p["title"] for p in stranky if not p.get("missing")}
    nalez = [(k, d) for k, d in kandidati if k in existuji]
    for ulice, _ in adresy:
        if not any(k.startswith(f"Category:{ulice} ") for k, _ in nalez):   # jiný tvar názvu („Panská ulice, Olomouc“)
            r = api(f"{COMMONS}/w/api.php", action="query", list="search", srnamespace=14, srlimit=10,
                    srsearch=f'intitle:"{ulice}" intitle:"{obec}"')
            nalez += [(x["title"], "ulice?") for x in r["query"]["search"]
                      if x["title"].removeprefix("Category:").startswith(ulice) and (x["title"], "ulice?") not in nalez]
    return nalez


def soubory_domu(nalez, adresy, cp=None):
    """Soubory, v jejichž názvu je dům: „Panská 11“ nebo „čp. 183“, „č.p.183“."""
    vzory = [rf"\b{re.escape(u)}\W+{c}(?!\d)" for u, c in adresy if c]
    if cp:
        vzory.append(rf"\bč\.?\s*p\.?\s*{cp}(?!\d)")
    if not vzory:
        return []
    vzor = re.compile("|".join(vzory), re.I)
    return sorted(((rok(info), soubor, kategorie, info) for soubor, (kategorie, info) in nalez.items() if vzor.search(soubor)),
                  key=lambda x: (x[0] or 9999, x[1]))


def kategorie_obce(obec, stredy):
    """Kategorie Commons obce z Wikidat: položka s tímto názvem a vlastností P373 do NEJDAL_KM od středu obce z RÚIAN.
    stredy = [(název podle RÚIAN, lat, lon)]; víc stejnojmenných obcí nebo žádný střed a víc položek = skončí se seznamem.
    Vrací (kategorie, popis položky)."""
    nalez = api(WIKIDATA, action="wbsearchentities", search=obec, language="cs", type="item", limit=10)["search"]
    ids = [x["id"] for x in nalez if (x.get("label") or "").lower() == obec.lower()]
    if not ids:
        sys.exit(f"Wikidata „{obec}“ neznají. Zkus --kategorie s názvem kategorie z commons.wikimedia.org.")
    polozky = api(WIKIDATA, action="wbgetentities", ids="|".join(ids), props="claims|descriptions", languages="cs|en")["entities"]
    kandidati = []   # (km k nejbližšímu středu, kategorie, popis položky, nejbližší obec podle RÚIAN)
    for q, e in polozky.items():
        kat = hodnota(e, "P373")
        if kat:
            vzdalenost, obec_ruian = nejblizsi_stred(hodnota(e, "P625"), stredy)
            kandidati.append((vzdalenost, kat, popis_polozky(q, e), obec_ruian))
    if not kandidati:
        sys.exit(f"Obec „{obec}“ nemá na Wikidatech kategorii Commons. Zkus --kategorie, nebo na Commons nic není.")
    v_obci = [k for k in kandidati if k[0] is not None and k[0] <= NEJDAL_KM]
    if len(stredy) == 1 and v_obci:
        return min(v_obci)[1:3]
    if not stredy and len(kandidati) == 1:
        return kandidati[0][1:3]
    sys.exit(f"Kategorii obce „{obec}“ nejde vybrat jednoznačně ({len(stredy)} obcí tohoto jména v RÚIAN), zadej ji --kategorie:\n"
             + "\n".join(f"  {kat}   ({popis}" + (f"; {v:.0f} km od {nazev}" if v is not None else "") + ")"
                          for v, kat, popis, nazev in kandidati))


def nejblizsi_stred(poloha, stredy):
    """(km, název) nejbližšího středu obce z RÚIAN k poloze položky Wikidat; bez polohy nebo středů (None, "")."""
    if not poloha or not stredy:
        return None, ""
    return min((km(lat, lon, poloha["latitude"], poloha["longitude"]), nazev) for nazev, lat, lon in stredy)


def popis_polozky(q, polozka):
    popisy = polozka.get("descriptions", {})
    return f"{q} {(popisy.get('cs') or popisy.get('en') or {}).get('value', '')}".strip()


def hodnota(polozka, vlastnost):
    for c in polozka.get("claims", {}).get(vlastnost, []):
        v = c["mainsnak"].get("datavalue", {}).get("value")
        if v:
            return v
    return None


def clenove(kategorie):
    """Podkategorie a soubory kategorie (soubory i s metadaty), přes všechny stránky odpovědi."""
    podkategorie, soubory, pokracovani = [], [], {}
    while True:
        r = api(f"{COMMONS}/w/api.php", action="query", generator="categorymembers", gcmtitle=kategorie,
                gcmtype="file|subcat", gcmlimit=100, prop="imageinfo", iiprop="extmetadata|url",
                iiextmetadatafilter=METADATA, **pokracovani)
        for p in r.get("query", {}).get("pages", []):
            if p["ns"] == 14:
                podkategorie.append(p["title"])
            elif p["ns"] == 6 and p.get("imageinfo") and OBRAZEK.search(p["title"]):
                soubory.append((p["title"], p["imageinfo"][0]))
        if "continue" not in r:
            return podkategorie, soubory
        pokracovani = r["continue"]


def projdi(koreny, nejvic=MAX_KATEGORII):
    """{soubor: (kategorie, imageinfo)}; kořeny v pořadí (dům, ulice, obec), do šířky, podkategorie historických
    kategorií napřed. Vrací i počet prošlých kategorií a zda zbyly neprojité."""
    fronta, videno, nalez = [(k, 0, bool(HISTORICKA.search(k))) for k in koreny], set(), {}
    while fronta and len(videno) < nejvic:
        kategorie, hloubka, historicka = fronta.pop(0)
        if kategorie in videno:
            continue
        videno.add(kategorie)
        if len(videno) % 10 == 0:
            print(f"… prošlo {len(videno)} kategorií", file=sys.stderr)
        podkategorie, soubory = clenove(kategorie)
        for soubor, info in soubory:
            nalez.setdefault(soubor, (kategorie, info))
        if hloubka < HLOUBKA:
            fronta += [(k, hloubka + 1, historicka or bool(HISTORICKA.search(k))) for k in podkategorie if not VYNECHAT.search(k)]
            fronta.sort(key=lambda k: not k[2])   # stabilní řazení: historické napřed, jinak do šířky
    return nalez, len(videno), bool(fronta)


def meta(info, klic):
    """Hodnota extmetadata bez HTML značek."""
    v = (info.get("extmetadata", {}).get(klic) or {}).get("value", "")
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(v)))
    text = re.sub(r"\bdate QS:\S+", "", text)            # strojový zápis data ze šablony {{other date}}
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"^(.+?) \1$", r"\1", text)             # skrytý popisek šablony zopakuje text („Unknown author Unknown author“)


def rok(info):
    m = re.search(r"\b(1[5-9]\d\d|20\d\d)\b", meta(info, "DateTimeOriginal"))
    return int(m.group(1)) if m else None


def vyber(nalez, roky=(0, DO)):
    """[(rok nebo None, soubor, kategorie, info)]: datované v rozsahu roky, nedatované jen přímo z historické kategorie
    (v podkategorii historické kategorie bývají i dnešní fotky)."""
    vysledek = []
    for soubor, (kategorie, info) in nalez.items():
        r = rok(info)
        if (r is not None and roky[0] <= r <= roky[1]) or (r is None and HISTORICKA.search(kategorie)):
            vysledek.append((r, soubor, kategorie, info))
    return sorted(vysledek, key=lambda x: (x[0] or 9999, x[1]))


def odkaz(soubor):
    return f"{COMMONS}/wiki/{urllib.parse.quote(soubor.replace(' ', '_'), safe=':/,()')}"


def radek(r, soubor, kategorie, info):
    casti = [str(r or "?"), soubor.removeprefix("File:"), kategorie.removeprefix("Category:"),
             meta(info, "LicenseShortName"), odkaz(soubor)]
    return "  " + " | ".join(c for c in casti if c)


def smi_obrazek(licence):
    if re.search(r"public domain|\bpd\b|cc0|pdm", licence, re.I):
        return "ano, volné dílo (uveďte zdroj Wikimedia Commons)"
    return f"ano, s autorem a licencí ({licence or 'licence u souboru'})"


def citace(soubor, info):
    casti = [meta(info, "Artist"), meta(info, "ObjectName") or soubor.removeprefix("File:"),
             meta(info, "DateTimeOriginal"), meta(info, "LicenseShortName"), f"Wikimedia Commons, {odkaz(soubor)}"]
    return ", ".join(c for c in casti if c)


def detail(soubor):
    if not soubor.startswith("File:"):
        soubor = "File:" + soubor
    stranky = api(f"{COMMONS}/w/api.php", action="query", titles=soubor, prop="imageinfo",
                  iiprop="extmetadata|url", iiextmetadatafilter=METADATA)["query"]["pages"]
    if not stranky or stranky[0].get("missing") or not stranky[0].get("imageinfo"):
        sys.exit(f"Soubor {soubor} na Wikimedia Commons není.")
    info = stranky[0]["imageinfo"][0]
    radky = [("Název", meta(info, "ObjectName")), ("Popis", meta(info, "ImageDescription")[:600]),
             ("Datum", meta(info, "DateTimeOriginal")), ("Autor", meta(info, "Artist")), ("Zdroj", meta(info, "Credit")[:300]),
             ("Licence", " ".join(x for x in (meta(info, "LicenseShortName"), meta(info, "LicenseUrl")) if x)),
             ("Odkaz", odkaz(soubor)), ("Obrázek", (info.get("url") or "").split("?")[0]), ("Citace", citace(soubor, info)),
             ("Obrázek do výstupu", smi_obrazek(meta(info, "LicenseShortName")))]
    return [f"{n}: {v}" for n, v in radky if v]


def roky_z(text):
    m = re.fullmatch(r"(\d{3,4})-(\d{3,4})", text or "")
    if not m:
        sys.exit(f"Roky zadej jako 1850-1950, ne „{text}“")
    return int(m.group(1)), int(m.group(2))


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    if argv[1] == "detail":
        if len(argv) < 3:
            sys.exit('Použití: commons.py detail "<soubor>" (název z výpisu)')
        print("\n".join(detail(argv[2])))
        return
    p = argparse.ArgumentParser(prog="commons.py", usage=__doc__)
    p.add_argument("obec")
    p.add_argument("roky", nargs="?")
    p.add_argument("--kategorie")
    p.add_argument("--kategorii", type=int, default=MAX_KATEGORII)
    p.add_argument("--adresa", action="append", default=[])
    p.add_argument("--cp")
    a = p.parse_args(argv[1:])
    roky = roky_z(a.roky) if a.roky else (0, DO)
    adresy = [adresa_z(x) for x in a.adresa]
    koreny = []
    if adresy:
        koreny = kategorie_adres(a.obec, adresy)
        print("Kategorie domu a ulic: " + ("; ".join(f"{k} ({d})" for k, d in koreny) if koreny else
              "žádná – zkus název ulice jako na Commons, nebo --kategorie"))
    if a.kategorie:
        kategorie, popis = "Category:" + a.kategorie.removeprefix("Category:"), "zadaná ručně"
    else:
        import mista   # střed obce z RÚIAN; jen v projektu (mista.py jinde skončí)
        kategorie, popis = kategorie_obce(a.obec, mista.obec_stred(a.obec))
        kategorie = "Category:" + kategorie
    print(f"Kategorie: {kategorie} ({popis}), {odkaz(kategorie)}")
    nalez, prosel, zbylo = projdi([k for k, _ in koreny] + [kategorie], a.kategorii)
    if adresy or a.cp:
        dum = soubory_domu(nalez, adresy, a.cp)
        print(f"\nSoubory s domem v názvu (všechny roky): {len(dum)}")
        print("\n".join(radek(*v) for v in dum) if dum else "  žádné")
        print()
    vybrane = vyber(nalez, roky)
    print(f"Prošlé kategorie: {prosel}, soubory: {len(nalez)}"
          f"{f' (další kategorie vynechány, víc: --kategorii {2 * a.kategorii})' if zbylo else ''}.\n"
          f"Z let {roky[0] or 'do'}{'–' if roky[0] else ' '}{roky[1]} a nedatované z historických kategorií: {len(vybrane)}")
    if vybrane:
        print("\n".join(radek(*v) for v in vybrane))
    else:
        print("Nic starého. Novější fotky ukáže odkaz na kategorii.")
    print("\nKategorie u souboru ukáže, co na něm je (muzeum, kostel, osoba); rok je datum vzniku podle Commons.\n"
          "Obrázek smí do výstupu i za peníze, u CC BY a CC BY-SA s autorem a licencí (commons.py detail \"<soubor>\").")


if __name__ == "__main__":
    main(sys.argv)
