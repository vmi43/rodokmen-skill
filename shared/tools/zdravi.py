#!/usr/bin/env python3
"""Kontrola portálů: funguje každý nástroj ještě proti živému portálu?

Archivy mění adresy a API bez ohlášení. Nástroj spustí každý nástroj na pevném, známém svazku (čtení + jeden malý
snímek) v dočasné složce – do dat projektu nesahá – a vypíše, co funguje a co ne.

Použití (z kořene projektu i ze složky skillu):
  zdravi.py                 všechny kontroly (~25 požadavků, pár minut)
  zdravi.py --rychle        bez stahování snímků
  zdravi.py --jen aron,cuzk
                            jen vybrané portály (názvy viz výpis)
Původ: převzato z vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/zdravi.py), commit bda6028; úprava: jen kontroly
nástrojů, které tu jsou (ostatní přibudou s nástroji). SOA Třeboň, SOA Praha a MZA stojí podle slusne.py, proto tu nejsou.
Portály, které nástrojům stahování nedovolují (tools/podminky.json), se vypíšou jako „vynecháno“.
Návratový kód 1 = aspoň jedna kontrola selhala. Selže-li portál, zkus to za chvíli znovu (výpadky bývají krátké);
trvá-li chyba, změnilo se API – oprav nástroj a zapiš to do poznamky_pro_skill.md.
"""
import glob, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)

TOOLS = os.path.dirname(os.path.abspath(__file__))
PY = [sys.executable, "-I", "-X", "utf8"]

# (portál, popis, příkaz, regex ve výstupu, výstupní obrázek nebo None)
# Pevná id: když portál svazek přečísluje, kontrola selže – to je taky zpráva (odkazy v datech projektů přestanou platit).
KONTROLY = [
    ("aron", "hledání svazků", ["aron_search.py", "Holice", "", "500"], r"0dfa5da8-0b8f-49f4-bc13-c2ea70fd100c", None),
    ("aron", "info svazku", ["aron_img.py", "0dfa5da8-0b8f-49f4-bc13-c2ea70fd100c", "info"], r"scans: [1-9]", None),
    ("aron", "snímek", ["aron_img.py", "0dfa5da8-0b8f-49f4-bc13-c2ea70fd100c", "3", "2", "{out}"], r"full size", "ar.jpg"),
    ("portafontium", "knihy fary", ["portafontium.py", "fara", "dolni-bela"], r"^dolni-bela-17 \|", None),
    ("portafontium", "snímek", ["portafontium.py", "snimek", "dolni-bela-17", "5", "{out}", "nahled"], r"odkaz:", "pf.jpg"),
    ("ahmp", "hledání svazků", ["bash", "ahmp_search.sh", "Smíchov"], r"9A79C81088C94C9DBEA2FC6758FD08E7", None),
    ("ahmp", "snímek", ["ahmp_scan.py", "9A79C81088C94C9DBEA2FC6758FD08E7", "5", "{out}", "1"], r"permalink", "ah.jpg"),
    ("policie", "hledání přihlášek", ["policie_prihlasky.py", "Kolar", "Josef"], r"záznamů", None),
    ("cuzk", "listy stabilního katastru", ["cuzk_archiv.py", "listy", "49.5234,14.4301"], r"TAB082018300", None),
    ("cuzk", "mladší řady a III. vojenské mapování", ["cuzk_archiv.py", "rady", "48.8300,14.6200"], r"1673 D1_21__4453-6", None),
    ("cuzk", "export listu", ["cuzk_archiv.py", "export", "skici", "195567", "{out}", "0,0,1,1", "400"], r"400×", "cz.jpg"),
    ("ruian", "adresa v RÚIAN", ["mista.py", "ruian", "Karlova 190/1"], r"k\. ú\. Staré Město", None),
    ("kramerius", "fulltext", ["kramerius.py", 'text_ocr:"Chyšky"', "1"], r"^found [1-9]", None),
    ("anno", "rakouské noviny", ["anno.py", "Chischka", "1880", "1890", "1"], r"ANNOP_", None),
]
# Portály bez pevného svazku (cestu k obrázku dává jen prohlížeč): jen „server odpovídá“
DOSTUPNOST = [
    ("soal", "obrázkový server SOA Litoměřice", "https://images.soalitomerice.cz/ximage/matriky/zoomify/"),
    ("opava", "obrázkový server ZA Opava", "https://images.archives.cz/ximage/matriky/zoomify/"),
    ("matricula", "Matricula", "https://data.matricula-online.eu/"),
]


def je_jpeg(path):
    """path smí obsahovat * (jméno souboru závisí na výstupu nástroje, např. ipr_praha.py)."""
    path = next(iter(glob.glob(path)), path)
    try:
        with open(path, "rb") as f:
            return f.read(3) == b"\xff\xd8\xff" and os.path.getsize(path) > 5000
    except OSError:
        return False


def server_odpovida(url):
    req = urllib.request.Request(url, headers={"User-Agent": slusne.UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, str(r.status)
    except urllib.error.HTTPError as e:   # 404 na kořeni obrázkového serveru je v pořádku – server žije
        return e.code < 500, str(e.code)
    except OSError as e:
        return False, str(getattr(e, "reason", e))
    except SystemExit as e:   # slusne.py: web zablokovaný nebo 403 na první dotaz – kontrola má pokračovat dál
        return False, str(e)[:80]


def main():
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        sys.exit(__doc__)
    rychle = "--rychle" in args
    jen = None
    if "--jen" in args:
        i = args.index("--jen")
        jen = set(args[i + 1].split(",")) if i + 1 < len(args) else set()
    portaly = {k[0] for k in KONTROLY} | {k[0] for k in DOSTUPNOST}
    if jen is not None and not jen <= portaly:
        sys.exit(f"Neznámý portál: {', '.join(sorted(jen - portaly))}. Známé: {', '.join(sorted(portaly))}")

    tmp = tempfile.mkdtemp(prefix="dejiny_zdravi_")
    selhalo = 0
    try:
        os.makedirs(os.path.join(tmp, "data"))
        open(os.path.join(tmp, "data", "STAV.md"), "w").close()   # nástroje jinak odmítnou běžet mimo projekt
        shutil.copytree(TOOLS, os.path.join(tmp, "tools"), ignore=shutil.ignore_patterns("__pycache__"))
        os.makedirs(os.path.join(tmp, "out"))
        for portal, popis, cmd, vzor, obr in KONTROLY:
            if (jen is not None and portal not in jen) or (rychle and obr):
                continue
            out = os.path.join("out", obr) if obr and "/" not in obr else obr
            cmd = [c.replace("{out}", out or "") for c in cmd]
            cmd = ["bash", "tools/" + cmd[1], *cmd[2:]] if cmd[0] == "bash" else [*PY, "tools/" + cmd[0], *cmd[1:]]
            t = time.time()
            try:
                p = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=180)
                vystup = p.stdout + p.stderr
                ok = p.returncode == 0 and re.search(vzor, p.stdout, re.M) is not None
                if ok and obr and not je_jpeg(os.path.join(tmp, out)):
                    ok, vystup = False, f"obrázek {obr} chybí nebo není JPEG\n" + vystup
            except subprocess.TimeoutExpired:
                ok, vystup = False, "vypršel čas (180 s)"
            radky = [r for r in vystup.strip().splitlines() if r.strip()]
            if not ok and "potřebuje API klíč" in vystup:   # klíč si uživatel nevyžádal – to není porucha
                print(f"—     {portal:13} {popis:28} vynecháno (chybí API klíč, reference/portaly.md)")
                continue
            if not ok and "PODMÍNKY:" in vystup:   # portál nástrojům stahování nedovoluje (podminky.json) – to není porucha
                print(f"—     {portal:13} {popis:28} vynecháno (podmínky portálu, reference/podminky.md)")
                continue
            print(f"{'OK   ' if ok else 'CHYBA'} {portal:13} {popis:28} {time.time() - t:5.1f} s")
            if not ok:
                selhalo += 1
                for r in radky[-3:]:
                    print("      ", r[:200])
        for portal, popis, url in DOSTUPNOST:
            if jen is not None and portal not in jen:
                continue
            ok, kod = server_odpovida(url)
            print(f"{'OK   ' if ok else 'CHYBA'} {portal:13} {popis:28} (jen dostupnost, {kod})")
            selhalo += not ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'Vše funguje.' if not selhalo else f'Selhalo: {selhalo}.'}")
    sys.exit(1 if selhalo else 0)


if __name__ == "__main__":
    main()
