"""Verbindung zur OBS-Frontend-API.

Threading-Regeln:
* Statusabfragen und Ereignisverarbeitung passieren in OBS-Callbacks.
* Der Tk-Thread darf nur request() und snapshot() benutzen (threadsicher).
* Frontend-Aktionsbefehle laufen separat, damit sie OBS-Callback-Sperren nicht blockieren.
"""
import queue
import threading
import time

from . import utils


class ObsController:
    def __init__(self, obs, cfg, log, on_exit=None):
        self._obs = obs
        self._log = log
        self._on_exit = on_exit
        t = cfg["timing"]
        self._debounce = t["command_debounce_ms"] / 1000.0
        self._busy_timeout = t["busy_timeout_ms"] / 1000.0
        self._reconcile_every = t["reconcile_ms"] / 1000.0
        self._lock = threading.Lock()
        self._action_lock = threading.Lock()
        self._commands = queue.Queue()
        self.ui_events = queue.Queue()   # ("toast", translation_key, optional_args...) / ("notice", key, args...)
        self._last_request = {}
        self._worker = None
        self._worker_stop = threading.Event()
        self._worker_busy = False
        self._pending_commands = 0
        self._stopping = False
        self._busy_until = {"rec": 0.0, "rep": 0.0, "save": 0.0}
        self._last_reconcile = 0.0
        self.ready = False
        self.recording = False
        self.paused = False
        self.replay = False
        self.replay_available = True
        self._rec_t0 = 0.0
        self._rec_acc = 0.0

    # ------------------------------------------------------------ Hilfen
    def _ev(self, name):
        return getattr(self._obs, "OBS_FRONTEND_EVENT_" + name, None)

    def _notice(self, key, *args):
        self.ui_events.put(("notice", key) + args)

    def mark_ready(self):
        with self._lock:
            already_ready = self.ready
            self.ready = True
        if not already_ready:
            self.sync()

    # ---------------------------------------------------- Befehls-Worker
    def start_worker(self):
        """Führt OBS-Aktionen außerhalb des OBS-Skript-Timers aus.

        OBS-Frontend-Aktionen lösen weitere Frontend-Ereignisse aus. Werden sie
        direkt im Skript-Timer ausgeführt, kann das mit OBS' Callback-Sperre
        kollidieren. Der Worker ruft ausschließlich die Frontend-Aktions-API
        auf; Status und Ereignisse bleiben beim OBS-Skript.
        """
        with self._lock:
            if self._stopping:
                return False
            if self._worker is not None and self._worker.is_alive():
                return True
            self._worker_stop.clear()
            self._worker = threading.Thread(
                target=self._worker_loop, name="ShadowPlayObsCommands", daemon=True)
            self._worker.start()
        return True

    def stop_worker(self, timeout=2.0):
        """Stoppt den Befehls-Worker und verwirft noch nicht ausgeführte Befehle."""
        with self._lock:
            self._stopping = True
            self._worker_stop.set()
        # Wartet höchstens auf den gerade laufenden, kurzen Frontend-Aufruf.
        # Danach kann kein Worker-Befehl mehr eine OBS-Aktion starten.
        with self._action_lock:
            pass
        # Befehle, die beim Beenden noch in der Queue liegen, nicht mehr ausführen.
        while True:
            try:
                self._commands.get_nowait()
            except queue.Empty:
                break
            else:
                try:
                    self._commands.task_done()
                except Exception:
                    pass
        with self._lock:
            self._pending_commands = 0
        worker = self._worker
        if worker is not None and worker.is_alive() and worker is not threading.current_thread():
            worker.join(timeout)
            if worker.is_alive():
                self._log.warning("OBS-Befehls-Worker beendet sich nicht rechtzeitig.")
        self._worker = None

    def _worker_loop(self):
        while not self._worker_stop.is_set():
            try:
                cmd = self._commands.get(timeout=0.2)
            except queue.Empty:
                continue
            if cmd is None:
                self._commands.task_done()
                break
            with self._lock:
                self._worker_busy = True
            try:
                self._execute(cmd)
            except Exception as exc:
                self._log.error("Befehl %s fehlgeschlagen: %s" % (cmd, exc))
                self._notice("n_error")
                self._clear_busy(cmd)
            finally:
                with self._lock:
                    self._worker_busy = False
                    self._pending_commands = max(0, self._pending_commands - 1)
                self._commands.task_done()

    def wait_for_idle(self, timeout=2.0):
        """Testhilfe: wartet begrenzt, bis alle Befehle abgearbeitet sind."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if self._pending_commands == 0:
                    return True
            time.sleep(0.01)
        return False

    def snapshot(self):
        """Threadsichere Kopie des Zustands für die Oberfläche."""
        now = time.monotonic()
        with self._lock:
            elapsed = 0.0
            if self.recording:
                elapsed = self._rec_acc + (0.0 if self.paused else now - self._rec_t0)
            return {
                "ready": self.ready, "recording": self.recording, "paused": self.paused,
                "replay": self.replay, "replay_available": self.replay_available,
                "elapsed": elapsed,
                "busy_rec": now < self._busy_until["rec"],
                "busy_rep": now < self._busy_until["rep"],
                "busy_save": now < self._busy_until["save"],
            }

    # ------------------------------------------------- Zustand synchronisieren
    def sync(self):
        """Liest den tatsächlichen OBS-Zustand (nur OBS-Thread, nur wenn ready)."""
        with self._lock:
            ready = self.ready
        if not ready:
            return
        obs = self._obs
        try:
            rec = bool(obs.obs_frontend_recording_active())
            rep = bool(obs.obs_frontend_replay_buffer_active())
            paused = bool(rec and obs.obs_frontend_recording_paused())
        except Exception as exc:
            self._log.error("Status konnte nicht gelesen werden: %s" % exc)
            return
        available = self._query_replay_available()
        with self._lock:
            if rec and not self.recording:
                self._rec_t0, self._rec_acc = time.monotonic(), 0.0  # Startzeit unbekannt -> ab jetzt
            if paused != self.paused and rec:
                self._apply_pause_locked(paused)
            self.recording, self.replay = rec, rep
            if not rec:
                self.paused = False
            self.replay_available = available or rep

    def _query_replay_available(self):
        getter = getattr(self._obs, "obs_frontend_get_replay_buffer_output", None)
        if getter is None:
            return True
        try:
            out = getter()
            if out is None:
                return False
            self._obs.obs_output_release(out)
            return True
        except Exception:
            return True

    def _apply_pause_locked(self, paused):
        now = time.monotonic()
        if paused and not self.paused:
            self._rec_acc += now - self._rec_t0
        elif not paused and self.paused:
            self._rec_t0 = now
        self.paused = paused

    def reconcile(self):
        now = time.monotonic()
        if now - self._last_reconcile >= self._reconcile_every:
            self._last_reconcile = now
            self.sync()

    # -------------------------------------------------------- OBS-Ereignisse
    def handle_event(self, event):
        """Wird aus dem OBS-Event-Callback aufgerufen."""
        try:
            self._handle_event(event)
        except Exception as exc:
            self._log.error("Fehler bei OBS-Ereignis %s: %s" % (event, exc))

    def _handle_event(self, event):
        if event is None:
            return
        # OBS kündigt das Ende des Python-Scripting-Subsystems vor dem
        # abschließenden Frontend-EXIT an. Beide Ereignisse dürfen den
        # idempotenten Shutdown auslösen.
        shutdown_events = (self._ev("SCRIPTING_SHUTDOWN"), self._ev("EXIT"))
        if event in shutdown_events:
            if self._on_exit:
                self._on_exit()
            return
        if event == self._ev("FINISHED_LOADING"):
            self.mark_ready()
            return
        if event in (self._ev("PROFILE_CHANGED"), self._ev("SCENE_COLLECTION_CHANGED")):
            self.sync()
            return
        with self._lock:
            ready = self.ready
        if not ready:
            return
        with self._lock:
            if event == self._ev("RECORDING_STARTED"):
                self.recording, self.paused = True, False
                self._rec_t0, self._rec_acc = time.monotonic(), 0.0
                self._busy_until["rec"] = 0.0
                self.ui_events.put(("toast", "toast_rec_started"))
            elif event == self._ev("RECORDING_STOPPED"):
                self.recording, self.paused = False, False
                self._busy_until["rec"] = 0.0
                self.ui_events.put(("toast", "toast_rec_stopped"))
            elif event == self._ev("RECORDING_PAUSED"):
                if self.recording:
                    self._apply_pause_locked(True)
                    self.ui_events.put(("toast", "toast_rec_paused"))
            elif event == self._ev("RECORDING_UNPAUSED"):
                if self.recording:
                    self._apply_pause_locked(False)
                    self.ui_events.put(("toast", "toast_rec_resumed"))
            elif event == self._ev("REPLAY_BUFFER_STARTED"):
                self.replay = True
                self.replay_available = True
                self._busy_until["rep"] = 0.0
                self.ui_events.put(("toast", "toast_replay_started"))
            elif event == self._ev("REPLAY_BUFFER_STOPPED"):
                self.replay = False
                self._busy_until["rep"] = 0.0
                self.ui_events.put(("toast", "toast_replay_stopped"))
            elif event == self._ev("REPLAY_BUFFER_SAVED"):
                name = self._last_replay_name()
                if name:
                    self.ui_events.put(("toast", "toast_clip_saved_named", name))
                else:
                    self.ui_events.put(("toast", "toast_clip_saved"))

    def _last_replay_name(self):
        getter = getattr(self._obs, "obs_frontend_get_last_replay", None)
        try:
            path = getter() if getter else None
        except Exception:
            return None
        if not path:
            return None
        return str(path).replace("\\", "/").rsplit("/", 1)[-1]

    # --------------------------------------------------------------- Befehle
    def request(self, cmd):
        """Threadsicher: legt einen Befehl in die Warteschlange (mit Entprellung)."""
        group = {"rec_start": "rec", "rec_stop": "rec", "rep_start": "rep",
                 "rep_stop": "rep", "rep_save": "save"}.get(cmd)
        if group is None:
            return False
        now = time.monotonic()
        with self._lock:
            if self._stopping:
                return False
            if now < self._busy_until[group] or now - self._last_request.get(cmd, 0.0) < self._debounce:
                return False  # Mehrfachklick -> ignorieren
            self._last_request[cmd] = now
            self._busy_until[group] = now + (self._debounce if group == "save" else self._busy_timeout)
            self._pending_commands += 1
            self._commands.put(cmd)
        return True

    def process_commands(self):
        """Synchroner Fallback für Tests; im OBS-Betrieb ist der Worker zuständig."""
        if self._worker is not None and self._worker.is_alive():
            return
        while True:
            try:
                cmd = self._commands.get_nowait()
            except queue.Empty:
                return
            try:
                self._execute(cmd)
            except Exception as exc:
                self._log.error("Befehl %s fehlgeschlagen: %s" % (cmd, exc))
                self._notice("n_error")
                self._clear_busy(cmd)
            finally:
                with self._lock:
                    self._pending_commands = max(0, self._pending_commands - 1)
                self._commands.task_done()

    def _clear_busy(self, cmd):
        group = {"rec_start": "rec", "rec_stop": "rec", "rep_start": "rep",
                 "rep_stop": "rep", "rep_save": "save"}[cmd]
        with self._lock:
            self._busy_until[group] = 0.0

    def _send_frontend_action(self, cmd, action):
        """Schützt OBS-Aktionsaufrufe vor einem gleichzeitigen Skript-Ende."""
        with self._action_lock:
            if self._worker_stop.is_set():
                self._clear_busy(cmd)
                return False
            action()
            return True

    def _execute(self, cmd):
        """Sendet genau einen Frontend-Befehl anhand des zuletzt bekannten Zustands.

        Absichtlich KEIN sync() hier: Diese Methode läuft im Worker und darf
        keine zusätzlichen OBS-Abfragen ausführen. Der Zustand wird durch
        Frontend-Events und den regulären OBS-Abgleich aktualisiert.
        """
        obs = self._obs
        with self._lock:
            ready = self.ready
            recording = self.recording
            replay = self.replay
            replay_available = self.replay_available

        if not ready:
            self._notice("n_not_ready")
            self._clear_busy(cmd)
            return
        if cmd == "rec_start":
            if recording:
                self._notice("n_rec_already"); self._clear_busy(cmd)
            else:
                self._send_frontend_action(cmd, obs.obs_frontend_recording_start)
        elif cmd == "rec_stop":
            if not recording:
                self._notice("n_rec_inactive"); self._clear_busy(cmd)
            else:
                self._send_frontend_action(cmd, obs.obs_frontend_recording_stop)
        elif cmd == "rep_start":
            if replay:
                self._notice("n_rep_already"); self._clear_busy(cmd)
            elif not replay_available:
                self._notice("n_rep_unavail"); self._clear_busy(cmd)
            else:
                self._send_frontend_action(cmd, obs.obs_frontend_replay_buffer_start)
        elif cmd == "rep_stop":
            if not replay:
                self._notice("n_rep_inactive"); self._clear_busy(cmd)
            else:
                self._send_frontend_action(cmd, obs.obs_frontend_replay_buffer_stop)
        elif cmd == "rep_save":
            if not replay:
                self._notice("n_rep_inactive"); self._clear_busy(cmd)
            else:
                self._send_frontend_action(cmd, obs.obs_frontend_replay_buffer_save)  # nur Replay-Buffer
