#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Draws one open passport spread for the invented island Republic of
Selvaria, entirely with the Python standard library (no network, no
files read, no time/random: fully deterministic).

Concept (one strong idea + one telling detail):
  - Holder Elena Maris Voss, lighthouse keeper of North Ferry, born in
    Port Meridian, capital of Selvaria. Portrait, place-name and
    occupation all belong to the same sea-faring island country.
  - Travel history, all after the 12 MAR 2019 issue date and before the
    12 MAR 2029 expiry: Talmora Apr 2019, Drevenka Sep 2021,
    Ostara May-Jun 2023, re-entry to Selvaria 03 JUN 2023.
  - Telling paperwork detail: Condition 7 -- SEA TRAVEL ONLY. The
    holder may not use the Northern Ice Road; entry only by the North
    Ferry, fee 40 TALM paid. That one box says what kind of place
    Selvaria is, with no caption needed.
"""

import math
import os
import struct
import zlib

W, H = 1024, 720

# ---------------------------------------------------------------- palette
DESK = (36, 46, 58)
DESK_DARK = (28, 36, 46)
PAGE = (246, 241, 227)
PAGE_LINE = (120, 110, 85)
GUILLOCHE = (232, 224, 198)
INK = (35, 35, 40)
LABEL = (96, 104, 122)
GREEN = (30, 70, 55)
GOLD = (176, 141, 60)
STAMP_BLUE = (38, 84, 140)
STAMP_RED = (168, 52, 44)
STAMP_GREEN = (46, 110, 70)
STAMP_PURPLE = (110, 70, 140)
MRZ_BG = (233, 228, 210)
SIG_BLUE = (30, 50, 110)
SKIN = (216, 165, 131)
SKIN_DARK = (198, 145, 112)
HAIR = (58, 42, 30)
JACKET = (43, 58, 85)
PHOTO_BG = (178, 192, 204)

# ---------------------------------------------------------------- framebuffer
buf = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i], buf[i + 1], buf[i + 2] = c


def fill_rect(x0, y0, x1, y1, c):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    for y in range(y0, y1):
        base = (y * W + x0) * 3
        for x in range(x0, x1):
            i = base + (x - x0) * 3
            buf[i], buf[i + 1], buf[i + 2] = c


def hline(x0, x1, y, c):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        px(x, y, c)


def vline(x, y0, y1, c):
    for y in range(min(y0, y1), max(y0, y1) + 1):
        px(x, y, c)


def line(x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def rect_outline(x0, y0, x1, y1, c, t=1):
    for k in range(t):
        hline(x0 + k, x1 - k, y0 + k, c)
        hline(x0 + k, x1 - k, y1 - k, c)
        vline(x0 + k, y0 + k, y1 - k, c)
        vline(x1 - k, y0 + k, y1 - k, c)


def circle_outline(cx, cy, r, c, t=1):
    for k in range(t):
        rr = r - k
        x = 0
        y = rr
        d = 3 - 2 * rr
        while x <= y:
            for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                px(cx + sx, cy + sy, c)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1


def filled_ellipse(cx, cy, rx, ry, c):
    for y in range(cy - ry, cy + ry + 1):
        t = (y - cy) / ry
        if abs(t) > 1:
            continue
        dx = int(rx * math.sqrt(1 - t * t))
        hline(cx - dx, cx + dx, y, c)


def filled_circle(cx, cy, r, c):
    filled_ellipse(cx, cy, r, r, c)


def fill_polygon(points, c):
    ys = [p[1] for p in points]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            hline(int(xs[i]), int(xs[i + 1]), y, c)


# ---------------------------------------------------------------- 5x7 font
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
}

BLANK = ("00000",) * 7


def text_width(s, scale, adv=None):
    if adv is None:
        adv = 6 * scale
    return len(s) * adv - (adv - 5 * scale)


def draw_text(x, y, s, scale, c, bold=False, adv=None):
    if adv is None:
        adv = 6 * scale
    cx = x
    for ch in s.upper():
        g = FONT.get(ch, BLANK)
        for r in range(7):
            row = g[r]
            for col in range(5):
                if row[col] == '1':
                    fill_rect(cx + col * scale, y + r * scale,
                              cx + col * scale + scale,
                              y + r * scale + scale, c)
                    if bold:
                        fill_rect(cx + col * scale + 1, y + r * scale,
                                  cx + col * scale + scale + 1,
                                  y + r * scale + scale, c)
        cx += adv
    return cx


def draw_centered(cx, y, s, scale, c, bold=False, adv=None):
    w = text_width(s, scale, adv)
    draw_text(cx - w // 2, y, s, scale, c, bold=bold, adv=adv)


# ---------------------------------------------------------------- coat of arms
def coat_of_arms(cx, cy, r):
    """Lighthouse over waves inside a ring -- the arms of Selvaria."""
    circle_outline(cx, cy, r, GREEN, t=2)
    circle_outline(cx, cy, r - 4, GREEN, t=1)
    # tower
    fill_rect(cx - 4, cy - 14, cx + 5, cy + 8, GREEN)
    fill_rect(cx - 6, cy - 18, cx + 7, cy - 14, GREEN)
    filled_circle(cx, cy - 19, 3, GOLD)
    # light rays
    line(cx - 6, cy - 19, cx - 22, cy - 26, GOLD)
    line(cx + 6, cy - 19, cx + 22, cy - 26, GOLD)
    line(cx - 6, cy - 19, cx - 24, cy - 16, GOLD)
    line(cx + 6, cy - 19, cx + 24, cy - 16, GOLD)
    # waves
    for k, wy in enumerate((cy + 12, cy + 18)):
        pts = []
        for dx in range(-r + 6, r - 5):
            pts.append((cx + dx, wy + int(2 * math.sin(dx / 6.0 + k))))
        for a, b in zip(pts, pts[1:]):
            line(a[0], a[1], b[0], b[1], GREEN)


# ---------------------------------------------------------------- portrait
def draw_photo(x0, y0, x1, y1):
    # backdrop: three vertical bands, pale harbour light
    mid = (x0 + x1) // 2
    fill_rect(x0, y0, mid, y1, PHOTO_BG)
    fill_rect(mid, y0, x1, y1, (168, 184, 198))
    fill_rect(x0, y0, x1, y0 + 26, (188, 200, 210))
    cx = (x0 + x1) // 2
    # shoulders / jacket
    fill_polygon([(x0 + 6, y1), (x1 - 6, y1), (x1 - 22, y1 - 58),
                  (cx + 16, y1 - 74), (cx - 16, y1 - 74),
                  (x0 + 22, y1 - 58)], JACKET)
    # shirt V
    fill_polygon([(cx - 14, y1 - 72), (cx + 14, y1 - 72),
                  (cx, y1 - 44)], (240, 238, 230))
    # neck
    fill_rect(cx - 9, y1 - 102, cx + 10, y1 - 70, SKIN)
    fill_rect(cx - 9, y1 - 102, cx + 10, y1 - 94, SKIN_DARK)
    # hair, back mass + bun
    filled_ellipse(cx, y1 - 138, 38, 46, HAIR)
    filled_circle(cx, y1 - 176, 15, HAIR)
    # face
    filled_ellipse(cx, y1 - 132, 32, 40, SKIN)
    # ears
    filled_ellipse(x0 + 40, y1 - 132, 5, 9, SKIN)
    filled_ellipse(x1 - 40, y1 - 132, 5, 9, SKIN)
    # hair, side locks
    fill_rect(x0 + 30, y1 - 168, x0 + 44, y1 - 62, HAIR)
    fill_rect(x1 - 44, y1 - 168, x1 - 30, y1 - 62, HAIR)
    fill_rect(x0 + 30, y1 - 168, x1 - 30, y1 - 152, HAIR)
    # eyebrows
    line(cx - 21, y1 - 142, cx - 7, y1 - 144, HAIR)
    line(cx + 7, y1 - 144, cx + 21, y1 - 142, HAIR)
    # eyes
    filled_ellipse(cx - 14, y1 - 136, 3, 2, INK)
    filled_ellipse(cx + 14, y1 - 136, 3, 2, INK)
    # nose
    line(cx, y1 - 134, cx - 2, y1 - 120, SKIN_DARK)
    line(cx - 2, y1 - 120, cx + 3, y1 - 118, SKIN_DARK)
    # mouth
    line(cx - 9, y1 - 108, cx + 9, y1 - 108, (140, 70, 60))
    line(cx - 9, y1 - 108, cx - 5, y1 - 106, (140, 70, 60))
    line(cx + 9, y1 - 108, cx + 5, y1 - 106, (140, 70, 60))
    # earrings
    filled_circle(x0 + 40, y1 - 120, 2, GOLD)
    filled_circle(x1 - 40, y1 - 120, 2, GOLD)
    rect_outline(x0, y0, x1, y1, INK, t=2)
    # embossed seal overlapping the photo's lower corner
    sx, sy, sr = x1 - 14, y1 - 14, 17
    circle_outline(sx, sy, sr, GOLD, t=2)
    circle_outline(sx, sy, sr - 4, GOLD, t=1)
    draw_centered(sx, sy - 4, "SLV", 1, GOLD, bold=True)


# ---------------------------------------------------------------- stamps
def stamp_rect(x0, y0, x1, y1, color, lines):
    """Rectangular ink stamp; lines = [(text, scale, bold, adv)]."""
    rect_outline(x0, y0, x1, y1, color, t=2)
    rect_outline(x0 + 5, y0 + 5, x1 - 5, y1 - 5, color, t=1)
    total = sum(t[1] * 7 + 4 for t in lines) - 4
    y = y0 + (y1 - y0 - total) // 2
    cx = (x0 + x1) // 2
    for text, scale, bold, adv in lines:
        draw_centered(cx, y, text, scale, color, bold=bold, adv=adv)
        y += scale * 7 + 4


def stamp_circle(cx, cy, r, color, lines):
    circle_outline(cx, cy, r, color, t=2)
    circle_outline(cx, cy, r - 5, color, t=1)
    total = sum(t[1] * 7 + 4 for t in lines) - 4
    y = cy - total // 2
    for text, scale, bold, adv in lines:
        draw_centered(cx, y, text, scale, color, bold=bold, adv=adv)
        y += scale * 7 + 4
    filled_circle(cx, cy - r + 12, 2, color)
    filled_circle(cx, cy + r - 12, 2, color)


# ---------------------------------------------------------------- the spread
def draw():
    fill_rect(0, 0, W, H, DESK)
    fill_rect(0, 0, W, 12, DESK_DARK)
    fill_rect(0, H - 12, W, H, DESK_DARK)
    # page shadow, then the two cream pages
    fill_rect(34, 38, 1002, 696, (20, 25, 34))
    fill_rect(28, 30, 996, 690, PAGE)
    # faint guilloche: diagonal lines + a large pale circle on the right page
    for d in range(-720, 1024, 26):
        line(28 + d, 690, 28 + d + 660, 30, GUILLOCHE)
    circle_outline(754, 375, 185, GUILLOCHE, t=1)
    circle_outline(754, 375, 150, GUILLOCHE, t=1)
    # gutter shadow between the pages
    fill_rect(505, 30, 510, 690, (210, 202, 180))
    fill_rect(510, 30, 514, 690, (190, 181, 158))
    vline(514, 30, 690, (170, 160, 136))
    rect_outline(34, 36, 990, 684, PAGE_LINE, t=1)
    vline(512, 36, 684, PAGE_LINE)

    # ================= LEFT PAGE: data page =================
    coat_of_arms(270, 82, 30)
    draw_centered(270, 118, "REPUBLIC OF SELVARIA", 3, GREEN, bold=True)
    draw_centered(270, 146, "PASSPORT  .  PASSEPORT", 2, INK, bold=True)
    draw_centered(270, 176, "TYPE P   CODE SLV   NO. SLV 0417826", 2, INK)
    hline(48, 492, 198, PAGE_LINE)

    draw_photo(48, 208, 198, 398)

    fields = [
        ("SURNAME", "VOSS"),
        ("GIVEN NAMES", "ELENA MARIS"),
        ("NATIONALITY", "SELVARIAN"),
        ("DATE OF BIRTH", "14 JUN 1988"),
        ("PLACE OF BIRTH", "PORT MERIDIAN"),
        ("SEX", "F"),
        ("OCCUPATION", "LIGHTHOUSE KEEPER"),
    ]
    y = 208
    for label, value in fields:
        draw_text(214, y, label, 1, LABEL, bold=True)
        draw_text(214, y + 10, value, 2, INK, bold=True)
        y += 32

    # issue block
    draw_text(48, 448, "DATE OF ISSUE", 1, LABEL, bold=True)
    draw_text(48, 458, "12 MAR 2019", 2, INK, bold=True)
    draw_text(200, 448, "AUTHORITY", 1, LABEL, bold=True)
    draw_text(200, 458, "MINISTRY OF", 2, INK, bold=True)
    draw_text(200, 474, "INTERIOR", 2, INK, bold=True)
    draw_text(360, 448, "DATE OF EXPIRY", 1, LABEL, bold=True)
    draw_text(360, 458, "12 MAR 2029", 2, INK, bold=True)
    hline(48, 492, 500, PAGE_LINE)

    # holder's signature (fixed squiggle, dark blue ink)
    draw_text(48, 518, "HOLDER'S SIGNATURE", 1, LABEL, bold=True)
    sig = [(52, 545), (70, 532), (86, 548), (102, 536), (118, 546),
           (134, 534), (152, 544), (170, 538), (188, 546), (206, 540),
           (224, 546), (240, 542)]
    for a, b in zip(sig, sig[1:]):
        line(a[0], a[1], b[0], b[1], SIG_BLUE)
        line(a[0], a[1] + 1, b[0], b[1] + 1, SIG_BLUE)
    hline(48, 300, 556, PAGE_LINE)

    # machine-readable zone (agrees with the data above)
    fill_rect(36, 572, 504, 632, MRZ_BG)
    rect_outline(36, 572, 504, 632, PAGE_LINE, t=1)
    mrz1 = ("P<SLVMARIS<<ELENA" + "<" * 27)[:44]
    mrz2 = "SLV0417828SEL8806149F2903127" + "<" * 14 + "08"
    assert len(mrz1) == 44 and len(mrz2) == 44
    draw_text(40, 580, mrz1, 2, INK, adv=10)
    draw_text(40, 600, mrz2, 2, INK, adv=10)

    draw_centered(270, 652,
                  "THIS PASSPORT REMAINS THE PROPERTY OF THE REPUBLIC OF SELVARIA",
                  1, LABEL)

    # ================= RIGHT PAGE: visas =================
    draw_centered(754, 52, "VISAS", 3, GREEN, bold=True)
    draw_text(898, 56, "PAGE 12", 2, LABEL, bold=True)
    hline(532, 976, 84, PAGE_LINE)

    stamp_rect(540, 100, 738, 190, STAMP_BLUE, [
        ("TALMORA", 2, True, None),
        ("ARRIVAL", 2, True, None),
        ("02 APR 2019", 2, False, None),
        ("NORTH FERRY", 2, False, None),
    ])
    stamp_rect(770, 100, 968, 190, STAMP_BLUE, [
        ("TALMORA", 2, True, None),
        ("DEPARTURE", 2, True, None),
        ("18 APR 2019", 2, False, None),
        ("NORTH FERRY", 2, False, None),
    ])
    stamp_rect(540, 208, 738, 298, STAMP_RED, [
        ("DREVENKA", 2, True, None),
        ("ARRIVAL", 2, True, None),
        ("07 SEP 2021", 2, False, None),
        ("SOUTH GATE", 2, False, None),
    ])
    stamp_rect(770, 208, 968, 298, STAMP_RED, [
        ("DREVENKA", 2, True, None),
        ("DEPARTURE", 2, True, None),
        ("21 SEP 2021", 2, False, None),
        ("SOUTH GATE", 2, False, None),
    ])
    stamp_circle(639, 385, 62, STAMP_PURPLE, [
        ("OSTARA", 2, True, None),
        ("ARRIVAL", 2, True, None),
        ("11 MAY 2023", 2, False, 9),
    ])
    stamp_rect(770, 330, 968, 420, STAMP_PURPLE, [
        ("OSTARA", 2, True, None),
        ("DEPARTURE", 2, True, None),
        ("02 JUN 2023", 2, False, None),
        ("BORDER POST 4", 2, False, None),
    ])
    stamp_rect(540, 440, 738, 520, STAMP_GREEN, [
        ("SELVARIA", 2, True, None),
        ("ENTRY", 2, True, None),
        ("03 JUN 2023", 2, False, None),
        ("PORT MERIDIAN", 2, False, None),
    ])

    # telling detail: the visa condition that reveals the place
    rect_outline(540, 536, 968, 668, STAMP_RED, t=2)
    draw_text(556, 550, "CONDITION 7", 2, STAMP_RED, bold=True)
    draw_centered(754, 576, "SEA TRAVEL ONLY", 2, STAMP_RED, bold=True)
    draw_centered(754, 598, "HOLDER MAY NOT USE THE", 2, INK)
    draw_centered(754, 620, "NORTHERN ICE ROAD.", 2, INK)
    draw_centered(754, 642, "FERRY FEE 40 TALM - PAID", 2, INK, bold=True)
    # fee stamp overlapping the box's top-right corner
    fill_rect(860, 522, 956, 558, PAGE)
    rect_outline(860, 522, 956, 558, STAMP_RED, t=2)
    draw_centered(908, 534, "FEE PAID", 2, STAMP_RED, bold=True)


# ---------------------------------------------------------------- PNG writer
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png():
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw.extend(buf[y * W * 3:(y + 1) * W * 3])
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    draw()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(encode_png())
    print("wrote", path)


if __name__ == "__main__":
    main()
