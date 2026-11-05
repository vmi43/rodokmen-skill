#!/usr/bin/env python3
"""Místa předků pro mapu na webu (data/mista.json); souřadnice z Mapy.com (REST API, geokódování).

Použití (z kořene projektu: python3 -I tools/slusne.py tools/mista.py …):
  mista.py pridej "Název" ["regulární výraz"] ["dotaz pro vyhledání"]
      přidá obec; výraz se hledá v údajích osob (výchozí = prvních 5 písmen názvu, aby sedělo i skloňování),
      dotaz pro Mapy.com (výchozí = „Název“, když nic nenajde, zkusí i mimo Česko);
      u víceznačných názvů (Podolí, Dub) přidej sousední obec: "Podolí, Odlochovice" – a ve výpisu vždy zkontroluj okres
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

API klíč Mapy.com (zdarma, základní tarif 250 000 kreditů měsíčně, jedno hledání = 4 kredity): založ si účet a projekt
na https://developer.mapy.com/portal-muj-ucet/ a vytvoř klíč. Dej ho do proměnné prostředí MAPY_API_KEY nebo do souboru
pracovni/.mapy_klic (složka pracovni/ je v .gitignore). Klíč nikdy nepiš do chatu, kódu ani commitu.
"""
import json, math, os, re, sys, time, urllib.parse, urllib.request
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


def main():
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
