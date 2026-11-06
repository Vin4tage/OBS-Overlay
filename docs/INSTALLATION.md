# Installation (Deutsch)

## 1. Voraussetzungen
Windows 10/11 64-bit, OBS Studio 30+ (64-bit). Details: [REQUIREMENTS.md](REQUIREMENTS.md).

## 2. Python mit Tkinter bereitstellen
**Variante A – eigene Python-Kopie nur für OBS (empfohlen für Anfänger)**
1. Ordner `OBS-Shadowplay-Overlay` entpacken, z. B. nach `C:\Users\<Name>\Documents\OBS-Shadowplay-Overlay`.
2. Rechtsklick auf `scripts\install_python.ps1` → „Mit PowerShell ausführen“. (Lädt den offiziellen Python-Installer von python.org und installiert ihn still nach `runtime\python`, mit Tcl/Tk.)
3. Das Skript nennt am Ende den Pfad, den Sie in OBS eintragen (Schritt 3).

**Variante B – vorhandenes Python nutzen**
Installieren Sie Python 3.12 (64-bit) von python.org. Im Installer „Customize“ → **tcl/tk and IDLE** angekreuzt lassen.

**Variante C – eingebettetes Python mit Tkinter (z. B. `python-3.6.8-embed-amd64`)**
Ordner entpacken (z. B. nach `runtime\python`) – der Ordner muss `python36.dll`, `_tkinter.pyd`, `tkinter\` und `tcl\` enthalten. In OBS diesen Ordner eintragen (Schritt 3). OBS ab Version 28 nötig bzw. empfohlen.

**Prüfen:** `<Python-Ordner>\python.exe scripts\check_environment.py` – alles muss „OK“ zeigen.

## 3. Python in OBS eintragen
OBS → *Werkzeuge → Skripte → Reiter „Python-Einstellungen“* → Ordner der Python-Installation wählen
(der Ordner, in dem `python.exe` liegt, z. B. `…\runtime\python`). OBS ggf. neu starten.

## 4. Skript hinzufügen
*Werkzeuge → Skripte → Reiter „Skripte“ → „+“* → **`obs_shadowplay_overlay.py`** aus dem Projektordner wählen
(nur diese Datei; der Ordner `shadowplay_overlay` muss daneben liegen bleiben). Im Skriptfenster sollte die Beschreibung erscheinen.

## 5. Automatischer Start
OBS merkt sich die Skriptliste und lädt das Skript bei jedem Start selbst. Es ist nichts weiter nötig.
Beim Beenden von OBS werden Overlay, Statussymbole und Hotkey entfernt.

## 6. Benutzung
- **Alt + Z**: Overlay öffnen/schließen (änderbar: OBS *Einstellungen → Hotkeys → „ShadowPlay Overlay“*).
- **Esc**: schließt das Overlay. · Titelzeile ziehen = verschieben (Position wird gespeichert).
- Replay Buffer vorher in *Einstellungen → Ausgabe → Aufnahme* aktivieren.
- Das Menü öffnet sich oben mittig mit drei Kacheln: Replay Buffer, Clip speichern und Aufnahme.
- Unten rechts bleiben kompakte Statussymbole: Replay Buffer nur als Icon, Aufnahme als Icon mit Laufzeit.
- Aktionen wie „Aufnahme gestartet“ erscheinen oben rechts für drei Sekunden – auch wenn du dafür einen OBS-Hotkey verwendest.
- Hinweis: Über Spielen im *exklusiven* Vollbild kann Windows keine Fenster darüber zeigen; im Fenster-/randlosen Modus funktioniert es.

Fehler? → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

# Installation (English)

## 1. Requirements
Windows 10/11 64-bit, OBS Studio 30+ (64-bit). See [REQUIREMENTS.md](REQUIREMENTS.md).

## 2. Provide Python with Tkinter
**Option A – dedicated Python copy for OBS (recommended for beginners)**
1. Extract the project, e.g. to `C:\Users\<name>\Documents\OBS-Shadowplay-Overlay`.
2. Right-click `scripts\install_python.ps1` → "Run with PowerShell". It downloads the official installer from python.org and installs it silently into `runtime\python`, including Tcl/Tk.
3. It prints the path to enter in OBS (step 3).

**Option B – use an existing Python**
Install Python 3.12 (64-bit) from python.org; keep **tcl/tk and IDLE** ticked under "Customize".

**Option C – embedded Python with Tkinter added (e.g. `python-3.6.8-embed-amd64`)**
Extract it (e.g. to `runtime\python`); the folder must contain `python36.dll`, `_tkinter.pyd`, `tkinter\` and `tcl\`. Enter that folder in OBS (step 3). Use OBS 28 or newer.

**Verify:** `<python folder>\python.exe scripts\check_environment.py` – everything should say OK.

## 3. Tell OBS where Python is
OBS → *Tools → Scripts → "Python Settings" tab* → select the folder containing `python.exe` (e.g. `…\runtime\python`). Restart OBS if asked.

## 4. Add the script
*Tools → Scripts → "Scripts" tab → "+"* → choose **`obs_shadowplay_overlay.py`** (only this file; keep the `shadowplay_overlay` folder next to it).

## 5. Auto-start
OBS remembers its script list and loads the script on every start. Everything is closed again when OBS exits.

## 6. Usage
- **Alt + Z** toggles the overlay (rebind in OBS *Settings → Hotkeys → "ShadowPlay Overlay"*). **Esc** closes it. Drag the title bar to move it.
- Enable the Replay Buffer first in *Settings → Output → Recording*.
- Status icons appear bottom-right automatically: Replay Buffer (top), Recording (bottom).
- Windows cannot draw windows above *exclusive* fullscreen games; windowed and borderless modes work.
