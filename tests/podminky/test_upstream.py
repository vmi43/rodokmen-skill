"""Test scripts/upstream.py bez internetu: zpracování odpovědi compare API a čtení základního commitu z hlaviček.

Z kořene repozitáře:  python3 -I tests/podminky/test_upstream.py
"""
import os, sys, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts"))
import upstream

ok = bad = 0


def kontrola(nazev, podminka, detail=""):
    global ok, bad
    ok, bad = (ok + 1, bad) if podminka else (ok, bad + 1)
    print(("OK  " if podminka else "CHYBA ") + nazev + ("" if podminka else "\n    " + detail))


tmp = tempfile.mkdtemp(prefix="upstream_test_")
try:
    cmp = {"files": [
        {"filename": "skills/dejiny-domu/tools/podminky.json", "status": "modified", "additions": 3, "deletions": 1, "patch": "@@ -1 +1 @@"},
        {"filename": "skills/dejiny-domu/tools/novy.py", "status": "added", "additions": 9, "deletions": 0},
        {"filename": "skills/dejiny-domu/template/web/src/pages/dum/[slug].astro", "status": "renamed",
         "previous_filename": "skills/dejiny-domu/template/web/src/pages/dum/x.astro", "additions": 0, "deletions": 0}]}
    prevzate, ostatni = upstream.zpracuj(cmp, tmp)
    kontrola("převzatý (i přejmenovaný) soubor se přiřadí k našemu", prevzate[0][1] == "shared/tools/podminky.json" and len(prevzate) == 2 and prevzate[1][2] == "renamed", str(prevzate))
    kontrola("nepřevzatý soubor jde mezi ostatní", ostatni == [("skills/dejiny-domu/tools/novy.py", "added")], str(ostatni))
    kontrola("rozdíl převzatého souboru se uloží", os.path.exists(os.path.join(tmp, "skills__dejiny-domu__tools__podminky.json.diff")))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
z = upstream.zaklad()
kontrola("základní commit se přečte z hlaviček", bool(z) and len(z) >= 7, str(z))
for nase in upstream.MAPA.values():
    kontrola(f"naše cesta existuje: {nase}", os.path.exists(os.path.join(upstream.ROOT, nase)))
print(f"\n{ok} z {ok + bad} v pořádku")
sys.exit(1 if bad else 0)
