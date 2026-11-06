"""Minimaler Ersatz für obspython (nur für Tests ohne OBS)."""
LOG_INFO, LOG_WARNING, LOG_ERROR = 100, 200, 300
OBS_FRONTEND_EVENT_RECORDING_STARTED = 1
OBS_FRONTEND_EVENT_RECORDING_STOPPED = 2
OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED = 3
OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPED = 4
OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED = 5
OBS_FRONTEND_EVENT_EXIT = 6
OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN = 12
OBS_FRONTEND_EVENT_FINISHED_LOADING = 7
OBS_FRONTEND_EVENT_RECORDING_PAUSED = 8
OBS_FRONTEND_EVENT_RECORDING_UNPAUSED = 9
OBS_FRONTEND_EVENT_PROFILE_CHANGED = 10
OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGED = 11

calls, logs = [], []
state = {"rec": False, "rep": False, "paused": False, "rep_output": True}
hotkeys, timers, event_cbs, saved_bindings = {}, [], [], {}


def script_log(level, msg): logs.append((level, msg))
def obs_frontend_recording_active(): return state["rec"]
def obs_frontend_recording_paused(): return state["paused"]
def obs_frontend_replay_buffer_active(): return state["rep"]
def obs_frontend_recording_start(): calls.append("rec_start")
def obs_frontend_recording_stop(): calls.append("rec_stop")
def obs_frontend_replay_buffer_start(): calls.append("rep_start")
def obs_frontend_replay_buffer_stop(): calls.append("rep_stop")
def obs_frontend_replay_buffer_save(): calls.append("rep_save")
def obs_frontend_get_last_replay(): return "C:\\Videos\\Replay 2026-11-06.mkv"
def obs_frontend_get_replay_buffer_output(): return object() if state["rep_output"] else None
def obs_output_release(o): pass
def obs_frontend_add_event_callback(cb): event_cbs.append(cb)
def obs_frontend_remove_event_callback(cb): event_cbs.remove(cb)
def timer_add(cb, ms): timers.append(cb)
def timer_remove(cb): timers.remove(cb)

OBS_INVALID_HOTKEY_ID = -1
def obs_hotkey_register_frontend(name, desc, cb):
    hotkeys[name] = cb; return len(hotkeys)
class _Data(dict): pass
def obs_data_has_user_value(s, k): return k in s
def obs_data_get_array(s, k): return s[k]
def obs_data_array_create(): return []
def obs_data_create(): return _Data()
def obs_data_set_string(d, k, v): d[k] = v
def obs_data_set_bool(d, k, v): d[k] = v
def obs_data_array_push_back(a, d): a.append(d)
def obs_data_release(d): pass
def obs_data_array_release(a): pass
def obs_hotkey_load(hid, arr): saved_bindings[hid] = list(arr)
def obs_hotkey_save(hid): return saved_bindings.get(hid, [])
def obs_data_set_array(s, k, a): s[k] = a
def obs_data_set_int(s, k, v): s[k] = v
def obs_data_get_int(s, k): return s[k]
