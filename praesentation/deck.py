# -*- coding: utf-8 -*-
"""Kurze Präsentation zur Deutschlandtabelle, A4 quer.

    python3 praesentation/deck.py              # alle drei Sportarten
    python3 praesentation/deck.py handball     # Fassung für den DHB
    python3 praesentation/deck.py basketball   # Fassung für den DBB

Die Zahlen und die Fundstücke auf Seite 4 holt das Skript von der
veröffentlichten Seite. So steht in der Unterlage immer der Stand von heute
und nicht der vom Tag, an dem sie zuletzt gesetzt wurde.
"""
import json
import sys
import urllib.request
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HIER = Path(__file__).resolve().parent
BILDER = HIER / "bilder"
QUELLE = "https://deutschlandtabelle.github.io"

# --- Die drei Fassungen ---------------------------------------------------
FASSUNGEN = {
    "allgemein": {
        "datei": "Deutschlandtabelle.pdf",
        "claim": "Der ganze Sport. Eine Tabelle.",
        "motiv": "00-motiv.jpg",
        "sportbild": "02-sportseite.jpg",
        "slugs": ["fussball", "fussball-frauen", "handball", "handball-frauen",
                  "basketball", "basketball-frauen"],
        "wer": "allen drei Sportarten",
        "zugang": "Entwurf1026#",
    },
    "handball": {
        "datei": "Deutschlandtabelle-Handball.pdf",
        "claim": "Der ganze Handball. Eine Tabelle.",
        "motiv": "10-handball.jpg",
        "sportbild": "11-handball-seite.jpg",
        "slugs": ["handball", "handball-frauen"],
        "wer": "im Handball",
        "zugang": "Entwurf1026#DHB",
    },
    "basketball": {
        "datei": "Deutschlandtabelle-Basketball.pdf",
        "claim": "Der ganze Basketball. Eine Tabelle.",
        "motiv": "20-basketball.jpg",
        "sportbild": "21-basketball-seite.jpg",
        "slugs": ["basketball", "basketball-frauen"],
        "wer": "im Basketball",
        "zugang": "Entwurf1026#DBB",
    },
}

INK = HexColor("#1d1d1f")
GRAU = HexColor("#6e6e73")
LINIE = HexColor("#d2d2d7")
GRUEN = HexColor("#1a6b3c")
FLAECHE = HexColor("#f5f5f7")
WEISS = HexColor("#ffffff")

B, H = landscape(A4)                       # 842 x 595 pt
RAND = 54

FETT, NORMAL = "Helvetica-Bold", "Helvetica"
for _name, _datei in (("DT", "/System/Library/Fonts/Supplemental/Arial.ttf"),
                      ("DT-Bold",
                       "/System/Library/Fonts/Supplemental/Arial Bold.ttf")):
    try:
        pdfmetrics.registerFont(TTFont(_name, _datei))
    except Exception:
        pass
if "DT-Bold" in pdfmetrics.getRegisteredFontNames():
    FETT, NORMAL = "DT-Bold", "DT"


# --- Daten ----------------------------------------------------------------
def hole(pfad: str):
    with urllib.request.urlopen(f"{QUELLE}/{pfad}", timeout=30) as antwort:
        return json.loads(antwort.read().decode("utf-8"))


def tausend(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def komma(text: str) -> str:
    """Englischer Dezimalpunkt zu deutschem Komma."""
    return text.replace(".", ",")


def daten_holen(slugs):
    """Eckzahlen und Fundstücke von der veröffentlichten Seite."""
    infos = {s: hole(f"data/{s}.info.json") for s in slugs}
    pakete = {s: hole(f"data/{s}.json") for s in slugs}
    eck = {
        "mannschaften": sum(i["teams"] for i in infos.values()),
        "staffeln": sum(i["leagues"] for i in infos.values()),
        "stufen": max(i["tiers"] for i in infos.values()),
        "rangfolgen": len(slugs),
        "saison": next(iter(infos.values()))["season"],
        "stand": next(iter(infos.values()))["generated"].split(",")[0],
    }

    def karte(slug, schluessel):
        for k in pakete[slug].get("kennzahlen", []):
            if k["key"] == schluessel:
                return k
        return None

    return eck, infos, pakete, karte


# --- Zeichnen -------------------------------------------------------------
def aufbau(c):
    def fusszeile(nr):
        c.setFont(NORMAL, 8.5)
        c.setFillColor(GRAU)
        c.drawString(RAND, 26, "deutschlandtabelle.github.io")
        c.drawRightString(B - RAND, 26, f"{nr}")

    def bild(pfad, x, y, breite, hoehe=None, rahmen=True):
        ir = ImageReader(str(pfad))
        bw, bh = ir.getSize()
        h = breite * bh / bw
        if hoehe and h > hoehe:
            c.saveState()
            form = c.beginPath()
            form.rect(x, y, breite, hoehe)
            c.clipPath(form, stroke=0)
            c.drawImage(ir, x, y + hoehe - h, width=breite, height=h, mask="auto")
            c.restoreState()
            h = hoehe
        else:
            c.drawImage(ir, x, y, width=breite, height=h, mask="auto")
        if rahmen:
            c.setStrokeColor(LINIE)
            c.setLineWidth(0.7)
            c.rect(x, y, breite, h, stroke=1, fill=0)
        return h

    def zeilen(text, x, y, breite, schrift=NORMAL, groesse=11.5,
               zeilenabstand=16, farbe=None):
        c.setFont(schrift, groesse)
        c.setFillColor(farbe or INK)
        aktuell = ""
        for wort in text.split(" "):
            probe = (aktuell + " " + wort).strip()
            if c.stringWidth(probe, schrift, groesse) > breite and aktuell:
                c.drawString(x, y, aktuell)
                y -= zeilenabstand
                aktuell = wort
            else:
                aktuell = probe
        if aktuell:
            c.drawString(x, y, aktuell)
            y -= zeilenabstand
        return y

    def kuerzen(text, schrift, groesse, breite):
        if c.stringWidth(text, schrift, groesse) <= breite:
            return text
        while text and c.stringWidth(text + "…", schrift, groesse) > breite:
            text = text[:-1]
        return text.rstrip(" .,·") + "…"

    def kachel(x, y, breite, hoehe, label, kopf, wert, fuss):
        c.setFillColor(FLAECHE)
        c.roundRect(x, y, breite, hoehe, 10, stroke=0, fill=1)
        c.setFont(NORMAL, 8)
        c.setFillColor(GRAU)
        c.drawString(x + 16, y + hoehe - 20,
                     kuerzen(label.upper(), NORMAL, 8, breite - 32))
        c.setFont(FETT, 14)
        c.setFillColor(INK)
        c.drawString(x + 16, y + hoehe - 40, kuerzen(kopf, FETT, 14, breite - 32))
        c.setFont(FETT, 11)
        c.setFillColor(GRUEN)
        c.drawString(x + 16, y + hoehe - 56, kuerzen(wert, FETT, 11, breite - 32))
        c.setFont(NORMAL, 8.5)
        c.setFillColor(GRAU)
        c.drawString(x + 16, y + hoehe - 71, kuerzen(fuss, NORMAL, 8.5, breite - 32))

    def rundes_bild(pfad, mx, my, radius):
        ir = ImageReader(str(pfad))
        bw, bh = ir.getSize()
        skala = max(2 * radius / bw, 2 * radius / bh)
        c.saveState()
        form = c.beginPath()
        form.circle(mx, my, radius)
        c.clipPath(form, stroke=0)
        c.drawImage(ir, mx - bw * skala / 2, my - bh * skala / 2,
                    width=bw * skala, height=bh * skala, mask="auto")
        c.restoreState()
        c.setStrokeColor(LINIE)
        c.setLineWidth(1)
        c.circle(mx, my, radius, stroke=1, fill=0)

    return fusszeile, bild, zeilen, kachel, rundes_bild


def bauen(name: str):
    f = FASSUNGEN[name]
    eck, infos, pakete, karte = daten_holen(f["slugs"])
    ziel = HIER / f["datei"]
    c = canvas.Canvas(str(ziel), pagesize=(B, H))
    c.setTitle(f"Deutschlandtabelle — {f['claim']}")
    c.setAuthor("Dominik Orbach")
    c.setSubject("Sichtbarkeit für den Amateursport")
    fusszeile, bild, zeilen, kachel, rundes_bild = aufbau(c)

    # --------------------------------------------------------------- Seite 1
    BAND = 268
    bild(BILDER / f["motiv"], 0, H - BAND, B, BAND, rahmen=False)
    c.setFont(FETT, 44)
    c.setFillColor(INK)
    c.drawString(RAND, H - BAND - 70, "Deutschlandtabelle")
    c.setFont(NORMAL, 21)
    c.setFillColor(GRUEN)
    c.drawString(RAND, H - BAND - 100, f["claim"])
    zeilen("Alle Vereine, alle Ligen in einer einzigen deutschlandweiten "
           "Reihenfolge: von der ersten Liga bis zur Kreisklasse, Männer und "
           "Frauen getrennt. Täglich neu gerechnet aus den Ergebnissen der "
           "laufenden Saison.",
           RAND, H - BAND - 138, 520, groesse=12.5, zeilenabstand=18, farbe=GRAU)
    c.setFont(FETT, 14)
    c.setFillColor(INK)
    c.drawString(RAND, 62, "deutschlandtabelle.github.io")
    fusszeile(1)
    c.showPage()

    # --------------------------------------------------------------- Seite 2
    c.setFillColor(INK)
    c.setFont(FETT, 26)
    c.drawString(RAND, H - 70, "Was es ist")
    zeilen("Eine einzige Rangfolge statt tausender getrennter Tabellen. "
           "Sortiert wird zuerst nach Ligastufe, innerhalb einer Stufe nach "
           "Punkten pro Spiel — dadurch verzahnen sich parallele Staffeln zu "
           "einer echten Reihenfolge, vom Meister bis zum Letzten der "
           "Kreisklasse.",
           RAND, H - 100, 386, groesse=12, farbe=GRAU)

    zahlen = [(tausend(eck["mannschaften"]), "Mannschaften"),
              (tausend(eck["staffeln"]), "Staffeln"),
              (str(eck["stufen"]), "Ligastufen"),
              (str(eck["rangfolgen"]), "Rangfolgen")]
    x = RAND
    for wert, wort in zahlen:
        c.setFillColor(FLAECHE)
        c.roundRect(x, H - 290, 92, 86, 10, stroke=0, fill=1)
        c.setFont(FETT, 22)
        c.setFillColor(INK)
        c.drawCentredString(x + 46, H - 250, wert)
        c.setFont(NORMAL, 9)
        c.setFillColor(GRAU)
        c.drawCentredString(x + 46, H - 272, wort)
        x += 104

    if name == "allgemein":
        satz = ("Drei Sportarten, Männer und Frauen getrennt — sie spielen "
                "getrennte Pyramiden mit eigenen Auf- und Abstiegsketten.")
    else:
        satz = (f"Die Zahlen oben stehen für die Rangfolgen {f['wer']}, "
                "Männer und Frauen getrennt. Dieselbe Rechnung läuft für "
                "Fußball und die jeweils anderen Sportarten.")
    zeilen(satz + f" Stand der Daten: {eck['stand']}, Saison {eck['saison']}.",
           RAND, H - 325, 386, groesse=11, farbe=GRAU)
    bild(BILDER / "04-karte.jpg", 470, 96, 318, 300)
    fusszeile(2)
    c.showPage()

    # --------------------------------------------------------------- Seite 3
    c.setFillColor(INK)
    c.setFont(FETT, 26)
    c.drawString(RAND, H - 70, "Wonach Menschen suchen")
    zeilen("„Wo steht mein Verein?“ ist die Frage, die den Amateursport "
           "bewegt — und die keine Ligatabelle beantwortet, weil sie an der "
           "Staffelgrenze endet.",
           RAND, H - 100, 386, groesse=12, farbe=GRAU)

    c.setFillColor(FLAECHE)
    c.roundRect(RAND, H - 336, 386, 196, 12, stroke=0, fill=1)
    c.setFont(FETT, 12)
    c.setFillColor(GRUEN)
    c.drawString(RAND + 22, H - 175, "Das Vorbild: der TTR-Wert im Tischtennis")
    zeilen("Seit 2011 trägt dort jede Spielerin und jeder Spieler, die im "
           "Verbandsportal click-TT geführt werden, eine persönliche Zahl. "
           "Sie wird täglich fortgeschrieben, vierteljährlich eingefroren — "
           "und entscheidet dann über Aufstellungsreihenfolge und "
           "Turniereinstufung. Eine Zahl, die über Liga- und Vereinsgrenzen "
           "hinweg vergleicht.",
           RAND + 22, H - 198, 344, groesse=10.5, zeilenabstand=14.5, farbe=GRAU)
    zeilen("Die Deutschlandtabelle überträgt diesen Gedanken auf die "
           "Mannschaft.",
           RAND + 22, H - 312, 344, schrift=FETT, groesse=10.5, farbe=INK)
    bild(BILDER / f["sportbild"], 470, 96, 318, 300)
    fusszeile(3)
    c.showPage()

    # --------------------------------------------------------------- Seite 4
    c.setFillColor(INK)
    c.setFont(FETT, 26)
    c.drawString(RAND, H - 70, "Wie es gemacht ist")
    punkte = [
        ("Offene Quellen, benannt",
         "Jede Zeile der frei abrufbaren CSV-Dateien nennt ihre Herkunft."),
        ("Geprüft, bevor es erscheint",
         "Rund zwanzig Prüfungen je Rangfolge: Torsummen, Spielzahlen, "
         "Tabellenplätze, Sortierung. Fällt eine durch, bleibt der letzte "
         "geprüfte Stand stehen."),
        ("Keine Messung, keine Werbung",
         "Keine Cookies, kein Tracker, keine Konten, keine fremden Server."),
        ("Ehrlich in den Grenzen",
         "Unterhalb der überregionalen Ligen verbindet keine Auf- und "
         "Abstiegskette die Verbände. Das steht auf jeder Sportseite."),
    ]
    y = H - 108
    for titel, text in punkte:
        c.setFillColor(GRUEN)
        c.circle(RAND + 4, y + 4, 3.2, stroke=0, fill=1)
        c.setFont(FETT, 11.5)
        c.setFillColor(INK)
        c.drawString(RAND + 16, y, titel)
        y = zeilen(text, RAND + 16, y - 16, 352, groesse=10,
                   zeilenabstand=13.5, farbe=GRAU) - 10

    c.setFont(NORMAL, 9)
    c.setFillColor(GRAU)
    c.drawString(455, H - 108, "AUS DER TABELLE VON HEUTE")

    def als_kachel(k, slug, platz):
        if not k:
            return
        info = infos[slug]
        kachel(455, platz, 333, 86, k["titel"], k["verein"], komma(k["wert"]),
               f"{k['liga']} · Ligastufe {k['stufe']} · "
               f"{info['sportName']} der {info['klasseName']}")

    erste, zweite = f["slugs"][0], f["slugs"][-1]
    als_kachel(karte(erste, "bester"), erste, H - 206)
    als_kachel(karte(erste, "torfabrik"), erste, H - 302)
    als_kachel(karte(zweite, "bester"), zweite, H - 398)

    beste = karte(erste, "bester")
    if beste and beste.get("stufe", 0) >= 5:
        c.setFont(NORMAL, 8.5)
        c.setFillColor(GRAU)
        c.drawString(455, H - 416, "Der beste Verein des Landes spielt in der "
                     f"Ligastufe {beste['stufe']}. Genau dafür ist die "
                     "Tabelle gebaut.")
    fusszeile(4)
    c.showPage()

    # --------------------------------------------------------------- Seite 5
    c.setFillColor(INK)
    c.setFont(FETT, 26)
    c.drawString(RAND, H - 70, "Worum es geht")
    c.setFont(FETT, 15)
    c.setFillColor(GRUEN)
    c.drawString(RAND, H - 100,
                 "Die Deutschlandtabelle schafft Sichtbarkeit für den "
                 "Amateursport.")
    zeilen("Von der ersten Liga bis zur Kreisklasse steht jede Mannschaft an "
           "einem Platz, den sonst niemand ausweist. Was dafür gezeigt wird, "
           "gehört den Verbänden — deshalb suche ich das Gespräch mit Ihnen, "
           "statt es zu vermeiden.",
           RAND, H - 128, 470, groesse=12, zeilenabstand=17, farbe=GRAU)
    zeilen("Die Seite ist heute ein Prototyp, gebaut von einer Person. Ich "
           "würde sie gern gemeinsam mit Ihnen aufbauen und weiterentwickeln.",
           RAND, H - 196, 470, schrift=FETT, groesse=12, zeilenabstand=17,
           farbe=INK)

    def aufruf(x, y, breite, nummer, titel, zeile1, zeile2):
        c.setStrokeColor(LINIE)
        c.setLineWidth(0.9)
        c.roundRect(x, y, breite, 104, 12, stroke=1, fill=0)
        c.setFillColor(GRUEN)
        c.circle(x + 26, y + 78, 10, stroke=0, fill=1)
        c.setFont(FETT, 10)
        c.setFillColor(WEISS)
        c.drawCentredString(x + 26, y + 74.5, nummer)
        c.setFont(FETT, 13)
        c.setFillColor(INK)
        c.drawString(x + 46, y + 73, titel)
        c.setFont(NORMAL, 10.5)
        c.setFillColor(GRAU)
        c.drawString(x + 46, y + 54, zeile1)
        c.setFont(FETT, 12)
        c.setFillColor(GRUEN)
        c.drawString(x + 46, y + 28, zeile2)

    aufruf(RAND, 132, 232, "1", "Ansehen",
           f"Zugangswort: {f['zugang']}", "deutschlandtabelle.github.io")
    aufruf(RAND + 248, 132, 232, "2", "Ansprechen",
           "Für alles Weitere brauche ich Sie.", "dominik.orbach@th-koeln.de")

    rundes_bild(BILDER / "05-portraet.jpg", 660, H - 230, 108)
    c.setFont(FETT, 15)
    c.setFillColor(INK)
    c.drawCentredString(660, H - 364, "Dominik Orbach")
    c.setFont(NORMAL, 11)
    c.setFillColor(GRAU)
    c.drawCentredString(660, H - 384, "Initiator der Deutschlandtabelle")
    c.drawCentredString(660, H - 402, "dominik.orbach@th-koeln.de")
    c.setFont(NORMAL, 9)
    c.drawCentredString(660, 60,
                        f"Stand der Daten: {eck['stand']} · Saison {eck['saison']}")
    fusszeile(5)
    c.showPage()

    c.save()
    print(f"geschrieben: {ziel.name}  "
          f"({tausend(eck['mannschaften'])} Mannschaften, Stand {eck['stand']})")


if __name__ == "__main__":
    welche = sys.argv[1] if len(sys.argv) > 1 else "allgemein"
    if welche not in FASSUNGEN:
        raise SystemExit(f"Unbekannt: {welche}. "
                         f"Möglich: {', '.join(FASSUNGEN)}")
    bauen(welche)
