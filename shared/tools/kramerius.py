#!/usr/bin/env python3
"""Kramerius: hledání ve fulltextu (NK nebo jiná knihovna přes Českou digitální knihovnu), text stránky, autoři díla.

Použití:
  kramerius.py 'SOLR_QUERY' [rows]                       – Kramerius NK (API v5)
      např. kramerius.py 'text_ocr:"Jan Novák" AND datum_begin:[1860 TO 1920]'
      Sloupec přístupu: public = volně; private+DNNT = čitelné po přihlášení na ndk.cz (reference/portaly.md → DNNT);
      private = jen v knihovně. Filtr datum_begin vyřadí část čísel periodik – při malém počtu nálezů hledej i bez něj.
  kramerius.py 'SOLR_QUERY' [rows] --knihovna vkol|mzk|cuni|…|vse
      totéž v Krameriu jiné knihovny přes Českou digitální knihovnu (ČDK; pole jako u NK, nástroj je přeloží).
      Přímo na kramerius.vkol.cz, kramerius.cuni.cz… nástroje nesmí (podminky.json) – VKOL dal 403 po 4 dotazech.
      Kód knihovny je ve sloupci „knihovna“ výpisu s --knihovna vse.
  kramerius.py text <pid> ['regulární výraz']
      OCR text veřejné stránky přes ČDK (z kterékoli knihovny); s výrazem jen okolí nálezů (±300 znaků).
  kramerius.py autori <uuid>
      autoři díla z katalogu (MODS přes ČDK) s roky narození a úmrtí a konec ochrany: 1. 1. roku úmrtí
      posledního autora + 71. Licence „public“ v ČDK NEZNAMENÁ volné dílo (plán Olomouce 1946: „public“,
      autor † 1974) – obrázek do výstupu až podle tohohle výpisu (reference/podminky.md, „Kramerius, volné dílo“).

Původ: převzato z vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/kramerius.py), commit e1cd204; nahrazuje náš dřívější
jednoduchý kramerius.py (hledání v NK, výstup „found N“ beze změny); úprava: slusne.py se u nás zapíná importem.
"""
import os, re, sys, json, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)

NK = "https://kramerius5.nkp.cz/search/api/v5.0/search"
CDK = "https://api.ceskadigitalniknihovna.cz/search/api/client/v7.0/"   # Krameria všech knihoven
CDK_POLE = {"fedora.model": "model", "root_title": "root.title", "datum_begin": "date_range_start.year",
            "datum_str": "date.str", "dostupnost": "accessibility", "PID": "pid"}   # pole NK (K5) → ČDK (K7)
PID = re.compile(r"uuid:[0-9a-f-]{36}")   # pid jde do adresy API: žádná lomítka ani tečky
MODS = {"m": "http://www.loc.gov/mods/v3"}
OCHRANA_LET = 70   # § 27 autorského zákona: 70 let po smrti posledního autora, počítá se od 1. 1. dalšího roku


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": slusne.UA}), timeout=90) as r:
        return r.read()


def cdk_dotaz(q):
    """Dotaz s poli Krameria NK přeložený na pole ČDK (Kramerius 7)."""
    return re.sub(r"\b(" + "|".join(map(re.escape, CDK_POLE)) + r"):", lambda m: CDK_POLE[m.group(1)] + ":", q)


def hledej_nk(q, rows):
    p = {'q': q + ' AND fedora.model:page', 'fl': 'PID,root_title,root_pid,datum_str,details,dostupnost,dnnt,dnnt-labels',
         'rows': rows, 'wt': 'json', 'hl': 'true', 'hl.fl': 'text_ocr', 'hl.fragsize': '250'}
    d = json.loads(get(NK + '?' + urllib.parse.urlencode(p)))
    print('found', d['response']['numFound'])
    hl = d.get('highlighting', {})
    for x in d['response']['docs']:
        h = ' | '.join(hl.get(x['PID'], {}).get('text_ocr', []))[:400].replace('\n', ' ')
        pristup = x.get('dostupnost') or '?'
        if pristup == 'private' and (x.get('dnnt') or 'dnnto' in (x.get('dnnt-labels') or [])):
            pristup = 'private+DNNT'
        det = str(x['details'][0]).split()[0] if x.get('details') else ''
        print('-', x.get('datum_str'), '|', str(x.get('root_title'))[:60], '| s.', det, '|', x['PID'], '|', pristup)
        if h:
            print('   ', h)


def hledej_cdk(q, rows, knihovna):
    q = f"({cdk_dotaz(q)}) AND model:page"
    if knihovna != "vse":
        q += f" AND cdk.collection:{re.sub(r'[^a-z0-9_-]', '', knihovna.lower())}"
    p = {"q": q, "fl": "pid,root.title,root.pid,date.str,page.number,accessibility,licenses,cdk.collection",
         "rows": rows}   # úryvky (hl) ČDK nevrací (HTTP 400) – okolí nálezu ukáže `text <pid> 'výraz'`
    d = json.loads(get(CDK + "search?" + urllib.parse.urlencode(p)))
    print("found", d["response"]["numFound"])
    for x in d["response"]["docs"]:
        pristup = "+".join([x.get("accessibility") or "?"] + [l for l in x.get("licenses") or [] if l != "public"])
        print("-", x.get("date.str"), "|", str(x.get("root.title"))[:60], "| s.", x.get("page.number", ""), "|", x["pid"],
              "|", pristup, "|", ",".join(x.get("cdk.collection") or []))
    print("Odkaz: https://www.ceskadigitalniknihovna.cz/uuid/<pid>. „public“ = čitelné, ne volné dílo: "
          "před použitím obrázku kramerius.py autori <pid>.")


def text(pid, vzor=None):
    t = re.sub(r"\s+", " ", get(f"{CDK}items/{pid}/ocr/text").decode("utf-8", "replace"))
    if not vzor:
        print(t)
        return
    nalezy = list(re.finditer(vzor, t, re.I))
    for m in nalezy:
        print(f"…{t[max(0, m.start() - 300):m.end() + 300]}…\n")
    print(f"{len(nalezy)} nálezů „{vzor}“ na stránce {pid}")


def rok_umrti(datum):
    """„1843-1903“ → 1903; „1880-“, „nar. 1880“ → None (žije, nebo úmrtí neznámé)."""
    roky = re.findall(r"\b(1[0-9]\d\d|20\d\d)\b", datum or "")
    if len(roky) >= 2 or re.search(r"zem[řr]|†|\bd\.", datum or "", re.I):
        return int(roky[-1]) if roky else None
    return None


def autori_z_mods(xml):
    """[(jméno, data, role)] a rok vydání z MODS (první záznam)."""
    koren = ET.fromstring(xml)
    mods = koren if koren.tag.endswith("}mods") else koren.find("m:mods", MODS)
    if mods is None:
        return [], None
    out = []
    for n in mods.findall("m:name", MODS):
        jmeno = ", ".join(p.text.strip() for p in n.findall("m:namePart", MODS) if p.text and p.get("type") != "date")
        datum = " ".join(p.text.strip() for p in n.findall("m:namePart[@type='date']", MODS) if p.text)
        role = ", ".join(r.text.strip() for r in n.findall("m:role/m:roleTerm", MODS) if r.text)
        if jmeno:
            out.append((jmeno, datum, role))
    vydano = next((v.text for v in mods.iter(f"{{{MODS['m']}}}dateIssued") if v.text), None)
    return out, vydano


def konec_ochrany(autori, vydano):
    """(rok, kdy je dílo volné – 1. 1. toho roku – nebo None, vysvětlení)."""
    if not autori:
        m = re.search(r"\b(1[5-9]\d\d|20\d\d)\b", vydano or "")
        if not m:
            return None, "autor ani rok vydání v katalogu nejsou – ověř v katalogu knihovny"
        return int(m.group(1)) + OCHRANA_LET + 1, "autor v katalogu není: anonymní dílo je chráněné 70 let od zveřejnění – ověř, že autor opravdu neznámý (mapy: kreslič, vydavatel)"
    roky = [rok_umrti(d) for _, d, _ in autori]
    znamy = max((r for r in roky if r), default=None)
    if None in roky and not (znamy and znamy + OCHRANA_LET + 1 > time.localtime().tm_year):
        return None, "u někoho chybí rok úmrtí (žije, nebo neznámý) – dohledej ho (Wikidata, NK autority), do té doby chráněné"
    return znamy + OCHRANA_LET + 1, f"autor zemřel {znamy}" + (", u dalšího rok úmrtí chybí (může být i déle)" if None in roky else "")


def autori(pid):
    d = json.loads(get(CDK + "search?" + urllib.parse.urlencode({
        "q": f'pid:"{pid}"', "fl": "pid,root.pid,root.title,model,date.str,licenses,accessibility,cdk.collection"})))
    docs = d["response"]["docs"]
    if not docs:
        sys.exit(f"{pid} v České digitální knihovně není")
    x = docs[0]
    koren = x.get("root.pid") or pid
    print(f"{x.get('root.title')} ({x.get('date.str') or '?'}), {koren}, knihovna {','.join(x.get('cdk.collection') or [])}, "
          f"přístup {x.get('accessibility')}, licence {','.join(x.get('licenses') or []) or '–'}")
    seznam, vydano = autori_z_mods(get(f"{CDK}items/{koren}/metadata/mods"))
    if not seznam and koren != pid:   # příloha nebo svazek s vlastními autory
        seznam, vydano2 = autori_z_mods(get(f"{CDK}items/{pid}/metadata/mods"))
        vydano = vydano or vydano2
    for jmeno, datum, role in seznam:
        print(f"  {jmeno}{f' ({datum})' if datum else ' (data v katalogu nejsou)'}{f' – {role}' if role else ''}")
    rok, proc = konec_ochrany(seznam, vydano)
    if rok is None:
        print(f"Volné dílo: NEOVĚŘENO – {proc}.")
    elif rok <= time.localtime().tm_year:
        print(f"Volné dílo od 1. 1. {rok} ({proc}). Do zdroje „Kramerius, volné dílo“ a citace: název, rok, autor, "
              "knihovna, trvalý odkaz https://www.ceskadigitalniknihovna.cz/uuid/" + koren)
    else:
        print(f"CHRÁNĚNÉ do 31. 12. {rok - 1} ({proc}): obrázek do výstupu ne, jen fakta s citací.")
    print("Katalog bývá neúplný (kreslič, spoluautor mapy): projdi i titulní list nebo tiráž.")


def main(a):
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if a[0] in ("text", "autori"):
        if len(a) < 2 or not PID.fullmatch(a[1]):
            sys.exit(f"{a[0]}: zadej pid ve tvaru uuid:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        if a[0] == "text":
            text(a[1], a[2] if len(a) > 2 else None)
        else:
            autori(a[1])
        return
    knihovna = None
    if "--knihovna" in a:
        i = a.index("--knihovna")
        if i + 1 >= len(a):
            sys.exit("--knihovna: chybí kód (vkol, mzk, cuni… nebo vse)")
        knihovna = a[i + 1]
        a = a[:i] + a[i + 2:]
    q, rows = a[0], a[1] if len(a) > 1 else '30'
    if knihovna:
        hledej_cdk(q, rows, knihovna)
    else:
        hledej_nk(q, rows)


if __name__ == "__main__":
    main(sys.argv[1:])
