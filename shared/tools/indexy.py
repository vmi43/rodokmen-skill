#!/usr/bin/env python3
"""Indexy knih: přepsaný rejstřík nebo rychlý průchod celou knihou, aby se k téže knize nešlo vracet kvůli každému jménu.
Bez sítě. Index je VODÍTKO (stav „index“), ne doklad: zásah se vždy ověří na snímku a uloží šesti kroky (zapis.py).

Použití (z kořene projektu `python3 -I tools/indexy.py …`):
  indexy.py pridej <klíč svazku> <vstup.json|-> [--cetl model/effort]
                                                  přidá řádky do data/indexy/<klíč>.tsv (soubor s JSON polem objektů
                                                  se sloupci níže; napiš ho nástrojem Write do pracovni/). Klíč musí být
                                                  ve data/svazky.json. Shodný řádek (typ, snímek, osoby, datum, obec, strana) se nepřidá podruhé.
                                                  Řádek bez `cetl` dostane „<model/effort> <dnešní datum>“ z --cetl.
  indexy.py hledej <část jména> [--ves V] [--klic K] [--typ N|O|Z|I]
                                                  najde řádky ve všech indexech (bez ohledu na diakritiku a velikost písmen);
                                                  u každého indexu řekne, co pokrývá, takže „jinde nejsou“ má váhu;
                                                  řádky rejstříku mají typ I, ne N/O/Z: `--typ Z` vyřadí i rejstřík
                                                  zemřelých (nástroj řekne kolik), pro ten zadej `--typ I` nebo nic
  indexy.py stav                                  přehled indexů: svazek, počet řádků, rozsah snímků, kolik řádků je „?“
  indexy.py mapa <klíč svazku> <písmeno>=<od>-<do> […]
                                                  zapíše, na kterých snímcích svazku je které písmeno rejstříku
                                                  (např. `mapa abc12345 A=3-4 B=4-6 N=21-23`); písmeno piš, jak ho rejstřík
                                                  má (N, Č, Ch, W); opakovaný zápis písmeno přepíše
  indexy.py prepsano <klíč svazku> <písmeno> […] | vse <od>-<do>
                                                  označí písmeno (zmapované) za přepsané celé, tedy řádky ze všech jeho
                                                  snímků jsou v indexu; `vse` = přepsaný celý rejstřík na snímcích od–do

Rejstřík se přepisuje po písmenech, jen podle potřeby (hledá se Novák → písmeno N). Evidence písmen je v
data/indexy/<klíč>.pismena.json a `hledej` podle ní říká, jestli neshoda něco znamená: u svazku s evidencí platí
„nenalezeno“ jen pro přepsaná písmena a u nepřepsaného písmene nástroj napíše, na kterých snímcích ho najdeš.
Upozorní i na obvyklé jiné tvary počátečního písmene (Vávra = Wawra, Č = Cz/Tsch, Š/Ž = Sch).

Sloupce TSV (pevné pořadí, UTF-8, LF, první řádek je záhlaví). Prvních devět je totéž jako v komunitním indexu matrik
(pe-pan/matriky-index, `precteno.tsv`), poslední dva jsou naše:
  snimek   snímek TOHOTO svazku, na kterém je řádek přečtený (u rejstříku snímek rejstříku)
  datum    datum události (RRRR-MM-DD, neúplné RRRR-MM nebo RRRR), je-li; nic jiného (ne „1832[?]“) – nejistota patří do
           ostatni a jistoty. `pridej` jiný tvar odmítne, stejně jako `kniha` ve tvaru samotného roku
  typ      N narození | O oddaní | Z zemřelí | I řádek rejstříku (jen náš; komunitní index rejstříky nemá)
  obec     ves a číslo popisné: „Lhota 12“
  osoby    role a jména: „zemřelý: Josef Hora; otec: Jan Hora“, „dítě: …; otec: …; matka: … roz. …; kmotr: …“,
           „ženich: …; nevěsta: …; otec ženicha: …“; nejisté kusy s [?] přímo v textu; u rejstříku jen jméno
  ostatni  volný text: věk, příčina, kdo pohřbíval, poznámky; ŽÁDNÉ závěry o tom, kdo osoba je a čí je příbuzný
  jistota  vysoká | střední | nízká  (vybledlé a nečitelné řádky piš s nízkou)
  cetl     kdo a čím četl: „claude-opus-5-5/high 2026-11-24“ (model/effort a datum; pomocník na Opusu to uvede do vstupu,
           nebo ho doplní `--cetl model/effort` při pridej)
  odkaz    adresa snímku, je-li (volitelné; vyplňuje ji až export)
  strana   strana/folio v knize (u rejstříku strana, na kterou odkazuje) – jen náš
  kniha    jen u typu I: značka knihy, do které rejstřík odkazuje (např. „N 1850–1870“; značka „littera matricae“ jako „Z lit. L.P“) – jen náš
           Značky knih bývají různé (rozsah let „N 1850–1870“, písmeno „Z lit. L.P“, číslo svazku). Drž v jednom indexu
           pro jednu knihu jediný zápis: typ knihy (N, O, Z) + rozsah let NEBO „lit.“ + značka. Co v rejstříku opravdu stojí,
           opiš doslova (nic nepřekládej ani nedomýšlej); nevíš-li, jak značku zapsat, napiš ji tak, jak je, a řekni to
           uživateli. `pridej` po zápisu vypíše všechny různé značky v souboru: jsou-li dvě z nich totéž psané jinak
           (např. „Lit. P“ a „Z lit. P“), sjednoť je v dalším `pridej` (stejný řádek s jinou značkou se přidá vedle, starý
           řádek smaž v TSV ručně).
"""
import datetime, glob, json, os, re, sys, unicodedata
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8-sig")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADR = os.path.join(ROOT, "data", "indexy")
SLOUPCE = ["snimek", "datum", "typ", "obec", "osoby", "ostatni", "jistota", "cetl", "odkaz", "strana", "kniha"]
TYPY = ("N", "O", "Z", "I")
JISTOTY = ("vysoká", "střední", "nízká")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def klic_shody(r):
    """Dva řádky jsou shodné, jen když sedí i ves a strana: v rejstříku bez dat stojí na jednom snímku stejnojmenní lidé z různých vsí."""
    return (r["typ"], r["snimek"], norm(r["osoby"]), r["datum"], norm(r["obec"]), norm(r["strana"]))


def kmen(slovo):
    """Kmen příjmení bez koncovky, aby „Hora“ našlo i „Horová“ a „Černý“ i „Černá“ (v rejstříku stojí ženy jako -ová)."""
    s = norm(slovo)
    for k in ("ova", "a", "y", "i", "e"):
        if s.endswith(k) and len(s) - len(k) >= 3:
            return s[:-len(k)]
    return s


CETL = re.compile(r"[a-z][a-z0-9.-]+/[a-z0-9]+ \d{4}-\d{2}-\d{2}")
DATUM = re.compile(r"\d{4}(-\d{2}(-\d{2})?)?")
JEN_ROK = re.compile(r"\d{4}\s*(\[\?\]|\(\?\)|\?)?")   # „1832“, „1832[?]“: rok ročníku, ne značka knihy


def cisti(v):
    return re.sub(r"[\t\r\n]+", " ", str(v if v is not None else "")).strip()


def svazky():
    try:
        return json.load(open(os.path.join(ROOT, "data", "svazky.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def cti(cesta):
    """(záhlaví ok?, řádky jako slovníky)."""
    with open(cesta, encoding="utf-8") as f:
        radky = [r.rstrip("\n").split("\t") for r in f if r.strip()]
    if not radky or radky[0] != SLOUPCE:
        return False, []
    return True, [dict(zip(SLOUPCE, r + [""] * (len(SLOUPCE) - len(r)))) for r in radky[1:]]


def pridej(klic, vstup, cetl=""):
    sv = svazky()
    if klic not in sv:
        sys.exit(f"Klíč {klic} není v data/svazky.json: index patří ke svazku, nejdřív ho zapiš (aron_img.py … svazek, zarad.py, zapis.py svazky).")
    if cetl and not re.fullmatch(r"[a-z][a-z0-9.-]+/[a-z0-9]+", cetl):
        sys.exit("--cetl: zadej model/effort, např. claude-opus-5-5/high")
    data = json.load(sys.stdin if vstup == "-" else open(vstup, encoding="utf-8-sig"))
    if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
        sys.exit("Vstup musí být JSON pole objektů, jeden objekt = jeden řádek indexu.")
    dnes = datetime.date.today().isoformat()
    nove, chyby = [], []
    for i, x in enumerate(data, 1):
        r = {c: cisti(x.get(c)) for c in SLOUPCE}
        if not r["cetl"] and cetl:
            r["cetl"] = f"{cetl} {dnes}"
        if r["cetl"] and not CETL.fullmatch(r["cetl"]):
            chyby.append(f"řádek {i}: cetl musí být „model/effort RRRR-MM-DD“, např. claude-opus-5-5/high 2026-11-24 "
                         f"(je „{r['cetl']}“); neznáš-li model nebo effort, nech cetl prázdné a dej --cetl")
        if r["typ"] not in TYPY:
            chyby.append(f"řádek {i}: typ musí být N, O, Z nebo I (je „{r['typ']}“)")
        if not r["snimek"].isdigit():
            chyby.append(f"řádek {i}: snimek musí být číslo snímku (je „{r['snimek']}“)")
        if not r["osoby"]:
            chyby.append(f"řádek {i}: chybí osoby")
        if r["jistota"] not in JISTOTY:
            chyby.append(f"řádek {i}: jistota musí být vysoká, střední nebo nízká (je „{r['jistota']}“)")
        if r["datum"] and not DATUM.fullmatch(r["datum"]):
            chyby.append(f"řádek {i}: datum musí být RRRR-MM-DD, RRRR-MM nebo RRRR (je „{r['datum']}“); "
                         f"nejistotu piš do ostatni a jistoty, ne do data")
        if JEN_ROK.fullmatch(r["kniha"]):
            chyby.append(f"řádek {i}: kniha je jen rok („{r['kniha']}“) – rok patří do datum, kniha je značka knihy (např. „Z 1836–1882“)")
        if r["typ"] == "I" and not r["kniha"]:
            chyby.append(f"řádek {i}: řádek rejstříku (typ I) musí mít knihu, do které odkazuje")
        if r["snimek"].isdigit() and sv[klic].get("snimku") and int(r["snimek"]) > int(sv[klic]["snimku"]):
            chyby.append(f"řádek {i}: snímek {r['snimek']} je za koncem svazku ({sv[klic]['snimku']} snímků)")
        nove.append(r)
    if chyby:
        sys.exit("Nic se nezapsalo:\n  " + "\n  ".join(chyby))
    os.makedirs(ADR, exist_ok=True)
    cesta = os.path.join(ADR, klic + ".tsv")
    mam, stavajici = set(), []
    if os.path.exists(cesta):
        ok, stavajici = cti(cesta)
        if not ok:
            sys.exit(f"{cesta} nemá záhlaví podle indexy.py (viz --help): neopravuji ho naslepo.")
        mam = {klic_shody(r) for r in stavajici}
    pridano = 0
    for r in nove:
        k = klic_shody(r)
        if k not in mam:
            mam.add(k)
            stavajici.append(r)
            pridano += 1
    stavajici.sort(key=lambda r: (int(r["snimek"]), r["typ"]))
    with open(cesta, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(SLOUPCE) + "\n")
        for r in stavajici:
            f.write("\t".join(r[c] for c in SLOUPCE) + "\n")
    ok, zpet = cti(cesta)   # zpětné čtení: co jsme zapsali, musí jít přečíst
    if not ok or len(zpet) != len(stavajici):
        sys.exit(f"POZOR: zpětné čtení {cesta} nesedí, zkontroluj soubor.")
    print(f"{klic}: přidáno {pridano} ř., přeskočeno {len(nove) - pridano} shodných, v indexu celkem {len(zpet)} ř.")
    knihy = {}
    for r in zpet:
        if r["typ"] == "I":
            knihy[r["kniha"]] = knihy.get(r["kniha"], 0) + 1
    if len(knihy) > 1:
        print("Značky knihy v rejstříku (jsou-li dvě totéž psané jinak, sjednoť je, viz indexy.py --help): "
              + "; ".join(f"{k} ({n})" for k, n in sorted(knihy.items())))


def vsechny():
    """Indexy svazků: i svazek, který má zatím jen mapu písmen rejstříku a žádný řádek."""
    klice = {os.path.basename(c)[:-4] for c in glob.glob(os.path.join(ADR, "*.tsv"))}
    klice |= {os.path.basename(c)[:-len(".pismena.json")] for c in glob.glob(os.path.join(ADR, "*.pismena.json"))}
    for klic in sorted(klice):
        cesta = os.path.join(ADR, klic + ".tsv")
        ok, radky = cti(cesta) if os.path.exists(cesta) else (True, [])
        yield klic, ok, radky


def pokryti(radky):
    sn = sorted({int(r["snimek"]) for r in radky if r["snimek"].isdigit()})
    roky = sorted({r["datum"][:4] for r in radky if re.match(r"\d{4}", r["datum"])})
    return (f"snímky {sn[0]}–{sn[-1]} ({len(sn)} s řádky)" if sn else "žádné snímky") + (f", roky {roky[0]}–{roky[-1]}" if roky else "")


ROZSAH = re.compile(r"(\d+)(?:-(\d+))?")
# obvyklé jiné tvary počátečního písmene v rejstřících (německý pravopis, I/J/Y); vodítko, ne úplný výčet
JINE = {"v": ["W"], "w": ["V"], "o": ["W"], "c": ["K", "Cz"], "k": ["C"], "č": ["C", "Cz", "T"], "ch": ["C", "H"],
        "h": ["Ch"], "š": ["S", "Sch"], "ž": ["S", "Sch", "Z"], "s": ["Š", "Sch"], "z": ["Ž", "S"],
        "j": ["I", "Y"], "i": ["J", "Y"], "y": ["I", "J"], "ř": ["R"], "r": ["Ř"], "t": ["Tsch"]}


def cesta_pismen(klic):
    return os.path.join(ADR, klic + ".pismena.json")


def cti_pismena(klic):
    """{písmeno: {"snimky": "od-do", "prepsano": "RRRR-MM-DD"?}} nebo None, když svazek evidenci písmen nemá."""
    try:
        return json.load(open(cesta_pismen(klic), encoding="utf-8"))
    except FileNotFoundError:
        return None
    except ValueError:
        sys.exit(f"{cesta_pismen(klic)} není platný JSON: neopravuji ho naslepo.")


def pis_pismena(klic, p):
    os.makedirs(ADR, exist_ok=True)
    with open(cesta_pismen(klic), "w", encoding="utf-8", newline="\n") as f:
        json.dump(dict(sorted(p.items(), key=lambda kv: (kv[0] != "*", norm(kv[0]), kv[0]))), f, ensure_ascii=False, indent=1)
        f.write("\n")
    if cti_pismena(klic) != p:   # zpětné čtení
        sys.exit(f"POZOR: zpětné čtení {cesta_pismen(klic)} nesedí, zkontroluj soubor.")


def snimky_rozsahu(s):
    m = ROZSAH.fullmatch(s or "")
    if not m:
        return None
    od, do = int(m.group(1)), int(m.group(2) or m.group(1))
    return range(od, do + 1) if od <= do else None


def over_klic(klic):
    sv = svazky()
    if klic not in sv:
        sys.exit(f"Klíč {klic} není v data/svazky.json: evidence písmen patří ke svazku s rejstříkem, nejdřív ho zapiš.")
    return sv[klic]


def mapa(klic, polozky):
    sv = over_klic(klic)
    p, chyby = cti_pismena(klic) or {}, []
    for x in polozky:
        pis, _, roz = x.partition("=")
        pis = pis.strip()
        rng = snimky_rozsahu(roz.strip())
        if not pis or pis.lower() in ("vse", "*") or not rng:
            chyby.append(f"„{x}“: zadej písmeno=od-do, např. N=21-23")
            continue
        if sv.get("snimku") and rng[-1] > int(sv["snimku"]):
            chyby.append(f"„{x}“: snímek {rng[-1]} je za koncem svazku ({sv['snimku']} snímků)")
            continue
        stare = p.get(pis, {})
        p[pis] = {"snimky": f"{rng[0]}-{rng[-1]}"}
        if stare.get("prepsano") and stare.get("snimky") == p[pis]["snimky"]:
            p[pis]["prepsano"] = stare["prepsano"]   # stejné snímky: přepsání platí dál
        elif stare.get("prepsano"):
            print(f"{pis}: snímky se změnily ({stare['snimky']} → {p[pis]['snimky']}), písmeno už nepočítám za přepsané")
    if chyby:
        sys.exit("Nic se nezapsalo:\n  " + "\n  ".join(chyby))
    pis_pismena(klic, p)
    print(f"{klic}: zmapováno {len(p)} písmen; přepsaná: {', '.join(k for k, v in p.items() if v.get('prepsano')) or 'žádné'}")


def prepsano(klic, pismena):
    over_klic(klic)
    p = cti_pismena(klic) or {}
    dnes = datetime.date.today().isoformat()
    if pismena and pismena[0].lower() == "vse":
        rng = snimky_rozsahu(pismena[1] if len(pismena) == 2 else "")
        if not rng:
            sys.exit("prepsano <klíč> vse <od>-<do>: zadej snímky celého rejstříku")
        p["*"] = {"snimky": f"{rng[0]}-{rng[-1]}", "prepsano": dnes}
        cile = ["*"]
    else:
        chybi = [x for x in pismena if x not in p]
        if not pismena or chybi:
            sys.exit(f"Nejdřív zmapuj, kde písmeno je: indexy.py mapa {klic} {'=od-do '.join(chybi or ['N'])}=od-do"
                     + (f" (zmapovaná: {', '.join(k for k in p if k != '*')})" if p else ""))
        for x in pismena:
            p[x]["prepsano"] = dnes
        cile = pismena
    _, radky = cti(os.path.join(ADR, klic + ".tsv")) if os.path.exists(os.path.join(ADR, klic + ".tsv")) else (True, [])
    mam = {int(r["snimek"]) for r in radky if r["typ"] == "I" and r["snimek"].isdigit()}
    for x in cile:
        prazdne = [s for s in snimky_rozsahu(p[x]["snimky"]) if s not in mam]
        if prazdne:
            print(f"Pozor: {('rejstřík' if x == '*' else 'písmeno ' + x)} – na snímcích {', '.join(map(str, prazdne))} nemá index "
                  "žádný řádek rejstříku (typ I). Zapsal jsi je přes `pridej`? Prázdný snímek je v pořádku jen tehdy, když na něm opravdu nic není.")
    pis_pismena(klic, p)
    print(f"{klic}: přepsaná {'celý rejstřík' if '*' in cile else ', '.join(cile)} ({dnes})")


def pocatky(slovo):
    """(vlastní písmena, jiné tvary) rejstříku pro jméno: Čapek → ([Č, C], [Cz, T]), Vávra → ([V], [W])."""
    s = slovo.strip().lower()
    if not s:
        return [], []
    prvni = "ch" if s.startswith("ch") else s[0]
    vlastni = [prvni.capitalize()]
    if norm(prvni).capitalize() not in vlastni:
        vlastni.append(norm(prvni).capitalize())
    return vlastni, [t for t in JINE.get(prvni, []) if t not in vlastni]


def stav_pismen(p, cast):
    """Řádky o tom, co evidence písmen říká k hledanému jménu."""
    if "*" in p:
        return [f"  rejstřík přepsaný celý (snímky {p['*']['snimky']})"]
    prep = [k for k, v in p.items() if v.get("prepsano")]
    out = [f"  rejstřík po písmenech: přepsaná {', '.join(prep) or 'žádná'}; zmapovaná nepřepsaná "
           f"{', '.join(k for k in p if k not in prep) or 'žádná'}"]
    for slovo in cast:
        vlastni, jine = pocatky(slovo)
        if not vlastni:
            continue
        hlavni = [k for k in p if any(norm(k) == norm(t) for t in vlastni)]   # Č i C, jsou-li zmapovaná zvlášť
        if not any(p[h].get("prepsano") for h in hlavni):
            kde = "; ".join(f"{h} na snímcích {p[h]['snimky']}" for h in hlavni) or "kde je, zatím není zmapováno"
            out.append(f"  POZOR: písmeno {vlastni[0]} ({slovo}) není přepsané ({kde}) – neshoda tady nic neznamená; "
                       "přepiš ho, než budeš hledat v knize")
        dalsi = [k for k in p if k not in hlavni and not p[k].get("prepsano") and any(norm(k) == norm(t) for t in jine)]
        if dalsi:
            out.append(f"  zkus i jiný tvar ({slovo}): " + "; ".join(f"{k} na snímcích {p[k]['snimky']}" for k in dalsi) + " – nepřepsané")
    return out


def hledej(args):
    cast = [a for a in args if not a.startswith("--")]
    opt = {}
    for i, a in enumerate(args):
        if a in ("--ves", "--klic", "--typ") and i + 1 < len(args):
            opt[a[2:]] = args[i + 1]
            cast = [c for c in cast if c != args[i + 1]]
    if not cast:
        sys.exit("hledej: zadej část jména, např. indexy.py hledej Hora")
    q = " ".join(kmen(w) for w in " ".join(cast).split())
    sv, nalez, pocet, rejstrik = svazky(), 0, 0, 0
    for klic, ok, radky in vsechny():
        if not ok:
            print(f"{klic}: soubor nemá správné záhlaví, přeskakuji (indexy.py --help)")
            continue
        if opt.get("klic") and opt["klic"] != klic:
            continue
        pocet += 1
        shody = [r for r in radky if (q in norm(r["osoby"]) or q in norm(r["ostatni"]))
                 and (not opt.get("ves") or norm(opt["ves"]) in norm(r["obec"]))]
        hity = [r for r in shody if not opt.get("typ") or r["typ"] == opt["typ"].upper()]
        if opt.get("typ") and opt["typ"].upper() != "I":
            rejstrik += sum(1 for r in shody if r["typ"] == "I")
        print(f"\n{klic} – {sv.get(klic, {}).get('svazek', '?')}: {len(radky)} ř., {pokryti(radky)}; shod {len(hity)}")
        p = cti_pismena(klic)
        if p:
            print("\n".join(stav_pismen(p, cast)))
        for r in hity:
            kam = f" → {r['kniha']}" if r["kniha"] else ""
            print("  " + " | ".join(x for x in (f"{r['typ']} sn. {r['snimek']}" + (f" str. {r['strana']}" if r["strana"] else "") + kam,
                  r["osoby"], r["datum"], r["obec"], r["ostatni"], r["jistota"] if r["jistota"] != "vysoká" else "") if x))
        nalez += len(hity)
    if not pocet:
        print("Žádný index (data/indexy/*.tsv) zatím není.")
        return
    if rejstrik:
        print(f"\nPozor: --typ {opt['typ'].upper()} vyřadil {rejstrik} shod v rejstříku (řádky typu I). "
              "Ukáže je `--typ I` nebo hledání bez --typ.")
    print(f"\nCelkem {nalez} shod. Index je vodítko, ne doklad: zásah ověř na snímku a ulož šesti kroky. "
          "Neshoda platí jen pro pokrytí uvedené výše.")


def stav():
    nic = True
    sv = svazky()
    for klic, ok, radky in vsechny():
        nic = False
        if not ok:
            print(f"{klic}: ŠPATNÉ ZÁHLAVÍ")
            continue
        celkem = sv.get(klic, {}).get("snimku")
        print(f"{klic} – {sv.get(klic, {}).get('svazek', 'NENÍ VE svazky.json')}: {len(radky)} ř., {pokryti(radky)}"
              + (f" z {celkem} snímků knihy" if celkem else "") + f", s nízkou jistotou {sum(1 for r in radky if r['jistota'] == 'nízká')}")
        p = cti_pismena(klic)
        if p:
            print(stav_pismen(p, [])[0])
    if nic:
        print("Žádný index zatím není.")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if a[0] == "pridej" and len(a) in (3, 5):
        pridej(a[1], a[2], a[4] if len(a) == 5 and a[3] == "--cetl" else "")
    elif a[0] == "hledej":
        hledej(a[1:])
    elif a[0] == "stav":
        stav()
    elif a[0] == "mapa" and len(a) >= 3:
        mapa(a[1], a[2:])
    elif a[0] == "prepsano" and len(a) >= 3:
        prepsano(a[1], a[2:])
    else:
        sys.exit(__doc__)
