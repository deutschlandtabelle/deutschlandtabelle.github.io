"""Die Bestenlisten: die Tabelle einmal quer gelesen.

Acht Kennzahlen ohne Rücksicht auf die Ligastufe -- der beste Verein des
Landes kann in der Kreisklasse spielen. Berechnet aus demselben Datensatz,
den auch die Tabelle zeigt; es gibt keine zweite Wahrheit.

Die Seitenvorlage steht in `site.py`.
"""
from __future__ import annotations


# Ein einziges gutes Spiel soll niemanden zum besten Verein Deutschlands
# machen. Die Schwelle sinkt automatisch, wenn zu Saisonbeginn noch kaum
# jemand so weit ist.
MIN_SPIELE_STUFEN = (5, 4, 3, 2, 1)
MIN_KANDIDATEN = 50


def _schwelle(ranking: list[dict]) -> int:
    for n in MIN_SPIELE_STUFEN:
        if sum(1 for r in ranking if r["played"] >= n) >= MIN_KANDIDATEN:
            return n
    return 1


def _pro_spiel(r: dict, feld: str) -> float:
    return r[feld] / r["played"] if r["played"] else 0.0


# Basketball wirft Körbe, kein Tor fällt dort. Die Rechnung ist dieselbe,
# nur die Wörter sind andere -- deshalb stehen sie an einer Stelle und nicht
# verstreut in den Texten.
WORTE_TOR = {
    "mehrzahl": "Tore", "diff": "Tordifferenz", "diff_kurz": "Tordiff.",
    "gegen": "Gegentore", "fabrik": "Die Torfabrik",
    "erzielt": "eigene Tore", "getroffen": "geschossenen Tore",
}
WORTE_KORB = {
    "mehrzahl": "Körbe", "diff": "Korbdifferenz", "diff_kurz": "Korbdiff.",
    "gegen": "Gegenkörbe", "fabrik": "Die Korbfabrik",
    "erzielt": "eigene Körbe", "getroffen": "geworfenen Körbe",
}


def kennzahlen(ranking: list[dict], worte: dict | None = None) -> dict:
    """Die Bestenlisten quer zur Ligastufe."""
    w = worte or WORTE_TOR
    n = _schwelle(ranking)
    feld = [r for r in ranking if r["played"] >= n]

    def bester(schluessel, quelle=None):
        kandidaten = quelle if quelle is not None else feld
        return max(kandidaten, key=schluessel) if kandidaten else None

    mit_delta = [r for r in ranking if r.get("delta") is not None]

    karten = [
        {
            "icon": "🏆", "titel": "Bester Verein Deutschlands", "key": "bester", "spalte": "Punkte/Spiel",
            "erklaerung": f"Ohne Rücksicht auf die Ligastufe: die meisten Punkte "
                          f"pro Spiel. Bei Gleichstand entscheidet die {w['diff']} "
                          f"pro Spiel, danach die Zahl der {w['getroffen']} "
                          f"pro Spiel. Mindestens {n} Spiele.",
            "team": bester(lambda r: (_pro_spiel(r, "points"),
                                      _pro_spiel(r, "goalDiff"),
                                      _pro_spiel(r, "goalsFor"))),
            "wert": lambda r: f"{_pro_spiel(r, 'points'):.2f} Punkte/Spiel",
        },
        {
            "icon": "🔥", "titel": "Der heißeste Club", "key": "heiss",
            "spalte": f"{w['diff_kurz']}/Spiel",
            "erklaerung": f"Die größte {w['diff']} pro Spiel — wer nicht nur "
                          f"gewinnt, sondern auseinandernimmt. Mindestens {n} Spiele.",
            "team": bester(lambda r: (_pro_spiel(r, "goalDiff"),
                                      _pro_spiel(r, "points"))),
            "wert": lambda r: f"{_pro_spiel(r, 'goalDiff'):+.2f} {w['mehrzahl']}/Spiel",
        },
        {
            "icon": "⚽", "titel": w["fabrik"], "key": "torfabrik",
            "spalte": f"{w['mehrzahl']}/Spiel",
            "erklaerung": f"Meiste {w['erzielt']} pro Spiel. Mindestens {n} Spiele.",
            "team": bester(lambda r: _pro_spiel(r, "goalsFor")),
            "wert": lambda r: f"{_pro_spiel(r, 'goalsFor'):.2f} {w['mehrzahl']}/Spiel",
        },
        {
            "icon": "🧱", "titel": "Das Bollwerk", "key": "bollwerk",
            "spalte": f"{w['gegen']}/Spiel",
            "erklaerung": f"Wenigste {w['gegen']} pro Spiel. Mindestens {n} Spiele.",
            "team": bester(lambda r: (-_pro_spiel(r, "goalsAgainst"),
                                      _pro_spiel(r, "points"))),
            "wert": lambda r: f"{_pro_spiel(r, 'goalsAgainst'):.2f} {w['gegen']}/Spiel",
        },
        {
            "icon": "📈", "titel": "Aufsteiger der Woche", "key": "aufsteiger", "spalte": "Plätze",
            "erklaerung": "Größter Sprung im bundesweiten Ranking gegenüber der "
                          "Vorwoche. Nur für Ligastufen mit Spieldaten — siehe unten.",
            "team": bester(lambda r: r["delta"], mit_delta),
            "wert": lambda r: f"{r['delta']:+d} Plätze auf Rang {r['rank']}",
        },
        {
            "icon": "📉", "titel": "Absteiger der Woche", "key": "absteiger", "spalte": "Plätze",
            "erklaerung": "Größter Verlust im bundesweiten Ranking gegenüber der "
                          "Vorwoche.",
            "team": bester(lambda r: -r["delta"], mit_delta),
            "wert": lambda r: f"{r['delta']:+d} Plätze auf Rang {r['rank']}",
        },
        {
            "icon": "🥶", "titel": "Das Schlusslicht", "key": "schlusslicht", "spalte": "Punkte/Spiel",
            "erklaerung": f"Die schwächste Punkteausbeute des Landes. "
                          f"Mindestens {n} Spiele.",
            "team": bester(lambda r: (-_pro_spiel(r, "points"),
                                      -_pro_spiel(r, "goalDiff"))),
            "wert": lambda r: f"{_pro_spiel(r, 'points'):.2f} Punkte/Spiel",
        },
        {
            "icon": "💥", "titel": "Die dickste Klatsche", "key": "klatsche",
            "spalte": f"{w['diff_kurz']}/Spiel",
            "erklaerung": f"Schlechteste {w['diff']} pro Spiel. "
                          f"Mindestens {n} Spiele.",
            "team": bester(lambda r: (-_pro_spiel(r, "goalDiff"),
                                      -_pro_spiel(r, "points"))),
            "wert": lambda r: f"{_pro_spiel(r, 'goalDiff'):+.2f} {w['mehrzahl']}/Spiel",
        },
    ]

    fertig = []
    for k in karten:
        r = k["team"]
        if not r:
            continue
        fertig.append({
            "icon": k["icon"], "titel": k["titel"], "key": k["key"],
            "spalte": k["spalte"], "erklaerung": k["erklaerung"],
            "verein": r["name"], "liga": r["league"], "stufe": r["tier"],
            "verband": r.get("verband") or "überregional",
            "rang": r["rank"], "wert": k["wert"](r),
        })
    return {"karten": fertig, "min_spiele": n}
