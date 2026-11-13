"""Data domů a obce pro web: z data/domy.py a data/mapy.json udělá části site.json (village, houses, maps…).

Volá ho export_web.py, jen když projekt má data/domy.py. Samo nic nezapisuje.

Původ: logika vychází z tools/export_web.py projektu dejiny-domu-skill (https://github.com/vzoha/dejiny-domu-skill),
commit bda6028bae08307727a4449931497c9f163ea691. Naše úprava: je to samostatný modul (rodokmenový export zůstává
v export_web.py), držitelé a obyvatelé mají pole `os` (vazba na osobu z data/osoby.py), viz `nacti()`. Z 5c1715b: domy.py se čte s utf-8-sig a chybějící soubor hlásí srozumitelně.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from platnost import (chyba_odkazu, chyba_polohy, chyba_vyrezu, chyby_adres_domu, cislo_domu, proc_neprolinat,  # noqa: E402
                      skupiny_map, slugify, vyhrady)

STATUS = {"doc": "doloženo pramenem", "lit": "z literatury", "prob": "pravděpodobné", "fam": "od pamětníků",
          "unk": "neznámé"}
JMENO_OBRAZKU = re.compile(r"\w[\w.-]*")   # klíč = jméno souboru ve vyrezy/ a zdroje/; žádné lomítko ani ../


def year_key(text):
    """Řadicí klíč z „1351“, „22. 7. 1351“, „asi 1600“, „1786–1820“ (první čtyřčíslí, pak den a měsíc)."""
    t = str(text or "")
    m = re.search(r"\d{4}", t)
    if not m:
        return 99999999
    parts = re.findall(r"\d+", t[:m.start()])
    d, mo = (parts + [0, 0])[:2] if len(parts) >= 2 else (0, (parts or [0])[0])
    return int(m.group(0)) * 10000 + int(mo) * 100 + int(d)


def load_houses(data_dir):
    ns = {}
    try:
        exec(open(os.path.join(data_dir, "domy.py"), encoding="utf-8-sig").read(), ns)
    except OSError as e:
        sys.exit(f"CHYBA: data/domy.py nejde načíst ({e.strerror}) – spouštěj z kořene projektu: python3 -I tools/export_web.py")
    for name, default in (("OBEC", {}), ("OBEC_UDALOSTI", []), ("D", {}), ("ISSUES", [])):
        ns.setdefault(name, default)
    return ns


def chyby_jmen_obrazku(odkud, jmena):
    spatne = [str(k) for k in jmena if not JMENO_OBRAZKU.fullmatch(str(k)) or ".." in str(k)]
    return [f"{odkud}: klíč obrázku smí mít jen písmena, číslice, _ - . (bez lomítek a ..): {', '.join(spatne)}"] if spatne else []


def chyby_dat(OBEC, D, maps_cfg, zaznamy, svazky, mista):
    """Chyby, které by rozbily web nebo zveřejnily spustitelný odkaz (podrobně je hlásí kontrola.py)."""
    odkazy = [(f"data/zaznamy.json {z.get('klic')}", z.get("odkaz")) for z in zaznamy]
    odkazy += [(f"data/svazky.json {k}", sv.get("url")) for k, sv in svazky.items()]
    odkazy += [(f"data/mapy.json {m.get('img')}", m.get("url")) for m in maps_cfg]
    odkazy += [(f"data/mista.json {n}", e.get("odkaz")) for n, e in mista.items()]
    chyby = [f"{kde}: {c}" for kde, url in odkazy if (c := chyba_odkazu(url))]
    polohy = [("domy.py OBEC", OBEC)] + [(f"domy.py dům {cp}", d) for cp, d in D.items()] + \
             [(f"data/mista.json {n}", e) for n, e in mista.items()]
    chyby += [f"{kde}: {c}" for kde, x in polohy if (c := chyba_polohy(x))]
    chyby += [f"domy.py {c}" for c in chyby_adres_domu(D)]
    chyby += [f"data/mapy.json {m.get('img')}: {c}" for m in maps_cfg if (c := chyba_vyrezu(m.get("vyrez")))]
    return chyby


def _cited(x, recs):
    return [r for r in x.get("r", []) if r in recs]


def _owner_year(o):
    return o["since"] if re.search(r"\d", o["since"]) else o["until"]


def _event(e, recs):
    return dict(year=str(e.get("rok", "")), text=e.get("text", ""), st=e.get("st", "unk"), status=STATUS.get(e.get("st"), ""),
                source=e.get("zdroj", ""), caveats=vyhrady(e), records=_cited(e, recs))


def sestav(ns, recs, docs_cfg, maps_cfg, mista, cfg, vyrezy, zdroje, osoby_slugs=None):
    """Vrací dict pro site.json: village, houses, mainHouse, maps, mapGroups, housePlaces, houseStats, houseIssues.

    recs = {klíč zápisu: řádek} (jen existující zápisy), osoby_slugs = {Kekulé číslo: adresa osoby} (nebo None bez rodokmenu).
    """
    OBEC, D = ns["OBEC"], ns["D"]
    osoby_slugs = osoby_slugs or {}

    def osoba(x):
        return osoby_slugs.get(x.get("os"))

    houses = {}
    for cp, d in D.items():
        slug = slugify(cp)
        people = [dict(name=o.get("n", ""), years=o.get("y", ""), role=o.get("role", ""), facts=o.get("f", []),
                       st=o.get("st", "unk"), status=STATUS.get(o.get("st"), ""), note=o.get("note", ""),
                       caveats=vyhrady(o), records=_cited(o, recs), person=osoba(o)) for o in d.get("obyvatele", [])]
        owners = [dict(since=str(o.get("od", "")), until=str(o.get("do", "")), name=o.get("n", ""), how=o.get("jak", ""),
                       st=o.get("st", "unk"), status=STATUS.get(o.get("st"), ""), note=o.get("note", ""),
                       caveats=vyhrady(o), records=_cited(o, recs), person=osoba(o)) for o in d.get("drzitele", [])]
        # neznámý začátek („?“ do 1820) řadí podle konce – před toho, kdo ve stejném roce začal
        owners.sort(key=lambda o: (year_key(_owner_year(o)), bool(re.search(r"\d", o["since"]))))
        events = sorted((_event(e, recs) for e in d.get("udalosti", [])), key=lambda e: year_key(e["year"]))
        refs = [r for x in events + owners + people for r in x["records"]]
        houses[slug] = dict(
            key=cp, cp=cislo_domu(cp, d), part=str(d.get("cast") or ""), slug=slug, name=d.get("nazev", ""), kind=d.get("druh", ""),
            st=d.get("st", "unk"), status=STATUS.get(d.get("st"), ""), desc=d.get("popis", ""), note=d.get("note", ""),
            lat=d.get("lat"), lon=d.get("lon"), numbers=[dict(when=a, num=b) for a, b in d.get("cisla", [])],
            events=events, owners=owners, people=people, records=list(dict.fromkeys(refs)),
            story=dict(title=d.get("pribeh_nadpis", ""), paras=list(d["pribeh"])) if d.get("pribeh") else None,
            docs=[dict(img=x["img"], caption=x["popis"]) for x in docs_cfg if str(cp) in [str(c) for c in x.get("domy", [])]
                  and os.path.exists(os.path.join(vyrezy, x["img"] + ".jpg"))],
        )
    # `poradi` u domu (menší dřív, bez něj 0), hlavní část obce (bez `cast`) první, pak části podle abecedy, v nich podle čísla
    houses = dict(sorted(houses.items(), key=lambda kv: (D[kv[1]["key"]].get("poradi", 0), kv[1]["part"],
                                                         int(re.match(r"\d*", kv[1]["cp"]).group(0) or 99999), kv[1]["cp"], kv[0])))
    for i, h in enumerate(houses.values()):
        h["order"] = i   # JavaScript řadí klíče jako „1“, „22“ vždy číselně – pořadí nese tohle pole (lib/data.js)

    village_events = sorted((_event(e, recs) for e in ns["OBEC_UDALOSTI"]), key=lambda e: year_key(e["year"]))
    village = dict(name=OBEC.get("nazev", ""), otherNames=OBEC.get("jine_nazvy", ""), municipality=OBEC.get("obec", ""),
                   parish=OBEC.get("farnost", ""), estate=OBEC.get("panstvi", ""), desc=OBEC.get("popis", ""),
                   lat=OBEC.get("lat"), lon=OBEC.get("lon"), events=village_events)

    maps = [dict(img=m["img"], year=str(m.get("rok", "")), title=m.get("nazev", ""), source=m.get("zdroj", ""),
                 url=m.get("url", ""), desc=m.get("popis", ""), group=m.get("skupina", ""),
                 full=os.path.exists(os.path.join(zdroje, m["img"] + ".jpg")))
            for m in maps_cfg if os.path.exists(os.path.join(vyrezy, m["img"] + ".jpg"))]
    maps.sort(key=lambda m: year_key(m["year"]))
    na_webu = {m["img"] for m in maps}
    map_groups = {g: dict(overlay=proc_neprolinat(ms, vyrezy) is None)
                  for g, ms in skupiny_map([m for m in maps_cfg if m["img"] in na_webu]).items()}

    places = [dict(name=n, lat=e["lat"], lon=e["lon"], desc=e.get("popis", ""), kind=e.get("druh", ""),
                   link=e.get("odkaz", ""), linkText=e.get("odkaz_text", ""), approx=bool(e.get("priblizne")))
              for n, e in mista.items() if e.get("lat") is not None]

    years = [year_key(e["year"]) // 10000 for e in village_events] + \
            [year_key(e["year"]) // 10000 for h in houses.values() for e in h["events"]] + \
            [year_key(_owner_year(o)) // 10000 for h in houses.values() for o in h["owners"]]
    years = [y for y in years if y < 9999]
    stats = dict(houses=len(houses), maps=len(maps),
                 people=sum(len(h["people"]) for h in houses.values()),
                 owners=sum(len(h["owners"]) for h in houses.values()), oldest=min(years) if years else None)

    main_house = slugify(cfg.get("hlavni_dum", "")) or next(iter(houses), "")
    refs = {}
    for h in houses.values():
        for r in h["records"]:
            refs.setdefault(r, []).append(h["slug"])
    return dict(village=village, houses=houses, mainHouse=main_house if main_house in houses else None,
                maps=maps, mapGroups=map_groups, housePlaces=places, houseStats=stats,
                houseIssues=[dict(title=i, text="") if isinstance(i, str) else dict(title=i[0], text=i[1]) for i in ns["ISSUES"]],
                recordHouses=refs, villageRecords=sorted({r for e in village_events for r in e["records"]}))
