"""Testy indexy.py (index knihy) a kontroly indexů v kontrola.py. Bez sítě.

Z kořene repozitáře:  python3 -I tests/podminky/test_indexy.py
"""
import json, os, shutil, subprocess, sys, tempfile, unittest

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared")
OSOBY = 'P = {1: {"n": "Jan Novák", "st": "doc", "r": ["z1"], "f": ["* 1900 Lhota 1"]}}\nSIDE = []\nLINES = {}\nSAME = {}\n'
ZAZNAMY = [{"klic": "z1", "druh": "N", "datum": "1900-01-01", "nazev": "Křest", "shrnuti": "x"}]
RADKY = [
    {"typ": "Z", "snimek": 1, "datum": "1840-03-02", "obec": "Lhota 4", "osoby": "zemřelý: Jan Fiala; otec: Josef Fiala", "ostatni": "70 let", "jistota": "střední"},
    {"typ": "I", "snimek": 3, "strana": "12", "kniha": "Z 1836–1882", "osoby": "Fiala Josef", "datum": "1850", "jistota": "nízká"},
]


class Indexy(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for p in ("tools", "data", "pracovni"):
            os.makedirs(os.path.join(self.d, p))
        for f in ("indexy.py", "kontrola.py"):
            shutil.copy(os.path.join(SKILL, "tools", f), os.path.join(self.d, "tools"))
        self.zapis("data/STAV.md", "# Stav\n"); self.zapis("data/osoby.py", OSOBY)
        self.zapis("data/zaznamy.json", json.dumps(ZAZNAMY))
        self.zapis("data/svazky.json", json.dumps({"abc12345": {"svazek": "Lhota Z", "snimku": 5}}))
        self.zapis("pracovni/radky.json", json.dumps(RADKY))

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def zapis(self, cesta, text):
        with open(os.path.join(self.d, cesta), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def spust(self, nastroj, *arg):
        r = subprocess.run([sys.executable, "-I", "tools/" + nastroj, *arg], cwd=self.d, capture_output=True, text=True, encoding="utf-8")
        return r.returncode, r.stdout + r.stderr

    def test_pridej_hledej_stav(self):
        rc, out = self.spust("indexy.py", "pridej", "abc12345", "pracovni/radky.json", "--cetl", "claude-opus-5-5/high")
        self.assertEqual(rc, 0, out); self.assertIn("přidáno 2", out)
        self.assertIn("claude-opus-5-5/high 20", open(os.path.join(self.d, "data", "indexy", "abc12345.tsv"), encoding="utf-8").read())
        rc, out = self.spust("indexy.py", "pridej", "abc12345", "pracovni/radky.json")   # podruhé nic nepřidá
        self.assertEqual(rc, 0, out); self.assertIn("přidáno 0", out); self.assertIn("celkem 2", out)
        rc, out = self.spust("indexy.py", "hledej", "FIALA")   # bez ohledu na velikost
        self.assertIn("shod 2", out); self.assertIn("→ Z 1836–1882", out); self.assertIn("vodítko, ne doklad", out)
        rc, out = self.spust("indexy.py", "hledej", "Fiala", "--typ", "Z")
        self.assertIn("Celkem 1 shod", out)
        rc, out = self.spust("indexy.py", "hledej", "josef")   # i ve vazbách
        self.assertIn("zemřelý: Jan Fiala", out)
        rc, out = self.spust("indexy.py", "hledej", "Novák")
        self.assertIn("Celkem 0 shod", out); self.assertIn("snímky 1–3", out)   # „nenalezeno“ nese pokrytí
        rc, out = self.spust("indexy.py", "stav")
        self.assertIn("s nízkou jistotou 1", out); self.assertIn("z 5 snímků", out)

    def test_spatny_vstup_nic_nezapise(self):
        self.zapis("pracovni/zly.json", json.dumps([{"typ": "X", "snimek": "a", "osoby": "", "jistota": "?"}, {"typ": "I", "snimek": 9, "osoby": "A", "jistota": "nízká"}]))
        rc, out = self.spust("indexy.py", "pridej", "abc12345", "pracovni/zly.json")
        self.assertNotEqual(rc, 0); self.assertIn("typ musí být", out); self.assertIn("jistota musí být", out); self.assertIn("za koncem svazku", out); self.assertIn("musí mít knihu", out)
        self.assertFalse(os.path.exists(os.path.join(self.d, "data", "indexy")))
        rc, out = self.spust("indexy.py", "pridej", "nenicklic", "pracovni/radky.json")
        self.assertNotEqual(rc, 0); self.assertIn("není v data/svazky.json", out)

    def test_kontrola_hlida_klic_a_zahlavi(self):
        self.spust("indexy.py", "pridej", "abc12345", "pracovni/radky.json")
        rc, out = self.spust("kontrola.py")
        self.assertNotIn("indexy", out.replace("tools/indexy.py", ""), out)
        os.rename(os.path.join(self.d, "data", "indexy", "abc12345.tsv"), os.path.join(self.d, "data", "indexy", "zzz.tsv"))
        rc, out = self.spust("kontrola.py")
        self.assertEqual(rc, 1); self.assertIn("klíč 'zzz' není v data/svazky.json", out)
        self.zapis("data/indexy/abc12345.tsv", "spatne\thlavicka\n")
        rc, out = self.spust("kontrola.py")
        self.assertIn("nesedí záhlaví", out)

    def test_prechylena_jmena_a_cetl(self):
        self.zapis("pracovni/zeny.json", json.dumps([{"typ": "I", "snimek": 2, "kniha": "Z", "osoby": "Fialová Josefa", "jistota": "vysoká", "cetl": "claude-opus-5-5/medium 2026-11-23"}]))
        rc, out = self.spust("indexy.py", "pridej", "abc12345", "pracovni/zeny.json")
        self.assertEqual(rc, 0, out)
        rc, out = self.spust("indexy.py", "hledej", "Fiala")   # „Fiala“ najde i „Fialová“
        self.assertIn("Celkem 1 shod", out)
        rc, out = self.spust("indexy.py", "hledej", "Fialová")
        self.assertIn("Celkem 1 shod", out)
        rc, out = self.spust("indexy.py", "hledej", "Fialek")   # jiné příjmení se nespojí
        self.assertIn("Celkem 0 shod", out)
        self.zapis("pracovni/zly_cetl.json", json.dumps([{"typ": "I", "snimek": 2, "kniha": "Z", "osoby": "Fiala X", "jistota": "vysoká", "cetl": "claude-opus (hlavní session) 2026-11-23"}]))
        rc, out = self.spust("indexy.py", "pridej", "abc12345", "pracovni/zly_cetl.json")
        self.assertNotEqual(rc, 0); self.assertIn("cetl musí být", out)

    def test_kontrola_nehlasi_historii_nastroju(self):
        self.zapis("todo.md", "- `trebon.py` odstraněn\n- ~~`stary.py` hotovo~~\n- nový krok přes `chybi.py`\n- aktualizace přes `novy_projekt.py`\n")
        rc, out = self.spust("kontrola.py")
        self.assertNotIn("trebon.py", out); self.assertNotIn("stary.py", out)
        self.assertIn("chybi.py", out); self.assertNotIn("novy_projekt.py", out)
        self.zapis("data/web.json", json.dumps({"nastroje_historie": ["chybi.py"]}))   # výjimka uživatele
        rc, out = self.spust("kontrola.py")
        self.assertNotIn("chybi.py", out)

    def test_web_index_nebere(self):
        zdroj = open(os.path.join(SKILL, "tools", "export_web.py"), encoding="utf-8").read()
        self.assertNotIn("indexy", zdroj)   # index je pracovní vodítko, na web nepatří


if __name__ == "__main__":
    unittest.main()
