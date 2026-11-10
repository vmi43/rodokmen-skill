# Prameny k dějinám domu a obce

> Původ: převzato z vzoha/dejiny-domu-skill (skills/dejiny-domu/reference/prameny.md), commit bda6028; odstavec o prázdných spojených vrstvách (bílý obrázek) a věta o `elipsa.py` z e1cd204, jinak beze změn. **Nástroje, které tu zatím nejsou:** `akon.py`, `brno_scitani.py`, `commons.py`, `ddb.py`, `dnnt.py`, `esbirky.py`, `europeana.py`, `geolab.py`, `industrial.py`, `ipr_praha.py`, `mis.py`, `narp.py`, `ortofota.py`, `pamatky.py`, `rejstrik.py`, `seidel.py`, `translokace.py`, `valecne_hroby.py`, `veduty.py`, `zanikleobce.py`. U nich postupuj ručně na webu portálu (adresy jsou v tabulce) a nález zapiš běžným způsobem; až se nástroj přidá, odkaz začne platit.

Postup: **od dneška zpátky**. Každý pramen vám dá číslo domu, jméno držitele a odkaz na starší pramen.
Matriky (jak je číst, lhůty, písmo) → `matriky.md`. Portály a nástroje na stahování snímků → `portaly.md`.
Kde něco nevíš jistě (adresa portálu, co je digitalizované), ověř to. Co funguje, zapiš do `portaly.md` nebo `poznamky_pro_skill.md`.

## Mapa pramenů podle doby
| Doba | Pramen | Co dá k domu | Kde |
|---|---|---|---|
| dnes | katastr nemovitostí, RÚIAN | parcela, k. ú., dnešní obec | `mista.py ruian "Osada čp"` (hned ve Fázi 0 – dnešní obec a k. ú. bývají jiné, než se čeká), nahlizenidokn.cuzk.cz |
| 1938–dnes | letecké snímky | jak dům a dvůr vypadaly, kdy přibyly a zmizely stavby | ags.cuzk.gov.cz/archiv (Archiv ČÚZK, ročníky vypíše `cuzk_archiv.py lms`), ortofoto CENIA z 50. let (`cuzk_archiv.py mapa cenia50`, smí do PDF), ortofota po letech od 1998 (`ortofota.py serie`, ČÚZK smí do PDF), mapy.cz → „Letecká“ s volbou roku |
| 1880–1950 | pozemkový katastr (mapa ~1900–1950) | parcely a budovy, sedí na dnešní mapu | `cuzk_archiv.py mapa pk` |
| 1945–1952 | konfiskace a příděly (**hlavně pohraničí, majetek Němců, Maďarů a „zrádců“**) | komu dům vzali a komu ho přidělili, odhad, popis domu a živnosti, žádosti novoosídlenců | fondy Osidlovacího úřadu a Fondu národní obnovy (dům, živnost) a Národního pozemkového fondu (statek, půda) v SOA a SOkA, níže „Konfiskace a příděly 1945–1952“ |
| 1951–1992 | smlouvy, dědictví, evidence nemovitostí (od 1964) | vlastníci, ale **1951–1964 bez úplné evidence** (níže „Vlastníci po roce 1950“) | majitelé domu, katastrální pracoviště, SOkA |
| 1870–1950 | pozemkové knihy (vložky) a sbírka listin | vlastníci, kupní a svatební smlouvy, dluhy, výměnky | katastrální pracoviště (do 1950 často SOA / SOkA) – `archivni_dotazy.md` |
| 1857–1921 | sčítání lidu (1857, 1869, 1880, 1890, 1900, 1910, 1921) | **celá domácnost po číslech domů**: jména, roky a místa narození, vztahy, řemesla, dobytek | SOkA. Jižní Čechy jsou na digi.ceskearchivy.cz (stejný portál jako matriky; snímky jen prohlížet, `podminky.md`) |
| 1784–1900 | matriky (od 1784 se v nich uvádí číslo domu) | kdo v domě bydlel při křtu, sňatku a úmrtí. **Čti podle čísla domu, ne podle jména.** Číslo je bydliště, ne vždy místo události (svatba v kostele, smrt v nemocnici, ženich z jiného domu) | `matriky.md`, `portaly.md` |
| 1824–1843 | stabilní katastr: císařské otisky, indikační skici, písemný operát | půdorys domu a dvora, číslo domu, parcely. **Indikační skica má u parcel i jméno držitele** | `cuzk_archiv.py` (Archiv ČÚZK: originální mapy s reambulací, otisky, skici), písemný operát (parcelní protokoly): Čechy Národní archiv, Morava MZA, Slezsko ZA Opava |
| 1785–1789 | josefský katastr | držitel, výměra pozemků, číslo domu | Čechy Národní archiv (fond Josefský katastr), Morava MZA, Slezsko ZA Opava (fond Josefský katastr: jen písemný operát, parcelní protokol a kniha pozemnostních archů po berních obcích, mezery hlavně Těšínsko; protokoly bývají v Digitální badatelně ZAO se snímky). Jinde často jen badatelna |
| 1748–1757 | tereziánský katastr (**Čechy, Morava**) | usedlíci podle kategorie (sedlák, chalupník), výměra | Čechy Národní archiv, Morava MZA. Slezsko má místo něj karolinský katastr. Výtahy bývají v regionální literatuře |
| 1550–1850 | **gruntovní knihy** (pozemkové knihy vrchnosti) | **všichni držitelé gruntu za sebou**: koupě, dědictví, cena, splátky, výminky, sirotci | fond velkostatku (panství) v SOA. Některé jsou digitalizované na portálech SOA |
| 1654 | berní rula (**jen Čechy**) | jméno hospodáře, kategorie usedlosti, výměra, dobytek | tištěná edice po krajích (Kramerius / knihovny) |
| 1656–1679 | lánové rejstříky (**Morava**, protějšek berní ruly) | **jména hospodářů** po kategoriích (láníci, pololáníci, čtvrtláníci, domkáři s poli i bez), nově osazení, pusté grunty (nové od 1657, staré), vinice; bez čísel domů | MZA fond D 1, **svazek = panství**, digitalizované v ARON MZA (`portaly.md` → ARON MZA). Edice F. Matějka: kraj brněnský 1673–75 (1981), jihlavský a znojemský 1671–78 (1983), hradišťský 1669–71 (1984), přerovský 1675–76 (sborník Ostrava 14, 1987) |
| 1727–1728 | translokační plány židovských obydlí (**jen ~200 obcí, kde žili Židé**) | plán ulice, náměstí nebo vsi s domy, synagogou, kostelem, často i radnicí a dvorem; sto let před stabilním katastrem | `translokace.py "Obec"`, `detail <č.>`; **plán je návrh přestěhování, ne doklad, že se stalo** – porovnej s indikační skicou |
| 1721–1790 | karolinský katastr (**Slezsko**) | usedlosti a poplatníci, pozemky, mlýny, lesy, řemesla ve městech | ZA Opava, fond Karolínský katastr (107 knih, 57 kartonů, částečně přístupný). Zda je obec online, ověř v Digitální badatelně ZAO (`portaly.md`), jinak dotaz archivu |
| 1651 | soupis poddaných podle víry (**jen Čechy**) | domácnosti s věkem, ale **ne vždy úplné**: děti někde všechny, jinde až od ~1 roku nebo od ~10 let (podle panství), věk zaokrouhlený | edice po krajích |
| 1400–1700 | urbáře | povinnosti a platy jednotlivých usedlostí | fond velkostatku v SOA, edice |
| pravěk–novověk | archeologické výzkumy a nálezy (AMČR) | starší fáze osídlení, zaniklé stavby, středověké jádro vsi; u běžné chalupy často nic | Digitální archiv AMČR (digiarchiv.aiscr.cz), hledej podle katastru; jen nekomerčně (`podminky.md`) |
| 1914–1918, 1939–1945 | pomníky padlých, válečné hroby, evidence padlých | jména mužů z obce, kteří padli, s rokem narození a smrti; u padlých v 1. sv. válce útvar, místo smrti a domovská obec. Shoda s obyvatelem domu podle jména a věku | `valecne_hroby.py obec "Obec"`, `padli <Příjmení> --obec X` |
| vše | Památkový katalog NPÚ (památky i evidované objekty bez ochrany) | vznik a stavební vývoj, popis, literatura, odkazy na fotky a plány NPÚ | `pamatky.py "Obec"`, `detail <id>`; dům v katalogu chybět smí. Fotky obce i mimo katalog `mis.py hledej`, plány a stavebněhistorické průzkumy Carmen (ručně, `portaly.md`) |
| 1700–1990 | průmyslové a technické stavby (Industriální topografie VCPD FA ČVUT) | mlýn, pivovar, cihelna, továrna: datace, majitelé firmy, přestavby, zánik, literatura | `industrial.py "Obec"`, `detail <id>`; jen vybrané stavby, chybět smí |
| 1930–dnes | filmy a seriály natočené u domu (Filmová místa) | scéna, rok, jak vypadala ulice nebo dvůr; hlavně města, u vesnice často nic | filmovamista.cz ručně, hledej obec i čtvrť (`portaly.md`) |
| 1850–1990 | fondy obce a úřadů: archiv obce, MNV, škola, JZD, spolky, firmy | stavební povolení, domovní knihy, konfiskace a přídělové listiny, kroniky, kolektivizace | **co se k obci dochovalo a kde:** `narp.py "Obec"` (Národní archivní portál, všechny archivy). Snímky nejsou, fond si vyžádej v SOkA → `archivni_dotazy.md` |
| 1990–dnes | veřejný rejstřík (ARES): firmy, družstva, společenství vlastníků se sídlem v domě | **datum vzniku SVJ ≈ kdy se prodávaly byty**, bytové družstvo jako vlastník, hospoda a obchod v přízemí; sbírka listin (stanovy, smlouvy) | `rejstrik.py "Část obce" <čp>`, `detail <IČO>`; jen dnes zapsané, zaniklé ručně (`portaly.md`). **Sídlo není doklad vlastnictví ani bydliště** |
| vše | literatura, vlastivědy, kroniky obce a školy, noviny | události obce (požáry, války, stavby), staré názvy | Kramerius (`kramerius.py`), ANNO (`anno.py`), Google Books, SOkA (kroniky bývají online) |
| 1500–1850 | veduty v archivech (Soupis vedut do roku 1850) | podoba města, zámku, kláštera, kostela, katastrofy | www.veduty.cz v prohlížeči (`portaly.md`), hlavně města; sken patří archivu uložení |
| 1600–1950 | veduty, grafické listy, pohlednice, plány měst (knihovny) | podoba vsi, kostela, zámku, náměstí; staré plány města | `veduty.py "Obec"` (MZK, UK a další přes CDK); veduta není plán, ověř mapou. Mapy malé vsi podle polohy: `veduty.py mapy <šířka> <délka>`; obrázky ručně grafiky.mzk.cz, muzea (`esbirky.py`) |
| 1880–1960 | Fotoateliér Seidel, Český Krumlov (**jen Krumlovsko, Šumava, Pošumaví**) | pohledy na obec a domy, pohlednice; **ateliérové portréty obyvatel se jménem a adresou s čp.** (kniha zakázek) | `seidel.py "Obec"`, `detail <id>`; stejnojmenné obce rozliší pošta v adrese |
| 1850–1945 | Deutsche Digitale Bibliothek: Foto Marburg (památky, kostely, domy), Deutsche Fotothek (pohlednice), univerzitní diapozitivy, architektonická muzea (**německá místa a města, památky**) | podoba kostela, náměstí, domů, ulic; pohlednice měst kolem 1910 | `ddb.py "Obec" "Německý název"`, `detail <id>`; licence u předmětu (PDM, CC0, CC BY-SA ano, NC ne) |
| 1800–1950 | Europeana: sbírky evropských muzeí a knihoven (**rakouská, maďarská, německá muzea, mapy PřF UK**) | podoba obce, kostela, hradu; mapy okresů a okolí | `europeana.py "Obec" "Německý název"` (okolí podle polohy i název), `detail <id>`; potřebuje klíč; licence u předmětu |
| 1880–1945 | Bildarchiv Herder-Institutu Marburg (**německá místa Čech, Moravy a Slezska**, ~800 tis. fotek, negativů, pohlednic, online třetina) | podoba obce, kostela, náměstí před odsunem; foto dokumentace památek | jen ručně uživatel v Bildkatalogu (Claude ho neotevírá), skeny objednat (`portaly.md`); obrázek jen se souhlasem a poplatkem |
| 1895–1945 | pohlednice v obchodech a aukcích (akpool.de, delcampe.net, ansichtskarten-lexikon.de; **i malé vsi, hospody, mlýny**) | že pohled na obec nebo dům existuje, rok odeslání, co je na něm | jen ručně uživatel, český i německý název (`portaly.md`); jen vodítko, obrázek do výstupu ne, koupená pohlednice je vlastní originál |
| 1850–2000 | zaniklé vsi, samoty, mlýny, dvory a kaple (zanikleobce.cz, **hlavně pohraničí po 1945, mlýny všude**) | co stálo kolem domu a zmizelo, dobové fotky a pohlednice, vzpomínky pamětníků, počty obyvatel a domů | `zanikleobce.py "Obec"` (okruh 3 km), `detail <id>`; příspěvky dobrovolníků, ověř v pramenech; fotky jen se souhlasem autora |
| 1700–1960 | Wikimedia Commons: pohlednice, fotky, rytiny, plány, které nahráli lidé a instituce (**hlavně města, hrady, kostely**) | podoba obce a jednotlivých staveb; u měst sbírky pohlednic (Brück & Sohn) | `commons.py "Obec"`, `detail "<soubor>"`; volná licence, smí do PDF s autorem a licencí |
| 1896–1925 | pohlednice AKON (Rakouská národní knihovna, **celá monarchie, hlavně města, lázně, hrady**) | podoba obce, náměstí, ulic, továren a hotelů kolem roku 1900 | `akon.py "Obec"` (okruh 3 km od středu obce, i německý název), `detail <id>`; obrázek volné dílo, smí do PDF s citací; plný AKON (asi 2× víc) odkazem na mapu |
| 1860–1990 | fotografie, pohlednice, kresby a předměty ve sbírkách muzeí (eSbírky) | podoba domu, ulice, náměstí, slavností; staré negativy Národního a krajských muzeí | `esbirky.py "Obec"`, `detail <id>` (název obce v názvu předmětu); obrázek podle licence předmětu |
| 1764–1880 | vojenská mapování (1. 1764–68, 2. 1836–52, 3. 1876–80) | vzhled vsi a okolí, cesty, mlýny | 3. mapování: topografická sekce 1 : 25 000 v ÚAZK (`cuzk_archiv.py rady`, smí do PDF), orientace `cuzk_archiv.py mapa vm3`; 1. a 2. mapování: Geolab (`geolab.py`, smí do PDF), WMS CENIA jen na orientaci (`portaly.md` → Staré mapy a drobné památky); mapire.eu (jen prohlížení) |

## Městský dům 20. století (činžák, vila, 1890–1990)
Matriky a sčítání do roku 1921 tu skoro nepomohou (dům často stojí až po 1921; sčítací archy z roku 1930 a pozdější
bývají nedostupné – ověř v archivu).
Osvědčené pořadí:
1. **Dnešní adresy domu i sousedů** z RÚIAN: `mista.py okoli "Ulice čp/čo" 80`. Rohový dům má dvě adresy.
2. **Staré plány a letecké snímky stejného výřezu** – kdy na parcele poprvé stojí budova. V Praze IPR (plány 1889, 1909,
   1920, 1938 s čísly popisnými, 1944, ortofota 1938–2006: `ipr_praha.py serie … --zapsat`); jinde `cuzk_archiv.py mapa pk`.
3. **Adresní kniha čp. → ulice a č. or.** (Praha: Orientační kniha Velké Prahy 1936/1937) – jaká orientační čísla dům
   tehdy měl. Bez toho nejde hledat v adresářích.
4. **Adresáře živností** (Adresář Republiky československé 1927–1938, Adresář Prahy 1936, Adressbuch des Protektorates 1939,
   telefonní seznamy 1950; Brno: adresáře města 1779–1946 v PDF, `portaly.md` → Archiv města Brna) – obchody v přízemí, řemeslníci, lékaři. Řazené podle oborů – hlavička stránky řekne obor.
5. **Stavební povolení a soutěže:** Stavitelské listy (rubrika „Kde se bude stavěti?“ – stavebník, pozemek, počet pater),
   inzeráty „zadá práce na stavbu…“ v denících (Právo lidu, Národní listy). Stavebníkem bývá družstvo, stavitel nebo firma.
6. **Ročenky a seznamy členů spolků a zaměstnanců** (s adresami) – bydliště konkrétních lidí po letech; stejná osoba
   ve dvou ročnících s jinou adresou domu = **vodítko** k přečíslování, ne doklad (mohla se přestěhovat).
7. **Družstva:** jubilejní sborníky („Dílo družstevní svépomoci“ 1933), výroční brožury – počty domů, sídlo, fotky.
   Nástupce (lidové / stavební bytové družstvo) může mít archiv stavební dokumentace.
8. **Archiv:** stavební spis (stavební úřad městské části; v Praze odbor výstavby MČ, v AHMP jen torza → `portaly.md` AHMP), pozemková kniha (katastrální úřad), archiv družstva →
   `archivni_dotazy.md`. **Stojící dům má spis na stavebním úřadu, zbořený v archivu města** (tak to výslovně píše
   Archiv města Ostravy, ten má popisy spisů a plánů s adresou v Digitální badatelně, `portaly.md`; jinde podobně, ověř).
   Spis stojícího domu nahlédne vlastník nebo kdo má jeho plnou moc.
9. **Pozůstalost architekta nebo stavitele** (víš-li, kdo dům navrhl: Stavitelské listy, Památkový katalog, spis):
   `narp.py "<příjmení>"` najde jeho fond – často Archiv architektury a stavitelství NTM (výkresy, skici, fotky,
   korespondence). Návrh v pozůstalosti nemusí být postavený, nebo jinak: porovnej s plánem ze spisu a s mapou.
10. **Dokumentace přípojek u vodárny** (kanalizace, vodovod): plán přípojky s rokem bývá doklad přestavby, přístavby
   nebo nového bytu, i když chybí stavební spis. Dostane ji **jen vlastník domu** (nebo s jeho plnou mocí), takže o ni
   požádá on. Praha: PVK, žádost „Poskytnutí kopie z dokumentace přípojky“ na vyjadrovaciportal.cz, jen co
   bylo předáno do archivu PVK (od kdy, neuvádí), zpoplatněno podle ceníku PVK. Jinde se ptej místní vodárny.
   Starší plány stokové sítě a kanalizačních přípojek mívá archiv města (Praha: AHMP, technické fondy).
Většina tisku 1900–1990 je v Krameriu NK **neveřejná, ale v režimu DNNT** – čitelná z domova po přihlášení
(`portaly.md` → DNNT, nástroj `dnnt.py`: hledání, úryvky, hromadné čtení, `adresa` najde i rozdělená slova).
Bez přihlášení vidíš jen úryvky ve vyhledávání.

## Čísla domů – největší past
- Čísla popisná zavedla konskripce 1770–1771. **Ves se pak často přečíslovala** (typicky kolem 1805–1830 a znovu
  po 1900). Dnešní čp. 12 může být v roce 1800 jiné číslo.
- **Stejná osoba pod dvěma čísly je jen vodítko.** Mohla se přestěhovat, mít dva domy nebo provozovny, starý údaj
  se mohl opisovat dál, nebo jde o jmenovce. Přečíslování dolož něčím, co se týká domu, ne osoby: srovnávací
  seznam čísel, vyhláška obce s datem, tentýž dům nebo parcela na mapě či v pozemkové knize pod oběma čísly,
  nebo totéž posunutí u **několika** sousedních domů naráz. Dokud to nemáš, zapiš obě možnosti (přečíslování ×
  přestěhování). Adresáře a OCR opisující tentýž zdroj nejsou dva nezávislé doklady.
- Jak to poznat: stejná rodina pod dvěma čísly v blízkých letech (matrika ↔ sčítání) jako vodítko, stabilní katastr (číslo
  z doby mapování obce + půdorys = dnešní parcela), indikační skica (jméno držitele). Do `cisla` u domu zapiš všechna čísla s roky
  a **doklad** (klíč zápisu).
- Nový dům na parcele starého (vyhořel, rozdělení gruntu) dostává často nové číslo. Rozdělený grunt má dvě čísla.
- Do ztotožnění starého a nového čísla je všechno starší `prob`, s poznámkou proč.
- **Města: orientační čísla se měnila** (i ve 20. století, celé ulice najednou) a rohové domy mají dvě adresy.
  Nejdřív sestav **tabulku adres domu v čase** (čp., všechna č. or. a ulice, rok změny) a zapiš ji do `cisla` domu
  i do `STAV.md`. Každý nález s adresou („Dlouhá 38“, 1946) převeď podle **data** přes tuto tabulku: stejná
  adresa v jiném roce může být jiný dům (sousední nebo naproti přes ulici). Rok přečíslování hledej „kotvou“ – osobou
  nebo firmou, která má v jednom roce starou a v dalším novou adresu – a potvrď ho jako výš (vyhláška, celá ulice
  posunutá naráz, čp. beze změny). Údaj s adresou bez čp. a mimo ověřené období je `prob`.

## Vlastníci po roce 1950 – díra v evidenci
Zdroj: ČÚZK, Historie pozemkových evidencí (cuzk.gov.cz → Katastr nemovitostí → O katastru).
- **1951–1964 se vlastnictví nikde úplně nevedlo.** Od 1. 1. 1951 (občanský zákoník 141/1950 Sb.) vlastnictví
  přecházelo už samotnou smlouvou, rozhodnutím soudu nebo úřadu, zápis do pozemkové knihy nebyl potřeba. Jednotná
  evidence půdy (od 1956) zapisovala, **kdo půdu užívá, ne kdo ji vlastní** (JZD, státní statek).
- Od 1. 4. 1964 evidence nemovitostí: převod platil po registraci smlouvy státním notářstvím. Vlastníky do ní
  doplňovali postupně až do 1988, údaje jsou často neúplné. Od 1993 katastr nemovitostí.
- **Poslední zápis v pozemkové knize neznamená, že dům dál patřil témuž člověku.** Prodej, dědictví nebo
  konfiskace po 1950 v knize být nemusí. U držitele z knihy piš „podle pozemkové knihy (poslední zápis <rok>)“,
  ne „vlastnil do …“. Další řádek v `drzitele` dej až podle dokladu.
- Doklady za 1951–1992: smlouvy a usnesení o dědictví u majitelů (zeptej se jich, `pametnici.md`), sbírka listin
  a list vlastnictví evidence nemovitostí (katastrální pracoviště), spisy státního notářství a národního výboru
  (SOkA). Které fondy obce (MNV, JZD) se dochovaly, vypíše `narp.py "Obec"`; co v nich je, ověř dotazem →
  `archivni_dotazy.md`. Nic z toho není online.
- Od 1990 pomůže veřejný rejstřík: `rejstrik.py "Část obce" <čp>`. Společenství vlastníků jednotek (SVJ) vzniklo,
  až když se dům rozdělil na byty jako jednotky a ty měly víc vlastníků (do 2013 ze zákona při 5 jednotkách a 3
  vlastnících, od 2014 zápisem). Datum vzniku v `detail <IČO>` („Datum vzniku společenství“) je tedy **zhruba doba
  prodeje bytů**, ne den rozdělení domu. Bytové družstvo v domě bývá vlastníkem domu. Kdo vlastní dnes, řekne list
  vlastnictví.

## Konfiskace a příděly 1945–1952
Týká se hlavně pohraničí a domů, kde do 1945 žili Němci (také Maďaři a lidé označení za zrádce). Dekrety 1945
majetek zkonfiskovaly a stát ho přidělil novým obyvatelům. Úřady se dělily podle druhu majetku:
- **Dům, živnost, firma, rodinný domek, nábytek:** Osidlovací úřad a Fond národní obnovy (FNO, dekret 108/1945),
  oblastní úřadovny (Plzeň, Karlovy Vary, České Budějovice, Teplice, Pardubice, Opava, Olomouc, Trutnov…) a místní
  správy národního majetku. Ve fondech spisy o konfiskaci a přídělu, odhady, prodejní spisy; v Plzni i zvláštní
  řada přídělů rodinných domků.
- **Statek a zemědělská půda:** Národní pozemkový fond (NPF, dekrety 12 a 28/1945) a okresní osidlovací komise
  ministerstva zemědělství. Ve fondech přídělové spisy (žádost, přídělová listina, výměra, budovy).
- Najdi je: `narp.py "Osidlovací"`, `narp.py "Fond národní obnovy"`, `narp.py "Národní pozemkový fond"` a vyber
  úřadovnu, pod kterou obec patřila (podle okresu). `detail <id>` řekne přístupnost a inventáře. Malé okresní fondy
  bývají nezpracované, ptej se v archivu. Úřadovna OsÚ a FNO pro Liberecko, Ústecko a Brno v NARP chybí (11/2026; NPF má pobočku Teplice a Brno):
  pak MNV a ONV, které konfiskaci a příděl taky řešily (`narp.py "Obec"` → „Místní národní výbor …“ od 1945),
  a osidlovací komise okresu (Rumburk, Děčín, Kaplice…). Stejnojmenné obce mají MNV v různých archivech (Levín 3×).
- Nic z toho není online. Spis si vyžádej podle obce a čísla domu, nejlépe se jménem posledního německého
  majitele → `archivni_dotazy.md`. Příděl bývá zapsaný i v pozemkové knize (vklad pro přídělce).
- **Citlivé:** odsun a konfiskace se týkají rodin, které možná dosud žijí ve vsi nebo v Německu → `soukromi.md`.

## Gruntovní knihy – jak na ně
1. Zjisti **panství**, ke kterému ves (nebo dům!) patřila před 1848. Ves mohla patřit pod dvě panství (část domů
   jednomu, část druhému). Panství najdeš ve vlastivědě, v Sedláčkově Místopisném slovníku nebo v hlavičce matrik.
2. Fond „Velkostatek <panství>“ v příslušném SOA → inventář → gruntovní knihy pro danou ves (podle let).
   SOA Třeboň: na portálu strom fondů „Pozemkové knihy“ → archiv → fond velkostatku; totéž urbáře, vrchnostenská
   registra, kroniky. Portál smí uživatel jen prohlížet (`podminky.md`), ty radíš, kde hledat.
   MZA Brno (jižní Morava, Vysočina): gruntovní a pozemkové knihy jsou v **ARON MZA** (www.mza.cz/aron), ne v Acta
   Publica (ta má jen matriky). Postup v `portaly.md`, oddíl MZA.
3. Zápis o gruntu: „grunt N. N. … prodán … za … kop / zlatých“, splátky (vejrunky), výměnek pro rodiče, podíly
   sourozenců. Postupně ho čti od posledního držitele zpátky. U každé změny držitele vznikne řádek v `drzitele`.
4. **Vrchnostenský dům** (myslivna, fara, dvůr, mlýn, hospoda, zámek) v poddanské gruntovní knize často není (kniha
   začne až čp. 2) a v tereziánském katastru chybí v rustikálu. Hledej ho pod vrchností: dominikál, fase vrchnosti
   a farářů, josefinský katastr „Der Obrigkeit“ (bez čísla domu), urbáře, účty velkostatku. Chybějící dům v poddanské
   knize ještě neznamená, že nestál.
5. Online nejsou všechny. Co není, zapiš do `archivni_dotazy.md` (fond, signatura, roky) a navrhni návštěvu badatelny.
   Ve kterém archivu fond velkostatku leží a jak se přesně jmenuje: `narp.py "Velkostatek <panství>"`.

## Stabilní katastr (Archiv ČÚZK, `cuzk_archiv.py`)
Archiv ČÚZK je na https://ags.cuzk.gov.cz/archiv/ (staré archivnimapy.cuzk.cz už neexistuje). Nástroj ho čte bez prohlížeče.
1. `python3 -I tools/cuzk_archiv.py listy "Osada čp"` → katastrální obec v době stabilního katastru (**malá ves bývá součástí
   katastru sousední obce**) a předpony rastrů originální mapy, otisku, evidenční mapy a skici.
2. `cuzk_archiv.py prehled stable <om_SIGN_INV> pracovni/katastr/prehled.jpg` → všechny listy v jednom náhledu
   (pod každým id) → najdi ves, pak výřez ve velkém (`export stable <id> … x0,y0,x1,y1 5000`, podíly 0–1 jako u
   `vyrez.py`). Jednotlivé listy: `rastry stable <om_SIGN_INV>` a `export stable <id> list.jpg 0,0,1,1 1500`.
3. Mladší mapy k místu: `cuzk_archiv.py rady "Osada čp"` – otisky katastrálních map (města 1 : 1000, 1. pol.
   20. stol.: dům i číslo parcely v době, kdy stál), mapa evidence nemovitostí, Státní mapa 1 : 5000 ve více vydáních,
   **III. vojenské mapování**: topografická sekce 1 : 25 000 (`D1_21__…`, originál 1876–80 i pozdější vydání do 1953)
   a speciální mapa 1 : 75 000 (`D1_22__…`, ~20 vydání 1875–1952). Vypíše id rastrů pro `export nonstable <id>`.
   Čísla popisná v nich zpravidla nejsou, jen parcely. Listy vojenských map nejsou georeferencované: okolní názvy
   ukáže `cuzk_archiv.py mapa vm3 "Osada čp" vm3.jpg 1000 1000` (speciální mapa CENIA, jen ke čtení), ves na listu
   najdi `prehled`/`export` po částech (podíly 0–1). Sekce je mapa celé vsi s budovami, cestami a mlýny kolem 1880,
   **do PDF smí z ÚAZK** s citací „Ústřední archiv zeměměřictví a katastru, sign. D1/21, sekce 4453/4“.
- **Originální mapa** (om) je nejcennější: zeměměřiči do ní **dokreslovali změny při reambulaci 1869–1882 (změny
  červeně)**. Nová stavba nebo rozdělení parcely je tam i s číslem. Rok reambulace vypíše `listy`.
  **Jak číst barvy budov:** růžová = zděná, žlutá = dřevěná (stav při mapování). **Červeně šrafovaná nebo sytě červená
  budova a červená čísla = dokresleno při reambulaci** – stavba nebo přestavba až po mapování. Nepiš pak „dům tu stál
  už v roce [mapování]“, ale „budova je do mapy dokreslená při opravě v roce [reambulace]“. Přeškrtnuté číslo = zrušená
  parcela. Číslo stavební parcely vyšší než ostatní ve vsi = zpravidla pozdější dům (čísla šla od nejstarších).
- **Císařský otisk** (cio, barevný, 1824–43) = podoba vsi. Domy zděné červeně, dřevěné žlutě, s čísly popisnými
  (u části listů barvy a čísla chybí).
- **Evidenční mapa** (sign. B2/a/14C, služba `nonstable`, vzor vypíše `listy`, když je naskenovaná) = pokračování
  originálu: od roku 1883 se změny kreslily sem, často až do 20.–30. let 20. století. Ukáže ves i za prvorepublikových
  majitelů (nové domy, dělení parcel). Doplňky mají data přímo na listu, poslední datum ověř tam. V některých
  k. ú. se pozdější změny kreslily i do originální mapy – i tam rozhoduje datum na listu, ne rok reambulace.
- **Indikační skica** (služba `skici`, předpona S0X) = pracovní mapa se jmény držitelů a změnami. Je v aplikaci ČÚZK,
  ale **patří Národnímu archivu (Čechy) nebo MZA (Morava) – na snímcích je vodoznak „NA + ZA“**. **Barvy čísel jsou tu
  jinak než na originální mapě: v budově je červeně číslo popisné a černě číslo stavební parcely** (originální mapa má
  u budovy jen černé číslo parcely, červená čísla tam znamenají reambulaci). Při záměně čteš celou ves obráceně; ověř
  přes `mapa pk` s adresními body (níže). Čti z ní (čísla domů, držitelé), ale výřez nepřikládej do e-mailu, PDF ani
  na web bez souhlasu archivu (`podminky.md`). Přikládej originální mapu nebo pozemkový katastr.
- **Pozemkový katastr** (`mapa pk "Osada čp" výstup.jpg`) je georeferencovaný v S-JTSK: sedí na dnešní mapu, takže
  přes RÚIAN budovy jde ztotožnit starou parcelu s dnešním domem, zpravidla do pár metrů. (Posun 60–100 m k SV, který
  tu dřív stál, byl chybou nástroje: výřez se zadával ve WGS 84 a server ho do S-JTSK převedl bez transformace datumu.
  Výřezy z verzí do 0.4.0 proto nemají dům uprostřed.) `mista.py parcely "Osada čp"` vypíše dnešní stavební parcely
  kolem domu s odstupem v metrech, podle jejich čísel dům na mapě najdeš. `mapa pk` navíc vypíše a zakreslí dnešní
  adresní body RÚIAN (`…_adresy.jpg`): na které staré stavební parcele dnešní čp. stojí. **Dům na staré mapě takhle
  vždy ztotožni, než napíšeš, kde stojí** – ne podle čísla parcely nalezeného na skice nebo otisku (stejné číslo může
  mít pozemková parcela jinde ve vsi). Čísla stavebních parcel se často drží od stabilního katastru dodnes. Spojené
  vrstvy `originalni_mapy` a `cisarske_otisky` malé obce ani města (Olomouc) často nepokrývají: bílý obrázek nástroj
  neuloží, vypíše listy a postup `rastry` → `prehled` → `export`.
  Dům na mapě pro čtenáře označ elipsou: `elipsa.py <mapa.jpg> <klíč> cx,cy,a,b,úhel --popisek "čp. 183"` (pixely
  mapy, elipsa přes celou parcelu), příkaz s čísly do `poznamka` v `mapy.json`.
- **Ortofoto z 50. let** (CENIA, většinou 1952–54): `mapa cenia50 "Osada čp" výstup.jpg` – stejný výřez a čísla domů
  jako u PK, rok snímku a citaci vypíše. Pod CC BY, **smí do PDF i na web** s celou citací. Porovnání PK × ortofoto
  ukáže, co z dvora stálo po válce.
- **Letecké měřické snímky** (armáda, 30.–60. léta): `cuzk_archiv.py lms "Osada čp"` vypíše ročníky nad domem
  (třeba 1949, 1952, 1957, 1961). Snímky si uživatel prohlédne v aplikaci Archiv ČÚZK (`?start=lms`). Co hledat:
  kdy přibyla nebo zmizela stavba ve dvoře, sady, a hlavně **kolektivizaci** – úzké pásy polí soukromníků proti
  velkým lánům JZD o pár let později. Ročníky jsou usazené jen přibližně, proti sobě se posouvají o desítky až stovky
  metrů: porovnávej podle návsi a cest, ne podle souřadnic. Do textu napiš, co je na snímku vidět, s citací
  „Letecký měřický snímek <rok>, VGHMÚř Dobruška © MO ČR, Archiv ČÚZK“. **Výřez nepřikládej** (soubor je placený
  a jen pro vlastní potřebu, `podminky.md`). Obrázek z 50. let do výstupu vezmi z ortofota CENIA (výše).
- **Ortofota po letech od 1998** (změny domu v posledních desetiletích: přístavby, zbořené stodoly, nové domy):
  `ortofota.py serie "Osada čp" 100 --zapsat dum` stáhne všechny ročníky archivu ČÚZK nad domem (každý rok se snímkovala
  jen část republiky, u domu bývá ~10 ročníků, do 2001 černobílé) se stejným výřezem a zapíše je do `mapy.json`
  (web je prolíná, „ČÚZK, rok“, CC BY 4.0, smí do PDF). Kraje Jihočeský, Plzeňský, Jihomoravský a Zlínský přidají
  ročníky, které ČÚZK u domu nemá (Jihomoravský okresy od 1996) – **jen ke čtení**, licence krajů není zveřejněná.
  Do textu napiš, co se mezi ročníky změnilo („mezi 2004 a 2007 zmizela stodola ve dvoře“), s citací snímků.
- Ulož výřez se vsí a s domem do `dokumenty/`, pak `vyrez.py` a `data/mapy.json` (zdroj „ČÚZK, Archiv ČÚZK,
  <mapa, signatura, list>“, url https://ags.cuzk.gov.cz/archiv/). Na stránce domu se ukáže v galerii, porovnání viz `web.md`.
- Mapy ÚAZK (stabilní katastr, císařské otisky) se smí zveřejnit bez souhlasu a poplatku s citací „Ústřední archiv
  zeměměřictví a katastru“. Indikační skici a archivní letecké snímky ne – viz `podminky.md`. U map z jiných zdrojů
  vždy uveď zdroj. Na neveřejném webu to stačí.

## Sčítání lidu
- Archy jsou **po domech**: hlavička s číslem domu, pak všichni obyvatelé (i výměnkáři, čeledíni, podruzi).
- Na digi.ceskearchivy.cz má každá obec a rok svazek. Číslo snímku domu najdeš listováním (archy jdou podle čp.).
  Portál snímky jen ukazuje, kopírovat je podmínky nedovolují: čte uživatel, ty radíš (`podminky.md`). Na ostatních
  portálech stahuj nástrojem nebo snímek uloží uživatel podle `portaly.md`.
- Sčítání 1857–1880 nemusí být pro každý soudní okres online, 1890–1921 obvykle ano.
- **Brno** (město, předměstí, připojené obce) má vlastní sčítání v Archivu města Brna s rejstříkem jmen po domech:
  `brno_scitani.py dum "Ulice" <číslo>`, `osoby …` (`portaly.md` → Archiv města Brna). 1910 jen v badatelně.
- **Ostrava:** sčítání je podle tehdejšího politického okresu, ne podle dnešního města. Archiv města Ostravy má jen
  1900, 1910 a 1921 obcí okresu Moravská Ostrava (Moravská Ostrava, Přívoz, Vítkovice, Mariánské Hory, Zábřeh,
  Hrabová…); před 1900 SOkA Frýdek-Místek, Slezská Ostrava 1921 SOkA Frýdek-Místek, Svinov SOkA Nový Jičín. Digitalizované
  operáty jsou v Digitální badatelně ZA Opava (`portaly.md`), 1930 a mladší Národní archiv.
- **Údaje o domě a obyvatelé bývají na různých snímcích.** 1910: titulní list s vlastníkem domu, na dalším snímku
  osoby; 1921: sběrný arch domovní → prázdný list → sčítací arch. **Vždy stáhni i 1–3 následující snímky.**
  1857: cizí (čeleď, učni, tovaryši z jiných obcí) bývají jen v souhrnné tabulce cizích (Fremden-Tabelle) za souhrny
  obce, ne na archu domu.
  Vlastníka domu uvádí až 1910 a 1921; v 1890/1900 je „majitel bytu“ = hlava domácnosti, ne vlastník domu.
- Ze sčítání vznikne: událost domu („1890: v domě 9 osob, hospodář Jan Novák, rolník…“), obyvatelé s `r` a podklad
  pro hledání v matrikách (roky narození).

## Matriky podle čísla domu
- Od 1784 je u každého zápisu číslo domu. V knize hledej **všechny** zápisy z daného čísla (křty, sňatky, úmrtí).
  Tak poznáš, které rodiny v domě žily a kdy se střídaly (přiženění, prodej).
- Rejstříky jsou podle jmen. U domu proto nejdřív získej jména ze sčítání nebo z gruntovní knihy, pak teprve rejstřík.
- Pomocníkům dej konkrétní knihu, rozsah snímků a číslo domu: „vypiš všechny zápisy z Horní Lhoty čp. 12“.
- Malý domek (domkář, bez polí) v gruntovních knihách panství často není. Začni matrikami podle čísla domu.
  Pak rejstřík knih smluv: některé jsou řazené podle čísla domu, jinak podle jmen. Jména z matrik můžou patřit
  nájemníkům, ne majitelům.

## Obec
- Literatura: vlastivědy okresu, dějiny panství (např. „Geschichte der Herrschaft …“), Sedláček (Hrady, zámky a tvrze;
  Místopisný slovník), Profous (Místní jména v Čechách – původ názvu), Statistický lexikon obcí (počty domů a obyvatel).
- Do `OBEC_UDALOSTI` se stavem `lit` a `zdroj` (kniha, strana). Údaj z literatury, který jde ověřit v prameni,
  ověř a změň na `doc`.
- Kroniky obce a školy: bývají digitalizované u SOkA (na stejných portálech jako matriky). Čti zápisy o požárech,
  válkách, elektrifikaci a stavbách, často jsou tam i jména a čísla domů.
- Noviny: požáry, dražby („exekuční dražba usedlosti čp. …“), soudní zprávy.

## Lidé
- Pamětníci a majitelé: kdy a od koho dům koupili, přestavby, staré fotky. Zapiš do `pametnici.md`, stav `fam`.
- Domovní dokumenty (kupní smlouvy, stavební povolení, plány) přečti celé, bývají nejcennější.
