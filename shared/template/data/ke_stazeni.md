# Knihy ke stažení

Jediný seznam knih, které musí uživatel stáhnout ručně. Claude sem zapisuje každou takovou knihu a jinde (`todo.md`,
`STAV.md`, chat) na ni jen odkazuje, ať se seznam nerozběhne na víc míst. Po zařazení přes
`python3 -I tools/zarad.py pracovni/<složka> --proved` se řádek sám odškrtne (najde ho podle čísla knihy v odkazu).

Sloupce: **Stav** (`[ ]` čeká, `[x]` zařazeno), **Kniha** (obec, typ, signatura), **Roky**, **Snímky** (počet),
**Proč** (koho nebo co v ní hledáme), **Matrika** (odkaz na stránku knihy v archivu; podle něj se řádek odškrtá),
**ZIP z pomůcky** (přímý odkaz na ZIP se všemi snímky z pomůcky NAD 190, je-li).

| Stav | Kniha | Roky | Snímky | Proč | Matrika | ZIP z pomůcky |
|---|---|---|---|---|---|---|
