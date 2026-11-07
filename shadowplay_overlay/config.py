"""Konfiguration und Übersetzungen."""
import copy
import json
import os

from . import utils

DEFAULTS = {
    "language": "auto",
    "overlay": {"opacity": 0.88, "default_position": "top_center"},
    "status": {"margin_right": 6, "margin_bottom": 6, "gap": 4,
               "opacity": 0.86, "use_work_area": False},
    "toast": {"duration_seconds": 3.0, "margin_top": 20,
              "margin_right": 20, "opacity": 0.90},
    "timing": {"ui_poll_ms": 50, "obs_pump_ms": 100, "reconcile_ms": 1000,
               "command_debounce_ms": 700, "busy_timeout_ms": 3000,
               "ready_fallback_s": 6},
}

STRINGS = {
    "de": {
        "title": "OBS Overlay", "close": "Schließen",
        "replay_title": "Sofort-Wiederholung", "save_title": "Clip speichern",
        "rec_title": "Aufnahme",
        "save_ready": "Bereit zum Speichern", "save_inactive": "Replay Buffer nicht aktiv",
        "replay_on": "Aktiv", "replay_off": "Aus", "replay_unavailable": "Nicht verfügbar",
        "rec_idle": "Bereit", "rec_running": "Läuft", "rec_paused": "Pausiert",
        "waiting": "OBS startet …",
        "btn_enable": "Aktivieren", "btn_disable": "Deaktivieren", "btn_save": "Clip speichern",
        "btn_rec_start": "Starten", "btn_rec_stop": "Stoppen",
        "hint": "Alt+Z  ·  Esc",
        "badge_replay": "Replay Buffer aktiv", "badge_rec": "REC", "badge_pause": "PAUSE",
        "toast_rec_started": "Aufnahme gestartet",
        "toast_rec_stopped": "Aufnahme gestoppt",
        "toast_rec_paused": "Aufnahme pausiert",
        "toast_rec_resumed": "Aufnahme fortgesetzt",
        "toast_replay_started": "Replay Buffer aktiviert",
        "toast_replay_stopped": "Replay Buffer deaktiviert",
        "toast_clip_saved": "Clip gespeichert",
        "toast_clip_saved_named": "Clip gespeichert: %s",
        "n_not_ready": "OBS ist noch nicht bereit.",
        "n_rep_unavail": "Replay Buffer in OBS aktivieren: Einstellungen → Ausgabe → Aufnahme.",
        "n_rep_already": "Replay Buffer ist bereits aktiv.",
        "n_rep_inactive": "Replay Buffer ist nicht aktiv.",
        "n_rec_already": "Aufnahme läuft bereits.",
        "n_rec_inactive": "Es läuft keine Aufnahme.",
        "n_error": "OBS-Aufruf fehlgeschlagen (siehe Skript-Protokoll).",
        "n_saved": "Clip gespeichert: %s",
    },
    "en": {
        "title": "OBS Overlay", "close": "Close",
        "replay_title": "Instant Replay", "save_title": "Save clip",
        "rec_title": "Recording",
        "save_ready": "Ready to save", "save_inactive": "Replay Buffer is off",
        "replay_on": "On", "replay_off": "Off", "replay_unavailable": "Unavailable",
        "rec_idle": "Ready", "rec_running": "Recording", "rec_paused": "Paused",
        "waiting": "OBS is starting …",
        "btn_enable": "Enable", "btn_disable": "Disable", "btn_save": "Save clip",
        "btn_rec_start": "Start", "btn_rec_stop": "Stop",
        "hint": "Alt+Z  ·  Esc",
        "badge_replay": "Replay Buffer on", "badge_rec": "REC", "badge_pause": "PAUSED",
        "toast_rec_started": "Recording started",
        "toast_rec_stopped": "Recording stopped",
        "toast_rec_paused": "Recording paused",
        "toast_rec_resumed": "Recording resumed",
        "toast_replay_started": "Replay Buffer enabled",
        "toast_replay_stopped": "Replay Buffer disabled",
        "toast_clip_saved": "Clip saved",
        "toast_clip_saved_named": "Clip saved: %s",
        "n_not_ready": "OBS is not ready yet.",
        "n_rep_unavail": "Enable the Replay Buffer in OBS: Settings → Output → Recording.",
        "n_rep_already": "Replay Buffer is already active.",
        "n_rep_inactive": "Replay Buffer is not active.",
        "n_rec_already": "Recording is already running.",
        "n_rec_inactive": "No recording is running.",
        "n_error": "OBS call failed (see script log).",
        "n_saved": "Clip saved: %s",
    },
}


def _merge(base, override):
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def load(root_dir, log=None):
    """DEFAULTS <- config/default_config.json <- config/user_config.json."""
    cfg = copy.deepcopy(DEFAULTS)
    for name in ("default_config.json", "user_config.json"):
        path = os.path.join(root_dir, "config", name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                _merge(cfg, json.load(fh))
        except Exception as exc:
            if log:
                log.warning("Konfiguration %s nicht lesbar (%s) - Standardwerte werden verwendet." % (name, exc))
    return cfg


class Translator:
    def __init__(self, language="auto"):
        if language not in STRINGS:
            language = "de" if utils.ui_language_is_german() else "en"
        self.language = language
        self._table = STRINGS[language]

    def __call__(self, key, *args):
        text = self._table.get(key) or STRINGS["en"].get(key) or key
        return text % args if args else text
