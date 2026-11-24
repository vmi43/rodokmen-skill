"""Test mista.py: odkazy na panorama ve výpisu `ruian` (Street View a Mapy.com). Bez internetu.

Z kořene repozitáře:  python3 -I tests/podminky/test_mista.py
"""
import contextlib, io, os, sys, unittest
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared", "tools")
sys.path.insert(0, TOOLS)
import mista  # noqa: E402


class PanoramaTest(unittest.TestCase):
    def test_odkazy(self):
        t = mista.odkazy_panorama(49.96, 14.07)
        self.assertIn("viewpoint=49.960000,14.070000", t)
        self.assertIn("mapy.com/cs/zakladni?x=14.070000&y=49.960000", t)

    def test_ruian_vypise_panoramu_a_nic_nestahuje(self):
        adr = [{"attributes": {"adresa": "Husova 66, Beroun", "stavebniobjekt": 1}, "geometry": {"y": 49.96, "x": 14.07}}]
        with mock.patch.object(mista, "adresni_mista", return_value=adr), \
                mock.patch.object(mista, "ruian_q", return_value=[]):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                mista.ruian("Husova 66, Beroun")
        self.assertIn("panorama (prochází uživatel)", out.getvalue())


class TvarAdresyTest(unittest.TestCase):
    A = "Lhota 14, 12399 Lhota u Dubé"

    def test_cela_adresa_z_vypisu_ruian(self):
        self.assertEqual(mista.adresa_a_obec(self.A), ("Lhota 14", "12399 Lhota u Dubé"))
        self.assertEqual(mista.adresa_a_obec("Ulice 12/3, Část, 12345 Obec"), ("Ulice 12/3", "12345 Obec"))
        self.assertEqual(mista.adresa_a_obec("Lhota 14"), ("Lhota 14", ""))

    def test_v_obci_s_psc(self):
        self.assertTrue(mista.v_obci(self.A, "12399 Lhota u Dubé"))
        self.assertTrue(mista.v_obci(self.A, "12399"))
        self.assertTrue(mista.v_obci(self.A, "123 99"))
        self.assertFalse(mista.v_obci(self.A, "12398"))
        self.assertFalse(mista.v_obci(self.A, "12399 Jiná obec"))
        self.assertTrue(mista.v_obci(self.A, "Lhota u Dubé"))   # beze změny
        self.assertFalse(mista.v_obci(self.A, "Dubá nad Lesem"))

    def test_ruian_bez_nalezu_s_obci_vypise_jine_nalezy(self):
        jinde = [{"attributes": {"adresa": self.A}, "geometry": {"y": 1, "x": 2}}]
        with mock.patch.object(mista, "adresni_mista", side_effect=lambda d, p, o="": [] if o else jinde):
            with self.assertRaises(SystemExit) as e:
                mista.ruian("Lhota 14, Dubá nad Lesem")
        self.assertIn("12399 Lhota u Dubé", str(e.exception))


if __name__ == "__main__":
    unittest.main()
