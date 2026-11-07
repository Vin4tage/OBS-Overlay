"""Zeichenhelfer (Tk-Canvas, keine Bilddateien/Zusatzpakete nötig)."""
import math

KEY = "#010203"  # Farbschlüssel für vollständig durchsichtige Bereiche (Windows: -transparentcolor)
FONT = "Segoe UI"
FONT_SEMI = "Segoe UI Semibold"   # fehlt die Schrift, nimmt Tk automatisch einen Ersatz
# Neutrale, leicht kühle Graustufen mit weißem Akzent (statt Grün).
C = {
    "panel": "#0f1114", "card": "#181a1e", "border": "#2a2d33", "border_hi": "#3d4148",
    "border_act": "#d5d9df", "hairline": "#1f2226",
    "text": "#f3f5f7", "muted": "#9399a3",
    "accent": "#f2f4f7", "accent_hi": "#ffffff", "accent_dim": "#26292e", "on_accent": "#0f1114",
    "danger": "#ff5a5f", "danger_hi": "#ff7a7e", "warn": "#f5b041",
    "btn": "#23262b", "btn_hi": "#31353c", "off": "#1a1c20", "off_text": "#585d66",
    "pill": "#0c0d0f", "ring": "#202328",
}


def recolor(c, tag, color):
    """Färbt alle Elemente eines Icons um, ohne gefüllte/ungefüllte Teile zu verwechseln."""
    for item in c.find_withtag(tag):
        for opt in ("fill", "outline"):
            try:
                if c.itemcget(item, opt):
                    c.itemconfigure(item, **{opt: color})
            except Exception:
                pass


def rrect(c, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def draw_icon(c, name, cx, cy, s, color, tag):
    """Zeichnet ein einfaches Vektor-Icon mit Kantenlänge ~s."""
    w = max(2, int(s / 8))
    if name == "replay":
        r = s * 0.42
        c.create_arc(cx - r, cy - r, cx + r, cy + r, start=60, extent=270, style="arc",
                     outline=color, width=w, tags=tag)
        a = math.radians(330)
        px, py = cx + r * math.cos(a), cy - r * math.sin(a)
        dx, dy = -math.sin(a), -math.cos(a)          # Laufrichtung (Bildschirmkoordinaten)
        nx, ny = -dy, dx
        k = s * 0.26
        c.create_polygon(px + dx * k, py + dy * k, px + nx * k * 0.8, py + ny * k * 0.8,
                         px - nx * k * 0.8, py - ny * k * 0.8, fill=color, outline=color, tags=tag)
        t = s * 0.14
        c.create_polygon(cx - t * 0.6, cy - t, cx - t * 0.6, cy + t, cx + t * 1.1, cy,
                         fill=color, outline=color, tags=tag)
    elif name == "record":
        r = s * 0.44
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=w, tags=tag)
        q = s * 0.24
        c.create_oval(cx - q, cy - q, cx + q, cy + q, fill=color, outline=color, tags=tag)
    elif name == "dot":
        q = s * 0.34
        c.create_oval(cx - q, cy - q, cx + q, cy + q, fill=color, outline=color, tags=tag)
    elif name == "pause":
        h, g = s * 0.34, s * 0.12
        for ox in (-g - w, g):
            c.create_rectangle(cx + ox, cy - h, cx + ox + w * 1.4, cy + h, fill=color, outline=color, tags=tag)
    elif name == "check":
        c.create_line(cx - s * 0.32, cy, cx - s * 0.08, cy + s * 0.26, cx + s * 0.34, cy - s * 0.26,
                      fill=color, width=w + 1, capstyle="round", joinstyle="round", tags=tag)
    elif name == "save":
        # Speicher-Symbol (Rahmen + oberer Einschub + Datenträger)
        d = s * 0.38
        c.create_rectangle(cx - d, cy - d, cx + d, cy + d, outline=color,
                           width=w, tags=tag)
        c.create_rectangle(cx - d * 0.55, cy + d * 0.02, cx + d * 0.55,
                           cy + d * 0.62, outline=color, width=max(1, w - 1), tags=tag)
        c.create_line(cx - d * 0.5, cy - d * 0.62, cx + d * 0.5, cy - d * 0.62,
                      fill=color, width=w, tags=tag)
    elif name == "alert":
        d = s * 0.38
        c.create_polygon(cx, cy - d, cx + d, cy + d * 0.78, cx - d, cy + d * 0.78,
                         outline=color, fill="", width=w, tags=tag)
        c.create_line(cx, cy - d * 0.35, cx, cy + d * 0.2,
                      fill=color, width=w, tags=tag)
        c.create_oval(cx - 1, cy + d * 0.42 - 1, cx + 1, cy + d * 0.42 + 1,
                      fill=color, outline=color, tags=tag)
    elif name == "close":
        d = s * 0.3
        c.create_line(cx - d, cy - d, cx + d, cy + d, fill=color, width=w, capstyle="round", tags=tag)
        c.create_line(cx - d, cy + d, cx + d, cy - d, fill=color, width=w, capstyle="round", tags=tag)
