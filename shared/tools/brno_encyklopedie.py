#!/usr/bin/env python3
"""Encyklopedie dějin města Brna (encyklopedie.brna.cz, Muzeum města Brna): co víme o ulici a domě.

Použití:
  brno_encyklopedie.py "<ulice>" [číslo]   – domy a stavby, objekty (pamětní desky, Kameny zmizelých), události
                                              v ulici a osobnosti s bydlištěm v ulici; s číslem jen domy, objekty
                                              a osobnosti toho domu (události celé ulice, adresu nemají)
  brno_encyklopedie.py detail <odkaz>       – text profilu: stavební vývoj, majitelé, osoby, události, popisky fotek
Ulici zadej dnešním názvem; staré názvy a přejmenování ulice najdeš v hesle ulice (Ulice na webu).
Bydliště osob hledá encyklopedie jako text: „Pekařská 4“ najde i Pekařská 40 – ověř v profilu.
Podmínky užití web neuvádí: fakta s citací ano, fotky a delší text jen se souhlasem Muzea města Brna.

Původ: převzato z vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/brno_encyklopedie.py), commit 5c1715b; úprava: slusne.py se u nás zapíná importem (bez instaluj())."""
import html, json, os, re, sys, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne   # noqa: E402 – společný limit rychlosti (slusne.py; u nás se zapíná importem)

WEB = "https://encyklopedie.brna.cz/home-mmb/"
STRAN = 5   # po 30 záznamech; víc u jedné ulice nebývá potřeba
# (nadpis, druh hledání webu, pole), osoby se hledají i s číslem domu
DRUHY = [("Domy a stavby", "home", "home_street_name"), ("Objekty (desky, sochy, kameny)", "element", "elm_street_name"),
         ("Události", "event", "evn_street_name"), ("Osobnosti s bydlištěm", "person", "pers_residence")]
KARTA = re.compile(r'<div class="card-body">(.*?)</div>', re.S)
ODKAZ = re.compile(r'href="\./(\?acc=profil-[a-z-]+&amp;load=\d+)')


def text(fragment):
    """HTML → řádky textu bez prázdných."""
    t = html.unescape(re.sub(r"<br\s*/?>|</p>|</div>|</a>", "\n", fragment))
    t = re.sub(r"<[^>]+>", "", t)
    return [r.strip() for r in t.splitlines() if r.strip()]


def stranka(druh, pole, hodnota, cislo_stranky):
    parametry = {"search": druh, pole: hodnota, "page_current": cislo_stranky, "per_page": "", "json": "search-v2"}
    with urllib.request.urlopen(f"{WEB}?{urllib.parse.urlencode(parametry)}", timeout=60) as r:
        return json.load(r)


def hledej(druh, pole, hodnota):
    """([(řádky karty, odkaz)], celkem)."""
    karty, celkem = [], 0
    for cislo in range(1, STRAN + 1):
        d = stranka(druh, pole, hodnota, cislo)
        vysledek = d["data"]["result"]
        celkem = vysledek.get("rows_total", 0)
        for karta in KARTA.findall("".join(d.get("html", {}).values())):
            odkaz = ODKAZ.search(karta)
            karty.append((text(karta), WEB + html.unescape(odkaz.group(1)) if odkaz else ""))
        if int(vysledek.get("page_next", 0)) > int(vysledek.get("page_total", 0)):
            break
    return karty, celkem


def ulice(nazev, cislo=None):
    for nadpis, druh, pole in DRUHY:
        hodnota = f"{nazev} {cislo}" if cislo and druh == "person" else nazev
        karty, celkem = hledej(druh, pole, hodnota)
        if cislo and druh in ("home", "element"):   # karty mají adresu; události ji nemají, ty zůstanou celé
            karty = [k for k in karty if re.search(rf"\b{re.escape(nazev)}\s+{re.escape(cislo)}\b", " ".join(k[0]))]
            celkem = len(karty)
        print(f"\n{nadpis}: {celkem}{f' (vypsáno {len(karty)})' if celkem > len(karty) else ''}")
        for radky, odkaz in karty:
            print(f"  {' | '.join(radky)} | {odkaz}")


def detail(odkaz):
    with urllib.request.urlopen(odkaz, timeout=60) as r:
        obsah = r.read().decode("utf-8", "replace")
    obsah = re.sub(r"<(script|style|nav|header|footer)\b.*?</\1>", "", obsah, flags=re.S)
    radky = text(obsah)
    zacatek = radky.index("Vyhledat") + 1 if "Vyhledat" in radky else 0
    konec = next((i for i, r in enumerate(radky) if r.startswith(("«« předchozí", "Máte více informací"))), len(radky))
    print("\n".join(radky[zacatek:konec]))
    print(f"\nCitace: Encyklopedie dějin města Brna, {odkaz}")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if argv[0] == "detail" and len(argv) == 2:
        detail(argv[1])
    else:
        ulice(argv[0], argv[1] if len(argv) > 1 else None)


if __name__ == "__main__":
    main(sys.argv[1:])
