# Správa repozitáře rodokmen-skill

Vydání nové verze: zvedni číslo ve třech místech najednou – `.claude-plugin/plugin.json` (`version`),
`shared/VERZE` (podle něj Claude u uživatele pozná, že má aktualizovat projekt) a README na dvou místech – nahoře „Aktuální verze: X.Y.Z (vydána D. M. RRRR)“ a v požadavcích
„Stav k D. M. RRRR (verze X.Y.Z)“, vždy s číslem verze i datem vydání.
Do `CHANGELOG.md` přidej nahoru sekci `## X.Y.Z – D. M. RRRR` (Nové / Opravy / Návody, krátké odrážky pro uživatele,
čísla issues jako `#11`). Po commitu a pushi vytvoř tag a vydání na GitHubu s textem té sekce:
`awk '/^## X.Y.Z /{f=1;next} /^## /{f=0} f' CHANGELOG.md > /tmp/notes.md && gh release create vX.Y.Z --repo vmi43/rodokmen-skill --target main --title "X.Y.Z" --notes-file /tmp/notes.md`.
**Každý příkaz `gh` (PR, release) piš s `--repo vmi43/rodokmen-skill`:** bez něj míří na upstream `sarsonj/rodokmen-skill`
(PR selže na „No commits between“, release by vznikl v cizím repozitáři). Tag `vX.Y.Z` s číslem, které už upstream
vydal, nezakládej (upstream má vlastní `v0.9.2`, `v0.10.0`). Plugin `rodokmen` čte lokální složku hlavního checkoutu:
po mergi udělej v ní `git pull --ff-only origin main` a v Claude Code `/reload-plugins`, jinak se nová verze neprojeví.
Mění-li se formát mezi `tools/` a `template/web/`, otestuj i aktualizaci projektu založeného předchozí verzí
(`novy_projekt.py` na stejnou složku, `npm install`, `npm run data`, `npm run build`).
