#!/usr/bin/env python3
"""Podmínky portálů: co smí nástroj stáhnout a který obrázek smí do výstupu (tools/podminky.json).

Lidská verze s vysvětlením: reference/podminky.md. Jen veřejné zdroje, není to právní rada.

Původ: převzato z vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/podminky.py), commit bda6028; úprava: tabulka jen pro
portály našich nástrojů, nástroje ji volají přes slusne.py, vyrez.py, kontrola.py a export_web.py. Z 5c1715b: čtení JSON s utf-8-sig (BOM).

Použití (z kořene projektu):
  podminky.py <adresa | doména>   -> pravidla pro portál (stahování stránek, snímků, obrázky ve výstupu)
  podminky.py obrazky             -> výřezy ve vyrezy/, které podle podmínek potřebují souhlas archivu
Nástroje to volají samy: slusne.py před každým požadavkem.
"""
import json, os, sys, urllib.parse
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

SOUBOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "podminky.json")
VOLNE = ("ano", "neresi")
_cache = None


def portaly():
    global _cache
    if _cache is None:
        try:   # bez tabulky by nástroje tiše pustily stahování i zveřejnění, které archiv zakazuje
            with open(SOUBOR, encoding="utf-8") as f:
                _cache = json.load(f)["portaly"]
        except (OSError, ValueError, KeyError) as e:
            sys.exit(f"Tabulka podmínek archivů {SOUBOR} chybí nebo je poškozená ({e}). "
                     "Aktualizuj nástroje projektu (novy_projekt.py) a pusť příkaz znovu.")
    return _cache


def host_z(adresa):
    a = (adresa or "").strip()
    if "://" not in a and "/" in a:
        a = "https://" + a
    return (urllib.parse.urlsplit(a).hostname if "://" in a else a).lower()


def pravidlo(adresa, text=""):
    """Pravidlo pro adresu (nebo doménu); text = zdroj/název pro výjimky. None = portál v tabulce není."""
    host = host_z(adresa)
    p = portaly().get(host)
    if p is None and host.startswith("www."):
        p = portaly().get(host[4:])
    if p is None:
        p = portaly().get("www." + host)
    if p is None:
        return None
    p = dict(p, host=host)
    hledat = f"{adresa} {text}".lower()
    for v in p.get("vyjimky", []):
        if v["obsahuje"] in hledat:
            p.update({k: v[k] for k in v if k != "obsahuje"})
            break
    return p


class Zakazano(SystemExit):   # SystemExit: nástroje chytají Exception, tohle neproklouzne do opakování
    pass


def zkontroluj_stahovani(adresa, co):
    """adresa = celá adresa nebo doména (výjimky podle cesty jen s celou adresou); co = 'dotaz' nebo 'obr'.
    Zakázaný portál → Zakazano s návodem, co dělat místo toho."""
    p = pravidlo(adresa)
    host = p["host"] if p else ""
    if not p:
        return
    smi = p.get("dotazy", True) if co == "dotaz" else p.get("obrazky", True)
    if smi:
        return
    druh = "stránky" if co == "dotaz" else "snímky"
    raise Zakazano(f"PODMÍNKY: {p['nazev']} ({host}) nástrojům nedovoluje stahovat {druh} – {p.get('proc', '')}.\n"
                   f"NEOBCHÁZEJ to jiným nástrojem, curl ani prohlížečem řízeným skriptem. Jak dál: {p.get('jinak') or 'reference/podminky.md'}\n"
                   f"Řekni to uživateli. Podrobnosti: reference/podminky.md")


def _jload(root, name, default):
    p = os.path.join(root, "data", name)
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def zdroj_obrazku(root, klic):
    """(adresa, text, záznam) obrázku podle dat projektu, nebo (None, '', None)."""
    svazky = _jload(root, "svazky.json", {})
    for z in _jload(root, "zaznamy.json", []):
        if z.get("klic") == klic:
            s = svazky.get(z.get("svazek", ""), {})
            adresa = z.get("odkaz") or s.get("url") or s.get("portal") or ""
            return adresa or None, f"{s.get('svazek', '')} {z.get('nazev', '')}", z
    for m in _jload(root, "mapy.json", []):
        if m.get("img") == klic:
            return m.get("url") or None, f"{m.get('zdroj', '')} {m.get('nazev', '')}", m
    for d in _jload(root, "dokumenty.json", []):
        if d.get("img") == klic:
            return d.get("url") or d.get("odkaz") or None, f"{d.get('zdroj', '')} {d.get('popis', '')}", d
    return None, "", None


def posoud_obrazek(root, klic):
    """(stav, zpráva): stav 'ok' | 'pozor' (jen nevýdělečně / zdroj neznámý) | 'souhlas' (bez souhlasu nezveřejňovat)."""
    adresa, text, polozka = zdroj_obrazku(root, klic)
    if polozka is not None and polozka.get("souhlas"):
        return "ok", f"souhlas: {polozka['souhlas']}"
    if not adresa and polozka is not None:   # položka bez odkazu: vlastní fotka nebo materiál od uživatele
        return "ok", "bez odkazu na portál (vlastní materiál)"
    if not adresa:
        return "pozor", ("zdroj obrázku v datech nenajdu (odkaz v zaznamy.json, url v mapy.json nebo dokumenty.json) – "
                         "u obrázku z archivu ověř podmínky v reference/podminky.md")
    p = pravidlo(adresa, text)
    if not p:
        return "pozor", f"portál {host_z(adresa)} v tabulce podmínek není – ověř jeho podmínky, než obrázek zveřejníš"
    if p["vyrez"] in VOLNE:
        return "ok", f"{p['nazev']}: {p.get('proc', '')}"
    if p["vyrez"] == "nekomercne":
        return "pozor", f"{p['nazev']}: jen nevýdělečně – {p.get('proc', '')}"
    return "souhlas", (f"{p['nazev']}: obrázek bez souhlasu nezveřejňovat – {p.get('proc', '')}. "
                       f"Na neveřejný web (za heslem) může. Se souhlasem archivu ho zapiš k položce: pole „souhlas“ "
                       f"(kdo a kdy, např. „SOA Třeboň, e-mail 5. 11. 2026“) přes zapis.py.")


def hlaska_obrazku(root, klic):
    """Zpráva pro vyrez.py a kontrola.py, když obrázek podle podmínek portálu nesmí na veřejný web (nebo je to nejisté);
    jinak None. Obrázek, jehož zdroj v datech ještě není, mlčí – ten hlásí kontrola odkazu u zápisu."""
    if zdroj_obrazku(root, klic)[2] is None:
        return None
    stav, zprava = posoud_obrazek(root, klic)
    return None if stav == "ok" or zprava.startswith("zdroj obrázku v datech nenajdu") else zprava


def main(a):
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if a[0] == "obrazky":
        root = os.getcwd()
        d = os.path.join(root, "vyrezy")
        nic = True
        for fn in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if fn.endswith(".jpg"):
                stav, zprava = posoud_obrazek(root, fn[:-4])
                if stav != "ok":
                    nic = False
                    print(f"{fn[:-4]}: {zprava}")
        if nic:
            print("Všechny výřezy se podle podmínek smí zveřejnit.")
        return
    p = pravidlo(a[0], " ".join(a[1:]))
    if not p:
        print(f"{host_z(a[0])}: v tabulce podmínek není – podmínky ověř na webu portálu (reference/podminky.md).")
        return
    ano = lambda b: "ano" if b else "NE"
    print(f"{p['nazev']} ({p['host']})\n  nástroj smí stahovat stránky: {ano(p.get('dotazy', True))}, snímky: {ano(p.get('obrazky', True))}"
          f"\n  obrázek do výstupu: {p['vyrez']}\n  proč: {p.get('proc', '')}")
    if p.get("jinak"):
        print(f"  jak dál: {p['jinak']}")


if __name__ == "__main__":
    main(sys.argv[1:])
