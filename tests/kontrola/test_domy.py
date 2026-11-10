"""Test kontroly data/domy.py v tools/kontrola.py (skill rodokmen:dum), hlavně vazby `os` na data/osoby.py.

Z kořene repozitáře, testovaná kontrola je argument:
  python3 -I tests/kontrola/test_domy.py shared/tools/kontrola.py
  (Windows: python -I -X utf8 …)
Každý případ si postaví vlastní dočasný projekt s vymyšlenými daty. Nic nestahuje, jen standardní knihovna.
"""
import json, os, shutil, subprocess, sys, tempfile

KONTROLA = os.path.abspath(sys.argv[1])
PY = [sys.executable, "-I", "-X", "utf8"]
VYSLEDKY = []

OSOBY = 'P = {1: {"n": "Jan Novák", "st": "doc", "r": ["z1"], "f": ["* 1900 Lhota 1"]}}\nSIDE = []\nLINES = {}\nSAME = {}\n'
ZAZNAMY = [{"klic": "z1", "druh": "N", "datum": "1900-01-01", "nazev": "Křest", "shrnuti": "x"}]


def zapis(cesta, text):
    os.makedirs(os.path.dirname(cesta), exist_ok=True)
    with open(cesta, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def kontrola(domy, osoby=OSOBY):
    """Vrátí (návratový kód, výstup) kontrola.py nad projektem s daným domy.py (a osoby.py, je-li zadáno)."""
    tmp = tempfile.mkdtemp(prefix="kontrola_domy_")
    try:
        zapis(os.path.join(tmp, "data", "domy.py"), domy)
        if osoby is not None:
            zapis(os.path.join(tmp, "data", "osoby.py"), osoby)
        zapis(os.path.join(tmp, "data", "zaznamy.json"), json.dumps(ZAZNAMY))
        os.makedirs(os.path.join(tmp, "tools"))
        shutil.copy(KONTROLA, os.path.join(tmp, "tools", "kontrola.py"))
        p = subprocess.run([*PY, "tools/kontrola.py"], cwd=tmp, capture_output=True, text=True, encoding="utf-8")
        return p.returncode, p.stdout + p.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def pripad(nazev, domy, ocekavej, osoby=OSOBY, rc=None):
    kod, vystup = kontrola(domy, osoby)
    ok = (ocekavej in vystup if ocekavej else "CHYBA" not in vystup) and (rc is None or kod == rc)
    VYSLEDKY.append(ok)
    print(("OK  " if ok else "SELHÁNÍ ") + nazev)
    if not ok:
        print(f"    rc={kod}, čekáno „{ocekavej}“, výstup:\n" + "\n".join("    " + l for l in vystup.splitlines()))


DOBRE = ('OBEC = dict(nazev="Lhota", lat=49.5, lon=14.4)\nOBEC_UDALOSTI = []\n'
         'D = {"1": dict(st="doc", lat=49.5, lon=14.4, drzitele=[dict(od="1800", do="1820", n="Jan Novák", st="doc", r=["z1"], os=1)],'
         ' obyvatele=[dict(n="Jan Novák", y="1900–1950", st="doc", r=["z1"], os=1)])}\n')

pripad("dobrá data projdou bez chyby", DOBRE, None, rc=0)
pripad("os na neexistující osobu je chyba", DOBRE.replace("os=1)],", "os=99)],", 1), "osoba 99 v data/osoby.py není", rc=1)
pripad("os, který není číslo, je chyba", DOBRE.replace("os=1)]", 'os="1")]', 1), "'os' má být číslo osoby", rc=1)
pripad("citace neexistujícího zápisu je chyba", DOBRE.replace('r=["z1"], os=1)],', 'r=["nic"], os=1)],', 1), "neexistující zápis 'nic'", rc=1)
pripad("držitel od po do je chyba", DOBRE.replace('od="1800", do="1820"', 'od="1850", do="1820"'), "je po 'do'", rc=1)
pripad("poloha mimo Česko je upozornění", DOBRE.replace("lat=49.5, lon=14.4, drzitele", "lat=14.4, lon=49.5, drzitele"), "mimo Česko", rc=0)
pripad("klíč domu jako číslo je chyba", DOBRE.replace('D = {"1"', "D = {1"), "klíč domu piš jako text", rc=1)
pripad("projekt jen s domy (bez osoby.py) běží; os pak nemá kam ukazovat", DOBRE, "osoba 1 v data/osoby.py není", osoby=None, rc=1)
pripad("projekt jen s domy bez os projde", DOBRE.replace(", os=1", ""), None, osoby=None, rc=0)

print(f"\n{sum(VYSLEDKY)} z {len(VYSLEDKY)} v pořádku")
sys.exit(0 if all(VYSLEDKY) else 1)
