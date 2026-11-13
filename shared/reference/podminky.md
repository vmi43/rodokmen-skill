# Co se smí v archivech a mapových portálech

> Původ: převzato z vzoha/dejiny-domu-skill (skills/dejiny-domu/reference/podminky.md), commit bda6028, řádky Krameria (ČDK, UK, VKOL) z e1cd204; zúženo na portály, které naše nástroje používají; Porta fontium a SOA Praha podle našeho nástroje a `slusne.py`. Ostatní portály a text bez zkrácení najdeš v upstreamu. Portály a řádky přidané z 5c1715b: Slavné vily, encyklopedie měst, DNB (`heimatbuch.py`), GenWiki, Bundesarchiv, Bildarchiv Austria, Polona, SBC.

> **Upozornění:** Vycházím jen z veřejných zdrojů: podmínky portálů, badatelské řády, ceníky a zákaz pro roboty (soubor robots.txt). Stav 3. 11. 2026. Není to právní rada a nic z toho jsem zatím neověřil přímo u archivů. Podmínky se mění. Platí vždy aktuální znění na webu archivu nebo jeho písemná odpověď. Když si nejste jistí, zeptejte se archivu.

## Jak tabulku číst
**Čtení** říká, jak se AI dostane ke snímkům:
- **Nástroj:** skript skillu stahuje sám, pomalu.
- **Ručně:** snímky stáhnete nebo uložíte vy, AI je pak přečte. Ověření „nejsem robot“ řešíte vy.
- **Jen číst:** snímky se nesmí kopírovat. Čtete vy, AI poradí, co hledat a jak číst staré písmo.
- **Objednat:** snímky jen přes archiv nebo e-shop.

**Zákaz pro roboty (soubor robots.txt)** je pokyn pro vyhledávače a plošné stahovače. Nástroj skillu na váš konkrétní dotaz se chová jako vy při klikání: vezme jen to, co hledáte, pomalu a nic dvakrát. Proto ho samotný robots.txt nezastaví. Nástroje se představují jako **Claude-User** (robot Anthropicu, který stahuje na dotaz uživatele) a dodrží robots.txt, který Claude-User jmenuje. Zákaz pro ClaudeBota (sbírá web pro trénink modelů), Claude-SearchBota nebo GPTBota se dotazu uživatele netýká. Vždy ale platí podmínky portálu, které roboty nebo kopírování výslovně zakazují. Ověření „nejsem robot“ a blokace se nikdy neobcházejí.

Další sloupce: **Pro sebe** (rodina, nevýdělečný web), **Za peníze** (placené bádání pro někoho jiného), **Obrázky** (zveřejnit snímek nebo výřez), **Výsledky** (zveřejnit zjištění a vlastní přepis).

„Za peníze“ znamená: smíte zdroj při placené práci prohlížet a použít zjištění. Hodnoty: **ano** · **neřeší** (podmínky o tom mlčí) · **souhlas** (jen s písemným souhlasem, objednávkou nebo smlouvou; tak se chovejte i tam, kde je to nejasné) · **ne**.

Vždy uveďte archiv, fond, signaturu, číslo snímku a trvalý odkaz. Zjištění a vlastní přepis nikomu nepatří, proto jsou Výsledky všude „ano“. „Za peníze: ne“ omezuje, jak se k zápisu dostanete, ne co smíte se zjištěním dělat. Když stejný zápis získáte jinou cestou (badatelna, objednaný sken, souhlas archivu), přepis použijete i za peníze.

## Archivy
| Archiv | Čtení | Pro sebe | Za peníze | Obrázky | Výsledky | Poznámka |
|---|---|---|---|---|---|---|
| SOA Třeboň (DigiArchiv) | Jen číst | ano | jen prohlížet | souhlas | ano | Snímky jen k prohlížení online, kopírovat se nesmí. Nástroj skillu archiv blokuje |
| SOA Plzeň (Porta fontium) | Nástroj (osobní bádání, brzda 10 s) | ano | **ne** | souhlas | ano | Podmínky skripty nezakazují (robots.txt: Crawl-delay 10 s). Popisy archiválií k nevýdělečným účelům s citací, snímky mimo portál jen podle § 92 autorského zákona. Za peníze jen badatelna nebo objednané skeny (ověřeno 5. 11. 2026, docs/decisions.md) |
| SOA Litoměřice | Ručně | ano | neřeší | souhlas | ano | Zveřejnit jen se souhlasem. Knihu najdete vy, snímky stáhne nástroj. Po ~100 rychlých kliknutích blok na 30 minut |
| ZA Opava | Ručně | ano | neřeší | souhlas | ano | Stejný portál jako Litoměřice. Ověření „nejsem robot“ řešíte vy |
| MZA Brno (Acta publica) | Ručně | ano | neřeší | souhlas | ano | Snímky nezveřejňovat a dál nevyužívat bez písemného souhlasu. Ověření řešíte vy |
| SOA Praha (eBadatelna) | Ručně | ano | neřeší | neřeší | ano | Od 2. 11. 2026 robots.txt zakazuje nástroji rodokmen vše a server vrací 403: nástroj stojí (slusne.py). Matriky čti v prohlížeči eBadatelny |
| SOA Hradec Králové (ARON) | Nástroj | ano | neřeší | neřeší | ano | Stahovat jednotlivé snímky i celé knihy se smí. Archiv si stěžuje na AI boty, stahujte málo a pomalu |
| Národní archiv (policejní přihlášky, konskripce Prahy) | Nástroj | ano | neřeší | neřeší | ano | Jen zákaz v robots.txt, podmínky nenalezeny (8. 11. 2026). Nástroj hledá jen konkrétní osoby |
| Národní archivní portál (seznam fondů všech archivů) | Nástroj | ano | ano | — | ano | Jen popis fondů, snímky tu nejsou. Veřejná evidence ze zákona, robots.txt ani ověření nemá (8. 11. 2026) |
| Národní archiv (Digitální badatelna) | Ručně | ano | neřeší | souhlas | ano | Ověření „nejsem robot“ řešíte vy. Zveřejnit jen se souhlasem |
| Archiv hl. m. Prahy | Nástroj | ano | souhlas | souhlas | ano | Objednávka s účelem, užití zdarma. Na web nejvýš 500 px s vodoznakem |
| FamilySearch | Ručně | ano | ano, pro klienta | souhlas | ano | Genealog smí bádat pro klienta a předat mu výsledek. Stahovat jen ručně, roboti zakázáni |
| Matricula | Ručně | ano | ne | nevýdělečně, beze změn | ano | České matriky tam nejsou |
| Kramerius NDK (knihy nedostupné na trhu) | Jen číst | ano | **ne**, ani číst | ne | ano | Jen pro osobní potřebu registrovaných čtenářů z ČR. Za peníze si knihu půjčte v knihovně, fakta s citací pak smíte |
| Česká digitální knihovna (Krameria knihoven) | Nástroj | ano | souhlas | souhlas | ano | Hledá ve všech knihovnách najednou (`kramerius.py --knihovna`). Nástroj čte jen text veřejných děl; kniha neveřejná v NK bývá veřejná jinde. Sken patří knihovně uložení (MZK, UK, VKOL…), podmínky ČDK nenalezeny |
| Kramerius UK a VKOL (i přes Českou digitální knihovnu), veřejná díla | Ručně | ano | ano | ano, volné dílo s citací | ano | Podmínky užití obou knihoven omezují jen díla po přihlášení. Licence „public“ ještě neznamená volné dílo: ověřte autory v katalogu (`kramerius.py autori <uuid>`: data narození a úmrtí), volné je až 70 let po smrti posledního autora. Pak do zdroje „Kramerius, volné dílo“ a citace: název, rok, autor, knihovna, trvalý odkaz (10. 11. 2026) |
| ANNO (staré noviny, ÖNB) | Nástroj | ano | ano | ano | ano | Kromě skenů od Googlu |

## Mapy
| Zdroj | Čtení | Pro sebe | Za peníze | Obrázky | Výsledky | Poznámka |
|---|---|---|---|---|---|---|
| ÚAZK (stabilní katastr, mapy kolem 1830) | Nástroj | ano | ano | ano | ano | Zveřejnit lze bez souhlasu i poplatku (ceník ÚAZK). Badatelský řád sice komerční využití obecně zpoplatňuje, státní sazebník ale takový poplatek nemá. Uveďte „Ústřední archiv zeměměřictví a katastru“ a signaturu |
| ČÚZK, dnešní letecké snímky | Nástroj | ano | ano | ano | ano | Uveďte „ČÚZK, rok“ |
| ČÚZK, archivní letecké snímky | Ručně, soubor objednat | ano | prohlížet ano, soubor souhlas | souhlas | ano | Prohlížení v aplikaci zdarma, popsat, co vidíte, smíte. Soubor 500 Kč a jen pro vlastní potřebu |
| ČÚZK, archivní ortofoto 1998–2023 (`ortofota.py`) | Nástroj | ano | ano | ano | ano | Otevřená data CC BY 4.0, uveďte „ČÚZK, rok snímku“ |
| Letecké snímky 50. let (CENIA) | Nástroj | ano | ano | ano | ano | Uveďte celý zdroj: „Historická ortofotomapa ©CENIA 2010 a ©GEODIS BRNO, spol. s r.o. 2010, Podkladové letecké snímky poskytl VGHMÚř Dobruška, ©MO ČR 2009“ |
| III. vojenské mapování (geoportál CENIA) | Nástroj | ano | prohlížet ano | souhlas | ano | Stejný rozpor podmínek jako u II. mapování. Obrázek vezměte z ÚAZK |
| Indikační skici, Čechy (Národní archiv) | Ručně | ano | neřeší | souhlas | ano | Najdete je v aplikaci ČÚZK Archiv, patří ale Národnímu archivu |
| Indikační skici, Morava (MZA) | Ručně | ano | neřeší | souhlas | ano | Platí podmínky MZA |
| Slavné vily (slavnevily.cz) | Ručně | ano | neřeší | souhlas | ano | robots.txt hledání nezakazuje; fotky a texty z knih nakladatelství Foibos, jen fakta s citací (10. 11. 2026) |
| Encyklopedie dějin města Brna (`brno_encyklopedie.py`), Plzně a Ostravy | Nástroj (Brno), ručně | ano | neřeší | souhlas | ano | Podmínky užití neuvedeny, robots.txt nemá; fakta s citací ano, fotky a delší text se souhlasem muzea (10. 11. 2026) |
| Katalog Německé národní knihovny (SRU, `heimatbuch.py`) | Nástroj | ano | ano | — | ano | Zdarma a bez registrace, metadata CC0. Jen popis knih; z knihy samé údaje s citací, fotky a delší text se souhlasem vydavatele (10. 11. 2026) |
| Mapa matrik (ondrnovy.github.io, `sdileni.py`) | Nástroj | ano | ano | — | ano | Jen čtení orientačních bodů knih (bez snímků a jmen); cizí projekt bez záruky provozu (13. 11. 2026) |
| Index matrik (pe-pan.github.io, `sdileni.py`) | Nástroj | ano | ano | — | ano | Jen čtení přepisů zápisů; licence CC BY 4.0 jen podle návodu upstreamu, na stránce indexu neověřeno; zápis je vodítko, ne doklad (13. 11. 2026) |
| GenWiki (wiki-de.genealogy.net) | Ručně | ano | neřeší | neřeší | ano | Ochrana Anubis odmítá Claude-User, Claude neotevírá. Hledá uživatel (stránky `Bezirk …`, literatura, Heimatkreis a Ortsbetreuer) (10. 11. 2026) |
| Bundesarchiv, Digitales Bildarchiv | Ručně | ano | poplatek | poplatek | ano | Zdarma jen soukromě a na nekomerčním webu do 800 px, publikace s poplatkem (BKMBGebV); robots.txt nemá. Dar Bundesarchivu na Commons je CC BY-SA 3.0 DE (10. 11. 2026) |
| Bildarchiv Austria (ÖNB, fotky) | Ručně | ano | poplatek | poplatek | ano | Web picturemaxx bez API; snímky objednat podle Tarifordnung ÖNB. Pohlednice ÖNB viz AKON (10. 11. 2026) |
| Polona (Polská národní knihovna) | Ručně | ano | podle licence | podle licence | ano | Nástrojům odmítá spojení, Claude neotevírá; licence u objektu (10. 11. 2026) |
| Śląska Biblioteka Cyfrowa | Ručně | ano | podle licence | podle licence | ano | robots.txt zakazuje jen stahování ZIP; hledání jen v prohlížeči; licence u objektu (10. 11. 2026) |

## Jak se tím řídí nástroje skillu
- `tools/podminky.json` je stejná tabulka pro nástroje (zúžená na portály, které naše nástroje používají). `slusne.py` ji kontroluje před každým požadavkem: portál, který stahování nedovoluje, skončí hláškou „PODMÍNKY: …“ s návodem, jak dál. Hláškou „PODMÍNKY“ ani „OCHRANA“ neobcházej jiným nástrojem, curl ani prohlížečem řízeným skriptem.
- Pravidla platí i pro část webu (`vyjimky` podle adresy).
- `python3 -I tools/podminky.py <adresa>` vypíše pravidla pro portál; `python3 -I tools/podminky.py obrazky` vypíše výřezy, které potřebují souhlas archivu.
- Souhlas archivu zapiš k zápisu nebo mapě do pole `souhlas` (kdo a kdy). `vyrez.py` po uložení výřezu a `kontrola.py` upozorní na obrázek, který bez souhlasu nesmí na veřejný web; `export_web.py` ho do veřejného webu nezveřejní (jen otevřený web, ne za heslem).

## Koho se zeptat
Třeboň digi@ceskearchivy.cz · Litoměřice badatelna@soalitomerice.cz · Opava digibadatelna.podpora@zao.archives.cz · MZA podatelna@mza.cz · Kramerius MZK digitalniknihovna@mzk.cz · CENIA geoportal@cenia.gov.cz · Geolab bruna@geolab.cz · IPR Praha hribal@ipr.praha.eu

## Dále platí
- Kroniky, fotky a kresby z 20. století zveřejněte, jen když víte, že autor zemřel před víc než 70 lety, nebo máte souhlas dědiců.
- Žijící lidi a dnešní majitele zmiňujte jen s jejich souhlasem.
- I tam, kde smí nástroj, stahujte jen snímky k jednomu domu a pomalu.
