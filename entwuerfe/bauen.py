"""Erzeugt entwuerfe/ikonen.js aus ranking/ikonen.py.

Die Entwürfe sollen dieselben Strichzeichnungen zeigen wie die Seite selbst --
ohne sie ein zweites Mal zu pflegen.

    python3 entwuerfe/bauen.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ranking import ikonen  # noqa: E402

ziel = Path(__file__).resolve().parent / "ikonen.js"
ziel.write_text("window.IKONEN = " + ikonen.js_objekt() + ";\n", encoding="utf-8")
print(f"{ziel.name}: {len(ikonen.IKONEN)} Einträge")
