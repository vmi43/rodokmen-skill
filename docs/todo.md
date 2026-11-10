# Todo

## Přerušený běh

### Skill `rodokmen:dum` (dějiny domu podle dejiny-domu-skill) – přerušeno 2026-11-05

Rozdělaná práce, která se dokončuje jako první: vlastní skill `rodokmen:dum` v tomto pluginu, odvozený z cizího skillu `vzoha/dejiny-domu-skill`, ne jeho klon. Leží na větvi `claude/rodokmen-misto-skill-4da757` v tomto worktree. Před pokračováním musí uživatel ručně pustit testy, které sandbox nepustil (viz Zbývající položky 1).

**Co přerušilo a co se udělalo.** Session se ukončuje kvůli délce kontextu. Hotovo a **commitnuto** (`78f9f7a`): `tools/`, `reference/`, `template/` a `VERZE` přesunuty ze `skills/rodokmen/` do `shared/` v kořeni; v `skills/rodokmen/` zůstal jen `SKILL.md` (nově odkazuje na `SHARED_DIR` = `${CLAUDE_PLUGIN_ROOT}/shared`); cesty upraveny v testech, README, LICENSE a CLAUDE.md; README Varianta B přepsána na „celý repozitář jako plugin“ (`claude --plugin-dir`). Kód skillu `dum` zatím nevznikl. Necommitnuté soubory:
- `docs/decisions.md` (nový) – zapsaná rozhodnutí: Porta fontium, název `dum`, rozsah první verze, sledování upstreamu, `shared/` v kořeni, licence, společná `shared/VERZE`.
- `docs/todo.md` (tento soubor, nový).

Ověřeno po přesunu (python3 -I, rc=0): testy aktualizace (20 z 20), kontrola (65), anno (8), vyrez (8), portafontium (13), prohlížeč (11). **Neověřeno** (sandbox blokuje lokální port): `tests/web/test_overit.py`, `tests/brzda/*`.

Rešerše: stažen a přečten celý upstream `dejiny-domu-skill` (0.5.0, větev `master`, odvozený z našeho rodokmenu 0.5.0). Stahování v sandboxu: `gh` nejde, `curl` jen s `allowed_domains` `api.github.com` a `raw.githubusercontent.com`, soubory s `[...]` v názvu s `curl -g`. Kopie byla ve scratchpadu, nová session si ji stáhne znovu. Upstream playbook je v cestě `skills/dejiny-domu/reference/playbook.md`.

**Zjištění o rozdílech**
- Rodokmen se točí kolem osoby (`data/osoby.py`, Kekulého čísla, rody, vějíř), dějiny domu kolem čísla popisného (`data/domy.py`: `OBEC`, `OBEC_UDALOSTI`, `D` s událostmi, držiteli, obyvateli, `ISSUES`). Stavy doložení: u domů přibývá `lit` (literatura).
- Společné a ve stejném formátu: `zaznamy.json`, `svazky.json`, `prepisy.json`, `zvyrazneni.json`, `research_log.md`, `zajimavosti.md`, `pribeh.md`, `mista.json`, `dokumenty.json`, `web.json`, šestikrokový zápis nálezu.
- Jen v upstreamu: `data/mapy.json` (staré mapy a snímky, skupiny pro porovnání), `pametnici.md`; web: `obec`, `domy`, `dum/[slug]`, `mapy`, `pribehy/[slug]`, komponenty Timeline, Gallery, HouseMap, HouseLink, RecLinks, `modern.css`, `lib/places.js`.
- Nástroje jen v upstreamu: `cuzk_archiv.py`, `mza.py`, `trebon.py`, `dnnt.py`, `ipr_praha.py`, `podminky.py` + `podminky.json`, `zdravi.py`, `hlidac.py`; rozšíření `mista.py` o `ruian`, `okoli`, `parcely`; `ramecek.py --vyrez`. Návody jen v upstreamu: `reference/prameny.md`, `reference/podminky.md`, `reference/texty.md`.
- Jen u nás (nepřepsat): `slusne.py` (691 řádků proti 307), `cache.py`, `hlidac_site.py`, `ged_import.py`, `ftb_export.py`, `napady.py`, `mapa_knihy.py`, `fan_chart.py`, `Containerfile` na UBI bez root a Podman (upstream má `Dockerfile` na `node:24-slim` a `nginx:alpine`, v rozporu s uživatelovými pravidly), testy aktualizace a brzd, CHANGELOG.

**Ověřeno 2026-11-06** (mimo sandbox, rc=0): `tests/web/test_overit.py shared` 9 z 9, `tests/brzda/test_hlidac.py shared` 71 z 71 (bash i bez shellu), `claude plugin validate .` prošlo. **Zbývá ručně:** `test_brzda.py` a `test_mezipamet.py` (chtějí alias `sudo ifconfig lo0 alias 127.0.0.2 up`), ruční aktualizace projektu, skutečné načtení přes `claude --plugin-dir`.

**Zbývající položky**
1. **Ruční ověření přesunu do `shared/`** (krok (a); část hotová, viz výše). Pustit `python3 -I tests/web/test_overit.py shared` a testy brzdy podle `tests/brzda/README.md` (potřebují lokální port); ruční aktualizace projektu založeného starší verzí podle `CLAUDE.md` repa (`novy_projekt.py` na stejnou složku, `npm install`, `npm run data`, `npm run build`); ověřit, že `claude --plugin-dir <repozitář>` načte skills a že `${CLAUDE_PLUGIN_ROOT}/shared` v `SKILL.md` se dosadí. Selže-li, opravit před krokem (b). Zároveň README (Varianta B) zatím tvrzení `--plugin-dir` nemá ověřené.
2. **Commit `docs/decisions.md` a `docs/todo.md`** (vyjmenované cesty) po schválení uživatele; commitovat a pushovat jen na výslovný pokyn.
3. **Krok (b): skill `skills/dum/SKILL.md` a nové soubory do `shared/`.** Jádro: `data/domy.py`, web domu a obce, `cuzk_archiv.py`, `podminky.py` + `podminky.json`, `prameny.md`, `texty.md`, rozšíření `mista.py`, plus `zdravi.py` a skript pro porovnání s upstreamem; `mista.py` a `ramecek.py` se rozšiřují v původních souborech, ne ve druhých verzích.
4. **Krok (c): `novy_projekt.py` rozšířit** (např. `--dum`); stránky domu zapínat, jen když je v projektu `domy.py`.
5. **Krok (d): `podminky.json`** – u `www.portafontium.eu` stejná hodnota, jakou dělá nástroj (dotazy a obrázky povolené jen pro osobní použití), `vyrez: souhlas` a poznámka, že obrázek na veřejný web chce souhlas archivu.
6. **Krok (e): u kontejneru zachovat `Containerfile` na UBI.**
7. **Krok (f): vazba osoba ↔ dům v datech** (upstream jen přes `note`).
8. **Krok (g): v hlavičce každého převzatého souboru odkaz na původ a commit.**
9. **Krok (h): vydání** – verze ve třech místech (`plugin.json`, `shared/VERZE`, README na dvou místech), sekce v `CHANGELOG.md`, tag a vydání na GitHubu (postup v `CLAUDE.md` repa).
10. **Parkované:** `reference/texty.md` a `zdravi.py` by se hodily i do skillu `rodokmen`; po zavedení `shared/` jde jen o to, zda je zmínit v `SKILL.md` `rodokmen`. Rozhodnout po `dum`.

**Vyvrácené a uzavřené**
- „Prostý klon repozitáře nebo přímá instalace upstreamu“: odmítl uživatel (chce stejné metody a vlastní vylepšení dat), proto vlastní skill.
- „Upstream je novější v celku“: neplatí. Dejiny domu jsou odvozené z rodokmenu 0.5.0 a my jsme na 0.8.2 (brzda, cache, hlídač sítě, Porta fontium 10 s). Z upstreamu se přebírá jen to, co je nové pro dům.
- „Druhý playbook přebírat“: ne. Upstreamový `playbook.md` (719 řádků) se od našeho (714) liší jen úvodní poznámkou, tělo je shodné (diff 2026-11-05).
- „Vše dát do `skills/rodokmen`, `dum` jen rozdíl“: uživatel odmítl ve prospěch `shared/`.
- „`shared/` ve `skills/shared/`“ a „klon repozitáře do `~/.claude/skills/`“: zamítnuto. Dokumentace neříká, zda se složka bez `SKILL.md` ve `skills/` ignoruje, a osobní skills se hledají jen jako `~/.claude/skills/<skill>/SKILL.md`.

**Rozhodnuté v běhu** (vše zapsáno v `docs/decisions.md`): Porta fontium – náš postup s brzdou 10 s, `User-Agent` a certifikát jako vědomá výjimka; název `rodokmen:dum`, skill pro obec je dlouhodobý výhled; rozsah první verze (jádro plus `zdravi.py`, později `mza.py`, `trebon.py`, `dnnt.py`, `ipr_praha.py`); sledování upstreamu skriptem s porovnáním do dočasné složky, původ a commit v hlavičkách; `shared/` v kořeni; licence (kód a návody s uvedením původu, playbook se nepřebírá); jedna společná `shared/VERZE`.

**Jak pokračovat:** Zjisti, zda existuje alias loopbacku (`ifconfig lo0 | grep 127.0.0.2`; k 2026-11-10 neexistoval, `sudo ifconfig lo0 alias 127.0.0.2 up` čekal na PIN karty), a je-li, pusť mimo sandbox `python3 -I shared/tools/slusne.py tests/brzda/test_brzda.py shared/tools/slusne.py` a `test_mezipamet.py` (příkazy v `tests/brzda/README.md`; `test_overit` a `test_hlidac` už prošly, viz Ověřeno 2026-11-06); pak ověř `claude --plugin-dir` a ruční aktualizaci projektu podle položky 1; potom se uživatele zeptej, zda commitnout `docs/decisions.md` a `docs/todo.md`, a pokračuj krokem (b) z položky 3. Blok a tuto sekci smaž, až je skill hotový a zapsaný v `CHANGELOG.md`.

## Parkované v session

- `reference/texty.md` (psaní textů na web) a `zdravi.py` (kontrola nástrojů proti živým portálům) z upstreamu by se hodily i do skillu `rodokmen`, ne jen do `dum` (do `dum` jdou v první verzi). Po zavedení `shared/` se otázka zjednoduší: soubory budou sdílené, jde jen o to, zda je zmínit v `SKILL.md` `rodokmen`. Rozhodnout po `dum`.
