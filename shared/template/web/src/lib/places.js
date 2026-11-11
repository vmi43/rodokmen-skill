// Původ: lib/places.js z dejiny-domu-skill (https://github.com/vzoha/dejiny-domu-skill, commit bda6028bae08307727a4449931497c9f163ea691). Beze změny.
// Druhy bodů na mapě (pole „druh“ v data/mista.json): název do legendy a barva.
// Pořadí = pořadí v legendě a v seznamu míst pod mapou.
export const PLACE_KINDS = {
  main: { name: 'Hlavní dům', color: '#d7302a' },
  house: { name: 'Další domy z dějin', color: '#EFB45F' },
  vira: { name: 'Kaple a kostely', color: '#8a5cb8' },
  pamatka: { name: 'Kříže a pomníky', color: '#4a4a4a' },
  remeslo: { name: 'Mlýny, hamry a řemesla', color: '#c0692b' },
  verejne: { name: 'Škola, hospoda a obecní místa', color: '#3f8f6b' },
  ves: { name: 'Sousední vsi', color: '#5b9bd5' },
  jine: { name: 'Další místa', color: '#86B8E8' },
};

// Od čeho se počítá vzdálenost v textu „… od návsi“ (2. pád; u města třeba 'náměstí' nebo 'středu obce').
export const STRED = 'návsi';

// Vzdálenost od středu obce (OBEC lat/lon) jako text („600 m od návsi“, „1,4 km od návsi“); blíž než 300 m = prázdné.
export function distText(village, p) {
  if (village?.lat == null || p?.lat == null) return '';
  const r = Math.PI / 180, dLat = (p.lat - village.lat) * r, dLon = (p.lon - village.lon) * r;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(village.lat * r) * Math.cos(p.lat * r) * Math.sin(dLon / 2) ** 2;
  const d = 12742 * Math.asin(Math.sqrt(h));
  return d <= 0.3 ? '' : d < 1 ? `${Math.round(d * 10) * 100} m od ${STRED}` : `${d.toFixed(1).replace('.', ',')} km od ${STRED}`;
}
