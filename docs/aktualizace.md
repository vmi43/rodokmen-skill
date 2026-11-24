# Aktualizace skillu v projektu

Dvě oddělené věci: **plugin** (skill, tedy `SKILL.md`, návody a sdílené nástroje) a **projekt** (vaše složka s daty,
vlastní kopií `tools/` a webem). Nejdřív se aktualizuje plugin, potom projekt. Opačně ne: projekt aktualizovaný
z novější kopie skillu, než jakou plugin má, popisuje nástroje, o kterých návod nic neví.

Verze se řídí souborem `VERZE` ve skillu a `.skill_verze` v projektu.

## 1. Aktualizace pluginu

- **Automaticky (doporučeno):** v `/plugin` na kartě **Marketplaces** vyberte `rodokmen` a zapněte **Enable auto-update**.
- **Ručně:**

  ```bash
  claude plugin marketplace update rodokmen
  ```

  ```bash
  claude plugin update rodokmen@rodokmen
  ```

- **Z vývojové kopie** (jen při testu rozpracované verze): `claude --plugin-dir <složka skillu>`. Takový skill je
  jiná verze než ta nainstalovaná; ověřte ji dotazem „jakou máš verzi skillu a odkud se načetl?“.

Potom **restartujte Claude Code**: do běžící relace se nový plugin nenačte.

## 2. Aktualizace projektu

Claude ji sám nabídne na začátku práce v projektu (zjistí rozdíl přes `verze.py`: `AKTUALIZUJ_PROJEKT`). Jde to i ručně,
z kořene projektu:

```bash
python3 -I <složka skillu>/shared/tools/novy_projekt.py <složka projektu>
```

Projekt bez webu přidejte `--bez-webu`; po běhu s webem ve složce `web/` `npm install`. Skript vám řekne, co udělal:

| Výpis | Co znamená a co dělat |
|---|---|
| Přepsáno novou verzí | Soubor jste neměnili, dostal novou verzi. Nic. |
| Sloučeno | Měnili jste vy i šablona, sloučilo se po řádcích. Zkontrolujte výsledek. |
| Ke kontrole / konflikt | Soubor zůstal váš, nová verze šablony je v `pracovni/zaloha_<datum>/nova_sablona/`. Převezměte změny ručně, pak `novy_projekt.py <projekt> --vyreseno <soubor>`. |
| Soubor, který šablona už nemá | Nemaže se. Smažte ho sami a spusťte `--vyreseno`. |
| Nový soubor (např. `indexy.py`) | Jen se přidal; v hlášení o přepsaných se neobjeví. Ověřte `ls tools/`. |

Data (`data/`) aktualizace nemění, jen **doplní chybějící soubory z šablony**, nikdy nic nepřepíše. Z toho plyne:

- Nová šablonová data (např. `data/ke_stazeni.md`, `data/indexy/`) vzniknou prázdná. Máte-li vlastní verzi na jiném místě
  (např. `ke_stazeni.md` v kořeni), skript upozorní na duplicitu; převeďte ji ručně.
- Starší data v jiném tvaru (např. ručně přepsaný rejstřík) se sama nepřevedou. Převod uděláte nástrojem skillu
  (např. `indexy.py pridej`).

Aktualizace odmítne, je-li projekt novější než skill (`CHYBA: projekt je z verze skillu …`). Řešení: aktualizovat plugin
(krok 1), ne projekt vracet.

## 3. Ověření

```bash
cat .skill_verze
```

```bash
python3 -I tools/kontrola.py
```

- `.skill_verze` má číslo nové verze.
- `kontrola.py` nehlásí nové chyby. Upozornění na zmínky nástrojů, které už neexistují, jdou umlčet seznamem
  `nastroje_historie` v `data/web.json` (viz `reference/web.md`).
- Nový nástroj se spouští: `python3 -I tools/<nástroj>.py` bez argumentů vypíše nápovědu.

Potom **restartujte Claude Code** v projektu, aby se projevily změny v `.claude/settings.json` (zákaz `curl`, hlídač sítě).

## 4. Git v projektu

Aktualizace mění `tools/`, `web/`, `.skill_verze`, `.skill_sablona/` a doplňuje soubory v `data/`. Commitujte je **zvlášť**
od vlastní badatelské práce (deník, zápisy, `data/indexy/`), ať jde aktualizaci případně vrátit samotnou.

## Časté potíže

- **Skill hlásí starší verzi než projekt.** Plugin se neaktualizoval nebo se Claude Code nerestartoval (krok 1).
- **Nová funkce se nepoužije.** Projekt má stará `tools/` nebo Claude běží se starým `SKILL.md`; ověřte obojí (krok 3
  a verzi skillu).
- **Skript nic nepřepsal ani nehlásí.** Projekt už je na dané verzi; porovnejte `.skill_verze` s `VERZE` ve skillu.
- **Hlídač sítě zamítl kontrolu verze** (starší projekt): spusťte ji přes brzdu
  `python3 -I tools/slusne.py <složka skillu>/shared/tools/verze.py <složka projektu>`.
