import os, sys, threading, time, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import fake_obs as obs
from shadowplay_overlay import config, utils
from shadowplay_overlay.obs_controller import ObsController
from shadowplay_overlay.overlay import RoundButton
from shadowplay_overlay.hotkeys import HotkeyManager, SETTINGS_KEY

ROOT = os.path.join(os.path.dirname(__file__), "..")


def make():
    obs.calls.clear(); obs.logs.clear()
    obs.state.update(rec=False, rep=False, paused=False, rep_output=True)
    cfg = config.load(ROOT)
    c = ObsController(obs, cfg, utils.Logger(obs))
    c.mark_ready()
    return c


def drain(q):
    out = []
    while not q.empty():
        out.append(q.get_nowait())
    return out


class CanvasStub:
    """Kleiner Canvas-Ersatz, um stabile Elemente ohne Display zu pruefen."""
    def __init__(self):
        self.created = []
        self.configured = []
        self.deleted = 0

    def create_polygon(self, *args, **kwargs):
        item_id = len(self.created) + 1
        self.created.append(("polygon", args, kwargs))
        return item_id

    def create_text(self, *args, **kwargs):
        item_id = len(self.created) + 1
        self.created.append(("text", args, kwargs))
        return item_id

    def itemconfigure(self, item_id, **kwargs):
        self.configured.append((item_id, kwargs))

    def delete(self, *_args):
        self.deleted += 1


class RoundButtonTests(unittest.TestCase):
    def test_hover_and_state_updates_reuse_existing_canvas_items(self):
        canvas = CanvasStub()
        button = RoundButton(canvas, 10, 20, 120, 36, lambda: None, "Test")
        self.assertEqual(len(canvas.created), 2)
        for _ in range(10):
            button.set_hover(True)
            button.set_hover(False)
        button.configure(text="Save", kind="primary", enabled=False)
        button.configure(enabled=True)
        self.assertEqual(len(canvas.created), 2)
        self.assertEqual(canvas.deleted, 0)
        self.assertGreater(len(canvas.configured), 2)


class ControllerTests(unittest.TestCase):
    def test_replay_save_uses_replay_api_only(self):
        c = make(); obs.state["rep"] = True; c.sync()
        self.assertTrue(c.request("rep_save")); c.process_commands()
        self.assertEqual(obs.calls, ["rep_save"])

    def test_save_refused_when_inactive(self):
        c = make(); c.request("rep_save"); c.process_commands()
        self.assertEqual(obs.calls, [])
        self.assertIn(("notice", "n_rep_inactive"), drain(c.ui_events))

    def test_double_click_ignored(self):
        c = make()
        self.assertTrue(c.request("rec_start"))
        self.assertFalse(c.request("rec_start"))
        c.process_commands()
        self.assertEqual(obs.calls, ["rec_start"])

    def test_already_active_not_restarted(self):
        c = make(); obs.state["rec"] = True; obs.state["rep"] = True; c.sync()
        c.request("rec_start"); c.request("rep_start"); c.process_commands()
        self.assertEqual(obs.calls, [])
        keys = [e[1] for e in drain(c.ui_events)]
        self.assertIn("n_rec_already", keys); self.assertIn("n_rep_already", keys)

    def test_replay_unavailable(self):
        c = make(); obs.state["rep_output"] = False; c.sync()
        c.request("rep_start"); c.process_commands()
        self.assertEqual(obs.calls, [])
        self.assertIn(("notice", "n_rep_unavail"), drain(c.ui_events))

    def test_events_drive_state_not_clicks(self):
        c = make()
        c.handle_event(obs.OBS_FRONTEND_EVENT_RECORDING_STARTED)
        self.assertTrue(c.snapshot()["recording"])
        c.handle_event(obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED)
        self.assertTrue(c.snapshot()["replay"])
        drain(c.ui_events)
        c.handle_event(obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED)
        self.assertEqual(drain(c.ui_events)[0],
                         ("toast", "toast_clip_saved_named", "Replay 2026-11-06.mkv"))
        c.handle_event(obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED)
        s = c.snapshot(); self.assertFalse(s["recording"])
        self.assertIn(("toast", "toast_rec_stopped"), drain(c.ui_events))
        c.handle_event(obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPED)
        self.assertFalse(c.snapshot()["replay"])
        self.assertIn(("toast", "toast_replay_stopped"), drain(c.ui_events))

    def test_reconcile_catches_missed_event(self):
        c = make(); obs.state["rec"] = True; c.reconcile()
        self.assertTrue(c.snapshot()["recording"])

    def test_pause_freezes_timer_and_emits_action_toasts(self):
        c = make()
        c.handle_event(obs.OBS_FRONTEND_EVENT_RECORDING_STARTED)
        self.assertIn(("toast", "toast_rec_started"), drain(c.ui_events))
        c.handle_event(obs.OBS_FRONTEND_EVENT_RECORDING_PAUSED)
        self.assertIn(("toast", "toast_rec_paused"), drain(c.ui_events))
        a = c.snapshot()["elapsed"]; time.sleep(0.05)
        self.assertAlmostEqual(a, c.snapshot()["elapsed"], places=3)
        c.handle_event(obs.OBS_FRONTEND_EVENT_RECORDING_UNPAUSED)
        self.assertIn(("toast", "toast_rec_resumed"), drain(c.ui_events))

    def test_api_error_does_not_raise(self):
        c = make(); obs.state["rec"] = False
        orig = obs.obs_frontend_recording_start
        obs.obs_frontend_recording_start = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            c.request("rec_start"); c.process_commands()
        finally:
            obs.obs_frontend_recording_start = orig
        self.assertIn(("notice", "n_error"), drain(c.ui_events))
        self.assertFalse(c.snapshot()["busy_rec"])

    def test_not_ready_blocks_commands(self):
        c = make(); c.ready = False
        c.request("rec_start"); c.process_commands()
        self.assertEqual(obs.calls, [])

    def test_exit_event_calls_shutdown(self):
        hit = []
        c = ObsController(obs, config.load(ROOT), utils.Logger(obs), on_exit=lambda: hit.append(1))
        c.handle_event(obs.OBS_FRONTEND_EVENT_EXIT)
        self.assertEqual(hit, [1])

    def test_scripting_shutdown_event_calls_shutdown(self):
        hit = []
        c = ObsController(obs, config.load(ROOT), utils.Logger(obs), on_exit=lambda: hit.append(1))
        c.handle_event(obs.OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN)
        self.assertEqual(hit, [1])

    def test_worker_runs_frontend_actions_outside_obs_timer(self):
        c = make()
        original = obs.obs_frontend_recording_start
        called_from = []

        def tracked_start():
            called_from.append(threading.current_thread().name)
            original()

        obs.obs_frontend_recording_start = tracked_start
        try:
            self.assertTrue(c.start_worker())
            self.assertTrue(c.request("rec_start"))
            self.assertTrue(c.wait_for_idle(2.0), "Befehls-Worker wurde nicht fertig")
            self.assertEqual(obs.calls, ["rec_start"])
            self.assertEqual(called_from, ["ShadowPlayObsCommands"])
        finally:
            obs.obs_frontend_recording_start = original
            c.stop_worker()



class HotkeyTests(unittest.TestCase):
    def test_default_alt_z_and_single_registration(self):
        obs.hotkeys.clear(); obs.saved_bindings.clear()
        h = HotkeyManager(obs, utils.Logger(obs)); s = {}
        self.assertTrue(h.register(s, lambda p: None))
        self.assertTrue(h.register(s, lambda p: None))
        self.assertEqual(len(obs.hotkeys), 1)
        b = obs.saved_bindings[h.hotkey_id][0]
        self.assertEqual((b["key"], b["alt"]), ("OBS_KEY_Z", True))
        h.save(s); self.assertIn(SETTINGS_KEY, s)

    def test_cleared_binding_respected(self):
        obs.hotkeys.clear(); obs.saved_bindings.clear()
        h = HotkeyManager(obs, utils.Logger(obs)); s = {SETTINGS_KEY: []}
        h.register(s, lambda p: None)
        self.assertEqual(obs.saved_bindings[h.hotkey_id], [])


class ConfigTests(unittest.TestCase):
    def test_translator(self):
        self.assertEqual(config.Translator("de")("btn_save"), "Clip speichern")
        self.assertEqual(config.Translator("en")("btn_save"), "Save clip")
        self.assertEqual(config.Translator("en")("n_saved", "a.mkv"), "Clip saved: a.mkv")

    def test_german_english_keys_match(self):
        self.assertEqual(set(config.STRINGS["de"]), set(config.STRINGS["en"]))
        self.assertEqual(config.Translator("de")("toast_rec_started"), "Aufnahme gestartet")
        self.assertEqual(config.Translator("en")("toast_replay_stopped"), "Replay Buffer disabled")
        self.assertEqual(config.Translator("de")("toast_clip_saved_named", "clip.mkv"),
                         "Clip gespeichert: clip.mkv")


if __name__ == "__main__":
    unittest.main(verbosity=2)
