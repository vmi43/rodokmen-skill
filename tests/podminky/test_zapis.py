"""Testy zapis.py: zápis položek beze změny zbytku souboru, zámek mezi procesy, deník s číslováním. Bez sítě.

Z kořene repozitáře:  python3 -I tests/podminky/test_zapis.py
Původ: výřez z tests/test_nastroje.py z vzoha/dejiny-domu-skill (commit 32bef07): třídy Projekt, TestZapis a část
TestSoubeh; cesty upraveny, testy nástrojů, které u nás nezapisují přes zapis.py (ebadatelna, mista), vynechány.
"""
import json, os, re, shutil, subprocess, sys, tempfile, time, unittest

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared")

DOMY = '''
OBEC = dict(nazev="Horní Lhota", jine_nazvy="Ober-Lhotta", obec="Horní Lhota, okres Pelhřimov",
            farnost="Dolní Lhota", panstvi="Kamenice", popis="Ves na kopci.", lat=49.4, lon=15.2)
OBEC_UDALOSTI = [
    dict(rok="1352", text="První zmínka o vsi.", st="lit", zdroj="vlastivěda, s. 12"),
]
D = {
    "12": dict(nazev="U Nováků", druh="chalupa", st="doc", popis="Chalupa u návsi.", lat=49.41, lon=15.21,
               udalosti=[dict(rok="1890", text="Sčítání lidu: 7 osob.", st="doc", r=["lhota_scitani_cp12_1890"])],
               drzitele=[dict(od="1820", do="1850", n="Josef Novák", st="doc", r=["lhota_scitani_cp12_1890"]),
                         dict(od="?", do="1820", n="Jan Novák", st="fam"),
                         dict(od="1786", do="1800", n="Matěj Dvořák", st="lit", zdroj="kronika, s. 3")],
               obyvatele=[dict(n="Josef Novák", y="1795–1860", role="hospodář", st="doc", r=["lhota_scitani_cp12_1890"])]),
}
ISSUES = [("Kdo byl držitel před 1786?", "Otevřené: gruntovní kniha není online.")]
'''

ZAZNAM = {"klic": "lhota_scitani_cp12_1890", "druh": "S", "datum": "1890", "nazev": "Sčítání lidu 1890, čp. 12",
          "shrnuti": "Domácnost Josefa Nováka, 7 osob.", "svazek": "trebon_4250", "snimek": "5",
          "odkaz": "https://digi.ceskearchivy.cz/4250/5"}
SVAZEK = {"archiv": "SOA Třeboň", "portal": "digi.ceskearchivy.cz", "svazek": "Sčítání lidu 1890",
          "popis": "Horní Lhota", "snimku": 40, "url": "https://digi.ceskearchivy.cz/4250"}


class Projekt(unittest.TestCase):
    """Nový projekt ze šablony v dočasné složce; pomocné funkce na spouštění nástrojů a čtení dat."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="dejiny_test_")
        self.root = os.path.join(self.tmp, "Horni-Lhota-12")
        p = subprocess.run([sys.executable, "-I", os.path.join(SKILL, "tools", "novy_projekt.py"), self.root],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def path(self, *p):
        return os.path.join(self.root, *p)

    def nastroj(self, nazev, *args, vstup=None):
        return subprocess.run([sys.executable, "-I", "-X", "utf8", self.path("tools", nazev), *args], cwd=self.root,
                              input=vstup, capture_output=True, text=True, encoding="utf-8")

    def zapis(self, soubor, klic, obj, *volby):
        vstup = self.path("pracovni", "vstup.json")
        with open(vstup, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        return self.nastroj("zapis.py", soubor, klic, vstup, *volby)

    def text(self, *p):
        with open(self.path(*p), encoding="utf-8", newline="") as f:
            return f.read()

    def data(self, soubor):
        return json.loads(self.text("data", soubor + ".json"))

    def napln(self):
        """Malý úplný projekt: jeden dům, jeden zápis se svazkem, výřezem, rámečkem a přepisem."""
        with open(self.path("data", "domy.py"), "w", encoding="utf-8") as f:
            f.write(DOMY)
        for args in (("zaznamy", ZAZNAM["klic"], ZAZNAM), ("svazky", "trebon_4250", SVAZEK),
                     ("prepisy", ZAZNAM["klic"], {"orig": "Novak Josef", "cs": "Novák Josef"}),
                     ("zvyrazneni", ZAZNAM["klic"], {"boxes": [[0.1, 0.1, 0.9, 0.5]]})):
            p = self.zapis(*args)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        for d in ("vyrezy", "zdroje"):
            with open(self.path(d, ZAZNAM["klic"] + ".jpg"), "wb") as f:
                f.write(JPEG)



class TestZapis(Projekt):

    def test_pridani_do_prazdneho_seznamu(self):
        p = self.zapis("zaznamy", "a_1", {"druh": "N", "nazev": "Křest Jana Nováka"})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("přidáno", p.stdout)
        self.assertEqual(self.data("zaznamy"), [{"druh": "N", "nazev": "Křest Jana Nováka", "klic": "a_1"}])

    def test_format_ceske_znaky_a_lf(self):
        self.zapis("zaznamy", "a_1", {"nazev": "Křest Jana Nováka"})
        t = self.text("data", "zaznamy.json")
        self.assertIn("Křest", t)            # ne Ř
        self.assertNotIn("\r\n", t)
        self.assertTrue(t.endswith("\n"))

    def test_nahrazeni_meni_jen_tu_polozku(self):
        self.zapis("zaznamy", "a_1", {"nazev": "první"})
        self.zapis("zaznamy", "a_2", {"nazev": "druhá"})
        pred = self.text("data", "zaznamy.json")
        p = self.zapis("zaznamy", "a_1", {"nazev": "první opravená"})
        self.assertIn("změněno", p.stdout)
        po = self.text("data", "zaznamy.json")
        self.assertEqual([z["nazev"] for z in self.data("zaznamy")], ["první opravená", "druhá"])
        zmenene = [(a, b) for a, b in zip(pred.splitlines(), po.splitlines()) if a != b]
        self.assertEqual(len(pred.splitlines()), len(po.splitlines()))
        self.assertEqual(len(zmenene), 1, zmenene)   # zbytek souboru doslova stejný

    def test_bez_sloucit_nahradi_celou_polozku(self):
        self.zapis("zaznamy", "a_1", {"nazev": "x", "datum": "1890"})
        self.zapis("zaznamy", "a_1", {"nazev": "y"})
        self.assertNotIn("datum", self.data("zaznamy")[0])

    def test_sloucit_doplni_pole(self):
        self.zapis("zaznamy", "a_1", {"nazev": "x", "datum": "1890"})
        self.zapis("zaznamy", "a_1", {"shrnuti": "doplněno"}, "--sloucit")
        self.assertEqual(self.data("zaznamy")[0], {"nazev": "x", "datum": "1890", "klic": "a_1", "shrnuti": "doplněno"})

    def test_slovnik_pridani_a_nahrazeni(self):
        self.zapis("svazky", "trebon_1", {"svazek": "A"})
        self.zapis("svazky", "trebon_2", {"svazek": "B"})
        self.zapis("svazky", "trebon_1", {"svazek": "A2"})
        self.assertEqual(self.data("svazky"), {"trebon_1": {"svazek": "A2"}, "trebon_2": {"svazek": "B"}})
        self.assertEqual(list(self.data("svazky")), ["trebon_1", "trebon_2"])   # pořadí zůstane

    def test_web_textova_hodnota_ze_vstupu(self):
        p = self.nastroj("zapis.py", "web", "nazev", "-", vstup='"Dějiny Horní Lhoty"')
        self.assertEqual(p.returncode, 0, p.stderr)
        web = self.data("web")
        self.assertEqual(web["nazev"], "Dějiny Horní Lhoty")
        self.assertIn("prihlaseni", web)   # ostatní nastavení zůstalo

    def test_jinde_nez_web_musi_byt_objekt(self):
        p = self.nastroj("zapis.py", "svazky", "x", "-", vstup='"text"')
        self.assertNotEqual(p.returncode, 0)

    def test_spatny_json_nezmeni_soubor(self):
        self.zapis("zaznamy", "a_1", {"nazev": "x"})
        pred = self.text("data", "zaznamy.json")
        p = self.nastroj("zapis.py", "zaznamy", "a_1", "-", vstup='{"nazev": ')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("není platný JSON", p.stdout + p.stderr)
        self.assertEqual(self.text("data", "zaznamy.json"), pred)

    def test_rozbity_soubor_dat_neprepise(self):
        with open(self.path("data", "zaznamy.json"), "w", encoding="utf-8") as f:
            f.write('[{"klic": "a_1",')
        p = self.zapis("zaznamy", "a_2", {"nazev": "y"})
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(self.text("data", "zaznamy.json"), '[{"klic": "a_1",')

    def test_klic_nesouhlasi_se_vstupem(self):
        p = self.zapis("zaznamy", "a_1", {"klic": "a_2"})
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(self.data("zaznamy"), [])

    def test_neznamy_soubor(self):
        p = self.zapis("domy", "12", {})
        self.assertNotEqual(p.returncode, 0)

    def test_odmitne_bezet_ze_slozky_skillu(self):
        p = subprocess.run([sys.executable, "-I", os.path.join(SKILL, "tools", "zapis.py"), "svazky", "x", "-"],
                           input="{}", capture_output=True, text=True, encoding="utf-8")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("není složka projektu", p.stdout + p.stderr)
        self.assertFalse(os.path.exists(os.path.join(SKILL, "data")))




class TestSoubeh(Projekt):
    """Souběžní pomocníci: zámek v zapis.py a nástroje, které do data/ zapisují přes něj."""

    def py(self, kod, cekat=True):
        cmd = [sys.executable, "-I", "-X", "utf8", "-c", "import sys; sys.path.insert(0, 'tools')\n" + kod]
        if not cekat:
            return subprocess.Popen(cmd, cwd=self.root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, encoding="utf-8")

    def test_zapis_pocka_na_zamek_a_cizi_zmenu_neprepise(self):
        drzi = self.py("import zapis, time\nwith zapis.zamek('svazky'):\n    print('mam', flush=True)\n    time.sleep(1)\n"
                       "    zapis.zamek = lambda n: __import__('contextlib').nullcontext()\n"
                       "    zapis.zapis('svazky', 'prvni', {'svazek': 'A'})", cekat=False)
        self.assertEqual(drzi.stdout.readline().strip(), "mam")
        druhy = subprocess.Popen([sys.executable, "-I", self.path("tools", "zapis.py"), "svazky", "druhy", "-"], cwd=self.root,
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        druhy.stdin.write(b'{"svazek": "B"}')
        druhy.stdin.close()
        time.sleep(0.4)
        self.assertIsNone(druhy.poll(), "zapis.py nečekal na zámek")
        self.assertEqual(drzi.wait(), 0, drzi.stderr.read())
        self.assertEqual(druhy.wait(), 0, druhy.stderr.read())
        self.assertEqual(sorted(self.data("svazky")), ["druhy", "prvni"])

    def test_drzeny_zamek_skonci_hlaskou(self):
        drzi = self.py("import zapis, time\nwith zapis.zamek('svazky'):\n    print('mam', flush=True)\n    time.sleep(5)",
                       cekat=False)
        self.assertEqual(drzi.stdout.readline().strip(), "mam")
        p = self.py("import zapis; zapis.CEKANI_NA_ZAMEK = 0.3; zapis.zapis('svazky', 's1', {})")
        drzi.kill()
        drzi.communicate()
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("zapisuje jiný proces", p.stderr)

    def test_denik_cislo_prideli_sam(self):
        log = self.path("data", "research_log.md")
        with open(log, "a", encoding="utf-8") as f:   # ručně dopsaný řádek s vyšším číslem
            f.write("| 7 | 1. 11. 2026 | Matriky | 1800 | křest | nic | M 1 |\n")
        for zdroj in ("Sčítání 1890", "Kronika"):
            p = self.nastroj("zapis.py", "denik", zdroj, "celé", "Novák", "nalezeno a|b", "inv. 1")
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        p = self.nastroj("zapis.py", "denik", "Gruntovnice", "1700–1800", "?", "nic", "GK 1", "--datum", "9. 11. 2026")
        self.assertIn("řádek 10", p.stdout)
        radky = [r for r in self.text("data", "research_log.md").splitlines() if r.startswith("| ") and r[2].isdigit()]
        self.assertEqual([r.split(" | ")[0] for r in radky[-3:]], ["| 8", "| 9", "| 10"])
        self.assertIn("nalezeno a\\|b", radky[-2])
        self.assertTrue(radky[-1].startswith("| 10 | 9. 11. 2026 | Gruntovnice |"))

    def test_neplatny_unicode_odmitne_bez_zmeny_souboru(self):
        self.zapis("svazky", "a", {"svazek": "Gruntovní kniha"})
        pred = self.text("data", "svazky.json")
        vstup = self.path("pracovni", "vstup.json")
        with open(vstup, "w", encoding="utf-8") as f:
            f.write('{"svazek": "Grunt\\ud800"}')   # osamělá polovina páru UTF-16
        p = self.nastroj("zapis.py", "svazky", "a", vstup)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("neplatný znak", p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        self.assertEqual(self.text("data", "svazky.json"), pred)


if __name__ == "__main__":
    unittest.main()
