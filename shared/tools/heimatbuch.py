#!/usr/bin/env python3
"""Heimatbücher a jiná německá literatura o obci z katalogu Německé národní knihovny (DNB).

Vysídlení Němci po roce 1945 vydali ke stovkám obcí Čech, Moravy a Slezska Heimatbücher, Ortschroniken a seznamy
domů s majiteli k roku 1945 (Häuserverzeichnis, Hauseigentümer), často s fotkami statků. České knihovny je mají
málokdy; DNB má skoro všechny, protože dostává povinný výtisk.

Použití:
  heimatbuch.py "<německý název>" ["<další název>" …]   – rok | název | autor | vydavatel | odkaz
Hledá název obce v názvu knihy (Bleiswedel, Prachatitz). Když je nálezů moc (velké město, stejné jméno v Německu),
nechá jen knihy se slovy Heimat, Chronik, Geschichte apod. Řádky s ⌂ mají v názvu domy, majitele nebo obyvatele.
Katalog DNB (SRU) je zdarma a bez registrace, metadata CC0.

Původ: převzato z vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/heimatbuch.py), commit 5c1715b; úprava: slusne.py se u nás zapíná importem (bez instaluj())."""
import os, re, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne   # noqa: E402 – společný limit rychlosti (slusne.py; u nás se zapíná importem)

SRU = "https://services.dnb.de/sru/dnb"
ODKAZ = "https://d-nb.info/"
NEJVIC = 100
BEZ_FILTRU = 40   # do tolika nálezů vypsat vše, nad to jen místopisné tituly
MISTOPIS = ("Heimat*", "Chronik", "Geschichte", "Ortsgeschichte", "Dorf*", "Gemeinde", "Kirchspiel", "Pfarr*",
            "Häuser*", "Haus*", "Hof*", "Höfe", "Familien*", "Einwohner*", "Bewohner*", "Gedenk*", "Erinnerung*")
DOMY = re.compile(r"(?i)häuser|haus(?:eigentümer|besitzer|geschichte|chronik)|hof(?:besitzer|geschichte)|höfe|"
                  r"anwesen|bewohner|einwohner|familien|besitzer")
NS = {"dc": "http://purl.org/dc/elements/1.1/", "srw": "http://www.loc.gov/zing/srw/",
      "oai": "http://www.openarchives.org/OAI/2.0/oai_dc/"}
TYP = "{http://www.w3.org/2001/XMLSchema-instance}type"


def dotaz(nazvy, jen_mistopis=False):
    """CQL pro SRU DNB: některý z názvů v názvu knihy, volitelně s místopisným slovem."""
    q = " or ".join(f'tit="{n}"' for n in nazvy)
    if jen_mistopis:
        q = f"({q}) and ({' or '.join(f'tit={s}' for s in MISTOPIS)})"
    return q


def sru(q):
    parametry = {"version": "1.1", "operation": "searchRetrieve", "query": q, "recordSchema": "oai_dc",
                 "maximumRecords": NEJVIC}
    with urllib.request.urlopen(f"{SRU}?{urllib.parse.urlencode(parametry)}", timeout=60) as r:
        return r.read()


def knihy_z_odpovedi(xml):
    """(záznamy jako slovníky, celkem podle DNB)."""
    koren = ET.fromstring(xml)
    celkem = int(koren.findtext("srw:numberOfRecords", "0", NS))
    vysledek = []
    for dc in koren.iterfind(".//oai:dc", NS):
        idn = next((i.text for i in dc.findall("dc:identifier", NS) if i.get(TYP) == "dnb:IDN"), "")
        vysledek.append({"nazev": dc.findtext("dc:title", "", NS), "autor": dc.findtext("dc:creator", "", NS),
                         "vydavatel": dc.findtext("dc:publisher", "", NS), "rok": dc.findtext("dc:date", "", NS),
                         "idn": idn})
    return vysledek, celkem


def hledej(nazvy):
    """(knihy seřazené podle roku, celkem, jen místopisné?)."""
    knihy, celkem = knihy_z_odpovedi(sru(dotaz(nazvy)))
    jen_mistopis = celkem > BEZ_FILTRU
    if jen_mistopis:
        knihy, celkem = knihy_z_odpovedi(sru(dotaz(nazvy, jen_mistopis=True)))
    return sorted(knihy, key=lambda k: k["rok"] or "9999"), celkem, jen_mistopis


def radek(k):
    znacka = "⌂" if DOMY.search(k["nazev"]) else " "
    autor = re.sub(r"\s*\[[^\]]*\]", "", k["autor"])
    return " | ".join([f"{znacka} {k['rok'] or '?':>4}", k["nazev"], autor, k["vydavatel"],
                       ODKAZ + k["idn"] if k["idn"] else ""])


def kde_pujcit(nazvy):
    hledani = urllib.parse.quote(nazvy[0])
    return (f"Kde půjčit: Knihovny.cz (https://www.knihovny.cz/Search/Results?lookfor={hledani}, otevře uživatel), "
            "jinak meziknihovní výpůjčka z Německa (MVS v místní knihovně) nebo Sudetendeutsche Bibliothek "
            "v Mnichově. Údaje z knihy (domy, majitelé, události) s citací do výstupu ano, fotky a delší text jen se "
            "souhlasem vydavatele (Heimatkreis).")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.exit(__doc__)
    knihy, celkem, jen_mistopis = hledej(argv)
    if not knihy:
        print(f"DNB nemá knihu s „{' / '.join(argv)}“ v názvu. Zkus jiný tvar německého názvu nebo okres "
              "(Heimatkreis) a farnost.")
        return
    print(f"Nalezeno v DNB: {celkem}{' (jen místopisné tituly)' if jen_mistopis else ''}"
          f"{f', vypsáno {len(knihy)}' if celkem > len(knihy) else ''}")
    for k in knihy:
        print(radek(k))
    print(kde_pujcit(argv))


if __name__ == "__main__":
    main(sys.argv[1:])
