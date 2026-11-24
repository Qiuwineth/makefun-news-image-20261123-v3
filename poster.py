"""THE WORLD ON MONDAY - a procedural newspaper front page.

Entry for the make.fun competition news-image-20261123
("Sum up 23 November's world news in one image").

Pure Python standard library: this module carries its own PNG
encoder and its own 5x7 bitmap typeface, draws the whole front
page pixel by pixel at 2x resolution, then downsamples for
anti-aliased type and artwork.  Running it writes entry.png
(1024x1024) into MAKEFUN_OUTPUT_DIR when that variable is set,
otherwise into the directory holding this file.
"""

import math
import os
import struct
import zlib

# ---------------------------------------------------------------- canvas

W = 1024          # final image width
H = 1024          # final image height
SS = 2            # supersampling factor
RW = W * SS       # render width
RH = H * SS       # render height

PAPER = (246, 239, 222)
INK = (26, 24, 20)
RED = (186, 30, 28)
DARKRED = (140, 26, 24)
BLUE = (28, 64, 148)
SKYBLUE = (120, 170, 225)
SEA = (46, 104, 186)
LAND = (70, 158, 78)
GREEN = (24, 116, 58)
ORANGE = (232, 116, 16)
FLAME = (248, 176, 32)
GRAY = (112, 110, 102)
LIGHTGRAY = (206, 200, 186)
WHITE = (252, 250, 244)
GOLD = (238, 196, 60)
BROWN = (128, 84, 44)
SMOKE = (168, 164, 154)

BUF = bytearray(bytes(PAPER) * (RW * RH))


def _put_row(y, x0, x1, color):
    """Fill render-space pixels [x0, x1) on row y with color."""
    if y < 0 or y >= RH:
        return
    x0 = max(0, x0)
    x1 = min(RW, x1)
    if x1 <= x0:
        return
    base = (y * RW + x0) * 3
    BUF[base:base + (x1 - x0) * 3] = bytes(color) * (x1 - x0)


def fill_rect(x, y, w, h, color):
    """Filled rectangle in final-image coordinates."""
    x0, y0 = int(x * SS), int(y * SS)
    x1, y1 = int((x + w) * SS), int((y + h) * SS)
    for yy in range(y0, y1):
        _put_row(yy, x0, x1, color)


def rect_outline(x, y, w, h, t, color):
    fill_rect(x, y, w, t, color)
    fill_rect(x, y + h - t, w, t, color)
    fill_rect(x, y, t, h, color)
    fill_rect(x + w - t, y, t, h, color)


def fill_circle(cx, cy, r, color, clip=None):
    """Filled circle; clip=(ccx, ccy, cr) keeps only pixels inside
    the clip circle (all in final-image coordinates)."""
    cx2, cy2, r2 = cx * SS, cy * SS, r * SS
    y_lo = int(cy2 - r2)
    y_hi = int(cy2 + r2)
    for yy in range(y_lo, y_hi + 1):
        dy = yy - cy2
        half = math.sqrt(max(0.0, r2 * r2 - dy * dy))
        x0, x1 = int(cx2 - half), int(cx2 + half)
        if clip is not None:
            ccx, ccy, cr = clip[0] * SS, clip[1] * SS, clip[2] * SS
            dyc = yy - ccy
            if abs(dyc) >= cr:
                continue
            halfc = math.sqrt(max(0.0, cr * cr - dyc * dyc))
            x0 = max(x0, int(ccx - halfc))
            x1 = min(x1, int(ccx + halfc))
        _put_row(yy, x0, x1, color)


def circle_outline(cx, cy, r, t, color):
    steps = max(24, int(2 * math.pi * r * 2))
    for i in range(steps):
        a = 2 * math.pi * i / steps
        fill_rect(cx + r * math.cos(a) - t / 2.0,
                  cy + r * math.sin(a) - t / 2.0, t, t, color)


def fill_poly(points, color, clip=None):
    """Scanline polygon fill (even-odd), optional circular clip."""
    ys = [p[1] for p in points]
    y_lo = int(min(ys) * SS)
    y_hi = int(max(ys) * SS)
    n = len(points)
    for yy in range(y_lo, y_hi + 1):
        fy = (yy + 0.5) / SS
        xs = []
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= fy < y1) or (y1 <= fy < y0):
                xs.append(x0 + (fy - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            x0, x1 = int(xs[k] * SS), int(xs[k + 1] * SS)
            if clip is not None:
                ccx, ccy, cr = clip[0] * SS, clip[1] * SS, clip[2] * SS
                dyc = yy - ccy
                if abs(dyc) >= cr:
                    continue
                halfc = math.sqrt(max(0.0, cr * cr - dyc * dyc))
                x0 = max(x0, int(ccx - halfc))
                x1 = min(x1, int(ccx + halfc))
            _put_row(yy, x0, x1, color)


def draw_line(x0, y0, x1, y1, t, color):
    steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(steps + 1):
        fx = x0 + (x1 - x0) * i / steps
        fy = y0 + (y1 - y0) * i / steps
        fill_rect(fx - t / 2.0, fy - t / 2.0, t, t, color)


def polyline(points, t, color):
    for i in range(len(points) - 1):
        draw_line(points[i][0], points[i][1],
                  points[i + 1][0], points[i + 1][1], t, color)


# ---------------------------------------------------------------- PNG out

def downsample():
    """Average each SS x SS block into the final 1024x1024 RGB bytes."""
    out = bytearray(W * H * 3)
    for y in range(H):
        for x in range(W):
            r = g = b = 0
            for dy in range(SS):
                base = ((y * SS + dy) * RW + x * SS) * 3
                for dx in range(SS):
                    i = base + dx * 3
                    r += BUF[i]
                    g += BUF[i + 1]
                    b += BUF[i + 2]
            o = (y * W + x) * 3
            n = SS * SS
            out[o] = r // n
            out[o + 1] = g // n
            out[o + 2] = b // n
    return bytes(out)


def write_png(path, rgb, w, h):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- typeface
# A hand-drawn 5x7 bitmap font.  Each glyph is seven rows of five
# pixels; '#' is ink, '.' is blank.

FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "#.#..", "..#..", "..#..", "..#..", "#####"),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": (".##..", ".##..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "\u2014": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "\u2022": (".....", ".....", ".##..", ".##..", ".....", ".....", "....."),
    "\u25aa": (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
    "(": ("..##.", ".#...", "#....", "#....", "#....", ".#...", "..##."),
    ")": (".##..", "...#.", "....#", "....#", "....#", "...#.", ".##.."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "*": (".....", "#.#.#", ".###.", "#.#.#", ".....", ".....", "....."),
}

ADV = 6  # glyph advance in font pixels (5 wide + 1 space)


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * ADV * scale - scale


def draw_text(x, y, text, scale, color, bold=False):
    """Draw text with its top-left at (x, y); returns the x just
    past the last glyph."""
    text = text.upper()
    cx = x
    passes = [(0, 0)]
    if bold:
        passes.append((max(1, scale // 2), 0))
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for ox, oy in passes:
            for row in range(7):
                line = glyph[row]
                for col in range(5):
                    if line[col] == "#":
                        fill_rect(cx + ox + col * scale,
                                  y + oy + row * scale, scale, scale, color)
        cx += ADV * scale
    return cx - scale


def draw_text_centered(cx, y, text, scale, color, bold=False):
    w = text_width(text, scale)
    return draw_text(cx - w / 2.0, y, text, scale, color, bold)


def draw_text_right(x_right, y, text, scale, color, bold=False):
    w = text_width(text, scale)
    return draw_text(x_right - w, y, text, scale, color, bold)


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that each fit
    max_width at the given scale."""
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(x, y, text, scale, color, max_width, line_pitch, bold=False):
    lines = wrap_text(text, scale, max_width)
    for i, line in enumerate(lines):
        draw_text(x, y + i * line_pitch, line, scale, color, bold)
    return y + len(lines) * line_pitch


# ---------------------------------------------------------------- artwork

SKY = (216, 232, 246)
FIELDBG = (96, 166, 84)
PITCH = (226, 208, 164)


def illu_globe(cx, cy, r):
    clip = (cx, cy, r)
    fill_circle(cx, cy, r, SEA)
    # continents: soft green blobs clipped to the ocean disc
    blobs = [(-0.42, -0.38, 0.30), (-0.10, -0.52, 0.22), (0.30, -0.30, 0.26),
             (-0.30, 0.05, 0.24), (0.08, 0.02, 0.30), (0.48, 0.18, 0.18),
             (-0.05, 0.48, 0.22), (0.38, 0.55, 0.15), (-0.55, 0.42, 0.14)]
    for dx, dy, dr in blobs:
        fill_circle(cx + dx * r, cy + dy * r, dr * r, LAND, clip=clip)
    # the crack: a jagged black split down the middle of the world
    crack = [(cx - 6, cy - r + 8), (cx + 8, cy - r * 0.55),
             (cx - 10, cy - r * 0.18), (cx + 6, cy + r * 0.16),
             (cx - 8, cy + r * 0.52), (cx + 4, cy + r - 10)]
    polyline(crack, 4, INK)
    branch = [(cx + 6, cy + r * 0.16), (cx + r * 0.42, cy + r * 0.34),
              (cx + r * 0.58, cy + r * 0.30)]
    polyline(branch, 3, INK)
    circle_outline(cx, cy, r, 3, INK)


def illu_thermometer(x, y):
    """x, y = top-left of the tube; the bulb sits ~118px below y."""
    fill_rect(x, y, 16, 104, WHITE)
    rect_outline(x, y, 16, 104, 2, INK)
    fill_circle(x + 8, y + 116, 14, WHITE)
    circle_outline(x + 8, y + 116, 14, 2, INK)
    # mercury: filled to the very top - past the limit
    fill_rect(x + 4, y + 4, 8, 100, RED)
    fill_circle(x + 8, y + 116, 9, RED)
    for i in range(4):
        fill_rect(x + 20, y + 10 + i * 24, 8, 2, INK)
    draw_text(x - 14, y + 140, "PAST 1.5C", 2, RED, bold=True)


def illu_tanker(x, y, w, h):
    fill_rect(x, y, w, h, SKY)
    sea_y = y + h * 0.58
    fill_rect(x, sea_y, w, y + h - sea_y, SEA)
    for i in range(6):  # wave dashes
        fill_rect(x + 10 + i * (w - 20) / 5.0, sea_y + 12 + (i % 2) * 14,
                  16, 3, WHITE)
    hull_y = y + h * 0.46
    fill_poly([(x + 8, hull_y), (x + w - 8, hull_y),
               (x + w - 24, hull_y + 22), (x + 24, hull_y + 22)], DARKRED)
    fill_rect(x + 8, hull_y - 4, w - 16, 5, INK)
    cols = [BLUE, GREEN, ORANGE, GRAY]
    for i in range(4):  # container stack
        fill_rect(x + 20 + i * 34, hull_y - 22, 30, 18, cols[i])
        rect_outline(x + 20 + i * 34, hull_y - 22, 30, 18, 1, INK)
    fill_rect(x + w - 52, hull_y - 40, 26, 36, WHITE)   # bridge tower
    rect_outline(x + w - 52, hull_y - 40, 26, 36, 2, INK)
    fill_rect(x + w - 47, hull_y - 34, 16, 8, SKYBLUE)
    fill_rect(x + w - 44, hull_y - 52, 10, 12, INK)     # funnel
    fill_circle(x + w - 39, hull_y - 60, 5, SMOKE)
    fill_circle(x + w - 30, hull_y - 66, 7, SMOKE)


def _windows(x, y, w, h, cols, rows, lit):
    for r in range(rows):
        for c in range(cols):
            wx = x + 7 + c * ((w - 10) / cols)
            wy = y + 8 + r * ((h - 12) / rows)
            fill_rect(wx, wy, 8, 10, GOLD if (r * cols + c) in lit else GRAY)


def illu_buildings(x, y, w, h):
    fill_rect(x, y, w, h, SKY)
    base = y + h
    # intact block, left
    fill_rect(x + 8, y + h * 0.30, w * 0.40, h * 0.70, LIGHTGRAY)
    rect_outline(x + 8, y + h * 0.30, w * 0.40, h * 0.70, 2, INK)
    _windows(x + 8, y + h * 0.30, w * 0.40, h * 0.70, 3, 4, {0, 3, 5, 9})
    # damaged block, right: jagged bitten top corner
    bx = x + w * 0.56
    bw = w * 0.40
    top = y + h * 0.34
    fill_poly([(bx, base), (bx, top), (bx + bw * 0.45, top),
               (bx + bw * 0.62, top + 14), (bx + bw * 0.80, top + 6),
               (bx + bw, top + 22), (bx + bw, base)], (196, 188, 172))
    polyline([(bx, base), (bx, top), (bx + bw * 0.45, top),
              (bx + bw * 0.62, top + 14), (bx + bw * 0.80, top + 6),
              (bx + bw, top + 22), (bx + bw, base)], 2, INK)
    _windows(bx, top + 16, bw, h * 0.60, 3, 3, {4})
    polyline([(bx + 16, top + 30), (bx + 26, top + 52), (bx + 18, base - 8)],
             2, INK)  # crack
    fill_circle(bx + bw * 0.62, top - 8, 9, SMOKE)      # smoke
    fill_circle(bx + bw * 0.78, top - 15, 12, SMOKE)
    fill_circle(bx + bw * 0.95, top - 6, 8, SMOKE)
    # rubble at the base
    fill_poly([(bx - 8, base), (bx + 12, base - 12), (bx + 30, base)], GRAY)
    fill_poly([(bx + 26, base), (bx + 44, base - 9), (bx + 58, base)], GRAY)
    # drone overhead
    dx, dy = x + w * 0.60, y + 12
    fill_rect(dx - 7, dy - 3, 14, 6, INK)
    draw_line(dx - 14, dy - 8, dx + 14, dy + 8, 2, INK)
    draw_line(dx - 14, dy + 8, dx + 14, dy - 8, 2, INK)
    for sx, sy in ((-15, -9), (15, -9), (-15, 9), (15, 9)):
        fill_circle(dx + sx, dy + sy, 3, INK)


def illu_factory(x, y, w, h):
    fill_rect(x, y, w, h, (240, 228, 205))
    base = y + h
    fill_rect(x + 10, base - 44, w - 20, 44, (188, 178, 164))
    rect_outline(x + 10, base - 44, w - 20, 44, 2, INK)
    fill_rect(x + 26, base - 66, 12, 24, GRAY)          # chimneys
    fill_rect(x + w - 40, base - 66, 12, 24, GRAY)
    rect_outline(x + 26, base - 66, 12, 24, 2, INK)
    rect_outline(x + w - 40, base - 66, 12, 24, 2, INK)
    fill_circle(x + 32, base - 74, 7, SMOKE)
    fill_circle(x + w - 34, base - 76, 8, SMOKE)
    for i in range(6):  # windows
        fill_rect(x + 24 + i * (w - 60) / 5.0, base - 30, 12, 14, INK)
    # flames along the roof line
    n = 7
    for i in range(n):
        fx = x + 18 + i * (w - 36) / (n - 1)
        fh = 26 + (14 if i % 2 else 0)
        fill_poly([(fx - 10, base - 44), (fx, base - 44 - fh),
                   (fx + 10, base - 44)], ORANGE)
        fill_poly([(fx - 5, base - 44), (fx, base - 44 - fh * 0.6),
                   (fx + 5, base - 44)], FLAME)


def illu_flags_eu_id(cx, y):
    """EU flag and Indonesian flag side by side, centred on cx."""
    fw, fh = 62, 40
    x0 = cx - fw - 8
    fill_rect(x0, y, fw, fh, BLUE)
    rect_outline(x0, y, fw, fh, 2, INK)
    for i in range(12):
        a = 2 * math.pi * i / 12
        fill_rect(x0 + fw / 2 + 13 * math.cos(a) - 2,
                  y + fh / 2 + 13 * math.sin(a) - 2, 4, 4, GOLD)
    x1 = cx + 8
    fill_rect(x1, y, fw, fh / 2, RED)
    fill_rect(x1, y + fh / 2, fw, fh / 2, WHITE)
    rect_outline(x1, y, fw, fh, 2, INK)


def illu_chip(x, y):
    """Chip at (x, y); a dotted route escapes to the right."""
    fill_rect(x, y, 46, 46, INK)
    rect_outline(x + 9, y + 9, 28, 28, 3, GOLD)
    for i in range(4):
        p = 6 + i * 11
        fill_rect(x + p, y - 6, 5, 6, GRAY)
        fill_rect(x + p, y + 46, 5, 6, GRAY)
        fill_rect(x - 6, y + p, 6, 5, GRAY)
        fill_rect(x + 46, y + p, 6, 5, GRAY)
    dx, dy = x + 58, y + 10
    for i in range(9):
        fill_circle(dx + i * 9, dy + (i * i) // 6, 3, RED if i > 5 else GRAY)


def illu_mountains_flags(x, y, w, h):
    fill_rect(x, y, w, h, SKY)
    base = y + h
    fill_poly([(x + 4, base), (x + w * 0.38, y + 8), (x + w * 0.66, base)],
              GRAY)
    fill_poly([(x + w * 0.40, base), (x + w * 0.72, y + 18),
               (x + w - 2, base)], (128, 126, 118))
    fill_poly([(x + w * 0.38 - 9, y + 22), (x + w * 0.38, y + 8),
               (x + w * 0.38 + 9, y + 22), (x + w * 0.38, y + 17)], WHITE)
    fill_poly([(x + w * 0.72 - 8, y + 30), (x + w * 0.72, y + 18),
               (x + w * 0.72 + 8, y + 30), (x + w * 0.72, y + 24)], WHITE)
    # India flag on a pole, left
    px = x + 14
    fill_rect(px, y + 26, 2, 34, INK)
    fill_rect(px + 2, y + 26, 24, 5, ORANGE)
    fill_rect(px + 2, y + 31, 24, 5, WHITE)
    fill_rect(px + 2, y + 36, 24, 5, GREEN)
    fill_circle(px + 14, y + 33, 2, BLUE)
    # Nepal pennant on a pole, right
    px = x + w - 30
    fill_rect(px, y + 26, 2, 34, INK)
    fill_poly([(px + 2, y + 26), (px + 22, y + 34), (px + 2, y + 38)], BLUE)
    fill_poly([(px + 2, y + 34), (px + 16, y + 40), (px + 2, y + 44)], BLUE)
    fill_circle(px + 7, y + 33, 2, WHITE)


def illu_cricket(x, y, w, h):
    fill_rect(x, y, w, h, FIELDBG)
    cx = x + w / 2
    fill_rect(cx - 15, y + 4, 30, h - 8, PITCH)
    rect_outline(cx - 15, y + 4, 30, h - 8, 1, INK)
    fill_rect(cx - 15, y + 16, 30, 2, WHITE)            # creases
    fill_rect(cx - 15, y + h - 18, 30, 2, WHITE)
    for i in range(3):                                   # stumps, both ends
        fill_rect(cx - 8 + i * 7, y + 5, 3, 12, GOLD)
        rect_outline(cx - 8 + i * 7, y + 5, 3, 12, 1, INK)
        fill_rect(cx - 8 + i * 7, y + h - 17, 3, 12, GOLD)
        rect_outline(cx - 8 + i * 7, y + h - 17, 3, 12, 1, INK)
    fill_poly([(cx + 20, y + h - 30), (cx + 30, y + h - 34),
               (cx + 40, y + h - 8), (cx + 32, y + h - 5)], BROWN)  # bat
    fill_circle(cx - 4, y + h - 26, 4, RED)              # ball


# ---------------------------------------------------------------- layout

def panel(x, y, w, h, header, color, header_h=30):
    fill_rect(x, y, w, h, PAPER)
    fill_rect(x, y, w, header_h, color)
    rect_outline(x, y, w, h, 2, INK)
    draw_text(x + 10, y + (header_h - 14) // 2, header, 2, WHITE, bold=True)


def build_page():
    # frame
    rect_outline(6, 6, 1012, 1012, 3, INK)
    rect_outline(14, 14, 996, 996, 1, INK)

    # ---- masthead
    draw_text(28, 27, "EST. TODAY \u25aa VOL. I \u2014 NO. 23", 2, INK)
    draw_text_right(996, 27, "PRICE: ONE DAY OF NEWS", 2, INK)
    fill_rect(24, 50, 976, 2, INK)
    draw_text_centered(512, 60, "THE WORLD ON MONDAY", 8, INK, bold=True)
    draw_text_centered(512, 124, "MONDAY 23 NOVEMBER 2026 \u2022 LATE EDITION",
                       3, RED, bold=True)
    fill_rect(24, 152, 976, 4, INK)
    fill_rect(24, 159, 976, 1, INK)

    # ---- lead story: COP31
    fill_rect(24, 168, 976, 302, PAPER)
    rect_outline(24, 168, 976, 302, 2, INK)
    draw_text(40, 182, "COP31 \u25aa ANTALYA, TURKIYE", 3, RED, bold=True)
    draw_text(40, 214, "CLIMATE TALKS", 7, INK, bold=True)
    draw_text(40, 272, "COLLAPSE", 7, INK, bold=True)
    draw_text(40, 334, "NO DEAL IN ANTALYA", 4, INK, bold=True)
    draw_wrapped(40, 366,
                 "THE FINAL PACT NEVER MENTIONED FOSSIL FUELS \u2014 THE WORDS "
                 "WERE CUT DESPITE 100+ NATIONS BACKING A PHASE-OUT. THE EU "
                 "WALKED OUT; AMERICA STAYED AWAY, HAVING QUIT CLIMATE "
                 "ACTION.", 2, INK, 552, 15)
    draw_text(40, 452, "'NO MENTION OF FOSSIL FUELS' \u2014 THE EU", 2, RED)
    illu_globe(748, 262, 88)
    illu_thermometer(898, 178)
    fill_rect(624, 364, 352, 40, INK)
    draw_text_centered(800, 370, "FOSSIL FUELS", 4, WHITE, bold=True)
    fill_rect(648, 385, 304, 4, RED)
    draw_text_centered(800, 414, "CUT FROM THE FINAL PACT", 2, INK)
    draw_text_centered(800, 434, "44H INTO OVERTIME \u2014 NO DEAL", 2, RED)

    # ---- row of three
    y2 = 480
    panel(24, y2, 320, 236, "WAR \u25aa THE GULF", BLUE)
    illu_tanker(34, y2 + 38, 300, 80)
    draw_text(36, y2 + 126, "HORMUZ ON FIRE", 3, INK, bold=True)
    draw_text(36, y2 + 152, "TANKERS HIT", 3, INK, bold=True)
    draw_wrapped(36, y2 + 184,
                 "TWO TANKERS STRUCK NEAR THE STRAIT. MISSILES FLEW AT "
                 "RIYADH.", 2, INK, 296, 15)

    panel(352, y2, 320, 236, "WAR \u25aa UKRAINE", BLUE)
    illu_buildings(362, y2 + 38, 300, 80)
    draw_text(364, y2 + 126, "14 MISSING IN", 3, INK, bold=True)
    draw_text(364, y2 + 152, "THE DYMER RUBBLE", 3, INK, bold=True)
    draw_wrapped(364, y2 + 184,
                 "IT LEVELS A FIVE-STOREY BLOCK NEAR KYIV IN ONE HIT.",
                 2, INK, 296, 15)

    panel(680, y2, 320, 236, "INDONESIA \u25aa DISASTER", ORANGE)
    illu_factory(690, y2 + 38, 300, 80)
    draw_text(692, y2 + 126, "CIKANDE FACTORY", 3, INK, bold=True)
    draw_text(692, y2 + 152, "INFERNO", 3, INK, bold=True)
    draw_wrapped(692, y2 + 184,
                 "FIRE GUTS A CANDY FACTORY: 24 BODY BAGS OUT, ABOUT 50 "
                 "MISSING.", 2, INK, 296, 15)

    # ---- row of four
    y3 = 726
    panel(24, y3, 232, 190, "TRADE \u25aa EU DEAL", GREEN, header_h=26)
    illu_flags_eu_id(140, y3 + 36)
    draw_text(36, y3 + 88, "730M PEOPLE,", 2, INK, bold=True)
    draw_text(36, y3 + 103, "ONE MARKET", 2, INK, bold=True)
    draw_wrapped(36, y3 + 122,
                 "JAKARTA AND BRUSSELS SIGN AFTER 10 YEARS OF TALKS.",
                 2, INK, 208, 15)

    panel(264, y3, 232, 190, "TECH \u25aa US-CHINA", INK, header_h=26)
    illu_chip(282, y3 + 36)
    draw_text(276, y3 + 88, "$12BN CHIP", 2, INK, bold=True)
    draw_text(276, y3 + 103, "PIPELINE", 2, INK, bold=True)
    draw_wrapped(276, y3 + 122,
                 "NVIDIA'S BEST AI CHIPS REACHED CHINA VIA SINGAPORE.",
                 2, INK, 208, 15)

    panel(504, y3, 232, 190, "ASIA \u25aa DIPLOMACY", BLUE, header_h=26)
    illu_mountains_flags(514, y3 + 34, 212, 50)
    draw_text(516, y3 + 88, "BALEN'S BIG", 2, INK, bold=True)
    draw_text(516, y3 + 103, "DELHI DAY", 2, INK, bold=True)
    draw_wrapped(516, y3 + 122,
                 "NEPAL'S PM MAKES HIS FIRST FOREIGN TRIP: MODI SUMMIT.",
                 2, INK, 208, 15)

    panel(744, y3, 256, 190, "SPORT \u25aa CRICKET", GREEN, header_h=26)
    illu_cricket(754, y3 + 34, 236, 50)
    draw_text(756, y3 + 88, "720! INDIA'S", 2, INK, bold=True)
    draw_text(756, y3 + 103, "RUN MOUNTAIN", 2, INK, bold=True)
    draw_wrapped(756, y3 + 122,
                 "WELLINGTON RECORD: RAHUL 136, PANT 128. NZ TRAIL BY 233.",
                 2, INK, 232, 15)

    # ---- markets strip
    fill_rect(24, 926, 976, 42, RED)
    draw_text_centered(512, 932,
                       "MARKETS IN SHOCK \u2014 AI ROUT: NASDAQ -5.28% "
                       "\u25aa S&P 500 -3.70% \u25aa CHIPS -10.7%",
                       2, WHITE, bold=True)
    draw_text_centered(512, 950,
                       "BTC $55,130 BACK TO $60,934 \u25aa GOLD $3,502 "
                       "-9.4% \u25aa BRENT $92.57", 2, WHITE)

    # ---- footer
    draw_text_centered(512, 976,
                       "ALSO TODAY: THOUSANDS MARCH IN LISBON OVER THE "
                       "COST OF LIVING", 2, INK)
    draw_text_centered(512, 992,
                       "A RUSSIAN CARGO SHIP STILL BURNS OFF FINLAND "
                       "AFTER A DRONE ATTACK", 2, INK)


def main():
    build_page()
    rgb = downsample()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        try:
            out_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            out_dir = os.getcwd()
    write_png(os.path.join(out_dir, "entry.png"), rgb, W, H)


if __name__ == "__main__":
    main()
