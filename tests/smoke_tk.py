"""Tk-Oberfläche + kompletter Lebenszyklus mit gefälschtem OBS.

Empfohlener Lauf unter Linux/Xvfb:
  SHADOWPLAY_ALLOW_NON_WINDOWS=1 xvfb-run -a python tests/smoke_tk.py

Wenn libXtst verfügbar ist, werden Mausbewegung und Mausklick über XTest an
X11 gesendet (echte X-Server-Mausereignisse, nicht nur Callback-Aufrufe).
Windows-spezifische Teile wie Click-Through werden hier nicht geprüft.
"""
import ctypes
import os
import sys
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import fake_obs as obs
from shadowplay_overlay import core


class XTestMouse:
    """Kleine optionale XTest-Hilfe für echte X11-Pointer-/Button-Events."""
    def __init__(self):
        self.display = None
        self.x11 = None
        self.xtst = None
        try:
            self.x11 = ctypes.CDLL("libX11.so.6")
            self.xtst = ctypes.CDLL("libXtst.so.6")
            self.x11.XOpenDisplay.restype = ctypes.c_void_p
            self.x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
            self.display = self.x11.XOpenDisplay(None)
            if not self.display:
                raise RuntimeError("X11-Display nicht verfügbar")
            self.xtst.XTestFakeMotionEvent.argtypes = [
                ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
            self.xtst.XTestFakeMotionEvent.restype = ctypes.c_int
            self.xtst.XTestFakeButtonEvent.argtypes = [
                ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
            self.xtst.XTestFakeButtonEvent.restype = ctypes.c_int
            self.x11.XFlush.argtypes = [ctypes.c_void_p]
            self.x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        except Exception:
            self.close()
            self.display = None

    @property
    def available(self):
        return self.display is not None

    def move(self, x, y):
        if not self.available:
            raise RuntimeError("XTest nicht verfügbar")
        if not self.xtst.XTestFakeMotionEvent(self.display, -1, int(x), int(y), 0):
            raise RuntimeError("XTestFakeMotionEvent fehlgeschlagen")
        self.x11.XFlush(self.display)
        time.sleep(0.08)

    def click(self, x, y):
        self.move(x, y)
        self.xtst.XTestFakeButtonEvent(self.display, 1, 1, 0)
        self.x11.XFlush(self.display)
        time.sleep(0.04)
        self.xtst.XTestFakeButtonEvent(self.display, 1, 0, 0)
        self.x11.XFlush(self.display)
        time.sleep(0.08)

    def close(self):
        if self.display and self.x11:
            try:
                self.x11.XCloseDisplay(self.display)
            except Exception:
                pass
        self.display = None


root = os.path.join(os.path.dirname(__file__), "..")
p = core.Plugin(obs, root)
# Alte v1.0.2-Einstellungen mit gespeicherter Bildschirmmitten-Position prüfen:
# ohne neue Positionsversion muss der erste Start oben zentriert sein.
settings = {"overlay_x": 80, "overlay_y": 420}
ev = lambda e: p.on_event(e)
tm = lambda: p.pump()
hk = lambda pressed: p.on_hotkey(pressed)
p.load(settings, ev, tm, hk)
assert len(obs.hotkeys) == 1 and len(obs.timers) == 1 and len(obs.event_cbs) == 1
p.load(settings, ev, tm, hk)  # zweiter Aufruf darf nichts doppeln
assert len(obs.hotkeys) == 1 and len(obs.timers) == 1


def wait(cond, t=3.0, message="Bedingung nicht erfüllt"):
    end = time.time() + t
    while time.time() < end:
        p.pump()
        if cond():
            return True
        time.sleep(0.03)
    raise AssertionError(message)


def pointer_click(button):
    # Buttonposition relativ zum Overlay-Canvas -> globale X11-Bildschirmkoordinaten.
    x = main.cv.winfo_rootx() + int(button.x + button.w / 2)
    y = main.cv.winfo_rooty() + int(button.y + button.h / 2)
    if mouse.available:
        mouse.click(x, y)
    else:
        # Fallback: bindet die Tk-Canvas-Ereignisse, falls XTest nicht vorhanden ist.
        main.cv.event_generate("<Motion>", x=int(button.x + button.w / 2),
                               y=int(button.y + button.h / 2))
        main.cv.event_generate("<ButtonRelease-1>", x=int(button.x + button.w / 2),
                               y=int(button.y + button.h / 2))


try:
    p.on_event(obs.OBS_FRONTEND_EVENT_FINISHED_LOADING)
    wait(lambda: p.app._started.is_set(), message="Tk-Thread startet nicht")
    main, status = p.app._main, p.app._status
    mouse = XTestMouse()

    # Overlay über Hotkey öffnen/schließen/öffnen.
    hk(True); wait(lambda: main.visible, message="Overlay öffnet nicht")
    hk(True); wait(lambda: not main.visible, message="Overlay schließt nicht")
    hk(True); wait(lambda: main.visible, message="Overlay öffnet sich nicht erneut")

    # Neues Layout: oben mittig, drei horizontale Kacheln.
    main.win.update_idletasks()
    assert main.win.winfo_y() < main.win.winfo_screenheight() // 5, "Overlay wurde nicht nach oben verlegt"
    assert abs((main.win.winfo_x() + main.win.winfo_width() // 2) -
               (main.win.winfo_screenwidth() // 2)) < 5, "Overlay ist nicht horizontal zentriert"
    assert len(main._buttons) == 3
    assert main.btn_rep_toggle.x < main.btn_rep_save.x < main.btn_rec.x

    # Statussymbole und Toast-Meldung prüfen (auch bei OBS-Hotkeys außerhalb des Menüs).
    obs.state.update(rep=True, rec=True)
    p.on_event(obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED)
    p.on_event(obs.OBS_FRONTEND_EVENT_RECORDING_STARTED)
    wait(lambda: status.replay.visible and status.rec.visible and p.app._toast.visible,
         message="Statussymbole/Toast erscheinen nicht")
    r, c = status.replay.win, status.rec.win
    r.update_idletasks(); c.update_idletasks()
    assert r.winfo_y() == c.winfo_y(), "Statussymbole müssen auf einer Linie liegen"
    assert r.winfo_x() + r.winfo_width() < c.winfo_x(), "Statussymbole überlappen"
    assert status.replay.W < 50 and status.rec.W < 130
    assert status.replay._text_id is None, "Replay-Anzeige soll nur das Icon enthalten"
    assert c.winfo_x() + c.winfo_width() + 12 == c.winfo_screenwidth(), "Aufnahmeanzeige nicht unten rechts"
    assert c.winfo_y() + c.winfo_height() + 12 == c.winfo_screenheight(), "Aufnahmeanzeige nicht am unteren Rand"
    toast = p.app._toast
    assert toast._duration == 3.0
    toast.win.update_idletasks()
    assert toast.win.winfo_x() + toast.W + 20 == toast.win.winfo_screenwidth(), "Toast nicht oben rechts"
    assert toast.win.winfo_y() == 20
    assert main.win.winfo_y() >= toast.win.winfo_y() + toast.H, "Menü und Toast dürfen sich nicht überdecken"
    toast.update(time.monotonic() + 3.1)
    assert not toast.visible, "Toast blendet sich nicht nach drei Sekunden aus"
    # Den nur für die Statusanzeige gestarteten Anfangszustand wieder beenden,
    # damit der Aufnahme-Button anschließend wirklich den Startpfad testet.
    obs.state["rec"] = False
    p.on_event(obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED)
    wait(lambda: not p.controller.snapshot()["recording"],
         message="Testaufnahmezustand lässt sich nicht zurücksetzen")

    # Replay-Button ausschalten (erst aktiv, dann deaktivieren).
    obs.state["rep"] = True
    p.on_event(obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED)
    wait(lambda: main.btn_rep_toggle.enabled, message="Replay-Toggle nicht aktiviert")
    # Hover-Pfad mehrfach mit dem realen X11-Pointer überqueren.
    if mouse.available:
        bx = main.cv.winfo_rootx() + int(main.btn_rep_toggle.x + main.btn_rep_toggle.w / 2)
        by = main.cv.winfo_rooty() + int(main.btn_rep_toggle.y + main.btn_rep_toggle.h / 2)
        for _ in range(5):
            mouse.move(main.cv.winfo_rootx() + 10, main.cv.winfo_rooty() + 10)
            mouse.move(bx, by)
            mouse.move(bx + 4, by + 3)
    pointer_click(main.btn_rep_toggle)
    wait(lambda: "rep_stop" in obs.calls, message="Replay deaktivieren löst keinen OBS-Befehl aus")
    obs.state["rep"] = False
    p.on_event(obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPED)

    # Replay Buffer wieder starten und Clip speichern.
    wait(lambda: main.btn_rep_toggle.enabled, message="Replay-Toggle nach Stop nicht aktiviert")
    pointer_click(main.btn_rep_toggle)
    wait(lambda: "rep_start" in obs.calls, message="Replay aktivieren löst keinen OBS-Befehl aus")
    obs.state["rep"] = True
    p.on_event(obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED)
    wait(lambda: main.btn_rep_save.enabled, message="Clip-Speichern-Button bleibt deaktiviert")
    pointer_click(main.btn_rep_save)
    wait(lambda: "rep_save" in obs.calls, message="Clip speichern löst keinen OBS-Befehl aus")
    p.on_event(obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED)

    # Aufnahme starten und stoppen.
    wait(lambda: main.btn_rec.enabled, message="Aufnahme-Button bleibt deaktiviert")
    pointer_click(main.btn_rec)
    wait(lambda: "rec_start" in obs.calls, message="Aufnahme starten löst keinen OBS-Befehl aus")
    obs.state["rec"] = True
    p.on_event(obs.OBS_FRONTEND_EVENT_RECORDING_STARTED)
    wait(lambda: main.btn_rec.enabled, message="Aufnahme-Button nach Start nicht aktiv")
    pointer_click(main.btn_rec)
    wait(lambda: "rec_stop" in obs.calls, message="Aufnahme stoppen löst keinen OBS-Befehl aus")
    obs.state["rec"] = False
    p.on_event(obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED)
    wait(lambda: not status.rec.visible, t=5.0,
         message="Aufnahme-Statussymbol verschwindet nach Stop nicht")

    # Alte gespeicherte Koordinaten bleiben zunächst migriert; erst eine bewusst
    # verschobene Menüposition wird mit der neuen Positionsversion gespeichert.
    p.save(settings)
    assert "overlay_position_version" not in settings
    p.app.saved_pos = (100, 100)
    p.save(settings)
    assert settings.get("overlay_position_version") == 2
    assert (settings.get("overlay_x"), settings.get("overlay_y")) == (100, 100)

    # Schließen über den tatsächlichen Schließen-Button.
    if mouse.available:
        close_x = main.cv.winfo_rootx() + main.cv.winfo_width() - 36
        close_y = main.cv.winfo_rooty() + 34
        mouse.click(close_x, close_y)
        wait(lambda: not main.visible, message="Schließen-Button reagiert nicht")
    else:
        main.cv.event_generate("<ButtonRelease-1>",
                               x=main.cv.winfo_width() - 36, y=34)
        wait(lambda: not main.visible, message="Schließen-Button reagiert nicht")

    assert all(name in obs.calls for name in
               ("rep_stop", "rep_start", "rep_save", "rec_start", "rec_stop")), obs.calls
    print("BUTTON TEST OK; ausgelöste Befehle:", obs.calls)
    print("Mausmodus:", "XTest (echte X11-Pointer-Ereignisse)" if mouse.available else "Tk event_generate fallback")

finally:
    try:
        mouse.close()
    except Exception:
        pass
    # Keine Tk-Objekte über den Tk-Thread hinweg festhalten.
    for name in ("main", "status", "r", "c", "toast"):
        if name in globals():
            del globals()[name]
    p.on_event(obs.OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN)
    time.sleep(0.25)
    assert not p.loaded and not obs.timers and not obs.event_cbs
    alive = [t.name for t in threading.enumerate() if t.name.startswith("ShadowPlay")]
    assert not alive, alive
    print("SHUTDOWN OK; Fehlerlogs:", [m for l, m in obs.logs if l == obs.LOG_ERROR])
