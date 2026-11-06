# runtime/

Optionaler Ordner für eine **eigene Python-Installation**, die nur OBS benutzt.
Optional folder for a **dedicated Python install** used only by OBS.

`scripts\install_python.ps1` installiert hier (`runtime\python`) die offizielle Python-Version von python.org
**inklusive Tcl/Tk**. Danach in OBS unter *Werkzeuge → Skripte → Python-Einstellungen* diesen Pfad eintragen.
Der Ordner `runtime/python/` wird nicht in Git eingecheckt und nicht ins Release-Archiv gepackt.

The "embeddable" Python zip from python.org **cannot** be used: it contains no Tkinter.
