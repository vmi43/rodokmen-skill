# Indexy knih

Sem patří přepsané rejstříky a rychlé průchody knihami: jeden soubor `<klíč svazku ze svazky.json>.tsv` na knihu.
Index je **vodítko** (stav „index“), ne doklad: zásah se ověří na snímku a uloží šesti kroky. Soubory zapisuje
a čte `python3 -I tools/indexy.py` (`pridej`, `hledej`, `stav`, `mapa`, `prepsano`); sloupce a pravidla jsou v jeho nápovědě. Rejstřík se přepisuje po písmenech a `<klíč>.pismena.json` eviduje, kde které písmeno je a které je přepsané. Do gitu patří
(přečtený index je práce jako `zaznamy.json`; snímky v `pracovni/` jdou stáhnout znovu, index ne). Na web nejdou. Sloupce odpovídají komunitnímu indexu matrik; ven jde jen to, co po tvém souhlasu pošle `tools/prispevek.py`.
