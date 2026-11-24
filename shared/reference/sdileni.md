# Mapa matrik a index matrik – co už někdo přečetl

> Původ: zúženo z vzoha/dejiny-domu-skill (skills/dejiny-domu/reference/sdileni.md, commit 5c1715b; původně ondrnovy, sarsonj/rodokmen-skill#185). `sdileni.py` je **jen čtení**. Odesílání vlastních přepisů do indexu je zvlášť v `prispevek.py` (od 24. 11. 2026, viz „Odesílání“ níž a `docs/decisions.md`); pull requesty pod vlastním účtem a posílání orientačních bodů do mapy se nepřebraly.

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

## Odesílání vlastních přepisů do indexu (`prispevek.py`)

Index matrik je společný a roste tím, co lidé přečtou. Chceš-li přispět tím, co jsi přečetl do `data/indexy/` (viz `matriky.md`, „Index knihy“), jde to nástrojem `prispevek.py`. **Nikdy neodesílej bez výslovného souhlasu uživatele a bez toho, aby viděl, co přesně odejde.**

1. `python3 -I tools/prispevek.py navrh` – nic neodešle. Vyrobí `pracovni/sdileni/prispevek.json` a vypíše počet řádků, knihy, ukázku, vynechané řádky s důvodem a **otisk dávky**.
2. Ukaž to uživateli a řekni mu na rovinu: (a) příspěvek jde přes **cizí službu** (sběrná schránka Mapy matrik, Cloudflare Worker, který provozuje autor Mapy matrik, bez záruky provozu) a skončí jako pull request ve **veřejném** repozitáři indexu pod licencí CC BY 4.0; (b) co je jednou v cizím repozitáři, se z historie nedá spolehlivě vymazat; (c) bez jména je příspěvek anonymní (v `cetl` jen model a datum, rozlišuje ho pseudonym z náhodného klíče), jméno nebo přezdívka se zveřejní navždy; (d) schránka sdělí, kdo ji provozuje, a může kdykoli přestat fungovat.
3. Po jeho výslovném „ano“: `prispevek.py souhlas ano [jméno]` (jméno jen na jeho přání), pak `prispevek.py odeslat <otisk>`. Nesedí-li otisk (data se změnila), nic neodejde.
4. Schránka bere nejvýš 200 řádků z 15 knih najednou; zbytek pošli dalším kolem (`navrh` ukáže, co zbývá). Odeslané řádky si nástroj pamatuje v `data/sdileni.json` a podruhé je neposílá.

**Co jde ven:** zápisy N, O, Z z knih Porta fontium, eBadatelny SOA Praha a AHMP, **starší zákonných lhůt** (narození 100 let, sňatky a úmrtí 75 let), s datem a `cetl`, doslovný přepis. **Nejde ven:** rejstříky, mladší řádky, řádky bez data, jiné archivy, řádky se slovy o příbuzenství a ztotožnění (do indexu patří jen to, co stojí v zápisu), výřezy, snímky, rodokmen, cokoli z projektu. Zápis z indexu je vodítko, ne doklad: posíláš to, co přečetl model a co jsi ověřil nebo označil nízkou jistotou.
