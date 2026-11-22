"""Test ged_export.py: převod dat projektu na GEDCOM (pro MacFamilyTree 11 aj.).

Z kořene repozitáře:
  python3 -I tests/ged_export/test_ged_export.py shared/tools
  (Windows: python -I -X utf8 …)
Každý případ postaví dočasný projekt z vymyšlených ukázkových dat (shared/template/ukazka), zkopíruje do něj nástroje
a pustí je. Nic nestahuje. Kontroluje oba směry: že export vznikne správně a projde zpět přes ged_import.py
(stejní předci, stejná čísla, data a místa), i že co do souboru nepatří (ISSUES, žijící s --bez-zivych), v něm není.
"""
import importlib.util, os, re, shutil, subprocess, sys, tempfile

TOOLS = os.path.abspath(sys.argv[1])
UKAZKA = os.path.join(os.path.dirname(TOOLS), "template", "ukazka")
PY = [sys.executable, "-I", "-X", "utf8"]
VYSLEDKY = []


def ma(nazev, ok, detail=""):
    VYSLEDKY.append(ok)
    print(("OK  " if ok else "CHYBA ") + nazev + ("" if ok else f"\n    {detail}"))


def projekt():
    tmp = tempfile.mkdtemp(prefix="ged_export_")
    os.makedirs(os.path.join(tmp, "tools"))
    os.makedirs(os.path.join(tmp, "data"))
    for n in ("ged_export.py", "ged_import.py"):
        shutil.copy(os.path.join(TOOLS, n), os.path.join(tmp, "tools", n))
    for n in ("osoby.py", "zaznamy.json", "svazky.json", "mista.json"):
        shutil.copy(os.path.join(UKAZKA, n), os.path.join(tmp, "data", n))
    return tmp


def spust(tmp, *args, nastroj="ged_export.py"):
    return subprocess.run(PY + [os.path.join("tools", nastroj), *args], cwd=tmp, capture_output=True, text=True,
                          encoding="utf-8")


def zaznamy(text):
    """GEDCOM -> {xref: [(úroveň, tag, hodnota)]} (CONC/CONT se nesklá, test je nepotřebuje)."""
    recs, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"(\d+) (@\S+@ )?(\S+) ?(.*)$", line)
        assert m, f"řádek není GEDCOM: {line!r}"
        lvl, xref, tag, val = int(m[1]), (m[2] or "").strip(), m[3], m[4]
        if lvl == 0:
            cur = recs.setdefault(xref or f"#{tag}", [])
        cur.append((lvl, tag, val))
    return recs


def nacti_modul(tmp):
    spec = importlib.util.spec_from_file_location("ged_export_t", os.path.join(tmp, "tools", "ged_export.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tmp = projekt()
try:
    # 1. export projde a má správnou hlavičku a konec
    r = spust(tmp, "out.ged")
    ma("export skončí kódem 0", r.returncode == 0, r.stdout + r.stderr)
    text = open(os.path.join(tmp, "out.ged"), encoding="utf-8").read()
    ma("hlavička GEDCOM 5.5.1, UTF-8, konec TRLR",
       text.startswith("0 HEAD\n") and "\n2 VERS 5.5.1\n" in text and "\n1 CHAR UTF-8\n" in text and text.rstrip().endswith("0 TRLR"))
    ma("výstup jde z ukázky: bez BOM, řádky max. 255 znaků",
       not text.startswith("﻿") and max(len(x) for x in text.splitlines()) <= 255)

    # 2. všechny odkazy na záznamy existují a nejsou escapované
    recs = zaznamy(text)
    odkazy = [v for rec in recs.values() for (_, t, v) in rec if t in ("HUSB", "WIFE", "CHIL", "FAMC", "FAMS", "SOUR", "SUBM")
              and v.startswith("@")]
    chybi = sorted({o for o in odkazy if o not in recs})
    ma("odkazy HUSB/WIFE/CHIL/FAMC/FAMS/SOUR ukazují na existující záznamy a nejsou escapované", odkazy and not chybi,
       f"chybí: {chybi[:5]}" if chybi else "žádné odkazy")

    # 3. struktura: Petr (1) má rodiče Josefa Nováka a Evu Dvořákovou a ti se vzali (rodiče 2, 3 sice mají MARR u svých rodičů)
    def jmeno(xref):
        return next(v for (_, t, v) in recs[xref] if t == "NAME")
    famc = next(v for (_, t, v) in recs["@I1@"] if t == "FAMC")
    fam = recs[famc]
    otec = next(v for (_, t, v) in fam if t == "HUSB")
    matka = next(v for (_, t, v) in fam if t == "WIFE")
    ma("osoba 1 má v rodině otce Josefa Nováka a matku Evu Dvořákovou",
       jmeno(otec).startswith("Josef /Novák/") and jmeno(matka).startswith("Eva /Dvořáková/"), f"{jmeno(otec)}, {jmeno(matka)}")

    # 4. sňatek rodičů č. 8 a 9 má datum, místo a souřadnice; narození s čp. má adresu
    f8 = next(rec for x, rec in recs.items() if ("1", "HUSB", "@I8@") in [(str(a), b, c) for a, b, c in rec])
    marr = [(l, t, v) for (l, t, v) in f8 if l >= 2]
    ma("sňatek Jana a Josefy: 20 JUN 1919, Holice, souřadnice",
       ("2", "DATE", "20 JUN 1919") in [(str(l), t, v) for l, t, v in marr] and any(t == "PLAC" and v == "Holice" for _, t, v in marr)
       and any(t == "LATI" for _, t, v in marr), str(marr))
    i8 = recs["@I8@"]
    ma("narození Jana 14 FEB 1890 s adresou čp. 112",
       (2, "DATE", "14 FEB 1890") in i8 and (2, "ADDR", "čp. 112") in i8 and (1, "OCCU", "kovář v Holicích") in i8, str(i8[:14]))
    ma("pohlaví podle čísla (8 = M, 9 = F), osoba 1 podle sex",
       (1, "SEX", "M") in i8 and (1, "SEX", "F") in recs["@I9@"] and (1, "SEX", "M") in recs["@I1@"])

    # 5. zdroje: osoba 8 cituje SOUR se stránkou, SOUR má název, archiv a odkaz
    cit = [(l, t, v) for (l, t, v) in i8 if t == "SOUR"]
    ma("osoba 8 cituje dva zdroje a citace má PAGE se snímkem", len(cit) == 2 and "snímek 57" in text, str(cit))
    s1 = recs[cit[0][2]]
    ma("zdroj má TITL, PUBL (archiv; svazek) a odkaz",
       (1, "TITL", "Křest Jana Nováka") in s1 and any(t == "PUBL" and "Státní oblastní archiv" in v for _, t, v in s1)
       and any(t == "NOTE" and v.startswith("Odkaz: https://") for _, t, v in s1), str(s1))

    # 6. nepatří dovnitř: ISSUES/HYPOTEZY a osoba „neuveden“ bez údajů
    ns = {}
    exec(open(os.path.join(tmp, "data", "osoby.py"), encoding="utf-8").read(), ns)
    citlive = [q for q, _ in ns.get("ISSUES", [])] + [h.get("nadpis", "") for h in ns.get("HYPOTEZY", [])]
    citlive = [c for c in citlive if len(c) > 8]
    unikly = [c for c in citlive if c in text]
    ma("ISSUES a HYPOTEZY v souboru nejsou", citlive and not unikly, f"{unikly[:2]}" if unikly else "ukázka je nemá – test nic neověří")
    ma("osoba „otec neuveden“ není samostatný záznam, její poznámka je u rodiny",
       "otec neuveden" not in text and "nemanželská" in text)

    # 7. zpátky přes ged_import.py: stejní předci s týmiž čísly
    r = spust(tmp, "out.ged", "Petr Novák", nastroj="ged_import.py")
    radky = {int(m[1]): m[2].strip() for m in re.finditer(r"^\s*(\d+) \| ([^|]+)\|", r.stdout, re.M)}
    ocek = {k: v["n"] for k, v in ns["P"].items() if k not in ns["SAME"] and not (v.get("st") == "unk" and not v.get("f"))}
    rozdil = {k: (radky.get(k), n) for k, n in ocek.items() if radky.get(k) != n}
    ma("round-trip: ged_import vrátí stejné předky pod stejnými Kekulého čísly", r.returncode == 0 and not rozdil,
       f"{len(rozdil)} rozdílů, např. {list(rozdil.items())[:3]}\n{r.stderr[:300]}")
    ma("round-trip: narození Jana 14. 2. 1890 Holice a sňatek 20. 6. 1919 s Josefou Pokornou",
       "* 14. 2. 1890 Holice" in r.stdout and "× 20. 6. 1919 Holice Josefa Pokorná" in r.stdout, r.stdout[:600])

    # 8. --bez-zivych: pryč Petr, Josef a Eva (bez úmrtí, narození po r. 1926); zůstane František (†) a Jan
    r = spust(tmp, "zive.ged", "--bez-zivych")
    z = open(os.path.join(tmp, "zive.ged"), encoding="utf-8").read()
    ma("--bez-zivych vynechá osoby 1, 2, 3 a ponechá zemřelé",
       r.returncode == 0 and "@I1@ INDI" not in z and "@I2@ INDI" not in z and "@I3@ INDI" not in z
       and "@I4@ INDI" in z and "@I8@ INDI" in z, r.stdout + r.stderr)
    zr = zaznamy(z)
    odk = [v for rec in zr.values() for (_, t, v) in rec if t in ("HUSB", "WIFE", "CHIL", "FAMC", "FAMS") and v.startswith("@")]
    ma("--bez-zivych nenechá visící odkazy", all(o in zr for o in odk), str([o for o in odk if o not in zr][:3]))

    # 9. GEDCOM 7.0: jiná hlavička, bez CHAR
    spust(tmp, "v7.ged", "--verze", "7")
    v7 = open(os.path.join(tmp, "v7.ged"), encoding="utf-8").read()
    ma("--verze 7: GEDC VERS 7.0, bez CHAR, bez SUBM", "2 VERS 7.0\n" in v7 and "CHAR" not in v7.split("0 @I1@")[0]
       and "SUBM" not in v7)

    # 10. převod dat a míst (jednotkově)
    m = nacti_modul(tmp)
    tab = {"14. 2. 1890": "14 FEB 1890", "1890": "1890", "3. 1867": "MAR 1867", "3/1867": "MAR 1867",
           "asi 1720": "ABT 1720", "před 1740": "BEF 1740", "po 1921": "AFT 1921", "mezi 1850 a 1860": "BET 1850 AND 1860",
           "1926 nebo 1927": "(1926 nebo 1927)", "podzim 1951": "(podzim 1951)", "31. 2. 1890": ""}
    chyby = {k: m.parse_date(k)[0] for k, v in tab.items() if m.parse_date(k)[0] != v}
    ma("převod českých dat na GEDCOM (tabulka případů)", not chyby, str(chyby))
    ev = m.parse_event("1855 Holice, na choleru")
    ma("událost: místo, příčina po čárce", ev["place"] == "Holice" and ev["cause"] == "na choleru" and ev["date"] == "1855", str(ev))
    ev = m.parse_event("1862 Ostřetín čp. 23 (podle stromu)")
    ma("událost: čp. jako adresa, závorka jako poznámka",
       ev["place"] == "Ostřetín" and ev["addr"] == "čp. 23" and ev["note"] == ["podle stromu"], str(ev))
    ev = m.parse_event("8. 11. 1924 Holice Ludmila Hrubá", "Ludmila Hrubá")
    ma("sňatek: jméno partnera se z místa odstraní", ev["place"] == "Holice" and ev["date"] == "8 NOV 1924", str(ev))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{sum(VYSLEDKY)}/{len(VYSLEDKY)} v pořádku")
sys.exit(0 if all(VYSLEDKY) else 1)
