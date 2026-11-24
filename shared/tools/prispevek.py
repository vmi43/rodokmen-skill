#!/usr/bin/env python3
"""Příspěvek do komunitního indexu matrik (pe-pan/matriky-index): z data/indexy/ vybere, co smí ven, a po souhlasu uživatele
to pošle přes sběrnou schránku Mapy matrik. Viz reference/sdileni.md, „Odesílání“.

Použití (z kořene projektu `python3 -I tools/prispevek.py …`):
  prispevek.py navrh                 vyrobí pracovni/sdileni/prispevek.json a vypíše, co by odešlo (kolik řádků, z kterých knih,
                                     ukázku) a co se vynechalo a proč. NIC NEODCHÁZÍ. Vypíše otisk dávky.
  prispevek.py souhlas ano [jméno]   uživatel souhlasí s odesíláním; bez jména anonymně (v indexu jen model a datum). Jméno nebo
                                     přezdívka se zveřejní ve sloupci `cetl` a v historii gitu cizího repozitáře NAVŽDY.
  prispevek.py souhlas ne            souhlas odvolá (už odeslané se tím nevrátí)
  prispevek.py odeslat <otisk>       pošle dávku, jejíž otisk uživatel viděl v `navrh`; jen se souhlasem; nesedí-li otisk
                                     (data se mezitím změnila), nepošle nic

Co jde ven: jen zápisy N, O a Z přečtené z knih podporovaných archivů (Porta fontium, eBadatelna SOA Praha, AHMP), starší
zákonných lhůt (narození 100 let, sňatky a úmrtí 75 let), s datem a s údajem `cetl` (model/effort). Nejde ven: rejstříky
(typ I), řádky mladší lhůt, bez data, z jiných archivů, řádky se slovy o příbuzenství a ztotožnění, výřezy, snímky, cokoli
jiného z projektu. Jen přidává: co už bylo odesláno (`data/sdileni.json`), se neposílá znovu.
Příspěvek jde přes cizí službu: sběrnou schránku Mapy matrik (Cloudflare Worker, provozuje autor Mapy matrik), která z něj
založí pull request do veřejného repozitáře indexu (licence dat CC BY 4.0). Přispěvatele rozlišuje pseudonym, který schránka
spočítá z náhodného klíče; klíč se vyrobí jednou do pracovni/sdileni/klic.txt (mimo git a web) a posílá se schránce s příspěvkem.
"""
import datetime, hashlib, json, os, re, secrets, sys, urllib.error, urllib.request
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda (tools/slusne.py)
import sdileni  # noqa: E402 – kniha_z_url (jen čtecí část, sama nic neodesílá)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
NASTAVENI = os.path.join(DATA, "sdileni.json")
SLOZKA = os.path.join(ROOT, "pracovni", "sdileni")
SCHRANKA = "https://mapa-matrik-schranka.schranka.workers.dev"
LHUTA = {"N": 100, "O": 75, "Z": 75}
SLOUPCE = ["snimek", "datum", "typ", "obec", "osoby", "ostatni", "jistota", "cetl", "odkaz", "strana", "kniha"]
CETL = re.compile(r"[a-z][a-z0-9.-]+/[a-z0-9]+ \d{4}-\d{2}-\d{2}")
PRIBUZENSTVI = re.compile(r"(?i)\b(můj|moje|moji|náš|naše|prapra\w*|praděd\w*|prababi\w*|předek|předci|předka|dědeček|dědečk\w*|babička|babičk\w*"
                          r"|strýc\w*|teta|tety|bratranec|bratranc\w*|sestřenic\w*|rodokmen\w*|ztotožn\w*|identick\w*|pravděpodobně (je|byl))\b")
MAX_ZAPISU, MAX_KNIH = 200, 15   # limity schránky na jedno odeslání


def nastaveni():
    try:
        n = json.load(open(NASTAVENI, encoding="utf-8"))
    except (OSError, ValueError):
        n = {}
    n.setdefault("souhlas", "ne"); n.setdefault("jmeno", ""); n.setdefault("odeslano", [])
    return n


def uloz_nastaveni(n):
    os.makedirs(DATA, exist_ok=True)
    tmp = NASTAVENI + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(n, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, NASTAVENI)


def otisk_radku(z):
    return hashlib.sha256("\t".join(str(z[k]) for k in ("archiv", "kniha", "snimek", "datum", "typ", "osoby")).encode("utf-8")).hexdigest()[:16]


def cti_index(cesta):
    with open(cesta, encoding="utf-8") as f:
        radky = [r.rstrip("\n").split("\t") for r in f if r.strip()]
    if not radky or radky[0] != SLOUPCE:
        return None
    return [dict(zip(SLOUPCE, r + [""] * (len(SLOUPCE) - len(r)))) for r in radky[1:]]


def vyber(dnes=None):
    """(zápisy k odeslání seřazené, vynechané {důvod: počet}, odeslané už dříve) podle data/indexy/ a data/svazky.json."""
    dnes = dnes or datetime.date.today()
    n = nastaveni()
    uz = set(n["odeslano"])
    try:
        sv = json.load(open(os.path.join(DATA, "svazky.json"), encoding="utf-8"))
    except (OSError, ValueError):
        sv = {}
    ven, vynech = [], {}

    def nic(duvod):
        vynech[duvod] = vynech.get(duvod, 0) + 1

    adr = os.path.join(DATA, "indexy")
    for jm in sorted(os.listdir(adr)) if os.path.isdir(adr) else []:
        if not jm.endswith(".tsv"):
            continue
        klic = jm[:-4]
        radky = cti_index(os.path.join(adr, jm))
        if radky is None:
            nic(f"{klic}: soubor má špatné záhlaví")
            continue
        s = sv.get(klic) or {}
        k = sdileni.kniha_z_url(s.get("url"))
        for r in radky:
            if r["typ"] not in LHUTA:
                nic("rejstřík (typ I) nebo jiný typ než N, O, Z")
                continue
            if not k:
                nic("archiv nebo kniha, kterou komunitní index nepodporuje (Porta fontium, eBadatelna SOA Praha, AHMP)")
                continue
            rok = re.match(r"\d{4}", r["datum"])
            if not rok:
                nic("řádek bez data")
                continue
            if int(rok[0]) >= dnes.year - LHUTA[r["typ"]]:
                nic("mladší zákonné lhůty (narození 100 let, sňatky a úmrtí 75 let)")
                continue
            if not CETL.search(r["cetl"]):
                nic("chybí sloupec cetl ve tvaru model/effort RRRR-MM-DD")
                continue
            if PRIBUZENSTVI.search(r["osoby"] + " " + r["ostatni"]):
                nic("slovo o příbuzenství nebo ztotožnění v osoby/ostatni (do indexu patří jen doslovný přepis; oprav text řádku)")
                continue
            ostatni = r["ostatni"] + (("; " if r["ostatni"] else "") + f"str. {r['strana']}" if r["strana"] else "")
            z = dict(archiv=k[1], kniha=k[2], snimek=r["snimek"], datum=r["datum"], typ=r["typ"], obec=r["obec"], osoby=r["osoby"],
                     ostatni=ostatni, jistota=r["jistota"], cetl=r["cetl"], nazev=(s.get("svazek") or "")[:200], url=s.get("url", ""))
            if otisk_radku(z) in uz:
                nic("už odesláno dříve")
                continue
            ven.append(z)
    return ven, vynech


def davka(zapisy, n):
    """Prvních MAX_ZAPISU řádků z nejvýš MAX_KNIH knih (limity schránky); jméno se přidá jen s výslovným souhlasem."""
    knihy, dav = [], []
    for z in zapisy:
        kk = (z["archiv"], z["kniha"])
        if kk not in knihy:
            if len(knihy) >= MAX_KNIH:
                continue
            knihy.append(kk)
        if len(dav) < MAX_ZAPISU:
            dav.append(dict(z, cetl=(f"{n['jmeno']} + " if n["jmeno"] else "") + z["cetl"] + " (z rodokmenu)"))
    return dav


def otisk_davky(dav):
    return hashlib.sha256(json.dumps(dav, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def navrh():
    n = nastaveni()
    zapisy, vynech = vyber()
    dav = davka(zapisy, n)
    os.makedirs(SLOZKA, exist_ok=True)
    cesta = os.path.join(SLOZKA, "prispevek.json")
    with open(cesta, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"zapisy": dav}, f, ensure_ascii=False, indent=1)
    print(f"K odeslání: {len(dav)} řádků ({len(zapisy)} způsobilých celkem; schránka bere najednou nejvýš {MAX_ZAPISU} řádků z {MAX_KNIH} knih)")
    po_knihach = {}
    for z in dav:
        po_knihach.setdefault(f"{z['archiv']}/{z['kniha']} {z['nazev']}", []).append(z)
    for kn, rr in po_knihach.items():
        print(f"  {kn}: {len(rr)} ř.")
    for z in dav[:5]:
        print(f"  např. sn. {z['snimek']} {z['datum']} {z['typ']} | {z['obec']} | {z['osoby']} | {z['ostatni']} | {z['jistota']} | {z['cetl']}")
    for d, c in sorted(vynech.items()):
        print(f"  vynecháno {c}×: {d}")
    print(f"Souhlas uživatele: {n['souhlas']}" + (f", jméno v cetl: {n['jmeno']}" if n["jmeno"] else ", anonymně (v cetl jen model a datum)"))
    if dav:
        print(f"Soubor k prohlédnutí: {os.path.relpath(cesta, ROOT)}\nOtisk dávky: {otisk_davky(dav)}\n"
              "Nic neodešlo. Ukaž to uživateli; odešle se až po jeho výslovném souhlasu: souhlas ano [jméno], pak odeslat <otisk>.")
    return 0


def souhlas(odpoved, jmeno=""):
    if odpoved not in ("ano", "ne"):
        sys.exit("souhlas ano [jméno] | souhlas ne")
    n = nastaveni()
    n["souhlas"], n["jmeno"] = odpoved, (jmeno.strip() if odpoved == "ano" else "")
    uloz_nastaveni(n)
    print("Souhlas zapsán: " + ("odesílání povoleno, " + (f"pod jménem „{n['jmeno']}“" if n["jmeno"] else "anonymně") if odpoved == "ano" else "odesílání zakázáno"))
    return 0


def klic_pseudonymu():
    cesta = os.path.join(SLOZKA, "klic.txt")
    try:
        k = open(cesta, encoding="utf-8").read().strip()
        if re.fullmatch(r"[A-Za-z0-9_-]{32,128}", k):
            return k
    except OSError:
        pass
    os.makedirs(SLOZKA, exist_ok=True)
    k = secrets.token_urlsafe(48)[:64]
    with open(cesta, "w", encoding="utf-8", newline="\n") as f:
        f.write(k + "\n")
    return k


def odeslat(otisk):
    n = nastaveni()
    if n["souhlas"] != "ano":
        sys.exit("Bez souhlasu uživatele nic neodesílám (prispevek.py souhlas ano [jméno]).")
    zapisy, _ = vyber()
    dav = davka(zapisy, n)
    if not dav:
        sys.exit("Není co odeslat.")
    if otisk_davky(dav) != otisk:
        sys.exit(f"Otisk dávky nesedí (teď {otisk_davky(dav)}): data se od `navrh` změnila. Spusť navrh znovu a ukaž ho uživateli.")
    telo = {"nastroj": "rodokmen/prispevek.py", "klic": klic_pseudonymu(), "zapisy": dav}
    slusne.pockej(SCHRANKA)
    req = urllib.request.Request(f"{SCHRANKA}/v1/prispevek", data=json.dumps(telo, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "User-Agent": slusne.UA}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            vysledek = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"Schránka odmítla příspěvek ({e.code}): {e.read().decode('utf-8', 'replace')[:300]}\nNic se nezapsalo jako odeslané.")
    except (OSError, ValueError) as e:
        sys.exit(f"Schránka neodpovídá nebo vrátila nesmysl ({e}): nic se nezapsalo jako odeslané, zkus to příště.")
    if vysledek.get("chyba"):
        sys.exit(f"Schránka: {vysledek['chyba']}\nNic se nezapsalo jako odeslané.")
    n["odeslano"] = sorted(set(n["odeslano"]) | {otisk_radku(z) for z in dav})
    uloz_nastaveni(n)
    print(f"Odesláno {len(dav)} řádků." + (f" Pull request do indexu: {vysledek['index']}" if vysledek.get("index") else " Schránka nevrátila odkaz na pull request."))
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if a[0] == "navrh":
        sys.exit(navrh())
    if a[0] == "souhlas" and len(a) >= 2:
        sys.exit(souhlas(a[1], " ".join(a[2:])))
    if a[0] == "odeslat" and len(a) == 2:
        sys.exit(odeslat(a[1]))
    sys.exit(__doc__)
