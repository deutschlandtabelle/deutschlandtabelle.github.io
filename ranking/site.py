"""Das Seitengerüst: eine Seite, vier Ansichten über die Adresszeile.

    #home        Marke, Beschreibung, Überblick über die Sportarten
    #fussball    Bestenlisten und komplette Tabelle
    #handball    dito
    #basketball  dito

Warum eine einzige Seite: so lauten die Adressen wie gewünscht
`.../#fussball`. Die Daten je Sportart liegen aber nicht in dieser Datei,
sondern in `data/<sport>.json` und werden erst beim Wechsel geladen -- die
Fußballtabelle allein wiegt gut zwei Megabyte, alle drei eingebettet wären
unbenutzbar. Dadurch startet die Seite in Millisekunden und lädt nur, was
wirklich angesehen wird.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import ikonen, karte

# Für die Teilen-Vorschau braucht es vollständige Adressen -- relative Pfade
# lösen Messenger nicht auf.
BASIS_URL = "https://deutschlandtabelle.github.io/"

# Pflichtangaben für Impressum (§ 5 DDG, § 18 Abs. 2 MStV) und für den
# Verantwortlichen in der Datenschutzerklärung (Art. 13 DSGVO). Sie stehen
# hier an einer Stelle, weil beide Seiten dieselben Angaben brauchen.
#
# Solange etwas fehlt, zeigen beide Seiten einen deutlichen Hinweis statt einer
# halben Pflichtangabe: ein unvollständiges Impressum ist schlechter als ein
# erkennbar fehlendes, weil es Vollständigkeit vortäuscht.
BETREIBER = {
    "name": "",
    "strasse": "",
    "plz_ort": "",
    "land": "Deutschland",
    "email": "dominik.orbach@th-koeln.de",
}


def betreiber_vollstaendig() -> bool:
    return all(BETREIBER.get(f) for f in ("name", "strasse", "plz_ort", "email"))


def _anschrift_html() -> str:
    """Anschriftsblock -- oder ein offener Hinweis, solange etwas fehlt."""
    if betreiber_vollstaendig():
        return ("<address>" + "<br>".join(html_escape(BETREIBER[f]) for f in
                ("name", "strasse", "plz_ort", "land")) + "</address>")
    return ('<div class="luecke"><b>Name und Anschrift fehlen hier noch.</b> '
            '§ 5 DDG verlangt eine ladungsfähige Anschrift; bis sie eingetragen '
            'ist, ist dieses Impressum unvollständig. Erreichbar bin ich '
            'zuverlässig über die unten genannte E-Mail-Adresse — wer eine '
            'Anschrift benötigt, bekommt sie auf Anfrage.</div>')


def _kontakt_html() -> str:
    post = BETREIBER.get("email")
    if not post:
        return '<p class="luecke">E-Mail-Adresse fehlt noch.</p>'
    return (f'<p>E-Mail: <a href="mailto:{html_escape(post)}">'
            f'{html_escape(post)}</a></p>')


def html_escape(text: str) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))

TEMPLATE = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Deutschlandtabelle — der ganze Sport. Eine Tabelle.</title>
<meta name="description" content="Alle Vereine, alle Ligen in einer einzigartigen deutschlandweiten Reihenfolge. Von der ersten Liga bis zur Kreisklasse: Wo steht dein Verein in der Deutschlandtabelle im Fußball, Handball oder Basketball?">
<link rel="canonical" href="__URL__">

<!-- Vorschau beim Teilen. Ohne diese Angaben raten Messenger, was Titel und
     Bild sein sollen -- mit ihnen erscheint eine saubere Karte mit Marke,
     Beschreibung und Startbild. Das Bild braucht eine vollständige Adresse,
     relative Pfade werden hier nicht aufgelöst. -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="Deutschlandtabelle">
<meta property="og:locale" content="de_DE">
<meta property="og:url" content="__URL__">
<meta property="og:title" content="Deutschlandtabelle — der ganze Sport. Eine Tabelle.">
<meta property="og:description" content="Alle Vereine, alle Ligen in einer einzigartigen deutschlandweiten Reihenfolge. Von der ersten Liga bis zur Kreisklasse: Wo steht dein Verein in der Deutschlandtabelle im Fußball, Handball oder Basketball?">
<meta property="og:image" content="__URL____TEASER__?v=__BILDVERSION__">
<meta property="og:image:width" content="__BILDBREITE__">
<meta property="og:image:height" content="__BILDHOEHE__">
<meta property="og:image:alt" content="Jubelnde Mannschaft eines Amateurvereins nach dem Sieg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Deutschlandtabelle — der ganze Sport. Eine Tabelle.">
<meta name="twitter:description" content="Alle Vereine, alle Ligen in einer einzigartigen deutschlandweiten Reihenfolge. Von der ersten Liga bis zur Kreisklasse: Wo steht dein Verein in der Deutschlandtabelle im Fußball, Handball oder Basketball?">
<meta name="twitter:image" content="__URL____TEASER__?v=__BILDVERSION__">
<style>
/* ======================================================================
   Gestaltung nach dem Vorbild von apple.com/de: wenige Flächen, große
   ruhige Typografie, Haarlinien statt Kästen, Abschnitte über die volle
   Breite im Wechsel weiß und hellgrau. Die Farbe bleibt das Grün des
   Projekts -- Apples Grammatik, nicht Apples Palette.
   ====================================================================== */
:root{
  --ink:#1d1d1f; --muted:#6e6e73; --bg:#ffffff; --flaeche:#f5f5f7;
  --panel:#ffffff; --hair:#d2d2d7; --line:#d2d2d7;
  --accent:#1a6b3c; --accent-soft:#eaf3ee; --up:#137a3d; --down:#b02a2a;
  --schatten:0 4px 24px rgba(0,0,0,.06);
  --land:#e8e8ed; --landlinie:#c7c7cc;
  --t1:#0b3d91; --t2:#1a6b3c; --t3:#8a6100; --t4:#7a3aa8; --t5:#a3442c;
  --t6:#0d6b74; --t7:#7a5a1f; --t8:#8a2f5e; --t9:#3f5aa6; --t10:#5c6b1f;
  --t11:#6b4a8a; --t12:#1f6b5c; --t13:#8a4a2f; --t14:#4a4a6b;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ink:#f5f5f7; --muted:#a1a1a6; --bg:#000000; --flaeche:#161617;
    --panel:#1d1d1f; --hair:#38383a; --line:#38383a;
    --accent:#4ec27f; --accent-soft:#17301f; --up:#4ec27f; --down:#e8695f;
    --schatten:0 4px 24px rgba(0,0,0,.5);
    --land:#2c2c2e; --landlinie:#55555a;
    --t1:#6ea8ff; --t2:#4ec27f; --t3:#e0b453; --t4:#c194ea; --t5:#f0937a;
    --t6:#5ec9d4; --t7:#d9b26a; --t8:#ef8ab8; --t9:#8fa8ee; --t10:#b3c96a;
    --t11:#bfa0e0; --t12:#66c9b4; --t13:#e0a184; --t14:#a0a4d4;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);letter-spacing:-.01em;
  font:17px/1.47 -apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue",
       Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--accent)}
[hidden]{display:none!important}
.wrap{max-width:1000px;margin:0 auto;padding:0 22px 70px}
.mitte{max-width:1000px;margin:0 auto;padding:0 22px}
.schmal{max-width:720px}

/* --- Kopfleiste: schmal, durchscheinend, kleine Schrift ---------------- */
.topbar{position:sticky;top:0;z-index:20;height:48px;
  background:color-mix(in srgb,var(--bg) 72%,transparent);
  backdrop-filter:saturate(180%) blur(20px);
  -webkit-backdrop-filter:saturate(180%) blur(20px);
  border-bottom:1px solid var(--hair)}
.topbar .inner{max-width:1000px;margin:0 auto;padding:0 22px;height:48px;
  display:flex;align-items:center;gap:26px}
.brand{font-weight:600;font-size:16px;letter-spacing:-.02em;color:var(--ink);
  text-decoration:none;white-space:nowrap}
.brand span{color:var(--accent)}
.topbar nav{display:flex;gap:22px;margin-left:auto;align-items:center}
.topbar nav a{color:var(--ink);opacity:.86;text-decoration:none;font-size:12.5px;
  display:inline-flex;align-items:center;white-space:nowrap}
.topbar nav a:hover{opacity:1}
.topbar nav a[aria-current="page"]{color:var(--accent);opacity:1}
.topbar nav a.leer{opacity:.4}

/* --- Bänder über die volle Breite -------------------------------------- */
.band{padding:78px 0}
.band.grau{background:var(--flaeche)}
.band.eng{padding:54px 0}
.band.voll{padding:0}

/* --- Bühne -------------------------------------------------------------- */
.hero{position:relative;overflow:hidden;display:flex;align-items:center;
  justify-content:center;min-height:clamp(320px,42vw,500px);background:#111;
  border-radius:22px}
.hero.klein{min-height:clamp(220px,30vw,320px);border-radius:18px;
  margin:26px 0 0}
.hero img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
  object-position:50% 22%}
.hero .schleier{position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(0,0,0,.42) 0%,rgba(0,0,0,.28) 45%,
             rgba(0,0,0,.62) 100%)}
.hero .inhalt{position:relative;padding:34px 22px;color:#fff;text-align:center;
  width:100%}
.marke{margin:0;font-weight:600;line-height:1.05;letter-spacing:-.028em;
  font-size:clamp(38px,6.6vw,76px);text-shadow:0 2px 24px rgba(0,0,0,.4)}
.marke span{color:#8ff0b6}
.marke .ikon{width:.86em;height:.86em;margin-right:.24em;vertical-align:-.08em;
  color:#fff}
.claim{margin:14px auto 0;max-width:30ch;font-weight:400;
  font-size:clamp(18px,2.5vw,26px);line-height:1.25;letter-spacing:-.02em;
  text-shadow:0 1px 16px rgba(0,0,0,.45)}
.hero.klein .marke{font-size:clamp(28px,4.4vw,46px)}
.hero.klein .claim{font-size:clamp(14px,1.9vw,18px);margin-top:8px}
.platzhalter{position:absolute;inset:16px;border:1px dashed rgba(255,255,255,.4);
  border-radius:12px;display:flex;align-items:flex-start;justify-content:center;
  padding:14px;pointer-events:none}
.platzhalter em{font-style:normal;background:rgba(0,0,0,.45);
  color:rgba(255,255,255,.92);font-size:12px;line-height:1.5;text-align:center;
  padding:7px 12px;border-radius:8px}
.platzhalter code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:11.5px;background:rgba(255,255,255,.16);padding:1px 5px;
  border-radius:4px}

/* --- Überschriften und Fließtext --------------------------------------- */
.titel{text-align:center;font-size:clamp(28px,4.2vw,46px);font-weight:600;
  letter-spacing:-.025em;line-height:1.08;margin:0 0 12px}
.untertitel{text-align:center;color:var(--muted);font-size:19px;margin:0 auto;
  max-width:62ch;letter-spacing:-.01em}
.intro{margin:0 auto;max-width:64ch;text-align:center;font-size:19px;
  line-height:1.5}
.intro p{margin:0 0 14px}
.intro p:last-child{margin-bottom:0}
h2{margin:52px 0 6px;font-size:clamp(24px,3vw,34px);font-weight:600;
  letter-spacing:-.025em;line-height:1.12}
h2 + p.unter{margin:0 0 22px;color:var(--muted);font-size:17px}

/* --- Suche -------------------------------------------------------------- */
.suche{display:flex;gap:10px;flex-wrap:wrap;margin:30px auto 0;max-width:640px;
  justify-content:center}
.suche input{flex:1 1 260px;min-width:0;background:var(--panel);color:var(--ink);
  border:1px solid var(--hair);border-radius:12px;padding:13px 16px;font-size:16px}
.suche select{flex:0 0 auto}
.knopf{display:inline-block;background:var(--accent);color:#fff;border:0;
  border-radius:980px;padding:13px 24px;font-size:16px;font-weight:400;
  cursor:pointer;text-decoration:none;white-space:nowrap}
.knopf:hover{filter:brightness(1.08)}

/* --- Kacheln der Sportarten -------------------------------------------- */
.sportkarten{display:grid;gap:16px;margin:40px 0 0;
  grid-template-columns:repeat(auto-fit,minmax(290px,1fr))}
.sportkarte{background:var(--panel);border-radius:22px;padding:34px 28px 28px;
  text-decoration:none;color:var(--ink);display:flex;flex-direction:column;
  align-items:center;text-align:center;box-shadow:var(--schatten)}
.band.grau .sportkarte{background:var(--bg)}
.sportkarte .ic{line-height:1}
.sportkarte .ic .ikon{width:42px;height:42px;color:var(--accent)}
.sportkarte h3{margin:14px 0 0;font-size:25px;font-weight:600;
  letter-spacing:-.02em}
.sportkarte .zahl{font-size:40px;font-weight:600;letter-spacing:-.03em;
  color:var(--ink);margin:4px 0 0;line-height:1.05}
.sportkarte .klein{color:var(--muted);font-size:14px}
.sportkarte.leer{opacity:.55}
.sportkarte .klassen{display:block;width:100%;margin:22px 0 0;
  border-top:1px solid var(--hair)}
.klassenzeile{display:grid;grid-template-columns:1fr auto;gap:2px 14px;
  align-items:baseline;padding:14px 2px;border-bottom:1px solid var(--hair);
  text-decoration:none;color:var(--ink);text-align:left}
.klassenzeile .wer{grid-row:1}
.klassenzeile .zahl{grid-row:1;justify-self:end}
.klassenzeile .klein{grid-column:1/-1}
a.klassenzeile:hover .zahl{color:var(--accent)}
.klassenzeile .wer{font-size:15px;font-weight:500}
.klassenzeile .zahl{font-size:25px;font-weight:600;letter-spacing:-.025em;
  margin:0;line-height:1.1}
.klassenzeile .klein{display:block;font-size:13px;color:var(--muted);
  font-weight:400}
.klassenzeile.leer{opacity:.5}
/* Jede Kachel endet mit zwei Knöpfen -- die Zeilen darüber sind zwar auch
   anklickbar, aber das sieht man ihnen nicht an. */
.kachelknoepfe{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;
  margin:22px 0 0;width:100%}
.kachelknoepfe .knopf{padding:10px 20px;font-size:15px}
.kachelknoepfe .knopf.zweit{background:var(--panel);color:var(--accent);
  box-shadow:inset 0 0 0 1px var(--accent)}
.band.grau .kachelknoepfe .knopf.zweit{background:var(--bg)}
.kachelknoepfe .knopf.zweit:hover{background:var(--accent-soft);filter:none}
.kachelknoepfe .knopf.aus{background:transparent;color:var(--muted);
  box-shadow:inset 0 0 0 1px var(--hair);cursor:default;pointer-events:none}

/* --- Umschalter Männer/Frauen ------------------------------------------ */
.klassenwahl{display:flex;gap:8px;margin:22px 0 0;flex-wrap:wrap;
  justify-content:center}
.klassenwahl:empty{display:none}
.klassenwahl a,.klassenwahl span{font-size:14px;font-weight:400;
  padding:8px 18px;border-radius:980px;border:1px solid var(--hair);
  text-decoration:none;color:var(--ink);background:var(--panel)}
.klassenwahl a:hover{border-color:var(--accent);color:var(--accent)}
.klassenwahl [aria-current="page"]{background:var(--accent);
  border-color:var(--accent);color:#fff}
.klassenwahl .leer{opacity:.4}

/* --- Deutschlandkarte --------------------------------------------------- */
#kartenwahl{margin:22px 0 0}
.karte-land{display:grid;gap:34px;align-items:center;margin:28px 0 0;
  grid-template-columns:minmax(0,330px) minmax(0,1fr)}
.karte-land figure{margin:0}
.karte-land svg{width:100%;height:auto;display:block}
.landflaeche{fill:var(--land);stroke:var(--landlinie);stroke-width:2.5;
  stroke-linejoin:round}
.stelle circle{fill:var(--accent);stroke:var(--bg);stroke-width:5}
.stelle text{fill:#fff;font-size:34px;font-weight:600;text-anchor:middle;
  letter-spacing:0}
.spitzen{display:grid;gap:2px}
.spitze{display:grid;grid-template-columns:30px 1fr;gap:14px;align-items:start;
  padding:13px 0;border-bottom:1px solid var(--hair);text-decoration:none;
  color:var(--ink)}
.spitze:first-child{border-top:1px solid var(--hair)}
.spitze .nr{width:26px;height:26px;border-radius:50%;background:var(--accent);
  color:#fff;font-size:14px;font-weight:600;display:grid;place-items:center;
  margin-top:2px}
.spitze .name{font-size:18px;font-weight:600;letter-spacing:-.015em;
  display:flex;align-items:center;gap:8px}
.spitze .name .ikon{width:17px;height:17px;color:var(--muted)}
.spitze .wo{font-size:14px;color:var(--muted);margin-top:2px}
.spitze .etwa{font-style:normal;opacity:.75}
.spitze:hover .name{color:var(--accent)}
.kartennotiz{margin:22px auto 0;max-width:62ch;text-align:center;
  font-size:14px;color:var(--muted)}

/* --- Eckdaten, Suche, Weiterführendes ----------------------------------- */
.eckdaten{margin:20px 0 0;text-align:center;color:var(--muted);font-size:15px}
.eckdaten b{color:var(--ink);font-weight:600}
.grossesuche{display:flex;gap:10px;margin:18px auto 0;max-width:620px}
.grossesuche input{flex:1 1 auto;min-width:0;background:var(--panel);
  color:var(--ink);border:1px solid var(--hair);border-radius:14px;
  padding:16px 20px;font-size:19px;letter-spacing:-.01em}
.grossesuche input:focus{outline:none;border-color:var(--accent);
  box-shadow:0 0 0 4px var(--accent-soft)}
.grossesuche .knopf{padding:16px 26px;font-size:17px}
.suchhinweis{margin:10px auto 0;max-width:620px;text-align:center;font-size:14px;
  color:var(--muted);min-height:1.2em}
.suchhinweis a{color:var(--accent);text-decoration:none;font-weight:500}
.mehrlink{margin:18px 0 0}

/* --- Kennzahlen-Karten --------------------------------------------------- */
.karten{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(290px,1fr))}
.karte{background:var(--panel);border-radius:20px;padding:26px 24px 22px;
  display:flex;flex-direction:column;gap:5px;box-shadow:var(--schatten)}
.karte .kopf{display:flex;align-items:center;gap:9px;font-size:13px;
  color:var(--muted);font-weight:400;letter-spacing:0}
.karte .kopf i{font-style:normal;font-size:19px}
.karte .kopf .ikon{width:19px;height:19px;color:var(--accent);vertical-align:-3px}
.karte .verein{font-size:25px;font-weight:600;letter-spacing:-.025em;
  line-height:1.16;margin-top:4px}
.karte .wert{font-size:17px;font-weight:600;color:var(--accent)}
.karte .liga{font-size:14px;color:var(--muted)}
.karte .erklaerung{font-size:14px;color:var(--muted);margin-top:8px;
  padding-top:12px;border-top:1px solid var(--hair)}
.topknopf{margin-top:14px;align-self:flex-start;font-size:15px;font-weight:400;
  color:var(--accent);text-decoration:none}
.topknopf:hover{text-decoration:underline}
.zurueckknopf{display:inline-block;margin:0 0 18px;font-size:15px;
  color:var(--accent);text-decoration:none}
.zurueckknopf:hover{text-decoration:underline}

.note{background:var(--flaeche);border:0;border-radius:14px;padding:16px 18px;
  margin:20px 0;font-size:15px;color:var(--muted)}
.band.grau .note{background:var(--bg)}
.note summary{cursor:pointer;color:var(--ink);font-weight:500;list-style:none}
.note summary::-webkit-details-marker{display:none}
.note summary::before{content:"› ";color:var(--muted)}
.note[open] summary::before{content:"⌄ "}
.note p{margin:10px 0 0}

/* --- Tabelle: Haarlinien statt Kasten ---------------------------------- */
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:20px 0 12px}
input[type=search],select{background:var(--panel);color:var(--ink);
  border:1px solid var(--hair);border-radius:10px;padding:10px 13px;font-size:14px;
  max-width:100%;min-width:0}
select{text-overflow:ellipsis}
input[type=search]{flex:1 1 240px}
.tip{margin:0 0 10px;font-size:14px;color:var(--muted)}
.legend{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}
.legend span{font-size:11px;padding:3px 10px;border-radius:980px;
  border:1px solid currentColor;font-weight:500}
.count{margin:0 0 10px;font-size:13px;color:var(--muted)}
/* Bewusst KEIN overflow: ein Scroll-Container würde den fixierten
   Spaltenkopf aushebeln. Schmale Fenster blenden stattdessen Spalten aus. */
.tablewrap{background:transparent;border:0}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{padding:13px 10px;text-align:right;border-bottom:1px solid var(--hair);
  white-space:nowrap;font-size:15px}
th{position:sticky;top:48px;z-index:3;font-size:12px;font-weight:400;
  color:var(--muted);letter-spacing:0;
  background:color-mix(in srgb,var(--bg) 88%,transparent);
  backdrop-filter:saturate(180%) blur(20px);
  -webkit-backdrop-filter:saturate(180%) blur(20px)}
.haupt th:nth-child(3),.haupt td:nth-child(3),
.haupt th:nth-child(4),.haupt td:nth-child(4){text-align:left}
.paarungen th:nth-child(2),.paarungen td:nth-child(2),
.paarungen th:nth-child(3),.paarungen td:nth-child(3){text-align:left}
.topliste th:nth-child(2),.topliste td:nth-child(2),
.topliste th:nth-child(3),.topliste td:nth-child(3){text-align:left}
.paarungen td:nth-child(2),.paarungen td:nth-child(3){padding-top:12px;padding-bottom:12px}
.paarungen .league{max-width:none;display:block;margin-top:2px}
/* In der Paarungstabelle ist Platz -- Vereinsnamen dürfen ausgeschrieben
   stehen, anders als in der 13-spaltigen Haupttabelle. */
.paarungen .club span{max-width:none;white-space:normal}
td.rank{font-weight:600;width:56px}
td.delta{width:56px;font-size:13px}
.club{display:flex;align-items:center;gap:11px;min-width:0}
.club img{width:22px;height:22px;object-fit:contain;flex:0 0 22px}
.club span{overflow:hidden;text-overflow:ellipsis;max-width:250px}
.tier{display:inline-block;padding:2px 8px;border-radius:980px;font-size:11px;
  font-weight:500;border:1px solid currentColor}
.league{color:var(--muted);font-size:13px;display:inline-block;max-width:205px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:middle}
.up{color:var(--up)}.down{color:var(--down)}.flat{color:var(--muted)}
.empty{padding:34px;text-align:center;color:var(--muted)}
.laden{padding:48px;text-align:center;color:var(--muted)}
__TIER_CSS__
tbody tr:hover{background:var(--flaeche)}

/* --- Icons -------------------------------------------------------------- */
.ikon{width:1.2em;height:1.2em;flex:0 0 auto;fill:none;stroke:currentColor;
  stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round;
  vertical-align:-.22em}
.topbar nav a .ikon{width:15px;height:15px;margin-right:6px;vertical-align:-3px}
h1 .ikon,h2 .ikon{width:.88em;height:.88em;color:var(--accent);margin-right:10px;
  vertical-align:-.1em}

/* --- Rechtstexte -------------------------------------------------------- */
.rechtslinks{margin:10px 0 0}
.odbl{margin:8px 0 0;font-size:13px}
.rechtstext{max-width:700px;margin:0 auto;padding:40px 0 30px}
.rechtstext h1{font-size:clamp(32px,4.4vw,48px);letter-spacing:-.03em;
  font-weight:600;margin:14px 0 8px}
.rechtstext h2{font-size:21px;margin:38px 0 10px;letter-spacing:-.02em}
.rechtstext p,.rechtstext ul{margin:0 0 15px}
.rechtstext ul{padding-left:22px}
.rechtstext li{margin-bottom:8px}
.rechtstext address{font-style:normal;line-height:1.7;margin:0 0 15px}
.rechtstext .fuehrung{font-size:19px;color:var(--muted);border:0;padding:0}
.rechtstext code{font-size:13px;background:var(--flaeche);padding:2px 6px;
  border-radius:5px}
.luecke{background:var(--flaeche);border:1px solid var(--hair);
  border-radius:14px;padding:16px 18px;margin:0 0 15px}
table.quellen{width:100%;border-collapse:collapse;margin:0 0 15px;font-size:15px}
table.quellen th,table.quellen td{text-align:left;vertical-align:top;
  padding:13px 14px 13px 0;border-bottom:1px solid var(--hair);
  white-space:normal}
table.quellen th{font-size:12px;font-weight:400;color:var(--muted);
  position:static;background:none;backdrop-filter:none}

footer{margin:56px 0 0;padding-top:24px;border-top:1px solid var(--hair);
  color:var(--muted);font-size:13px;line-height:1.8}
footer a{color:var(--accent);text-decoration:none}
footer a:hover{text-decoration:underline}

/* --- Schmale Fenster ---------------------------------------------------- */
@media (max-width:1100px){
  .haupt th:nth-child(5),.haupt td:nth-child(5),
  .haupt th:nth-child(7),.haupt td:nth-child(7),
  .haupt th:nth-child(8),.haupt td:nth-child(8),
  .haupt th:nth-child(9),.haupt td:nth-child(9){display:none}
  .club span{max-width:130px}
  .league{max-width:150px}
}
/* Auf dem Telefon passt die Kopfzeile sonst nicht: "Basketball" wird an
   den Rand gedrückt. Der Verweis "Start" entfällt dort -- die Marke links
   führt ohnehin zur Startseite. */
@media (max-width:560px){
  .topbar nav a[href="#home"]{display:none}
  .topbar nav{gap:12px}
  .topbar nav a{font-size:12px}
  /* Die Icons entfallen ebenfalls: die drei Wörter stehen für sich, und
     sie kosten zusammen die Breite, die "Basketball" gefehlt hat. */
  .topbar nav a .ikon{display:none}
  .brand{font-size:15px}
}
@media (max-width:860px){
  .band{padding:52px 0}
  .band.eng{padding:38px 0}
  .karte-land{grid-template-columns:1fr;gap:24px;
    justify-items:center}
  .karte-land figure{max-width:300px;width:100%}
  .spitzen{width:100%}
  .topbar nav{gap:14px}
  .topbar .inner{gap:14px;padding:0 16px}
  .mitte,.wrap{padding-left:16px;padding-right:16px}
  .haupt th:nth-child(2),.haupt td:nth-child(2),
  .haupt th:nth-child(10),.haupt td:nth-child(10),
  .haupt th:nth-child(11),.haupt td:nth-child(11),
  .haupt th:nth-child(12),.haupt td:nth-child(12){display:none}
  th,td{padding:11px 6px;white-space:normal}
  .club span,.league{max-width:none;white-space:normal;overflow:visible;
    text-overflow:clip;display:inline;min-width:0}
  .club{align-items:flex-start}
  table{table-layout:fixed}
  .haupt th:nth-child(1),.haupt td:nth-child(1){width:11%}
  .haupt th:nth-child(3),.haupt td:nth-child(3){width:41%}
  .haupt th:nth-child(4),.haupt td:nth-child(4){width:25%}
  .haupt th:nth-child(6),.haupt td:nth-child(6){width:9%}
  .haupt th:nth-child(13),.haupt td:nth-child(13){width:14%}
  /* Die Top-100-Liste hat acht Spalten. Auf dem Telefon fliegt die
     Differenz raus -- sie steckt bereits in der Angabe daneben -- und der
     Rest teilt sich die Breite nach dem, was drinsteht. */
  .topliste th:nth-child(6),.topliste td:nth-child(6){display:none}
  .topliste th,.topliste td{padding:10px 3px}
  .topliste th{overflow-wrap:anywhere}
  .topliste td:nth-child(4),.topliste td:nth-child(5),
  .topliste td:nth-child(7),.topliste td:nth-child(8){white-space:nowrap;
    overflow-wrap:normal}
  .topliste th:nth-child(1),.topliste td:nth-child(1){width:10%}
  .topliste th:nth-child(2),.topliste td:nth-child(2){width:21%}
  .topliste th:nth-child(3),.topliste td:nth-child(3){width:16%}
  .topliste th:nth-child(4),.topliste td:nth-child(4){width:7%}
  .topliste th:nth-child(5),.topliste td:nth-child(5){width:16%}
  .topliste th:nth-child(7),.topliste td:nth-child(7){width:15%}
  .topliste th:nth-child(8),.topliste td:nth-child(8){width:15%;font-size:11px}
  td:nth-child(2),td:nth-child(3){overflow-wrap:break-word;hyphens:auto}
  td.rank{width:11%}
  .league{font-size:11px}
}
</style>
</head>
<body>

<div class="topbar"><div class="inner">
  <a class="brand" href="#home">Deutschland<span>tabelle</span></a>
  <nav id="nav"></nav>
</div></div>

<!-- ============================ Startseite ============================ -->
<section id="view-home">

  <div class="band eng"><div class="mitte">
    <div class="hero">
      <!-- Startbild: eine Datei docs/header.jpg ablegen, dann verschwindet
           der Platzhalter von selbst. -->
      <img src="header.jpg?v=__STARTBILD__" alt=""
           onload="document.getElementById('platzhalter').remove()"
           onerror="this.remove()">
      <div class="schleier"></div>
      <div class="platzhalter" id="platzhalter"><em>Platzhalter für das Startbild —
        am besten eines mit allen Sportarten.<br>Datei <code>docs/header.jpg</code>
        ablegen</em></div>
      <div class="inhalt">
        <h1 class="marke">Deutschland<span>tabelle</span></h1>
        <p class="claim">Jeder Verein des Landes in einer einzigen Tabelle.
          Wo steht deiner?</p>
      </div>
    </div>
  </div></div>

  <div class="band"><div class="mitte">
    <div class="intro">
      <p><b>Nicht nur die Bundesliga.</b> Die komplette Pyramide bis hinunter
      zur Kreisklasse, für drei Sportarten und beide Klassen — Tag für Tag neu
      gerechnet aus den Ergebnissen der laufenden Saison.</p>
      <p>Sortiert wird zuerst nach Ligastufe, innerhalb einer Stufe nach Punkten
      pro Spiel. Dadurch stehen parallele Staffeln nicht blockweise
      hintereinander, sondern verzahnen sich zu einer echten Rangfolge.</p>
    </div>
    <form class="suche" id="homeSuche">
      <input type="search" id="homeQuery" placeholder="Vereinsnamen eingeben …"
             autocomplete="off">
      <select id="homeSport"></select>
      <button class="knopf" type="submit">Verein finden</button>
    </form>
  </div></div>

  <div class="band grau"><div class="mitte">
    <h2 class="titel">Drei Sportarten, sechs Tabellen</h2>
    <p class="untertitel">Männer und Frauen spielen getrennte Pyramiden mit
      eigenen Auf- und Abstiegsketten. Deshalb stehen sie auch getrennt.</p>
    <div class="sportkarten" id="sportkarten"></div>
  </div></div>

  <div class="band" id="kartenband" hidden><div class="mitte">
    <h2 class="titel">Die Spitze des Landes</h2>
    <p class="untertitel" id="kartenunter"></p>
    <div class="klassenwahl" id="kartenwahl"></div>
    <div class="karte-land" id="kartenbereich"></div>
    <p class="kartennotiz" id="kartennotiz"></p>
  </div></div>

  <div class="band eng"><div class="mitte">
    <footer>
      <p>Ein Projekt aus offen zugänglichen Ergebnisdaten. Die Datenquellen und
      die jeweilige Abdeckung stehen auf der Seite der Sportart.</p>
      <p class="rechtslinks"><a href="#impressum">Impressum</a> ·
        <a href="#datenschutz">Datenschutz</a> ·
        <a href="#impressum">Quellen und Lizenzen</a></p>
      <p class="odbl">Enthält Daten von <a href="https://www.openligadb.de/"
        rel="noopener">OpenLigaDB</a>, lizenziert unter der
        <a href="https://opendatacommons.org/licenses/odbl/1-0/"
        rel="noopener">Open Database License 1.0</a>.</p>
    </footer>
  </div></div>
</section>

<div class="wrap">

<!-- ========================= Impressum ========================= -->
<section id="view-impressum" hidden>
  <div class="rechtstext">
    <a class="zurueckknopf" href="#home">← Zurück zur Startseite</a>
    <h1>Impressum</h1>

    <h2>Angaben gemäß § 5 DDG</h2>
    __ANSCHRIFT__

    <h2>Kontakt</h2>
    __KONTAKT__

    <h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
    <p>Dieselbe Person wie oben.</p>

    <h2>Art des Angebots</h2>
    <p>Die Deutschlandtabelle ist ein privates, nicht-kommerzielles Projekt.
    Sie verkauft nichts, zeigt keine Werbung und verlangt keine Anmeldung.</p>

    <h2>Zu den Zahlen</h2>
    <p>Die Tabellen stammen aus den unten genannten Quellen und werden
    unverändert übernommen, lediglich in eine gemeinsame Rangfolge gebracht.
    Für ihre Richtigkeit und Vollständigkeit kann ich nicht einstehen: ein
    Punktabzug, eine zurückgezogene Mannschaft oder ein nachgetragenes Ergebnis
    erscheinen hier erst, wenn die Quelle sie führt. Wer einen Fehler
    bemerkt, darf mir gern schreiben.</p>
    <p>Die Rangfolge selbst ist eine Rechnung, kein sportliches Urteil.
    Unterhalb der überregionalen Ligen gibt es zwischen den Landesverbänden
    keine gemeinsame Auf- und Abstiegskette; ein Vergleich über Verbandsgrenzen
    hinweg ist dort nicht sportlich begründet.</p>

    <h2 id="lizenzen">Quellen und Lizenzen</h2>
    <p>Jede Zeile der <a href="fussball-vereine.csv">CSV-Dateien</a> nennt in
    der Spalte <code>quelle</code>, woher sie stammt.</p>
    <table class="quellen">
      <thead><tr><th>Quelle</th><th>Deckt ab</th><th>Rechtlicher Stand</th></tr></thead>
      <tbody>
        <tr>
          <td><a href="https://www.openligadb.de/" rel="noopener">OpenLigaDB</a></td>
          <td>Fußball, obere Ligen</td>
          <td><a href="https://opendatacommons.org/licenses/odbl/1-0/"
              rel="noopener">ODbL 1.0</a> — Namensnennung und Weitergabe unter
              gleichen Bedingungen. Die mit <code>OpenLigaDB</code>
              gekennzeichneten Zeilen der CSV-Dateien stehen unter dieser
              Lizenz.</td>
        </tr>
        <tr>
          <td><a href="https://www.fussball.de/" rel="noopener">fussball.de</a></td>
          <td>Fußball, Landesverbände</td>
          <td>DFB GmbH &amp; Co. KG. Keine freie Lizenz.</td>
        </tr>
        <tr>
          <td><a href="https://www.handball.net/" rel="noopener">handball.net</a></td>
          <td>Handball ab 3. Liga</td>
          <td>Deutscher Handballbund. Keine freie Lizenz.</td>
        </tr>
        <tr>
          <td><a href="https://www.opel-hbl.de/" rel="noopener">HBL</a> ·
              Sportradar</td>
          <td>Handball-Bundesligen</td>
          <td>HBL GmbH. Keine freie Lizenz.</td>
        </tr>
        <tr>
          <td><a href="https://www.basketball-bund.net/" rel="noopener">basketball-bund.net</a></td>
          <td>Basketball, alle Stufen</td>
          <td>Deutscher Basketball Bund. Keine freie Lizenz.</td>
        </tr>
        <tr>
          <td><a href="https://www.naturalearthdata.com/" rel="noopener">Natural
              Earth</a></td>
          <td>Umriss der Deutschlandkarte</td>
          <td>Gemeinfrei („no rights reserved“). Namensnennung ist nicht
              verlangt, geschieht hier trotzdem.</td>
        </tr>
      </tbody>
    </table>
    <p>Die Vereinswappen stammen aus OpenLigaDB und werden von dieser Seite
    ausgeliefert, damit kein Seitenaufruf an fremde Server geht. Die Rechte an
    den Wappen liegen bei den jeweiligen Vereinen; sie erscheinen hier zur
    Kennzeichnung der Mannschaft, nicht als eigene Leistung.</p>
    <p class="rechtslinks"><a href="#datenschutz">Weiter zur
      Datenschutzerklärung →</a></p>
  </div>
</section>

<!-- ====================== Datenschutzerklärung ====================== -->
<section id="view-datenschutz" hidden>
  <div class="rechtstext">
    <a class="zurueckknopf" href="#home">← Zurück zur Startseite</a>
    <h1>Datenschutzerklärung</h1>

    <p class="fuehrung">Diese Seite setzt keine Cookies, misst nichts und
    bindet nichts von fremden Servern ein. Alles, was Sie hier sehen —
    Schriften, Bilder, Wappen, Daten — kommt von deutschlandtabelle.github.io. Übrig
    bleibt, was beim Ausliefern einer Seite technisch anfällt.</p>

    <h2>Verantwortlicher</h2>
    __ANSCHRIFT__
    __KONTAKT__

    <h2>Was beim Aufruf der Seite verarbeitet wird</h2>
    <p>Die Seite wird über <b>GitHub Pages</b> ausgeliefert, einen Dienst der
    GitHub Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA
    (Teil der Microsoft Corporation). Beim Abruf überträgt Ihr Browser
    unvermeidlich Daten, die GitHub in Server-Protokollen erfasst:</p>
    <ul>
      <li>Ihre IP-Adresse</li>
      <li>Datum und Uhrzeit des Abrufs</li>
      <li>die angeforderte Datei und die übertragene Datenmenge</li>
      <li>die zuvor besuchte Seite (Referrer), sofern Ihr Browser sie sendet</li>
      <li>Browser und Betriebssystem</li>
    </ul>
    <p><b>Zweck und Rechtsgrundlage.</b> Diese Verarbeitung ist erforderlich,
    um die Seite überhaupt ausliefern und ihren sicheren Betrieb gewährleisten
    zu können. Rechtsgrundlage ist das berechtigte Interesse an einem
    funktionsfähigen Angebot, Art. 6 Abs. 1 lit. f DSGVO.</p>
    <p><b>Übermittlung in die USA.</b> GitHub verarbeitet die Protokolldaten
    auch in den Vereinigten Staaten. Die Übermittlung stützt sich auf das
    EU-US Data Privacy Framework beziehungsweise auf Standardvertragsklauseln.
    Einzelheiten stehen in der
    <a href="https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement"
    rel="noopener">Datenschutzerklärung von GitHub</a>.</p>
    <p><b>Speicherdauer.</b> Auf die Protokolle von GitHub habe ich keinen
    Zugriff und kein Einsichtsrecht; ihre Dauer richtet sich nach den Angaben
    von GitHub.</p>

    <h2>Was nicht stattfindet</h2>
    <ul>
      <li><b>Keine Cookies</b> und keine vergleichbare Speicherung in Ihrem
        Browser.</li>
      <li><b>Keine Reichweitenmessung</b>, keine Analysewerkzeuge, keine
        Zählpixel, keine Werbung.</li>
      <li><b>Keine Einbindung Dritter.</b> Schriften sind die Ihres
        Betriebssystems, Bilder und Vereinswappen liegen auf dieser Seite.
        Es wird keine Verbindung zu einem anderen Server aufgebaut.</li>
      <li><b>Keine Konten, keine Formulare.</b> Die Suche läuft in Ihrem
        Browser; es wird nichts abgeschickt.</li>
      <li><b>Keine automatisierte Entscheidungsfindung</b> und kein
        Profiling.</li>
    </ul>

    <h2>Die angezeigten Daten</h2>
    <p>Gezeigt werden Mannschaften, Ligen und Tabellenstände. Namen von
    Spielerinnen, Spielern oder Schiedsrichtern werden nicht erhoben,
    gespeichert oder angezeigt. Ein Mannschaftsname wie „SV Lengede II“ ist
    kein personenbezogenes Datum.</p>
    <p>Sollte in einem Mannschaftsnamen ausnahmsweise eine natürliche Person
    erkennbar sein und Sie damit nicht einverstanden sein, schreiben Sie mir —
    die Zeile wird dann entfernt.</p>

    <h2>Ihre Rechte</h2>
    <p>Sie haben gegenüber dem Verantwortlichen das Recht auf Auskunft
    (Art. 15 DSGVO), Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung
    der Verarbeitung (Art. 18), Datenübertragbarkeit (Art. 20) sowie das Recht,
    der Verarbeitung zu widersprechen (Art. 21). Sie können sich außerdem bei
    einer Datenschutz-Aufsichtsbehörde beschweren, Art. 77 DSGVO.</p>
    <p>Da ich selbst keine Protokolle führe und auf die von GitHub keinen
    Zugriff habe, richten sich Auskunfts- und Löschbegehren zu diesen Daten
    zweckmäßigerweise direkt an GitHub.</p>

    <p class="rechtslinks"><a href="#impressum">Zum Impressum →</a></p>
  </div>
</section>

<!-- ========================= Ansicht Sportart ========================= -->
<section id="view-sport" hidden>
  <!-- Headerbild je Sportart: eine Datei docs/header-<sport>.jpg ablegen,
       dann verschwindet der Platzhalter von selbst. -->
  <div class="hero klein">
    <img id="sportBild" alt="">
    <div class="schleier"></div>
    <div class="platzhalter" id="sportPlatzhalter"><em>Platzhalter für das
      Headerbild dieser Sportart<br>Datei <code id="sportBildName"></code>
      ablegen, empfohlen 1800 × 870 px</em></div>
    <div class="inhalt">
      <h1 class="marke" id="sportTitel"></h1>
      <p class="claim" id="sportUnter"></p>
    </div>
  </div>
  <nav class="klassenwahl" id="klassenwahl" aria-label="Männer oder Frauen"></nav>
  <div id="sportInhalt"><div class="laden">Daten werden geladen …</div></div>
</section>

<template id="tpl-sport">
  <!-- Zuerst die Suche: wer hierher kommt, sucht meist genau einen Verein.
       Danach drei Karten als Ausblick, dann die Tabelle. Die Eckdaten und
       die übrigen Auswertungen stehen unter ?analyse=1 -- sie haben vorher
       den halben Bildschirm gekostet, bevor irgendetwas Nützliches kam. -->
  <p class="eckdaten" id="eckdaten"></p>
  <form class="grossesuche" id="sportSuche">
    <input type="search" id="q" placeholder="Deinen Verein suchen …"
           autocomplete="off" enterkeyhint="search">
    <button class="knopf" type="submit">Finden</button>
  </form>
  <p class="suchhinweis" id="suchhinweis"></p>

  <div id="topBereich" hidden></div>
  <div id="analyseBereich" hidden></div>

  <h2>Die Bestenlisten</h2>
  <p class="unter" id="bestenUnter">Quer zur Tabelle gelesen — ohne Rücksicht darauf, in welcher Liga jemand spielt.</p>
  <div class="karten" id="karten"></div>
  <p class="mehrlink" id="mehrlink"></p>

  <div id="pokalBereich" hidden></div>

  <h2 id="tabellenTitel">Die komplette Tabelle</h2>
  <p class="unter" id="tabellenUnter"></p>
  <div class="controls">
    <select id="verbandFilter"></select>
    <select id="tierFilter"></select>
    <select id="leagueFilter"></select>
  </div>
  <p class="tip" id="vergleichHinweis"></p>
  <div class="legend" id="legend"></div>
  <p class="count" id="zaehler"></p>
  <div class="tablewrap">
    <table class="haupt">
      <thead><tr>
        <th>#</th><th title="Veränderung gegenüber der Vorwoche">± Wo.</th>
        <th>Verein</th><th>Liga</th><th title="Platz in der eigenen Staffel">Pl.</th>
        <th>Sp</th><th>S</th><th>U</th><th>N</th><th id="thTore">Tore</th>
        <th id="thDiff">Diff</th><th>Pkt</th>
        <th title="Punkte pro Spiel — Sortierkriterium innerhalb der Ligastufe">Pkt/Sp</th>
      </tr></thead>
      <tbody id="rows"></tbody>
    </table>
    <div class="empty" id="empty" hidden>Keine Treffer.</div>
  </div>
  <footer id="sportFuss"></footer>
</template>

</div>

<script>
const SPORTS = __SPORTS__;
const IKONEN = __IKONEN__;
const KARTE = {box: "__KARTENBOX__", umriss: "__KARTENPFAD__"};
// Basketball wirft Körbe. Ältere Datenpakete kennen das Feld noch nicht.
const WORTE = s => s.worte || {mehrzahl: 'Tore', diff: 'Tordifferenz',
  diff_kurz: 'Tordiff.', gegen: 'Gegentore', getroffen: 'geschossenen Tore'};
// Erst der sprechende Schlüssel, dann das, was im Datenpaket steht (dort
// stehen teils noch Emoji aus älteren Läufen).
const ikon = (...schluessel) => {
  const pfad = schluessel.map(k => IKONEN[k]).find(Boolean);
  return pfad ? `<svg class="ikon" viewBox="0 0 24 24" aria-hidden="true">${pfad}</svg>` : '';
};
const esc = s => String(s ?? '').replace(/[&<>"]/g, c =>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const tausend = n => Number(n).toLocaleString('de-DE');
const daten = {};                      // slug -> geladener Datensatz

// --- Kopfleiste und Startseite ----------------------------------------
// Sechs Rangfolgen, aber drei Sportarten: die Kopfleiste zeigt die Sportart,
// die Klasse (Männer/Frauen) wird in der Sportansicht umgeschaltet.
const SPORTARTEN = [];
SPORTS.forEach(s => {
  let eintrag = SPORTARTEN.find(x => x.sportart === s.sportart);
  if (!eintrag) SPORTARTEN.push(eintrag = {
    sportart: s.sportart, name: s.sportName, klassen: [],
  });
  eintrag.klassen.push(s);
});

document.getElementById('nav').innerHTML =
  '<a href="#home">Start</a>' + SPORTARTEN.map(a => {
    const erste = a.klassen.find(k => k.ready) || a.klassen[0];
    return `<a href="#${erste.slug}" data-sportart="${a.sportart}"
       class="${a.klassen.some(k => k.ready) ? '' : 'leer'}">${ikon(a.sportart)}${esc(a.name)}</a>`;
  }).join('');

document.getElementById('sportkarten').innerHTML = SPORTARTEN.map(a => {
  const zeilen = a.klassen.map(k => k.ready
    ? `<a class="klassenzeile" href="#${k.slug}">
         <span class="wer">${esc(k.klasseName)}</span>
         <span class="zahl">${tausend(k.teams)}</span>
         <span class="klein">Mannschaften · ${tausend(k.leagues)} Staffeln</span></a>`
    : `<div class="klassenzeile leer">
         <span class="wer">${esc(k.klasseName)}</span>
         <span class="klein">${esc(k.hinweis || 'in Arbeit')}</span></div>`).join('');
  const knoepfe = a.klassen.map((k, i) => k.ready
    ? `<a class="knopf${i ? ' zweit' : ''}" href="#${k.slug}">${esc(k.klasseName)}
         ansehen</a>`
    : `<span class="knopf aus">${esc(k.klasseName)} folgt</span>`).join('');
  return `<div class="sportkarte">
      <div class="ic">${ikon(a.sportart)}</div><h3>${esc(a.name)}</h3>
      <div class="klassen">${zeilen}</div>
      <div class="kachelknoepfe">${knoepfe}</div></div>`;
}).join('');

// --- Deutschlandkarte -------------------------------------------------
// Zwei Sichten auf dieselbe Frage: der beste Verein ohne Rücksicht auf die
// Liga (Kreisklasse möglich) und der Erste der obersten Liga. Die Nummern
// sind fest vergeben -- 1 Fußball Männer, 2 Fußball Frauen, 3 Handball
// Männer und so fort -- damit dieselbe Zahl immer dieselbe Rangfolge meint,
// auch wenn ein Punkt einmal fehlt.
const KARTEN_FOLGE = ['fussball', 'fussball-frauen', 'handball',
                      'handball-frauen', 'basketball', 'basketball-frauen'];
const KARTEN_SICHT = {
  gesamt: {knopf: 'Bester Verein', text: 'Die meisten Punkte pro Spiel — ohne '
    + 'Rücksicht auf die Liga. Das kann die Bundesliga sein oder die Kreisklasse.'},
  liga1:  {knopf: 'Erste Liga', text: 'Wer in der obersten erfassten Liga jeder '
    + 'Rangfolge an der Spitze steht.'},
};
let kartenSicht = 'gesamt';

function karteZeichnen(){
  const punkte = KARTEN_FOLGE.map((slug, i) => {
    const sport = SPORTS.find(x => x.slug === slug);
    const p = sport && sport.ready && sport.karte && sport.karte[kartenSicht];
    return (p && p.x != null)
      ? {...p, nr: i + 1, slug, sportart: sport.sportart,
         sportName: sport.sportName, klasse: sport.klasseName}
      : null;
  }).filter(Boolean);
  if (!punkte.length) return false;

  // Zwei Vereine aus derselben Stadt würden aufeinander liegen. Der zweite
  // weicht zur Kartenmitte hin aus -- nach außen läge er neben dem Land.
  const gesetzt = [];
  punkte.forEach(p => {
    p.px = p.x; p.py = p.y;
    let n = 0;
    const richtung = p.x > 500 ? -1 : 1;
    while (gesetzt.some(q => Math.hypot(q.px - p.px, q.py - p.py) < 64) && n < 8){
      n += 1;
      p.px = Math.min(966, Math.max(34, p.x + richtung * 58 * n));
      p.py = Math.min(1325, Math.max(34, p.y + 22 * n));
    }
    gesetzt.push(p);
  });

  const stellen = punkte.map(p => `<g class="stelle">
      <title>${esc(p.name)}</title>
      <circle cx="${p.px}" cy="${p.py}" r="27"/>
      <text x="${p.px}" y="${p.py + 12}">${p.nr}</text></g>`).join('');
  const liste = punkte.map(p => `<a class="spitze" href="#${p.slug}">
      <span class="nr">${p.nr}</span>
      <span><span class="name">${ikon(p.sportart)}${esc(p.name)}</span>
        <span class="wo">${esc(p.sportName)} der ${esc(p.klasse)} ·
          ${esc(p.liga)} · ${esc(p.ort)}${p.art === 'verein' ? ''
            : ' <i class="etwa">(ungefähr)</i>'}</span></span></a>`).join('');

  document.getElementById('kartenbereich').innerHTML = `
    <figure><svg viewBox="${KARTE.box}" role="img"
        aria-label="Karte von Deutschland mit den Spitzenvereinen">
      <path class="landflaeche" d="${KARTE.umriss}"/>${stellen}
    </svg></figure>
    <div class="spitzen">${liste}</div>`;
  document.getElementById('kartenunter').textContent =
    KARTEN_SICHT[kartenSicht].text;
  document.getElementById('kartenwahl').innerHTML =
    Object.entries(KARTEN_SICHT).map(([k, v]) => k === kartenSicht
      ? `<span aria-current="page">${esc(v.knopf)}</span>`
      : `<a href="#home" data-sicht="${k}">${esc(v.knopf)}</a>`).join('');
  document.querySelectorAll('#kartenwahl a').forEach(a =>
    a.addEventListener('click', e => {
      e.preventDefault();
      kartenSicht = a.dataset.sicht;
      karteZeichnen();
    }));
  const ungenau = punkte.some(p => p.art !== 'verein');
  document.getElementById('kartennotiz').innerHTML =
    'Der Ort stammt aus dem Vereinsnamen, sonst aus dem Ligennamen, sonst '
    + 'aus dem Verbandsgebiet — Vereinsadressen liefert keine der Quellen. '
    + (ungenau ? 'Die mit <i>(ungefähr)</i> gekennzeichneten Punkte geben '
       + 'deshalb nur die Gegend an. ' : '')
    + 'Sitzen zwei Vereine in derselben Stadt, rückt der zweite Punkt zur '
    + 'Seite. Umriss: Natural Earth, gemeinfrei.';
  return true;
}
if (karteZeichnen()) document.getElementById('kartenband').hidden = false;

document.getElementById('homeSport').innerHTML = SPORTS.filter(s => s.ready)
  .map(s => `<option value="${s.slug}">${esc(s.name)} · ${esc(s.klasseName)}`
            + `</option>`).join('');
document.getElementById('homeSuche').addEventListener('submit', e => {
  e.preventDefault();
  const slug = document.getElementById('homeSport').value;
  const q = document.getElementById('homeQuery').value.trim();
  location.hash = `#${slug}` + (q ? `?q=${encodeURIComponent(q)}` : '');
});

// --- Router -------------------------------------------------------------
function aktuelleRoute(){
  const roh = (location.hash || '#home').slice(1);
  const [slug, query] = roh.split('?');
  return {slug: slug || 'home', params: new URLSearchParams(query || '')};
}

async function route(){
  const {slug, params} = aktuelleRoute();
  const sport = SPORTS.find(s => s.slug === slug);
  document.querySelectorAll('#nav a').forEach(a =>
    a.toggleAttribute('aria-current',
      a.getAttribute('href') === '#' + slug ||
      (!!sport && a.dataset.sportart === sport.sportart)));
  // Vier Ansichten, immer genau eine sichtbar.
  const ANSICHTEN = ['view-home', 'view-sport', 'view-impressum', 'view-datenschutz'];
  const zeige = id => ANSICHTEN.forEach(a =>
    document.getElementById(a).hidden = (a !== id));
  const home = document.getElementById('view-home');
  const view = document.getElementById('view-sport');
  if (slug === 'impressum' || slug === 'datenschutz'){
    zeige('view-' + slug);
    window.scrollTo(0, 0);
    return;
  }
  if (!sport){ zeige('view-home'); window.scrollTo(0,0); return; }
  zeige('view-sport');
  document.getElementById('sportTitel').innerHTML =
    ikon(sport.sportart, sport.icon) + esc(sport.name);
  document.getElementById('sportUnter').textContent = sport.ready
    ? `Saison ${sport.season} · Stand ${sport.generated}` : '';

  // Umschalter Männer/Frauen. Beide Klassen sind eigene Rangfolgen: sie
  // spielen getrennte Pyramiden mit eigenen Auf- und Abstiegsketten, ein
  // gemeinsamer Platz hätte keine sportliche Grundlage.
  const geschwister = SPORTS.filter(s => s.sportart === sport.sportart);
  const umschalter = document.getElementById('klassenwahl');
  umschalter.innerHTML = geschwister.length < 2 ? '' : geschwister.map(k =>
    k.slug === sport.slug
      ? `<span aria-current="page">${esc(k.klasseName)}</span>`
      : (k.ready ? `<a href="#${k.slug}">${esc(k.klasseName)}</a>`
                 : `<span class="leer" title="noch keine Daten">${esc(k.klasseName)}</span>`)
  ).join('');

  // Kopfbild der Sportart. Fehlt die Datei, bleibt der Verlauf mit Platzhalter.
  const bild = document.getElementById('sportBild');
  const platz = document.getElementById('sportPlatzhalter');
  // Erst ein Motiv für genau diese Klasse, sonst das der Sportart.
  const kandidaten = [`header-${sport.slug}.jpg`, `header-${sport.sportart}.jpg`];
  document.getElementById('sportBildName').textContent = `docs/${kandidaten[0]}`;
  platz.hidden = false;
  bild.hidden = true;
  let versuch = 0;
  bild.onload = () => { platz.hidden = true; bild.hidden = false; };
  bild.onerror = () => {
    versuch += 1;
    if (versuch < kandidaten.length){ bild.src = kandidaten[versuch]; return; }
    bild.hidden = true; platz.hidden = false;
  };
  bild.src = kandidaten[0];
  if (!sport.ready){
    document.getElementById('sportInhalt').innerHTML =
      `<div class="note"><p>${esc(sport.hinweis || 'Diese Sportart ist noch in Arbeit.')}</p></div>`;
    window.scrollTo(0,0); return;
  }
  document.getElementById('sportInhalt').innerHTML =
    '<div class="laden">Daten werden geladen …</div>';
  window.scrollTo(0,0);
  try {
    if (!daten[slug]) daten[slug] = await (await fetch(`data/${slug}.json`)).json();
  } catch (err) {
    document.getElementById('sportInhalt').innerHTML =
      '<div class="note"><p>Die Daten konnten nicht geladen werden.</p></div>';
    return;
  }
  zeigeSport(sport, daten[slug], params);
}
window.addEventListener('hashchange', route);

// --- Eine Sportart darstellen ------------------------------------------
// Dieselben Kriterien wie bei den Kennzahlen-Karten, damit Karte und
// Top-100-Liste nie auseinanderlaufen. Sortiert wird immer absteigend nach
// dem ersten Wert, bei Gleichstand nach dem zweiten.
const proSpiel = (r, feld) => r.played ? r[feld] / r.played : 0;
const SORTIERUNG = {
  // Gleichstand bei den Punkten: erst die Differenz, dann die erzielten
  // Treffer -- dieselbe Reihenfolge, nach der auch eine Ligatabelle ordnet.
  bester:       r => [proSpiel(r,'points'), proSpiel(r,'goalDiff'),
                      proSpiel(r,'goalsFor')],
  heiss:        r => [proSpiel(r,'goalDiff'), proSpiel(r,'points')],
  torfabrik:    r => [proSpiel(r,'goalsFor'), proSpiel(r,'points')],
  bollwerk:     r => [-proSpiel(r,'goalsAgainst'), proSpiel(r,'points')],
  schlusslicht: r => [-proSpiel(r,'points'), -proSpiel(r,'goalDiff')],
  klatsche:     r => [-proSpiel(r,'goalDiff'), -proSpiel(r,'points')],
  aufsteiger:   r => [r.delta ?? -1e9, 0],
  absteiger:    r => [-(r.delta ?? 1e9), 0],
};
const WERT = {
  bester:       r => proSpiel(r,'points').toFixed(2),
  heiss:        r => (proSpiel(r,'goalDiff') >= 0 ? '+' : '') + proSpiel(r,'goalDiff').toFixed(2),
  torfabrik:    r => proSpiel(r,'goalsFor').toFixed(2),
  bollwerk:     r => proSpiel(r,'goalsAgainst').toFixed(2),
  schlusslicht: r => proSpiel(r,'points').toFixed(2),
  klatsche:     r => (proSpiel(r,'goalDiff') >= 0 ? '+' : '') + proSpiel(r,'goalDiff').toFixed(2),
  aufsteiger:   r => (r.delta > 0 ? '+' : '') + r.delta,
  absteiger:    r => (r.delta > 0 ? '+' : '') + r.delta,
};
// Bei den Wochenlisten zählt nur, wer überhaupt einen Vorwochenwert hat.
const NUR_MIT_DELTA = new Set(['aufsteiger', 'absteiger']);

function zeigeSport(sport, d, params){
  const ziel = document.getElementById('sportInhalt');
  ziel.innerHTML = '';
  ziel.appendChild(document.getElementById('tpl-sport').content.cloneNode(true));

  const RANKING = d.rows.map(a => ({
    rank: a[0], delta: a[1], name: a[2], icon: a[3], tier: a[4],
    league: d.leagues[a[5]], verband: d.verbaende[a[6]],
    leaguePos: a[7], played: a[8], won: a[9], drawn: a[10], lost: a[11],
    goalsFor: a[12], goalsAgainst: a[13], goalDiff: a[14], points: a[15], ppg: a[16],
  }));

  const $ = id => ziel.querySelector('#' + id);
  const wort = WORTE(sport);
  $('thTore').textContent = wort.mehrzahl;
  $('thTore').title = `Erzielte ${wort.mehrzahl} : ${wort.gegen}`;
  $('thDiff').title = wort.diff;
  $('tabellenUnter').textContent =
    `${tausend(RANKING.length)} Mannschaften, sortiert nach Ligastufe und Punkten pro Spiel.`;
  $('vergleichHinweis').innerHTML = sport.vergleichHinweis || '';

  // Die Eckdaten als eine Zeile statt als vier Kacheln -- ausführlich
  // stehen sie auf der Analyseseite.
  const eckdaten = [
    ['Mannschaften', tausend(RANKING.length)],
    ['Staffeln', tausend(d.meta.leagues)],
    ['Ligastufen', new Set(RANKING.map(r => r.tier)).size],
    ['Verbände', new Set(RANKING.map(r => r.verband).filter(Boolean)).size],
  ];
  $('eckdaten').innerHTML = eckdaten
    .map(([k, v]) => `<b>${v}</b> ${k}`).join(' · ');

  // Die Abdeckungsnotiz gehört unter die Tabelle, nicht davor: sie erklärt
  // die Zahlen, sie hält niemanden von ihnen ab.
  const notiz = d.meta.note
    ? `<details class="note"><summary>${esc(d.meta.note_summary || 'Abdeckung')}</summary>
       <p>${d.meta.note}</p></details>` : '';

  // Drei Karten als Ausblick. Der Rest steht auf der Analyseseite.
  const AUSBLICK = ['bester', 'torfabrik', 'aufsteiger'];
  // `knapp` lässt die Erklärung weg: auf der Sportseite sind die drei
  // Karten ein Ausblick, die Begründung steht in der Top-100 darüber.
  const kennzahl = (k, knapp) => `
    <div class="karte">
      <div class="kopf">${ikon(k.key, k.icon)}${esc(k.titel)}</div>
      <div class="verein">${esc(k.verein)}</div>
      <div class="wert">${esc(k.wert)}</div>
      <div class="liga">${esc(k.liga)} · Ligastufe ${k.stufe} · ${esc(k.verband)}
        · Rang ${tausend(k.rang)}</div>
      ${knapp ? '' : `<div class="erklaerung">${esc(k.erklaerung)}</div>`}
      <a class="topknopf" href="#${sport.slug}?top=${k.key}">Zur Top-100 →</a>
    </div>`;
  const alle = d.kennzahlen || [];
  const ausblick = AUSBLICK.map(key => alle.find(k => k.key === key)).filter(Boolean);
  $('karten').innerHTML = ausblick.map(k => kennzahl(k, true)).join('');
  $('mehrlink').innerHTML = (alle.length || d.pokal)
    ? `<a class="topknopf" href="#${sport.slug}?analyse=1">Alle Auswertungen`
      + `${d.pokal ? ' und der DFB-Pokal' : ''} →</a>` : '';

  $('sportFuss').innerHTML = notiz + (sport.fuss || '');

  // --- Filter befüllen --------------------------------------------------
  const q = $('q'), tierFilter = $('tierFilter'), leagueFilter = $('leagueFilter'),
        verbandFilter = $('verbandFilter'), rows = $('rows'), empty = $('empty'),
        zaehler = $('zaehler');
  const opt = (wert, text) => `<option value="${esc(wert)}">${esc(text)}</option>`;
  const stufen = [...new Set(RANKING.map(r => r.tier))].sort((a,b) => a-b);
  const verbaende = [...new Set(RANKING.map(r => r.verband).filter(Boolean))].sort();
  const staffeln = [...new Set(RANKING.map(r => r.league))].sort();
  verbandFilter.innerHTML = opt('', 'Alle Verbände') + verbaende.map(v => opt(v,v)).join('');
  tierFilter.innerHTML = opt('', 'Alle Ligastufen')
    + stufen.map(t => opt(t, `${t}. Ligastufe`)).join('');
  leagueFilter.innerHTML = opt('', 'Alle Staffeln') + staffeln.map(l => opt(l,l)).join('');
  $('legend').innerHTML = stufen.map(t =>
    `<span class="tier t${t}-fg">${t}. Stufe</span>`).join('');

  const deltaCell = v => v === null || v === undefined
    ? '<span class="flat">–</span>'
    : (v === 0 ? '<span class="flat">±0</span>'
       : (v > 0 ? `<span class="up">▲ ${v}</span>` : `<span class="down">▼ ${-v}</span>`));

  const STUECK = 400;
  let gefiltert = [], gezeigt = 0, letzteStufe = null;

  function zeile(r, step){
    const icon = r.icon ? `<img src="${esc(r.icon)}" alt="" loading="lazy"
      onerror="this.style.visibility='hidden'">` : '<img alt="" style="visibility:hidden">';
    return `<tr class="t${r.tier}${step ? ' step' : ''}">
      <td class="rank">${r.rank}</td>
      <td class="delta">${deltaCell(r.delta)}</td>
      <td><div class="club">${icon}<span title="${esc(r.name)}">${esc(r.name)}</span></div></td>
      <td><span class="tier t${r.tier}-fg">${r.tier}</span>
          <span class="league" title="${esc(r.league)}">${esc(r.league)}</span></td>
      <td>${r.leaguePos ?? '–'}</td>
      <td>${r.played}</td><td>${r.won}</td><td>${r.drawn}</td><td>${r.lost}</td>
      <td>${r.goalsFor}:${r.goalsAgainst}</td>
      <td>${r.goalDiff > 0 ? '+' : ''}${r.goalDiff}</td>
      <td><b>${r.points}</b></td>
      <td>${r.ppg.toFixed(2)}</td>
    </tr>`;
  }

  function nachladen(){
    const teil = gefiltert.slice(gezeigt, gezeigt + STUECK);
    if (teil.length){
      rows.insertAdjacentHTML('beforeend', teil.map(r => {
        const step = r.tier !== letzteStufe; letzteStufe = r.tier; return zeile(r, step);
      }).join(''));
      gezeigt += teil.length;
    }
    zaehler.textContent = gezeigt < gefiltert.length
      ? `${tausend(gezeigt)} von ${tausend(gefiltert.length)} angezeigt — weiterscrollen lädt nach`
      : `${tausend(gefiltert.length)} Mannschaften`;
    if (gezeigt < gefiltert.length &&
        document.body.scrollHeight <= window.innerHeight + 200) nachladen();
  }

  function render(){
    const term = q.value.trim().toLowerCase();
    const tier = tierFilter.value, league = leagueFilter.value,
          verband = verbandFilter.value;
    gefiltert = RANKING.filter(r =>
      (!tier || String(r.tier) === tier) &&
      (!league || r.league === league) &&
      (!verband || r.verband === verband) &&
      (!term || r.name.toLowerCase().includes(term)));
    gezeigt = 0; letzteStufe = null; rows.innerHTML = '';
    empty.hidden = gefiltert.length > 0;
    nachladen();
    if (suchhinweis){
      const wort = q.value.trim();
      suchhinweis.innerHTML = !wort ? ''
        : (gefiltert.length
            ? `${tausend(gefiltert.length)} ${gefiltert.length === 1
                ? 'Treffer' : 'Treffer'} — <a href="#" id="zumTreffer">zur Tabelle ↓</a>`
            : 'Kein Verein dieses Namens in dieser Rangfolge.');
      const sprung = suchhinweis.querySelector('#zumTreffer');
      if (sprung) sprung.addEventListener('click', e => {
        e.preventDefault(); zurTabelle();
      });
    }
  }

  // Wird von beiden Sonderansichten gebraucht -- muss deshalb vor ihnen
  // deklariert sein, sonst greift die temporale Todeszone von const zu.
  const topBereich = $('topBereich');

  // --- Sonderauswertung DFB-Pokal -------------------------------------
  const pokal = d.pokal;
  const pokalBereich = $('pokalBereich');
  const paarungsZeile = p => `<tr>
      <td class="rank">${p.abstand > 0 ? tausend(p.abstand) : 0}</td>
      <td><div class="club"><span title="${esc(p.heim)}">${esc(p.heim)}</span></div>
          <span class="league">${esc(p.heimLiga)} · Rang ${tausend(p.heimRang)}</span></td>
      <td><div class="club"><span title="${esc(p.gast)}">${esc(p.gast)}</span></div>
          <span class="league">${esc(p.gastLiga)} · Rang ${tausend(p.gastRang)}</span></td>
      <td><b class="${p.differenz < 0 ? 'up' : (p.differenz > 0 ? 'down' : 'flat')}">${
          p.differenz > 0 ? '+' : ''}${tausend(p.differenz)}</b></td>
    </tr>`;

  if (pokal && params.get('pokal')){
    topBereich.hidden = false;
    topBereich.innerHTML = `
      <a class="zurueckknopf" href="#${sport.slug}">← Zurück zu ${esc(sport.name)}</a>
      <h2>🏆 DFB-Pokal, ${esc(pokal.runde)} — alle ${pokal.paarungen.length} Paarungen</h2>
      <p class="unter">Sortiert nach dem Abstand im bundesweiten Ranking. Die
      Differenz ist aus Sicht der Heimmannschaft gerechnet: <b>Rang Heim −
      Rang Gast</b>. Negativ heißt, die Heimmannschaft steht besser.</p>
      <div class="tablewrap"><table class="paarungen">
        <thead><tr><th>Abstand</th><th>Heim</th><th>Gast</th><th>Differenz</th></tr></thead>
        <tbody>${pokal.paarungen.map(paarungsZeile).join('')}</tbody>
      </table></div>`;
    ziel.querySelectorAll('h2, p.unter, #karten, #mehrlink, #eckdaten, '
      + '.grossesuche, #suchhinweis, .controls, '
      + '.tip, .legend, .count, .tablewrap, #pokalBereich').forEach(el => {
        if (!topBereich.contains(el)) el.hidden = true;
      });
    topBereich.querySelectorAll('h2, p.unter, .tablewrap').forEach(el => el.hidden = false);
    window.scrollTo(0, 0);
    return;
  }

  if (pokal){
    pokalBereich.hidden = false;
    pokalBereich.innerHTML = `
      <h2>${ikon('bester')}Sonderauswertung: DFB-Pokal, ${esc(pokal.runde)}</h2>
      <p class="unter">Ausgelost für den ${esc(pokal.termin.split('-').reverse().join('.'))}.
        Wie weit liegen die Gegner im bundesweiten Ranking auseinander?</p>
      <div class="karten">${pokal.hoehepunkte.map(h => `
        <div class="karte">
          <div class="kopf">${ikon(h.key, h.icon)}${esc(h.titel)}</div>
          <div class="verein">${esc(h.wert)}</div>
          <div class="liga">${esc(h.text)}</div>
        </div>`).join('')}</div>
      <p style="margin:12px 0 0"><a class="topknopf"
        href="#${sport.slug}?pokal=1">Alle ${pokal.paarungen.length} Paarungen →</a></p>`;
    // Auf der Sportseite selbst tritt der Pokal hinter die Tabelle zurück;
    // gezeigt wird er nur in der Analyse.
    pokalBereich.hidden = !params.get('analyse');
  }

  // --- Analyseseite ---------------------------------------------------
  // Eckdaten, die übrigen Bestenlisten und die Pokal-Auswertung. Auf der
  // Sportseite standen sie vor der Tabelle und haben sie nach unten
  // gedrückt; wer sie sucht, findet sie hier zusammen.
  if (params.get('analyse')){
    const analyse = $('analyseBereich');
    analyse.hidden = false;
    analyse.innerHTML = `
      <a class="zurueckknopf" href="#${sport.slug}">← Zurück zu ${esc(sport.name)}</a>
      <h2>Auswertungen — ${esc(sport.name)}</h2>
      <p class="unter">Die Zahlen hinter der Tabelle, alle Bestenlisten${
        d.pokal ? ' und die Pokal-Auswertung' : ''}.</p>
      <div class="sportkarten">${eckdaten.map(([k, v]) =>
        `<div class="sportkarte"><div class="zahl">${v}</div>
         <div class="klein">${k}</div></div>`).join('')}</div>
      ${alle.length ? `<h2>Alle Bestenlisten</h2>
        <p class="unter">Alle ${alle.length} Auswertungen quer zur Tabelle,
          jede mit ihrer vollständigen Liste.</p>
        <div class="karten">${alle.map(k => kennzahl(k)).join('')}</div>` : ''}`;
    ziel.querySelectorAll('h2, p.unter, #karten, #mehrlink, #eckdaten, '
      + '.grossesuche, #suchhinweis, .controls, .tip, .legend, .count, '
      + '.tablewrap').forEach(el => {
        if (!analyse.contains(el) && !pokalBereich.contains(el)) el.hidden = true;
      });
    analyse.querySelectorAll('h2, p.unter').forEach(el => el.hidden = false);
    window.scrollTo(0, 0);
    return;
  }

  // --- Top-100 einer Kennzahl ----------------------------------------
  const karte = (d.kennzahlen || []).find(k => k.key === params.get('top'));
  if (karte){
    const minSpiele = d.minSpiele || 1;
    // Bei den Wochenlisten nur, wer sich in die passende Richtung bewegt hat --
    // sonst stünden unter den "Aufsteigern" am Ende die größten Verlierer.
    let feld;
    if (karte.key === 'aufsteiger')      feld = RANKING.filter(r => r.delta > 0);
    else if (karte.key === 'absteiger')  feld = RANKING.filter(r => r.delta < 0);
    else                                 feld = RANKING.filter(r => r.played >= minSpiele);
    feld = feld.slice().sort((a, b) => {
      const wa = SORTIERUNG[karte.key](a), wb = SORTIERUNG[karte.key](b);
      for (let i = 0; i < wa.length; i++){
        if (wb[i] !== wa[i]) return wb[i] - wa[i];
      }
      return 0;
    }).slice(0, 100);

    topBereich.hidden = false;
    topBereich.innerHTML = `
      <a class="zurueckknopf" href="#${sport.slug}">← Zurück zu ${esc(sport.name)}</a>
      <h2>${ikon(karte.key, karte.icon)}${esc(karte.titel)} — ${feld.length < 100
          ? `alle ${tausend(feld.length)}` : 'Top 100'}</h2>
      <p class="unter">${esc(karte.erklaerung)}</p>
      <div class="tablewrap"><table class="topliste">
        <thead><tr><th>#</th><th>Verein</th><th>Liga</th>
          <th>Sp</th><th title="Erzielte ${esc(wort.mehrzahl)} : ${esc(wort.gegen)}">${esc(wort.mehrzahl)}</th>
          <th title="${esc(wort.diff)}">Diff</th>
          <th>${esc(karte.spalte)}</th><th>Rang gesamt</th></tr></thead>
        <tbody>${feld.map((r, i) => `<tr class="t${r.tier}">
          <td class="rank">${i + 1}</td>
          <td><div class="club"><span title="${esc(r.name)}">${esc(r.name)}</span></div></td>
          <td><span class="tier t${r.tier}-fg">${r.tier}</span>
              <span class="league" title="${esc(r.league)}">${esc(r.league)}</span></td>
          <td>${r.played}</td>
          <td>${r.goalsFor}:${r.goalsAgainst}</td>
          <td>${r.goalDiff > 0 ? '+' : ''}${r.goalDiff}</td>
          <td><b>${WERT[karte.key](r)}</b></td>
          <td>${tausend(r.rank)}</td></tr>`).join('')}</tbody>
      </table></div>`;
    // Karten und Gesamttabelle treten dahinter zurück.
    ziel.querySelectorAll('h2, p.unter, #karten, #mehrlink, #eckdaten, '
      + '.grossesuche, #suchhinweis, .controls, '
      + '.tip, .legend, .count, .tablewrap').forEach(el => {
        if (!topBereich.contains(el)) el.hidden = true;
      });
    topBereich.querySelectorAll('h2, p.unter, .tablewrap').forEach(el => el.hidden = false);
    window.scrollTo(0, 0);
    return;
  }

  // Die große Suche filtert die Tabelle darunter. Enter springt hin --
  // sonst tippt jemand oben und sieht nicht, dass unten etwas passiert.
  const suchhinweis = $('suchhinweis');
  const zurTabelle = () => $('tabellenTitel').scrollIntoView({behavior: 'smooth'});
  $('sportSuche').addEventListener('submit', e => { e.preventDefault(); zurTabelle(); });

  if (params.get('q')) q.value = params.get('q');
  if (params.get('verband')) verbandFilter.value = params.get('verband');
  if (params.get('stufe')) tierFilter.value = params.get('stufe');
  [q, tierFilter, leagueFilter, verbandFilter].forEach(el =>
    el.addEventListener('input', render));
  if (!window.__scrollHandler){
    window.__scrollHandler = true;
    window.addEventListener('scroll', () => {
      const fn = window.__nachladen;
      if (fn) fn();
    }, {passive: true});
  }
  window.__nachladen = () => {
    if (gezeigt >= gefiltert.length) return;
    if (window.scrollY + window.innerHeight >= document.body.scrollHeight - 800) nachladen();
  };
  render();
}

route();
</script>
</body>
</html>
"""


def _tier_css(max_tier: int = 14) -> str:
    """Farbband je Ligastufe plus farbige Kante beim Stufenwechsel."""
    zeilen = []
    for t in range(1, max_tier + 1):
        zeilen.append(f".t{t}-fg{{color:var(--t{t})}}")
        zeilen.append(f"tbody tr.t{t}{{background:color-mix(in srgb,"
                      f"var(--t{t}) 7%, var(--panel))}}")
    zeilen.append("tbody tr.step > td{border-top:2px solid var(--line)}")
    for t in range(1, max_tier + 1):
        zeilen.append(f"tbody tr.step.t{t} > td{{border-top-color:var(--t{t})}}")
    return "\n".join(zeilen)


def write_shell(out_dir: Path, sports: list[dict]) -> None:
    """Schreibt index.html. Die Daten je Sportart liegen in data/<slug>.json."""
    # Kennung des Startbilds, damit Messenger eine neue Vorschau holen, wenn
    # sich das Bild ändert -- sie zwischenspeichern sonst tagelang.
    # Für die Teilen-Vorschau das eigens zugeschnittene Teaserbild, sonst
    # das Startbild. Der Zuschnitt spart den verwaschenen Bildteil aus.
    start = out_dir / "header.jpg"
    startversion = (hashlib.sha1(start.read_bytes()).hexdigest()[:8]
                    if start.exists() else "0")
    teaser = "teaser.jpg" if (out_dir / "teaser.jpg").exists() else "header.jpg"
    bild = out_dir / teaser
    version, breite, hoehe = "0", "1200", "630"
    if bild.exists():
        version = hashlib.sha1(bild.read_bytes()).hexdigest()[:8]
        try:
            from PIL import Image
            with Image.open(bild) as im:
                breite, hoehe = str(im.size[0]), str(im.size[1])
        except Exception:
            pass

    html = TEMPLATE
    for schluessel, wert in {
        "__TIER_CSS__": _tier_css(),
        "__SPORTS__": json.dumps(sports, ensure_ascii=False),
        "__IKONEN__": ikonen.js_objekt(),
        "__KARTENBOX__": karte.VIEWBOX,
        "__KARTENPFAD__": karte.UMRISS,
        "__URL__": BASIS_URL,
        "__BILDVERSION__": version,
        "__BILDBREITE__": breite,
        "__BILDHOEHE__": hoehe,
        "__TEASER__": teaser,
        "__STARTBILD__": startversion,
        "__ANSCHRIFT__": _anschrift_html(),
        "__KONTAKT__": _kontakt_html(),
    }.items():
        html = html.replace(schluessel, wert)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
