"""Test geolab.py a slusne.strop_dlazdic: nástroj volá funkci, která musí v slusne.py být, a strop zastaví obří snímek.
Bez internetu.

Z kořene repozitáře:  python3 -I tests/podminky/test_geolab.py
"""
import ast, http.client, os, sys, unittest
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared", "tools")
sys.path.insert(0, TOOLS)
import geolab  # noqa: E402
import slusne  # noqa: E402


class StropDlazdicTest(unittest.TestCase):
    def test_pod_stropem_projde(self):
        slusne.strop_dlazdic(slusne.MAX_DLAZDIC, "Geolab X")

    def test_nad_stropem_skonci(self):
        with self.assertRaises(SystemExit) as c:
            slusne.strop_dlazdic(slusne.MAX_DLAZDIC + 1, "Geolab X")
        self.assertIn("nic nestahuji", str(c.exception))

    def test_vsechna_volani_slusne_existuji(self):
        """Každé `slusne.<jméno>(` v nástrojích musí v slusne.py existovat (chyba se jinak ukáže až za běhu na portálu)."""
        chybi = {}
        for f in os.listdir(TOOLS):
            if f.endswith(".py") and f != "slusne.py":
                for n in ast.walk(ast.parse(open(os.path.join(TOOLS, f), encoding="utf-8").read())):
                    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "slusne" \
                            and not hasattr(slusne, n.attr):
                        chybi.setdefault(n.attr, []).append(f)
        self.assertEqual(chybi, {})


class StahniTest(unittest.TestCase):
    def test_zopakuje_utrzenou_odpoved_jednou(self):
        chyby = [http.client.IncompleteRead(b"x")]

        class R:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def read(s): return b"ok"

        def urlopen(*a, **k):
            if chyby:
                raise chyby.pop()
            return R()
        with mock.patch.object(geolab.urllib.request, "urlopen", urlopen), mock.patch.object(geolab.time, "sleep"):
            self.assertEqual(geolab.stahni("https://oldmaps.geolab.cz/x"), b"ok")

    def test_podruhe_skonci_lidskou_zpravou(self):
        def urlopen(*a, **k):
            raise http.client.IncompleteRead(b"x")
        with mock.patch.object(geolab.urllib.request, "urlopen", urlopen), mock.patch.object(geolab.time, "sleep"):
            with self.assertRaises(SystemExit) as c:
                geolab.stahni("https://oldmaps.geolab.cz/x")
        self.assertIn("oldmaps.geolab.cz", str(c.exception))

    def test_http_chyba_se_neopakuje_ale_predava(self):
        volani = []

        def urlopen(*a, **k):
            volani.append(1)
            raise geolab.urllib.error.HTTPError("u", 404, "nenalezeno", {}, None)
        with mock.patch.object(geolab.urllib.request, "urlopen", urlopen):
            with self.assertRaises(geolab.urllib.error.HTTPError):
                geolab.stahni("https://oldmaps.geolab.cz/x")
        self.assertEqual(len(volani), 1)


if __name__ == "__main__":
    unittest.main()
