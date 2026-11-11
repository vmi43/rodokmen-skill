"""Testy pomucka.py: rozbor Archivní pomůcky NAD 190 (text + odkazy) a hledání knih. Bez sítě, bez PDF.

Z kořene repozitáře:  python3 -I tests/podminky/test_pomucka.py
"""
import contextlib, io, os, sys, unittest

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared")
sys.path.insert(0, os.path.join(SKILL, "tools"))
import pomucka  # noqa: E402

TXT = """Úrov. Označení                                       Poř. č.                                 Ukládací číslo
      Obsah                                                                                        Datace

      215000010/190                                    1
      Sbírka matrik Východočeského kraje pom
  1                                                    2
      Římskokatolická církev
  2                                                    3
      fary B
  3                                                    4
      Babice
  4                                                    5                                                1
      původní signatura: I.
      signatura: 1-1
      neplatné inventární číslo: 1
      římskokatolická matrika NAROZENÝCH, ZEMŘELÝCH,                                         1787–1803
      ODDANÝCH, Babice + Malé Babice
      úřední kniha: 1; EJ
      odkazy: Prohlížet v ARchivu ONline
                Stáhnout všechny snímky
      čeština; 21x35 cm, 26 fol.; vazba: nová polokožená
      matriční místo: Babice (Hradec Králové, Česko); Malé Babice (Babice, Hradec Králové, Česko : nižší
      sídelní jednotka)
      tematický popis jednotky popisu: N 2.1787-11.1803, O 6.1787-6.1803, Z od 4.1787

  4                                                    6                                                2
      původní signatura: II.
      signatura: 1-5
      římskokatolická matrika ZEMŘELÝCH 1804–1830                                             1804–1830
      úřední kniha: 2; EJ
      čeština; 21x35 cm, 40 fol.
      matriční místo: Barchov (Hradec Králové, Česko)
"""
URIS = ["https://aron.vychodoceskearchivy.cz/apu/80c78b00-ab7d-4604-9b28-8e9c05d6146f",
        "https://storage.vychodoceskearchivy.cz/matriky/O/CZ_215000010_00190_OA4B2IPL_sign-1-1.zip"]


class Pomucka(unittest.TestCase):
    def test_rozbor_a_parovani(self):
        knihy, spar, pary = pomucka.rozeber(TXT, URIS)
        self.assertEqual((len(knihy), spar, pary), (2, 1, 1))
        k = knihy[0]
        self.assertEqual(k["aron"], URIS[0])
        self.assertEqual(k["zip"], URIS[1])
        self.assertEqual(k["sign"], "1-1")
        self.assertEqual(k["fol"], 26)
        self.assertEqual(k["datace"], "1787–1803")
        self.assertIn("Malé Babice", k["misto"])
        self.assertEqual(k["cesta"][1:], ["fary B", "Babice"])
        self.assertNotIn("aron", knihy[1])     # kniha bez odkazu se nespáruje s cizím odkazem

    def test_hledani(self):
        knihy, _, _ = pomucka.rozeber(TXT, URIS)
        self.assertEqual(len(pomucka.hledej(knihy, "babice")), 1)         # bez diakritiky a velikosti písmen
        self.assertEqual(len(pomucka.hledej(knihy, "Barchov")), 0)         # bez odkazu jen s --vse
        self.assertEqual(len(pomucka.hledej(knihy, "Barchov", vse=True)), 1)
        self.assertEqual(len(pomucka.hledej(knihy, "Babice", rok=1790)), 1)
        self.assertEqual(len(pomucka.hledej(knihy, "Babice", rok=1850)), 0)
        self.assertEqual(len(pomucka.hledej(knihy, "Babice", typ="Z")), 1)  # kniha zahrnuje i zemřelé

    def test_spatne_poradi_odkazu_zastavi(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                pomucka.dvojice_odkazu([URIS[1], URIS[0]])
            with self.assertRaises(SystemExit):
                pomucka.dvojice_odkazu(URIS[:1])

    def test_vic_knih_s_odkazy_nez_odkazu_zastavi(self):
        txt = TXT.replace("úřední kniha: 2; EJ", "odkazy: Prohlížet v ARchivu ONline")
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                pomucka.rozeber(txt, URIS)


if __name__ == "__main__":
    unittest.main()
