#!/usr/bin/env python3
"""Vyrobí GEDCOM (.ged) z data/osoby.py – pro MacFamilyTree 11, Gramps, Ancestry a další programy.

Použití (z kořene projektu):
  python3 -I tools/ged_export.py                     -> pracovni/gedcom/rodokmen.ged (GEDCOM 5.5.1, UTF-8) + pracovni/gedcom/media/
  python3 -I tools/ged_export.py cesta/strom.ged     -> jiný výstupní soubor, media/ vznikne vedle něj
  … --bez-obrazku                                    -> bez výřezů zápisů (jen .ged)
  … --verze 7                                        -> GEDCOM 7.0 (5.5.1 je kompatibilnější, MacFamilyTree umí obojí)
  … --bez-zivych                                     -> vynechá osoby bez úmrtí narozené před méně než 100 lety

Co se převede: osoby a jejich rodiče podle Kekulého čísel (2n otec, 2n+1 matka), narození (*), sňatek (×) a úmrtí (†)
s datem a místem, čp. jako adresa události, souřadnice z data/mista.json, řemeslo, poznámky, stav jistoty údaje (st),
sourozenci a příbuzní ze SIDE jako poznámka a zápisy z data/zaznamy.json jako zdroje (SOUR) osob, které je citují;
k zdroji se připojí výřez zápisu vyrezy/<klic>.jpg (OBJE), zkopírovaný do media/ vedle .ged – celá složka tvoří jeden export.
Co se nepřevede: ISSUES a HYPOTEZY (jsou pro web a mohou mít citlivý obsah), celé stránky matrik (zdroje/) a ostatní obrázky, osoby „neuveden“
bez údajů (jejich poznámka jde k rodině dítěte) a příčina úmrtí u osob narozených v posledních 100 letech.
Nic se neposílá po síti, soubor vznikne jen na disku. Žijící osoby se bez --bez-zivych exportují také – před předáním
cizí službě (MyHeritage, Ancestry…) použij přepínač.
"""
import calendar, datetime, json, os, re, shutil, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
DATA = os.path.join(ROOT, "data")

MON = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
SEASONS = ("jaro", "léto", "podzim", "zima")
STATUS = {"doc": "doloženo matrikou", "lit": "z literatury", "prob": "pravděpodobné", "fam": "údaj od rodiny",
          "mh": "jen z cizího rodokmenu", "unk": "neznámé"}
NOTE_FACT = re.compile(r"^(provd\.|roz\.|také\b|TÁŽ OSOBA)", re.I)   # volný text, který není řemeslo → poznámka


# ---------- data ----------

def parse_one(txt):
    """Jedno datum na začátku: '14. 2. 1890' | '2. 1890' | '3/1867' | '1890' -> (GEDCOM, zbytek) nebo None."""
    for rx, kind in ((r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{3,4})(?!\d)", "dmy"), (r"(\d{1,2})[./]\s*(\d{3,4})(?!\d)", "my"),
                     (r"(\d{3,4})(?!\d)", "y")):
        m = re.match(rx, txt)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        if kind == "dmy" and 1 <= g[1] <= 12 and 1 <= g[0] <= calendar.monthrange(max(g[2], 1), g[1])[1]:
            return f"{g[0]} {MON[g[1] - 1]} {g[2]}", txt[m.end():]
        if kind == "my" and 1 <= g[0] <= 12:
            return f"{MON[g[0] - 1]} {g[1]}", txt[m.end():]
        if kind == "y":
            return str(g[0]), txt[m.end():]
    return None


def parse_date(txt):
    """Datum na začátku textu faktu -> (GEDCOM datum nebo '', zbytek textu). Co nepoznám, jde jako fráze v závorce."""
    s = txt.strip()
    for words, pre in ((("asi", "cca", "přibližně", "≈"), "ABT "), (("před",), "BEF "), (("po",), "AFT ")):
        m = re.match(r"(?:%s)\s*(?=\d)" % "|".join(re.escape(w) for w in words), s)
        if m:
            r = parse_one(s[m.end():])
            return (pre + r[0], r[1].strip()) if r else ("", s)
    m = re.match(r"mezi\s+", s)
    if m:
        a = parse_one(s[m.end():])
        if a:
            m2 = re.match(r"\s*a\s+", a[1])
            b = parse_one(a[1][m2.end():]) if m2 else None
            if b:
                return f"BET {a[0]} AND {b[0]}", b[1].strip()
    m = re.match(r"(%s)\s+(\d{4})(?!\d)" % "|".join(SEASONS), s)
    if m:
        return f"({m.group(1)} {m.group(2)})", s[m.end():].strip()
    r = parse_one(s)
    if not r:
        return "", s
    m = re.match(r"\s*nebo\s+", r[1])   # „1926 nebo 1927“ GEDCOM neumí → fráze
    if m and parse_one(r[1][m.end():]):
        r2 = parse_one(r[1][m.end():])
        return f"({s[:len(s) - len(r2[1])].strip()})", r2[1].strip()
    return r[0], r[1].strip()


def parse_event(txt, partner=""):
    """Text faktu po symbolu (* × †) -> dict(date, place, addr, cause, note). Co se nedá rozpoznat, nezahodí se – jde do note."""
    date, rest = parse_date(txt)
    if partner and rest.endswith(partner):
        rest = rest[:-len(partner)].strip()
    notes = []
    for m in re.findall(r"\(([^)]*)\)", rest):
        notes.append(m.strip())
    rest = re.sub(r"\s*\([^)]*\)", "", rest)
    addr = ""
    m = re.search(r"\s*\bčp\.\s*(\d+\w*)", rest)
    if m:
        addr = "čp. " + m.group(1)
        rest = (rest[:m.start()] + rest[m.end():]).strip()
    place, _, tail = rest.partition(",")
    return dict(date=date, place=place.strip(), addr=addr, cause=tail.strip(), note=[n for n in notes if n])


def coords(place, addr, mista):
    """(lat, lon) z mista.json: přesný bod domu, jinak střed obce."""
    if not place:
        return None
    e = mista.get(place)
    if e is None:
        for v in mista.values():
            try:
                if v.get("re") and re.search(v["re"], place):
                    e = v
                    break
            except re.error:
                continue
    if not e:
        return None
    num = addr.replace("čp. ", "")
    a = (e.get("adresy") or {}).get(num) if num else None
    for src in (a, e):
        if src and src.get("lat") is not None and src.get("lon") is not None:
            return src["lat"], src["lon"]
    return None


def split_name(n):
    parts = n.split()
    return (" ".join(parts[:-1]), parts[-1]) if len(parts) > 1 else (n, "")


def birth_year(p):
    for f in p.get("f", []):
        if f.strip().startswith("*"):
            m = re.search(r"\d{4}", f)
            if m:
                return int(m.group())
    m = re.search(r"\d{4}", p.get("y", "") or "")
    return int(m.group()) if m else None


def is_dead(p):
    return any(f.strip().startswith("†") for f in p.get("f", [])) or "†" in (p.get("y") or "") \
        or bool(re.search(r"\d\s*[–-]\s*\S*\s*\d{4}", p.get("y") or ""))


# ---------- zápis GEDCOMu ----------

class Out:
    def __init__(self, v7):
        self.v7, self.lines = v7, []

    def _put(self, lvl, tag, val, xref, conc_lvl):
        head = f"{lvl} {xref + ' ' if xref else ''}{tag}"
        if self.v7 or len(val) <= 200:
            self.lines.append((head + " " + val).rstrip())
            return
        self.lines.append(head + " " + val[:200])
        for i in range(200, len(val), 200):   # CONC jen u 5.5.1 (řádek max. 255 znaků); dělí se po znacích, ne po bajtech
            self.lines.append(f"{conc_lvl} CONC {val[i:i + 200]}")

    def add(self, lvl, tag, val="", xref=""):
        val = str(val).replace("\r", "")
        if not re.fullmatch(r"@[^@\s]+@", val):   # odkaz na záznam (@I1@) se neescapuje, text s @ ano
            val = re.sub(r"^@", "@@", val) if self.v7 else val.replace("@", "@@")
        first, *more = val.split("\n")
        self._put(lvl, tag, first, xref, lvl + 1)
        for m in more:
            self._put(lvl + 1, "CONT", m, "", lvl + 1)


def project_version():
    for base in (ROOT, os.path.dirname(ROOT), os.path.join(ROOT, "shared")):
        p = os.path.join(base, "VERZE")
        if os.path.exists(p):
            return open(p, encoding="utf-8-sig").read().strip()
    return ""


def jload(name, default):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)


def build(ns, v7=False, bez_zivych=False, today=None, vyrezy=None):
    """Vrátí (řádky GEDCOMu, statistika). vyrezy = složka s <klic>.jpg; zápisy, k nimž soubor existuje, dostanou OBJE."""
    today = today or datetime.date.today()
    P, SAME = ns.get("P", {}), ns.get("SAME", {})
    SIDE = ns.get("SIDE", [])
    zaznamy = {z["klic"]: z for z in jload("zaznamy.json", [])}
    svazky, mista = jload("svazky.json", {}), jload("mista.json", {})
    stat = dict(osob=0, rodin=0, zdroju=0, vynechano_zive=0, vynechano_neuvedeno=0, data_text=0, chybi_zaznam=0, priciny_vynechany=0)

    def res(k):
        return SAME.get(k, k)

    unk = {k for k, p in P.items() if p.get("st") == "unk" and not p.get("f") and k not in SAME}
    stat["vynechano_neuvedeno"] = len(unk)
    present = {k for k in P if k not in SAME and k not in unk}
    if bez_zivych:
        cut = today.year - 100
        zivi = {k for k in present if not is_dead(P[k]) and (birth_year(P[k]) or 0) > cut}
        present -= zivi
        stat["vynechano_zive"] = len(zivi)

    # rodiny: pár (otec, matka) podle čísel dítěte
    fams, famc = {}, {}
    for k in sorted(present):
        fa, mo = (x if x in present else None for x in (res(2 * k), res(2 * k + 1)))
        if fa is None and mo is None:
            continue
        key = (fa, mo)
        fams.setdefault(key, dict(id=f"@F{len(fams) + 1}@", kids=[], notes=[]))
        fams[key]["kids"].append(k)
        for j in (2 * k, 2 * k + 1):
            if j in unk and P[j].get("note"):
                fams[key]["notes"].append(P[j]["note"])
        famc[k] = fams[key]["id"]
    fams_of = {}
    for (fa, mo), f in fams.items():
        for k in (fa, mo):
            if k is not None:
                fams_of.setdefault(k, []).append(f["id"])

    # zdroje použité exportovanými osobami
    used = []
    for k in sorted(present):
        for r in P[k].get("r", []):
            if r in zaznamy and r not in used:
                used.append(r)
            elif r not in zaznamy:
                stat["chybi_zaznam"] += 1
    sid = {r: f"@S{i}@" for i, r in enumerate(used, 1)}
    obr = [r for r in used if vyrezy and re.fullmatch(r"[\w.-]+", r) and os.path.isfile(os.path.join(vyrezy, r + ".jpg"))]
    mid = {r: f"@M{i}@" for i, r in enumerate(obr, 1)}
    stat["media"] = obr

    o = Out(v7)

    def event(lvl, tag, ev, dead=False, recent=False):
        if recent and ev["cause"]:   # příčina úmrtí je zdravotní údaj: u osob z posledních ~100 let se nevyváží (soukromi.md)
            ev = dict(ev, cause="")
            stat["priciny_vynechany"] += 1
        details = ev["date"] or ev["place"] or ev["addr"] or ev["cause"] or ev["note"]
        o.add(lvl, tag, "" if details else "Y")
        if ev["date"]:
            o.add(lvl + 1, "DATE", ev["date"])
            if ev["date"].startswith("("):
                stat["data_text"] += 1
        if ev["place"]:
            o.add(lvl + 1, "PLAC", ev["place"])
            c = coords(ev["place"], ev["addr"], mista)
            if c:
                o.add(lvl + 2, "MAP")
                o.add(lvl + 3, "LATI", f"{'N' if c[0] >= 0 else 'S'}{abs(c[0]):.6f}")
                o.add(lvl + 3, "LONG", f"{'E' if c[1] >= 0 else 'W'}{abs(c[1]):.6f}")
        if ev["addr"]:
            o.add(lvl + 1, "ADDR", ev["addr"])
        if ev["cause"]:
            if dead:
                o.add(lvl + 1, "CAUS", ev["cause"])
            else:
                o.add(lvl + 1, "NOTE", ev["cause"])
        for n in ev["note"]:
            o.add(lvl + 1, "NOTE", n)

    # hlavička
    o.add(0, "HEAD")
    o.add(1, "GEDC")
    o.add(2, "VERS", "7.0" if v7 else "5.5.1")
    if not v7:
        o.add(2, "FORM", "LINEAGE-LINKED")
        o.add(1, "CHAR", "UTF-8")
    o.add(1, "SOUR", "rodokmen-skill")
    ver = project_version()
    if ver:
        o.add(2, "VERS", ver)
    o.add(1, "DATE", f"{today.day} {MON[today.month - 1]} {today.year}")
    if not v7:
        o.add(1, "SUBM", "@U1@")
        o.add(0, "SUBM", xref="@U1@")
        o.add(1, "NAME", "rodokmen-skill")

    # osoby
    marr_facts = {}
    for k in sorted(present):
        p = P[k]
        given, sur = split_name(p["n"])
        o.add(0, "INDI", xref=f"@I{k}@")
        o.add(1, "NAME", f"{given} /{sur}/" if sur else given)
        if given:
            o.add(2, "GIVN", given)
        if sur:
            o.add(2, "SURN", sur)
        sex = p.get("sex") if k == 1 else ("M" if k % 2 == 0 else "F")
        if sex in ("M", "F"):
            o.add(1, "SEX", sex)
        free, notes = [], []
        for f in p.get("f", []):
            s = f.strip()
            if s.startswith("*"):
                event(1, "BIRT", parse_event(s[1:].strip()))
            elif s.startswith("†"):
                event(1, "DEAT", parse_event(s[1:].strip()), dead=True,
                      recent=(birth_year(p) or 0) > today.year - 100)
            elif s.startswith("×"):
                marr_facts.setdefault(k, []).append(s[1:].strip())
            elif s:
                (notes if NOTE_FACT.match(s) else free).append(s)
        for s in free:
            o.add(1, "OCCU", s)
        if p.get("st") in STATUS:
            notes.insert(0, f"Jistota údaje: {STATUS[p['st']]}.")
        if p.get("note"):
            notes.append(p["note"])
        for s in SIDE:
            if s.get("k") == k and s.get("n"):
                notes.append(f"Příbuzný: {s['n']}" + (f" – {s['t']}" if s.get("t") else ""))
        for n in notes:
            o.add(1, "NOTE", n)
        for r in p.get("r", []):
            if r in sid:
                o.add(1, "SOUR", sid[r])
                z, sv = zaznamy[r], svazky.get(zaznamy[r].get("svazek", ""), {})
                page = ", ".join(x for x in (sv.get("svazek", ""), f"snímek {z['snimek']}" if z.get("snimek") else "") if x)
                if page:
                    o.add(2, "PAGE", page)
        if k in famc:
            o.add(1, "FAMC", famc[k])
        for fid in fams_of.get(k, []):
            o.add(1, "FAMS", fid)
        stat["osob"] += 1

    # rodiny
    for (fa, mo), f in fams.items():
        o.add(0, "FAM", xref=f["id"])
        if fa is not None:
            o.add(1, "HUSB", f"@I{fa}@")
        if mo is not None:
            o.add(1, "WIFE", f"@I{mo}@")
        for kid in f["kids"]:
            o.add(1, "CHIL", f"@I{kid}@")
        if fa is not None and mo is not None:   # sňatek: první fakt ×, který jmenuje partnera
            for me, other in ((fa, mo), (mo, fa)):
                hit = next((t for t in marr_facts.get(me, []) if P[other]["n"] in t), None)
                if hit:
                    event(1, "MARR", parse_event(hit, P[other]["n"]))
                    break
        for n in f["notes"]:
            o.add(1, "NOTE", n)
        stat["rodin"] += 1

    # zdroje
    for r in used:
        z, sv = zaznamy[r], svazky.get(zaznamy[r].get("svazek", ""), {})
        o.add(0, "SOUR", xref=sid[r])
        o.add(1, "TITL", z.get("nazev", r))
        publ = "; ".join(x for x in (sv.get("archiv", ""), sv.get("svazek", "")) if x)
        if publ:
            o.add(1, "PUBL", publ)
        if z.get("datum"):
            o.add(1, "NOTE", f"Datum zápisu: {z['datum']}")
        if z.get("shrnuti"):
            o.add(1, "NOTE", z["shrnuti"])
        url = z.get("odkaz") or sv.get("url", "")
        if url:
            o.add(1, "NOTE", f"Odkaz: {url}")
        if r in mid:
            o.add(1, "OBJE", mid[r])
        stat["zdroju"] += 1

    # obrázky (výřezy zápisů z matrik): soubory leží v media/ vedle .ged
    for r in obr:
        o.add(0, "OBJE", xref=mid[r])
        o.add(1, "FILE", f"media/{r}.jpg")
        o.add(2, "FORM", "image/jpeg" if v7 else "jpg")
        o.add(2, "TITL", zaznamy[r].get("nazev", r))

    o.add(0, "TRLR")
    return o.lines, stat


def main():
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        sys.exit(__doc__.strip())
    for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    v7 = False
    if "--verze" in args:
        i = args.index("--verze")
        v = args[i + 1] if i + 1 < len(args) else ""
        if v not in ("5", "7"):
            sys.exit("--verze: použij 5 (GEDCOM 5.5.1) nebo 7 (GEDCOM 7.0).")
        v7 = v == "7"
        del args[i:i + 2]
    zivi = "--bez-zivych" in args
    bez_obr = "--bez-obrazku" in args
    args = [a for a in args if a not in ("--bez-zivych", "--bez-obrazku")]
    if any(a.startswith("--") for a in args) or len(args) > 1:
        sys.exit("Neznámý přepínač nebo víc výstupních souborů – viz --help.")
    path = os.path.join(DATA, "osoby.py")
    if not os.path.exists(path):
        sys.exit("V projektu chybí data/osoby.py – není co exportovat.")
    ns = {}
    exec(open(path, encoding="utf-8-sig").read(), ns)
    if not ns.get("P"):
        sys.exit("V data/osoby.py je prázdné P – není co exportovat.")
    out = args[0] if args else os.path.join(ROOT, "pracovni", "gedcom", "rodokmen.ged")
    vyrezy = os.path.join(ROOT, "vyrezy")
    lines, st = build(ns, v7=v7, bez_zivych=zivi, vyrezy=None if bez_obr else vyrezy)
    slozka = os.path.dirname(os.path.abspath(out))
    os.makedirs(slozka, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    if st["media"]:
        os.makedirs(os.path.join(slozka, "media"), exist_ok=True)
        for r in st["media"]:
            shutil.copyfile(os.path.join(vyrezy, r + ".jpg"), os.path.join(slozka, "media", r + ".jpg"))
    print(f"{out}: GEDCOM {'7.0' if v7 else '5.5.1'}, {st['osob']} osob, {st['rodin']} rodin, {st['zdroju']} zdrojů")
    if st["media"]:
        print(f"  {len(st['media'])} výřezů zápisů zkopírováno do {os.path.join(slozka, 'media')}")
    if st["vynechano_neuvedeno"]:
        print(f"  vynecháno {st['vynechano_neuvedeno']} osob „neuveden“ bez údajů (jejich poznámka je u rodiny dítěte)")
    if st["vynechano_zive"]:
        print(f"  vynecháno {st['vynechano_zive']} možná žijících osob (--bez-zivych)")
    if st["data_text"]:
        print(f"  {st['data_text']} dat nešlo převést na GEDCOM, jsou zapsána jako text v závorce")
    if st["priciny_vynechany"]:
        print(f"  příčina úmrtí vynechána u {st['priciny_vynechany']} osob narozených v posledních 100 letech (zdravotní údaj)")
    if st["chybi_zaznam"]:
        print(f"  POZOR: {st['chybi_zaznam']} citací klíče, který není v zaznamy.json (vynecháno)")
    print("Import: MacFamilyTree 11 → úvodní obrazovka → Import GEDCOM file (složku media/ nech vedle souboru .ged).")


if __name__ == "__main__":
    main()
