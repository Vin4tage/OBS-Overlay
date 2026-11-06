# OBS ShadowPlay-Style Overlay

**DE** · Ein Overlay im Stil von NVIDIA ShadowPlay – als reines **OBS-Python-Skript** (Tkinter, keine eigene Anwendung, keine Plugins, keine Injection in Spiele).
**EN** · A NVIDIA-ShadowPlay-style overlay delivered purely as an **OBS Python script** (Tkinter, no standalone app, no plugins, no game injection).

> **Unabhängiges Community-Projekt. / Independent community project.**
> Keine offizielle NVIDIA- oder OBS-Software und nicht mit NVIDIA oder dem OBS Project verbunden. „NVIDIA“ und „ShadowPlay“ sind Marken der NVIDIA Corporation; „OBS“ gehört dem OBS Project. Es werden keine Logos oder Assets dieser Firmen verwendet.
> Not affiliated with or endorsed by NVIDIA or the OBS Project. All trademarks belong to their owners.

## Funktionen / Features
- **Alt + Z** öffnet/schließt das Overlay, **Esc** schließt es (OBS-Hotkey-API; Belegung in OBS änderbar). Das kompakte Menü startet oben mittig, ist frei verschiebbar und bleibt im Vordergrund.
- **Replay Buffer:** aktivieren, deaktivieren, speichern (`obs_frontend_replay_buffer_save` – startet keine Aufnahme), Statusanzeige.
- **Aufnahme:** starten, stoppen, Status und Aufnahmezeit (inkl. Pause).
- **Kompakte Statussymbole unten rechts**, auch bei geschlossenem Overlay: Replay Buffer nur als Icon, Aufnahme als Aufnahme-Icon plus Laufzeit; klickdurchlässig.
- **Aktions-Popups oben rechts** für drei Sekunden, z. B. „Aufnahme gestartet“, „Replay Buffer deaktiviert“ oder „Clip gespeichert“. Sie erscheinen auch bei Aktionen über OBS-Hotkeys.
- Zustand kommt aus **OBS-Ereignissen** (nicht aus Button-Klicks); ein günstiger Abgleich einmal pro Sekunde fängt verpasste Ereignisse ab.
- Entprellung gegen Mehrfachklicks, keine doppelten Fenster/Hotkeys, sauberes Beenden bei OBS-Exit.
- OBS-Frontend-Aktionen werden über einen eigenen Befehls-Worker ausgelöst; der OBS-Timer verarbeitet nur Statusabgleich und Logs.
- Nur Python-Standardbibliothek (`tkinter`, `ctypes`) – keine Zusatzpakete. Deutsch/Englisch.

## Schnellstart / Quick start
1. Python **mit Tkinter** bereitstellen: `scripts\install_python.ps1` (oder eigenes Python 3.12 64-bit, „tcl/tk“ aktiv).
2. OBS → *Werkzeuge/Tools → Skripte/Scripts → Python-Einstellungen*: Python-Ordner eintragen.
3. *Skripte → „+“* → **`obs_shadowplay_overlay.py`** wählen. Fertig – startet ab jetzt mit OBS.

Ausführlich (Deutsch + English): [docs/INSTALLATION.md](docs/INSTALLATION.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Requirements](docs/REQUIREMENTS.md)

**Wichtig / Important:** OBS liefert unter Windows kein Python mit, und das „embeddable“ Python enthält kein Tkinter. Eine externe, vollständige Python-Installation ist daher zwingend (kein Zusatzpaket nötig).

## Projektstruktur / Layout
```
obs_shadowplay_overlay.py      <- OBS-Einstiegsdatei (nur diese in OBS hinzufügen)
shadowplay_overlay/            <- Module: core, obs_controller, overlay, status_indicators, hotkeys, config, gfx, utils
config/default_config.json     <- Standardwerte (Überschreiben: config/user_config.json)
docs/  scripts/  runtime/  releases/  tests/
```
Abweichung von der Vorgabe: Die Module liegen in einem Paket `shadowplay_overlay/` neben der Einstiegsdatei (statt `src/main.py`), damit Modulnamen wie `config`/`utils` nicht mit anderen OBS-Skripten kollidieren. Es gibt keine `assets/`-Ordner: Icons werden als Vektorgrafik gezeichnet, es sind keine Schriften/Bilder nötig (verwendet wird die Windows-Systemschrift „Segoe UI“).

## Teststatus – ehrlich / Honest test status
| Geprüft / Verified | Wie |
|---|---|
| Zustandslogik, Befehle, Entprellung, Worker-Dispatch, Fehlerfälle, Hotkey-Standardbelegung (Alt+Z), Übersetzungen und OBS-Aktionsmeldungen | `python tests/test_logic.py` (**simuliertes** `obspython`) |
| Tk-Oberfläche, oberes Drei-Kachel-Menü, kompakte Statussymbole unten rechts, 3-Sekunden-Aktionsmeldungen, alle Button-Aktionen und Beenden ohne übrig gebliebene Threads | `tests/smoke_tk.py` unter Linux/Xvfb mit **simuliertem** OBS |
| Hover + Klick | Soweit `libXtst` verfügbar ist: X11/XTest sendet echte X-Server-Mausbewegungen und Klicks über alle Buttons; andernfalls Tk-Ereignis-Fallback. Kein echter Windows-Mauszeiger/OBS-Test. |
| **NICHT getestet** | Echtes OBS unter Windows; echter Replay-Speichervorgang und echte Aufnahme; Windows-Transparenz/Click-Through (`ctypes`); Fokus/Esc-Polling; Anzeige über Spielen; `install_python.ps1`; RAR-Erstellung. Der Code folgt der dokumentierten OBS-API, ist aber auf einem echten System noch zu verifizieren. |

Bitte Fehler als GitHub-Issue melden (OBS-Version, Python-Version, Auszug aus dem Skript-Protokoll).

## Bekannte Grenzen / Known limitations
- Nur Windows. Kein Overlay über *exklusivem* Vollbild (Windows-Einschränkung; randlos/Fenster geht).
- Hotkey Alt+Z wird nur beim ersten Laden vorbelegt; danach gilt, was in OBS gespeichert ist. OBS-Einstellung „Hotkey-Fokusverhalten“ kann Hotkeys deaktivieren.
- Esc wird nur **solange das Overlay offen ist** per Tastenabfrage (Polling) erkannt, kein globaler Hook.
- Die Aufnahmezeit läuft ab dem Moment, in dem das Skript die Aufnahme bemerkt (OBS liefert keine Startzeit).
- Replay Buffer muss in den OBS-Ausgabeeinstellungen aktiviert sein.

## Entwicklung / Development
`python tests/test_logic.py` · `SHADOWPLAY_ALLOW_NON_WINDOWS=1 xvfb-run -a python tests/smoke_tk.py` (Linux) · `python scripts/package_release.py`

Lizenz / License: MIT – siehe [LICENSE](LICENSE). Version 1.0.3.
