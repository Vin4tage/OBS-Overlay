"""Hilfsfunktionen: Logging (threadsicher) und Windows-Fensterfunktionen (ctypes)."""
import ctypes
import os
import queue
import sys

IS_WINDOWS = sys.platform == "win32"
PREFIX = "[ShadowPlay Overlay]"


class Logger:
    """Sammelt Logmeldungen aus beliebigen Threads; geschrieben wird nur im OBS-Thread.

    Der Tk-Thread ruft niemals obspython auf. Meldungen werden per flush()
    (vom OBS-Timer) an script_log weitergereicht.
    """

    def __init__(self, obs_module=None):
        self._obs = obs_module
        self._q = queue.Queue()

    def info(self, msg):
        self._q.put(("info", str(msg)))

    def warning(self, msg):
        self._q.put(("warning", str(msg)))

    def error(self, msg):
        self._q.put(("error", str(msg)))

    def flush(self):
        while True:
            try:
                level, msg = self._q.get_nowait()
            except queue.Empty:
                return
            self._emit(level, msg)

    def _emit(self, level, msg):
        text = "%s %s" % (PREFIX, msg)
        if self._obs is not None:
            try:
                lv = {"info": self._obs.LOG_INFO, "warning": self._obs.LOG_WARNING,
                      "error": self._obs.LOG_ERROR}[level]
                self._obs.script_log(lv, text)
                return
            except Exception:  # pragma: no cover - Fallback
                pass
        print(text)


def fmt_time(seconds):
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return "%d:%02d:%02d" % (h, m, s) if h else "%02d:%02d" % (m, s)


def tk_try(widget, *args):
    """wm_attributes, aber ohne Absturz auf Plattformen ohne die Option."""
    try:
        widget.attributes(*args)
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------
# Windows-spezifisch (nur ctypes, keine Zusatzpakete)
# --------------------------------------------------------------------------
if IS_WINDOWS:
    from ctypes import wintypes

    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    _get_long = getattr(_user32, "GetWindowLongPtrW", None) or _user32.GetWindowLongW
    _set_long = getattr(_user32, "SetWindowLongPtrW", None) or _user32.SetWindowLongW
    _get_long.restype = ctypes.c_ssize_t
    _get_long.argtypes = [wintypes.HWND, ctypes.c_int]
    _set_long.restype = ctypes.c_ssize_t
    _set_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    _user32.GetParent.restype = wintypes.HWND
    _user32.GetParent.argtypes = [wintypes.HWND]
    _user32.GetForegroundWindow.restype = wintypes.HWND
    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    _user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    _user32.BringWindowToTop.argtypes = [wintypes.HWND]
    _user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    _user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                     ctypes.c_int, ctypes.c_int, wintypes.UINT]
    _user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    _user32.GetAsyncKeyState.restype = ctypes.c_short
    _kernel32.GetCurrentThreadId.restype = wintypes.DWORD

_GWL_EXSTYLE = -20
_WS_EX_LAYERED = 0x00080000
_WS_EX_TRANSPARENT = 0x00000020
_WS_EX_TOOLWINDOW = 0x00000080
_WS_EX_NOACTIVATE = 0x08000000
VK_ESCAPE = 0x1B


def get_hwnd(widget):
    """HWND des Top-Level-Fensters eines Tk-Widgets (nur Windows)."""
    if not IS_WINDOWS:
        return 0
    wid = widget.winfo_id()
    return _user32.GetParent(wid) or wid


def make_click_through(hwnd):
    """Fenster wird für Mausklicks 'durchsichtig' und nimmt nie den Fokus."""
    if not (IS_WINDOWS and hwnd):
        return
    style = _get_long(hwnd, _GWL_EXSTYLE)
    style |= _WS_EX_LAYERED | _WS_EX_TRANSPARENT | _WS_EX_TOOLWINDOW | _WS_EX_NOACTIVATE
    _set_long(hwnd, _GWL_EXSTYLE, style)
    # NOMOVE|NOSIZE|NOZORDER|NOACTIVATE|FRAMECHANGED
    _user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0004 | 0x0010 | 0x0020)


def force_foreground(hwnd):
    """Versucht, das Overlay in den Vordergrund zu holen (Windows blockiert das manchmal)."""
    if not (IS_WINDOWS and hwnd):
        return
    try:
        fg = _user32.GetForegroundWindow()
        cur = _kernel32.GetCurrentThreadId()
        fg_tid = _user32.GetWindowThreadProcessId(fg, None) if fg else 0
        attached = False
        if fg_tid and fg_tid != cur:
            attached = bool(_user32.AttachThreadInput(cur, fg_tid, True))
        _user32.BringWindowToTop(hwnd)
        _user32.SetForegroundWindow(hwnd)
        if attached:
            _user32.AttachThreadInput(cur, fg_tid, False)
    except Exception:
        pass


def key_down(vk):
    """Fragt den aktuellen Tastenzustand ab (Polling, kein globaler Hook)."""
    if not IS_WINDOWS:
        return False
    try:
        return bool(_user32.GetAsyncKeyState(vk) & 0x8000)
    except Exception:
        return False


def work_area():
    """Arbeitsbereich des Hauptbildschirms (ohne Taskleiste) als (l, t, r, b) oder None."""
    if not IS_WINDOWS:
        return None
    try:
        rect = wintypes.RECT()
        if _user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        pass
    return None


def ui_language_is_german():
    if not IS_WINDOWS:
        return (os.environ.get("LANG", "") or "").lower().startswith("de")
    try:
        return (_kernel32.GetUserDefaultUILanguage() & 0xFF) == 0x07
    except Exception:
        return False


def ensure_tcl_env(log=None):
    """Hilft eingebettetem Python (embed-Paket) in OBS, die Tcl/Tk-Bibliotheken zu finden.

    Im OBS-Prozess läuft kein python.exe; Tcl sucht seine Skripte sonst relativ zu obs64.exe.
    Gesetzt wird nur, wenn die Variablen fehlen und ein Ordner  tcl/tcl8.x + tcl/tk8.x  gefunden wird.
    """
    import glob
    if os.environ.get("TCL_LIBRARY") and os.environ.get("TK_LIBRARY"):
        return
    bases = []
    for entry in list(sys.path) + [sys.prefix, sys.exec_prefix, getattr(sys, "base_prefix", "")]:
        if not entry:
            continue
        entry = os.path.dirname(entry) if os.path.isfile(entry) else entry   # python36.zip -> Ordner
        bases += [entry, os.path.dirname(entry)]
    seen = set()
    for base in bases:
        if base in seen:
            continue
        seen.add(base)
        tcl = sorted(glob.glob(os.path.join(base, "tcl", "tcl8.*", "init.tcl")))
        tk = sorted(glob.glob(os.path.join(base, "tcl", "tk8.*", "tk.tcl")))
        if tcl and tk:
            os.environ.setdefault("TCL_LIBRARY", os.path.dirname(tcl[-1]))
            os.environ.setdefault("TK_LIBRARY", os.path.dirname(tk[-1]))
            if log:
                log.info("TCL_LIBRARY gesetzt auf %s" % os.environ["TCL_LIBRARY"])
            return
