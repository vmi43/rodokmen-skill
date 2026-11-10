#!/usr/bin/env python3
"""Přidá nebo nahradí jednu položku v datech projektu – formát souboru zůstane stejný (odsazení 1, české znaky, konce
řádků LF), takže změna v historii je jen ta jedna položka.

Použití (z kořene projektu):
  zapis.py <soubor> <klíč> <vstup.json> [--sloucit]
    soubor     zaznamy | svazky | prepisy | zvyrazneni | mista | dokumenty | mapy | web   (= data/<soubor>.json)
    klíč       zaznamy: „klic“ zápisu; dokumenty, mapy: „img“; web: pole nastavení (uvod, pribeh, prihlaseni,
               zajimavosti_na_uvodu, nazev…); ostatní: klíč ve slovníku (id svazku, klíč zápisu, obec)
    vstup.json soubor s jedním objektem JSON (napiš ho nástrojem Write do pracovni/), „-“ = ze vstupu
    --sloucit  jen změní / doplní uvedená pole, ostatní pole položky nechá
Položka se stejným klíčem se nahradí, jinak se přidá na konec. Python skripty ani `sed -i` na data nepoužívej.
  zapis.py denik "<zdroj>" "<rozsah>" "<hledáno>" "<výsledek>" "<citace>" [--datum "10. 11. 2026"]
    přidá řádek do deníku data/research_log.md; číslo # přidělí sám (nejvyšší + 1) až pod zámkem těsně před
    zápisem – dvě session na jedné zakázce si čísla nepřepíšou. Datum výchozí dnes. Řádky deníku piš jen takhle.
Souběžní pomocníci se střídají přes zámek (pracovni/.zamky/), žádný zápis se neztratí. Ostatní nástroje u nás zapisují do data/ po svém (ne přes zapis()).

Původ: převzato z vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/zapis.py), commit 32bef07; úprava: věta o ostatních nástrojích.
"""
import contextlib, json, os, re, sys, tempfile, time
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "data", "STAV.md")):   # spuštěno ze složky skillu: data projektu tam nejsou, zápis by šel do skillu
    sys.exit(f"{os.path.basename(__file__)}: {ROOT} není složka projektu (chybí data/STAV.md). "
             f"Spusť projektovou kopii z kořene projektu: python3 -I tools/{os.path.basename(__file__)} …")
SEZNAMY = {"zaznamy": "klic", "dokumenty": "img", "mapy": "img"}   # soubory se seznamem: pole, podle kterého se položka pozná
SLOVNIKY = {"svazky", "prepisy", "zvyrazneni", "mista", "web"}
LIBOVOLNE = {"web"}   # hodnota nemusí být objekt (web.json: „nazev“ je text, „zajimavosti_na_uvodu“ seznam)
WS = re.compile(r"\s*")
CEKANI_NA_ZAMEK = 60   # s; zámek drží jen pár milisekund, déle = zaseknutý proces


def polozky(text):
    """Položky nejvyšší úrovně: [(klíč nebo None, začátek hodnoty, konec hodnoty)] – pozice v původním textu."""
    dec, i = json.JSONDecoder(), WS.match(text).end()
    otevreni, i, out = text[i], i + 1, []
    while True:
        i = WS.match(text, i).end()
        if text[i] in "]}":
            return out
        klic = None
        if otevreni == "{":
            klic, i = dec.raw_decode(text, i)
            i = WS.match(text, WS.match(text, i).end() + 1).end()   # za dvojtečku
        _, j = dec.raw_decode(text, i)
        out.append((klic, i, j))
        i = WS.match(text, j).end()
        if text[i] == ",":
            i += 1


def jako(text, s, e, v):
    """Hodnota v JSON ve stejném stylu jako text[s:e] (na jednom řádku, nebo odsazená po jedné mezeře)."""
    if "\n" not in text[s:e]:
        return json.dumps(v, ensure_ascii=False)
    odsazeni = text[text.rfind("\n", 0, s) + 1:s]
    odsazeni = odsazeni[:len(odsazeni) - len(odsazeni.lstrip())]
    return json.dumps(v, ensure_ascii=False, indent=1).replace("\n", "\n" + odsazeni)


@contextlib.contextmanager
def zamek(nazev):
    """Výhradní přístup k data/<nazev>.json napříč procesy; systém zámek uvolní i po pádu procesu."""
    slozka = os.path.join(ROOT, "pracovni", ".zamky")
    os.makedirs(slozka, exist_ok=True)
    with open(os.path.join(slozka, nazev + ".lock"), "a+b") as f:
        if os.name == "nt":
            import msvcrt
            zamkni = lambda: msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            odemkni = lambda: msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            zamkni = lambda: fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            odemkni = lambda: fcntl.flock(f, fcntl.LOCK_UN)
        f.seek(0)   # msvcrt zamyká bajty od aktuální pozice – zamknout i odemknout musí stejný bajt
        konec = time.time() + CEKANI_NA_ZAMEK
        while True:
            try:
                zamkni()
                break
            except OSError:
                if time.time() > konec:
                    sys.exit(f"data/{nazev}.json zapisuje jiný proces déle než {CEKANI_NA_ZAMEK} s – "
                             "zkontroluj, jestli nějaký nevisí, a zkus to znovu.")
                time.sleep(0.05)
        try:
            yield
        finally:
            f.seek(0)
            odemkni()


def zapis(nazev, klic, obj, sloucit=False):
    """Přidá nebo nahradí položku `klic` v data/<nazev>.json; vrací True, když ji přidal."""
    if not isinstance(obj, dict) and nazev not in LIBOVOLNE:
        sys.exit("Vstup musí být jeden objekt JSON ({…}).")
    if sloucit and not isinstance(obj, dict):
        sys.exit("--sloucit jde jen s objektem JSON ({…}).")
    try:   # osamělá polovina páru UTF-16 (\ud800 ve vstupu) by spadla až při zápisu – odmítnout dřív, než se sáhne na data
        json.dumps([klic, obj], ensure_ascii=False).encode("utf-8")
    except UnicodeEncodeError as e:
        sys.exit(f"Vstup obsahuje neplatný znak ({e.object[e.start:e.end]!r}, poškozená diakritika?) – oprav ho, nic jsem nezapsal.")
    seznam = nazev in SEZNAMY
    if seznam and obj.setdefault(SEZNAMY[nazev], klic) != klic:
        sys.exit(f"Klíč „{klic}“ nesedí s „{SEZNAMY[nazev]}“ ve vstupu („{obj[SEZNAMY[nazev]]}“).")
    path = os.path.join(ROOT, "data", nazev + ".json")
    with zamek(nazev):   # čtení i zápis pod jedním zámkem, jinak by souběžný zápis přepsal cizí změnu
        text = open(path, encoding="utf-8-sig").read() if os.path.exists(path) else ""
        try:
            data = json.loads(text) if text.strip() else ([] if seznam else {})
            if not isinstance(data, list if seznam else dict):
                raise ValueError("čekal jsem " + ("seznam [ … ]" if seznam else "slovník { … }"))
        except ValueError as e:
            sys.exit(f"data/{nazev}.json nejde přečíst ({e}) – oprav ho nejdřív (git diff ukáže poslední změnu).")

        poz = polozky(text) if data else []
        if seznam:
            idx = next((n for n, x in enumerate(data) if isinstance(x, dict) and x.get(SEZNAMY[nazev]) == klic), None)
        else:
            idx = next((n for n, (k, _, _) in enumerate(poz) if k == klic), None)
        stare = None if idx is None else (data[idx] if seznam else data[klic])
        nove = {**stare, **obj} if sloucit and isinstance(stare, dict) else obj
        if not poz:   # prázdný nebo nový soubor
            text = json.dumps([nove] if seznam else {klic: nove}, ensure_ascii=False, indent=1) + "\n"
        elif idx is not None:   # nahradit jen text té jedné položky, zbytek souboru zůstane doslova
            _, s, e = poz[idx]
            text = text[:s] + jako(text, s, e, nove) + text[e:]
        else:   # přidat za poslední položku ve stejném stylu
            _, s, e = poz[-1]
            radek = text[text.rfind("\n", 0, s) + 1:s]
            odsazeni = radek[:len(radek) - len(radek.lstrip())]
            text = (text[:e] + ",\n" + odsazeni + ("" if seznam else json.dumps(klic, ensure_ascii=False) + ": ")
                    + jako(text, s, e, nove) + text[e:])
        json.loads(text)   # pojistka: výsledek musí být platný JSON

        zapis_atomicky(path, text)
        return idx is None


def zapis_atomicky(path, text):
    """Celý soubor naráz přes dočasný soubor – při chybě nezůstane rozepsaný."""
    fd, tmp = tempfile.mkstemp(prefix=".zapis_", suffix=".tmp", dir=os.path.dirname(path))
    try:
        with open(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


RADEK_DENIKU = re.compile(r"^\|\s*(\d+)\s*\|", re.M)


def bunka(text):
    """Text do buňky tabulky Markdownu: bez nových řádků, svislítko escapované."""
    return re.sub(r"\s+", " ", str(text)).strip().replace("|", "\\|")


def dnes():
    t = time.localtime()
    return f"{t.tm_mday}. {t.tm_mon}. {t.tm_year}"


def zapis_denik(zdroj, rozsah, hledano, vysledek, citace, datum=None):
    """Přidá řádek do data/research_log.md za poslední řádek tabulky; vrací přidělené číslo."""
    path = os.path.join(ROOT, "data", "research_log.md")
    with zamek("research_log"):   # číslo i zápis pod jedním zámkem – souběžná session dostane další číslo
        try:
            text = open(path, encoding="utf-8-sig").read()
        except OSError:
            sys.exit("data/research_log.md chybí – založ projekt přes novy_projekt.py.")
        hlavicka = re.search(r"^\|\s*#\s*\|.*\n\|[-| :]+\|[ \t]*$", text, re.M)
        if not hlavicka:
            sys.exit("V data/research_log.md chybí tabulka „| # | datum | zdroj | rozsah | hledáno | výsledek | citace |“.")
        cislo = max((int(c) for c in RADEK_DENIKU.findall(text)), default=0) + 1
        radky = text[hlavicka.end():].split("\n")
        konec = hlavicka.end()   # za poslední řádek tabulky (tabulka končí prvním řádkem bez „|“)
        for r in radky[1:]:
            if not r.startswith("|"):
                break
            konec += len(r) + 1
        radek = "| " + " | ".join([str(cislo), bunka(datum or dnes())] + [bunka(x) for x in
                                  (zdroj, rozsah, hledano, vysledek, citace)]) + " |"
        text = text[:konec] + "\n" + radek + text[konec:] if konec < len(text) else text.rstrip("\n") + "\n" + radek + "\n"
        zapis_atomicky(path, text)
    return cislo


def main():
    if sys.argv[1:2] == ["denik"]:
        a = sys.argv[2:]
        datum = None
        if "--datum" in a:
            i = a.index("--datum")
            datum = a[i + 1] if i + 1 < len(a) else sys.exit("--datum: chybí hodnota")
            del a[i:i + 2]
        if len(a) != 5:
            sys.exit('Použití: zapis.py denik "<zdroj>" "<rozsah>" "<hledáno>" "<výsledek>" "<citace>" [--datum "10. 11. 2026"]')
        print(f"data/research_log.md: přidán řádek {zapis_denik(*a, datum=datum)}")
        return
    args = [a for a in sys.argv[1:] if a != "--sloucit"]
    if len(args) != 3 or args[0] not in {*SEZNAMY, *SLOVNIKY}:
        sys.exit(__doc__)
    nazev, klic, vstup = args
    try:
        obj = json.load(sys.stdin if vstup == "-" else open(vstup, encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        sys.exit(f"Vstup {vstup} není platný JSON: {e}")
    if nazev == "prepisy" and (not isinstance(obj, dict) or set(obj) - {"orig", "cs"}):
        sys.exit("prepisy: povolené klíče jsou jen 'orig' (přepis) a 'cs' (překlad), viz reference/data.md")
    pridano = zapis(nazev, klic, obj, sloucit="--sloucit" in sys.argv)
    print(f"data/{nazev}.json: {'přidáno' if pridano else 'změněno'} „{klic}“")


if __name__ == "__main__":
    main()
