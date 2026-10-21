#!/usr/bin/env python3
"""Prüfsumme für ein Zugangswort erzeugen.

    python3 zugangswort.py "Entwurf1026#-DFB" DFB

Die Ausgabe wird in ranking/site.py unter ZUGANGSWOERTER eingetragen. Das
Wort selbst gehört nicht ins Repository -- es ist öffentlich.
"""
import hashlib
import sys

if len(sys.argv) < 2:
    raise SystemExit(__doc__)
wort = sys.argv[1]
name = sys.argv[2] if len(sys.argv) > 2 else "Empfänger"
print(f'    "{hashlib.sha256(wort.encode()).hexdigest()}": "{name}",')
