"""Kompakte Statussymbole unten rechts und Aktionsmeldungen oben rechts."""
import tkinter as tk

from . import gfx, utils
from .gfx import C, KEY, FONT, FONT_SEMI


class StatusBadge:
    """Kleine, klickdurchlässige Statusanzeige mit stabilen Canvas-Elementen."""
    H = 24

    def __init__(self, root, width, opacity, with_text=False):
        self.W = int(width)
        self.with_text = with_text
        self.win = tk.Toplevel(root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        utils.tk_try(self.win, "-topmost", True)
        utils.tk_try(self.win, "-alpha", opacity)
        utils.tk_try(self.win, "-transparentcolor", KEY)
        self.win.configure(bg=KEY)
        self.canvas = tk.Canvas(self.win, width=self.W, height=self.H, bg=KEY,
                                highlightthickness=0, bd=0)
        self.canvas.pack()
        self.visible = False
        self._sig = None
        self._bg_id = gfx.rrect(self.canvas, 1, 1, self.W - 1, self.H - 1,
                                self.H // 2, fill=C["pill"], outline=C["border_hi"], width=1)
        self._text_id = self.canvas.create_text(
            25, self.H // 2, text="", anchor="w", fill=C["text"],
            font=(FONT_SEMI, 8)) if with_text else None
        self._icon = ""
        self._icon_color = None

    def place(self, x, y):
        self.win.geometry("%dx%d+%d+%d" % (self.W, self.H, x, y))

    def render(self, icon, text, color, fill=C["pill"]):
        sig = (icon, text, color, fill)
        if sig == self._sig:
            return
        self._sig = sig
        c = self.canvas
        c.itemconfigure(self._bg_id, fill=fill)   # Rand bleibt dezent, die Farbe trägt das Icon
        if self._icon != icon or self._icon_color != color:
            c.delete("status_icon")
            icon_x = self.W // 2 if not self.with_text else 13
            gfx.draw_icon(c, icon, icon_x, self.H // 2,
                          12 if self.with_text else 14, color, "status_icon")
            self._icon = icon
            self._icon_color = color
        if self._text_id is not None:
            c.itemconfigure(self._text_id, text=text, fill=C["text"])

    def show(self):
        if not self.visible:
            self.win.deiconify()
            self.win.update_idletasks()
            utils.make_click_through(utils.get_hwnd(self.win))
            self.win.lift()
            self.visible = True

    def hide(self):
        if self.visible:
            self.win.withdraw()
            self.visible = False

    def destroy(self):
        try:
            self.win.destroy()
        except Exception:
            pass


class StatusIndicators:
    """Zwei kompakte Symbole nebeneinander, fest am unteren rechten Bildschirmrand."""

    def __init__(self, root, cfg, tr):
        self._cfg = cfg["status"]
        self._root = root
        self.replay = StatusBadge(root, 26, self._cfg["opacity"], with_text=False)
        self.rec = StatusBadge(root, 78, self._cfg["opacity"], with_text=True)
        self._last_layout = None

    def _place(self, replay_active, rec_active):
        # Bildschirmkoordinaten statt Arbeitsbereich: die Badges sitzen wirklich
        # am unteren rechten Displayrand und nicht oberhalb der Taskleiste.
        area = (0, 0, self._root.winfo_screenwidth(), self._root.winfo_screenheight())
        right = area[2] - int(self._cfg["margin_right"])
        y = area[3] - int(self._cfg["margin_bottom"]) - StatusBadge.H
        gap = int(self._cfg["gap"])
        if replay_active and rec_active:
            rec_x = right - self.rec.W
            replay_x = rec_x - gap - self.replay.W
            self.replay.place(replay_x, y)
            self.rec.place(rec_x, y)
        elif rec_active:
            self.rec.place(right - self.rec.W, y)
        elif replay_active:
            self.replay.place(right - self.replay.W, y)

    def update(self, snap, now):
        replay_active = bool(snap["ready"] and snap["replay"])
        rec_active = bool(snap["ready"] and snap["recording"])
        layout = (replay_active, rec_active)
        if layout != self._last_layout:
            self._place(replay_active, rec_active)
            self._last_layout = layout

        if replay_active:
            self.replay.render("replay", "", C["accent"], C["pill"])
            self.replay.show()
        else:
            self.replay.hide()

        if rec_active:
            if snap["paused"]:
                icon, color = "pause", C["warn"]
            else:
                icon = "dot"
                color = C["danger"] if int(now * 1.6) % 2 == 0 else C["danger_hi"]
            self.rec.render(icon, utils.fmt_time(snap["elapsed"]), color, C["pill"])
            self.rec.show()
        else:
            self.rec.hide()

    def destroy(self):
        self.replay.destroy()
        self.rec.destroy()


class ActionToast:
    """Kurze, klickdurchlässige Bestätigung oben rechts (Standard: drei Sekunden)."""
    W, H = 336, 48

    def __init__(self, root, cfg):
        toast_cfg = cfg.get("toast", {})
        self._duration = float(toast_cfg.get("duration_seconds", 3.0))
        self._margin_top = int(toast_cfg.get("margin_top", 20))
        self._margin_right = int(toast_cfg.get("margin_right", 20))
        self._opacity = float(toast_cfg.get("opacity", 0.96))
        self._root = root
        self._until = 0.0
        self._sig = None
        self.visible = False
        self.win = tk.Toplevel(root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        utils.tk_try(self.win, "-topmost", True)
        utils.tk_try(self.win, "-alpha", self._opacity)
        utils.tk_try(self.win, "-transparentcolor", KEY)
        self.win.configure(bg=KEY)
        self.canvas = tk.Canvas(self.win, width=self.W, height=self.H, bg=KEY,
                                highlightthickness=0, bd=0)
        self.canvas.pack()
        self._bg_id = gfx.rrect(self.canvas, 1, 1, self.W - 1, self.H - 1, 12,
                                fill=C["panel"], outline=C["border_hi"], width=1)
        self._text_id = self.canvas.create_text(
            52, self.H // 2, text="", anchor="w", width=self.W - 70,
            fill=C["text"], font=(FONT_SEMI, 10))
        self._icon = ""
        self._position()

    def _position(self):
        sw = self.win.winfo_screenwidth()
        x = max(0, sw - self.W - self._margin_right)
        y = self._margin_top
        self.win.geometry("%dx%d+%d+%d" % (self.W, self.H, x, y))

    def show(self, text, now, icon="check", style="success"):
        colors = {
            "success": C["accent"],
            "warning": C["warn"],
            "danger": C["danger"],
        }
        color = colors.get(style, C["accent"])
        sig = (text, icon, color)
        if sig != self._sig:
            self._sig = sig
            # Erfolg = dezenter Rand; Warnung/Fehler behalten ihre Farbe am Rand.
            self.canvas.itemconfigure(
                self._bg_id, outline=C["border_hi"] if style == "success" else color)
            self.canvas.itemconfigure(self._text_id, text=text)
            if self._icon != icon:
                self.canvas.delete("toast_icon")
                gfx.draw_icon(self.canvas, icon, 26, self.H // 2, 20, color, "toast_icon")
                self._icon = icon
        self._until = now + self._duration
        if not self.visible:
            self._position()
            self.win.deiconify()
            self.win.update_idletasks()
            utils.make_click_through(utils.get_hwnd(self.win))
            self.win.lift()
            self.visible = True

    def update(self, now):
        if self.visible and now >= self._until:
            self.win.withdraw()
            self.visible = False

    def destroy(self):
        try:
            self.win.destroy()
        except Exception:
            pass
