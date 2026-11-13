"""Testy heimatbuch.py (katalog DNB): dotaz, čtení odpovědi SRU, výpis. Bez internetu.

Z kořene repozitáře:  python3 -I tests/podminky/test_heimatbuch.py
Původ: tests/test_heimatbuch.py z vzoha/dejiny-domu-skill (commit 5c1715b), cesty upraveny.
"""
import os, sys, tempfile, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared", "tools")
sys.path.insert(0, TOOLS)
os.environ["SLUSNE_STAV"] = tempfile.mkdtemp(prefix="heimatbuch_stav_")   # brzda nesmí sahat na stav skutečných dotazů
import heimatbuch  # noqa: E402

# zkrácená skutečná odpověď SRU (10. 11. 2026)
ODPOVED = b"""<?xml version="1.0" encoding="UTF-8"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/"><version>1.1</version><numberOfRecords>1</numberOfRecords>
<records><record><recordData><dc xmlns="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>B\xc3\xbcrger- und Hauseigent\xc3\xbcmerverzeichnisse der Stadt Prachatitz / Karl Pechtl</dc:title>
  <dc:creator>Pechtl, Karl [Verfasser]</dc:creator>
  <dc:publisher>Ingolstadt : B\xc3\xb6hmerwaldheimatkreis Prachatitz</dc:publisher>
  <dc:date>1987</dc:date>
  <dc:identifier xsi:type="tel:ISBN">Hgewebe.</dc:identifier>
  <dc:identifier xsi:type="dnb:IDN">1008712477</dc:identifier>
</dc></recordData></record></records></searchRetrieveResponse>"""


class HeimatbuchTest(unittest.TestCase):

    def test_dotaz(self):
        self.assertEqual(heimatbuch.dotaz(["Rumburg", "Rumburk"]), 'tit="Rumburg" or tit="Rumburk"')
        q = heimatbuch.dotaz(["Rumburg"], jen_mistopis=True)
        self.assertTrue(q.startswith('(tit="Rumburg") and (tit=Heimat* or tit=Chronik or '), q)

    def test_knihy_z_odpovedi(self):
        knihy, celkem = heimatbuch.knihy_z_odpovedi(ODPOVED)
        self.assertEqual(celkem, 1)
        self.assertEqual(knihy[0]["idn"], "1008712477")
        self.assertEqual(knihy[0]["rok"], "1987")

    def test_radek_oznaci_seznam_domu(self):
        knihy, _ = heimatbuch.knihy_z_odpovedi(ODPOVED)
        self.assertEqual(heimatbuch.radek(knihy[0]),
                         "⌂ 1987 | Bürger- und Hauseigentümerverzeichnisse der Stadt Prachatitz / Karl Pechtl | "
                         "Pechtl, Karl | Ingolstadt : Böhmerwaldheimatkreis Prachatitz | https://d-nb.info/1008712477")
        self.assertTrue(heimatbuch.radek({"nazev": "Kaplitz", "autor": "", "vydavatel": "", "rok": "", "idn": ""})
                        .startswith("     ? | Kaplitz"))


if __name__ == "__main__":
    unittest.main()
