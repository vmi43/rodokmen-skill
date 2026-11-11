"""Vzdálenost dvou bodů v km (rovinná aproximace, na desítky km stačí).

Původ: vzoha/dejiny-domu-skill (skills/dejiny-domu/tools/vzdalenost.py), commit 32bef07; beze změny."""
import math


def km(lat, lon, lat2, lon2):
    return math.hypot((lon2 - lon) * 111.32 * math.cos(math.radians(lat)), (lat2 - lat) * 111.32)
