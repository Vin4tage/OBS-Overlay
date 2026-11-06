# OBS ShadowPlay-Style Overlay

Ein leichtgewichtiges, NVIDIA-ShadowPlay-inspiriertes Overlay für **OBS Studio unter Windows**. Das Projekt wird als Python-Skript direkt in OBS geladen und nutzt OBS für Replay Buffer und Aufnahme.

> **Unabhängiges Community-Projekt:** Dieses Projekt ist weder von NVIDIA noch vom OBS Project entwickelt, unterstützt oder offiziell mit ihnen verbunden. „NVIDIA“, „ShadowPlay“ und „OBS“ sind Marken ihrer jeweiligen Rechteinhaber. Das Overlay verwendet keine offiziellen NVIDIA- oder OBS-Logos.

## Features

- **Overlay ein-/ausblenden:** `Alt + Z` öffnet und schließt das Menü. Die Tastenkombination kann in den OBS-Hotkeys geändert werden. `Esc` schließt das geöffnete Menü.
- **Menü im ShadowPlay-Stil:** Kompakte Leiste oben mittig mit drei Aktionen: Replay Buffer, Clip speichern und Aufnahme.
- **Replay Buffer:** Buffer direkt über OBS aktivieren oder deaktivieren und den aktuellen Replay-Clip speichern.
- **Aufnahme:** OBS-Aufnahme starten und stoppen; der aktuelle Aufnahmestatus und die Laufzeit werden angezeigt.
- **Kompakte Statussymbole:** Unten rechts wird der Replay-Status als Icon angezeigt. Während einer Aufnahme erscheinen das Aufnahme-Icon und die Laufzeit.
- **Aktionsmeldungen:** Oben rechts erscheinen kurze Meldungen für ungefähr drei Sekunden, zum Beispiel „Aufnahme gestartet“ oder „Clip gespeichert“.
- **OBS-Hotkeys werden berücksichtigt:** Die Statusanzeige und Aktionsmeldungen reagieren auch, wenn Aufnahme oder Replay Buffer über OBS-Hotkeys statt über das Overlay gesteuert werden.
- **Verschiebbares Menü:** Das Hauptmenü kann verschoben werden; seine Position bleibt gespeichert.
- **Keine zusätzlichen Python-Pakete:** Das Skript verwendet Python-Standardbibliotheken und die von OBS bereitgestellte `obspython`-API. Für die Oberfläche wird Tkinter benötigt.

## Download

Öffne auf der GitHub-Projektseite den Bereich **Releases** und lade für die jeweilige Version beide Dateien herunter:

| Release-Datei | Inhalt |
|---|---|
| `OBS-Shadowplay-Overlay-vX.Y.Z.rar` | Das Overlay: Python-Einstiegsdatei, Module, Konfiguration und Dokumentation. |
| `python-3.6.8-embed-amd64.rar` | Die für dieses Paket vorbereitete 64-Bit-Python-Laufzeit inklusive Tkinter sowie Tcl/Tk. |

Die beiden Archive sind **separate Release-Dateien**. Das Python-Archiv muss zuerst entpackt werden. OBS kann keine RAR-Datei direkt als Python-Installation verwenden.

## Installation unter Windows

### 1. Beide Archive herunterladen und entpacken

1. Lade die beiden oben genannten RAR-Dateien aus demselben GitHub-Release herunter.
2. Entpacke `OBS-Shadowplay-Overlay-vX.Y.Z.rar` in einen dauerhaften Ordner, zum Beispiel:
   `C:\OBS-Shadowplay-Overlay\`
3. Entpacke `python-3.6.8-embed-amd64.rar` ebenfalls in einen dauerhaften Ordner, zum Beispiel:
   `C:\OBS-Python\python-3.6.8-embed-amd64\`
4. Verschiebe die entpackten Ordner später nicht, ohne den Python-Pfad in OBS zu aktualisieren.

### 2. Python in OBS auswählen

1. Starte OBS Studio.
2. Öffne **Werkzeuge → Skripte → Python-Einstellungen**.
3. Wähle als Python-Pfad den **entpackten Ordner**, in dem `python.exe` liegt, zum Beispiel:
   `C:\OBS-Python\python-3.6.8-embed-amd64\`
4. Wähle **nicht** die RAR-Datei und auch nicht nur `python.exe` aus – benötigt wird der Ordner.
5. Achte darauf, dass OBS und Python beide 64-Bit-Versionen sind.
6. Falls OBS einen Neustart verlangt, starte OBS neu.

Das mitgelieferte Python-Archiv ist für dieses Projekt vorbereitet und enthält unter anderem `python.exe`, `python36.dll`, `_tkinter.pyd`, den Ordner `tkinter` sowie die Tcl/Tk-Dateien. Eine normale Python-Embeddable-RAR ohne diese Tkinter-Dateien reicht nicht aus.

> **Hinweis zur Python-Version:** Das beigefügte Python 3.6.8 ist eine ältere Laufzeit und sollte nur für diese OBS-Installation verwendet werden. OBS muss diese Python-Version in den Python-Einstellungen laden können. Wenn deine OBS-Version eine andere Python-Version verlangt, benötigst du eine dazu passende 64-Bit-Python-Installation mit Tkinter.

### 3. Overlay-Skript hinzufügen

1. Öffne in OBS **Werkzeuge → Skripte**.
2. Wechsle zum Reiter **Skripte** und klicke auf **`+`**.
3. Wähle die Datei `obs_shadowplay_overlay.py` aus dem entpackten Projektordner aus, zum Beispiel:
   `C:\OBS-Shadowplay-Overlay\obs_shadowplay_overlay.py`
4. Der Ordner `shadowplay_overlay` muss direkt neben `obs_shadowplay_overlay.py` liegen. Verschiebe oder lösche ihn nicht.
5. Nach erfolgreichem Laden sollte die Skriptbeschreibung im OBS-Skriptfenster erscheinen.

### 4. Replay Buffer einschalten

Wenn du Replay-Clips speichern möchtest, aktiviere zuerst den **Replay Buffer** in den OBS-Ausgabeeinstellungen. Ohne aktivierten Replay Buffer kann das Overlay keinen Replay-Clip speichern.

## Bedienung

| Aktion | Bedienung |
|---|---|
| Overlay öffnen/schließen | `Alt + Z` |
| Overlay schließen | `Esc` |
| Menü verschieben | Titelleiste mit der Maus ziehen |
| Replay Buffer aktivieren/deaktivieren | Replay-Buffer-Kachel im Overlay |
| Replay-Clip speichern | Kachel „Clip speichern“ |
| Aufnahme starten/stoppen | Aufnahme-Kachel |

Die Hotkey-Belegung kann in **OBS → Einstellungen → Hotkeys** angepasst werden. OBS speichert die Belegung nach der ersten Einrichtung.

## Projektstruktur

```text
OBS-Shadowplay-Overlay/
├── obs_shadowplay_overlay.py   # Diese Datei in OBS hinzufügen
├── shadowplay_overlay/         # Interne Overlay- und OBS-Module
├── config/                     # Standardkonfiguration
├── docs/                       # Installation, Anforderungen und Fehlerbehebung
├── scripts/                    # Hilfs- und Entwicklungsskripte
├── tests/                      # Automatisierte Tests
├── releases/                   # Lokaler Ablageort für Release-Archive
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Fehlerbehebung

- **OBS zeigt „Python nicht konfiguriert“:** Prüfe den Ordner unter *Werkzeuge → Skripte → Python-Einstellungen*. Er muss der entpackte Ordner mit `python.exe` sein.
- **Tkinter-Fehler:** Prüfe, ob `_tkinter.pyd`, `tkinter/`, `tcl/`, `tcl86t.dll` und `tk86t.dll` im Python-Ordner vorhanden sind. Verwende das für dieses Projekt bereitgestellte Runtime-Archiv.
- **Replay Buffer nicht verfügbar:** Aktiviere den Replay Buffer in den OBS-Ausgabeeinstellungen.
- **`Alt + Z` reagiert nicht:** Prüfe die Belegung unter *OBS → Einstellungen → Hotkeys*. Eine andere Anwendung kann dieselbe Kombination verwenden.
- **Overlay erscheint nicht über einem Spiel:** Bei exklusivem Vollbild kann Windows zusätzliche Fenster unter Umständen nicht über dem Spiel darstellen. Verwende nach Möglichkeit randloses Fenster oder Fenstermodus.
- **Weitere Informationen:** Siehe [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) und das OBS-Skript-Protokoll unter *Werkzeuge → Skripte → Skript-Protokoll*.

## Entwicklung und Tests

Das Projekt enthält Tests für die Zustandslogik und eine simulierte OBS-Umgebung:

```powershell
python tests/test_logic.py
```

Der Tk-Oberflächentest benötigt unter Linux eine grafische Testumgebung (Xvfb). Die automatisierten Tests ersetzen keinen Funktionstest mit der eigenen OBS-Installation unter Windows. Teste insbesondere Replay Buffer und Aufnahme zunächst mit kurzen Aufnahmen.

## Version und Änderungsverlauf

Aktuelle Projektversion: **1.0.3**. Details zu Änderungen stehen in [`CHANGELOG.md`](CHANGELOG.md).

## Lizenz

MIT – siehe [`LICENSE`](LICENSE).
