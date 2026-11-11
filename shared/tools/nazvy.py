"""Porovnávání názvů obcí v textech portálů: bez diakritiky a velikosti písmen, obec i v jiném pádě.

Původ: vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/nazvy.py), commit 32bef07; beze změny."""
import re, unicodedata


def bez_diakritiky(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def zminuje_obec(text, obec):
    """Obec jako slovo v textu, i v jiném pádě („ze Lniště“, „v Telči“, „pod Lhotou“), ne jiná obec
    s delším názvem nebo zdrobnělinou („Telčice“, „Lhotka“): koncovka pádu má nejvýš dvě písmena a začíná samohláskou.
    Pády se střídáním souhlásek („v Praze“) nepozná."""
    kmen = re.sub(r"[aeiouy]+$", "", bez_diakritiky(obec))
    return re.search(rf"\b{re.escape(kmen)}(?:[aeiouy][a-z]?)?\b", bez_diakritiky(text)) is not None
