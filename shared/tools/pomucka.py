#!/usr/bin/env python3
"""Archivní pomůcka NAD 190 (SOA Hradec Králové, Sbírka matrik Východočeského kraje): rozbor PDF a hledání knih.

Pomůcka je PDF o ~4350 stranách – rejstřík všech východočeských matrik s odkazy na ARON (`apu`) a na ZIP se snímky.
Odkazy jsou anotace v PDF, `pdftotext` je nevypíše; nástroj je vytáhne přes `qpdf --json` a spáruje s knihami podle pořadí.
Nic nestahuje ze sítě: PDF si stáhni ručně (adresa a postup v reference/portaly.md, „Archivní pomůcka“).

Použití (z kořene projektu):
  pomucka.py rozbor <pomucka.pdf> [pracovni/pomucka_190.json]
      rozebere PDF do JSON (jednorázově, trvá desítky sekund; potřebuje `qpdf` a `pdftotext`)
  pomucka.py hledej <obec> [N|O|Z] [rok] [--vse] [--json soubor]
      najde knihy: obec se hledá v názvu fary a v „matričních místech“ (bez ohledu na diakritiku a velikost písmen);
      N = narození, O = oddaní, Z = zemřelí; rok = kniha, která ho pokrývá; --vse = i knihy bez odkazu (jen badatelna)
Odkaz `aron` je adresa svazku v ARON (apu_id je poslední část; pak `aron_img.py <apu_id> info`), `zip` všechny snímky.

Instalace závislostí: macOS `brew install qpdf poppler`, Windows `winget install qpdf.qpdf` a poppler (pdftotext).
"""
import json, os, re, shutil, subprocess, sys, tempfile, unicodedata
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VYSTUP = os.path.join(ROOT, "pracovni", "pomucka_190.json")

LV = re.compile(r"^\s+(\d)\s{2,}(\d+)(?:\s{2,}(\S.*?))?\s*$")
HDR = re.compile(r"^(Úrov\. Označení|\s+Obsah\s+Datace)")
PG = re.compile(r"^\s+\d+\s*$")
TYPY = {"N": "NAROZEN", "O": "ODDAN", "Z": "ZEMŘEL"}


def bez_diakritiky(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def dvojice_odkazu(uris):
    """(ARON, ZIP) po dvou v pořadí z PDF; když pořadí neodpovídá, skončí – párování by bylo špatně."""
    if len(uris) % 2:
        sys.exit(f"Lichý počet odkazů v PDF ({len(uris)}): pomůcka má jiný tvar, než nástroj čeká. Nic jsem nezapsal.")
    out = []
    for i in range(0, len(uris), 2):
        a, z = uris[i], uris[i + 1]
        if "/apu/" not in a or not z.lower().endswith(".zip"):
            sys.exit(f"Odkazy {i + 1}. a {i + 2}. nejsou dvojice (ARON, ZIP): {a} / {z}. Nic jsem nezapsal.")
        out.append((a, z))
    return out


def rozeber(txt, uris):
    """Text z `pdftotext -layout` + seznam odkazů z PDF → (knihy, počet spárovaných odkazů, počet dvojic v PDF)."""
    pary = dvojice_odkazu(uris)
    start = txt.index("215000010/190")
    radky = txt[start:].replace("\f", "\n").split("\n")
    recs, jmena, cur, pend_level, pend = [], {}, None, None, None
    for ln in radky:
        if HDR.match(ln) or PG.match(ln) or not ln.strip():
            continue
        m = LV.match(ln)
        if m:
            if cur:
                recs.append(cur)
                cur = None
            pend_level, pend = int(m.group(1)), m
            continue
        if pend_level:
            if re.match(r"^\s+(původní signatura|signatura|neplatné inventární)", ln) or pend_level == 4:
                cur = {"por": int(pend.group(2)), "ukl": pend.group(3),
                       "cesta": [jmena.get(i, "") for i in (1, 2, 3) if i < pend_level or i == 3 and pend_level > 3],
                       "raw": [ln]}
                pend_level = None
                continue
            jmena[pend_level] = ln.strip()
            for k in list(jmena):
                if k > pend_level:
                    del jmena[k]
            pend_level = None
            continue
        if cur is not None:
            cur["raw"].append(ln)
    if cur:
        recs.append(cur)
    out, n = [], 0
    for r in recs:
        raw = r.pop("raw")
        title, date, place, mode, extra = [], "", [], "head", {}
        for ln in raw:
            s = ln.strip()
            if s.startswith("původní signatura:"):
                extra["puvodni_sign"] = s.split(":", 1)[1].strip()
                continue
            if s.startswith("signatura:"):
                extra["sign"] = s.split(":", 1)[1].strip()
                continue
            if s.startswith("neplatné inventární číslo"):
                extra["neplatne_inv"] = s.split(":", 1)[1].strip()
                continue
            if s.startswith("odkazy:"):
                if n >= len(pary):
                    sys.exit("Knih s odkazy je v textu víc než odkazů v PDF – pomůcka má jiný tvar. Nic jsem nezapsal.")
                r["aron"], r["zip"] = pary[n]
                n += 1
                mode = "after"
                continue
            if s.startswith("Stáhnout všechny"):
                continue
            if s.startswith("matriční místo:"):
                mode = "place"
                place.append(s.split(":", 1)[1].strip())
                continue
            if re.match(r"^(tematický popis|fyzický stav|existence kopií|úřední kniha|čeština|němčina|latina|"
                        r"[a-zěščřžýáíé, ]+; [\d,]+x)", s):
                mode = "meta"
                m = re.search(r"(\d+) fol\.", s)
                if m:
                    r["fol"] = int(m.group(1))
                continue
            if mode == "head":
                parts = re.split(r"\s{3,}", s)
                title.append(parts[0])
                if len(parts) > 1:
                    date = parts[-1]
            elif mode == "place":
                place.append(s)
        r.update(extra)
        r["popis"] = " ".join(title)
        r["datace"] = date
        r["misto"] = " ".join(place)
        out.append(r)
    return out, n, len(pary)


def odkazy_z_pdf(pdf, tmp):
    """Odkazy (/URI) z anotací stránek v pořadí stránek a anotací (`qpdf --json`); pořadí objektů v souboru neplatí."""
    js = os.path.join(tmp, "pomucka.json")
    p = subprocess.run(["qpdf", "--json=2", "--json-key=pages", "--json-key=qpdf", pdf, js], capture_output=True, text=True)
    if p.returncode not in (0, 3):   # 3 = varování, výstup vznikl
        sys.exit(f"qpdf selhal (rc={p.returncode}): {p.stderr.strip()[:300]}")
    with open(js, encoding="utf-8") as f:
        d = json.load(f)
    objs = d["qpdf"][1]

    def hodnota(x):
        while isinstance(x, str) and ("obj:" + x) in objs:
            x = objs["obj:" + x]["value"]
        return x

    out = []
    for pg in d["pages"]:
        annots = hodnota(hodnota(pg["object"]).get("/Annots")) or []
        for a in annots:
            uri = (hodnota(hodnota(a).get("/A")) or {}).get("/URI")
            if isinstance(uri, str):
                out.append(uri[2:] if uri.startswith("u:") else uri)
    return out


def cmd_rozbor(args):
    if not args:
        sys.exit(__doc__)
    pdf = args[0]
    vystup = args[1] if len(args) > 1 else VYSTUP
    if not os.path.isfile(pdf):
        sys.exit(f"PDF {pdf} neexistuje.")
    for nastroj, rada in (("qpdf", "brew install qpdf"), ("pdftotext", "brew install poppler")):
        if not shutil.which(nastroj):
            sys.exit(f"Chybí {nastroj}. Nainstaluj ho (macOS: {rada}) a spusť nástroj znovu.")
    with tempfile.TemporaryDirectory() as tmp:
        uris = odkazy_z_pdf(pdf, tmp)
        txt_path = os.path.join(tmp, "pomucka.txt")
        p = subprocess.run(["pdftotext", "-layout", pdf, txt_path], capture_output=True, text=True)
        if p.returncode:
            sys.exit(f"pdftotext selhal (rc={p.returncode}): {p.stderr.strip()[:300]}")
        with open(txt_path, encoding="utf-8") as f:
            txt = f.read()
    if "215000010/190" not in txt:
        sys.exit("V textu není „215000010/190“ – to není Archivní pomůcka NAD 190. Nic jsem nezapsal.")
    knihy, spar, pary = rozeber(txt, uris)
    if spar != pary:
        sys.exit(f"Spárováno {spar} odkazů z {pary}: kniha s odkazem se v textu nenašla nebo je jich méně. Nic jsem nezapsal.")
    os.makedirs(os.path.dirname(os.path.abspath(vystup)), exist_ok=True)
    with open(vystup, "w", encoding="utf-8") as f:
        json.dump(knihy, f, ensure_ascii=False, indent=0)
    print(f"{len(knihy)} knih, odkazů spárováno {spar} z {pary}, bez odkazu {len(knihy) - spar} → {vystup}")


def roky(dat):
    r = [int(x) for x in re.findall(r"\d{4}", dat)]
    return (min(r), max(r)) if r else None


def hledej(knihy, obec, typ=None, rok=None, vse=False):
    o = bez_diakritiky(obec)
    nalezy = []
    for r in knihy:
        if "aron" not in r and not vse:
            continue
        if not (re.search(r"\b" + re.escape(o), bez_diakritiky(r["misto"])) or o in bez_diakritiky(" ".join(r["cesta"]))):
            continue
        if typ and TYPY[typ] not in r["popis"].upper() and "ZEMŘELÝCH, ODDANÝCH" not in r["popis"].upper():
            continue
        if rok:
            ry = roky(r["datace"])
            if not ry or not ry[0] <= rok <= ry[1]:
                continue
        nalezy.append(r)
    return nalezy


def cmd_hledej(args):
    soubor = VYSTUP
    if "--json" in args:
        i = args.index("--json")
        soubor = args[i + 1] if i + 1 < len(args) else sys.exit("Za --json chybí soubor.")
        args = args[:i] + args[i + 2:]
    a = [x for x in args if not x.startswith("--")]
    if not a:
        sys.exit(__doc__)
    typ = rok = None
    for x in a[1:]:
        if x.upper() in TYPY:
            typ = x.upper()
        elif x.isdigit():
            rok = int(x)
        else:
            sys.exit(f"Nerozumím argumentu „{x}“ (čekám N, O, Z nebo rok).")
    if not os.path.isfile(soubor):
        sys.exit(f"Chybí {soubor}. Nejdřív: pomucka.py rozbor <pomucka.pdf>")
    with open(soubor, encoding="utf-8") as f:
        knihy = json.load(f)
    nalezy = hledej(knihy, a[0], typ, rok, "--vse" in args)
    for r in nalezy:
        print(f"[{r['por']}] {' / '.join(r['cesta'][1:])} | {r['popis'][:110]} | {r['datace']} | "
              f"sign. {r.get('sign', '?')} | {r.get('fol', '?')} fol.")
        print("    " + (r.get("zip") or "BEZ ODKAZU (jen badatelna)") + ("\n    " + r["aron"] if "aron" in r else ""))
    print(f"{len(nalezy)} knih.", file=sys.stderr)


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if argv[0] == "rozbor":
        cmd_rozbor(argv[1:])
    elif argv[0] == "hledej":
        cmd_hledej(argv[1:])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
