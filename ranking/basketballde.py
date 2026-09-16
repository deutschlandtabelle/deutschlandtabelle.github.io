"""Adapter für basketball-bund.net, das Portal des Deutschen Basketball Bunds.

Zwei Endpunkte reichen für alles:

    POST /rest/wam/data                     -- Ligasuche, seitenweise
    GET  /rest/competition/actual/id/<id>   -- Tabelle einer Liga

Die Ligasuche ist derselbe Dienst, der die Suchmaske auf der Seite füllt. Sie
nimmt Filter für Verband, Gebiet, Spielklasse und Altersklasse/Geschlecht
entgegen; wir setzen nur letzteren, auf "Senioren m" oder "Senioren w", und
blättern über `startAtIndex`, bis `hasMoreData` falsch wird.

Anders als im Fußball gibt es keine Pyramidenreihenfolge in den Daten: die
Spielklassen-IDs sind je Verband frei vergeben (über hundert verschiedene), und
ihre Nummerierung sagt nichts über die Höhe. Die Einordnung läuft deshalb über
den Klassennamen -- `skName` ist die Sprache des Verbands ("Oberliga",
"Bezirksklasse", "Kreisliga B") und über alle Verbände hinweg erstaunlich
einheitlich. Unterhalb der Bundesligen bleibt das eine Näherung; im Fußball
liefert die Quelle die Reihenfolge mit, hier nicht.

Punkte: der deutsche Basketball zählt zwei Punkte je Sieg, null je Niederlage,
Unentschieden gibt es nicht. `anzGewinnpunkte` ist die fertige Punktzahl.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ENABLED = True

BASE = "https://www.basketball-bund.net/rest"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Altersklasse/Geschlecht in der Ligasuche. Jugend lassen wir aus -- ClubRank
# rankt Vereinsmannschaften im Seniorenbereich.
GESCHLECHT = {"maenner": "3_1", "frauen": "3_2"}

# Klassenname -> Ligastufe. Von oben nach unten geprüft, die erste Regel
# gewinnt; deshalb stehen "Kreisliga B" und "1. Regionalliga" vor den
# allgemeineren Formen. Die Bundesligen sind gesetzt, darunter folgt die
# übliche Staffelung der Landesverbände.
STUFEN: list[tuple[re.Pattern, int]] = [
    (re.compile(r"^1\.\s*bundesliga"), 1),
    (re.compile(r"^2\.\s*bundesliga"), 2),      # ProA; ProB wird unten auf 3 gesetzt
    (re.compile(r"^1\.\s*regionalliga"), 4),
    (re.compile(r"^2\.\s*regionalliga"), 5),
    (re.compile(r"^regionalliga"), 4),
    (re.compile(r"^(oberliga|bayernliga)"), 6),
    (re.compile(r"^(landesliga|stadtliga|regionsliga)"), 7),
    (re.compile(r"^bezirksoberliga"), 8),
    (re.compile(r"^(bezirksliga|bestenliga)"), 9),
    (re.compile(r"^(bezirksklasse|regionsklasse|bestenklasse)"), 10),
    # Von fein nach grob: "Kreisliga B" muss vor "Kreisliga" stehen, sonst
    # fängt die allgemeine Regel sie ab.
    (re.compile(r"^(kreisliga\s*c\b|c-klasse)"), 13),
    (re.compile(r"^(2\.\s*kreisliga|kreisliga\s*b\b|b-klasse|kreisklasse)"), 12),
    (re.compile(r"^(kreisliga\s*a\b|a-klasse)"), 11),
    (re.compile(r"^(kreisliga|seniorenliga)"), 11),
]

# ProA und ProB heißen beide "2. Bundesliga", liegen aber übereinander: die
# ProB ist die dritthöchste Spielklasse. Nur der Liganame trennt sie.
PROB = re.compile(r"\bpro\s*b\b", re.I)

# Kein Ligabetrieb: Pokale, Endrunden, Turniere. Sie stehen in derselben Liste
# wie die Ligen und würden sonst als eigene "Staffeln" im Ranking landen.
KEIN_LIGABETRIEB = re.compile(
    r"pokal|meisterschaft|endrunde|turnier|offene\s+runde|^keine$|"
    r"freundschaft|testspiel|vorbereitung|play-?off|quali|finale|"
    # Relegation und Ü-Wettbewerbe (Ü35, Ü40, Ü50) sind kein regulärer
    # Ligabetrieb der Aktiven.
    r"relegation|auf-?\s*/?\s*abstieg|\bü\s?\d{2}\b",
    re.I)

# Rollstuhlbasketball hat einen eigenen Verband, eigene Regeln und eine eigene
# Bundesliga. Er gehört nicht in dieselbe Rangfolge -- so wenig wie Hallenfußball
# in die des Rasens.
AUSGESCHLOSSENE_VERBAENDE = {"Deutscher Rollstuhlbasketball"}


def _stufe(sk_name: str, liga_name: str = "") -> int | None:
    text = (sk_name or "").strip().lower()
    for muster, stufe in STUFEN:
        if muster.match(text):
            if stufe == 2 and PROB.search(liga_name or ""):
                return 3
            return stufe
    return None


class BasketballBund:
    def __init__(self, cache_dir: Path, min_interval: float = 0.5,
                 ttl: float = 3 * 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.min_interval = min_interval
        self.ttl = ttl
        self._last = 0.0

    def _abruf(self, url: str, body: dict | None = None):
        schluessel = hashlib.sha1(
            (url + json.dumps(body or {}, sort_keys=True)).encode()).hexdigest()[:20]
        blob = self.cache_dir / f"bbd_{schluessel}.json"
        if blob.exists() and (time.time() - blob.stat().st_mtime) < self.ttl:
            try:
                return json.loads(blob.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        warten = self.min_interval - (time.monotonic() - self._last)
        if warten > 0:
            time.sleep(warten)
        kopf = {"User-Agent": UA, "Accept": "application/json"}
        daten = None
        if body is not None:
            kopf["Content-Type"] = "application/json"
            daten = json.dumps(body).encode()
        req = urllib.request.Request(url, data=daten, headers=kopf,
                                     method="POST" if body is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                text = resp.read().decode("utf-8", "ignore")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            self._last = time.monotonic()
            return None
        self._last = time.monotonic()
        if not text.strip():
            return None
        try:
            antwort = json.loads(text)
        except json.JSONDecodeError:
            return None
        blob.write_text(text, encoding="utf-8")
        return antwort

    def _suche(self, geschlecht: str, verband=None, spielklasse=None,
               gebiet=None) -> dict:
        return (self._abruf(f"{BASE}/wam/data", {
            "token": 0,
            "verbandIds": [verband] if verband is not None else [],
            "gebietIds": [gebiet] if gebiet is not None else [],
            "ligatypId": 0,
            "akgGeschlechtIds": [GESCHLECHT[geschlecht]],
            "altersklasseIds": [],
            "spielklasseIds": [spielklasse] if spielklasse is not None else [],
            "sortBy": 0, "startAtIndex": 0,
        }) or {}).get("data") or {}

    def ligen(self, geschlecht: str, verbose: bool = True) -> list[dict]:
        """Alle Seniorenligen einer Geschlechtsklasse.

        Die Suche liefert immer nur die ersten zehn Treffer -- `startAtIndex`
        wird von der Schnittstelle ignoriert, blättern geht also nicht. Was sie
        mitliefert, sind die Trefferzahlen je Verband, Spielklasse und Gebiet.
        Damit lässt sich die Menge so lange verfeinern, bis sie auf eine Seite
        passt: erst je Verband, bei mehr als zehn Treffern zusätzlich je
        Spielklasse, und wenn das noch nicht reicht, je Gebiet.
        """
        gefunden: dict[int, dict] = {}
        unvollstaendig: list[str] = []

        def einsammeln(seite: dict) -> bool:
            """Übernimmt die Ligen einer Antwort. True, wenn sie vollständig war."""
            liste = seite.get("ligaListe") or {}
            for l in liste.get("ligen") or []:
                if l.get("ligaId") is not None:
                    gefunden.setdefault(l["ligaId"], l)
            return not liste.get("hasMoreData")

        wurzel = self._suche(geschlecht)
        for v in wurzel.get("verbaende") or []:
            if not v.get("hits"):
                continue
            antwort = self._suche(geschlecht, verband=v["id"])
            if einsammeln(antwort):
                continue
            for sk in antwort.get("spielklassen") or []:
                unter = self._suche(geschlecht, verband=v["id"],
                                    spielklasse=sk["id"])
                if einsammeln(unter):
                    continue
                for geb in unter.get("gebiete") or []:
                    tiefer = self._suche(geschlecht, verband=v["id"],
                                         spielklasse=sk["id"], gebiet=geb["id"])
                    if not einsammeln(tiefer):
                        unvollstaendig.append(
                            f'{v.get("label")}/{sk.get("label")}/{geb.get("id")}')
        if verbose and unvollstaendig:
            print(f"  basketball-bund.net: {len(unvollstaendig)} Abschnitte "
                  f"blieben angeschnitten ({unvollstaendig[:3]})", file=sys.stderr)
        return list(gefunden.values())

    def tabelle(self, liga_id: int) -> tuple[list[dict], str | None]:
        """Tabellenzeilen einer Liga und der Saisonname zur Kontrolle."""
        antwort = self._abruf(f"{BASE}/competition/actual/id/{liga_id}")
        daten = (antwort or {}).get("data") or {}
        eintraege = ((daten.get("tabelle") or {}).get("entries")) or []
        saison = (daten.get("ligaData") or {}).get("seasonName")
        zeilen = []
        for e in eintraege:
            team = e.get("team") or {}
            name = (team.get("teamname") or "").strip()
            if not name or team.get("verzicht"):
                # "verzicht" heißt zurückgezogen -- die Mannschaft steht noch
                # in der Tabelle, spielt aber nicht mehr.
                continue
            siege, niederlagen = int(e.get("s") or 0), int(e.get("n") or 0)
            spiele = int(e.get("anzspiele") or 0)
            # Basketball kennt kein Unentschieden -- eine abgesagte oder
            # annullierte Partie wird aber gelegentlich als solche gewertet und
            # bringt je einen Punkt statt zwei. In der Tabelle steht sie dann
            # unter den Spielen, aber weder bei den Siegen noch den Niederlagen.
            # Was übrig bleibt, gehört also in diese Spalte; sie hart auf null
            # zu setzen hieße, dass Siege + Niederlagen die Spielzahl verfehlen.
            unentschieden = max(0, spiele - siege - niederlagen)
            zeilen.append({
                "name": name,
                "played": spiele,
                "won": siege, "drawn": unentschieden, "lost": niederlagen,
                "goals_for": int(e.get("koerbe") or 0),
                "goals_against": int(e.get("gegenKoerbe") or 0),
                # Zwei Punkte je Sieg. Steht fertig in den Daten, wird aber
                # zur Sicherheit aus den Siegen abgeleitet, wenn das Feld fehlt.
                "points": int(e.get("anzGewinnpunkte") or (2 * siege)),
            })
        return zeilen, saison


def fetch(cache_dir: Path, geschlecht: str = "maenner",
          verbose: bool = True) -> list[dict]:
    """Liefert je Liga {name, tier, verband, area, spielklasse, staffel, rows}."""
    if not ENABLED:
        return []
    client = BasketballBund(cache_dir)
    ligen = client.ligen(geschlecht, verbose)
    if verbose:
        print(f"  basketball-bund.net: {len(ligen)} Wettbewerbe gefunden "
              f"({geschlecht})", file=sys.stderr)

    kandidaten, ohne_stufe = [], set()
    for l in ligen:
        name = (l.get("liganame") or "").strip()
        sk = (l.get("skName") or "").strip()
        if KEIN_LIGABETRIEB.search(name) or KEIN_LIGABETRIEB.search(sk):
            continue
        if (l.get("verbandName") or "") in AUSGESCHLOSSENE_VERBAENDE:
            continue
        stufe = _stufe(sk, name)
        if stufe is None:
            ohne_stufe.add(sk)
            continue
        # ProA und ProB heißen bei der Quelle beide "2. Bundesliga", liegen aber
        # auf zwei Stufen. Die Spielklasse muss den Unterschied mitführen, sonst
        # steht in den CSV-Dateien derselbe Name für zwei Ebenen.
        if stufe == 3 and PROB.search(name):
            sk = f"{sk} (ProB)"
        elif stufe == 2 and sk.lower().startswith("2."):
            sk = f"{sk} (ProA)"
        kandidaten.append((l, stufe, sk))

    if verbose and ohne_stufe:
        print(f"  basketball-bund.net: keine Stufe für {sorted(ohne_stufe)}",
              file=sys.stderr)

    raus, benutzt = [], set()
    for l, stufe, sk in kandidaten:
        liga_id = l.get("ligaId")
        if liga_id is None:
            continue
        zeilen, _saison = client.tabelle(liga_id)
        if len(zeilen) < 2:
            continue
        label = (l.get("liganame") or sk).strip()
        gebiet = (l.get("gebietName") or l.get("verbandName") or "").strip() or None
        if label in benutzt:
            label = f"{label} ({liga_id})"
        benutzt.add(label)
        raus.append({
            "name": label, "tier": stufe, "verband": l.get("verbandName") or None,
            "area": gebiet, "spielklasse": sk, "staffel": str(liga_id),
            "rows": zeilen, "quelle": "basketball-bund.net",
        })
    if verbose:
        mannschaften = sum(len(g["rows"]) for g in raus)
        gespielt = sum(1 for g in raus for r in g["rows"] if r["played"])
        print(f"  basketball-bund.net: {len(raus)} Ligen mit Tabelle, "
              f"{mannschaften} Mannschaften, davon {gespielt} mit Spielen",
              file=sys.stderr)
    return raus
