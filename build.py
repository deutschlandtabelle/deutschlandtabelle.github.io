#!/usr/bin/env python3
"""Baut das Club-Ranking und schreibt die Seite nach docs/.

    python3 build.py --sport fussball     # Standard
    python3 build.py --sport handball
    python3 build.py --nur-huelle         # nur index.html aus vorhandenen Daten

Je Sportart entstehen:
    docs/data/<sport>.json      Rangfolge, Kennzahlen und Metadaten für die Seite
    docs/<sport>-vereine.csv    eine Zeile je Mannschaft
    docs/<sport>-ligen.csv      eine Zeile je Staffel
Dazu docs/index.html, das alle Sportarten unter #home/#fussball/… zeigt.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

from ranking import (basketballde, fussballde, handballnet, hbl, karte,
                     landing, load, pokal, rank, render, site, wappen)
from ranking.api import OpenLigaDB
from ranking.leagues import EXPECTED_TIER4, current_season

ROOT = Path(__file__).resolve().parent

# Jede Rangfolge ist eine Sportart in einer Geschlechtsklasse. Männer und
# Frauen spielen getrennte Pyramiden mit eigenen Auf- und Abstiegsketten --
# eine gemeinsame Rangfolge hätte keine sportliche Grundlage. Der Slug der
# Männerklasse bleibt ohne Zusatz, damit geteilte Links weiter funktionieren.
SPORTARTEN = {
    "fussball": {
        "name": "Fußball", "sportart": "fussball", "sportName": "Fußball",
        "klasse": "maenner", "klasseName": "Männer",
        "icon": "⚽", "torwort": "Tore", "worte": landing.WORTE_TOR,
        "hinweis": None,
    },
    "fussball-frauen": {
        "name": "Fußball der Frauen", "sportart": "fussball",
        "sportName": "Fußball", "klasse": "frauen", "klasseName": "Frauen",
        "icon": "⚽", "torwort": "Tore", "worte": landing.WORTE_TOR,
        "hinweis": None,
    },
    "handball": {
        "name": "Handball", "sportart": "handball", "sportName": "Handball",
        "klasse": "maenner", "klasseName": "Männer",
        "icon": "🤾", "torwort": "Tore", "worte": landing.WORTE_TOR,
        "hinweis": None,
    },
    "handball-frauen": {
        "name": "Handball der Frauen", "sportart": "handball",
        "sportName": "Handball", "klasse": "frauen", "klasseName": "Frauen",
        "icon": "🤾", "torwort": "Tore", "worte": landing.WORTE_TOR,
        "hinweis": None,
    },
    "basketball": {
        "name": "Basketball", "sportart": "basketball",
        "sportName": "Basketball", "klasse": "maenner", "klasseName": "Männer",
        "icon": "🏀", "torwort": "Körbe", "worte": landing.WORTE_KORB,
        "hinweis": None,
    },
    "basketball-frauen": {
        "name": "Basketball der Frauen", "sportart": "basketball",
        "sportName": "Basketball", "klasse": "frauen", "klasseName": "Frauen",
        "icon": "🏀", "torwort": "Körbe", "worte": landing.WORTE_KORB,
        "hinweis": None,
    },
}

VERGLEICH = ("Unterhalb der überregionalen Ligen gibt es zwischen den "
             "Landesverbänden keine sportliche Verbindung — für einen "
             "belastbaren Vergleich oben einen <b>Verband</b> wählen.")


# --- Fußball --------------------------------------------------------------
def baue_fussball(cache_dir: Path, season: int, ohne_fussballde: bool,
                  art: str = "Herren"):
    client = OpenLigaDB(cache_dir)
    matches, teams, leagues = load.load(client, season, art=art)
    if not matches and ohne_fussballde:
        return None

    external = {}
    if not ohne_fussballde:
        groups = fussballde.fetch(cache_dir, season, art)
        external = load.merge_standings(teams, groups)
        leagues += [{"shortcut": g["staffel"], "tier": g["tier"], "name": g["name"],
                     "verband": g["verband"], "matches": None,
                     "source": "fussball.de"} for g in groups]

    ranking = rank.build(matches, teams, external)

    found = {lg["name"] for lg in leagues}
    gaps = [n for n in EXPECTED_TIER4 if n not in found]
    verbaende = sorted({lg.get("verband") for lg in leagues
                        if lg.get("source") == "fussball.de" and lg.get("verband")})
    note = note_summary = None
    if external and art == "Frauen":
        note_summary = ("Ab Ligastufe 4 nur innerhalb eines Landesverbands "
                        "sinnvoll vergleichbar")
        note = (f"Erfasst sind die Landesverbände ({len(verbaende)} mit Daten) "
                "ab der obersten Frauenklasse abwärts. Die Frauenpyramide ist "
                "flacher als die der Männer: unter der Regionalliga folgt "
                "direkt die oberste Klasse des Landesverbands. <b>Zwei Lücken:</b> "
                "von den fünf Regionalligen liefert die offene Quelle nur den "
                "Westen, und wie bei den Männern gibt es unterhalb der "
                "Regionalliga zwischen den Verbänden keine gemeinsame Auf- und "
                "Abstiegskette — ein Vergleich ist dort nicht sportlich "
                "begründet, sondern nur rechnerisch.")
    elif external:
        note_summary = ("Ab Ligastufe 5 nur innerhalb eines Landesverbands "
                        "sinnvoll vergleichbar")
        note = (f"Erfasst sind alle {len(verbaende)} Landesverbände, von der "
                "Bundesliga bis hinunter zur Kreisklasse. <b>Aber:</b> unterhalb "
                "der Regionalliga gibt es zwischen den Verbänden keine sportliche "
                "Verbindung — ein Kreisligist aus Oberberg und einer aus Sachsen "
                "begegnen sich nie, weder direkt noch über eine Auf- und "
                "Abstiegskette. Die bundesweite Rangfolge ordnet dort nur nach "
                "Ligastufe und Punkten pro Spiel; ein sportliches Kräftemessen "
                "ist sie nicht. Innerhalb eines Verbands ist sie belastbar, weil "
                "dort alle Staffeln über Auf- und Abstieg zusammenhängen.")
    if gaps and art == "Herren":
        note = (note or "") + " Auf Ligastufe 4 fehlen zudem " + ", ".join(gaps) + "."

    return ranking, len(leagues), len(matches), note, note_summary


# --- Handball -------------------------------------------------------------
def baue_handball(cache_dir: Path, season: int, klasse: str = "maenner"):
    # Zwei Quellen: die Bundesligen laufen über das Sportradar-Widget der HBL,
    # alles darunter über handball.net. Für die Frauen gibt es kein passendes
    # HBL-Widget -- ihre Rangfolge beginnt deshalb bei der 3. Liga.
    # handball.net führt die Geschlechter als "M"/"F"/"X" (Male, Female, Mixed).
    geschlecht = "F" if klasse == "frauen" else "M"
    groups = handballnet.fetch(cache_dir, season, geschlecht)
    if klasse == "maenner":
        groups = hbl.fetch(cache_dir) + groups
    if not groups:
        return None
    teams: dict = {}
    external = load.merge_standings(teams, groups)
    ranking = rank.build([], teams, external)
    verbaende = sorted({g["verband"] for g in groups if g["verband"]})
    note_summary = ("Ab Ligastufe 3 nur innerhalb eines Verbands sinnvoll "
                    "vergleichbar")
    if klasse == "frauen":
        note = ("Die Rangfolge beginnt bei der 3. Liga: die Handball-Bundesliga "
                "Frauen und die 2. Bundesliga liegen auf einer eigenen Plattform, "
                f"für die es keine offene Schnittstelle gibt. Darunter deckt "
                f"handball.net {len(verbaende)} Verbände und Kreise ab — aber "
                "nicht jeder Landesverband wickelt seinen Spielbetrieb dort ab, "
                "die Abdeckung ist also nicht flächendeckend. Und zwischen "
                "Verbänden gibt es unterhalb der Regionalliga keine gemeinsame "
                "Auf- und Abstiegskette; ein Vergleich ist dort nicht sportlich "
                "begründet.")
        return ranking, len(groups), 0, note, note_summary
    note = ("Die 1. und 2. Bundesliga kommen von der HBL, alles darunter aus dem "
            f"Spielbetrieb auf handball.net mit {len(verbaende)} Verbänden und "
            "Kreisen. <b>Eine Lücke bleibt:</b> nicht jeder Landesverband wickelt "
            "seinen Spielbetrieb über handball.net ab, die Abdeckung unterhalb der "
            "überregionalen Ligen ist daher nicht flächendeckend. Und wie im Fußball "
            "gilt: zwischen Verbänden gibt es unterhalb der Regionalliga keine "
            "gemeinsame Auf- und Abstiegskette, ein Vergleich ist dort also nicht "
            "sportlich begründet.")
    return ranking, len(groups), 0, note, note_summary


# --- Basketball -----------------------------------------------------------
def baue_basketball(cache_dir: Path, klasse: str = "maenner"):
    groups = basketballde.fetch(cache_dir, klasse)
    if not groups:
        return None
    teams: dict = {}
    external = load.merge_standings(teams, groups)
    ranking = rank.build([], teams, external)
    verbaende = sorted({g["verband"] for g in groups if g["verband"]})
    gespielt = sum(1 for r in ranking if r["played"])
    note_summary = ("Ab Ligastufe 3 nur innerhalb eines Verbands sinnvoll "
                    "vergleichbar")
    note = (f"Alles aus dem Spielbetrieb des Deutschen Basketball Bunds, "
            f"{len(verbaende)} Verbände von der Bundesliga bis zur Kreisliga. "
            "<b>Zur Einordnung:</b> anders als im Fußball liefert die Quelle "
            "keine Reihenfolge der Spielklassen mit — die Ligastufe wird aus dem "
            "Klassennamen abgeleitet (Oberliga, Bezirksliga, Kreisliga A …). "
            "Das trifft die Ordnung innerhalb eines Verbands, ist zwischen "
            "Verbänden aber eine Näherung. Und wie in den anderen Sportarten "
            "verbindet unterhalb der Regionalliga keine Auf- und Abstiegskette "
            "die Verbände miteinander.")
    if not gespielt:
        note = ("<b>Die Saison hat noch nicht begonnen.</b> Alle Mannschaften "
                "stehen bei null Spielen, die Rangfolge ordnet deshalb vorerst "
                "nur nach Ligastufe. Sobald die ersten Spieltage laufen, füllt "
                "sie sich von selbst. ") + note
    return ranking, len(groups), 0, note, note_summary


# --- Ausgabe --------------------------------------------------------------
def schreibe_sport(out: Path, slug: str, ranking, leagues, matches,
                   note, note_summary, season) -> dict:
    meta = {
        "generated": dt.datetime.now().strftime("%d.%m.%Y, %H:%M Uhr"),
        "generatedIso": dt.datetime.now().isoformat(timespec="seconds"),
        "season": season,
        "season_label": f"{season}/{str(season + 1)[2:]}",
        "teams": len(ranking),
        "leagues": leagues,
        "matches": matches,
        "note": note,
        "note_summary": note_summary,
    }
    (out / "data").mkdir(parents=True, exist_ok=True)
    paket = render.compact(ranking)
    paket["meta"] = meta
    # Wappen mitliefern statt verlinken: ein Bild von einem fremden Server
    # gibt die IP-Adresse jedes Besuchers dorthin weiter.
    wappen.einbetten(paket, out)
    zahlen = landing.kennzahlen(ranking, SPORTARTEN[slug].get("worte"))
    paket["kennzahlen"] = zahlen["karten"]
    # Die Seite baut die Top-100-Listen selbst; dafür braucht sie dieselbe
    # Mindestspielzahl, mit der auch die Karten gerechnet wurden.
    paket["minSpiele"] = zahlen["min_spiele"]
    (out / "data" / f"{slug}.json").write_text(
        json.dumps(paket, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    if slug == "fussball":
        # Sonderauswertung DFB-Pokal: die zuletzt ausgeloste Runde mit dem
        # Rangabstand beider Gegner.
        sonder = pokal.auswertung(OpenLigaDB(ROOT / "data" / "cache"),
                                  season, ranking)
        if sonder:
            paket["pokal"] = sonder
            wappen.einbetten(paket, out)
            (out / "data" / f"{slug}.json").write_text(
                json.dumps(paket, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8")

    render.write_vereine(out, ranking, slug)
    render.write_ligen(out, ranking, slug)

    # Spitzenreiter für die Deutschlandkarte auf der Startseite. Der Ort
    # kommt aus dem Vereinsnamen; gibt er keinen her, bleibt der Verein ohne
    # Punkt auf der Karte -- eine geratene Position wäre schlechter als keine.
    spitze = None
    if ranking:
        erster = ranking[0]
        ort = karte.verorten(erster["name"])
        spitze = {"name": erster["name"], "liga": erster["league"],
                  "stufe": erster["tier"],
                  "ort": ort[0] if ort else None,
                  "x": ort[1] if ort else None, "y": ort[2] if ort else None}

    info = dict(SPORTARTEN[slug])
    info.update({
        "spitze": spitze,
        "slug": slug, "ready": True, "teams": len(ranking), "leagues": leagues,
        "tiers": len({r["tier"] for r in ranking}),
        "season": meta["season_label"], "generated": meta["generated"],
        "vergleichHinweis": VERGLEICH,
        "fuss": (f'<p>Stand {meta["generated"]} · Saison {meta["season_label"]} · '
                 f'<a href="{slug}-vereine.csv">{slug}-vereine.csv</a> · '
                 f'<a href="{slug}-ligen.csv">{slug}-ligen.csv</a></p>'
                 '<p class="rechtslinks"><a href="#impressum">Impressum</a> · '
                 '<a href="#datenschutz">Datenschutz</a> · '
                 '<a href="#impressum">Quellen und Lizenzen</a></p>'),
    })
    return info


def huelle(out: Path) -> None:
    """index.html aus den vorhandenen Sportdaten neu schreiben."""
    verzeichnis = out / "data"
    uebersicht = []
    for slug, vorgabe in SPORTARTEN.items():
        pfad = verzeichnis / f"{slug}.info.json"
        if pfad.exists():
            uebersicht.append(json.loads(pfad.read_text(encoding="utf-8")))
        else:
            uebersicht.append({**vorgabe, "slug": slug, "ready": False})
    site.write_shell(out, uebersicht)
    fertig = [s["slug"] for s in uebersicht if s.get("ready")]
    print(f"index.html geschrieben · Sportarten mit Daten: {', '.join(fertig) or '—'}",
          file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sport", choices=sorted(SPORTARTEN), default="fussball")
    ap.add_argument("--nur-huelle", action="store_true",
                    help="nur index.html neu bauen, nichts abrufen")
    ap.add_argument("--no-cache", action="store_true", help="Cache vorher leeren")
    ap.add_argument("--no-fussballde", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "docs"))
    ap.add_argument("--season", type=int, default=None)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.nur_huelle:
        huelle(out)
        return 0

    cache_dir = ROOT / "data" / "cache"
    if args.no_cache and cache_dir.exists():
        shutil.rmtree(cache_dir)
    season = args.season or current_season()
    print(f"{SPORTARTEN[args.sport]['name']} · Saison {season}/{str(season+1)[2:]}",
          file=sys.stderr)


    vorgabe = SPORTARTEN[args.sport]
    sportart, klasse = vorgabe["sportart"], vorgabe["klasse"]
    if sportart == "fussball":
        ergebnis = baue_fussball(cache_dir, season, args.no_fussballde,
                                 "Frauen" if klasse == "frauen" else "Herren")
    elif sportart == "handball":
        ergebnis = baue_handball(cache_dir, season, klasse)
    else:
        ergebnis = baue_basketball(cache_dir, klasse)

    if not ergebnis:
        print("Keine Daten erhalten — Abbruch.", file=sys.stderr)
        return 1

    ranking, leagues, matches, note, note_summary = ergebnis
    info = schreibe_sport(out, args.sport, ranking, leagues, matches,
                          note, note_summary, season)
    (out / "data" / f"{args.sport}.info.json").write_text(
        json.dumps(info, ensure_ascii=False), encoding="utf-8")
    huelle(out)

    print(f"\n{len(ranking)} Mannschaften · {leagues} Staffeln · "
          f"{info['tiers']} Ligastufen", file=sys.stderr)
    for r in ranking[:6]:
        print(f"  {r['rank']:5d}. {r['name']:<32.32s} {r['league']:<26.26s} "
              f"{r['points']:3d} Pkt / {r['played']:2d} Sp", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
