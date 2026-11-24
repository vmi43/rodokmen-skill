"""Testy prispevek.py: výběr řádků z data/indexy/ k odeslání do komunitního indexu a odeslání (atrapa, nic naostro). Bez sítě.

Z kořene repozitáře:  python3 -I tests/podminky/test_prispevek.py
"""
import importlib.util, io, json, os, shutil, subprocess, sys, tempfile, unittest, urllib.error

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared")
HLAVICKA = "snimek\tdatum\ttyp\tobec\tosoby\tostatni\tjistota\tcetl\todkaz\tstrana\tkniha\n"
CETL = "claude-opus-5-5/high 2026-11-24"


def radek(snimek, datum, typ, osoby, ostatni="", cetl=CETL, strana="", kniha="", jistota="střední"):
    return "\t".join([str(snimek), datum, typ, "Lhota 4", osoby, ostatni, jistota, cetl, "", strana, kniha]) + "\n"


INDEX = HLAVICKA + radek(1, "1850-03-02", "Z", "zemřelý: Jan Fiala", "70 let", strana="12") \
    + radek(2, "1990-01-01", "N", "dítě: Petr") \
    + radek(3, "1850-05-05", "Z", "zemřelý: Anna Fiala", cetl="") \
    + radek(4, "", "Z", "zemřelý: Karel") \
    + radek(5, "1850-06-06", "Z", "zemřelý: Josef Fiala", "můj praděd") \
    + radek(6, "1850", "I", "Fiala Josef", kniha="Z 1836–1882") \
    + radek(7, "1860-01-01", "O", "ženich: Václav; nevěsta: Marie", jistota="nízká")


class Prispevek(unittest.TestCase):
    def setUp(self):
        self.popen = subprocess.Popen.__init__   # slusne.py při načtení zabalí Popen: po testu ho vrátíme
        self.d = tempfile.mkdtemp()
        shutil.copytree(os.path.join(SKILL, "tools"), os.path.join(self.d, "tools"), ignore=shutil.ignore_patterns("__pycache__"))
        os.makedirs(os.path.join(self.d, "data", "indexy")); os.makedirs(os.path.join(self.d, "pracovni"))
        self.zapis("data/STAV.md", "# Stav\n")
        self.zapis("data/svazky.json", json.dumps({
            "pf1": {"svazek": "Lhota Z", "snimku": 50, "url": "https://www.portafontium.eu/register/soap-pn/lhota-1"},
            "aron1": {"svazek": "ARON kniha", "snimku": 9, "url": "https://aron.vychodoceskearchivy.cz/apu/620ba073-6edf-496f-bb7e-e389cb8fcd24"}}))
        self.zapis("data/indexy/pf1.tsv", INDEX)
        self.zapis("data/indexy/aron1.tsv", HLAVICKA + radek(1, "1850-03-02", "Z", "zemřelý: Jan"))

    def tearDown(self):
        subprocess.Popen.__init__ = self.popen
        shutil.rmtree(self.d, ignore_errors=True)

    def zapis(self, cesta, text):
        with open(os.path.join(self.d, cesta), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def spust(self, *arg):
        r = subprocess.run([sys.executable, "-I", "tools/prispevek.py", *arg], cwd=self.d, capture_output=True, text=True, encoding="utf-8")
        return r.returncode, r.stdout + r.stderr

    def modul(self):
        sp = importlib.util.spec_from_file_location("prispevek_t", os.path.join(self.d, "tools", "prispevek.py"))
        m = importlib.util.module_from_spec(sp)
        sys.path.insert(0, os.path.join(self.d, "tools"))
        try:
            sp.loader.exec_module(m)
        finally:
            sys.path.pop(0)
        m.slusne.pockej = lambda *a, **k: None
        return m

    def otisk(self):
        rc, out = self.spust("navrh")
        self.assertEqual(rc, 0, out)
        return out, out.split("Otisk dávky: ")[1].split()[0]

    def test_navrh_vybere_jen_zpusobile(self):
        out, _ = self.otisk()
        self.assertIn("K odeslání: 2 řádků", out)   # Fiala Jan (1850 Z) a sňatek 1860 (O)
        self.assertIn("zemřelý: Jan Fiala", out); self.assertNotIn("Anna Fiala", out)
        for duvod in ("mladší zákonné lhůty", "chybí sloupec cetl", "řádek bez data", "rejstřík (typ I)", "o příbuzenství", "nepodporuje"):
            self.assertIn(duvod, out)
        dav = json.load(open(os.path.join(self.d, "pracovni", "sdileni", "prispevek.json"), encoding="utf-8"))["zapisy"]
        self.assertEqual([z["archiv"] for z in dav], ["portafontium", "portafontium"])
        self.assertIn("70 let; str. 12", [z["ostatni"] for z in dav]); self.assertTrue(all(z["cetl"].endswith("(z rodokmenu)") for z in dav))
        self.assertIn("Nic neodešlo", out)

    def test_bez_souhlasu_se_neodesle(self):
        _, otisk = self.otisk()
        rc, out = self.spust("odeslat", otisk)
        self.assertEqual(rc, 1); self.assertIn("Bez souhlasu", out)

    def test_odeslani_zapise_a_neposle_dvakrat(self):
        m = self.modul()
        _, otisk = self.otisk()
        self.assertEqual(self.spust("souhlas", "ano")[0], 0)
        poslano = []

        class Odp(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): return False
        def falesne(req, timeout=0):
            poslano.append(json.loads(req.data.decode("utf-8")))
            return Odp(json.dumps({"mapa": None, "index": "https://github.com/x/pull/1"}).encode())
        m.urllib.request.urlopen = falesne
        rc = m.odeslat(otisk)
        self.assertEqual(rc, 0)
        self.assertEqual(len(poslano), 1); self.assertEqual(len(poslano[0]["zapisy"]), 2)
        self.assertRegex(poslano[0]["klic"], r"^[A-Za-z0-9_-]{32,128}$")
        self.assertNotIn("Jan +", poslano[0]["zapisy"][0]["cetl"])   # anonymně
        self.assertEqual(len(json.load(open(os.path.join(self.d, "data", "sdileni.json")))["odeslano"]), 2)
        out = self.spust("navrh")[1]
        self.assertIn("K odeslání: 0", out); self.assertIn("už odesláno dříve", out)

    def test_jmeno_jen_se_souhlasem_a_chyba_nezapise(self):
        m = self.modul()
        self.assertEqual(self.spust("souhlas", "ano", "Jan Test")[0], 0)
        _, otisk = self.otisk()
        def chyba(req, timeout=0):
            raise urllib.error.HTTPError(req.full_url, 429, "limit", {}, io.BytesIO(b'{"chyba":"limit"}'))
        m.urllib.request.urlopen = chyba
        with self.assertRaises(SystemExit) as c:
            m.odeslat(otisk)
        self.assertIn("429", str(c.exception)); self.assertIn("Nic se nezapsalo", str(c.exception))
        n = json.load(open(os.path.join(self.d, "data", "sdileni.json")))
        self.assertEqual(n["odeslano"], [])
        dav = json.load(open(os.path.join(self.d, "pracovni", "sdileni", "prispevek.json"), encoding="utf-8"))["zapisy"]
        self.assertTrue(dav[0]["cetl"].startswith("Jan Test + "))

    def test_nesedici_otisk_nic_neposle(self):
        m = self.modul()
        self.spust("souhlas", "ano")
        m.urllib.request.urlopen = lambda *a, **k: self.fail("nemělo se odesílat")
        with self.assertRaises(SystemExit) as c:
            m.odeslat("000000000000")
        self.assertIn("Otisk dávky nesedí", str(c.exception))

    def test_indexy_py_nema_sit(self):
        zdroj = open(os.path.join(SKILL, "tools", "indexy.py"), encoding="utf-8").read()
        for slovo in ("urllib", "http.client", "subprocess", "socket"):
            self.assertNotIn(slovo, zdroj)


if __name__ == "__main__":
    unittest.main()
