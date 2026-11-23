"""Test detekce prázdného (bílého) obrázku v cuzk_archiv.py. Bez internetu.

Z kořene repozitáře:  python3 -I tests/podminky/test_cuzk_archiv.py
Původ: nový test, nápad z vzoha/dejiny-domu-skill (commit e1cd204).
"""
import builtins, http.client, io, os, shutil, sys, tempfile, unittest

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


class OdolnostTest(unittest.TestCase):
    """Přerušený přenos, odmítnutá velikost a chybějící písmo pro popisky (poznámky z projektu 2026-11-23)."""

    def test_get_zopakuje_utrzenou_odpoved(self):
        from unittest import mock
        odpovedi = [http.client.IncompleteRead(b"x"), http.client.IncompleteRead(b"x")]

        class R:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def read(s): return b'{"ok": 1}'

        def urlopen(*a, **k):
            if odpovedi:
                raise odpovedi.pop()
            return R()
        with mock.patch.object(cuzk_archiv.urllib.request, "urlopen", urlopen), mock.patch.object(cuzk_archiv.time, "sleep"):
            self.assertEqual(cuzk_archiv.get("https://ags.cuzk.gov.cz/x"), {"ok": 1})

    def test_get_po_tretim_pokusu_skonci_lidskou_zpravou(self):
        from unittest import mock

        def urlopen(*a, **k):
            raise http.client.IncompleteRead(b"x")
        with mock.patch.object(cuzk_archiv.urllib.request, "urlopen", urlopen), mock.patch.object(cuzk_archiv.time, "sleep"):
            with self.assertRaises(SystemExit) as c:
                cuzk_archiv.get("https://ags.cuzk.gov.cz/x")
        self.assertIn("IncompleteRead", str(c.exception))
        self.assertIn("ags.cuzk.gov.cz", str(c.exception))

    def test_export_pri_limitu_velikosti_snizi_sirku(self):
        from unittest import mock
        sirky = []

        def falesny_archiv(cesta, par, binary=False):
            if not binary:
                return {"features": [{"geometry": {"rings": [[[0, 0], [10, 0], [10, 10], [0, 10]]]}}]}
            sirky.append(par["size"].split(",")[0])
            return b'{"error": "image exceeds the size limit"}' if len(sirky) == 1 else b"\xff\xd8\xff\xe0jpeg"
        ulozeno = {}
        with mock.patch.object(cuzk_archiv, "archiv", falesny_archiv), \
                mock.patch.object(cuzk_archiv, "save_jpeg", lambda img, out: ulozeno.update(img=img)):
            cuzk_archiv.export("skici", "1", "x.jpg", "0,0.2,0.2,0.55", 3000)
        self.assertEqual(sirky, ["3000", "2100"])
        self.assertTrue(ulozeno["img"].startswith(b"\xff\xd8"))

    def test_prehled_bez_pisma_nepouzije_label(self):
        from unittest import mock
        prikazy = []
        feats = [{"attributes": {"OBJECTID": 7, "Name": "S0X_1"}}]
        with mock.patch.object(cuzk_archiv.mapa_knihy, "PISMO", None), \
                mock.patch.object(cuzk_archiv, "najdi_rastry", lambda *a: feats), \
                mock.patch.object(cuzk_archiv, "export", lambda *a: None), \
                mock.patch.object(cuzk_archiv.shutil, "which", lambda n: "/usr/bin/magick"), \
                mock.patch.object(cuzk_archiv.subprocess, "run",
                                  lambda cmd, **k: prikazy.append(cmd) or mock.Mock(returncode=0)):
            cuzk_archiv.prehled("skici", "S0X", "p.jpg", 600)
        self.assertNotIn("-label", prikazy[0])
        self.assertNotIn("-font", prikazy[0])

    def test_prehled_s_pismem_ho_preda_montage(self):
        from unittest import mock
        prikazy = []
        feats = [{"attributes": {"OBJECTID": 7, "Name": "S0X_1"}}]
        with mock.patch.object(cuzk_archiv.mapa_knihy, "PISMO", "/p/Arial.ttf"), \
                mock.patch.object(cuzk_archiv, "najdi_rastry", lambda *a: feats), \
                mock.patch.object(cuzk_archiv, "export", lambda *a: None), \
                mock.patch.object(cuzk_archiv.shutil, "which", lambda n: "/usr/bin/magick"), \
                mock.patch.object(cuzk_archiv.subprocess, "run",
                                  lambda cmd, **k: prikazy.append(cmd) or mock.Mock(returncode=0)):
            cuzk_archiv.prehled("skici", "S0X", "p.jpg", 600)
        self.assertIn("-label", prikazy[0])
        self.assertEqual(prikazy[0][prikazy[0].index("-font") + 1], "/p/Arial.ttf")


if __name__ == "__main__":
    unittest.main()
