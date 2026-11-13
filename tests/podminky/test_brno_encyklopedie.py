"""Testy brno_encyklopedie.py: karty z JSON hledání, filtr podle čísla domu. Bez internetu.

Z kořene repozitáře:  python3 -I tests/podminky/test_brno_encyklopedie.py
Původ: tests/test_brno_encyklopedie.py z vzoha/dejiny-domu-skill (commit 5c1715b), cesty upraveny.
"""
import contextlib, io, os, sys, tempfile, unittest
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared", "tools")
sys.path.insert(0, TOOLS)
os.environ["SLUSNE_STAV"] = tempfile.mkdtemp(prefix="brno_enc_stav_")   # brzda nesmí sahat na stav skutečných dotazů
import brno_encyklopedie as enc  # noqa: E402

# zkrácené skutečné karty (10. 11. 2026)
DUM = ('<div class="card-body"><a class="card-link" href="./?acc=profil-domu&amp;load=1215" title=""></a>'
       '<p class="card-title"><a class="card-link" href="./?acc=profil-domu&amp;load=1215">Orlovna</a></p>'
       '<p class="card-text">Poděbradova 5/156</p></div>')
DUM2 = DUM.replace("1215", "99").replace("Orlovna", "Nájemní dům").replace("5/156", "51/300")
OSOBA = ('<div class="card-body"><a class="card-link" href="./?acc=profil-osobnosti&amp;load=46430&amp;" '
         'title="Elise Munková"></a><p class="card-title"><a class="card-link" '
         'href="./?acc=profil-osobnosti&amp;load=46430&amp;"><span>Elise</span> <b>Munková</b></a></p>'
         '<p class="card-text">*1879 - &dagger;1945</p></div>')


def odpoved(karty, celkem):
    return {"data": {"result": {"rows_total": celkem, "page_next": 2, "page_total": 1}},
            "html": {"page-result-1": "".join(karty)}}


class BrnoEncyklopedieTest(unittest.TestCase):

    def test_karta_s_odkazem(self):
        with mock.patch.object(enc, "stranka", return_value=odpoved([OSOBA], 1)):
            karty, celkem = enc.hledej("person", "pers_residence", "Poděbradova 5")
        self.assertEqual(celkem, 1)
        self.assertEqual(karty[0], (["Elise Munková", "*1879 - †1945"], enc.WEB + "?acc=profil-osobnosti&load=46430"))

    def test_cislo_domu_filtruje_domy(self):
        vystup = io.StringIO()
        with mock.patch.object(enc, "stranka", return_value=odpoved([DUM, DUM2], 2)), contextlib.redirect_stdout(vystup):
            enc.ulice("Poděbradova", "5")
        self.assertIn("Domy a stavby: 1\n  Orlovna | Poděbradova 5/156 |", vystup.getvalue())
        self.assertNotIn("51/300", vystup.getvalue().split("Objekty")[0])


if __name__ == "__main__":
    unittest.main()
