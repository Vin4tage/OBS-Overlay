"""Hotkey-Registrierung über die OBS-Hotkey-API (kein globaler Tastatur-Hook)."""

HOTKEY_NAME = "shadowplay_overlay.toggle"
HOTKEY_DESC = "ShadowPlay Overlay: öffnen/schließen (Open/Close)"
SETTINGS_KEY = "shadowplay_overlay_toggle_hotkey"


class HotkeyManager:
    def __init__(self, obs, log):
        self._obs = obs
        self._log = log
        self.hotkey_id = None

    def register(self, settings, callback):
        """Registriert den Hotkey genau einmal. Standardbelegung: Alt+Z."""
        if self.hotkey_id is not None:
            return True
        obs = self._obs
        try:
            hid = obs.obs_hotkey_register_frontend(HOTKEY_NAME, HOTKEY_DESC, callback)
        except Exception as exc:
            self._log.error("Hotkey konnte nicht registriert werden: %s" % exc)
            return False
        if hid == getattr(obs, "OBS_INVALID_HOTKEY_ID", None):
            self._log.error("Hotkey-Registrierung wurde von OBS abgelehnt.")
            return False
        self.hotkey_id = hid
        self._load_binding(settings)
        return True

    def _load_binding(self, settings):
        obs = self._obs
        arr = None
        try:
            if obs.obs_data_has_user_value(settings, SETTINGS_KEY):
                # Gespeicherte Belegung (auch eine bewusst geleerte) wird respektiert.
                arr = obs.obs_data_get_array(settings, SETTINGS_KEY)
            else:
                arr = obs.obs_data_array_create()
                item = obs.obs_data_create()
                obs.obs_data_set_string(item, "key", "OBS_KEY_Z")
                obs.obs_data_set_bool(item, "alt", True)
                obs.obs_data_array_push_back(arr, item)
                obs.obs_data_release(item)
            obs.obs_hotkey_load(self.hotkey_id, arr)
        except Exception as exc:
            self._log.error("Hotkey-Belegung konnte nicht geladen werden: %s" % exc)
        finally:
            if arr is not None:
                try:
                    obs.obs_data_array_release(arr)
                except Exception:
                    pass

    def save(self, settings):
        if self.hotkey_id is None:
            return
        obs = self._obs
        try:
            arr = obs.obs_hotkey_save(self.hotkey_id)
            obs.obs_data_set_array(settings, SETTINGS_KEY, arr)
            obs.obs_data_array_release(arr)
        except Exception as exc:
            self._log.error("Hotkey-Belegung konnte nicht gespeichert werden: %s" % exc)

    def release(self):
        # OBS entfernt vom Skript registrierte Hotkeys beim Entladen selbst.
        self.hotkey_id = None
