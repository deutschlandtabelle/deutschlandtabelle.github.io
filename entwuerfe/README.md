# Entwürfe

Zwei vollständige Gestaltungsentwürfe für ClubRank. Beide sind **lokal**, sie
liegen nicht in `docs/` und werden nicht veröffentlicht.

| Datei | Vorbild | Kurz |
|---|---|---|
| `apple.html` | apple.com/de | Weiß, mittig, sehr große Schrift, viel Luft, Haarlinien |
| `allianz.html` | allianz.de | Dunkelblau, linksbündig, Module mit Rahmen, dichte Tabelle |

Beide ziehen **echte Daten** aus `../docs/data/` — dieselben Zahlen, Wappen und
Bestenlisten wie die Seite selbst. Deshalb brauchen sie einen Server, der das
Projektverzeichnis ausliefert (nicht nur `docs/`):

```
python3 -m http.server 8902
```

Dann `http://localhost:8902/entwuerfe/apple.html` bzw. `.../allianz.html`
öffnen. Unten rechts führt ein Knopf zum jeweils anderen Entwurf.

Die Icons kommen aus `ikonen.js`, erzeugt aus `ranking/ikonen.py`:

```
python3 entwuerfe/bauen.py
```
