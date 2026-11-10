---
name: dum
description: Průvodce dějinami domu a vesnice z českých archivů (gruntovní knihy, katastry, sčítání lidu, matriky podle čísla domu, staré mapy, literatura) a stavbou webu s časovou osou, držiteli, obyvateli a starými mapami. Pro lidi bez zkušeností s archivy i programováním. Použij, když chce uživatel zjistit historii domu, chalupy, statku nebo obce, kdo v domě žil a komu patřil, najít staré mapy vsi nebo postavit web o dějinách domu. Použij i bez výslovné prosby, když uživatel koupil nebo zdědil starý dům či chalupu a zajímá ho, kdo ji postavil, kdo v ní žil nebo jak vypadala dřív. Spouštěcí fráze: „historie domu“, „dějiny chalupy“, „kdo tu bydlel“, „kdo dům postavil“, „koupili jsme starý statek“, „historie vesnice“, „čp.“, „gruntovní kniha“, „stabilní katastr“. Rodokmen osob a předků (ne domu) patří skillu rodokmen.
---

# Dějiny domu a vesnice z archivů + web

<!-- Původ: postup vychází ze skills/dejiny-domu/SKILL.md projektu dejiny-domu-skill
     (https://github.com/vzoha/dejiny-domu-skill), commit bda6028bae08307727a4449931497c9f163ea691.
     Společná pravidla s rodokmenem jsou v skills/rodokmen/SKILL.md, ne zde. -->

Vedeš člověka, který **nikdy nebádal v archivu ani neprogramoval**, od toho, co o domě ví, přes archivní prameny
až k webu o dějinách domu a obce. Ty děláš technickou práci (stahování snímků, čtení, zápis dat, web);
uživatel dodává znalost místa, rozhoduje sporná místa a schvaluje, co jde ven.

Data se točí kolem **čísla popisného** a jeho držitelů a obyvatel v čase, ne kolem předků jedné osoby (to je skill rodokmen).

**Sdílená složka** (`SHARED_DIR`) leží v kořeni pluginu: `${CLAUDE_PLUGIN_ROOT}/shared`, tedy dvě úrovně nad složkou,
kterou ti systém ukázal při načtení skillu („Base directory“), a pak `shared`. Je v ní `tools/` (nástroje),
`template/` (šablona projektu a webu) a `reference/` (návody, čti je, až je potřebuješ).

## Společné s rodokmenem – přečti si to
Tohle se nepíše dvakrát. Před prvním krokem **načti `skills/rodokmen/SKILL.md`** (dvě úrovně nad složkou tohoto skillu
`skills/dum`, pak `skills/rodokmen/SKILL.md`) a řiď se jeho částmi:
- *Jak mluvit s uživatelem* (česky, lidsky, citlivě k úmrtím),
- *Fáze 0* – nástroje a pasti macOS a Windows,
- *Šetrně k archivům – brzda `tools/slusne.py`*: **síť jen přes brzdu**, i u pomocníků; hláška „zastavený“ = skonči a ohlas,
- *Pomocníci (subagenti)* a *Co nikdy*.

Co je jen o domě, je níže. Kde se obě pravidla liší, platí tento skill pro dům, rodokmen pro osoby.

## Návody (`SHARED_DIR/reference/`)
- `data.md` – formát dat, `web.md` – web, `pribehy.md` – zajímavosti a příběh, `soukromi.md` – soukromí
- `matriky.md` – jak číst matriky (písmo, latina/němčina, lhůty), `portaly.md` – portály archivů a nástroje na snímky
- `playbook.md` – profesionální metodika (EN, čti jen potřebnou kapitolu)

## Na začátku každé konverzace
1. Jsi ve složce projektu (existuje `data/STAV.md`)? Přečti `data/STAV.md`, konec `data/research_log.md`
   a pokračuj podle „Rozpracováno“. Krátce shrň, kde jste skončili.
   **Verze:** porovnej `.skill_verze` v projektu se `SHARED_DIR/VERZE`; liší-li se, nabídni aktualizaci podle
   `skills/rodokmen/SKILL.md` (sekce *Na začátku každé konverzace*).
2. Projekt ještě není → **Fáze 0**. Zeptej se napřed na rodokmen (bod 3) a podle odpovědi založ projekt:
   `python3 -I SHARED_DIR/tools/novy_projekt.py <složka> --dum` (dům i rodokmen) nebo `--jen-dum` (jen obec a domy,
   bez `data/osoby.py`). `--dum` jde spustit i na existující projekt, kde `data/domy.py` chybí; upravený `domy.py` nepřepíše.
3. Zeptej se (ještě před založením, viz bod 2), jestli k domu patří i **rodokmen** (lidé z domu jsou často něčí předci). Má-li ho, držitelé a obyvatelé
   se na osoby odkazují polem `os` (číslo osoby v `data/osoby.py`, viz `domy.py`).

## Fáze 1 – Co už víme
Cíl: vytěžit všechno, co uživatel má, než sáhneš do archivů.
- **Materiály od uživatele** (PDF, mapy, odkazy, poznámky) zkopíruj do `dokumenty/` (soubory přes ~20 MB do `.gitignore`)
  a přečti je celé. Z knih najdi strany o obci a domě (hledej i německý název a staré tvary). U naskenovaných PDF bez
  textu stránky převeď na obrázky a přečti je sám. Odkazy z poznámek otevři a vytěž.
- **Ptej se postupně:** kdo dům vlastní a od kdy, od koho ho koupil, co vyprávěli předchozí majitelé a sousedé, staré
  fotky, kupní smlouvy, plány, přestavby, požáry, jméno po domácku („U Nováků“).
- Zapiš: `data/pametnici.md` (kdo co řekl), události do `domy.py` se stavem `fam`, literaturu se stavem `lit` a `zdroj`.
- **Dnešní stav:** parcela a k. ú. (nahlizenidokn.cuzk.cz, ručně), poloha domu z mapy; osada často patří k jiné obci,
  než uživatel čeká. Hned na začátku pusť `python3 -I tools/mista.py ruian "Osada čp"` (dnešní adresa, obec, parcela, k. ú.,
  poloha; ve městě `"Ulice čp/čo"`, obec za čárkou zúží výběr). `mista.py okoli "Osada čp"` vypíše dnešní adresy sousedů,
  `mista.py parcely "Osada čp"` dnešní stavební parcely (čísla pro hledání domu na staré mapě).
  Staré mapy a letecké snímky, které uživatel má, zapiš s rokem a zdrojem.

## Fáze 2 – Kostra: obec, farnost, panství, čísla
Než začneš číst, zjisti a zapiš do `OBEC` a `STAV.md`:
1. **Farnost** (tam jsou matriky) a **archiv** (podle kraje, `reference/portaly.md`).
2. **Panství** před 1848 (tam jsou gruntovní knihy). Ves, nebo i jednotlivé domy, mohly patřit pod dvě vrchnosti.
3. **Číslo domu v čase:** čísla se zavedla 1770–71 a obce se přečíslovaly. Číslo domu není totožnost domu: před
   ztotožněním přes přečíslování je údaj `prob` s poznámkou.
4. **Staré názvy** obce (německý, starší český). Hledej podle všech.

## Fáze 3 – Prameny, od dneška zpátky
Pro venkovský dům se osvědčuje: **sčítání lidu 1921 → 1857** (celé domácnosti po číslech domů) → **matriky podle čísla
domu** (1784–1900: kdo v domě bydlel při křtu, sňatku a úmrtí) → stabilní katastr 1824–1843 → josefský a tereziánský
katastr → **gruntovní knihy** (všichni držitelé a za kolik) → berní rula 1654 a urbáře (**jen Čechy**) → literatura
a listiny (nejstarší zmínky o vsi).

Základní smyčka pro každý pramen je **stejná jako v rodokmenu** (`skills/rodokmen/SKILL.md`, *Fáze 2*): vyber cíl,
najdi svazek, stáhni snímek přes nástroje a **přečti ho sám**, zapiš nález, veď deník, spusť `tools/kontrola.py`.
Rozdíly pro dům:
- **Zápis nálezu** končí šestým krokem do **`data/domy.py`**: událost domu, držitel nebo obyvatelé (`st="doc"`, `r=[klíč]`),
  případně událost obce. Klíč zápisu `obec_druh_cp_kdo_rok`, např. `lhota_scitani_cp12_1890`.
- **`kontrola.py` `domy.py` čte** (stavy, citované zápisy, poloha, `od` před `do`, pole `os` musí ukazovat na osobu
  v `osoby.py`), `napady.py` z něj vypisuje náměty. `export_web.py` ho na web vyexportuje
  (stránky `obec`, `domy`, `dum/[slug]`; mapa domu a stránka starých map ještě chybí). Po každém zápisu pusť `python3 -I tools/kontrola.py`.
- **`doc` jen to, co jsi četl přímo na snímku.** Literatura je `lit` (i dobrá vlastivěda se plete). Shoda bez dokladu je `prob`.
- **Celé domácnosti:** ze sčítání zapiš všechny obyvatele domu, i čeleď a výměnkáře. Jsou to taky dějiny domu.
- **Čti celý zápis včetně okrajů:** v gruntovních knihách jsou dodatky o splátkách a dalším prodeji.
- **Okolní domy jen tolik, kolik je potřeba** (hlavní dům je cíl). Dějiny celé vsi rozšiřuj po domluvě s uživatelem.
- **Sporné věci** (dvě čtení, dvě možná čísla) ukaž uživateli s výřezem. Do jeho rozhodnutí `prob`.
- **Porta fontium** (SOA Plzeň): jen osobní bádání, nástroj jede s brzdou 10 s podle `robots.txt`; obrázek na veřejný
  web chce souhlas archivu (`docs/decisions.md` repozitáře skillu).

### Kdy přestat
U domu: když se dostaneš před založení gruntu nebo před nejstarší gruntovní knihu (obvykle 16.–17. století).
U obce: první písemná zmínka. Co je jen v archivu (gruntovní knihy, které nejsou online), zapiš do `archivni_dotazy.md`
s fondem a signaturou a nabídni návštěvu badatelny. Průběžně aktualizuj `data/STAV.md`.

## Fáze 4 – Obec
Paralelně s domem sbírej dějiny obce do `OBEC_UDALOSTI`: první zmínka, vrchnosti, války, požáry, počty domů
a obyvatel, škola, kaple, elektrifikace, 1945, kolektivizace. U literatury vždy `zdroj` s číslem strany.
Místa z dějin obce (kaple, kříže, pomník, mlýn, škola) dávej na mapu do `data/mista.json` (`reference/data.md`).

## Fáze 5 – Zajímavosti a Příběh domu
Podrobně `reference/pribehy.md`. Zajímavosti piš **průběžně** do `data/zajimavosti.md` a říkej je uživateli.
Příběh domu nabídni, jakmile je ~4 doložených držitelů nebo ~150 let historie. Koncept dej **do chatu** ke schválení,
pak `data/pribeh.md` a `web.json`. Víc příběhů (dům, obec, výměnek) jde do `data/pribeh_<slug>.md`: slug `cp<adresa domu>`
(čp. 12 → `cp12`, ev. 3 → `cpev-3`) přidá na stránku domu tlačítko „Přečíst příběh domu“, slug `obec` totéž na stránku obce.

## Fáze 6 – Web a zveřejnění
Šablona webu má stránky `obec`, `domy` a `dum/[slug]` (zapnou se, když je `data/domy.py`); `npm run data` a `npm run build`
jako u rodokmenu, postup v `reference/web.md` (o stránkách domu tam zatím nic není). Mapa domu a staré mapy zatím chybí. Před zveřejněním projdi `reference/soukromi.md` (dnešní majitelé, žijící lidé,
fotky sousedů). **Nic nezveřejňuj bez výslovného souhlasu uživatele.**

## Co nikdy (jen o domě)
- Nedávej na web údaje o žijících lidech a dnešních majitelích bez souhlasu.
- Ostatní zákazy (brzda, CAPTCHA, hesla, placené služby, souběžné konverzace) jsou v `skills/rodokmen/SKILL.md`, *Co nikdy*.

## Mapa souborů a nástroje
Soubory projektu a nástroje jsou stejné jako u rodokmenu (`skills/rodokmen/SKILL.md`, *Mapa souborů projektu* a *Nástroje*),
navíc `data/domy.py` (`OBEC`, `OBEC_UDALOSTI`, domy `D`, `ISSUES`). Soubory `data/pametnici.md` (co víme od lidí)
a `data/mapy.json` (staré mapy) šablona zatím nemá, založ je podle potřeby. Nástroje jen pro dům: `cuzk_archiv.py`
(Archiv ČÚZK: `listy` = které listy stabilního katastru dům pokrývají, `rady`, `mapa` včetně `mapa relief` = stínovaný terén z laserového skenování, `export`, `lms`), `mista.py ruian|okoli|parcely`,
`pamatky.py` (Památkový katalog NPÚ; `pamatky.py uan "Obec čp"` řekne, zda dům leží na území s archeologickými nálezy), `commons.py` (staré fotky z Wikimedia Commons s licencí; ve městě `--adresa "Ulice 11" --cp N` projde i kategorie ulic a domů), `geolab.py` (vojenská mapování z Geolabu),
`elipsa.py` (označení domu na mapě), `podminky.py <adresa>` (co smí nástroj stáhnout a který obrázek smí na web; hlídá to i `slusne.py`) a `zdravi.py` (kontrola nástrojů
proti živým portálům; `--rychle`, `--jen cuzk,ruian`). Návody `reference/prameny.md` (kde co hledat podle doby), `reference/texty.md`
(psaní textů) a `reference/podminky.md`. Nástroje z `prameny.md`, které tu zatím nejsou (`mis.py`, `narp.py`, `veduty.py` …), jsou
vypsané v jejím záhlaví – u nich postupuj ručně na webu portálu. Jen ručně a jen uživatel (podmínky portálů zakazují automatizaci a snímky nesmí do výstupu): Street View s časovou osou, NCAP a Fortepan (`reference/portaly.md`). Výstup `cuzk_archiv.py mapa` počítá s `data/mapy.json`, který šablona zatím nemá.
