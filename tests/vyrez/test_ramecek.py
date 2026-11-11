"""Test ramecek.py --vyrez: přepočet rámečku ze souřadnic stránky na souřadnice výřezu.

Z kořene repozitáře:  python3 -I tests/vyrez/test_ramecek.py shared/tools
Potřebuje ImageMagick; bez něj test neběží (vypíše to).
"""
import json, os, shutil, subprocess, sys, tempfile

TOOLS = os.path.abspath(sys.argv[1])
MAGICK = shutil.which("magick") or shutil.which("convert")
if not MAGICK:
    sys.exit("Chybí ImageMagick, test se nespustí.")
ok = bad = 0


def kontrola(nazev, podminka, detail=""):
    global ok, bad
    if podminka:
        ok += 1
        print("OK  " + nazev)
    else:
        bad += 1
        print("CHYBA " + nazev + "\n    " + detail)


def spust(tmp, *args):
    return subprocess.run([sys.executable, "-I", os.path.join(tmp, "tools", "ramecek.py"), "k", *args],
                          capture_output=True, text=True, cwd=tmp)


tmp = tempfile.mkdtemp(prefix="ramecek_")
try:
    for d in ("tools", "data", "vyrezy", "pracovni"):
        os.makedirs(os.path.join(tmp, d))
    shutil.copy(os.path.join(TOOLS, "ramecek.py"), os.path.join(tmp, "tools", "ramecek.py"))
    subprocess.run([MAGICK, "-size", "200x100", "xc:white", os.path.join(tmp, "vyrezy", "k.jpg")], check=True)
    r = spust(tmp, "0.3,0.3,0.5,0.5", "--vyrez", "0.2,0.2,0.6,0.6")
    zv = os.path.join(tmp, "data", "zvyrazneni.json")
    box = json.load(open(zv, encoding="utf-8"))["k"]["boxes"][0] if os.path.exists(zv) else None
    kontrola("stránkové souřadnice se přepočtou na výřez", box == [0.25, 0.25, 0.75, 0.75], f"{box} {r.stderr}")
    r = spust(tmp, "0.3,0.3,0.5,0.5", "--vyrez", "0.6,0.2,0.2,0.6")
    kontrola("špatná oblast výřezu skončí chybou", r.returncode != 0 and "Špatná oblast" in (r.stderr + r.stdout), r.stderr)
    r = spust(tmp, "0.1,0.1,0.4,0.4")
    box = json.load(open(zv, encoding="utf-8"))["k"]["boxes"][0]
    kontrola("bez --vyrez se souřadnice nemění", box == [0.1, 0.1, 0.4, 0.4], str(box))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print(f"\n{ok} z {ok + bad} v pořádku")
sys.exit(1 if bad else 0)
