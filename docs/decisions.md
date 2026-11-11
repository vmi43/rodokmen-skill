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
