"""Sonderauswertung DFB-Pokal: wie weit liegen die Gegner auseinander?

Die Paarungen kommen aus OpenLigaDB (Wettbewerb `dfb`). Zu jeder Partie wird
der bundesweite Rang beider Mannschaften herausgesucht und die Differenz
gebildet -- aus Sicht der Heimmannschaft, also Rang(Heim) − Rang(Gast).
Ein negativer Wert heißt: die Heimmannschaft steht besser.

Warum das interessant ist: die Rangfolge kennt jede Ligastufe, deshalb misst
die Differenz den Abstand zweier Gegner über Ligagrenzen hinweg -- und genau
davon lebt der Pokal.
"""
from __future__ import annotations

import sys

from .api import OpenLigaDB
from .model import normalize_name

# Namen, die meine Vereinserkennung nicht selbst auflösen kann.
# "Jeddeloh II" ist ein Ortsname (die Gemeinde heißt so) und kein Hinweis auf
# eine zweite Mannschaft -- die Normalisierung trennt deshalb, was zusammen
# gehört. Solche Fälle lassen sich nur von Hand nachtragen.
ALIASE = {
    "ssv jeddeloh": "ssv jeddeloh ii",
}


def _rang_index(ranking: list[dict]) -> dict[str, dict]:
    """Schnellzugriff Name -> Datensatz. Bei doppelten Namen gewinnt der
    höhere Rang: im Pokal spielt die erste Mannschaft, nicht die Reserve."""
    index: dict[str, dict] = {}
    for r in ranking:
        key = normalize_name(r["name"])
        if key not in index or r["rank"] < index[key]["rank"]:
            index[key] = r
    return index


def _finde(index: dict[str, dict], name: str) -> dict | None:
    key = normalize_name(name)
    return index.get(key) or index.get(ALIASE.get(key, ""))


def auswertung(client: OpenLigaDB, season: int, ranking: list[dict],
               runde: str | None = None, verbose: bool = True) -> dict | None:
    """Liefert die Paarungen der jüngsten ausgelosten Runde mit Rangdifferenz."""
    spiele = client.matches("dfb", season, is_current=True)
    if not spiele:
        return None

    # Die jüngste Runde, in der noch nichts gespielt wurde -- das ist die
    # zuletzt ausgeloste. Ist alles gespielt, nehmen wir die letzte Runde.
    runden: dict[str, list] = {}
    for m in spiele:
        runden.setdefault((m.get("group") or {}).get("groupName") or "?", []).append(m)
    if runde and runde in runden:
        name = runde
    else:
        offen = [(n, ms) for n, ms in runden.items()
                 if not any(m.get("matchIsFinished") for m in ms)]
        if not offen:
            return None
        name = max(offen, key=lambda p: min(m["matchDateTime"] for m in p[1]))[0]

    index = _rang_index(ranking)
    paarungen, fehlend = [], []
    for m in sorted(runden[name], key=lambda m: m["matchDateTime"]):
        heim, gast = (m.get("team1") or {}), (m.get("team2") or {})
        rh, rg = _finde(index, heim.get("teamName", "")), _finde(index, gast.get("teamName", ""))
        if not rh or not rg:
            fehlend.append(heim.get("teamName") if not rh else gast.get("teamName"))
            continue
        paarungen.append({
            "termin": m["matchDateTime"][:10],
            "heim": rh["name"], "heimRang": rh["rank"], "heimLiga": rh["league"],
            "heimStufe": rh["tier"], "heimWappen": rh.get("icon"),
            "gast": rg["name"], "gastRang": rg["rank"], "gastLiga": rg["league"],
            "gastStufe": rg["tier"], "gastWappen": rg.get("icon"),
            # Aus Sicht der Heimmannschaft: negativ heißt, sie steht besser.
            "differenz": rh["rank"] - rg["rank"],
            "abstand": abs(rh["rank"] - rg["rank"]),
        })

    if verbose:
        print(f"  DFB-Pokal {name}: {len(paarungen)} Paarungen zugeordnet"
              + (f", nicht gefunden: {fehlend}" if fehlend else ""), file=sys.stderr)
    if not paarungen:
        return None

    def plaetze(n: int) -> str:
        return f"{n:,}".replace(",", ".") + (" Platz" if n == 1 else " Plätze")

    nach_abstand = sorted(paarungen, key=lambda p: -p["abstand"])
    aussenseiter = max(paarungen, key=lambda p: max(p["heimRang"], p["gastRang"]))
    schlechter = ("heim" if aussenseiter["heimRang"] > aussenseiter["gastRang"]
                  else "gast")
    return {
        "runde": name,
        "termin": min(p["termin"] for p in paarungen),
        "paarungen": nach_abstand,
        "fehlend": fehlend,
        "hoehepunkte": [
            {"key": "abstand", "icon": "🪜", "titel": "Größter Abstand",
             "text": f"{nach_abstand[0]['heim']} (Rang "
                     f"{nach_abstand[0]['heimRang']:,}) gegen "
                     f"{nach_abstand[0]['gast']} (Rang "
                     f"{nach_abstand[0]['gastRang']:,})".replace(",", "."),
             "wert": plaetze(nach_abstand[0]["abstand"])},
            {"key": "eng", "icon": "⚖️", "titel": "Engste Paarung",
             "text": f"{nach_abstand[-1]['heim']} gegen {nach_abstand[-1]['gast']}",
             "wert": plaetze(nach_abstand[-1]["abstand"])},
            {"key": "klein", "icon": "🐜", "titel": "Der kleinste Verbliebene",
             "text": f"{aussenseiter[schlechter]} "
                     f"({aussenseiter[schlechter + 'Liga']})",
             "wert": f"Rang {max(aussenseiter['heimRang'], aussenseiter['gastRang']):,}"
                     .replace(",", ".")},
        ],
    }
