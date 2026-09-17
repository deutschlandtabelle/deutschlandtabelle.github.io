#!/usr/bin/env python3
"""Headerbilder aus dem Projektordner nach docs/ übernehmen.

    python3 bilder.py

Legt einfach eine Datei im Projektordner ab und ruf das Skript auf:

    clubrank_fußball.png     ->  docs/header-fussball.jpg
    clubrank_handball.png    ->  docs/header-handball.jpg
    clubrank_basketball.png  ->  docs/header-basketball.jpg
    clubrank_home.png        ->  docs/header.jpg        (Startseite)

Aus dem Startmotiv entsteht zusätzlich docs/teaser.jpg -- das Bild, das
Messenger beim Teilen eines Links zeigen.

Die Bilder werden dabei auf 1800 px Breite gebracht und als JPEG gespeichert.
Ein unbearbeitetes PNG wiegt schnell zwei Megabyte -- als JPEG sind es rund
250 KB, und der Header lädt bei jedem Seitenaufruf mit.

Gewandelt wird mit `sips`, das auf macOS mitgeliefert wird.
"""
from __future__ import annotations

import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
BREITE = 1800
QUALITAET = 82

# Das Teaserbild ist der Ausschnitt, den Messenger beim Teilen eines Links
# zeigen. Sie erwarten ungefähr 1,91:1; das Startmotiv ist höher. Geschnitten
# wird deshalb vom oberen Rand aus -- dort sind die Gesichter.
TEASER_SEITEN = 1.91
TEASER_OBEN = 0.02              # Abstand von oben, Anteil der Höhe
TEASER_DATEI = "teaser.jpg"

# Dateiname (ohne "clubrank_") -> Zieldatei in docs/
ZIELE = {
    "fussball": "header-fussball.jpg",
    "handball": "header-handball.jpg",
    "basketball": "header-basketball.jpg",
    # Eigene Motive für die Frauenklassen. Fehlen sie, greift die Seite von
    # selbst auf das Bild der Sportart zurück -- es muss also keins geben.
    "fussball-frauen": "header-fussball-frauen.jpg",
    "handball-frauen": "header-handball-frauen.jpg",
    "basketball-frauen": "header-basketball-frauen.jpg",
    "home": "header.jpg",
    "start": "header.jpg",
    "startbild": "header.jpg",
    "alle": "header.jpg",
}


def schluessel(name: str) -> str:
    """Dateiname -> Zielschlüssel.

    Erkannt werden beide Schreibweisen, die sich eingebürgert haben:
    "clubrank_fußball.png" und "Fußball_header.png" meinen dasselbe.
    ß und Umlaute werden vereinheitlicht.
    """
    text = name.lower().removeprefix("clubrank_").removeprefix("clubrank-")
    text = text.replace("ß", "ss").replace("ä", "ae").replace("ö", "oe")
    text = text.replace("ü", "ue")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    # "clubrank_fussball_frauen" und "clubrank_fussball-frauen" meinen dasselbe.
    text = text.replace("_", "-")
    # "header" darf vorn oder hinten stehen und wird abgeschnitten.
    for teil in ("-header", "header-"):
        text = text.removesuffix(teil) if teil.startswith("-") \
            else text.removeprefix(teil)
    # Angehängte Ziffern erlauben mehrere Anläufe für dasselbe Motiv:
    # "clubrank_handball2" landet ebenfalls bei header-handball.jpg.
    return text.strip("-").rstrip("0123456789 -")


def _masse(datei: Path) -> tuple[int, int]:
    werte = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight",
                            str(datei)], capture_output=True, text=True).stdout
    zahlen = [int(z.split(":")[-1]) for z in werte.splitlines() if "pixel" in z]
    return (zahlen[0], zahlen[1]) if len(zahlen) == 2 else (0, 0)


def _zuschneiden(quelle: Path, ziel: Path, breite: int, hoehe: int,
                 oben: int = 0, links: int = 0) -> bool:
    """Ausschnitt ab der linken oberen Ecke (oben, links).

    Zur Eigenheit von `sips --cropOffset`, ausgemessen statt vermutet:
    mit `0 0` schneidet es aus der **Bildmitte**, mit jedem anderen Wertepaar
    dagegen **absolut ab der linken oberen Ecke** (Reihenfolge: oben, links).
    Negative Werte laufen ins Leere und erzeugen schwarze Ränder. Für den
    Fall "genau in der Ecke" wird deshalb um ein Pixel nach rechts gerückt --
    das ist unsichtbar und umgeht den Sonderfall.
    """
    if oben == 0 and links == 0:
        links = 1
    lauf = subprocess.run(
        ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "88",
         "--cropToHeightWidth", str(hoehe), str(breite),
         "--cropOffset", str(oben), str(links),
         str(quelle), "--out", str(ziel)],
        capture_output=True, text=True)
    return lauf.returncode == 0 and ziel.exists()


def teaser(quelle: Path) -> None:
    """Das Bild für die Teilen-Vorschau aus dem Startmotiv schneiden."""
    b, h = _masse(quelle)
    if not b:
        return
    ziel = DOCS / TEASER_DATEI
    oben = int(h * TEASER_OBEN)
    hoehe = min(h - oben, int(b / TEASER_SEITEN))
    if _zuschneiden(quelle, ziel, b, hoehe, oben, 0):
        print(f"  ok {quelle.name} -> docs/{TEASER_DATEI} "
              f"({ziel.stat().st_size / 1024:.0f} KB, Teilen-Vorschau)",
              file=sys.stderr)


def main() -> int:
    DOCS.mkdir(parents=True, exist_ok=True)
    gefunden = [p for p in ROOT.iterdir()
                if p.is_file()
                and p.suffix.lower() in (".png", ".jpg", ".jpeg")
                and schluessel(p.stem) in ZIELE]

    # Zeigen zwei Vorlagen auf dasselbe Ziel ("clubrank_home.png" und
    # "Startbild_header.png"), gewinnt die zuletzt abgelegte. Nach dem
    # Dateinamen zu sortieren wäre Zufall -- und der Zufall hat hier schon
    # einmal das alte Motiv über das neue geschrieben.
    # Gruppiert wird nach dem ZIEL, nicht nach dem Schlüssel: "startbild"
    # und "home" sind zwei Schlüssel, meinen aber dieselbe Datei.
    beste: dict[str, Path] = {}
    for datei in gefunden:
        ziel = ZIELE[schluessel(datei.stem)]
        if ziel not in beste or datei.stat().st_mtime > beste[ziel].stat().st_mtime:
            beste[ziel] = datei
    for datei in sorted(gefunden):
        ziel = ZIELE[schluessel(datei.stem)]
        if beste[ziel] != datei:
            print(f"  -  {datei.name}: übergangen, {beste[ziel].name} "
                  f"ist neuer ({ziel})", file=sys.stderr)
    quellen = sorted(beste.values())

    # Vorlagen gehören nicht nach docs/: was dort liegt, wird veröffentlicht.
    # Ein unbearbeitetes PNG wiegt zwei Megabyte und wird von keiner Seite
    # geladen -- deshalb hier ein deutlicher Hinweis statt stillem Übergehen.
    verirrt = [p for p in DOCS.iterdir()
               if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg")
               and schluessel(p.stem) in ZIELE
               and not p.name.startswith(("header", "teaser"))]
    if verirrt:
        print("  !  Diese Vorlagen liegen in docs/ und würden mit "
              "veröffentlicht werden:", file=sys.stderr)
        for p in verirrt:
            print(f"       {p.name}  ->  gehört in den Projektordner",
                  file=sys.stderr)
    if not quellen:
        print("Keine Datei clubrank_*.png im Projektordner gefunden.", file=sys.stderr)
        print("Erwartet werden: " + ", ".join(f"clubrank_{k}" for k in
                                              ("fussball", "handball", "basketball", "home")),
              file=sys.stderr)
        return 1

    fehler = 0
    for quelle in quellen:
        ziel_name = ZIELE.get(schluessel(quelle.stem))
        if not ziel_name:
            print(f"  ?  {quelle.name}: kein Ziel bekannt — übersprungen",
                  file=sys.stderr)
            continue
        ziel = DOCS / ziel_name
        # Nur verkleinern, nie vergrößern -- Hochskalieren macht das Bild
        # weich, ohne einen einzigen Bildpunkt hinzuzugewinnen.
        befehl = ["sips", "-s", "format", "jpeg",
                  "-s", "formatOptions", str(QUALITAET)]
        try:
            breite_quelle = int(subprocess.run(
                ["sips", "-g", "pixelWidth", str(quelle)],
                capture_output=True, text=True).stdout.split(":")[-1].strip())
        except (ValueError, IndexError):
            breite_quelle = 0
        if breite_quelle > BREITE:
            befehl += ["--resampleWidth", str(BREITE)]
        befehl += [str(quelle), "--out", str(ziel)]
        ergebnis = subprocess.run(befehl, capture_output=True, text=True)
        if ergebnis.returncode != 0 or not ziel.exists():
            print(f"  !  {quelle.name}: {ergebnis.stderr.strip()[:120]}", file=sys.stderr)
            fehler += 1
            continue
        vorher = quelle.stat().st_size / 1024
        nachher = ziel.stat().st_size / 1024
        print(f"  ok {quelle.name} -> docs/{ziel_name} "
              f"({vorher:.0f} KB -> {nachher:.0f} KB)", file=sys.stderr)
        if ziel_name == "header.jpg":
            teaser(quelle)
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
