#!/usr/bin/env python3
"""Hledání svazků na portálu ARON (SOA Zámrsk, fond Sbírka matrik Východočeského kraje).
Použití: aron_search.py "<text v popisu, např. obec>" [filtr názvu fondu] [max] [--sken]
  --sken: u každého svazku (nejvýš 40, po jednom dotazu přes brzdu) doplní počet snímků, nebo „BEZ SNÍMKŮ“
  Víc slov oddělených čárkou musí být v popisu všechna: "Vinice,Hořice" = Vinice ve farnosti Hořice
  (stejnojmenných obcí bývá víc – výsledky jsou proto seřazené podle farnosti / první obce v popisu).
Vypíše: apu_id | signatura, druh a roky | popis (obce, které svazek pokrývá).
Vypisuje i svazky bez snímků (hlavně 20. století, ale i oddací kniha z roku 1939 může být jen v badatelně: lhůta 75 let
ještě neznamená online) – jestli je svazek online, ukáže --sken nebo `aron_img.py <apu_id> info` (scans: 0 = není)."""
import json, re, sys, time, urllib.request
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

API = "https://aron.vychodoceskearchivy.cz/api/aron"

def post(path, body, tries=3):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    for attempt in range(tries):   # ARON občas neodpoví (timeout) – zkusit znovu s pauzou
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except OSError:
            if attempt == tries - 1:
                raise
            time.sleep(5 * (attempt + 1))

def search(desc, name="Sbírka matrik Východočeského kraje", maxn=500):
    out, offset = [], 0
    while True:
        d = post("/apu/listview?listType=SEARCH", {
            "filters": [{"field": "type", "operation": "EQ", "value": "ARCH_DESC"},
                        {"operation": "FTXF", "field": "name", "value": name},
                        *({"operation": "FTXF", "field": "description", "value": w.strip()}
                          for w in desc.split(",") if w.strip())],
            "sort": [], "offset": offset, "size": 100, "aggregations": []})
        items = d.get("items", [])
        out += items
        offset += len(items)
        if not items or offset >= min(d.get("count", 0), maxn):
            return out, d.get("count")

def place(desc):
    """Řadicí klíč: popis bez úvodního druhu knihy („římskokatolická matrika NAROZENÝCH, …“), tj. od farnosti / první obce."""
    parts = (desc or "").split(", ")
    while parts and re.search(r"matrika|index", parts[0]):
        parts.pop(0)
    return re.sub(r"^\(?(farnost|soudní okres) ", "", ", ".join(parts))

if __name__ == "__main__":
    SKEN = "--sken" in sys.argv
    argv = [a for a in sys.argv if a != "--sken"]
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    desc = argv[1]
    name = argv[2] if len(argv) > 2 and argv[2] else "Sbírka matrik Východočeského kraje"
    maxn = int(argv[3]) if len(argv) > 3 else 500
    items, cnt = search(desc, name, maxn)
    print("count", cnt)
    if SKEN:
        import aron_img   # volume() ukládá do mezipaměti a jde přes brzdu; jeden dotaz na svazek
    for k, i in enumerate(sorted(items, key=lambda i: (place(i.get("description")), i["name"]))):
        n = i["name"].split(": ", 1)[-1]
        znacka = ""
        if SKEN and k < 40:
            try:
                pocet = len(aron_img.tiles_by_order(aron_img.volume(i["id"])))
                znacka = f" [{pocet} sn.]" if pocet else " [BEZ SNÍMKŮ]"
            except Exception as e:   # svazek, který ARON nezveřejňuje (404), nebo výpadek: značka, ne pád
                znacka = f" [snímky nezjištěny: {type(e).__name__}]"
        print(i["id"], "|", n.replace("Sbírka matrik Východočeského kraje, ", "") + znacka, "|", (i.get("description") or "")[:220])
    if SKEN and len(items) > 40:
        print(f"(snímky zjištěny jen u prvních 40 z {len(items)}; zúži hledání)")
