# Testy brzdy proti zablokování archivem

Regresní testy pro `shared/tools/slusne.py` (brzda) a `shared/tools/hlidac_site.py` (volitelný hlídač).
Ve složce skillu nejsou, aby se nekopírovaly uživatelům. Nic nestahují z internetu: brzdu zkoušejí na lokálních serverech
(127.0.0.2 a 127.0.0.3 – localhost brzda záměrně nebrzdí), hlídači jen posílají JSON jako Claude Code.

Z kořene repozitáře, přes obal (testy samy obsahují příkazy s curl):

    python3 -I shared/tools/slusne.py tests/brzda/test_brzda.py shared/tools/slusne.py
    python3 -I shared/tools/slusne.py tests/brzda/test_hlidac.py shared
    python3 -I shared/tools/slusne.py tests/brzda/test_mezipamet.py shared/tools   # mezipaměť: jen celé obrázky
    python3 -I tests/brzda/test_prohlizec.py shared/tools   # cache.py uloz/najdi: snímky z prohlížeče (eBadatelna, FamilySearch)

Na Windows `python -I -X utf8` a obojí pustit z Git Bashe i z PowerShellu. `ROZSIRENI=0` spustí u brzdy jen základní testy
(bez heredocu, prodlužování stopky, podprocesů a opakovaného souběhu vláken).

Výsledky na Windows 11 (Python 3.13, Git Bash, PowerShell 7), 2. 11. 2026:

| | Git Bash | PowerShell |
|---|---|---|
| `test_brzda.py`, 0.6.0 (základní testy) | 16 z 19 | 16 z 19 (bash s curl nebrzdí) |
| `test_brzda.py`, tato větev | 24 z 24 | 24 z 24 |
| `test_hlidac.py`, 0.6.0 | 39 z 59 | 0 z 59 (příkaz hooku se nespustí) |

Na macOS je pro 127.0.0.2 potřeba alias na lo0 (`sudo ifconfig lo0 alias 127.0.0.2 up`, stejně pro .3 a .4);
bez něj jde `test_brzda.py` pustit v Dockeru (`python:3.12-bookworm`).

Od 0.6.1 zapisuje `novy_projekt.py --hlidac` na Windows hook bez shellu (`command` + `args`), takže nezáleží na tom,
jestli hooky běží v Git Bashi, nebo v PowerShellu. `test_hlidac.py` zkouší tvar bez shellu vždy, shellový tvar jen mimo
Windows. Výsledky 0.6.1, 2. 11. 2026: macOS a Linux (Docker) `test_brzda.py` 24 z 24 (Linux), `test_hlidac.py` 69 z 69
přes bash i bez shellu. Na Windows zatím neověřeno.
