# Vydání nové verze skillu

Postup od zvednutí čísla po aktualizaci pluginu. `X.Y.Z` je číslo nové verze, `D. M. RRRR` datum vydání.
Repozitář vydání je `vmi43/rodokmen-skill` (fork); upstream `sarsonj/rodokmen-skill` má vlastní vydání.

## Před začátkem

- Práce je hotová a slučuje se do `main` přes PR. Na `main` se nepracuje přímo.
- Číslo verze: opravy `Z`, nové funkce `Y`. Tag s číslem, které už upstream vydal, nezakládej
  (upstream má `v0.9.2` a `v0.10.0`).

## Postup

1. **Větev.** Z `main` založ `chore/release-X.Y.Z`.

2. **Číslo verze na čtyřech místech najednou**, vždy s číslem verze i datem vydání:

   | Soubor | Co se mění |
   |---|---|
   | `.claude-plugin/plugin.json` | `version` |
   | `shared/VERZE` | celý obsah; podle něj Claude u uživatele pozná, že má aktualizovat projekt |
   | `README.md` nahoře | „Aktuální verze: X.Y.Z (vydána D. M. RRRR)“ |
   | `README.md` v požadavcích | „Stav k D. M. RRRR (verze X.Y.Z)“ |

3. **`CHANGELOG.md`.** Nahoru přidej sekci `## X.Y.Z – D. M. RRRR` s oddíly Nové / Opravy / Návody, krátké odrážky
   pro uživatele, čísla issues jako `#11`. Z této sekce se později vezme text vydání na GitHubu.

4. **Testy.** Každý soubor `tests/podminky/test_*.py` musí skončit kódem 0:

   ```bash
   for f in tests/podminky/test_*.py; do python3 -I "$f" >/dev/null 2>&1; echo "$? $f"; done
   ```

   Mění-li se formát mezi `tools/` a `template/web/`, otestuj i aktualizaci projektu založeného předchozí verzí:
   `novy_projekt.py` na stejnou složku, pak `npm install`, `npm run data`, `npm run build`.

5. **Commit a push.** Do commitu vyjmenuj cesty (ne `git add -A`), před commitem `git diff --cached --stat`.
   Před prvním commitem ověř `git config user.email`.

6. **PR.** Vždy s `--repo`:

   ```bash
   gh pr create --repo vmi43/rodokmen-skill --base main --head chore/release-X.Y.Z --title "chore: release X.Y.Z" --body-file notes.md
   ```

7. **Merge.** Přes `--merge` (ne squash ani rebase), aby šla větev smazat bezpečně `git branch -d`:

   ```bash
   gh pr merge <číslo> --repo vmi43/rodokmen-skill --merge
   ```

8. **Tag a vydání na GitHubu** až po mergi. Nejdřív v hlavním checkoutu `git pull --ff-only origin main`, pak text
   sekce z CHANGELOGu do souboru a vydání:

   ```bash
   awk '/^## X.Y.Z /{f=1;next} /^## /{f=0} f' CHANGELOG.md > /tmp/notes.md
   ```

   ```bash
   gh release create vX.Y.Z --repo vmi43/rodokmen-skill --target main --title "X.Y.Z" --notes-file /tmp/notes.md
   ```

9. **Plugin u sebe.** Plugin `rodokmen` čte lokální složku hlavního checkoutu (`~/ai_tools/rozvoj/skills/rodokmen`).
   V ní `git pull --ff-only origin main`, v Claude Code `/reload-plugins`. Bez toho se nová verze neprojeví.

10. **Úklid.** Sloučenou větev smaž:

    ```bash
    git push origin --delete chore/release-X.Y.Z
    ```

    ```bash
    git branch -d chore/release-X.Y.Z
    ```

## Ověření, že je vydáno

- `git ls-remote origin refs/heads/main 'refs/tags/vX.Y.Z'` vrací obě položky a commit tagu je merge PR.
- `gh release view vX.Y.Z --repo vmi43/rodokmen-skill` vrací vydání, které není koncept.
- `shared/VERZE` v hlavním checkoutu obsahuje `X.Y.Z` a `~/.claude/plugins/installed_plugins.json` má verzi `X.Y.Z`.

## Pasti

- **`--repo` u každého `gh`.** Bez něj míří `gh` na upstream: PR selže na „No commits between“ a vydání by vzniklo
  v cizím repozitáři.
- **Sandbox Claude Code.** `git push` a `gh` potřebují přístup na GitHub (`github.com`, `api.github.com`) a `gh` navíc čte
  `~/.config/gh`, které sandbox blokuje; spouštějí se proto mimo sandbox, po schválení. `git push -u` v sandboxu dokončí
  push, ale ohlásí chybu při zápisu nastavení větve; push přesto proběhl (ověř `git ls-remote`).
- **Soubor s textem PR a vydání** ulož do scratchpadu session, ne do `$TMPDIR`: mimo sandbox je jiný a `gh` by soubor
  nenašel.
- **Souběžná session.** Přebírá-li vydání jiná session, na větvi nic necommituj ani nepushuj a vydání nezakládej podruhé.
  Před každým krokem ověř stav: PR, tag i vydání už mohly vzniknout.
- **Přimergovaný PR ještě není vydání.** U 0.9.6 se po mergi zapomněly kroky 8–10 (doplněno až 27. 11.). Před další verzí zkontroluj `gh release list --repo vmi43/rodokmen-skill`, jestli má předchozí verze tag i vydání.
- **`gh release create --target` chce celý hash commitu.** Se zkráceným hashem vrátí HTTP 422 „tag_name is not a valid tag“; použij `--target $(git rev-parse <hash>)`, nebo `main`.
- **`git branch -d` v sandboxu** větev smaže, ale nemůže zapsat do `.git/config` (`could not lock config file`) a nechá tam sekci `[branch "…"]`. Neškodí; uklidí ji `git config --remove-section branch.<větev>` mimo sandbox.
- **Merge, který vypadá přerušený.** Zrušený příkaz `gh pr merge` mohl proběhnout. Před opakováním zkontroluj stav PR.
