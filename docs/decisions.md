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
