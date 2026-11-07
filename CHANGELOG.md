# Changelog

## 1.0.0 – 2026-11-06
- Erste Version / First release.
- Overlay (Tkinter) mit Replay Buffer (aktivieren, deaktivieren, speichern) und Aufnahme (starten, stoppen, Zeit).
- Dauerhafte Statussymbole unten rechts (Replay Buffer oben, Aufnahme darunter), gesteuert durch OBS-Ereignisse.
- Hotkey Alt+Z über die OBS-Hotkey-API (änderbar in OBS), Esc schließt das Overlay.
- Sauberes Beenden bei OBS-Exit / Skript-Entladen.
- `TCL_LIBRARY`/`TK_LIBRARY` werden für eingebettetes Python automatisch gesetzt; Code ist Python-3.6-kompatibel.
- Hilfsskripte: `scripts/check_environment.py`, `scripts/install_python.ps1`, `scripts/package_release.py`.
- Automatisierte Tests mit simuliertem OBS (`tests/`). **Nicht** mit echtem OBS unter Windows getestet – siehe README.


## 1.0.1 – 2026-11-06
- OBS-Frontend-Aktionen werden nicht mehr direkt aus dem OBS-Skript-Timer ausgeführt.
- Neuer Befehls-Worker für Replay-Buffer- und Aufnahme-Aktionen; Status/Ereignisse bleiben beim OBS-Skript.
- Worker wird beim Entladen/Beenden von OBS kontrolliert gestoppt; nicht ausgeführte Befehle werden verworfen.
- Zusätzlicher Test, der prüft, dass OBS-Aktionsfunktionen tatsächlich im separaten Worker aufgerufen werden.


## 1.0.2 – 2026-11-06
- Fehlerhafte Hover-Implementierung der drei Canvas-Buttons behoben: Canvas-Elemente werden nicht mehr bei jedem Enter/Leave gelöscht und neu erstellt.
- Hover- und Klickereignisse werden zentral am Canvas verarbeitet; die Buttons behalten stabile Element-IDs.
- OBS-`SCRIPTING_SHUTDOWN` wird zusätzlich zu `EXIT` behandelt, damit Tk- und Befehls-Threads vor dem Herunterfahren des Python-Subsystems beendet werden.
- Tk-Rauchtest löst Button-Klicks jetzt über Canvas-Mausereignisse statt durch direkten Aufruf der Callback-Funktion aus.
- Zusätzlicher Test stellt sicher, dass Hover-/Statusänderungen keine neuen Canvas-Elemente erzeugen.
- Erweiterten Tk-Rauchtest ergänzt: XTest-Mausbewegungen und echte X11-Mausklicks über alle drei Buttons sowie den Close-Button; Replay ein/aus, Clip speichern und Aufnahme starten/stoppen werden geprüft.
- Unter Xvfb erfolgreich: alle fünf OBS-Aktionsaufrufe ausgelöst, Close-Button reagiert, kein Hängen der Tk-Ereignisschleife und keine zurückbleibenden Threads. Echtes OBS unter Windows bleibt separat zu testen.


## 1.0.3 – 2026-11-06
- Hauptmenü in eine kompakte Leiste mit drei horizontalen Kacheln (Replay Buffer, Clip speichern, Aufnahme) umgebaut und standardmäßig oben mittig positioniert.
- Gespeicherte Overlay-Positionen aus älteren Versionen werden einmalig migriert; danach bleiben bewusst manuell verschobene Positionen erhalten.
- Dauerhafte Statusanzeige unten rechts stark verkleinert: Replay Buffer nur als Icon, Aufnahme als Icon plus Laufzeit; beide Anzeigen nebeneinander und mit kleinem Bildschirmrand-Abstand.
- Neue, klickdurchlässige Aktionsmeldungen oben rechts, die drei Sekunden angezeigt werden. Sie reagieren auf OBS-Ereignisse für Aufnahme/Replay (auch wenn die Aktionen über OBS-Hotkeys ausgelöst wurden), einschließlich Pause/Fortsetzen und Clip gespeichert.
- Zusätzliche Übersetzungen und Tests für neue Layout-, Status- und Toast-Ereignisse.


## 1.0.4 – 2026-11-07
- Design-Überarbeitung bei unveränderter Logik und (fast) unveränderten Positionen.
- Grüner Akzent durch weiße/neutrale Töne ersetzt: weiße Primär-Buttons, neutrale Graustufen, Rot (Aufnahme) und Gelb (Pause/Warnung) bleiben als Signalfarben.
- Mehr Transparenz: Hauptmenü 88 %, Statusanzeigen 86 %, Meldungen 90 % Deckkraft (`config/user_config.json`: `overlay.opacity`, `status.opacity`, `toast.opacity`; 1.0 = undurchsichtig).
- Aktive Kacheln werden sichtbar hervorgehoben (heller Rand/Icon bei Replay Buffer aktiv, roter Rand bei Aufnahme, gelber bei Pause); inaktive sind gedämpft.
- Statusanzeigen unten rechts verkleinert (Höhe 36 → 24 px, Replay-Icon 26 px, Aufnahme 78 px) und näher an die Ecke (Rand 12 → 6 px, Abstand 6 → 4 px).
- Kleinere, feinere Aktionsmeldung (336×48), feine Trennlinie unter dem Titel, Segoe UI Semibold für Überschriften/Buttons.
- Neue Hilfsfunktion `gfx.recolor`; Icons werden nur bei Zustandsänderung umgefärbt (keine neuen Canvas-Elemente bei Hover).
- Tests (18 Unit-Tests, Tk-Rauchtest mit echten X11-Mausereignissen) laufen weiterhin durch. Die Transparenz selbst ist unter Linux/Xvfb nicht sichtbar prüfbar (kein Compositor) und muss unter Windows angesehen werden.
