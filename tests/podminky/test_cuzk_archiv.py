"""Test detekce prázdného (bílého) obrázku v cuzk_archiv.py. Bez internetu.

Z kořene repozitáře:  python3 -I tests/podminky/test_cuzk_archiv.py
Původ: nový test, nápad z vzoha/dejiny-domu-skill (commit e1cd204).
"""
import builtins, io, os, shutil, sys, tempfile, unittest

SHARED = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared")
# nástroj odmítne běžet mimo složku projektu (data/STAV.md), proto ho zkopírujeme do dočasného projektu
PROJEKT = tempfile.mkdtemp(prefix="cuzk_projekt_")
shutil.copytree(os.path.join(SHARED, "tools"), os.path.join(PROJEKT, "tools"))
os.makedirs(os.path.join(PROJEKT, "data"))
open(os.path.join(PROJEKT, "data", "STAV.md"), "w").close()
sys.path.insert(0, os.path.join(PROJEKT, "tools"))
os.environ["SLUSNE_STAV"] = tempfile.mkdtemp(prefix="cuzk_stav_")   # brzda nesmí sahat na stav skutečných dotazů
import cuzk_archiv  # noqa: E402

try:
    from PIL import Image
except ImportError:
    Image = None


def jpeg(barva, kresba=False):
    img = Image.new("RGB", (400, 400), barva)
    if kresba:
        for x in range(0, 400, 4):
            for y in range(150, 250):
                img.putpixel((x, y), (20, 20, 20))
    buf = io.BytesIO()
    img.save(buf, "JPEG")
    return buf.getvalue()


@unittest.skipIf(Image is None, "bez Pillow nejde obrázek vyrobit")
class PrazdnyTest(unittest.TestCase):

    def test_bily_obrazek_je_prazdny(self):
        self.assertTrue(cuzk_archiv.prazdny(jpeg((255, 255, 255))))

    def test_mapa_s_kresbou_neni_prazdna(self):
        self.assertFalse(cuzk_archiv.prazdny(jpeg((255, 255, 255), kresba=True)))

    def test_tmavy_obrazek_neni_prazdny(self):
        self.assertFalse(cuzk_archiv.prazdny(jpeg((90, 120, 60))))

    def test_nejde_o_obrazek(self):
        self.assertFalse(cuzk_archiv.prazdny(b"<html>chyba serveru</html>"))

    def test_bez_pillow_vrati_false(self):
        bily = jpeg((255, 255, 255))   # před zákazem: save() si Pillow samo dohrává PIL._util
        puvodni = builtins.__import__

        def bez_pil(jmeno, *a, **k):
            if jmeno == "PIL" or jmeno.startswith("PIL."):
                raise ImportError(jmeno)
            return puvodni(jmeno, *a, **k)
        builtins.__import__ = bez_pil
        try:
            self.assertFalse(cuzk_archiv.prazdny(bily))
        finally:
            builtins.__import__ = puvodni


class ReliefTest(unittest.TestCase):
    def test_relief_pta_dmr5g_a_uklada_obrazek(self):
        from unittest import mock
        videno = {}

        def falesne_get(url, par, **k):
            videno["url"], videno["par"] = url, par
            return b"\xff\xd8\xff\xe0jpeg"

        ulozeno = {}
        with mock.patch.object(cuzk_archiv.mista, "stred", return_value=(49.96, 14.07)), \
                mock.patch.object(cuzk_archiv.mista, "sjtsk", return_value=(-1000.0, -1100000.0)), \
                mock.patch.object(cuzk_archiv, "get", falesne_get), \
                mock.patch.object(cuzk_archiv, "save_jpeg", lambda img, out: ulozeno.update(out=out)), \
                mock.patch.object(cuzk_archiv, "magick", lambda: None), \
                mock.patch.object(cuzk_archiv, "adresy", lambda *a, **k: None), \
                mock.patch.object(cuzk_archiv, "vyrez_sjtsk", lambda b: [0, 0, 1, 1]):
            cuzk_archiv.mapa("relief", "49.96,14.07", "relief.jpg", 150, 800)
        self.assertEqual(videno["url"], cuzk_archiv.DMR5G)
        self.assertIn("GrayscaleHillshade", videno["par"]["renderingRule"])
        self.assertEqual(ulozeno["out"], "relief.jpg")
        self.assertEqual(videno["par"]["size"], "800,800")


if __name__ == "__main__":
    unittest.main()
