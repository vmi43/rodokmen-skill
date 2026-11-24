"""Testy zarad.py: zařazení ručně stažených knih (obsah.txt, přejmenování, svazky.json). Bez sítě.

Z kořene repozitáře:  python3 -I tests/podminky/test_zarad.py
"""
import json, os, shutil, subprocess, sys, tempfile, unittest

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared")

ARCHIVALIE = """jikev-pozemkova-kniha

Original title
Kniha gruntovní obce
Archival fund
Velkostatek Křinec
Date from to
1773 - 1853
Inventory number
2206
Signature
Nymburk 48
Scans
{n}

Localities
Jíkev / Jikew / Jikev

https://ebadatelna.soapraha.cz/pages/ArchivaliePage/archivalieId/1349/idx/{n}
"""
MATRIKA = """loucen-05

Date from to
1800 - 1850
Number of scans
2

https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/8084
"""
ARON = """Lhota 4321

Státní oblastní archiv v Hradci Králové: Sbírka matrik Východočeského kraje, sign.: 4321 (poř.č. 4301), 3.1862-11.1921

MATRIČNÍ MÍSTO
Lhota (Chrudim, Česko), obec v okrese Chrudim

https://aron.vychodoceskearchivy.cz/apu/1a2b3c4d-0000-4000-8000-000000000001/dao/1a2b3c4d-0000-4000-8000-000000000001/file/
"""


class Zarad(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.d, "tools")); os.makedirs(os.path.join(self.d, "data")); os.makedirs(os.path.join(self.d, "pracovni"))
        for f in ("zarad.py", "zapis.py"):
            shutil.copy(os.path.join(SKILL, "tools", f), os.path.join(self.d, "tools"))
        open(os.path.join(self.d, "data", "STAV.md"), "w").write("# Stav\n")
        self.sv(None)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def sv(self, nove):
        p = os.path.join(self.d, "data", "svazky.json")
        if nove is None:
            open(p, "w").write("{}\n")
        else:
            json.dump(nove, open(p, "w"), ensure_ascii=False)

    def cti_sv(self):
        return json.load(open(os.path.join(self.d, "data", "svazky.json"), encoding="utf-8"))

    def slozka(self, jmeno, obsah, soubory):
        p = os.path.join(self.d, "pracovni", jmeno)
        os.makedirs(p)
        if obsah is not None:
            open(os.path.join(p, "obsah.txt"), "w", encoding="utf-8").write(obsah)
        for f in soubory:
            open(os.path.join(p, f), "wb").write(b"\xff\xd8x")
        return p

    def spust(self, *arg):
        r = subprocess.run([sys.executable, "-I", "tools/zarad.py", *arg], cwd=self.d, capture_output=True, text=True, encoding="utf-8")
        return r.returncode, r.stdout + r.stderr

    def test_nahled_nic_nemeni(self):
        self.slozka("jikev-pozemkova-kniha", ARCHIVALIE.format(n=3), [f"jikev-{i:03d}.jpg" for i in (1, 2, 3)])
        rc, out = self.spust()
        self.assertEqual(rc, 0, out)
        self.assertIn("ebad_a_1349", out)
        self.assertTrue(os.path.isdir(os.path.join(self.d, "pracovni", "jikev-pozemkova-kniha")))
        self.assertEqual(self.cti_sv(), {})

    def test_archivalie_proved(self):
        self.slozka("jikev-pozemkova-kniha", ARCHIVALIE.format(n=3), ["a-10.jpg", "a-2.jpg", "a-3.jpg"])
        rc, out = self.spust("--proved")
        self.assertEqual(rc, 0, out)
        cil = os.path.join(self.d, "pracovni", "ebad_a_1349_jikev_pozemkova_kniha_manual")
        self.assertEqual(sorted(os.listdir(cil)), ["obsah.md", "obsah.txt", "s1.jpg", "s2.jpg", "s3.jpg"])
        z = self.cti_sv()["ebad_a_1349"]
        self.assertEqual((z["upload"], z["snimku"], z["typ"], z["portal"]), ("manual", 3, "archivalie", "eBadatelna"))
        self.assertIn("1773–1853", z["svazek"]); self.assertIn("sign. Nymburk 48", z["svazek"])
        self.assertEqual(z["popis"], "Jíkev")

    def test_archivalie_klic_z_projektu(self):
        self.sv({"archivalie_1349": {"svazek": "Jíkev, pozemková kniha", "archiv": "SOA Praha", "portal": "eBadatelna"}})
        self.slozka("jikev-pozemkova-kniha", ARCHIVALIE.format(n=1), ["x1.jpg"])
        rc, out = self.spust("--proved")
        self.assertEqual(rc, 0, out)
        self.assertTrue(os.path.isdir(os.path.join(self.d, "pracovni", "archivalie_1349_jikev_manual")), out)
        self.assertEqual(self.cti_sv()["archivalie_1349"]["upload"], "manual")
        self.assertEqual(self.cti_sv()["archivalie_1349"]["archiv"], "SOA Praha")   # stará pole zůstala

    def ke_stazeni(self, radky):
        cesta = os.path.join(self.d, "data", "ke_stazeni.md")
        open(cesta, "w", encoding="utf-8").write("# Knihy ke stažení\n\n| Stav | Kniha | Matrika |\n|---|---|---|\n" + "\n".join(radky) + "\n")
        return cesta

    def test_ke_stazeni_odskrtne_jen_zarazenou_knihu(self):
        cesta = self.ke_stazeni([
            "| [ ] | Loučeň | https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/8084 |",
            "| [ ] | jiná Loučeň | https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/80841 |",
            "| [ ] | Lhota | https://aron.vychodoceskearchivy.cz/apu/1a2b3c4d-0000-4000-8000-000000000001 |"])
        self.slozka("loucen-05", MATRIKA, ["a.jpg", "b.jpg"])
        rc, out = self.spust("--proved")
        self.assertEqual(rc, 0, out)
        self.assertIn("odškrtnuto 1", out)
        r = open(cesta, encoding="utf-8").read().split("\n")
        self.assertIn("[x] zařazeno `ebad_8084`", [x for x in r if "| Loučeň |" in x][0])
        self.assertIn("[ ]", [x for x in r if "jiná Loučeň" in x][0])   # 80841 není 8084
        self.assertIn("[ ]", [x for x in r if "Lhota" in x][0])

    def test_ke_stazeni_aron_podle_apu(self):
        cesta = self.ke_stazeni(["| [ ] | Lhota | https://aron.vychodoceskearchivy.cz/apu/1a2b3c4d-0000-4000-8000-000000000001 |"])
        self.slozka("lhota", ARON, ["a.jpg"])
        rc, out = self.spust("--proved", "--ignoruj-pocet")
        self.assertEqual(rc, 0, out)
        self.assertIn("[x] zařazeno `1a2b3c4d`", open(cesta, encoding="utf-8").read())

    def test_ke_stazeni_bez_souboru_a_bez_radku(self):
        self.slozka("loucen-05", MATRIKA, ["a.jpg", "b.jpg"])
        rc, out = self.spust("--proved")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("ke_stazeni", out)                      # projekt bez souboru: nic se nehlásí ani nezakládá
        self.assertFalse(os.path.exists(os.path.join(self.d, "data", "ke_stazeni.md")))
        shutil.rmtree(os.path.join(self.d, "pracovni", "ebad_8084_loucen_05_manual"))
        cesta = self.ke_stazeni(["| [ ] | cizí | https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/1 |"])
        self.slozka("loucen-05", MATRIKA, ["a.jpg", "b.jpg"])
        rc, out = self.spust("--proved")
        self.assertEqual(rc, 0, out)
        self.assertIn("nic neodškrtnuto", out)
        self.assertNotIn("[x]", open(cesta, encoding="utf-8").read())

    def test_nahled_neodskrtava(self):
        cesta = self.ke_stazeni(["| [ ] | Loučeň | https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/8084 |"])
        self.slozka("loucen-05", MATRIKA, ["a.jpg", "b.jpg"])
        rc, out = self.spust()
        self.assertEqual(rc, 0, out)
        self.assertNotIn("[x]", open(cesta, encoding="utf-8").read())

    def test_pocet_nesedi(self):
        p = self.slozka("jikev-pozemkova-kniha", ARCHIVALIE.format(n=5), ["a1.jpg", "a2.jpg"])
        rc, out = self.spust("--proved")
        self.assertEqual(rc, 1); self.assertIn("PROBLÉM: počet snímků", out)
        self.assertTrue(os.path.isdir(p)); self.assertEqual(self.cti_sv(), {})
        rc, out = self.spust("--proved", "--ignoruj-pocet")
        self.assertEqual(rc, 0, out); self.assertEqual(self.cti_sv()["ebad_a_1349"]["snimku"], 2)

    def test_matrika_a_rozpor_nazvu(self):
        self.sv({"ebad_8084": {"svazek": "Žleby 27", "archiv": "x", "portal": "eBadatelna"}})
        self.slozka("zleby-27", MATRIKA, ["s-1.jpg", "s-2.jpg"])
        rc, out = self.spust("--proved")
        self.assertEqual(rc, 1); self.assertIn("se liší od svazky.json", out)
        self.assertTrue(os.path.isdir(os.path.join(self.d, "pracovni", "zleby-27")))   # nic se neudělalo

    def test_aron_apu8_a_stare_cesty(self):
        self.slozka("aron-lhota", ARON, ["CZ_215000010_00190_1a2b3c4d_00001_sign-4321.jpg", "CZ_215000010_00190_1a2b3c4d_00002_sign-4321.jpg"])
        self.slozka("aron_1a2b3c4d", None, ["s1.jpg"])   # strojová kopie
        open(os.path.join(self.d, "data", "STAV.md"), "w").write("čti pracovni/aron-lhota/s1.jpg\n")
        rc, out = self.spust("pracovni/aron-lhota")
        self.assertEqual(rc, 0, out)
        self.assertIn("strojová kopie: pracovni/aron_1a2b3c4d", out); self.assertIn("data/STAV.md:1", out)
        rc, out = self.spust("pracovni/aron-lhota", "--proved")
        self.assertEqual(rc, 0, out)
        self.assertTrue(os.path.isdir(os.path.join(self.d, "pracovni", "aron_1a2b3c4d_lhota_4321_manual")), out)
        z = self.cti_sv()["1a2b3c4d"]
        self.assertTrue(z["url"].endswith("/apu/1a2b3c4d-0000-4000-8000-000000000001"))
        self.assertIn("3.1862-11.1921", z["svazek"])
        self.assertTrue(os.path.isdir(os.path.join(self.d, "pracovni", "aron_1a2b3c4d")))   # strojovou kopii nemaže

    def test_neznamy_odkaz_a_bez_obsahu(self):
        self.slozka("neco", "bez odkazu\n", ["a.jpg"])
        rc, out = self.spust(); self.assertEqual(rc, 1); self.assertIn("není odkaz", out)
        self.slozka("prazdna", None, ["a.jpg"])
        rc, out = self.spust("pracovni/prazdna"); self.assertEqual(rc, 1); self.assertIn("chybí obsah.txt", out)


    def test_aron_svazek_bez_obce_neni_problem(self):
        self.sv({"1a2b3c4d": {"archiv": "SOA Hradec Králové", "portal": "ARON", "snimku": 2,
                              "svazek": "Sbírka matrik Východočeského kraje, sign.: 4321 (poř.č. 4301), 3.1862-11.1921",
                              "url": "https://aron.vychodoceskearchivy.cz/apu/1a2b3c4d-0000-4000-8000-000000000001"}})
        self.slozka("aron-lhota", ARON, ["a-1.jpg", "a-2.jpg"])
        rc, out = self.spust("pracovni/aron-lhota")
        self.assertEqual(rc, 0, out); self.assertNotIn("PROBLÉM", out)
        self.assertIn("aron_1a2b3c4d_lhota_4321_manual", out)   # název složky z obsah.txt, ne ze svazky.json
        # jiná signatura ve svazky.json = opravdu jiný svazek
        self.sv({"1a2b3c4d": {"portal": "ARON", "snimku": 2, "svazek": "Sbírka matrik, sign.: 1234"}})
        rc, out = self.spust("pracovni/aron-lhota")
        self.assertEqual(rc, 1); self.assertIn("se liší od svazky.json", out)

    def test_pocet_snimku_ebadatelna_archivalie(self):
        obsah = ARCHIVALIE.format(n=3).replace("Scans\n3", "Snímky\n3")
        self.slozka("jikev-pozemkova-kniha", obsah, ["a-1.jpg", "a-2.jpg"])
        rc, out = self.spust()
        self.assertEqual(rc, 1); self.assertIn("počet snímků: ve složce 2, podle obsah.txt 3", out)

    def test_prikaz_ke_smazani_kopie(self):
        self.slozka("aron-lhota", ARON, ["a-1.jpg", "a-2.jpg"])
        k = self.slozka("aron_1a2b3c4d", None, ["s1.jpg", "s2.jpg", "stahovani.log"])
        rc, out = self.spust("pracovni/aron-lhota")
        self.assertIn("rm -r 'pracovni/aron_1a2b3c4d'", out)
        open(os.path.join(k, "poznamky.txt"), "w").write("x")
        rc, out = self.spust("pracovni/aron-lhota")
        self.assertNotIn("rm -r", out); self.assertIn("jiné soubory", out)
        self.assertTrue(os.path.isdir(k))   # nic nemaže


if __name__ == "__main__":
    unittest.main()
