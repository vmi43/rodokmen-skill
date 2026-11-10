# Dějiny obce a jejích domů (skill rodokmen:dum). Každý údaj má stav doložení `st`:
#   doc  = přečteno přímo v prameni (snímek matriky, gruntovní knihy, katastru, sčítání…)
#   lit  = z literatury (vlastivěda, kronika v knižním vydání, článek) – uvést kde v `note`/`zdroj`
#   prob = pravděpodobné (shoda údajů, ne přímý doklad) – v `note` proč
#   fam  = od majitele / pamětníka / rodiny (ústní podání, rodinné dokumenty)
#   unk  = neznámé (jen místo v přehledu)
# `r` = klíče zápisů z data/zaznamy.json, které údaj dokládají.
#
# Původ: struktura (OBEC, OBEC_UDALOSTI, D, ISSUES) vychází ze souboru skills/dejiny-domu/template/data/domy.py
# projektu dejiny-domu-skill (https://github.com/vzoha/dejiny-domu-skill), commit bda6028bae08307727a4449931497c9f163ea691.
# Naše úprava: pole `os` (vazba na osobu v data/osoby.py), viz níže.

# Obec – vstupní stránka webu „Obec“
OBEC = dict(
    nazev="",            # dnešní název („Horní Lhota“)
    jine_nazvy="",       # historické a německé názvy („Ober-Lhotta“)
    obec="",             # dnešní obec / katastr, okres („Dolní Lhota, okres Pelhřimov“)
    farnost="",          # kam patřila farou (matriky!) („Dolní Lhota“)
    panstvi="",          # panství před 1848 („Kamenice / Pacov“)
    popis="",            # 2–4 věty pro úvod stránky obce
    lat=None, lon=None,  # střed vsi (tools/mista.py hledej "Horní Lhota, Pelhřimov")
)

# Časová osa obce: dict(rok="1352", text="…", st="lit", r=[klíče], zdroj="vlastivěda okresu, s. 389")
# rok jako text („1352“, „22. 7. 1352“, „asi 1600“, „1618–1620“) – web podle prvního čtyřčíslí řadí.
OBEC_UDALOSTI = [
]

# Domy podle čísla popisného (klíč = číslo jako text, i „12a“, „ev. 3“). Dvě části obce se stejným čp. nebo nový
# dům na místě starého: jiný klíč („lhota-12“) a cp="12", cast="Horní Lhota" (reference/data.md).
# Pozor na přečíslování: čísla se zaváděla 1770–71 a obce se často přečíslovaly (hlavně 1805–1830 a po 1900).
# dict(
#   nazev="U Nováků",                   # jméno statku / chalupy (po domácku), může být prázdné
#   druh="selský dvůr",                 # selský dvůr / chalupa / domek / mlýn / hospoda / kovárna / škola…
#   st="doc",
#   popis="2–4 věty: co to je za dům dnes a čím je zajímavý",
#   lat=49.431, lon=15.221,             # poloha domu (tools/mista.py ruian "Horní Lhota 12" nebo ručně z mapy)
#   cisla=[("1771–1830", "čp. 7"), ("od 1830", "čp. 12")],   # starší a pozdější čísla téhož domu
#   udalosti=[dict(rok="1890", text="Sčítání lidu: v domě 7 osob…", st="doc", r=["lhota_scitani_cp12_1890"])],
#   drzitele=[dict(od="1786", do="1820", n="Jan Novák", jak="koupě od otce za 300 zl.", st="doc", r=[…], note="", os=None)],
#   obyvatele=[dict(n="Jan Novák", y="1790–1850", role="hospodář", f=["* 1790 Horní Lhota 12", "× 1815 Marie …"], st="doc", r=[…], os=None)],
#   note="rozpory, odkud údaj",
#   pribeh=["krátký příběh na stránce domu, odstavce"], pribeh_nadpis="", poradi=0,   # nepovinné
# )
#
# `os` (nepovinné, u držitele i obyvatele) = číslo téže osoby v data/osoby.py (Kekulého číslo předka). Má-li projekt
# i rodokmen, je to jediné místo vazby: dům odkazuje na osobu, osoba na dům ne. (Kontrola, že číslo v osoby.py
# existuje, se do kontrola.py teprve doplní.) U osoby mimo přímou linii (strýc, soused) `os` vynech a odkaz na rodokmen napiš do `note`.
D = {
}

# Rozpory a otevřené otázky (na web do „Co hledáme“) jako dvojice (otázka, odpověď). Odpověď začněte
# „Vyřešeno: …“ (na webu se skryje), „Hypotéza: …“ nebo „Otevřené: …“. Jde na web – nic citlivého.
ISSUES = [
]
