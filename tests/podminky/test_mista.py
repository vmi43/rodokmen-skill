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


if __name__ == "__main__":
    unittest.main()
