#!/usr/bin/env python3
"""Co se v upstreamu vzoha/dejiny-domu-skill změnilo od commitu, ze kterého jsme přebírali.

Údržbářský skript repozitáře (do projektů uživatelů se nekopíruje). Nic neklonuje a repozitář nemění: jedním
dotazem na GitHub API (compare) zjistí změněné soubory, vypíše, které z nich máme převzaté, a jejich rozdíly uloží
do dočasné složky. Rozhodnutí, co přebrat, je na člověku; po přebrání zvedni commit v hlavičkách souborů.

Použití (z kořene repozitáře):
  python3 -I scripts/upstream.py [--od <commit>] [--ven <složka>]
      --od   základ porovnání; bez něj se přečte z hlaviček „Původ“ převzatých souborů (nejčastější commit)
      --ven  kam uložit rozdíly po souborech (výchozí: nová dočasná složka)
Sandbox: curl/urllib musí smět api.github.com. Bez přihlášení platí limit GitHubu (60 dotazů za hodinu); skript dělá jeden.
"""
import collections, http.client, json, os, re, sys, tempfile, urllib.request
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "vzoha/dejiny-domu-skill"
U = "skills/dejiny-domu/"
W = "shared/template/web/src/"

# upstreamová cesta -> naše cesta (jen soubory, které jsme převzali, i upravené)
MAPA = {
    **{f"{U}tools/{n}": f"shared/tools/{n}" for n in
       ("podminky.py", "podminky.json", "cuzk_archiv.py", "zdravi.py", "platnost.py", "ramecek.py")},
    f"{U}tools/export_web.py": "shared/tools/domy_web.py",   # logika domů; náš export_web.py je jiný soubor
    **{f"{U}reference/{n}": f"shared/reference/{n}" for n in ("podminky.md", "prameny.md", "texty.md")},
    f"{U}template/data/domy.py": "shared/template/dum/data/domy.py",
    **{f"{U}template/web/src/{n}": W + n for n in
       ("components/HouseLink.astro", "components/HouseMap.astro", "components/RecLinks.astro",
        "components/Timeline.astro", "components/Vyhrady.astro", "lib/places.js", "pages/domy.astro",
        "pages/mapy.astro", "pages/obec.astro", "pages/dum/[slug].astro", "pages/pribehy/[slug].astro")},
    "tests/test_podminky.py": "tests/podminky/test_podminky.py",
}
HLAVICKA = re.compile(r"commit ([0-9a-f]{7,40})|\(([0-9a-f]{7,40})\)")


def zaklad(root=ROOT):
    """Nejčastější commit z hlaviček „Původ“ převzatých souborů, nebo None."""
    c = collections.Counter()
    for nase in MAPA.values():
        try:
            with open(os.path.join(root, nase), encoding="utf-8") as f:
                hlava = "".join(f.readline() for _ in range(14))
        except OSError:
            continue
        for r in hlava.splitlines():
            if "dejiny-domu-skill" in r:
                for m in HLAVICKA.finditer(r):
                    c[m.group(1) or m.group(2)] += 1
    return c.most_common(1)[0][0] if c else None


def zpracuj(cmp, ven, root=ROOT):
    """Z odpovědi compare API: (převzaté změněné, ostatní změněné); rozdíly převzatých uloží do `ven`."""
    prevzate, ostatni = [], []
    for f in cmp.get("files", []):
        cesta = f["filename"]
        if cesta in MAPA or f.get("previous_filename") in MAPA:
            nase = MAPA.get(cesta) or MAPA[f["previous_filename"]]
            prevzate.append((cesta, nase, f["status"], f.get("additions", 0), f.get("deletions", 0)))
            if f.get("patch"):
                cil = os.path.join(ven, cesta.replace("/", "__") + ".diff")
                with open(cil, "w", encoding="utf-8") as o:
                    o.write(f["patch"] + "\n")
        else:
            ostatni.append((cesta, f["status"]))
    return prevzate, ostatni


def main(a):
    if "-h" in a or "--help" in a:
        sys.exit(__doc__)
    od = a[a.index("--od") + 1] if "--od" in a else zaklad()
    if not od:
        sys.exit("Nenašel jsem základní commit v hlavičkách souborů; zadej --od <commit>.")
    ven = a[a.index("--ven") + 1] if "--ven" in a else tempfile.mkdtemp(prefix="upstream_")
    os.makedirs(ven, exist_ok=True)
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/compare/{od}...master",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "rodokmen-upstream-check",
                                          "Accept-Encoding": "identity"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            cmp = json.load(r)
    except (OSError, http.client.HTTPException, ValueError) as e:   # IncompleteRead: sandbox nebo proxy přerušily odpověď
        sys.exit(f"Dotaz na GitHub API se nepovedl ({type(e).__name__}: {e}). V sandboxu povol api.github.com, "
                 "případně skript pusť mimo sandbox.")
    prevzate, ostatni = zpracuj(cmp, ven)
    hlava = cmp.get("commits", [{}])[-1].get("sha", "?")[:7]
    print(f"Upstream {REPO}: od {od} do {hlava}, {cmp.get('total_commits', '?')} commitů, "
          f"{len(cmp.get('files', []))} změněných souborů"
          + (" (výpis GitHubu je zkrácený na 300 souborů)" if len(cmp.get("files", [])) >= 300 else ""))
    print(f"\nPřevzaté soubory, které se v upstreamu změnily ({len(prevzate)}):")
    for up, nase, st, p, m in prevzate:
        print(f"  {st:9} +{p}/-{m}  {up}  →  {nase}")
    if not prevzate:
        print("  žádné")
    print(f"\nOstatní změny upstreamu, které nemáme převzaté ({len(ostatni)}):")
    for cesta, st in ostatni:
        print(f"  {st:9} {cesta}")
    print(f"\nRozdíly po souborech: {ven}")
    print(f"Po přebrání změn zvedni commit v hlavičkách „Původ“ z {od} na {hlava} a zapiš to do docs/decisions.md.")


if __name__ == "__main__":
    main(sys.argv[1:])
