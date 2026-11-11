#!/usr/bin/env python3
"""Zařazení ručně stažených knih (složka s `obsah.txt` v pracovni/) do projektu – bez sítě, nic nestahuje.

Použití (z kořene projektu):
  zarad.py [pracovni/<složka> …]                 náhled: co by se udělalo a co nesedí (nic nemění)
  zarad.py [pracovni/<složka> …] --proved        provede: přejmenuje složku a snímky, napíše obsah.md, zapíše svazky.json
  zarad.py … --ignoruj-pocet                     zařadí i složku, kde se počet snímků liší od údaje v obsah.txt
Bez složek vezme všechny složky v pracovni/ s obsah.txt, které ještě nejsou zařazené (nekončí na `_manual`).

Co udělá (postup v reference/portaly.md, „Ručně stažené knihy“):
  - klíč svazku z odkazu v obsah.txt: eBadatelna `ebad_<matrikaId>`, archiválie `ebad_a_<id>` (je-li ve svazky.json už
    `archivalie_<id>`, zůstane tak), ARON prvních 8 znaků apu (složka `aron_<apu8>_…`);
  - složka → `pracovni/<klíč>_<název>_manual/`, snímky → `s<n>.jpg` podle pořadí (čísla z názvů souborů jen třídí);
  - `obsah.md` (koncept z obsah.txt; doplň, co kniha obsahuje), záznam ve svazky.json s `"upload": "manual"` (přes zapis.py);
  - hlásí rozpory: počet snímků × údaj v obsah.txt, název × záznam ve svazky.json, jiný klíč v názvu složky;
  - vypíše strojové kopie téhož svazku (nemaže je) a místa v textech projektu, kde zůstaly staré cesty (přepiš přes /replace).
Nic nemaže. Strojové kopie smaž ručně až po shodě počtů a po diffu toho, co zmizelo.
"""
import glob, json, os, re, subprocess, sys, unicodedata
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRAC = os.path.join(ROOT, "pracovni")
SCANS = re.compile(r"(?im)^(?:number of scans|scans|počet snímků)[ \t]*[:\n][ \t]*(\d+)")
OBRAZEK = re.compile(r"\.jpe?g$", re.I)


def slug(s):
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_") or "svazek"


def pole(txt, *popisky):
    """Hodnota pod řádkem s popiskem (eBadatelna: popisek a hodnota na dalším řádku; ARON: VELKÝMI)."""
    radky = [r.strip() for r in txt.splitlines()]
    for i, r in enumerate(radky):
        if r.lower() in [p.lower() for p in popisky] and i + 1 < len(radky) and radky[i + 1] not in ("", "---"):
            return radky[i + 1]
    return ""


def rozpoznej(txt, slozka):
    """(portál, klíč ve svazky.json, předpona složky, id, url, typ) podle odkazu v obsah.txt."""
    m = re.search(r"matrikaId/(\d+)", txt)
    if m:
        return "eBadatelna", f"ebad_{m[1]}", f"ebad_{m[1]}", m[1], f"https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/{m[1]}", ""
    m = re.search(r"archivalieId/(\d+)", txt)
    if m:
        return "eBadatelna", f"ebad_a_{m[1]}", None, m[1], f"https://ebadatelna.soapraha.cz/pages/ArchivaliePage/archivalieId/{m[1]}", "archivalie"
    m = re.search(r"aron\.vychodoceskearchivy\.cz/apu/([0-9a-f]{8})(?:-[0-9a-f-]{27})?", txt) \
        or re.search(r"_00190_([0-9a-f]{8})_", slozka)
    if m:
        plny = re.search(r"/apu/([0-9a-f]{8}-[0-9a-f-]{27})", txt)
        return ("ARON", m[1], f"aron_{m[1]}", m[1], f"https://aron.vychodoceskearchivy.cz/apu/{plny[1]}" if plny else "", "")
    return None


def obrazky(slozka):
    """Snímky seřazené podle čísla v názvu (jinak podle jména); (seznam, upozornění)."""
    soubory = [f for f in os.listdir(slozka) if OBRAZEK.search(f) and not f.endswith(".part.jpg")]

    def klic(f):
        c = re.findall(r"\d+", os.path.splitext(f)[0])
        return (int(c[-1]) if c else 0, f)
    soubory.sort(key=klic)
    cisla = [klic(f)[0] for f in soubory]
    upoz = "" if cisla == list(range(1, len(soubory) + 1)) else "čísla v názvech nenavazují od 1, očísluji podle pořadí"
    return soubory, upoz


def roky(txt):
    r = pole(txt, "Date from to", "DATACE VZNIKU")
    return r.replace(" - ", "–") if r else ""


def nazev_aron(txt):
    m = re.search(r"(?m)^Státní oblastní archiv[^:\n]*:\s*(.+)$", txt)
    return re.sub(r"^Sbírka matrik Východočeského kraje,\s*", "", m[1].strip()) if m else ""


def plan(slozka, svazky):
    jmeno = os.path.basename(slozka.rstrip("/\\"))
    txt = open(os.path.join(slozka, "obsah.txt"), encoding="utf-8", errors="replace").read()
    p = {"zdroj": slozka, "jmeno": jmeno, "problemy": [], "poznamky": [], "txt": txt}
    r = rozpoznej(txt, jmeno)
    if not r:
        p["problemy"].append("v obsah.txt není odkaz s matrikaId, archivalieId ani apu (ARON): zařaď ručně")
        return p
    portal, klic, predpona, ident, url, typ = r
    if typ == "archivalie" and f"archivalie_{ident}" in svazky:
        klic = f"archivalie_{ident}"
    p.update(portal=portal, klic=klic, ident=ident, typ=typ)
    predpona = predpona or klic
    prvni = next((x.strip() for x in txt.splitlines() if x.strip()), "")
    stary = svazky.get(klic, {})
    if url == "" and stary.get("url"):
        url = stary["url"]
    jmeno_svazku = (stary.get("svazek") or prvni).split(",")[0]
    p["slozka_nova"] = os.path.join(PRAC, f"{predpona}_{slug(jmeno_svazku)}_manual")
    obr, upoz = obrazky(slozka)
    p["obrazky"] = obr
    if upoz:
        p["poznamky"].append(upoz)
    ocekavano = SCANS.search(txt)
    ocekavano = int(ocekavano[1]) if ocekavano else stary.get("snimku")
    if ocekavano is None:
        p["poznamky"].append(f"počet snímků neověřen (obsah.txt ho nemá, svazky.json také); ve složce {len(obr)}")
    elif ocekavano != len(obr):
        p["problemy"].append(f"počet snímků: ve složce {len(obr)}, podle {'obsah.txt' if SCANS.search(txt) else 'svazky.json'} {ocekavano}")
    if not obr:
        p["problemy"].append("ve složce nejsou žádné snímky (.jpg)")
    sa, sb = slug(prvni), slug(stary.get("svazek", ""))
    if stary.get("svazek") and prvni and not (sb.startswith(sa) or sa.startswith(sb)):   # „loucen-05“ × „Loučeň 05, N 1800–…“ je shoda
        p["problemy"].append(f"název z obsah.txt „{prvni}“ se liší od svazky.json „{stary['svazek']}“: ověř, že složka patří ke svazku")
    m = re.search(r"(?:ebad_a?_?|archivalie_|aron_)(\d+|[0-9a-f]{8})", jmeno)
    if m and m[1] != ident:
        p["problemy"].append(f"název složky obsahuje jiný klíč ({m[1]}) než odkaz v obsah.txt ({ident})")
    if os.path.exists(p["slozka_nova"]):
        p["problemy"].append(f"cílová složka už existuje: {p['slozka_nova']}")
    zaznam = dict(stary)
    zaznam.update(portal=portal, snimku=len(obr), upload="manual")
    if url:
        zaznam["url"] = url
    if typ:
        zaznam["typ"] = typ
    if not stary:
        if portal == "ARON":
            zaznam["archiv"] = "SOA Hradec Králové – Sbírka matrik Východočeského kraje"
            zaznam["svazek"] = ", ".join(x for x in (prvni, nazev_aron(txt)) if x)
            zaznam["popis"] = pole(txt, "MATRIČNÍ MÍSTO")[:300]
        elif typ:
            zaznam["archiv"] = "SOA Praha – " + (pole(txt, "Archival fund") or "archiválie")
            zaznam["svazek"] = ", ".join(x for x in (pole(txt, "Original title") or prvni, roky(txt),
                                                      "inv. č. " + pole(txt, "Inventory number") if pole(txt, "Inventory number") else "",
                                                      "sign. " + pole(txt, "Signature") if pole(txt, "Signature") else "") if x)
        else:
            zaznam["archiv"] = "SOA Praha – Sbírka matrik"
            zaznam["svazek"] = ", ".join(x for x in (prvni, roky(txt)) if x)
        if portal == "eBadatelna":
            lok = re.search(r"(?s)\nLocalities\n(.*?)\n(?:\n|https://)", txt)
            if lok:
                zaznam["popis"] = ", ".join(l.split(" / ")[0].strip() for l in lok[1].splitlines() if l.strip())[:300]
    p["zaznam"] = zaznam
    p["predpona"] = predpona
    return p


def kopie_a_odkazy(p):
    """Strojové kopie téhož svazku a staré cesty v textech projektu."""
    out = []
    klice = {p["klic"], p["predpona"], f"ebad_{p['ident']}", f"archivalie_{p['ident']}", f"ebad_a_{p['ident']}", f"aron_{p['ident']}"}
    for d in sorted(glob.glob(os.path.join(PRAC, "*/"))):
        n = os.path.basename(d.rstrip("/\\"))
        if d.rstrip("/\\") in (p["zdroj"].rstrip("/\\"), p["slozka_nova"].rstrip("/\\")) or n.endswith("_manual"):
            continue
        if any(n == k or n.startswith(k + "_") for k in klice):
            out.append(f"strojová kopie: pracovni/{n} ({len(glob.glob(os.path.join(d, 's*.jpg')))} snímků) – nemažu")
    stare = {p["jmeno"]} | {re.sub(r"^.*pracovni/", "", x.split(": ")[1].split(" (")[0]) for x in out}
    hity = []
    for f in glob.glob(os.path.join(ROOT, "*.md")) + glob.glob(os.path.join(ROOT, "data", "*.md")) \
            + glob.glob(os.path.join(ROOT, "data", "*.json")) + glob.glob(os.path.join(ROOT, "docs", "*.md")):
        try:
            for i, r in enumerate(open(f, encoding="utf-8"), 1):
                if any(s and s in r for s in stare):
                    hity.append(f"{os.path.relpath(f, ROOT)}:{i}")
        except (OSError, UnicodeDecodeError):
            pass
    if hity:
        out.append("staré cesty v textech (přepiš přes /replace): " + ", ".join(hity[:15]) + (" …" if len(hity) > 15 else ""))
    return out


def obsah_md(p):
    z = p["zaznam"]
    return (f"# {z.get('svazek', p['jmeno'])}\n\nKlíč: `{p['klic']}`; {z.get('archiv', '')} ({z['portal']}); "
            f"{z['snimku']} snímků; stažení ručně.\n\nOdkaz: {z.get('url', '–')}\n\n"
            "Co kniha obsahuje (rejstříky a na kterých snímcích, rozsah let, farnost): **doplnit z `obsah.txt`**.\n")


def proved(p):
    z = p["slozka_nova"]
    for n, f in enumerate(p["obrazky"], 1):   # dvoufázově, aby se nové názvy nepotkaly se starými
        os.rename(os.path.join(p["zdroj"], f), os.path.join(p["zdroj"], f"__{n}.tmp"))
    for n in range(1, len(p["obrazky"]) + 1):
        os.rename(os.path.join(p["zdroj"], f"__{n}.tmp"), os.path.join(p["zdroj"], f"s{n}.jpg"))
    os.rename(p["zdroj"], z)
    md = os.path.join(z, "obsah.md")
    if not os.path.exists(md):
        with open(md, "w", encoding="utf-8", newline="\n") as f:
            f.write(obsah_md(p))
    vstup = os.path.join(PRAC, f"_zarad_{p['klic']}.json")
    with open(vstup, "w", encoding="utf-8", newline="\n") as f:
        json.dump(p["zaznam"], f, ensure_ascii=False)
    try:
        r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "zapis.py"), "svazky", p["klic"], vstup, "--sloucit"],
                           capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    finally:
        os.remove(vstup)
    if r.returncode:
        sys.exit(f"zapis.py selhal (složka už je přejmenovaná na {z}):\n{r.stdout}{r.stderr}")
    # zpětné čtení: co jsme zapsali, musí být na disku
    sv = json.load(open(os.path.join(ROOT, "data", "svazky.json"), encoding="utf-8"))
    ok = sv.get(p["klic"], {}).get("upload") == "manual" and all(os.path.exists(os.path.join(z, f"s{n}.jpg"))
                                                               for n in range(1, len(p["obrazky"]) + 1))
    print("  hotovo, ověřeno zpětným čtením" if ok else "  POZOR: zpětné čtení nesedí, zkontroluj složku a svazky.json")
    return ok


def main():
    arg = [a for a in sys.argv[1:] if not a.startswith("--")]
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        sys.exit(__doc__)
    if not os.path.exists(os.path.join(ROOT, "data", "STAV.md")):
        sys.exit(f"{ROOT} není složka projektu (chybí data/STAV.md). Spusť projektovou kopii z kořene projektu.")
    svp = os.path.join(ROOT, "data", "svazky.json")
    svazky = json.load(open(svp, encoding="utf-8")) if os.path.exists(svp) else {}
    slozky = [os.path.abspath(a) for a in arg] or [d.rstrip("/\\") for d in sorted(glob.glob(os.path.join(PRAC, "*/")))
                                                    if os.path.exists(os.path.join(d, "obsah.txt"))
                                                    and not d.rstrip("/\\").endswith("_manual")]
    if not slozky:
        sys.exit("Není co zařadit (žádná složka s obsah.txt mimo `_manual`).")
    ok_vse = True
    for s in slozky:
        if not os.path.exists(os.path.join(s, "obsah.txt")):
            print(f"{s}: chybí obsah.txt, zeptej se uživatele na údaje (portaly.md, „Co má obsah.txt říct“)")
            ok_vse = False
            continue
        p = plan(s, svazky)
        print(f"\n{os.path.basename(s)}")
        if "klic" in p:
            print(f"  klíč {p['klic']} ({p['portal']}) → {os.path.relpath(p['slozka_nova'], ROOT)}, {len(p['obrazky'])} snímků → s1…s{len(p['obrazky'])}.jpg")
            print(f"  svazky.json: {p['zaznam'].get('svazek', '')} | {p['zaznam'].get('archiv', '')}")
            for x in kopie_a_odkazy(p):
                print("  " + x)
        for x in p["poznamky"]:
            print("  poznámka: " + x)
        for x in p["problemy"]:
            print("  PROBLÉM: " + x)
        if p["problemy"] and not ("--ignoruj-pocet" in sys.argv and all(x.startswith("počet snímků") for x in p["problemy"])):
            ok_vse = False
            if "--proved" in sys.argv:
                print("  přeskočeno")
            continue
        if "--proved" in sys.argv:
            ok_vse = proved(p) and ok_vse
    if "--proved" not in sys.argv:
        print("\nNáhled, nic se nezměnilo. Potvrď s uživatelem a spusť znovu s --proved.")
    sys.exit(0 if ok_vse else 1)


if __name__ == "__main__":
    main()
