"""Vereinswappen mitliefern statt verlinken.

Die Wappen kommen aus OpenLigaDB und liegen auf fremden Servern -- Wikimedia,
imgur, kicker und ein halbes Dutzend weitere. Ein `<img src>` dorthin überträgt
bei jedem Seitenaufruf die IP-Adresse des Besuchers an diesen Dritten, ohne
dessen Wissen und ohne Einwilligung. Das ist derselbe Vorgang, für den das
Landgericht München I im Januar 2022 wegen einer eingebundenen Google-Schriftart
Schadenersatz zusprach (Az. 3 O 17493/20).

Deshalb wird jedes Wappen einmal geholt und danach aus `docs/wappen/`
ausgeliefert. Der Dateiname ist der SHA1 der Quelladresse: dieselbe Quelle
ergibt dieselbe Datei, ein zweiter Lauf lädt also nichts doppelt, und die
Dateien überleben einen Neubau der Daten.

Was sich nicht laden lässt, verliert sein Wappen. Die fremde Adresse
stehenzulassen wäre das Gegenteil dessen, worum es hier geht.

Nachträglich über die bereits gebauten Daten laufen:

    python3 -m ranking.wappen           # docs/ neben diesem Paket
    python3 -m ranking.wappen <ordner>
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ORDNER = "wappen"                 # unterhalb von docs/
MAX_BYTES = 512 * 1024            # ein Wappen, das größer ist, ist keins
UA = "ClubRank/1.0 (+https://clubrank.github.io/)"

# Die Seite zeigt Wappen mit 20 Pixeln Kantenlänge. Manche Quellen liefern
# 2275 × 2065 -- ein Drittel Megabyte für ein Icon. Rasterbilder werden
# deshalb auf diese Kantenlänge gebracht (mit Reserve für hohe Auflösungen),
# SVGs bleiben, wie sie sind: sie skalieren von selbst und sind klein.
KANTE = 96
RASTER = {".png", ".jpg", ".gif", ".webp"}

# Endung nach Inhaltstyp. Die Quelladresse taugt dafür nicht immer: manche
# Server liefern PNG unter einer Adresse ohne Endung aus.
ENDUNGEN = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif",
    "image/svg+xml": ".svg", "image/webp": ".webp", "image/x-icon": ".ico",
}


def _name(url: str, endung: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:16] + endung


def _vorhanden(ziel: Path, url: str) -> str | None:
    """Bereits geholt? Dann den Pfad zurückgeben, ohne erneut zu laden."""
    stamm = hashlib.sha1(url.encode()).hexdigest()[:16]
    for datei in ziel.glob(f"{stamm}.*"):
        return f"{ORDNER}/{datei.name}"
    return None


def _kodiert(url: str) -> str:
    """Umlaute und Gedankenstriche im Pfad prozentkodieren.

    OpenLigaDB führt Adressen wie ".../1._FC_Nürnberg_logo.svg" ungeschützt.
    urllib schickt solche Zeichen unverändert los, und der Server antwortet
    nicht. `safe` enthält das Prozentzeichen, damit bereits kodierte Folgen
    wie %E2%80%93 nicht ein zweites Mal kodiert werden.
    """
    teile = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((
        teile.scheme, teile.netloc,
        urllib.parse.quote(teile.path, safe="/%:@&=+$,~!*'()"),
        urllib.parse.quote(teile.query, safe="/%:@&=+$,~!*'()?"),
        teile.fragment))


def _laden(url: str, ziel: Path) -> str | None:
    if not url.lower().startswith(("http://", "https://")):
        return None
    req = urllib.request.Request(_kodiert(url), headers={"User-Agent": UA})
    daten = typ = None
    # Wikimedia drosselt, wenn viele Bilder kurz hintereinander abgerufen
    # werden, und antwortet dann mit 429. Einmal abwarten und erneut fragen
    # reicht; ohne das gehen ausgerechnet die bekanntesten Wappen verloren.
    for versuch in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                typ = (resp.headers.get("Content-Type") or "").split(";")[0]
                typ = typ.strip().lower()
                daten = resp.read(MAX_BYTES + 1)
            break
        except urllib.error.HTTPError as fehler:
            if fehler.code not in (429, 500, 502, 503) or versuch == 2:
                return None
            wartezeit = fehler.headers.get("Retry-After")
            time.sleep(float(wartezeit) if (wartezeit or "").isdigit()
                       else 2.0 * (versuch + 1))
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            return None
    if daten is None or not typ.startswith("image/"):
        return None
    if not daten or len(daten) > MAX_BYTES:
        return None
    endung = ENDUNGEN.get(typ)
    if endung is None:
        vermutet = Path(urllib.parse.urlparse(url).path).suffix.lower()
        endung = vermutet if vermutet in ENDUNGEN.values() else ".img"
    datei = ziel / _name(url, endung)
    datei.write_bytes(daten)
    _verkleinern(datei)
    return f"{ORDNER}/{datei.name}"


def _verkleinern(datei: Path) -> None:
    """Rasterbilder auf Icon-Größe bringen. Fehlt `sips`, bleibt alles wie es ist."""
    if datei.suffix.lower() not in RASTER:
        return
    try:
        masse = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight",
                                str(datei)], capture_output=True, text=True,
                               timeout=30).stdout
        kante = max(int(z.split(":")[-1]) for z in masse.splitlines()
                    if "pixel" in z)
    except (ValueError, OSError, subprocess.SubprocessError):
        return
    if kante <= KANTE:
        return
    subprocess.run(["sips", "--resampleHeightWidthMax", str(KANTE), str(datei),
                    "--out", str(datei)], capture_output=True, timeout=60)


def holen(urls, docs: Path, verbose: bool = True) -> dict[str, str | None]:
    """Adresse -> lokaler Pfad. None, wo das Wappen nicht zu holen war."""
    ziel = Path(docs) / ORDNER
    ziel.mkdir(parents=True, exist_ok=True)
    karte: dict[str, str | None] = {}
    neu = fehler = 0
    for url in sorted({u for u in urls if u}):
        schon = _vorhanden(ziel, url)
        if schon:
            karte[url] = schon
            continue
        pfad = _laden(url, ziel)
        karte[url] = pfad
        if pfad:
            neu += 1
        else:
            fehler += 1
        # Nach jedem Abruf pausieren, auch nach einem gescheiterten. Sonst
        # feuert gerade eine Reihe von Fehlschlägen ungebremst weiter und
        # provoziert genau die Drosselung, die sie ausgelöst hat.
        time.sleep(0.25)
    if verbose and (neu or fehler):
        print(f"  Wappen: {neu} neu geholt, {len(karte) - neu - fehler} schon da"
              + (f", {fehler} nicht erreichbar" if fehler else ""), file=sys.stderr)
    return karte


def _adressen(paket: dict) -> list[str]:
    urls = [r[3] for r in paket.get("rows") or [] if len(r) > 3 and r[3]]
    for paarung in (paket.get("pokal") or {}).get("paarungen") or []:
        urls += [paarung.get("heimWappen"), paarung.get("gastWappen")]
    return [u for u in urls if u and u.startswith("http")]


def _ersetzen(paket: dict, karte: dict[str, str | None]) -> int:
    """Setzt die lokalen Pfade ein. Gibt zurück, wie viele ersetzt wurden."""
    ersetzt = 0
    for r in paket.get("rows") or []:
        if len(r) > 3 and r[3] and r[3].startswith("http"):
            r[3] = karte.get(r[3])
            ersetzt += 1
    for paarung in (paket.get("pokal") or {}).get("paarungen") or []:
        for feld in ("heimWappen", "gastWappen"):
            wert = paarung.get(feld)
            if wert and wert.startswith("http"):
                paarung[feld] = karte.get(wert)
                ersetzt += 1
    return ersetzt


def einbetten(paket: dict, docs: Path, verbose: bool = True) -> dict:
    """Beim Bauen: Wappen holen und die Adressen im Paket ersetzen."""
    adressen = _adressen(paket)
    if adressen:
        _ersetzen(paket, holen(adressen, docs, verbose))
    return paket


def nachtragen(docs: Path, verbose: bool = True) -> int:
    """Nachträglich über die fertigen Dateien in docs/data/ laufen."""
    docs = Path(docs)
    dateien = [p for p in sorted((docs / "data").glob("*.json"))
               if not p.name.endswith(".info.json")]
    alle: list[str] = []
    pakete: dict[Path, dict] = {}
    for p in dateien:
        paket = json.loads(p.read_text(encoding="utf-8"))
        pakete[p] = paket
        alle += _adressen(paket)
    if not alle:
        print("Keine fremden Wappenadressen gefunden.", file=sys.stderr)
        return 0
    print(f"{len(alle)} Verweise auf {len({urllib.parse.urlparse(u).netloc for u in alle})} "
          f"fremde Server, {len(set(alle))} verschiedene Bilder.", file=sys.stderr)
    karte = holen(alle, docs, verbose)
    gesamt = 0
    for p, paket in pakete.items():
        n = _ersetzen(paket, karte)
        if not n:
            continue
        p.write_text(json.dumps(paket, ensure_ascii=False, separators=(",", ":")),
                     encoding="utf-8")
        gesamt += n
        print(f"  {p.name}: {n} Adressen ersetzt", file=sys.stderr)
    verloren = [u for u, p in karte.items() if p is None]
    if verloren:
        print(f"  {len(verloren)} Wappen waren nicht erreichbar und entfallen:",
              file=sys.stderr)
        for u in verloren[:5]:
            print(f"    {u}", file=sys.stderr)
    return gesamt


if __name__ == "__main__":
    ordner = Path(sys.argv[1]) if len(sys.argv) > 1 \
        else Path(__file__).resolve().parent.parent / "docs"
    raise SystemExit(0 if nachtragen(ordner) else 1)
