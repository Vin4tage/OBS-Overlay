"""Zentrale Logik: verbindet OBS-Callbacks, Controller, Hotkey und Overlay-Thread."""
import os
import time

from . import __version__, config, utils
from .hotkeys import HotkeyManager
from .obs_controller import ObsController

DESCRIPTION = (
    "<h2>ShadowPlay-Style Overlay %s</h2>"
    "<p>Alt+Z öffnet/schließt das Overlay · Esc schließt es.<br>"
    "Alt+Z can be changed in Settings → Hotkeys (\"ShadowPlay Overlay\").</p>"
    "<p><i>Unabhängiges Community-Projekt – keine offizielle NVIDIA- oder OBS-Software.<br>"
    "Independent community project – not affiliated with NVIDIA or OBS.</i></p>"
) % __version__


class Plugin:
    def __init__(self, obs, root_dir):
        self.obs = obs
        self.root_dir = root_dir
        self.log = utils.Logger(obs)
        self.loaded = False
        self.controller = None
        self.app = None
        self.hotkeys = HotkeyManager(obs, self.log)
        self._timer_cb = None
        self._loaded_at = 0.0
        self._warned_dead = False
        self._ready_fallback = 6.0

    # ------------------------------------------------------------------ Laden
    def load(self, settings, event_cb, timer_cb, hotkey_cb):
        if self.loaded:
            self.log.warning("Skript ist bereits geladen - doppelter Start verhindert.")
            self.log.flush()
            return
        self.loaded = True
        self._loaded_at = time.monotonic()
        cfg = config.load(self.root_dir, self.log)
        self._ready_fallback = float(cfg["timing"]["ready_fallback_s"])
        tr = config.Translator(cfg["language"])
        self.controller = ObsController(self.obs, cfg, self.log, on_exit=self.shutdown)
        self.controller.start_worker()
        self.hotkeys.register(settings, hotkey_cb)
        self.obs.obs_frontend_add_event_callback(event_cb)
        self._event_cb = event_cb
        self._timer_cb = timer_cb
        self.obs.timer_add(timer_cb, int(cfg["timing"]["obs_pump_ms"]))
        self._start_ui(cfg, tr, settings)
        self.log.info("Version %s geladen." % __version__)
        self.log.flush()

    def _start_ui(self, cfg, tr, settings):
        import os as _os
        if not utils.IS_WINDOWS and not _os.environ.get("SHADOWPLAY_ALLOW_NON_WINDOWS"):
            self.log.error("Dieses Overlay unterstützt nur Windows. Oberfläche wird nicht gestartet.")
            return
        utils.ensure_tcl_env(self.log)
        try:
            import tkinter  # noqa: F401  - früh prüfen, im OBS-Thread
        except Exception as exc:
            self.log.error(
                "Tkinter ist nicht verfügbar (%s). Die in OBS eingetragene Python-Installation "
                "enthält kein Tcl/Tk. Siehe docs/INSTALLATION.md (Abschnitt Python/Tkinter)." % exc)
            return
        from .overlay import OverlayApp
        pos = None
        try:
            # Vor 1.0.3 gespeicherte Positionen lagen standardmäßig in der Bildschirmmitte.
            # Diese einmalig migrieren wir auf die neue obere Standardposition.
            pos_version = 0
            if self.obs.obs_data_has_user_value(settings, "overlay_position_version"):
                pos_version = self.obs.obs_data_get_int(settings, "overlay_position_version")
            if pos_version >= 2 and self.obs.obs_data_has_user_value(settings, "overlay_x"):
                pos = (self.obs.obs_data_get_int(settings, "overlay_x"),
                       self.obs.obs_data_get_int(settings, "overlay_y"))
        except Exception:
            pos = None
        self.app = OverlayApp(self.controller, cfg, tr, self.log, pos)
        self.app.start()

    # ------------------------------------------------------------------ Laufzeit
    def pump(self):
        """OBS-Timer: Zustand abgleichen und Logs ausgeben."""
        if not self.loaded:
            return
        try:
            c = self.controller
            if not c.ready and time.monotonic() - self._loaded_at > self._ready_fallback:
                c.mark_ready()   # Skript wurde nachträglich geladen (kein FINISHED_LOADING-Ereignis)
            # OBS-Befehle laufen im separaten Controller-Worker, nicht im Timer.
            c.reconcile()
            if self.app is not None and not self.app.alive and not self._warned_dead:
                self._warned_dead = True
                self.log.error("Overlay-Thread läuft nicht mehr.")
        except Exception as exc:
            self.log.error("Fehler im OBS-Timer: %s" % exc)
        self.log.flush()

    def on_event(self, event):
        if self.loaded and self.controller is not None:
            self.controller.handle_event(event)
        self.log.flush()

    def on_hotkey(self, pressed):
        if not pressed or not self.loaded:
            return
        if self.app is None or not self.app.alive:
            self.log.warning("Overlay ist nicht verfügbar (siehe Skript-Protokoll).")
        else:
            self.app.post("toggle")

    def toggle_overlay(self):
        self.on_hotkey(True)

    # ------------------------------------------------------------------ Speichern/Beenden
    def save(self, settings):
        if not self.loaded:
            return
        self.hotkeys.save(settings)
        if self.app is not None and self.app.saved_pos:
            try:
                # Erst eine bewusst verschobene Position markieren. So bleiben
                # alte, früher automatisch gespeicherte Center-Koordinaten ungültig.
                self.obs.obs_data_set_int(settings, "overlay_x", int(self.app.saved_pos[0]))
                self.obs.obs_data_set_int(settings, "overlay_y", int(self.app.saved_pos[1]))
                self.obs.obs_data_set_int(settings, "overlay_position_version", 2)
            except Exception:
                pass

    def shutdown(self):
        """Idempotent: darf aus EXIT-Ereignis und script_unload aufgerufen werden."""
        if not self.loaded:
            return
        self.loaded = False
        if self._timer_cb is not None:
            try:
                self.obs.timer_remove(self._timer_cb)
            except Exception:
                pass
        try:
            self.obs.obs_frontend_remove_event_callback(self._event_cb)
        except Exception:
            pass
        if self.controller is not None:
            self.controller.stop_worker()
        if self.app is not None:
            self.app.stop()
            self.app = None
        self.hotkeys.release()
        self.log.info("Beendet, alle Ressourcen freigegeben.")
        self.log.flush()
