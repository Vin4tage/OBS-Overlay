# Fehlerbehebung / Troubleshooting

Das Protokoll findet man in OBS unter *Werkzeuge → Skripte → „Skript-Protokoll“* (Zeilen mit `[ShadowPlay Overlay]`).
Logs: OBS *Tools → Scripts → "Script Log"* (lines starting with `[ShadowPlay Overlay]`).

| Problem / Problem | Ursache / Cause | Lösung / Fix |
|---|---|---|
| Skript lässt sich nicht hinzufügen, „Python nicht konfiguriert“ | Kein Python-Pfad in OBS | Installation Schritt 3. Pfad = Ordner mit `python.exe`. |
| „Tkinter ist nicht verfügbar“ | Python ohne Tcl/Tk (z. B. *embeddable zip*) | Vollständigen python.org-Installer verwenden, „tcl/tk and IDLE“ aktiv; oder `scripts\install_python.ps1`. |
| Pythonversion/Architektur passt nicht | OBS und Python müssen zusammenpassen (64-bit; Version laut OBS-Protokoll) | Passende Version installieren; `scripts\check_environment.py` ausführen. |
| Alt+Z tut nichts | Tastenkombination von anderem Programm belegt, oder in OBS *Einstellungen → Erweitert → Hotkey-Fokusverhalten* deaktiviert Hotkeys | Belegung in OBS *Einstellungen → Hotkeys → „ShadowPlay Overlay“* ändern; Fokusverhalten auf „Hotkeys nie deaktivieren“. Notfalls Button *Overlay öffnen/schließen* im Skriptfenster. |
| Overlay erscheint nicht über dem Spiel | Spiel im exklusiven Vollbild | Randlosen Fenstermodus nutzen. |
| „Nicht verfügbar“ beim Replay Buffer | Replay Buffer in OBS nicht aktiviert | *Einstellungen → Ausgabe → Aufnahme* (Einfach) bzw. *Replay Buffer* (Erweitert) aktivieren; OBS ggf. neu starten. |
| Aufnahmezeit zählt erst ab Skriptstart | Skript wurde geladen, während schon eine Aufnahme lief | Erwartetes Verhalten: OBS liefert keine Startzeit per API; Zeit läuft ab dem Moment, in dem das Skript die Aufnahme bemerkt. |
| Overlay-Thread läuft nicht mehr | Interner Fehler der Tk-Oberfläche | Skript neu laden (Skriptliste → Aktualisieren-Symbol) und Fehlermeldung im Protokoll melden. |
| OBS reagiert beim Bewegen des Mauszeigers über einen Button oder nach einem Klick nicht mehr | Eine ältere Version hat Canvas-Elemente beim Hover gelöscht und neu erstellt; das konnte eine Enter/Leave-Ereignisschleife auslösen. | Version 1.0.3 verwenden. Die Buttons behalten stabile Canvas-Elemente und verarbeiten Mausereignisse zentral. Falls OBS weiterhin hängt, bitte OBS-Skript-Protokoll und OBS-Version mitteilen. |
| Statussymbole verdecken Taskleiste/Elemente | Abstand unpassend | `config\user_config.json` anlegen, z. B. `{"status": {"margin_right": 40, "margin_bottom": 60}}`. |

Die Sprache kann mit `{"language": "de"}` oder `"en"` in `config\user_config.json` erzwungen werden (Standard: automatisch).
