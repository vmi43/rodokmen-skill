"""Test voleb --dum, --jen-dum a --bez-webu v shared/tools/novy_projekt.py (skill rodokmen:dum).

Z kořene repozitáře, složka `shared` je argument:
  python3 -I tests/web/test_novy_projekt_dum.py shared
  (Windows: python -I -X utf8 …)
Každý případ zakládá vlastní dočasný projekt. Nic nestahuje a nespouští npm, jen novy_projekt.py,
export_web.py a standardní knihovna.
"""
import json, os, shutil, subprocess, sys, tempfile

SHARED = os.path.abspath(sys.argv[1])
PY = [sys.executable, "-I", "-X", "utf8"]
VYSLEDKY = []


def zaloz(dst, *args):
    r = subprocess.run(PY + [os.path.join(SHARED, "tools", "novy_projekt.py"), dst, *args],
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout + r.stderr


def export(dst):
    r = subprocess.run(PY + [os.path.join(dst, "tools", "export_web.py")], cwd=dst,
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout + r.stderr


def pripad(nazev, podminka):
    tmp = tempfile.mkdtemp(prefix="novy_dum_")
    try:
        ok = bool(podminka(os.path.join(tmp, "projekt")))
    except Exception as e:   # noqa: BLE001 – chyba testu je neúspěch případu
        print("   výjimka:", repr(e))
        ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    VYSLEDKY.append(ok)
    print(("OK    " if ok else "CHYBA ") + nazev)


def je(dst, *cesta):
    return os.path.exists(os.path.join(dst, *cesta))


def bez_voleb(dst):
    rc, _ = zaloz(dst)
    return rc == 0 and je(dst, "data", "osoby.py") and not je(dst, "data", "domy.py")


def s_dum(dst):
    rc, _ = zaloz(dst, "--dum")
    return rc == 0 and je(dst, "data", "osoby.py") and je(dst, "data", "domy.py") and je(dst, "tools", "domy_web.py")


def jen_dum(dst):
    rc, _ = zaloz(dst, "--jen-dum")
    return (rc == 0 and je(dst, "data", "domy.py") and not je(dst, "data", "osoby.py")
            and je(dst, "data", "web.json") and je(dst, "data", "zaznamy.json"))


def jen_dum_export(dst):
    """Prázdná šablona domů bez rodokmenu se musí dát exportovat (web jen s obcí a domy)."""
    zaloz(dst, "--jen-dum")
    rc, out = export(dst)
    if rc != 0:
        print(out)
        return False
    site = json.load(open(os.path.join(dst, "web", "src", "data", "site.json"), encoding="utf-8"))
    return site.get("people", {}) == {} or not site.get("people")


def dodatecne(dst):
    zaloz(dst)
    rc, _ = zaloz(dst, "--dum")
    return rc == 0 and je(dst, "data", "domy.py") and je(dst, "data", "osoby.py")


def neprepise(dst):
    zaloz(dst, "--dum")
    p = os.path.join(dst, "data", "domy.py")
    with open(p, "a", encoding="utf-8") as f:
        f.write("# moje úprava\n")
    zaloz(dst, "--dum")
    return "# moje úprava" in open(p, encoding="utf-8").read()


def nemaze_osoby(dst):
    zaloz(dst)
    rc, out = zaloz(dst, "--jen-dum")
    return rc == 0 and je(dst, "data", "osoby.py") and "POZOR" in out


def s_ukazkou(dst):
    rc, _ = zaloz(dst, "--dum", "--ukazka")
    return rc == 0 and je(dst, "data", "domy.py") and je(dst, "data", "osoby.py")


def jen_dum_ukazka(dst):
    rc, out = zaloz(dst, "--jen-dum", "--ukazka")
    return rc != 0 and "nejdou spolu" in out and not je(dst, "data")


def bez_webu(dst):
    rc, _ = zaloz(dst, "--bez-webu")
    return rc == 0 and not je(dst, "web") and je(dst, "tools", "export_web.py") and je(dst, "data", "STAV.md")


def bez_webu_pak_s_webem(dst):
    zaloz(dst, "--bez-webu")
    rc, _ = zaloz(dst)
    return rc == 0 and je(dst, "web", "package.json")


def s_webem_a_bez_webu_nesmaze_web(dst):
    zaloz(dst)
    rc, _ = zaloz(dst, "--bez-webu")
    return rc == 0 and je(dst, "web", "package.json")


pripad("bez voleb: žádné domy", bez_voleb)
pripad("--dum: domy.py a nástroj domy_web.py, rodokmen zůstává", s_dum)
pripad("--jen-dum: domy.py bez osoby.py", jen_dum)
pripad("--jen-dum: export_web.py proběhne bez rodokmenu", jen_dum_export)
pripad("--dum jde dodatečně na existující projekt", dodatecne)
pripad("--dum nepřepíše upravený domy.py", neprepise)
pripad("--jen-dum na projekt s rodokmenem osoby.py nemaže, jen upozorní", nemaze_osoby)
pripad("--dum --ukazka: ukázkový rodokmen i domy.py", s_ukazkou)
pripad("--jen-dum s --ukazka skončí chybou a nic nezaloží", jen_dum_ukazka)
pripad("--bez-webu: data a nástroje, bez web/", bez_webu)
pripad("--bez-webu a pak běh bez volby web doplní", bez_webu_pak_s_webem)
pripad("--bez-webu na projekt s webem web nesmaže", s_webem_a_bez_webu_nesmaze_web)

print(f"\n{sum(VYSLEDKY)} z {len(VYSLEDKY)} v pořádku")
sys.exit(0 if all(VYSLEDKY) else 1)
