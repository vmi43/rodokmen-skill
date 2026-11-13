# Mapa matrik a index matrik – co už někdo přečetl

> Původ: zúženo z vzoha/dejiny-domu-skill (skills/dejiny-domu/reference/sdileni.md, commit 5c1715b; původně ondrnovy, sarsonj/rodokmen-skill#185). Přebrali jsme **jen čtení**. Odesílání (pull requesty do cizích repozitářů, sběrná schránka, souhlas uživatele) se nepřebralo, důvod je v `docs/decisions.md`.

Stejné knihy otvírají desítky badatelů. Dva cizí otevřené projekty sbírají, co už z nich někdo zjistil:

1. **[Mapa matrik](https://github.com/ondrnovy/mapa-matrik)**: které knihy pokrývají obec a rok a kde v knize co začíná („snímek 40 = rok 1785, ves Lhota“, začátek rejstříku). Bez jmen osob.
2. **[Index matrik](https://github.com/pe-pan/matriky-index)**: přepisy zápisů přečtených očima a OCR celých knih, vždy s odkazem na snímek u archivu.

## Kdy se nástroj použije

Při hledání svazku (`matriky.md`, krok „Najdi svazek“), **před otevřením knihy**:

```bash
python3 -I tools/sdileni.py najdi "Obec" 1785 N
```

Vypíše knihy z mapy, které obec a rok pokrývají, odhad snímku, kde začít, poznámky ke knize (posuny stránkování, oddíly po vsích) a kolik zápisů z knihy je v indexu. Rok i druh (N, O, Z) jsou nepovinné.

```bash
python3 -I tools/sdileni.py kniha <klíč svazku | adresa knihy>
```

Vypíše všechny orientační body knihy z mapy a zápisy, které už někdo přečetl.

## Pravidla

- **Zápis z indexu je vodítko, ne doklad.** Většinu přečetl jazykový model, často s nízkou jistotou. Ušetří hledání, ne čtení: ověř ho na snímku. Do `data/` jde jen to, co přečteš sám (`st="doc"`), nikdy převzatý řádek indexu.
- **Odhad snímku může být o pár snímků vedle.** Je to start, ne cíl.
- **Mapa ani index nejsou záruka.** Nemá-li mapa obec nebo kniha chybí, nebo služba neodpovídá, nástroj to řekne a postup jde dál obvyklou cestou (`portaly.md`).
- **Nic se neodesílá.** Nástroj jen čte; z projektu neodchází žádný údaj, snímek ani jméno. Dotazy jdou přes brzdu (`slusne.py`) a ukládají se na den do `~/.cache/rodokmen_sdileni/`.
- **Podporované archivy:** SOA Plzeň (Porta fontium) a SOA Praha (eBadatelna) pro mapu, k tomu AHMP pro index. U ostatních nástroj napíše, že je nepodporuje.
