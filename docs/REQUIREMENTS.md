# Requirements / Voraussetzungen

| | |
|---|---|
| Betriebssystem / OS | Windows 10 / 11 (64-bit). Das Overlay nutzt Windows-Funktionen (Transparenz, Click-Through). |
| OBS Studio | 30 oder neuer, 64-bit. Verwendet werden nur die Frontend-API-Funktionen für Aufnahme/Replay Buffer und Ereignisse. |
| Python | **Vollständige** 64-bit-Installation, deren Version zur OBS-Version passt. Empfohlen: **3.12** (von OBS-Entwicklern/Community für OBS 31/32 genannt). Maßgeblich ist, was OBS in *Python-Einstellungen* bzw. im Protokoll verlangt. |
| Tkinter / Tcl/Tk | Muss in dieser Python-Installation enthalten sein (Standard bei python.org-Installer mit „tcl/tk and IDLE“). |
| Zusatzpakete | Keine. Nur Standardbibliothek + `obspython`. |
| OBS-Einstellung | Replay Buffer muss in *Einstellungen → Ausgabe → Aufnahme/Replay Buffer* **aktiviert** sein, sonst meldet das Overlay „Nicht verfügbar“. |

## Eingebettetes Python mit nachgerüstetem Tkinter (z. B. `python-3.6.8-embed-amd64`)
Funktioniert **nur**, wenn das Paket `_tkinter.pyd`, `tcl86t.dll`, `tk86t.dll`, den Ordner `tkinter/` und `tcl/tcl8.6` + `tcl/tk8.6` enthält
(`scripts/check_environment.py` prüft das mit genau diesem Python). OBS ab 28 akzeptiert laut OBS-Forum Python ab 3.6; ältere OBS-Versionen **nur** 3.6.
Das Skript setzt `TCL_LIBRARY`/`TK_LIBRARY` bei Bedarf selbst. Nicht auf echtem OBS verifiziert.

## Warum reicht das *offizielle* eingebettete Python nicht?
- OBS liefert unter Windows **kein** Python mit. Man muss eine externe Installation angeben (OBS-Dokumentation: „Scripting“).
- Das „embeddable package“ von python.org enthält **kein Tkinter** → ungeeignet.
- Ein skriptseitiges „Automatisch Python finden“ ist nicht möglich: OBS muss Python *vor* dem Laden des Skripts kennen.
  Daher: `scripts/check_environment.py` (Prüfung) und `scripts/install_python.ps1` (optionale Installationshilfe).
