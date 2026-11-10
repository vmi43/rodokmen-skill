"""Testy elipsa.py: elipsa a popisek v obrázku, vodicí čára z nejbližšího bodu elipsy. Bez internetu.

Z kořene repozitáře:  python3 -I tests/podminky/test_elipsa.py
Původ: tests/test_elipsa.py z vzoha/dejiny-domu-skill (commit e1cd204), cesty upraveny.
"""
import os, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared", "tools")
sys.path.insert(0, TOOLS)
import elipsa  # noqa: E402
from PIL import Image  # noqa: E402


class ElipsaTest(unittest.TestCase):

    def test_nejblizsi_bod(self):
        x, y = elipsa.nejblizsi_bod(100, 100, 50, 20, 0, (300, 100))
        self.assertAlmostEqual(x, 150, delta=0.5)
        self.assertAlmostEqual(y, 100, delta=0.5)
        x, y = elipsa.nejblizsi_bod(100, 100, 50, 20, 90, (100, 300))   # natočená o 90°: dlouhá osa svisle
        self.assertAlmostEqual(y, 150, delta=0.5)

    def test_kresli_elipsu_i_popisek(self):
        im = elipsa.oznac(Image.new("RGBA", (600, 400), (128, 128, 128, 255)), 200, 200, 100, 40, 20, "čp. 183")
        cervene = lambda box: any(p[0] > 200 and p[1] < 40 for p in im.crop(box).getdata())
        self.assertTrue(cervene((290, 150, 320, 250)))    # pravý okraj elipsy
        self.assertFalse(cervene((180, 180, 220, 220)))   # střed elipsy zůstal
        self.assertTrue(cervene((300, 0, 600, 150)))      # popisek vpravo nahoře


if __name__ == "__main__":
    unittest.main()
