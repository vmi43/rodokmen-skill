# Rozhodnutí

## Porta fontium: ponechat náš postup, ne upstreamový zákaz skriptů

**Rozhodnuto 2026-11-05.** `portafontium.py` dál dotazuje portál skriptem, v rozsahu osobního bádání.

**Problém.** Upstream `dejiny-domu-skill` má v `podminky.json` pro `www.portafontium.eu` `dotazy: false`, `obrazky: false`, `vyrez: souhlas` s důvodem „firewall blokuje skripty“. Náš nástroj pracuje a upstream to pokládá za obcházení.

**Ověřeno na portálu 2026-11-05** (robots.txt a https://www.portafontium.eu/terms-of-use):
- `robots.txt`: `Crawl-delay: 10`; `Disallow: /search/`, ale náš nástroj hledá přes `/searching/register`, jiná cesta.
- Podmínky skripty nezakazují. Popisy archiválií smí k nevýdělečným účelům s citací zdroje. Snímky smí mimo portál jen podle § 92 autorského zákona (osobní potřeba, věda, výuka, s uvedením zdroje a adresy).
- Firewall skripty technicky blokuje: bez `User-Agent` vrací 403 a chybí mezilehlý certifikát.

**Varianty.**
- *Náš postup (vyhrál):* brzda 10 s podle `robots.txt` (`slusne.py`), jen osobní bádání. Důvod: podmínky skript nezakazují a uživatel chce stejné metody jako u ostatních portálů.
- *Jako upstream:* nástroj stojí, snímek ukládá uživatel ručně. Zamítnuto jako přísnější, než podmínky vyžadují.

**Vědomá výjimka.** `User-Agent: Mozilla/5.0 (rodokmen)` a doplněný certifikát GEANT TLS RSA 1 obcházejí technickou blokádu firewallu, ne podmínky. Platí jen v rámci brzdy 10 s.

**Důsledek pro `podminky.json` (skill `dum`).** U `www.portafontium.eu` stejná hodnota, jakou dělá nástroj (`dotazy` a `obrazky` povolené jen pro osobní použití), `vyrez: souhlas` a poznámka, že obrázek na veřejný web chce souhlas archivu. Skill se tak nehádá sám se sebou.

## Název skillu: `rodokmen:dum`

**Rozhodnuto 2026-11-05.** Nový skill se jmenuje `rodokmen:dum` (dějiny domu, chalupy, statku), ne `rodokmen:misto`.

**Problém.** Pracovní název „místo“ je dvojznačný: dům, nebo obec jako celek.

**Varianty.** `misto` (zamítnuto: sliboval by i obec, kterou první verze neřeší); `dum` (vyhrál: přesně říká, co skill dělá).

**Důsledek.** Skill pro místo ve smyslu obce je možný v dalekém výhledu jako samostatný skill, nyní není v plánu. Obec dnes řeší `OBEC` a `OBEC_UDALOSTI` v `data/domy.py` skillu `dum` jen jako kontext domu. Název větve `claude/rodokmen-misto-skill-4da757` zůstává, protože se nepřejmenovává.

## Rozsah první verze skillu `dum`

**Rozhodnuto 2026-11-05.** První verze obsahuje jádro a navíc `zdravi.py`.

**Jádro:** `data/domy.py`, web domu a obce, `cuzk_archiv.py`, `podminky.py` + `podminky.json`, `reference/prameny.md`, `reference/texty.md`, rozšíření `mista.py`.

**Později:** `mza.py`, `trebon.py`, `dnnt.py`, `ipr_praha.py`. Jsou vázané na jednu instituci nebo region a zvětšily by plochu k testování.

**Proč i `zdravi.py`.** Kontroluje nástroje proti živým portálům, takže včas ukáže, že portál změnil podmínky nebo začal blokovat (jako u MZA od 2. 11. 2026). Hodí se hned u jádra, které portálové nástroje používá.

## Sledování upstreamu `dejiny-domu-skill`

**Rozhodnuto 2026-11-05.** Změny upstreamu sledujeme skriptem, který stáhne jeho aktuální stav do dočasné složky a ukáže rozdíl proti našim převzatým souborům. Nic z upstreamu se neklonuje do repozitáře.

**Původ v souborech.** V hlavičce každého převzatého souboru je odkaz na původ a commit, ze kterého se přebíralo. Podle něj skript pozná, co se od té doby změnilo.

**Proč.** Bez toho se o opravách a změnách podmínek portálů v upstreamu nedozvíme, dokud je někdo nenajde ručně. Klon do repa zamítnut kvůli pravidlu neklonovat repozitáře.

**Skript.** `scripts/upstream.py` (údržbářský, do projektů uživatelů se nekopíruje; test `tests/podminky/test_upstream.py`) udělá jeden dotaz GitHub compare API od commitu z hlaviček „Původ“ do `master`, vypíše změněné soubory rozdělené na převzaté a ostatní a rozdíly převzatých uloží do dočasné složky. Nic nestahuje do repozitáře. První běh 2026-11-10: `bda6028` → `e6aff7a`, 1 commit, mění se `podminky.json`, `cuzk_archiv.py`, `prameny.md`, `podminky.md` (zatím nepřevzato).

**Rozsah přebírání (uživatel 2026-11-10).** Z upstreamu se přebírá postupně všechno, co nerozbije dřívější rozhodnutí; fronta je v `docs/todo.md`, *Přerušený běh*, položka 11. Zavrženo: přebrat jen nejmenší změnu a zbytek nechat jen v hlášení skriptu.

**Přebráno 2026-11-10, krok (a).** Z `e1cd204` jen detekce prázdného obrázku spojené vrstvy: `prazdny()` v `cuzk_archiv.py` (Pillow volitelně, bez něj False; bílý obrázek se neuloží, vypíše se `listy` a postup `rastry` → `prehled` → `export`) a odpovídající odstavec v `prameny.md`; test `tests/podminky/test_cuzk_archiv.py`. Hlavičky „Původ“ těchto dvou souborů říkají, co je z `e1cd204`, zbytek zůstává na `bda6028`. **Nepřebráno zatím:** vrstva `relief` (DMR 5G, `magick()` pomocník), řádky o Street View, NCAP a ÚAN v tabulce `prameny.md` (vázané na `pamatky.py uan` a `portaly.md`), změny `podminky.json` a `podminky.md`. Patří do kroků (c), (e). Upstream se mezitím posunul na `e1cd204` (6 commitů, 20 souborů).

**Přebráno 2026-11-10, krok (b).** `elipsa.py` z `e1cd204` (označení domu elipsou s popiskem, výstup do `zdroje/` a `vyrezy/` jako `vyrez.py`) a `tests/podminky/test_elipsa.py`. Úprava proti upstreamu: podmínky obrázku hlásí přes `podminky.hlaska_obrazku` stejně jako `vyrez.py`. Zapadá do dat bez změny: `mapy.json` nese příkaz jen jako volný text v `poznamka`, export webu a kontrola to pole nečtou. Věta o nástroji je v `prameny.md` u stabilního katastru.

**Přebráno 2026-11-10, krok (c).** Do `podminky.json` portály `archivnimapy.cuzk.gov.cz` (pravidla jako `ags.cuzk.gov.cz`, včetně výjimek pro indikační skici a letecké měřické snímky) a `geoportal.gov.cz` (jako `gis.cenia.cz`; upstream vojenská mapování nevyjímá, my ano, protože jde o tytéž podmínky CENIA). Test v `test_podminky.py`. **Odloženo na (e):** portály Street View, Mapy.com/Mapy.cz, NCAP, `geoportal.npu.cz` a řádek reliéfu DMR 5G (vázané na `portaly.md`, `pamatky.py uan` a vrstvu `relief`).

**Přebráno 2026-11-10, krok (d).** Upstreamový `kramerius.py` (e1cd204) nahradil náš dřívější stejnojmenný jednoduchý nástroj: je to jeho nadmnožina (hledání v NK včetně výstupu `found N`, na který se spoléhá `zdravi.py`, plus `--knihovna` přes Českou digitální knihovnu, `text <pid>` a `autori <uuid>` s koncem ochrany díla). Úprava: `slusne.py` se u nás zapíná importem, bez `slusne.instaluj()`. Do `podminky.json` přibyly `api.ceskadigitalniknihovna.cz`, `www.ceskadigitalniknihovna.cz` (bez odkazu na `veduty.py`, který nemáme), `kramerius.cuni.cz` a `kramerius.vkol.cz` s textem `jinak` o `kramerius.py`; do `podminky.md` řádky ČDK a Krameria UK/VKOL, do `portaly.md` použití. Test `tests/podminky/test_kramerius.py` 4/4. Živě ověřeno jedním dotazem do NK a jedním do ČDK; `text` a `autori` živě neověřeny (parsování kryje test).

**Postup stahování.** V sandboxu `gh` nejde, funguje `curl` s povolenými doménami `api.github.com` a `raw.githubusercontent.com` (soubory s `[...]` v názvu s `curl -g`).

## Sdílená složka `shared/` v kořeni repozitáře

**Rozhodnuto 2026-11-05.** Společné `tools/`, `reference/` a `template/` se přesunou ze `skills/rodokmen/` do `shared/` v kořeni repozitáře. `skills/rodokmen/` i `skills/dum/` pak obsahují jen `SKILL.md` (a případně `VERZE`). V textu `SKILL.md` se odkazuje přes `${CLAUDE_PLUGIN_ROOT}/shared/...`.

**Problém.** Dva skills mají sdílet nástroje a šablonu. Verze „vše v `rodokmen`, `dum` jen rozdíl“ se špatně spravuje: u každého nového nástroje by se řešilo, kam patří.

**Varianty.**
- *`shared/` v kořeni (vyhrál):* nespoléhá na nic neověřeného; instalace přes `/plugin` funguje (`marketplace.json` má `"source": "./"`).
- *`skills/shared/`:* zamítnuto. Dokumentace Claude Code neříká, zda se složka bez `SKILL.md` ve `skills/` ignoruje, a nepopisuje ani relativní cestu `../shared` z těla `SKILL.md`.
- *Vše ve `skills/rodokmen`, `dum` jen rozdíl:* zamítnuto uživatelem.

**Ověřeno v dokumentaci (2026-11-05, code.claude.com/docs).** Osobní skills se hledají jen jako `~/.claude/skills/<skill>/SKILL.md`; klon repozitáře v `~/.claude/skills/` se nenačte. `${CLAUDE_PLUGIN_ROOT}` se dosazuje v textu skillu.

**Důsledek.** Ruční instalace (README, Varianta B) znamená celý repozitář jako plugin, ne kopii jedné podsložky. Před vydáním ověřit, že `claude --plugin-dir` s tímto repozitářem skills načte.

## Licence a převzaté soubory z `dejiny-domu-skill`

**Rozhodnuto 2026-11-05.** Kód a návody se přebírají s uvedením původu v hlavičce souboru (odkaz a commit). Upstreamový `playbook.md` se nepřebírá: tělo je shodné s naším, liší se jen úvodní poznámka (diff 2026-11-05).

## Jedna společná `VERZE` v `shared/VERZE`

**Rozhodnuto 2026-11-05.** Skills `rodokmen` a `dum` mají jednu verzi: `shared/VERZE` (dřív `skills/rodokmen/VERZE`), shodnou s `plugin.json`.

**Proč.** Plugin má stejně jedno číslo a oba skills sdílí `tools/` i `template/`. Dvě verze by se rozcházely a `novy_projekt.py` si pamatuje jen jedno číslo v `.skill_verze`.

**Důsledek.** `CLAUDE.md` repa a `novy_projekt.py` čtou `shared/VERZE`. Číslo se dál zvedá na stejných třech místech.

## Šablona domu: `shared/template/dum/` a pole `os` (vazba domu na osobu)

**Rozhodnuto 2026-11-10.** Datový soubor domu je `shared/template/dum/data/domy.py`, mimo `shared/template/data/`, takže ho `novy_projekt.py` nekopíruje do každého rodokmenového projektu. Do projektu ho dá až volba pro dům (krok (c) v `docs/todo.md`).

**Vazba osoba ↔ dům.** Držitel a obyvatel v `domy.py` mají nepovinné pole `os` = číslo téže osoby v `data/osoby.py`. Jen jedním směrem (dům → osoba), aby vazba byla na jednom místě. Upstream má vazbu jen textem v `note`; `note` zůstává pro osoby mimo přímou linii.

**Kontrola `os`.** Hotovo 2026-11-10 v `kontrola.py` (funkce `kontrola_domu`, test `tests/kontrola/test_domy.py`): `os` musí být celé číslo a osoba musí být v `osoby.py`; bez `osoby.py` (projekt jen s domem) je každé `os` chyba.

**Skill `dum` neopisuje rodokmen.** Brzda, pomocníci, technické pasti a „co nikdy“ jsou jen v `skills/rodokmen/SKILL.md`; `skills/dum/SKILL.md` na ně odkazuje (pravidlo jednoho místa). Cena: `dum` vyžaduje načtení `rodokmen/SKILL.md`, ověřit při prvním skutečném použití.

## Díl 2 skillu `dum`: co se z upstreamu převzalo a jak

**Rozhodnuto 2026-11-10** (commit upstreamu, ze kterého se přebíralo: `bda6028`).

**Tabulka podmínek je zúžená.** `shared/tools/podminky.json` má 20 portálů, které naše nástroje používají (upstream ~80, včetně portálů nástrojů, které tu nejsou). Ostatní portály se doplní spolu s nástrojem. Neznámý portál `podminky.py` hlásí jako „není v tabulce, ověř podmínky“, nepouští ho tiše.

**`slusne.py` má přednost před `podminky.json`.** `pockej()` nejdřív použije dosavadní `ZAKAZ` (MZA, Třeboň, SOA Praha, actapublica.eu), pak teprve tabulku. Důvod: `ZAKAZ` je přísnější (u MZA smí jen hledání knih) a je ověřené ve starších verzích. Tabulka musí s `ZAKAZ` souhlasit: SOA Praha `dotazy: false` (upstream má `true` podle zákazu jen pro ClaudeBota, ale náš `slusne.py` od 2. 11. 2026 hlásí robots.txt `User-agent: rodokmen / Disallow: /` a 403; sporné, neověřeno znovu), Porta fontium `dotazy` i `obrazky: true` podle rozhodnutí výše.

**Neověřený rozpor s upstreamem (SOA Praha).** Upstream k 8. 11. 2026 píše, že robots.txt zakazuje ClaudeBota, ale Claude-User ne, a nástroj pouští. Náš `slusne.py` ho blokuje podle zjištění z 2. 11. 2026. Nepřepisováno, dokud někdo neověří aktuální `robots.txt` na eBadatelně; zapsáno v `docs/todo.md`.

**`cuzk_archiv.py` bez `platnost.py`.** Z upstreamového `platnost.py` (společné kontroly pro `kontrola.py` a `export_web.py`) se převzala jen funkce `vyrez_sjtsk`, a ta je přímo v `cuzk_archiv.py`. Ostatní helpery se přebírají, až je web domu bude potřebovat. Příkaz `mapa` vypisuje „do `data/mapy.json`“, ale šablona `mapy.json` nemá (přijde s webem domu).

**`mista.py` rozšířen vedle Mapy.com, ne nahrazen.** Přibyly `ruian`, `okoli`, `parcely` (RÚIAN, bez klíče). Upstreamový `mista.py` je jiný nástroj (Nominatim, `hledej`, `pridej` do `mista.json` jinak) a přebírat se nebude; `hledej` proto u nás není a texty na něj neodkazují.

**`zdravi.py` jen pro nástroje, které tu jsou** (ARON, Porta fontium, AHMP, policejní přihlášky, ČÚZK, RÚIAN, Kramerius, ANNO a dostupnost tří obrázkových serverů). Třeboň, SOA Praha a MZA v něm nejsou, protože je `slusne.py` stejně zastaví. Ověřeno živě jen `--jen cuzk,ruian` (4 kontroly OK); zbytek jsem nepouštěl, aby se nezatěžovaly portály (pravidlo o rozsahu testů).

**Návody.** `reference/prameny.md` a `texty.md` jsou přebrané beze změny obsahu s hlavičkou původu; `prameny.md` v hlavičce vypisuje nástroje, které odkazuje a tu nejsou. `reference/podminky.md` je zúžená na portály z tabulky.

## Web domu: volitelná vrstva v naší šabloně (2026-11-10)

**Rozhodnuto uživatelem.** Stránky domu a obce (`obec`, `domy`, `dum/[slug]`) jsou volitelná vrstva v `shared/template/web`, zapnutá přítomností `data/domy.py`. Zavrženo: samostatná šablona `web-dum` (dva weby ke správě a aktualizaci) a doslovné převzetí upstreamového webu (přepsalo by náš `Base`, `index` a styl).

**Jak je to provedeno.** Export domů je samostatný modul `shared/tools/domy_web.py` (+ `platnost.py` s validací odkazů a poloh, původ bda6028), rodokmenový export zůstává v `export_web.py`. `site.json` dostane klíče `village`, `houses`, `maps`, `mapGroups`, `housePlaces`, `houseStats`; místa z `mista.json` jdou do `housePlaces`, aby se nepletla s místy rodokmenu (`places`). Projekt bez `osoby.py` se vyexportuje i sestaví (prázdný `fan.svg`, nabídka bez rodokmenových stránek); běžný projekt dostane `domy.py` kopií šablony. Domy mají vlastní styl `styles/domy.css` načítaný jen z jejich stránek. Obrázky, které portál bez souhlasu nedovoluje zveřejnit, se na otevřený web nekopírují (`podminky.posoud_obrazek`).

**Vynecháno zatím:** `Doplnky` (uživatelské doplňky z upstreamu). Příběhy domu jsou doplněné níže (*Další příběhy*). Mapa a staré mapy jsou doplněné níže (*Mapa domu a staré mapy*), `Gallery` vynechána.

## Založení projektu s domem: `--dum` a `--jen-dum` (2026-11-10)

**Rozhodnuto.** `novy_projekt.py` má dvě volby: `--dum` přidá k projektu `data/domy.py` ze `shared/template/dum/` (rodokmen zůstává), `--jen-dum` navíc nezaloží `data/osoby.py`, takže web má jen obec a domy. Volba jde spustit i dodatečně na existující projekt a upravený `domy.py` nepřepíše (kopíruje se jen chybějící soubor).

**Zavrženo.** Jediná volba `--dum` bez možnosti vynechat rodokmen: kostra `osoby.py` by na webu dělala prázdný rodokmen. Dvojice `--dum` + `--bez-rodokmenu`: dvě volby, z nichž jedna nedává smysl samostatně. `--jen-dum` s `--ukazka` skončí chybou, protože ukázka je rodokmen Novákových (použije se `--dum --ukazka`).

**Ověřeno.** `tests/web/test_novy_projekt_dum.py shared` 9/9; živě `npm install` a `npm run build` rc=0 s ukázkou a čtyřmi domy, z toho dva se stejným čp. v různých částech obce (stránky `dum/1`, `dum/2`, `dum/horni-3`, `dum/dolni-3`).

**Známé zbytky.** Bez `domy.py` se stránky `/domy/` a `/obec/` vyrobí jako prázdné a nelinkované (Astro neumí vynechat statickou stránku); nabídka je skrytá. Případně řešit později přesunem do dynamické cesty.

## Mapa domu a staré mapy (2026-11-10)

**Převzato z upstreamu** (`dejiny-domu-skill`, commit bda6028; původ je v hlavičkách souborů): `components/HouseMap.astro` (Leaflet, OpenStreetMap, přepínač ortofota a katastru ČÚZK), `lib/places.js` (druhy bodů, vzdálenost od návsi), `pages/mapy.astro` (porovnání map vedle sebe nebo prolnutím, přehled všech map). Úpravy: v naší `data.js` se místa z `mista.json` jmenují `housePlaces`; styl porovnání map jsme napsali sami do `styles/domy.css` (upstream ho v souboru, který jsme četli, nemá).

**Kde se mapa ukazuje.** Stránka `obec` (celá mapa, když je poloha obce, domu nebo místa), stránka domu s `lat`/`lon` (zaostřeno na dům), odkaz `Staré mapy` v nabídce a na stránce obce jen když jsou v `mapy.json` mapy.

**Zavrženo.** `Gallery`: stránka domu už ukazuje fotky a dokumenty mřížkou `.docs`, druhá galerie by byla duplicita; vrátit, až bude potřeba skupinová galerie s dvojicemi „tehdy – dnes“.

**Ověřeno.** `npm run build` rc=0 s ukázkou, čtyřmi domy a dvěma mapami ve skupině; vznikly `/mapy/`, `/obec/` a `/dum/*` s mapou, odkaz v nabídce a na obci je. **Neověřeno:** vzhled a chování mapy v prohlížeči (Leaflet běží až v prohlížeči), prolínání map. **Pozor:** `housePlaces` vychází z celého `mista.json`; v projektu s rodokmenem se na mapě domů ukážou i místa předků jako „Další místa“. Rozhodnout, až se to ukáže na skutečném projektu.

## Další příběhy: `pribeh_<slug>.md` a `pribehy/[slug]` (2026-11-10)

**Rozhodnuto.** Převzat upstreamový mechanismus: `data/pribeh_<slug>.md` → `/pribehy/<slug>/`, frontmatter `title`, `lead`, `poradi`, `obdobi`; seznam jde do `site.json` → `config.dalsiPribehy`, texty do `src/generated/pribehy/` (osiřelé se při exportu mažou). Slug `cp<adresa domu>` přidá na stránku domu tlačítko „Přečíst příběh domu“, `obec` tlačítko na stránku obce. Hlavní příběh `pribeh.md` zůstává; `/pribehy/` pod ním vypíše další příběhy, a když `pribeh.md` není, ukáže jen seznam (`config.maHlavniPribeh`). Odkazy `/dum/…` v příbězích kontroluje export jako u `pribeh.md`.

**Zavrženo.** Upstreamový rozcestník s kartami a galerií (`obrazek`, `skupina`, `par`) – galerii jsme vynechali už dřív a kvůli obrázkům by bylo nutné napojit `posoud_obrazek`. `Doplnky` zůstávají vynechané. Příběh uvedený v `dum[slug]` z pole `pribeh` v `domy.py` zůstává jako krátký text přímo na stránce domu; delší příběh patří do `pribeh_cp<adresa>.md`.

**Ověřeno.** `tests/web/test_export_domy.py shared` 13/13; živě `npm install` a `npm run build` rc=0 s ukázkou, domem a příběhy `cp1` a `obec` (tlačítka na `dum/1` a `obec`, seznam na `/pribehy/`). **Neověřeno:** vzhled v prohlížeči.

## Přebírání upstreamu, krok (e): `commons.py`, `geolab.py`, `pamatky.py` (2026-11-10)

Upstream je teď na `32bef07` (9 commitů za naším základem `bda6028`). Přebrané soubory a pomocné moduly `vzdalenost.py` a `nazvy.py`
(oba krátké, jinde u nás nejsou) mají v hlavičce původ a commit `32bef07`; jedinou úpravou je `import slusne` místo
`slusne.instaluj()` (u nás se brzda zapíná importem). Do `podminky.json` přibylo 13 portálů, které tyto nástroje používají
(Commons, Wikidata, Geolab, Památkový katalog, geoportál a MIS NPÚ) a portály, které nástroje zakazují (Google, Mapy.com, Mapy.cz,
NCAP). Zbylých 44 upstreamových portálů se **nepřebralo**, protože patří nástrojům, které tu nejsou (`mza.py`, `trebon.py`, `dnnt.py`,
`ipr_praha.py`, `esbirky`, `ddb`…); tabulka má podle svého záhlaví obsahovat jen portály, které naše nástroje používají.
Odkazy na `mis.py` a `ortofota.py` v převzatých textech jsme přepsali na existující nástroje. Nepřebral se `tests/test_nastroje.py` (1 228 řádků pro
nástroje, které tu nejsou); z něj jsou jen testy `zapis.py`.

**`zapis.py` převzat celý** (náš byl starší podmnožina): zámek mezi procesy (`pracovni/.zamky/`), příkaz `denik` s číslem řádku
přiděleným pod zámkem, soubory `mapy` a `web`, odmítnutí neplatného Unicode a běhu ze složky skillu. Upstream tvrdí, že přes
`zapis()` zapisují i ostatní nástroje; u nás to neplatí (`ebadatelna.py`, `mista.py` zapisují po svém, bez zámku), věta v záhlaví je
opravená. Sjednotit je otevřená možnost, ne rozhodnutí.


## `User-Agent` pro Wikimedii (2026-11-10)

`commons.py` se Wikimedii představuje vlastním `UA_WIKIMEDIA`: `rodokmen-skill/<verze ze shared/VERZE> (https://github.com/vmi43/rodokmen-skill; …)`. Wikimedia chce od klientů API identifikaci s kontaktem a bez ní vrací 403 (`www.wikidata.org` ho dal 10. 11. 2026). Kontaktem je adresa repozitáře, **ne osobní e-mail** (rozhodl uživatel 10. 11. 2026, návrh potvrzen).
- Zavrženo: změnit společné `slusne.UA`. Některé archivy odmítají cokoli jiného než „Mozilla/5.0 (…)“ a SOA Třeboň blokuje jméno „rodokmen“, takže by změna rozbila jiné portály. UA se mění jen v `commons.py`, ostatní nástroje zůstávají na `slusne.UA`.
- Oprava dřívějšího zápisu: 403 nedostal „Mozilla/5.0 (rodokmen)“. `commons.py` poslal výchozí UA urllibu a `slusne.UA` do `urllib` nejde.
- Test: `tests/podminky/test_commons.py` (`UserAgentTest`, bez e-mailu, s verzí a adresou, `api()` ho opravdu posílá), 15/15.

## Přebírání upstreamu, krok (e) dokončen: `mista.py`, `relief`, `--bez-webu`, ruční portály (2026-11-10)

Porovnáno proti `32bef07` (upstream je `vzoha/dejiny-domu-skill`; `sarsonj` je jen náš remote `upstream`, ale soubory z něj `raw` nevrací). `scripts/upstream.py` se na `api.github.com` opakovaně sekl (`IncompleteRead`), proto se soubory brali přímo přes `curl -g`.
- **`mista.py`:** funkce společné s upstreamem jsou shodné. Přebráno jen `odkazy_panorama` a jeho výpis v `ruian` (Street View a Mapy.com na polohu domu, prochází jen uživatel). **Nepřebráno `obec_nebo_poloha` a `POLOHA`**: v upstreamu je nikdo nevolá. `hledej` a Nominatim zůstávají nepřevzaté (viz *Díl 2*).
- **`cuzk_archiv.py`:** vrstva `relief` (DMR 5G, CC BY 4.0, smí do PDF i na web) a pomocník `magick()` (náš duplicitní blok v `adresy()` ho teď volá).
- **`novy_projekt.py --bez-webu`:** web se nezaloží ani neaktualizuje; další běh bez volby ho doplní, běh s volbou na projekt s webem ho nesmaže.
- **`prameny.md`:** řádky Street View, NCAP, Fortepan, `pamatky.py uan` v řádku AMČR a odstavec o reliéfu. **`portaly.md`:** sekce Street View, NCAP, Fortepan (beze změn, s původem v hlavičce); ostatní domovní portály z upstreamového `portaly.md` (veduty, Ostrava, Europeana…) se nepřebírají, jejich přehled drží `prameny.md`.
- **Už bylo hotové:** `data.md` (věta o `zapis.py denik`), `SKILL.md` tabulka u `zapis.py denik`, `podminky.md` řádek reliéfu.
- Testy: `test_mista.py` (2), `ReliefTest` v `test_cuzk_archiv.py` (6 celkem), `--bez-webu` ve `test_novy_projekt_dum.py` (12 z 12); aktualizace, kontrola, export domů a ostatní `tests/podminky` rc=0.

## Přebírání upstreamu, krok (f): `slusne.py` a SOA Praha (2026-11-11)

- **Rozdíl upstreamu:** `slusne.py` se mezi `bda6028` a `e1cd204` změnil jediným řádkem (`LIMITY["kramerius.vkol.cz"] = (5.0, 0.5)`, VKOL dal 403 po 4 rychlých dotazech na OCR). **Nepřebráno:** naše nástroje na `kramerius.vkol.cz` přímo nesmí (`podminky.json`, VKOL jde jen přes Českou digitální knihovnu v `kramerius.py`), takže limit pro tento web by se nikdy neuplatnil. Soubor zůstává bez změny a bez hlavičky původu.
- **SOA Praha ověřeno 2026-11-11:** `https://ebadatelna.soapraha.cz/robots.txt` (HTTP 200) dál obsahuje `User-agent: rodokmen` / `Disallow: /` (vedle ClaudeBot, GPTBot, Amazonbot; ostatní roboty mají zakázané jen `/d/` a `/a/`). Upstreamové tvrzení, že zakázán je jen ClaudeBot, se našeho nástroje netýká, protože se představuje jako `rodokmen`. **`ZAKAZ["soapraha.cz"]` v `slusne.py` i řádek v `podminky.json` zůstávají beze změny**, `ebadatelna.py` dál stojí; stahuje jen prohlížeč uživatele.
- Ověřilo se jedním `curl` na `robots.txt` a stažením dvou verzí upstreamového `slusne.py` ze `raw.githubusercontent.com`; žádný dotaz na eBadatelnu mimo `robots.txt`.

## Živé ověření převzatých nástrojů a `strop_dlazdic` (2026-11-11)

- Mimo sandbox prošly `commons.py`, `pamatky.py uan` a `geolab.py export`. V sandboxu se větší odpovědi přerušují (`IncompleteRead`), proto se živé ověření pouští mimo něj, po schválení.
- `geolab.py` (převzatý v kroku (e)) volal `slusne.strop_dlazdic`, kterou náš přepracovaný `slusne.py` neměl; export padal na `AttributeError`. Funkce a `MAX_DLAZDIC = 3000` jsou doplněné z upstreamu (`bda6028`), beze změny našeho `ZAKAZ`, brzdy a mezipaměti. `tests/podminky/test_geolab.py` kontroluje přes `ast`, že každé volání `slusne.<jméno>` v `shared/tools/` existuje; poučení: u převzatého nástroje ověřit i funkce, které volá z našich sdílených modulů, ne jen jeho vlastní běh.

## Poznámky z uživatelova projektu: co se zapracovalo a co ne (2026-11-11)

**Rozhodnuto s uživatelem:** poznámky z projektu (`poznamky_pro_skill.md`) se zapracují před přebíráním upstreamu `rodokmen-skill`; pořadí: opravy kódu, návody, pak větší nástroje zvlášť. Víc než třetina poznámek už ve skillu byla (`SAME` v exportu a vějíři, `mista.py nova`, kmotři, `Containerfile` na UBI, kontrola svazku v `kontrola.py`, `ramecek.py --vyrez`, `upload: manual`, sňatek ve farnosti nevěsty).

**Odchylky od návrhů v poznámkách.** (1) `--rozsah` je podpříkaz `aron_img.py <apu> rozsah <od-do>`, ne přepínač, aby seděl k ostatním podpříkazům; stejný nástroj pro `ebadatelna.py` se nedělá, protože ho archiv od 2. 11. 2026 zakazuje. (2) Počet snímků u svazků v `aron_search.py` jde jen přes `--sken` (jeden dotaz na svazek, nejvýš 40), protože výpis ARON počet skenů neobsahuje. (3) Klíč archivalií z eBadatelny je `ebad_a_<archivalieId>` (jak ho zapisuje `ebadatelna.py a-svazek`); `zarad.py` ale použije `archivalie_<id>`, je-li už ve `svazky.json` (tvar z uživatelova projektu), takže existující projekt se nerozbije. (4) Poznámka o hlídači sítě se ověřila: `hlidac_site.py` kontroluje spuštěný příkaz, text `curl` v `grep` ani v heredocu ho nezastaví; návod to jen říká. (5) Zkušenost s aliasy `.2` a `.3` v `tests/brzda/README.md` je uvedená jako zkušenost uživatele, ne jako ověřená u nás (test na `.5` jsme nepustili).

**Nepřevzato:** příručka písma a úprava obrazu (uživatel ji jen zkoušel, bez výsledku); Kraken a cizí AI modely na kurent jsou v `matriky.md` jako negativní zkušenost.

**`zarad.py` (2026-11-11).** Nástroj na zařazení ruční dávky (`shared/tools/zarad.py`, test `tests/podminky/test_zarad.py`, 7 případů). Náhled je výchozí, změny jen s `--proved`; nic nemaže (strojové kopie jen vypíše), rozpory (počet snímků, název × `svazky.json`, klíč ve jménu složky) složku zastaví, `--ignoruj-pocet` povolí jen rozpor v počtu. Zapisuje do `svazky.json` přes `zapis.py --sloucit`, takže stará pole záznamu zůstanou. Nevyzkoušeno na živých `obsah.txt` mimo vzorky z uživatelova projektu (eBadatelna archiválie a matrika, ARON); u ARON `obsah.txt` počet snímků neuvádí, takže se kontroluje jen proti `svazky.json`. Pomůcka NAD 190 a dávkové stahování zůstávají v `docs/todo.md`.

**`pomucka.py` (2026-11-11).** Nástroj na Archivní pomůcku NAD 190: `rozbor <pdf>` a `hledej <obec> [N|O|Z] [rok] [--vse]`, test `tests/podminky/test_pomucka.py` (4 případy, bez PDF). Vychází z rozboru uživatele (`pomucka_parse.py`, `hledej_pomucku.py`), ale odkazy bere přes `qpdf --json` v pořadí stránek a anotací; pořadí objektů v `qpdf --qdf` pořadí v textu neodpovídá (první pokus selhal na 27. odkazu, kontrola dvojic ARON a ZIP to chytila). Varianta (a) bez stahování: PDF se stahuje ručně, protože přímá adresa souboru z dostupných podkladů není známá a stahování by šlo přes brzdu; hledání je lokální. Výstup shodný s uživatelovým JSON (14 189 knih, 12 911 odkazů, `==`). `qpdf` a `pdftotext` jsou závislost, nástroj bez nich skončí s návodem k instalaci. Dávkové stahování zůstává v `docs/todo.md`.

## Přebírání sarsonj/rodokmen-skill 0.10.0 (2026-11-11)

Základ `bc6cd33` (0.8.2), upstream `0fb0c03` (0.10.0), 64 souborů. Rozhodnuto s uživatelem po rozboru po souborech:
- **Cloudflare přebrat jako výchozí zveřejnění webu**; Netlify a náš `Containerfile` na UBI zůstanou jako další možnosti, upstreamový nginx a Docker se nepřebírají. Důvod: Netlify zdarma vystačí asi na 20 nasazení měsíčně (neověřeno).
- **`verze.py` převzít s úpravou** na `vmi43/rodokmen-skill`, id pluginu `rodokmen@rodokmen` a cestu `shared/VERZE`; bez úpravy by hlásil novou verzi podle cizího repozitáře.
- **`playbook.md` smazat, nahrazuje ho `metodika.md`** (česky, MIT; zmizí výjimka v `LICENSE`, odkazy na 7 místech se převedou). Stopa: playbook se vědomě nepřebíral ani neudržoval dál, protože ho upstream nahradil metodikou.
- **`SKILL.md` zeštíhlit**: Fáze 0 do `instalace.md`, import stromu do `data.md`; naše přidané pasáže (`zarad.py`, `pomucka.py`, brzda, dům) zůstanou.
- **Číslo vydání 0.9.1** (uživatel zvolil proti doporučení 0.10.0): plynulá řada našich verzí; upstreamová čísla 0.9.0 a 0.10.0 mají jiný obsah, v `CHANGELOG.md` uvést, které upstreamové verze obsahuje.
- **Ostrý výřez indikační skici v `portaly.md` nepřebírat** (upstream ho stahuje přes `fetch` ve stránce, mimo brzdu); odkázat na `cuzk_archiv.py`. Opravu čtení barev čísel převzít (rozpor `portaly.md:555` × `prameny.md:191`).

### Krok 2 přebírání: `verze.py` a pojistka verze (2026-11-11)

- **`shared/tools/verze.py` převzat a zjednodušen.** Dotazuje se na `vmi43/rodokmen-skill`, hledá plugin `rodokmen@rodokmen` a jeho složku `shared/`. **Větev „ručně nakopírovaný skill v `~/.claude/skills/rodokmen`“ je vypuštěna**: po přesunu do `shared/` takto nainstalovaný skill nefunguje (viz README, varianta B), takže nová verze se vždy radí přes `claude plugin update rodokmen@rodokmen`. Stopa: upstream tuto větev a test k ní má.
- **`novy_projekt.py`**: `_python_windows()` vrací vždy `sys.executable`; `nastaveni()` čte JSON s BOM (`utf-8-sig`); `zkontroluj_verzi()` odmítne aktualizovat projekt novější než skill.
- **Testy**: `tests/verze/test_verze.py` (20/20, bez případu ručního skillu), `test_hlidac.py` 83/83 po sloučení upstreamových případů (`git merge-file`), `test_hook_windows.py` 3/3.
- **`SKILL.md` ještě `verze.py` nevolá** – přijde v kroku 5 (zeštíhlení), spolu s textem, kdy ho Claude spouští na začátku konverzace.

### Krok 3 přebírání: Cloudflare, oprava nginx a `podminky.json` (2026-11-11)

- **Cloudflare převzat** (`worker.sablona.js`, `scripts/nasadit_cloudflare.mjs`, `scripts/npx.mjs`, změny `overit.mjs`, `package.json` skript `nasadit-cloudflare`, `.gitignore`, `.dockerignore`, `cloudflare_files()` v `export_web.py`, `tests/web/test_cloudflare.py` 34/34, `test_overit.py` 13/13). Netlify i `Containerfile` zůstávají. `export_web.py` se slučoval `git merge-file` (dva střety, vyřešeno: náš `os.path.exists(osoby.py)` s `utf-8-sig`, upstreamová regulární výrazová oprava dvojího `default`); převzaly se tím i další drobné opravy upstreamu v něm (BOM, číselná odpověď, zástupná matka, shodné názvy rodů, `SAME` bez cíle).
- **Nginx: upstreamové soubory se nepřebraly** (`Dockerfile`, `nginx.sablona.conf` do `conf.d`), **jediná oprava ano**: do naší šablony `map_hash_bucket_size 128;`. Ověřeno v `ubi9/nginx-126` přes Podman: bez řádku `nginx -t` selže („could not build map_hash“ u 64znakového otisku), s ním projde. Chyba tedy v kontejneru s ochranou odpovědí existovala. `tests/web/test_nginx.py` převeden na Podman/UBI (10/10).
- **Nalezená vlastní chyba vydání 0.9.0:** `novy_projekt.py` kopíroval do `tools/` jen `.py` a `.sh`, takže `podminky.json` v projektu chyběl a `podminky.py` (a tím `slusne.pockej`) zastavil každé stahování a export otevřeného webu s „Tabulka podmínek chybí“. Opraveno seznamem `DATA_NASTROJU`; nový případ 22 v `test_aktualizace.py` (22/22). Existující projekty se opraví aktualizací (`novy_projekt.py` na stejnou složku). Patří do `CHANGELOG.md` 0.9.1 jako oprava.
- **Neověřeno:** skutečné nasazení na účet Cloudflare (potřebuje přihlášení uživatele), vzhled webu v prohlížeči.

### Krok 4 přebírání sarsonj/rodokmen-skill: `playbook.md` → `metodika.md` (2026-11-11)

- **`shared/reference/playbook.md` smazán, nahradila ho česká `shared/reference/metodika.md`** převzatá beze změny z `upstream/HEAD` (`0fb0c03`, MIT). Zmizela výjimka z licence v `LICENSE` a v `README.md` (strom souborů, odstavec Licence).
- **Stopa:** playbook byl anglická rešeršní zpráva bez uvedeného autora (stav 2026-10-09), vědomě se nepřebíral ani neudržoval dál; vrátit by se mohl omylem z upstreamu `dejiny-domu-skill`, který ho ještě má.
- **Odkazy převedeny ručně, ne slepě:** `portaly.md` a `matriky.md` (§2 → kapitola Prameny mimo ČR), `skills/rodokmen/SKILL.md`, `skills/dum/SKILL.md`. Věta v `matriky.md` „Pomocníci a OCR/AI čtou písmo chybně (`playbook.md` §1 bod 10)“ zůstala bez odkazu, protože `metodika.md` to netvrdí.

### Krok 5 přebírání sarsonj/rodokmen-skill: zeštíhlení `SKILL.md` (2026-11-11)

- **Fáze 0 přesunuta do `shared/reference/instalace.md`** (základ upstream `0fb0c03`, `SKILL_DIR` → `SHARED_DIR`). Naše doplňky zůstaly v návodu: `--bez-webu`, výpis „NEZAPSÁNO“ při sandboxu a pravidlo, že `git` v sandboxu nesmí do `.git`. V `SKILL.md` zbyl odstavec s odkazem a zkratkou pro Windows.
- **Import rodinného stromu přesunut do `data.md`** (nová sekce „Import rodinného stromu (Fáze 1)“, text upstreamu); ve Fázi 1 zůstal jen odkaz.
- **Na začátku konverzace se volá `verze.py`** (dosud ho `SKILL.md` nevolal): výsledky `NOVA_VERZE_SKILLU`, `PROJEKT_NOVEJSI`, `SKILL_NEZJISTEN`, `AKTUALIZUJ_PROJEKT`; náš text o `--bez-webu` a hlídači zůstal. Záložní cesta přes `slusne.py`, když hlídač kontrolu zamítne.
- **Výsledná velikost `SKILL.md` je 34 KB** (bylo 39,8 KB, upstream 23 KB). Dál se nezkracuje: zbytek jsou naše pasáže (`zarad.py`, `pomucka.py`, brzda, pomocníci, dům), které upstream nemá.
- **Neověřeno:** že Claude podle zkráceného `SKILL.md` opravdu otevře `instalace.md` při zakládání projektu (chce zkoušku v živé session).

### Krok 6 přebírání sarsonj/rodokmen-skill: README, kontrola, zapis, overit, portaly (2026-11-11)

- **`kontrola.py`** (sloučeno ručně, tři střety): `--help`, čtení dat s BOM (`utf-8-sig`), nová upozornění (boční příbuzný bez textu, dokument bez popisu), chyby (alias `SAME` na zástupnou osobu, dva rody se stejným názvem). Naše `jen_dum` a import `podminky` zůstaly. Testy `tests/kontrola/*` 65/65 a 9/9.
- **`zapis.py`: jen podpříkaz `odkaz`** (přidá klíč zápisu do `r` u osoby nebo bočního příbuzného, zbytek `osoby.py` zůstane doslova, před zápisem se ověří, že se změnil jen ten seznam) a čtení vstupu v UTF-8. Naše `denik`, zámek a `--sloucit` zůstaly. Přibyly čtyři testy `TestOdkaz` v `tests/podminky/test_zapis.py` (upstream test nemá), 21 testů celkem. `SKILL.md` ho volá ve Fázi 2 (krok 6 zápisu), v pravidlech zápisu a v tabulce nástrojů.
- **`overit.py`: naše druhá nápověda smazána**, platí upstreamová na začátku souboru. Vedlejší důsledek: `overit.py <snímek> <výřez> --kontrast` bez prefixu (tři argumenty včetně přepínače) projde kontrolou počtu a spadne na rozbalení, místo aby vypsal nápovědu. Vědomě přijato.
- **`portaly.md`:** převzaty `zapis.py svazky` místo „ručně“, MZA (403 po 45–60 snímcích, vestavěný prohlížeč Claude desktop nepoužívat, 410 = vypršel token), pozemkové knihy Třeboň a Opava, pauza 5 s a zákaz smyček na pozadí, oprava čtení barev indikační skici. **Nepřevzat ostrý výřez skici** (`fetch` ve stránce mimo brzdu): odkaz na `cuzk_archiv.py export`. Z věty o skice vypadlo „stahování je placené“: nešlo ověřit a odporovalo `cuzk_archiv.py`, který listy stahuje.
- **`README.md`:** Cloudflare jako výchozí zveřejnění (4 místa) a strom `reference/`. **Číslo verze zůstalo 0.9.0 až do kroku 7.**
- **Neověřeno:** `tests/web/test_overit.py` se nespouštěl (měnil se v kroku 3); tvrzení o MZA (403, pozemkové knihy Třeboň a Opava) jsou z upstreamu, neověřeno na živých archivech.

## Krok 7 přebírání upstreamu: ověření právních tvrzení (2026-11-13)

- **§ 25b zákona 301/2000 Sb. doložen** čtením textu na zakonyprolidi.cz/cs/2000-301 (znění k 1. 1. 2025): zápis starší 100 / 75 / 30 let vydá úřad fyzické osobě, rodina je definována v § 8a odst. 6, mladší zápisy podle § 25 odst. 1. Převzato do `matriky.md` včetně rodiny a doslovného výpisu.
- **Chyba v upstreamu i v našem textu opravena:** do archivu jde kniha úmrtí po 75 letech od posledního zápisu (§ 23), ne po 30. „30“ je lhůta přístupu u úřadu (§ 25b). Opraveno v `matriky.md`, `SKILL.md`, `README.md`, `ged_import.py`. Upstream to dál tvrdí chybně.
- **„Lhůta běží u každého zápisu zvlášť“** zákon výslovně neříká; plyne z formulace „od provedení dotčeného zápisu“ (úsudek, ne citace).
- **Zahraniční lhůty (SK, AT, DE, PL, HU) neověřeny** primárními zdroji; v `metodika.md` označeno. Důvod: mimo hlavní oblast skillu, ověření pěti zákonů by bylo samostatná práce. Ověřit, až je někdo bude potřebovat.
- Tvrzení o MZA a pozemkových knihách Třeboně a Opavy v `portaly.md` zůstávají z upstreamu neověřená.

## Přebírání vzoha/dejiny-domu-skill 32bef07 → 5c1715b (2026-11-13)

- **Co se převzalo:** `reference/prameny.md` (sekce *Čísla domů*, indikační skica „N° X“, Heimatbücher, Brno, elipsa na všech mapách, farní hranice Gundackera), nové `tools/heimatbuch.py` (katalog DNB) a `tools/brno_encyklopedie.py` s testy `tests/podminky/test_heimatbuch.py` (3) a `test_brno_encyklopedie.py` (2), 11 portálů v `podminky.json` a řádky v `podminky.md`, kontroly v `zdravi.py`, sekce v `portaly.md` (Encyklopedie měst, Místní fotoarchivy, Slavné vily, Heimatbücher, Bundesarchiv, ÖNB/Polona/SBC), `utf-8-sig` ve čtení `domy.py` (`domy_web.py`), v `podminky.py` a `export_web.py`, komentář o přečíslování v šabloně `domy.py`. `ramecek.py` (`utf-8-sig`) už převzatý byl. Hlavičky „Původ“ jsou zvednuté jen u těchto souborů.
- **Úprava při převzetí:** `slusne.py` se u nás zapíná importem, proto `import slusne` bez volání `slusne.instaluj()` (u nás neexistuje). Řádky zdravi u `ddb`, `seidel` a dalších nástrojů, které tu nejsou, se nepřevzaly.
- **Ověření tvrzení v `prameny.md` (webové vyhledávání, jen přečtená shrnutí zdrojů, ne text zákonů):** doloženo vyhl. 97/1961 § 8, § 31 zákona o obcích (čísla nelze užívat opakovaně), zákon 266/1920 (podle návrhu z 1920), patent z 23. 3. 1857 č. 67 jako sčítací (ČSÚ), první vlna přečíslování 1805–1815; jen částečně patenty 10. 3. 1770 (zdroje se liší: únor × 10. březen) a 25. 10. 1804, sčítání 1869; neověřeno datum 1. 7. 2010 a novela 227/2009, „dodnes Brno“, příklady měst a let. Označeno poznámkou v sekci *Čísla domů*; doplnit z textu zákonů (zakonyprolidi.cz), až půjde o jejich citaci.
- **Nepřevzato:** `sdileni.py` a `sdileni.md` v původní podobě (580 řádků, posílá PR do cizích repozitářů); rozhodnutí 13. 11. 2026 je níže, kus se převzal jako jen čtení. Dál nepřevzato: `brno_scitani.py`, `ddb.py`, `europeana.py` a další nástroje, které v `rodokmen` nejsou (už dřív rozhodnuto: jen to, co dává smysl pro náš rozsah).
- **Živě ověřeno 13. 11. 2026 (jeden dotaz):** `heimatbuch.py Bleiswedel` (1 nález, kniha z 1966) a `brno_encyklopedie.py Poděbradova 5` (dům Orlovna, deska, 4 události). Ostatní kontroly `zdravi.py` nebyly spuštěny.

### `sdileni.py`: přebráno jen čtení (2026-11-13)

- **Rozhodnutí uživatele:** z `sdileni.py` a `sdileni.md` upstreamu `dejiny-domu-skill` přebrat **jen čtení** (`najdi`, `kniha`). Doporučoval jsem nepřebírat nic.
- **Co se převzalo:** `shared/tools/sdileni.py` (jen dotazy do Mapy matrik `ondrnovy.github.io/mapa-matrik` a indexu `pe-pan.github.io/matriky-index`, odhad snímku, poznámky ke knize, přečtené zápisy; brzda přes `slusne.pockej`, mezipaměť na den v `~/.cache/rodokmen_sdileni/`), `shared/reference/sdileni.md` (zúžený návod), řádek v tabulce nástrojů ve `SKILL.md`, sekce v `portaly.md`, dva portály v `podminky.json` a `podminky.md` (`vyrez: ne`), `tests/podminky/test_sdileni.py` (5 testů bez sítě).
- **Co se vědomě nepřevzalo a proč:** příkazy `bod`, `prehled`, `souhlas`, `kanal`, `navrh`, `odeslat`, fronta bodů a `data/sdileni.json`. Posílaly by údaje o bádání uživatele (kde bádá, které knihy, přepisy jmen) na cizí servery a do cizích repozitářů přes pull request nebo přes sběrnou schránku, kterou provozuje třetí strana (`mapa-matrik-schranka.schranka.workers.dev`). To je v rozporu se zásadou soukromí skillu (`soukromi.md`). Test `test_nic_se_neodesila` hlídá, že tyto funkce ani `subprocess` ve zdroji nejsou.
- **Proč čtení stačí:** ušetří listování knihou a nic neodchází. Rizika jsou jiná: závislost na dvou cizích službách bez záruky provozu (nástroj při výpadku řekne chybu a postup jde dál) a kvalita indexu (většinu přečetl jazykový model, proto je zápis vodítko, ne doklad a do dat jde jen to, co uživatel přečte sám).
- **Vrátit se k odesílání:** jen na výslovný pokyn a s rozborem soukromí; původní kód je v upstreamu (`skills/dejiny-domu/tools/sdileni.py`, commit 5c1715b).
- **Živě ověřeno 13. 11. 2026 (jeden dotaz):** `sdileni.py najdi Kozlany 1905 Z` vrátil knihu Kožlany 22, poznámky ke stránkování a 2 přečtené zápisy v indexu. První běh spadl na přerušeném čtení `knihy.json` (`IncompleteRead`), opraveno a pokryto testem. **Neověřeno:** příkaz `kniha` naživo; licence indexu CC BY 4.0 je podle návodu upstreamu, na stránce indexu jsem ji nekontroloval; tvar JSON mapy (`obce/<slug>.json`, `svazky/…`) je převzatý z upstreamového kódu.

### Dávkové stahování s frontou: zahozeno (2026-11-13)

- **Rozhodnutí uživatele:** nedělat. Byla to položka C z poznámek uživatele (fronta svazků, rozpočet MB, přeskakování hotového, zastavení při 429/503, časový limit na snímek).
- **Proč:** strojové stahování z ARON a eBadatelny může být blokované (poznámka 2026-11-05, neověřeno) a nástroj by musel zachovat brzdu, takže by přinesl málo; ruční stahování zůstává výchozí a `zarad.py` zařadí ručně stažené snímky. Část potřeby už kryje `aron_img.py … rozsah` (stáhne jen část svazku a přeskočí hotové).
- **Vrátit se k tomu:** jen na nový pokyn; zadání je v poznámkách `poznamky_pro_skill.md` v uživatelově projektu (2026-10-28 a 2026-11-03).

### `texty.md` a `zdravi.py` i ve skillu `rodokmen` (2026-11-13)
- **Rozhodnutí:** `skills/rodokmen/SKILL.md` odkazuje na `reference/texty.md` (před psaním textů pro web, ve Fázi 3) a má v tabulce nástrojů řádek `zdravi.py`. Soubory se nekopírují, jsou ve `shared/` a sdílí je oba skilly.
- **Proč:** po přesunu do `shared/` šlo jen o zmínku. Pravidla psaní (krátké věty, bez archivního žargonu, nejistota lidsky) platí pro příběh rodu stejně jako pro dům; `zdravi.py` pomáhá poznat, že portál změnil adresu nebo API.
- **Nezměněno:** `texty.md` zůstává beze změny obsahu, příklady z domů v něm zůstávají.

## Poznámky z uživatelova projektu 2026-11-22: co se zapracovalo a co ne (2026-11-23)

Deset poznámek z aktualizace 0.8.0 → 0.9.1 v sandboxu (macOS). Větev `fix/poznamky-2026-11-22`.

- **Zapracováno:** `npm install --cache "$TMPDIR/npm-cache"` a host `registry.npmjs.org` v `web.md` a `instalace.md`; `verze.py` vypisuje cestu instalace skillu, kterou porovnává (plugin z registru × složka skillu, výstup se lišil podle místa spuštění); `sdileni.py` rozliší výpadek (síť, nepovolený host) od „obec v mapě není“ a řekne, které hosty povolit; věta o číslu deníku (psát až po zápisu řádku) v `data.md`; tvar adresy pro `mista.py ruian` a host `ags.cuzk.cz` v hlavičce `mista.py`; ruční kopie `domy.py` do existujícího projektu v `skills/dum/SKILL.md`.
- **Už ve skillu a netřeba měnit:** zsh nerozděluje proměnnou na slova (`matriky.md`, technické pasti); písmo pro `mapa_knihy.py` (funkce `pismo()` hledá Arial v `/System/Library/Fonts/Supplemental`); cesta k verzi skillu (`SHARED_DIR/VERZE`, ne `SKILL_DIR/VERZE`; ověřeno grepem, v návodech jiná cesta není); mezipaměť `sdileni.py` mimo zapisovatelné složky (jede bez ní, commit `a3800ce`).
- **Dokončeno 2026-11-23 (kód):** `kontrola.py` varuje, když `data/STAV.md`, `todo.md` nebo `docs/todo.md` projektu zmiňují `něco.py`, které není v `tools/` ani `data/` (jen upozornění, test v `tests/kontrola/test_domy.py`). `mista.py` přijme celou adresu z výpisu `ruian` („Lhota 14, 12399 Lhota u Dubé“) i samotné PSČ za čárkou, takže `okoli` a `parcely` jdou zavolat s tím, co vypsal `ruian`; při nenalezení s obcí za čárkou vypíše, co k adrese zná jinde (testy v `tests/podminky/test_mista.py`). **Zúžení podle k. ú. nedělám:** k. ú. není v adrese, vyžadovalo by dotaz na parcelu každého kandidáta; PSČ stačí. **Číslo řádku** z výpisu nepřijímám (nástroj nemá stav mezi voláními); funguje celá adresa nebo `lat,lon`. **Seznam obcí v Mapě matrik** nástroj mít nemůže, dokud ho nevystaví mapa (`v1/obce/index.json` je 404).

## Poznámky z uživatelova projektu 2026-11-23: šest mapových poznámek (2026-11-23)

Šest poznámek z práce s mapami domu (`cuzk_archiv.py`, `geolab.py`). Stejná větev `fix/poznamky-2026-11-22`.

- **Zapracováno v kódu:** `cuzk_archiv.py prehled` a `adresy` předávají ImageMagicku písmo z `mapa_knihy.PISMO` (dřív padaly na „unable to read font“; `mapa_knihy.py` ho měl vyřešené, `cuzk_archiv.py` ne – proto dřívější „už ve skillu“ platilo jen pro `mapa_knihy.py`); bez písma `prehled` listy nepopíše, vypíše jejich pořadí a nepadne. `cuzk_archiv.export` při odpovědi „image exceeds the size limit“ sníží šířku na 70 % a zkusí znovu (do 500 px). `cuzk_archiv.get` a `geolab.stahni` zopakují i useknutý přenos (`IncompleteRead` je `HTTPException`, ne `OSError`, proto ho původní opakování nechytalo) a po vyčerpání pokusů skončí větou s hostem, ne tracebackem. Testy: `tests/podminky/test_cuzk_archiv.py`, `test_geolab.py`.
- **Zapracováno v návodech:** hosty pro sandbox (`ags.cuzk.gov.cz`, `ags.cuzk.cz`, `gis.cenia.cz`, `geolab.cz`, `oldmaps.geolab.cz`) v hlavičkách nástrojů a v `prameny.md`; indikační skica jako klíč k ztotožnění čp. se stavební parcelou a vrstva `pk` jako první pokus u malých obcí (`prameny.md`); postup, jak mapu zapsat jako zápis, aby ji `kontrola.py` přijala jako doklad (`prameny.md`, před odrážkou o zveřejnění map).
- **Zvolená cesta k mapě jako dokladu:** návod, ne změna `kontrola.py`. Zápis s `druh` `J` už dnes projde, má výřez, rámeček a přepis jako každý jiný zápis, takže se nic nového nevyvíjí. **Zavržená varianta:** nechat `kontrola.py` přijmout odkaz na `mapy.json` – ten je jen pro prolínání na webu, nemá `shrnuti` ani přepis a doklad bez čitelného textu by kontrolu oslabil.
- **Neověřeno:** živě proti serveru ČÚZK a Geolabu (testy jsou s napodobenými odpověďmi); sestavení `montage` s písmem jen na ukázkových obrázcích.

## Export do GEDCOM: `ged_export.py` (2026-11-22)
- **Rozhodnutí uživatele:** GEDCOM 5.5.1 jako výchozí (MacFamilyTree 11 umí i 7.0, ale vendor v manuálu 5.5.1 doporučuje, 7.0 podporuje málo programů), zdroje jako plnohodnotné `SOUR`, obrázky v první verzi ne.
- **Proč GEDCOM:** manuál MacFamilyTree 11.1 (kap. 1.5.2, 25) popisuje jako importní cestu jen GEDCOM (*Import GEDCOM file* na úvodní obrazovce, u médií se aplikace ptá na složku). Jiný importní formát vendor neuvádí.
- **Zdroje u osoby, ne u události:** zápis ze `zaznamy.json` cituje víc osob a víc událostí (křest Jana dokládá i jeho rodiče), takže přiřazení k `BIRT`/`MARR`/`DEAT` podle druhu zápisu by vyrobilo nepravdivé citace. Zápis proto visí na osobě s `PAGE` (svazek, snímek).
- **Soukromí:** `ISSUES` a `HYPOTEZY` se nevyvážejí (jsou pro web, mohou mít citlivé věci); příčina úmrtí jen u osob narozených před více než 100 lety (zdravotní údaj, `soukromi.md`); `--bez-zivych` vynechá osoby bez úmrtí narozené před méně než 100 lety. Bez přepínače se žijící exportují, soubor je ale jen na disku.
- **Nevyřešeno:** zacházení MacFamilyTree 11 s vlastními tagy a s médii není v manuálu popsáno textem, jen screenshoty; export je zkoušený jen vlastním importem (`tests/ged_export`), ne v MacFamilyTree 11.
- **Výřezy zápisů v exportu (2026-11-22, na pokyn uživatele):** výstup je jedna složka `pracovni/gedcom/` s `rodokmen.ged` a `media/<klic>.jpg`; `OBJE` je samostatný záznam odkazovaný ze `SOUR` (jediný tvar platný v 5.5.1 i 7.0), `FILE` relativní `media/…`. Jen `vyrezy/` (zápis, který zdroj dokládá), ne celé stránky z `zdroje/` (68 MB u ukázkového projektu, nic navíc nedokládají). Kopírují se jen výřezy zdrojů exportovaných osob, takže `--bez-zivych` je nevynese. Zavržené: `GEDZIP` (ZIP navíc, MacFamilyTree 11 importuje složku bez něj), obrázky u osoby místo u zdroje (stejný důvod jako u citací). Ověřeno testem i importem v MacFamilyTree 11 (2026-11-23): obrázek je u zdroje (*Source Citations* → *Media*), v seznamu *Media* je všech 41; u osoby samotné ne. Odkaz přímo z osoby uživatel zamítl – nechat u zdroje.

## Verze 0.9.3 místo 0.9.2 (2026-11-23)
- **Rozhodnutí:** GEDCOM export, opravy z poznámek z 22. a 23. 11. a dokumentace jdou do jednoho vydání 0.9.3. Verze 0.9.2 v tomto forku nevyšla (tag nevznikl), její sekce v `CHANGELOG.md` je sloučená do 0.9.3.
- **Proč:** tag `v0.9.2` už existuje v upstreamu (`sarsonj/rodokmen-skill`, jiné vydání: kontrola verze, MZA přes Playwright), takže stejné číslo u nás by označovalo dvě různé věci. Upstream mezitím vydal i 0.10.0; převzetí je v `docs/todo.md`.

## Poznámky z uživatelova projektu 2026-11-23: čtyři poznámky o knihách a pomocnících (2026-11-23)

Větev `fix/poznamky-2026-11-23-dalsi`, bez změny verze (vydání zvlášť).

- **Seznam knih ke stažení: `data/ke_stazeni.md` v šabloně projektu.** Jeden soubor s tabulkou (stav, kniha, roky, snímky, proč, odkaz na matriku, ZIP z pomůcky), ostatní místa na něj jen odkazují. `zarad.py … --proved` po úspěšném zařazení odškrtne řádek (`[ ]` → `[x] zařazeno <klíč>`); řádek najde podle čísla knihy v odkazu na matriku (`matrikaId/<id>` s hranicí čísla, `archivalieId/<id>`, `apu/<apu8>`), jiný nedotkne. **Soubor v projektu chybí → nástroj mlčí a nic nezakládá** (starší projekty ho nemají; aktualizace projektu mění jen `tools/` a `web/`, ne `data/`, a návod říká, že ho má Claude zkopírovat ze šablony). **Zavržené:** odškrtávat podle názvu knihy (nespolehlivé), zakládat soubor automaticky v `zarad.py` (zásah do projektu bez vyžádání).
- **Model pomocníka:** čtení kurentu před ~1830 zadávat Opusu, ne Sonnetu (`SKILL.md`, README). Opírá se o jednu knihu oddaných z přelomu 18./19. stol.: Sonnet přehlédl zápisy a „Panna“ přečetl jako „Anna“, Opus tutéž knihu přečetl spolehlivě. Pro kurent po roce 1830 zkušenost chybí a návod to říká. Zavržené: pravidlo „kurent vždy Opus“ bez data (nepodložené).
- **Sonnet „čte z přehledu“:** v zadání chtít přečtené jméno **každého** ženicha a nevěsty ze zvětšení do `postup.md`; „nenalezeno“ od Sonneta platí jako „bez zásahu“. Starší věta „na špatně čitelné knihy (kurent 1. poloviny 19. století) pomocníky nepouštěj“ je zúžená na vybledlé snímky, protože s přesným zadáním na Opusu kurent funguje.
- **Rychlé hledání v oddílu knihy zemřelých:** už popsané mapa knihy a montáž sloupců (`matriky.md`, bod 3 a 4) se doplnilo o půlstrany, příklad (18 let jedné vsi ve třech obrázcích), past s posunem stránky a ořez pro knihu oddaných. **Kód se nemění:** `--vedle` se zarovnáním podle linek tabulky je nápad bez ověření, jde do `docs/todo.md`.

## Index knihy: `data/indexy/` a `indexy.py` (2026-11-24)

Uživatel rozhodl, že se index dělá (návrh z poznámky z jeho projektu 2026-11-23). Větev `fix/poznamky-2026-11-23-dalsi`.

- **Problém:** hledání jedné osoby přeskočí ostatní zápisy, u „domácích“ knih se vracíme k témuž svazku znovu (v jednom projektu kniha oddaných v 14 hledáních, narozených v 9, zemřelých v 8) a přečtené jméno se čte podruhé.
- **Rozhodnuto:** index jako TSV `data/indexy/<klíč svazku ze svazky.json>.tsv`, pevné sloupce (první verze `druh snimek strana kniha jmeno datum ves cp vazby poznamka jistota`; téhož dne nahrazeno komunitním formátem, viz níž), nástroj `tools/indexy.py` (`pridej`, `hledej`, `stav`). `hledej` u každého indexu říká, co pokrývá, aby odpověď „jinde nejsou“ měla váhu. Index je vodítko se stavem „index“, ne `doc`.
- **Umístění:** `data/indexy/`, ne složka knihy v `pracovni/` (je v `.gitignore`; snímky jdou stáhnout znovu, přečtený index ne) a klíč svazku přežije přejmenování složky nástrojem `zarad.py`. Na web nepatří: `export_web.py` ho nečte a test to hlídá. `kontrola.py` hlásí chybu, když klíč indexu není ve `svazky.json` nebo nesedí záhlaví, a upozornění na snímek za koncem svazku.
- **Zavržené:** vlastní formát shodný s komunitním `precteno.tsv` (nezávislý cizí projekt bez záruky, hlavičky jsme nezkoumali; převod jde doplnit později), index do složky knihy v `pracovni/` (ztratil by se s úklidem), zápis zásahu z indexu rovnou jako `doc` (index čte model, často z vybledlého písma).
- **Nedokončeno:** nástroj zatím nic neindexuje sám, řádky připravuje pomocník (u kurentu před ~1830 Opus) a zapisuje hlavní session; šablona zakládá jen `data/indexy/README.md`. Starší projekty složku nemají: `indexy.py pridej` ji založí sám. Úspornost průchodu celou knihou jsme změřili jen na pilotu (rejstřík zemřelých farnosti, 1 snímek, 42 řádků, ~10 tis. tokenů kontextu, asi 1 % 5h limitu); průchod celou knihou ověřen nebyl.

### Index knihy: komunitní formát a odesílání přes schránku (2026-11-24)

- **Formát přepsán na komunitní** (`pe-pan/matriky-index`, `precteno.tsv`, ověřeno na ukázkové knize AHMP): `snimek datum typ obec osoby ostatni jistota cetl odkaz` plus naše `strana` a `kniha` (rejstříky, typ `I`). Důvod: shodné sloupce znamenají, že soubory jdou číst i porovnávat s komunitním indexem bez převodu. Jistota je slovně `vysoká | střední | nízká` (v ukázkové knize jen `nízká` a `střední`; „vysoká“ jsem v datech neviděl, vychází z návodu), nejisté kusy textu mají `[?]`. `jmeno` a `vazby` se sloučily do `osoby` („role: jméno; …“), `ves` a `cp` do `obec`. Klíč zůstává klíč svazku ze `svazky.json`, umístění `data/indexy/<klíč>.tsv`; komunitní `knihy.json` (katalog 1144 knih s počty přečtených zápisů a metadaty z `kniha.yaml`) nepřebíráme, souhrn počítá `indexy.py stav`.
- **Odesílání: uživatel rozhodl převzít, kanál „export + schránka“** (výslovný pokyn 2026-11-24; rozhodnutí z 2026-11-13 „jen čtení“ se tím mění, viz *`sdileni.py`: přebráno jen čtení*; tam uvedená podmínka „rozbor soukromí“ je splněna níž). Nástroj `shared/tools/prispevek.py`: `navrh` (nic neodchází, ukáže dávku a otisk), `souhlas ano [jméno] | ne`, `odeslat <otisk>`. `sdileni.py` zůstává jen čtecí a jeho test `test_nic_se_neodesila` platí dál.
- **Rozbor soukromí.** Ven jde jen doslovný přepis zápisů N, O, Z z podporovaných archivů (Porta fontium, eBadatelna SOA Praha, AHMP) starších zákonných lhůt (rok < letos − 100 u N, − 75 u O a Z; přísněji než minimum), s `cetl` ve tvaru model/effort datum; rejstříky, mladší řádky, řádky bez data a řádky se slovy o příbuzenství či ztotožnění se vynechají. Příspěvek jde přes **cizí službu** (sběrná schránka Mapy matrik, Cloudflare Worker autora Mapy matrik, `mapa-matrik-schranka.schranka.workers.dev`), která založí pull request do veřejného repozitáře (CC BY 4.0): nevratné, bez záruky provozu. Anonymně: v `cetl` jen model a datum; přispěvatele rozlišuje pseudonym, který schránka spočítá z náhodného klíče (`pracovni/sdileni/klic.txt`, mimo git). Jméno jen s výslovným souhlasem. Bez souhlasu (`data/sdileni.json`) a bez shody otisku dávky s tím, co uživatel viděl, se neodešle nic. Odesláno se zapisuje (otisk řádku) a podruhé se neposílá. Schránka dedupuje a limituje (200 řádků, 15 knih, 256 kB najednou).
- **Zavržené:** odesílání pod účtem GitHub přes `gh` (zveřejnilo by tvoje jméno a e-mail z commitu a umožnilo fork pod cizím repozitářem; chceš-li, zvážíme později), odesílání orientačních bodů do Mapy matrik (jiný projekt, zatím nepotřebné), `subprocess` a `git` v nástroji (schránka stačí jedním POST).
- **Neověřeno:** **živé odeslání se nezkoušelo** (nic naostro se neposílalo, test používá atrapu). Tvar těla příspěvku a limity jsou z README schránky (`ondrnovy/mapa-matrik`, `schranka/README.md`) a z upstreamového `sdileni.py` (5c1715b); jestli schránka přijme naše `cetl` s příponou „(z rodokmenu)“ a pole `nastroj` `rodokmen/prispevek.py`, uvidíme až při prvním odeslání. První odeslání dělej malé (pár řádků) a výsledek pull requestu zkontroluj.

### Index knihy: první zkouška na živém projektu (2026-11-24)

Druhá session s `claude --plugin-dir <worktree>` (0.9.5) v uživatelově projektu, zadání „najdi úmrtí <předka> v <obci>, asi 1870“ (kniha zemřelých farnosti).
- **Co se ukázalo.** Session šla nejdřív do přepsaného rejstříku zemřelých farnosti (1836–1882), ne do knihy: hledaný zemřel roku 1863, rejstřík uváděl stranu 4. Podle toho otevřela snímek 6, zápis byl na **snímku 7**; ověřila ho ve zvětšení a uložila šesti kroky (zápis, výřez, rámeček, přepis s překladem, stopa mezi příbuznými, deník č. 228; kontrola dat bez chyb). Index tedy posloužil jako vodítko a chybu o jeden snímek zachytilo ověření v knize. Číslo strany nevede na snímek přímo; pomůcku „zkus i sousední snímek“ jsme do návodu nedopsali.
- **Cena.** `/usage` za celou session: **1,55 USD** (Opus 5.5 1,55 USD, Haiku 0,0003 USD), 2 min 16 s API, 6 min 20 s celkem, 96 % vstupu z cache. Zahrnuje i uložení zápisu, ne jen hledání.
- **Výsledek hledání.** Jediný nositel hledaného jména v rejstříku je šestiměsíční chlapec, ne dospělý kolem roku 1870; zadání „asi 1870“ je tedy nejspíš chybné, původ údaje se ověřuje u uživatele.
- **Index (`indexy.py`) se nepoužil.** Projekt měl `.skill_verze` 0.9.1, `tools/indexy.py` a `data/indexy/` v něm nebyly (zjištěno 2026-11-24), takže session četla z pluginu 0.9.5 jen návody; rejstřík, podle kterého hledala, byl starší přepis. Zkouška platí jako hledání přes rejstřík farnosti, ne jako zkouška nástroje.
- **Co se tím neověřilo.** `indexy.py` a průchod celou knihou pomocníkem na Opusu, počet řádků s `[?]` a přesnost čtení. Ostré odeslání `prispevek.py` se nezkoušelo. Session pracovala v projektu na hlavní větvi a nic nekomitovala.

## Poznámky z uživatelova projektu 2026-11-23: opravy `zarad.py` a `aron_img.py`, rejstřík farnosti (2026-11-24)

Větev `fix/poznamky-2026-11-23-dalsi`, bez změny verze (CHANGELOG, sekce „Nevydáno“).

- **`zarad.py`, ARON svazek bez obce ve `svazky.json`** („Sbírka matrik Východočeského kraje, sign.: 148 …“): shoda svazku se pozná podle klíče (apu) a signatury, která stojí v `obsah.txt`, ne podle názvu; složka se u ARON jmenuje podle prvního řádku `obsah.txt` („Lhota 148“). Jiná signatura ve `svazky.json` se dál hlásí jako rozpor. **Zavržené:** přepisovat `svazky.json` automaticky (zásah do dat bez vyžádání; uživatel to udělá přes `zapis.py --sloucit`).
- **`zarad.py`, počet snímků a popis archiválie:** `SCANS` zná „Snímky“; archiv = „Místo uložení – Archivní fond“, popis z „Popis archiválie“ (anglické popisky zůstávají jako záloha).
- **Staré strojové kopie:** nástroj je **nemaže**. Je-li v kopii jen `s*.jpg` a `stahovani.log` a počet snímků sedí, vypíše hotový `rm -r` pro uživatele; automatická kontrola oprávnění Claudovi `rm -r` velkých složek zamítá i tehdy, když to pravidlo projektu ukládá. Jiné soubory nebo nesedící počet = „nemazat“.
- **`aron_img.py`:** 8znakový klíč ze `svazky.json` se doplní na celé apu z pole `url`; dřív to hlásilo „Svazek v ARONu není (HTTP 404)“, což svádí k závěru, že svazek neexistuje.
- **Návod `matriky.md`:** nenajde-li se úmrtí starého člověka v jeho vsi, nejdřív rejstřík zemřelých celé farnosti (výměnkář zemřel u příbuzných v sousední vsi téže farnosti). Opírá se o jeden případ; rejstřík se může splést v měsíci, platí matrika.
- **Model pomocníka u kurentu před ~1830 (Opus):** už byl v `SKILL.md` z 0.9.4, nic se nepřidávalo.

