#!/usr/bin/env python3
"""Čtení z komunitní Mapy matrik a indexu matrik: co už někdo v knize našel, než ji otevřeš. Viz reference/sdileni.md.

Použití (z kořene projektu `python3 -I tools/sdileni.py …`):
  sdileni.py najdi <obec> [rok] [N|O|Z]   -> knihy z Mapy matrik s odhadem snímku a kolik zápisů z knihy už je v indexu
  sdileni.py kniha <klíč svazku | url>     -> orientační body knihy z mapy a zápisy z knihy, které už někdo přečetl

Jen čtení: nic se neodesílá a nic z projektu neodchází. Mapa (ondrnovy/mapa-matrik) a index (pe-pan/matriky-index) jsou
cizí otevřené projekty bez záruky provozu; nejsou-li dosažitelné, nástroj to řekne a postup jde dál. Zápis z indexu je
vodítko, ne doklad (většinu přečetl jazykový model): do dat patří jen to, co přečteš sám na snímku.
Dotazy jdou přes brzdu (tools/slusne.py) a ukládají se na den do ~/.cache/rodokmen_sdileni/.
Podporované archivy: SOA Plzeň (Porta fontium) a SOA Praha (eBadatelna) pro mapu, k tomu AHMP pro index.

Původ: převzato z vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/sdileni.py, commit 5c1715b; původně ondrnovy,
sarsonj/rodokmen-skill#185, MIT). Úprava: jen čtení (odesílání, souhlas a fronta bodů se nepřebraly, viz decisions.md),
brzda se volá podle našeho slusne.pockej(url).
"""
import http.client, json, os, re, sys, time, unicodedata, urllib.error, urllib.request
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda (tools/slusne.py)

MAPA = "https://ondrnovy.github.io/mapa-matrik/v1"
INDEX = "https://pe-pan.github.io/matriky-index"
CACHE = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.cache"), "rodokmen_sdileni")
DEN = 24 * 3600
ROOT = os.getcwd()
DATA = os.path.join(ROOT, "data")


# ---------- síť (přes brzdu) a mezipaměť ----------

def stahni(url, max_stari=DEN):
    """Text z url; uloží se na den. Bez sítě vrátí starší uloženou kopii, jinak None (404 = None)."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9._-]+", "_", url.split("://", 1)[-1])[-180:])
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < max_stari:
        return open(path, encoding="utf-8").read()
    try:
        brzda(url)
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": slusne.UA}), timeout=60) as r:
            text = r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        print(f"sdileni: {url} odpověděl {e.code}", file=sys.stderr)
        return open(path, encoding="utf-8").read() if os.path.exists(path) else None
    except (OSError, http.client.HTTPException, UnicodeDecodeError) as e:   # i přerušené čtení (IncompleteRead)
        print(f"sdileni: {url} neodpovídá ({e!r})", file=sys.stderr)
        return open(path, encoding="utf-8").read() if os.path.exists(path) else None
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def brzda(url):
    """Počkej podle tools/slusne.py (rozestupy, blokace, podmínky portálů)."""
    slusne.pockej(url)


def json_z(url):
    t = stahni(url)
    return json.loads(t) if t else None


def norm(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", norm(text)).strip("-")


# ---------- kniha v projektu -> mapa a index ----------

def kniha_z_url(url):
    """(archiv mapy, archiv indexu, kniha) z adresy svazku; None pro archivy, které zatím nepodporujeme."""
    url = url or ""
    if m := re.search(r"portafontium\.eu/register/soap-pn/([a-z0-9-]+)", url) or re.search(r"portafontium\.eu/iipimage/\d+/([a-z0-9-]+)_\d", url):
        return "soa-plzen", "portafontium", m.group(1)
    if m := re.search(r"ebadatelna\.soapraha\.cz/(?:d/|pages/MatrikaPage/matrikaId/)(\d+)", url):
        return "soa-praha", "soapraha", m.group(1)
    if m := re.search(r"ahmp\.cz/.*?xid=([0-9A-Fa-f]{8})", url):
        return None, "ahmp", m.group(1).lower()
    return None


def svazky():
    p = os.path.join(DATA, "svazky.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def kniha_svazku(klic_nebo_url):
    if "://" in klic_nebo_url:
        return kniha_z_url(klic_nebo_url), None
    s = svazky().get(klic_nebo_url)
    if not s:
        sys.exit(f"Svazek {klic_nebo_url} v data/svazky.json není.")
    return kniha_z_url(s.get("url")), s


def index_knihy():
    return {k["id"]: k for k in (json_z(f"{INDEX}/data/knihy.json") or [])}


def precteno_knihy(archiv, kniha):
    t = stahni(f"{INDEX}/knihy/{archiv}/{kniha}/precteno.tsv")
    if not t:
        return []
    radky = [r.split("\t") for r in t.splitlines() if r.strip()]
    return [dict(zip(radky[0], r)) for r in radky[1:]]


# ---------- čtení ----------

def odhad(body, rok):
    body = [b for b in body if b.get("year")]
    presne = [b for b in body if b["year"] <= rok <= b.get("year_to", b["year"])]
    if presne:
        return min(b["scan"] for b in presne), "přímo z bodu"
    pred = [b for b in body if b["year"] <= rok]
    po = [b for b in body if b.get("year_to", b["year"]) >= rok]
    if pred and po:
        a = max(pred, key=lambda b: (b["year"], b["scan"]))
        b = min(po, key=lambda b: (b["year"], b["scan"]))
        if a["year"] != b["year"]:
            return round(a["scan"] + (rok - a["year"]) * (b["scan"] - a["scan"]) / (b["year"] - a["year"])), \
                f"odhad mezi sn. {a['scan']} ({a['year']}) a {b['scan']} ({b['year']})"
    return None


def pokryva(ref, rok, druh):
    for k, rozsah in (ref.get("records") or {}).items():
        if druh and k != druh:
            continue
        roky = [int(r) for r in re.findall(r"\d{4}", rozsah)]
        if not rok or (roky and min(roky) <= rok <= max(roky)):
            return True
    return False


def najdi(obec, rok=None, druh=None):
    refs = json_z(f"{MAPA}/obce/{slug(obec)}.json")
    if refs is None:
        print(f"Mapa matrik obec „{obec}“ nezná (zatím). Najdi knihu obvyklou cestou (portaly.md).")
        return 0
    idx = index_knihy()
    nic = True
    for ref in refs:
        if not pokryva(ref, rok, druh):
            continue
        nic = False
        rec = ", ".join(f"{k} {v}" for k, v in (ref.get("records") or {}).items())
        print(f"\n{ref['signature']} ({ref['archive']}/{ref['portal_id']}) – {rec}; uspořádání {ref.get('order', '?')}, "
              f"bodů v mapě {ref.get('points', 0)}")
        vol = json_z(f"{MAPA}/{ref['path']}") or {}
        body = [b for b in vol.get("points") or [] if not druh or b.get("type") in (druh, None)]
        if vol.get("order", "").startswith("by_village"):
            vlastni = [b for b in body if norm(b.get("place") or "") == norm(obec)]
            body = vlastni or []
            if not vlastni:
                print(f"  kniha je po vsích a oddíl {obec} v mapě zatím není – hledej podle sekcí a poznámek knihy")
        if rok and (o := odhad(body, rok)):
            print(f"  → začni na sn. {o[0]} ({o[1]})")
        for n in vol.get("notes") or []:
            print(f"  pozn.: {n}")
        archiv_idx = {"soa-plzen": "portafontium", "soa-praha": "soapraha"}.get(ref["archive"])
        k = idx.get(f"{archiv_idx}/{ref['portal_id']}")
        if k:
            print(f"  v indexu matrik: {k.get('precteno', '?')} přečtených zápisů{', OCR ' + str(k['ocr_stran']) + ' stran' if k.get('ocr_stran') else ''} "
                  f"(sdileni.py kniha {vol.get('url') or ref['portal_id']})")
    if nic:
        print(f"Pro {obec} {rok or ''} {druh or ''} mapa žádnou knihu nemá.")
    return 0


def kniha(klic_nebo_url):
    k, s = kniha_svazku(klic_nebo_url)
    if not k:
        print("Tenhle archiv zatím sdílení nepodporuje (reference/sdileni.md).")
        return 0
    archiv_mapy, archiv_idx, kn = k
    if archiv_mapy and (vol := json_z(f"{MAPA}/svazky/{archiv_mapy}/{kn}.json")):
        print(f"Mapa matrik: {vol['signature']}, uspořádání {vol.get('order', '?')}")
        for b in sorted(vol.get("points") or [], key=lambda b: b["scan"]):
            co = " ".join(str(x) for x in (b.get("type"), b.get("year"), b.get("place"), b.get("page") and f"str. {b['page']}",
                                            b.get("letters") and f"rejstřík {b['letters']}", b.get("note")) if x)
            print(f"  sn. {b['scan']}: {co}")
    else:
        print("Mapa matrik knihu zatím nemá.")
    radky = precteno_knihy(archiv_idx, kn)
    print(f"Index matrik: {len(radky)} přečtených zápisů" + (":" if radky else "."))
    for r in radky:
        print(f"  sn. {r.get('snimek')}: {r.get('typ')} {r.get('datum')} {r.get('obec')} – {r.get('osoby')}")
    return 0


def main(a):
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    prikaz, args = a[0], a[1:]
    if prikaz == "najdi" and args:
        rok = next((int(x) for x in args[1:] if x.isdigit()), None)
        druh = next((x.upper() for x in args[1:] if x.upper() in ("N", "O", "Z")), None)
        return najdi(args[0], rok, druh)
    if prikaz == "kniha" and args:
        return kniha(args[0])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
