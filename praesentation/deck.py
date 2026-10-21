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


def kachel(x, y, breite, hoehe, label, verein, wert, liga):
    """Eine Highlight-Kachel im Stil der Seite."""
    c.setFillColor(FLAECHE)
    c.roundRect(x, y, breite, hoehe, 10, stroke=0, fill=1)
    c.setFont(NORMAL, 8)
    c.setFillColor(GRAU)
    c.drawString(x + 16, y + hoehe - 20, label.upper())
    c.setFont(FETT, 14)
    c.setFillColor(INK)
    name = verein
    while c.stringWidth(name, FETT, 14) > breite - 32 and len(name) > 6:
        name = name[:-2]
    if name != verein:
        name = name.rstrip(" .") + "…"
    c.drawString(x + 16, y + hoehe - 40, name)
    c.setFont(FETT, 11)
    c.setFillColor(GRUEN)
    c.drawString(x + 16, y + hoehe - 56, wert)
    c.setFont(NORMAL, 8.5)
    c.setFillColor(GRAU)
    text = liga
    while c.stringWidth(text, NORMAL, 8.5) > breite - 32 and len(text) > 6:
        text = text[:-2]
    c.drawString(x + 16, y + hoehe - 71, text + ("…" if text != liga else ""))


def rundes_bild(pfad, mx, my, radius):
    """Porträt in einem Kreis."""
    ir = ImageReader(str(pfad))
    bw, bh = ir.getSize()
    kante = 2 * radius
    skala = max(kante / bw, kante / bh)
    c.saveState()
    pfadform = c.beginPath()
    pfadform.circle(mx, my, radius)
    c.clipPath(pfadform, stroke=0)
    c.drawImage(ir, mx - bw * skala / 2, my - bh * skala / 2,
                width=bw * skala, height=bh * skala, mask="auto")
    c.restoreState()
    c.setStrokeColor(LINIE)
    c.setLineWidth(1)
    c.circle(mx, my, radius, stroke=1, fill=0)



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
     "Jede Zeile der frei abrufbaren CSV-Dateien nennt ihre Herkunft."),
    ("Geprüft, bevor es erscheint",
     "Rund zwanzig Prüfungen je Rangfolge: Torsummen, Spielzahlen, "
     "Tabellenplätze, Sortierung. Fällt eine durch, bleibt der letzte "
     "geprüfte Stand stehen."),
    ("Keine Messung, keine Werbung",
     "Keine Cookies, kein Tracker, keine Konten, keine fremden Server."),
    ("Ehrlich in den Grenzen",
     "Unterhalb der Regionalliga verbindet keine Auf- und Abstiegskette die "
     "Verbände. Das steht auf jeder Sportseite."),
]
y = H - 108
for titel, text in punkte:
    c.setFillColor(GRUEN)
    c.circle(RAND + 4, y + 4, 3.2, stroke=0, fill=1)
    c.setFont(FETT, 11.5)
    c.setFillColor(INK)
    c.drawString(RAND + 16, y, titel)
    y = zeilen(text, RAND + 16, y - 16, 352, groesse=10, zeilenabstand=13.5,
               farbe=GRAU) - 10

# Was die Rangfolge sichtbar macht -- drei Funde von heute.
c.setFont(NORMAL, 9)
c.setFillColor(GRAU)
c.drawString(455, H - 108, "AUS DER TABELLE VON HEUTE")
kachel(455, H - 206, 333, 86, "Bester Verein Deutschlands",
       "GW Harsewinkel", "3,00 Punkte/Spiel",
       "Kreisliga C · Kreis Gütersloh · Ligastufe 11")
kachel(455, H - 302, 333, 86, "Die Korbfabrik",
       "Gladiators Trier", "100,00 Körbe/Spiel",
       "1. Bundesliga · Ligastufe 1")
kachel(455, H - 398, 333, 86, "DFB-Pokal, größter Abstand",
       "99 Plätze", "SSV Jeddeloh II gegen Hertha BSC",
       "Rang 118 gegen Rang 19 der Deutschlandtabelle")
c.setFont(NORMAL, 8.5)
c.setFillColor(GRAU)
c.drawString(455, H - 416, "Der beste Verein des Landes spielt in der "
             "Kreisliga C. Genau dafür ist die Tabelle gebaut.")
fusszeile(4)
c.showPage()

# ------------------------------------------------------------------ Seite 5
c.setFillColor(INK)
c.setFont(FETT, 26)
c.drawString(RAND, H - 70, "Worum es geht")
c.setFont(FETT, 15)
c.setFillColor(GRUEN)
c.drawString(RAND, H - 100, "Die Deutschlandtabelle schafft Sichtbarkeit für "
             "den Amateursport.")
zeilen("Von der Bundesliga bis zur Kreisklasse steht jede Mannschaft an einem "
       "Platz, den sonst niemand ausweist. Was dafür gezeigt wird, gehört den "
       "Verbänden — deshalb suche ich das Gespräch mit Ihnen, statt es zu "
       "vermeiden.",
       RAND, H - 128, 470, groesse=12, zeilenabstand=17, farbe=GRAU)
zeilen("Die Seite ist heute ein Prototyp, gebaut von einer Person. Ich würde "
       "sie gern gemeinsam mit Ihnen aufbauen und weiterentwickeln.",
       RAND, H - 196, 470, schrift=FETT, groesse=12, zeilenabstand=17,
       farbe=INK)

# --- Zwei Wege, die offen stehen
def aufruf(x, y, breite, nummer, titel, zeile1, zeile2):
    c.setStrokeColor(LINIE)
    c.setLineWidth(0.9)
    c.roundRect(x, y, breite, 104, 12, stroke=1, fill=0)
    c.setFillColor(GRUEN)
    c.circle(x + 26, y + 78, 10, stroke=0, fill=1)
    c.setFont(FETT, 10)
    c.setFillColor(HexColor("#ffffff"))
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
       "Der Pilot läuft — schauen Sie hinein.", "deutschlandtabelle.github.io")
aufruf(RAND + 248, 132, 232, "2", "Ansprechen",
       "Für alles Weitere brauche ich Sie.", "dominik.orbach@th-koeln.de")

# --- Porträt
rundes_bild(BILDER / "05-portraet.jpg", 660, H - 230, 108)
c.setFont(FETT, 15)
c.setFillColor(INK)
c.drawCentredString(660, H - 364, "Dominik Orbach")
c.setFont(NORMAL, 11)
c.setFillColor(GRAU)
c.drawCentredString(660, H - 384, "Initiator der Deutschlandtabelle")
c.drawCentredString(660, H - 402, "dominik.orbach@th-koeln.de")
c.setFont(NORMAL, 9)
c.drawCentredString(660, 60, "Stand der Daten: 20.10.2026 · Saison 2026/27")
fusszeile(5)
c.showPage()

c.save()
print("geschrieben:", ZIEL)
