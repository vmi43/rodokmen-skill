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

**Vynecháno zatím:** `Doplnky` (uživatelské doplňky z upstreamu), příběhová tlačítka a `pribehy/[slug]` pro dům. Mapa a staré mapy jsou doplněné níže (*Mapa domu a staré mapy*), `Gallery` vynechána.

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
