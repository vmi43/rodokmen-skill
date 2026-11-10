"""Testy kramerius.py: autoři z MODS a konec ochrany díla, překlad dotazu pro ČDK. Bez internetu.

Z kořene repozitáře:  python3 -I tests/podminky/test_kramerius.py
Původ: tests/test_kramerius.py z vzoha/dejiny-domu-skill (commit e1cd204), cesty upraveny.
"""
import os, sys, tempfile, time, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared", "tools")
sys.path.insert(0, TOOLS)
os.environ["SLUSNE_STAV"] = tempfile.mkdtemp(prefix="kramerius_stav_")   # brzda nesmí sahat na stav skutečných dotazů
import kramerius  # noqa: E402

# zkrácené MODS plánu Olomouce 1946 z ČDK (VKOL, 10. 11. 2026)
MODS = """<modsCollection xmlns="http://www.loc.gov/mods/v3"><mods>
<name type="personal"><namePart>Dubový, Ladislav</namePart><role><roleTerm type="code">aut</roleTerm></role></name>
<name type="personal"><namePart>Promberger, Romuald</namePart><namePart type="date">1893-1974</namePart></name>
<originInfo><dateIssued>[1946]</dateIssued></originInfo></mods></modsCollection>"""


class AutoriTest(unittest.TestCase):

    def test_autori_z_mods(self):
        autori, vydano = kramerius.autori_z_mods(MODS)
        self.assertEqual(autori, [("Dubový, Ladislav", "", "aut"), ("Promberger, Romuald", "1893-1974", "")])
        self.assertEqual(vydano, "[1946]")

    def test_rok_umrti(self):
        self.assertEqual(kramerius.rok_umrti("1843-1903"), 1903)
        self.assertIsNone(kramerius.rok_umrti("1907-"))
        self.assertIsNone(kramerius.rok_umrti(""))
        self.assertEqual(kramerius.rok_umrti("zemř. 1932"), 1932)

    def test_konec_ochrany(self):
        self.assertEqual(kramerius.konec_ochrany([("Sitte", "1843-1903", "")], "1899")[0], 1974)
        rok, proc = kramerius.konec_ochrany(*kramerius.autori_z_mods(MODS))   # † 1974 = chráněné i bez dat kresliče
        self.assertEqual(rok, 2045)
        self.assertIn("chybí", proc)
        self.assertIsNone(kramerius.konec_ochrany([("A", "", ""), ("B", "1800-1850", "")], None)[0])
        self.assertEqual(kramerius.konec_ochrany([], "1890")[0], 1961)   # anonymní: od zveřejnění

    def test_cdk_dotaz(self):
        self.assertEqual(kramerius.cdk_dotaz('text_ocr:"Panská 11" AND datum_begin:[1900 TO 1940] AND dostupnost:public'),
                         'text_ocr:"Panská 11" AND date_range_start.year:[1900 TO 1940] AND accessibility:public')


if __name__ == "__main__":
    unittest.main()
