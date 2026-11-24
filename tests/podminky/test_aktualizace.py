"""Test novy_projekt.py: upozornění na ke_stazeni.md v kořeni projektu. Bez sítě.

Z kořene repozitáře:  python3 -I tests/podminky/test_aktualizace.py
"""
import os, shutil, subprocess, sys, tempfile, unittest

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared")


class Aktualizace(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def spust(self):
        r = subprocess.run([sys.executable, "-I", os.path.join(SKILL, "tools", "novy_projekt.py"), self.d, "--bez-webu"],
                           capture_output=True, text=True, encoding="utf-8")
        return r.returncode, r.stdout + r.stderr

    def test_ke_stazeni_v_koreni_se_ohlasi(self):
        with open(os.path.join(self.d, "ke_stazeni.md"), "w", encoding="utf-8") as f:
            f.write("# vlastní seznam\n")
        rc, out = self.spust()
        self.assertEqual(rc, 0, out); self.assertIn("ke_stazeni.md v kořeni i v data/", out)

    def test_bez_ke_stazeni_v_koreni_ticho(self):
        rc, out = self.spust()
        self.assertEqual(rc, 0, out); self.assertNotIn("ke_stazeni.md v kořeni", out)


if __name__ == "__main__":
    unittest.main()
