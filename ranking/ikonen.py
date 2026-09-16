"""Strichzeichnungen statt bunter Emoji.

Emoji sehen auf jedem Betriebssystem anders aus -- ein ⚽ ist unter macOS
fotorealistisch, unter Windows flach, unter Android wieder anders. Sie lassen
sich nicht einfärben, nicht auf die Schriftgröße abstimmen und passen zu keinem
Gestaltungsraster. Deshalb liegen hier eigene Icons: ein Strich, eine Farbe
(die des umgebenden Textes), 24x24 als Raster.

Der Schlüssel ist entweder ein sprechender Name (`fussball`, `bester`) oder
das Emoji, das früher an der Stelle stand. Das zweite ist Absicht: die bereits
gebauten Datenpakete führen in `kennzahlen[].icon` noch Emoji, und die sollen
weiter funktionieren, ohne dass jede Sportart neu berechnet werden muss.
"""
from __future__ import annotations

import json

# Alle Pfade im Raster 24x24, Mittelpunkt (12,12), Ballradius 9.
IKONEN: dict[str, str] = {

    # --- Sportarten -----------------------------------------------------
    # Fußball: Fünfeck mit Speichen zur Außenlinie.
    "fussball": (
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M12 7.5 16.28 10.61 14.65 15.64H9.35L7.72 10.61Z"/>'
        '<path d="M12 7.5V3"/><path d="m16.28 10.61 4.28-1.39"/>'
        '<path d="m14.65 15.64 2.64 3.64"/><path d="m9.35 15.64-2.64 3.64"/>'
        '<path d="M7.72 10.61 3.44 9.22"/>'
    ),
    # Handball: drei Nähte, die sich in der Mitte treffen -- das Muster des
    # echten Balls. Unterscheidet sich dadurch klar vom Fußball daneben.
    "handball": (
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M12 12c0-3.4 1.6-6.4 4.6-8.3"/>'
        '<path d="M12 12c-3 .6-6-.3-8.5-2.6"/>'
        '<path d="M12 12c1.4 2.9 1.3 6-.4 9"/>'
    ),
    # Basketball: Längs- und Quernaht plus die beiden Seitennähte. Ohne die
    # Seitennähte -- nur Äquator und Meridiane -- wird daraus ein Globus.
    "basketball": (
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M12 3v18"/><path d="M3.1 12h17.8"/>'
        '<path d="M5.3 5.3c2.4 1.9 3.7 4.1 3.7 6.7s-1.3 4.8-3.7 6.7"/>'
        '<path d="M18.7 5.3C16.3 7.2 15 9.4 15 12s1.3 4.8 3.7 6.7"/>'
    ),

    # --- Kennzahlen-Karten ----------------------------------------------
    "bester": (                                     # Pokal
        '<path d="M8 3.5h8V9a4 4 0 0 1-8 0Z"/>'
        '<path d="M8 5H5.4a2.6 2.6 0 0 0 2.9 4.2"/>'
        '<path d="M16 5h2.6a2.6 2.6 0 0 1-2.9 4.2"/>'
        '<path d="M12 13v3"/><path d="M10.1 16h3.8l.5 4h-4.8Z"/>'
        '<path d="M8.5 20h7"/>'
    ),
    "heiss": (                                      # Flamme
        '<path d="M12 3.2c3 2.9 4.8 5.4 4.8 8.4a4.8 4.8 0 1 1-9.6 0'
        'c0-1.9.9-3.5 2.2-4.9.1 1.3.7 2.2 1.6 2.7.3-2.4-.1-4.3 1-6.2Z"/>'
        '<path d="M12 20a2.6 2.6 0 0 1-2.6-2.6c0-1.4 1.3-2.1 2.6-3.8'
        '1.3 1.7 2.6 2.4 2.6 3.8A2.6 2.6 0 0 1 12 20Z"/>'
    ),
    "torfabrik": (                                  # Tor mit Ball
        '<path d="M4 20.5V7.5h16v13"/><path d="M4 13.5h16"/>'
        '<circle cx="12" cy="17" r="2.4"/>'
    ),
    "bollwerk": (                                   # Schild
        '<path d="M12 3.2 19 5.8v5.3c0 4.3-2.9 7.7-7 9.1-4.1-1.4-7-4.8-7-9.1V5.8Z"/>'
    ),
    "aufsteiger": (
        '<path d="M3.5 16.5 9 11l3.5 3.5L20.5 6.5"/>'
        '<path d="M15.5 6.5h5v5"/>'
    ),
    "absteiger": (
        '<path d="M3.5 7.5 9 13l3.5-3.5 8 8"/>'
        '<path d="M15.5 17.5h5v-5"/>'
    ),
    "schlusslicht": (                               # Schneeflocke
        '<path d="M12 3v18"/><path d="m3.34 7.5 17.32 10"/>'
        '<path d="M20.66 7.5 3.34 17.5"/>'
        '<path d="m9.6 5.4 2.4 2.4 2.4-2.4"/><path d="m9.6 18.6 2.4-2.4 2.4 2.4"/>'
    ),
    "klatsche": (                                   # Blitz
        '<path d="M13.5 2.8 5.8 13.6h5.1l-1 7.6 8-10.9h-5.1Z"/>'
    ),

    # --- Pokal-Sonderauswertung ------------------------------------------
    "abstand": (                                    # Leiter
        '<path d="M8 3v18"/><path d="M16 3v18"/>'
        '<path d="M8 7.5h8"/><path d="M8 12h8"/><path d="M8 16.5h8"/>'
    ),
    "eng": (                                        # Waage
        '<path d="M12 4.5v15"/><path d="M8.5 20h7"/><path d="M4.5 8h15"/>'
        '<path d="M4.5 8 2 13.4a2.9 2.9 0 0 0 5 0Z"/>'
        '<path d="m19.5 8 2.5 5.4a2.9 2.9 0 0 1-5 0Z"/>'
    ),
    "klein": (                                      # groß neben klein
        '<path d="M3 20.5h18"/><path d="M4.8 20.5V14h4.6v6.5"/>'
        '<path d="M14.6 20.5V5.5h4.6v15"/>'
    ),
}

# Die Emoji, die früher an diesen Stellen standen. Alte Datenpakete führen
# sie weiterhin; so greift die Zeichnung auch ohne Neuberechnung.
IKONEN.update({
    "⚽": IKONEN["fussball"], "🤾": IKONEN["handball"], "🏀": IKONEN["basketball"],
    "🏆": IKONEN["bester"], "🔥": IKONEN["heiss"], "🧱": IKONEN["bollwerk"],
    "📈": IKONEN["aufsteiger"], "📉": IKONEN["absteiger"],
    "🥶": IKONEN["schlusslicht"], "💥": IKONEN["klatsche"],
    "🪜": IKONEN["abstand"], "⚖️": IKONEN["eng"], "⚖": IKONEN["eng"],
    "🐜": IKONEN["klein"],
})


def js_objekt() -> str:
    """Als JavaScript-Objektliteral für das Seitengerüst."""
    return json.dumps(IKONEN, ensure_ascii=False, separators=(",", ":"))


def svg(name: str, klasse: str = "ikon") -> str:
    """Fertiges <svg> -- für Stellen, die serverseitig gebaut werden."""
    pfad = IKONEN.get(name)
    if not pfad:
        return ""
    return (f'<svg class="{klasse}" viewBox="0 0 24 24" aria-hidden="true">'
            f"{pfad}</svg>")
