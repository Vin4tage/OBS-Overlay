"""Tk-Oberfläche. Läuft komplett in EINEM eigenen Thread; dort entstehen und enden alle Tk-Objekte.

Der Tk-Thread ruft niemals obspython auf: Befehle gehen über ObsController.request(),
Zustand wird über ObsController.snapshot() gelesen.
"""
import gc
import queue
import threading
import time
import tkinter as tk

from . import gfx, utils
from .gfx import C, KEY, FONT, FONT_SEMI
from .status_indicators import ActionToast, StatusIndicators

# Kompaktes, horizontal ausgerichtetes Menü im oberen Bildschirmbereich.
W, H = 690, 226
CARD_X = (18, 240, 462)
CARD_W, CARD_Y, CARD_H = 210, 70, 140


class RoundButton:
    """Canvas-Schaltfläche mit stabilen Elementen (kein Löschen/Neuzeichnen bei Hover)."""
    def __init__(self, canvas, x, y, w, h, on_click, text="", kind="secondary"):
        self.c, self.x, self.y, self.w, self.h = canvas, x, y, w, h
        self.on_click = on_click
        self.text, self.kind, self.enabled, self.hover = text, kind, True, False
        self._shape_id = gfx.rrect(
            self.c, self.x, self.y, self.x + self.w, self.y + self.h, 9,
            fill=C["btn"])
        self._text_id = self.c.create_text(
            self.x + self.w / 2, self.y + self.h / 2, text=self.text,
            fill=C["text"], font=(FONT_SEMI, 9))
        self._apply_style()

    def contains(self, x, y):
        return self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h

    def set_hover(self, hovered):
        hovered = bool(hovered and self.enabled)
        if hovered != self.hover:
            self.hover = hovered
            self._apply_style()

    def invoke(self):
        if self.enabled:
            self.on_click()

    def configure(self, text=None, kind=None, enabled=None):
        if text is not None and text != self.text:
            self.text = text
            self.c.itemconfigure(self._text_id, text=self.text)
        if kind is not None:
            self.kind = kind
        if enabled is not None:
            self.enabled = bool(enabled)
            if not self.enabled:
                self.hover = False
        self._apply_style()

    def _apply_style(self):
        if not self.enabled:
            fill, fg = C["off"], C["off_text"]
        elif self.kind == "primary":
            fill, fg = (C["accent_hi"] if self.hover else C["accent"]), C["on_accent"]
        elif self.kind == "danger":
            fill, fg = (C["danger_hi"] if self.hover else C["danger"]), "#ffffff"
        else:
            fill, fg = (C["btn_hi"] if self.hover else C["btn"]), C["text"]
        self.c.itemconfigure(self._shape_id, fill=fill)
        self.c.itemconfigure(self._text_id, fill=fg)


class MainOverlay:
    def __init__(self, root, app, cfg, tr):
        self.app, self.tr = app, tr
        self.visible = False
        self.shown_at = 0.0
        self._sig = None
        self.win = tk.Toplevel(root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        utils.tk_try(self.win, "-topmost", True)
        utils.tk_try(self.win, "-alpha", cfg["overlay"]["opacity"])
        utils.tk_try(self.win, "-transparentcolor", KEY)
        self.win.configure(bg=KEY)
        self.win.bind("<Escape>", lambda _e: self.hide())
        self._cards = {}
        self.cv = c = tk.Canvas(self.win, width=W, height=H, bg=KEY, highlightthickness=0, bd=0)
        c.pack()
        self._build(c)

    # ------------------------------------------------------------------ Aufbau
    def _build(self, c):
        tr = self.tr
        gfx.rrect(c, 2, 2, W - 2, H - 2, 18, fill=C["panel"], outline=C["border_hi"], width=1)

        # Titel und Ziehbereich. Der Schließen-Button bleibt separat anklickbar.
        c.create_rectangle(18, 10, W - 62, 58, fill=C["panel"], outline=C["panel"], tags="drag")
        c.create_text(W / 2, 34, text=tr("title"), anchor="center", fill=C["text"],
                      font=(FONT_SEMI, 12), tags="drag")
        c.create_line(26, 60, W - 26, 60, fill=C["hairline"])   # feine Trennlinie unter dem Titel
        for ev, fn in (("<ButtonPress-1>", self._drag_start), ("<B1-Motion>", self._drag_move),
                       ("<ButtonRelease-1>", self._drag_end)):
            c.tag_bind("drag", ev, fn)

        # Schließen-Knopf
        gfx.rrect(c, W - 52, 18, W - 20, 50, 8, fill=C["panel"], tags="xbtn")
        gfx.draw_icon(c, "close", W - 36, 34, 16, C["muted"], "xbtn")
        c.tag_bind("xbtn", "<Enter>", lambda _e: c.configure(cursor="hand2"))
        c.tag_bind("xbtn", "<Leave>", lambda _e: c.configure(cursor=""))
        c.tag_bind("xbtn", "<ButtonRelease-1>", lambda _e: self.hide())

        # Drei horizontale Kacheln im Stil der Nvidia-Overlay-Leiste:
        # Replay Buffer | Clip speichern | Aufnahme.
        self._card(c, CARD_X[0], "replay", tr("replay_title"), "st_rep")
        self._card(c, CARD_X[1], "save", tr("save_title"), "st_save")
        self._card(c, CARD_X[2], "record", tr("rec_title"), "st_rec")

        self.btn_rep_toggle = RoundButton(
            c, CARD_X[0] + 15, CARD_Y + 104, 180, 30, self._rep_toggle)
        self.btn_rep_save = RoundButton(
            c, CARD_X[1] + 15, CARD_Y + 104, 180, 30, self._rep_save,
            tr("btn_save"), "primary")
        self.btn_rec = RoundButton(
            c, CARD_X[2] + 15, CARD_Y + 104, 180, 30, self._rec_toggle)
        self._buttons = (self.btn_rep_toggle, self.btn_rep_save, self.btn_rec)
        self._cursor = ""

        # Mausereignisse am Canvas halten die Hover-Flächen stabil.
        c.bind("<Motion>", self._on_canvas_motion, add="+")
        c.bind("<Leave>", self._on_canvas_leave, add="+")
        c.bind("<ButtonRelease-1>", self._on_canvas_release, add="+")

    def _card(self, c, x, icon, title, status_tag):
        y = CARD_Y
        card = gfx.rrect(c, x, y, x + CARD_W, y + CARD_H, 13,
                         fill=C["card"], outline=C["border"], width=1)
        c.create_text(x + CARD_W / 2, y + 21, text=title, anchor="center",
                      fill=C["text"], font=(FONT_SEMI, 10))
        ring = c.create_oval(x + CARD_W / 2 - 22, y + 39,
                             x + CARD_W / 2 + 22, y + 83,
                             fill=C["ring"], outline=C["border"])
        gfx.draw_icon(c, icon, x + CARD_W / 2, y + 61, 24, C["muted"], "ic_" + status_tag)
        setattr(self, "t_" + status_tag, c.create_text(
            x + CARD_W / 2, y + 91, text="", anchor="center",
            fill=C["muted"], font=(FONT, 9)))
        self._cards[status_tag] = (card, ring, None)

    def _style_card(self, tag, border, icon_color):
        """Aktive Kacheln bekommen einen hellen Rand und ein helles Icon (nur bei Änderung)."""
        card, ring, last = self._cards[tag]
        if last == (border, icon_color):
            return
        self.cv.itemconfigure(card, outline=border)
        self.cv.itemconfigure(ring, outline=border)
        gfx.recolor(self.cv, "ic_" + tag, icon_color)
        self._cards[tag] = (card, ring, (border, icon_color))

    # --------------------------------------------------------- Maus / Buttons
    def _on_canvas_motion(self, event):
        hovered = None
        for button in self._buttons:
            if button.contains(event.x, event.y) and button.enabled:
                hovered = button
                break
        for button in self._buttons:
            button.set_hover(button is hovered)
        over_close = (W - 52 <= event.x <= W - 20 and 18 <= event.y <= 50)
        cursor = "hand2" if hovered is not None or over_close else ""
        if cursor != self._cursor:
            self.cv.configure(cursor=cursor)
            self._cursor = cursor

    def _on_canvas_leave(self, _event):
        for button in self._buttons:
            button.set_hover(False)
        if self._cursor:
            self.cv.configure(cursor="")
            self._cursor = ""

    def _on_canvas_release(self, event):
        for button in self._buttons:
            if button.enabled and button.contains(event.x, event.y):
                button.invoke()
                return "break"

    # ------------------------------------------------------------------ Aktionen
    def _rep_toggle(self):
        snap = self.app.controller.snapshot()
        self.app.controller.request("rep_stop" if snap["replay"] else "rep_start")

    def _rep_save(self):
        self.app.controller.request("rep_save")

    def _rec_toggle(self):
        snap = self.app.controller.snapshot()
        self.app.controller.request("rec_stop" if snap["recording"] else "rec_start")

    # ------------------------------------------------------------------ Ziehen
    def _drag_start(self, e):
        self._dx, self._dy = e.x_root - self.win.winfo_x(), e.y_root - self.win.winfo_y()

    def _drag_move(self, e):
        self.win.geometry("+%d+%d" % (e.x_root - self._dx, e.y_root - self._dy))

    def _drag_end(self, _e):
        self.app.saved_pos = (self.win.winfo_x(), self.win.winfo_y())

    # ------------------------------------------------------------ Anzeigen/Verbergen
    def _position(self):
        pos = self.app.saved_pos
        sw, sh = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        vx, vy = self.win.winfo_vrootx(), self.win.winfo_vrooty()
        vw, vh = self.win.winfo_vrootwidth() or sw, self.win.winfo_vrootheight() or sh
        if pos and vx - W + 80 <= pos[0] <= vx + vw - 80 and vy <= pos[1] <= vy + vh - H:
            x, y = pos
        else:
            x = (sw - W) // 2
            y = max(80, int(sh * 0.05))
        self.win.geometry("%dx%d+%d+%d" % (W, H, x, y))

    def show(self):
        if self.visible:
            return
        self._position()
        self.win.deiconify()
        utils.tk_try(self.win, "-topmost", True)
        self.win.lift()
        self.win.update_idletasks()
        utils.force_foreground(utils.get_hwnd(self.win))
        try:
            self.win.focus_force()
        except tk.TclError:
            pass
        self.visible = True
        self.shown_at = time.monotonic()
        self._sig = None

    def hide(self):
        if self.visible:
            self.win.withdraw()
            self.visible = False

    def toggle(self):
        self.hide() if self.visible else self.show()

    # ------------------------------------------------------------------ Aktualisieren
    def refresh(self, snap, now):
        c, tr = self.cv, self.tr
        sig = (snap["ready"], snap["recording"], snap["paused"], snap["replay"],
               snap["replay_available"], snap["busy_rec"], snap["busy_rep"],
               snap["busy_save"], int(snap["elapsed"]))
        if sig == self._sig:
            return
        self._sig = sig
        ready = snap["ready"]

        # Replay Buffer
        if not ready:
            rep_txt, rep_col = tr("waiting"), C["muted"]
        elif snap["replay"]:
            rep_txt, rep_col = tr("replay_on"), C["accent"]
        elif not snap["replay_available"]:
            rep_txt, rep_col = tr("replay_unavailable"), C["warn"]
        else:
            rep_txt, rep_col = tr("replay_off"), C["muted"]
        c.itemconfigure(self.t_st_rep, text=rep_txt, fill=rep_col)
        self.btn_rep_toggle.configure(
            text=tr("btn_disable") if snap["replay"] else tr("btn_enable"),
            enabled=ready and not snap["busy_rep"] and
                    (snap["replay"] or snap["replay_available"]))
        self.btn_rep_save.configure(
            enabled=ready and snap["replay"] and not snap["busy_save"])
        save_txt = tr("save_ready") if ready and snap["replay"] else tr("save_inactive")
        save_col = C["accent"] if ready and snap["replay"] else C["muted"]
        c.itemconfigure(self.t_st_save, text=save_txt, fill=save_col)
        rep_on = bool(ready and snap["replay"])
        self._style_card("st_rep", C["border_act"] if rep_on else C["border"],
                         C["accent"] if rep_on else C["muted"])
        self._style_card("st_save", C["border_hi"] if rep_on else C["border"],
                         C["accent"] if rep_on else C["muted"])

        # Aufnahme
        elapsed = utils.fmt_time(snap["elapsed"])
        if not ready:
            rec_txt, rec_col = tr("waiting"), C["muted"]
        elif snap["recording"] and snap["paused"]:
            rec_txt, rec_col = "%s  %s" % (tr("rec_paused"), elapsed), C["warn"]
        elif snap["recording"]:
            rec_txt, rec_col = "%s  %s" % (tr("rec_running"), elapsed), C["danger"]
        else:
            rec_txt, rec_col = tr("rec_idle"), C["muted"]
        c.itemconfigure(self.t_st_rec, text=rec_txt, fill=rec_col)
        if ready and snap["recording"]:
            self._style_card("st_rec", C["warn"] if snap["paused"] else C["danger"],
                             C["warn"] if snap["paused"] else C["danger"])
        else:
            self._style_card("st_rec", C["border"], C["muted"])
        self.btn_rec.configure(
            text=tr("btn_rec_stop") if snap["recording"] else tr("btn_rec_start"),
            kind="danger" if snap["recording"] else "primary",
            enabled=ready and not snap["busy_rec"])

    def destroy(self):
        try:
            self.win.destroy()
        except Exception:
            pass


class OverlayApp:
    """Besitzt den Tk-Thread. Genau eine Instanz pro Skript."""

    def __init__(self, controller, cfg, tr, log, saved_pos=None):
        self.controller, self.cfg, self.tr, self.log = controller, cfg, tr, log
        self.saved_pos = saved_pos
        self._inbox = queue.Queue()
        self._stop = threading.Event()
        self._started = threading.Event()
        self._thread = None
        self.failed = False
        self._esc_prev = False

    # ------------------------------------------------------- von außen (OBS-Thread)
    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="ShadowPlayOverlayTk", daemon=True)
        self._thread.start()

    @property
    def alive(self):
        return self._thread is not None and self._thread.is_alive()

    def post(self, cmd):
        self._inbox.put(cmd)

    def stop(self, timeout=3.0):
        self._stop.set()
        t = self._thread
        if t is not None and t.is_alive() and t is not threading.current_thread():
            t.join(timeout)
            if t.is_alive():
                self.log.warning("Tk-Thread hat sich nicht rechtzeitig beendet (daemon, wird mit OBS beendet).")
        self._thread = None

    # ------------------------------------------------------------------ Tk-Thread
    def _run(self):
        """Alle Tk-Objekte werden im Tk-Thread erzeugt, benutzt und freigegeben."""
        try:
            self._run_tk()
        except Exception as exc:
            self.failed = True
            self.log.error("Overlay konnte nicht erstellt werden: %s" % exc)
        finally:
            self._root = self._main = self._status = self._toast = None
            gc.collect()

    def _run_tk(self):
        root = main = status = toast = None
        try:
            root = tk.Tk()
            root.withdraw()
            main = MainOverlay(root, self, self.cfg, self.tr)
            status = StatusIndicators(root, self.cfg, self.tr)
            toast = ActionToast(root, self.cfg)
            self._root, self._main, self._status, self._toast = root, main, status, toast
            self._poll = int(self.cfg["timing"]["ui_poll_ms"])
            root.after(self._poll, self._tick)
            self._started.set()
            root.mainloop()
        finally:
            for obj in (toast, status, main):
                if obj is not None:
                    obj.destroy()
            if root is not None:
                try:
                    root.destroy()
                except Exception:
                    pass
            self._root = self._main = self._status = self._toast = None

    def _show_event_toast(self, key, args, now, warning=False):
        text = self.tr(key, *args)
        meta = {
            "toast_rec_started": ("record", "danger"),
            "toast_rec_stopped": ("check", "success"),
            "toast_rec_paused": ("pause", "warning"),
            "toast_rec_resumed": ("record", "danger"),
            "toast_replay_started": ("replay", "success"),
            "toast_replay_stopped": ("replay", "warning"),
            "toast_clip_saved": ("check", "success"),
            "toast_clip_saved_named": ("check", "success"),
        }
        icon, style = meta.get(key, ("alert", "warning" if warning else "success"))
        if warning:
            style = "warning"
        self._toast.show(text, now, icon=icon, style=style)

    def _tick(self):
        try:
            if self._stop.is_set():
                self._root.quit()
                return
            now = time.monotonic()
            while True:
                try:
                    cmd = self._inbox.get_nowait()
                except queue.Empty:
                    break
                if cmd == "toggle":
                    self._main.toggle()
                elif cmd == "show":
                    self._main.show()
                elif cmd == "hide":
                    self._main.hide()
            while True:
                try:
                    ev = self.controller.ui_events.get_nowait()
                except queue.Empty:
                    break
                if ev[0] == "toast":
                    self._show_event_toast(ev[1], ev[2:], now)
                elif ev[0] == "notice":
                    self._show_event_toast(ev[1], ev[2:], now, warning=(ev[1] != "n_saved"))
            snap = self.controller.snapshot()
            self._status.update(snap, now)
            self._toast.update(now)
            if self._main.visible:
                esc = utils.key_down(utils.VK_ESCAPE)
                if esc and not self._esc_prev and now - self._main.shown_at > 0.25:
                    self._main.hide()
                self._esc_prev = esc
                if self._main.visible:
                    self._main.refresh(snap, now)
            else:
                self._esc_prev = False
        except Exception as exc:
            self.log.error("Fehler in der Overlay-Schleife: %s" % exc)
        try:
            self._root.after(self._poll, self._tick)
        except Exception:
            pass
