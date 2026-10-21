# -*- coding: utf-8 -*-
"""Kurze Präsentation zur Deutschlandtabelle, A4 quer."""
from pathlib import Path
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BILDER = Path(__file__).parent / "bilder"
ZIEL = Path(__file__).parent / "Deutschlandtabelle.pdf"
B, H = landscape(A4)                       # 842 x 595 pt

INK   = HexColor("#1d1d1f")
GRAU  = HexColor("#6e6e73")
LINIE = HexColor("#d2d2d7")
GRUEN = HexColor("#1a6b3c")
FLAECHE = HexColor("#f5f5f7")

# Helvetica trägt alle Umlaute; für den Schriftzug reicht sie.
FETT, NORMAL = "Helvetica-Bold", "Helvetica"
for name, datei in (("DT", "/System/Library/Fonts/Supplemental/Arial.ttf"),
                    ("DT-Bold", "/System/Library/Fonts/Supplemental/Arial Bold.ttf")):
    try:
        pdfmetrics.registerFont(TTFont(name, datei))
    except Exception:
        pass
if "DT-Bold" in pdfmetrics.getRegisteredFontNames():
    FETT, NORMAL = "DT-Bold", "DT"

c = canvas.Canvas(str(ZIEL), pagesize=(B, H))
c.setTitle("Deutschlandtabelle — der ganze Sport. Eine Tabelle.")
c.setAuthor("Dominik Orbach")
c.setSubject("Jeder Verein des Landes in einer Rangfolge")

RAND = 54


def fusszeile(nr):
    c.setFont(NORMAL, 8.5)
    c.setFillColor(GRAU)
    c.drawString(RAND, 26, "deutschlandtabelle.github.io")
    c.drawRightString(B - RAND, 26, f"{nr}")


def bild(pfad, x, y, breite, hoehe=None, rahmen=True):
    """Bild einpassen, Seitenverhältnis bleibt erhalten."""
    ir = ImageReader(str(pfad))
    bw, bh = ir.getSize()
    h = breite * bh / bw
    if hoehe and h > hoehe:                 # oben beschneiden statt stauchen
        c.saveState()
        p = c.beginPath()
        p.rect(x, y, breite, hoehe)
        c.clipPath(p, stroke=0)
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


def zeilen(text, x, y, breite, schrift=NORMAL, groesse=11.5, zeilenabstand=16,
           farbe=None):
    c.setFont(schrift, groesse)
    c.setFillColor(farbe or INK)
    wort, aktuell = text.split(" "), ""
    for w in wort:
        probe = (aktuell + " " + w).strip()
        if c.stringWidth(probe, schrift, groesse) > breite and aktuell:
            c.drawString(x, y, aktuell)
            y -= zeilenabstand
            aktuell = w
        else:
            aktuell = probe
    if aktuell:
        c.drawString(x, y, aktuell)
        y -= zeilenabstand
    return y


# ------------------------------------------------------------------ Seite 1
BAND = 268
bild(BILDER / "00-motiv.jpg", 0, H - BAND, B, BAND, rahmen=False)
c.setFont(FETT, 44)
c.setFillColor(INK)
c.drawString(RAND, H - BAND - 70, "Deutschlandtabelle")
c.setFont(NORMAL, 21)
c.setFillColor(GRUEN)
c.drawString(RAND, H - BAND - 100, "Der ganze Sport. Eine Tabelle.")
zeilen("Alle Vereine, alle Ligen in einer einzigen deutschlandweiten "
       "Reihenfolge: von der ersten Liga bis zur Kreisklasse, Männer und "
       "Frauen getrennt, in Fußball, Handball und Basketball. Täglich neu "
       "gerechnet aus den Ergebnissen der laufenden Saison.",
       RAND, H - BAND - 138, 520, groesse=12.5, zeilenabstand=18, farbe=GRAU)
c.setFont(FETT, 14)
c.setFillColor(INK)
c.drawString(RAND, 62, "deutschlandtabelle.github.io")
fusszeile(1)
c.showPage()

# ------------------------------------------------------------------ Seite 2
c.setFillColor(INK)
c.setFont(FETT, 26)
c.drawString(RAND, H - 70, "Was es ist")
zeilen("Eine einzige Rangfolge statt tausender getrennter Tabellen. Sortiert "
       "wird zuerst nach Ligastufe, innerhalb einer Stufe nach Punkten pro "
       "Spiel — dadurch verzahnen sich parallele Staffeln zu einer echten "
       "Reihenfolge, vom Meister bis zum Letzten der Kreisklasse.",
       RAND, H - 100, 386, groesse=12, farbe=GRAU)

zahlen = [("36.644", "Mannschaften"), ("2.948", "Staffeln"),
          ("14", "Ligastufen"), ("6", "Rangfolgen")]
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

zeilen("Drei Sportarten, Männer und Frauen getrennt — sie spielen getrennte "
       "Pyramiden mit eigenen Auf- und Abstiegsketten. Jede Rangfolge wird "
       "aus den Ergebnissen der laufenden Saison neu gerechnet.",
       RAND, H - 325, 386, groesse=11, farbe=GRAU)
bild(BILDER / "04-karte.jpg", 470, 96, 318, 300)
fusszeile(2)
c.showPage()

# ------------------------------------------------------------------ Seite 3
c.setFillColor(INK)
c.setFont(FETT, 26)
c.drawString(RAND, H - 70, "Wonach Menschen suchen")
zeilen("„Wo steht mein Verein?“ ist die Frage, die den Amateursport bewegt — "
       "und die keine Ligatabelle beantwortet, weil sie an der Staffelgrenze "
       "endet.", RAND, H - 100, 386, groesse=12, farbe=GRAU)

c.setFillColor(FLAECHE)
c.roundRect(RAND, H - 336, 386, 196, 12, stroke=0, fill=1)
c.setFont(FETT, 12)
c.setFillColor(GRUEN)
c.drawString(RAND + 22, H - 175, "Das Vorbild: der TTR-Wert im Tischtennis")
zeilen("Seit 2011 trägt dort jede Spielerin und jeder Spieler, die im "
       "Verbandsportal click-TT geführt werden, eine persönliche Zahl. Sie "
       "wird täglich fortgeschrieben, vierteljährlich eingefroren — und "
       "entscheidet dann über Aufstellungsreihenfolge und Turniereinstufung. "
       "Eine Zahl, die über Liga- und Vereinsgrenzen hinweg vergleicht.",
       RAND + 22, H - 198, 344, groesse=10.5, zeilenabstand=14.5, farbe=GRAU)
zeilen("Die Deutschlandtabelle überträgt diesen Gedanken auf die Mannschaft.",
       RAND + 22, H - 312, 344, schrift=FETT, groesse=10.5, farbe=INK)

bild(BILDER / "02-sportseite.jpg", 470, 96, 318, 300)
fusszeile(3)
c.showPage()

# ------------------------------------------------------------------ Seite 4
c.setFillColor(INK)
c.setFont(FETT, 26)
c.drawString(RAND, H - 70, "Wie es gemacht ist")
punkte = [
    ("Offene Quellen, benannt",
     "Jede Zeile der frei abrufbaren CSV-Dateien nennt ihre Herkunft. "
     "OpenLigaDB steht unter ODbL und wird als solche ausgewiesen."),
    ("Geprüft, bevor es erscheint",
     "Rund zwanzig Prüfungen je Rangfolge: Torsummen, Spielzahlen, "
     "Tabellenplätze, Sortierung. Fällt eine Rangfolge durch eine der "
     "harten, bleibt sie auf dem letzten geprüften Stand."),
    ("Keine Messung, keine Werbung",
     "Keine Cookies, kein Tracker, keine Konten, keine fremden Server — "
     "Schriften und Vereinswappen liegen auf der Seite selbst."),
    ("Ehrlich in den Grenzen",
     "Unterhalb der Regionalliga verbindet keine Auf- und Abstiegskette die "
     "Verbände. Das steht auf jeder Sportseite, statt es zu verschweigen."),
]
y = H - 108
for titel, text in punkte:
    c.setFillColor(GRUEN)
    c.circle(RAND + 4, y + 4, 3.2, stroke=0, fill=1)
    c.setFont(FETT, 12)
    c.setFillColor(INK)
    c.drawString(RAND + 16, y, titel)
    y = zeilen(text, RAND + 16, y - 17, 386, groesse=10.5, zeilenabstand=14,
               farbe=GRAU) - 12
bild(BILDER / "03-tabelle.jpg", 470, 96, 318, 300)
fusszeile(4)
c.showPage()

# ------------------------------------------------------------------ Seite 5
c.setFillColor(INK)
c.setFont(FETT, 26)
c.drawString(RAND, H - 70, "Worum es geht")
zeilen("Die Deutschlandtabelle ist ein privates, nicht-kommerzielles Projekt. "
       "Sie verkauft nichts, zeigt keine Werbung und verlangt keine Anmeldung. "
       "Was sie zeigt, gehört den Verbänden — deshalb sucht sie das Gespräch "
       "mit ihnen, statt es zu vermeiden.",
       RAND, H - 100, 640, groesse=12.5, zeilenabstand=18, farbe=GRAU)

kasten = [
    ("Für Vereine", "Der eigene Platz im Land, nicht nur in der Staffel."),
    ("Für Verbände", "Ein Schaufenster für die Breite des eigenen Spielbetriebs."),
    ("Für die Daten", "Namensnennung, Nachvollziehbarkeit, keine Weiterverwertung."),
]
x = RAND
for titel, text in kasten:
    c.setStrokeColor(LINIE)
    c.setLineWidth(0.8)
    c.roundRect(x, H - 296, 236, 112, 12, stroke=1, fill=0)
    c.setFont(FETT, 12)
    c.setFillColor(GRUEN)
    c.drawString(x + 18, H - 212, titel)
    zeilen(text, x + 18, H - 234, 200, groesse=10.5, zeilenabstand=14, farbe=GRAU)
    x += 252

c.setFillColor(FLAECHE)
c.roundRect(RAND, 120, 734, 96, 12, stroke=0, fill=1)
c.setFont(FETT, 15)
c.setFillColor(INK)
c.drawString(RAND + 24, 180, "deutschlandtabelle.github.io")
c.setFont(NORMAL, 11.5)
c.setFillColor(GRAU)
c.drawString(RAND + 24, 158, "Dominik Orbach · dominik.orbach@th-koeln.de")
c.drawString(RAND + 24, 138, "Stand der Daten: 20.10.2026 · Saison 2026/27")
fusszeile(5)
c.showPage()

c.save()
print("geschrieben:", ZIEL)
