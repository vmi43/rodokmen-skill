"""Testy podmínek portálů (podminky.py, podminky.json) a jejich napojení na slusne.py. Bez internetu.

Z kořene repozitáře:  python3 -I tests/podminky/test_podminky.py
(Windows: python -I -X utf8 …)
Původ: upravený tests/test_podminky.py z vzoha/dejiny-domu-skill (commit bda6028).
"""
import json, os, shutil, sys, tempfile, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared", "tools")
sys.path.insert(0, TOOLS)
_tmp_stav = tempfile.mkdtemp(prefix="podminky_stav_")
os.environ["SLUSNE_STAV"] = _tmp_stav   # brzda nesmí sahat na stav skutečných dotazů uživatele
import podminky, slusne  # noqa: E402


class PodminkyTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "data"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def data(self, name, obsah):
        with open(os.path.join(self.tmp, "data", name), "w", encoding="utf-8") as f:
            json.dump(obsah, f, ensure_ascii=False)

    def test_json_je_platny(self):
        p = podminky.portaly()
        self.assertIn("digi.ceskearchivy.cz", p)
        for host, x in p.items():
            self.assertIn(x["vyrez"], ("ano", "neresi", "nekomercne", "souhlas", "ne"), host)
            self.assertIsInstance(x["dotazy"], bool, host)
            self.assertIsInstance(x["obrazky"], bool, host)

    def test_zakazany_portal_zastavi_slusne(self):
        with self.assertRaises(podminky.Zakazano) as e:
            podminky.zkontroluj_stahovani("digi.ceskearchivy.cz", "dotaz")
        self.assertIn("PODMÍNKY", str(e.exception))

    def test_slusne_pusti_povoleny_a_zastavi_zakazany_obrazek(self):
        # MZA: stránky ano, snímky ne (cesta hledání prochází i ZAKAZ ve slusne.py)
        slusne.pockej("https://www.mza.cz/actapublica/matrika/hledani?typ=obec")
        with self.assertRaises(podminky.Zakazano):
            slusne.pockej("https://www.mza.cz/actapublica/matrika/hledani/x.jpg")

    def test_porta_fontium_je_povolena_jak_rozhodnuto(self):   # docs/decisions.md: náš postup, ne upstreamový zákaz
        p = podminky.pravidlo("https://www.portafontium.eu/iiif/x/full/full/0/default.jpg")
        self.assertTrue(p["dotazy"] and p["obrazky"])
        self.assertEqual(p["vyrez"], "souhlas")
        slusne.pockej("https://www.portafontium.eu/iiif/x/full/full/0/default.jpg")   # neskončí výjimkou

    def test_neznamy_portal_projde(self):
        slusne.pockej("https://example.org/neco")

    def test_vyjimka_podle_textu(self):
        self.assertEqual(podminky.pravidlo("https://ags.cuzk.gov.cz/archiv/")["vyrez"], "ano")
        self.assertEqual(podminky.pravidlo("https://ags.cuzk.gov.cz/archiv/", "Indikační skica")["vyrez"], "souhlas")

    def test_posouzeni_obrazku(self):
        self.data("svazky.json", {})
        self.data("zaznamy.json", [
            {"klic": "a", "svazek": "s", "odkaz": "https://www.mza.cz/actapublica/matrika/detail/1"},
            {"klic": "b", "svazek": "s", "odkaz": "https://www.mza.cz/actapublica/matrika/detail/1", "souhlas": "MZA, 1. 1. 2027"},
            {"klic": "c", "svazek": "s", "odkaz": "https://aron.vychodoceskearchivy.cz/apu/1"}])
        self.data("dokumenty.json", [{"img": "foto"}])
        self.assertEqual(podminky.posoud_obrazek(self.tmp, "a")[0], "souhlas")
        self.assertEqual(podminky.posoud_obrazek(self.tmp, "b")[0], "ok")
        self.assertEqual(podminky.posoud_obrazek(self.tmp, "c")[0], "ok")
        self.assertEqual(podminky.posoud_obrazek(self.tmp, "foto")[0], "ok")   # vlastní fotka bez odkazu
        self.assertEqual(podminky.posoud_obrazek(self.tmp, "nic")[0], "pozor")

    def test_hlaska_obrazku_pro_vyrez_a_kontrolu(self):
        self.data("svazky.json", {})
        self.data("zaznamy.json", [
            {"klic": "a", "svazek": "s", "odkaz": "https://www.mza.cz/actapublica/matrika/detail/1"},
            {"klic": "b", "svazek": "s", "odkaz": "https://aron.vychodoceskearchivy.cz/apu/1"},
            {"klic": "bez", "svazek": "s"}])
        self.assertIn("souhlas", podminky.hlaska_obrazku(self.tmp, "a"))   # bez souhlasu archivu
        self.assertIsNone(podminky.hlaska_obrazku(self.tmp, "b"))           # smí
        self.assertIsNone(podminky.hlaska_obrazku(self.tmp, "nic"))         # zdroj v datech ještě není: mlčí
        self.assertIsNone(podminky.hlaska_obrazku(self.tmp, "bez"))         # chybějící odkaz hlásí kontrola jinde


if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        shutil.rmtree(_tmp_stav, ignore_errors=True)
