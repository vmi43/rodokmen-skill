"""Test geolab.py a slusne.strop_dlazdic: nástroj volá funkci, která musí v slusne.py být, a strop zastaví obří snímek.
Bez internetu.

Z kořene repozitáře:  python3 -I tests/podminky/test_geolab.py
"""
import ast, os, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared", "tools")
sys.path.insert(0, TOOLS)
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


if __name__ == "__main__":
    unittest.main()
