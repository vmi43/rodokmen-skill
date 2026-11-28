"""Test upozornění na celé knihy v tools/kontrola.py: kniha *_manual ještě v pracovni/, svazek `upload: manual`
bez složky v knihy/. Obojí je jen upozornění (kontrola projde), snímky jdou stáhnout znovu.

Z kořene repozitáře, testovaná kontrola je argument:
  python3 -I tests/kontrola/test_knihy.py shared/tools/kontrola.py
  (Windows: python -I -X utf8 …)
Nic nestahuje, jen standardní knihovna.
"""
import json, os, shutil, subprocess, sys, tempfile

KONTROLA = os.path.abspath(sys.argv[1])
PY = [sys.executable, "-I", "-X", "utf8"]
VYSLEDKY = []


def zapis(cesta, text):
    os.makedirs(os.path.dirname(cesta), exist_ok=True)
    with open(cesta, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def kontrola(svazky, knihy=(), pracovni=()):
    """Postaví projekt se svazky a složkami knih a vrátí (návratový kód, výstup kontrola.py)."""
    tmp = tempfile.mkdtemp(prefix="kontrola_knihy_")
    try:
        zapis(os.path.join(tmp, "data", "osoby.py"), "P = {1: dict(n='Jan Novák', st='fam')}\n")
        zapis(os.path.join(tmp, "data", "svazky.json"), json.dumps(svazky, ensure_ascii=False))
        for kde, jmena in (("knihy", knihy), ("pracovni", pracovni)):
            for n in jmena:
                zapis(os.path.join(tmp, kde, n, "s1.jpg"), "x")
        os.makedirs(os.path.join(tmp, "tools"))
        shutil.copy(KONTROLA, os.path.join(tmp, "tools", "kontrola.py"))
        r = subprocess.run(PY + [os.path.join(tmp, "tools", "kontrola.py")], capture_output=True, text=True,
                           encoding="utf-8")
        return r.returncode, r.stdout + r.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def pripad(popis, ok, vystup):
    VYSLEDKY.append(ok)
    print(("  [OK] " if ok else "  [CHYBA] ") + popis + ("" if ok else "\n" + vystup))


MANUAL = {"upload": "manual", "svazek": "Loučeň 05"}

rc, out = kontrola({"ebad_8084": MANUAL, "1a2b3c4d": MANUAL, "ebad_a_1349": MANUAL, "strojovy": {"svazek": "x"}},
                   knihy=["ebad_8084_loucen_05_manual", "aron_1a2b3c4d_lhota_manual", "ebad_a_1349_jikev_manual"])
pripad("knihy v knihy/ (i ARON aron_<apu8>_…): bez upozornění", rc == 0 and "knihy/" not in out, out)

rc, out = kontrola({"ebad_8084": MANUAL}, pracovni=["ebad_8084_loucen_05_manual"])
pripad("kniha v pracovni/: upozornění, ne chyba, a svazek se nehlásí podruhé",
       rc == 0 and "upozornění: 1 knih je ještě v pracovni/" in out and "nemá složku" not in out, out)

rc, out = kontrola({"ebad_8084": MANUAL, "ebad_9": MANUAL, "strojovy": {"svazek": "x"}},
                   knihy=["ebad_8084_loucen_05_manual", "ebad_90_jiny_manual"])
pripad("svazek upload: manual bez složky: upozornění jen pro něj (ebad_9 ≠ ebad_90), strojový svazek ne",
       rc == 0 and "1 svazků s upload: manual nemá složku v knihy/ (ebad_9)" in out and "strojovy" not in out, out)

print(f"{sum(VYSLEDKY)} z {len(VYSLEDKY)} v pořádku")
sys.exit(0 if all(VYSLEDKY) else 1)
