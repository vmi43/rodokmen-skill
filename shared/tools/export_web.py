#!/usr/bin/env python3
"""Export dat rodokmenu (data/*) do webu ve složce web/.

Čte data/osoby.py (bez něj jen dějiny domu), data/domy.py (jen je-li; dějiny domu a obce, viz domy_web.py),
data/mapy.json, data/zaznamy.json, data/svazky.json, data/prepisy.json, data/zvyrazneni.json,
data/mista.json, data/web.json, data/dokumenty.json a markdownové poznámky. Zapisuje
web/src/data/site.json, web/src/generated/*, web/public/{img,zdroje}, web/public/prihlaseni.html,
web/nginx.conf a web/netlify/edge-functions/brana.js.

Spouští se z web/ příkazem `npm run data` (nebo přímo `python3 -I tools/export_web.py`, na Windows `python -I -X utf8 …`).
"""
import hashlib, html, json, os, re, shutil, subprocess, sys, unicodedata
if sys.argv[1:2] in (["-h"], ["--help"]):   # nápověda místo pádu
    sys.exit(__doc__.strip())
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import domy_web  # noqa: E402
ROOT = os.path.dirname(TOOLS)
DATA = os.path.join(ROOT, "data")
WEB = os.path.join(ROOT, "web")
VYREZY = os.path.join(ROOT, "vyrezy")      # výřezy zápisů a dokumentů (asi 1800 px) – zobrazují se na webu
ZDROJE = os.path.join(ROOT, "zdroje")      # tytéž výřezy v plném rozlišení (proklik)

LINE_COLORS = {8: "#EFB45F", 9: "#F09A78", 10: "#E58AA6", 11: "#B99AE0",
               12: "#86B8E8", 13: "#6FCBB9", 14: "#9CD17A", 15: "#D3D46A"}
STATUS = {"doc": "doloženo matrikou", "lit": "z literatury", "prob": "pravděpodobné", "fam": "údaj od rodiny",
          "mh": "jen z cizího rodokmenu", "unk": "neznámé"}
KINDS = {"N": "křest / narození", "O": "sňatek", "Z": "úmrtí", "I": "rejstřík", "S": "sčítání lidu",
         "G": "gruntovní / pozemková kniha", "K": "katastr", "M": "mapa", "C": "kronika", "L": "literatura",
         "J": "jiný pramen"}


def jload(name, default):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def load_people():
    ns = {}
    if os.path.exists(os.path.join(DATA, "osoby.py")):
        exec(open(os.path.join(DATA, "osoby.py"), encoding="utf-8-sig").read(), ns)
    for name, default in (("P", {}), ("SIDE", []), ("LINES", {}), ("ISSUES", []), ("HYPOTEZY", []), ("SAME", {})):
        ns.setdefault(name, default)
    return ns


def neverejne_obrazky(cfg):
    """Otevřený web: obrázky, které archiv bez souhlasu nedovoluje zveřejnit (podminky.py). Na webu jen přepis a odkaz."""
    if not (cfg.get("prihlaseni") or {}).get("otevreny") or not os.path.isdir(VYREZY):
        return set()
    import podminky
    return {fn[:-4] for fn in os.listdir(VYREZY)
            if fn.endswith(".jpg") and podminky.posoud_obrazek(ROOT, fn[:-4])[0] == "souhlas"}


def record_rows(skryte=()):
    svazky = jload("svazky.json", {})
    rows = []
    for z in jload("zaznamy.json", []):
        sv = svazky.get(z.get("svazek", ""), {})
        key = z["klic"]
        rows.append(dict(
            key=key, kind=z.get("druh", "J"), date=z.get("datum", ""), title=z.get("nazev", key),
            summary=z.get("shrnuti", ""), scan=z.get("snimek", ""),
            archive=sv.get("archiv", ""), volume=sv.get("svazek", ""), vdesc=sv.get("popis", ""),
            portal=sv.get("portal", "archivu"), url=z.get("odkaz") or sv.get("url", ""),
            img=key not in skryte and os.path.exists(os.path.join(VYREZY, key + ".jpg")),
            full=key not in skryte and os.path.exists(os.path.join(ZDROJE, key + ".jpg")),
        ))
    return rows


def strip_comments(md):
    """Poznámky <!-- … --> v markdownu jsou pro Clauda, ne pro web."""
    return re.sub(r"<!--.*?-->\n?", "", md, flags=re.S)


def slugify(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def norm_answer(text):
    """Stejná normalizace jako v prihlaseni.html: bez diakritiky, malá písmena, jen a-z0-9."""
    t = unicodedata.normalize("NFD", text)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]", "", t)


def years(y):
    y = (y or "").strip()
    ys = re.findall(r"\d{4}", y)
    if not ys:
        return ""
    approx = "≈" if re.match(r"^(asi|≈)", y) else ""
    head, dash, tail = y.partition("–")
    if y.startswith(("?", "†")) or (dash and not re.search(r"\d", head)) or re.match(r"po\b", y):
        # neznámé narození: ukázat jen úmrtí („? – před 1743“ → „† před 1743“, „– po 1921“ → „žil 1921“)
        if re.search(r"\bpo\b", tail or y):
            return "žil " + ys[-1]
        return "† " + ("před " if "před" in y else "") + ys[-1]
    if y.startswith("*"):
        return "* " + ys[0]
    if len(ys) == 1:
        return approx + ys[0]
    second = "?" if "před" in tail else ("po " if re.search(r"\bpo\b", tail) else "") + \
        ("≈" if re.search(r"(asi|≈)", tail) else "") + ys[-1]
    return f"{approx}{ys[0]}–{second}"


def gen(k):
    return k.bit_length() - 1


def relation(k):
    g, male = gen(k), (k % 2 == 0)
    if g == 0:
        return "výchozí osoba rodokmenu"
    if g == 1:
        return "otec" if male else "matka"
    base = "dědeček" if male else "babička"
    if g <= 5:
        return "pra" * (g - 2) + base
    return f"{'předek' if male else 'předkyně'} v {g}. generaci ({'pra' * (g - 2)}{base})"


def placeholder(p):
    return p["n"].startswith(("otec neuveden", "matka neuvedena")) or p["n"] in ("", "?")


def magick_bin():   # ImageMagick 7 (magick), jinak 6 (convert) – ten ale ne na Windows, tam je convert.exe jiný program
    return shutil.which("magick") or (os.name != "nt" and shutil.which("convert")) or None


def size(path):
    w, h = subprocess.run([magick_bin(), path + "[0]", "-format", "%w %h", "info:"],
                          capture_output=True, text=True, check=True).stdout.split()
    return int(w), int(h)


def draw_boxes(src, dst, boxes, small):
    """Kopie výřezu v plném rozlišení s nakreslenými rámečky (pokud má stejný poměr stran jako webový výřez,
    na kterém se rámečky měřily). Vrací False, pak se kopíruje bez rámečků."""
    if not os.path.exists(small) or not magick_bin():
        return False
    (W, H), (w, h) = size(src), size(small)
    if abs(W / H - w / h) > 0.015 * (w / h):
        return False
    sw = max(4, round(W / 450))
    cmd = [magick_bin(), src, "-fill", "none", "-stroke", "#d7302a", "-strokewidth", str(sw)]
    for x0, y0, x1, y1 in boxes:
        cmd += ["-draw", f"rectangle {x0 * W:.0f},{y0 * H:.0f},{x1 * W:.0f},{y1 * H:.0f}"]
    subprocess.run(cmd + ["-quality", "90", dst], check=True)
    return True


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def login_files(cfg):
    """Přihlašovací brána: otázka na webu, na serveru (nginx i Netlify) jen otisk odpovědi (SHA-256).
    Stejný otisk spočítá přihlašovací stránka a uloží ho do cookie – samotná odpověď se nikam neukládá."""
    login = cfg.get("prihlaseni") or {}
    answer = norm_answer(str(login.get("odpoved", "")))   # i číslo („1923“ bez uvozovek)
    tpl = open(os.path.join(WEB, "prihlaseni.sablona.html"), encoding="utf-8").read()
    if "rodokmen:" not in tpl:   # stará šablona (do 0.4.0) ukládá do cookie odpověď – s novou bránou by se nikdo nepřihlásil
        sys.exit("CHYBA: web/ má starou šablonu přihlášení. Aktualizujte projekt: python3 -I <skill>/tools/novy_projekt.py <složka projektu>")
    contact = cfg.get("kontakt") or {}
    hint = ""
    if contact.get("email"):
        hint = (f'Neznáte odpověď? Napište {html.escape(contact.get("jmeno", ""))} na '
                f'<a href="mailto:{html.escape(contact["email"])}">{html.escape(contact["email"])}</a>.')
    page = (tpl.replace("{{NAZEV}}", html.escape(cfg.get("nazev", "Rodokmen")))
               .replace("{{UVOD}}", html.escape(login.get("uvod", "Tenhle web je jen pro rodinu a příbuzné.")))
               .replace("{{OTAZKA}}", html.escape(login.get("otazka", "Odpověď na rodinnou otázku")))
               .replace("{{NAPOVEDA}}", hint))
    write(os.path.join(WEB, "public", "prihlaseni.html"), page)

    edge = os.path.join(WEB, "netlify", "edge-functions", "brana.js")
    if answer:
        digest = hashlib.sha256(("rodokmen:" + answer).encode()).hexdigest()
        nginx_map = f'  "{digest}" 1;'
        write(edge, open(os.path.join(WEB, "netlify", "brana.sablona.js"), encoding="utf-8").read().replace("{{HASH}}", digest))
    else:   # bez přihlášení – web je otevřený
        nginx_map = "  default 1;"
        if os.path.exists(edge):
            os.remove(edge)
    nginx = open(os.path.join(WEB, "nginx.sablona.conf"), encoding="utf-8").read()
    if not answer:   # otevřený web: default 0 v mapě přihlášení nahradí default 1 (dva default nginx odmítne)
        nginx = re.sub(r"(map \$cookie_rodokmen \$rodokmen_ok \{.*?)\n *default 0;", r"\1", nginx, count=1, flags=re.S)
    nginx = nginx.replace("{{ODPOVED}}", nginx_map)
    write(os.path.join(WEB, "nginx.conf"), nginx)
    cloudflare_files(cfg, digest if answer else "")
    return bool(answer)


def cloudflare_files(cfg, digest):
    """Brána pro Cloudflare (web/cloudflare/worker.js) a web/wrangler.jsonc pro `npm run nasadit-cloudflare`."""
    tpl = os.path.join(WEB, "cloudflare", "worker.sablona.js")
    if not os.path.exists(tpl):
        return
    # Adresa https://<web>.<nazev>.workers.dev: cloudflare.nazev = subdoména účtu (jedna na účet, zakládá ji
    # nasadit_cloudflare.mjs), cloudflare.web = název webu na účtu (výchozí „rodokmen“; druhý projekt na stejném
    # účtu musí mít jiný, jinak by první web přepsal).
    cf = cfg.get("cloudflare") or {}
    for pole, priklad in (("nazev", "novakovi"), ("web", "rodokmen-dvorakovi")):
        hodnota = (cf.get(pole) or "").strip()
        if hodnota and not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,48}[a-z0-9])?", hodnota):
            sys.exit(f"CHYBA: cloudflare.{pole} v data/web.json „{hodnota}“ nejde použít – jen malá písmena bez diakritiky, "
                     f"číslice a pomlčky (nejvýš 50 znaků), např. „{priklad}“.")
    web_nazev = (cf.get("web") or "").strip() or "rodokmen"
    worker = (open(tpl, encoding="utf-8").read().replace("{{HASH}}", digest)
              .replace("{{OTEVRENY}}", "false" if digest else "true"))
    write(os.path.join(WEB, "cloudflare", "worker.js"), worker)
    wrangler = {
        "name": web_nazev,
        "main": "cloudflare/worker.js",
        "compatibility_date": "2026-10-01",
        "workers_dev": True,      # adresa https://<web>.<subdoména>.workers.dev
        "preview_urls": False,    # bez zvláštních adres pro jednotlivé verze
        "assets": {"directory": "./dist", "binding": "ASSETS", "run_worker_first": True,
                   "not_found_handling": "404-page"},
    }
    write(os.path.join(WEB, "wrangler.jsonc"),
          "// Vyrábí tools/export_web.py – ručně neupravovat. Nasazení: npm run nasadit-cloudflare.\n"
          + json.dumps(wrangler, ensure_ascii=False, indent=2) + "\n")


def main():
    ns = load_people()
    P, LINES, SIDE, ISSUES = ns["P"], ns["LINES"], ns["SIDE"], ns["ISSUES"]
    have_people = os.path.exists(os.path.join(DATA, "osoby.py"))
    have_houses = os.path.exists(os.path.join(DATA, "domy.py"))
    if not have_people and not have_houses:
        sys.exit("V projektu chybí data/osoby.py i data/domy.py – není co exportovat.")
    if have_people and 1 not in P:
        sys.exit("V data/osoby.py chybí výchozí osoba (číslo 1).")
    SAME = ns["SAME"]                       # alias Kekulé → kanonické Kekulé (předek v rodokmenu vícekrát)
    cfg = jload("web.json", {})
    login = cfg.get("prihlaseni") or {}
    if "--nasazeni" in sys.argv and not norm_answer(str(login.get("odpoved", ""))) and not login.get("otevreny"):
        if str(login.get("odpoved", "")).strip():
            sys.exit("CHYBA: odpověď na přihlašovací otázku musí obsahovat písmena nebo číslice z latinky "
                     "(azbuka a samotné symboly nejdou, diakritika nevadí). Zvolte s uživatelem jinou odpověď.")
        sys.exit("CHYBA: v data/web.json není odpověď na přihlašovací otázku – web by byl otevřený komukoli.\n"
                 "Nastavte prihlaseni.odpoved, nebo (jen když to opravdu chcete) prihlaseni.otevreny: true.")
    skryte = neverejne_obrazky(cfg)
    if skryte:
        print(f"Otevřený web: {len(skryte)} obrázků archiv bez souhlasu nedovoluje zveřejnit, na webu bude jen přepis "
              "a odkaz (seznam: python3 -I tools/kontrola.py, reference/podminky.md)")
    docs_cfg = [d for d in jload("dokumenty.json", []) if not d.get("skryt") and d.get("img") not in skryte]   # "skryt": true = na web nedávat
    maps_cfg = [m for m in jload("mapy.json", []) if m.get("img") not in skryte]
    recs = {r["key"]: r for r in record_rows(skryte)}
    hns = domy_web.load_houses(DATA) if have_houses else None
    if hns:
        chyby = domy_web.chyby_jmen_obrazku("data/mapy.json", [m.get("img", "") for m in maps_cfg]) + \
            domy_web.chyby_dat(hns["OBEC"], hns["D"], maps_cfg, jload("zaznamy.json", []), jload("svazky.json", {}), jload("mista.json", {}))
        if chyby:
            sys.exit("CHYBA: data by rozbila web:\n  " + "\n  ".join(chyby) + "\nOprav je (python3 -I tools/kontrola.py) a export pusť znovu.")

    slugs, used = {}, set()
    for k in sorted(P):
        p = P[k]
        if placeholder(p) or k in SAME:
            continue
        yv = (p.get("y") or "").strip()
        ys = [] if yv.startswith(("?", "†")) else re.findall(r"\d{4}", yv)   # rok úmrtí do adresy nedávat
        s = slugify(p["n"] + (" " + ys[0] if ys else ""))
        if s in used or not s:
            s = f"{s}-{k}"
        used.add(s)
        slugs[k] = s
    for a, c in list(SAME.items()):
        if c not in slugs:   # hlavní osoba je zástupná (bez jména) nebo chybí – alias nemá kam ukazovat
            print(f"POZOR: SAME {a} -> {c} – osoba {c} je zástupná nebo chybí, alias vynechávám (oprav data/osoby.py)")
            del SAME[a]
            continue
        slugs[a] = slugs[c]
    aliases_of = {}
    for a, c in SAME.items():
        aliases_of.setdefault(c, []).append(a)

    def line_of(k):
        g = gen(k)
        return k >> (g - 3) if g >= 3 else None

    people = {}
    for k, p in sorted(P.items()):
        if k not in slugs or k in SAME:
            continue
        path, c = [], k
        while c >= 1:
            path.append(slugs.get(c))
            c //= 2
        people[slugs[k]] = dict(
            k=k, slug=slugs[k], name=p["n"], y=p.get("y", ""), years=years(p.get("y")), st=p.get("st", "unk"),
            status=STATUS.get(p.get("st"), ""), gen=gen(k), sex="M" if k == 1 and p.get("sex", "M") == "M" or k > 1 and k % 2 == 0 else "F",
            rel=relation(k), line=line_of(k), facts=p.get("f", []), note=p.get("note", ""), records=[r for r in p.get("r", []) if r in recs],
            father=slugs.get(2 * k), mother=slugs.get(2 * k + 1),
            fatherUnknown=(2 * k in P and placeholder(P[2 * k])), motherUnknown=(2 * k + 1 in P and placeholder(P[2 * k + 1])),
            child=slugs.get(k // 2) if k > 1 else None, spouse=slugs.get(k ^ 1) if k > 1 else None,
            family=None, ownFamily=None, path=path,
            side=[dict(name=s["n"], text=s.get("t", ""), records=[r for r in s.get("r", []) if r in recs]) for s in SIDE if s["k"] == k],
            docs=[dict(img=d["img"], caption=d.get("popis", "")) for d in docs_cfg if k in d.get("osoby", [])],
            children=[slugs[c] for c in [k // 2] + [a // 2 for a in aliases_of.get(k, [])] if k > 1 and c in slugs],
            also=[dict(k=a, rel=relation(a), line=line_of(a), child=slugs.get(a // 2)) for a in aliases_of.get(k, [])],
        )
        if aliases_of.get(k):
            for a in aliases_of[k]:
                people[slugs[k]]["records"] = list(dict.fromkeys(people[slugs[k]]["records"] + [r for r in P.get(a, {}).get("r", []) if r in recs]))
            people[slugs[k]]["facts"] = [f for f in people[slugs[k]]["facts"] if not f.startswith("TÁŽ OSOBA")]

    families = {}
    for k in sorted(P):
        f, m = 2 * k, 2 * k + 1
        if k not in slugs or k in SAME or (f not in slugs and m not in slugs):
            continue
        fs, ms = slugs.get(f), slugs.get(m)
        fid = "-a-".join(x for x in (fs, ms) if x) if fs and ms else (fs or ms) + "-rodina"
        surname = ((P[m]["n"].split() or [""])[-1] if m in P else "").strip("()?")   # i zástupná matka bez jména
        mfacts = [x for x in P.get(f, {}).get("f", []) + P.get(m, {}).get("f", []) if x.startswith("×")]
        marriage = [x for x in mfacts if surname and surname[:5] in x] or mfacts
        frec = P.get(f, {}).get("r", []) + P.get(m, {}).get("r", [])
        child_rec = [r for r in P[k].get("r", []) if r in recs and recs[r]["kind"] == "N"]
        rlist = [r for r in dict.fromkeys(frec) if r in recs and recs[r]["kind"] == "O"] + child_rec
        if fid in families:   # stejný pár potkán dvakrát (předek v rodokmenu vícekrát) – jedna rodina, víc dětí
            fam = families[fid]
            fam["children"].append(slugs[k])
            fam["records"] = list(dict.fromkeys(fam["records"] + rlist))
            fam["side"] += people[slugs[k]]["side"]
        else:
            families[fid] = dict(id=fid, father=fs, mother=ms, fatherUnknown=f in P and placeholder(P[f]),
                                 child=slugs[k], children=[slugs[k]], marriage=marriage, records=rlist,
                                 line=line_of(f) if f in P else line_of(m), gen=gen(f), side=list(people[slugs[k]]["side"]))
        people[slugs[k]]["family"] = fid
        for x in (fs, ms):
            if x:
                people[x]["ownFamily"] = fid

    house_part = domy_web.sestav(hns, recs, docs_cfg, maps_cfg, jload("mista.json", {}), cfg, VYREZY, ZDROJE,
                                 {k: slugs[k] for k in slugs}) if hns else None
    refs = {}
    for s, p in people.items():
        for r in p["records"] + [r for e in p["side"] for r in e["records"]]:
            refs.setdefault(r, []).append(s)
    hl = jload("zvyrazneni.json", {})
    prep = jload("prepisy.json", {})
    records = []
    for key, r in recs.items():
        r = dict(r)
        r["boxes"] = hl.get(key, {}).get("boxes", [])
        tr = prep.get(key, {})
        r["orig"], r["cs"] = tr.get("orig", ""), tr.get("cs", "")
        r["kindName"] = KINDS.get(r["kind"], r["kind"])
        r["people"] = list(dict.fromkeys(refs.get(key, [])))
        if house_part:
            r["houses"] = list(dict.fromkeys(house_part["recordHouses"].get(key, [])))
            r["village"] = key in house_part["villageRecords"]
        records.append(r)

    lines = {}
    for k, (name, desc) in sorted(LINES.items()):
        if k not in LINE_COLORS:
            continue
        members = [(p["k"], p) for p in people.values() if p["line"] == k]
        members += [(a["k"], p) for p in people.values() for a in p["also"] if a["line"] == k]
        members.sort(key=lambda x: x[0])
        ls = slugify(name)
        if ls in lines:   # dva rody stejného jména (např. Novákové z obou stran) – jinak by jeden tiše zmizel
            print(f"POZOR: rody {lines[ls]['k']} a {k} mají stejný název „{name}“ – rozliš je v LINES (data/osoby.py)")
            ls = f"{ls}-{k}"
        lines[ls] = dict(k=k, slug=ls, name=name, desc=desc, color=LINE_COLORS[k],
                                    root=slugs.get(k), people=[p["slug"] for _, p in members],
                                    gens={p["slug"]: gen(kk) for kk, p in members})
    lines = {s: l for s, l in lines.items() if l["root"]}
    for p in people.values():
        p["lineSlug"] = next((l["slug"] for l in lines.values() if l["k"] == p["line"]), None)

    places = []
    for name, e in jload("mista.json", {}).items():
        if "lat" not in e:
            continue
        rx = re.compile(e.get("re") or re.escape(name))
        hits = [p for p in people.values() if rx.search(" ".join(p["facts"]))]
        byline = {}
        for p in sorted(hits, key=lambda p: p["k"]):
            byline.setdefault(p["line"] or 0, []).append(p["slug"])
        if e.get("hypoteza"):
            byline = {e.get("rod", 0): []}
        if not byline:
            continue
        yrs = [int(y) for p in hits for y in re.findall(r"\b1[4-9]\d\d\b", p["y"] or "")]
        addresses = []   # přesné body domů (mista.py, "adresy"): osoby, které mají u místa daný čp.
        for cp, a in sorted((e.get("adresy") or {}).items(), key=lambda x: int(x[0])):
            arx = re.compile(rf"(?:{e.get('re') or re.escape(name)})\w*\s+čp\.\s*{re.escape(cp)}(?!\d)")
            who = [p for p in sorted(hits, key=lambda p: p["k"]) if arx.search(" ".join(p["facts"]))]
            if "lat" in a and who:
                addresses.append(dict(cp=cp, lat=a["lat"], lon=a["lon"], line=who[0]["line"] or 0, people=[p["slug"] for p in who]))
        places.append(dict(name=name, lat=e["lat"], lon=e["lon"], lines=[dict(k=k, people=v) for k, v in sorted(byline.items())],
                           years=[min(yrs), max(yrs)] if yrs else None, hypothesis=bool(e.get("hypoteza")), addresses=addresses))

    known = [p for p in people.values() if p["k"] > 1]
    stats = dict(ancestors=len(known), documented=sum(p["st"] == "doc" for p in known), records=len(records),
                 generations=max((p["gen"] for p in people.values()), default=-1) + 1)
    hypotheses = [dict(line=h.get("rod"), title=h.get("nadpis", "Hypotéza"), text=h.get("text", ""),
                       items=[dict(name=a, text=b) for a, b in h.get("polozky", [])],
                       records=[r for r in h.get("zaznamy", []) if r in recs]) for h in ns["HYPOTEZY"]]

    has_story = os.path.exists(os.path.join(DATA, "pribeh.md"))
    public_cfg = {k: v for k, v in cfg.items() if k != "prihlaseni"}
    # další příběhy: data/pribeh_<slug>.md → /pribehy/<slug>/ (původ: export_web.py z dejiny-domu-skill, bda6028)
    extra_stories = []
    for fn in sorted(os.listdir(DATA)):
        m = re.match(r"pribeh_([a-z0-9-]+)\.md$", fn)
        if not m:
            continue
        text = strip_comments(open(os.path.join(DATA, fn), encoding="utf-8").read())
        fm = dict(re.findall(r"^(title|lead|poradi|obdobi):\s*(.*)$", text.split("---")[1] if text.startswith("---") else "", re.M))
        poradi = fm.get("poradi", "").strip()
        extra_stories.append(dict(slug=m.group(1), title=fm.get("title", m.group(1)).strip().strip("'\""),
                                  lead=fm.get("lead", "").strip().strip("'\""), text=text,
                                  poradi=int(poradi) if poradi.isdigit() else 99, obdobi=fm.get("obdobi", "").strip().strip("'\"")))
    extra_stories.sort(key=lambda st: (st["poradi"], st["slug"]))
    public_cfg["maPribeh"] = has_story or bool(extra_stories)
    public_cfg["maHlavniPribeh"] = has_story
    public_cfg["dalsiPribehy"] = [{k: v for k, v in st.items() if k != "text"} for st in extra_stories]
    site = dict(config=public_cfg, places=places, root=slugs.get(1), aliases={a: slugs[a] for a in SAME}, people=people,
                families=families, records=records, lines=lines,
                issues=[dict(title=i, text="") if isinstance(i, str) else dict(title=i[0], text=i[1]) for i in ISSUES], stats=stats, hypotheses=hypotheses,
                docs=[dict(img=d["img"], caption=d.get("popis", ""), people=[slugs[k] for k in d.get("osoby", []) if k in slugs])
                      for d in docs_cfg if os.path.exists(os.path.join(VYREZY, d["img"] + ".jpg"))])
    if house_part:   # dějiny domu a obce: klíče village, houses, maps… (stránky domu se zapínají podle nich, viz lib/data.js)
        for k in ("recordHouses", "villageRecords"):
            house_part.pop(k)
        site.update(house_part)
        site["stats"].update(house_part["houseStats"])

    write(os.path.join(WEB, "src", "data", "site.json"), json.dumps(site, ensure_ascii=False, indent=1))
    gen_dir = os.path.join(WEB, "src", "generated")
    for src, dst in (("archivni_dotazy.md", "dotazy.md"), ("research_log.md", "denik.md"), ("zajimavosti.md", "zajimavosti.md")):
        path = os.path.join(DATA, src)
        text = open(path, encoding="utf-8-sig").read() if os.path.exists(path) else ""
        write(os.path.join(gen_dir, dst), strip_comments(re.sub(r"^# .*\n", "", text, count=1)))
    story = os.path.join(DATA, "pribeh.md")
    write(os.path.join(gen_dir, "pribeh.md"), strip_comments(open(story, encoding="utf-8-sig").read()) if has_story else "---\ntitle: Příběh\nlead: ''\n---\n")

    stories_dir = os.path.join(gen_dir, "pribehy")
    os.makedirs(stories_dir, exist_ok=True)
    for old in os.listdir(stories_dir):
        if old.endswith(".md") and old[:-3] not in {st["slug"] for st in extra_stories}:
            os.remove(os.path.join(stories_dir, old))
    for st in extra_stories:
        write(os.path.join(stories_dir, st["slug"] + ".md"), st["text"])

    if not have_people:   # bez rodokmenu: prázdný vějíř, aby stránky, které ho načítají, šly sestavit (v nabídce nejsou)
        write(os.path.join(gen_dir, "fan.svg"), '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"></svg>\n')
    if have_people:
        hrefs = os.path.join(gen_dir, "fan_hrefs.json")
        json.dump({k: f"/osoba/{s}/" for k, s in slugs.items()}, open(hrefs, "w", encoding="utf-8", newline="\n"))
        subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(TOOLS, "fan_chart.py"),
                        os.path.join(gen_dir, "fan.svg"), "--web", hrefs], check=True, capture_output=True)

    gated = login_files(cfg)

    copied = 0
    zv = os.path.join(DATA, "zvyrazneni.json")
    hl_mtime = os.path.getmtime(zv) if os.path.exists(zv) else 0
    for sub, src_dir in (("img", VYREZY), ("zdroje", ZDROJE)):
        dst_dir = os.path.join(WEB, "public", sub)
        os.makedirs(dst_dir, exist_ok=True)
        for key in list(recs) + [d["img"] for d in docs_cfg] + [m["img"] for m in maps_cfg] + ([cfg["uvod"]["foto"]] if cfg.get("uvod", {}).get("foto") else []):
            src = os.path.join(src_dir, key + ".jpg")
            dst = os.path.join(dst_dir, key + ".jpg")
            if key in skryte:   # bez souhlasu archivu se na veřejný web nedostane; zůstat tam po dřívějším exportu nesmí
                if os.path.exists(dst):
                    os.remove(dst)
                continue
            if not os.path.exists(src):
                continue
            boxes = hl.get(key, {}).get("boxes", [])
            stale = not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst) \
                or (sub == "zdroje" and boxes and hl_mtime > os.path.getmtime(dst))
            if not stale:
                continue
            if sub == "zdroje" and boxes and draw_boxes(src, dst, boxes, os.path.join(VYREZY, key + ".jpg")):
                copied += 1
                continue
            shutil.copy2(src, dst)
            copied += 1
    houses_info = f"{len(house_part['houses'])} domů, {len(house_part['maps'])} map, " if house_part else ""
    print(f"{len(people)} osob, {len(families)} rodin, {houses_info}{len(records)} zápisů, {len(lines)} rodů, {len(places)} míst; "
          f"zkopírováno {copied} obrázků; přihlášení {'zapnuté' if gated else 'VYPNUTÉ (web je otevřený)'}")

    # odkazy v textech, které nikam nevedou (adresa osoby se změní třeba doplněním roku narození: jan-novak → jan-novak-1798)
    targets = dict(osoba=people, zdroj=recs, rod=lines, rodina=families, dum=(house_part or {}).get("houses", {}))
    texts = {f: open(os.path.join(gen_dir, f), encoding="utf-8").read() for f in ("pribeh.md", "zajimavosti.md")}
    texts.update({f"pribeh_{st['slug']}.md": st["text"] for st in extra_stories})
    texts["web.json"] = json.dumps(cfg, ensure_ascii=False)
    texts["osoby.py (hypotézy)"] = json.dumps(hypotheses, ensure_ascii=False)
    broken = [(f, m.group(0)) for f, t in texts.items()
              for m in re.finditer(r"/(osoba|zdroj|rod|rodina|dum)/([^/\s)\"'#?<>\]]+)", t) if m.group(2) not in targets[m.group(1)]]
    for f, link in dict.fromkeys(broken):
        print(f"POZOR: nefunkční odkaz {link}/ v {f} – oprav ho (adresy stránek jsou ve web/src/data/site.json)")


if __name__ == "__main__":
    main()
