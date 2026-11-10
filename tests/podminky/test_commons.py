"""Testy commons.py (Wikimedia Commons): výběr kategorie obce, průchod stromem, výběr starých souborů, metadata. Bez internetu.

Z kořene repozitáře:  python3 -I tests/podminky/test_commons.py
Původ: tests/test_commons.py z vzoha/dejiny-domu-skill (commit 32bef07), cesty upraveny.
"""
import os, sys, unittest
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared", "tools")
sys.path.insert(0, TOOLS)
import commons  # noqa: E402


def info(datum="", licence="CC0", **dalsi):
    meta = {"DateTimeOriginal": {"value": datum}, "LicenseShortName": {"value": licence}}
    meta.update({k: {"value": v} for k, v in dalsi.items()})
    return {"extmetadata": meta, "url": "https://upload.wikimedia.org/x.jpg?utm_source=commons"}


# zkrácené odpovědi Wikidat (9. 11. 2026)
HLEDANI = {"search": [{"id": "Q1684004", "label": "Slavče"}, {"id": "Q8556396", "label": "Slavče"},
                      {"id": "Q999", "label": "Slavčice"}]}


def polozka(kat, lat, lon, popis):
    claims = {"P625": [{"mainsnak": {"datavalue": {"value": {"latitude": lat, "longitude": lon}}}}]}
    if kat:
        claims["P373"] = [{"mainsnak": {"datavalue": {"value": kat}}}]
    return {"claims": claims, "descriptions": {"cs": {"value": popis}}}


POLOZKY = {"entities": {"Q1684004": polozka(None, 48.7979, 14.6150, "obec"),
                        "Q8556396": polozka("Slavče (Vrábče)", 48.9272, 14.3442, "část obce Vrábče")}}


def wikidata(adresa, **p):
    return HLEDANI if p["action"] == "wbsearchentities" else POLOZKY


class KategorieObceTest(unittest.TestCase):

    def test_jedna_obec_v_ruian_vybere_blizkou(self):
        with mock.patch.object(commons, "api", side_effect=wikidata):
            self.assertEqual(commons.kategorie_obce("Slavče", [("Slavče, 37001 Vrábče", 48.927, 14.344)]),
                             ("Slavče (Vrábče)", "Q8556396 část obce Vrábče"))

    def test_daleka_polozka_se_nevezme(self):
        with mock.patch.object(commons, "api", side_effect=wikidata), self.assertRaises(SystemExit) as e:
            commons.kategorie_obce("Slavče", [("Slavče, 37401 Slavče", 48.798, 14.612)])   # kategorii má jen Vrábče, 30 km
        self.assertIn("--kategorie", str(e.exception))

    def test_stejnojmenne_obce_vypise(self):
        with mock.patch.object(commons, "api", side_effect=wikidata), self.assertRaises(SystemExit) as e:
            commons.kategorie_obce("Slavče", [("a", 48.798, 14.612), ("b", 48.927, 14.344)])
        self.assertIn("Slavče (Vrábče)", str(e.exception))


class ProchazeniTest(unittest.TestCase):
    STROM = {
        "Category:Rumburk": (["Category:Bus stops in Rumburk", "Category:Muzeum Rumburk", "Category:History of Rumburk"],
                             [("File:Nove.jpg", info("2015"))]),
        "Category:History of Rumburk": (["Category:Postcards of Rumburk"], [("File:Eckarth 1773.jpg", info("1773"))]),
        "Category:Postcards of Rumburk": ([], [("File:Markt.jpg", info("")), ("File:Zvon.wav", info("1940"))]),
        "Category:Muzeum Rumburk": (["Category:Výstava 2009"], [("File:Frind.jpg", info("1950", "CC BY-SA 4.0"))]),
        "Category:Výstava 2009": ([], [("File:Plakat.jpg", info(""))]),
    }

    def clenove(self, kategorie):
        podkategorie, soubory = self.STROM[kategorie]
        return podkategorie, [s for s in soubory if commons.OBRAZEK.search(s[0])]

    def test_historicke_napred_a_vynecha_zastavky(self):
        with mock.patch.object(commons, "clenove", side_effect=self.clenove) as c:
            nalez, prosel, zbylo = commons.projdi(["Category:Rumburk"])
        self.assertEqual([x.args[0] for x in c.call_args_list][:3],
                         ["Category:Rumburk", "Category:History of Rumburk", "Category:Postcards of Rumburk"])
        self.assertNotIn("Category:Bus stops in Rumburk", [x.args[0] for x in c.call_args_list])
        self.assertEqual((prosel, zbylo), (5, False))

    def test_limit_kategorii(self):
        with mock.patch.object(commons, "clenove", side_effect=self.clenove):
            _, prosel, zbylo = commons.projdi(["Category:Rumburk"], nejvic=2)
        self.assertEqual((prosel, zbylo), (2, True))

    def test_vyber_starych(self):
        with mock.patch.object(commons, "clenove", side_effect=self.clenove):
            nalez, _, _ = commons.projdi(["Category:Rumburk"])
        vybrane = [(r, s) for r, s, _, _ in commons.vyber(nalez)]
        # nedatovaný plakát z podkategorie muzea ne, nedatovaná pohlednice ano, zvuk vůbec
        self.assertEqual(vybrane, [(1773, "File:Eckarth 1773.jpg"), (1950, "File:Frind.jpg"), (None, "File:Markt.jpg")])
        self.assertEqual([s for _, s, _, _ in commons.vyber(nalez, (1800, 1960))], ["File:Frind.jpg", "File:Markt.jpg"])


class MetadataTest(unittest.TestCase):

    def test_meta_cisti_sablony(self):
        i = info("before 1882 date QS:P,+1882-00-00T00:00:00Z/7", Artist="<span>Unknown author</span> Unknown author")
        self.assertEqual(commons.meta(i, "DateTimeOriginal"), "before 1882")
        self.assertEqual(commons.meta(i, "Artist"), "Unknown author")
        self.assertEqual(commons.rok(i), 1882)

    def test_smi_obrazek(self):
        self.assertTrue(commons.smi_obrazek("Public domain").startswith("ano, volné dílo"))
        self.assertTrue(commons.smi_obrazek("CC0").startswith("ano, volné dílo"))
        self.assertEqual(commons.smi_obrazek("CC BY-SA 4.0"), "ano, s autorem a licencí (CC BY-SA 4.0)")

    def test_odkaz_a_detail(self):
        self.assertEqual(commons.odkaz("File:Telč Castle (1835).jpg"),
                         "https://commons.wikimedia.org/wiki/File:Tel%C4%8D_Castle_(1835).jpg")
        odpoved = {"query": {"pages": [{"title": "File:A.jpg", "imageinfo": [info("1905", Artist="Brück & Sohn")]}]}}
        with mock.patch.object(commons, "api", return_value=odpoved):
            radky = commons.detail("A.jpg")
        self.assertIn("Obrázek: https://upload.wikimedia.org/x.jpg", radky)
        self.assertIn("Citace: Brück & Sohn, A.jpg, 1905, CC0, Wikimedia Commons, https://commons.wikimedia.org/wiki/File:A.jpg", radky)

    def test_detail_neni(self):
        with mock.patch.object(commons, "api", return_value={"query": {"pages": [{"missing": True}]}}), \
                self.assertRaises(SystemExit):
            commons.detail("Neni.jpg")


class AdresaTest(unittest.TestCase):

    def test_adresa_z(self):
        self.assertEqual(commons.adresa_z("Panská 11"), ("Panská", "11"))
        self.assertEqual(commons.adresa_z("Žerotínovo nám."), ("Žerotínovo náměstí", None))
        self.assertEqual(commons.adresa_z("Panská 183/11"), ("Panská", "183"))

    def test_kategorie_adres(self):
        def odpoved(adresa, **p):   # Olomouc 10. 11. 2026: ulice ano, dům ne
            if p.get("list") == "search":
                return {"query": {"search": [{"title": "Category:Školní ulice (Olomouc)"}, {"title": "Category:Jiná"}]}}
            return {"query": {"pages": [{"title": "Category:Panská 11 (Olomouc)", "missing": True},
                                        {"title": "Category:Panská (Olomouc)"},
                                        {"title": "Category:Školní (Olomouc)", "missing": True}]}}
        with mock.patch.object(commons, "api", side_effect=odpoved):
            self.assertEqual(commons.kategorie_adres("Olomouc", [("Panská", "11"), ("Školní", None)]),
                             [("Category:Panská (Olomouc)", "ulice"), ("Category:Školní ulice (Olomouc)", "ulice?")])

    def test_soubory_domu(self):
        nalez = {"File:Olomouc, Panská 11.JPG": ("Category:Panská (Olomouc)", info("2014")),
                 "File:Olomouc, Panská 110.jpg": ("Category:Panská (Olomouc)", info("2014")),
                 "File:Měšťanský dům (Olomouc), č.p.183.JPG": ("Category:Panská (Olomouc)", info("")),
                 "File:Olomouc, Panská 2.jpg": ("Category:Panská (Olomouc)", info("1900"))}
        self.assertEqual([x[1] for x in commons.soubory_domu(nalez, [("Panská", "11")], "183")],
                         ["File:Olomouc, Panská 11.JPG", "File:Měšťanský dům (Olomouc), č.p.183.JPG"])


if __name__ == "__main__":
    unittest.main()
