"""Prüft, ob DIESE Python-Installation für das OBS-Overlay geeignet ist.
Ausführen mit dem Python, das in OBS eingetragen wird:  <pfad>\\python.exe scripts\\check_environment.py
Checks whether THIS Python is suitable for the OBS overlay."""
import platform
import struct
import sys

ok = True


def report(name, good, detail=""):
    global ok
    ok &= bool(good)
    print("[%s] %s %s" % ("OK" if good else "FEHLER/FAIL", name, detail))


report("Windows", sys.platform == "win32", "(%s)" % sys.platform)
report("64-bit Python", struct.calcsize("P") == 8, "(%s)" % platform.architecture()[0])
report("Python >= 3.8", sys.version_info >= (3, 8), "(%s)" % platform.python_version())
if sys.version_info[:2] != (3, 12):
    print("[HINWEIS/NOTE] Empfohlen/recommended: 3.12 - maßgeblich ist die von OBS geforderte Version.")
try:
    import ctypes  # noqa: F401
    report("ctypes", True)
except Exception as exc:
    report("ctypes", False, str(exc))
try:
    import tkinter
    root = tkinter.Tk()
    root.withdraw()
    version = root.tk.call("info", "patchlevel")
    root.destroy()
    report("Tkinter / Tcl/Tk", True, "(Tcl/Tk %s)" % version)
except Exception as exc:
    report("Tkinter / Tcl/Tk", False, "-> Python mit 'tcl/tk and IDLE' installieren (%s)" % exc)
print("\nPython-Ordner für OBS / folder to enter in OBS:", sys.exec_prefix)
print("Ergebnis / Result:", "ALLES OK / ALL OK" if ok else "PROBLEME GEFUNDEN / PROBLEMS FOUND")
sys.exit(0 if ok else 1)
