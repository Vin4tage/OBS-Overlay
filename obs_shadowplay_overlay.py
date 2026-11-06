"""
OBS-Einstiegsdatei - diese eine Datei in OBS unter  Werkzeuge -> Skripte -> "+"  hinzufügen.
Add THIS file in OBS under Tools -> Scripts -> "+".

ShadowPlay-Style Overlay für OBS Studio (Windows) - unabhängiges Community-Projekt,
nicht von NVIDIA oder dem OBS Project. Siehe README.md.
"""
import os
import sys

import obspython as obs

try:
    _ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:  # pragma: no cover
    _ROOT = os.path.dirname(os.path.abspath(obs.script_path()))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Beim Neuladen des Skripts keine veralteten Modulversionen verwenden.
for _name in [m for m in sys.modules if m == "shadowplay_overlay" or m.startswith("shadowplay_overlay.")]:
    del sys.modules[_name]

from shadowplay_overlay import core  # noqa: E402

_plugin = core.Plugin(obs, _ROOT)


# Callbacks müssen Funktionen auf Modulebene sein (keine Methoden).
def _on_frontend_event(event):
    _plugin.on_event(event)


def _on_timer():
    _plugin.pump()


def _on_hotkey(pressed):
    _plugin.on_hotkey(pressed)


def _on_toggle_button(props, prop):
    _plugin.toggle_overlay()
    return False


def script_description():
    return core.DESCRIPTION


def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_button(props, "toggle", "Overlay öffnen/schließen (Open/Close)", _on_toggle_button)
    return props


def script_load(settings):
    _plugin.load(settings, _on_frontend_event, _on_timer, _on_hotkey)


def script_save(settings):
    _plugin.save(settings)


def script_unload():
    _plugin.shutdown()
