"""Testy sdileni.py (jen čtení z Mapy matrik a indexu matrik) bez sítě: knihy z adres, odhad snímku, výpis najdi a kniha.
Z kořene repozitáře:  python3 -I tests/podminky/test_sdileni.py
Původ: tests/test_sdileni.py z vzoha/dejiny-domu-skill (commit 5c1715b), zúženo na čtení; navíc kontrola, že nástroj nic neodesílá."""
import contextlib, io, os, sys, tempfile, unittest

os.environ["SLUSNE_STAV"] = tempfile.mkdtemp(prefix="sdileni_stav_")   # brzda nesmí sahat na stav skutečných dotazů
TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared", "tools")
sys.path.insert(0, TOOLS)
import sdileni  # noqa: E402

PF = "https://www.portafontium.eu/register/soap-pn/kozlany-22"
OBEC = [{"signature": "Kožlany 22", "archive": "soa-plzen", "portal_id": "kozlany-22", "records": {"Z": "1900–1930"},
         "order": "chronological", "points": 2, "path": "svazky/soa-plzen/kozlany-22.json"}]
SVAZEK = {"signature": "Kožlany 22", "order": "chronological", "url": PF, "notes": ["od sn. 60 jiné stránkování"],
          "points": [{"scan": 10, "year": 1900}, {"scan": 30, "year": 1910}]}
KNIHY = [{"id": "portafontium/kozlany-22", "precteno": 5}]


def falesna_sit(url, *a, **k):
    if url.endswith("/obce/kozlany.json"):
        return OBEC
    if url.endswith("/svazky/soa-plzen/kozlany-22.json"):
        return SVAZEK
    if url.endswith("/data/knihy.json"):
        return KNIHY
    return None


class SdileniTest(unittest.TestCase):

    def test_kniha_z_url(self):
        self.assertEqual(sdileni.kniha_z_url(PF), ("soa-plzen", "portafontium", "kozlany-22"))
        self.assertEqual(sdileni.kniha_z_url("https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/4888"),
                         ("soa-praha", "soapraha", "4888"))
        self.assertEqual(sdileni.kniha_z_url("https://ebadatelna.soapraha.cz/d/11973/15")[2], "11973")
        self.assertEqual(sdileni.kniha_z_url("https://katalog.ahmp.cz/pragapublica/permalink?xid=144286C6CCB648968F0C7879316827D0"),
                         (None, "ahmp", "144286c6"))
        self.assertIsNone(sdileni.kniha_z_url("https://aron.vychodoceskearchivy.cz/apu/abc"))

    def test_odhad(self):
        body = [{"scan": 10, "year": 1800}, {"scan": 30, "year": 1810}, {"scan": 40, "year": 1812, "year_to": 1813}]
        self.assertEqual(sdileni.odhad(body, 1805), (20, "odhad mezi sn. 10 (1800) a 30 (1810)"))
        self.assertEqual(sdileni.odhad(body, 1813)[0], 40)
        self.assertIsNone(sdileni.odhad(body, 1700))
        self.assertEqual(sdileni.slug("Nová Ves u Plzně"), "nova-ves-u-plzne")

    def test_najdi_vypise_odhad_a_poznamky(self):
        puvodni = sdileni.json_z
        sdileni.json_z = falesna_sit
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(sdileni.najdi("Kožlany", 1905, "Z"), 0)
        finally:
            sdileni.json_z = puvodni
        text = out.getvalue()
        self.assertIn("Kožlany 22", text)
        self.assertIn("začni na sn. 20", text)
        self.assertIn("od sn. 60 jiné stránkování", text)

    def test_najdi_neznama_obec_nepada(self):
        puvodni = sdileni.json_z
        sdileni.json_z = lambda url, *a, **k: None
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(sdileni.najdi("Nikde"), 0)
        finally:
            sdileni.json_z = puvodni
        self.assertIn("nezná", out.getvalue())

    def test_prerusene_cteni_nepada(self):
        import http.client
        stara_cache, stary_open = sdileni.CACHE, sdileni.urllib.request.urlopen
        sdileni.CACHE = tempfile.mkdtemp(prefix="sdileni_cache_")

        def pad(*a, **k):
            raise http.client.IncompleteRead(b"x")
        sdileni.urllib.request.urlopen = pad
        try:
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertIsNone(sdileni.stahni("https://pe-pan.github.io/matriky-index/data/knihy.json"))
        finally:
            sdileni.CACHE, sdileni.urllib.request.urlopen = stara_cache, stary_open
        self.assertIn("neodpovídá", err.getvalue())

    def test_nic_se_neodesila(self):
        for jmeno in ("odeslat", "bod", "souhlas", "navrh", "gh", "odeslat_schrankou"):
            self.assertFalse(hasattr(sdileni, jmeno), jmeno)
        self.assertEqual(sdileni.main(["odeslat"]), 2)
        with open(os.path.join(TOOLS, "sdileni.py"), encoding="utf-8") as f:
            self.assertNotIn("subprocess", f.read())


if __name__ == "__main__":
    unittest.main()
