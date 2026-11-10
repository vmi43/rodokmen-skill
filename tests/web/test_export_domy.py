"""Test exportu domů a obce do webu (shared/tools/export_web.py + domy_web.py, skill rodokmen:dum).

Z kořene repozitáře, složka `shared` je argument:
  python3 -I tests/web/test_export_domy.py shared
  (Windows: python -I -X utf8 …)
Každý případ si postaví vlastní dočasný projekt s vymyšlenými daty (tools/, šablonové soubory přihlášení, data/).
Nic nestahuje a nespouští npm, jen export_web.py a standardní knihovna.
"""
import json, os, shutil, subprocess, sys, tempfile

SHARED = os.path.abspath(sys.argv[1])
PY = [sys.executable, "-I", "-X", "utf8"]
VYSLEDKY = []

OSOBY = 'P = {1: {"n": "Jan Novák", "st": "doc", "r": ["z1"], "f": ["* 1900 Lhota 1"]}}\nSIDE = []\nLINES = {}\nSAME = {}\n'
DOMY = ('OBEC = dict(nazev="Lhota", lat=49.5, lon=14.4)\n'
        'OBEC_UDALOSTI = [dict(rok="1352", text="První zmínka", st="lit", r=["z1"])]\n'
        'D = {"1": dict(nazev="U Nováků", st="doc", lat=49.5, lon=14.4, cisla=[("od 1830", "čp. 1")],\n'
        '  drzitele=[dict(od="1800", do="1820", n="Jan Novák", st="doc", r=["z1"], os=1)],\n'
        '  obyvatele=[dict(n="Marie", y="1790–1850", st="fam")], pribeh=["Odstavec."])}\n'
        'ISSUES = [("Kdo postavil dům?", "Otevřené: neznámo")]\n')
ZAZNAMY = [{"klic": "z1", "druh": "G", "datum": "1800", "nazev": "Kniha", "shrnuti": "x"}]
JPEG = b"\xff\xd8\xff\xe0" + b"\0" * 60   # obsah nehraje roli, export jen kopíruje


def zapis(cesta, text, mod="w"):
    os.makedirs(os.path.dirname(cesta), exist_ok=True)
    with open(cesta, mod, **({"encoding": "utf-8", "newline": "\n"} if mod == "w" else {})) as f:
        f.write(text)


def export(domy=DOMY, osoby=OSOBY, zaznamy=ZAZNAMY, mapy=None, obrazky=(), web=None, pribehy=None):
    """Vrátí (rc, výstup, složka site.json nebo None, složka projektu) – projekt se smaže až v `uklid`."""
    tmp = tempfile.mkdtemp(prefix="export_domy_")
    zapis(os.path.join(tmp, "data", "STAV.md"), "x")
    zapis(os.path.join(tmp, "data", "domy.py"), domy)
    if osoby is not None:
        zapis(os.path.join(tmp, "data", "osoby.py"), osoby)
    zapis(os.path.join(tmp, "data", "zaznamy.json"), json.dumps(zaznamy))
    zapis(os.path.join(tmp, "data", "web.json"), json.dumps(web or {"nazev": "Test", "prihlaseni": {"odpoved": "ano"}}))
    if mapy is not None:
        zapis(os.path.join(tmp, "data", "mapy.json"), json.dumps(mapy))
    for nazev, text in (pribehy or {}).items():
        zapis(os.path.join(tmp, "data", nazev), text)
    for img in obrazky:
        zapis(os.path.join(tmp, "vyrezy", img + ".jpg"), JPEG, "wb")
    tmpl = os.path.join(SHARED, "template", "web")
    for rel in ("prihlaseni.sablona.html", "nginx.sablona.conf", os.path.join("netlify", "brana.sablona.js")):
        os.makedirs(os.path.dirname(os.path.join(tmp, "web", rel)), exist_ok=True)
        shutil.copy(os.path.join(tmpl, rel), os.path.join(tmp, "web", rel))
    shutil.copytree(os.path.join(SHARED, "tools"), os.path.join(tmp, "tools"), ignore=shutil.ignore_patterns("__pycache__"))
    p = subprocess.run([*PY, "tools/export_web.py"], cwd=tmp, capture_output=True, text=True, encoding="utf-8")
    site = os.path.join(tmp, "web", "src", "data", "site.json")
    return p.returncode, p.stdout + p.stderr, (json.load(open(site, encoding="utf-8")) if os.path.exists(site) else None), tmp


def pripad(nazev, podminka, vysledek):
    rc, vystup, site, tmp = vysledek
    try:
        ok = bool(podminka(rc, vystup, site, tmp))
    except Exception as e:   # noqa: BLE001 – chybějící klíč v site.json = selhání případu, ne pád testu
        ok, vystup = False, f"{vystup}\n{type(e).__name__}: {e}"
    shutil.rmtree(tmp, ignore_errors=True)
    VYSLEDKY.append(ok)
    print(("OK  " if ok else "SELHÁNÍ ") + nazev)
    if not ok:
        print(f"    rc={rc}, výstup:\n" + "\n".join("    " + l for l in vystup.splitlines()))


pripad("projekt jen s domy (bez osoby.py) se vyexportuje",
       lambda rc, o, s, t: rc == 0 and list(s["houses"]) == ["1"] and s["mainHouse"] == "1" and s["village"]["name"] == "Lhota"
       and s["stats"]["houses"] == 1 and s["stats"]["owners"] == 1 and s["root"] is None and s["people"] == {},
       export(osoby=None))
pripad("události obce a zápisy se vážou na domy",
       lambda rc, o, s, t: s["village"]["events"][0]["records"] == ["z1"] and s["houses"]["1"]["records"] == ["z1"]
       and s["records"][0]["houses"] == ["1"] and s["records"][0]["village"] is True and s["records"][0]["kindName"].startswith("gruntovní"),
       export(osoby=None))
pripad("pole os se změní na adresu osoby (rodokmen i domy)",
       lambda rc, o, s, t: rc == 0 and s["houses"]["1"]["owners"][0]["person"] == "jan-novak"
       and s["houses"]["1"]["people"][0]["person"] is None and s["records"][0]["people"] == ["jan-novak"],
       export())
pripad("javascript: odkaz v zápisu zastaví export",
       lambda rc, o, s, t: rc != 0 and "CHYBA" in o and "javascript:" in o,
       export(zaznamy=[dict(ZAZNAMY[0], odkaz="javascript:alert(1)")]))
pripad("poloha jen s lat zastaví export",
       lambda rc, o, s, t: rc != 0 and "CHYBA" in o and "lon" in o,
       export(domy=DOMY.replace("lat=49.5, lon=14.4, cisla", "lat=49.5, cisla")))
pripad("klíč mapy s lomítkem zastaví export",
       lambda rc, o, s, t: rc != 0 and "CHYBA" in o and "bez lomítek" in o,
       export(mapy=[{"img": "../tajne", "nazev": "x"}]))
pripad("mapa a její obrázek jdou na web, jedna mapa není skupina",
       lambda rc, o, s, t: rc == 0 and s["maps"][0]["img"] == "mapa1" and s["mapGroups"] == {}
       and os.path.exists(os.path.join(t, "web", "public", "img", "mapa1.jpg")),
       export(mapy=[{"img": "mapa1", "rok": 1840, "nazev": "Stabilní katastr", "skupina": "lhota"}], obrazky=["mapa1"]))
pripad("web bez hesla nezveřejní obrázek archivu, který chce souhlas",
       lambda rc, o, s, t: rc == 0 and "bez souhlasu nedovoluje" in o and not os.path.exists(os.path.join(t, "web", "public", "img", "z1.jpg"))
       and s["records"][0]["img"] is False,
       export(zaznamy=[dict(ZAZNAMY[0], odkaz="https://digi.archives.cz/da/x")], obrazky=["z1"],
              web={"nazev": "Test", "prihlaseni": {"otevreny": True}}))
pripad("web s heslem obrázek zveřejní (za heslem to smí)",
       lambda rc, o, s, t: rc == 0 and os.path.exists(os.path.join(t, "web", "public", "img", "z1.jpg")) and s["records"][0]["img"] is True,
       export(zaznamy=[dict(ZAZNAMY[0], odkaz="https://digi.archives.cz/da/x")], obrazky=["z1"]))
pripad("odkaz /dum/x/, který nikam nevede, se ohlásí",
       lambda rc, o, s, t: rc == 0 and "nefunkční odkaz /dum/nikde/" in o,
       export(web={"nazev": "Test", "prihlaseni": {"odpoved": "ano"}, "uvod": {"text": "viz /dum/nikde/"}}))
PRIBEHY = {
    "pribeh_obec.md": "---\ntitle: Ves Lhota\nlead: 'Od založení.'\nporadi: 2\n---\nText.\n",
    "pribeh_cp1.md": "---\ntitle: Statek čp. 1\nporadi: 1\nobdobi: 1800–dnes\n---\n<!-- poznámka pro Clauda -->\nText o domu.\n",
}
pripad("další příběhy se vyexportují seřazené a bez poznámek pro Clauda",
       lambda rc, o, s, t: rc == 0 and [p["slug"] for p in s["config"]["dalsiPribehy"]] == ["cp1", "obec"]
       and s["config"]["dalsiPribehy"][0]["obdobi"] == "1800–dnes" and s["config"]["dalsiPribehy"][1]["lead"] == "Od založení."
       and s["config"]["maPribeh"] is True and s["config"]["maHlavniPribeh"] is False and "text" not in s["config"]["dalsiPribehy"][0]
       and "poznámka" not in open(os.path.join(t, "web", "src", "generated", "pribehy", "cp1.md"), encoding="utf-8").read(),
       export(pribehy=PRIBEHY))
pripad("bez příběhů není v nabídce příběh a seznam je prázdný",
       lambda rc, o, s, t: rc == 0 and s["config"]["dalsiPribehy"] == [] and s["config"]["maPribeh"] is False,
       export())
pripad("odkaz /dum/x/ v dalším příběhu se ohlásí",
       lambda rc, o, s, t: rc == 0 and "nefunkční odkaz /dum/nikde/ v pribeh_cp1.md" in o,
       export(pribehy={"pribeh_cp1.md": "---\ntitle: A\n---\nviz [dům](/dum/nikde/)\n"}))

print(f"\n{sum(VYSLEDKY)} z {len(VYSLEDKY)} v pořádku")
sys.exit(0 if all(VYSLEDKY) else 1)
